import os
import json
import uuid
import subprocess
import tempfile

import numpy as np
import torch
from PIL import Image


class FBX_Depth_Blender:
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
                "Num_Frames": ("INT", {"default": 24, "min": 1, "max": 9999}),
                "Start_Frame": ("INT", {"default": 0, "min": 0, "max": 999999}),
                "End_Frame": ("INT", {"default": 100, "min": 0, "max": 999999}),
                "Frame_Step": ("INT", {"default": 1, "min": 1, "max": 9999}),
                "Output_Width": ("INT", {"default": 512, "min": 64, "max": 4096}),
                "Output_Height": ("INT", {"default": 512, "min": 64, "max": 4096}),
                "Zoom_Factor": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 20.0, "step": 0.1}),
                "View_Mode": (
                    ["Front", "Back", "Left_Side", "Right_Side", "Top", "Auto_Rotate"],
                    {"default": "Front"},
                ),
                "Invert_Depth": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("Depth_Images", "Depth_Info",)
    FUNCTION = "generate_depth_images"
    CATEGORY = "Animation/FBX_Clivey"

    def _get_script_path(self):
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "fbx_depth_extract.py")
        if not os.path.isfile(path):
            raise RuntimeError(
                f"FBX Depth (Blender Z-Depth): fbx_depth_extract.py not found:\n{path}"
            )
        return path

    def _blank_image_stack(self, frames, width, height):
        if frames <= 0:
            frames = 1
        arr = np.zeros((frames, height, width, 3), dtype=np.float32)
        return torch.from_numpy(arr)

    def _load_depth_stack(self, depth_dir, width, height, invert):
        if not os.path.isdir(depth_dir):
            return None

        files = sorted(
            f for f in os.listdir(depth_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        )
        if not files:
            return None

        images = []
        for fname in files:
            path = os.path.join(depth_dir, fname)
            try:
                img = Image.open(path)
            except Exception:
                continue

            if img.mode in ("I;16", "I"):
                arr = np.array(img, dtype=np.uint16).astype(np.float32)
                maxval = 65535.0
            else:
                img = img.convert("L")
                arr = np.array(img, dtype=np.float32)
                maxval = 255.0

            if arr.shape != (height, width):
                img_resized = Image.fromarray(
                    arr.astype(np.uint16) if maxval == 65535.0 else arr.astype(np.uint8)
                )
                img_resized = img_resized.resize((width, height), Image.BILINEAR)
                arr = np.array(img_resized, dtype=np.float32)

            arr = np.clip(arr / maxval, 0.0, 1.0)
            if invert:
                arr = 1.0 - arr
            arr3 = np.stack([arr, arr, arr], axis=-1)
            images.append(arr3)

        if not images:
            return None

        depth_np = np.stack(images, axis=0)
        return torch.from_numpy(depth_np.astype(np.float32))

    def generate_depth_images(
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
        Zoom_Factor,
        View_Mode,
        Invert_Depth,
    ):
        blender_exe = Blender_Executable.strip().strip('"')
        if not blender_exe or not os.path.isfile(blender_exe):
            raise RuntimeError(
                f"FBX Depth (Blender Z-Depth): Blender executable not found:\n{blender_exe}"
            )

        fbx_path = FBX_File.strip().strip('"')
        if not fbx_path or not os.path.isfile(fbx_path):
            raise RuntimeError(
                f"FBX Depth (Blender Z-Depth): FBX file not found:\n{fbx_path}"
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
            f"fbx_pose_blender_depth_{uuid.uuid4().hex}",
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
            "--out_width", str(Output_Width),
            "--out_height", str(Output_Height),
            "--zoom_factor", str(Zoom_Factor),
            "--view_mode", View_Mode,
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
                "FBX Depth (Blender Z-Depth): Blender depth extractor failed.\n"
                f"Command: {' '.join(args)}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}\n"
            )

        depth_dir = os.path.join(out_dir, "depth")
        depth_tensor = self._load_depth_stack(
            depth_dir, Output_Width, Output_Height, Invert_Depth
        )
        if depth_tensor is None:
            depth_tensor = self._blank_image_stack(
                Num_Frames, Output_Width, Output_Height
            )

        info_path = os.path.join(out_dir, "depth_info.json")
        if os.path.isfile(info_path):
            try:
                with open(info_path, "r", encoding="utf-8") as f:
                    depth_info = json.load(f)
            except Exception:
                depth_info = {}
        else:
            depth_info = {}

        depth_info.setdefault("fbx_file", fbx_path)
        depth_info.setdefault("frame_mode", Frame_Mode)
        depth_info.setdefault("num_frames_requested", Num_Frames)
        depth_info.setdefault("output_width", Output_Width)
        depth_info.setdefault("output_height", Output_Height)
        depth_info.setdefault("zoom_factor", Zoom_Factor)
        depth_info.setdefault("view_mode", View_Mode)
        depth_info.setdefault("inverted", bool(Invert_Depth))

        return (depth_tensor, json.dumps(depth_info))
