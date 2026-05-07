import time
import statistics
import requests

URL = "http://localhost:8000/doe/generate"

payload = {
    "design_type": "fatorial_2k",
    "factors": 3,
    "center_points": 2,
    "fractionality": 1,
    "replicates": 1,
    "levels": [
        {"name": "A", "minimum": 10, "maximum": 20},
        {"name": "B", "minimum": 5, "maximum": 15},
        {"name": "C", "minimum": 1, "maximum": 3}
    ]
}

times = []
warmup = 5
num_tests = 30

print("Fazendo aquecimento...")
for _ in range(warmup):
    response = requests.post(URL, json=payload, timeout=60)
    if response.status_code != 200:
        print("Erro no aquecimento:")
        print(response.status_code)
        print(response.text)
        raise SystemExit()

print("Iniciando medições...")
for i in range(num_tests):
    start = time.perf_counter()
    response = requests.post(URL, json=payload, timeout=60)
    end = time.perf_counter()

    if response.status_code != 200:
        print("Erro durante teste:")
        print(response.status_code)
        print(response.text)
        raise SystemExit()

    elapsed_ms = (end - start) * 1000
    times.append(elapsed_ms)
    print(f"Teste {i+1}: {elapsed_ms:.2f} ms")

times_sorted = sorted(times)

def percentile(data, p):
    k = (len(data) - 1) * (p / 100)
    f = int(k)
    c = min(f + 1, len(data) - 1)
    if f == c:
        return data[f]
    return data[f] + (data[c] - data[f]) * (k - f)

print("\n===== RESULTADOS =====")
print(f"Média:   {statistics.mean(times):.2f} ms")
print(f"Mediana: {statistics.median(times):.2f} ms")
print(f"Mínimo:  {min(times):.2f} ms")
print(f"Máximo:  {max(times):.2f} ms")
print(f"P95:     {percentile(times_sorted, 95):.2f} ms")
print(f"P99:     {percentile(times_sorted, 99):.2f} ms")