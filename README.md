# FBX Animation Import for Video
Convert FBX animations into Controlnet Openpose images
---

## ⭐ Why does this exist?
- Because like most, I can never find the right video to copy the motion from
- This opens Comfyui up to use 100,000s of animations to drive AI videos
- If you can animated even with little basic knowledge in Unreal/iclone for example, you can now control every single frame of your movement
- If you cant animate, then just uses the FBXs available, they are everywhere!

## ⭐ Important
- I have a life, so support will be extremely limnited, but please do any fork or code changes you want to.
- Due to lots of issues recently with Comfyui stability, I cannot guarantee this wont break at some point
- This method is far from perfect and suffers from all the same issues as Openpose does
- Still having a little issue with head direction tracking, it works but not the best
- This is just a testing phase. It probably wont work on the cloud due to headless blender requirement
- Untested in Linux, I dont have it, so dont ask, Fork away if you want to recode for Linux
- I steered away from Autodesk SDK due to them changing older SDK versions to remove python support
- My testing machine: Windows 11, Comfyui portable, Blender 3.6, 5070ti 16GB VRAM, i5-14600K, 64GB DDR5

[![Watch the video](https://img.youtube.com/vi/GLFpgOq_m_c/maxresdefault.jpg)](https://youtu.be/GLFpgOq_m_c)

### [Watch this video on YouTube](https://youtu.be/GLFpgOq_m_c)


## ⭐ Features

- Converts **FBX animation** into a sequence of **BODY-25/OpenPose** pose frames  
- Optional **perspective projection mode for Root Motion**  
- Handles **root motion** or **in-place** animation  


## 📦 Requirements

| Dependency | Version | Required | Notes |
|-----------|----------|----------|-------|
| **Blender** | **3.6+** | ✔ | Must be installed for FBX extraction |
| **ComfyUI** | Latest | ✔ | Node integrates into `custom_nodes` |
| **Python** | 3.10–3.11 | ✔ | Use ComfyUI’s environment |
| **FBX File** | supported animated FBX | ✔ | Must contain armature + animation |

Download Blender 3.6 LTS:  
https://www.blender.org/download/lts/3-6/

---

## 📥 Installation

### 1. Install Blender 3.6
- Ensure Blender is installed at a path similar to: "C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"
- It wont work with earlier version, but untested with later versions
- You will never need to open Blender, just install it.
---

## 🎥 How It Works

### Step 1 — Animation Extraction  
A headless Blender instance runs `fbx_pose_extract.py`, which:

- Loads your FBX  
- Samples frames from the animation  
- Outputs `joint_data.json` with 3D joint positions per frame

### Step 2 — 3D → 2D Projection  
The node converts FBX joints into a BODY-25 pose:

- Yaw correction (Auto Face Camera)  
- Orthographic or perspective projection  
- Whole-animation bounding box scaling (prevents zoom jitter)  

### Step 3 — Optional Reference Pose Alignment  
If you supply a stickman image (OpenPose/DWPose):

- Bounding box is extracted from non-black pixels  
- Your FBX animation is scaled + centered to match it  
- If the ref is upper-body → legs are cropped automatically  

### Step 4 — Stickman Drawing  
Finally, the skeleton is drawn into clean 2D frames using:

- OpenPose / ControlNet colours  
- Adjustable line/joint sizes  
- Optional FACE-70 pairing

---

## 🧭 Node Parameters (Settings Explained)

### 🔧 FBX Info  
- **Blender_Executable** — path to Blender 3.6+  
- **FBX_File** — path to your animated FBX  

### 🎞 Frame Extraction  
- **Frame_Mode**  
  - `Frame_Spread_TotalAnim` (even distribution)  
  - `Frame_Range` (manual range)  
- **Num_Frames** — total output frames  
- **Start_Frame / End_Frame / Frame_Step** — used in range mode  
- If fewer frames exist → last frame is padded
- **Projection Mode** - Orthographic for InPlace and Perspective for root
- **colour Mode** - Default to Controlnet colour scheme
- **Alignment Mode** Default to full body matching, but depending on input image and animation, can be set to Upper Body only.
- **Camera_View** - Front / Back / Left Side / Right Side / Top / Auto face
  - Front / Back / Left Side / Right Side / Top / Auto  
- **Zoom_Factor** — Disabled if Camera Node conntected as that node will control zoom
---

✅ Supported FBX Files

The node supports any FBX file that meets the following conditions:

✔ 1. The FBX contains an Armature (Skeleton)

Your FBX must have: A skeleton hierarchy,  Keyframed animation data,  A root bone (hips/root,  Standard humanoid proportions

## 📦 Supported FBX

| Skeleton | Supported | Notes |
|-----------|----------|----------|
| **Mixamo** | Full | Fully tested, auto-detects joints |
| **Unreal Mannequin** | Full | Works via joint-name remapping |
| **Unity Humanoid** | Full | Works as long as names follow expected pattern |
| **Blender Rigify** | Good | Must bake animation before export |
| **Reallusion CC/iClone** | Full | Very reliable — standard naming |


**Iclone exporting Settings:**

<img width="678" height="604" alt="image" src="https://github.com/user-attachments/assets/832962e3-de85-496e-8733-c9cc609c13f4" />


**Camera Director**   (Its more of a Skeleton Director than camera)

I would always advise to disable the Wan22FunControlToVideo until you are happy with the animation, then re-enable it to generate the video.
There are two main controls, rotation and zoom.

**Rotation**
With rotation, if the FBX animation is 'InPlace' the rotation will rotation the OpenPose in an orbital basis where the FBX skeleton is the center of the pivot. so you are rotating on X0 Y0 of the object (assuming the fbx was created properly)
If the FBX animation is a root, the pivot point is offset to the further distance of the animation from X0 Y), which means the slightest change in rotation values will manifest in perceived larger rotation depending on how fat the animation has moved from X0Y0. 
So because the rotation works on degrees, 5 Degrees change can on a root anim where the skeleton is only 5m away from X0 Y0, may result in a small rotation, but if the anim is 30m away from X0Y0, the that same 5 degrees will move the animation alot more than thr 5m one. There is a Pivot.png in the Images folder of this custom node that may explain it better!

**Zoom**

Zoom is just what it says it is. 1.0 is the scale set as the default size in the Apose Image. The size of the person may vary on screen, but no matter their size, they will always be 1.0. A 0.1 increment either negative or positive is essential 10% of the original size, so of you zoom to -0.1, you are effectively shrinking by 90%.

If you want to disable the scale of the ref image then set "Use 1st Image Ref Pose" Node to 'No' (purple color node) and the node will then calculate based on the amnimation scale

Both work by Frame number then a , (comma) then a value

**Contraints**

Rules. There are inbuilt restrictions that will prevent the animation from changing.
1. You cannot have negative frame numbers
2. Frame numbers MUST be sequential
3. The last frame must be the number of frames -1, so on an 81 frame animation, your last frame number you can use is 80.
4. Rotation (top multine) is the value is degrees and go from -60 to 60
5. Zoom works on %, so 0.1 is a 10% change. Remember you are zooming the animation, not the camera.

If you want a more 3D perspective feeling to root motion, use Perspective (Experimental) in the Projection mode.

You can add as many frame changes as you want
e.g for rotation you can do
0, 0
30, 20
50, -20
70, -20
80, 5

What this means is that from frame 0 to 30 it will rotate evenly from 0 to 20 degrees, then from 30 to 50, it will evenly rotate from 20 to -20 degrees (40 degree change). Then from 50 to 70 it wont rotate as the values are the same and then from 70 to 90 it will rotate from -20 to positive 5 degrees

**Defaults:** for best results 
Camera View: Front
Projection Mode: Perspective
Color Mode: ControNet Colors
Face Mode: Full Face
Joint Size: 2
Bone Thick: 1
Zoom Factor: 1  (this is increase you dont connect the camera node, it offers basic control)
Alignment Mode: Match Full Body

Start Frame: The frame number you want to capture from
End Frame: End last frame you want to capture from.

"Frame Range" will calculate the frames between the start frame to the number of frames in the video length, so if you set you Frame Length to 81, it will capture 81 frames from the Start frame. 

However, if you change the Step from 1 to 2, it will capture from 81 frames every 2nd frame, so effectively 0 to 160 step 2.

Frame_Spread_TotalAnim:  This will evenly capture the  frame from Start to End. So I load a 227 frame animation and select Frame_Spread_TotalAnim, is will evenly calculate the frames over that 227 regardless of what you put in Frame_Step..
e.g
"frame_indices": [1, 4, 7, 9, 12, 15, 18, 21, 24, 26, 29, 32, 35, 38, 41, 43, 46, 49, 52, 55, 57, 60, 63, 66, 69, 72, 74, 77, 80, 83, 86, 89, 91, 94, 97, 100, 103, 106, 108, 111, 114, 117, 120, 122, 125, 128, 131, 134, 137, 139, 142, 145, 148, 151, 154, 156, 159, 162, 165, 168, 171, 173, 176, 179, 182, 185, 187, 190, 193, 196, 199, 202, 204, 207, 210, 213, 216, 219, 221, 224, 227]


You have to be conscious of that although it was 81 frames, the large changes in frames will mean it will play back really fast, so make you keep an eye on the total frames in the anim and your Frame_End. If I adjust the Frame_End to 180, you then get this.
[1, 3, 5, 8, 10, 12, 14, 17, 19, 21, 23, 26, 28, 30, 32, 35, 37, 39, 41, 44, 46, 48, 50, 52, 55, 57, 59, 61, 64, 66, 68, 70, 73, 75, 77, 79, 82, 84, 86, 88, 91, 93, 95, 97, 99, 102, 104, 106, 108, 111, 113, 115, 117, 120, 122, 124, 126, 129, 131, 133, 135, 137, 140, 142, 144, 146, 149, 151, 153, 155, 158, 160, 162, 164, 167, 169, 171, 173, 176, 178, 180]

