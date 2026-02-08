# Unity Avatar Integration Guide

This guide explains how to export avatars from Unity and use them in the wedding chapel 3D scene.

## Unity Setup

### 1. Export Avatars as GLTF/GLB

Unity doesn't natively export GLTF, so you'll need one of these options:

**Option A: Use GLTF Exporter Package (Recommended)**
1. Install the [Unity GLTF Exporter](https://github.com/KhronosGroup/UnityGLTF) package
2. In Unity, select your avatar GameObject
3. Go to `Tools > Export > GLTF`
4. Export as `.glb` (binary) or `.gltf` (text + separate files)
5. Save to your project's static files directory

**Option B: Use Third-Party Tools**
- [Blender](https://www.blender.org/) - Import FBX from Unity, export as GLTF
- [glTF Exporter for Unity](https://assetstore.unity.com/packages/tools/utilities/gltf-exporter-132884) (Asset Store)
- Online converters (FBX → GLTF)

### 2. Avatar Requirements

For best results in the chapel scene:
- **Scale**: Unity units should match Three.js scale (1 unit ≈ 1 meter)
- **Height**: Avatars should be ~1.8 units tall (human scale)
- **Format**: GLB (binary) is preferred for web (single file)
- **Textures**: Embedded in GLB or as separate files with correct paths
- **Animations**: Optional - can include idle animations

### 3. File Organization

Organize your Unity avatars:

```
celebration/static/celebration/avatars/
├── unity/
│   ├── guest-1.glb
│   ├── guest-2.glb
│   ├── bride.glb
│   └── groom.glb
```

## Integration Steps

### 1. Store Avatar URLs in Database

Add a field to your RSVP or Guest model:

```python
# In celebration/models.py
unity_avatar_url = models.URLField(blank=True, null=True)
# Or store local path:
unity_avatar_path = models.CharField(max_length=255, blank=True)
```

### 2. Map Guests to Avatar Files

Create a mapping system:

```python
# In celebration/utils.py or a new file
UNITY_AVATAR_MAP = {
    "Mr. and Mrs. John Doe": "/static/celebration/avatars/unity/couple-1.glb",
    "Jane Smith": "/static/celebration/avatars/unity/guest-1.glb",
    # ... etc
}
```

Or store in database per guest/RSVP.

### 3. Update Seating Chart

Include Unity avatar URLs in seating data:

```python
# In celebration/utils.py - build_seating_chart()
seating_plan.append({
    "row": row_label,
    "seat_number": seat_number,
    "name": name,
    "position": position,
    "unity_avatar_url": get_unity_avatar_url(response.guest),  # Add this
    # ... other fields
})
```

### 4. Load in Chapel Scene

Update `frontend/chapel/main.js`:

```javascript
import { loadAllUnityAvatars } from "./unityAvatars.js";

// In initializeScene(), after building scene:
const avatarUrlMap = {};
seating.forEach(seat => {
    if (seat.unity_avatar_url) {
        avatarUrlMap[seat.name] = seat.unity_avatar_url;
    }
});

// Load Unity avatars instead of 2D
if (Object.keys(avatarUrlMap).length > 0) {
    await loadAllUnityAvatars(scene, seating, avatarUrlMap, {
        scale: 0.8,
        showNameLabel: true, // Optional
    });
} else {
    // Fallback to 2D avatars
    render2DAvatars(container, seating, camera, renderer);
}
```

## Unity Export Settings

### Recommended GLTF Export Settings:

- **Format**: GLB (binary, single file)
- **Scale Factor**: 1.0 (or adjust in Three.js)
- **Include Animations**: Yes (if you have idle animations)
- **Embed Textures**: Yes (keeps everything in one file)
- **Export Materials**: Yes
- **Export Lights**: No (we use Three.js lighting)

### Avatar Preparation in Unity:

1. **Rigging**: Use Humanoid rig if possible (better compatibility)
2. **Materials**: Use Standard or URP materials (will convert to PBR)
3. **Textures**: 
   - Diffuse/Albedo map
   - Normal map (optional but recommended)
   - Roughness/Metallic maps (optional)
4. **LOD**: Not needed for web (keep full quality)

## Example Workflow

1. **Create/Import Avatar in Unity**
   - Use Unity Character Creator, Asset Store, or custom model
   - Position at origin (0, 0, 0)
   - Scale appropriately

2. **Export**
   - Select avatar GameObject
   - Export as GLB
   - Save to `celebration/static/celebration/avatars/unity/`

3. **Add to Database**
   - Map guest name to avatar file
   - Store in database or config

4. **Test in Chapel**
   - Refresh chapel page
   - Avatar should load and appear in correct seat

## Tips

- **Performance**: GLB files should be < 2MB per avatar for web
- **Caching**: Browser will cache GLB files after first load
- **Fallback**: Keep 2D avatar system as backup
- **Testing**: Test with a few avatars first before exporting all
- **Variety**: Export multiple variations for different guests

## Troubleshooting

- **Avatar too big/small**: Adjust `scale` parameter in `loadUnityAvatar()`
- **Wrong rotation**: Adjust `rotationY` parameter
- **Missing textures**: Check that textures are embedded or paths are correct
- **CORS errors**: Serve GLB files from same domain or configure CORS
- **Loading slow**: Optimize GLB file size, use compression
