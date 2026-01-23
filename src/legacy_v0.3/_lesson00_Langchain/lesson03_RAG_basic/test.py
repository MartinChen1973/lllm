# The old code is not handling the error properly. 
# It is giving an error: IndexError: list index out of range when the key is expired or wrong.
# Other api errors might also not be handled properly.

# Please test with the following code

# Old code gives error: IndexError: list index out of range
# New code gives error on expired key: ValueError: Not enough available money, Please go to  recharge
#            and error on wrong key: ValueError: Please check sk-************6GzDaH key from the  platform..

import os

# Fix OpenMP conflict: allow multiple OpenMP runtimes to coexist
# This is needed when using FAISS with other libraries that use OpenMP
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from langchain_community.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings
import os

os.environ['OPENAI_API_BASE'] = "https://api.agicto.cn/v1"
os.environ['OPENAI_API_KEY'] = "sk-8Dxxl7SxhIHU8J3M6GzDaHfzgUjC3Cm21BSR8Dxx4EuctMJ2" # Expired key, out of money
# os.environ['OPENAI_API_KEY'] = "sk-8Dxxl7SxhIHU8J3M6GzDaH" # Wrong key

vectorstore = FAISS.from_texts(
    [
        "some text",
        "some more text"
    ],
    embedding=OpenAIEmbeddings(), 
)