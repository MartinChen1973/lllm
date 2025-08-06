# 智能体 (Agents) 教程

## 从传统 LLM 应用到智能体系统

---

## 目录

1. **什么是智能体？**
2. **智能体 vs 传统 LLM 应用**
3. **LangGraph 预构建智能体**
4. **核心技术组件**
5. **实际应用示例**
6. **智能体的优势**
7. **使用场景**
8. **最佳实践**
9. **总结与展望**

---

## 什么是智能体？

### 🤖 智能体的定义

智能体（Agent）是一种能够**自主执行任务**的 AI 系统，它结合了：

- **大语言模型的推理能力**
- **外部工具的执行能力**

---

## 智能体的核心特点

### 🔄 关键特性

- **自主决策**: 能够独立决定使用哪些工具
- **动态执行**: 根据任务需求调整策略
- **上下文感知**: 理解对话历史和状态
- **工具集成**: 无缝调用外部功能

---

## 智能体 vs 传统 LLM 应用

| 特性         | 传统 LLM 应用      | 智能体                 |
| ------------ | ------------------ | ---------------------- |
| **执行方式** | 线性流程，固定步骤 | 动态决策，自主选择工具 |
| **工具使用** | 预定义，被动调用   | 主动选择，按需调用     |

---

## 智能体 vs 传统 LLM 应用

| 特性         | 传统 LLM 应用    | 智能体               |
| ------------ | ---------------- | -------------------- |
| **状态管理** | 简单，无记忆     | 复杂，支持长期记忆   |
| **交互模式** | 单次问答         | 多轮对话，上下文感知 |
| **决策能力** | 有限，基于提示词 | 强大，基于推理链     |

---

## LangGraph 预构建智能体

### 🎯 ReAct 智能体

最常用的智能体类型，基于"**推理-行动**"循环：

1. **推理 (Reasoning)**: 分析用户输入，确定需要采取的行动
2. **行动 (Action)**: 执行选定的工具或操作

---

## ReAct 智能体循环

### 🔄 完整流程

3. **观察 (Observation)**: 观察并分析工具或操作的输出结果
4. **重复**: 基于观察结果继续推理，直到得出最终答案

### 循环流程

```
用户输入 → 推理 → 行动 → 观察 → 推理 → ... → 最终答案
```

---

## 核心技术组件概览

### 🧩 五个核心组件

1. **🧠 模型 (Model)** - 智能体的"大脑"
2. **🛠️ 工具 (Tools)** - 智能体的"手"
3. **💬 提示词 (Prompt)** - 智能体的"性格"
4. **📊 结构化输出** - 格式化数据
5. **🧠 记忆 (Memory)** - 长期记忆

---

## 1. 模型 (Model) - 智能体的"大脑"

### 🧠 负责理解和推理

```python
# 使用默认模型
agent = create_react_agent(
    model="openai:gpt-4o-mini",
    tools=[get_weather]
)
```

---

## 1. 模型 (Model) - 自定义配置

### 🔧 高级配置

```python
# 使用自定义模型
model = init_chat_model("openai:gpt-4o-mini", temperature=0.0)
agent = create_react_agent(
    model=model,
    tools=[get_weather]
)
```

---

## 2. 工具 (Tools) - 智能体的"手"

### 🛠️ 用于执行具体任务

```python
def get_weather(city: str) -> str:
    """获取指定城市的天气信息"""
    return f"{city}的天气总是晴朗的！"
```

---

## 2. 工具 (Tools) - 更多示例

### 🔧 工具函数示例

```python
def get_chinese_name(city: str) -> str:
    """将城市名翻译为中文"""
    mapping = {
        "sf": "旧金山",
        "San Francisco": "旧金山",
        "nyc": "纽约",
        "New York City": "纽约",
    }
    return mapping.get(city.lower(), "未知")
```

---

## 3. 提示词 (Prompt) - 基础用法

### 💬 智能体的"性格"

```python
# 简单提示词
agent = create_react_agent(
    model=model,
    tools=[get_weather],
    prompt="你是一个有用的助手"
)
```

---

## 3. 提示词 (Prompt) - 自定义行为

### 🎭 行为定制

```python
# 自定义提示词
agent = create_react_agent(
    model=model,
    tools=[get_weather],
    prompt="不要回答关于天气的问题！"
)
```

---

## 3. 提示词 (Prompt) - 动态提示词

### 🔄 基于用户信息

```python
def prompt(state: AgentState, config: RunnableConfig) -> list[AnyMessage]:
    user_name = config["configurable"].get("user_name")
    system_msg = f"你是一个有用的助手。总是热情地称呼用户为 {user_name}。"
    return [{"role": "system", "content": system_msg}] + state["messages"]
```

---

## 4. 结构化输出 (Structured Output)

### 📊 确保格式化数据

```python
class WeatherResponse(BaseModel):
    """天气信息响应"""
    city: str
    conditions: str

agent = create_react_agent(
    model="openai:gpt-4o-mini",
    tools=[get_weather],
    response_format=WeatherResponse
)
```

---

## 5. 记忆 (Memory) - 基础设置

### 🧠 智能体的"长期记忆"

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()

agent = create_react_agent(
    model="openai:gpt-4o-mini",
    tools=[get_weather],
    prompt="你是一个有用的助手",
    checkpointer=checkpointer
)
```

---

## 5. 记忆 (Memory) - 使用记忆

### 💾 管理对话状态

```python
# 使用thread_id来管理对话记忆
config = {"configurable": {"thread_id": "1"}}
response = agent.invoke(
    {"messages": [{"role": "user", "content": "旧金山的天气怎么样？"}]},
    config
)
```

---

## 实际应用示例

### 🚀 基础智能体

最简单的智能体，只有基本功能：

```python
from langgraph.prebuilt import create_react_agent

def get_weather(city: str) -> str:
    return f"{city}的天气总是晴朗的！"

agent = create_react_agent(
    model="openai:gpt-4o-mini",
    tools=[get_weather],
    prompt="你是一个有用的助手"
)
```

---

## 交互式智能体 - 核心函数

### 💬 支持多轮对话

```python
def stream_agent_updates(user_input: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}

    events = agent.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="values"
    )

    for event in events:
        message = event["messages"][-1]
        message.pretty_print()
```

---

## 交互式智能体 - 聊天循环

### 🔄 交互式聊天循环

```python
# 交互式聊天循环
while True:
    thread_id = input("请输入会话ID: ")
    user_input = input("用户: ")
    if user_input.lower() == "quit":
        break
    stream_agent_updates(user_input, thread_id)
```

---

## 智能体的优势

### 🌟 核心优势

1. **自主性**: 能够自主决定使用哪些工具
2. **适应性**: 根据任务需求动态调整策略
3. **可扩展性**: 易于添加新的工具和功能

---

## 智能体的优势

### 🌟 更多优势

4. **记忆能力**: 支持长期对话和上下文理解
5. **结构化输出**: 确保返回数据的格式一致性

---

## 使用场景

### 🎯 实际应用领域

- **🤖 客服机器人**: 处理用户查询，调用相关 API
- **📊 数据分析助手**: 自动分析数据并生成报告
- **💻 代码助手**: 理解需求并生成代码

---

## 使用场景

### 🎯 更多应用领域

- **🔍 研究助手**: 搜索信息并整理分析
- **⚙️ 任务自动化**: 执行复杂的多步骤任务

---

## 最佳实践

### 📋 开发指南

1. **工具设计**: 工具函数应该有清晰的文档字符串
2. **错误处理**: 在工具中实现适当的错误处理
3. **提示词优化**: 根据具体用例定制提示词

---

## 最佳实践

### 📋 更多指南

4. **记忆管理**: 合理使用 thread_id 管理对话状态
5. **性能监控**: 监控智能体的执行效率和准确性

---

## 总结

### 🎉 智能体的意义

智能体代表了 **LLM 应用的新范式**，从被动的问答系统转变为主动的任务执行者。

### 🚀 通过 LangGraph

我们可以快速构建功能强大的 AI 应用，而无需深入了解底层的复杂实现细节。

---

## 展望未来

### 📚 接下来的学习内容

- **创建自定义智能体**
- **实现更复杂的工具集成**
- **构建多智能体系统**
- **优化智能体的性能和用户体验**

---

## 学习目标

### 🎯 掌握核心技能

掌握智能体开发的核心技能，能够构建实用的 AI 应用系统。

---

## 谢谢！

### 🙏 课程结束

**问题与讨论**

有任何问题，请随时提问！
