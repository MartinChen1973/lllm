from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv, find_dotenv
from langchain_tools.retriever.md.split_md import parse_markdown
import os

# Load API key from .env
load_dotenv(find_dotenv())

# Step 1: Load and embed markdown data
current_file_dir = os.path.dirname(os.path.abspath(__file__))
file_name = os.path.join(current_file_dir, "data", "acupoint.pos")

# Step 2: Construct prompt with system role
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一位提供中医学习助手，可以回答学生的问题以供其学习。只能根据文档内容列出相关的穴位名称。不要提供任何医疗建议、描述或解释。"),
    ("human", """
以下内容用于中医学习参考，请根据常见病症列出与之相关的穴位名称。
症状与穴位参考资料：{context}
用户问题: {question}

**注意**：
     1. 直接输出穴位的名字（如“太阳穴”），不要任何标点符号、解释。
     2. 只使用“症状与穴位参考资料”中提供的知识。
""")
])

# Step 3: Choose model and parser
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
output_parser = StrOutputParser()

# Step 4: Build the chain
setup_and_retrieval = RunnableParallel({
    "context": retriever,
    "question": RunnablePassthrough(),
})

chain = setup_and_retrieval | prompt | llm 

# Step 5: Ask question
question = "失眠怎么办？"
result = chain.invoke(question)

# Step 6: Show result
print(f"Q: {question}\nA: {result}")
