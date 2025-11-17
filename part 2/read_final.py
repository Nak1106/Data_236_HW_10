# agents/read_final.py
import json
from kafka import KafkaConsumer

BOOTSTRAP = "localhost:9092"

def main():
    consumer = KafkaConsumer(
        "final",
        bootstrap_servers=BOOTSTRAP,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="final-reader",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    print("[final-reader] listening on topic: final")
    for msg in consumer:
        print(json.dumps(msg.value, indent=2))

if __name__ == "__main__":
    main()
