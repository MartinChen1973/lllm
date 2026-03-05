# 1. Demonstrates how to use LangServe's add_routes method to add chain to FastAPI app
# See code end for specific usage

#!/usr/bin/env python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_tools.retriever.LangChainRetriever import LangChainRetriever
from dotenv import load_dotenv, find_dotenv
from fastapi.responses import RedirectResponse
from langserve import add_routes

# Load the API key from the .env file
load_dotenv(find_dotenv(), override=True)


# Define Pydantic model for request body
class QuestionRequest(BaseModel):
    question: str

# Langchain_tools retriever
retriever = LangChainRetriever.create_question_and_context_from_path(
    "src/lesson06_LLM_Application_Structure/example_02_xzm/xmz.md"
)

# Create a prompt
template_text = """Answer the user's question based only on the context below:
Context：{context}

Question: {question}

Note:
1. If some conditions of the question (such as age, gender, symptoms, etc.) cannot be fully matched in the context, please explain this when giving the answer.
2. Please refer to "context" as "my knowledge base".
"""

prompt_template = ChatPromptTemplate.from_template(template_text)

# Create model
model = ChatOpenAI(model="gpt-5-nano")

# Create parser
parser = StrOutputParser()

# Create RunnableParallel for question and context
question_and_context = RunnableParallel(
    {
        "question": RunnablePassthrough(),
        "context": retriever,
    }
)

# Create the chain
chain = question_and_context | prompt_template | model | parser

# ==============================
# Define the FastAPI app
app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="A simple API server using LangChain's Runnable interfaces",
)

# Add the chain route
add_routes(
    app,
    chain,
    path="/chain",
)

@app.post("/ask")
async def get_chain_response(request: QuestionRequest):
    try:
        # Extract only the question text
        result = chain.invoke(request.question)
        return {"question": request.question, "answer": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def read_root():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8930)

# Run the server with the following command:

# 1. Terminal / New Terminal: Open a terminal window (should be at project root directory), run the following command
# python .src\lesson06_LLM_Application_Structure\lesson06020_xmz_server.py

# 2. Test access to the following addresses should show relevant content (not 404 page not found)
# Root: http://localhost:8930/
# Swagger UI: http://localhost:8930/docs
# Playground UI: http://localhost:8930/chain/playground
# ReDoc UI: http://localhost:8930/redoc
# OpenAPI JSON: http://localhost:8930/openapi.json
# Chain Endpoint: http://localhost:8930/chain

# 3. If you want to run the Client code, please refer to the usage instructions in the Client code.