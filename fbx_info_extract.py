
import bpy
import sys
import json
import struct
import re


def read_fbx_header(fbx_path):
    """
    Best-effort read of FBX version and Creator/exporter
    directly from the FBX file header.

    Works for both binary and ASCII FBX.
    """
    fbx_version = ""
    exporter = ""

    try:
        with open(fbx_path, "rb") as f:
            chunk = f.read(8192)  # small header chunk is enough

        # ----- FBX version -----
        # Binary header starts with 'FBX Binary  ' then a few bytes,
        # then a 4-byte little-endian version integer.
        if chunk.startswith(b"Kaydara FBX Binary"):
            if len(chunk) >= 27:
                ver_int = struct.unpack("<I", chunk[23:27])[0]
                fbx_version = str(ver_int)
        else:
            # ASCII or unknown; look for FBXHeaderVersion
            m = re.search(rb"FBXHeaderVersion[^0-9]*([0-9]+)", chunk)
            if m:
                fbx_version = m.group(1).decode("ascii", "ignore")

        # ----- Creator / exporter -----
        # Look for 'Creator: "something"' in the header.
        m = re.search(rb"Creator[^\"]*\"([^\"]+)\"", chunk)
        if m:
            exporter = m.group(1).decode("utf-8", "ignore")

    except Exception:
        # Leave them empty; node will treat as "Unknown".
        pass

    return fbx_version, exporter


def safe_print_result(
    error=None,
    fps=0.0,
    frame_count=0,
    skinned=False,
    fbx_version="",
    exporter="",
    root_motion=False,
):
    """
    Always print a single JSON line as the LAST thing printed.
    The Comfy node will look for this.
    """
    result = {
        "error": error or "",
        "fps": float(fps),
        "frame_count": int(frame_count),
        "skinned": bool(skinned),
        "fbx_version": fbx_version or "",
        "exporter": exporter or "",
        "root_motion": bool(root_motion),
    }
    print(json.dumps(result))


def find_animation_frame_range():
    """
    Scan all actions & fcurves and compute the min/max keyframe.
    Returns (min_frame, max_frame) or (None, None) if no keys found.
    """
    min_frame = None
    max_frame = None

    for action in bpy.data.actions:
        for fcu in action.fcurves:
            for kp in fcu.keyframe_points:
                frame = kp.co.x  # x is the frame position
                if min_frame is None or frame < min_frame:
                    min_frame = frame
                if max_frame is None or frame > max_frame:
                    max_frame = frame

    return min_frame, max_frame


def detect_root_motion(scene, min_frame, max_frame):
    """
    Heuristic detection of root motion vs in-place.

    Strategy:
        - Find an armature object.
        - Prefer a root bone (Root/Hips/Pelvis/etc); else use armature object.
        - Sample its world position over a set of frames.
        - If it clearly travels in space, classify as root motion.

    Returns True if root motion is detected, otherwise False.
    """
    try:
        armature = next(obj for obj in scene.objects if obj.type == 'ARMATURE')
    except StopIteration:
        return False

    if min_frame is None or max_frame is None:
        return False

    start = int(round(min_frame))
    end = int(round(max_frame))
    if end <= start:
        return False

    # Number of samples (max 20 for efficiency)
    length = end - start
    steps = min(20, max(2, length + 1))
    frames = [start + int((length * i) / (steps - 1)) for i in range(steps)]

    # Choose a root bone if possible
    arm_data = armature.data
    root_bone = None

    # First try "no parent" bones
    for bone in arm_data.bones:
        if bone.parent is None:
            root_bone = bone
            break

    # Override with more specific common root names if present
    for name in ["root", "hips", "hip", "pelvis"]:
        b = arm_data.bones.get(name)
        if b is not None:
            root_bone = b
            break

    positions = []

    for fr in frames:
        scene.frame_set(fr)

        if root_bone:
            pose_bone = armature.pose.bones.get(root_bone.name)
            if pose_bone:
                world_mat = armature.matrix_world @ pose_bone.matrix
                pos = world_mat.to_translation()
            else:
                pos = armature.matrix_world.translation.copy()
        else:
            pos = armature.matrix_world.translation.copy()

        positions.append(pos.copy())

    if len(positions) < 2:
        return False

    # Net displacement between first and last sample
    net_disp = (positions[-1] - positions[0]).length

    # Path length (sum of step distances)
    path_len = 0.0
    for i in range(len(positions) - 1):
        step = (positions[i + 1] - positions[i]).length
        path_len += step

    # Thresholds (rough but practical):
    # - Anything under ~5cm total is treated as in-place (numerical wobble).
    # - Bigger moves are treated as root motion.
    threshold = 0.05  # 5 cm in Blender units (~meters)

    if net_disp > threshold or path_len > threshold * 2.0:
        return True

    return False


def main():
    argv = sys.argv

    if "--" not in argv:
        safe_print_result(error="No FBX path passed after --")
        return

    fbx_path = argv[argv.index("--") + 1]

    # Try to read header info up front (works even if Blender import fails)
    fbx_version, exporter = read_fbx_header(fbx_path)

    try:
        # Fresh scene
        try:
            bpy.ops.wm.read_homefile(use_empty=True)
        except Exception:
            bpy.ops.wm.read_factory_settings()

        # Import FBX
        try:
            bpy.ops.import_scene.fbx(filepath=fbx_path)
        except Exception as e:
            safe_print_result(
                error=f"Failed to import FBX: {e}",
                fbx_version=fbx_version,
                exporter=exporter,
            )
            return

        scene = bpy.context.scene

        # FPS
        fps = float(scene.render.fps) / float(scene.render.fps_base)

        # Frame count from keyframes
        min_frame, max_frame = find_animation_frame_range()
        if min_frame is not None and max_frame is not None:
            min_f = int(round(min_frame))
            max_f = int(round(max_frame))
            frame_count = max(0, max_f - min_f + 1)
        else:
            frame_start = int(scene.frame_start)
            frame_end = int(scene.frame_end)
            if len(bpy.data.actions) == 0:
                frame_count = 0
            else:
                frame_count = max(0, frame_end - frame_start + 1)
            # Use scene range for motion detection if we didn't get keyframes
            min_f = frame_start
            max_f = frame_end

        # Detect skinned mesh (mesh with armature modifier)
        skinned = False
        for obj in scene.objects:
            if obj.type == 'MESH':
                for mod in obj.modifiers:
                    if mod.type == 'ARMATURE':
                        skinned = True
                        break
            if skinned:
                break

        # Detect root motion vs in-place
        root_motion = False
        try:
            root_motion = detect_root_motion(scene, min_f, max_f)
        except Exception:
            root_motion = False

        safe_print_result(
            error="",
            fps=fps,
            frame_count=frame_count,
            skinned=skinned,
            fbx_version=fbx_version,
            exporter=exporter,
            root_motion=root_motion,
        )

    except Exception as e:
        safe_print_result(
            error=f"Unexpected exception: {e}",
            fbx_version=fbx_version,
            exporter=exporter,
            root_motion=False,
        )


if __name__ == "__main__":
    main()
