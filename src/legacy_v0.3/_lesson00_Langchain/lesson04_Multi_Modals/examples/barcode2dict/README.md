# Barcode2Dict API 服务

基于 GPT-4o 模型的条码标签信息提取 API 服务。接收图片文件，返回识别后的结构化 JSON 数据。

## 功能特性

- 从图片中提取条码标签信息
- 支持多种图片格式：JPG, JPEG, PNG, GIF, WEBP
- RESTful API 接口
- 完整的错误处理
- 自动生成 API 文档

## 文件结构

```
barcode2dict/
├── extractor.py      # 核心提取逻辑模块
├── service.py        # FastAPI 服务主文件
├── test_client.py    # 测试客户端脚本
└── README.md         # 本文件
```

## 依赖项

所有依赖项已在项目根目录的 `requirements.txt` 中定义：

- `fastapi==0.115.12`
- `uvicorn==0.34.1`
- `langchain_openai>=1.0.3`
- `python-dotenv==1.1.0`
- `Requests==2.32.3`

确保已安装所有依赖：

```bash
pip install -r requirements.txt
```

## 环境配置

确保已配置 `.env` 文件，包含以下环境变量：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1  # 或使用其他兼容的 API 端点
```

## 启动服务

### 方法 1: 直接运行 Python 脚本

```bash
cd src/legacy_v0.3/_lesson00_Langchain/lesson04_Multi_Modals/examples/barcode2dict
python service.py
```

### 方法 2: 使用 uvicorn 命令

```bash
cd src/legacy_v0.3/_lesson00_Langchain/lesson04_Multi_Modals/examples/barcode2dict
uvicorn service:app --host 0.0.0.0 --port 5010
```

服务启动后，将运行在 `http://localhost:5010`

## API 端点

### 根路径

- **URL**: `GET /`
- **说明**: 返回 API 基本信息

### 提取条码信息

- **URL**: `POST /extract`
- **说明**: 上传图片文件并提取条码信息
- **请求格式**: `multipart/form-data`
- **参数**:
  - `file` (file, required): 图片文件（支持 JPG, JPEG, PNG, GIF, WEBP）

**请求示例** (使用 curl):

```bash
curl -X POST "http://localhost:5010/extract" \
  -F "file=@path/to/your/image.jpg"
```

**响应格式**:

```json
{
  "extracted_info": {
    "customer_part_number": "941733-GK0E",
    "manufacturer_part_number": "941733",
    "revision": "G",
    "trace_code": "20250710001",
    "lot_code": null,
    "batch_number": null,
    "date_code": "20250710",
    "expiry_date": null,
    "quantity": "28",
    "purchase_order_number": null,
    "carton_number": null,
    "supplier_code": "246416",
    "country_of_origin": "EON",
    "manufacturer_part_number_alt": null,
    "additional_info": {}
  }
}
```

### API 文档

- **Swagger UI**: `http://localhost:5010/docs`
- **ReDoc**: `http://localhost:5010/redoc`

## 测试

### 使用测试客户端

运行测试脚本，自动从上一级目录的 `images/barcode.jpg` 发送请求：

```bash
cd src/legacy_v0.3/_lesson00_Langchain/lesson04_Multi_Modals/examples/barcode2dict
python test_client.py
```

### 使用 curl

```bash
curl -X POST "http://localhost:5010/extract" \
  -F "file=@../images/barcode.jpg"
```

### 使用 Python requests

```python
import requests

url = "http://localhost:5010/extract"
with open("path/to/image.jpg", "rb") as f:
    files = {"file": ("image.jpg", f, "image/jpeg")}
    response = requests.post(url, files=files)
    print(response.json())
```

## 提取的字段说明

API 返回的 JSON 包含以下字段（可能为 `null`）：

| 字段名 | 中文名称 | 说明 |
|--------|---------|------|
| `customer_part_number` | 客户零件号 | 客户指定的零件编号 |
| `manufacturer_part_number` | 制造商零件号 | 制造商零件编号 |
| `revision` | 版本/修订号 | 零件版本或修订号 |
| `trace_code` | 追踪码 | 追踪代码 |
| `lot_code` | 批次号 | 批次代码 |
| `batch_number` | 批次编号 | 批次编号 |
| `date_code` | 日期代码 | 日期代码 |
| `expiry_date` | 到期日期 | 到期日期 |
| `quantity` | 数量 | 数量 |
| `purchase_order_number` | 采购订单号 | 采购订单号 |
| `carton_number` | 箱号 | 箱号 |
| `supplier_code` | 供应商代码 | 供应商代码 |
| `country_of_origin` | 原产国 | 原产国代码 |
| `manufacturer_part_number_alt` | 制造商零件号(备用) | 备用制造商零件号 |
| `additional_info` | 其他信息 | 其他额外信息或错误信息 |

## 错误处理

服务会返回适当的 HTTP 状态码：

- `200`: 成功
- `400`: 请求错误（如不支持的文件类型）
- `500`: 服务器错误（处理图片时发生错误）

错误响应格式：

```json
{
  "detail": "错误描述信息"
}
```

## 注意事项

1. 确保已正确配置 OpenAI API 密钥
2. 服务使用 GPT-4o 模型，需要相应的 API 权限
3. 处理大图片时可能需要较长响应时间，建议设置适当的超时时间
4. 测试客户端默认超时时间为 60 秒

## 许可证

与项目主许可证保持一致。


