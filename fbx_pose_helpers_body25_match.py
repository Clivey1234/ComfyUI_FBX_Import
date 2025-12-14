# - Read a reference OpenPose/DWPose stickman IMAGE, cannot be bother to keep typing openpose, so stickman it is
# - Computes a 2D bounding box of the pose in that image
# - Aligns (scale + offset) the FBX-projected stickman into that bbox
# - Can treat the reference as:full body upper body (head->hips) or auto-detected

import math
import numpy as np
import torch

from .fbx_pose_helpers_body25 import (
    project_and_normalize as base_project_and_normalize,
    draw_pose_images as base_draw_pose_images,
    numpy_to_comfy_image,
)

# Joints we definitely want to hide when we treat the reference as "upper body".
LEG_JOINTS = {
    "left_knee",
    "left_ankle",
    "right_knee",
    "right_ankle",
}


def _compute_ref_bbox_from_image(ref_image, out_width, out_height, threshold=0.01):
    """
    ref_image: Comfy IMAGE tensor [B,H,W,C] or [H,W,C] in 0..1.

    Returns bbox in *output-coordinate space* (scaled to out_width/out_height):

        (min_x, max_x, min_y, max_y, img_w, img_h)

    or None if no skeleton detected.
    """
    if ref_image is None or not isinstance(ref_image, torch.Tensor):
        return None

    img = ref_image
    if img.ndim == 4:
        # [B, H, W, C] -> take first frame
        img = img[0]
    if img.ndim != 3:
        return None

    img_np = img.detach().cpu().numpy()  # [H, W, C]
    h, w, c = img_np.shape

    if c == 1:
        mask = img_np[..., 0]
    else:
        mask = img_np.sum(axis=-1)

    mask = mask > threshold
    coords = np.argwhere(mask)
    if coords.size == 0:
        return None

    ys = coords[:, 0]
    xs = coords[:, 1]
    min_x = xs.min()
    max_x = xs.max()
    min_y = ys.min()
    max_y = ys.max()

    # Scale bbox to the node's output resolution, in case they differ
    scale_x = float(out_width) / float(w)
    scale_y = float(out_height) / float(h)

    min_x_out = float(min_x) * scale_x
    max_x_out = float(max_x) * scale_x
    min_y_out = float(min_y) * scale_y
    max_y_out = float(max_y) * scale_y

    return (min_x_out, max_x_out, min_y_out, max_y_out, float(out_width), float(out_height))


def _classify_body_coverage_auto(bbox, img_h):
    """
    AUTO detection:
      - "full": full body visible (head to feet)
      - "upper": cropped (waist/chest up)

    We err on the side of "upper" if the pose is relatively short in the frame
    OR leaves a noticeable gap at the bottom.
    """
    if bbox is None:
        return "full"

    _, _, min_y, max_y, _, _ = bbox
    pose_height = max_y - min_y
    if pose_height <= 1e-3:
        return "full"

    rel_height = pose_height / float(img_h)
    bottom_margin = float(img_h - 1 - max_y)

    # Definitely full body if it fills most of the frame vertically AND
    # reaches very close to the bottom edge.
    if rel_height >= 0.85 and bottom_margin <= img_h * 0.08:
        return "full"

    # If it only uses a moderate fraction of the vertical space OR
    # leaves a clear gap at the bottom, treat as upper body.
    if rel_height <= 0.7 or bottom_margin >= img_h * 0.12:
        return "upper"

    # Ambiguous zone: default to full to avoid over-cropping.
    return "full"


def _decide_body_mode(alignment_mode, bbox):
    """
    Map the node's Alignment_Mode string to an internal "full"/"upper" mode.
    alignment_mode:
        "Match Full Body"
        "Upper Body (Head-Hips)"
        "Auto (Full/Partial)"
    """
    if alignment_mode == "Upper Body (Head-Hips)":
        # Explicit user choice wins, no auto magic.
        return "upper"
    if alignment_mode == "Match Full Body":
        return "full"

    # Auto
    if bbox is None:
        return "full"
    _, _, _, _, _, img_h = bbox
    return _classify_body_coverage_auto(bbox, img_h)


def _rotate_single_frame(frame, angle_deg):
    """
    Rotate a single frame's joints around the vertical axis (Z) by angle_deg.
    Expects frame: dict[joint_name -> [x, y, z]].
    Returns a NEW dict with rotated coordinates.

    We treat:
      - Z as "up"
      - X/Y as the ground plane (camera orbits horizontally around the subject)
    """
    if not frame:
        return {}

    angle = math.radians(float(angle_deg))
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    rotated = {}
    for jname, pos in frame.items():
        if not isinstance(pos, (list, tuple)) or len(pos) != 3:
            continue
        x, y, z = pos
        # Rotate in X–Y plane around Z (up):
        x_rot = x * cos_a - y * sin_a
        y_rot = x * sin_a + y * cos_a
        rotated[jname] = [float(x_rot), float(y_rot), float(z)]

    return rotated


def _apply_camera_pan_rotation(joint_frames, start_deg, end_deg, camera_view):
    """
    Apply a smooth yaw rotation across frames between start_deg and end_deg.
    - Only applied when camera_view == "Front".
    - joint_frames: list[dict[joint_name -> [x, y, z]]]
    Returns a NEW list of rotated frames.
    """
    if not joint_frames or camera_view != "Front":
        return joint_frames

    num_frames = len(joint_frames)
    if num_frames == 0:
        return joint_frames

    start_deg = float(start_deg)
    end_deg = float(end_deg)

    # If no change or only one frame, just rotate everything with start_deg.
    if num_frames == 1 or start_deg == end_deg:
        angle = start_deg
        return [_rotate_single_frame(frame, angle) for frame in joint_frames]

    rotated_frames = []
    denom = float(num_frames - 1)
    for idx, frame in enumerate(joint_frames):
        t = idx / denom  # 0.0 -> 1.0
        angle = start_deg + (end_deg - start_deg) * t
        rotated_frames.append(_rotate_single_frame(frame, angle))

    return rotated_frames


def _align_projected_frames_to_bbox(projected_frames, bbox, alignment_mode):
    """
    Aligns the 2D coordinates of projected_frames into the reference bbox
    using a *single* global scale/center for the whole animation to avoid
    per-frame zooming.

    projected_frames: list[dict[joint_name -> (x,y)]]
    bbox: (min_x, max_x, min_y, max_y, img_w, img_h)
    alignment_mode: node-level Alignment_Mode string.
    """
    if bbox is None:
        return projected_frames

    min_x_ref, max_x_ref, min_y_ref, max_y_ref, img_w, img_h = bbox
    ref_height = max_y_ref - min_y_ref
    ref_center_x = (min_x_ref + max_x_ref) * 0.5

    if ref_height <= 1e-3:
        return projected_frames

    # Decide "full" vs "upper" once for the whole clip
    body_mode = _decide_body_mode(alignment_mode, bbox)

    # ------------------------------------------------------------------
    # Pass 1: compute global bounds over the entire animation, in the
    #         same "body segment" sense as before (full or upper body).
    # ------------------------------------------------------------------
    global_top_y = None
    global_bottom_y = None
    global_min_x = None
    global_max_x = None

    for frame_proj in projected_frames:
        if not frame_proj:
            continue

        # Determine our own top/bottom Y extents for the relevant body part.
        top_candidates = []
        # Prefer head/neck/chest for the top
        for j in ("head", "neck", "chest"):
            if j in frame_proj:
                top_candidates.append(frame_proj[j][1])

        # Fallback: any joint
        if not top_candidates:
            top_candidates = [y for (_, y) in frame_proj.values()]

        bottom_candidates = []
        if body_mode == "full":
            # Use feet / knees / hips for full-body bottom
            for j in (
                "left_ankle", "right_ankle",
                "left_knee", "right_knee",
                "hips", "left_hip", "right_hip"
            ):
                if j in frame_proj:
                    bottom_candidates.append(frame_proj[j][1])
        else:
            # Upper-body: use hips / spine / chest as bottom
            for j in ("hips", "left_hip", "right_hip", "spine", "chest"):
                if j in frame_proj:
                    bottom_candidates.append(frame_proj[j][1])

        if not bottom_candidates:
            bottom_candidates = [y for (_, y) in frame_proj.values()]

        frame_top_y = float(min(top_candidates))
        frame_bottom_y = float(max(bottom_candidates))

        if global_top_y is None or frame_top_y < global_top_y:
            global_top_y = frame_top_y
        if global_bottom_y is None or frame_bottom_y > global_bottom_y:
            global_bottom_y = frame_bottom_y

        xs = [x for (x, _) in frame_proj.values()]
        frame_min_x = float(min(xs))
        frame_max_x = float(max(xs))

        if global_min_x is None or frame_min_x < global_min_x:
            global_min_x = frame_min_x
        if global_max_x is None or frame_max_x > global_max_x:
            global_max_x = frame_max_x

    if global_top_y is None or global_bottom_y is None:
        # No usable data; return as-is.
        return projected_frames

    global_height = global_bottom_y - global_top_y
    if global_height <= 1e-3:
        return projected_frames

    global_center_x = (global_min_x + global_max_x) * 0.5

    # Unified scale factor for the whole animation
    scale = ref_height / global_height

    # ------------------------------------------------------------------
    # Pass 2: apply the same global scale + center to every frame.
    # ------------------------------------------------------------------
    aligned_frames = []

    for frame_proj in projected_frames:
        if not frame_proj:
            aligned_frames.append({})
            continue

        aligned = {}
        for jname, (x, y) in frame_proj.items():
            # Normalized vertical position within the global segment
            y_rel = (y - global_top_y) / global_height  # 0 at top, 1 at bottom
            y_new = min_y_ref + y_rel * ref_height

            # Horizontal: center-align and scale with same factor as vertical
            x_offset = x - global_center_x
            x_new = ref_center_x + x_offset * scale

            aligned[jname] = (float(x_new), float(y_new))

        if body_mode == "upper":
            # 1) Drop explicit leg joints (knees/ankles).
            aligned = {
                jname: pos
                for jname, pos in aligned.items()
                if jname not in LEG_JOINTS
            }

            # 2) Hard crop: drop any joint that sits below the reference bbox bottom.
            cropped = {}
            for jname, (x_new, y_new) in aligned.items():
                if y_new <= max_y_ref:
                    cropped[jname] = (x_new, y_new)
            aligned = cropped

        aligned_frames.append(aligned)

    return aligned_frames


def generate_aligned_pose_images(
    joint_frames,
    output_width,
    output_height,
    camera_view,
    zoom_factor,
    inplace,
    color_mode,
    face_mode,
    joint_size,
    line_thickness,
    ref_pose_image,
    alignment_mode,
    projection_mode="Orthographic (Stable)",
    cam_profile_str=None,
):
    """
    High-level helper for the "match image" node:

    1. Use the existing BODY_25 projection (project_and_normalize).
    2. If alignment is enabled and a ref pose image is provided:
       - Compute bbox of non-black pixels
       - Align our projected joints to that bbox (full or upper body),
         using a *whole-animation* global bounding box for stability.
    3. Draw pose images and convert to Comfy tensor.
    """
    # Step 1: base projection (our "raw" FBX stickman), with optional
    # per-frame CameraDirector yaw/zoom applied inside BODY_25 helper.
    projected = base_project_and_normalize(
        joint_frames,
        output_width,
        output_height,
        camera_view,
        zoom_factor,
        inplace,
        projection_mode,
        cam_profile_str=cam_profile_str,
    )

    # Step 2: optional alignment to reference pose image
    if alignment_mode != "Off" and ref_pose_image is not None:
        bbox = _compute_ref_bbox_from_image(
            ref_pose_image,
            output_width,
            output_height,
        )
        if bbox is not None:
            projected = _align_projected_frames_to_bbox(
                projected,
                bbox,
                alignment_mode,
            )

    # Step 3: draw and convert
    images_np = base_draw_pose_images(
        projected,
        output_width,
        output_height,
        joint_size,
        line_thickness,
        color_mode,
        face_mode,
    )
    return numpy_to_comfy_image(images_np)
