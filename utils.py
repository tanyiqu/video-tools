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

    @classmethod
    def merge_videos(cls, input_files: List[str], output_path: str, target_format: str, use_gpu: bool = False) -> Tuple[str, str]:
        """生成合并视频的命令，返回 (cmd, filelist_path)
        
        Args:
            input_files: 输入文件列表
            output_path: 输出文件路径
            target_format: 目标格式 (MP4/TS/FLV/MKV)
            use_gpu: 是否使用NVIDIA GPU加速
        """
        # 创建临时文件列表
        temp_dir = Path(output_path).parent
        filelist_path = temp_dir / "filelist.txt"

        with open(filelist_path, 'w', encoding='utf-8') as f:
            for file_path in input_files:
                # 使用正斜杠，Windows上FFmpeg可以处理
                normalized_path = file_path.replace('\\', '/')
                f.write(f"file '{normalized_path}'\n")

        # 选择编码器
        if use_gpu:
            video_encoder = 'h264_nvenc'
            audio_encoder = 'aac'
        else:
            video_encoder = 'libx264'
            audio_encoder = 'aac'

        # 根据目标格式选择编码参数
        if target_format.lower() == 'mp4':
            if use_gpu:
                cmd = f'ffmpeg -y -f concat -safe 0 -i "{filelist_path}" -c:v {video_encoder} -preset fast -cq 23 -c:a {audio_encoder} -b:a 192k -strict experimental "{output_path}"'
            else:
                cmd = f'ffmpeg -y -f concat -safe 0 -i "{filelist_path}" -c:v {video_encoder} -crf 23 -preset fast -c:a {audio_encoder} -b:a 192k -strict experimental "{output_path}"'
        elif target_format.lower() == 'ts':
            # TS格式使用mpeg2video
            cmd = f'ffmpeg -y -f concat -safe 0 -i "{filelist_path}" -c:v mpeg2video -crf 23 -c:a mp2 -b:a 192k "{output_path}"'
        elif target_format.lower() == 'flv':
            if use_gpu:
                cmd = f'ffmpeg -y -f concat -safe 0 -i "{filelist_path}" -c:v {video_encoder} -preset fast -cq 23 -c:a {audio_encoder} -strict experimental "{output_path}"'
            else:
                cmd = f'ffmpeg -y -f concat -safe 0 -i "{filelist_path}" -c:v {video_encoder} -crf 23 -preset fast -c:a {audio_encoder} -strict experimental "{output_path}"'
        elif target_format.lower() == 'mkv':
            if use_gpu:
                cmd = f'ffmpeg -y -f concat -safe 0 -i "{filelist_path}" -c:v {video_encoder} -preset fast -cq 23 -c:a {audio_encoder} "{output_path}"'
            else:
                cmd = f'ffmpeg -y -f concat -safe 0 -i "{filelist_path}" -c:v {video_encoder} -crf 23 -preset fast -c:a {audio_encoder} "{output_path}"'
        else:
            cmd = f'ffmpeg -y -f concat -safe 0 -i "{filelist_path}" -c copy "{output_path}"'

        return cmd, str(filelist_path)

    @classmethod
    def check_gpu_available(cls) -> Tuple[bool, str]:
        """检测 h264_nvenc 编码器是否可用
        
        Returns:
            (available, message) - 是否可用及原因
        """
        try:
            # 使用 ffmpeg -encoders 检查是否有 h264_nvenc
            cmd = 'ffmpeg -encoders 2>&1 | findstr /C:"h264_nvenc"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            if 'h264_nvenc' not in result.stdout:
                return False, "未找到 h264_nvenc 编码器"
            
            # 进一步测试编码器是否能实际工作（尝试编码一个空文件）
            # 使用 nullsrc 生成一帧测试
            test_cmd = 'ffmpeg -y -f lavfi -i nullsrc=s=128x72:duration=0.1 -c:v h264_nvenc -preset fast -f null - 2>&1'
            test_result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            if test_result.returncode != 0:
                # 检查错误信息中是否有驱动版本问题
                stderr = test_result.stdout + test_result.stderr
                if 'Driver does not support' in stderr or 'minimum required Nvidia driver' in stderr:
                    return False, "NVIDIA 驱动版本过低，请升级到 570.0 或更高版本"
                elif 'No NVENC capable devices found' in stderr or 'Cannot allocate memory' in stderr:
                    return False, "未找到支持 NVENC 的 NVIDIA 显卡"
                else:
                    return False, "h264_nvenc 编码器无法正常工作"
            
            return True, "GPU 加速可用"
        except Exception as e:
            return False, f"检测失败: {str(e)}"

    @classmethod
    def merge_videos_safe(cls, input_files: List[str], output_path: str, target_format: str, use_gpu: bool = False) -> Tuple[str, str]:
        """【已弃用】请使用两步法合并
        
        保留此方法仅用于向后兼容。
        """
        return cls.merge_videos_safe_step1(input_files, output_path, target_format, use_gpu)

    @classmethod
    def has_audio_stream(cls, file_path: str) -> bool:
        """检测视频文件是否有音频流"""
        try:
            cmd = f'ffprobe -v error -select_streams a -show_entries stream=codec_type -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            return result.returncode == 0 and result.stdout.strip() == 'audio'
        except:
            return False

    @classmethod
    def merge_videos_safe_step1(cls, input_files: List[str], temp_dir: str, use_gpu: bool = False) -> List[Tuple[str, str, bool]]:
        """第一步：将每个视频转码为统一规格的临时TS文件
        
        Returns:
            List of (temp_file_path, ffmpeg_cmd, has_audio) 对，按顺序
        """
        if use_gpu:
            video_encoder = 'h264_nvenc'
        else:
            video_encoder = 'libx264'
        
        results = []
        for i, f in enumerate(input_files):
            escaped_path = f.replace('\\', '/')
            temp_file = str(Path(temp_dir) / f"temp_merge_{i}.ts")
            
            has_audio = cls.has_audio_stream(f)
            
            if has_audio:
                # 有音频流：正常转码
                cmd = (
                    f'ffmpeg -y -i "{escaped_path}" '
                    f'-c:v {video_encoder} -preset fast -cq 23 '
                    f'-pix_fmt yuv420p -r 30 '
                    f'-c:a aac -b:a 192k -ar 48000 -ac 2 '
                    f'-strict experimental '
                    f'-f mpegts "{temp_file}"'
                )
            else:
                # 没有音频流：生成静音音频
                cmd = (
                    f'ffmpeg -y -i "{escaped_path}" '
                    f'-f lavfi -i anullsrc=r=48000:cl=stereo '
                    f'-c:v {video_encoder} -preset fast -cq 23 '
                    f'-pix_fmt yuv420p -r 30 '
                    f'-c:a aac -b:a 192k '
                    f'-shortest '
                    f'-strict experimental '
                    f'-f mpegts "{temp_file}"'
                )
            
            results.append((temp_file, cmd, has_audio))
        
        return results

    @classmethod
    def merge_videos_safe_step2(cls, temp_files: List[str], output_path: str, target_format: str, use_gpu: bool = False) -> Tuple[str, str]:
        """第二步：使用concat demuxer合并所有临时TS文件
        
        Returns:
            (cmd, filelist_path)
        """
        if use_gpu:
            video_encoder = 'h264_nvenc'
        else:
            video_encoder = 'libx264'
        
        temp_dir = Path(output_path).parent
        filelist_path = temp_dir / "filelist_merge.txt"
        
        # 写入文件列表
        with open(filelist_path, 'w', encoding='utf-8') as f:
            for temp_file in temp_files:
                normalized_path = temp_file.replace('\\', '/')
                f.write(f"file '{normalized_path}'\n")
        
        # 根据目标格式选择编码
        if target_format.lower() == 'mp4':
            cmd = (
                f'ffmpeg -y -f concat -safe 0 -i "{filelist_path}" '
                f'-c:v {video_encoder} -preset fast -cq 23 '
                f'-c:a aac -b:a 192k -strict experimental '
                f'"{output_path}"'
            )
        elif target_format.lower() == 'ts':
            cmd = (
                f'ffmpeg -y -f concat -safe 0 -i "{filelist_path}" '
                f'-c:v mpeg2video -crf 23 '
                f'-c:a mp2 -b:a 192k '
                f'"{output_path}"'
            )
        elif target_format.lower() == 'flv':
            cmd = (
                f'ffmpeg -y -f concat -safe 0 -i "{filelist_path}" '
                f'-c:v {video_encoder} -preset fast -cq 23 '
                f'-c:a aac -strict experimental '
                f'"{output_path}"'
            )
        elif target_format.lower() == 'mkv':
            cmd = (
                f'ffmpeg -y -f concat -safe 0 -i "{filelist_path}" '
                f'-c:v {video_encoder} -preset fast -cq 23 '
                f'-c:a aac '
                f'"{output_path}"'
            )
        else:
            cmd = f'ffmpeg -y -f concat -safe 0 -i "{filelist_path}" -c copy "{output_path}"'
        
        return cmd, str(filelist_path)


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
