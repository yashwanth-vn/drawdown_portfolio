from llm.gemini_client import ask_gemini

response = ask_gemini(
    "Hello, introduce yourself in one sentence."
)

print(response)