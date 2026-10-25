import os
import json
from dotenv import load_dotenv
import ollama
from google import genai

load_dotenv()

# load file
with open("./config/config.json", "r") as f:
    SYS_CONFIG =  json.load(f)

# define functions to run GEMINI models
def run_gemini(prompt: str) -> str:
    try:
        api_key=os.getenv("GEMINI_API_KEY")        
        client = genai.Client(api_key=api_key)

        model_name = SYS_CONFIG["gemini"]["model"]
        print(f"\n Model Name: {model_name}")

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={
                "temperature": SYS_CONFIG["gemini"].get("temperature"),
                "top_p": SYS_CONFIG["gemini"].get("top_p"),
                "max_output_tokens": SYS_CONFIG["gemini"].get("max_output_tokens")
            }
        )
        generated_text = response.text.strip()
        return generated_text
    except Exception as e:
        return f"\n [Error] in run_gemini(): { str(e) }"


# define functions to run local OLLAMA models
def run_ollama(history: str) -> str:
    try:
        options = {
            "temperature": SYS_CONFIG["ollama"].get("temperature", 0.2), 
            "top_p": SYS_CONFIG["ollama"].get("top_p", 0.9), 
            "num_predict": int(SYS_CONFIG["ollama"].get("num_predict", 100))
            }
        
        response = ollama.chat(
            model="qwen2.5-coder:3b",
            messages=history,
            options=options
        )
        generated_text = response["message"]["content"].strip()
        return generated_text
    except Exception as e:
        return f"\n [Error] in run_ollama(): {str(e)}"

# execute LLM function
def run_llm(history):
    try:
        provider = SYS_CONFIG["provider"]
        if provider == "ollama":
            return run_ollama(history)
        elif provider == "gemini":
            conversation_text = "\n".join(f"{m['role']}: {m['content']}" for m in history)
            return run_gemini(conversation_text)
        else:
            return "[Error] Invalid provider in config.json"
    except Exception as e:
        return f"\n [Error] in run_llm(): { str(e) }"
