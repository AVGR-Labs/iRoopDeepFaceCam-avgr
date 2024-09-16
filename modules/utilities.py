import glob
import mimetypes
import os
import platform
import shutil
import ssl
import subprocess
import urllib
from pathlib import Path
from typing import List, Any
from tqdm import tqdm

import modules.globals

TEMP_FILE = 'temp.mp4'
TEMP_DIRECTORY = 'temp'

# monkey patch ssl for mac
if platform.system().lower() == 'darwin':
    ssl._create_default_https_context = ssl._create_unverified_context


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
    temp_directory_path = get_temp_directory_path(target_path)
    run_ffmpeg(['-i', target_path, '-pix_fmt', 'rgb24', os.path.join(temp_directory_path, '%04d.png')])


def create_video(target_path: str, fps: float = 30.0) -> None:
    temp_output_path = get_temp_output_path(target_path)
    temp_directory_path = get_temp_directory_path(target_path)
    run_ffmpeg(['-r', str(fps), '-i', os.path.join(temp_directory_path, '%04d.png'), '-c:v', modules.globals.video_encoder, '-crf', str(modules.globals.video_quality), '-pix_fmt', 'yuv420p', '-vf', 'colorspace=bt709:iall=bt601-6-625:fast=1', '-y', temp_output_path])


def restore_audio(target_path: str, output_path: str) -> None:
    temp_output_path = get_temp_output_path(target_path)
    done = run_ffmpeg(['-i', temp_output_path, '-i', target_path, '-c:v', 'copy', '-map', '0:v:0', '-map', '1:a:0', '-y', output_path])
    if not done:
        move_temp(target_path, output_path)


def get_temp_frame_paths(target_path: str) -> List[str]:
    temp_directory_path = get_temp_directory_path(target_path)
    return glob.glob((os.path.join(glob.escape(temp_directory_path), '*.png')))


def get_temp_directory_path(target_path: str) -> str:
    target_name, _ = os.path.splitext(os.path.basename(target_path))
    target_directory_path = os.path.dirname(target_path)
    return os.path.join(target_directory_path, TEMP_DIRECTORY, target_name)


def get_temp_output_path(target_path: str) -> str:
    temp_directory_path = get_temp_directory_path(target_path)
    return os.path.join(temp_directory_path, TEMP_FILE)


def normalize_output_path(source_path: str, target_path: str, output_path: str) -> Any:
    if source_path and target_path:
        source_name, _ = os.path.splitext(os.path.basename(source_path))
        target_name, target_extension = os.path.splitext(os.path.basename(target_path))
        if os.path.isdir(output_path):
            return os.path.join(output_path, source_name + '-' + target_name + target_extension)
    return output_path


def create_temp(target_path: str) -> None:
    temp_directory_path = get_temp_directory_path(target_path)
    Path(temp_directory_path).mkdir(parents=True, exist_ok=True)


def move_temp(target_path: str, output_path: str) -> None:
    temp_output_path = get_temp_output_path(target_path)
    if os.path.isfile(temp_output_path):
        if os.path.isfile(output_path):
            os.remove(output_path)
        shutil.move(temp_output_path, output_path)


def clean_temp(target_path: str) -> None:
    temp_directory_path = get_temp_directory_path(target_path)
    parent_directory_path = os.path.dirname(temp_directory_path)
    if not modules.globals.keep_frames and os.path.isdir(temp_directory_path):
        shutil.rmtree(temp_directory_path)
    if os.path.exists(parent_directory_path) and not os.listdir(parent_directory_path):
        os.rmdir(parent_directory_path)


def has_image_extension(image_path: str) -> bool:
    return image_path.lower().endswith(('png', 'jpg', 'jpeg'))


def is_image(image_path: str) -> bool:
    if image_path and os.path.isfile(image_path):
        mimetype, _ = mimetypes.guess_type(image_path)
        return bool(mimetype and mimetype.startswith('image/'))
    return False


def is_video(video_path: str) -> bool:
    if video_path and os.path.isfile(video_path):
        mimetype, _ = mimetypes.guess_type(video_path)
        return bool(mimetype and mimetype.startswith('video/'))
    return False

def is_valid_file(path: str) -> bool:
    if path and (is_video(path) or is_image(path)):
        return True
    return False

def conditional_download(download_directory_path: str, urls: List[str]) -> None:
    if not os.path.exists(download_directory_path):
        os.makedirs(download_directory_path)
    for url in urls:
        download_file_path = os.path.join(download_directory_path, os.path.basename(url))
        if not os.path.exists(download_file_path):
            request = urllib.request.urlopen(url) # type: ignore[attr-defined]
            total = int(request.headers.get('Content-Length', 0))
            with tqdm(total=total, desc='Downloading', unit='B', unit_scale=True, unit_divisor=1024) as progress:
                urllib.request.urlretrieve(url, download_file_path, reporthook=lambda count, block_size, total_size: progress.update(block_size)) # type: ignore[attr-defined]


def resolve_relative_path(path: str) -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), path))

def debug_message():
    """
    Prints a detailed debug message with the current values of all the key parameters
    from the modules.globals.
    """
    debug_info = {
        "source_folder_path": modules.globals.source_folder_path,
        "target_folder_path": modules.globals.target_folder_path,
        "use_source_folder": modules.globals.use_source_folder,
        "use_target_folder": modules.globals.use_target_folder,
        "use_default_folders": modules.globals.use_default_folders,
        "source_path": modules.globals.source_path,
        "target_path": modules.globals.target_path,
        "output_path": modules.globals.output_path,
        "frame_processors": modules.globals.frame_processors,
        "keep_fps": modules.globals.keep_fps,
        "keep_audio": modules.globals.keep_audio,
        "keep_frames": modules.globals.keep_frames,
        "many_faces": modules.globals.many_faces,
        "nsfw_filter": modules.globals.nsfw_filter,
        "video_encoder": modules.globals.video_encoder,
        "video_quality": modules.globals.video_quality,
        "live_mirror": modules.globals.live_mirror,
        "flip_y": modules.globals.flip_y,
        "flip_x": modules.globals.flip_x,
        "live_resizable": modules.globals.live_resizable,
        "max_memory": modules.globals.max_memory,
        "execution_providers": modules.globals.execution_providers,
        "execution_threads": modules.globals.execution_threads,
        "headless": modules.globals.headless,
        "log_level": modules.globals.log_level,
        "fp_ui": modules.globals.fp_ui,
        "camera_input_combobox": modules.globals.camera_input_combobox,
        "webcam_preview_running": modules.globals.webcam_preview_running,
        "both_faces": modules.globals.both_faces,
        "flip_faces": modules.globals.flip_faces,
        "detect_face_right": modules.globals.detect_face_right,
        "detect_face_right_value": modules.globals.detect_face_right_value,
        "show_target_face_box": modules.globals.show_target_face_box,
        "mouth_mask": modules.globals.mouth_mask,
        "mask_feather_ratio": modules.globals.mask_feather_ratio,
        "mask_down_size": modules.globals.mask_down_size,
        "mask_size": modules.globals.mask_size,
        "show_mouth_mask_box": modules.globals.show_mouth_mask_box,
        "flip_faces_value": modules.globals.flip_faces_value,
        "sticky_face_value": modules.globals.sticky_face_value,
        "use_pseudo_face": modules.globals.use_pseudo_face,
        "pseudo_face_threshold": modules.globals.pseudo_face_threshold,
        "max_pseudo_face_count": modules.globals.max_pseudo_face_count,
        "face_tracking": modules.globals.face_tracking,
        "face_tracking_value": modules.globals.face_tracking_value,
        "target_face1_score": modules.globals.target_face1_score,
        "target_face2_score": modules.globals.target_face2_score,
        "target_face_left_embedding": modules.globals.target_face_left_embedding,
        "target_face_right_embedding": modules.globals.target_face_right_embedding,
        "source_face_left_embedding": modules.globals.source_face_left_embedding,
        "source_face_right_embedding": modules.globals.source_face_right_embedding,
        "target_face": modules.globals.target_face,
        "embedding_weight_size": modules.globals.embedding_weight_size,
        "weight_distribution_size": modules.globals.weight_distribution_size,
        "position_size": modules.globals.position_size,
        "old_embedding_weight": modules.globals.old_embedding_weight,
        "new_embedding_weight": modules.globals.new_embedding_weight,
    }

    # Print the debug message
    print("Debug Information:")
    for key, value in debug_info.items():
        print(f"{key}: {value}")

# Example usage of the debug function
debug_message()
