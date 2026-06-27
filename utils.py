import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List

from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QFileInfo


class FileDialog:
    @staticmethod
    def select_files(parent, title: str, file_filter: str = "All Files (*)") -> List[str]:
        files, _ = QFileDialog.getOpenFileNames(
            parent, title, "", file_filter
        )
        return files

    @staticmethod
    def select_folder(parent, title: str, default_path: str = "") -> Optional[str]:
        folder = QFileDialog.getExistingDirectory(
            parent, title, default_path,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        return folder if folder else None


class FFmpegCommand:
    COPY_CODEC_TEMPLATE = 'ffmpeg -y -i "{input}" -vcodec copy -acodec copy "{output}"'
    FIX_MP4_INDEX_TEMPLATE = 'ffmpeg -y -i "{input}" -c:v copy -c:a copy "{output}"'

    SUPPORTED_FORMATS = ['mp4', 'ts', 'flv', 'mkv']

    @classmethod
    def generate(cls, input_path: str, target_format: str) -> Optional[str]:
        input_file = Path(input_path)
        output_path = str(input_file.parent / f"{input_file.stem}.{target_format.lower()}")
        return cls.COPY_CODEC_TEMPLATE.format(input=input_path, output=output_path)

    @classmethod
    def generate_with_output_dir(cls, input_path: str, target_format: str, output_dir: str) -> Optional[str]:
        input_file = Path(input_path)
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir_path / f"{input_file.stem}.{target_format.lower()}")
        return cls.COPY_CODEC_TEMPLATE.format(input=input_path, output=output_path)

    @classmethod
    def fix_mp4_index(cls, input_path: str, output_path: str) -> str:
        return cls.FIX_MP4_INDEX_TEMPLATE.format(input=input_path, output=output_path)

    @classmethod
    def cut_intro(cls, input_path: str, output_path: str, hours: int, minutes: int, seconds: int, frames: int) -> str:
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{frames:03d}"
        return f'ffmpeg -i "{input_path}" -ss {time_str} -c:v h264_nvenc -preset fast -cq 18 -c:a aac -b:a 192k -async 1 -avoid_negative_ts make_zero -y "{output_path}"'


class CommandExecutor:
    @staticmethod
    def execute(cmd: str) -> Tuple[bool, str]:
        try:
            print(f"Executing command: {cmd}")
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                check=False
            )
            if result.returncode == 0:
                print("Command executed successfully")
                return True, result.stdout
            else:
                print(f"Command failed with code {result.returncode}")
                print(f"Error: {result.stderr}")
                return False, result.stderr
        except Exception as e:
            print(f"Error executing command: {e}")
            return False, str(e)


class FileManager:
    @staticmethod
    def delete(file_path: str) -> bool:
        path = Path(file_path)
        if not path.exists():
            print(f"File does not exist: {file_path}")
            return False
        try:
            path.unlink()
            print(f"File deleted: {file_path}")
            return True
        except OSError as e:
            print(f"Error deleting file {file_path}: {e}")
            return False

    @staticmethod
    def rename(old_path: str, new_path: str) -> bool:
        old_file = Path(old_path)
        new_file = Path(new_path)
        if not old_file.exists():
            print(f"Source file does not exist: {old_path}")
            return False
        if new_file.exists():
            print(f"Target file already exists: {new_path}")
            return False
        try:
            old_file.rename(new_file)
            print(f"File renamed: {old_path} -> {new_path}")
            return True
        except OSError as e:
            print(f"Error renaming file: {e}")
            return False

    @staticmethod
    def get_temp_path(file_path: str) -> str:
        path = Path(file_path)
        temp_name = f"{path.stem}_temp{path.suffix}"
        return str(path.parent / temp_name)

    @staticmethod
    def get_file_extension(file_path: str) -> str:
        return Path(file_path).suffix.lower().lstrip('.')
