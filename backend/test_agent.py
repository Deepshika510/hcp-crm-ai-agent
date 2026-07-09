from agent import agent_app

print("=== TEST 1: LOG NEW INTERACTION ===")
result1 = agent_app.invoke({
    "user_input": "Met Dr Verma today, discussed OncoPrime, she was very positive and wants samples next week.",
    "intent": None, "extracted_data": None, "reply": None, "saved_id": None,
})
print("REPLY:", result1["reply"])

print("\n=== TEST 2: EDIT EXISTING INTERACTION ===")
result2 = agent_app.invoke({
    "user_input": "Update interaction 6, change the sentiment to positive",
    "intent": None, "extracted_data": None, "reply": None, "saved_id": None,
})
print("REPLY:", result2["reply"])

print("\n=== TEST 3: FETCH HCP HISTORY ===")
result3 = agent_app.invoke({
    "user_input": "Show me the history for HCP number 1",
    "intent": None, "extracted_data": None, "reply": None, "saved_id": None,
})
print("REPLY:", result3["reply"])

print("\n=== TEST 4: SUGGEST NEXT ACTION ===")
result4 = agent_app.invoke({
    "user_input": "What should I focus on for my next visit with HCP 1?",
    "intent": None, "extracted_data": None, "reply": None, "saved_id": None,
})
print("REPLY:", result4["reply"])

print("\n=== TEST 5: SCHEDULE FOLLOW-UP ===")
result5 = agent_app.invoke({
    "user_input": "Schedule a follow-up with HCP 1 for next Friday to check on the OncoPrime samples",
    "intent": None, "extracted_data": None, "reply": None, "saved_id": None,
})
print("REPLY:", result5["reply"])