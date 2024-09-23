
from typing import Callable, Tuple
import cv2
from PIL import Image, ImageOps
import customtkinter as ctk

from modules.utilities.frame import get_video_frame, get_video_frame_total
from modules.filehandle.check import is_image, is_video, has_image_extension
from modules.ai.processors.frame.core import get_frame_processors_modules
from modules.ai.face_analyser import get_one_face, get_one_face_left, get_one_face_right,get_many_faces

import modules.ui.ui_globals as ui
import modules.ui.utility as util

import modules.globals
def toggle_preview() -> None:
    if ui.PREVIEW.state() == 'normal':
        ui.PREVIEW.withdraw()
    elif modules.globals.source_path and modules.globals.target_path:
        init_preview()
        update_preview()

def init_preview() -> None:
    if is_image(modules.globals.target_path):
        ui.preview_slider.pack_forget()
    if is_video(modules.globals.target_path):
        video_frame_total = get_video_frame_total(modules.globals.target_path)
        ui.preview_slider.configure(to=video_frame_total)
        ui.preview_slider.pack(fill='x')
        ui.preview_slider.set(0)

def update_preview(frame_number: int = 0) -> None:
    if modules.globals.source_path and modules.globals.target_path:
        util.update_status('Processing...')
        temp_frame = get_video_frame(modules.globals.target_path, frame_number)
        if modules.globals.nsfw_filter and util.check_and_ignore_nsfw(temp_frame):
            return
        
        source_image_left = None  # Left source face image
        source_image_right = None  # Right source face image
        
        # Initialize variables for the selected face/s image. 
        # Source image can have one face or two faces we simply detect face from left of frame
        # then right of frame. This insures we always have a face to work with
        if source_image_left is None and modules.globals.source_path:
            source_image_left = get_one_face_left(cv2.imread(modules.globals.source_path))
        if source_image_right is None and modules.globals.source_path:
            source_image_right = get_one_face_right(cv2.imread(modules.globals.source_path))

        # no face found
        if source_image_left is None:
            print('No face found in source image')
            return
        
        if modules.globals.flip_x:
            temp_frame = cv2.flip(temp_frame, 1)
        if modules.globals.flip_y:
            temp_frame = cv2.flip(temp_frame, 0)

        for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
            temp_frame = frame_processor.process_frame([source_image_left,source_image_right],
                temp_frame
            )
        image = Image.fromarray(cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB))
        image = ImageOps.contain(image, (ui.PREVIEW_MAX_WIDTH, ui.PREVIEW_MAX_HEIGHT), Image.LANCZOS)
        image = ctk.CTkImage(image, size=image.size)
        ui.preview_label.configure(image=image)
        util.update_status('Processing succeed!')
        ui.PREVIEW.deiconify()
