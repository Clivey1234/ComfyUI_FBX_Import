.

🕺 FBX Pose Blender BODY25 Match — ComfyUI Node

Convert FBX Animations Into Stable BODY-25 Pose Images Aligned To Any Reference Stickman


(Add your own banner here)

⭐ Features
✔ Converts any FBX animation into a sequence of BODY-25 / OpenPose style stickman frames
✔ Aligns the animation to any reference OpenPose/DWPose image
✔ Stable global scaling (no zoom jitter)
✔ Upper-body / full-body detection & cropping
✔ Auto face-camera yaw alignment
✔ Supports root motion or in-place mode
✔ Optional Perspective projection mode
✔ Automatic padding when fewer frames exist than requested
✔ Designed for WAN2.2, AnimateDiff, Reactors, T2I-Adapters, and all pose-guided pipelines
📦 Requirements
Dependency	Version	Required?	Notes
Blender	3.6+	✔ Yes	Runs fbx_pose_extract.py via CLI
ComfyUI	Latest	✔ Yes	Node integrates into the custom_nodes folder
Python 3.10–3.11	ComfyUI’s environment	✔ Yes	No external pip installs needed
FBX file	Any	Required at runtime	Animation is extracted per-frame
NVIDIA GPU	Recommended	Optional	Only required for downstream AI workflows

Blender 3.6 is mandatory
Older versions may not have compatible FBX import/export APIs.

Download Blender 3.6 LTS:
https://www.blender.org/download/lts/3-6/

📥 Installation
1. Install/Update Blender

Download & install Blender 3.6+.

Ensure the path in the node matches your installation, such as:

C:\Program Files\Blender Foundation\Blender 3.6\blender.exe

2. Add The Node To ComfyUI

Place the folder:

fbx_pose_body25_match/


into:

ComfyUI/custom_nodes/


Your folder should contain:

__init__.py
fbx_pose_extract.py
fbx_pose_helpers_body25.py
fbx_pose_helpers_body25_match.py
fbx_pose_node_body25_match.py

3. Restart ComfyUI

The node will appear under:

Animation → FBX

🎥 How It Works (Technical Overview)
Step 1 — Blender extracts animation frames

A bundled Python script (fbx_pose_extract.py) is executed via Blender.
It samples your FBX animation based on either:

Spread across whole animation

Explicit frame range selection

It outputs:

joint_data.json


containing 3D joint coordinates per frame.

Step 2 — Node converts 3D → 2D (BODY-25)

Internally, we:

Apply yaw rotation (Auto Face Camera mode)

Apply world→view projection

Apply orthographic or perspective scaling

Stabilize the entire animation using whole-animation bounding boxes

Step 3 — Optional Reference Pose Matching

If you input a reference stickman (OpenPose/DWPose image):

Non-black pixels → define bounding box

Your FBX pose frames are globally scaled, centered, and aligned

If reference is upper-body → legs are removed & cropped

Step 4 — Pose drawing

The node draws the BODY-25 skeleton with:

Custom line thickness

Custom joint size

OpenPose or ControlNet color schemes

Optional face dots / full FACE-70 overlay

Output as an image tensor

🧭 Node Parameters (Every Button Explained)

Below is a complete, user-friendly explanation of every control.

🔧 Input Settings
Blender_Executable

Path to Blender 3.6+.
Used to run the extractor script in headless mode.

FBX_File

Path to your FBX animation.

🎞 Frame Extraction
Frame_Mode

Choose how to select frames:

Frame_Spread_TotalAnim

Divides the FBX animation evenly into Num_Frames samples.

Frame_Range

Allows manual control using:

Start_Frame

End_Frame

Frame_Step

Num_Frames

How many images to generate.

If the animation has fewer frames than requested, the last frame is repeated until the count matches.

Start_Frame / End_Frame / Frame_Step

Used only with Frame_Range.

🖼 Output
Output_Width / Output_Height

Resolution of the pose images.

🎥 Camera & Projection
Camera_View

Choose projection angle:

Front

Back

Left Side

Right Side

Top

Auto (Face Camera) → auto-detects and rotates the body to face the camera

Projection_Mode
Orthographic (Stable) (default)

No depth distortion.
Perfect for ControlNet/WAN.

Perspective (Experimental)

Simulates depth scaling when root motion is enabled.

🎨 Appearance Options
Color_Mode

White

OpenPose-style colors

ControlNet Colors

Face_Mode

Off

Dots Only (BODY-25 face keypoints)

Full Face (FACE-70 expanded face mesh)

Joint_Size

Radius of joint circles.

Line_Thickness

Width of bone lines.

📏 Scaling & Motion Behaviour
Zoom_Factor

Global scale multiplier.

Inplace

True → Character is locked in place (removes root motion)

False → Uses full root motion + global bounding box stabilization

🎯 Reference Pose Matching
Alignment_Mode

Choose how to match to a reference pose image:

Off

Match Full Body

Upper Body (Head-Hips)

Auto (Full/Partial) → detects whether the reference is upper-body only

Ref_Pose_Image

Input any OpenPose/DWPose stickman (e.g. from WAN2.2):

Defines expected bounding box

Your FBX pose is scaled + centered to match

Optional leg removal (if upper-body)

📤 Outputs
Pose_Images

The generated 2D pose frames as a Comfy image tensor.

Frame_Info

A JSON string describing:

FBX file

Frame sampling

camera view

projection mode

scaling

alignment decision (full/upper)

skeleton style

Use this for debugging or automations.

🌈 Example Workflows
1. FBX → BODY-25 → WAN2.2 Pose Condition
Load FBX → FBX_BODY25_MATCH → WAN2.2 → Video Generation

2. Match FBX Animation to Real Human Pose
YourPose.png → FBX_BODY25_MATCH → Image/Video Generator

3. Stabilize Jittery Mocap Before Feeding to AI
FBX Mocap → FBX_BODY25_MATCH (InPlace ON) → ControlNet Pose

🧪 Troubleshooting
"Blender executable not found"

Make sure your path is correct and has no quotes:

C:\Program Files\Blender Foundation\Blender 3.6\blender.exe

"joint_data.json not produced"

Check:

Blender version ≥ 3.6

FBX loads correctly in Blender

Your file path has no non-ASCII characters

Pose appears too small/large

Increase or decrease Zoom_Factor.

Upper-body mode still shows legs

Ensure Alignment_Mode = Upper Body (Head-Hips)
or the reference image itself is upper-body.

🧱 Folder Structure
📂 fbx_pose_body25_match
 ├── __init__.py
 ├── fbx_pose_helpers_body25.py
 ├── fbx_pose_helpers_body25_match.py
 ├── fbx_pose_node_body25_match.py
 └── fbx_pose_extract.py   ← Runs inside Blender

🤝 Contributing

Pull requests are welcome!
Ideas especially appreciated:

Better face mapping

Improved sideways face logic

More skeleton types (BODY70, SMPL, Mixamo)

📄 License

MIT License — free to use commercially & modify.

🚀 Want help writing a banner image or project logo?

I can generate one styled to match your node’s visual identity.

Want auto-generated GIF examples?
I can produce those too.

Just ask!
