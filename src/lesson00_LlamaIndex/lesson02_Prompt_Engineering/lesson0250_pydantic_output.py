# 1. 演示如何使用Pydantic 告知LLM所需的输出格式。
# Why Pydantic？
# Pydantic可以让一个类自动把自己所需的格式，以json的形式反向放到提示词中，保证LLM输出的结果一定能被正确解析。

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, field_validator
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Initialize ChatOpenAI model with desired parameters
model = ChatOpenAI(model="gpt-4o-mini")
# model = ChatOpenAI(temperature=0, model="gpt-4o")

# =============================================
# Define the data structure for the couplet response
class Couplet(BaseModel):
    """Data model for Chinese couplet with validation rules."""
    
    upper_part: str = Field(
        # description="对联的上联",
        description="对联的上联，字数必须在10-15个字之间",
        min_length=10,
        max_length=15
    )
    lower_part: str = Field(
        # description="对联的下联",
        description="对联的下联，字数必须与上联相同，且字数在10-15个字之间",
        min_length=10,
        max_length=15
    )
    horizontal_part: str = Field(
        description="对联的横批，必须是4个字",
        min_length=4,
        max_length=4
    )
# ---------------------------------------------

    # Field validator for the lower part of the couplet - check if it matches upper part length
    @field_validator("lower_part", mode="before")
    @classmethod
    def lower_part_must_match_upper_length(cls, value, info):
        """Ensure lower part length matches upper part length."""
        upper_part = info.data.get("upper_part")
        if upper_part and len(value) != len(upper_part):
            raise ValueError(f"下联的长度必须和上联相同。当前上联：{upper_part}，下联：{value}")
        return value

# Define the prompt with background instructions and format
topic = "请写一副蛇年对联。"

# Create a parser to handle the Pydantic structure
parser = PydanticOutputParser(pydantic_object=Couplet)

# =============================================
# Set up the prompt template and add instructions
prompt = PromptTemplate(
    template="""
    根据用户提出的主题，为其编写一幅春联。\n
    主题：{topic}\n
    格式：{format_instructions}\n
    """,
    input_variables=["topic"],
    partial_variables={
        "format_instructions": parser.get_format_instructions(),
    }
)
# ---------------------------------------------

print("=== Prompt Template ===")
print(prompt.format(topic=topic))
print("=== End Prompt Template ===")

# Combine the components into a chain
chain = prompt | model | parser

# Run the chain and print the output
try:
    result = chain.invoke({"topic": topic})
    print("=== Generated Couplet ===")
    print(f"上联: {result.upper_part}")
    print(f"下联: {result.lower_part}")
    print(f"横批: {result.horizontal_part}")
    print("=== End Couplet ===")
except Exception as e:
    print(f"Error: {e}")
