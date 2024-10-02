import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog
from PyQt5.QtCore import QFileInfo
import os
from pathlib import Path

# 弹出对话框，选择单个文件


def showSelectFileDialog(parent, title, filter):
    options = QFileDialog.Options()
    fileName, _ = QFileDialog.getOpenFileName(
        parent, title, "", filter, options=options)
    if fileName:
        fileInfo = QFileInfo(fileName)
        print("selected: " + fileInfo.absoluteFilePath())
        return fileInfo
    return None


# 构造ffmpeg命令
def generate_cmd(mode, option, input_filename, output_filename):
    # ts -> mp4
    cmd_0_0 = 'ffmpeg -y -i "{}" -vcodec copy -acodec copy -vbsf h264_mp4toannexb "{}"'

    # mp4 -> flv
    cmd_0_1 = ''

    # 修复mp4索引
    cmd_1_0 = 'ffmpeg -i "{}" -c:v copy -c:a copy "{}"'

    if mode == 0:
        if option == 0:
            return cmd_0_0.format(input_filename, output_filename)
            pass
        elif option == 1:

            pass
        pass
    elif mode == 1:
        if option == 0:
            return cmd_1_0.format(input_filename, output_filename)
            pass
        pass

    pass


# 弹出窗口执行命令
def shell_exec(cmd):
    # subprocess.Popen(['start', 'cmd', '/k', cmd])
    print(cmd)
    # subprocess.run([cmd], capture_output=True, text=True)
    os.system(cmd)
    print('success')
    pass


# 删除文件
def unlink(path):
    file_path = Path(path)
    try:
        file_path.unlink()
        print(f"File {file_path} has been deleted successfully.")
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
    except OSError as e:
        print(f"Error: {e}")
    pass


# 重命名文件
def rename(old_path, new_path):
    # 创建路径对象
    old_file_path = Path(old_path)

    # 新文件路径
    new_file_path = Path(new_path)

    try:
        old_file_path.rename(new_file_path)
        print(
            f"File has been renamed from {old_file_path} to {new_file_path}.")
    except FileExistsError:
        print(f"Error: The file {new_file_path} already exists.")
    except NotADirectoryError:
        print(f"Error: {old_file_path} is not a directory.")
    except IsADirectoryError:
        print(f"Error: {new_file_path} is a directory.")
    except PermissionError:
        print(f"Error: Permission denied when renaming {old_file_path}.")
    except OSError as e:
        print(f"Error: {e}")
    pass
