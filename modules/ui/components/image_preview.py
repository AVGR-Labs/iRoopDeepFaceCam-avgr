
import customtkinter as ctk
import modules.ui.ui_globals as ui
import modules.ui.component as c
def image_component(component):
    
 # Image preview area
  component.source_label = ctk.CTkLabel(component.root, text=None)
  component.source_label.place(relx=0.03, rely=ui.y_start + 0.40*ui.y_increment, relwidth=0.40, relheight=0.15)
  component.target_label = ctk.CTkLabel(component.root, text=None)
  component.target_label.place(relx=0.58, rely=ui.y_start + 0.40*ui.y_increment, relwidth=0.40, relheight=0.15)
  return component