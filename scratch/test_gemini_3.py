import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key found: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")

llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", google_api_key=api_key)
try:
    response = llm.invoke("Hello, are you working?")
    print(f"Response: {response.content}")
except Exception as e:
    print(f"Error: {e}")
