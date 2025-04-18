---
marp: true
---

# OpenWebUI 开箱即用的 Agent+RAG 框架

---

## OpenWebUI 安装

**什么是 OpenWebUI？**

1. OpenWebUI 是一个可以私域部署的应用，其功能非常接近 ChatGpt、通义千问、Deepseek。
2. 可以通过上传文档作为 RAG 的输入。
3. 可以设置独立的工作空间和相应的用户访问。
4. 有大量可以直接使用的工具（开源社区持续增加中）。

---

**安装**

1. 在 windows 搜索框输入 cmd
2. **重要**：在弹出的窗口右侧，选择“**以管理员运行**”

- 否则会遇到写入权限错误。

4. 运行安装指令：

   ```
   pip install open-webui
   ```

5. 运行启动服务指令：

   ```
   open-webui serve
   ```

---

## 首次使用

1. 访问地址 http://localhost:8080

- 注意：首次使用可能需要 1~2 分钟才能启动，且伴随大量错误（如未能加载秘钥）。请耐心等待

2. 创建管理员账号

- 首次使用请创建管理员帐号（建议使用用户名 Admin 或 Administrator）
- 此账号拥有创建工作空间、审核用户的能力

---

## 添加知识

**知识库概述**

1. 知识库是 OpenWebUI 的 RAG（Retriever-Augmented Generation）功能的一部分，用于向模型提供额外的背景信息，以增强模型的回答能力。
2. 可以通过上传文档（如 PDF、Word 文件等）或连接外部知识库来扩展知识。

**添加步骤**

1. 进入目标工作空间的“**知识管理**”页面。
2. 点击“**上传知识**”按钮，选择需要上传的文件格式（支持多种格式，如 TXT、PDF、Word 等）。
3. 在文件上传后，可以选择是否对文件内容进行索引，以便于 RAG 模型进行高效检索。
4. 上传完成后，文件内容将被自动处理，并可以与模型进行交互时引用。

---## 添加工具（以 Tavily 为例）

**工具概述**

1. OpenWebUI 支持集成各种工具（如 Tavily、ElasticSearch、知识图谱等），以提高模型的能力和实用性。
2. Tavily 是一款强大的文本分析工具，可以用于文本生成、情感分析等任务。

**添加 Tavily 工具步骤**

1. 点击**Workspace / tools / Discover a tool**
2. 在弹出的 web 窗口中
   1. 选择类型**tool**
   2. 搜**tavily**，完成导入过程
3. 回到 OpenWebUI，点击工具后的配置图标
   1. 设置 Tavily Api Key
4. 在目标工作空间的“**工具管理**”页面，点击“**添加工具**”。
5. 在弹出的工具选择框中选择“**Tavily**”。
6. 配置 Tavily 工具所需的 API 密钥和相关参数：
   - **API 密钥**：获取 Tavily 提供的 API 密钥。
   - **请求超时设置**：根据需要设置 API 请求的超时时间。
7. 点击“**保存**”按钮，完成工具的添加。

---

## 添加模型

**模型概述**

1. OpenWebUI 中的 Model 是一个包含 RAG 功能的 Agent，而非原始模型（如果 gpt-4o）。
2. 支持多种 AI 模型（如 GPT 系列、BERT、T5 等），并可以灵活配置其输入输出。

**步骤**

1. 添加一个基础模型
   1. 点击**Workspace / Models / Discover a model**
   2. 在弹出的 web 窗口中
      1. 选择类型**model**
      2. 搜搜
1. 基于基础模型创建模型
   1. 点击**Workspace / Models / +**
1. 点击**Workspace / Models / +**
1.
1. 点击“**模型管理**”选项卡，进入模型配置页面。
1. 点击“**添加模型**”按钮，填写模型信息：
   - **模型名称**：指定模型的名称。
   - **模型类型**：选择模型的类型，例如 OpenAI GPT-3 或自定义模型。
   - **API 密钥**：根据需要，填写模型的 API 密钥（如使用 OpenAI GPT 模型，需填写 OpenAI 提供的密钥）。
1. 配置其他参数，如最大请求次数、超时时间等。
1. 点击“**保存**”按钮，完成模型添加。

---

## 为 Workspace 指定可访问的用户

**用户访问控制**

1. OpenWebUI 支持基于角色的访问控制，可以为不同的用户分配不同的权限。
2. 每个工作空间都可以指定哪些用户可以访问，并为其设置相应的权限（如查看、编辑、管理员权限等）。

**步骤**

1. 在工作空间管理页面，选择目标工作空间。
2. 点击“**用户管理**”选项卡。
3. 点击“**添加用户**”按钮，输入用户的基本信息：
   - **用户名**：指定用户的名称。
   - **角色**：选择该用户在该工作空间中的角色（如管理员、普通用户等）。
4. 配置用户的权限(查看/编辑/管理员)
