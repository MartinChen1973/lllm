# 1. 演示用gpt4o模型从图片中提取条码标签信息到字典

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv, find_dotenv
import base64
import json
import re
from pathlib import Path
from typing import Dict, Any

# Load environment variables
load_dotenv(find_dotenv(), override=True)


# Initialize the ChatOpenAI model with structured output
model = ChatOpenAI(model="gpt-4o", temperature=0)

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

def extract_barcode_info(image_path: str) -> Dict[str, Any]:
    """
    从图片中提取条码标签信息并返回统一的字典结构
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        包含提取信息的字典，符合统一的字段结构
    """
    # Read and encode the local image file in base64
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")
    
    # Determine image MIME type based on file extension
    image_path_obj = Path(image_path)
    suffix = image_path_obj.suffix.lower()
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

def print_extracted_info(image_path: str, info_dict: Dict[str, Any]):
    """
    打印提取的信息字典
    
    Args:
        image_path: 图片路径
        info_dict: 提取的信息字典
    """
    print(f"\n{'='*60}")
    print(f"图片路径: {image_path}")
    print(f"{'='*60}")
    
    # 打印所有非空字段
    print("\n提取的信息:")
    has_data = False
    for key, value in info_dict.items():
        if key == "additional_info":
            if value:
                print(f"  其他信息: {value}")
                has_data = True
        elif value is not None:
            # 翻译字段名为中文显示
            field_names = {
                "customer_part_number": "客户零件号",
                "manufacturer_part_number": "制造商零件号",
                "revision": "版本/修订号",
                "trace_code": "追踪码",
                "lot_code": "批次号",
                "batch_number": "批次编号",
                "date_code": "日期代码",
                "expiry_date": "到期日期",
                "quantity": "数量",
                "purchase_order_number": "采购订单号",
                "carton_number": "箱号",
                "supplier_code": "供应商代码",
                "country_of_origin": "原产国",
                "manufacturer_part_number_alt": "制造商零件号(备用)"
            }
            field_name = field_names.get(key, key)
            print(f"  {field_name}: {value}")
            has_data = True
    
    if not has_data:
        print("  未提取到任何信息")
    
    print("\n完整字典结构:")
    print(json.dumps(info_dict, ensure_ascii=False, indent=2))
    print(f"{'='*60}\n")


# Get the directory where this script is located
script_dir = Path(__file__).parent

# List of image paths to extract (relative to script directory)
# 请将您的6张图片放在images目录下，并在此处列出文件名
image_paths = [
    script_dir / "images" / "barcode.jpg",
    # 添加更多图片路径，例如：
    # script_dir / "images" / "barcode2.jpg",
    # script_dir / "images" / "barcode3.jpg",
    # script_dir / "images" / "barcode4.jpg",
    # script_dir / "images" / "barcode5.jpg",
    # script_dir / "images" / "barcode6.jpg",
]

# Extract information from each image
all_results = []
for image_path in image_paths:
    if not image_path.exists():
        print(f"警告: 图片文件不存在: {image_path}")
        continue
        
    try:
        print(f"\n正在处理: {image_path.name}...")
        extracted_info = extract_barcode_info(str(image_path))
        all_results.append({
            "image_path": str(image_path),
            "extracted_info": extracted_info
        })
        print_extracted_info(image_path.name, extracted_info)
    except Exception as e:
        print(f"处理图片时发生错误 {image_path}: {e}")
        import traceback
        traceback.print_exc()

# 打印汇总信息
if all_results:
    print(f"\n{'#'*60}")
    print(f"处理完成，共处理 {len(all_results)} 张图片")
    print(f"{'#'*60}")
    
    # 保存所有结果到JSON文件
    output_file = script_dir / "extracted_barcode_info.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n所有结果已保存到: {output_file}")
