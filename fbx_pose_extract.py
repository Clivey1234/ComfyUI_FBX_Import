# stupidly long way of doing this. need to potentially break this down into seperate files for different skeleton
# maybe for v2, but this will fo for now lol
import bpy
import sys
import os
import json
from mathutils import Vector
import math


_FACE_PREV_FWD = None
def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    args = {
        "fbx": "",
        "out": "",
        "frame_mode": "Frame_Spread_TotalAnim",
        "num_frames": 24,
        "start_frame": 0,
        "end_frame": 100,
        "frame_step": 1,
    }

    key = None
    for item in argv:
        if item.startswith("--"):
            key = item[2:]
        else:
            if key in args:
                if key in ["num_frames", "start_frame", "end_frame", "frame_step"]:
                    args[key] = int(item)
                else:
                    args[key] = item
            key = None

    return args


CANONICAL_JOINTS = [
    "hips",
    "spine",
    "chest",
    "neck",
    "head",

    "left_shoulder",
    "left_elbow",
    "left_wrist",

    "right_shoulder",
    "right_elbow",
    "right_wrist",

    "left_hip",
    "left_knee",
    "left_ankle",

    "right_hip",
    "right_knee",
    "right_ankle",

    "left_thumb_base",
    "left_thumb_tip",
    "left_index_base",
    "left_index_tip",
    "left_middle_base",
    "left_middle_tip",
    "left_ring_base",
    "left_ring_tip",
    "left_pinky_base",
    "left_pinky_tip",

    "right_thumb_base",
    "right_thumb_tip",
    "right_index_base",
    "right_index_tip",
    "right_middle_base",
    "right_middle_tip",
    "right_ring_base",
    "right_ring_tip",
    "right_pinky_base",
    "right_pinky_tip",

    "left_eye",
    "right_eye",
    "nose",
    "left_ear",
    "right_ear",
]

BONE_CANDIDATES = {
    "hips": [
        "mixamorig:Hips", "mixamorig2:Hips", "Hips", "hips",
        "pelvis", "Pelvis", "root", "Root", "RootNode"
    ],
    "spine": [
        "mixamorig:Spine", "mixamorig2:Spine", "Spine", "spine",
        "spine_01", "Spine1", "spine1"
    ],
    "chest": [
        "mixamorig:Spine2", "mixamorig2:Spine2",
        "mixamorig:Spine1", "mixamorig2:Spine1",
        "Spine2", "Spine1",
        "spine_02", "spine_03", "upperchest", "upper_chest", "spine_upper", "spine2"
    ],
    "neck": [
        "mixamorig:Neck", "mixamorig2:Neck", "Neck", "neck",
        "neck_01", "neck1"
    ],
    "head": [
        "mixamorig:Head", "mixamorig2:Head", "Head", "head", "head_01", "head1"
    ],

    "left_shoulder": [
        "mixamorig:LeftShoulder", "mixamorig2:LeftShoulder", "LeftShoulder",
        "clavicle_l", "shoulder_l", "upperarm_parent_l"
    ],
    "left_elbow": [
        "mixamorig:LeftForeArm", "mixamorig2:LeftForeArm", "LeftForeArm",
        "lowerarm_l", "lowerarm_twist_01_l", "elbow_l"
    ],
    "left_wrist": [
        "mixamorig:LeftHand", "mixamorig2:LeftHand", "LeftHand",
        "hand_l", "hand_l_ik"
    ],

    "right_shoulder": [
        "mixamorig:RightShoulder", "mixamorig2:RightShoulder", "RightShoulder",
        "clavicle_r", "shoulder_r", "upperarm_parent_r"
    ],
    "right_elbow": [
        "mixamorig:RightForeArm", "mixamorig2:RightForeArm", "RightForeArm",
        "lowerarm_r", "lowerarm_twist_01_r", "elbow_r"
    ],
    "right_wrist": [
        "mixamorig:RightHand", "mixamorig2:RightHand", "RightHand",
        "hand_r", "hand_r_ik"
    ],

    "left_hip": [
        "mixamorig:LeftUpLeg", "mixamorig2:LeftUpLeg", "LeftUpLeg",
        "thigh_l", "upperleg_l"
    ],
    "left_knee": [
        "mixamorig:LeftLeg", "mixamorig2:LeftLeg", "LeftLeg",
        "calf_l", "lowerleg_l", "knee_l"
    ],
    "left_ankle": [
        "mixamorig:LeftFoot", "mixamorig2:LeftFoot", "LeftFoot",
        "foot_l", "ankle_l"
    ],

    "right_hip": [
        "mixamorig:RightUpLeg", "mixamorig2:RightUpLeg", "RightUpLeg",
        "thigh_r", "upperleg_r"
    ],
    "right_knee": [
        "mixamorig:RightLeg", "mixamorig2:RightLeg", "RightLeg",
        "calf_r", "lowerleg_r", "knee_r"
    ],
    "right_ankle": [
        "mixamorig:RightFoot", "mixamorig2:RightFoot", "RightFoot",
        "foot_r", "ankle_r"
    ],

    "left_thumb_base": [
        "mixamorig:LeftHandThumb1", "mixamorig2:LeftHandThumb1", "LeftHandThumb1",
        "thumb_01_l"
    ],
    "left_thumb_tip": [
        "mixamorig:LeftHandThumb3", "mixamorig2:LeftHandThumb3", "LeftHandThumb3",
        "thumb_03_l", "thumb_02_l"
    ],
    "left_index_base": [
        "mixamorig:LeftHandIndex1", "mixamorig2:LeftHandIndex1", "LeftHandIndex1",
        "index_01_l"
    ],
    "left_index_tip": [
        "mixamorig:LeftHandIndex3", "mixamorig2:LeftHandIndex3", "LeftHandIndex3",
        "index_03_l", "index_02_l"
    ],
    "left_middle_base": [
        "mixamorig:LeftHandMiddle1", "mixamorig2:LeftHandMiddle1", "LeftHandMiddle1",
        "middle_01_l"
    ],
    "left_middle_tip": [
        "mixamorig:LeftHandMiddle3", "mixamorig2:LeftHandMiddle3", "LeftHandMiddle3",
        "middle_03_l", "middle_02_l"
    ],
    "left_ring_base": [
        "mixamorig:LeftHandRing1", "mixamorig2:LeftHandRing1", "LeftHandRing1",
        "ring_01_l"
    ],
    "left_ring_tip": [
        "mixamorig:LeftHandRing3", "mixamorig2:LeftHandRing3", "LeftHandRing3",
        "ring_03_l", "ring_02_l"
    ],
    "left_pinky_base": [
        "mixamorig:LeftHandPinky1", "mixamorig2:LeftHandPinky1", "LeftHandPinky1",
        "pinky_01_l", "little_01_l"
    ],
    "left_pinky_tip": [
        "mixamorig:LeftHandPinky3", "mixamorig2:LeftHandPinky3", "LeftHandPinky3",
        "pinky_03_l", "pinky_02_l", "little_03_l"
    ],

    "right_thumb_base": [
        "mixamorig:RightHandThumb1", "mixamorig2:RightHandThumb1", "RightHandThumb1",
        "thumb_01_r"
    ],
    "right_thumb_tip": [
        "mixamorig:RightHandThumb3", "mixamorig2:RightHandThumb3", "RightHandThumb3",
        "thumb_03_r", "thumb_02_r"
    ],
    "right_index_base": [
        "mixamorig:RightHandIndex1", "mixamorig2:RightHandIndex1", "RightHandIndex1",
        "index_01_r"
    ],
    "right_index_tip": [
        "mixamorig:RightHandIndex3", "mixamorig2:RightHandIndex3", "RightHandIndex3",
        "index_03_r", "index_02_r"
    ],
    "right_middle_base": [
        "mixamorig:RightHandMiddle1", "mixamorig2:RightHandMiddle1", "RightHandMiddle1",
        "middle_01_r"
    ],
    "right_middle_tip": [
        "mixamorig:RightHandMiddle3", "mixamorig2:RightHandMiddle3", "RightHandMiddle3",
        "middle_03_r", "middle_02_r"
    ],
    "right_ring_base": [
        "mixamorig:RightHandRing1", "mixamorig2:RightHandRing1", "RightHandRing1",
        "ring_01_r"
    ],
    "right_ring_tip": [
        "mixamorig:RightHandRing3", "mixamorig2:RightHandRing3", "RightHandRing3",
        "ring_03_r", "ring_02_r"
    ],
    "right_pinky_base": [
        "mixamorig:RightHandPinky1", "mixamorig2:RightHandPinky1", "RightHandPinky1",
        "pinky_01_r", "little_01_r"
    ],
    "right_pinky_tip": [
        "mixamorig:RightHandPinky3", "mixamorig2:RightHandPinky3", "RightHandPinky3",
        "pinky_03_r", "pinky_02_r", "little_03_r"
    ],

    "left_eye": [
        "eye_l", "Eye_L", "eye_left"
    ],
    "right_eye": [
        "eye_r", "Eye_R", "eye_right"
    ],
    "nose": [
        "nose", "Nose"
    ],
    "left_ear": [
        "ear_l", "Ear_L"
    ],
    "right_ear": [
        "ear_r", "Ear_R"
    ],
}


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_fbx(path):
    bpy.ops.import_scene.fbx(filepath=path)


def find_armature():
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            return obj
    return None


def get_action_and_range(arm_obj):
    if arm_obj.animation_data and arm_obj.animation_data.action:
        action = arm_obj.animation_data.action
        f_start, f_end = action.frame_range
        return action, int(f_start), int(f_end)
    scene = bpy.context.scene
    return None, scene.frame_start, scene.frame_end


def _normalize_name(name: str) -> str:
    """
    Normalise a bone name so different rigs map more easily:
    - Strip namespace prefixes (e.g. "mixamorig:")
    - Strip Blender-style hierarchy ("Armature|Hips")
    - Lowercase + strip spaces
    """
    if ":" in name:
        name = name.split(":", 1)[-1]
    if "|" in name:
        name = name.split("|", 1)[-1]
    return name.lower().strip()


def _canonical_side_hint(canonical_name: str):
    """
    Very simple side hint:
      - 'left_*'  -> 'left'
      - 'right_*' -> 'right'
      - otherwise -> None
    """
    if canonical_name.startswith("left_"):
        return "left"
    if canonical_name.startswith("right_"):
        return "right"
    return None


def find_bone_for_canonical(pbones, canonical_name):
    """
    Try to find the best pose bone for a given canonical joint name.

    Strategy:
      1) Exact alias lookup using BONE_CANDIDATES keys
      2) Normalised-name match against aliases
      3) Heuristic scoring against *all* bones:
         - Match side (left/right)
         - Match key tokens (hip, thigh, calf, foot, arm, etc.)
    """
    candidates = BONE_CANDIDATES.get(canonical_name, [])
    side_hint = _canonical_side_hint(canonical_name)

    # --- PASS 1: direct name match against known candidates ---
    if candidates:
        for cand in candidates:
            b = pbones.get(cand)
            if b is not None:
                return b

    # --- PASS 2: normalised name match against candidate aliases ---
    short_candidates = [_normalize_name(c) for c in candidates] if candidates else []

    if short_candidates:
        for p in pbones:
            pname_norm = _normalize_name(p.name)
            for sc in short_candidates:
                if not sc:
                    continue
                if (
                    pname_norm == sc
                    or pname_norm.endswith(sc)
                    or sc in pname_norm
                ):
                    return p

    # --- PASS 3: heuristic search over *all* bones (auto-mapper) ---

    # Base tokens from canonical name (e.g. "left_shoulder" -> ["shoulder"])
    base = canonical_name
    if base.startswith("left_"):
        base = base[len("left_"):]
    elif base.startswith("right_"):
        base = base[len("right_"):]
    tokens = [t for t in base.split("_") if t]

    # Some extra hints per body region
    EXTRA_HINTS = {
        "hip": ["hip", "pelvis", "upleg", "thigh"],
        "knee": ["knee", "leg", "calf", "lowerleg"],
        "ankle": ["ankle", "foot"],
        "shoulder": ["shoulder", "clavicle"],
        "elbow": ["elbow", "forearm", "lowerarm"],
        "wrist": ["wrist", "hand"],
        "spine": ["spine"],
        "chest": ["chest", "upperchest", "rib"],
        "neck": ["neck"],
        "head": ["head"],
        "eye": ["eye"],
        "ear": ["ear"],
        "nose": ["nose"],
        "thumb": ["thumb"],
        "index": ["index"],
        "middle": ["middle"],
        "ring": ["ring"],
        "pinky": ["pinky", "little"],
    }

    # Merge base tokens into a flat hint list
    hint_tokens = list(tokens)
    for t in tokens:
        extra = EXTRA_HINTS.get(t, [])
        hint_tokens.extend(extra)

    def score_bone(pbone):
        name_norm = _normalize_name(pbone.name)
        score = 0.0

        # Prefer correct side (left/right) if applicable
        if side_hint == "left":
            if any(tag in name_norm for tag in [".l", "_l", " l_", "left"]):
                score += 2.0
            if any(tag in name_norm for tag in [".r", "_r", " r_", "right"]):
                score -= 1.0
        elif side_hint == "right":
            if any(tag in name_norm for tag in [".r", "_r", " r_", "right"]):
                score += 2.0
            if any(tag in name_norm for tag in [".l", "_l", " l_", "left"]):
                score -= 1.0

        # Body-part token matches
        for ht in hint_tokens:
            if ht and ht in name_norm:
                score += 1.0

        return score

    best_bone = None
    best_score = 0.0

    for p in pbones:
        s = score_bone(p)
        if s > best_score:
            best_score = s
            best_bone = p

    # Require at least some confidence (e.g. score >= 2)
    if best_bone is not None and best_score >= 2.0:
        return best_bone

    return None


def build_pose_bone_map(arm_obj):
    pbones = arm_obj.pose.bones
    mapping = {}
    found_joints = {}
    missing_joints = []

    for cname in CANONICAL_JOINTS:
        b = find_bone_for_canonical(pbones, cname)
        mapping[cname] = b
        if b is not None:
            found_joints[cname] = b.name
        else:
            missing_joints.append(cname)

    print("FBX Pose: found joints:", found_joints)
    if missing_joints:
        print("FBX Pose: missing joints:", missing_joints)

    return mapping, found_joints, missing_joints


def compute_frames(args, default_start, default_end):
    mode = args["frame_mode"]
    num_frames = args["num_frames"]
    start = args["start_frame"]
    end = args["end_frame"]
    step = max(args["frame_step"], 1)

    # Mode 1: Frame_Spread_TotalAnim  (old Sample_N_Frames behaviour)
    if mode == "Frame_Spread_TotalAnim":
        if end <= start:
            # If end not sensible, fall back to the full scene range
            start = default_start
            end = default_end
        else:
            start = max(start, default_start)
            end = min(end, default_end)
            if end <= start:
                end = start

        candidate = list(range(start, end + 1, step))
        if not candidate:
            candidate = [start]

        if num_frames <= 1:
            return [candidate[0]]

        if len(candidate) == 1:
            return [candidate[0]] * num_frames

        frames = []
        last_idx = len(candidate) - 1
        for i in range(num_frames):
            t = i / float(max(num_frames - 1, 1))
            idx = int(round(t * last_idx))
            if idx < 0:
                idx = 0
            elif idx > last_idx:
                idx = last_idx
            frames.append(candidate[idx])
        return frames

    # Mode 2: Frame_Range (new semantics: Start + Step, stop after Num_Frames)
    elif mode == "Frame_Range":
        # Clamp start into the scene range
        start = max(start, default_start)
        if start > default_end:
            start = default_end

        frames = []
        current = start
        # Collect up to num_frames, but never go past the scene end
        for i in range(max(num_frames, 1)):
            if current > default_end:
                break
            frames.append(current)
            current += step

        if not frames:
            frames = [start]

        return frames

    # Fallback: simple clamped range using start/end/step
    else:
        if end < start:
            end = start
        start = max(start, default_start)
        end = min(end, default_end)
        if end < start:
            end = start
        frames = list(range(start, end + 1, step))
        if not frames:
            frames = [start]
        return frames


def _ensure_face_joints_3d(joints_vec):
    global _FACE_PREV_FWD
    """
    Populate basic and extended face joints in 3D so they naturally inherit
    head orientation per-frame.

    We build a simple local frame at the head using:
      - up    ~ head - neck
      - right ~ right_shoulder - left_shoulder
      - fwd   ~ up x right (sign fixed so it roughly points away from chest)

    Then we place:
      - canonical points: nose, left_eye, right_eye, left_ear, right_ear
      - clusters:
          * nose_dot_0..5
          * eye_L_0..4, eye_R_0..4
          * mouth_0..7
          * chin_0..10  (jaw-left -> chin -> jaw-right)

    These are all synthetic joints – ControlNet only cares that they are
    consistent pixels, not that their names match any specific schema.
    """
    head = joints_vec.get("head")
    neck = joints_vec.get("neck")
    chest = joints_vec.get("chest")
    left_sh = joints_vec.get("left_shoulder")
    right_sh = joints_vec.get("right_shoulder")

    if head is None:
        return

    # Local basis around head
    # Up: head - neck
    if neck is not None:
        up = (head - neck)
    else:
        up = Vector((0.0, 0.0, 1.0))

    if up.length < 1e-6:
        up = Vector((0.0, 0.0, 1.0))
    else:
        up.normalize()

    # Right: shoulder span
    if left_sh is not None and right_sh is not None:
        right = (right_sh - left_sh)
        shoulder_span = right.length
        if shoulder_span < 1e-6:
            right = Vector((1.0, 0.0, 0.0))
        else:
            right.normalize()
    else:
        right = Vector((1.0, 0.0, 0.0))
        shoulder_span = 0.25

    # Forward: up x right
    fwd = up.cross(right)
    if fwd.length < 1e-6:
        fwd = Vector((0.0, 1.0, 0.0))
    else:
        fwd.normalize()

    # Try to orient fwd from chest towards head if possible
    if chest is not None:
        v = (head - chest)
        if v.length > 1e-6 and fwd.dot(v) < 0.0:
            fwd = -fwd


    # Stabilise forward direction across frames to avoid 180° flips.
    if _FACE_PREV_FWD is not None:
        dot_prev = fwd.dot(_FACE_PREV_FWD)
        if dot_prev < 0.0:
            fwd = -fwd

    _FACE_PREV_FWD = fwd.copy()

    # Base scale: head-to-neck or shoulder span
    radius = 0.0
    if neck is not None:
        radius = (head - neck).length
    if radius < 1e-3 and shoulder_span > 0.0:
        radius = shoulder_span * 0.45
    if radius < 1e-3:
        radius = 0.25

    # Make the whole face ~10% larger than default
    radius *= 1.10

    center = head


    # --- Canonical points (single joints) ---

    # Nose: anchor point for the face – roughly centre, slightly in front
    nose = center + fwd * (radius * 0.55)
    # Override any rig-provided nose so the synthetic face stays consistent
    joints_vec["nose"] = nose

    # Eyes: explicitly ABOVE the nose so they never slip under the mouth.
    # We place them symmetrically around the head using the local up/right axes.
    eye_vertical = up * (radius * 0.22)    # clearly higher than the nose
    eye_side     = right * (radius * 0.32)
    eye_back     = -fwd * (radius * 0.05)  # a touch behind the nose

    eye_base = nose + eye_vertical + eye_back
    left_eye_pos  = eye_base - eye_side
    right_eye_pos = eye_base + eye_side

    # Override any rig-provided eyes so the 2D face is consistent
    joints_vec["left_eye"] = left_eye_pos
    joints_vec["right_eye"] = right_eye_pos

    # Ears: slightly above and behind head on each side
    ear_up = up * (radius * 0.15)
    ear_side = right * (radius * 0.55)
    ear_back = -fwd * (radius * 0.10)
    left_ear_pos = center + ear_up - ear_side + ear_back
    right_ear_pos = center + ear_up + ear_side + ear_back
    joints_vec.setdefault("left_ear", left_ear_pos)
    joints_vec.setdefault("right_ear", right_ear_pos)

    # --- Clusters: nose, eyes, mouth, chin ---

    # Nose: 6 dots along the bridge towards the mouth
    nose_dir_down = -up * (radius * 0.08)
    base_nose = joints_vec.get("nose", nose)
    for i in range(6):
        t = i / 5.0  # 0..1
        p = base_nose + nose_dir_down * (t * 5.0)
        joints_vec[f"nose_dot_{i}"] = p

    # Eyes: small 5-point clusters around each eye centre (ellipse in right/up plane)
    eye_cluster_radius_h = radius * 0.06
    eye_cluster_radius_v = radius * 0.04
    eye_centres = {
        "L": joints_vec.get("left_eye", left_eye_pos),
        "R": joints_vec.get("right_eye", right_eye_pos),
    }
    for side, centre in eye_centres.items():
        for i in range(5):
            # Angles across upper & lower eyelid
            angle = (-0.6 + 0.3 * i) * math.pi  # -0.6π .. 0.6π
            offset = (right * (math.cos(angle) * eye_cluster_radius_h) +
                      up    * (math.sin(angle) * eye_cluster_radius_v))
            p = centre + offset
            joints_vec[f"eye_{side}_{i}"] = p

    # Mouth: compact arc just under the nose
    mouth_center = nose - up * (radius * 0.18)
    mouth_h = radius * 0.25
    mouth_v = radius * 0.08
    for i in range(8):
        # -1..1 across the smile
        t = -1.0 + 2.0 * (i / 7.0)
        # Concave arc (simple smile)
        x_off = t
        y_off = -(1.0 - t * t)
        offset = right * (x_off * mouth_h) + up * (y_off * mouth_v)
        joints_vec[f"mouth_{i}"] = mouth_center + offset

    # --- Jaw / chin: strong U-shaped arc ---
    #
    # We want the jaw-line endpoints (left/right) roughly level with the eyes,
    # and the chin clearly below the mouth, forming a rounded U / heart shape.

    # Mid-point between the two eyes gives us a natural "cheek height".
    eye_mid = (left_eye_pos + right_eye_pos) * 0.5

    # Jaw endpoints: at (approximately) eye height, but pushed out wider than the mouth.
#was 0.9
    jaw_half_width = radius * 0.7
    jaw_left  = eye_mid - right * jaw_half_width
    jaw_right = eye_mid + right * jaw_half_width

    # Chin: drop well below the mouth to create a strong arc.
    chin_drop = radius * 2.1
    chin = eye_mid - up * chin_drop

    # Quadratic Bezier from jaw-left -> chin -> jaw-right
    for i in range(11):
        t = i / 10.0  # 0..1
        one_t = 1.0 - t
        p = (jaw_left * (one_t * one_t) +
             chin     * (2.0 * one_t * t) +
             jaw_right * (t * t))
        joints_vec[f"chin_{i}"] = p

def main():
    args = parse_args()

    fbx_path = args["fbx"]
    out_dir = args["out"]

    if not fbx_path or not os.path.isfile(fbx_path):
        print("ERROR: FBX file missing or invalid:", fbx_path)
        return

    if not out_dir:
        print("ERROR: Output folder not specified.")
        return

    os.makedirs(out_dir, exist_ok=True)

    clear_scene()
    import_fbx(fbx_path)

    arm = find_armature()
    if arm is None:
        print("ERROR: No armature found in FBX.")
        return

    action, f_start, f_end = get_action_and_range(arm)
    frame_indices = compute_frames(args, f_start, f_end)

    pbone_map, found_joints, missing_joints = build_pose_bone_map(arm)

    scene = bpy.context.scene

    frames_out = []
    for f in frame_indices:
        scene.frame_set(f)
        bpy.context.view_layer.update()

        joints_vec = {}
        for cname in CANONICAL_JOINTS:
            pbone = pbone_map.get(cname)
            if pbone is None:
                continue
            world_pos = arm.matrix_world @ pbone.head
            joints_vec[cname] = world_pos

        _ensure_face_joints_3d(joints_vec)

        joints = {}
        for cname, v in joints_vec.items():
            joints[cname] = [float(v.x), float(v.y), float(v.z)]

        frames_out.append({
            "frame_index": int(f),
            "joints": joints,
        })

    data = {
        "fbx_file": os.path.abspath(fbx_path),
        "frame_indices": frame_indices,
        "frames": frames_out,
    }

    out_json = os.path.join(out_dir, "joint_data.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    frame_info = {
        "fbx_file": os.path.abspath(fbx_path),
        "frame_indices": frame_indices,
        "frame_start": f_start,
        "frame_end": f_end,
        "frame_mode": args["frame_mode"],
        "num_frames": args["num_frames"],
        "start_frame_arg": args["start_frame"],
        "end_frame_arg": args["end_frame"],
        "frame_step": args["frame_step"],
        "found_joints": found_joints,
        "missing_joints": missing_joints,
    }
    info_path = os.path.join(out_dir, "frame_info.json")
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(frame_info, f, indent=2)

    print("FBX pose extraction complete.")


if __name__ == "__main__":
    main()