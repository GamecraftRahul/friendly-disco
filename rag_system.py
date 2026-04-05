import json
from datetime import datetime

LOG_FILE = "conversation_logs/log.json"

def save_log(question, answer):
    log_entry = {
        "timestamp": str(datetime.now()),
        "question": question,
        "answer": answer
    }

    try:
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
    except:
        data = []

    data.append(log_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=4)


print("🏥 Medical RAG System Ready. Type 'exit' to stop.")

while True:
    query = input("\nAsk Medical Question: ")
    if query.lower() == "exit":
        break

    response = qa_chain.run(query)
    print("\nAnswer:", response)

    save_log(query, response)