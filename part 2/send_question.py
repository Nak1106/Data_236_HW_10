# agents/send_question.py
import json
import sys
from datetime import datetime
from kafka import KafkaProducer

BOOTSTRAP = "localhost:9092"

def now_id():
    return datetime.utcnow().strftime("%Y%m%d%H%M%S%f")

def main():
    question = "Explain HTTP/2 vs HTTP/1.1 in a few sentences."
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    msg = {"id": now_id(), "question": question}
    producer.send("inbox", msg)
    producer.flush()
    print(f"[sender] sent question to inbox: {question!r}")

if __name__ == "__main__":
    main()
