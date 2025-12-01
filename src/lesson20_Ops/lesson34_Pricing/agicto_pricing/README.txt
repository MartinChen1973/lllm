========================================
Agicto Pricing Web Interface
使用说明 / Usage Instructions
========================================

本应用有两种运行方式：
There are two ways to run this application:

方式 1: 使用批处理文件运行 (开发模式)
Method 1: Run using batch file (Development mode)

  1. 双击运行: run_agicto_pricing.bat
     Double-click: run_agicto_pricing.bat
  
  2. 浏览器将自动打开 http://localhost:5000
     Browser will automatically open http://localhost:5000


方式 2: 使用可执行文件运行 (发布版本)
Method 2: Run using executable (Release version)

  步骤 1: 构建可执行文件
  Step 1: Build the executable

    1. 确保已激活虚拟环境
       Make sure virtual environment is activated:
       
       cd c:\Projects\Courses\lllm
       .\venv\Scripts\activate

    2. 运行构建脚本
       Run the build script:
       
       cd src\lesson30_Production\lesson34_Pricing\agicto_pricing
       build_exe.bat

    3. 构建脚本会自动：
       The build script will automatically:
       - 检查并安装 PyInstaller (如果未安装)
         Check and install PyInstaller (if not installed)
       - 创建 bin 文件夹 (如果不存在)
         Create bin folder (if it doesn't exist)
       - 生成可执行文件: bin\agicto_pricing.exe
         Generate executable: bin\agicto_pricing.exe

  步骤 2: 运行可执行文件
  Step 2: Run the executable
    
    双击: bin\agicto_pricing.exe
    Double-click: bin\agicto_pricing.exe
    
    浏览器将自动打开
    Browser will open automatically


========================================
重要提示 / Important Notes
========================================

1. 端口占用: 如果端口 5000 已被占用，请修改 src\agicto_pricing.py 中的端口号
   Port conflict: If port 5000 is in use, change the port in src\agicto_pricing.py

2. 首次运行: 应用会从 agicto.com 获取最新数据
   First run: Application will fetch latest data from agicto.com

3. 停止应用: 关闭服务器窗口即可停止应用
   Stop application: Close the server window to stop the application

4. 文件位置:
   File locations:
   - 可执行文件: bin\agicto_pricing.exe
     Executable: bin\agicto_pricing.exe
   - 开发脚本: run_agicto_pricing.bat
     Development script: run_agicto_pricing.bat


========================================
故障排除 / Troubleshooting
========================================

问题: 构建失败
Issue: Build fails

  解决: 确保 PyInstaller 已安装
  Solution: Make sure PyInstaller is installed
  
    pip install pyinstaller

问题: 找不到模块
Issue: Module not found

  解决: 确保虚拟环境已激活且所有依赖已安装
  Solution: Make sure virtual environment is activated and dependencies installed
  
    pip install -r requirements.txt

问题: 浏览器未自动打开
Issue: Browser doesn't open automatically

  解决: 手动打开浏览器访问 http://localhost:5000
  Solution: Manually open browser and visit http://localhost:5000



