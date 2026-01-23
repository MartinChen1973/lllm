# 条码标签信息提取模块
# 从图片中提取条码标签信息到字典

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv, find_dotenv
import base64
import json
import re
from pathlib import Path
from typing import Dict, Any, Union

# Load environment variables
load_dotenv(find_dotenv())

# Initialize the ChatOpenAI model with structured output
model = ChatOpenAI(model="gpt-5", temperature=0)

# 定义统一的字典结构模板
EXTRACTION_PROMPT = """请仔细分析图片中的条码标签，提取所有可见的信息字段，并按照以下JSON格式返回。

注意：图片中可能包含以下字段，请识别所有出现的字段：
- 客户零件号: 可能标记为 "(P)Celestica P/N", "(P)CELESTICA P/N", "(P)PN", "CUSTOMER P/N" 等
- 制造商零件号: 可能标记为 "(1P)Manufacturer P/N", "(1P) MANUFACTURER P/N", "KINGPOWER P/N", "(C)MPN", "MFG PR" 等
- 版本/修订号: 可能标记为 "Rev", "Cust Rev", "IJ Rev" 等
- 追踪码: 可能标记为 "(1T)Trace Code", "(1T)Trace code" 等
- 批次号: 可能标记为 "(2T)B/N", "LOT CODE", "Batch Number" 等
- 日期代码: 可能标记为 "(10D)Date Code", "(10D)Date code", "DATE CODE" 等
- 到期日期: 可能标记为 "Expiry Date" 等
- 数量: 可能标记为 "(Q)Quantity", "(Q)QUANTITY", "QTY", "(Q)QTY" 等
- 采购订单号: 可能标记为 "P/O NUMBER", "PO#", "P/O" 等
- 箱号: 可能标记为 "(30T)CTN" 等
- 供应商代码: 可能标记为 "(V)Supplier Code", "(V)SUPPLIER CODE", "(V)SO" 等
- 原产国: 可能标记为 "(4L)COO", "(4L)coo", "COUNTRY OF ORIGIN", "(4L) COO" 等

请返回JSON格式，只包含图片中实际出现的字段。如果某个字段不存在，请将其设置为null。
所有文本值请保持原始格式，不要修改。

返回格式示例：
{{
    "customer_part_number": "值或null",
    "manufacturer_part_number": "值或null",
    "revision": "值或null",
    "trace_code": "值或null",
    "lot_code": "值或null",
    "batch_number": "值或null",
    "date_code": "值或null",
    "expiry_date": "值或null",
    "quantity": "值或null",
    "purchase_order_number": "值或null",
    "carton_number": "值或null",
    "supplier_code": "值或null",
    "country_of_origin": "值或null",
    "manufacturer_part_number_alt": "值或null",
    "additional_info": {{}}
}}

请直接返回JSON，不要添加任何额外的说明文字。"""


def extract_barcode_info(image_source: Union[str, bytes], filename: str = None) -> Dict[str, Any]:
    """
    从图片中提取条码标签信息并返回统一的字典结构
    
    Args:
        image_source: 图片文件路径（str）或图片文件内容（bytes）
        filename: 当 image_source 为 bytes 时，提供文件名以确定 MIME 类型
        
    Returns:
        包含提取信息的字典，符合统一的字段结构
    """
    # Handle both file path and file content (bytes)
    if isinstance(image_source, str):
        # Read from file path
        with open(image_source, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")
        
        # Determine image MIME type based on file extension
        image_path_obj = Path(image_source)
        suffix = image_path_obj.suffix.lower()
        filename = filename or image_path_obj.name
    elif isinstance(image_source, bytes):
        # Read from bytes
        image_data = base64.b64encode(image_source).decode("utf-8")
        # Determine MIME type from filename
        if filename:
            suffix = Path(filename).suffix.lower()
        else:
            suffix = ".jpg"  # Default to jpeg
    else:
        raise ValueError("image_source must be either a file path (str) or file content (bytes)")
    
    mime_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }
    mime_type = mime_type_map.get(suffix, "image/jpeg")  # Default to jpeg
    
    # Create a HumanMessage to request structured extraction
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": EXTRACTION_PROMPT
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
            },
        ],
    )
    
    # Invoke the model to get the response
    response = model.invoke([message])
    
    # Parse JSON from response
    try:
        # Try to extract JSON from the response
        response_text = response.content.strip()
        
        # Remove markdown code blocks if present
        if "```" in response_text:
            # Find the JSON block between ``` or ```json and ```
            # Match ```json...``` or ```...```
            json_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1).strip()
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(0).strip()
        
        # Parse JSON
        extracted_dict = json.loads(response_text)
        
        # Ensure all fields are present with None as default
        default_structure = {
            "customer_part_number": None,
            "manufacturer_part_number": None,
            "revision": None,
            "trace_code": None,
            "lot_code": None,
            "batch_number": None,
            "date_code": None,
            "expiry_date": None,
            "quantity": None,
            "purchase_order_number": None,
            "carton_number": None,
            "supplier_code": None,
            "country_of_origin": None,
            "manufacturer_part_number_alt": None,
            "additional_info": {}
        }
        
        # Merge extracted data with default structure
        result = {**default_structure, **extracted_dict}
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print(f"响应内容: {response.content}")
        # Return empty structure on error
        return {
            "customer_part_number": None,
            "manufacturer_part_number": None,
            "revision": None,
            "trace_code": None,
            "lot_code": None,
            "batch_number": None,
            "date_code": None,
            "expiry_date": None,
            "quantity": None,
            "purchase_order_number": None,
            "carton_number": None,
            "supplier_code": None,
            "country_of_origin": None,
            "manufacturer_part_number_alt": None,
            "additional_info": {"error": str(e), "raw_response": response.content}
        }

