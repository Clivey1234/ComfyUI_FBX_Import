# neede a simple way of sticking the frame number on the image for keyframe editing
import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont


class FBX_ImageBatchNumberOverlay:
    """
    Layers (bottom → top):

      OpenPose with Background:
        1. Background image (optional)
        2. Stickman from 'images' with black keyed out
        3. Frame/index number text at bottom-left

      OpenPose only:
        1. Stickman from 'images' on black background
        2. Frame/index number text at bottom-left
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Stickman images on black
                "images": ("IMAGE",),
                "start_index": (
                    "INT",
                    {
                        "default": 1,
                        "min": 0,
                        "max": 999,
                        "step": 1,
                    },
                ),
            },
            "optional": {
                # Optional background layer
                "background": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("IMAGE", "IMAGE")
    RETURN_NAMES = ("OpenPose with Background", "OpenPose only")
    FUNCTION = "apply_numbers"
    CATEGORY = "Animation/FBX_Clivey"

    # Threshold for treating foreground pixels as "black/transparent"
    BLACK_THRESHOLD = 0.05  # 0..1 (approx 13/255)

    def _get_font(self, height: int):
        # Font size scales with image height (fallback to default if TTF not available)
        try:
            size = max(36, height // 10)
            return ImageFont.truetype("arial.ttf", size=size)
        except Exception:
            return ImageFont.load_default()

    def _draw_index(self, pil_img: Image.Image, text: str):
        draw = ImageDraw.Draw(pil_img)
        font = self._get_font(pil_img.height)

        # Measure text size
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except Exception:
            # Fallback for older Pillow versions
            text_w, text_h = draw.textsize(text, font=font)

        # Bottom-left with padding
        x = 46
        y = pil_img.height - text_h - 46

        # Simple outline for readability
        outline_offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dx, dy in outline_offsets:
            draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0))

        # Main text (white)
        draw.text((x, y), text, font=font, fill=(255, 255, 255))

    def _prepare_batch(self, tensor: torch.Tensor, name: str):
        if not isinstance(tensor, torch.Tensor):
            raise TypeError(f"Expected '{name}' to be a torch.Tensor of type IMAGE")

        if tensor.ndim != 4 or tensor.shape[-1] != 3:
            raise ValueError(
                f"Expected IMAGE tensor '{name}' of shape [B, H, W, 3], got {tensor.shape}"
            )

        arr = tensor.detach().cpu().numpy()
        arr = np.clip(arr, 0.0, 1.0).astype(np.float32)
        return arr

    def _broadcast_background(self, fg_np: np.ndarray, bg_np: np.ndarray):
        b_fg, h_fg, w_fg, c_fg = fg_np.shape
        b_bg, h_bg, w_bg, c_bg = bg_np.shape

        if (h_fg, w_fg) != (h_bg, w_bg):
            raise ValueError(
                f"Foreground and background sizes differ: "
                f"FG={h_fg}x{w_fg}, BG={h_bg}x{w_bg}. "
                f"Resize them to match before this node."
            )

        if b_bg == 1 and b_fg > 1:
            # Broadcast single background to whole batch
            bg_np = np.repeat(bg_np, b_fg, axis=0)
        elif b_bg != b_fg:
            raise ValueError(
                f"Batch size mismatch: foreground={b_fg}, background={b_bg}. "
                f"Use either 1 background frame or match the batch size."
            )

        return bg_np

    def apply_numbers(self, images, start_index, background=None):
        """
        images:    stickman on black (IMAGE tensor)
        background: optional background images (IMAGE tensor) or None

        Returns:
          OpenPose with Background  (IMAGE)
          OpenPose only             (IMAGE)
        """

        device = images.device

        # Prepare foreground (stickman) batch 0..1
        fg_np = self._prepare_batch(images, "images")

        # Prepare background (if any)
        if background is not None:
            bg_np = self._prepare_batch(background, "background")
            bg_np = self._broadcast_background(fg_np, bg_np)
        else:
            # If no background: use foreground as base (so behavior is sane)
            bg_np = fg_np.copy()

        # Create mask from foreground: non-black → 1, black → 0
        max_chan = fg_np.max(axis=-1, keepdims=True)  # [B, H, W, 1]
        mask = (max_chan > self.BLACK_THRESHOLD).astype(np.float32)

        # Composite for "with background"
        comp_np = bg_np * (1.0 - mask) + fg_np * mask

        batch, height, width, channels = fg_np.shape

        # Output arrays
        out_with_bg = np.empty_like(comp_np, dtype=np.float32)
        out_only = np.empty_like(fg_np, dtype=np.float32)

        for i in range(batch):
            index_text = str(start_index + i)

            # --- OpenPose with Background ---
            img_with_bg_uint8 = np.clip(comp_np[i] * 255.0, 0, 255).astype(np.uint8)
            pil_with_bg = Image.fromarray(img_with_bg_uint8)
            self._draw_index(pil_with_bg, index_text)
            out_with_bg[i] = np.asarray(pil_with_bg, dtype=np.float32) / 255.0

            # --- OpenPose only (stickman on black) ---
            img_only_uint8 = np.clip(fg_np[i] * 255.0, 0, 255).astype(np.uint8)
            pil_only = Image.fromarray(img_only_uint8)
            self._draw_index(pil_only, index_text)
            out_only[i] = np.asarray(pil_only, dtype=np.float32) / 255.0

        # Back to tensors
        out_with_bg_tensor = torch.from_numpy(out_with_bg).to(device)
        out_only_tensor = torch.from_numpy(out_only).to(device)

        return (out_with_bg_tensor, out_only_tensor)
