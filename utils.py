import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog
from PyQt5.QtCore import QFileInfo
import subprocess  
import os


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