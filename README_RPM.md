# Ready Player Me Integration Guide

This guide explains how to set up Ready Player Me 3D avatars for the wedding chapel.

## Prerequisites

1. **Register at Ready Player Me**
   - Go to https://readyplayer.me/developers
   - Create an account
   - Create a new application
   - Copy your **Application ID**

2. **Set Environment Variable**
   ```bash
   export READY_PLAYER_ME_APPLICATION_ID="your-application-id-here"
   ```
   
   Or add to your Django settings:
   ```python
   READY_PLAYER_ME_APPLICATION_ID = "your-application-id-here"
   ```

## How It Works

### Current Implementation (2D Avatars)
- Uses DiceBear API for 2D avatar images
- Avatars are displayed as circular images positioned in pews
- Works immediately without additional setup

### Ready Player Me Implementation (3D Avatars)
- Uses Ready Player Me API for 3D GLTF avatar models
- Avatars are full 3D models that can be viewed from any angle
- Requires Ready Player Me account and application setup

## Integration Steps

### 1. Database Setup

Add fields to store Ready Player Me data (optional migration):

```python
# In celebration/models.py - add to RSVP or Guest model:
rpm_user_id = models.CharField(max_length=255, blank=True, null=True)
rpm_token = models.TextField(blank=True, null=True)  # Store encrypted
rpm_avatar_url = models.URLField(blank=True, null=True)
```

### 2. Create Ready Player Me Users

When a guest RSVPs, create an anonymous Ready Player Me user:

```python
from celebration.rpm_utils import create_anonymous_rpm_user

# In your RSVP view:
rpm_data = create_anonymous_rpm_user()
if rpm_data:
    rsvp.rpm_user_id = rpm_data["user_id"]
    rsvp.rpm_token = rpm_data["token"]  # Store securely!
    rsvp.save()
```

### 3. Avatar Creation

Ready Player Me avatars are typically created through their web-based avatar builder. You have two options:

**Option A: Direct users to Ready Player Me builder**
- Redirect users to Ready Player Me's avatar builder
- They customize their avatar
- The avatar URL is returned and stored

**Option B: Programmatic creation (if supported)**
- Use Ready Player Me's REST API to create avatars
- Map your avatar customization options to Ready Player Me parameters

### 4. Load 3D Avatars in Chapel

Update `frontend/chapel/main.js` to use Ready Player Me avatars:

```javascript
import { loadAllRPMAvatars } from "./rpmAvatars.js";

// In initializeScene():
if (USE_RPM_AVATARS) {
    const rpmUserMap = {}; // Build from seating data
    seating.forEach(seat => {
        if (seat.rpm_user_id && seat.rpm_token) {
            rpmUserMap[seat.name] = {
                userId: seat.rpm_user_id,
                token: seat.rpm_token
            };
        }
    });
    
    await loadAllRPMAvatars(scene, seating, rpmUserMap);
} else {
    // Use 2D avatars (current implementation)
    render2DAvatars(container, seating, camera, renderer);
}
```

## Important Notes

1. **Token Security**: Ready Player Me tokens should be stored securely (encrypted) in your database
2. **API Limits**: Check Ready Player Me's rate limits and pricing
3. **Avatar URLs**: GLTF model URLs from Ready Player Me are typically permanent
4. **Fallback**: Keep 2D avatar system as fallback if Ready Player Me fails

## Testing

1. Set your `READY_PLAYER_ME_APPLICATION_ID`
2. Create a test RSVP
3. Check that Ready Player Me user is created
4. Verify avatar GLTF URL is retrieved
5. Test loading in the chapel scene

## Troubleshooting

- **"APPLICATION_ID not set"**: Make sure environment variable is set
- **"Failed to create user"**: Check your application ID is correct
- **"No avatar URL"**: User may not have created an avatar yet
- **GLTF loading errors**: Check CORS settings and model URL validity
