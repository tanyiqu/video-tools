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

    def _set_default_output_folder(self):
        if not self.output_folder:
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
