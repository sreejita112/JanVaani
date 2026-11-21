import json
import sys
sys.path.insert(0, "src")

from graph import graph
from state import AgentState

def run_evaluation(data_path="src\eval_data.json"):
    print("Evaluation script started...")

    with open(data_path, "r") as f:
        test_cases = json.load(f)
    
    results = []
    for i, case in enumerate(test_cases):
        initial_state = {
            "ticket_id": f"EVAL-{i}",
            "citizen_text": case["text"],
            "citizen_name": None,
            "citizen_email": None,
            "citizen_phone": None,
            "intent": None,
            "sentiment": None,
            "sector": None,
            "subcategory": None,
            "priority": None,
            "risk_level": None,
            "confidence": 0.0,
            "duplicate_of": None,
            "embedding": None,
            "needs_review": False,
            "human_corrections": {},
            "email_sent": False,
            "retry_count": 0,
            "errors": []
        }
        
        final = graph.invoke(initial_state)
        
        # Compare expected vs actual
        results.append({
            "text": case["text"],
            "intent": (case["expected_intent"] == final.get("intent")),
            "sentiment": (case["expected_sentiment"] == final.get("sentiment")),
            "sector": (case["expected_sector"] == final.get("sector")),
            "subcategory": (case["expected_subcategory"] == final.get("subcategory")),
            "priority": (case["expected_priority"] == final.get("priority"))
        })
    
    # Calculate accuracy per field
    total = len(results)
    acc = {field: sum(1 for r in results if r[field]) / total for field in results[0].keys() if field != "text"}
    
    print(f"Accuracy over {total} test cases:")
    for field, score in acc.items():
        print(f"  {field}: {score:.1%}")
    
    # Also count any fallback or low confidence
    # compute overall accuracy 
    all_correct = sum(1 for r in results if all(r[f] for f in r if f != "text"))
    print(f"\nOverall exact match (all fields): {all_correct/total:.1%}")

if __name__ == "__main__":
    run_evaluation()