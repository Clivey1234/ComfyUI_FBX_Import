import bpy
import sys
import os
import json
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
        "frame_mode": "Sample_N_Frames",
        "num_frames": 24,
        "start_frame": 0,
        "end_frame": 100,
        "frame_step": 1,
        "out_width": 512,
        "out_height": 512,
        "zoom_factor": 1.0,
        "view_mode": "Front",
    }

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--fbx" and i + 1 < len(argv):
            args["fbx"] = argv[i + 1]
            i += 2
        elif a == "--out" and i + 1 < len(argv):
            args["out"] = argv[i + 1]
            i += 2
        elif a == "--frame_mode" and i + 1 < len(argv):
            args["frame_mode"] = argv[i + 1]
            i += 2
        elif a == "--num_frames" and i + 1 < len(argv):
            try:
                args["num_frames"] = int(argv[i + 1])
            except Exception:
                pass
            i += 2
        elif a == "--start_frame" and i + 1 < len(argv):
            try:
                args["start_frame"] = int(argv[i + 1])
            except Exception:
                pass
            i += 2
        elif a == "--end_frame" and i + 1 < len(argv):
            try:
                args["end_frame"] = int(argv[i + 1])
            except Exception:
                pass
            i += 2
        elif a == "--frame_step" and i + 1 < len(argv):
            try:
                args["frame_step"] = int(argv[i + 1])
            except Exception:
                pass
            i += 2
        elif a == "--out_width" and i + 1 < len(argv):
            try:
                args["out_width"] = int(argv[i + 1])
            except Exception:
                pass
            i += 2
        elif a == "--out_height" and i + 1 < len(argv):
            try:
                args["out_height"] = int(argv[i + 1])
            except Exception:
                pass
            i += 2
        elif a == "--zoom_factor" and i + 1 < len(argv):
            try:
                args["zoom_factor"] = float(argv[i + 1])
            except Exception:
                pass
            i += 2
        elif a == "--view_mode" and i + 1 < len(argv):
            args["view_mode"] = argv[i + 1]
            i += 2
        else:
            i += 1

    return args


def clear_scene():
    bpy.ops.wm.read_homefile(use_empty=True)


def import_fbx(filepath):
    bpy.ops.import_scene.fbx(filepath=filepath)
    armature = None
    mesh_obj = None

    for obj in bpy.context.scene.objects:
        if obj.type == "ARMATURE" and armature is None:
            armature = obj
        if obj.type == "MESH" and mesh_obj is None:
            mesh_obj = obj

    if armature is not None:
        return armature
    if mesh_obj is not None:
        return mesh_obj

    for obj in bpy.context.scene.objects:
        return obj

    return None


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

    radius = max(width, depth) * 0.5
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
    else:
        # Front / default
        pos = center + Vector((0.0, -distance, 0.0))

    return pos


def ensure_camera_and_rgb(scene, ref_obj, out_width, out_height, rgb_dir, zoom_factor, view_mode):
    scene.render.engine = "CYCLES"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"

    world = scene.world
    if world is None:
        world = bpy.data.worlds.new("FBXCannyWorld")
        scene.world = world

    center, radius, height = _get_world_bbox_center_radius_height(ref_obj)

    cam = None
    for obj in scene.objects:
        if obj.type == "CAMERA":
            cam = obj
            break

    if cam is None:
        cam_data = bpy.data.cameras.new("FBXCannyCamera")
        cam = bpy.data.objects.new("FBXCannyCamera", cam_data)
        scene.collection.objects.link(cam)
        scene.camera = cam

    cam.data.type = "ORTHO"
    # Similar logic to depth node: ortho scale based on radius/height and zoom
    scale_base = max(radius * 2.5, height * 1.4)
    if zoom_factor <= 0.0:
        zoom_factor = 1.0
    cam.data.ortho_scale = scale_base / zoom_factor

    cam.location = _get_camera_position(center, radius, ref_obj, view_mode)

    direction = (center - cam.location).normalized()
    up = Vector((0.0, 0.0, 1.0))
    if view_mode == "Top":
        up = Vector((0.0, 1.0, 0.0))

    quat = direction.to_track_quat("-Z", "Y")
    cam.rotation_euler = quat.to_euler()
    cam.data.shift_x = 0.0
    cam.data.shift_y = 0.0

    distance = (cam.location - center).length
    cam.data.clip_start = max(distance * 0.1, 0.01)
    cam.data.clip_end = distance * 10.0

    scene.render.resolution_x = out_width
    scene.render.resolution_y = out_height
    scene.render.resolution_percentage = 100

    rgb_dir_abs = os.path.abspath(rgb_dir)
    os.makedirs(rgb_dir_abs, exist_ok=True)

    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()

    rl = tree.nodes.new("CompositorNodeRLayers")
    rl.location = (0, 0)

    out = tree.nodes.new("CompositorNodeOutputFile")
    out.location = (200, 0)
    out.base_path = rgb_dir_abs
    out.file_slots[0].path = "rgb_"
    out.format.file_format = "PNG"
    out.format.color_mode = "RGB"
    out.format.color_depth = "8"

    tree.links.new(rl.outputs["Image"], out.inputs[0])


def compute_frame_indices(scene, frame_mode, num_frames, start, end, step):
    if not scene:
        return []

    default_start, default_end = scene.frame_start, scene.frame_end
    if default_end < default_start:
        default_end = default_start

    if frame_mode == "Sample_N_Frames":
        frame_start = max(default_start, start)
        frame_end = min(default_end, end if end >= start else default_end)
        if frame_end < frame_start:
            frame_end = frame_start

        candidate = list(range(frame_start, frame_end + 1))
        if not candidate:
            return [frame_start]

        if num_frames <= 1:
            return [candidate[0]]

        frames = []
        last_idx = len(candidate) - 1
        for i in range(num_frames):
            t = i / float(max(num_frames - 1, 1))
            idx = int(round(t * last_idx))
            idx = max(0, min(last_idx, idx))
            frames.append(candidate[idx])
        return frames
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


def main():
    args = parse_args()

    fbx_path = args["fbx"]
    out_dir = args["out"]

    if not fbx_path or not os.path.isfile(fbx_path):
        print("ERROR: FBX file missing or invalid:", fbx_path)
        return
    if not out_dir:
        print("ERROR: output directory not specified.")
        return

    clear_scene()
    ref_obj = import_fbx(fbx_path)
    if ref_obj is None:
        print("ERROR: Failed to import FBX or find reference object.")
        return

    scene = bpy.context.scene
    frames = compute_frame_indices(
        scene,
        args["frame_mode"],
        args["num_frames"],
        args["start_frame"],
        args["end_frame"],
        args["frame_step"],
    )

    rgb_dir = os.path.join(out_dir, "rgb")
    frame_indices = []

    for frame in frames:
        scene.frame_set(frame)
        frame_indices.append(frame)

        ensure_camera_and_rgb(
            scene,
            ref_obj,
            args["out_width"],
            args["out_height"],
            rgb_dir,
            args["zoom_factor"],
            args["view_mode"],
        )
        bpy.ops.render.render(write_still=True)

    frame_info = {
        "fbx_file": os.path.abspath(fbx_path),
        "frame_indices": frame_indices,
        "frame_start": args["start_frame"],
        "frame_end": args["end_frame"],
        "frame_mode": args["frame_mode"],
        "num_frames_requested": args["num_frames"],
        "frame_step": args["frame_step"],
        "out_width": args["out_width"],
        "out_height": args["out_height"],
        "zoom_factor": args["zoom_factor"],
        "view_mode": args["view_mode"],
    }
    info_path = os.path.join(out_dir, "canny_info.json")
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(frame_info, f, indent=2)

    print("FBX Canny (RGB frames for edge detection) extraction complete.")


if __name__ == "__main__":
    main()
