import os
import webbrowser
import customtkinter as ctk
from typing import Callable, Tuple
import cv2
from PIL import Image, ImageOps

import modules.globals
import modules.utilities.metadata
import modules.ui.commands as cmd
import modules.ui.preview.preview as ui_preview
import modules.ui.preview.render as ui_render
from modules.ai.face_analyser import get_one_face, get_one_face_left, get_one_face_right,get_many_faces
from modules.ai.processors.frame.core import get_frame_processors_modules
from modules.ai.processors.frame.face_swapper import update_face_assignments
from modules.utilities.env import Enviroment
from modules.filehandle.check import is_image, is_video, has_image_extension
from modules.filehandle.path import resolve_relative_path
import numpy as np
import time

import modules.ui.ui_globals as ui

import modules.ui.component as C
def init(start: Callable[[], None], destroy: Callable[[], None]) -> ctk.CTk:
    C.root = create_root(start, destroy)
    ui.PREVIEW = create_preview(C.root)

    return C.root

def create_root(start: Callable[[], None], destroy: Callable[[], None]) -> ctk.CTk:
    
    global status_label
    global preview_size_var
    
    ctk.deactivate_automatic_dpi_awareness()
    ctk.set_appearance_mode('system')
    ctk.set_default_color_theme(resolve_relative_path('ui.json'))
 
    root = C.Init(ctk.CTk())
    root.minsize(ui.ROOT_WIDTH, ui.ROOT_HEIGHT)
    root.title(f'{modules.utilities.metadata.name} {modules.utilities.metadata.version} {modules.utilities.metadata.edition}')
    root.configure()
    root.protocol('WM_DELETE_WINDOW', lambda: destroy())

    import modules.ui.components.init as GUI
    root =  GUI.Init().Set(root)
    y_align = 3.35

    ## Target Face Track

    # Outline frame for mouth mask and dropdown
    # outline_face_track_sticky_frame = ctk.CTkFrame(root, fg_color="transparent", border_width=1, border_color="grey")
    # outline_face_track_sticky_frame.place(relx=0.02, rely=15.4*ui.y_increment, relwidth=0.96, relheight=0.07)




    # Mouth mask switch
    # target_face_var = ctk.BooleanVar(value=modules.globals.target_face)
    # target_face_switch = ctk.CTkSwitch(outline_face_track_sticky_frame, text='Use Target Face', variable=target_face_var, cursor='hand2',
    #                                 command=lambda: setattr(modules.globals, 'target_face', target_face_var.get()))
    # target_face_switch.place(relx=0.02, rely=0.5, relwidth=0.6, relheight=0.8, anchor="w")

    # Size dropdown (rightmost)



    # Bottom buttons
    button_width = 0.18  # Width of each button
    button_height = 0.05  # Height of each button
    button_y = 0.85  # Y position of the buttons
    space_between = (1 - (button_width * 5)) / 6  # Space between buttons

    start_button = ctk.CTkButton(root, text='Start', cursor='hand2', command=lambda: select_output_path(start))
    start_button.place(relx=space_between, rely=button_y, relwidth=button_width, relheight=button_height)

    stop_button = ctk.CTkButton(root, text='Destroy', cursor='hand2', command=lambda: destroy())
    stop_button.place(relx=space_between*2 + button_width, rely=button_y, relwidth=button_width, relheight=button_height)

    preview_button = ctk.CTkButton(root, text='Preview', cursor='hand2', command=lambda: ui_preview.toggle_preview())
    preview_button.place(relx=space_between*3 + button_width*2, rely=button_y, relwidth=button_width, relheight=button_height)

    live_button = ctk.CTkButton(root, text='Live', cursor='hand2', command=lambda: webcam_preview(), fg_color="green", hover_color="dark green")
    live_button.place(relx=space_between*4 + button_width*3, rely=button_y, relwidth=button_width, relheight=button_height)

    preview_size_var = ctk.StringVar(value="640x360")
    preview_size_dropdown = ctk.CTkOptionMenu(root, values=["426x240","480x270","512x288","640x360","854x480", "960x540", "1280x720", "1920x1080"],
                                              variable=preview_size_var,
                                              command=update_preview_size,
                                              fg_color="green", button_color="dark green", button_hover_color="forest green")
    preview_size_dropdown.place(relx=space_between*5 + button_width*4, rely=button_y, relwidth=button_width, relheight=button_height)

    # Status and donate labels
    status_label = ctk.CTkLabel(root, text=None, justify='center')
    status_label.place(relx=0.05, rely=0.93, relwidth=0.9)

    donate_label = ctk.CTkLabel(root, text='iRoopDeepFaceCam', justify='center', cursor='hand2')
    donate_label.place(relx=0.05, rely=0.96, relwidth=0.9)
    donate_label.configure(text_color=ctk.ThemeManager.theme.get('URL').get('text_color'))
    donate_label.bind('<Button>', lambda event: webbrowser.open('https://buymeacoffee.com/ivideogameboss'))

    if not modules.globals.face_tracking:
        # C.pseudo_face_switch.configure(state="disabled")
        C.stickiness_dropdown.configure(state="disabled")
        C.pseudo_threshold_dropdown.configure(state="disabled")
        C.clear_tracking_button.configure(state="disabled")
        C.embedding_weight_size_dropdown.configure(state="disabled")
        C.weight_distribution_size_dropdown.configure(state="disabled")
        C.position_size_dropdown.configure(state="disabled")
        C.old_embedding_size_dropdown.configure(state="disabled")
        C.new_embedding_size_dropdown.configure(state="disabled")

    return root


def create_preview(parent: ctk.CTkToplevel) -> ctk.CTkToplevel:
    global preview_label, preview_slider

    preview = ctk.CTkToplevel(parent)
    preview.withdraw()
    preview.title('Always Reset Face Tracking When no Faces, Switching Live Video Stream, or New Faces')
    preview.configure()
    preview.protocol('WM_DELETE_WINDOW', lambda: ui_preview.toggle_preview())
    preview.resizable(width=True, height=True)

    preview_label = ctk.CTkLabel(preview, text=None)
    preview_label.pack(fill='both', expand=True)

    preview_slider = ctk.CTkSlider(preview, from_=0, to=0, command=lambda frame_value: ui_preview.update_preview(frame_value))

    return preview

def select_target_path() -> None:
    global RECENT_DIRECTORY_TARGET

    ui.PREVIEW.withdraw()
    if modules.globals.use_target_folder:
        folder_path = ctk.filedialog.askdirectory(title='Select a target folder', initialdir=RECENT_DIRECTORY_TARGET)
        if folder_path:
            modules.globals.target_folder_path = folder_path
            RECENT_DIRECTORY_TARGET = folder_path
        return
    target_path = ctk.filedialog.askopenfilename(title='select an target image or video', initialdir=RECENT_DIRECTORY_TARGET, filetypes=[img_ft, vid_ft])
    if is_image(target_path):
        modules.globals.target_path = target_path
        RECENT_DIRECTORY_TARGET = os.path.dirname(modules.globals.target_path)
        image = ui_render.render_image_preview(modules.globals.target_path, (200, 200))
        C.target_label.configure(image=image)
        if modules.globals.face_tracking:
            cmd.clear_face_tracking_data()
            modules.globals.face_tracking = False
            C.face_tracking_value.set(False)  # Update the switch state
            C.pseudo_face_var.set(False)  # Update the switch state
            face_tracking()  # Call face_tracking to update UI elements
    elif is_video(target_path):
        modules.globals.target_path = target_path
        RECENT_DIRECTORY_TARGET = os.path.dirname(modules.globals.target_path)
        video_frame = ui_render.render_video_preview(target_path, (200, 200))
        C.target_label.configure(image=video_frame)
        if modules.globals.face_tracking:
            cmd.clear_face_tracking_data()
    else:
        modules.globals.target_path = None
        target_label.configure(image=None)
        if modules.globals.face_tracking:
            cmd.clear_face_tracking_data()

def select_output_path(start: Callable[[], None]) -> None:
    global RECENT_DIRECTORY_OUTPUT, img_ft, vid_ft
    # if modules.globals.use_target_folder or modules.globals.use_source_folder:
    output_path = ctk.filedialog.askdirectory(title='Select a output folder', initialdir=RECENT_DIRECTORY_TARGET)
    # else:
    #     if is_image(modules.globals.target_path):
    #         output_path = ctk.filedialog.asksaveasfilename(title='save image output file', filetypes=[img_ft], defaultextension='.png', initialfile='output.png', initialdir=RECENT_DIRECTORY_OUTPUT)
    #     elif is_video(modules.globals.target_path):
    #         output_path = ctk.filedialog.asksaveasfilename(title='save video output file', filetypes=[vid_ft], defaultextension='.mp4', initialfile='output.mp4', initialdir=RECENT_DIRECTORY_OUTPUT)
    #     else:
    #         output_path = None
    if output_path:
        modules.globals.output_path = output_path
        RECENT_DIRECTORY_OUTPUT = os.path.dirname(modules.globals.output_path)
        start()


def fit_image_to_size(image, width: int, height: int):
    if width is None and height is None:
      return image
    h, w, _ = image.shape
    ratio_h = 0.0
    ratio_w = 0.0
    if width > height:
        ratio_h = height / h
    else:
        ratio_w = width  / w
    ratio = max(ratio_w, ratio_h)
    new_size = (int(ratio * w), int(ratio * h))
    return cv2.resize(image, dsize=new_size)

def webcam_preview():
    if modules.globals.source_path is None:
        return
    global preview_label, camera
    global first_face_id, second_face_id  # Add these global variables
    global first_face_embedding, second_face_embedding  # Add these global variables

    # Reset face assignments
    first_face_embedding = None
    second_face_embedding = None
    first_face_id = None
    second_face_id = None

    # Reset face assignments
    first_face_embedding = None
    second_face_embedding = None
    # Reset face assignments
    first_face_id = None
    second_face_id = None

    camera = cv2.VideoCapture(0)
    update_camera_resolution()
    # Configure the preview window
    ui.PREVIEW.deiconify()
    ui.PREVIEW.geometry(f"{ui.WEBCAM_PREVIEW_WIDTH}x{ui.WEBCAM_PREVIEW_HEIGHT}")
    preview_label.configure(width=ui.WEBCAM_PREVIEW_WIDTH, height=ui.WEBCAM_PREVIEW_HEIGHT)
    frame_processors = get_frame_processors_modules(modules.globals.frame_processors)
    
    if modules.globals.face_tracking:
        for frame_processor in frame_processors:
            if hasattr(frame_processor, 'reset_face_tracking'):
                    frame_processor.reset_face_tracking()

    source_image_left = None
    source_image_right = None
    
    target_image_left = None
    target_image_right = None

    if modules.globals.source_path:
        source_image_left = get_one_face_left(cv2.imread(modules.globals.source_path))
        source_image_right = get_one_face_right(cv2.imread(modules.globals.source_path))
    
    if source_image_left is None:
        print('No face found in source image')
        return
    else:
        for frame_processor in frame_processors:
            if hasattr(frame_processor, 'extract_face_embedding'):
                modules.globals.source_face_left_embedding=frame_processor.extract_face_embedding(source_image_left)
                modules.globals.source_face_right_embedding=frame_processor.extract_face_embedding(source_image_right)
                # print('face found in source image')

    # if modules.globals.target_path:
    #     target_image_left = get_one_face_left(cv2.imread(modules.globals.target_path))
    #     target_image_right = get_one_face_right(cv2.imread(modules.globals.target_path))
    
    # if target_image_left is None:
    #     print('No face found in target image')
    # else:
    #     for frame_processor in frame_processors:
    #         if hasattr(frame_processor, 'extract_face_embedding'):
    #             modules.globals.target_face_left_embedding=frame_processor.extract_face_embedding(target_image_left)
    #             modules.globals.target_face_right_embedding=frame_processor.extract_face_embedding(target_image_right)
    #             # print('face found in target image')


    # FPS calculation variables
    frame_count = 0
    start_time = time.time()
    fps = 0

    while camera.isOpened():
        ret, frame = camera.read()
        if not ret:
            break
        temp_frame = frame.copy()
        
        if modules.globals.flip_x:
            temp_frame = cv2.flip(temp_frame, 1)
        if modules.globals.flip_y:
            temp_frame = cv2.flip(temp_frame, 0)
        
        for frame_processor in frame_processors:
            temp_frame = frame_processor.process_frame([source_image_left, source_image_right], temp_frame)
        
        # # Calculate and display FPS
        frame_count += 1
        current_time = time.time()
        elapsed_time = current_time - start_time
        if elapsed_time > 1:  # Update FPS every second
            fps = frame_count / elapsed_time
            frame_count = 0
            start_time = current_time
        
        #cv2.putText(temp_frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        C.fps_label.configure(text=f'FPS: {fps:.2f}')
        C.target_face1_value.configure(text=f': {modules.globals.target_face1_score:.2f}')
        C.target_face2_value.configure(text=f': {modules.globals.target_face2_score:.2f}')
        # Get current preview window size
        current_width = ui.PREVIEW.winfo_width()
        current_height = ui.PREVIEW.winfo_height()
        # Resize the processed frame to fit the current preview window size
        temp_frame = fit_image_to_preview(temp_frame, current_width, current_height)
        image = cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        image = ctk.CTkImage(image, size=(current_width, current_height))
        preview_label.configure(image=image, width=current_width, height=current_height)
        ui.ROOT.update()
        if ui.PREVIEW.state() == 'withdrawn':
            break
    camera.release()
    ui.PREVIEW.withdraw()

def fit_image_to_preview(image, preview_width, preview_height):
    h, w = image.shape[:2]
    aspect_ratio = w / h

    if preview_width / preview_height > aspect_ratio:
        new_height = preview_height
        new_width = int(new_height * aspect_ratio)
    else:
        new_width = preview_width
        new_height = int(new_width / aspect_ratio)

    resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

    # Create a black canvas of the size of the preview window
    canvas = np.zeros((preview_height, preview_width, 3), dtype=np.uint8)

    # Calculate position to paste the resized image
    y_offset = (preview_height - new_height) // 2
    x_offset = (preview_width - new_width) // 2

    # Paste the resized image onto the canvas
    canvas[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = resized_image

    return canvas

def update_preview_size(*args):
    global PREVIEW_DEFAULT_WIDTH, PREVIEW_DEFAULT_HEIGHT, camera
    size = preview_size_var.get().split('x')
    PREVIEW_DEFAULT_WIDTH = int(size[0])
    PREVIEW_DEFAULT_HEIGHT = int(size[1])
    
    if camera is not None and camera.isOpened():
        update_camera_resolution()
    
    if ui.PREVIEW.state() == 'normal':
        ui_preview.update_preview()

def update_camera_resolution():
    global camera, PREVIEW_DEFAULT_WIDTH, PREVIEW_DEFAULT_HEIGHT
    if camera is not None and camera.isOpened():
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, PREVIEW_DEFAULT_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, PREVIEW_DEFAULT_HEIGHT)
        camera.set(cv2.CAP_PROP_FPS, 60)  # You may want to make FPS configurable as well

def face_tracking(*args):
    size = C.face_tracking_value.get()
    modules.globals.face_tracking = size  # Use boolean directly
    modules.globals.face_tracking_value = size

    if size:  # If face tracking is enabled
        # Disable many faces
        modules.globals.many_faces = False
        many_faces_var.set(False)  # Update the many faces switch state
  
    # Enable/disable UI elements based on face tracking state
    if size:  # If face tracking is enabled
        C.pseudo_face_switch.configure(state="normal")
        C.stickiness_dropdown.configure(state="normal")
        C.pseudo_threshold_dropdown.configure(state="normal")
        C.clear_tracking_button.configure(state="normal")
        C.embedding_weight_size_dropdown.configure(state="normal")
        C.weight_distribution_size_dropdown.configure(state="normal")
        C.position_size_dropdown.configure(state="normal")
        C.old_embedding_size_dropdown.configure(state="normal")
        C.new_embedding_size_dropdown.configure(state="normal")
    else:  # If face tracking is disabled
        C.pseudo_face_switch.configure(state="disabled")
        C.stickiness_dropdown.configure(state="disabled")
        C.pseudo_threshold_dropdown.configure(state="disabled")
        C.clear_tracking_button.configure(state="disabled")
        C.embedding_weight_size_dropdown.configure(state="disabled")
        C.weight_distribution_size_dropdown.configure(state="disabled")
        C.position_size_dropdown.configure(state="disabled")
        C.old_embedding_size_dropdown.configure(state="disabled")
        C.new_embedding_size_dropdown.configure(state="disabled")
        C.pseudo_face_var.set(False)  # Update the switch state

    cmd.clear_face_tracking_data()

def stickyface_size(*args):
    size = stickyface_var.get()
    modules.globals.sticky_face_value = float(size)
  
def detect_faces_right(*args):
    size = detect_face_right_value.get()
    modules.globals.detect_face_right = int(size)
    modules.globals.detect_face_right_value = True
    if modules.globals.face_tracking:
        cmd.clear_face_tracking_data()


