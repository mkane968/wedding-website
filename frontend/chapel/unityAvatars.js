/**
 * Unity Avatar Loader for Chapel Scene
 * Loads GLTF/GLB avatar models exported from Unity
 */

import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const gltfLoader = new GLTFLoader();

/**
 * Load a Unity avatar GLTF model and add it to the scene
 * @param {THREE.Scene} scene - Three.js scene
 * @param {object} seat - Seat data with position and avatar info
 * @param {string} gltfUrl - URL to the Unity-exported GLTF/GLB file
 * @param {object} options - Optional configuration
 */
export async function loadUnityAvatar(scene, seat, gltfUrl, options = {}) {
    const {
        scale = 0.8,           // Scale factor for avatar size
        rotationY = Math.PI,   // Rotation to face forward
        sittingHeight = 1.1,   // Y position for sitting in pew
        standingHeight = 1.8,   // Y position for standing on stage
        isStanding = false,     // Whether avatar is standing or sitting
    } = options;

    try {
        // Load the GLTF model
        const gltf = await new Promise((resolve, reject) => {
            gltfLoader.load(
                gltfUrl,
                (gltf) => resolve(gltf),
                (progress) => {
                    // Optional: track loading progress
                    if (options.onProgress) {
                        options.onProgress(progress);
                    }
                },
                (error) => reject(error)
            );
        });

        // Get the position from seat data
        const position = seat.position || { x: 0, z: 0 };
        const avatarY = isStanding ? standingHeight : sittingHeight;

        // Create a group for the avatar
        const avatarGroup = new THREE.Group();
        
        // Clone the scene from the GLTF (contains the avatar model)
        const avatarModel = gltf.scene.clone();
        
        // Scale the avatar to appropriate size
        avatarModel.scale.set(scale, scale, scale);
        
        // Position the avatar
        avatarGroup.position.set(position.x, avatarY, position.z);
        
        // Rotate to face forward (toward stage)
        avatarGroup.rotation.y = rotationY;
        
        // Add the model to the group
        avatarGroup.add(avatarModel);
        
        // Add to scene
        scene.add(avatarGroup);
        
        // Store reference for potential cleanup or interaction
        avatarGroup.userData = {
            seat: seat,
            gltfUrl: gltfUrl,
            name: seat.name || 'Guest',
        };
        
        // Add name label (optional - can be a 3D text or billboard)
        if (options.showNameLabel) {
            addNameLabel(avatarGroup, seat.name || 'Guest');
        }
        
        return avatarGroup;
    } catch (error) {
        console.error(`Error loading Unity avatar for seat ${seat.name}:`, error);
        return null;
    }
}

/**
 * Add a name label above the avatar (optional)
 */
function addNameLabel(avatarGroup, name) {
    // Create a simple text sprite or 3D text
    // For now, we'll use a simple approach with CSS (can be enhanced with 3D text)
    // This would require additional setup with TextGeometry or a sprite
}

/**
 * Load all Unity avatars for seating
 * @param {THREE.Scene} scene - Three.js scene
 * @param {Array} seating - Array of seat data
 * @param {object} avatarUrlMap - Map of seat names to GLTF URLs
 * @param {object} options - Global options for all avatars
 */
export async function loadAllUnityAvatars(scene, seating, avatarUrlMap, options = {}) {
    const avatarPromises = seating.map(async (seat) => {
        const gltfUrl = avatarUrlMap[seat.name] || avatarUrlMap[seat.guest_name];
        if (!gltfUrl) {
            console.warn(`No Unity avatar URL found for ${seat.name}`);
            return null;
        }
        
        return loadUnityAvatar(scene, seat, gltfUrl, {
            ...options,
            isStanding: seat.isBride || seat.isGroom, // Bride/groom stand, guests sit
        });
    });
    
    const avatars = await Promise.all(avatarPromises);
    return avatars.filter(avatar => avatar !== null);
}

/**
 * Create a simple placeholder avatar from Unity export
 * Useful for testing or fallback
 */
export function createPlaceholderAvatar(scene, position, name) {
    const geometry = new THREE.CapsuleGeometry(0.3, 1.2, 4, 8);
    const material = new THREE.MeshStandardMaterial({ 
        color: 0xd7c7de, // Lavender
        roughness: 0.7,
    });
    const placeholder = new THREE.Mesh(geometry, material);
    placeholder.position.set(position.x, 1.1, position.z);
    placeholder.userData = { name, isPlaceholder: true };
    scene.add(placeholder);
    return placeholder;
}
