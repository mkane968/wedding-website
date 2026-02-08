import * as THREE from "three";
import { colors, seatsPerRow, layout } from "./constants.js";

const seatsPerSide = Math.ceil(seatsPerRow / 2);
const seatSpacing = layout.seatSpacing;
const rowSpacing = layout.rowSpacing;
const rowOffset = layout.rowOffset || 0;
const sideCenterOffset =
    layout.aisleHalfWidth + layout.aisleGap + ((seatsPerSide - 1) * seatSpacing) / 2;

const textureLoader = new THREE.TextureLoader();
textureLoader.crossOrigin = "anonymous";

const SKIN_PALETTE = {
    dark1: "614335",
    medium1: "ae5d29",
    light1: "edb98a",
    // Additional skin tones from before
    porcelain: "eeb4a4",
    rosy: "e7a391",
    sienna: "d78774",
    amber: "b16a5b",
    espresso: "92594b",
};

const HAIR_COLORS = {
    dark1: "2c1b18",
    dark2: "4a312c",
    brown1: "724133",
    brown2: "a55728",
    brown3: "b58143",
    red: "c93305",
    blonde1: "d6b370",
    blonde2: "e8e1e1",
};

const HAIR_STYLES = {
    shortWaved: "shortWaved",
    longButNotTooLong: "longButNotTooLong",
    straightAndStrand: "straightAndStrand",
    sides: "sides",
    shortFlat: "shortFlat",
    curvy: "curvy",
};

const BACKGROUND_SWATCHES = {
    champagne: "f7e8d8",
    lavender: "b19acb",
    midnight: "1c1c3c",
    sage: "b8c4ae",
    rose: "f3c0c6",
    white: "ffffff",
};

const ACCENT_EYES = {
    na: "default",
    floral: "happy",
    "pocket-square": "wink",
    veil: "sleep",
    "bow-tie": "default",  // Glasses will be handled via accessories
};

const ACCENT_MOUTH = {
    na: "default",
    floral: "smile",
    "pocket-square": "smile",
    veil: "default",
    "bow-tie": "smirk",
};

const CLOTHING_STYLES = {
    blazer: "blazerAndShirt",
    vneck: "shirtVNeck",
};

const FACIAL_HAIR_OPTIONS = {
    none: "blank",
    beard: "beardLight",
    mustache: "moustacheMagnum",
};

const ACCESSORIES_OPTIONS = {
    none: "blank",
    glasses: "prescription02",
};

const ACCESSORIES_COLORS = {
    dark: "3c4f5c",
    blue: "65c9ff",
    black: "262e33",
};

const CLOTHES_COLORS = {
    pink: "ff488e",
    blue: "65c9ff",
    purple: "b19acb",  // Using lavender as purple
    green: "a7ffc4",
    red: "ff5c5c",
    black: "262e33",
};

// Legacy mapping for accent-based accessories (for backward compatibility)
const ACCENT_ACCESSORIES = {
    na: "blank",
    floral: "blank",
    "pocket-square": "blank",
    veil: "blank",
    "bow-tie": "prescription01",  // Glasses for bow-tie accent
};

function seatOffset(seatIndex) {
    const side = seatIndex < seatsPerSide ? "left" : "right";
    const indexWithinSide = side === "left" ? seatIndex : seatIndex - seatsPerSide;
    const lateral = (indexWithinSide - (seatsPerSide - 1) / 2) * seatSpacing;
    const xCenter = (side === "left" ? -1 : 1) * sideCenterOffset;
    return xCenter + lateral;
}

function buildAvatarUrl(config = {}, fallbackSeed = "guest") {
    const params = new URLSearchParams();
    params.append("seed", (config.signature || fallbackSeed || "guest-avatar").trim());
    const hairColor = HAIR_COLORS[config.hair] || HAIR_COLORS.dark1;
    const hairStyle = HAIR_STYLES[config.hairStyle] || HAIR_STYLES.shortFlat;
    const clothesColor = CLOTHES_COLORS[config.clothesColor] || CLOTHES_COLORS.blue;
    params.append("skinColor", SKIN_PALETTE[config.skin] || SKIN_PALETTE.light1);
    params.append("hairColor", hairColor);
    params.append("top", hairStyle);
    params.append("clothing", config.clothesType || "collarAndSweater");  // Use selected clothing style
    params.append("clothesColor", clothesColor);
    params.append("eyes", "default");  // Default eyes
    params.append("eyebrows", "defaultNatural");
    params.append("mouth", "smile");  // Default smile
    params.append("facialHairColor", hairColor);  // Facial hair and eyebrow color matches hair color
    
    // Facial hair: use facialHair field or default to none
    const facialHair = FACIAL_HAIR_OPTIONS[config.facialHair] || "blank";
    
    // Only add facial hair if not "blank", otherwise set probability to 0
    if (facialHair === "blank") {
        params.append("facialHairProbability", "0");
    } else {
        params.append("facialHair", facialHair);
        params.append("facialHairProbability", "100");  // Ensure facial hair appears when selected
    }
    
    // Accessories: use accessories field or default to none
    const accessories = ACCESSORIES_OPTIONS[config.accessories] || "blank";
    
    // Only add accessories if not "blank", otherwise set probability to 0
    if (accessories === "blank") {
        params.append("accessoriesProbability", "0");
    } else {
        params.append("accessories", accessories);
        params.append("accessoriesProbability", "100");  // Ensure accessories appear when selected
    }
    
    return `https://api.dicebear.com/9.x/avataaars/svg?${params.toString()}`;
}

// 3D AVATARS - COMMENTED OUT (BACKUP)
// Using 2D avatars instead for better compatibility
/*
export function addAvatars(scene, seating) {
    seating.forEach((seat) => {
        const seatIdx = typeof seat.seat_index === "number" ? seat.seat_index : 0;
        const rowIdx = typeof seat.row_index === "number" ? seat.row_index : 0;
        
        // Ensure row_index is valid (non-negative)
        if (rowIdx < 0) {
            console.warn('Invalid row_index:', rowIdx, 'for seat:', seat);
            return; // Skip invalid seats
        }
        
        const hasExplicitPosition =
            seat.position && typeof seat.position === "object";
        const x =
            hasExplicitPosition && typeof seat.position.x === "number"
                ? seat.position.x
                : seatOffset(seatIdx);
        // Use server-provided coordinates when available, otherwise fall back to layout offsets.
        const z =
            hasExplicitPosition && typeof seat.position.z === "number"
                ? seat.position.z
                : -((rowIdx + rowOffset) * rowSpacing) - 1.2;
        
        // Safety check: ensure z is negative (in pews area, not on stage)
        if (z >= 0) {
            console.warn('Avatar z position would be on stage:', z, 'for seat:', seat);
            return; // Skip seats that would be on stage
        }
        
        const url = buildAvatarUrl(seat.config || {}, seat.name || "guest");

        textureLoader.load(
            url,
            (texture) => {
                const material = new THREE.MeshBasicMaterial({
                    map: texture,
                    transparent: true,
                    side: THREE.DoubleSide,
                });
                const plane = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 2.3), material);
                plane.position.set(x, 1.7, z);
                plane.lookAt(0, 1.5, 10);
                scene.add(plane);
            },
            undefined,
            () => {
                const fallback = new THREE.Mesh(
                    new THREE.CylinderGeometry(0.7, 0.7, 1.6, 24),
                    new THREE.MeshStandardMaterial({ color: colors.lavender })
                );
                fallback.position.set(x, 1.1, z);
                scene.add(fallback);
            }
        );
    });
}
*/

export function addCouple(scene) {
    const bride = createHeroAvatar(0.8, colors.plum);
    bride.position.set(-1.2, 1.1, 4);
    scene.add(bride);

    const groom = createHeroAvatar(0.8, 0x2e2d34);
    groom.position.set(1.2, 1.1, 4);
    scene.add(groom);
}

export function addBrideAndGroom(scene) {
    // Both avatars should have purple backgrounds
    // Build custom URLs with purple backgrounds for both
    
    // Bride: brown hair (chestnut), glasses, purple background
    const brideParams = new URLSearchParams();
    brideParams.append("seed", "bride-megan-white");
    brideParams.append("skinColor[]", SKIN_PALETTE.porcelain);
    brideParams.append("hair[]", HAIR_STYLES.long);
    brideParams.append("hairColor[]", HAIR_COLORS.chestnut);
    brideParams.append("backgroundColor[]", BACKGROUND_SWATCHES.lavender); // Purple background
    brideParams.append("eyes[]", ACCENT_EYES["bow-tie"]); // Glasses
    brideParams.append("mouth[]", "smile");
    brideParams.append("nose[]", "mediumRound");
    brideParams.append("size", "210");
    brideParams.append("translateY", "-6");
    const brideUrl = `https://api.dicebear.com/9.x/personas/svg?${brideParams.toString()}`;
    
    // Groom: brown hair (chestnut), glasses, bow tie, purple background
    const groomParams = new URLSearchParams();
    groomParams.append("seed", "groom-stephen-black");
    groomParams.append("skinColor[]", SKIN_PALETTE.porcelain);
    groomParams.append("hair[]", HAIR_STYLES.short);
    groomParams.append("hairColor[]", HAIR_COLORS.chestnut);
    groomParams.append("backgroundColor[]", BACKGROUND_SWATCHES.lavender); // Purple background
    groomParams.append("eyes[]", ACCENT_EYES["bow-tie"]); // Glasses
    groomParams.append("mouth[]", ACCENT_MOUTH["bow-tie"] || "smirk"); // Bow tie mouth
    groomParams.append("nose[]", "mediumRound");
    groomParams.append("size", "210");
    groomParams.append("translateY", "-6");
    const groomUrl = `https://api.dicebear.com/9.x/personas/svg?${groomParams.toString()}`;

    // Position on stage - move closer to front of stage
    // Stage front is around z=2-3, so use z=2.5
    const stageZ = 2.5;
    const brideX = -2.5; // Left side
    const groomX = 2.5;  // Right side
    const stageY = 1.8;  // Standing height on stage

    // Load and add bride
    textureLoader.load(
        brideUrl,
        (texture) => {
            const material = new THREE.MeshBasicMaterial({
                map: texture,
                transparent: true,
                side: THREE.DoubleSide,
            });
            const plane = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 2.3), material);
            plane.position.set(brideX, stageY, stageZ);
            plane.lookAt(0, stageY, -20); // Face forward (toward audience/negative z)
            scene.add(plane);
        },
        undefined,
        () => {
            console.warn("Failed to load bride avatar");
        }
    );

    // Load and add groom
    textureLoader.load(
        groomUrl,
        (texture) => {
            const material = new THREE.MeshBasicMaterial({
                map: texture,
                transparent: true,
                side: THREE.DoubleSide,
            });
            const plane = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 2.3), material);
            plane.position.set(groomX, stageY, stageZ);
            plane.lookAt(0, stageY, -20); // Face forward (toward audience/negative z)
            scene.add(plane);
        },
        undefined,
        () => {
            console.warn("Failed to load groom avatar");
        }
    );
}

function createHeroAvatar(scale, color) {
    const group = new THREE.Group();
    const body = new THREE.Mesh(
        new THREE.CylinderGeometry(0.9 * scale, 0.9 * scale, 2.5 * scale, 32),
        new THREE.MeshStandardMaterial({ color, roughness: 0.35 })
    );
    body.position.y = 1.2 * scale;
    group.add(body);

    const head = new THREE.Mesh(
        new THREE.SphereGeometry(0.8 * scale, 32, 32),
        new THREE.MeshStandardMaterial({ color: 0xf4e9e0 })
    );
    head.position.y = 2.6 * scale;
    group.add(head);

    const halo = new THREE.Mesh(
        new THREE.TorusGeometry(1.2 * scale, 0.06, 16, 60),
        new THREE.MeshBasicMaterial({ color: colors.lavender })
    );
    halo.rotation.x = Math.PI / 2;
    halo.position.y = 3.3 * scale;
    group.add(halo);

    return group;
}
