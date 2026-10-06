from pathlib import Path
import sys

print("Python:", sys.version)
print("Executable:", sys.executable)

try:
    import llama_cpp
    print("llama_cpp:", getattr(llama_cpp, "__version__", "unknown"))
except Exception as exc:
    print("IMPORT ERROR:", repr(exc))
    raise

from llama_cpp import Llama

model_path = Path("models/qwen3-8b-q4_k_m.gguf").resolve()

print("Model:", model_path)
print("Exists:", model_path.is_file())
print("Size GB:", round(model_path.stat().st_size / 1024**3, 2))

print("Loading model...")

llm = Llama(
    model_path=str(model_path),
    n_ctx=2048,
    n_threads=1,
    n_gpu_layers=0,
    n_batch=64,
    use_mmap=False,
    verbose=True,
)

print("MODEL LOADED")

result = llm.create_chat_completion(
    messages=[
        {
            "role": "user",
            "content": "Say only: LOCAL AI TEST OK"
        }
    ],
    max_tokens=32,
    temperature=0.0,
)

print(result["choices"][0]["message"]["content"])