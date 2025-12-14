
import os
import json
import subprocess


class FBX_Info:
    """
    FBX Info node - extracts FBX animation info via Blender.

    Inputs:
        fbx_path          (STRING) - full path to FBX file
        blender_path      (STRING) - path to Blender executable
        video_fps_target  (DROPDOWN) - "16", "24", "30"

    Outputs:
        fps                  (FLOAT)
        frame_count          (INT)
        skinned              (BOOLEAN)
        fbx_out              (STRING)  - absolute FBX path
        blender_out          (STRING)  - absolute Blender path
        text_debug           (STRING)  - multiline summary
        suggested_frame_step (INT)     - fps / Video FPS Target (rounded, min 1)
        root_motion          (BOOLEAN) - True if root motion, False if in-place
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "fbx_path": (
                    "STRING",
                    {"multiline": False, "default": ""},
                ),
                "blender_path": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
                    },
                ),
                # Proper dropdown: type is a list of choices
                "video_fps_target": (
                    ["16", "24", "30"],
                    {"default": "16"},
                ),
            }
        }

    CATEGORY = "Animation/FBX_Clivey"

    # NEW: extra BOOLEAN at the end for root_motion
    RETURN_TYPES = (
        "FLOAT",
        "INT",
        "BOOLEAN",
        "STRING",
        "STRING",
        "STRING",
        "INT",
        "BOOLEAN",
    )
    RETURN_NAMES = (
        "fps",
        "frame_count",
        "skinned",
        "fbx_out",
        "blender_out",
        "text_debug",
        "suggested_frame_step",
        "root_motion",
    )

    FUNCTION = "analyze_fbx"

    def sanitize_exporter(self, raw_exporter):
        """
        Normalises the exporter string by looking for known applications.
        Returns a clean single-word/short label or 'Unknown'.
        """
        if not raw_exporter:
            return "Unknown"

        raw = raw_exporter.lower()

        # Order matters – first match wins
        checks = [
            "blender",
            "maya",
            "3dsmax",
            "mixamo",
            "unreal",              # you changed this from "unreal engine"
            "reallusion",
            "iclone",
            "cc4",
            "character creator",
            "daz",
            "cascadeur",
            "autodesk",
        ]

        for key in checks:
            if key in raw:
                # Return nicely formatted label
                if key == "3dsmax":
                    return "3dsMax"
                if key == "cc4":
                    return "CC4"
                if key == "iclone":
                    return "iClone"
                if key == "character creator":
                    return "Character Creator"
                # Default: title case
                return key.title()

        return "Unknown"

    def analyze_fbx(self, fbx_path, blender_path, video_fps_target):
        raw_fbx = fbx_path.strip()
        raw_blender = blender_path.strip()

        # video_fps_target is now one of "16", "24", "30"
        try:
            target_fps = float(video_fps_target)
            if target_fps <= 0:
                target_fps = 16.0
        except Exception:
            target_fps = 16.0

        # Convert input paths to absolute
        abs_fbx = os.path.abspath(raw_fbx) if raw_fbx else ""
        abs_blender = os.path.abspath(raw_blender) if raw_blender else ""

        # Default suggested step
        suggested_step = 1

        def basic_debug():
            return (
                "FPS=0.0\n"
                "Frame Count=0\n"
                "Skinned=False\n"
                "FBX Version=Unknown\n"
                "Exported By=Unknown\n"
                "MotionType=Unknown"
            )

        # Path validation
        if not abs_fbx or not os.path.isfile(abs_fbx):
            print(f"[FBX_Info_Blender] Invalid FBX path: {abs_fbx}")
            debug = basic_debug()
            return (0.0, 0, False, abs_fbx, abs_blender, debug, suggested_step, False)

        script_path = os.path.join(os.path.dirname(__file__), "fbx_info_extract.py")
        if not os.path.isfile(script_path):
            print(f"[FBX_Info_Blender] Missing helper script: {script_path}")
            debug = basic_debug()
            return (0.0, 0, False, abs_fbx, abs_blender, debug, suggested_step, False)

        if not abs_blender:
            abs_blender = "blender"

        cmd = [
            abs_blender,
            "-b",
            "-noaudio",
            "--python", script_path,
            "--",
            abs_fbx,
        ]

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
        except Exception as e:
            print(f"[FBX_Info_Blender] Failed to run Blender: {e}")
            debug = basic_debug()
            return (0.0, 0, False, abs_fbx, abs_blender, debug, suggested_step, False)

        if result.stderr:
            print("[FBX_Info_Blender] Blender stderr:\n", result.stderr)

        stdout = result.stdout.strip()
        if not stdout:
            print("[FBX_Info_Blender] No output from Blender helper")
            debug = basic_debug()
            return (0.0, 0, False, abs_fbx, abs_blender, debug, suggested_step, False)

        # Find JSON line
        data = None
        for line in reversed(stdout.splitlines()):
            try:
                data = json.loads(line.strip())
                break
            except Exception:
                continue

        if data is None:
            print("[FBX_Info_Blender] Failed to decode JSON.")
            debug = basic_debug()
            return (0.0, 0, False, abs_fbx, abs_blender, debug, suggested_step, False)

        # Extract base values
        fps = float(data.get("fps", 0.0))
        frame_count = int(data.get("frame_count", 0))
        skinned = bool(data.get("skinned", False))

        # New fields from helper
        fbx_version = data.get("fbx_version") or "Unknown"
        raw_exporter = data.get("exporter") or ""
        exporter = self.sanitize_exporter(raw_exporter)

        # Root motion flag from helper
        root_motion_flag = bool(data.get("root_motion", False))

        # Suggested frame step: fps / target_fps, rounded, minimum 1
        if fps > 0 and target_fps > 0:
            suggested_step = max(1, int(round(fps / target_fps)))
        else:
            suggested_step = 1

        # Motion type label for debug
        if frame_count <= 0:
            motion_label = "Unknown"
        else:
            motion_label = "RootMotion" if root_motion_flag else "InPlace"

        # Build debug string including version, exporter, and motion type
        text_debug = (
            f"FPS={fps}\n"
            f"Frame Count={frame_count}\n"
            f"Skinned={skinned}\n"
            f"FBX Version={fbx_version}\n"
            f"Exported By={exporter}\n"
            f"MotionType={motion_label}"
        )

        return (
            fps,
            frame_count,
            skinned,
            abs_fbx,
            abs_blender,
            text_debug,
            suggested_step,
            root_motion_flag,
        )
