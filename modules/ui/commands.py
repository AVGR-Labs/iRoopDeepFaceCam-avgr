
from modules.ai.processors.frame.core import get_frame_processors_modules
from modules.filehandle.check import is_image, is_video, has_image_extension

import modules.ui.ui_globals as ui
import modules.ui.commands as cmd
from modules.ui.preview import preview, render
import modules.globals
import modules.ui.component as C
import os
import customtkinter as ctk
def clear_face_tracking_data(*args):
    frame_processors = get_frame_processors_modules(modules.globals.frame_processors)
    for frame_processor in frame_processors:
        if hasattr(frame_processor, 'reset_face_tracking'):
                frame_processor.reset_face_tracking()

def flip_faces(*args):
    size = C.flip_faces_value.get()
    modules.globals.flip_faces = int(size)
    modules.globals.flip_faces_value = True
    if modules.globals.face_tracking:
        clear_face_tracking_data()


def toggle_target_mode(use_folder: bool) -> None:
    modules.globals.use_target_folder = use_folder
    if use_folder:
        modules.globals.target_path = None
        C.target_label.configure(image=None)
    else:
        modules.globals.target_folder_path = None
        C.target_label.configure(image=None)


def toggle_source_mode(use_folder: bool) -> None:
    modules.globals.use_source_folder = use_folder
    if use_folder:
        modules.globals.source_path = None
        C.source_label.configure(image=None)
    else:
        modules.globals.source_folder_path = None
        C.source_label.configure(image=None)
        
def toggle_default_mode(use_defaults: bool) -> None:
    
    global Enviroment
    env = Enviroment()
    if use_defaults:
        if env.ready(target='DEFAULT_SOURCE'):
            modules.globals.source_folder_path = env.Default()
            toggle_source_mode(True)
        if env.ready(target='DEFAULT_TARGET'):
            modules.globals.target_folder_path = env.Default()
            toggle_target_mode(True)
        if env.ready(target='DEFAULT_OUTPUT'):
            modules.globals.output_path = env.Default()
    else:
        toggle_source_mode(False)
        toggle_target_mode(False)
        
        

def stickiness_factor_size(*args):
    size = C.stickyface_var.get()
    modules.globals.sticky_face_value = float(size)
    
def pseudo_threshold_size(*args):
    size = C.pseudo_threshold_var.get()
    modules.globals.pseudo_face_threshold = float(size)



def weight_wistribution_size(*args):
    size = C.weight_distribution_size_var.get()
    modules.globals.weight_distribution_size = float(size)

def embedding_weight_size(*args):
    size = C.embedding_weight_size_var.get()
    modules.globals.embedding_weight_size = float(size)

def position_size(*args):
    size = C.position_size_var.get()
    modules.globals.position_size = float(size)

def old_embedding_size(*args):
    size = C.old_embedding_size_var.get()
    modules.globals.old_embedding_weight  = float(size)

def new_embedding_size(*args):
    size = C.new_embedding_size_var.get()
    modules.globals.new_embedding_weight  = float(size)


def select_source_path() -> None:
    global RECENT_DIRECTORY_SOURCE, img_ft, vid_ft

    ui.PREVIEW.withdraw()
    
    if modules.globals.use_source_folder:
        folder_path = ctk.filedialog.askdirectory(title='Select a source folder', initialdir=RECENT_DIRECTORY_SOURCE)
        if folder_path:
            modules.globals.source_folder_path = folder_path
            RECENT_DIRECTORY_SOURCE = folder_path
            # Update UI accordingly, if needed
        return
    source_path = ctk.filedialog.askopenfilename(title='select an source image', initialdir=RECENT_DIRECTORY_SOURCE, filetypes=[img_ft])
    if is_image(source_path):
        modules.globals.source_path = source_path
        RECENT_DIRECTORY_SOURCE = os.path.dirname(modules.globals.source_path)
        image = render.render_image_preview(modules.globals.source_path, (200, 200))
        ui.source_label.configure(image=image)
        if modules.globals.face_tracking:
            cmd.clear_face_tracking_data()
    else:
        modules.globals.source_path = None
        ui.source_label.configure(image=None)
        if modules.globals.face_tracking:
            cmd.clear_face_tracking_data()
