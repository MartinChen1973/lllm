# CRUD 模板

本文档提供若干 CRUD 操作模板，用于为不同实体类型定义标准的动作模式。

## CIDED 模板

**Create、Index（列表）、Details、Edit、Delete**

适用于支持完整创建、读取、更新与删除操作的实体的标准 CRUD 模板。

- **Create**：新建实体实例
- **Index**：列出全部实体实例
- **Details**：查看某一实体实例
- **Edit**：修改已有实体实例
- **Delete**：删除实体实例

## CIDRA 模板

**Create、Index、Details、Reject（通常伴随 Edit）、Approve**

适用于需要审批流程的实体，例如申请、报送或待处理记录。

- **Create**：新建实体实例
- **Index**：列出全部实体实例
- **Details**：查看某一实体实例
- **Reject**：驳回实体实例（通常包含编辑能力）
- **Approve**：批准实体实例

## CID 模板

**Create、Index、Details**

适用于创建后不可修改或删除的只读类实体，例如日志、审计轨迹或历史记录。

- **Create**：新建实体实例
- **Index**：列出全部实体实例
- **Details**：查看某一实体实例
