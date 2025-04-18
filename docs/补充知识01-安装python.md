### **Windows 系统安装和配置 Python 的完整指南**

---

#### **0. 以管理员身份运行安装程序**

确保以管理员身份运行安装程序，以避免权限问题：

- 右键单击下载的安装程序（如 `python-3.x.x.exe`），选择 **“以管理员身份运行”** 。

---

#### **1. 安装 Python**

1. **下载 Python 安装包**
   - 前往 [Python 官方网站](https://www.python.org/) 下载最新的 Python 安装程序，选择适合您的系统版本（Windows 通常是 `64-bit`）。
2. **运行安装程序**
   - 以**管理员权限运行**下载的 `.exe` 文件。
3. **选择安装组件**
   - 确保以下选项已勾选：
   - **pip** （Python 包管理工具）
   - **IDLE** （Python 内置编辑器）
   - **Documentation** （文档）
   - **tcl/tk 和其他模块** （用于图形界面支持）
   - **测试套件** （可选）
4. **高级选项**
   - 在 **“Advanced Options”** 页面中，确保勾选：
     - **“Add Python to environment variables”** （将 Python 路径添加到环境变量）。
   - 默认安装路径通常为 `C:\Users\<用户名>\AppData\Local\Programs\Python\Python3.x`，也可以自定义路径。
5. **完成安装**
   - 点击 **“Install”** ，等待安装完成。

![1737900004656](image/补充知识01-安装python/1737900004656.png)

![1737900118470](image/补充知识01-安装python/1737900118470.png)---

#### **2. 手动加入 Python 到环境变量**

如果在安装时未勾选 **“Add Python to PATH”** ，可以手动将 Python 添加到环境变量：

1. **获取 Python 路径**

   - 找到 Python 的安装目录（如：`C:\Users\<用户名>\AppData\Local\Programs\Python\Python3.x`）。
   - 复制该路径，以及其下的 `Scripts` 目录路径（如：`C:\Users\<用户名>\AppData\Local\Programs\Python\Python3.x\Scripts`）。

2. **配置环境变量**

   - **打开系统设置：**
     - 在任务栏搜索框输入“环境变量”，点击 **“编辑系统环境变量”** 。
   - **编辑 PATH 变量：**
     - 点击 **“环境变量”** 按钮。
     - 在 **“系统变量”** 下，找到 **“Path”** ，双击或点击 **“编辑”** 。
     - 点击 **“新建”** ，添加以下路径：
       - Python 主目录路径（如：`C:\Users\<用户名>\AppData\Local\Programs\Python\Python3.x`）。
       - `Scripts` 目录路径（如：`C:\Users\<用户名>\AppData\Local\Programs\Python\Python3.x\Scripts`）。
     - 保存并退出。

3. **验证环境变量**

   - 打开命令提示符（`Win + R`，输入 `cmd`，回车），输入：

     ```bash
     python --version
     ```

     如果成功显示版本号，则配置完成。

---

#### **3. 检查 Python 版本**

安装完成后，检查 Python 是否安装成功及版本号：

1. 打开命令提示符（`cmd`）。
2. 输入以下命令并回车：

   ```bash
   python --version
   ```

   或者：

   ```bash
   python3 --version
   ```

   如果正确显示 Python 的版本号（如 `Python 3.x.x`），说明安装成功。

---

#### **4. 启动和使用虚拟环境**

虚拟环境是 Python 提供的一种工具，用于在隔离的环境中管理项目的依赖和库，避免冲突。以下是使用虚拟环境的步骤：

1. **创建虚拟环境**

   - 进入项目目录，运行以下命令：

     ```bash
     python -m venv venv
     ```

     这将在当前目录下创建一个名为 `venv` 的虚拟环境。

2. **激活虚拟环境**

   - **Windows** ：

   ```bash
   .\venv\Scripts\activate
   ```

   - **macOS/Linux** ：

   ```bash
   source venv/bin/activate
   ```

3. **验证虚拟环境是否激活**

   - 激活后，终端会显示 `(venv)`，表示已进入虚拟环境。
   - 在虚拟环境中安装的库与全局环境相互独立。

4. **退出虚拟环境**

   - 使用以下命令退出虚拟环境：
     ```bash
     deactivate
     ```

---

#### **5. 虚拟环境的目的**

虚拟环境的主要作用是 **隔离项目环境，避免依赖冲突** ，以下是其核心目标：

1. **解决依赖冲突**

   不同项目需要不同版本的库（例如，项目 A 使用 `Django 4.0`，项目 B 使用 `Django 3.2`）。虚拟环境为每个项目提供独立的依赖环境。

2. **支持多个 Python 版本**

   在同一台机器上，可以为每个项目分配不同版本的 Python 环境，而不互相干扰。

3. **提高可维护性**

   - 通过虚拟环境可以确保项目的依赖固定，在不同的环境下运行一致。
   - 便于导出依赖（通过 `pip freeze > requirements.txt`）并在新环境中快速恢复。

4. **增强项目的迁移和部署能力**

   - 依赖集中管理，方便在本地、测试和生产环境中保持一致。

---
