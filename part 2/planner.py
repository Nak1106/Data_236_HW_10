# agents/planner.py
import json
import time
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer

BOOTSTRAP = "localhost:9092"

def pretty_now():
    return datetime.utcnow().isoformat()

def main():
    consumer = KafkaConsumer(
        "inbox",
        bootstrap_servers=BOOTSTRAP,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="planner-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print("[planner] listening on topic: inbox")
    for msg in consumer:
        payload = msg.value
        question = payload.get("question", "").strip()
        qid = payload.get("id", "")

        print(f"[planner] got question ({qid}): {question!r}")

        if not question:
            print("[planner] skipping empty question")
            continue

        plan = [
            "Skim the question and identify key asks.",
            "Draft a concise answer (5–7 sentences).",
            "Add one concrete fact or example.",
            "Finish with a one-line takeaway."
        ]

        out = {
            "id": qid,
            "question": question,
            "plan": plan,
            "planner_ts": pretty_now(),
        }
        producer.send("tasks", out)
        producer.flush()
        print(f"[planner] sent plan to tasks for id={qid}")

if __name__ == "__main__":
    main()
