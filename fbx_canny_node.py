import os
import json
import uuid
import subprocess
import tempfile

import numpy as np
import torch
from PIL import Image
import cv2


class FBX_Canny_Blender:
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
                    ["Sample_N_Frames", "Frame_Range"],
                    {"default": "Sample_N_Frames"},
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
                "Canny_Low": ("INT", {"default": 100, "min": 0, "max": 1000}),
                "Canny_High": ("INT", {"default": 200, "min": 0, "max": 2000}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("Canny_Images", "Canny_Info",)
    FUNCTION = "generate_canny_images"
    CATEGORY = "Animation/FBX_Clivey"

    def _get_script_path(self):
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "fbx_canny_extract.py")
        if not os.path.isfile(path):
            raise RuntimeError(
                f"FBX Canny (Blender Edges): fbx_canny_extract.py not found:\n{path}"
            )
        return path

    def _blank_image_stack(self, frames, width, height):
        if frames <= 0:
            frames = 1
        arr = np.zeros((frames, height, width, 3), dtype=np.float32)
        return torch.from_numpy(arr)

    def _load_canny_stack(self, rgb_dir, width, height, low, high):
        if not os.path.isdir(rgb_dir):
            return None

        files = sorted(
            f for f in os.listdir(rgb_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        )
        if not files:
            return None

        images = []
        for fname in files:
            path = os.path.join(rgb_dir, fname)
            try:
                img = Image.open(path).convert("L")
            except Exception:
                continue

            arr = np.array(img, dtype=np.uint8)
            edges = cv2.Canny(arr, int(low), int(high))

            edges = edges.astype(np.float32) / 255.0

            if edges.shape[1] != width or edges.shape[0] != height:
                edges = cv2.resize(edges, (width, height), interpolation=cv2.INTER_LINEAR)

            edges_rgb = np.stack([edges, edges, edges], axis=-1)
            images.append(edges_rgb)

        if not images:
            return None

        stack = np.stack(images, axis=0)
        return torch.from_numpy(stack.astype(np.float32))

    def generate_canny_images(
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
        Canny_Low,
        Canny_High,
    ):
        blender_exe = Blender_Executable.strip().strip('"')
        if not blender_exe or not os.path.isfile(blender_exe):
            raise RuntimeError(
                f"FBX Canny (Blender Edges): Blender executable not found:\n{blender_exe}"
            )

        fbx_path = FBX_File.strip().strip('"')
        if not fbx_path or not os.path.isfile(fbx_path):
            raise RuntimeError(
                f"FBX Canny (Blender Edges): FBX file not found:\n{fbx_path}"
            )

        script_path = self._get_script_path()

        if Frame_Mode == "Sample_N_Frames":
            if End_Frame <= Start_Frame:
                End_Frame = Start_Frame + max(Num_Frames - 1, 0)
        else:
            if End_Frame < Start_Frame:
                End_Frame = Start_Frame

        out_dir = os.path.join(
            tempfile.gettempdir(),
            f"fbx_canny_blender_{uuid.uuid4().hex}",
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
            "--zoom_factor", str(float(Zoom_Factor)),
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
                "FBX Canny (Blender Edges): Blender canny extractor failed.\n"
                f"Command: {' '.join(args)}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}\n"
            )

        rgb_dir = os.path.join(out_dir, "rgb")
        canny_tensor = self._load_canny_stack(
            rgb_dir, Output_Width, Output_Height, Canny_Low, Canny_High
        )
        if canny_tensor is None:
            canny_tensor = self._blank_image_stack(
                Num_Frames, Output_Width, Output_Height
            )

        info_path = os.path.join(out_dir, "canny_info.json")
        if os.path.isfile(info_path):
            try:
                with open(info_path, "r", encoding="utf-8") as f:
                    canny_info = json.load(f)
            except Exception:
                canny_info = {}
        else:
            canny_info = {}

        canny_info.setdefault("fbx_file", fbx_path)
        canny_info.setdefault("frame_mode", Frame_Mode)
        canny_info.setdefault("num_frames_requested", Num_Frames)
        canny_info.setdefault("output_width", Output_Width)
        canny_info.setdefault("output_height", Output_Height)
        canny_info.setdefault("zoom_factor", Zoom_Factor)
        canny_info.setdefault("view_mode", View_Mode)
        canny_info.setdefault("canny_low", int(Canny_Low))
        canny_info.setdefault("canny_high", int(Canny_High))

        return (canny_tensor, json.dumps(canny_info))
