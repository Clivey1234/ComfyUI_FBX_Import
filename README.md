# FBX Pose Blender BODY25 Match — ComfyUI Node  
Convert FBX animations into stable BODY-25 pose images aligned to any reference stickman.

---

## ⭐ Features

- Converts any **FBX animation** into a sequence of **BODY-25/OpenPose** pose frames  
- Aligns animation to a **reference OpenPose/DWPose image**  
- Stable **global scaling** (no zoom jitter)  
- Supports **upper-body** or **full-body** matching  
- Automatic **face-camera** orientation  
- Optional **perspective projection mode**  
- Handles **root motion** or **in-place** animation  
- Automatic padding when fewer frames exist than requested  
- Designed for **WAN2.2**, **AnimateDiff**, **Reactor**, **ControlNet**, **T2I Adapters**, etc.

---

## 📦 Requirements

| Dependency | Version | Required | Notes |
|-----------|----------|----------|-------|
| **Blender** | **3.6+** | ✔ | Must be installed for FBX extraction |
| **ComfyUI** | Latest | ✔ | Node integrates into `custom_nodes` |
| **Python** | 3.10–3.11 | ✔ | Use ComfyUI’s environment |
| **FBX File** | Any animated FBX | ✔ | Must contain armature + animation |
| **GPU** | Optional | – | Only required for downstream AI generation |

Download Blender 3.6 LTS:  
https://www.blender.org/download/lts/3-6/

---

## 📥 Installation

### 1. Install Blender 3.6+
Ensure Blender is installed at a path similar to:


---

## 🎥 How It Works

### Step 1 — Animation Extraction  
A headless Blender instance runs `fbx_pose_extract.py`, which:

- Loads your FBX  
- Samples frames from the animation  
- Outputs `joint_data.json` with 3D joint positions per frame

### Step 2 — 3D → 2D Projection  
The node converts FBX joints into a BODY-25 stickman:

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

- OpenPose / ControlNet colors  
- Adjustable line/joint sizes  
- Optional FACE-70 pairing

---

## 🧭 Node Parameters (Every Setting Explained)

### 🔧 FBX Input  
- **Blender_Executable** — path to Blender 3.6+  
- **FBX_File** — path to your animated FBX  

### 🎞 Frame Extraction  
- **Frame_Mode**  
  - `Frame_Spread_TotalAnim` (even distribution)  
  - `Frame_Range` (manual range)  
- **Num_Frames** — total output frames  
- **Start_Frame / End_Frame / Frame_Step** — used in range mode  
- If fewer frames exist → last frame is padded  

### 🖼 Output Settings  
- **Output_Width / Output_Height** — resolution of output pose images  

### 🎥 Camera & Projection  
- **Camera_View**  
  - Front / Back / Left Side / Right Side / Top / Auto  
- **Projection_Mode**  
  - `Orthographic (Stable)`  
  - `Perspective (Experimental)`  

### 🎨 Appearance  
- **Color_Mode**  
  - White / OpenPose / ControlNet Colors  
- **Face_Mode**  
  - Off / BODY-25 dots / FACE-70 full  
- **Joint_Size** — radius of circles  
- **Line_Thickness** — bone line width  

### 📏 Scaling & Motion  
- **Zoom_Factor** — global scale of pose  
- **Inplace**  
  - ON → remove root motion  
  - OFF → preserve root motion  

### 🎯 Reference Alignment  
- **Alignment_Mode**  
  - Off  
  - Match Full Body  
  - Upper Body (Head-Hips)  
  - Auto (Full/Partial)  
- **Ref_Pose_Image** — optional stickman image input  

---

## 📤 Outputs

### **Pose_Images**
A ComfyUI tensor containing the entire sequence of BODY-25 pose frames.

### **Frame_Info**
A JSON string including:

- FBX file  
- Frame extraction settings  
- Camera view  
- Alignment mode  
- Projection mode  
- Final scaling/centering information  

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
