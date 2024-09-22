from typing import Any, List, Optional, Tuple
import cv2
import insightface
import threading
import os
import urllib
import modules.ai.processors.frame
import modules.ai.processors.frame.core
import modules.globals
import modules.ai.processors
from modules.ai.typing import Frame, Face
from modules.filehandle.path import  resolve_relative_path
from modules.filehandle.check import is_image, is_video
from modules.ai.face_analyser import get_one_face, get_many_faces, get_one_face_left, get_one_face_right, get_face_analyser
import  modules.utilities.download as download
from collections import deque
import numpy as np
import time

FACE_SWAPPER = None
# INSWAPPER_MODEL = 'inswapper_128_fp16.onnx' # Default
INSWAPPER_MODEL = 'inswapper_128.onnx'
THREAD_LOCK = threading.Lock()
NAME = 'DLC.FACE-SWAPPER'

COOLDOWN_PERIOD = 1.0  # 1 second cooldown
POSITION_WEIGHT = 0.4
EMBEDDING_WEIGHT = 0.6
BLUR_AMOUNT =12
MAX_LOST_COUNT = 1800  # Assuming 30 fps, this is 60 seconds
STICKINESS_FACTOR = 0.8  # Adjust this to change how "sticky" the tracking is

first_face_lost_count: int = 0
second_face_lost_count: int = 0
face_position_history = deque(maxlen=30)  # Stores last 30 positions
last_swap_time = 0

first_face_id: Optional[int] = None
second_face_id: Optional[int] = None
source_face_embeddings: List[np.ndarray] = []
first_face_embedding: Optional[np.ndarray] = None
second_face_embedding: Optional[np.ndarray] = None
first_face_position: Optional[Tuple[float, float]] = None
second_face_position: Optional[Tuple[float, float]] = None
position_threshold = 0.2  # Adjust this value to change sensitivity to position changes
last_assignment_time: float = 0
assignment_cooldown: float = 1.0  # 1 second cooldown

face_lost_count = 0

    
def pre_check() -> bool:
    
    if os.name == 'nt':
        download_directory_path = resolve_relative_path('..\models')
    else:
        download_directory_path = resolve_relative_path('../models')
    download.conditional(download_directory_path, ['https://huggingface.co/ivideogameboss/iroopdeepfacecam/blob/main/inswapper_128_fp16.onnx'])
    return True

def pre_start() -> bool:
    from modules.core import update_status
    if  modules.globals.target_folder_path:
        return True
    if not is_image(modules.globals.source_path):
        update_status('Select an image for source path.', NAME)
        return False
    elif not get_one_face(cv2.imread(modules.globals.source_path)):
        update_status('No face in source path detected.', NAME)
        return False
    if not is_image(modules.globals.target_path) and not is_video(modules.globals.target_path):
        update_status('Select an image or video for target path.', NAME)
        return False
    return True

def get_face_swapper() -> Any:
    global FACE_SWAPPER

    with THREAD_LOCK:
        if FACE_SWAPPER is None:
            model_path = resolve_relative_path(f'../models/{INSWAPPER_MODEL}')
            FACE_SWAPPER = insightface.model_zoo.get_model(model_path, providers=modules.globals.execution_providers)
    return FACE_SWAPPER

def swap_face(source_face: Face, target_face: Face, temp_frame: Frame) -> Frame:
    
    face_swapper = get_face_swapper()
    
    # Apply the face swap
    swapped_frame = face_swapper.get(temp_frame, target_face, source_face, paste_back=True)
    
    # Create a mask for the target face
    target_mask = create_face_mask(target_face, temp_frame)
    
    # Blur the edges of the mask
    blurred_mask = blur_edges(target_mask)
    blurred_mask = blurred_mask / 255.0
    
    # Ensure the mask has 3 channels to match the frame
    blurred_mask_3channel = np.repeat(blurred_mask[:, :, np.newaxis], 3, axis=2)
    
    # Blend the swapped face with the original frame using the blurred mask
    blended_frame = (swapped_frame * blurred_mask_3channel + 
                     temp_frame * (1 - blurred_mask_3channel))
    
    return blended_frame.astype(np.uint8)

def process_frame(source_face: List[Face], temp_frame: Frame) -> Frame:
    # Declare global variables used for face tracking
    global face_lost_count
    global first_face_embedding, second_face_embedding, first_face_position, second_face_position
    global first_face_id, second_face_id
    global first_face_lost_count, second_face_lost_count
    global face_position_history, last_swap_time

    #temp_frame = cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB)
    
    # Get the current time for tracking purposes
    current_time = time.time()
    
    # Get the face analyzer object to detect faces in the frame
    face_analyser = get_face_analyser()
       
    # Try to detect all faces in the current frame
    try:
        all_faces = face_analyser.get(temp_frame)
    except Exception as e:
        # If face detection fails, return the original frame without processing
        return temp_frame
    
    # Handle face tracking settings
    if modules.globals.face_tracking:
        # Reset face tracking if detect_face_right setting has changed
        if modules.globals.detect_face_right_value:
            reset_face_tracking()
            modules.globals.detect_face_right_value = False

        # Reset face tracking if flip_faces setting has changed
        if modules.globals.flip_faces_value:
            reset_face_tracking()
            modules.globals.flip_faces_value = False
        
        # Initialize pseudo face count for potential use in face tracking
        pseudo_face_count = 0 
    else:
        # If face tracking was previously enabled but now disabled, reset all tracking data
        if modules.globals.face_tracking_value:
            reset_face_tracking()   
            modules.globals.face_tracking_value = False

    # Determine which faces to process based on user settings
    if modules.globals.many_faces:
        # If 'many_faces' is enabled, process all detected faces
        # Sort faces from left to right based on their bounding box x-coordinate
        target_faces = sorted(all_faces, key=lambda face: face.bbox[0])
    elif modules.globals.both_faces:
        # If 'both_faces' is enabled, process two faces
        if modules.globals.detect_face_right:
            # If 'detect_face_right' is enabled, sort faces from right to left and take the two rightmost faces
            target_faces = sorted(all_faces, key=lambda face: -face.bbox[0])[:2]
        else:
            # Otherwise, sort faces from left to right and take the two leftmost faces
            target_faces = sorted(all_faces, key=lambda face: face.bbox[0])[:2]
    else:
        # If neither 'many_faces' nor 'both_faces' is enabled, process a single face
        if modules.globals.face_tracking:
            # Face tracking is enabled
            if first_face_embedding is None:
                # If no face is being tracked yet, start with either the leftmost or rightmost face
                if modules.globals.detect_face_right:
                    # Select the rightmost face if 'detect_face_right' is enabled
                    target_faces = [max(all_faces, key=lambda face: face.bbox[0])] if all_faces else []
                else:
                    # Otherwise, select the leftmost face
                    target_faces = [min(all_faces, key=lambda face: face.bbox[0])] if all_faces else []
            else:
                # If a face is already being tracked, find the best match based on face embedding
                best_match = find_best_match(first_face_embedding, all_faces)
                target_faces = [best_match] if best_match else []
        else:
            # Face tracking is disabled, simply select either the rightmost or leftmost face
            if modules.globals.detect_face_right:
                # Select the rightmost face if 'detect_face_right' is enabled
                target_faces = [max(all_faces, key=lambda face: face.bbox[0])] if all_faces else []
            else:
                # Otherwise, select the leftmost face
                target_faces = [min(all_faces, key=lambda face: face.bbox[0])] if all_faces else [] 

    # Limit the number of faces to process if not in 'many_faces' mode
    if modules.globals.many_faces is False:             
        # Limit to max two faces if both_faces is True, otherwise just one face
        max_faces = 2 if modules.globals.both_faces else 1
        target_faces = target_faces[:max_faces]
    
    # Pre-compute mouth masks if needed
    mouth_masks = []
    face_masks = []
    if modules.globals.mouth_mask:
        # Create mouth masks for each face based on the current mode (many_faces, both_faces, or single face)
        if modules.globals.many_faces:
            for face in target_faces:
                face_mask = create_face_mask(face, temp_frame)
                face_masks.append(face_mask)
                mouth_mask, mouth_cutout, mouth_box,lower_lip_polygon = create_lower_mouth_mask(face, temp_frame)
                mouth_masks.append((mouth_mask, mouth_cutout, mouth_box,lower_lip_polygon))
        elif modules.globals.both_faces:
            for face in target_faces[:2]:
                face_mask = create_face_mask(face, temp_frame)
                face_masks.append(face_mask)
                mouth_mask, mouth_cutout, mouth_box,lower_lip_polygon = create_lower_mouth_mask(face, temp_frame)
                mouth_masks.append((mouth_mask, mouth_cutout, mouth_box,lower_lip_polygon))
        else:
            face = target_faces[0] if target_faces else None
            if face:
                face_mask = create_face_mask(face, temp_frame)
                face_masks.append(face_mask)
                # mouth_mask, mouth_cutout, mouth_box = create_mouth_mask(face, temp_frame)
                mouth_mask, mouth_cutout, mouth_box,lower_lip_polygon = create_lower_mouth_mask(face, temp_frame)
                
                mouth_masks.append((mouth_mask, mouth_cutout, mouth_box,lower_lip_polygon))

    # Determine the active source face index and order
    active_source_index = 1 if modules.globals.flip_faces else 0
    source_face_order = [1, 0] if modules.globals.flip_faces else [0, 1]

    # Process faces
    if modules.globals.many_faces:
        # Process multiple faces
        for i, target_face in enumerate(target_faces):
            # Determine which source face to use
            if modules.globals.both_faces and len(source_face) > 1:
                source_index = source_face_order[i % 2]
            else:
                source_index = active_source_index  # Use the active source face for all targets
       
            # Face tracking is disabled, perform simple face swap
            # Crop the face region
            cropped_frame, crop_info = crop_face_region(temp_frame, target_face)
            # Create an adjusted face for the cropped region
            # Adjust the face bbox for the cropped frame
            adjusted_target_face = create_adjusted_face(target_face, crop_info)
            # Perform face swapping on the cropped region
            swapped_region = swap_face(source_face[source_index], adjusted_target_face, cropped_frame)

            # Create a mask for blending with blurred edges
            mask = create_edge_blur_mask(swapped_region.shape, blur_amount=BLUR_AMOUNT)
            
            # Blend the swapped region with the original cropped region
            blended_region = blend_with_mask(swapped_region, cropped_frame, mask)
            
            # Paste the swapped region back into the original frame
            x, y, w, h = crop_info
            temp_frame[y:y+h, x:x+w] = blended_region

            # Perform face swapping
            #temp_frame = swap_face(source_face[source_index], target_face, temp_frame)
            
            # Apply mouth mask if enabled
            if modules.globals.mouth_mask and i < len(mouth_masks):
                mouth_mask, mouth_cutout, mouth_box,lower_lip_polygon  = mouth_masks[i]
                face_mask = face_masks[i]
                # Calculate mouth polygon using facial landmarks
                landmarks = target_face.landmark_2d_106
                if landmarks is not None:
                 
                    # Apply mouth area with calculated polygon
                    temp_frame = apply_mouth_area(temp_frame, mouth_cutout, mouth_box, face_mask, lower_lip_polygon)
                else:
                    # If landmarks are not available, fall back to the original method without mouth_polygon
                    temp_frame = apply_mouth_area(temp_frame, mouth_cutout, mouth_box, face_mask, None)

                # Draw mouth mask visualization if enabled
                if modules.globals.show_mouth_mask_box:
                    if i < len(mouth_masks):
                        mouth_mask_data = mouth_masks[i]
                        temp_frame = draw_mouth_mask_visualization(temp_frame, target_faces[i], mouth_mask_data)            

    else:
        # Process single face or two faces
        if modules.globals.face_tracking:
            processed_faces = []
        
        # Determine number of faces to process
        faces_to_process = 2 if modules.globals.both_faces and len(source_face) > 1 else 1
        for i in range(min(faces_to_process, len(target_faces))):
            
            # Determine which source face to use
            if modules.globals.both_faces and len(source_face) > 1:
                source_index = source_face_order[i]
            else:
                source_index = active_source_index  # Always use the active source face
            
            if modules.globals.face_tracking:
                # Face tracking logic
                target_embedding = extract_face_embedding(target_faces[i])
                target_position = get_face_center(target_faces[i])
                face_id = id(target_faces[i])

                if modules.globals.both_faces:
                    # Two-face tracking logic
                    global first_face_position_history, second_face_position_history
                    if 'first_face_position_history' not in globals():
                        first_face_position_history = deque(maxlen=30)
                    if 'second_face_position_history' not in globals():
                        second_face_position_history = deque(maxlen=30)
                    use_pseudo_face = False

                    if first_face_embedding is not None and second_face_embedding is not None:
                        # Calculate similarity and consistency scores for both faces
                        first_similarity = cosine_similarity(first_face_embedding, target_embedding)
                        second_similarity = cosine_similarity(second_face_embedding, target_embedding)

                        first_position_consistency = 1 / (1 + np.linalg.norm(np.array(target_position) - np.array(first_face_position))) if first_face_position else 0
                        second_position_consistency = 1 / (1 + np.linalg.norm(np.array(target_position) - np.array(second_face_position))) if second_face_position else 0

                        # Get these values from modules.globals set by UI
                        EMBEDDING_WEIGHT = modules.globals.embedding_weight_size
                        POSITION_WEIGHT = modules.globals.position_size
                        total = modules.globals.old_embedding_weight  + modules.globals.new_embedding_weight 
                        OLD_WEIGHT  = modules.globals.old_embedding_weight  / total 
                        NEW_WEIGHT  = modules.globals.new_embedding_weight  / total 
                        TOTAL_WEIGHT = EMBEDDING_WEIGHT * modules.globals.weight_distribution_size + POSITION_WEIGHT


                        # Combine embedding similarity and position consistency for overall match score
                        first_score = ((EMBEDDING_WEIGHT * first_similarity + 
                                        POSITION_WEIGHT * first_position_consistency)/TOTAL_WEIGHT)
                        
                        second_score = ((EMBEDDING_WEIGHT * second_similarity + 
                                        POSITION_WEIGHT * second_position_consistency)/TOTAL_WEIGHT)


                        # Apply stickiness factor to favor previously tracked faces
                        if face_id == first_face_id:
                            first_score *= (1 + STICKINESS_FACTOR)
                        
                        if face_id == second_face_id:
                            second_score *= (1 + STICKINESS_FACTOR)
                        
                        # Store scores for potential use elsewhere
                        modules.globals.target_face1_score = first_score
                        

                        # Determine which face to track based on scores
                        if first_score > second_score:
                            if first_score > modules.globals.sticky_face_value:
                               
                                # Update first face tracking
                                source_index = source_face_order[0]
                                first_face_embedding = OLD_WEIGHT * first_face_embedding + NEW_WEIGHT * target_embedding
                                first_face_position = target_position
                                first_face_id = face_id
                                first_face_position_history.append(first_face_position)
                            
                            elif modules.globals.use_pseudo_face and first_score < modules.globals.pseudo_face_threshold:
                                # Use pseudo face if score is below threshold
                                use_pseudo_face = True
                                source_index = source_face_order[0]
                        else:
                            if second_score > modules.globals.sticky_face_value:
                                
                                # Update second face tracking
                                source_index = source_face_order[1]
                                second_face_embedding = OLD_WEIGHT * second_face_embedding + NEW_WEIGHT * target_embedding
                                second_face_position = target_position
                                second_face_id = face_id
                                second_face_position_history.append(second_face_position)
                            
                            elif modules.globals.use_pseudo_face and second_score < modules.globals.pseudo_face_threshold:
                                # Use pseudo face if score is below threshold
                                use_pseudo_face = True
                                source_index = source_face_order[1]
                        modules.globals.target_face2_score = second_score
                    else:
                        # Initialize face tracking for both faces
                        source_index = source_face_order[i % 2]
                        if i % 2 == 0:
                            first_face_embedding = target_embedding
                            first_face_position = target_position
                            first_face_id = face_id
                            first_face_position_history.append(first_face_position)
                        else:
                            second_face_embedding = target_embedding
                            second_face_position = target_position
                            second_face_id = face_id
                            second_face_position_history.append(second_face_position)

                    # Apply face swapping or use pseudo face
                    if use_pseudo_face:
                        # Create and use a pseudo face based on average position
                        if source_index == source_face_order[0]:
                            avg_position = np.mean(first_face_position_history, axis=0) if first_face_position_history else first_face_position
                        else:
                            avg_position = np.mean(second_face_position_history, axis=0) if second_face_position_history else second_face_position
                        pseudo_face = create_pseudo_face(avg_position)
                                                # Crop the face region
                        cropped_frame, crop_info = crop_face_region(temp_frame, pseudo_face)
                        # Create an adjusted face for the cropped region
                        # Adjust the face bbox for the cropped frame
                        adjusted_target_face = create_adjusted_face(pseudo_face, crop_info)
                        # Perform face swapping on the cropped region
                        swapped_region = swap_face(source_face[source_index], adjusted_target_face, cropped_frame)
                        
                        # Create a mask for blending with blurred edges
                        mask = create_edge_blur_mask(swapped_region.shape, blur_amount=BLUR_AMOUNT)
                        
                        # Blend the swapped region with the original cropped region
                        blended_region = blend_with_mask(swapped_region, cropped_frame, mask)

                        # Paste the swapped region back into the original frame
                        x, y, w, h = crop_info
                        temp_frame[y:y+h, x:x+w] = blended_region
                        # temp_frame = swap_face(source_face[source_index], pseudo_face, temp_frame)
                    else:
                        # Perform normal face swap
                        # Crop the face region
                        cropped_frame, crop_info = crop_face_region(temp_frame, target_faces[i])
                        # Create an adjusted face for the cropped region
                        # Adjust the face bbox for the cropped frame
                        adjusted_target_face = create_adjusted_face(target_faces[i], crop_info)
                        # Perform face swapping on the cropped region
                        swapped_region = swap_face(source_face[source_index], adjusted_target_face, cropped_frame)
                        # Create a mask for blending with blurred edges
                        mask = create_edge_blur_mask(swapped_region.shape, blur_amount=BLUR_AMOUNT)
                        
                        # Blend the swapped region with the original cropped region
                        blended_region = blend_with_mask(swapped_region, cropped_frame, mask)
                        
                        # Paste the swapped region back into the original frame
                        x, y, w, h = crop_info
                        temp_frame[y:y+h, x:x+w] = blended_region

                        # temp_frame = swap_face(source_face[source_index], target_faces[i], temp_frame)
                    
                    processed_faces.append((target_faces[i], source_index))
                else:
                    # Single face tracking logic
                    if first_face_embedding is None:
                        # Initialize tracking for the first detected face
                        first_face_embedding = target_embedding
                        first_face_position = target_position
                        first_face_id = face_id
                        face_lost_count = 0
                        face_position_history.clear()
                        face_position_history.append(target_position)
                        last_swap_time = current_time
                    else:
                        # Find the best matching face among all detected faces
                        best_match_score = 0
                        best_match_face = None

                        # Calculate average position of previously tracked face
                        avg_position = np.mean(face_position_history, axis=0) if face_position_history else first_face_position

                        for face in target_faces:
                            # Extract embedding and position for current face
                            target_embedding = extract_face_embedding(face)
                            target_position = get_face_center(face)

                            # Calculate similarity between current face and tracked face
                            embedding_similarity = cosine_similarity(first_face_embedding, target_embedding)
                            
                            # Calculate position consistency
                            position_consistency = 1 / (1 + np.linalg.norm(np.array(target_position) - np.array(avg_position)) + 1e-6)

                            # Get these values from modules.globals set by UI
                            EMBEDDING_WEIGHT = modules.globals.embedding_weight_size
                            POSITION_WEIGHT = modules.globals.position_size
                            total = modules.globals.old_embedding_weight  + modules.globals.new_embedding_weight 
                            OLD_WEIGHT  = modules.globals.old_embedding_weight  / total 
                            NEW_WEIGHT  = modules.globals.new_embedding_weight  / total 
                            TOTAL_WEIGHT = EMBEDDING_WEIGHT * modules.globals.weight_distribution_size + POSITION_WEIGHT


                            # Combine embedding similarity and position consistency for overall match score
                            match_score = ((EMBEDDING_WEIGHT * embedding_similarity + 
                                           POSITION_WEIGHT * position_consistency)/TOTAL_WEIGHT)

                            # Apply stickiness factor if this is the previously tracked face
                            if id(face) == first_face_id:
                                match_score *= (1 + STICKINESS_FACTOR)

                            # Update best match if this face has a higher score
                            if match_score > best_match_score:
                                best_match_score = match_score
                                best_match_face = face

                        # Store the best match score for potential use elsewhere
                        modules.globals.target_face1_score = best_match_score

                        if best_match_score > modules.globals.sticky_face_value:
                            # Good match found, update tracking
                            face_lost_count = 0
                            pseudo_face_count = 0  # Reset pseudo face count
                            
                            # Update face embedding with a weighted average (90% old, 10% new)
                            first_face_embedding = OLD_WEIGHT * first_face_embedding + NEW_WEIGHT * extract_face_embedding(best_match_face)
                            first_face_position = get_face_center(best_match_face)
                            first_face_id = id(best_match_face)

                            # Add current position to history
                            face_position_history.append(first_face_position)
                            # Crop the face region
                            cropped_frame, crop_info = crop_face_region(temp_frame, best_match_face)
                            # Create an adjusted face for the cropped region
                            # Adjust the face bbox for the cropped frame
                            adjusted_target_face = create_adjusted_face(best_match_face, crop_info)
                            # Perform face swapping on the cropped region
                            swapped_region = swap_face(source_face[active_source_index], adjusted_target_face, cropped_frame)
                            
                            # Create a mask for blending with blurred edges
                            mask = create_edge_blur_mask(swapped_region.shape, blur_amount=BLUR_AMOUNT)
                            
                            # Blend the swapped region with the original cropped region
                            blended_region = blend_with_mask(swapped_region, cropped_frame, mask)
                            
                            # Paste the swapped region back into the original frame
                            x, y, w, h = crop_info
                            temp_frame[y:y+h, x:x+w] = blended_region
                            # Proceed with face swapping using best_match_face
                            #temp_frame = swap_face(source_face[active_source_index], best_match_face, temp_frame)
                        else:
                            # No good match found, but don't reset tracking immediately
                            face_lost_count += 1

                            # Use the last known position for brief occlusions
                            if face_position_history and modules.globals.use_pseudo_face:
                                # Calculate average position from history
                                avg_position = np.mean(face_position_history, axis=0)

                                # If match score is below threshold and we haven't exceeded max pseudo face count
                                if best_match_score < modules.globals.pseudo_face_threshold and pseudo_face_count < modules.globals.max_pseudo_face_count:
                                    # Create and use a pseudo face
                                    pseudo_face = create_pseudo_face(avg_position)
                                    # Crop the face region
                                    cropped_frame, crop_info = crop_face_region(temp_frame, pseudo_face)
                                    # Create an adjusted face for the cropped region
                                    # Adjust the face bbox for the cropped frame
                                    adjusted_target_face = create_adjusted_face(pseudo_face, crop_info)
                                    # Perform face swapping on the cropped region
                                    swapped_region = swap_face(source_face[active_source_index], adjusted_target_face, cropped_frame)
                                    
                                    # Create a mask for blending with blurred edges
                                    mask = create_edge_blur_mask(swapped_region.shape, blur_amount=BLUR_AMOUNT)
                                    
                                    # Blend the swapped region with the original cropped region
                                    blended_region = blend_with_mask(swapped_region, cropped_frame, mask)

                                    # Paste the swapped region back into the original frame
                                    x, y, w, h = crop_info
                                    temp_frame[y:y+h, x:x+w] = blended_region
                                    #temp_frame = swap_face(source_face[active_source_index], pseudo_face, temp_frame)
                                    pseudo_face_count += 1
                                    # print(pseudo_face_count)  # Debugging line
                                else:
                                    # Skip using pseudo face and reset count
                                    # print(f"Skipping pseudo face. Score: {best_match_score}, Count: {pseudo_face_count}")  # Debugging line
                                    pseudo_face_count = 0  # Reset count if we skip
            else:
                # Face tracking is disabled, perform simple face swap
                # Crop the face region
                cropped_frame, crop_info = crop_face_region(temp_frame, target_faces[i])
                # Create an adjusted face for the cropped region
                # Adjust the face bbox for the cropped frame
                adjusted_target_face = create_adjusted_face(target_faces[i], crop_info)
                # Perform face swapping on the cropped region
                swapped_region = swap_face(source_face[source_index], adjusted_target_face, cropped_frame)

                # Create a mask for blending with blurred edges
                mask = create_edge_blur_mask(swapped_region.shape, blur_amount=BLUR_AMOUNT)
                
                # Blend the swapped region with the original cropped region
                blended_region = blend_with_mask(swapped_region, cropped_frame, mask)

                # Paste the swapped region back into the original frame
                x, y, w, h = crop_info
                temp_frame[y:y+h, x:x+w] = blended_region
                # temp_frame = cropped_frame
                

            # Apply mouth mask if enabled
            if modules.globals.mouth_mask and i < len(mouth_masks):
                mouth_mask, mouth_cutout, mouth_box,lower_lip_polygon = mouth_masks[i]
                face_mask = face_masks[i]
                # Calculate mouth polygon using facial landmarks
                landmarks = target_faces[i].landmark_2d_106
                if landmarks is not None:
                    # Apply mouth area with calculated polygon
                    temp_frame = apply_mouth_area(temp_frame, mouth_cutout, mouth_box, face_mask, lower_lip_polygon)
                else:
                    # If landmarks are not available, fall back to the original method without mouth_polygon
                    temp_frame = apply_mouth_area(temp_frame, mouth_cutout, mouth_box, face_mask, None)

            # Add visualization of mouth mask if enabled
            if modules.globals.show_mouth_mask_box:
                if i < len(mouth_masks):
                        mouth_mask_data = mouth_masks[i]
                        temp_frame = draw_mouth_mask_visualization(temp_frame, target_faces[i], mouth_mask_data)

    # Draw face boxes on the frame if enabled
    if modules.globals.show_target_face_box:
        temp_frame = face_analyser.draw_on(temp_frame, target_faces)
        for face in target_faces:
            temp_frame = draw_all_landmarks(temp_frame, face)


    # Return the processed frame
    return temp_frame

def process_frames(source_path: str, temp_frame_paths: List[str], progress: Any = None) -> None:
    
    source_image_left = None  # Initialize variable for the selected face image
    source_image_right = None  # Initialize variable for the selected face image

    if source_image_left is None and source_path:
        source_image_left = get_one_face_left(cv2.imread(source_path))
    if source_image_right is None and source_path:
        source_image_right = get_one_face_right(cv2.imread(source_path))
    

    for temp_frame_path in temp_frame_paths:
        temp_frame = cv2.imread(temp_frame_path)
        try:
            if modules.globals.flip_x:
                temp_frame = cv2.flip(temp_frame, 1)
            if modules.globals.flip_y:
                temp_frame = cv2.flip(temp_frame, 0)
            result = process_frame([source_image_left,source_image_right], temp_frame)
            cv2.imwrite(temp_frame_path, result)
        except Exception as exception:
            print(exception)
            pass
        if progress:
            progress.update(1)

def process_image(source_path: str, target_path: str, output_path: str) -> None:
    
    source_image_left = None  # Initialize variable for the selected face image
    source_image_right = None  # Initialize variable for the selected face image

    if source_image_left is None and source_path:
        source_image_left = get_one_face_left(cv2.imread(source_path))
    if source_image_right is None and source_path:
        source_image_right = get_one_face_right(cv2.imread(source_path))

    source_face = get_one_face(cv2.imread(source_path))
    target_frame = cv2.imread(target_path)

    if modules.globals.flip_x:
        target_frame = cv2.flip(target_frame, 1)
    if modules.globals.flip_y:
        target_frame = cv2.flip(target_frame, 0)

    result = process_frame([source_image_left,source_image_right], target_frame)
    cv2.imwrite(output_path, result)

def process_video(source_path: str, temp_frame_paths: List[str]) -> None:
    if modules.globals.face_tracking:
        reset_face_tracking()
    modules.ai.processors.frame.core.process_video(source_path, temp_frame_paths, process_frames)

def create_face_mask(face: Face, frame: Frame) -> np.ndarray:
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    landmarks = face.landmark_2d_106
    if landmarks is not None:
        # Convert landmarks to int32
        landmarks = landmarks.astype(np.int32)
        
        # Extract facial features
        right_side_face = landmarks[0:16]
        left_side_face = landmarks[17:32]
        right_eye = landmarks[33:42]
        right_eye_brow = landmarks[43:51]
        left_eye = landmarks[87:96]
        left_eye_brow = landmarks[97:105]

        # Calculate forehead extension
        right_eyebrow_top = np.min(right_eye_brow[:, 1])
        left_eyebrow_top = np.min(left_eye_brow[:, 1])
        eyebrow_top = min(right_eyebrow_top, left_eyebrow_top)
        
        face_top = np.min([right_side_face[0, 1], left_side_face[-1, 1]])
        forehead_height = face_top - eyebrow_top
        extended_forehead_height = int(forehead_height * 5.0)  # Extend by 50%

        # Create forehead points
        forehead_left = right_side_face[0].copy()
        forehead_right = left_side_face[-1].copy()
        forehead_left[1] -= extended_forehead_height
        forehead_right[1] -= extended_forehead_height

        # Combine all points to create the face outline
        face_outline = np.vstack([
            [forehead_left],
            right_side_face,
            left_side_face[::-1],  # Reverse left side to create a continuous outline
            [forehead_right]
        ])

        # Calculate padding
        padding = int(np.linalg.norm(right_side_face[0] - left_side_face[-1]) * 0.05)  # 5% of face width

        # Create a slightly larger convex hull for padding
        hull = cv2.convexHull(face_outline)
        hull_padded = []
        for point in hull:
            x, y = point[0]
            center = np.mean(face_outline, axis=0)
            direction = np.array([x, y]) - center
            direction = direction / np.linalg.norm(direction)
            padded_point = np.array([x, y]) + direction * padding
            hull_padded.append(padded_point)

        hull_padded = np.array(hull_padded, dtype=np.int32)

        # Fill the padded convex hull
        cv2.fillConvexPoly(mask, hull_padded, 255)

        # Smooth the mask edges
        mask = cv2.GaussianBlur(mask, (5, 5), 3)

    return mask

def blur_edges(mask: np.ndarray, blur_amount: int = 40) -> np.ndarray:
    blur_amount = blur_amount if blur_amount % 2 == 1 else blur_amount + 1
    return cv2.GaussianBlur(mask, (blur_amount, blur_amount), 0)

def apply_color_transfer(source, target):
    """
    Apply color transfer from target to source image
    """
    source = cv2.cvtColor(source, cv2.COLOR_BGR2LAB).astype("float32")
    target = cv2.cvtColor(target, cv2.COLOR_BGR2LAB).astype("float32")

    source_mean, source_std = cv2.meanStdDev(source)
    target_mean, target_std = cv2.meanStdDev(target)

    # Reshape mean and std to be broadcastable
    source_mean = source_mean.reshape(1, 1, 3)
    source_std = source_std.reshape(1, 1, 3)
    target_mean = target_mean.reshape(1, 1, 3)
    target_std = target_std.reshape(1, 1, 3)

    # Perform the color transfer
    source = (source - source_mean) * (target_std / source_std) + target_mean

    return cv2.cvtColor(np.clip(source, 0, 255).astype("uint8"), cv2.COLOR_LAB2BGR)

def create_feathered_mask(shape, feather_amount):
    mask = np.zeros(shape[:2], dtype=np.float32)
    center = (shape[1] // 2, shape[0] // 2)
    
    # Ensure the feather amount doesn't exceed half the smaller dimension
    max_feather = min(shape[0] // 2, shape[1] // 2) - 1
    feather_amount = min(feather_amount, max_feather)
    
    # Ensure the axes are at least 1 pixel
    axes = (max(1, shape[1] // 2 - feather_amount), 
            max(1, shape[0] // 2 - feather_amount))
    
    cv2.ellipse(mask, center, axes, 0, 0, 360, 1, -1)
    
    # Ensure the kernel size is odd and at least 3
    kernel_size = max(3, feather_amount * 2 + 1)
    if kernel_size % 2 == 0:
        kernel_size += 1
    
    mask = cv2.GaussianBlur(mask, (kernel_size, kernel_size), 0)
    return mask / np.max(mask)

def create_mouth_mask(face: Face, frame: Frame) -> (np.ndarray, np.ndarray, tuple):
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    mouth_cutout = None
    landmarks = face.landmark_2d_106
    if landmarks is not None:
        nose_tip = landmarks[80].astype(np.float32)
        center_bottom = landmarks[73].astype(np.float32)
       
        # Recreate mask polygon
        center_to_nose = nose_tip - center_bottom
        largest_vector = center_to_nose  # Simplified for this example
        base_height = largest_vector * 0.8
        mask_height = np.linalg.norm(base_height) * modules.globals.mask_size * 0.3
        
        mask_top = nose_tip + center_to_nose * 0.2 + np.array([0, +modules.globals.mask_down_size ])
        mask_bottom = mask_top + center_to_nose * (mask_height / np.linalg.norm(center_to_nose))
        
        mouth_points = landmarks[52:71].astype(np.float32)
        mouth_width = np.max(mouth_points[:, 0]) - np.min(mouth_points[:, 0])
        base_width = mouth_width * 0.4
        mask_width = base_width * modules.globals.mask_size * 0.8
        
        mask_direction = np.array([-center_to_nose[1], center_to_nose[0]])
        mask_direction /= np.linalg.norm(mask_direction)
        
        mask_polygon = np.array([
            mask_top + mask_direction * (mask_width / 2),
            mask_top - mask_direction * (mask_width / 2),
            mask_bottom - mask_direction * (mask_width / 2),
            mask_bottom + mask_direction * (mask_width / 2)
        ]).astype(np.int32)
        
        # Ensure the mask stays within the frame
       # mask_polygon[:, 0] = np.clip(mask_polygon[:, 0], 0, frame.shape[1] - 1)
        #mask_polygon[:, 1] = np.clip(mask_polygon[:, 1], 0, frame.shape[0] - 1)
        
        # Draw the mask
        cv2.fillPoly(mask, [mask_polygon], 255)
        
        # Calculate bounding box for the mouth cutout
        min_x, min_y = np.min(mask_polygon, axis=0)
        max_x, max_y = np.max(mask_polygon, axis=0)
        
        # Extract the masked area from the frame
        mouth_cutout = frame[min_y:max_y, min_x:max_x].copy()
    
    return mask, mouth_cutout, (min_x, min_y, max_x, max_y)

def create_lower_mouth_mask(face: Face, frame: Frame) -> (np.ndarray, np.ndarray, tuple, np.ndarray):
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    mouth_cutout = None
    landmarks = face.landmark_2d_106
    if landmarks is not None:
        #                  0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20
        lower_lip_order = [65,66,62,70,69,18,19,20,21,22,23,24,0 ,8 ,7 ,6 ,5 ,4 ,3 ,2 ,65]
        lower_lip_landmarks = landmarks[lower_lip_order].astype(np.float32)  # Use float for precise calculations

        # Calculate the center of the landmarks
        center = np.mean(lower_lip_landmarks, axis=0)

        # Expand the landmarks outward
        expansion_factor = 1 + modules.globals.mask_down_size  # Adjust this for more or less expansion
        expanded_landmarks = (lower_lip_landmarks - center) * expansion_factor + center

        # Extend the top lip part
        toplip_indices = [20, 0, 1, 2, 3, 4, 5]  # Indices for landmarks 2, 65, 66, 62, 70, 69, 18
        toplip_extension = modules.globals.mask_size * 0.5  # Adjust this factor to control the extension
        for idx in toplip_indices:
            direction = expanded_landmarks[idx] - center
            direction = direction / np.linalg.norm(direction)
            expanded_landmarks[idx] += direction * toplip_extension

        # Extend the bottom part (chin area)
        chin_indices = [11, 12, 13, 14, 15, 16]  # Indices for landmarks 21, 22, 23, 24, 0, 8
        chin_extension = 2 * 0.2  # Adjust this factor to control the extension
        for idx in chin_indices:
            expanded_landmarks[idx][1] += (expanded_landmarks[idx][1] - center[1]) * chin_extension


        # Convert back to integer coordinates
        expanded_landmarks = expanded_landmarks.astype(np.int32)

        # Calculate bounding box for the expanded lower mouth
        min_x, min_y = np.min(expanded_landmarks, axis=0)
        max_x, max_y = np.max(expanded_landmarks, axis=0)

        # Add some padding to the bounding box
        padding = int((max_x - min_x) * 0.1)  # 10% padding
        min_x = max(0, min_x - padding)
        min_y = max(0, min_y - padding)
        max_x = min(frame.shape[1], max_x + padding)
        max_y = min(frame.shape[0], max_y + padding)

        # Ensure the bounding box dimensions are valid
        if max_x <= min_x or max_y <= min_y:
            if (max_x - min_x) <= 1:
                max_x = min_x + 1
            if (max_y - min_y) <= 1:
                max_y = min_y + 1

        # Create the mask
        mask_roi = np.zeros((max_y - min_y, max_x - min_x), dtype=np.uint8)
        cv2.fillPoly(mask_roi, [expanded_landmarks - [min_x, min_y]], 255)

        # Apply Gaussian blur to soften the mask edges
        mask_roi = cv2.GaussianBlur(mask_roi, (15, 15), 5)

        # Place the mask ROI in the full-sized mask
        mask[min_y:max_y, min_x:max_x] = mask_roi

        # Extract the masked area from the frame
        mouth_cutout = frame[min_y:max_y, min_x:max_x].copy()

        # Return the expanded lower lip polygon in original frame coordinates
        lower_lip_polygon = expanded_landmarks

    return mask, mouth_cutout, (min_x, min_y, max_x, max_y), lower_lip_polygon

def draw_mouth_mask_visualization(frame: Frame, face: Face, mouth_mask_data: tuple) -> Frame:
    landmarks = face.landmark_2d_106
    if landmarks is not None and mouth_mask_data is not None:
        mask, mouth_cutout, (min_x, min_y, max_x, max_y), lower_lip_polygon = mouth_mask_data

        vis_frame = frame.copy()

        # Ensure coordinates are within frame bounds
        height, width = vis_frame.shape[:2]
        min_x, min_y = max(0, min_x), max(0, min_y)
        max_x, max_y = min(width, max_x), min(height, max_y)

        # Adjust mask to match the region size
        mask_region = mask[0:max_y-min_y, 0:max_x-min_x]
        
        # Remove the color mask overlay
        # color_mask = cv2.applyColorMap((mask_region * 255).astype(np.uint8), cv2.COLORMAP_JET)

        # Ensure shapes match before blending
        vis_region = vis_frame[min_y:max_y, min_x:max_x]
        # Remove blending with color_mask
        # if vis_region.shape[:2] == color_mask.shape[:2]:
        #     blended = cv2.addWeighted(vis_region, 0.7, color_mask, 0.3, 0)
        #     vis_frame[min_y:max_y, min_x:max_x] = blended

        # Draw the lower lip polygon
        cv2.polylines(vis_frame, [lower_lip_polygon], True, (0, 255, 0), 2)

        # Remove the red box
        # cv2.rectangle(vis_frame, (min_x, min_y), (max_x, max_y), (0, 0, 255), 2)

        # Visualize the feathered mask
        feather_amount = max(1, min(30, (max_x - min_x) // modules.globals.mask_feather_ratio, (max_y - min_y) // modules.globals.mask_feather_ratio))
        # Ensure kernel size is odd
        kernel_size = 2 * feather_amount + 1
        feathered_mask = cv2.GaussianBlur(mask_region.astype(float), (kernel_size, kernel_size), 0)
        feathered_mask = (feathered_mask / feathered_mask.max() * 255).astype(np.uint8)
        # Remove the feathered mask color overlay
        # color_feathered_mask = cv2.applyColorMap(feathered_mask, cv2.COLORMAP_VIRIDIS)

        # Ensure shapes match before blending feathered mask
        # if vis_region.shape == color_feathered_mask.shape:
        #     blended_feathered = cv2.addWeighted(vis_region, 0.7, color_feathered_mask, 0.3, 0)
        #     vis_frame[min_y:max_y, min_x:max_x] = blended_feathered

        # Add labels
        cv2.putText(vis_frame, "Lower Mouth Mask", (min_x, min_y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(vis_frame, "Feathered Mask", (min_x, max_y+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return vis_frame
    return frame

def apply_mouth_area(frame: np.ndarray, mouth_cutout: np.ndarray, mouth_box: tuple, face_mask: np.ndarray, mouth_polygon: np.ndarray) -> np.ndarray:
    min_x, min_y, max_x, max_y = mouth_box
    box_width = max_x - min_x
    box_height = max_y - min_y
   
    if mouth_cutout is None or box_width is None or box_height is None or face_mask is None or mouth_polygon is None:
        return frame
   
    try:
        resized_mouth_cutout = cv2.resize(mouth_cutout, (box_width, box_height))
        roi = frame[min_y:max_y, min_x:max_x]
       
        if roi.shape != resized_mouth_cutout.shape:
            resized_mouth_cutout = cv2.resize(resized_mouth_cutout, (roi.shape[1], roi.shape[0]))
       
        color_corrected_mouth = apply_color_transfer(resized_mouth_cutout, roi)
       
        # Use the provided mouth polygon to create the mask
        polygon_mask = np.zeros(roi.shape[:2], dtype=np.uint8)
        adjusted_polygon = mouth_polygon - [min_x, min_y]
        cv2.fillPoly(polygon_mask, [adjusted_polygon], 255)
        
        # Apply feathering to the polygon mask
        feather_amount = min(30, box_width // modules.globals.mask_feather_ratio, box_height // modules.globals.mask_feather_ratio)
        feathered_mask = cv2.GaussianBlur(polygon_mask.astype(float), (0, 0), feather_amount)
        feathered_mask = feathered_mask / feathered_mask.max()
        
        face_mask_roi = face_mask[min_y:max_y, min_x:max_x]
        combined_mask = feathered_mask * (face_mask_roi / 255.0)
       
        combined_mask = combined_mask[:, :, np.newaxis]
        blended = (color_corrected_mouth * combined_mask + roi * (1 - combined_mask)).astype(np.uint8)
       
        # Apply face mask to blended result
        face_mask_3channel = np.repeat(face_mask_roi[:, :, np.newaxis], 3, axis=2) / 255.0
        final_blend = blended * face_mask_3channel + roi * (1 - face_mask_3channel)
       
        frame[min_y:max_y, min_x:max_x] = final_blend.astype(np.uint8)
    except Exception as e:
        pass
   
    return frame

def reset_face_tracking():
    global first_face_embedding, second_face_embedding
    global first_face_position, second_face_position
    global first_face_id, second_face_id
    global first_face_lost_count, second_face_lost_count

    first_face_embedding = None
    second_face_embedding = None
    first_face_position = None
    second_face_position = None
    first_face_id = None
    second_face_id = None
    first_face_lost_count = 0
    second_face_lost_count = 0
    modules.globals.target_face1_score=0.00
    modules.globals.target_face2_score=0.00

def get_face_center(face: Face) -> Tuple[float, float]:
    bbox = face.bbox
    return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)

def extract_face_embedding(face: Face) -> np.ndarray:
    try:
        if hasattr(face, 'embedding') and face.embedding is not None:
            embedding = face.embedding
        else:
            # If the face doesn't have an embedding, we need to generate one
            embedding = get_face_analyser.get(face)
        
        # Normalize the embedding
        return embedding / np.linalg.norm(embedding)
    except Exception as e:
        print(f"Error extracting face embedding: {e}")
        # Return a default embedding (all zeros) if extraction fails
        return np.zeros(512, dtype=np.float32)

def find_best_match(embedding: np.ndarray, faces: List[Face]) -> Face:
    if embedding is None:
        # Handle case where embedding is None, maybe log a message or skip processing
        print("No embedding to match against, skipping face matching.")
        return None
    best_match = None
    best_similarity = -1

    for face in faces:
        face_embedding = extract_face_embedding(face)
        similarity = cosine_similarity(embedding, face_embedding)
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = face

    return best_match

def update_face_assignments(target_faces: List[Face]):
    global first_face_embedding, second_face_embedding, first_face_position, second_face_position, last_assignment_time

    if len(target_faces) == 0:
        return

    current_time = time.time()
    if current_time - last_assignment_time < assignment_cooldown:
        return  # Don't update assignments during cooldown period

    try:
        face_embeddings = [extract_face_embedding(face) for face in target_faces]
        face_positions = [get_face_center(face) for face in target_faces]

        if first_face_embedding is None and face_embeddings:
            first_face_embedding = face_embeddings[0]
            first_face_position = face_positions[0]
            last_assignment_time = current_time
        
        if modules.globals.both_faces and second_face_embedding is None and len(face_embeddings) > 1:
            second_face_embedding = face_embeddings[1]
            second_face_position = face_positions[1]
            last_assignment_time = current_time

        if first_face_embedding is not None:
            best_match_index = -1
            best_match_score = -1
            for i, (embedding, position) in enumerate(zip(face_embeddings, face_positions)):
                embedding_similarity = cosine_similarity(first_face_embedding, embedding)
                position_consistency = 1 / (1 + np.linalg.norm(np.array(position) - np.array(first_face_position))) if first_face_position else 0
                combined_score = embedding_similarity * 0.7 + position_consistency * 0.3
                
                if combined_score > best_match_score and combined_score > 0.8:  # Increased threshold
                    best_match_score = combined_score
                    best_match_index = i

            if best_match_index != -1:
                first_face_embedding = face_embeddings[best_match_index]
                first_face_position = face_positions[best_match_index]
                last_assignment_time = current_time

        if modules.globals.both_faces and second_face_embedding is not None:
            remaining_embeddings = face_embeddings[:best_match_index] + face_embeddings[best_match_index+1:]
            remaining_positions = face_positions[:best_match_index] + face_positions[best_match_index+1:]
            
            if remaining_embeddings:
                best_match_index = -1
                best_match_score = -1
                for i, (embedding, position) in enumerate(zip(remaining_embeddings, remaining_positions)):
                    embedding_similarity = cosine_similarity(second_face_embedding, embedding)
                    position_consistency = 1 / (1 + np.linalg.norm(np.array(position) - np.array(second_face_position))) if second_face_position else 0
                    combined_score = embedding_similarity * 0.7 + position_consistency * 0.3
                    
                    if combined_score > best_match_score and combined_score > 0.8:  # Increased threshold
                        best_match_score = combined_score
                        best_match_index = i

                if best_match_index != -1:
                    second_face_embedding = remaining_embeddings[best_match_index]
                    second_face_position = remaining_positions[best_match_index]
                    last_assignment_time = current_time

    except Exception as e:
        print(f"Error in update_face_assignments: {e}")

def cosine_similarity(a, b):
    if a is None or b is None:
        # Log an error message or handle the None case appropriately
        #print("Warning: One of the embeddings is None.")
        return 0  # or handle it as needed
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_best_match(embedding: np.ndarray, face_embeddings: List[np.ndarray]) -> int:
    similarities = [cosine_similarity(embedding, face_embedding) for face_embedding in face_embeddings]
    return np.argmax(similarities)

def crop_face_region(frame: Frame, face: Face, padding: float = 0.2) -> Tuple[Frame, Tuple[int, int, int, int]]:
    h, w = frame.shape[:2]
    bbox = face.bbox
    x1, y1, x2, y2 = map(int, bbox)
    
    # Add padding
    pw, ph = int((x2-x1)*padding), int((y2-y1)*padding)
    x1, y1 = max(0, x1-pw), max(0, y1-ph)
    x2, y2 = min(w, x2+pw), min(h, y2+ph)
    
    cropped_frame = frame[y1:y2, x1:x2].copy()  # Use .copy() to ensure we're not working with a view
    return cropped_frame, (x1, y1, x2-x1, y2-y1)

def adjust_face_bbox(face: Face, crop_info: Tuple[int, int, int, int]) -> Face:
    x, y, _, _ = crop_info
    adjusted_face = Face()
    adjusted_face.bbox = face.bbox - np.array([x, y, x, y])
    adjusted_face.kps = face.kps - np.array([x, y])
    adjusted_face.landmark_2d_106 = face.landmark_2d_106 - np.array([x, y])
    adjusted_face.landmark_3d_68 = face.landmark_3d_68.copy()
    adjusted_face.landmark_3d_68[:, :2] -= np.array([x, y])
    # Copy other necessary attributes
    for attr in ['det_score', 'gender', 'age', 'embedding', 'embedding_norm', 'normed_embedding']:
        if hasattr(face, attr):
            setattr(adjusted_face, attr, getattr(face, attr))
    return adjusted_face

def create_adjusted_face(face: Face, crop_info: Tuple[int, int, int, int]) -> Face:
    x, y, _, _ = crop_info
    adjusted_face = Face(bbox=face.bbox - np.array([x, y, x, y]),
                         kps=face.kps - np.array([x, y]),
                         det_score=face.det_score,
                         landmark_3d_68=face.landmark_3d_68.copy(),
                         landmark_2d_106=face.landmark_2d_106 - np.array([x, y]),
                         gender=face.gender,
                         age=face.age,
                         embedding=face.embedding)

    # Adjust 3D landmarks
    adjusted_face.landmark_3d_68[:, :2] -= np.array([x, y])

    return adjusted_face

def create_ellipse_mask(shape, feather_amount=5):
    mask = np.zeros(shape[:2], dtype=np.float32)
    center = (shape[1] // 2, shape[0] // 2)
    axes = (int(shape[1] * 0.42), int(shape[0] * 0.48))
    cv2.ellipse(mask, center, axes, 0, 0, 360, 1, -1)
    mask = cv2.GaussianBlur(mask, (0, 0), feather_amount * min(shape[:2]))
    return mask

def create_edge_blur_mask(shape, blur_amount=40):
    h, w = shape[:2]
    mask = np.ones((h, w), dtype=np.float32)
    
    # Adjust blur_amount to not exceed half the minimum dimension
    blur_amount = min(blur_amount, min(h, w) // 4)
    
    # Create smoother gradients
    v_gradient = np.power(np.linspace(0, 1, blur_amount), 2)
    h_gradient = np.power(np.linspace(0, 1, blur_amount), 2)
    
    # Apply vertical gradients
    mask[:blur_amount, :] = v_gradient[:, np.newaxis]
    mask[-blur_amount:, :] = v_gradient[::-1, np.newaxis]
    
    # Apply horizontal gradients
    mask[:, :blur_amount] *= h_gradient[np.newaxis, :]
    mask[:, -blur_amount:] *= h_gradient[::-1][np.newaxis, :]
    
    return cv2.GaussianBlur(mask, (0, 0), sigmaX=blur_amount/4, sigmaY=blur_amount/4)

def blend_with_mask(swapped_region, original_region, mask):
    mask_3d = np.expand_dims(mask, axis=2).repeat(3, axis=2)
    return (swapped_region * mask_3d + original_region * (1 - mask_3d)).astype(np.uint8)


def create_pseudo_face(position):
    class PseudoFace:
        def __init__(self, position):
            x, y = position
            width = height = 100  # Approximate face size
            
            # More realistic bbox
            self.bbox = np.array([x - width/2, y - height/2, x + width/2, y + height/2])
            
            # Generate landmarks
            self.landmark_2d_106 = generate_anatomical_landmarks(position)
            
            # Extract kps from landmarks
            self.kps = np.array([
                self.landmark_2d_106[36],  # Left eye
                self.landmark_2d_106[90],  # Right eye
                self.landmark_2d_106[80],  # Nose tip
                self.landmark_2d_106[57],  # Left mouth corner
                self.landmark_2d_106[66]   # Right mouth corner
            ])
            
            # Generate 3D landmarks (just add a random z-coordinate to 2D landmarks)
            self.landmark_3d_68 = np.column_stack((self.landmark_2d_106[:68], np.random.normal(0, 5, 68)))
            
            # Other attributes
            self.det_score = 0.99
            self.embedding = np.random.rand(512)  # Random embedding
            self.embedding_norm = np.linalg.norm(self.embedding)
            self.gender = 0
            self.age = 25
            self.pose = np.zeros(3)
            self.normed_embedding = self.embedding / self.embedding_norm

    return PseudoFace(position)

def generate_anatomical_landmarks(position):
    x, y = position
    landmarks = []

    # Right side face (0-16)
    for i in range(17):
        landmarks.append([x - 40 + i*2, y - 30 + i*3])

    # Left side face (17-32)
    for i in range(16):
        landmarks.append([x + 40 - i*2, y - 30 + i*3])

    # Right eye (33-42)
    eye_center = [x - 20, y - 10]
    for i in range(10):
        angle = i * (2 * np.pi / 10)
        landmarks.append([eye_center[0] + 10 * np.cos(angle), eye_center[1] + 5 * np.sin(angle)])

    # Right eyebrow (43-51)
    for i in range(9):
        landmarks.append([x - 35 + i*5, y - 30])

    # Mouth (52-71)
    mouth_center = [x, y + 30]
    for i in range(20):
        angle = i * (2 * np.pi / 20)
        landmarks.append([mouth_center[0] + 15 * np.cos(angle), mouth_center[1] + 7 * np.sin(angle)])

    # Nose (72-86)
    for i in range(15):
        landmarks.append([x - 7 + i, y + 10 + i//2])

    # Left eye (87-96)
    eye_center = [x + 20, y - 10]
    for i in range(10):
        angle = i * (2 * np.pi / 10)
        landmarks.append([eye_center[0] + 10 * np.cos(angle), eye_center[1] + 5 * np.sin(angle)])

    # Left eyebrow (97-105)
    for i in range(9):
        landmarks.append([x + 5 + i*5, y - 30])

    return np.array(landmarks, dtype=np.float32)

def draw_all_landmarks(frame: Frame, face: Face) -> Frame:
    if face.landmark_2d_106 is None:
        return frame
    
    landmarks = face.landmark_2d_106.astype(np.int32)
    
    # Define colors for different parts of the face
    colors = {
        'face_outline': (255, 255, 255),    # White
        'lefteye': (0, 255, 0),             # Green
        'righteye': (0, 255, 0),            # Green
        'eyebrows': (235, 213, 52),         # Cyan
        'nose': (0, 255, 255),              # Yellow
        'uppermouth': (0, 0, 255),          # Red
        'lowermouth': (255, 150, 0)         # Blue
    }

    
    # Draw face outline (landmarks 0-33)
    for i in range(33):
        cv2.circle(frame, tuple(landmarks[i]), 1, colors['face_outline'], -1)
    
    # Right Eye (landmarks 33-43)
    for i in range(33, 43):
        cv2.circle(frame, tuple(landmarks[i]), 1, colors['righteye'], -1)

    # Right Eyebrow (landmarks 43-52)
    for i in range(43, 52):
        cv2.circle(frame, tuple(landmarks[i]), 1, colors['eyebrows'], -1)
    
    # Lower mouth (landmarks 52-62)
    lower_lip_order = [65,66,62,70,69,18, 19, 20, 21, 22, 23, 24, 0, 8, 7, 6, 5, 4, 3, 2, 65]
    lower_lip_landmarks = landmarks[lower_lip_order]

    # mouth (landmarks 52-72)
    for i in range(52, 62):
        cv2.circle(frame, tuple(landmarks[i]), 1, colors['lowermouth'], -1)

    # Draw polyline connecting lower lip points
    cv2.polylines(frame, [lower_lip_landmarks], isClosed=True, color=colors['lowermouth'], thickness=1)

    # mouth (landmarks 52-72)
    for i in range(62, 72):
        cv2.circle(frame, tuple(landmarks[i]), 1, colors['uppermouth'], -1)

    # nose (landmarks 72-87)
    for i in range(72, 87):
        cv2.circle(frame, tuple(landmarks[i]), 1, colors['nose'], -1)

    # Left Eye (landmarks 87-97)
    for i in range(87, 97):
        cv2.circle(frame, tuple(landmarks[i]), 1, colors['lefteye'], -1)

    # Left Eyebrow (landmarks 97-106)
    for i in range(97, 106):
        cv2.circle(frame, tuple(landmarks[i]), 1, colors['eyebrows'], -1)
    
    
    return frame

def apply_mouth_area_with_landmarks(temp_frame, mouth_cutout, mouth_box, face_mask, target_face):
    landmarks = target_face.landmark_2d_106
    if landmarks is not None:
        nose_tip = landmarks[80].astype(np.float32)
        center_bottom = landmarks[73].astype(np.float32)
        center_to_nose = nose_tip - center_bottom
        mask_height = np.linalg.norm(center_to_nose) * modules.globals.mask_size * 0.3
        mask_top = nose_tip + center_to_nose * 0.2 + np.array([0, -modules.globals.mask_size * 0.1])
        mask_bottom = mask_top + center_to_nose * (mask_height / np.linalg.norm(center_to_nose))
        mouth_points = landmarks[52:71].astype(np.float32)
        mouth_width = np.max(mouth_points[:, 0]) - np.min(mouth_points[:, 0])
        base_width = mouth_width * 0.4
        mask_width = base_width * modules.globals.mask_size * 0.8
        mask_direction = np.array([-center_to_nose[1], center_to_nose[0]], dtype=np.float32)
        mask_direction /= np.linalg.norm(mask_direction)
        mouth_polygon = np.array([
            mask_top + mask_direction * (mask_width / 2),
            mask_top - mask_direction * (mask_width / 2),
            mask_bottom - mask_direction * (mask_width / 2),
            mask_bottom + mask_direction * (mask_width / 2)
        ]).astype(np.int32)

        return apply_mouth_area(temp_frame, mouth_cutout, mouth_box, face_mask, mouth_polygon)
    else:
        return apply_mouth_area(temp_frame, mouth_cutout, mouth_box, face_mask, None)


def get_two_faces(frame: Frame) -> List[Face]:
    faces = get_many_faces(frame)
    if faces:
        # Sort faces from left to right based on the x-coordinate of the bounding box
        sorted_faces = sorted(faces, key=lambda x: x.bbox[0])
        return sorted_faces[:2]  # Return up to two faces, leftmost and rightmost
    return []
