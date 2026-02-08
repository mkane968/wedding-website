/**
 * Ready Player Me 3D Avatar Loader for Chapel Scene
 * Loads GLTF models from Ready Player Me and places them in the 3D scene
 */

import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { getAvatarUrl } from "./readyPlayerMe.js";

const gltfLoader = new GLTFLoader();

/**
 * Load a Ready Player Me avatar and add it to the scene
 * @param {THREE.Scene} scene - Three.js scene
 * @param {object} seat - Seat data with position and avatar info
 * @param {string} rpmUserId - Ready Player Me user ID
 * @param {string} rpmToken - Ready Player Me access token
 */
export async function loadRPMAvatar(scene, seat, rpmUserId, rpmToken) {
    try {
        // Get the avatar GLTF URL
        const avatarUrl = await getAvatarUrl(rpmUserId, rpmToken);
        
        if (!avatarUrl) {
            console.warn(`No avatar URL found for user ${rpmUserId}`);
            return null;
        }

        // Load the GLTF model
        const gltf = await new Promise((resolve, reject) => {
            gltfLoader.load(
                avatarUrl,
                (gltf) => resolve(gltf),
                undefined,
                (error) => reject(error)
            );
        });

        // Get the position from seat data
        const position = seat.position || { x: 0, z: 0 };
        const avatarY = 1.1; // Sitting height in pew

        // Create a group for the avatar
        const avatarGroup = new THREE.Group();
        
        // Clone the scene from the GLTF (contains the avatar model)
        const avatarModel = gltf.scene.clone();
        
        // Scale the avatar to appropriate size (Ready Player Me avatars are typically ~1.8 units tall)
        const scale = 0.8; // Adjust based on your scene scale
        avatarModel.scale.set(scale, scale, scale);
        
        // Position the avatar
        avatarGroup.position.set(position.x, avatarY, position.z);
        
        // Rotate to face forward (toward stage)
        avatarGroup.rotation.y = Math.PI; // Face forward
        
        // Add the model to the group
        avatarGroup.add(avatarModel);
        
        // Add to scene
        scene.add(avatarGroup);
        
        // Store reference for potential cleanup
        avatarGroup.userData = {
            seat: seat,
            rpmUserId: rpmUserId,
        };
        
        return avatarGroup;
    } catch (error) {
        console.error(`Error loading Ready Player Me avatar for seat ${seat.name}:`, error);
        return null;
    }
}

/**
 * Load all Ready Player Me avatars for seating
 * @param {THREE.Scene} scene - Three.js scene
 * @param {Array} seating - Array of seat data
 * @param {object} rpmUserMap - Map of seat/user names to { userId, token }
 */
export async function loadAllRPMAvatars(scene, seating, rpmUserMap) {
    const avatarPromises = seating.map(async (seat) => {
        const rpmData = rpmUserMap[seat.name];
        if (!rpmData || !rpmData.userId || !rpmData.token) {
            console.warn(`No Ready Player Me data for ${seat.name}`);
            return null;
        }
        
        return loadRPMAvatar(scene, seat, rpmData.userId, rpmData.token);
    });
    
    const avatars = await Promise.all(avatarPromises);
    return avatars.filter(avatar => avatar !== null);
}
