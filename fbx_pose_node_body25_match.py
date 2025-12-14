# Alignment_Mode dropdown to scale/position our FBX stickman
# to match that reference pose image.
#  Cam_Rotate_Start / Cam_Rotate_End to pan the camera in Front view
# I know, all you Linux users are maoning that this probably wont wont on linux
# but Ive tried Linux and hate it, so sorry, unless you can change the code to get it working, its just for windows


import os
import json
import uuid
import subprocess
import tempfile

import numpy as np

from .fbx_pose_helpers_body25_match import generate_aligned_pose_images


class FBX_Extraction:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Blender_Executable": (
                    "STRING",
                    {
                        "default": "C:\\Program Files\\Blender Foundation\\Blender 3.6\\blender.exe",
                        "multiline": False,
                    },
                ),
                "FBX_File": ("STRING", {"default": "", "multiline": False}),
                "Frame_Mode": (
                    ["Frame_Spread_TotalAnim", "Frame_Range"],
                    {"default": "Frame_Spread_TotalAnim"},
                ),
                "Num_Frames": ("INT", {"default": 81, "min": 1, "max": 9999}),
                "Start_Frame": ("INT", {"default": 0, "min": 0, "max": 999999}),
                "End_Frame": ("INT", {"default": 500, "min": 0, "max": 999999}),
                "Frame_Step": ("INT", {"default": 1, "min": 1, "max": 9999}),
                "Output_Width": ("INT", {"default": 1024, "min": 64, "max": 2048}),
                "Output_Height": ("INT", {"default": 1024, "min": 64, "max": 2048}),
                "Camera_View": (
                    ["Front", "Back", "Left Side", "Right Side", "Top", "Auto (Face Camera)"],
                    {"default": "Front"},
                ),
                "Projection_Mode": (
                    ["Orthographic (Stable)", "Perspective (Experimental)"],
                    {"default": "Perspective (Experimental)"},
                ),
                "Color_Mode": (
                    ["White", "OpenPose", "ControlNet Colors"],
                    {"default": "ControlNet Colors"},
                ),
                "Face_Mode": (
                    ["Off", "Dots Only (BODY_25)", "Full Face (FACE_70)"],
                    {"default": "Full Face (FACE_70)"},
                ),
                "Joint_Size": ("INT", {"default": 4, "min": 1, "max": 50}),
                "Line_Thickness": ("INT", {"default": 2, "min": 1, "max": 50}),
                "Zoom_Factor": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.1, "max": 20.0, "step": 0.1},
                ),
                "Alignment_Mode": (
                    [
                        "Off",
                        "Match Full Body",
                        "Upper Body (Head-Hips)",
                        "Auto (Full/Partial)",
                    ],
                    {"default": "Match Full Body"},
                ),
            },
            "optional": {
                "Ref_Pose_Image": ("IMAGE",),
                "Cam_In": ("STRING", {"default": "", "multiline": False}),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("Pose_Images", "Frame_Info",)
    FUNCTION = "generate_pose_images"
    CATEGORY = "Animation/FBX_Clivey"

    def _get_script_path(self):
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "fbx_pose_extract.py")
        if not os.path.isfile(path):
            raise RuntimeError(
                f"FBX Pose BODY_25 Match (Blender): fbx_pose_extract.py not found:\n{path}"
            )
        return path

    def _blank_image_stack(self, frames, width, height):
        import torch
        if frames <= 0:
            frames = 1
        arr = np.zeros((frames, height, width, 3), dtype=np.float32)
        return torch.from_numpy(arr)

    def generate_pose_images(
        self,
        Blender_Executable,
        FBX_File,
        Frame_Mode,
        Num_Frames,
        Start_Frame,
        End_Frame,
        Frame_Step,
        Output_Width,
        Output_Height,
        Camera_View,
        Projection_Mode,
        Color_Mode,
        Face_Mode,
        Joint_Size,
        Line_Thickness,
        Zoom_Factor,

        Alignment_Mode,
        Cam_In=None,
        Ref_Pose_Image=None,
    ):
        Inplace = False
        blender_exe = Blender_Executable.strip().strip('"')
        if not blender_exe or not os.path.isfile(blender_exe):
            raise RuntimeError(
                f"FBX Pose BODY_25 Match (Blender): Blender executable not found:\n{blender_exe}"
            )

        fbx_path = FBX_File.strip().strip('"')
        if not fbx_path or not os.path.isfile(fbx_path):
            raise RuntimeError(
                f"FBX Pose BODY_25 Match (Blender): FBX file not found:\n{fbx_path}"
            )

        script_path = self._get_script_path()

        if Frame_Mode == "Frame_Spread_TotalAnim":
            if End_Frame <= Start_Frame:
                End_Frame = Start_Frame + max(Num_Frames - 1, 0)
        else:
            if End_Frame < Start_Frame:
                End_Frame = Start_Frame

        out_dir = os.path.join(
            tempfile.gettempdir(),
            f"fbx_pose_blender_body25_match_{uuid.uuid4().hex}",
        )
        os.makedirs(out_dir, exist_ok=True)

        args = [
            blender_exe,
            "-b",
            "-P", script_path,
            "--",
            "--fbx", fbx_path,
            "--out", out_dir,
            "--frame_mode", Frame_Mode,
            "--num_frames", str(Num_Frames),
            "--start_frame", str(Start_Frame),
            "--end_frame", str(End_Frame),
            "--frame_step", str(Frame_Step),
        ]

        result = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "FBX Pose BODY_25 Match (Blender): Blender pose extractor failed.\n"
                f"Command: {' '.join(args)}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}\n"
            )

        joint_json_path = os.path.join(out_dir, "joint_data.json")
        if not os.path.isfile(joint_json_path):
            raise RuntimeError(
                "FBX Pose BODY_25 Match (Blender): joint_data.json not produced by Blender script.\n"
                f"Output dir: {out_dir}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}\n"
            )

        with open(joint_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        frames = data.get("frames", [])
        joint_frames = []
        for fitem in frames:
            joints = fitem.get("joints", {})
            cleaned = {}
            for jname, pos in joints.items():
                if not isinstance(pos, (list, tuple)) or len(pos) != 3:
                    continue
                cleaned[jname] = [float(pos[0]), float(pos[1]), float(pos[2])]
            joint_frames.append(cleaned)

        num_actual = len(joint_frames)

        if num_actual == 0:
            pose_tensor = self._blank_image_stack(
                1, Output_Width, Output_Height
            )
        else:
            # If fewer frames than requested, pad with last frame
            if num_actual < Num_Frames:
                last_frame = joint_frames[-1]
                pad_count = Num_Frames - num_actual
                for _ in range(pad_count):
                    joint_frames.append(last_frame)

            pose_tensor = generate_aligned_pose_images(
                joint_frames,
                Output_Width,
                Output_Height,
                Camera_View,
                Zoom_Factor,
                Inplace,
                Color_Mode,
                Face_Mode,
                Joint_Size,
                Line_Thickness,
                Ref_Pose_Image,
                Alignment_Mode,
                Projection_Mode,
                cam_profile_str=Cam_In,
            )

        frame_info_path = os.path.join(out_dir, "frame_info.json")
        if os.path.isfile(frame_info_path):
            try:
                with open(frame_info_path, "r", encoding="utf-8") as f:
                    frame_info = json.load(f)
            except Exception:
                frame_info = {}
        else:
            frame_info = {}

        frame_info.setdefault("fbx_file", fbx_path)
        frame_info.setdefault("frame_mode", Frame_Mode)
        frame_info.setdefault("num_frames_requested", Num_Frames)
        frame_info.setdefault("camera_view", Camera_View)
        frame_info.setdefault("projection_mode", Projection_Mode)
        frame_info.setdefault("color_mode", Color_Mode)
        frame_info.setdefault("face_mode", Face_Mode)
        frame_info.setdefault("output_width", Output_Width)
        frame_info.setdefault("output_height", Output_Height)
        frame_info.setdefault("zoom_factor", Zoom_Factor)
        frame_info.setdefault("inplace", bool(Inplace))
        frame_info.setdefault("alignment_mode", Alignment_Mode)
        frame_info.setdefault("skeleton_style", "BODY_25_MATCH_IMAGE")

        return (pose_tensor, json.dumps(frame_info))
