import os
import httpx

GROK_API_KEY = os.getenv("GROK_API_KEY")


async def ask_grok(prompt: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "grok-beta",
                "messages": [
                    {"role": "system", "content": "Ты поддерживающий психолог, говоришь просто и по-человечески."},
                    {"role": "user", "content": prompt}
                ]
            }
        )

        data = response.json()
        return data["choices"][0]["message"]["content"]