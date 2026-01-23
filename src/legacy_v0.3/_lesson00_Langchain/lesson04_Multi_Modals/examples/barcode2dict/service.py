# FastAPI 服务：条码标签信息提取 API

from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import Dict, Any
import uvicorn
from pathlib import Path

from extractor import extract_barcode_info

app = FastAPI(
    title="Barcode2Dict API",
    description="从图片中提取条码标签信息到字典的 API 服务",
    version="1.0.0"
)


@app.get("/")
async def root():
    """根路径，返回 API 信息"""
    return {
        "service": "Barcode2Dict API",
        "version": "1.0.0",
        "description": "从图片中提取条码标签信息的 API 服务",
        "endpoints": {
            "/extract": "POST - 上传图片文件并提取条码信息",
            "/docs": "GET - API 文档 (Swagger UI)",
            "/redoc": "GET - API 文档 (ReDoc)"
        }
    }


@app.post("/extract")
async def extract_barcode(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    提取条码标签信息
    
    接收图片文件上传，返回识别后的 JSON 结果
    
    Args:
        file: 上传的图片文件
        
    Returns:
        包含提取信息的 JSON 响应：
        {
            "extracted_info": {
                "customer_part_number": "...",
                "manufacturer_part_number": "...",
                ...
            }
        }
    """
    # 验证文件类型
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    file_extension = Path(file.filename).suffix.lower() if file.filename else ""
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。支持的格式: {', '.join(allowed_extensions)}"
        )
    
    try:
        # 读取上传的文件内容
        file_content = await file.read()
        
        # 调用提取函数
        extracted_info = extract_barcode_info(
            image_source=file_content,
            filename=file.filename
        )
        
        # 返回结果
        return {
            "extracted_info": extracted_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理图片时发生错误: {str(e)}"
        )


if __name__ == "__main__":
    # 运行服务，端口 5010
    uvicorn.run(app, host="0.0.0.0", port=5010)

