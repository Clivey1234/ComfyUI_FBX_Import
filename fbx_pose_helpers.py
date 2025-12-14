import math
import numpy as np
from PIL import Image, ImageDraw
import torch

# Body + hands skeleton segments
SKELETON_SEGMENTS = [
    ("hips", "spine"),
    ("spine", "chest"),
    ("chest", "neck"),
    ("neck", "head"),

    ("chest", "left_shoulder"),
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),

    ("chest", "right_shoulder"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),

    ("hips", "left_hip"),
    ("left_hip", "left_knee"),
    ("left_knee", "left_ankle"),

    ("hips", "right_hip"),
    ("right_hip", "right_knee"),
    ("right_knee", "right_ankle"),

    ("left_wrist", "left_thumb_base"),
    ("left_thumb_base", "left_thumb_tip"),

    ("left_wrist", "left_index_base"),
    ("left_index_base", "left_index_tip"),

    ("left_wrist", "left_middle_base"),
    ("left_middle_base", "left_middle_tip"),

    ("left_wrist", "left_ring_base"),
    ("left_ring_base", "left_ring_tip"),

    ("left_wrist", "left_pinky_base"),
    ("left_pinky_base", "left_pinky_tip"),

    ("right_wrist", "right_thumb_base"),
    ("right_thumb_base", "right_thumb_tip"),

    ("right_wrist", "right_index_base"),
    ("right_index_base", "right_index_tip"),

    ("right_wrist", "right_middle_base"),
    ("right_middle_base", "right_middle_tip"),

    ("right_wrist", "right_ring_base"),
    ("right_ring_base", "right_ring_tip"),

    ("right_wrist", "right_pinky_base"),
    ("right_pinky_base", "right_pinky_tip"),
]

# Approx face segments for "Full Face" mode
FACE_SEGMENTS = [
    ("left_eye", "right_eye"),
    ("left_eye", "nose"),
    ("right_eye", "nose"),
    ("left_ear", "left_eye"),
    ("right_ear", "right_eye"),
    ("nose", "head"),
]

# Grouping for colors (OpenPose-style)
JOINT_GROUPS = {
    "hips": "torso",
    "spine": "torso",
    "chest": "torso",
    "neck": "torso",
    "head": "torso",

    "left_shoulder": "left_arm",
    "left_elbow": "left_arm",
    "left_wrist": "left_arm",

    "right_shoulder": "right_arm",
    "right_elbow": "right_arm",
    "right_wrist": "right_arm",

    "left_hip": "left_leg",
    "left_knee": "left_leg",
    "left_ankle": "left_leg",

    "right_hip": "right_leg",
    "right_knee": "right_leg",
    "right_ankle": "right_leg",

    "left_thumb_base": "left_hand",
    "left_thumb_tip": "left_hand",
    "left_index_base": "left_hand",
    "left_index_tip": "left_hand",
    "left_middle_base": "left_hand",
    "left_middle_tip": "left_hand",
    "left_ring_base": "left_hand",
    "left_ring_tip": "left_hand",
    "left_pinky_base": "left_hand",
    "left_pinky_tip": "left_hand",

    "right_thumb_base": "right_hand",
    "right_thumb_tip": "right_hand",
    "right_index_base": "right_hand",
    "right_index_tip": "right_hand",
    "right_middle_base": "right_hand",
    "right_middle_tip": "right_hand",
    "right_ring_base": "right_hand",
    "right_ring_tip": "right_hand",
    "right_pinky_base": "right_hand",
    "right_pinky_tip": "right_hand",

    "nose": "face",
    "left_eye": "face",
    "right_eye": "face",
    "left_ear": "face",
    "right_ear": "face",
}

GROUP_COLORS_OPENPOSE = {
    "torso":      (255, 255, 0),
    "left_arm":   (0, 255, 0),
    "right_arm":  (0, 128, 255),
    "left_leg":   (255, 0, 255),
    "right_leg":  (255, 128, 0),
    "left_hand":  (0, 200, 0),
    "right_hand": (0, 100, 220),
    "face":       (255, 0, 0),
}

# Per-joint colors approximating modern ControlNet OpenPose style.
CONTROLNET_JOINT_COLORS = {
    # Torso / core
    "hips":          (0, 255, 0),
    "spine":         (0, 220, 0),
    "chest":         (0, 200, 255),
    "neck":          (0, 100, 255),
    "head":          (255, 0, 255),

    # Left arm: warm gradient
    "left_shoulder": (255, 0, 0),
    "left_elbow":    (255, 128, 0),
    "left_wrist":    (255, 255, 0),

    # Right arm: cool gradient
    "right_shoulder": (0, 128, 255),
    "right_elbow":    (0, 200, 255),
    "right_wrist":    (0, 255, 200),

    # Left leg: green-ish
    "left_hip":   (0, 255, 0),
    "left_knee":  (0, 220, 120),
    "left_ankle": (0, 200, 180),

    # Right leg: blue/teal
    "right_hip":   (0, 255, 128),
    "right_knee":  (0, 220, 200),
    "right_ankle": (0, 200, 255),

    # Left hand fingers
    "left_thumb_base":  (255, 255, 0),
    "left_thumb_tip":   (255, 220, 0),
    "left_index_base":  (0, 180, 255),
    "left_index_tip":   (0, 140, 255),
    "left_middle_base": (0, 255, 180),
    "left_middle_tip":  (0, 255, 140),
    "left_ring_base":   (255, 0, 180),
    "left_ring_tip":    (255, 0, 140),
    "left_pinky_base":  (180, 0, 255),
    "left_pinky_tip":   (140, 0, 255),

    # Right hand fingers
    "right_thumb_base":  (255, 255, 0),
    "right_thumb_tip":   (255, 220, 0),
    "right_index_base":  (0, 180, 255),
    "right_index_tip":   (0, 140, 255),
    "right_middle_base": (0, 255, 180),
    "right_middle_tip":  (0, 255, 140),
    "right_ring_base":   (255, 0, 180),
    "right_ring_tip":    (255, 0, 140),
    "right_pinky_base":  (180, 0, 255),
    "right_pinky_tip":   (140, 0, 255),

    # Face (white dots)
    "nose":      (255, 255, 255),
    "left_eye":  (255, 255, 255),
    "right_eye": (255, 255, 255),
    "left_ear":  (255, 255, 255),
    "right_ear": (255, 255, 255),
}

WHITE_COLOR = (255, 255, 255)


def get_joint_color(jname: str, color_mode: str):
    """Return RGB tuple for a joint based on the selected color mode."""
    if color_mode == "White":
        return WHITE_COLOR

    if color_mode == "ControlNet Colors":
        col = CONTROLNET_JOINT_COLORS.get(jname)
        if col is not None:
            return col
        group = JOINT_GROUPS.get(jname)
        if group is not None:
            return GROUP_COLORS_OPENPOSE.get(group, WHITE_COLOR)
        return WHITE_COLOR

    # Default "OpenPose"
    group = JOINT_GROUPS.get(jname)
    if group is None:
        return WHITE_COLOR
    return GROUP_COLORS_OPENPOSE.get(group, WHITE_COLOR)


def get_segment_color(jname_a: str, jname_b: str, color_mode: str):
    """Colour for a bone segment between two joints."""
    if color_mode == "White":
        return WHITE_COLOR
    col_a = get_joint_color(jname_a, color_mode)
    col_b = get_joint_color(jname_b, color_mode)
    r = (col_a[0] + col_b[0]) // 2
    g = (col_a[1] + col_b[1]) // 2
    b = (col_a[2] + col_b[2]) // 2
    return (r, g, b)


def _estimate_yaw_angle_for_auto(first_frame_positions):
    hips = first_frame_positions.get("hips")
    left_sh = first_frame_positions.get("left_shoulder")
    right_sh = first_frame_positions.get("right_shoulder")
    head = first_frame_positions.get("head")

    forward = None

    if left_sh is not None and right_sh is not None:
        lh = np.array(left_sh, dtype=np.float32)
        rh = np.array(right_sh, dtype=np.float32)
        side = rh - lh
        up = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        forward = np.cross(up, side)

        if hips is not None and head is not None:
            hips_v = np.array(hips, dtype=np.float32)
            head_v = np.array(head, dtype=np.float32)
            v = head_v - hips_v
            f_xy = forward[:2]
            v_xy = v[:2]
            if np.linalg.norm(f_xy) > 1e-6 and np.linalg.norm(v_xy) > 1e-6:
                f_xy_n = f_xy / np.linalg.norm(f_xy)
                v_xy_n = v_xy / np.linalg.norm(v_xy)
                dot = float(np.dot(f_xy_n, v_xy_n))
                if dot < 0.0:
                    forward = -forward

    if forward is None:
        left_hip = first_frame_positions.get("left_hip")
        right_hip = first_frame_positions.get("right_hip")
        if hips is None or left_hip is None or right_hip is None:
            return 0.0
        lh = np.array(left_hip, dtype=np.float32)
        rh = np.array(right_hip, dtype=np.float32)
        side = rh - lh
        up = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        forward = np.cross(up, side)

    f_xy = forward[:2]
    norm = np.linalg.norm(f_xy)
    if norm < 1e-6:
        return 0.0

    f_xy /= norm
    alpha = math.atan2(f_xy[1], f_xy[0])
    yaw = -math.pi / 2.0 - alpha
    return yaw


def _apply_yaw(wx, wy, wz, yaw):
    if abs(yaw) < 1e-6:
        return wx, wy, wz
    cos_y = math.cos(yaw)
    sin_y = math.sin(yaw)
    x2 = cos_y * wx - sin_y * wy
    y2 = sin_y * wx + cos_y * wy
    return x2, y2, wz


def _world_to_view(wx, wy, wz, view):
    """Map world coords (already yaw-rotated) into a 2D view plane."""
    if view in ["Front", "Auto (Face Camera)"]:
        sx, sy = wx, wz
    elif view == "Back":
        sx, sy = -wx, wz
    elif view == "Left Side":
        sx, sy = -wy, wz
    elif view == "Right Side":
        sx, sy = wy, wz
    elif view == "Top":
        sx, sy = wx, wy
    else:
        sx, sy = wx, wz
    return sx, sy


def project_and_normalize(
    joint_frames,
    width,
    height,
    camera_view,
    zoom_factor=1.0,
    inplace=True,
):
    """
    Projects 3D joints to 2D with auto-scaling, zoom, and optional global
    bounding box for root motion:

    - inplace=True  (default):   per-frame bounds, centered on hips (or frame),
                                 effectively "camera follows" the character.
    - inplace=False:             compute a global bounding box across *all*
                                 frames and scale once so the entire motion
                                 path fits into the image.
    """
    projected_frames = []
    view = camera_view

    try:
        zoom_factor = float(zoom_factor)
    except Exception:
        zoom_factor = 1.0
    if zoom_factor <= 0.0:
        zoom_factor = 1.0

    inplace = bool(inplace)

    # Yaw auto-rotate once from the first non-empty frame
    yaw_angle = 0.0
    if view == "Auto (Face Camera)":
        for frame_positions in joint_frames:
            if frame_positions:
                yaw_angle = _estimate_yaw_angle_for_auto(frame_positions)
                break

    # If NOT inplace, first pass: build a global bounding box in view space
    global_min_x = None
    global_max_x = None
    global_min_y = None
    global_max_y = None

    if not inplace:
        for frame_positions in joint_frames:
            if not frame_positions:
                continue

            for _, pos in frame_positions.items():
                wx, wy, wz = pos
                rx, ry, rz = _apply_yaw(wx, wy, wz, yaw_angle)
                sx, sy = _world_to_view(rx, ry, rz, view)

                if global_min_x is None:
                    global_min_x = sx
                    global_max_x = sx
                    global_min_y = sy
                    global_max_y = sy
                else:
                    if sx < global_min_x:
                        global_min_x = sx
                    if sx > global_max_x:
                        global_max_x = sx
                    if sy < global_min_y:
                        global_min_y = sy
                    if sy > global_max_y:
                        global_max_y = sy

        if global_min_x is None:
            inplace = True

    if not inplace:
        width_3d = global_max_x - global_min_x
        height_3d = global_max_y - global_min_y
        if width_3d <= 1e-6:
            width_3d = 1.0
        if height_3d <= 1e-6:
            height_3d = 1.0

        scale_w = (width * 0.9) / float(width_3d)
        scale_h = (height * 0.9) / float(height_3d)
        global_scale = min(scale_w, scale_h) * zoom_factor

        cx_global = (global_min_x + global_max_x) * 0.5
        cy_global = (global_min_y + global_max_y) * 0.5
    else:
        global_scale = None
        cx_global = None
        cy_global = None

    # Second pass: project per frame
    for frame_positions in joint_frames:
        if not frame_positions:
            projected_frames.append({})
            continue

        rotated = {}
        for jname, pos in frame_positions.items():
            wx, wy, wz = pos
            rotated[jname] = _apply_yaw(wx, wy, wz, yaw_angle)

        if not inplace:
            projected = {}
            for jname, (rx, ry, rz) in rotated.items():
                sx, sy = _world_to_view(rx, ry, rz, view)

                x_rel = sx - cx_global
                y_rel = sy - cy_global

                u = width * 0.5 + x_rel * global_scale
                v = height * 0.5 - y_rel * global_scale
                projected[jname] = (float(u), float(v))

            projected_frames.append(projected)
            continue

        xs = []
        ys = []
        for (rx, ry, rz) in rotated.values():
            sx, sy = _world_to_view(rx, ry, rz, view)
            xs.append(sx)
            ys.append(sy)

        xs = np.array(xs, dtype=np.float32)
        ys = np.array(ys, dtype=np.float32)
        if xs.size == 0:
            projected_frames.append({})
            continue

        min_x, max_x = xs.min(), xs.max()
        min_y, max_y = ys.min(), ys.max()

        width_3d = max_x - min_x
        height_3d = max_y - min_y
        if height_3d <= 1e-6:
            height_3d = 1.0

        scale_w = (width * 0.9) / float(width_3d) if width_3d > 1e-6 else (width * 0.9)
        scale_h = (height * 0.9) / float(height_3d)
        scale = min(scale_w, scale_h) * zoom_factor

        hips_world = rotated.get("hips")
        projected = {}

        for jname, (rx2, ry2, rz2) in rotated.items():
            sx, sy = _world_to_view(rx2, ry2, rz2, view)

            if hips_world is not None:
                hx, hy, hz = hips_world
                hx_s, hy_s = _world_to_view(hx, hy, hz, view)
                x_rel = sx - hx_s
                y_rel = sy - hy_s
            else:
                cx = (min_x + max_x) * 0.5
                cy = (min_y + max_y) * 0.5
                x_rel = sx - cx
                y_rel = sy - cy

            u = width * 0.5 + x_rel * scale
            v = height * 0.5 - y_rel * scale
            projected[jname] = (float(u), float(v))

        projected_frames.append(projected)

    return projected_frames


def _generate_face_points_2d(frame_proj):
    head = frame_proj.get("head")
    neck = frame_proj.get("neck")
    left_sh = frame_proj.get("left_shoulder")
    right_sh = frame_proj.get("right_shoulder")

    if "nose" not in frame_proj and head is not None and neck is not None:
        hx, hy = head
        nx, ny = neck
        nose_x = hx
        nose_y = hy - (hy - ny) * 0.2
        frame_proj["nose"] = (nose_x, nose_y)

    if "left_eye" not in frame_proj or "right_eye" not in frame_proj:
        nose = frame_proj.get("nose", head)
        if head is not None and nose is not None:
            hx, hy = head
            nx, ny = nose
            cx = (hx + nx) * 0.5
            cy = (hy + ny) * 0.5
            if left_sh is not None and right_sh is not None:
                lx, ly = left_sh
                rx, ry = right_sh
                span = abs(rx - lx)
                eye_offset = span * 0.18
            else:
                eye_offset = 15.0
            if "left_eye" not in frame_proj:
                frame_proj["left_eye"] = (cx - eye_offset, cy)
            if "right_eye" not in frame_proj:
                frame_proj["right_eye"] = (cx + eye_offset, cy)

    if ("left_ear" not in frame_proj or "right_ear" not in frame_proj) and head is not None:
        hx, hy = head
        if left_sh is not None and right_sh is not None:
            lx, ly = left_sh
            rx, ry = right_sh
            span = abs(rx - lx)
            ear_offset = span * 0.33
        else:
            ear_offset = 25.0
        if "left_ear" not in frame_proj:
            frame_proj["left_ear"] = (hx - ear_offset, hy)
        if "right_ear" not in frame_proj:
            frame_proj["right_ear"] = (hx + ear_offset, hy)


def draw_pose_images(projected_frames, width, height, joint_size, line_thickness, color_mode, face_mode):
    images = []
    for frame_proj in projected_frames:
        if face_mode in ["Dots Only (BODY_25)", "Full Face (FACE_70)"]:
            _generate_face_points_2d(frame_proj)

        img = Image.new("RGB", (width, height), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        for a, b in SKELETON_SEGMENTS:
            if a not in frame_proj or b not in frame_proj:
                continue
            x1, y1 = frame_proj[a]
            x2, y2 = frame_proj[b]
            color = get_segment_color(a, b, color_mode)
            draw.line((x1, y1, x2, y2), fill=color, width=line_thickness)

        if face_mode == "Full Face (FACE_70)":
            for a, b in FACE_SEGMENTS:
                if a not in frame_proj or b not in frame_proj:
                    continue
                x1, y1 = frame_proj[a]
                x2, y2 = frame_proj[b]
                color = get_segment_color(a, b, color_mode)
                draw.line((x1, y1, x2, y2), fill=color, width=line_thickness)

        r = joint_size
        for jname, (x, y) in frame_proj.items():
            if face_mode == "Off" and jname in ("nose", "left_eye", "right_eye", "left_ear", "right_ear"):
                continue
            color = get_joint_color(jname, color_mode)
            draw.ellipse((x - r, y - r, x + r, y + r), fill=color)

        npimg = np.array(img, dtype=np.uint8)
        images.append(npimg)

    if not images:
        blank = np.zeros((height, width, 3), dtype=np.uint8)
        images = [blank]

    return np.stack(images, axis=0)


def numpy_to_comfy_image(arr):
    arr = arr.astype(np.float32) / 255.0
    return torch.from_numpy(arr)
