from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import os


@dataclass
class VideoConfig:
    video_files: List[str] = field(default_factory=list)
    output_folder: str = ""
    fix_output_folder: str = ""
    cut_output_folder: str = ""
    merge_output_folder: str = ""
    mode: int = 0
    option: int = 0
    overwrite_source: bool = True
    cut_overwrite_source: bool = False
    cut_hour: int = 0
    cut_minute: int = 0
    cut_second: int = 0
    cut_frame: int = 0

    def __post_init__(self):
        self._set_default_output_folder()

    @staticmethod
    def get_ffmpeg_path() -> str:
        """获取 ffmpeg 程序路径（支持自定义 Encoder 文件夹）"""
        # 获取当前脚本所在目录
        current_dir = Path(__file__).parent
        encoder_dir = current_dir / "Encoder"
        
        # 检查 Encoder 文件夹中是否有 ffmpeg.exe
        ffmpeg_in_encoder = encoder_dir / "ffmpeg.exe"
        if ffmpeg_in_encoder.exists():
            return str(ffmpeg_in_encoder)
        
        # 如果没有，返回系统 PATH 中的 ffmpeg
        return "ffmpeg"

    def _set_default_output_folder(self):
        if not self.output_folder:
            desktop = self._get_windows_desktop_path()
            if desktop and Path(desktop).exists():
                self.output_folder = desktop
            else:
                # 兜底方案
                desktop = Path.home() / "Desktop"
                if desktop.exists():
                    self.output_folder = str(desktop)
                else:
                    self.output_folder = os.path.expanduser("~")
        if not self.fix_output_folder:
            self.fix_output_folder = self.output_folder
        if not self.cut_output_folder:
            self.cut_output_folder = self.output_folder
        if not self.merge_output_folder:
            self.merge_output_folder = self.output_folder

    def _get_windows_desktop_path(self) -> str:
        """获取Windows用户自定义的桌面路径"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            )
            try:
                value, _ = winreg.QueryValueEx(key, "Desktop")
                # 展开环境变量（如 %USERPROFILE%）
                expanded = os.path.expandvars(value)
                # 处理路径中可能存在的引号
                expanded = expanded.strip('"')
                if Path(expanded).exists():
                    return expanded
            finally:
                winreg.CloseKey(key)
        except:
            pass
        return ""

    @property
    def has_files(self) -> bool:
        return len(self.video_files) > 0

    def get_output_path(self, input_path: str, mode: int, overwrite: Optional[bool] = None, output_dir: Optional[str] = None) -> str:
        input_file = Path(input_path)
        if mode == 0:
            output_dir_path = Path(output_dir or self.output_folder)
            output_dir_path.mkdir(parents=True, exist_ok=True)
            return str(output_dir_path / input_file.name)
        elif mode == 1:
            overwrite_flag = overwrite if overwrite is not None else self.overwrite_source
            if overwrite_flag:
                return input_path
            else:
                output_dir_path = Path(output_dir or self.fix_output_folder)
                output_dir_path.mkdir(parents=True, exist_ok=True)
                new_name = f"{input_file.stem}-已修复{input_file.suffix}"
                return str(output_dir_path / new_name)
        else:  # mode == 2, 去除片头
            overwrite_flag = overwrite if overwrite is not None else self.cut_overwrite_source
            if overwrite_flag:
                return input_path
            else:
                output_dir_path = Path(output_dir or self.cut_output_folder)
                output_dir_path.mkdir(parents=True, exist_ok=True)
                base_name = input_file.stem
                suffix = input_file.suffix
                new_name = f"{base_name}-去除片头{suffix}"
                # 检查是否重名，如果重名则添加序号
                counter = 1
                while (output_dir_path / new_name).exists():
                    new_name = f"{base_name}-去除片头{counter}{suffix}"
                    counter += 1
                return str(output_dir_path / new_name)


config = VideoConfig()
