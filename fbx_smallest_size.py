#too mnay resize nodes out there, none do everything i needed so did this one, not great but it does the job i need it to
class SmallestSize:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "resize_mode": (["None", "By Width", "By Height"], {
                    "default": "None"
                }),
                "target_width": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 8192,
                    "step": 2,
                }),
                "target_height": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 8192,
                    "step": 2,
                }),
            }
        }

    RETURN_TYPES = (
        "INT",   # smallest
        "INT",   # largest
        "INT",   # width
        "INT",   # height
        "INT",   # resized_smallest
        "INT",   # resized_largest
        "INT",   # batch size
        "INT",   # channels
        "FLOAT", # aspect ratio
        "BOOL",  # portrait_Boolean
        "BOOL",  # landscape_Boolean
        "BOOL",  # square_Boolean
        "INT",   # resized_width_Div2
        "INT",   # resized_height_Div2
        "INT",   # resized_width_Div16
        "INT",   # resized_height_Div16
    )

    RETURN_NAMES = (
        "smallest",
        "largest",
        "width",
        "height",
        "resized_smallest",
        "resized_largest",
        "batch",
        "channels",
        "aspect",
        "portrait_Boolean",
        "landscape_Boolean",
        "square_Boolean",
        "resized_width_Div2",
        "resized_height_Div2",
        "resized_width_Div16",
        "resized_height_Div16",
    )

    FUNCTION = "calc"
    CATEGORY = "Animation/FBX_Clivey"

    def calc(self, image, resize_mode, target_width, target_height):
        # image tensor shape: [B, H, W, C]
        b = image.shape[0]
        h = image.shape[1]
        w = image.shape[2]
        c = image.shape[3]

        smallest = min(w, h)
        largest = max(w, h)
        aspect = w / h if h != 0 else 0.0

        portrait = h > w
        landscape = w > h
        square = w == h

        # Defaults (no resizing)
        resized_w = w
        resized_h = h

        # Helper: ensure divisibility
        def make_divisible(value, divisor):
            if value <= 0:
                return 0
            return value - (value % divisor)

        # Resize logic
        if resize_mode == "By Width" and target_width > 0:
            resized_w = target_width
            resized_h = int(round(target_width * h / w))

        elif resize_mode == "By Height" and target_height > 0:
            resized_h = target_height
            resized_w = int(round(target_height * w / h))

        # Raw resized values
        resized_smallest = min(resized_w, resized_h)
        resized_largest = max(resized_w, resized_h)

        # Div2 outputs
        resized_w_div2 = make_divisible(resized_w, 2)
        resized_h_div2 = make_divisible(resized_h, 2)

        # Div16 outputs
        resized_w_div16 = make_divisible(resized_w, 16)
        resized_h_div16 = make_divisible(resized_h, 16)

        return (
            smallest,
            largest,
            w,
            h,
            resized_smallest,
            resized_largest,
            b,
            c,
            aspect,
            portrait,
            landscape,
            square,
            resized_w_div2,
            resized_h_div2,
            resized_w_div16,
            resized_h_div16,
        )
