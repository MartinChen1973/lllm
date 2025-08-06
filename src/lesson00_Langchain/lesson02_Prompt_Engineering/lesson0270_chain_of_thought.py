# 1. 演示复杂过程的提示词工程
# 2. 思维链的特点：分步骤、阶段性成果、可迭代（重复之前的步骤）

# Load the API key from the .env file (#010) 从.env文件中加载API密钥
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI

load_dotenv(find_dotenv())

# Create the OpenAI chatbot 创建聊天机器人
# model = ChatOpenAI(model="gpt-4o-mini")
model = ChatOpenAI(model="gpt-4o") 

# Read code from a file 从文件中读取代码
with open("src/lesson02_Prompt_Engineering/data/code.py", "r", encoding="utf-8") as file:
    code = file.read()

# 普通提示词
# print("普通提示词的结果***********************************")
# query  = """
# 利用代码中的 add_node() 和 add_edge() 和 add_conditional_edges() 
# 创建一个 mermaid td digram 脚本。
# 完整代码如下：
# """

# input = query + code

# response = model.invoke(input)

# print(response.content)
# exit(0)

# 思维链提示词
print("思维链提示词的结果***********************************")
# =============================================
query  = """
# 第1步 提取代码
提取代码中包含 add_node() 和 add_edge() 和 add_conditional_edges() 的代码行
# 第2步 列出代码
单独列出包含 add_node(), add_edge 和 add_conditional_edges 的代码行
# 第3步 替换
tools_condition 实际上就是名称为“tools”的node，请把tools_condition替换为"tools"
# 第4步：增加开始和结束
1. 总是在chatbot（或类似的node）的前面，增加一个__start__节点，且用实线链接（add_edge）。
2. 总是在chatbot（或类似的node）的后面，增加一个"__end__"节点，且用虚线链接（add_conditional_edges)。
# 第5步：列出此时的代码。
# 第6步：创建脚本
创建一个 mermaid td digram 脚本。请严格按照第5步中的代码行的数量绘制：
**注意：**
1. 所有 add_edge 绘制为实线(符号为：-->)
2. 所有 add_conditional_edges 绘制为虚线(符号为：-.->)。
两种情况都不要在线上写字。
# 第7步：检查mermaid td digram脚本是否正确。
尤其是
1. 应该包含一行:
graph TD
2. 检查虚线的绘制是否正确
第二步中的每行add_condition_edges代码，都应该在图中有一个虚线。注意！不要在线上写字，只需要绘制虚线。
3. 两个node之间，朝向单个方向最多只能有一个edge（不能同时有-->和-.->)。
4. 如果两个node之间有两根线（edge），则只能方向相反，否则就是错误的。
5. 两个node之间，最多只能有两根线（edge）。
6. 检查线条的格式是否正确（实线为-->，虚线为-.->）。
如果有错误，请返回第五步，但不要超过3次循环。


完整代码如下：
"""
# ---------------------------------------------

input = query + code

response = model.invoke(input)

print(response.content)
