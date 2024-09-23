
import customtkinter as ctk

import modules.ui.component as c
def info_component(component):
    component.info_label = ctk.CTkLabel(component.root, text='Webcam takes 30 seconds to start on first face detection', justify='center')
    component.info_label.place(relx=0, rely=0, relwidth=1)
    component.fps_label = ctk.CTkLabel(component.root, text='FPS:  ', justify='center',font=("Arial", 12))
    component.fps_label.place(relx=0, rely=0.04, relwidth=1)
    return component