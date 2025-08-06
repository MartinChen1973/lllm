import requests
from langchain_ollama import OllamaLLM

##### 访问本地Ollama API并查询可用模型
BASE_URL = "http://localhost:11434/v1"  # 本地Ollama API URL
models = requests.get(f"{BASE_URL}/models", timeout=10).json()["data"]

for model_data in models:
    print(f"Model ID: {model_data['id']}")

##### 调用模型 
# model = OllamaLLM(model="deepseek-r1:1.5b")

# response = model.invoke("请给我讲一个关于猫的笑话。")

# print(response)

model = OllamaLLM(model="deepseek-r1:14b")

response = model.invoke("请给我讲一个关于猫的笑话。")

print(response)
