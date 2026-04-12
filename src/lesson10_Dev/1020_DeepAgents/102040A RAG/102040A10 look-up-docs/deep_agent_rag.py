"""
Deep agent with RAG - Document lookup over organization and leave policy.

Loads the pre-built FAISS vector store from faiss/faiss_index/, exposes a lookup_docs
tool to a deep agent, and answers questions from lesson0331_tools_cross_files.

Run build_faiss_index.py first to create the index from docs/.
"""

import os
import uuid
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.tools import tool
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv(find_dotenv(), override=True)

## ⬇️ Resolve FAISS index path (built by build_faiss_index.py)
_SCRIPT_DIR = Path(__file__).resolve().parent
FAISS_INDEX_PATH = _SCRIPT_DIR / "faiss" / "faiss_index"

## ⬇️ Load pre-built FAISS index and create retriever
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = FAISS.load_local(str(FAISS_INDEX_PATH), embeddings, allow_dangerous_deserialization=True)
retriever = vectorstore.as_retriever(k=7)

## ⬇️ Build RAG chain (context + question -> answer)
RAG_PROMPT = """仅依赖下面的context回答用户的问题:
Context: {context}

Question: {question}
"""
prompt = ChatPromptTemplate.from_template(RAG_PROMPT)
llm = ChatOpenAI(
    model="gpt-4o-mini"
)

rag_chain = (
    RunnablePassthrough.assign(
        context=lambda x: "\n\n".join(
            d.page_content for d in retriever.invoke(x["question"])
        )
    )
    | prompt
    | llm
    | StrOutputParser()
)


@tool
def lookup_docs(query: str) -> str:
    """Search your document knowledge base for relevant information.

    Use this FIRST for any question about organization structure, leave policy,
    or the loaded directory documents. Returns retrieved context for answering.
    """
    return rag_chain.invoke({"question": query})


## ⬇️ Create deep agent with RAG tool
checkpointer = MemorySaver()
agent_model = init_chat_model(
    model="openai:gpt-4o-mini"
)
agent = create_deep_agent(
    model=agent_model,
    tools=[lookup_docs],
    system_prompt="""You are a helpful research assistant with access to specialized document lookup.

    ALWAYS use `lookup_docs` first for questions about organization structure, leave policy,
    or any topic covered by the loaded documents.
    Use filesystem tools to save/organize findings (e.g., write reports to /reports/).
    Plan complex queries with `write_todos`. Delegate with `task` subagent if needed.
    如果用户的问题不在context中，请回答“我不知道”。 ## ⬅️ 如果用户的问题不在context中，请回答“我不知道”。
    """,
    checkpointer=checkpointer,
)

## ⬇️ Questions from lesson0331_tools_cross_files (cross-file reasoning)
QUESTIONS = [
    "请问找谁请病假？",
    "于禁的直属领导是谁？",
    "根据于禁相关的组织结构回答：于禁的直接主管是谁？",
    "根据组织结构回答：张飞的直接主管是谁？",
    "员工张飞要请假，请问要找哪位？请提供姓名",
    "根据组织结构与请假政策思考并回答：张飞要请假，请问要找哪位？张飞的直接主管叫什么名字？",
    "需要什么证明文件吗？",
    "最多可以请几天呢？",
]

if __name__ == "__main__":
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    for question in QUESTIONS:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config,
        )
        answer = result["messages"][-1].content
        print(f"Q: {question}\nA: {answer}\n{'-' * 60}")
