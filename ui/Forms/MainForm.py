from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QProcess
from pathlib import Path
import re

from ui.Forms.Ui_MainForm import Ui_MainForm
import config
import utils


class VideoWorker(QThread):
    progress_updated = pyqtSignal(int, str)
    file_finished = pyqtSignal(int, bool, str)
    all_finished = pyqtSignal()
    status_updated = pyqtSignal(str)
    current_progress_updated = pyqtSignal(int)

    def __init__(self, files, mode, target_format, output_folder, overwrite_source, fix_output_folder,
                 cut_hour=0, cut_minute=0, cut_second=0, cut_frame=0, cut_overwrite_source=False, cut_output_folder=""):
        super().__init__()
        self.files = files
        self.mode = mode
        self.target_format = target_format
        self.output_folder = output_folder
        self.overwrite_source = overwrite_source
        self.fix_output_folder = fix_output_folder
        self.cut_hour = cut_hour
        self.cut_minute = cut_minute
        self.cut_second = cut_second
        self.cut_frame = cut_frame
        self.cut_overwrite_source = cut_overwrite_source
        self.cut_output_folder = cut_output_folder

    def run(self):
        total = len(self.files)
        for i, file_path in enumerate(self.files):
            self.progress_updated.emit(i, f"处理中: {Path(file_path).name}")

            try:
                success = self._process_single_file(file_path)
                self.file_finished.emit(i, success, "成功" if success else "失败")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                self.file_finished.emit(i, False, f"错误: {str(e)}")

        self.all_finished.emit()

    def _process_single_file(self, file_path):
        input_path = Path(file_path)
        if not input_path.exists():
            print(f"输入文件不存在: {file_path}")
            return False

        if self.mode == 0:
            cmd = utils.FFmpegCommand.generate_with_output_dir(
                str(file_path), self.target_format, self.output_folder
            )
            if not cmd:
                return False
            success, _ = utils.CommandExecutor.execute(cmd)
            return success
        elif self.mode == 1:
            if self.overwrite_source:
                output_path = utils.FileManager.get_temp_path(file_path)
            else:
                output_path = config.config.get_output_path(
                    str(file_path), self.mode, self.overwrite_source, self.fix_output_folder
                )

            print(f"修复命令输出路径: {output_path}")
            cmd = utils.FFmpegCommand.fix_mp4_index(str(file_path), output_path)
            success, error_msg = utils.CommandExecutor.execute(cmd)
            print(f"FFmpeg执行结果: success={success}")

            output_file = Path(output_path)
            file_exists = output_file.exists()
            print(f"输出文件存在: {file_exists}")

            final_success = success or file_exists

            if final_success and self.overwrite_source:
                temp_file = Path(output_path)
                if temp_file.exists():
                    try:
                        backup_path = str(input_path) + ".backup"
                        if input_path.exists():
                            input_path.rename(backup_path)
                        temp_file.rename(input_path)
                        Path(backup_path).unlink(missing_ok=True)
                    except Exception as e:
                        print(f"文件替换操作: {e}")
                        try:
                            temp_file.rename(input_path)
                        except:
                            pass

            return final_success
        else:  # mode == 2, 去除片头
            if self.cut_overwrite_source:
                output_path = utils.FileManager.get_temp_path(file_path)
            else:
                output_path = config.config.get_output_path(
                    str(file_path), self.mode, self.cut_overwrite_source, self.cut_output_folder
                )

            print(f"去除片头输出路径: {output_path}")
            cmd = utils.FFmpegCommand.cut_intro(
                str(file_path), output_path,
                self.cut_hour, self.cut_minute, self.cut_second, self.cut_frame
            )
            success = self._execute_with_progress(cmd, str(file_path))
            print(f"FFmpeg执行结果: success={success}")

            output_file = Path(output_path)
            file_exists = output_file.exists()
            print(f"输出文件存在: {file_exists}")

            final_success = success or file_exists

            if final_success and self.cut_overwrite_source:
                temp_file = Path(output_path)
                if temp_file.exists():
                    try:
                        backup_path = str(input_path) + ".backup"
                        if input_path.exists():
                            input_path.rename(backup_path)
                        temp_file.rename(input_path)
                        Path(backup_path).unlink(missing_ok=True)
                    except Exception as e:
                        print(f"文件替换操作: {e}")
                        try:
                            temp_file.rename(input_path)
                        except:
                            pass

            return final_success

    def _execute_with_progress(self, cmd, input_file):
        import subprocess
        process = subprocess.Popen(
            cmd,
            shell=True,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            encoding='utf-8',
            errors='replace'
        )
        
        duration = self._get_video_duration(input_file)
        
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            
            if 'time=' in line:
                match = re.search(r'time=(\d+:\d+:\d+\.\d+)', line)
                if match:
                    time_str = match.group(1)
                    current_time = self._parse_time(time_str)
                    if duration > 0:
                        percent = min(100, int((current_time / duration) * 100))
                        self.status_updated.emit(f"处理中... {percent}% ({time_str})")
                        self.current_progress_updated.emit(percent)
        
        return process.returncode == 0

    def _get_video_duration(self, file_path):
        import subprocess
        try:
            cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.returncode == 0:
                return float(result.stdout.strip())
        except:
            pass
        return 0

    def _parse_time(self, time_str):
        parts = time_str.split(':')
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        return 0


class MainForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainForm()
        self.ui.setupUi(self)
        self._setup_ui()
        self._setup_connections()
        self._setup_drag_drop()

    def _setup_ui(self):
        self.ui.tableWidget.setColumnWidth(0, 200)
        self.ui.tableWidget.setColumnWidth(1, 100)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.ui.lineEdit_output.setText(config.config.output_folder)
        self.ui.lineEdit_fix_output.setText(config.config.fix_output_folder)
        self.ui.lineEdit_cut_output.setText(config.config.cut_output_folder)
        self.ui.spinBox_hour.setValue(config.config.cut_hour)
        self.ui.spinBox_minute.setValue(config.config.cut_minute)
        self.ui.spinBox_second.setValue(config.config.cut_second)
        self.ui.spinBox_frame.setValue(config.config.cut_frame)
        self.ui.checkBox_cut_intro_overwrite.setChecked(config.config.cut_overwrite_source)
        self._update_cut_output_visibility()
        self.setFixedSize(self.width(), self.height())

    def _setup_connections(self):
        self.ui.btn_add_files.clicked.connect(self._on_add_files)
        self.ui.btn_delete_selected.clicked.connect(self._on_delete_selected)
        self.ui.btn_clear_list.clicked.connect(self._on_clear_list)
        self.ui.btn_browse_output.clicked.connect(self._on_browse_output)
        self.ui.btn_browse_fix_output.clicked.connect(self._on_browse_fix_output)
        self.ui.btn_browse_cut_output.clicked.connect(self._on_browse_cut_output)
        self.ui.btn_start.clicked.connect(self._on_start)
        self.ui.tabWidget.currentChanged.connect(self._on_tab_changed)
        self.ui.checkBox_overwrite.stateChanged.connect(self._on_overwrite_changed)
        self.ui.checkBox_cut_intro_overwrite.stateChanged.connect(self._on_cut_overwrite_changed)
        self.ui.spinBox_hour.valueChanged.connect(self._on_cut_time_changed)
        self.ui.spinBox_minute.valueChanged.connect(self._on_cut_time_changed)
        self.ui.spinBox_second.valueChanged.connect(self._on_cut_time_changed)
        self.ui.spinBox_frame.valueChanged.connect(self._on_cut_time_changed)

    def _setup_drag_drop(self):
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                files.append(url.toLocalFile())
        self._add_files_to_list(files)

    def _add_files_to_list(self, file_paths):
        existing_files = set(config.config.video_files)
        for file_path in file_paths:
            if file_path not in existing_files:
                config.config.video_files.append(file_path)
                self._add_file_to_table(file_path)
        self._update_source_format_display()

    def _add_file_to_table(self, file_path):
        path = Path(file_path)
        row = self.ui.tableWidget.rowCount()
        self.ui.tableWidget.insertRow(row)

        item_name = QTableWidgetItem(path.name)
        item_name.setData(Qt.UserRole, file_path)
        self.ui.tableWidget.setItem(row, 0, item_name)

        item_status = QTableWidgetItem("待处理")
        self.ui.tableWidget.setItem(row, 1, item_status)

        item_path = QTableWidgetItem(str(path.parent))
        self.ui.tableWidget.setItem(row, 2, item_path)

    def _update_source_format_display(self):
        if config.config.has_files:
            first_file = config.config.video_files[0]
            ext = utils.FileManager.get_file_extension(first_file)
            self.ui.label_source_format.setText(ext.upper())
        else:
            self.ui.label_source_format.setText("未选择")

    def _check_mp4_files(self):
        non_mp4_files = []
        for file_path in config.config.video_files:
            ext = utils.FileManager.get_file_extension(file_path)
            if ext.lower() != 'mp4':
                non_mp4_files.append(Path(file_path).name)
        return non_mp4_files

    def _on_add_files(self):
        files = utils.FileDialog.select_files(
            self, "选择视频文件",
            "视频文件 (*.mp4 *.ts *.flv *.avi *.mkv *.mov);;所有文件 (*.*)"
        )
        self._add_files_to_list(files)

    def _on_delete_selected(self):
        selected_rows = set()
        for item in self.ui.tableWidget.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选择要删除的视频文件")
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除选中的 {len(selected_rows)} 个视频吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for row in sorted(selected_rows, reverse=True):
                file_path = self.ui.tableWidget.item(row, 0).data(Qt.UserRole)
                if file_path in config.config.video_files:
                    config.config.video_files.remove(file_path)
                self.ui.tableWidget.removeRow(row)
            self._update_source_format_display()

    def _on_clear_list(self):
        self.ui.tableWidget.setRowCount(0)
        config.config.video_files = []
        self.ui.label_source_format.setText("未选择")

    def _on_browse_output(self):
        folder = utils.FileDialog.select_folder(
            self, "选择输出文件夹", config.config.output_folder
        )
        if folder:
            config.config.output_folder = folder
            self.ui.lineEdit_output.setText(folder)

    def _on_browse_fix_output(self):
        folder = utils.FileDialog.select_folder(
            self, "选择输出文件夹", config.config.fix_output_folder
        )
        if folder:
            config.config.fix_output_folder = folder
            self.ui.lineEdit_fix_output.setText(folder)

    def _on_browse_cut_output(self):
        folder = utils.FileDialog.select_folder(
            self, "选择输出文件夹", config.config.cut_output_folder
        )
        if folder:
            config.config.cut_output_folder = folder
            self.ui.lineEdit_cut_output.setText(folder)

    def _on_overwrite_changed(self, state):
        is_overwrite = state == Qt.Checked
        self.ui.lineEdit_fix_output.setEnabled(not is_overwrite)
        self.ui.btn_browse_fix_output.setEnabled(not is_overwrite)

    def _on_cut_overwrite_changed(self, state):
        is_overwrite = state == Qt.Checked
        config.config.cut_overwrite_source = is_overwrite
        self._update_cut_output_visibility()

    def _update_cut_output_visibility(self):
        is_overwrite = self.ui.checkBox_cut_intro_overwrite.isChecked()
        self.ui.lineEdit_cut_output.setEnabled(not is_overwrite)
        self.ui.btn_browse_cut_output.setEnabled(not is_overwrite)

    def _on_cut_time_changed(self):
        config.config.cut_hour = self.ui.spinBox_hour.value()
        config.config.cut_minute = self.ui.spinBox_minute.value()
        config.config.cut_second = self.ui.spinBox_second.value()
        config.config.cut_frame = self.ui.spinBox_frame.value()

    def _on_tab_changed(self, index):
        pass

    def _on_start(self):
        if not config.config.has_files:
            self.ui.label_status.setText("请先添加视频文件！")
            return

        config.config.mode = self.ui.tabWidget.currentIndex()

        target_format = ""
        overwrite_source = False
        fix_output_folder = ""
        cut_hour = 0
        cut_minute = 0
        cut_second = 0
        cut_frame = 0
        cut_overwrite_source = False
        cut_output_folder = ""

        if config.config.mode == 0:
            target_format = self.ui.comboBox_target.currentText()
            if not target_format:
                self.ui.label_status.setText("请选择目标格式！")
                return
            if not config.config.output_folder:
                self.ui.label_status.setText("请选择输出文件夹！")
                return
        elif config.config.mode == 1:
            non_mp4_files = self._check_mp4_files()
            if non_mp4_files:
                file_list = '\n'.join(non_mp4_files)
                reply = QMessageBox.question(
                    self, "格式警告",
                    f"以下文件不是MP4格式，是否继续处理？\n\n{file_list}",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            overwrite_source = self.ui.checkBox_overwrite.isChecked()
            config.config.overwrite_source = overwrite_source
            fix_output_folder = config.config.fix_output_folder
            if not overwrite_source and not fix_output_folder:
                self.ui.label_status.setText("请选择输出文件夹！")
                return
        else:  # mode == 2
            cut_hour = self.ui.spinBox_hour.value()
            cut_minute = self.ui.spinBox_minute.value()
            cut_second = self.ui.spinBox_second.value()
            cut_frame = self.ui.spinBox_frame.value()
            cut_overwrite_source = self.ui.checkBox_cut_intro_overwrite.isChecked()
            cut_output_folder = config.config.cut_output_folder

            if cut_hour == 0 and cut_minute == 0 and cut_second == 0 and cut_frame == 0:
                self.ui.label_status.setText("请输入要去除的时长！")
                return

            if not cut_overwrite_source and not cut_output_folder:
                self.ui.label_status.setText("请选择输出文件夹！")
                return

        self._set_ui_enabled(False)

        self.worker = VideoWorker(
            config.config.video_files.copy(),
            config.config.mode,
            target_format,
            config.config.output_folder,
            overwrite_source,
            fix_output_folder,
            cut_hour,
            cut_minute,
            cut_second,
            cut_frame,
            cut_overwrite_source,
            cut_output_folder
        )
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.file_finished.connect(self._on_file_finished)
        self.worker.all_finished.connect(self._on_all_finished)
        self.worker.status_updated.connect(self._on_status_updated)
        self.worker.current_progress_updated.connect(self._on_current_progress_updated)
        self.worker.start()

    def _on_status_updated(self, status_text):
        self.ui.label_status.setText(status_text)

    def _on_current_progress_updated(self, percent):
        self.ui.progressBar.setValue(percent)

    def _on_progress_updated(self, index, status_text):
        total = len(config.config.video_files)
        progress = int((index / total) * 100)
        self.ui.progressBar_total.setValue(progress)
        self.ui.label_status.setText(status_text)

    def _on_file_finished(self, index, success, status_text):
        item = self.ui.tableWidget.item(index, 1)
        if item:
            item.setText(status_text)
            if success:
                item.setForeground(Qt.green)
            else:
                item.setForeground(Qt.red)

    def _on_all_finished(self):
        self.ui.progressBar.setValue(100)
        self.ui.progressBar_total.setValue(100)
        self.ui.label_status.setText("处理完成！")
        self._set_ui_enabled(True)

    def _set_ui_enabled(self, enabled):
        self.ui.btn_add_files.setEnabled(enabled)
        self.ui.btn_delete_selected.setEnabled(enabled)
        self.ui.btn_clear_list.setEnabled(enabled)
        self.ui.btn_start.setEnabled(enabled)
        self.ui.btn_browse_output.setEnabled(enabled)
        self.ui.btn_browse_fix_output.setEnabled(enabled)
        self.ui.btn_browse_cut_output.setEnabled(enabled)
        self.ui.tabWidget.setEnabled(enabled)
        self.ui.tableWidget.setEnabled(enabled)
        self.ui.comboBox_target.setEnabled(enabled)
        self.ui.checkBox_overwrite.setEnabled(enabled)
        self.ui.lineEdit_fix_output.setEnabled(enabled and not self.ui.checkBox_overwrite.isChecked())
        self.ui.checkBox_cut_intro_overwrite.setEnabled(enabled)
        self.ui.lineEdit_cut_output.setEnabled(enabled and not self.ui.checkBox_cut_intro_overwrite.isChecked())
        self.ui.spinBox_hour.setEnabled(enabled)
        self.ui.spinBox_minute.setEnabled(enabled)
        self.ui.spinBox_second.setEnabled(enabled)
        self.ui.spinBox_frame.setEnabled(enabled)
