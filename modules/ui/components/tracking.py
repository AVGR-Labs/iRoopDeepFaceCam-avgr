


import customtkinter as ctk
import modules.ui.ui_globals as ui
import modules.globals

import modules.ui.component as c
import modules.ui.commands as cmd
def tracking_component(component):
    
    ##### Face Tracking Frame

    # Outline frame for face tracking
    component.outline_face_track_frame = ctk.CTkFrame(component.root, fg_color="transparent", border_width=1, border_color="grey")
    component.outline_face_track_frame.place(relx=0.02, rely=ui.y_start + 10.3*ui.y_increment, relwidth=0.96, relheight=0.24)

     # Face Tracking switch
    component.face_tracking_value = ctk.BooleanVar(value=component.face_tracking)
    component.face_tracking_switch = ctk.CTkSwitch(component.outline_face_track_frame, text='Auto Face Track', variable=component.face_tracking_value, cursor='hand2',
                                    command=lambda: modules.globals.face_tracking('face_tracking', component.face_tracking_value.get()))
    component.face_tracking_switch.place(relx=0.02, rely=0.1, relwidth=0.4)
 
    # Pseudo Face switch
    component.pseudo_face_var = ctk.BooleanVar(value=component.use_pseudo_face)
    component.pseudo_face_switch = ctk.CTkSwitch(component.outline_face_track_frame, text='Pseudo Face\n(fake face\nfor occlusions)', variable=component.pseudo_face_var, cursor='hand2',
                                    command=lambda: setattr(modules.globals, 'use_pseudo_face', component.pseudo_face_var.get()))
    component.pseudo_face_switch.place(relx=0.02, rely=0.3, relwidth=0.4)


    # Red box frame
    component.red_box_frame = ctk.CTkFrame(component.outline_face_track_frame, fg_color="transparent", border_width=1, border_color="#800000")
    component.red_box_frame.place(relx=0.33, rely=0.02, relwidth=0.28, relheight=0.65)
   
    # Face Cosine Similarity label
    component.similarity_label = ctk.CTkLabel(component.red_box_frame, text="Similarity * Position",font=("Arial", 14) )
    component.similarity_label.place(relx=0.05, rely=0.01, relwidth=0.85 )
    # Target Face 1 label and value
    component.target_face1_label = ctk.CTkLabel(component.red_box_frame, text="Target Face 1:", font=("Arial", 12))
    component.target_face1_label.place(relx=0.05, rely=0.18, relwidth=0.6)

    component.target_face1_value = ctk.CTkLabel(component.red_box_frame, text="0.00", anchor="w")
    component.target_face1_value.place(relx=0.65, rely=0.18, relwidth=0.3)

    # Target Face 2 label and value
    component.target_face2_label = ctk.CTkLabel(component.red_box_frame, text="Target Face 2:", font=("Arial", 12))
    component.target_face2_label.place(relx=0.05, rely=0.33, relwidth=0.6)

    component.target_face2_value = ctk.CTkLabel(component.red_box_frame, text="0.00", anchor="w")
    component.target_face2_value.place(relx=0.65, rely=0.33, relwidth=0.3)

        # Target Face 2 label and value
    component.target_face2_label = ctk.CTkLabel(component.red_box_frame, text="* MAX TWO FACE ON\nSCREEN DETECTED FROM\nLEFT OR RIGHT *", font=("Arial", 10))
    component.target_face2_label.place(relx=0.05, rely=0.60, relwidth=0.9)

 
    # Stickiness Factor label
    component.stickiness_label = ctk.CTkLabel(component.outline_face_track_frame, text="Stickiness Factor",font=("Arial", 14))
    component.stickiness_label.place(relx=0.72, rely=0.01, relwidth=0.2)

    # Stickiness Greater label
    component.stickiness_greater_label = ctk.CTkLabel(component.outline_face_track_frame, text=">",font=("Arial", 14))
    component.stickiness_greater_label.place(relx=0.65, rely=0.14, relwidth=0.1)

    # Stickiness Factor dropdown
    component.stickyface_var = ctk.StringVar(value="0.20")
    component.stickiness_dropdown = ctk.CTkOptionMenu(component.outline_face_track_frame, values=["0.05","0.10","0.15","0.20","0.25","0.30","0.35","0.40","0.45","0.50","0.55","0.60","0.65","0.70","0.75","0.80","0.85","0.90","0.95","1.00"],
                                            variable=component.stickyface_var,
                                            command=cmd.stickiness_factor_size)
    component.stickiness_dropdown.place(relx=0.75, rely=0.14, relwidth=0.15)


    # Stickiness Greater label
    component.pseudo_threshold_greater_label = ctk.CTkLabel(component.outline_face_track_frame, text="<",font=("Arial", 14))
    component.pseudo_threshold_greater_label.place(relx=0.65, rely=0.30, relwidth=0.1)

    # Pseudo Threshold dropdown
    component.pseudo_threshold_var = ctk.StringVar(value="0.20")
    component.pseudo_threshold_dropdown = ctk.CTkOptionMenu(component.outline_face_track_frame, values=["0.05","0.10","0.15","0.20","0.25","0.30","0.35","0.40","0.45","0.50","0.55","0.60","0.65","0.70","0.75","0.80","0.85","0.90","0.95","1.00"],
                                                variable=component.pseudo_threshold_var,
                                                command=cmd.pseudo_threshold_size)
    component.pseudo_threshold_dropdown.place(relx=0.75, rely=0.30, relwidth=0.15)

    # Pseudo Threshold label
    component.pseudo_threshold_label = ctk.CTkLabel(component.outline_face_track_frame, text="Pseudo Threshold",font=("Arial", 14))
    component.pseudo_threshold_label.place(relx=0.72, rely=0.42, relwidth=0.2)


    # Clear Face Tracking Data button
    component.clear_tracking_button = ctk.CTkButton(component.outline_face_track_frame, text="Reset Face Tracking", 
                                        command=cmd.clear_face_tracking_data)
    component.clear_tracking_button.place(relx=0.65, rely=0.55, relwidth=0.34)

    component.track_settings_label = ctk.CTkLabel(component.outline_face_track_frame, text="Embedding Weight   *   Weight Distribution   +   Position Weight            Old Weight   +   New Weight", font=("Arial", 12))
    component.track_settings_label.place(relx=0.01, rely=0.68, relwidth=0.96)


    component.embedding_weight_size_var = ctk.StringVar(value="0.60")
    component.embedding_weight_size_dropdown = ctk.CTkOptionMenu(component.outline_face_track_frame, values=["0.05","0.10","0.15","0.20","0.25","0.30","0.35","0.40","0.45","0.50","0.55","0.60","0.65","0.70","0.75","0.80","0.85","0.90","0.95","1.00"],
                                            variable=component.embedding_weight_size_var,
                                            command=cmd.embedding_weight_size)
    component.embedding_weight_size_dropdown.place(relx=0.03, rely=0.84, relwidth=0.13)

    component.weight_distribution_size_var = ctk.StringVar(value="1.00")
    component.weight_distribution_size_dropdown = ctk.CTkOptionMenu(component.outline_face_track_frame, values=["0.05","0.15","0.25","0.35","0.45","0.55","0.65","0.75","0.85","0.95","1.00","1.25","1.50","1.75","2.00","2.25","2.50","2.75","3.00","3.25","3.50","3.75","4.00","4.25","4.50","4.75","5.00"],
                                            variable=component.weight_distribution_size_var,
                                            command=cmd.weight_wistribution_size)
    component.weight_distribution_size_dropdown.place(relx=0.25, rely=0.84, relwidth=0.13)

    # Down size dropdown
    component.position_size_var = ctk.StringVar(value="0.40")
    component.position_size_dropdown = ctk.CTkOptionMenu(component.outline_face_track_frame, values=["0.05","0.10","0.15","0.20","0.25","0.30","0.35","0.40","0.45","0.50","0.55","0.60","0.65","0.70","0.75","0.80","0.85","0.90","0.95","1.00"],
                                            variable=component.position_size_var,
                                            command=cmd.position_size)
    component.position_size_dropdown.place(relx=0.48, rely=0.84, relwidth=0.13)

    # Feather ratio dropdown
    component.old_embedding_size_var = ctk.StringVar(value="0.90")
    component.old_embedding_size_dropdown = ctk.CTkOptionMenu(component.outline_face_track_frame, values=["0.05","0.10","0.15","0.20","0.25","0.30","0.35","0.40","0.45","0.50","0.55","0.60","0.65","0.70","0.75","0.80","0.85","0.90","0.95","1.00"],
                                            variable=component.old_embedding_size_var,
                                            command=cmd.old_embedding_size)
    component.old_embedding_size_dropdown.place(relx=0.68, rely=0.84, relwidth=0.13)

    # Feather ratio dropdown
    component.new_embedding_size_var = ctk.StringVar(value="0.10")
    component.new_embedding_size_dropdown = ctk.CTkOptionMenu(component.outline_face_track_frame, values=["0.05","0.10","0.15","0.20","0.25","0.30","0.35","0.40","0.45","0.50","0.55","0.60","0.65","0.70","0.75","0.80","0.85","0.90","0.95","1.00"],
                                            variable=component.new_embedding_size_var,
                                            command=cmd.new_embedding_size)
    component.new_embedding_size_dropdown.place(relx=0.84, rely=0.84, relwidth=0.13)
