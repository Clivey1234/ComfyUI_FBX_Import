from .fbx_info_node import FBX_Info
from .fbx_pose_node_body25_match import FBX_Extraction
from .fbx_camera_director import FBX_CameraDirector
from .image_batch_number_overlay import FBX_ImageBatchNumberOverlay
from .fbx_smallest_size import SmallestSize
from .batch_list_resize import BatchListResize
from .fbx_depth_node import FBX_Depth_Blender
from .fbx_canny_node import FBX_Canny_Blender

NODE_CLASS_MAPPINGS = {
    "FBX_Info": FBX_Info,
    "FBX_Extraction": FBX_Extraction, 
    "FBX_CameraDirector": FBX_CameraDirector,
    "FBX_ImageBatchNumberOverlay": FBX_ImageBatchNumberOverlay,
    "FBX_ImageResInfo": SmallestSize,
    "BatchListResize": BatchListResize,
    "FBX_Depth_Blender": FBX_Depth_Blender,
    "FBX_Canny_Blender": FBX_Canny_Blender,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FBX_Info": "FBX Info",
    "FBX_Extraction": "FBX_Extraction",
    "FBX_CameraDirector": "FBX Camera Director",
    "FBX_ImageBatchNumberOverlay": "FBX_Image Batch Number Overlay",
    "FBX_ImageResInfo": "FBX_ImageResInfo",
    "BatchListResize": "BatchListResize",
    "FBX_Depth_Blender": "FBX Depth (Blender Z-Depth)",
    "FBX_Canny_Blender": "FBX Canny (Blender Edges)",
}