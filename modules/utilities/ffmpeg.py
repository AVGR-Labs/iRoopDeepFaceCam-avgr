import subprocess
import os
from typing import  List

import modules.globals
import modules.filehandle.path as pwd
def run_ffmpeg(args: List[str]) -> bool:
    commands = ['ffmpeg', '-hide_banner', '-hwaccel', 'auto', '-loglevel', modules.globals.log_level]
    commands.extend(args)
    try:
        subprocess.check_output(commands, stderr=subprocess.STDOUT)
        return True
    except Exception:
        pass
    return False


def detect_fps(target_path: str) -> float:
    command = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'default=noprint_wrappers=1:nokey=1', target_path]
    output = subprocess.check_output(command).decode().strip().split('/')
    try:
        numerator, denominator = map(int, output)
        return numerator / denominator
    except Exception:
        pass
    return 30.0


def extract_frames(target_path: str) -> None:
    temp_directory_path = pwd.get_temp_directory_path(target_path)
    run_ffmpeg(['-i', target_path, '-pix_fmt', 'rgb24', os.path.join(temp_directory_path, '%04d.png')])


def create_video(target_path: str, fps: float = 30.0) -> None:
    temp_output_path = pwd.get_temp_output_path(target_path)
    temp_directory_path = pwd.get_temp_directory_path(target_path)
    run_ffmpeg(['-r', str(fps), '-i', os.path.join(temp_directory_path, '%04d.png'), '-c:v', modules.globals.video_encoder, '-crf', str(modules.globals.video_quality), '-pix_fmt', 'yuv420p', '-vf', 'colorspace=bt709:iall=bt601-6-625:fast=1', '-y', temp_output_path])


def restore_audio(target_path: str, output_path: str) -> None:
    temp_output_path = pwd.get_temp_output_path(target_path)
    done = run_ffmpeg(['-i', temp_output_path, '-i', target_path, '-c:v', 'copy', '-map', '0:v:0', '-map', '1:a:0', '-y', output_path])
    if not done:
        pwd.move_temp(target_path, output_path)

