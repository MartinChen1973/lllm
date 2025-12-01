# 自定义智能体教程 (Custom Agents Tutorial)

---

## 目录 (Table of Contents)

1. [概述](#概述)
2. [基础智能体](#基础智能体)
3. [工具集成](#工具集成)
4. [多工具支持](#多工具支持)
5. [记忆功能](#记忆功能)
6. [自定义状态](#自定义状态)
7. [总结](#总结)

---

## 概述

### 什么是自定义智能体？

自定义智能体是基于 LangGraph 框架构建的智能对话系统，具有以下特点：

- **模块化设计**：使用节点和边构建对话流程
- **状态管理**：通过 State 类管理对话状态
- **工具集成**：支持外部工具调用
- **记忆功能**：保持对话历史
- **可扩展性**：易于添加新功能

### 核心组件

```python
# 状态定义
class State(TypedDict):
    messages: Annotated[list, add_messages]

# 图构建
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
```

---

## 基础智能体

### lesson1210_basic.py

**功能**：最简单的无记忆、无工具智能体

**核心特点**：

- 直接调用 LLM 处理用户输入
- 无状态保持
- 无外部工具

**代码结构**：

```python
def chatbot(state: State):
    return {"messages": [model.invoke(state["messages"])]}
```

**使用场景**：

- 简单的问答对话
- 文本生成任务
- 基础对话测试

**运行方式**：

```bash
python lesson1210_basic.py
```

---

## 工具集成

### lesson1220_tools_tavily.py

**功能**：集成 Tavily 搜索引擎的智能体

**核心特点**：

- 自动调用搜索引擎
- 条件性工具使用
- 智能工具选择

**关键代码**：

```python
# 工具绑定
tavily = TavilySearchResults(max_results=10)
tools = [tavily]
model_knows_tools = model.bind_tools(tools)

# 条件边
graph_builder.add_conditional_edges("chatbot", tools_condition)
```

**工具节点**：

```python
tool_node = ToolNode(tools=[tavily])
graph_builder.add_node("tools", tool_node)
```

**使用场景**：

- 实时信息查询
- 新闻搜索
- 知识问答

---

## 多工具支持

### lesson1221_tools_date_time.py

**功能**：集成多个工具的智能体

**工具列表**：

1. **Tavily 搜索**：网络信息查询
2. **日期时间工具**：时间相关查询

**代码示例**：

```python
# 多工具初始化
tavily = TavilySearchResults(max_results=10)
tools = [tavily, get_datetime_info]
model_knows_tools = model.bind_tools(tools)

# 工具节点
tool_node = ToolNode(tools=tools)
```

**工具功能**：

- **Tavily**：搜索最新信息
- **DateTime**：获取当前时间、日期计算

**使用场景**：

- 时间相关查询
- 信息搜索 + 时间处理
- 综合信息获取

---

## 记忆功能

### lesson1230_memory.py

**功能**：具有记忆功能的智能体

**核心特性**：

- 对话历史保持
- 会话隔离
- 状态持久化

**记忆实现**：

```python
# 记忆保存器
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# 线程ID管理
config = {"configurable": {"thread_id": thread_id}}
```

**会话管理**：

```python
def stream_graph_updates(user_input: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    events = graph.stream(
        {"messages": [("user", user_input)]}, config, stream_mode="values"
    )
```

**使用场景**：

- 长期对话
- 多用户会话
- 上下文保持

---

## 自定义状态

### lesson1270_customize_state.py

**功能**：对联助手智能体

**自定义状态**：

```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
    upper_part_of_the_couplet: str      # 上联
    lower_part_of_the_couplet: str      # 下联
    horizontal_part_of_the_couplet: str # 横批
```

**系统提示词**：

```python
SYSTEM_PROMPT = """你是一个对联助手，专门帮助用户创作对联。
1. 你的主要任务是根据用户提供的主题，帮他们写出一副对联
2. 每次与用户对话时，你都要以"Hi，我可以帮你写对联，请提供主题。"开头
3. 每次回复用户时，都要展示当前生成的对联内容
"""
```

**内容提取**：

```python
def extract_couplet_parts(content: str) -> tuple[str, str, str]:
    """从消息内容中提取对联部分"""
    upper_match = re.search(r"上联[:：](.*)", content)
    lower_match = re.search(r"下联[:：](.*)", content)
    horizontal_match = re.search(r"横批[:：](.*)", content)
    # ...
```

**输出格式**：

```
上联：{upper_part_of_the_couplet}
下联：{lower_part_of_the_couplet}
横批：{horizontal_part_of_the_couplet}
```

---

## 智能体架构对比

| 特性       | 基础智能体 | 工具智能体 | 多工具智能体 | 记忆智能体 | 自定义状态智能体 |
| ---------- | ---------- | ---------- | ------------ | ---------- | ---------------- |
| 工具支持   | ❌         | ✅         | ✅           | ✅         | ✅               |
| 记忆功能   | ❌         | ❌         | ❌           | ✅         | ✅               |
| 自定义状态 | ❌         | ❌         | ❌           | ❌         | ✅               |
| 条件路由   | ❌         | ✅         | ✅           | ✅         | ✅               |
| 会话管理   | ❌         | ❌         | ❌           | ✅         | ✅               |

---

## 开发最佳实践

### 1. 状态设计

```python
# 好的状态设计
class State(TypedDict):
    messages: Annotated[list, add_messages]
    custom_field: str  # 根据需要添加自定义字段
```

### 2. 工具集成

```python
# 工具绑定
tools = [tool1, tool2, tool3]
model_knows_tools = model.bind_tools(tools)

# 工具节点
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)
```

### 3. 条件路由

```python
# 条件边设置
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
```

### 4. 记忆管理

```python
# 记忆配置
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# 线程配置
config = {"configurable": {"thread_id": thread_id}}
```

---

## 常见问题与解决方案

### Q1: 如何添加新的工具？

```python
# 1. 定义工具函数
@tool
def my_custom_tool(input: str) -> str:
    """自定义工具描述"""
    return "处理结果"

# 2. 添加到工具列表
tools = [existing_tools, my_custom_tool]

# 3. 重新绑定模型
model_knows_tools = model.bind_tools(tools)
```

### Q2: 如何自定义状态字段？

```python
# 1. 扩展状态类
class State(TypedDict):
    messages: Annotated[list, add_messages]
    my_field: str

# 2. 在节点中更新状态
def my_node(state: State):
    return {
        "messages": [new_message],
        "my_field": "新值"
    }
```

### Q3: 如何处理错误？

```python
# 错误处理示例
def safe_chatbot(state: State):
    try:
        response = model.invoke(state["messages"])
        return {"messages": [response]}
    except Exception as e:
        error_message = f"处理出错: {str(e)}"
        return {"messages": [HumanMessage(content=error_message)]}
```

---

## 总结

### 学习路径

1. **基础智能体** → 理解基本架构
2. **工具集成** → 学习工具使用
3. **多工具支持** → 掌握工具组合
4. **记忆功能** → 实现状态保持
5. **自定义状态** → 扩展功能

### 关键概念

- **StateGraph**：状态图框架
- **节点 (Node)**：处理单元
- **边 (Edge)**：流程控制
- **状态 (State)**：数据管理
- **工具 (Tools)**：外部功能
- **记忆 (Memory)**：历史保持

### 下一步

- 探索更多工具集成
- 实现复杂对话流程
- 优化性能和响应速度
- 添加用户界面
- 部署到生产环境

---

## 参考资料

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [LangChain 工具文档](https://python.langchain.com/docs/modules/tools/)
- [Tavily 搜索 API](https://tavily.com/)
- [Python 正则表达式](https://docs.python.org/3/library/re.html)

---

_教程结束 - 感谢学习！_
