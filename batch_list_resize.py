import torch


class BatchListResize:
    """
    BatchListResize

    Slice an image batch using start and end indices.

    - images: IMAGE batch (B, H, W, C)
    - start_index: INT, 0-based index to start from (inclusive)
    - end_index: INT, index to end at (exclusive)
        * If end_index < 0, it means "to the end of the batch"
        * If end_index > batch length, it is clamped to batch length

    Examples (for a batch of length 81):
    - start_index = 0, end_index = -1  → frames [0..80] (all)
    - start_index = 1, end_index = -1  → frames [1..80] (drops frame 0)
    - start_index = 10, end_index = 20 → frames [10..19]
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "start_index": (
                    "INT",
                    {
                        "default": 0,
                        "min": -9999,
                        "max": 9999,
                        "step": 1,
                        "display": "number",
                    },
                ),
                "end_index": (
                    "INT",
                    {
                        "default": -1,
                        "min": -9999,
                        "max": 9999,
                        "step": 1,
                        "display": "number",
                    },
                ),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "batch_resize"
    CATEGORY = "Animation/FBX_Clivey"

    def batch_resize(self, images: torch.Tensor, start_index: int, end_index: int):
        if images is None:
            return (images,)

        if not isinstance(images, torch.Tensor):
            images = torch.stack(images, dim=0)

        batch_len = images.shape[0]
        if batch_len == 0:
            return (images,)

        s = int(start_index)
        e = int(end_index)

        # clamp start
        if s < 0:
            s = 0
        if s > batch_len:
            s = batch_len

        # end < 0 = full batch end
        if e < 0 or e > batch_len:
            e = batch_len

        sliced = images[s:e]

        return (sliced,)
