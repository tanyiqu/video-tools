from ui.Forms.Ui_MainForm import Ui_MainForm
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog
from PyQt5.QtCore import QFileInfo
import utils
import config


class MainForm(QWidget):
    def __init__(self, parent=None):
        super(MainForm, self).__init__(parent)
        self.mainForm = Ui_MainForm()
        self.mainForm.setupUi(self)
        self.init_func()
        pass
    pass

    # 初始化事件
    def init_func(self):
        # 选择视频文件
        self.mainForm.btn_select_video.clicked.connect(self.select_video)

        # 点击开始
        self.mainForm.btn_start.clicked.connect(self.start)

        # # 选择模式

        # # 点击下拉菜单时
        # self.mainForm.comboBox_trans.activated.connect(lambda:print(333))
        # self.mainForm.comboBox_fix.activated.connect(lambda:print(4444))
        pass

    # 选择视频文件
    def select_video(self):
        file = utils.showSelectFileDialog(self, "请选择视频文件", "All Files (*);;")
        if file:
            config._config['selected_video_file_path'] = file.absoluteFilePath()
            config._config['selected_video_path'] = file.absolutePath()
            config._config['selected_video_file_name'] = file.fileName()
            self.mainForm.txt_select_video.setText(
                config._config['selected_video_file_path'])
            pass
        pass

    def start(self):
        print('start')
        config._config['mode'] = self.mainForm.tabWidget.currentIndex()
        if config._config['mode'] == 0:
            config._config['option'] = self.mainForm.comboBox_trans.currentIndex()
            pass
        elif config._config['mode'] == 1:
            config._config['option'] = self.mainForm.comboBox_fix.currentIndex()
            pass

        print(config._config['mode'])
        print(config._config['option'])

        cmd = utils.generate_cmd(config._config['mode'],
                                 config._config['option'],
                                 config._config['selected_video_file_path'],
                                 config._config['selected_video_path'] + '/' + '_out_' + config._config['selected_video_file_name'])
        utils.shell_exec(cmd)
        pass
