

import customtkinter as ctk
import modules.ui.ui_globals as ui
import modules.globals

import modules.ui.component as c

import modules.ui.commands as cmd
from modules.utilities.env import Enviroment
def left_collum_component(component):
    component.use_folder_as_source = ctk.BooleanVar(value=modules.globals.use_source_folder)
    component.use_folder_as_source_switch = ctk.CTkSwitch(component.root, text='Use folder as source', variable=component.use_folder_as_source, cursor='hand2', command=lambda: cmd.toggle_source_mode(component.use_folder_as_source.get()))
    component.use_folder_as_source_switch.place(relx=0.03, rely=ui.y_start + 4.6*ui.y_increment, relwidth=0.8)
    
    component.use_folder_as_target = ctk.BooleanVar(value=modules.globals.use_target_folder)
    component.use_folder_as_target_switch = ctk.CTkSwitch(component.root, text='Use folder as target', variable=component.use_folder_as_target, cursor='hand2', command=lambda: cmd.toggle_target_mode(component.use_folder_as_target.get()))
    component.use_folder_as_target_switch.place(relx=0.55, rely=ui.y_start + 4.6*ui.y_increment, relwidth=0.2)
    
    # Left column of switches
    component.both_faces_var = ctk.BooleanVar(value=modules.globals.both_faces)
    component.both_faces_switch = ctk.CTkSwitch(component.root, text='Show Both Faces', variable=component.both_faces_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'both_faces', component.both_faces_var.get()))
    component.both_faces_switch.place(relx=0.03, rely=ui.y_start + 5.2*ui.y_increment, relwidth=0.8)

    component.flip_faces_value = ctk.BooleanVar(value=modules.globals.flip_faces)
    component.flip_faces_switch = ctk.CTkSwitch(component.root, text='Flip Left/Right Faces', variable=component.flip_faces_value, cursor='hand2',
                                    command=lambda: cmd.flip_faces('flip_faces', component.flip_faces_value.get()))
    component.flip_faces_switch.place(relx=0.03, rely=ui.y_start + 5.8*ui.y_increment, relwidth=0.4)

    component.detect_face_right_value = ctk.BooleanVar(value=modules.globals.detect_face_right)
    component.detect_face_right_switch = ctk.CTkSwitch(component.root, text='Detect Face From Right', variable=component.detect_face_right_value, cursor='hand2',
                                    command=lambda: cmd.detect_faces_right('detect_face_right', component.detect_face_right_value.get()))
    component.detect_face_right_switch.place(relx=0.03, rely=ui.y_start + 6.4*ui.y_increment, relwidth=0.4)

    component.many_faces_var = ctk.BooleanVar(value=modules.globals.many_faces)
    component.many_faces_switch = ctk.CTkSwitch(component.root, text='Many Faces', variable=component.many_faces_var, cursor='hand2',
                                    command=lambda: many_faces('many_faces', component.many_faces_var.get()))
    component.many_faces_switch.place(relx=0.03, rely=ui.y_start + 7*ui.y_increment, relwidth=0.8)

    component.show_target_face_box_var = ctk.BooleanVar(value=modules.globals.show_target_face_box)
    component.show_target_face_box_switch = ctk.CTkSwitch(component.root, text='Show InsightFace Landmarks', variable=component.show_target_face_box_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'show_target_face_box', component.show_target_face_box_var.get()))
    component.show_target_face_box_switch.place(relx=0.03, rely=ui.y_start + 7.6*ui.y_increment, relwidth=0.8)

    component.show_mouth_mask_var = ctk.BooleanVar(value=modules.globals.show_mouth_mask_box)
    component.show_mouth_mask_switch = ctk.CTkSwitch(component.root, text='Show Mouth Mask Box', variable=component.show_mouth_mask_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'show_mouth_mask_box', component.show_mouth_mask_var.get()))
    component.show_mouth_mask_switch.place(relx=0.03, rely=ui.y_start + 8.2*ui.y_increment, relwidth=0.8)
    return component
 
def middle_collum_component(component):
  
    # Middle column of switches
    component.live_flip_x_var = ctk.BooleanVar(value=modules.globals.flip_x)
    component.live_flip_x_vswitch = ctk.CTkSwitch(component.root, text='Flip X', variable=component.live_flip_x_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'flip_x', component.live_flip_x_var.get()))
    component.live_flip_x_vswitch.place(relx=0.55, rely=ui.y_start + 5.2*ui.y_increment, relwidth=0.2)

    component.live_flip_y_var = ctk.BooleanVar(value=modules.globals.flip_y)
    component.live_flip_y_switch = ctk.CTkSwitch(component.root, text='Flip Y', variable=component.live_flip_y_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals.l, 'flip_y', component.live_flip_y_var.get()))
    component.live_flip_y_switch.place(relx=0.55, rely=ui.y_start + 5.8*ui.y_increment, relwidth=0.2)

    component.keep_fps_var = ctk.BooleanVar(value=modules.globals.keep_fps)
    component.keep_fps_switch = ctk.CTkSwitch(component.root, text='Keep fps', variable=component.keep_fps_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'keep_fps', component.keep_fps_var.get()))
    component.keep_fps_switch.place(relx=0.55, rely=ui.y_start + 6.4*ui.y_increment, relwidth=0.4)

    component.keep_audio_var = ctk.BooleanVar(value=modules.globals.keep_audio)
    component.keep_audio_switch = ctk.CTkSwitch(component.root, text='Keep Audio', variable=component.keep_audio_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'keep_audio', component.keep_audio_var.get()))
    component.keep_audio_switch.place(relx=0.55, rely=ui.y_start + 7*ui.y_increment, relwidth=0.4)

    component.keep_frames_var = ctk.BooleanVar(value=modules.globals.keep_frames)
    component.keep_frames_switch = ctk.CTkSwitch(component.root, text='Keep Frames', variable=component.keep_frames_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'keep_frames', component.keep_frames_var.get()))
    component.keep_frames_switch.place(relx=0.55, rely=ui.y_start + 7.6*ui.y_increment, relwidth=0.4)

    component.nsfw_filter_var = ctk.BooleanVar(value=modules.globals.nsfw_filter)
    component.nsfw_filter_switch = ctk.CTkSwitch(component.root, text='NSFW Filter', variable=component.nsfw_filter_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'nsfw_filter', component.nsfw_filter_var.get()))
    component.nsfw_filter_switch.place(relx=0.55, rely=ui.y_start + 8.2*ui.y_increment, relwidth=0.4)
 
    component.enhancer_value = ctk.BooleanVar(value=modules.globals.fp_ui['face_enhancer'])
    component.enhancer_switch = ctk.CTkSwitch(component.root, text='Face Enhancer', variable=component.enhancer_value, cursor='hand2',
                                    command=lambda: update_tumbler('face_enhancer', component.enhancer_value.get()))
    component.enhancer_switch.place(relx=0.55, rely=ui.y_start + 8.8*ui.y_increment, relwidth=0.4)
    return component

    
def right_collum_component(component):
    # Right collum 
    component.use_default_os_envs = ctk.BooleanVar(value=modules.globals.use_default_folders)
    component.use_default_os_envs_switch = ctk.CTkSwitch(component.root, text='Use default input/outputs\n (if set. See docs)', variable=component.use_default_os_envs, cursor='hand2', command=lambda: toggle_default_mode(component.use_default_os_envs.get()))
    component.use_default_os_envs_switch.place(relx=0.80, rely=ui.y_start + 5.2*ui.y_increment, relwidth=0.2)
    return component

def update_tumbler(var: str, value: bool) -> None:
    modules.globals.fp_ui[var] = value


def many_faces(*args):
    size = c.many_faces_var.get()
    modules.globals.many_faces = size  # Use boolean directly
    if size:  # If many faces is enabled
        # Disable face tracking
        modules.globals.face_tracking = False
        c.face_tracking_value.set(False)  # Update the switch state
        c.pseudo_face_var.set(False)  # Update the switch state
        c.face_tracking()  # Call face_tracking to update UI elements
def toggle_default_mode(use_defaults: bool) -> None:
    global Enviroment
    env = Enviroment()
    if use_defaults:
        if env.ready(target='DEFAULT_SOURCE'):
            modules.globals.source_folder_path = env.ReturnAndClear()
            cmd.toggle_source_mode(True)
        if env.ready(target='DEFAULT_TARGET'):
            modules.globals.target_folder_path = env.ReturnAndClear()
            cmd.toggle_target_mode(True)
        if env.ready(target='DEFAULT_OUTPUT'):
            modules.globals.output_path = env.ReturnAndClear()
    else:
        cmd.toggle_source_mode(False)
        cmd.toggle_target_mode(False)
        