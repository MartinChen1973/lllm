# Load the API key from the .env file (#010) 从.env文件中加载API密钥
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI

# 从当前文件夹或父文件夹中加载.env文件的配置（成为全局可访问的静态变量）。
load_dotenv(find_dotenv())

# Create the OpenAI chatbot 创建聊天机器人
model = ChatOpenAI(model="gpt-4o-mini") # Very Clever, but still not enough
# model = ChatOpenAI(model="gpt-4o") # Super Clever

################# 数字幻觉 #################
# 注意以下问题的答案随模型版本的差异可能会有略微不同
# Coplit答案  =     12.19354839
# 4o-mini答案 =     12.2072211
# 4o答案      =     12.1932631112635269
# 计算器答案  =      12.19326311126353
# query  = """
#     1.23456789 * 9.87654321 = ?
# """

# response = model.invoke(query)

# print(response.content)
# 
################# 内容幻觉 #################
response = model.invoke("请用100字总结一下下面的内容：“小明是一个小学生。”")
print(response.content)