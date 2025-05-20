def build_prompt(messages: list[dict], system_prompt: str) -> str:
    """
    Инструктивный prompt для DeepSeek/Mistral.
    Начинается с system_prompt, затем диалог Игрока и Ответы.
    """
    prompt = system_prompt.strip() + "\n\n"

    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        if not isinstance(content, str):
            continue  # ⚠️ пропускаем не-строковые значения (например, dict)
        if role == "user":
            prompt += f"Игрок: {content.strip()}\n"
        elif role == "assistant":
            prompt += f"Ответ: {content.strip()}\n"

    prompt += "Ответ:"
    return prompt.strip()
