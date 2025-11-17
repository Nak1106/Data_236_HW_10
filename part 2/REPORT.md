# Homework Part 2 - Evaluating Kafka Agents with GEval

## Student Information
Assignment: Data 236 - Homework Part 2
Topic: Automated Evaluation of Multi-Agent Kafka System using GEval and Ollama

---

## Evaluation Results

### Test Question
**Question:** "How does HTTPS encryption work?"

### GEval Scores

| Agent | Metric | Score | Status |
|-------|--------|-------|--------|
| Planner | Plan Quality | 0.200 | FAIL |
| Writer | Helpfulness | 0.900 | PASS |
| Reviewer | Helpfulness (Final) | 0.800 | PASS |
| Reviewer | Draft Improvement | 1.000 | PASS |

**Average Score: 0.725**

**Final Status: approved**

---

## Detailed Results

### Planner (Score: 0.200)
**Reason:** The plan steps are not clear and specific, as they use vague terms like 'skim the question' and 'draft a concise answer'. Additionally, the steps do not directly address the question, instead providing general guidelines for writing an answer. The plan also lacks coverage of necessary aspects, such as considering the audience or purpose of the response.

### Writer (Score: 0.900)
**Reason:** The response directly answers the question, is easy to understand, covers key points, and provides concrete examples or facts. The explanation of TLS protocol and its use of symmetric and asymmetric cryptography demonstrates a strong understanding of HTTPS encryption. However, the takeaway statement could be more concise.

### Reviewer - Helpfulness (Score: 0.800)
**Reason:** The response directly answers the question, provides easy-to-understand explanations of key concepts like TLS handshakes and symmetric/asymmetric cryptography. It also covers important points about HTTPS encryption's purpose and mechanism. However, it could be improved by including more concrete examples or facts to further illustrate its points.

### Reviewer - Draft Improvement (Score: 1.000)
**Reason:** The response demonstrates strong alignment with the evaluation steps, as it effectively compares the quality of the final and draft responses, adds missing information (concrete fact), improves clarity, and fixes errors. The response also provides a clear takeaway summarizing the main point.

---

## Reflection on Automated Evaluation

Using automated evaluation with GEval and Ollama helped me understand how well my agents actually work together. Before this, I could only eyeball the outputs and guess if they were good. Now I have concrete scores that show the Writer agent performs well (0.900) when using llama3, but the Planner needs work because it gives generic plans instead of question-specific ones. The Draft Improvement metric (1.000) proves the Reviewer is doing its job by actually improving the Writer's output. This kind of automated scoring makes it way easier to spot weak points in the pipeline. For example, I can now see that fixing the Planner to generate better plans would probably boost the overall system quality. Having these metrics also means I can test changes and immediately know if they helped or hurt performance, which beats manually reading through outputs every time. Overall, automated evaluation turns a guessing game into something measurable and actionable.

---

## System Architecture

### Components
1. **Planner Agent**: Reads questions from `inbox` topic, creates a plan, sends to `tasks` topic
2. **Writer Agent**: Reads from `tasks` topic, uses Ollama llama3 to generate draft answer, sends to `drafts` topic
3. **Reviewer Agent**: Reads from `drafts` topic, reviews the draft, sends approved/rejected to `final` topic
4. **Evaluator**: Collects messages by correlation_id and evaluates using GEval with Ollama as judge

### Technologies Used
- **Kafka**: Message broker for agent coordination
- **Ollama**: Local LLM (llama3) for both Writer agent and evaluation judge
- **LangChain**: Integration framework for Ollama
- **DeepEval**: Framework for GEval metrics
- **Python**: Agent implementation language

### Kafka Topics
- `inbox`: Input questions
- `tasks`: Plans from Planner
- `drafts`: Draft answers from Writer
- `final`: Final approved/rejected answers from Reviewer

---

## How to Run

### Prerequisites
1. Docker (for Kafka and Zookeeper)
2. Ollama with llama3 model installed
3. Python 3.10+ with virtual environment

### Steps
1. Start Kafka containers:
   ```bash
   npm run start:docker
   ```

2. Activate virtual environment and run agents:
   ```bash
   cd agents
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run agents in separate terminals:
   ```bash
   python planner.py
   python writer.py
   python reviewer.py
   ```

4. Send a question and run evaluation:
   ```bash
   python run_evaluation_demo.py "Your question here"
   ```

---

## Code Implementation

See the following files for implementation details:
- `evaluator.py`: OllamaModel wrapper and custom GEval metrics
- `writer.py`: Writer agent with ChatOllama integration
- `run_evaluation_demo.py`: End-to-end evaluation demo
- `evaluation_results_20251117191747571128.json`: Sample evaluation output

