import json

class FBX_CameraDirector:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "Num_Frames_Default": ("INT", {"default": 81, "min": 1, "max": 999}),
                "Rotation": (
                    "STRING",
                    {
                        "default": (
                            "# Rotation keys (frame, value) - Leave this line here, it will be ignored\n"
                            "0, 0.0\n"
                            "80, 0.0\n"
                        ),
                        "multiline": True,
                    },
                ),
                "Zoom": (
                    "STRING",
                    {
                        "default": (
                            "# Zoom keys (frame, value)- Leave this line here, it will be ignored\n"
                            "0, 1.0\n"
                            "80, 1.0\n"
                        ),
                        "multiline": True,
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("Cam_Out", "Debug_Out",)
    FUNCTION = "build_profile"
    CATEGORY = "Animation/FBX_Clivey"

    def _parse_keys(self, text, num_frames, value_clamp=None):
        """Parse a multiline string of "frame, value" pairs.

        Returns:
            keys: list[(frame_int, value_float)]
            has_negative: True if any user frame < 0
            has_overflow: True if any user frame > num_frames-1
            has_order_issue: True if user frames are not in non-decreasing order
        """
        keys = []
        frames_raw = []
        has_negative = False
        has_overflow = False

        if not text:
            return [], has_negative, has_overflow, False

        max_user_frame = num_frames - 1

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            # Ignore comment lines (used for inline instructions)
            if line.startswith("#"):
                continue

            if "," in line:
                parts = line.split(",")
            elif ":" in line:
                parts = line.split(":")
            else:
                continue

            if len(parts) < 2:
                continue

            try:
                f_raw = int(parts[0].strip())
                v = float(parts[1].strip())
            except Exception:
                continue

            frames_raw.append(f_raw)

            # Check frame issues BEFORE clamping
            if f_raw < 0:
                has_negative = True
            if f_raw > max_user_frame:
                has_overflow = True

            # Clamp frame into usable index range [0, num_frames-1]
            if f_raw < 0:
                f = 0
            elif f_raw > max_user_frame:
                f = max_user_frame
            else:
                f = f_raw

            # Clamp value if needed
            if value_clamp is not None:
                lo, hi = value_clamp
                if v < lo:
                    v = lo
                if v > hi:
                    v = hi

            keys.append((f, v))

        # Determine order issue from raw user-entered frames
        has_order_issue = False
        if len(frames_raw) > 1:
            prev = frames_raw[0]
            for fr in frames_raw[1:]:
                if fr < prev:
                    has_order_issue = True
                    break
                prev = fr

        if not keys:
            return [], has_negative, has_overflow, has_order_issue

        # Sort and merge keys by clamped frame index
        keys.sort(key=lambda x: x[0])
        merged = []
        for f, v in keys:
            if merged and merged[-1][0] == f:
                merged[-1] = (f, v)
            else:
                merged.append((f, v))

        return merged, has_negative, has_overflow, has_order_issue

    def _build_curve(self, num_frames, keys, default):
        vals = [default] * num_frames
        if not keys:
            return vals
        if len(keys) == 1:
            return [keys[0][1]] * num_frames

        for i in range(num_frames):
            if i <= keys[0][0]:
                vals[i] = keys[0][1]
                continue
            if i >= keys[-1][0]:
                vals[i] = keys[-1][1]
                continue
            for idx in range(len(keys) - 1):
                f0, v0 = keys[idx]
                f1, v1 = keys[idx + 1]
                if f0 <= i <= f1:
                    t = (i - f0) / float(f1 - f0) if f1 != f0 else 0.0
                    vals[i] = v0 + (v1 - v0) * t
                    break
        return vals

    def build_profile(self, Num_Frames_Default, Rotation, Zoom):
        num_frames = Num_Frames_Default
        if num_frames < 1:
            num_frames = 1

        # Parse keys and track issues
        rot_keys, rot_neg, rot_over, rot_order = self._parse_keys(
            Rotation, num_frames, value_clamp=(-85.0, 85.0)
        )
        zoom_keys, zoom_neg, zoom_over, zoom_order = self._parse_keys(
            Zoom, num_frames, value_clamp=(0.1, 4.0)
        )

        has_negative = rot_neg or zoom_neg
        has_overflow = rot_over or zoom_over
        has_order_issue = rot_order or zoom_order

        invalid = has_negative or has_overflow or has_order_issue

        if invalid:
            # Default curves so nothing downstream breaks
            rot_curve = [0.0] * num_frames
            zoom_curve = [1.0] * num_frames

            if has_negative:
                debug_msg = "Data construct has an issue, cannot have negative frame numbers"
            elif has_overflow:
                max_user_frame = num_frames - 1
                debug_msg = (
                    "Data construct has an issue, check your frame numbers. "
                    f"The maximum frame you can enter is {max_user_frame}"
                )
            elif has_order_issue:
                debug_msg = "Data construct has an issue, frame numbers not in a sequential order"
            else:
                debug_msg = "Data construct has an unspecified issue"
        else:
            rot_curve = self._build_curve(num_frames, rot_keys, 0.0)
            zoom_curve = self._build_curve(num_frames, zoom_keys, 1.0)
            debug_msg = "Data construct is fine"

        rot_curve = [round(v, 2) for v in rot_curve]
        zoom_curve = [round(v, 2) for v in zoom_curve]

        profile = {
            "num_frames": num_frames,
            "rotation": rot_curve,
            "zoom": zoom_curve,
        }

        return (json.dumps(profile), debug_msg)
