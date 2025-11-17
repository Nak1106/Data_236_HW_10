# agents/run_evaluation_demo.py
# Demo script that sends a question and runs evaluation on it

import json
import time
import sys
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer

BOOTSTRAP = "localhost:9092"

def generate_id():
    # create unique id for correlation
    return datetime.utcnow().strftime("%Y%m%d%H%M%S%f")


def send_question(question_text: str) -> str:
    # send question to inbox topic and return the id
    msg_id = generate_id()
    
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    
    msg = {"id": msg_id, "question": question_text}
    producer.send("inbox", msg)
    producer.flush()
    producer.close()
    
    print(f"Sent question to inbox")
    print(f"ID: {msg_id}")
    print(f"Question: {question_text}")
    
    return msg_id


def wait_for_completion(msg_id: str, timeout=60):
    # wait for the final message to appear
    print(f"\nWaiting for pipeline to complete (timeout={timeout}s)...")
    
    consumer = KafkaConsumer(
        "final",
        bootstrap_servers=BOOTSTRAP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        group_id=f"demo-waiter-{int(time.time())}",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        consumer_timeout_ms=1000
    )
    
    start = time.time()
    found = False
    
    while time.time() - start < timeout:
        try:
            for msg in consumer:
                data = msg.value
                if data.get("id") == msg_id:
                    print(f"Pipeline complete!")
                    print(f"Status: {data.get('status')}")
                    found = True
                    break
            if found:
                break
        except Exception:
            pass
        
        time.sleep(1)
        elapsed = int(time.time() - start)
        if elapsed % 5 == 0:
            print(f"still waiting ({elapsed}s elapsed)")
    
    consumer.close()
    
    if not found:
        print(f"Timeout reached. Pipeline may still be processing.")
        print(f"You can manually run: python evaluator.py {msg_id}")
    
    return found


def run_evaluator(msg_id: str, model="llama3"):
    # run the evaluator script
    import subprocess
    
    print(f"\nStarting evaluation...")
    print(f"Model: {model}")
    
    cmd = ["python", "evaluator.py", msg_id, model]
    result = subprocess.run(cmd, capture_output=False)
    
    return result.returncode == 0


def main():
    # main workflow
    print("="*80)
    print("KAFKA AGENTS EVALUATION DEMO")
    print("="*80)
    
    # get question from args or use default
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "What are the main differences between REST and GraphQL APIs?"
    
    model_to_use = "llama3"
    
    print(f"\nQuestion: {question}")
    print(f"Judge Model: {model_to_use}")
    print(f"\n{'='*80}\n")
    
    # reminder to start agents
    print("IMPORTANT: Make sure these agents are running in separate terminals:")
    print("1. python planner.py")
    print("2. python writer.py")
    print("3. python reviewer.py")
    input("\nPress Enter to continue (Ctrl+C to cancel)...")
    
    # step 1: send the question
    print(f"\n{'='*80}")
    print("STEP 1: Sending Question")
    print("="*80)
    msg_id = send_question(question)
    
    # step 2: wait for it to process
    print(f"\n{'='*80}")
    print("STEP 2: Waiting for Pipeline")
    print("="*80)
    ok = wait_for_completion(msg_id, timeout=60)
    
    if not ok:
        print("\nPipeline did not complete in time.")
        print(f"Try running manually: python evaluator.py {msg_id}")
        sys.exit(1)
    
    # step 3: run evaluation
    print(f"\n{'='*80}")
    print("STEP 3: Running Evaluation")
    print("="*80)
    
    # give it a moment
    time.sleep(2)
    
    eval_ok = run_evaluator(msg_id, model_to_use)
    
    if eval_ok:
        print(f"\n{'='*80}")
        print("DEMO COMPLETED")
        print("="*80)
        print(f"\nResults saved to: evaluation_results_{msg_id}.json")
    else:
        print(f"\n{'='*80}")
        print("Evaluation encountered issues")
        print("="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(0)
