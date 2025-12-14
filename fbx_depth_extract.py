import bpy
import sys
import os
import json
import math
from mathutils import Vector


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
        "out_width": 512,
        "out_height": 512,
        "zoom_factor": 1.0,
        "view_mode": "Front",
    }

    key = None
    for item in argv:
        if item.startswith("--"):
            key = item[2:]
        else:
            if key in args:
                if key in ["num_frames", "start_frame", "end_frame", "frame_step", "out_width", "out_height"]:
                    args[key] = int(item)
                elif key == "zoom_factor":
                    try:
                        args[key] = float(item)
                    except Exception:
                        args[key] = 1.0
                elif key == "view_mode":
                    args[key] = item
                else:
                    args[key] = item
            key = None

    if args["zoom_factor"] <= 0.0:
        args["zoom_factor"] = 1.0

    valid_views = {"Front", "Back", "Left_Side", "Right_Side", "Top", "Auto_Rotate"}
    if args["view_mode"] not in valid_views:
        args["view_mode"] = "Front"

    return args


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_fbx(path):
    bpy.ops.import_scene.fbx(filepath=path)


def find_ref_object():
    arm_obj = None
    mesh_obj = None
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and mesh_obj is None:
            mesh_obj = obj
        if obj.type == 'ARMATURE' and arm_obj is None:
            arm_obj = obj
    return mesh_obj or arm_obj


def get_action_and_range(ref_obj):
    if ref_obj.animation_data and ref_obj.animation_data.action:
        action = ref_obj.animation_data.action
        f_start, f_end = action.frame_range
        return action, int(f_start), int(f_end)
    scene = bpy.context.scene
    return None, scene.frame_start, scene.frame_end


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
        for _ in range(max(num_frames, 1)):
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


def _get_world_bbox_center_radius_height(obj):
    if not hasattr(obj, "bound_box"):
        return Vector((0.0, 0.0, 1.6)), 1.0, 2.0

    pts_world = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    center = sum(pts_world, Vector()) / 8.0

    xs = [p.x for p in pts_world]
    ys = [p.y for p in pts_world]
    zs = [p.z for p in pts_world]
    width = max(xs) - min(xs)
    depth = max(ys) - min(ys)
    height = max(zs) - min(zs)

    radius = max(width, depth, height) * 0.5
    if radius < 0.1:
        radius = 0.1
    if height < 0.1:
        height = 0.1

    return center, radius, height


def _get_camera_position(center, radius, ref_obj, view_mode):
    distance = radius * 3.0

    if view_mode == "Back":
        pos = center + Vector((0.0, distance, 0.0))
    elif view_mode == "Left_Side":
        pos = center + Vector((distance, 0.0, 0.0))
    elif view_mode == "Right_Side":
        pos = center + Vector((-distance, 0.0, 0.0))
    elif view_mode == "Top":
        pos = center + Vector((0.0, 0.0, distance))
    elif view_mode == "Auto_Rotate":
        local_forward = Vector((0.0, 1.0, 0.0))
        world_forward = (ref_obj.matrix_world.to_3x3() @ local_forward).normalized()
        pos = center - world_forward * distance
    else:
        pos = center + Vector((0.0, -distance, 0.0))

    return pos


def ensure_camera_and_mist(scene, ref_obj, out_width, out_height, depth_dir, zoom_factor, view_mode):
    scene.render.engine = 'CYCLES'

    for view_layer in scene.view_layers:
        view_layer.use_pass_mist = True

    world = scene.world
    if world is None:
        world = bpy.data.worlds.new("FBXDepthWorld")
        scene.world = world

    center, radius, height = _get_world_bbox_center_radius_height(ref_obj)

    world.mist_settings.use_mist = True
    world.mist_settings.start = 0.0
    world.mist_settings.depth = radius * 4.0
    world.mist_settings.falloff = 'LINEAR'

    cam = None
    for obj in scene.objects:
        if obj.type == 'CAMERA':
            cam = obj
            break

    if cam is None:
        cam_data = bpy.data.cameras.new("FBXDepthCam")
        cam = bpy.data.objects.new("FBXDepthCam", cam_data)
        scene.collection.objects.link(cam)

    scene.camera = cam

    cam.data.type = 'ORTHO'
    # Base scale uses both radius and height so we keep the whole body
    base_scale = max(radius * 2.6, height * 1.4)
    cam.data.ortho_scale = base_scale / zoom_factor

    cam.location = _get_camera_position(center, radius, ref_obj, view_mode)

    direction = (center - cam.location).normalized()
    up = Vector((0.0, 0.0, 1.0))
    if view_mode == "Top":
        up = Vector((0.0, 1.0, 0.0))

    quat = direction.to_track_quat('-Z', 'Y')
    cam.rotation_euler = quat.to_euler()
    cam.data.shift_x = 0.0
    cam.data.shift_y = 0.0

    distance = (cam.location - center).length
    cam.data.clip_start = max(distance * 0.1, 0.01)
    cam.data.clip_end = distance * 10.0

    scene.render.resolution_x = out_width
    scene.render.resolution_y = out_height
    scene.render.resolution_percentage = 100

    depth_dir_abs = os.path.abspath(depth_dir)
    os.makedirs(depth_dir_abs, exist_ok=True)

    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()

    rl = tree.nodes.new('CompositorNodeRLayers')
    rl.location = (0, 0)

    mist_socket_name = None
    for candidate in ["Mist"]:
        if candidate in rl.outputs:
            mist_socket_name = candidate
            break

    if mist_socket_name is None:
        print("FBX Depth: WARNING - no Mist output on Render Layers node; depth maps will not be saved.")
        return

    normalize = tree.nodes.new('CompositorNodeNormalize')
    normalize.location = (200, 0)

    out = tree.nodes.new('CompositorNodeOutputFile')
    out.location = (400, 0)
    out.base_path = depth_dir_abs
    out.file_slots[0].path = "depth_"
    out.format.file_format = 'PNG'
    out.format.color_mode = 'BW'
    out.format.color_depth = '16'

    tree.links.new(rl.outputs[mist_socket_name], normalize.inputs[0])
    tree.links.new(normalize.outputs[0], out.inputs[0])


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

    ref_obj = find_ref_object()
    if ref_obj is None:
        print("ERROR: No armature or mesh found in FBX.")
        return

    action, f_start, f_end = get_action_and_range(ref_obj)
    frame_indices = compute_frames(args, f_start, f_end)

    scene = bpy.context.scene

    depth_dir = os.path.join(out_dir, "depth")

    for f in frame_indices:
        scene.frame_set(f)
        bpy.context.view_layer.update()
        # Recompute bbox & camera per frame so nothing clips out
        ensure_camera_and_mist(
            scene,
            ref_obj,
            args["out_width"],
            args["out_height"],
            depth_dir,
            args["zoom_factor"],
            args["view_mode"],
        )
        bpy.ops.render.render(write_still=True)

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
        "out_width": args["out_width"],
        "out_height": args["out_height"],
        "zoom_factor": args["zoom_factor"],
        "view_mode": args["view_mode"],
    }
    info_path = os.path.join(out_dir, "depth_info.json")
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(frame_info, f, indent=2)

    print("FBX depth (zoomable mist + views, recentered per frame) extraction complete.")


if __name__ == "__main__":
    main()
