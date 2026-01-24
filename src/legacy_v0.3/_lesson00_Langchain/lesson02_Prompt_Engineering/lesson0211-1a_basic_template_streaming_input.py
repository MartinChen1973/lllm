# 1. 演示使用参数化模板，限制用户输入的问题，以便更好地引导用户输入。
# 2. 交互式选择：运行时由用户输入选择各个参数

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load the API key from the .env file 从.env文件中加载API密钥
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# 定义各字段的选项
OPTIONS = {
    "grade": {
        "1": "小学三年级",
        "2": "初中三年级",
        "3": "高中三年级"
    },
    "subject": {
        "1": "雪花",
        "2": "春节",
        "3": "是否应该废除死刑"
    },
    "type": {
        "1": "记叙文",
        "2": "说明文",
        "3": "议论文"
    },
    "size": {
        "1": "500",
        "2": "600",
        "3": "800"
    }
}

# 字段的中文名称
FIELD_NAMES = {
    "grade": "年级",
    "subject": "主题",
    "type": "作文类型",
    "size": "字数"
}

def get_user_choice(field_name: str, options: dict) -> str:
    """
    显示选项并获取用户输入
    Display options and get user input
    """
    field_display = FIELD_NAMES[field_name]
    print(f"\n请选择 {field_display}:")
    for key, value in options.items():
        print(f"  {key}. {value}")
    
    while True:
        choice = input(f"请输入选项 (1-{len(options)}): ").strip()
        if choice in options:
            selected_value = options[choice]
            print(f"✓ 已选择: {selected_value}")
            return selected_value
        else:
            print(f"❌ 无效输入，请输入 1-{len(options)} 之间的数字")

def collect_user_inputs() -> dict:
    """
    收集所有用户输入
    Collect all user inputs
    """
    print("=" * 60)
    print("欢迎使用AI作文助手！")
    print("=" * 60)
    
    params = {}
    for field_name in ["grade", "subject", "type", "size"]:
        params[field_name] = get_user_choice(field_name, OPTIONS[field_name])
    
    return params

# Prompt: create a prompt 创建提示词
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个热心的AI作文助手。你写的作文总是不低于300字，不超过1000字。"),
    ("user", "请用{grade}的水平给我写一个关于{subject}的{type}，长度大约{size}字。") # 使用参数化模板，限制用户输入的问题，以便更好地引导用户输入。
])

# Model: Create the OpenAI chatbot 创建聊天机器人
llm = ChatOpenAI(model="gpt-5-nano")

# OutputParser: Create an output parser 创建输出解析器
output_parser = StrOutputParser()

# Chain: Create and invoke a chain 创建并调用链
chain = prompt | llm | output_parser

# 收集用户输入
params = collect_user_inputs()

# 显示选择的参数
print("\n" + "=" * 60)
print("生成作文中...")
print(f"年级: {params['grade']} | 主题: {params['subject']} | 类型: {params['type']} | 字数: {params['size']}")
print("=" * 60 + "\n")

# Stream the chain responses 使用流式输出
for chunk in chain.stream(params):
    print(chunk, end="", flush=True)

print("\n" + "=" * 60)
print("作文生成完成！")
print("=" * 60)
