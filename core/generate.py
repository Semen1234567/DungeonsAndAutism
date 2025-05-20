import re
from core.chat import build_prompt
from core.model import llama_generate

def postprocess_response(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[.]{3,}", "...", text)
    text = text.split("Итак,")[0].strip()  # 💥 Жёстко режем "Итак..."
    return text

def generate_response(chat: list, system_prompt: str, max_tokens: int = 600) -> str:
    """
    Генерирует ответ, используя system_prompt + chat, собранные как единый текст.
    """
    prompt_lines = [system_prompt.strip(), ""]
    round_number = 1

    # Перебираем чаты попарно: user → assistant
    for i in range(0, len(chat) - 1, 2):
        user_msg = chat[i]["content"].strip()
        assistant_msg = chat[i + 1]["content"].strip()
        prompt_lines.append(
            f"Раунд {round_number}:\n"
            f"Игрок: {user_msg}\n"
            f"Ответ: {assistant_msg}"
        )
        round_number += 1

    # Добавляем последнее сообщение игрока без ответа
    if chat and chat[-1]["role"] == "user":
        user_msg = chat[-1]["content"].strip()
        prompt_lines.append(
            f"Раунд {round_number}:\n"
            f"Игрок: {user_msg}\n"
            f"Ответ:"
        )

    full_prompt = "\n\n".join(prompt_lines)

    try:
        response = llama_generate(full_prompt, max_tokens=max_tokens)
        return response.strip()
    except Exception as e:
        return f"⚠️ Ошибка генерации: {e}"
