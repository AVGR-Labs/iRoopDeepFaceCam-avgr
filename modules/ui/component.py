import customtkinter as ctk

def Init(r: ctk.CTk):
    
    global face_tracking, root, use_default_os_envs, use_pseudo_face, source_label, target_label, info_label
    global fps_label, select_face_button, swap_faces_button, select_target_button, outline_face_track_frame
    global face_tracking_value, face_tracking_switch, live_flip_x_var, live_flip_y_var, keep_fps_var
    global keep_audio_var, keep_frames_var, nsfw_filter_var, enhancer_value, use_default_os_envs_switch
    global live_flip_x_vswitch, live_flip_y_switch, keep_fps_switch, keep_audio_switch, keep_frames_switch
    global nsfw_filter_switch, enhancer_switch, use_folder_as_source, use_folder_as_target, both_faces_var
    global flip_faces_value, detect_face_right_value, many_faces_var, show_target_face_box_var, show_mouth_mask_var
    global use_folder_as_source_switch, use_folder_as_target_switch, both_faces_switch, flip_faces_switch
    global detect_face_right_switch, many_faces_switch, show_target_face_box_switch, show_mouth_mask_switch
    global outline_frame, mouth_mask_switch, mouth_mask_var, mask_size_var, mask_size_dropdown, mask_down_size_var
    global mask_down_size_dropdown, mask_feather_ratio_var, mask_feather_ratio_size_dropdown, red_box_frame
    global similarity_label, target_face1_label, target_face1_value, target_face2_label, target_face2_value
    global stickiness_label, stickiness_greater_label, stickyface_var, stickiness_dropdown, pseudo_threshold_greater_label
    global pseudo_threshold_var, pseudo_threshold_dropdown, pseudo_threshold_label, clear_tracking_button
    global track_settings_label, embedding_weight_size_var, embedding_weight_size_dropdown, weight_distribution_size_var
    global weight_distribution_size_dropdown, position_size_var, position_size_dropdown, old_embedding_size_var
    global old_embedding_size_dropdown, new_embedding_size_var, new_embedding_size_dropdown

    root=r
    face_tracking = None
    use_pseudo_face = False
    source_label = ctk.CTkLabel(master=root) 
    target_label = ctk.CTkLabel(master=root) 
    info_label = ctk. CTkLabel(master=root) 
    fps_label = ctk. CTkLabel(master=root) 
    # Settings
    select_face_button = ctk.CTkButton(master=root) 
    swap_faces_button = ctk.CTkButton(master=root) 
    select_target_button = ctk.CTkButton(master=root) 
    outline_face_track_frame = None
    face_tracking_value = None
    face_tracking_switch = ctk.CTkSwitch(master=root) 
    
    use_default_os_envs = ctk.BooleanVar(master=root) 
    live_flip_x_var = ctk.BooleanVar(master=root) 
    live_flip_y_var = ctk.BooleanVar(master=root) 
    keep_fps_var = ctk.BooleanVar(master=root) 
    keep_audio_var = ctk.BooleanVar(master=root) 
    keep_frames_var = ctk.BooleanVar(master=root) 
    nsfw_filter_var = ctk.BooleanVar(master=root) 
    enhancer_value = ctk.BooleanVar(master=root) 
    
    use_default_os_envs_switch = ctk.CTkSwitch(master=root) 
    live_flip_x_vswitch = ctk.CTkSwitch(master=root) 
    live_flip_y_switch = ctk.CTkSwitch(master=root) 
    keep_fps_switch = ctk.CTkSwitch(master=root) 
    keep_audio_switch = ctk.CTkSwitch(master=root) 
    keep_frames_switch = ctk.CTkSwitch(master=root) 
    nsfw_filter_switch = ctk.CTkSwitch(master=root) 
    enhancer_switch = ctk.CTkSwitch(master=root) 
    
    
    use_folder_as_source = ctk.BooleanVar(master=root) 
    use_folder_as_target = ctk.BooleanVar(master=root) 
    both_faces_var = ctk.BooleanVar(master=root) 
    flip_faces_value = ctk.BooleanVar(master=root) 
    detect_face_right_value = ctk.BooleanVar(master=root) 
    many_faces_var = ctk.BooleanVar(master=root) 
    show_target_face_box_var = ctk.BooleanVar(master=root) 
    show_mouth_mask_var = ctk.BooleanVar(master=root) 
    
    use_folder_as_source_switch = ctk.CTkSwitch(master=root) 
    use_folder_as_target_switch = ctk.CTkSwitch(master=root) 
    both_faces_switch = ctk.CTkSwitch(master=root) 
    flip_faces_switch = ctk.CTkSwitch(master=root) 
    detect_face_right_switch = ctk.CTkSwitch(master=root) 
    many_faces_switch = ctk.CTkSwitch(master=root) 
    show_target_face_box_switch = ctk.CTkSwitch(master=root) 
    show_mouth_mask_switch = ctk.CTkSwitch(master=root) 
    outline_frame = ctk.CTkFrame(master=root) 
    mouth_mask_switch = ctk.CTkSwitch(master=root) 
    mouth_mask_var = ctk.BooleanVar(master=root) 
    mask_size_var = ctk.StringVar(master=root) 
    mask_size_dropdown = ctk.CTkOptionMenu(master=root) 
    mask_down_size_var = ctk.StringVar(master=root) 
    mask_down_size_dropdown = ctk.CTkOptionMenu(master=root) 
    mask_feather_ratio_var = ctk.StringVar(master=root) 
    mask_feather_ratio_size_dropdown = ctk.CTkOptionMenu(master=root) 
    
    outline_face_track_frame = ctk.CTkFrame(master=root) 
    
    face_tracking_value = ctk.BooleanVar(master=root) 
    face_tracking_switch = ctk.CTkSwitch(master=root) 
    pseudo_face_var = ctk.BooleanVar(master=root) 
    pseudo_face_switch = ctk.CTkSwitch(master=root) 
    red_box_frame = ctk.CTkFrame(master=root) 
    similarity_label = ctk.CTkLabel(master=root) 
    target_face1_label = ctk.CTkLabel(master=root) 
    target_face1_value = ctk.CTkLabel(master=root) 
    target_face2_label = ctk.CTkLabel(master=root) 
    target_face2_value = ctk.CTkLabel(master=root) 
    target_face2_label = ctk.CTkLabel(master=root) 
    
    stickiness_label = ctk.CTkLabel(master=root) 
    stickiness_greater_label = ctk.CTkLabel(master=root) 
    stickyface_var = ctk.StringVar(master=root) 
    stickiness_dropdown = ctk.CTkOptionMenu(master=root) 
    pseudo_threshold_greater_label = ctk.CTkLabel(master=root) 
    pseudo_threshold_var = ctk.StringVar(master=root) 
    pseudo_threshold_dropdown = ctk.CTkOptionMenu(master=root) 
    
    
    pseudo_threshold_label = ctk.CTkLabel(master=root) 
    clear_tracking_button = ctk.CTkButton(master=root) 
    track_settings_label = ctk.CTkLabel(master=root) 
    embedding_weight_size_var = ctk.StringVar(master=root) 
    embedding_weight_size_dropdown = ctk.CTkOptionMenu(master=root) 
    weight_distribution_size_var = ctk.StringVar(master=root) 
    weight_distribution_size_dropdown = ctk.CTkOptionMenu(master=root) 
    
    position_size_var = ctk.StringVar(master=root) 
    position_size_dropdown = ctk.CTkOptionMenu(master=root) 
    old_embedding_size_var = ctk.StringVar(master=root) 
    old_embedding_size_dropdown = ctk.CTkOptionMenu(master=root) 
    new_embedding_size_var = ctk.StringVar(master=root) 
    new_embedding_size_dropdown = ctk.CTkOptionMenu(master=root) 
   
    return r