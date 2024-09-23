
from modules.filehandle.check import is_image, is_video, has_image_extension
import modules.ui.ui_globals as ui
import modules.globals

from modules.ui.preview import preview, render
import modules.ui.component as C
from typing import Callable
import os
def check_and_ignore_nsfw(target, destroy: Callable = None) -> bool:
    ''' Check if the target is NSFW.
    TODO: Consider to make blur the target.
    '''
    from numpy import ndarray
    from modules.ai.predict.predicter import predict_image, predict_video, predict_frame
    if type(target) is str: # image/video file path
        check_nsfw = predict_image if has_image_extension(target) else predict_video
    elif type(target) is ndarray: # frame object
        check_nsfw = predict_frame
    if check_nsfw and check_nsfw(target):
        if destroy: destroy(to_quit=False) # Do not need to destroy the window frame if the target is NSFW
        update_status('Processing ignored!')
        return True
    else: return False
    
def update_status(text: str) -> None:
    ui.status_label.configure(text=text)
    ui.ROOT.update()


def swap_faces_paths() -> None:
    global RECENT_DIRECTORY_SOURCE, RECENT_DIRECTORY_TARGET

    source_path = modules.globals.source_path
    target_path = modules.globals.target_path

    if not is_image(source_path) or not is_image(target_path):
        return

    modules.globals.source_path = target_path
    modules.globals.target_path = source_path

    RECENT_DIRECTORY_SOURCE = os.path.dirname(modules.globals.source_path)
    RECENT_DIRECTORY_TARGET = os.path.dirname(modules.globals.target_path)

    ui.PREVIEW.withdraw()

    source_image = render.render_image_preview(modules.globals.source_path, (200, 200))
    C.Component().source_label.configure(image=source_image)

    target_image = render.render_image_preview(modules.globals.target_path, (200, 200))
    C.Component().target_label.configure(image=target_image)
