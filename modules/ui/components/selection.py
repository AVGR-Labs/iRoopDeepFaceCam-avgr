
import customtkinter as ctk
import modules.ui.ui_globals as ui
import modules.ui.utility as util

import modules.ui.component as c
import modules.ui.commands as cmd
    
from modules.ui.preview import preview, render
def selection_component(component):
    

 # Buttons for selecting source and target
    component.select_face_button = ctk.CTkButton(component.root, text='Select a face/s\n( left face ) ( right face )', cursor='hand2', command=lambda: cmd.select_source_path())
    component.select_face_button.place(relx=0.05, rely=ui.y_start + 3.35*ui.y_increment, relwidth=0.36, relheight=0.06)

    component.swap_faces_button = ctk.CTkButton(component.root, text='↔', cursor='hand2', command=lambda: util.swap_faces_paths())
    component.swap_faces_button.place(relx=0.46, rely=ui.y_start + 3.35*ui.y_increment, relwidth=0.10, relheight=0.06)

    component.select_target_button = ctk.CTkButton(component.root, text='Select a target\n( Image / Video )', cursor='hand2', command=lambda: cmd.select_target_path())
    component.select_target_button.place(relx=0.60, rely=ui.y_start + 3.35*ui.y_increment, relwidth=0.36, relheight=0.06)
    
   