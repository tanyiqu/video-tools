# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'f:\Code\Python\video-tools\ui\Forms\MainForm.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainForm(object):
    def setupUi(self, MainForm):
        MainForm.setObjectName("MainForm")
        MainForm.resize(537, 367)
        self.verticalLayout = QtWidgets.QVBoxLayout(MainForm)
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame_select_video = QtWidgets.QFrame(MainForm)
        self.frame_select_video.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_select_video.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_select_video.setObjectName("frame_select_video")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame_select_video)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btn_select_video = QtWidgets.QPushButton(self.frame_select_video)
        self.btn_select_video.setObjectName("btn_select_video")
        self.horizontalLayout.addWidget(self.btn_select_video)
        self.txt_select_video = QtWidgets.QLineEdit(self.frame_select_video)
        self.txt_select_video.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.txt_select_video.setReadOnly(True)
        self.txt_select_video.setObjectName("txt_select_video")
        self.horizontalLayout.addWidget(self.txt_select_video)
        self.verticalLayout.addWidget(self.frame_select_video)
        self.tabWidget = QtWidgets.QTabWidget(MainForm)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.comboBox_trans = QtWidgets.QComboBox(self.tab)
        self.comboBox_trans.setGeometry(QtCore.QRect(10, 10, 141, 22))
        self.comboBox_trans.setObjectName("comboBox_trans")
        self.comboBox_trans.addItem("")
        self.comboBox_trans.addItem("")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.comboBox_fix = QtWidgets.QComboBox(self.tab_2)
        self.comboBox_fix.setGeometry(QtCore.QRect(10, 10, 141, 22))
        self.comboBox_fix.setObjectName("comboBox_fix")
        self.comboBox_fix.addItem("")
        self.tabWidget.addTab(self.tab_2, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.frame = QtWidgets.QFrame(MainForm)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(433, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.btn_start = QtWidgets.QPushButton(self.frame)
        self.btn_start.setObjectName("btn_start")
        self.horizontalLayout_2.addWidget(self.btn_start)
        self.verticalLayout.addWidget(self.frame)

        self.retranslateUi(MainForm)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainForm)

    def retranslateUi(self, MainForm):
        _translate = QtCore.QCoreApplication.translate
        MainForm.setWindowTitle(_translate("MainForm", "video-tools"))
        self.btn_select_video.setText(_translate("MainForm", "请选择视频："))
        self.comboBox_trans.setItemText(0, _translate("MainForm", "ts -> mp4"))
        self.comboBox_trans.setItemText(1, _translate("MainForm", "mp4 -> flv"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainForm", "转码"))
        self.comboBox_fix.setItemText(0, _translate("MainForm", "修复mp4索引"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainForm", "修复"))
        self.btn_start.setText(_translate("MainForm", "开始"))
