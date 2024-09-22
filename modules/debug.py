import modules.globals

enabled = None
def print(msg):
    global enabled
    if enabled:
        print(msg)
def print_debug():
    """
    Prints a detailed debug message with the current values of all the key parameters
    from the modules.globals.
    """
    debug_info = {
        "source_folder_path": modules.globals.source_folder_path,
        "target_folder_path": modules.globals.target_folder_path,
        "use_source_folder": modules.globals.use_source_folder,
        "use_target_folder": modules.globals.use_target_folder,
        "use_default_folders": modules.globals.use_default_folders,
        "source_path": modules.globals.source_path,
        "target_path": modules.globals.target_path,
        "output_path": modules.globals.output_path,
        "frame_processors": modules.globals.frame_processors,
        "keep_fps": modules.globals.keep_fps,
        "keep_audio": modules.globals.keep_audio,
        "keep_frames": modules.globals.keep_frames,
        "many_faces": modules.globals.many_faces,
        "nsfw_filter": modules.globals.nsfw_filter,
        "video_encoder": modules.globals.video_encoder,
        "video_quality": modules.globals.video_quality,
        "live_mirror": modules.globals.live_mirror,
        "flip_y": modules.globals.flip_y,
        "flip_x": modules.globals.flip_x,
        "live_resizable": modules.globals.live_resizable,
        "max_memory": modules.globals.max_memory,
        "execution_providers": modules.globals.execution_providers,
        "execution_threads": modules.globals.execution_threads,
        "headless": modules.globals.headless,
        "log_level": modules.globals.log_level,
        "fp_ui": modules.globals.fp_ui,
        "camera_input_combobox": modules.globals.camera_input_combobox,
        "webcam_preview_running": modules.globals.webcam_preview_running,
        "both_faces": modules.globals.both_faces,
        "flip_faces": modules.globals.flip_faces,
        "detect_face_right": modules.globals.detect_face_right,
        "detect_face_right_value": modules.globals.detect_face_right_value,
        "show_target_face_box": modules.globals.show_target_face_box,
        "mouth_mask": modules.globals.mouth_mask,
        "mask_feather_ratio": modules.globals.mask_feather_ratio,
        "mask_down_size": modules.globals.mask_down_size,
        "mask_size": modules.globals.mask_size,
        "show_mouth_mask_box": modules.globals.show_mouth_mask_box,
        "flip_faces_value": modules.globals.flip_faces_value,
        "sticky_face_value": modules.globals.sticky_face_value,
        "use_pseudo_face": modules.globals.use_pseudo_face,
        "pseudo_face_threshold": modules.globals.pseudo_face_threshold,
        "max_pseudo_face_count": modules.globals.max_pseudo_face_count,
        "face_tracking": modules.globals.face_tracking,
        "face_tracking_value": modules.globals.face_tracking_value,
        "target_face1_score": modules.globals.target_face1_score,
        "target_face2_score": modules.globals.target_face2_score,
        "target_face_left_embedding": modules.globals.target_face_left_embedding,
        "target_face_right_embedding": modules.globals.target_face_right_embedding,
        "source_face_left_embedding": modules.globals.source_face_left_embedding,
        "source_face_right_embedding": modules.globals.source_face_right_embedding,
        "target_face": modules.globals.target_face,
        "embedding_weight_size": modules.globals.embedding_weight_size,
        "weight_distribution_size": modules.globals.weight_distribution_size,
        "position_size": modules.globals.position_size,
        "old_embedding_weight": modules.globals.old_embedding_weight,
        "new_embedding_weight": modules.globals.new_embedding_weight,
    }
    # Print the debug message
    print("Debug Information:")
    for key, value in debug_info.items():
        print(f"{key}: {value}")