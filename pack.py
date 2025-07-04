# pack.py
import os
import PyInstaller.__main__

# 确保图标文件存在
if not os.path.exists('app_icon.ico'):
    raise FileNotFoundError("应用图标 app_icon.ico 未找到")

# PyInstaller配置参数
params = [
    'main.py',              # 主程序入口
    '--onefile',            # 打包成单文件
    '--windowed',           # 不显示控制台窗口
    '--icon=app_icon.ico',  # 应用图标
    '--name=EasyMosaicApp', # 可执行文件名称
    '--add-data=app_icon.ico;.',  # 包含图标文件
    '--exclude-module=present'    # 排除present模块
]

# 添加隐藏导入（根据实际依赖可能需要调整）
hidden_imports = [
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets'
]

for module in hidden_imports:
    params.append(f'--hidden-import={module}')

# 执行打包命令
PyInstaller.__main__.run(params)
