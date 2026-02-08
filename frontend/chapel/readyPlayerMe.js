/**
 * Ready Player Me API Integration
 * 
 * NOTE: You'll need to:
 * 1. Register at https://readyplayer.me/developers
 * 2. Create an application and get your APPLICATION_ID
 * 3. Set the APPLICATION_ID in your environment or config
 */

const READY_PLAYER_ME_API = "https://api.readyplayer.me/v1";
let APPLICATION_ID = null; // Set this from your config

/**
 * Set the Ready Player Me application ID
 */
export function setApplicationId(appId) {
    APPLICATION_ID = appId;
}

/**
 * Create an anonymous Ready Player Me user
 * Returns: { userId, token }
 */
export async function createAnonymousUser() {
    if (!APPLICATION_ID) {
        throw new Error("Ready Player Me APPLICATION_ID not set. Call setApplicationId() first.");
    }

    try {
        const response = await fetch(`${READY_PLAYER_ME_API}/users`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                data: {
                    applicationId: APPLICATION_ID,
                },
            }),
        });

        if (!response.ok) {
            throw new Error(`Failed to create user: ${response.statusText}`);
        }

        const result = await response.json();
        return {
            userId: result.data.id,
            token: result.data.token,
        };
    } catch (error) {
        console.error("Error creating Ready Player Me user:", error);
        throw error;
    }
}

/**
 * Create or update an avatar for a user
 * @param {string} token - User's access token
 * @param {object} avatarConfig - Avatar configuration
 * @returns {string} Avatar GLTF URL
 */
export async function createOrUpdateAvatar(token, avatarConfig = {}) {
    // Ready Player Me uses a web-based avatar editor
    // For programmatic creation, you'd typically:
    // 1. Use their avatar builder API
    // 2. Or redirect users to their avatar builder
    // 3. Or use their REST API to create avatars with specific parameters
    
    // This is a placeholder - you'll need to check Ready Player Me's
    // actual API documentation for creating avatars programmatically
    // They may require using their avatar builder UI
    
    try {
        // Example: Create a draft avatar
        // The actual endpoint and parameters depend on Ready Player Me's API
        const response = await fetch(`${READY_PLAYER_ME_API}/avatars`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`,
            },
            body: JSON.stringify({
                // Avatar configuration parameters
                // Check Ready Player Me docs for available options
                ...avatarConfig,
            }),
        });

        if (!response.ok) {
            throw new Error(`Failed to create avatar: ${response.statusText}`);
        }

        const result = await response.json();
        return result.data.modelUrl || result.data.gltfUrl; // GLTF model URL
    } catch (error) {
        console.error("Error creating Ready Player Me avatar:", error);
        throw error;
    }
}

/**
 * Get avatar GLTF URL for a user
 * @param {string} userId - User ID
 * @param {string} token - User's access token
 * @returns {string} Avatar GLTF URL
 */
export async function getAvatarUrl(userId, token) {
    try {
        const response = await fetch(`${READY_PLAYER_ME_API}/avatars?userId=${userId}`, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            throw new Error(`Failed to get avatar: ${response.statusText}`);
        }

        const result = await response.json();
        // Return the GLTF model URL
        return result.data?.[0]?.modelUrl || result.data?.modelUrl;
    } catch (error) {
        console.error("Error getting Ready Player Me avatar:", error);
        throw error;
    }
}

/**
 * Convert DiceBear config to Ready Player Me parameters
 * This is a mapping helper - Ready Player Me has different parameter names
 */
export function convertDiceBearToRPM(config) {
    // Ready Player Me uses different parameters than DiceBear
    // This is a placeholder mapping - you'll need to adjust based on
    // Ready Player Me's actual API parameters
    
    return {
        // Map skin tones, hair styles, etc. to Ready Player Me format
        // Check Ready Player Me documentation for exact parameter names
        bodyType: "fullbody", // or "halfbody"
        // Add other mappings based on Ready Player Me's API
    };
}
