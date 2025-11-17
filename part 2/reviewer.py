
# agents/reviewer.py
import json
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer

BOOTSTRAP = "localhost:9092"

def pretty_now():
    return datetime.utcnow().isoformat()

def passes_basic_check(answer: str) -> tuple[bool, list[str]]:
    reasons = []
    ok = True
    if not answer or len(answer.strip()) < 80:
        ok = False
        reasons.append("Answer is too short.")
    if "Takeaway" not in answer:
        ok = False
        reasons.append("Missing final takeaway line.")
    return ok, reasons

def main():
    consumer = KafkaConsumer(
        "drafts",
        bootstrap_servers=BOOTSTRAP,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="reviewer-group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print("[reviewer] listening on topic: drafts")
    for msg in consumer:
        draft = msg.value
        qid = draft.get("id", "")
        answer = draft.get("answer", "")

        print(f"[reviewer] got draft for id={qid}")
        ok, reasons = passes_basic_check(answer)

        out = {
            "id": qid,
            "status": "approved" if ok else "rejected",
            "reasons": [] if ok else reasons,
            "answer": answer if ok else "",
            "reviewer_ts": pretty_now(),
        }
        producer.send("final", out)
        producer.flush()
        print(f"[reviewer] sent result to final for id={qid} (status={out['status']})")

if __name__ == "__main__":
    main()
