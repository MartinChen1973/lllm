from setuptools import setup, find_packages

setup(
    name="lllm",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Add your dependencies from requirements.txt here
        "langchain",
        "langchain-openai",
        "langchain-community",
        "langgraph",
        "python-dotenv",
        # Add other dependencies as needed
    ],
    python_requires=">=3.8",
) 