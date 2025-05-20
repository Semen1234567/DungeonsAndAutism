import os
from dotenv import load_dotenv
from llama_cpp import Llama

load_dotenv(r"D:\DungeonsAndAutism\.env")


MODEL_PATH = os.getenv("MODEL_PATH")
N_CTX = int(os.getenv("N_CTX"))
N_THREADS = int(os.getenv("N_THREADS"))
N_BATCH      = int(os.getenv("N_BATCH"))
N_GPU_LAYERS = int(os.getenv("N_GPU_LAYERS"))

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=N_CTX,
    n_threads=N_THREADS,
    n_batch = N_BATCH,  # ⚡ ускоряет вывод
    n_gpu_layers = N_GPU_LAYERS,  # 0 = чистый CPU
    chat_format = "llama-3",  # обязателен для Llama-3

    f16_kv = True,  # экономит RAM, не трогаем
    use_mmap = True,  # модель читается быстрее
    use_mlock = False,  # не держим в RAM насильно
    verbose = True
)

def llama_generate(prompt: str, max_tokens) -> str:
    response = llm.create_chat_completion(
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.9,
        top_k=80,
        top_p=0.95,
        stop=["<|eot_id|>"]  # или попробуй без stop вообще
    )

    return response["choices"][0]["message"]["content"]
