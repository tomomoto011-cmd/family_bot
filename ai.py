import os
import aiohttp

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


async def ask_grok(prompt: str):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {"role": "system", "content": "Ты психолог, отвечаешь просто, по-человечески и поддерживающе."},
            {"role": "user", "content": prompt}
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as resp:
            result = await resp.json()

            try:
                return result["choices"][0]["message"]["content"]
            except:
                return "Ошибка AI 😢"