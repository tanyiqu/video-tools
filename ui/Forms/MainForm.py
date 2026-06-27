from PyQt5.QtWidgets import (
    QWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTableWidget, QAbstractItemView,
    QScrollArea, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMimeData, QSize, QRect
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont, QDrag, QPalette
from pathlib import Path
import re
import sys
import time
import os

from ui.Forms.Ui_MainForm import Ui_MainForm
import config
import utils


from PyQt5.QtWidgets import (
    QWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTableWidget, QAbstractItemView,
    QScrollArea, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QApplication, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMimeData, QSize, QRect, QEvent, QPoint
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont, QDrag, QPalette, QFontMetrics
from pathlib import Path
import re

from ui.Forms.Ui_MainForm import Ui_MainForm
import config
import utils


COL_INDEX_WIDTH = 40
COL_STATUS_WIDTH = 100
SCROLLBAR_WIDTH = 10  # 滚动条预留宽度


class TableRowWidget(QWidget):
    """自定义表格行控件"""
    drag_started = pyqtSignal(int)  # 行索引
    clicked = pyqtSignal(int)  # 行索引

    def __init__(self, file_path, row_index, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.row_index = row_index
        self.is_selected = False
        self._drag_start_pos = None
        self._is_dragging = False
        self._name_width = 0
        self._path_width = 0
        self._setup_ui()
        self.setFixedHeight(26)
        self._update_style()

    def _setup_ui(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.label_index = QLabel(str(self.row_index + 1))
        self.label_index.setFixedWidth(COL_INDEX_WIDTH)
        self.label_index.setAlignment(Qt.AlignCenter)

        self.label_name = QLabel()
        self.label_name.setWordWrap(False)
        self.label_name.setMinimumWidth(1)

        self.label_status = QLabel("待处理")
        self.label_status.setFixedWidth(COL_STATUS_WIDTH)

        self.label_path = QLabel()
        self.label_path.setWordWrap(False)
        self.label_path.setMinimumWidth(1)

        layout.addWidget(self.label_index, 0)
        layout.addWidget(self.label_name, 0)
        layout.addWidget(self.label_status, 0)
        layout.addWidget(self.label_path, 0)
        layout.addStretch(1)

        self._update_name_text()
        self._update_path_text()

    def set_column_widths(self, name_width, path_width):
        """手动设置文件名和路径列的宽度"""
        self._name_width = name_width
        self._path_width = path_width
        self.label_name.setFixedWidth(max(10, name_width))
        self.label_path.setFixedWidth(max(10, path_width))
        self._update_elided_text()

    def _update_name_text(self):
        name = Path(self.file_path).name
        self.label_name.setToolTip(name)
        self.label_name.setText(name)

    def _update_path_text(self):
        path = str(Path(self.file_path).parent)
        self.label_path.setToolTip(path)
        self.label_path.setText(path)

    def _update_elided_text(self):
        """根据当前宽度更新省略文本"""
        name = Path(self.file_path).name
        fm = QFontMetrics(self.label_name.font())
        w = self.label_name.width()
        if w > 0:
            elided = fm.elidedText(name, Qt.ElideRight, max(10, w - 8))
            self.label_name.setText(elided)

        path = str(Path(self.file_path).parent)
        fm = QFontMetrics(self.label_path.font())
        w = self.label_path.width()
        if w > 0:
            elided = fm.elidedText(path, Qt.ElideRight, max(10, w - 8))
            self.label_path.setText(elided)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elided_text()

    def _update_style(self):
        """根据选中状态更新样式"""
        if self.is_selected:
            self.setStyleSheet("""
                QWidget {
                    background-color: #ecf5ff;
                    border-bottom: 1px solid #d9ecff;
                }
            """)
            self.label_index.setStyleSheet("background-color: transparent; color: #409eff; font-weight: bold; font-size: 12px; padding: 2px;")
            self.label_name.setStyleSheet("background-color: transparent; color: #409eff; font-weight: bold; font-size: 12px; padding: 2px 4px;")
            self.label_status.setStyleSheet("background-color: transparent; color: #409eff; font-size: 12px; padding: 2px 4px;")
            self.label_path.setStyleSheet("background-color: transparent; color: #409eff; font-size: 12px; padding: 2px 4px;")
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                    border-bottom: 1px solid #e4e7ed;
                }
                QWidget:hover {
                    background-color: #f5f7fa;
                }
            """)
            self.label_index.setStyleSheet("background-color: transparent; color: #909399; font-size: 12px; padding: 2px;")
            self.label_name.setStyleSheet("background-color: transparent; color: #303133; font-weight: bold; font-size: 12px; padding: 2px 4px;")
            self.label_status.setStyleSheet("background-color: transparent; color: #909399; font-size: 12px; padding: 2px 4px;")
            self.label_path.setStyleSheet("background-color: transparent; color: #c0c4cc; font-size: 12px; padding: 2px 4px;")

    def set_selected(self, selected):
        self.is_selected = selected
        self._update_style()

    def set_status(self, text, success=True):
        self.label_status.setText(text)
        if success:
            self.label_status.setStyleSheet("color: #67c23a; font-size: 12px; padding: 2px 4px;")
        else:
            self.label_status.setStyleSheet("color: #f56c6c; font-size: 12px; padding: 2px 4px;")

    def update_index(self, new_index):
        self.row_index = new_index
        self.label_index.setText(str(new_index + 1))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.pos()
            self._is_dragging = False
            self.clicked.emit(self.row_index)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self._drag_start_pos is not None:
            if not self._is_dragging:
                if (event.pos() - self._drag_start_pos).manhattanLength() > 8:
                    self._is_dragging = True
                    self.drag_started.emit(self.row_index)
                    return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        self._is_dragging = False
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        if not self.is_selected:
            self.setStyleSheet("""
                QWidget {
                    background-color: #f5f7fa;
                    border-bottom: 1px solid #e4e7ed;
                }
            """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.is_selected:
            self.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                    border-bottom: 1px solid #e4e7ed;
                }
            """)
        super().leaveEvent(event)


class CustomTableWidget(QWidget):
    """自定义表格控件"""
    order_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []
        self._row_widgets = []
        self._selected_index = -1
        self._drag_index = -1
        self._drop_indicator_pos = -1
        self._setup_ui()
        self.setAcceptDrops(True)

    def _setup_ui(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 外层容器，统一管理边框圆角
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                border: 1px solid #dcdfe6;
                border-radius: 8px;
                background-color: #fafafa;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # 表头
        self.header = QWidget()
        self.header.setFixedHeight(28)
        self.header.setStyleSheet("""
            background-color: #409eff;
            border-top-left-radius: 7px;
            border-top-right-radius: 7px;
        """)
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(0, 0, SCROLLBAR_WIDTH, 0)
        self.header_layout.setSpacing(0)

        self.h_index = QLabel("序号")
        self.h_index.setFixedWidth(COL_INDEX_WIDTH)
        self.h_index.setAlignment(Qt.AlignCenter)
        self.h_name = QLabel("文件名")
        self.h_name.setMinimumWidth(1)
        self.h_status = QLabel("状态")
        self.h_status.setFixedWidth(COL_STATUS_WIDTH)
        self.h_path = QLabel("路径")
        self.h_path.setMinimumWidth(1)

        for label in [self.h_index, self.h_name, self.h_status, self.h_path]:
            label.setStyleSheet("background-color: transparent; color: #ffffff; font-weight: bold; font-size: 12px; padding: 4px;")

        self.header_layout.addWidget(self.h_index, 0)
        self.header_layout.addWidget(self.h_name, 0)
        self.header_layout.addWidget(self.h_status, 0)
        self.header_layout.addWidget(self.h_path, 0)
        self.header_layout.addStretch(1)

        container_layout.addWidget(self.header)

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setAcceptDrops(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #fafafa;
            }
            QScrollBar:vertical {
                border: none;
                width: 8px;
                background: #f5f7fa;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #c0c4cc;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #909399;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                height: 0px;
            }
        """)

        # 内容容器
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: #fafafa;")
        self.content_widget.setAcceptDrops(True)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.addStretch(1)

        self.scroll_area.setWidget(self.content_widget)
        container_layout.addWidget(self.scroll_area, 1)

        main_layout.addWidget(container)

        # 安装事件过滤器，确保拖拽事件传递到本表控件
        self.scroll_area.installEventFilter(self)
        self.scroll_area.viewport().installEventFilter(self)
        self.content_widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.DragEnter, QEvent.DragMove, QEvent.DragLeave, QEvent.Drop):
            if event.mimeData().hasText() and event.mimeData().text().startswith("row:"):
                # 转换坐标到本表控件坐标系
                global_pos = event.pos()
                if hasattr(obj, 'mapTo'):
                    global_pos = obj.mapTo(self, event.pos())
                else:
                    global_pos = event.pos()

                # 创建一个带转换后坐标的事件
                fake_pos = global_pos

                if event.type() == QEvent.DragEnter:
                    event.acceptProposedAction()
                    self._drop_indicator_pos = self._calc_drop_target(fake_pos)
                    self.update()
                    return True
                elif event.type() == QEvent.DragMove:
                    event.acceptProposedAction()
                    target_row = self._calc_drop_target(fake_pos)
                    if target_row != self._drop_indicator_pos:
                        self._drop_indicator_pos = target_row
                        self.update()
                    return True
                elif event.type() == QEvent.DragLeave:
                    self._drop_indicator_pos = -1
                    self.update()
                    return True
                elif event.type() == QEvent.Drop:
                    self._handle_drop(event, fake_pos)
                    return True
        return super().eventFilter(obj, event)

    def _handle_drop(self, event, pos):
        """处理放下事件"""
        try:
            source_row = int(event.mimeData().text().split(":")[1])
        except (ValueError, IndexError):
            event.ignore()
            return

        target_row = self._calc_drop_target(pos)

        if source_row < 0 or source_row >= len(self._rows):
            event.ignore()
            return

        if target_row < 0:
            target_row = 0
        if target_row > len(self._rows):
            target_row = len(self._rows)

        # 计算实际插入位置
        insert_pos = target_row
        if insert_pos > source_row:
            insert_pos -= 1

        if source_row == insert_pos:
            event.ignore()
            return

        # 移动数据
        file_path = self._rows.pop(source_row)
        self._rows.insert(insert_pos, file_path)

        # 移动控件
        widget = self._row_widgets.pop(source_row)
        self._row_widgets.insert(insert_pos, widget)

        # 重新排列布局
        for i, w in enumerate(self._row_widgets):
            w.update_index(i)
            self.content_layout.insertWidget(i, w)

        # 更新选中
        if 0 <= self._selected_index < len(self._row_widgets):
            self._row_widgets[self._selected_index].set_selected(False)

        self._selected_index = insert_pos
        self._row_widgets[insert_pos].set_selected(True)

        self._drop_indicator_pos = -1
        self.update()
        event.acceptProposedAction()
        self.order_changed.emit()

    def start_row_drag(self, row_index):
        """由行控件调用，开始拖拽"""
        self._drag_index = row_index
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"row:{row_index}")
        drag.setMimeData(mime_data)
        drag.exec_(Qt.MoveAction)
        self._drag_index = -1
        self._drop_indicator_pos = -1
        self.update()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("row:"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("row:"):
            event.acceptProposedAction()
            pos = event.pos()
            target_row = self._calc_drop_target(pos)
            if target_row != self._drop_indicator_pos:
                self._drop_indicator_pos = target_row
                self.update()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._drop_indicator_pos = -1
        self.update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        if not (event.mimeData().hasText() and event.mimeData().text().startswith("row:")):
            event.ignore()
            return

        try:
            source_row = int(event.mimeData().text().split(":")[1])
        except (ValueError, IndexError):
            event.ignore()
            return

        target_row = self._calc_drop_target(event.pos())

        if source_row < 0 or source_row >= len(self._rows):
            event.ignore()
            return

        if target_row < 0:
            target_row = len(self._rows)

        if target_row > len(self._rows):
            target_row = len(self._rows)

        # 计算实际插入位置
        insert_pos = target_row
        if insert_pos > source_row:
            insert_pos -= 1

        if source_row == insert_pos:
            event.ignore()
            return

        # 移动数据
        file_path = self._rows.pop(source_row)
        self._rows.insert(insert_pos, file_path)

        # 移动控件
        widget = self._row_widgets.pop(source_row)
        self._row_widgets.insert(insert_pos, widget)

        # 重新排列布局
        for i, w in enumerate(self._row_widgets):
            w.update_index(i)
            self.content_layout.insertWidget(i, w)

        # 更新选中
        if 0 <= self._selected_index < len(self._row_widgets):
            self._row_widgets[self._selected_index].set_selected(False)

        self._selected_index = insert_pos
        self._row_widgets[insert_pos].set_selected(True)

        self._drop_indicator_pos = -1
        self.update()
        event.acceptProposedAction()
        self.order_changed.emit()

    def _calc_drop_target(self, pos):
        """计算拖拽目标行索引，pos 是本表控件坐标系"""
        # 转换为内容区坐标系
        content_pos = self.content_widget.mapFrom(self, pos)
        scroll_offset = self.scroll_area.verticalScrollBar().value()
        adjusted_y = content_pos.y() + scroll_offset

        row_height = 26
        if adjusted_y < 0:
            return 0

        target = adjusted_y // row_height

        # 上半部分插到当前行前，下半部分插到下一行前
        row_top = target * row_height
        if adjusted_y - row_top > row_height // 2:
            target += 1

        return target

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._drop_indicator_pos >= 0:
            painter = QPainter(self)
            painter.setPen(QPen(QColor("#409eff"), 2, Qt.SolidLine))

            # 计算指示器在本表控件坐标系中的位置
            content_y = self._drop_indicator_pos * 26
            content_y -= self.scroll_area.verticalScrollBar().value()
            # 转换到本表坐标
            indicator_pos = self.content_widget.mapTo(self, QPoint(0, content_y))
            y = indicator_pos.y()

            if y >= 0 and y <= self.height():
                painter.drawLine(8, y, self.width() - 8 - SCROLLBAR_WIDTH, y)

    def clear(self):
        while self._row_widgets:
            widget = self._row_widgets.pop()
            widget.deleteLater()
        self._rows.clear()
        self._selected_index = -1

    def add_row(self, file_path):
        row_index = len(self._rows)
        self._rows.append(file_path)

        row_widget = TableRowWidget(file_path, row_index)
        row_widget.clicked.connect(self._on_row_clicked)
        row_widget.drag_started.connect(self.start_row_drag)
        self._row_widgets.append(row_widget)

        self.content_layout.insertWidget(len(self._row_widgets) - 1, row_widget)

        # 应用当前列宽
        self._apply_column_widths_to_row(row_widget)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_column_widths()

    def _update_column_widths(self):
        """统一计算并更新所有列的宽度"""
        total_width = self.content_widget.width()
        if total_width <= 0:
            return

        remaining = total_width - COL_INDEX_WIDTH - COL_STATUS_WIDTH
        if remaining < 20:
            remaining = 20

        # 文件名占 3/7，路径占 4/7
        name_width = int(remaining * 3 / 7)
        path_width = remaining - name_width

        # 更新表头
        self.h_name.setFixedWidth(name_width)
        self.h_path.setFixedWidth(path_width)

        # 更新所有行
        for row in self._row_widgets:
            self._apply_column_widths_to_row(row, name_width, path_width)

    def _apply_column_widths_to_row(self, row_widget, name_width=None, path_width=None):
        if name_width is None or path_width is None:
            total_width = self.content_widget.width()
            if total_width <= 0:
                return
            remaining = total_width - COL_INDEX_WIDTH - COL_STATUS_WIDTH
            if remaining < 20:
                remaining = 20
            name_width = int(remaining * 3 / 7)
            path_width = remaining - name_width
        row_widget.set_column_widths(name_width, path_width)

    def remove_row(self, index):
        if 0 <= index < len(self._rows):
            self._rows.pop(index)
            widget = self._row_widgets.pop(index)
            widget.deleteLater()

            for i, w in enumerate(self._row_widgets):
                w.update_index(i)

            if self._selected_index == index:
                self._selected_index = -1
            elif self._selected_index > index:
                self._selected_index -= 1

    def set_status(self, index, text, success=True):
        if 0 <= index < len(self._row_widgets):
            self._row_widgets[index].set_status(text, success)

    def get_row_count(self):
        return len(self._rows)

    def get_row_data(self, index):
        if 0 <= index < len(self._rows):
            return self._rows[index]
        return None

    def get_all_data(self):
        return self._rows.copy()

    def _on_row_clicked(self, row_index):
        if self._selected_index != row_index:
            if 0 <= self._selected_index < len(self._row_widgets):
                self._row_widgets[self._selected_index].set_selected(False)
            self._selected_index = row_index
            self._row_widgets[row_index].set_selected(True)


class VideoWorker(QThread):
    progress_updated = pyqtSignal(int, str)
    file_finished = pyqtSignal(int, bool, str)
    all_finished = pyqtSignal()
    status_updated = pyqtSignal(str)
    current_progress_updated = pyqtSignal(int)

    def __init__(self, files, mode, target_format, output_folder, overwrite_source, fix_output_folder,
                 cut_hour=0, cut_minute=0, cut_second=0, cut_frame=0, cut_overwrite_source=False, cut_output_folder="",
                 merge_filename="合并视频", merge_format="MP4", merge_output_folder="", merge_use_gpu=False):
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
        self.merge_filename = merge_filename
        self.merge_format = merge_format
        self.merge_output_folder = merge_output_folder
        self.merge_use_gpu = merge_use_gpu
        self._is_running = True
        self._current_process = None

    def stop(self):
        """停止当前任务"""
        print("[Stop] 收到停止请求，设置停止标志...")
        self._is_running = False
        if self._current_process:
            print(f"[Stop] 正在终止进程 PID={self._current_process.pid}...")
            self._terminate_process(self._current_process)
            print("[Stop] 进程终止命令已发送")
        else:
            print("[Stop] 当前没有运行中的进程")

    def run(self):
        if self.mode == 3:
            # 合并模式：所有文件作为整体处理
            self._process_merge()
            return

        total = len(self.files)
        for i, file_path in enumerate(self.files):
            if not self._is_running:
                break
            self.progress_updated.emit(i, f"处理中: {Path(file_path).name}")

            try:
                success = self._process_single_file(file_path)
                self.file_finished.emit(i, success, "成功" if success else "失败")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                self.file_finished.emit(i, False, f"错误: {str(e)}")

        self.all_finished.emit()

    def _run_ffmpeg_cmd(self, cmd, duration, progress_prefix="处理中"):
        """执行FFmpeg命令，支持停止，返回 (success, stderr_lines)
        
        Args:
            cmd: FFmpeg命令
            duration: 总时长（秒），用于计算进度
            progress_prefix: 进度提示前缀
        Returns:
            (success, stderr_lines)
        """
        import subprocess
        import threading
        import time

        process = subprocess.Popen(
            cmd,
            shell=True,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            encoding='utf-8',
            errors='replace'
        )
        self._current_process = process

        last_percent = 0
        stderr_lines = []
        stderr_lock = threading.Lock()

        def read_stderr():
            try:
                for line in process.stderr:
                    with stderr_lock:
                        stderr_lines.append(line.strip())
            except:
                pass

        # 启动线程读取 stderr
        reader_thread = threading.Thread(target=read_stderr, daemon=True)
        reader_thread.start()

        while True:
            # 检查停止标志
            if not self._is_running:
                self._terminate_process(process)
                reader_thread.join(timeout=1)
                break

            # 检查进程是否结束
            if process.poll() is not None:
                reader_thread.join(timeout=1)
                break

            # 解析进度（从已读取的行中）
            with stderr_lock:
                for line in stderr_lines:
                    if 'time=' in line and duration > 0 and last_percent < 99:
                        try:
                            time_str = line.split('time=')[1].split()[0]
                            parts = time_str.split(':')
                            if len(parts) == 3:
                                current_time = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                            elif len(parts) == 2:
                                current_time = float(parts[0]) * 60 + float(parts[1])
                            else:
                                current_time = float(parts[0])
                            
                            percent = min(int((current_time / duration) * 100), 99)
                            if percent > last_percent:
                                last_percent = percent
                                self.current_progress_updated.emit(percent)
                                self.progress_updated.emit(percent, f"{progress_prefix} ({percent}%)")
                        except (ValueError, IndexError):
                            pass

            time.sleep(0.1)

        self._current_process = None
        # 再次确保进程终止
        if process.poll() is None:
            self._terminate_process(process)
        
        # 等待线程结束
        reader_thread.join(timeout=1)
        
        success = process.returncode == 0 and self._is_running
        return success, stderr_lines

    def _terminate_process(self, process):
        """安全终止进程（Windows 下处理 shell=True 的子进程问题）"""
        print(f"[Terminate] 开始终止进程 PID={process.pid}")
        try:
            if sys.platform == 'win32':
                # Windows 下 shell=True 时，terminate 只杀 cmd.exe，不杀 ffmpeg
                # 使用 taskkill 递归杀死整个进程树
                try:
                    import subprocess as sp
                    result = sp.run(
                        ['taskkill', '/F', '/T', '/PID', str(process.pid)],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    print(f"[Terminate] taskkill 返回码: {result.returncode}")
                    if result.stdout:
                        print(f"[Terminate] taskkill stdout: {result.stdout.strip()}")
                    if result.stderr:
                        print(f"[Terminate] taskkill stderr: {result.stderr.strip()}")
                except Exception as e:
                    print(f"[Terminate] taskkill 异常: {e}")
                    try:
                        process.terminate()
                    except:
                        pass
            else:
                try:
                    process.terminate()
                except:
                    pass
        except Exception as e:
            print(f"[Terminate] 终止异常: {e}")
        
        time.sleep(0.5)
        
        try:
            if process.poll() is None:
                print("[Terminate] 进程仍在运行，尝试再次终止...")
                if sys.platform == 'win32':
                    try:
                        import subprocess as sp
                        result = sp.run(
                            ['taskkill', '/F', '/T', '/PID', str(process.pid)],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        print(f"[Terminate] 第二次 taskkill 返回码: {result.returncode}")
                    except Exception as e:
                        print(f"[Terminate] 第二次 taskkill 异常: {e}")
                        try:
                            process.kill()
                        except:
                            pass
                else:
                    try:
                        process.kill()
                    except:
                        pass
        except Exception as e:
            print(f"[Terminate] 二次终止异常: {e}")
        
        time.sleep(0.2)
        try:
            if process.poll() is not None:
                print(f"[Terminate] 进程已终止，返回码: {process.returncode}")
            else:
                print("[Terminate] 警告: 进程仍未终止")
        except:
            pass

    def _process_merge(self):
        """处理合并视频"""
        self.status_updated.emit("正在合并视频...")

        input_files = self.files
        if not input_files:
            self.status_updated.emit("没有可合并的视频文件！")
            self.all_finished.emit()
            return

        output_dir = Path(self.merge_output_folder) if self.merge_output_folder else Path(self.output_folder)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_ext = self.merge_format.lower()
        output_path = str(output_dir / f"{self.merge_filename}.{output_ext}")

        if Path(output_path).exists():
            Path(output_path).unlink()

        self.progress_updated.emit(0, f"正在合并 {len(input_files)} 个视频...")

        import subprocess

        # 检查 GPU 是否可用
        actual_use_gpu = self.merge_use_gpu
        if self.merge_use_gpu:
            gpu_available, gpu_msg = utils.FFmpegCommand.check_gpu_available()
            if not gpu_available:
                print(f"[Merge] GPU 加速不可用: {gpu_msg}")
                print(f"[Merge] 自动回退到软件编码 (libx264)")
                self.status_updated.emit(f"GPU加速不可用（{gpu_msg}），使用软件编码...")
                actual_use_gpu = False

        # GPU模式下使用两步法：先转码为统一规格的TS，再合并
        if actual_use_gpu:
            # ========== 第一步：将每个视频转码为统一规格的临时TS文件 ==========
            temp_dir = str(output_dir)
            step1_results = utils.FFmpegCommand.merge_videos_safe_step1(
                input_files, temp_dir, actual_use_gpu
            )
            
            temp_files = []
            all_success = True
            
            for i, (temp_file, cmd, has_audio) in enumerate(step1_results):
                if not self._is_running:
                    break
                self.status_updated.emit(f"准备中: 转码第 {i+1}/{len(step1_results)} 个视频...")
                self.progress_updated.emit(0, f"转码中: 第 {i+1}/{len(step1_results)} 个视频")
                
                print(f"[Merge Step1] 处理第 {i+1} 个视频: {Path(input_files[i]).name}")
                print(f"[Merge Step1] 有音频流: {has_audio}")
                print(f"[Merge Step1] 命令: {cmd}")
                
                file_duration = self._get_video_duration(input_files[i])
                success, stderr_lines = self._run_ffmpeg_cmd(
                    cmd, file_duration, f"转码中: 第 {i+1}/{len(step1_results)} 个视频"
                )
                
                if not success:
                    all_success = False
                    if self._is_running:
                        print(f"[Merge Step1 ERROR] 第 {i+1} 个视频转码失败")
                        print(f"[Merge Step1 ERROR] 命令: {cmd}")
                        print(f"[Merge Step1 ERROR] 最后30行stderr:")
                        for line in stderr_lines[-30:]:
                            print(f"  {line}")
                    break
                
                print(f"[Merge Step1] 第 {i+1} 个视频转码成功")
                temp_files.append(temp_file)
            
            if not all_success:
                # 清理临时文件
                for f in temp_files:
                    try:
                        Path(f).unlink(missing_ok=True)
                    except:
                        pass
                self.progress_updated.emit(0, "合并失败（转码阶段）")
                self.file_finished.emit(0, False, "合并失败")
                self.status_updated.emit("合并失败")
                self.all_finished.emit()
                return
            
            # ========== 第二步：使用concat demuxer合并所有临时TS文件 ==========
            self.status_updated.emit("合并中: 正在合并视频...")
            self.progress_updated.emit(0, "合并中...")
            
            cmd, filelist_path = utils.FFmpegCommand.merge_videos_safe_step2(
                temp_files, output_path, self.merge_format, actual_use_gpu
            )
            
            # 计算总时长
            total_duration = 0.0
            for f in temp_files:
                d = self._get_video_duration(f)
                if d > 0:
                    total_duration += d
            
            success, stderr_lines = self._run_ffmpeg_cmd(cmd, total_duration, "合并中")
            
            # 清理临时文件
            for f in temp_files:
                try:
                    Path(f).unlink(missing_ok=True)
                except:
                    pass
            if filelist_path:
                try:
                    Path(filelist_path).unlink(missing_ok=True)
                except:
                    pass
            
            if success:
                self.current_progress_updated.emit(100)
                self.progress_updated.emit(100, f"合并完成: {Path(output_path).name}")
                self.file_finished.emit(0, True, f"合并成功: {Path(output_path).name}")
                self.status_updated.emit("合并完成！")
            else:
                if self._is_running:
                    print(f"[Merge Step2 ERROR] FFmpeg command failed")
                    print(f"[Merge Step2 ERROR] Command: {cmd}")
                    print(f"[Merge Step2 ERROR] Last 20 lines of stderr:")
                    for line in stderr_lines[-20:]:
                        print(f"  {line}")
                self.progress_updated.emit(0, "合并失败")
                self.file_finished.emit(0, False, "合并失败")
                self.status_updated.emit("合并失败")
        else:
            # 非GPU模式（或GPU不可用回退）：使用两步法合并（软件编码）
            # 两步法更稳定，能处理参数不一致的视频
            temp_dir = str(output_dir)
            step1_results = utils.FFmpegCommand.merge_videos_safe_step1(
                input_files, temp_dir, actual_use_gpu
            )
            
            temp_files = []
            all_success = True
            
            for i, (temp_file, cmd, has_audio) in enumerate(step1_results):
                if not self._is_running:
                    break
                self.status_updated.emit(f"准备中: 转码第 {i+1}/{len(step1_results)} 个视频...")
                self.progress_updated.emit(0, f"转码中: 第 {i+1}/{len(step1_results)} 个视频")
                
                print(f"[Merge Step1] 处理第 {i+1} 个视频: {Path(input_files[i]).name}")
                print(f"[Merge Step1] 有音频流: {has_audio}")
                
                file_duration = self._get_video_duration(input_files[i])
                success, stderr_lines = self._run_ffmpeg_cmd(
                    cmd, file_duration, f"转码中: 第 {i+1}/{len(step1_results)} 个视频"
                )
                
                if not success:
                    all_success = False
                    if self._is_running:
                        print(f"[Merge Step1 ERROR] 第 {i+1} 个视频转码失败")
                        print(f"[Merge Step1 ERROR] 命令: {cmd}")
                        print(f"[Merge Step1 ERROR] 最后30行stderr:")
                        for line in stderr_lines[-30:]:
                            print(f"  {line}")
                    break
                
                print(f"[Merge Step1] 第 {i+1} 个视频转码成功")
                temp_files.append(temp_file)
            
            if not all_success:
                for f in temp_files:
                    try:
                        Path(f).unlink(missing_ok=True)
                    except:
                        pass
                self.progress_updated.emit(0, "合并失败（转码阶段）")
                self.file_finished.emit(0, False, "合并失败")
                self.status_updated.emit("合并失败")
                self.all_finished.emit()
                return
            
            # 第二步：合并
            self.status_updated.emit("合并中: 正在合并视频...")
            self.progress_updated.emit(0, "合并中...")
            
            cmd, filelist_path = utils.FFmpegCommand.merge_videos_safe_step2(
                temp_files, output_path, self.merge_format, actual_use_gpu
            )
            
            total_duration = 0.0
            for f in temp_files:
                d = self._get_video_duration(f)
                if d > 0:
                    total_duration += d
            
            success, stderr_lines = self._run_ffmpeg_cmd(cmd, total_duration, "合并中")
            
            # 清理临时文件
            for f in temp_files:
                try:
                    Path(f).unlink(missing_ok=True)
                except:
                    pass
            if filelist_path:
                try:
                    Path(filelist_path).unlink(missing_ok=True)
                except:
                    pass
            
            if success:
                self.current_progress_updated.emit(100)
                self.progress_updated.emit(100, f"合并完成: {Path(output_path).name}")
                self.file_finished.emit(0, True, f"合并成功: {Path(output_path).name}")
                self.status_updated.emit("合并完成！")
            else:
                if self._is_running:
                    print(f"[Merge Step2 ERROR] FFmpeg command failed")
                    print(f"[Merge Step2 ERROR] Command: {cmd}")
                    print(f"[Merge Step2 ERROR] Last 20 lines of stderr:")
                    for line in stderr_lines[-20:]:
                        print(f"  {line}")
                self.progress_updated.emit(0, "合并失败")
                self.file_finished.emit(0, False, "合并失败")
                self.status_updated.emit("合并失败")

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
        import threading
        import time

        process = subprocess.Popen(
            cmd,
            shell=True,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            encoding='utf-8',
            errors='replace'
        )
        self._current_process = process

        duration = self._get_video_duration(input_file)
        stderr_lines = []
        stderr_lock = threading.Lock()

        def read_stderr():
            try:
                for line in process.stderr:
                    with stderr_lock:
                        stderr_lines.append(line.strip())
            except:
                pass

        reader_thread = threading.Thread(target=read_stderr, daemon=True)
        reader_thread.start()

        while True:
            if not self._is_running:
                self._terminate_process(process)
                reader_thread.join(timeout=1)
                break

            if process.poll() is not None:
                reader_thread.join(timeout=1)
                break

            with stderr_lock:
                for line in stderr_lines:
                    if 'time=' in line:
                        match = re.search(r'time=(\d+:\d+:\d+\.\d+)', line)
                        if match:
                            time_str = match.group(1)
                            current_time = self._parse_time(time_str)
                            if duration > 0:
                                percent = min(100, int((current_time / duration) * 100))
                                self.status_updated.emit(f"处理中... {percent}% ({time_str})")
                                self.current_progress_updated.emit(percent)

            time.sleep(0.1)

        self._current_process = None
        if process.poll() is None:
            self._terminate_process(process)
        reader_thread.join(timeout=1)
        return process.returncode == 0 and self._is_running

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
        # 替换 tableWidget 为自定义表格
        old_table = self.ui.tableWidget
        layout = old_table.parentWidget().layout()
        index = layout.indexOf(old_table)

        new_table = CustomTableWidget(self)
        new_table.setObjectName(old_table.objectName())
        new_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        old_table.deleteLater()
        layout.insertWidget(index, new_table)
        self.ui.tableWidget = new_table

        # 设置各区域尺寸策略
        self.ui.groupBox_files.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ui.tabWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ui.groupBox_progress.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ui.groupBox_progress.setMaximumHeight(120)

        self.ui.lineEdit_output.setText(config.config.output_folder)
        self.ui.lineEdit_fix_output.setText(config.config.fix_output_folder)
        self.ui.lineEdit_cut_output.setText(config.config.cut_output_folder)
        self.ui.lineEdit_merge_output.setText(config.config.merge_output_folder)
        self.ui.checkBox_merge_gpu.setChecked(True)
        self.ui.spinBox_hour.setValue(config.config.cut_hour)
        self.ui.spinBox_minute.setValue(config.config.cut_minute)
        self.ui.spinBox_second.setValue(config.config.cut_second)
        self.ui.spinBox_frame.setValue(config.config.cut_frame)
        self.ui.checkBox_cut_intro_overwrite.setChecked(config.config.cut_overwrite_source)
        self._update_cut_output_visibility()
        self.setMinimumSize(600, 500)
        self.resize(800, 630)

        # 设置停止按钮为红色
        self.ui.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)

    def _setup_connections(self):
        self.ui.btn_add_files.clicked.connect(self._on_add_files)
        self.ui.btn_delete_selected.clicked.connect(self._on_delete_selected)
        self.ui.btn_clear_list.clicked.connect(self._on_clear_list)
        self.ui.btn_browse_output.clicked.connect(self._on_browse_output)
        self.ui.btn_browse_fix_output.clicked.connect(self._on_browse_fix_output)
        self.ui.btn_browse_cut_output.clicked.connect(self._on_browse_cut_output)
        self.ui.btn_browse_merge_output.clicked.connect(self._on_browse_merge_output)
        self.ui.btn_start.clicked.connect(self._on_start)
        self.ui.btn_stop.clicked.connect(self._on_stop)
        self.ui.tabWidget.currentChanged.connect(self._on_tab_changed)
        self.ui.checkBox_overwrite.stateChanged.connect(self._on_overwrite_changed)
        self.ui.checkBox_cut_intro_overwrite.stateChanged.connect(self._on_cut_overwrite_changed)
        self.ui.spinBox_hour.valueChanged.connect(self._on_cut_time_changed)
        self.ui.spinBox_minute.valueChanged.connect(self._on_cut_time_changed)
        self.ui.spinBox_second.valueChanged.connect(self._on_cut_time_changed)
        self.ui.spinBox_frame.valueChanged.connect(self._on_cut_time_changed)

    def _setup_drag_drop(self):
        self.setAcceptDrops(True)
        self.ui.tableWidget.order_changed.connect(self._on_order_changed)

    def _on_order_changed(self):
        self._sync_video_files_order()

    def _sync_video_files_order(self):
        config.config.video_files = self.ui.tableWidget.get_all_data()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self._on_delete_selected()
        super().keyPressEvent(event)

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
        self.ui.tableWidget.add_row(file_path)

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
        selected_index = self.ui.tableWidget._selected_index

        if selected_index < 0:
            QMessageBox.information(self, "提示", "请先选择要删除的视频文件")
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除选中的 1 个视频吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            file_path = self.ui.tableWidget.get_row_data(selected_index)
            if file_path and file_path in config.config.video_files:
                config.config.video_files.remove(file_path)
            self.ui.tableWidget.remove_row(selected_index)
            self._update_source_format_display()

    def _on_clear_list(self):
        self.ui.tableWidget.clear()
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

    def _on_browse_merge_output(self):
        folder = utils.FileDialog.select_folder(
            self, "选择输出文件夹", config.config.merge_output_folder
        )
        if folder:
            config.config.merge_output_folder = folder
            self.ui.lineEdit_merge_output.setText(folder)

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
        merge_filename = "合并视频"
        merge_format = "MP4"
        merge_use_gpu = False

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
        elif config.config.mode == 2:
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
        else:  # mode == 3, 合并视频
            merge_format = self.ui.comboBox_merge_format.currentText()
            merge_filename = self.ui.lineEdit_merge_filename.text().strip()
            merge_use_gpu = self.ui.checkBox_merge_gpu.isChecked()
            if not merge_filename:
                merge_filename = "合并视频"
            if not config.config.merge_output_folder:
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
            cut_output_folder,
            merge_filename,
            merge_format,
            config.config.merge_output_folder,
            merge_use_gpu
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
        total = self.ui.tableWidget.get_row_count()
        progress = int((index / total) * 100) if total > 0 else 0
        self.ui.progressBar_total.setValue(progress)
        self.ui.label_status.setText(status_text)

    def _on_file_finished(self, index, success, status_text):
        self.ui.tableWidget.set_status(index, status_text, success)

    def _on_all_finished(self):
        self.ui.progressBar.setValue(100)
        self.ui.progressBar_total.setValue(100)
        self.ui.label_status.setText("处理完成！")
        self._set_ui_enabled(True)

    def _on_stop(self):
        """停止当前任务"""
        print("[UI] 点击了停止按钮")
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            print("[UI] worker 正在运行，调用 stop()...")
            self.worker.stop()
            self.ui.label_status.setText("正在停止...")
            self.ui.btn_stop.setEnabled(False)
        else:
            print("[UI] worker 未运行或不存在")

    def _set_ui_enabled(self, enabled):
        self.ui.btn_add_files.setEnabled(enabled)
        self.ui.btn_delete_selected.setEnabled(enabled)
        self.ui.btn_clear_list.setEnabled(enabled)
        self.ui.btn_start.setEnabled(enabled)
        self.ui.btn_stop.setEnabled(not enabled)
        self.ui.btn_browse_output.setEnabled(enabled)
        self.ui.btn_browse_fix_output.setEnabled(enabled)
        self.ui.btn_browse_cut_output.setEnabled(enabled)
        self.ui.tabWidget.setEnabled(enabled)
        self.ui.comboBox_target.setEnabled(enabled)
        self.ui.checkBox_overwrite.setEnabled(enabled)
        self.ui.lineEdit_fix_output.setEnabled(enabled and not self.ui.checkBox_overwrite.isChecked())
        self.ui.checkBox_cut_intro_overwrite.setEnabled(enabled)
        self.ui.lineEdit_cut_output.setEnabled(enabled and not self.ui.checkBox_cut_intro_overwrite.isChecked())
        self.ui.spinBox_hour.setEnabled(enabled)
        self.ui.spinBox_minute.setEnabled(enabled)
        self.ui.spinBox_second.setEnabled(enabled)
        self.ui.spinBox_frame.setEnabled(enabled)
        self.ui.comboBox_merge_format.setEnabled(enabled)
        self.ui.lineEdit_merge_filename.setEnabled(enabled)
        self.ui.lineEdit_merge_output.setEnabled(enabled)
        self.ui.btn_browse_merge_output.setEnabled(enabled)
        self.ui.checkBox_merge_gpu.setEnabled(enabled)