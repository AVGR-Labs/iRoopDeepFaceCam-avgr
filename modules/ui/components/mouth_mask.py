

import customtkinter as ctk
import modules.ui.ui_globals as ui
import modules.globals



import modules.ui.component as c
def mouth_mask_component(component):
    

    ##### Mouth Mask Frame

    # Outline frame for mouth mask and dropdown
    component.outline_frame = ctk.CTkFrame(component.root, fg_color="transparent", border_width=1, border_color="grey")
    component.outline_frame.place(relx=0.02, rely=ui.y_start + 9.3*ui.y_increment, relwidth=0.96, relheight=0.05)

    # Mouth mask switch
    component.mouth_mask_var = ctk.BooleanVar(value=modules.globals.mouth_mask)
    component.mouth_mask_switch = ctk.CTkSwitch(component.outline_frame, text='Mouth Mask | Feather, Padding, Top ->', variable=component.mouth_mask_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'mouth_mask', component.mouth_mask_var.get()))
    component.mouth_mask_switch.place(relx=0.02, rely=0.5, relwidth=0.6, relheight=0.5, anchor="w")

    # Size dropdown (rightmost)
    component.mask_size_var = ctk.StringVar(value="1")
    component.mask_size_dropdown = ctk.CTkOptionMenu(component.outline_frame, values=["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20"],
                                            variable=component.mask_size_var,
                                            command=mask_size)
    component.mask_size_dropdown.place(relx=0.98, rely=0.5, relwidth=0.1, anchor="e")
 
    # Down size dropdown
    component.mask_down_size_var = ctk.StringVar(value="0.50")
    component.mask_down_size_dropdown = ctk.CTkOptionMenu(component.outline_frame, values=["0.01","0.02","0.03","0.04","0.05","0.06","0.07","0.08","0.09","0.10","0.15","0.20","0.25","0.30","0.35","0.40","0.45","0.50","0.55","0.60","0.65","0.70","0.75","0.80","0.85","0.90","0.95","1.00","1.25","1.50","1.75","2.00","2.25","2.50","2.75","3.00"],
                                            variable=component.mask_down_size_var,
                                            command=mask_down_size)
    component.mask_down_size_dropdown.place(relx=0.87, rely=0.5, relwidth=0.12, anchor="e")

    # Feather ratio dropdown
    component.mask_feather_ratio_var = ctk.StringVar(value="8")
    component.mask_feather_ratio_size_dropdown = ctk.CTkOptionMenu(component.outline_frame, values=["1","2","3","4","5","6","7","8","9","10"],
                                            variable=component.mask_feather_ratio_var,
                                            command=mask_feather_ratio_size)
    component.mask_feather_ratio_size_dropdown.place(relx=0.76, rely=0.5, relwidth=0.1,  anchor="e")



def mask_size(*args):
    size = c.Component().mask_size_var.get()
    modules.globals.mask_size = int(size)

def mask_down_size(*args):
    size =  c.Component().mask_down_size_var.get()
    modules.globals.mask_down_size = float(size)

def mask_feather_ratio_size(*args):
    size =  c.Component().mask_feather_ratio_var.get()
    modules.globals.mask_feather_ratio = int(size)
