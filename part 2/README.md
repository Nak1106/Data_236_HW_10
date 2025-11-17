# Part 2: Automated Evaluation with GEval and Ollama

This folder contains the code and documentation for Homework Part 2, which extends the three-agent Kafka system with automated evaluation using GEval and Ollama.

## Files Included

### Core Evaluation Files
- **`evaluator.py`** - Main evaluation script with OllamaModel wrapper and custom GEval metrics
  - Lines 27-49: OllamaModel class that wraps Ollama for DeepEval
  - Lines 123-172: Custom GEval metrics (Plan Quality, Helpfulness, Draft Improvement)
  
- **`run_evaluation_demo.py`** - End-to-end demo that sends a question and runs evaluation

### Agent Files
- **`planner.py`** - Planner agent (reads from inbox, sends to tasks)
- **`writer.py`** - Writer agent with Ollama llama3 integration (lines 35-44)
- **`reviewer.py`** - Reviewer agent (reads from drafts, sends to final)

### Helper Files
- **`send_question.py`** - Script to send a question to the inbox topic
- **`read_final.py`** - Script to read messages from the final topic
- **`requirements.txt`** - Python dependencies

### Results and Documentation
- **`REPORT.md`** - Complete report with evaluation results and reflection paragraph
- **`evaluation_results_sample.json`** - Sample evaluation output showing all metrics

## Key Implementation Highlights

### 1. OllamaModel Integration
The `OllamaModel` class in `evaluator.py` wraps Ollama to work with DeepEval's GEval framework:

```python
class OllamaModel(DeepEvalBaseLLM):
    def __init__(self, model_name="llama3"):
        self.model_name = model_name
        if HAVE_OLLAMA:
            self.llm = ChatOllama(model=model_name, temperature=0.0)
```

### 2. Writer Agent with Ollama
The Writer agent uses LangChain's ChatOllama to generate answers:

```python
llm = ChatOllama(model="llama3", temperature=0.4)
```

### 3. Custom GEval Metrics
Three custom metrics evaluate the agent pipeline:
- **Plan Quality**: Evaluates if the Planner's plan is clear and actionable
- **Helpfulness**: Evaluates Writer and Reviewer answers
- **Draft Improvement**: Checks if the Reviewer improved the Writer's draft

## How to Run

### Prerequisites
1. Docker with Kafka and Zookeeper running
2. Ollama installed with llama3 model: `ollama pull llama3`
3. Python 3.10+ with virtual environment

### Setup
```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Running the System
1. Start agents in separate terminals:
   ```bash
   python planner.py
   python writer.py
   python reviewer.py
   ```

2. Run the evaluation demo:
   ```bash
   python run_evaluation_demo.py "Your question here"
   ```

## Evaluation Results

### Test Question: "How does HTTPS encryption work?"

| Metric | Score | Status |
|--------|-------|--------|
| Planner - Plan Quality | 0.200 | FAIL |
| Writer - Helpfulness | 0.900 | PASS |
| Reviewer - Helpfulness | 0.800 | PASS |
| Reviewer - Draft Improvement | 1.000 | PASS |
| **Average** | **0.725** | |

See `REPORT.md` for detailed analysis and reflection.

## Technologies Used

- **Kafka**: Message broker for agent coordination
- **Ollama**: Local LLM (llama3) for both content generation and evaluation
- **LangChain**: Framework for LLM integration
- **DeepEval**: Framework for GEval metrics
- **Python**: Implementation language

## Notes

- The Planner currently produces generic plans, which is why it scores low (0.200)
- The Writer agent performs well (0.900) using llama3
- The Reviewer consistently improves drafts (1.000 improvement score)
- All agents coordinate via Kafka topics using correlation IDs

