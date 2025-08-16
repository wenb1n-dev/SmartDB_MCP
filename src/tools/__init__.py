import os
import glob
from importlib import import_module



# 自动导入该目录下其他模块中的所有类
# 获取当前目录下的所有Python文件
current_dir = os.path.dirname(__file__)
module_files = glob.glob(os.path.join(current_dir, "*.py"))

# 需要排除的文件
exclude_files = ['__init__.py', 'base.py']
exclude_classes = {}

# 存储已导入的类名，避免重复导入
imported_classes = set()

# 遍历所有模块文件
for file_path in module_files:
    file_name = os.path.basename(file_path)
    module_name = os.path.splitext(file_name)[0]
    
    # 排除特定文件
    if file_name in exclude_files:
        continue
    
    # 动态导入模块
    try:
        module = import_module(f'.{module_name}', package='tools')
        # 导入模块中所有类（除了已手动导入的）
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            # 检查是否为类，且未被导入过，且类名以Tool结尾
            if (isinstance(attr, type) and 
                attr_name not in imported_classes and 
                attr_name not in exclude_classes and
                attr_name.endswith('Tool')):
                # 将类添加到当前模块的命名空间
                globals()[attr_name] = attr
                imported_classes.add(attr_name)
    except ImportError:
        # 如果导入失败，跳过该模块
        pass

# 清理临时变量
del os, glob, import_module, current_dir, module_files, exclude_files
del exclude_classes, imported_classes, file_path, file_name, module_name