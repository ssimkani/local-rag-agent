import time
import ollama

PROMPT = "Explain what retrieval-augmented generation is in 3 sentences."

start = time.time()
response = ollama.generate(model="llama3", prompt=PROMPT)
elapsed = time.time() - start

tokens = response['eval_count']
tps = tokens / (response['eval_duration'] / 1e9)

print(f"Tokens generated: {tokens}")
print(f"Time: {elapsed:.2f}s")
print(f"Tokens/sec: {tps:.1f}")