# agents/evaluator.py
# Evaluator for the kafka agent pipeline using GEval from deepeval
# Uses ollama as the judge model

import json
import time
from datetime import datetime
from typing import Optional
from kafka import KafkaConsumer

# deepeval stuff
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import GEval
from deepeval.models.base_model import DeepEvalBaseLLM

# langchain ollama
try:
    from langchain_ollama import ChatOllama
    HAVE_OLLAMA = True
except ImportError:
    HAVE_OLLAMA = False
    print("Warning: langchain-ollama not installed")

BOOTSTRAP = "localhost:9092"

class OllamaModel(DeepEvalBaseLLM):
    # wrapper to use ollama with deepeval
    def __init__(self, model_name="llama3"):
        self.model_name = model_name
        if HAVE_OLLAMA:
            self.llm = ChatOllama(model=model_name, temperature=0.0)
        else:
            self.llm = None
        
    def load_model(self):
        return self.llm
    
    def generate(self, prompt: str) -> str:
        if self.llm is None:
            return "Error: Ollama not available"
        response = self.llm.invoke(prompt)
        return response.content
    
    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)
    
    def get_model_name(self) -> str:
        return f"ollama/{self.model_name}"


class AgentPipelineCollector:
    # collects messages from kafka topics using the correlation id
    def __init__(self, timeout_seconds=30):
        self.timeout = timeout_seconds
        self.bootstrap = BOOTSTRAP
        
    def collect_by_id(self, corr_id: str):
        # get plan, draft, and final for a given correlation id
        print(f"\nCollecting messages for id={corr_id}")
        
        data_collected = {
            "plan": None,
            "draft": None,
            "final": None
        }
        
        # check each topic
        topics = [
            ("tasks", "plan"),
            ("drafts", "draft"),
            ("final", "final")
        ]
        
        for topic_name, key in topics:
            msg = self._find_in_topic(topic_name, corr_id)
            if msg:
                data_collected[key] = msg
                print(f"Found {key} in topic '{topic_name}'")
            else:
                print(f"Missing {key} from topic '{topic_name}'")
        
        return data_collected
    
    def _find_in_topic(self, topic, corr_id: str) -> Optional[dict]:
        # search a topic for message with matching id
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            group_id=f"evaluator-{topic}-{int(time.time())}",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            consumer_timeout_ms=5000
        )
        
        found = None
        try:
            for msg in consumer:
                data = msg.value
                if data.get("id") == corr_id:
                    found = data
                    break
        except Exception as e:
            pass
        finally:
            consumer.close()
        
        return found


class AgentEvaluator:
    # evaluates the agent pipeline using geval metrics
    def __init__(self, model_name="llama3"):
        print(f"Initializing evaluator with model: {model_name}")
        self.judge = OllamaModel(model_name)
        
        # setup the metrics we'll use
        self.plan_metric = self._make_plan_quality_metric()
        self.helpful_metric = self._make_helpfulness_metric()
        self.improvement_metric = self._make_improvement_metric()
    
    def _make_plan_quality_metric(self):
        # metric for evaluating planner's plan
        from deepeval.test_case import LLMTestCaseParams
        return GEval(
            name="Plan Quality",
            criteria="Evaluate whether the plan is clear, actionable, and appropriate for answering the question. Consider: 1) Clarity - are steps clear and specific, 2) Relevance - do steps address the question, 3) Completeness - does it cover necessary aspects, 4) Actionability - can a writer follow these steps.",
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            evaluation_steps=[
                "Check if the plan steps are clear and specific",
                "Verify the steps directly address the question",  
                "Assess if the plan covers necessary aspects",
                "Determine if a writer can follow these steps"
            ],
            model=self.judge,
            threshold=0.5
        )
    
    def _make_helpfulness_metric(self):
        # metric for answer helpfulness
        from deepeval.test_case import LLMTestCaseParams
        return GEval(
            name="Helpfulness",
            criteria="Evaluate how helpful and complete the answer is for the given question. Consider: 1) Relevance - does it directly answer the question, 2) Clarity - is it easy to understand, 3) Completeness - does it cover key points, 4) Examples - are there concrete examples or facts.",
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            evaluation_steps=[
                "Check if it directly answers the question",
                "Assess if the answer is easy to understand",
                "Verify it covers key points",
                "Check for concrete examples or facts"
            ],
            model=self.judge,
            threshold=0.5
        )
    
    def _make_improvement_metric(self):
        # metric to check if reviewer improved the draft
        from deepeval.test_case import LLMTestCaseParams
        return GEval(
            name="Draft Improvement",
            criteria="Evaluate whether the final answer is better than the draft. Consider: 1) Quality - is the final answer higher quality, 2) Completeness - does it add missing information, 3) Clarity - is it clearer and more concise, 4) Correctness - are errors fixed.",
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            evaluation_steps=[
                "Compare the quality of final vs draft",
                "Check if missing information was added",
                "Assess if clarity improved",
                "Verify if errors were fixed"
            ],
            model=self.judge,
            threshold=0.3
        )
    
    def eval_planner(self, question: str, plan: list) -> dict:
        # evaluate the planner's output
        print("\nEvaluating Planner...")
        
        plan_str = "\n".join([f"{i+1}. {step}" for i, step in enumerate(plan)])
        
        test_case = LLMTestCase(
            input=question,
            actual_output=plan_str,
            context=[question]
        )
        
        self.plan_metric.measure(test_case)
        
        return {
            "agent": "Planner",
            "metric": "Plan Quality",
            "score": self.plan_metric.score,
            "reason": self.plan_metric.reason,
            "passed": self.plan_metric.score >= self.plan_metric.threshold
        }
    
    def eval_writer(self, question: str, draft: str) -> dict:
        # evaluate writer's draft
        print("\nEvaluating Writer...")
        
        test_case = LLMTestCase(
            input=question,
            actual_output=draft,
            context=[question]
        )
        
        self.helpful_metric.measure(test_case)
        
        return {
            "agent": "Writer",
            "metric": "Helpfulness",
            "score": self.helpful_metric.score,
            "reason": self.helpful_metric.reason,
            "passed": self.helpful_metric.score >= self.helpful_metric.threshold
        }
    
    def eval_reviewer(self, question: str, final_ans: str) -> dict:
        # evaluate reviewer's final answer
        print("\nEvaluating Reviewer...")
        
        test_case = LLMTestCase(
            input=question,
            actual_output=final_ans,
            context=[question]
        )
        
        self.helpful_metric.measure(test_case)
        
        return {
            "agent": "Reviewer",
            "metric": "Helpfulness (Final)",
            "score": self.helpful_metric.score,
            "reason": self.helpful_metric.reason,
            "passed": self.helpful_metric.score >= self.helpful_metric.threshold
        }
    
    def eval_improvement(self, question: str, draft: str, final: str) -> dict:
        # check if reviewer improved the draft
        print("\nEvaluating improvement from draft to final...")
        
        comparison = f"DRAFT:\n{draft}\n\nFINAL:\n{final}"
        
        test_case = LLMTestCase(
            input=question,
            actual_output=comparison,
            context=[question, draft]
        )
        
        self.improvement_metric.measure(test_case)
        
        return {
            "agent": "Reviewer",
            "metric": "Draft Improvement",
            "score": self.improvement_metric.score,
            "reason": self.improvement_metric.reason,
            "passed": self.improvement_metric.score >= self.improvement_metric.threshold
        }


def print_results(results: list):
    # print evaluation results
    print("\n" + "="*80)
    print("EVALUATION RESULTS")
    print("="*80)
    
    for r in results:
        print(f"\nAgent: {r['agent']} - Metric: {r['metric']}")
        print(f"Score: {r['score']:.3f}")
        status = "PASS" if r['passed'] else "FAIL"
        print(f"Status: {status}")
        # truncate reason if too long
        reason_text = r['reason'][:150] + "..." if len(r['reason']) > 150 else r['reason']
        print(f"Reason: {reason_text}")
    
    print("\n" + "="*80)
    avg = sum(r['score'] for r in results) / len(results)
    print(f"Average Score: {avg:.3f}")
    print("="*80 + "\n")


def main():
    # main function to run evaluation
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python evaluator.py <correlation_id> [model_name]")
        print("Example: python evaluator.py 20251103120000123456 llama3")
        sys.exit(1)
    
    corr_id = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "llama3"
    
    print(f"Starting evaluation for correlation_id={corr_id}")
    print(f"Using model: {model}")
    
    # step 1: collect messages from topics
    collector = AgentPipelineCollector()
    collected = collector.collect_by_id(corr_id)
    
    # check if we got everything
    if not all([collected["plan"], collected["draft"], collected["final"]]):
        print("\nERROR: Missing messages from pipeline")
        print(f"Plan: {'found' if collected['plan'] else 'missing'}")
        print(f"Draft: {'found' if collected['draft'] else 'missing'}")
        print(f"Final: {'found' if collected['final'] else 'missing'}")
        sys.exit(1)
    
    # extract the data we need
    question = collected["plan"]["question"]
    plan = collected["plan"]["plan"]
    draft_ans = collected["draft"]["answer"]
    final_ans = collected["final"]["answer"]
    status = collected["final"]["status"]
    
    print(f"\nAll messages collected successfully")
    print(f"Question: {question[:60]}...")
    print(f"Final Status: {status}")
    
    # step 2: run evaluations
    evaluator = AgentEvaluator(model)
    
    all_results = []
    
    # evaluate each stage
    all_results.append(evaluator.eval_planner(question, plan))
    all_results.append(evaluator.eval_writer(question, draft_ans))
    all_results.append(evaluator.eval_reviewer(question, final_ans))
    all_results.append(evaluator.eval_improvement(question, draft_ans, final_ans))
    
    # step 3: display and save results
    print_results(all_results)
    
    # save to file
    output_file = f"evaluation_results_{corr_id}.json"
    with open(output_file, "w") as f:
        json.dump({
            "correlation_id": corr_id,
            "question": question,
            "evaluated_at": datetime.utcnow().isoformat(),
            "model": model,
            "results": all_results
        }, f, indent=2)
    
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()
