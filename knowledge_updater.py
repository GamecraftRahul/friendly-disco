import json

LOG_FILE = "conversation_logs/log.json"
APPROVED_FILE = "approved_knowledge.json"

with open(LOG_FILE, "r") as f:
    logs = json.load(f)

approved = []

print("Review Conversations:\n")

for i, entry in enumerate(logs):
    print(f"\n{i+1}. Q: {entry['question']}")
    print(f"   A: {entry['answer']}")
    
    choice = input("Approve this knowledge? (y/n): ")
    
    if choice.lower() == 'y':
        approved.append(entry)

with open(APPROVED_FILE, "w") as f:
    json.dump(approved, f, indent=4)

print("Approved knowledge saved.")