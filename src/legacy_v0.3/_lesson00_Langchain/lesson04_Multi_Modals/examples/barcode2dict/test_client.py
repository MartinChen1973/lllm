# 测试客户端：发送图片到 Barcode2Dict API 服务进行测试

import requests
import json
from pathlib import Path

# API 服务地址
API_URL = "http://localhost:5010/extract"

# 测试图片路径（相对于此脚本的路径）
# 从 examples/barcode2dict/ 到 images/barcode.jpg 的路径
# examples/barcode2dict -> examples -> lesson04_Multi_Modals -> images
script_dir = Path(__file__).parent
test_image_path = script_dir.parent.parent / "images" / "barcode.jpg"


def test_extract_barcode(image_path: Path):
    """
    测试条码提取 API
    
    Args:
        image_path: 测试图片文件路径
    """
    if not image_path.exists():
        print(f"错误: 图片文件不存在: {image_path}")
        print(f"请确保图片文件存在于: {image_path.absolute()}")
        return
    
    print(f"{'='*60}")
    print(f"测试 Barcode2Dict API")
    print(f"{'='*60}")
    print(f"API 地址: {API_URL}")
    print(f"测试图片: {image_path}")
    print(f"{'='*60}\n")
    
    try:
        # 读取图片文件
        print("正在读取图片文件...")
        with open(image_path, "rb") as f:
            files = {
                "file": (image_path.name, f, "image/jpeg")
            }
            
            print("正在发送请求到 API 服务...")
            print("注意: 图片识别可能需要较长时间，请耐心等待...")
            # 发送 POST 请求，增加超时时间到 120 秒（API 调用可能需要较长时间）
            response = requests.post(API_URL, files=files, timeout=120)
            
            # 检查响应状态
            if response.status_code == 200:
                print("\n[成功] 请求成功！\n")
                
                # 解析 JSON 响应
                result = response.json()
                
                # 格式化输出
                print("提取的条码信息:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                
                # 提取并显示非空字段
                extracted_info = result.get("extracted_info", {})
                print(f"\n{'='*60}")
                print("非空字段摘要:")
                print(f"{'='*60}")
                has_data = False
                for key, value in extracted_info.items():
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
                
                print(f"{'='*60}\n")
                
            else:
                print(f"\n[失败] 请求失败！")
                print(f"状态码: {response.status_code}")
                print(f"错误信息: {response.text}\n")
                
    except requests.exceptions.ConnectionError:
        print(f"\n[错误] 连接错误: 无法连接到 API 服务 ({API_URL})")
        print("请确保服务正在运行。启动服务: python service.py\n")
    except requests.exceptions.Timeout:
        print(f"\n[错误] 请求超时: API 服务响应时间过长\n")
    except Exception as e:
        print(f"\n[错误] 发生错误: {str(e)}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n开始测试...\n")
    test_extract_barcode(test_image_path)
    print("测试完成。\n")

