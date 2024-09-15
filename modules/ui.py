import os
import webbrowser
import customtkinter as ctk
from typing import Callable, Tuple
import cv2
from PIL import Image, ImageOps

import modules.globals
import modules.metadata
from modules.face_analyser import get_one_face, get_one_face_left, get_one_face_right,get_many_faces
from modules.capturer import get_video_frame, get_video_frame_total
from modules.processors.frame.core import get_frame_processors_modules
from modules.processors.frame.face_swapper import update_face_assignments

from modules.utilities import is_image, is_video, resolve_relative_path, has_image_extension
import numpy as np
import time

global camera
camera = None

ROOT = None
ROOT_HEIGHT = 900
ROOT_WIDTH = 600

PREVIEW = None
PREVIEW_MAX_HEIGHT = 700
PREVIEW_MAX_WIDTH  = 1200
PREVIEW_DEFAULT_WIDTH  = 640
PREVIEW_DEFAULT_HEIGHT = 360
BLUR_SIZE=1

RECENT_DIRECTORY_SOURCE = None
RECENT_DIRECTORY_TARGET = None
RECENT_DIRECTORY_OUTPUT = None

preview_label = None
preview_slider = None
source_label = None
target_label = None
status_label = None

img_ft, vid_ft = modules.globals.file_types


def init(start: Callable[[], None], destroy: Callable[[], None]) -> ctk.CTk:
    global ROOT, PREVIEW

    ROOT = create_root(start, destroy)
    PREVIEW = create_preview(ROOT)

    return ROOT

def create_root(start: Callable[[], None], destroy: Callable[[], None]) -> ctk.CTk:
    
    global source_label, target_label, status_label
    global preview_size_var, mouth_mask_var,mask_size_var
    global mask_down_size_var,mask_feather_ratio_var
    global flip_faces_value,fps_label,stickyface_var
    global detect_face_right_value,target_face1_value
    global target_face2_value,pseudo_threshold_var
    global face_tracking_value,many_faces_var,pseudo_face_var
    
    global use_folder_as_source, use_folder_as_source_switch
    global use_folder_as_target, use_folder_as_target_switch
    
    global pseudo_face_switch, stickiness_dropdown, pseudo_threshold_dropdown, clear_tracking_button
    global embedding_weight_size_var,position_size_var,old_embedding_size_var,new_embedding_size_var
    global weight_distribution_size_var,embedding_weight_size_dropdown,weight_distribution_size_dropdown
    global position_size_dropdown, old_embedding_size_dropdown,new_embedding_size_dropdown

    ctk.deactivate_automatic_dpi_awareness()
    ctk.set_appearance_mode('system')
    ctk.set_default_color_theme(resolve_relative_path('ui.json'))

    root = ctk.CTk()
    root.minsize(ROOT_WIDTH, ROOT_HEIGHT)
    root.title(f'{modules.metadata.name} {modules.metadata.version} {modules.metadata.edition}')
    root.configure()
    root.protocol('WM_DELETE_WINDOW', lambda: destroy())

    y_start = 0.01
    y_increment = 0.05

    info_label = ctk.CTkLabel(root, text='Webcam takes 30 seconds to start on first face detection', justify='center')
    info_label.place(relx=0, rely=0, relwidth=1)
    fps_label = ctk.CTkLabel(root, text='FPS:  ', justify='center',font=("Arial", 12))
    fps_label.place(relx=0, rely=0.04, relwidth=1)
    
    # Image preview area
    source_label = ctk.CTkLabel(root, text=None)
    source_label.place(relx=0.03, rely=y_start + 0.40*y_increment, relwidth=0.40, relheight=0.15)

    target_label = ctk.CTkLabel(root, text=None)
    target_label.place(relx=0.58, rely=y_start + 0.40*y_increment, relwidth=0.40, relheight=0.15)

    y_align = 3.35

    # Buttons for selecting source and target
    select_face_button = ctk.CTkButton(root, text='Select a face/s\n( left face ) ( right face )', cursor='hand2', command=lambda: select_source_path())
    select_face_button.place(relx=0.05, rely=y_start + 3.35*y_increment, relwidth=0.36, relheight=0.06)

    swap_faces_button = ctk.CTkButton(root, text='↔', cursor='hand2', command=lambda: swap_faces_paths())
    swap_faces_button.place(relx=0.46, rely=y_start + 3.35*y_increment, relwidth=0.10, relheight=0.06)

    select_target_button = ctk.CTkButton(root, text='Select a target\n( Image / Video )', cursor='hand2', command=lambda: select_target_path())
    select_target_button.place(relx=0.60, rely=y_start + 3.35*y_increment, relwidth=0.36, relheight=0.06)
    
    use_folder_as_source = ctk.BooleanVar(value=modules.globals.use_source_folder)
    use_folder_as_source_switch = ctk.CTkSwitch(root, text='Use folder as source', variable=use_folder_as_source, cursor='hand2', command=lambda: toggle_source_mode(use_folder_as_source.get()))
    
    use_folder_as_source_switch.place(relx=0.03, rely=y_start + 4.6*y_increment, relwidth=0.8)
    
    use_folder_as_target = ctk.BooleanVar(value=modules.globals.use_target_folder)
    use_folder_as_target_switch = ctk.CTkSwitch(root, text='Use folder as target', variable=use_folder_as_target, cursor='hand2', command=lambda: toggle_target_mode(use_folder_as_target.get()))
    
    use_folder_as_target_switch.place(relx=0.80, rely=y_start + 4.6*y_increment, relwidth=0.2)
    # Left column of switches
    both_faces_var = ctk.BooleanVar(value=modules.globals.both_faces)
    both_faces_switch = ctk.CTkSwitch(root, text='Show Both Faces', variable=both_faces_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'both_faces', both_faces_var.get()))
    both_faces_switch.place(relx=0.03, rely=y_start + 5.2*y_increment, relwidth=0.8)

    flip_faces_value = ctk.BooleanVar(value=modules.globals.flip_faces)
    flip_faces_switch = ctk.CTkSwitch(root, text='Flip Left/Right Faces', variable=flip_faces_value, cursor='hand2',
                                    command=lambda: flip_faces('flip_faces', flip_faces_value.get()))
    flip_faces_switch.place(relx=0.03, rely=y_start + 5.8*y_increment, relwidth=0.4)

    detect_face_right_value = ctk.BooleanVar(value=modules.globals.detect_face_right)
    detect_face_right_switch = ctk.CTkSwitch(root, text='Detect Face From Right', variable=detect_face_right_value, cursor='hand2',
                                    command=lambda: detect_faces_right('detect_face_right', detect_face_right_value.get()))
    detect_face_right_switch.place(relx=0.03, rely=y_start + 6.4*y_increment, relwidth=0.4)

    many_faces_var = ctk.BooleanVar(value=modules.globals.many_faces)
    many_faces_switch = ctk.CTkSwitch(root, text='Many Faces', variable=many_faces_var, cursor='hand2',
                                    command=lambda: many_faces('many_faces', many_faces_var.get()))
    many_faces_switch.place(relx=0.03, rely=y_start + 7*y_increment, relwidth=0.8)

    show_target_face_box_var = ctk.BooleanVar(value=modules.globals.show_target_face_box)
    show_target_face_box_switch = ctk.CTkSwitch(root, text='Show InsightFace Landmarks', variable=show_target_face_box_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'show_target_face_box', show_target_face_box_var.get()))
    show_target_face_box_switch.place(relx=0.03, rely=y_start + 7.6*y_increment, relwidth=0.8)

    show_mouth_mask_var = ctk.BooleanVar(value=modules.globals.show_mouth_mask_box)
    show_mouth_mask_switch = ctk.CTkSwitch(root, text='Show Mouth Mask Box', variable=show_mouth_mask_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'show_mouth_mask_box', show_mouth_mask_var.get()))
    show_mouth_mask_switch.place(relx=0.03, rely=y_start + 8.2*y_increment, relwidth=0.8)


    # Right column of switches
    live_flip_x_var = ctk.BooleanVar(value=modules.globals.flip_x)
    live_flip_x_vswitch = ctk.CTkSwitch(root, text='Flip X', variable=live_flip_x_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'flip_x', live_flip_x_var.get()))
    live_flip_x_vswitch.place(relx=0.80, rely=y_start + 5.2*y_increment, relwidth=0.2)

    live_flip_y_var = ctk.BooleanVar(value=modules.globals.flip_y)
    live_flip_y_switch = ctk.CTkSwitch(root, text='Flip Y', variable=live_flip_y_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'flip_y', live_flip_y_var.get()))
    live_flip_y_switch.place(relx=0.80, rely=y_start + 5.8*y_increment, relwidth=0.2)

    keep_fps_var = ctk.BooleanVar(value=modules.globals.keep_fps)
    keep_fps_switch = ctk.CTkSwitch(root, text='Keep fps', variable=keep_fps_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'keep_fps', keep_fps_var.get()))
    keep_fps_switch.place(relx=0.80, rely=y_start + 6.4*y_increment, relwidth=0.4)

    keep_audio_var = ctk.BooleanVar(value=modules.globals.keep_audio)
    keep_audio_switch = ctk.CTkSwitch(root, text='Keep Audio', variable=keep_audio_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'keep_audio', keep_audio_var.get()))
    keep_audio_switch.place(relx=0.80, rely=y_start + 7*y_increment, relwidth=0.4)

    keep_frames_var = ctk.BooleanVar(value=modules.globals.keep_frames)
    keep_frames_switch = ctk.CTkSwitch(root, text='Keep Frames', variable=keep_frames_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'keep_frames', keep_frames_var.get()))
    keep_frames_switch.place(relx=0.80, rely=y_start + 7.6*y_increment, relwidth=0.4)

    nsfw_filter_var = ctk.BooleanVar(value=modules.globals.nsfw_filter)
    nsfw_filter_switch = ctk.CTkSwitch(root, text='NSFW Filter', variable=nsfw_filter_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'nsfw_filter', nsfw_filter_var.get()))
    nsfw_filter_switch.place(relx=0.80, rely=y_start + 8.2*y_increment, relwidth=0.4)

    enhancer_value = ctk.BooleanVar(value=modules.globals.fp_ui['face_enhancer'])
    enhancer_switch = ctk.CTkSwitch(root, text='Face Enhancer', variable=enhancer_value, cursor='hand2',
                                    command=lambda: update_tumbler('face_enhancer', enhancer_value.get()))
    enhancer_switch.place(relx=0.80, rely=y_start + 8.8*y_increment, relwidth=0.4)


    ##### Mouth Mask Frame

    # Outline frame for mouth mask and dropdown
    outline_frame = ctk.CTkFrame(root, fg_color="transparent", border_width=1, border_color="grey")
    outline_frame.place(relx=0.02, rely=y_start + 9.3*y_increment, relwidth=0.96, relheight=0.05)

    # Mouth mask switch
    mouth_mask_var = ctk.BooleanVar(value=modules.globals.mouth_mask)
    mouth_mask_switch = ctk.CTkSwitch(outline_frame, text='Mouth Mask | Feather, Padding, Top ->', variable=mouth_mask_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'mouth_mask', mouth_mask_var.get()))
    mouth_mask_switch.place(relx=0.02, rely=0.5, relwidth=0.6, relheight=0.5, anchor="w")

    # Size dropdown (rightmost)
    mask_size_var = ctk.StringVar(value="1")
    mask_size_dropdown = ctk.CTkOptionMenu(outline_frame, values=["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20"],
                                            variable=mask_size_var,
                                            command=mask_size)
    mask_size_dropdown.place(relx=0.98, rely=0.5, relwidth=0.1, anchor="e")

    # Down size dropdown
    mask_down_size_var = ctk.StringVar(value="0.50")
    mask_down_size_dropdown = ctk.CTkOptionMenu(outline_frame, values=["0.01","0.02","0.03","0.04","0.05","0.06","0.07","0.08","0.09","0.10","0.15","0.20","0.25","0.30","0.35","0.40","0.45","0.50","0.55","0.60","0.65","0.70","0.75","0.80","0.85","0.90","0.95","1.00","1.25","1.50","1.75","2.00","2.25","2.50","2.75","3.00"],
                                            variable=mask_down_size_var,
                                            command=mask_down_size)
    mask_down_size_dropdown.place(relx=0.87, rely=0.5, relwidth=0.12, anchor="e")

    # Feather ratio dropdown
    mask_feather_ratio_var = ctk.StringVar(value="8")
    mask_feather_ratio_size_dropdown = ctk.CTkOptionMenu(outline_frame, values=["1","2","3","4","5","6","7","8","9","10"],
                                            variable=mask_feather_ratio_var,
                                            command=mask_feather_ratio_size)
    mask_feather_ratio_size_dropdown.place(relx=0.76, rely=0.5, relwidth=0.1,  anchor="e")


    ##### Face Tracking Frame

    # Outline frame for face tracking
    outline_face_track_frame = ctk.CTkFrame(root, fg_color="transparent", border_width=1, border_color="grey")
    outline_face_track_frame.place(relx=0.02, rely=y_start + 10.3*y_increment, relwidth=0.96, relheight=0.24)

     # Face Tracking switch
    face_tracking_value = ctk.BooleanVar(value=modules.globals.face_tracking)
    face_tracking_switch = ctk.CTkSwitch(outline_face_track_frame, text='Auto Face Track', variable=face_tracking_value, cursor='hand2',
                                    command=lambda: face_tracking('face_tracking', face_tracking_value.get()))
    face_tracking_switch.place(relx=0.02, rely=0.1, relwidth=0.4)

    # Pseudo Face switch
    pseudo_face_var = ctk.BooleanVar(value=modules.globals.use_pseudo_face)
    pseudo_face_switch = ctk.CTkSwitch(outline_face_track_frame, text='Pseudo Face\n(fake face\nfor occlusions)', variable=pseudo_face_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'use_pseudo_face', pseudo_face_var.get()))
    pseudo_face_switch.place(relx=0.02, rely=0.3, relwidth=0.4)


    # Red box frame
    red_box_frame = ctk.CTkFrame(outline_face_track_frame, fg_color="transparent", border_width=1, border_color="#800000")
    red_box_frame.place(relx=0.33, rely=0.02, relwidth=0.28, relheight=0.65)
   
    # Face Cosine Similarity label
    similarity_label = ctk.CTkLabel(red_box_frame, text="Similarity * Position",font=("Arial", 14) )
    similarity_label.place(relx=0.05, rely=0.01, relwidth=0.85 )
    # Target Face 1 label and value
    target_face1_label = ctk.CTkLabel(red_box_frame, text="Target Face 1:", font=("Arial", 12))
    target_face1_label.place(relx=0.05, rely=0.18, relwidth=0.6)

    target_face1_value = ctk.CTkLabel(red_box_frame, text="0.00", anchor="w")
    target_face1_value.place(relx=0.65, rely=0.18, relwidth=0.3)

    # Target Face 2 label and value
    target_face2_label = ctk.CTkLabel(red_box_frame, text="Target Face 2:", font=("Arial", 12))
    target_face2_label.place(relx=0.05, rely=0.33, relwidth=0.6)

    target_face2_value = ctk.CTkLabel(red_box_frame, text="0.00", anchor="w")
    target_face2_value.place(relx=0.65, rely=0.33, relwidth=0.3)

        # Target Face 2 label and value
    target_face2_label = ctk.CTkLabel(red_box_frame, text="* MAX TWO FACE ON\nSCREEN DETECTED FROM\nLEFT OR RIGHT *", font=("Arial", 10))
    target_face2_label.place(relx=0.05, rely=0.60, relwidth=0.9)


    # Stickiness Factor label
    stickiness_label = ctk.CTkLabel(outline_face_track_frame, text="Stickiness Factor",font=("Arial", 14))
    stickiness_label.place(relx=0.72, rely=0.01, relwidth=0.2)

    # Stickiness Greater label
    stickiness_greater_label = ctk.CTkLabel(outline_face_track_frame, text=">",font=("Arial", 14))
    stickiness_greater_label.place(relx=0.65, rely=0.14, relwidth=0.1)

    # Stickiness Factor dropdown
    stickyface_var = ctk.StringVar(value="0.20")
    stickiness_dropdown = ctk.CTkOptionMenu(outline_face_track_frame, values=["0.05","0.10","0.15","0.20","0.25","0.30","0.35","0.40","0.45","0.50","0.55","0.60","0.65","0.70","0.75","0.80","0.85","0.90","0.95","1.00"],
                                            variable=stickyface_var,
                                            command=stickiness_factor_size)
    stickiness_dropdown.place(relx=0.75, rely=0.14, relwidth=0.15)


    # Stickiness Greater label
    pseudo_threshold_greater_label = ctk.CTkLabel(outline_face_track_frame, text="<",font=("Arial", 14))
    pseudo_threshold_greater_label.place(relx=0.65, rely=0.30, relwidth=0.1)

    # Pseudo Threshold dropdown
    pseudo_threshold_var = ctk.StringVar(value="0.20")
    pseudo_threshold_dropdown = ctk.CTkOptionMenu(outline_face_track_frame, values=["0.05","0.10","0.15","0.20","0.25","0.30","0.35","0.40","0.45","0.50","0.55","0.60","0.65","0.70","0.75","0.80","0.85","0.90","0.95","1.00"],
                                                variable=pseudo_threshold_var,
                                                command=pseudo_threshold_size)
    pseudo_threshold_dropdown.place(relx=0.75, rely=0.30, relwidth=0.15)

    # Pseudo Threshold label
    pseudo_threshold_label = ctk.CTkLabel(outline_face_track_frame, text="Pseudo Threshold",font=("Arial", 14))
    pseudo_threshold_label.place(relx=0.72, rely=0.42, relwidth=0.2)


    # Clear Face Tracking Data button
    clear_tracking_button = ctk.CTkButton(outline_face_track_frame, text="Reset Face Tracking", 
                                        command=clear_face_tracking_data)
    clear_tracking_button.place(relx=0.65, rely=0.55, relwidth=0.34)

    track_settings_label = ctk.CTkLabel(outline_face_track_frame, text="Embedding Weight   *   Weight Distribution   +   Position Weight            Old Weight   +   New Weight", font=("Arial", 12))
    track_settings_label.place(relx=0.01, rely=0.68, relwidth=0.96)


    embedding_weight_size_var = ctk.StringVar(value="0.60")
    embedding_weight_size_dropdown = ctk.CTkOptionMenu(outline_face_track_frame, values=["0.05","0.10","0.15","0.20","0.25","0.30","0.35","0.40","0.45","0.50","0.55","0.60","0.65","0.70","0.75","0.80","0.85","0.90","0.95","1.00"],
                                            variable=embedding_weight_size_var,
                                            command=embedding_weight_size)
    embedding_weight_size_dropdown.place(relx=0.03, rely=0.84, relwidth=0.13)

    weight_distribution_size_var = ctk.StringVar(value="1.00")
    weight_distribution_size_dropdown = ctk.CTkOptionMenu(outline_face_track_frame, values=["0.05","0.15","0.25","0.35","0.45","0.55","0.65","0.75","0.85","0.95","1.00","1.25","1.50","1.75","2.00","2.25","2.50","2.75","3.00","3.25","3.50","3.75","4.00","4.25","4.50","4.75","5.00"],
                                            variable=weight_distribution_size_var,
                                            command=weight_wistribution_size)
    weight_distribution_size_dropdown.place(relx=0.25, rely=0.84, relwidth=0.13)

    # Down size dropdown
    position_size_var = ctk.StringVar(value="0.40")
    position_size_dropdown = ctk.CTkOptionMenu(outline_face_track_frame, values=["0.05","0.10","0.15","0.20","0.25","0.30","0.35","0.40","0.45","0.50","0.55","0.60","0.65","0.70","0.75","0.80","0.85","0.90","0.95","1.00"],
                                            variable=position_size_var,
                                            command=position_size)
    position_size_dropdown.place(relx=0.48, rely=0.84, relwidth=0.13)

    # Feather ratio dropdown
    old_embedding_size_var = ctk.StringVar(value="0.90")
    old_embedding_size_dropdown = ctk.CTkOptionMenu(outline_face_track_frame, values=["0.05","0.10","0.15","0.20","0.25","0.30","0.35","0.40","0.45","0.50","0.55","0.60","0.65","0.70","0.75","0.80","0.85","0.90","0.95","1.00"],
                                            variable=old_embedding_size_var,
                                            command=old_embedding_size)
    old_embedding_size_dropdown.place(relx=0.68, rely=0.84, relwidth=0.13)

    # Feather ratio dropdown
    new_embedding_size_var = ctk.StringVar(value="0.10")
    new_embedding_size_dropdown = ctk.CTkOptionMenu(outline_face_track_frame, values=["0.05","0.10","0.15","0.20","0.25","0.30","0.35","0.40","0.45","0.50","0.55","0.60","0.65","0.70","0.75","0.80","0.85","0.90","0.95","1.00"],
                                            variable=new_embedding_size_var,
                                            command=new_embedding_size)
    new_embedding_size_dropdown.place(relx=0.84, rely=0.84, relwidth=0.13)

    ## Target Face Track

    # Outline frame for mouth mask and dropdown
    # outline_face_track_sticky_frame = ctk.CTkFrame(root, fg_color="transparent", border_width=1, border_color="grey")
    # outline_face_track_sticky_frame.place(relx=0.02, rely=15.4*y_increment, relwidth=0.96, relheight=0.07)




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

    preview_button = ctk.CTkButton(root, text='Preview', cursor='hand2', command=lambda: toggle_preview())
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
        pseudo_face_switch.configure(state="disabled")
        stickiness_dropdown.configure(state="disabled")
        pseudo_threshold_dropdown.configure(state="disabled")
        clear_tracking_button.configure(state="disabled")
        embedding_weight_size_dropdown.configure(state="disabled")
        weight_distribution_size_dropdown.configure(state="disabled")
        position_size_dropdown.configure(state="disabled")
        old_embedding_size_dropdown.configure(state="disabled")
        new_embedding_size_dropdown.configure(state="disabled")

    return root



def toggle_source_mode(use_folder: bool) -> None:
    modules.globals.use_source_folder = use_folder
    if use_folder:
        modules.globals.source_path = None
        source_label.configure(image=None)
    else:
        modules.globals.source_folder_path = None
        source_label.configure(image=None)

def toggle_target_mode(use_folder: bool) -> None:
    modules.globals.use_target_folder = use_folder
    if use_folder:
        modules.globals.target_path = None
        target_label.configure(image=None)
    else:
        modules.globals.target_folder_path = None
        target_label.configure(image=None)


def weight_wistribution_size(*args):
    size = weight_distribution_size_var.get()
    modules.globals.weight_distribution_size = float(size)

def embedding_weight_size(*args):
    size = embedding_weight_size_var.get()
    modules.globals.embedding_weight_size = float(size)

def position_size(*args):
    size = position_size_var.get()
    modules.globals.position_size = float(size)

def old_embedding_size(*args):
    size = old_embedding_size_var.get()
    modules.globals.old_embedding_weight  = float(size)

def new_embedding_size(*args):
    size = new_embedding_size_var.get()
    modules.globals.new_embedding_weight  = float(size)

def create_preview(parent: ctk.CTkToplevel) -> ctk.CTkToplevel:
    global preview_label, preview_slider

    preview = ctk.CTkToplevel(parent)
    preview.withdraw()
    preview.title('Always Reset Face Tracking When no Faces, Switching Live Video Stream, or New Faces')
    preview.configure()
    preview.protocol('WM_DELETE_WINDOW', lambda: toggle_preview())
    preview.resizable(width=True, height=True)

    preview_label = ctk.CTkLabel(preview, text=None)
    preview_label.pack(fill='both', expand=True)

    preview_slider = ctk.CTkSlider(preview, from_=0, to=0, command=lambda frame_value: update_preview(frame_value))

    return preview

def update_status(text: str) -> None:
    status_label.configure(text=text)
    ROOT.update()

def update_tumbler(var: str, value: bool) -> None:
    modules.globals.fp_ui[var] = value

def select_source_path() -> None:
    global RECENT_DIRECTORY_SOURCE, img_ft, vid_ft

    PREVIEW.withdraw()
    
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
        image = render_image_preview(modules.globals.source_path, (200, 200))
        source_label.configure(image=image)
        if modules.globals.face_tracking:
            clear_face_tracking_data()
    else:
        modules.globals.source_path = None
        source_label.configure(image=None)
        if modules.globals.face_tracking:
            clear_face_tracking_data()

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

    PREVIEW.withdraw()

    source_image = render_image_preview(modules.globals.source_path, (200, 200))
    source_label.configure(image=source_image)

    target_image = render_image_preview(modules.globals.target_path, (200, 200))
    target_label.configure(image=target_image)

def select_target_path() -> None:
    global RECENT_DIRECTORY_TARGET, img_ft, vid_ft

    PREVIEW.withdraw()
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
        image = render_image_preview(modules.globals.target_path, (200, 200))
        target_label.configure(image=image)
        if modules.globals.face_tracking:
            clear_face_tracking_data()
            modules.globals.face_tracking = False
            face_tracking_value.set(False)  # Update the switch state
            pseudo_face_var.set(False)  # Update the switch state
            face_tracking()  # Call face_tracking to update UI elements
    elif is_video(target_path):
        modules.globals.target_path = target_path
        RECENT_DIRECTORY_TARGET = os.path.dirname(modules.globals.target_path)
        video_frame = render_video_preview(target_path, (200, 200))
        target_label.configure(image=video_frame)
        if modules.globals.face_tracking:
            clear_face_tracking_data()
    else:
        modules.globals.target_path = None
        target_label.configure(image=None)
        if modules.globals.face_tracking:
            clear_face_tracking_data()

def select_output_path(start: Callable[[], None]) -> None:
    global RECENT_DIRECTORY_OUTPUT, img_ft, vid_ft
    if modules.globals.use_target_folder or modules.globals.use_source_folder:
        output_path = ctk.filedialog.askdirectory(title='Select a output folder', initialdir=RECENT_DIRECTORY_TARGET)
    else:
        if is_image(modules.globals.target_path):
            output_path = ctk.filedialog.asksaveasfilename(title='save image output file', filetypes=[img_ft], defaultextension='.png', initialfile='output.png', initialdir=RECENT_DIRECTORY_OUTPUT)
        elif is_video(modules.globals.target_path):
            output_path = ctk.filedialog.asksaveasfilename(title='save video output file', filetypes=[vid_ft], defaultextension='.mp4', initialfile='output.mp4', initialdir=RECENT_DIRECTORY_OUTPUT)
        else:
            output_path = None
    if output_path:
        modules.globals.output_path = output_path
        RECENT_DIRECTORY_OUTPUT = os.path.dirname(modules.globals.output_path)
        start()

def check_and_ignore_nsfw(target, destroy: Callable = None) -> bool:
    ''' Check if the target is NSFW.
    TODO: Consider to make blur the target.
    '''
    from numpy import ndarray
    from modules.predicter import predict_image, predict_video, predict_frame
    if type(target) is str: # image/video file path
        check_nsfw = predict_image if has_image_extension(target) else predict_video
    elif type(target) is ndarray: # frame object
        check_nsfw = predict_frame
    if check_nsfw and check_nsfw(target):
        if destroy: destroy(to_quit=False) # Do not need to destroy the window frame if the target is NSFW
        update_status('Processing ignored!')
        return True
    else: return False


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

def render_image_preview(image_path: str, size: Tuple[int, int]) -> ctk.CTkImage:
    image = Image.open(image_path)
    if size:
        image = ImageOps.fit(image, size, Image.LANCZOS)
    return ctk.CTkImage(image, size=image.size)

def render_video_preview(video_path: str, size: Tuple[int, int], frame_number: int = 0) -> ctk.CTkImage:
    capture = cv2.VideoCapture(video_path)
    if frame_number:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    has_frame, frame = capture.read()
    if has_frame:
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if size:
            image = ImageOps.fit(image, size, Image.LANCZOS)
        return ctk.CTkImage(image, size=image.size)
    capture.release()
    cv2.destroyAllWindows()

def toggle_preview() -> None:
    if PREVIEW.state() == 'normal':
        PREVIEW.withdraw()
    elif modules.globals.source_path and modules.globals.target_path:
        init_preview()
        update_preview()

def init_preview() -> None:
    if is_image(modules.globals.target_path):
        preview_slider.pack_forget()
    if is_video(modules.globals.target_path):
        video_frame_total = get_video_frame_total(modules.globals.target_path)
        preview_slider.configure(to=video_frame_total)
        preview_slider.pack(fill='x')
        preview_slider.set(0)

def update_preview(frame_number: int = 0) -> None:
    if modules.globals.source_path and modules.globals.target_path:
        update_status('Processing...')
        temp_frame = get_video_frame(modules.globals.target_path, frame_number)
        if modules.globals.nsfw_filter and check_and_ignore_nsfw(temp_frame):
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
        image = ImageOps.contain(image, (PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT), Image.LANCZOS)
        image = ctk.CTkImage(image, size=image.size)
        preview_label.configure(image=image)
        update_status('Processing succeed!')
        PREVIEW.deiconify()

def webcam_preview():
    if modules.globals.source_path is None:
        return
    global preview_label, PREVIEW, ROOT, camera
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

    # Set initial size of the preview window
    PREVIEW_WIDTH = 640
    PREVIEW_HEIGHT = 360
    camera = cv2.VideoCapture(0)
    update_camera_resolution()
    # Configure the preview window
    PREVIEW.deiconify()
    PREVIEW.geometry(f"{PREVIEW_WIDTH}x{PREVIEW_HEIGHT}")
    preview_label.configure(width=PREVIEW_WIDTH, height=PREVIEW_HEIGHT)
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
        fps_label.configure(text=f'FPS: {fps:.2f}')
        target_face1_value.configure(text=f': {modules.globals.target_face1_score:.2f}')
        target_face2_value.configure(text=f': {modules.globals.target_face2_score:.2f}')
        # Get current preview window size
        current_width = PREVIEW.winfo_width()
        current_height = PREVIEW.winfo_height()
        # Resize the processed frame to fit the current preview window size
        temp_frame = fit_image_to_preview(temp_frame, current_width, current_height)
        image = cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        image = ctk.CTkImage(image, size=(current_width, current_height))
        preview_label.configure(image=image, width=current_width, height=current_height)
        ROOT.update()
        if PREVIEW.state() == 'withdrawn':
            break
    camera.release()
    PREVIEW.withdraw()

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
    
    if PREVIEW.state() == 'normal':
        update_preview()

def update_camera_resolution():
    global camera, PREVIEW_DEFAULT_WIDTH, PREVIEW_DEFAULT_HEIGHT
    if camera is not None and camera.isOpened():
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, PREVIEW_DEFAULT_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, PREVIEW_DEFAULT_HEIGHT)
        camera.set(cv2.CAP_PROP_FPS, 60)  # You may want to make FPS configurable as well

def many_faces(*args):
    global face_tracking_value
    size = many_faces_var.get()
    modules.globals.many_faces = size  # Use boolean directly
    if size:  # If many faces is enabled
        # Disable face tracking
        modules.globals.face_tracking = False
        face_tracking_value.set(False)  # Update the switch state
        pseudo_face_var.set(False)  # Update the switch state
        face_tracking()  # Call face_tracking to update UI elements

def face_tracking(*args):
    global pseudo_face_switch, stickiness_dropdown, pseudo_threshold_dropdown, clear_tracking_button,pseudo_face_var
    global many_faces_var,embedding_weight_size_dropdown,weight_distribution_size_dropdown,position_size_dropdown
    global old_embedding_size_dropdown,new_embedding_size_dropdown
    
    
    size = face_tracking_value.get()
    modules.globals.face_tracking = size  # Use boolean directly
    modules.globals.face_tracking_value = size

    if size:  # If face tracking is enabled
        # Disable many faces
        modules.globals.many_faces = False
        many_faces_var.set(False)  # Update the many faces switch state
    
    # Enable/disable UI elements based on face tracking state
    if size:  # If face tracking is enabled
        pseudo_face_switch.configure(state="normal")
        stickiness_dropdown.configure(state="normal")
        pseudo_threshold_dropdown.configure(state="normal")
        clear_tracking_button.configure(state="normal")
        embedding_weight_size_dropdown.configure(state="normal")
        weight_distribution_size_dropdown.configure(state="normal")
        position_size_dropdown.configure(state="normal")
        old_embedding_size_dropdown.configure(state="normal")
        new_embedding_size_dropdown.configure(state="normal")
    else:  # If face tracking is disabled
        pseudo_face_switch.configure(state="disabled")
        stickiness_dropdown.configure(state="disabled")
        pseudo_threshold_dropdown.configure(state="disabled")
        clear_tracking_button.configure(state="disabled")
        embedding_weight_size_dropdown.configure(state="disabled")
        weight_distribution_size_dropdown.configure(state="disabled")
        position_size_dropdown.configure(state="disabled")
        old_embedding_size_dropdown.configure(state="disabled")
        new_embedding_size_dropdown.configure(state="disabled")
        pseudo_face_var.set(False)  # Update the switch state

    clear_face_tracking_data()

def mask_size(*args):
    size = mask_size_var.get()
    modules.globals.mask_size = int(size)

def mask_down_size(*args):
    size = mask_down_size_var.get()
    modules.globals.mask_down_size = float(size)

def mask_feather_ratio_size(*args):
    size = mask_feather_ratio_var.get()
    modules.globals.mask_feather_ratio = int(size)

def stickyface_size(*args):
    size = stickyface_var.get()
    modules.globals.sticky_face_value = float(size)
    
def flip_faces(*args):
    size = flip_faces_value.get()
    modules.globals.flip_faces = int(size)
    modules.globals.flip_faces_value = True
    if modules.globals.face_tracking:
        clear_face_tracking_data()

def detect_faces_right(*args):
    size = detect_face_right_value.get()
    modules.globals.detect_face_right = int(size)
    modules.globals.detect_face_right_value = True
    if modules.globals.face_tracking:
        clear_face_tracking_data()


def stickiness_factor_size(*args):
    size = stickyface_var.get()
    modules.globals.sticky_face_value = float(size)

def pseudo_threshold_size(*args):
    size = pseudo_threshold_var.get()
    modules.globals.pseudo_face_threshold = float(size)

def clear_face_tracking_data(*args):
    frame_processors = get_frame_processors_modules(modules.globals.frame_processors)
    for frame_processor in frame_processors:
        if hasattr(frame_processor, 'reset_face_tracking'):
                frame_processor.reset_face_tracking()
