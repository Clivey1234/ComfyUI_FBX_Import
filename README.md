# FBX Animation Import for Video
Convert FBX animations into Controlnet Openpose images
---

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
Ensure Blender is installed at a path similar to: "C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"
It wont work with earlier version, but untested with later versions

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


