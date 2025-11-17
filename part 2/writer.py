# agents/writer.py
import json
import os
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer

# LangChain imports
try:
    from langchain_core.prompts import PromptTemplate
    from langchain_ollama import ChatOllama
    from langchain_core.output_parsers import StrOutputParser
    HAVE_LC = True
except Exception as _:
    HAVE_LC = False

BOOTSTRAP = "localhost:9092"

def pretty_now():
    return datetime.utcnow().isoformat()

def local_fallback_writer(question: str, plan: list[str]) -> str:
    # Simple, deterministic writer for offline runs
    body = (
        f"Question: {question}\n\n"
        f"Quick plan: {', '.join(plan)}.\n\n"
        "Draft:\n"
        f"- Here's a brief answer to '{question}'.\n"
        "- It covers the essentials in a few sentences.\n"
        "- Add a concrete example to keep it grounded.\n"
        "- Wrap up with a one-line takeaway.\n\n"
        "Takeaway: Keep it concise and specific."
    )
    return body

def build_chain():
    # build langchain pipeline using ollama
    prompt = PromptTemplate.from_template(
        "You are a helpful technical writer. Using the plan below, answer the question."
        "\n\nQuestion: {question}\nPlan: {plan}\n\n"
        "Write 5-7 sentences and end with a single-sentence takeaway."
    )
    llm = ChatOllama(model="llama3", temperature=0.4)
    parser = StrOutputParser()
    return prompt | llm | parser

def main():
    consumer = KafkaConsumer(
        "tasks",
        bootstrap_servers=BOOTSTRAP,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="writer-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    use_fallback = os.getenv("USE_FAKE_LLM", "0") == "1" or not HAVE_LC
    chain = None
    if not use_fallback and HAVE_LC:
        try:
            chain = build_chain()
            print("[writer] LangChain chain ready with Ollama llama3.")
        except Exception as e:
            print(f"[writer] Could not build chain: {e}")
            print("[writer] Using local fallback writer.")
    else:
        print("[writer] Using local fallback writer.")

    print("[writer] listening on topic: tasks")
    for msg in consumer:
        data = msg.value
        qid = data.get("id", "")
        question = data.get("question", "")
        plan = data.get("plan", [])

        print(f"[writer] got task for id={qid}")

        if chain:
            answer = chain.invoke({"question": question, "plan": plan})
        else:
            answer = local_fallback_writer(question, plan)

        out = {
            "id": qid,
            "question": question,
            "plan": plan,
            "answer": answer,
            "writer_ts": pretty_now(),
        }
        producer.send("drafts", out)
        producer.flush()
        print(f"[writer] sent draft to drafts for id={qid}")

if __name__ == "__main__":
    main()
