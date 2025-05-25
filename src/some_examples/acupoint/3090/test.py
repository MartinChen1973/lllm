import requests
import json

# 接口URL
url = "http://116.63.15.30:28001/api"

# 请求参数
payload = {
    "texts": "你好"
}

# 请求头
headers = {
    "Content-Type": "application/json"
}

# 发送POST请求
response = requests.post(url, data=json.dumps(payload), headers=headers)

# 打印响应状态码和内容
if response.status_code == 200:
    print("请求成功！响应内容如下：")
    print(response.text)  # 打印原始响应内容
else:
    print(f"请求失败，状态码：{response.status_code}")
    print("错误信息：", response.text)
