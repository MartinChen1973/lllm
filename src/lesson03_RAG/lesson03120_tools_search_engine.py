from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from dotenv import load_dotenv, find_dotenv
from langchain_community.retrievers import TavilySearchAPIRetriever

# Load the API key from the .env file
load_dotenv(find_dotenv())

# Create the retriever from Tavily
retriever = TavilySearchAPIRetriever()

# Create a prompt
template = """仅依赖下面的context回答用户的问题:
{context}

Question: {question}
"""
prompt = ChatPromptTemplate.from_template(template)
model = ChatOpenAI(model="gpt-4o-mini")
parser = StrOutputParser()

# Function to get context from Tavily retriever
# def get_context(question):
#     documents = retriever.invoke(question)
#     return "\n".join([doc.page_content[:300] for doc in documents])  # Truncate content for brevity

def get_context(question):
    documents = retriever.invoke(question)
    context_with_sources = [
        f"Content: {doc.page_content[:300]}...\nSource: {doc.metadata.get('source', 'No URL')}"
        for doc in documents
    ]
    return "\n".join(context_with_sources)  # Include source URL along with content

# Define the full chain
question = "懂王赢得了2024大选吗？（请列出相关信息的出处，包括网站名称，网址，内容摘要）"
context = get_context(question)
chain = prompt | model | parser

# Run the chain
result = chain.invoke({"context": context, "question": question})
print(f"Q: {question}\nA: {result}")

question = "这是第几次当选？"
result = chain.invoke({"context": "", "question": question})
print(f"Q: {question}\nA: {result}")
