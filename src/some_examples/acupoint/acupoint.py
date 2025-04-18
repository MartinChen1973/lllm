from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda
from langchain_openai.chat_models import ChatOpenAI
from dotenv import load_dotenv, find_dotenv
from load_acupoints import load_acupoint_data
from image_viewer import show_images

import os

# Load .env
load_dotenv(find_dotenv())

# Step 1: Load acupoint data
current_file_dir = os.path.dirname(os.path.abspath(__file__))
acupoint_data = load_acupoint_data()
unique_symptoms = sorted(set(item["symptom"] for item in acupoint_data))
symptom_context = "，".join(unique_symptoms)

# Step 2: Prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一位提供中医学习助手，可以把用户提出的问题，归纳为以下提供的预设症状。不要提供任何医疗建议、描述或解释。"),
    ("human", """
系统预设的症状：{context}
用户问题: {question}

**注意**：
     1. 直接用户问题对应的预设症状，（如“感冒”），不要任何标点符号、解释。
     2. 如果没有，请返回空。
     3. 如果有多个症状，用空格隔开。
     4. 只使用“系统预设的症状”中提供的症状，不要使用其中不存在的症状。
""")
])

# Step 3: LLM and chain setup
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
output_parser = StrOutputParser()
setup_and_retrieval = RunnableParallel({
    "context": RunnableLambda(lambda _: symptom_context),
    "question": RunnablePassthrough(),
})
chain = setup_and_retrieval | prompt | llm | output_parser

# Step 4: Ask a question
# question = "半夜了睡不着怎么办？"
question = "半夜睡不着，牙龈还有点疼，怎么办？"
result = chain.invoke(question)
print(f"Q: {question}\nA: {result}")

# Step 5: Process matched symptoms
matched_symptoms = result.strip().split()
matched_files = []

if not matched_symptoms or all(s.strip() == "" for s in matched_symptoms):
    print("⚠️ 没有识别出任何预设症状。")
else:
    for symptom in matched_symptoms:
        matches = [item for item in acupoint_data if item["symptom"] == symptom]
        if not matches:
            print(f"⚠️ 症状“{symptom}”未找到。")
        for m in matches:
            image_path = os.path.join(current_file_dir, "data", f"{m['file_name']}.png")
            if os.path.exists(image_path):
                matched_files.append((symptom, image_path, m["x"], m["y"]))
            else:
                print(f"⚠️ 文件不存在: {image_path}")

# Step 6: Show image(s) with red dot(s)
show_images(matched_files)
