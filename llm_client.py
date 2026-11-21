import os
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    def __init__(self):
        # Ensure you have updated these in your .env file
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    def call_with_fallback(self, system_prompt: str, user_prompt: str, temperature: float = 0) -> tuple[str, float, str]:
        """Returns (response_text, latency_ms, error_or_None)"""
        # Try Groq first
        try:
            start = time.time()
            llm = ChatGroq(
                model=self.groq_model,
                temperature=temperature,
                api_key=os.getenv("GROQ_API_KEY_A")
            )
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            response = llm.invoke(messages)
            latency = (time.time() - start) * 1000
            return response.content, latency, None
        except Exception as e:
            print(f"Groq failed: {e}. Falling back to Gemini...")

        # Fallback to Gemini
        try:
            start = time.time()
            llm = ChatGoogleGenerativeAI(
                model=self.gemini_model,
                temperature=temperature,
                google_api_key=os.getenv("GEMINI_API_KEY_A")
            )
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            response = llm.invoke(messages)
            latency = (time.time() - start) * 1000
            return response.content, latency, None
        except Exception as e:
            print(f"Gemini also failed: {e}")
            return "", 0, str(e)


llm_client = LLMClient()
