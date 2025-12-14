# Grouping for basic OpenPose-style colors
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
