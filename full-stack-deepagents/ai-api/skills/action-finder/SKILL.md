---
name: action-finder
description: >-
  先选定 CRUD 模板（CIDED/CIDRA/CID），再映射为 camelCase 动作名，并推断领域相关的额外动作（例如 payOrder）。
  适用于实体动作与 API 命名等场景。
license: MIT
metadata:
  version: "1.1.0"
  author: agno-docs
  tags: ["crud", "entity", "actions", "api"]
---

# Action Finder 技能

使用本技能时，须**首先**为给定实体选定模板（例如 CIDED），再将该模板映射为 camelCase 动作名，并在适当时**进一步推断**与领域相关的**额外**动作。

## 适用情形

- 用户询问与某一实体相关的动作。
- 用户需要生成 API 端点或操作名称。
- 用户希望梳理某一实体可用的操作。
- 用户正在设计 REST API 或服务接口。

## 流程

**关键要求**：必须生成 **camelCase** 动作名（例如 `createUser`、`listUsers`、`payOrder`），**不得**将模板槽位标签（如 `Create`、`Index`）直接作为输出；否则会导致记录失败。

### 用户可见的模板说明（必填）

用户**必须**知晓所采用的模式。在列出任何动作**之前**，先按下列形式输出一小段说明（若用户使用中文书写，可相应使用中文叙述，但**模板代号请仍使用英文**）：

```text
**Template:** CIDED (Create, Index, Details, Edit, Delete)
**Rationale:** ……一行理由……
```

- `Template:` 之后的代号**必须**为 **`CIDED`**、**`CIDRA`** 或 **`CID`** 之一——**不得**使用 **`CRUD`** 一词。上述三种代号定义于 `crud-templates.md`。
- 括号内请**展开缩写**，槽位名称须与该文件一致，以便用户看到完整模板结构。
- 调用 **`action_finder_log(..., template_selected=...)`** 时须使用相同代号：`CIDED`、`CIDRA` 或 `CID`，**不得**填写 `CRUD`。

### 禁止的偷懒写法（将导致技能失败）

- 在已选择 **CIDED** 时，**不得**将所有操作笼统写成「创建 / 读取 / 更新 / 删除」式动词（`read*`、`update*`）。对 CIDED 而言，「读」应拆分为 **list**（Index，集合）与 **get**（Details，单条），「更新」对应 **edit**（Edit）：应使用 `list{Entity}s`、`get{Entity}`、`edit{Entity}`——详见下表。
- **不得**仅用 **创建 / 读取 / 更新 / 删除** 等标题呈现结果，而不同时给出 **Template: CIDED**（或正确代号）及**五槽位**对应关系。若使用中文标题，每一行须对应到模板槽位（例如 列表/索引 → Index → `list…`，详情 → Details → `get…`，编辑 → Edit → `edit…`）。

### 步骤顺序（不得跳过）

1. **加载模板** — 使用 `read_file`，路径为 `/skills/action-finder/references/crud-templates.md`，在命名动作**之前**确认 CIDED、CIDRA、CID 的含义。
2. **选定一种模板** — 依据实体与场景选择最契合的一种。须说明**所选**模板（CIDED、CIDRA 或 CID）及**简要理由**（一句话即可）。模板是**起点模式**，并非唯一允许使用的动词集合。
3. **映射模板槽位** — 对该模板中的每一个槽位，按下文映射表生成对应的 camelCase 动作名。
4. **推断额外动作** — 完成模板映射后，再补充领域合理、但模板正文未列出的操作。当实体明显需要更多能力时，**不得**停留在机械的 create/read/update/delete 列举（例如 **Order**：`payOrder`、`cancelOrder`、`shipOrder`；**Subscription**：`renewSubscription`、`pauseSubscription`）。此类动作凭产品与领域常识**推断**，而非从模板文件中逐字抄写。
5. **去重与排序** — 每种操作仅保留一个规范名称；先按模板槽位顺序列出由模板导出的动作，再列出推断出的额外动作（可按逻辑分组或字母序）。

### 模板选择（参考）

- **CIDED**：具有完整生命周期的标准实体（Create、Index、Details、Edit、Delete）。
- **CIDRA**：带审批流程的实体（Create、Index、Details、Reject、Approve）。
- **CID**：仅追加或大体只读的实体，例如日志、审计轨迹（Create、Index、Details）。

### 将模板槽位映射为 camelCase

**关键要求**：将模板中的**角色**转换为 camelCase 函数名：

- "Create" → `create{Entity}`（例如 `createUser`）。
- "Index" → `list{Entity}s`（复数，例如 `listUsers`）。
- "Details" → `get{Entity}`（例如 `getUser`）。
- "Edit" → `edit{Entity}`（例如 `editUser`）。
- "Delete" → `delete{Entity}`（例如 `deleteUser`）。
- "Reject" → `reject{Entity}`（例如 `rejectRequest`）。
- "Approve" → `approve{Entity}`（例如 `approveRequest`）。

**不得**将 "Create"、"Index"、"Details" 等标签本身作为动作列表输出。

### 仅适用于 CIDED — 五槽位核对清单（必填）

选择 **CIDED** 即表示模板槽位为 **Create、Index、Details、Edit、Delete**——而非笼统的「通用 CRUD」。在写入任何**推断**动作**之前**，须为每一槽位各输出**恰好一个** camelCase 名称（共**五个**）。

| 模板槽位 | 英文动词         | camelCase 模式                          | 禁止用法                                    |
| -------- | ---------------- | --------------------------------------- | ------------------------------------------- |
| Create   | create           | `create{Entity}`                        | —                                           |
| Index    | **list**（集合） | `list{Entity}s` 或 `list{PluralEntity}` | 将列表操作写成 `read*`、`fetch*`、`query*`  |
| Details  | **get**（单条）  | `get{Entity}`                           | 将单条读取写成 `read*`                      |
| Edit     | **edit**         | `edit{Entity}`                          | 将编辑槽位写成 `update*`、`patch*`、`save*` |
| Delete   | delete           | `delete{Entity}`                        | —                                           |

**记录前自检（CIDED）：**

1. 统计**模板行**：须包含**五个**名称：`create*`、`list*`、`get*`、`edit*`、`delete*`。
2. 若仅有**四个**名称，且以 `create` / `read` / `update` / `delete` 类动词结尾，说明将 **Index 与 Details** 合并成了一个 `read*`——**须修正**：拆成 `list*` **与** `get*`。
3. 若任一名称以 `read`、`update`、`fetch` 或 `patch` 作为操作动词开头，**须替换**为上表约定（`list*`、`get*`、`edit*`）。

**错误示例（仍为「泛 CRUD」，未按 CIDED 槽位）：**

```text
createExamRecord, readExamRecord, updateExamRecord, deleteExamRecord   ← 仅四项；read/update 动词错误
```

**正确示例（符合 CIDED 槽位）：**

```text
createExamRecord, listExamRecords, getExamRecord, editExamRecord, deleteExamRecord
```

随后再于上述五项**之后**追加**推断**动作（例如 `publishExamRecord`）。

### 注意事项

- **`read*` 与 `update*` 不是 CIDED 的槽位名。** Index 对应 **`list*`**；Details 对应 **`get*`**；Edit 对应 **`edit*`**。API 提供的 `action_finder_log` 工具对 CIDED 会**拒绝**包含 `read*` / `update*` / `fetch*` / `patch*`，或缺少 `list*` / `get*` / `edit*` 的记录。
- 中文 **「读取」** 往往应对应 **list（列表）** 或 **get（详情）** 之一——**不得**用单一 `read*` 同时表示两者。

### 推断动作（须结合领域判断）

- 模板给出的是**最低限度**覆盖；当某实体在业务上通常还有支付、履约、取消、发布、归档等操作时，**须推断**额外动词。
- 推断动作仍采用相同 camelCase 风格：动词 + `Entity` 或语义清晰的对象名（`payOrder`、`refundOrder`、`archiveThread`）。
- 若实体较通用且无充分理由增加操作，可简要说明并**不**添加多余项——**不得**堆砌无意义名称。

### 示例

- **User** + CIDED → `createUser`、`listUsers`、`getUser`、`editUser`、`deleteUser`（除非用户明确要求角色/密码等，否则可不加额外项，例如 `resetUserPassword`）。
- **Request** + CIDRA → `createRequest`、`listRequests`、`getRequest`、`rejectRequest`、`approveRequest`；若流程允许，可选 `withdrawRequest`。
- **Order** + CIDED → 模板映射**之外**可推断：`payOrder`、`cancelOrder`、`refundOrder` 等，视系统描述而定。
- **Log** + CID → `createLog`、`listLogs`、`getLog`（只读场景通常不含 delete/edit）。

6. **必填 — 记录操作**：须通过以下**任一**方式记录本次运行：
   - 本地工具 `action_finder_log`（推荐）：传入**全部**最终动作（模板 + 推断），例如 `action_finder_log(entity_name="Order", template_selected="CIDED", actions=["createOrder", "listOrders", "getOrder", "editOrder", "deleteOrder", "payOrder", "cancelOrder"])`，**或**
   - `execute` 工具配合**主机真实路径**（shell 内不能使用虚拟路径 `/skills/...`）。API 会将 `AI_API_SKILLS_ROOT` 设为技能目录。示例（Windows cmd）：  
     `execute(command='python "%AI_API_SKILLS_ROOT%\\action-finder\\scripts\\log.py" Order CIDED createOrder listOrders getOrder editOrder deleteOrder payOrder cancelOrder')`  
     或在 `%AI_API_SKILLS_ROOT%\\action-finder\\scripts\\` 下同样方式调用 `log.bat`。
7. **返回结果**：须在**最前面**包含**必填的用户可见模板块**，随后：
   - 先按模板槽位顺序列出由模板导出的 camelCase 动作，再列出推断动作。

     示例：

     ```
     **Template:** CIDED (Create, Index, Details, Edit, Delete)
     **Rationale:** 该实体具备常规持久化生命周期，需支持列表、查看、编辑与删除。

     自模板映射的操作：
     - createOrder
     - listOrders
     - getOrder
     - editOrder
     - deleteOrder

     推断的额外操作：
     - payOrder
     - cancelOrder
     ```

     示例（中文界面，模板仍须显式写出）：

     ```
     **Template:** CIDED (Create, Index, Details, Edit, Delete)
     **Rationale:** 考试试卷作为标准业务实体，需要列表、详情、编辑与删除。

     自模板映射的操作：
     - createExamPaper   ← Create
     - listExamPapers    ← Index
     - getExamPaper      ← Details
     - editExamPaper     ← Edit
     - deleteExamPaper   ← Delete

     推断的额外操作：
     - publishExamPaper
     - duplicateExamPaper
     ```

## 重要说明

- **不得依赖脚本「发明」动作名**：由模型选定模板并推导名称；仅使用 `action_finder_log` 或配合 `log.py` 的 `execute` 来**持久化**结果。
- **模板优先**：须始终加载 `crud-templates.md`，明确选定 CIDED/CIDRA/CID 后再映射槽位——不得在未命名模板的情况下，将问题压缩为笼统的五词 CRUD 列表。
- **模板 + 推断**：模板是**主干**；当领域明显需要时（订单与支付、订阅、审批等），**必须**补充推断动作。
- **模板选择**：结合实体用途（例如「Request」常对应 CIDRA；「Log」常对应 CID）。
- **动作命名**：保持 camelCase 一致，动词贴切。
- **必填 — 记录**：在返回最终答复**之前**须调用 `action_finder_log`。日志文件位于 API 主机上的 `skills/action-finder/scripts/history.yaml`。

## 参考

- `/skills/action-finder/references/crud-templates.md` — 需要时使用 `read_file` 加载。

## 记录（必填）

每一轮完整执行须调用一次 `action_finder_log`，**或**使用 `execute` 调用 `log.py` / `log.bat`，传入实体名、所选模板与最终 camelCase 动作列表。

**错误**（模板标签）：`actions=["Create", "Index", "Details", "Edit", "Delete"]`。

**错误**（已选 CIDED 却仍用泛 CRUD 动词）：`actions=["createExamRecord", "readExamRecord", "updateExamRecord", "deleteExamRecord"]` —— 缺少 `list*` 与 `get*`；CIDED 下 `read*` / `update*` 会被 `action_finder_log` 拒绝。

**正确**（CIDED 的 camelCase，含模板与推断）：`actions=["createOrder", "listOrders", "getOrder", "editOrder", "deleteOrder", "payOrder"]`。

**正确**（考试记录 / ExamRecord）：`actions=["createExamRecord", "listExamRecords", "getExamRecord", "editExamRecord", "deleteExamRecord"]`。
