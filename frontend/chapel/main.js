import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
// Optional: Import Unity avatar loader
// import { loadAllUnityAvatars } from "./unityAvatars.js";

import { colors } from "./constants.js";
import { loadSeating } from "./seating.js";
import { buildPews } from "./pews.js";
import { addAvatars, addBrideAndGroom } from "./avatars.js";
import {
    addEnvironment,
    addWindows,
    addOrgan,
    addPulpit,
} from "./environment.js";
import { addFloatingPetals } from "./petals.js";

// Global zoom level tracker (0 = front rows, increases as you zoom out)
// Reset to 0 on page load to show first 3 rows
let currentZoomLevel = 0;

function initializeScene() {
    const container = document.querySelector("[data-chapel-scene]");
    if (!container) {
        return;
    }
    const seating = loadSeating();
    const width = container.clientWidth || 900;
    const height = 520;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(colors.rose);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 500); // Increased far plane for better zoom
    camera.position.set(0, 10, -28);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 2, 5);
    controls.enableDamping = true;
    controls.minDistance = 5; // Allow closer zoom
    controls.maxDistance = 200; // Allow further zoom out

    const ambient = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambient);
    const directional = new THREE.DirectionalLight(0xffffff, 0.5);
    directional.position.set(10, 20, 15);
    scene.add(directional);

    const warmSpot = new THREE.SpotLight(0xfff2e5, 1.1, 60, Math.PI / 6, 0.45, 1.5);
    warmSpot.position.set(0, 18, 10);
    warmSpot.target.position.set(0, 0, -5);
    scene.add(warmSpot);
    scene.add(warmSpot.target);

    addEnvironment(scene);
    addWindows(scene);
    addOrgan(scene);
    addPulpit(scene);
    // Calculate total rows needed (all rows have 10 seats each)
    const SEATS_PER_ROW = 10;
    const totalRows = Math.ceil(seating.length / SEATS_PER_ROW);
    // Only build pews for rows that have guests (plus one extra row for visual completeness)
    const maxRowIndex = seating.length > 0 ? Math.max(...seating.map(s => s.row_index || 0)) : 0;
    buildPews(scene, maxRowIndex);
    // 3D avatars commented out - using 2D avatars instead
    // addAvatars(scene, seating);
    // addBrideAndGroom(scene);
    
    const animatePetals = addFloatingPetals(scene);
    
    // Render 2D avatars that track with the 3D scene
    const avatarElements = render2DAvatars(container, seating, camera, renderer);
    
    // Add zoom buttons (right side)
    const zoomControls = document.createElement('div');
    zoomControls.style.position = 'absolute';
    zoomControls.style.top = '10px';
    zoomControls.style.right = '10px';
    zoomControls.style.zIndex = '1000';
    zoomControls.style.display = 'flex';
    zoomControls.style.flexDirection = 'column';
    zoomControls.style.gap = '8px';
    
    // Add game/photo buttons (left side)
    const gameControls = document.createElement('div');
    gameControls.style.position = 'absolute';
    gameControls.style.top = '10px';
    gameControls.style.left = '10px';
    gameControls.style.zIndex = '1001'; // Higher than zoom controls
    gameControls.style.display = 'flex';
    gameControls.style.flexDirection = 'row';
    gameControls.style.gap = '8px';
    gameControls.style.pointerEvents = 'auto'; // Ensure clicks work
    
    const zoomInBtn = document.createElement('button');
    zoomInBtn.textContent = '+';
    zoomInBtn.style.width = '40px';
    zoomInBtn.style.height = '40px';
    zoomInBtn.style.borderRadius = '4px';
    zoomInBtn.style.border = '2px solid #4c2a4f';
    zoomInBtn.style.background = '#ffffff';
    zoomInBtn.style.color = '#4c2a4f';
    zoomInBtn.style.fontSize = '24px';
    zoomInBtn.style.cursor = 'pointer';
    zoomInBtn.style.fontFamily = 'inherit';
    zoomInBtn.style.fontWeight = 'bold';
    zoomInBtn.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
    zoomInBtn.addEventListener('click', () => {
        // Zoom in (move camera closer)
        const currentDistance = camera.position.distanceTo(controls.target);
        const newDistance = Math.max(5, currentDistance - 10);
        const direction = camera.position.clone().sub(controls.target).normalize();
        camera.position.copy(controls.target.clone().add(direction.multiplyScalar(newDistance)));
        controls.update();
    });
    
    const zoomOutBtn = document.createElement('button');
    zoomOutBtn.textContent = '−';
    zoomOutBtn.style.width = '40px';
    zoomOutBtn.style.height = '40px';
    zoomOutBtn.style.borderRadius = '4px';
    zoomOutBtn.style.border = '2px solid #4c2a4f';
    zoomOutBtn.style.background = '#ffffff';
    zoomOutBtn.style.color = '#4c2a4f';
    zoomOutBtn.style.fontSize = '24px';
    zoomOutBtn.style.cursor = 'pointer';
    zoomOutBtn.style.fontFamily = 'inherit';
    zoomOutBtn.style.fontWeight = 'bold';
    zoomOutBtn.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
    zoomOutBtn.addEventListener('click', () => {
        // Zoom out (move camera further)
        const currentDistance = camera.position.distanceTo(controls.target);
        const newDistance = Math.min(200, currentDistance + 10);
        const direction = camera.position.clone().sub(controls.target).normalize();
        camera.position.copy(controls.target.clone().add(direction.multiplyScalar(newDistance)));
        controls.update();
    });
    
    zoomControls.appendChild(zoomInBtn);
    zoomControls.appendChild(zoomOutBtn);
    
    // Add "Take Picture" button
    const photoBtn = document.createElement('button');
    photoBtn.textContent = '📷 Take Picture';
    photoBtn.style.width = 'auto';
    photoBtn.style.height = '40px';
    photoBtn.style.padding = '0 16px';
    photoBtn.style.borderRadius = '4px';
    photoBtn.style.border = '2px solid #4c2a4f';
    photoBtn.style.background = '#ffffff';
    photoBtn.style.color = '#4c2a4f';
    photoBtn.style.fontSize = '14px';
    photoBtn.style.cursor = 'pointer';
    photoBtn.style.fontFamily = 'inherit';
    photoBtn.style.fontWeight = 'bold';
    photoBtn.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
    photoBtn.addEventListener('click', () => {
        // Get current RSVP ID from page if available
        const rsvpIdScript = document.getElementById('current-rsvp-id');
        const currentRsvpId = rsvpIdScript ? JSON.parse(rsvpIdScript.textContent) : null;
        showPhotoModal(seating, currentRsvpId);
    });
    
    // Add "Play Minigame" button
    const gameBtn = document.createElement('button');
    gameBtn.textContent = '🎮 Play Minigame';
    gameBtn.style.width = 'auto';
    gameBtn.style.height = '40px';
    gameBtn.style.padding = '0 16px';
    gameBtn.style.borderRadius = '4px';
    gameBtn.style.border = '2px solid #4c2a4f';
    gameBtn.style.background = '#ffffff';
    gameBtn.style.color = '#4c2a4f';
    gameBtn.style.fontSize = '14px';
    gameBtn.style.cursor = 'pointer';
    gameBtn.style.fontFamily = 'inherit';
    gameBtn.style.fontWeight = 'bold';
    gameBtn.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
    gameBtn.style.pointerEvents = 'auto';
    gameBtn.style.position = 'relative';
    gameBtn.style.zIndex = '1002';
    gameBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('Game button clicked');
        // Get current RSVP ID from page if available
        const rsvpIdScript = document.getElementById('current-rsvp-id');
        const currentRsvpId = rsvpIdScript ? JSON.parse(rsvpIdScript.textContent) : null;
        console.log('Calling showMinigameModal with seating:', seating?.length, 'currentRsvpId:', currentRsvpId);
        try {
            showMinigameModal(seating, currentRsvpId);
        } catch (error) {
            console.error('Error showing minigame modal:', error);
            alert('Error starting minigame: ' + error.message);
        }
    });
    
    gameControls.appendChild(photoBtn);
    gameControls.appendChild(gameBtn);
    container.appendChild(gameControls);
    container.appendChild(zoomControls);

    function onWindowResize() {
        const newWidth = container.clientWidth || width;
        camera.aspect = newWidth / height;
        camera.updateProjectionMatrix();
        renderer.setSize(newWidth, height);
    }
    window.addEventListener("resize", onWindowResize);

    function animate() {
        requestAnimationFrame(animate);
        controls.update();
        animatePetals();
        renderer.render(scene, camera);
        
        // Update 2D avatar positions based on current camera view
        if (avatarElements) {
            updateAvatarPositions(avatarElements, seating, camera, renderer, container, controls);
        }
    }
    animate();
}

function buildBrideAvatarUrl() {
    const params = new URLSearchParams();
    params.append("seed", "bride-megan");
    params.append("skinColor", "eeb4a4"); // porcelain (second skin tone)
    params.append("hairColor", "4a312c"); // dark2 (second hair color)
    params.append("clothing", "shirtVNeck"); // V-neck
    params.append("clothesColor", "ffffff"); // white
    params.append("eyes", "default"); // Default eyes
    params.append("eyebrows", "defaultNatural");
    params.append("mouth", "smile"); // Default smile
    params.append("facialHairColor", "4a312c"); // Eyebrow color matches hair color
    params.append("accessories", "prescription02"); // glasses
    params.append("accessoriesProbability", "100"); // Ensure glasses appear
    params.append("accessoriesColor", "b19acb"); // purple glasses
    return `https://api.dicebear.com/9.x/avataaars/svg?${params.toString()}`;
}

function buildGroomAvatarUrl() {
    const params = new URLSearchParams();
    params.append("seed", "groom-stephen");
    params.append("skinColor", "eeb4a4"); // porcelain (second skin tone)
    params.append("hairColor", "724133"); // brown1 (third hair color)
    params.append("top", "shortWaved"); // Short 1 hair style
    params.append("clothing", "blazerAndSweater"); // Blazer and sweater
    params.append("clothesColor", "b19acb"); // purple blazer
    params.append("eyes", "default"); // Default eyes
    params.append("eyebrows", "defaultNatural");
    params.append("mouth", "smile"); // Default smile
    params.append("facialHairColor", "724133"); // Eyebrow color matches hair color
    params.append("accessories", "prescription02"); // glasses
    params.append("accessoriesProbability", "100"); // Ensure glasses appear
    params.append("accessoriesColor", "b8860b"); // Darker gold color for glasses
    return `https://api.dicebear.com/9.x/avataaars/svg?${params.toString()}`;
}

function render2DAvatars(container, seating, camera, renderer) {
    // Create a container for 2D avatars positioned over the 3D scene
    const avatarContainer = document.createElement('div');
    avatarContainer.id = 'chapel-2d-avatars';
    avatarContainer.style.position = 'absolute';
    avatarContainer.style.top = '0';
    avatarContainer.style.left = '0';
    avatarContainer.style.width = '100%';
    avatarContainer.style.height = '100%';
    avatarContainer.style.pointerEvents = 'none';
    avatarContainer.style.overflow = 'visible'; // Changed to visible for tooltips
    container.style.position = 'relative';
    container.appendChild(avatarContainer);
    
    // Create tooltip element
    const tooltip = document.createElement('div');
    tooltip.id = 'chapel-avatar-tooltip';
    tooltip.style.position = 'absolute';
    tooltip.style.padding = '0.5rem 0.75rem';
    tooltip.style.background = 'rgba(44, 42, 47, 0.95)';
    tooltip.style.color = '#ffffff';
    tooltip.style.borderRadius = '4px';
    tooltip.style.fontFamily = "'Cormorant Garamond', Georgia, serif";
    tooltip.style.fontSize = '0.9rem';
    tooltip.style.pointerEvents = 'none';
    tooltip.style.zIndex = '100';
    tooltip.style.opacity = '0';
    tooltip.style.transition = 'opacity 0.2s';
    tooltip.style.whiteSpace = 'nowrap';
    tooltip.style.boxShadow = '0 2px 8px rgba(0,0,0,0.3)';
    avatarContainer.appendChild(tooltip);
    
    const avatarElements = [];
    
    // Add bride and groom at the front by podium
    // Podium is at position (0, 2.4, 4.2), stage is at z=6
    // Position them on stage in front of podium
    const brideEl = document.createElement('img');
    brideEl.src = buildBrideAvatarUrl();
    brideEl.alt = 'Megan';
    brideEl.style.position = 'absolute';
    brideEl.style.width = '57px';
    brideEl.style.height = '57px';
    brideEl.style.objectFit = 'cover';
    brideEl.style.transform = 'translateZ(0)';
    brideEl.style.zIndex = '5'; // Lower z-index so guests can appear in front when closer
    brideEl.style.cursor = 'pointer';
    brideEl.style.pointerEvents = 'auto'; // Enable pointer events for hover
    brideEl.title = 'Megan';
    brideEl.style.opacity = '0';
    brideEl.dataset.guestName = 'Megan';
    setupAvatarHover(brideEl, tooltip);
    avatarContainer.appendChild(brideEl);
    avatarElements.push({
        element: brideEl,
        position: { x: -2.5, z: 4.2 }, // Left side of podium
        isBride: true
    });
    
    const groomEl = document.createElement('img');
    groomEl.src = buildGroomAvatarUrl();
    groomEl.alt = 'Stephen';
    groomEl.style.position = 'absolute';
    groomEl.style.width = '70px';
    groomEl.style.height = '70px';
    groomEl.style.objectFit = 'cover';
    groomEl.style.transform = 'translateZ(0)';
    groomEl.style.zIndex = '5'; // Lower z-index so guests can appear in front when closer
    groomEl.style.cursor = 'pointer';
    groomEl.style.pointerEvents = 'auto'; // Enable pointer events for hover
    groomEl.title = 'Stephen';
    groomEl.style.opacity = '0';
    groomEl.dataset.guestName = 'Stephen';
    setupAvatarHover(groomEl, tooltip);
    avatarContainer.appendChild(groomEl);
    avatarElements.push({
        element: groomEl,
        position: { x: 2.5, z: 4.2 }, // Right side of podium
        isGroom: true
    });
    
    seating.forEach((seat) => {
        if (!seat.avatar_url) return;
        
        // Create avatar element
        const avatarEl = document.createElement('img');
        avatarEl.src = seat.avatar_url;
        avatarEl.alt = seat.name || 'Guest';
        avatarEl.style.position = 'absolute';
        avatarEl.style.width = '60px';
        avatarEl.style.height = '60px';
        avatarEl.style.objectFit = 'cover';
        avatarEl.style.transform = 'translateZ(0)'; // Force GPU acceleration
        avatarEl.style.zIndex = '10';
        avatarEl.style.cursor = 'pointer';
        avatarEl.style.pointerEvents = 'auto'; // Enable pointer events for hover
        avatarEl.title = seat.name || 'Guest';
        avatarEl.style.opacity = '0'; // Start hidden, will be shown when positioned
        avatarEl.dataset.guestName = seat.name || 'Guest';
        setupAvatarHover(avatarEl, tooltip);
        
        // Store seat data with element for updates (including row_index for zoom-based fading)
        avatarElements.push({
            element: avatarEl,
            seat: seat,
            position: seat.position || { x: 0, z: 0 },
            isBride: false,
            isGroom: false
        });
        
        avatarContainer.appendChild(avatarEl);
    });
    
    return avatarElements;
}

function updateAvatarPositions(avatarElements, seating, camera, renderer, container, controls) {
    const width = container.clientWidth || 900;
    const height = 520;
    
    // Update camera matrices for accurate projection
    camera.updateMatrixWorld();
    
    // Estimate total number of rows (all rows have 10 seats each)
    const SEATS_PER_ROW = 10;
    const estimatedTotalRows = Math.ceil(seating.length / SEATS_PER_ROW);
    
    // Hardcoded rule: show exactly 3 rows based on zoom level
    // Zoom level 0: rows 0, 1, 2
    // Zoom level 1: rows 1, 2, 3 (row 0 disappears, row 3 appears)
    // Zoom level 2: rows 2, 3, 4 (row 1 disappears, row 4 appears)
    // etc.
    const startRow = currentZoomLevel;
    const minVisibleRow = startRow;
    const maxVisibleRow = Math.min(estimatedTotalRows - 1, startRow + 2);
    
    avatarElements.forEach(({ element, position, isBride, isGroom, seat }) => {
        const avatarX = position.x || 0;
        const avatarZ = position.z || 0;
        
        // Bride and groom stand on stage, guests sit in pews
        const avatarY = (isBride || isGroom) ? 1.8 : 1.1; // Standing height on stage vs sitting in pew
        
        // Create a vector for the 3D position
        const vector = new THREE.Vector3(avatarX, avatarY, avatarZ);
        
        // Project to screen space using current camera
        vector.project(camera);
        
        // Check if avatar is in front of camera and within reasonable bounds
        // vector.z in NDC: -1 is far, 1 is near, values > 1 are behind camera
        const isVisible = vector.z > -1 && vector.z < 1 && 
                         vector.x > -1.5 && vector.x < 1.5 && 
                         vector.y > -1.5 && vector.y < 1.5;
        
        if (isVisible) {
            // Convert normalized device coordinates to screen coordinates
            const screenX = (vector.x * 0.5 + 0.5) * width;
            let screenY = (vector.y * -0.5 + 0.5) * height; // Flip Y axis
            
            // Base size for avatars
            let baseSize = isBride ? 28.5 : (isGroom ? 35 : 30); // Bride smaller (57px), groom larger (70px), guests standard (60px)
            
            // Scale avatars based on row distance (smaller in back rows)
            let size = baseSize;
            if (!isBride && !isGroom && seat && typeof seat.row_index === 'number') {
                const rowIndex = seat.row_index;
                // Scale down avatars in back rows: front rows (0-2) = 100%, rows 3-5 = 90%, rows 6+ = 80%
                if (rowIndex <= 2) {
                    size = baseSize; // Full size for front rows
                } else if (rowIndex <= 5) {
                    size = baseSize * 0.9; // 90% for middle rows
                } else {
                    size = baseSize * 0.8; // 80% for back rows
                }
            }
            
            // Adjust bride's screen Y position to align avatar bottoms
            // Groom is 70px (size 35), bride is 57px (size 28.5), difference is 13px
            // To align bottoms, lower bride by half the difference (6.5px) - increase Y value
            if (isBride) {
                screenY = screenY + 6.5;
            }
            
            // Clamp to container bounds to prevent weird positioning
            const clampedX = Math.max(size, Math.min(width - size, screenX));
            const clampedY = Math.max(size, Math.min(height - size, screenY));
            
            element.style.left = `${clampedX - size}px`;
            element.style.top = `${clampedY - size}px`;
            
            // Set z-index based on projected depth so closer avatars appear in front
            // vector.z in NDC: -1 is far, 1 is near, so higher values = closer = should be on top
            // Convert to z-index range (1-20) where higher = closer
            const depthZIndex = Math.round((vector.z + 1) * 10); // Maps -1 to 1 range to 0-20
            element.style.zIndex = depthZIndex.toString();
            
            // Calculate visibility - show only 3 rows at a time based on zoom level
            let opacity = 1;
            let shouldShow = true;
            
            // Bride and groom always visible
            if (isBride || isGroom) {
                opacity = 1;
                shouldShow = true;
            } else if (seat && typeof seat.row_index === 'number') {
                const rowIndex = seat.row_index;
                
                // Show the 3 most visible rows fully, others slightly transparent
                if (rowIndex >= minVisibleRow && rowIndex <= maxVisibleRow) {
                    // Fully visible rows (the 3 most visible to camera)
                    opacity = 1;
                    shouldShow = true;
                } else {
                    // Rows outside the 3 most visible are slightly transparent but still visible
                    opacity = 0.3;
                    shouldShow = true;
                }
            }
            
            if (shouldShow) {
                element.style.opacity = opacity.toString();
                element.style.pointerEvents = 'auto';
            } else {
                element.style.opacity = '0';
                element.style.pointerEvents = 'none';
            }
            element.style.transition = 'opacity 0.3s ease-in-out'; // Smooth fade transitions
            
            // Fixed size - no scaling based on depth/zoom
            element.style.transform = 'translateZ(0)';
            element.style.width = `${size * 2}px`;
            element.style.height = `${size * 2}px`;
        } else {
            // Hide if behind camera, too far, or out of bounds
            element.style.opacity = '0';
        }
    });
}

function setupAvatarHover(avatarEl, tooltip) {
    avatarEl.addEventListener('mouseenter', function(e) {
        const guestName = this.dataset.guestName || this.title || 'Guest';
        tooltip.textContent = guestName;
        tooltip.style.opacity = '1';
        
        // Position tooltip above the avatar
        const rect = this.getBoundingClientRect();
        const containerRect = this.closest('[data-chapel-scene]').getBoundingClientRect();
        tooltip.style.left = `${rect.left - containerRect.left + (rect.width / 2)}px`;
        tooltip.style.top = `${rect.top - containerRect.top - 10}px`;
        tooltip.style.transform = 'translate(-50%, -100%)';
    });
    
    avatarEl.addEventListener('mouseleave', function() {
        tooltip.style.opacity = '0';
    });
    
    avatarEl.addEventListener('mousemove', function(e) {
        // Update tooltip position as mouse moves
        const rect = this.getBoundingClientRect();
        const containerRect = this.closest('[data-chapel-scene]').getBoundingClientRect();
        tooltip.style.left = `${rect.left - containerRect.left + (rect.width / 2)}px`;
        tooltip.style.top = `${rect.top - containerRect.top - 10}px`;
    });
}

function showPhotoModal(seating, currentRsvpId) {
    // Automatically find the user's party from seating data
    // Group seats by base name (without party number suffix)
    const guestMap = new Map();
    seating.forEach(seat => {
        const baseName = seat.name.replace(/\s*\(\d+\)$/, ''); // Remove party number suffix
        if (!guestMap.has(baseName)) {
            guestMap.set(baseName, []);
        }
        guestMap.get(baseName).push(seat);
    });
    
    // Get the most recent guest's party (first in seating list, which is most recent)
    let selectedSeats = [];
    if (seating.length > 0) {
        const firstSeat = seating[0];
        const baseName = firstSeat.name.replace(/\s*\(\d+\)$/, '');
        selectedSeats = guestMap.get(baseName) || [];
    }
    
    // Create modal overlay
    const modal = document.createElement('div');
    modal.style.position = 'fixed';
    modal.style.top = '0';
    modal.style.left = '0';
    modal.style.width = '100%';
    modal.style.height = '100%';
    modal.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    modal.style.zIndex = '10000';
    modal.style.display = 'flex';
    modal.style.justifyContent = 'center';
    modal.style.alignItems = 'center';
    modal.style.fontFamily = "'Cormorant Garamond', Georgia, serif";
    
    // Create modal content
    const content = document.createElement('div');
    content.style.backgroundColor = '#ffffff';
    content.style.borderRadius = '12px';
    content.style.padding = '2rem';
    content.style.maxWidth = '800px';
    content.style.width = '90%';
    content.style.maxHeight = '90vh';
    content.style.overflow = 'auto';
    content.style.boxShadow = '0 4px 20px rgba(0,0,0,0.3)';
    
    // Create photo preview container (show immediately)
    const photoContainer = document.createElement('div');
    photoContainer.id = 'photo-preview-container';
    photoContainer.style.display = 'block';
    photoContainer.style.padding = '2rem';
    photoContainer.style.backgroundColor = '#f7f1ee';
    photoContainer.style.borderRadius = '8px';
    photoContainer.style.textAlign = 'center';
    photoContainer.style.position = 'relative';
    content.appendChild(photoContainer);
    
    // Create close button
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'Close';
    closeBtn.style.padding = '0.75rem 2rem';
    closeBtn.style.fontSize = '1rem';
    closeBtn.style.backgroundColor = '#cccccc';
    closeBtn.style.color = '#333333';
    closeBtn.style.border = 'none';
    closeBtn.style.borderRadius = '4px';
    closeBtn.style.cursor = 'pointer';
    closeBtn.style.fontFamily = 'inherit';
    closeBtn.style.fontWeight = 'bold';
    closeBtn.style.marginTop = '1rem';
    closeBtn.style.display = 'block';
    closeBtn.style.margin = '1rem auto 0';
    
    closeBtn.addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    content.appendChild(closeBtn);
    
    modal.appendChild(content);
    document.body.appendChild(modal);
    
    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });
    
    // Render photo immediately
    renderPhoto(selectedSeats, photoContainer);
}

function showMinigameModal(seating, currentRsvpId) {
    console.log('showMinigameModal called', { seatingLength: seating?.length, currentRsvpId });
    
    // Get user's avatar
    let userAvatarUrl = null;
    if (seating && seating.length > 0) {
        const firstSeat = seating[0];
        userAvatarUrl = firstSeat.avatar_url || buildBrideAvatarUrl(); // Fallback to bride avatar
    } else {
        userAvatarUrl = buildBrideAvatarUrl();
    }
    
    console.log('User avatar URL:', userAvatarUrl);
    
    // Create modal overlay
    const modal = document.createElement('div');
    modal.style.position = 'fixed';
    modal.style.top = '0';
    modal.style.left = '0';
    modal.style.width = '100%';
    modal.style.height = '100%';
    modal.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    modal.style.zIndex = '10000';
    modal.style.display = 'flex';
    modal.style.justifyContent = 'center';
    modal.style.alignItems = 'center';
    modal.style.fontFamily = "'Cormorant Garamond', Georgia, serif";
    
    // Create game container
    const gameContainer = document.createElement('div');
    gameContainer.style.backgroundColor = '#d7c7de';
    gameContainer.style.borderRadius = '12px';
    gameContainer.style.padding = '2rem';
    gameContainer.style.maxWidth = '600px';
    gameContainer.style.width = '90%';
    gameContainer.style.boxShadow = '0 4px 20px rgba(0,0,0,0.3)';
    
    // Create canvas for game
    const canvas = document.createElement('canvas');
    canvas.width = 560;
    canvas.height = 400;
    canvas.style.width = '100%';
    canvas.style.height = 'auto';
    canvas.style.borderRadius = '8px';
    canvas.style.backgroundColor = '#d7c7de'; // Light purple background
    canvas.style.display = 'block';
    gameContainer.appendChild(canvas);
    
    // Create leaderboard
    const leaderboardDiv = document.createElement('div');
    leaderboardDiv.id = 'game-leaderboard';
    leaderboardDiv.style.marginTop = '1rem';
    leaderboardDiv.style.padding = '1rem';
    leaderboardDiv.style.backgroundColor = '#f5f0f8';
    leaderboardDiv.style.borderRadius = '8px';
    leaderboardDiv.style.border = '1px solid #b19acb';
    
    const leaderboardTitle = document.createElement('h3');
    leaderboardTitle.textContent = 'Top Scores';
    leaderboardTitle.style.margin = '0 0 0.5rem 0';
    leaderboardTitle.style.fontSize = '1.1rem';
    leaderboardTitle.style.color = '#4c2a4f';
    leaderboardTitle.style.fontWeight = '400';
    leaderboardDiv.appendChild(leaderboardTitle);
    
    const leaderboardList = document.createElement('div');
    leaderboardList.id = 'leaderboard-list';
    leaderboardList.style.fontSize = '0.9rem';
    leaderboardList.style.color = '#4c2a4f';
    leaderboardDiv.appendChild(leaderboardList);
    
    gameContainer.appendChild(leaderboardDiv);
    
    // Game UI
    const gameUI = document.createElement('div');
    gameUI.style.display = 'flex';
    gameUI.style.justifyContent = 'space-between';
    gameUI.style.alignItems = 'center';
    gameUI.style.marginTop = '1rem';
    gameUI.style.color = '#4c2a4f';
    gameUI.style.fontSize = '1.2rem';
    
    const scoreDiv = document.createElement('div');
    scoreDiv.id = 'game-score';
    scoreDiv.textContent = 'Score: 0';
    gameUI.appendChild(scoreDiv);
    
    const timerDiv = document.createElement('div');
    timerDiv.id = 'game-timer';
    timerDiv.textContent = 'Time: 30';
    gameUI.appendChild(timerDiv);
    
    gameContainer.appendChild(gameUI);
    
    // Instructions (bigger, at top)
    const instructions = document.createElement('div');
    instructions.innerHTML = '<h3 style="font-family: \'Cormorant Garamond\', Georgia, serif; font-size: 1.8rem; font-weight: 400; margin: 0 0 1rem 0; color: #4c2a4f; text-align: center;">How to Play</h3><p style="text-align: center; margin: 0 0 1rem 0; color: #4c2a4f; font-size: 1.3rem; line-height: 1.6;">Use ← → arrow keys or A/D keys to move.<br>Collect as many petals as you can!</p>';
    instructions.style.marginBottom = '1rem';
    gameContainer.insertBefore(instructions, canvas);
    
    // Close button
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'Close';
    closeBtn.style.padding = '0.75rem 2rem';
    closeBtn.style.fontSize = '1rem';
    closeBtn.style.backgroundColor = '#cccccc';
    closeBtn.style.color = '#333333';
    closeBtn.style.border = 'none';
    closeBtn.style.borderRadius = '4px';
    closeBtn.style.cursor = 'pointer';
    closeBtn.style.fontFamily = 'inherit';
    closeBtn.style.fontWeight = 'bold';
    closeBtn.style.marginTop = '1rem';
    closeBtn.style.display = 'block';
    closeBtn.style.margin = '1rem auto 0';
    
    closeBtn.addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    gameContainer.appendChild(closeBtn);
    modal.appendChild(gameContainer);
    document.body.appendChild(modal);
    
    console.log('Modal created and added to DOM');
    
    // Load and display leaderboard
    updateLeaderboard(leaderboardList);
    
    // Start the game
    try {
        startMinigame(canvas, userAvatarUrl, scoreDiv, timerDiv, modal, leaderboardList);
    } catch (error) {
        console.error('Error starting minigame:', error);
        alert('Error starting game: ' + error.message);
    }
}

function updateLeaderboard(leaderboardList) {
    // Get scores from localStorage
    const scores = JSON.parse(localStorage.getItem('minigameScores') || '[]');
    
    // Sort by score (highest first) and get top 3
    const topScores = scores.sort((a, b) => b.score - a.score).slice(0, 3);
    
    if (topScores.length === 0) {
        leaderboardList.innerHTML = '<div style="color: #999; font-style: italic;">No scores yet. Be the first!</div>';
        return;
    }
    
    leaderboardList.innerHTML = topScores.map((entry, index) => {
        const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉';
        return `<div style="margin: 0.25rem 0;">${medal} ${entry.score} points</div>`;
    }).join('');
}

function startMinigame(canvas, avatarUrl, scoreDiv, timerDiv, modal, leaderboardList) {
    const ctx = canvas.getContext('2d');
    
    // Game state
    let score = 0;
    let timeLeft = 30;
    let gameOver = false;
    let gameStarted = false;
    let timerInterval = null;
    
    // Player (2x bigger)
    const player = {
        x: canvas.width / 2 - 50,
        y: canvas.height - 120,
        width: 100, // 2x bigger (was 50)
        height: 100, // 2x bigger (was 50)
        speed: 5,
        avatar: new Image(),
        avatarLoaded: false
    };
    
    player.avatar.crossOrigin = 'anonymous';
    player.avatar.onload = () => {
        player.avatarLoaded = true;
    };
    player.avatar.src = avatarUrl;
    
    // Petals array (dark purple)
    const petals = [];
    const petalColors = ['#4c2a4f', '#5a3a5f', '#6b4a6f', '#7d5a7f', '#8f6a8f']; // Dark purple shades
    
    // Keys
    const keys = {};
    
    // Event listeners
    const keyHandler = (e) => {
        if (e.key === 'ArrowLeft' || e.key === 'ArrowRight' || 
            e.key === 'a' || e.key === 'A' || e.key === 'd' || e.key === 'D') {
            keys[e.key] = e.type === 'keydown';
        }
    };
    
    document.addEventListener('keydown', keyHandler);
    document.addEventListener('keyup', keyHandler);
    
    // Create petal
    function createPetal() {
        petals.push({
            x: Math.random() * (canvas.width - 20) + 10,
            y: -20,
            size: Math.random() * 15 + 10,
            speed: Math.random() * 3 + 2,
            rotation: Math.random() * Math.PI * 2,
            rotationSpeed: (Math.random() - 0.5) * 0.1,
            color: petalColors[Math.floor(Math.random() * petalColors.length)]
        });
    }
    
    // Draw petal
    function drawPetal(petal) {
        ctx.save();
        ctx.translate(petal.x, petal.y);
        ctx.rotate(petal.rotation);
        
        // Draw petal shape (simplified flower petal)
        ctx.fillStyle = petal.color;
        ctx.beginPath();
        ctx.ellipse(0, 0, petal.size / 2, petal.size, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Add highlight (lighter purple for dark purple petals)
        ctx.fillStyle = 'rgba(183, 154, 203, 0.4)'; // Light purple highlight
        ctx.beginPath();
        ctx.ellipse(-petal.size / 6, -petal.size / 4, petal.size / 4, petal.size / 2, 0, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.restore();
    }
    
    // Check collision
    function checkCollision(petal) {
        const playerCenterX = player.x + player.width / 2;
        const playerCenterY = player.y + player.height / 2;
        const distance = Math.sqrt(
            Math.pow(playerCenterX - petal.x, 2) + 
            Math.pow(playerCenterY - petal.y, 2)
        );
        return distance < (player.width / 2 + petal.size / 2);
    }
    
    // Game loop
    function gameLoop() {
        if (gameOver) return;
        
        // Clear canvas (light purple background)
        ctx.fillStyle = '#d7c7de';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Don't update game state until game has started
        if (!gameStarted) {
            requestAnimationFrame(gameLoop);
            return;
        }
        
        // Move player
        if ((keys['ArrowLeft'] || keys['a'] || keys['A']) && player.x > 0) {
            player.x -= player.speed;
        }
        if ((keys['ArrowRight'] || keys['d'] || keys['D']) && player.x < canvas.width - player.width) {
            player.x += player.speed;
        }
        
        // Draw player
        if (player.avatarLoaded) {
            ctx.drawImage(player.avatar, player.x, player.y, player.width, player.height);
        } else {
            // Fallback rectangle
            ctx.fillStyle = '#4c2a4f';
            ctx.fillRect(player.x, player.y, player.width, player.height);
        }
        
        // Update and draw petals
        for (let i = petals.length - 1; i >= 0; i--) {
            const petal = petals[i];
            petal.y += petal.speed;
            petal.rotation += petal.rotationSpeed;
            
            // Check collision
            if (checkCollision(petal)) {
                score++;
                scoreDiv.textContent = `Score: ${score}`;
                petals.splice(i, 1);
                continue;
            }
            
            // Remove if off screen
            if (petal.y > canvas.height) {
                petals.splice(i, 1);
            } else {
                drawPetal(petal);
            }
        }
        
        // Create new petals
        if (Math.random() < 0.15) {
            createPetal();
        }
        
        requestAnimationFrame(gameLoop);
    }
    
    // Start the game loop immediately (but it won't do anything until gameStarted is true)
    gameLoop();
    
    // Countdown before game starts
    let countdown = 10;
    const countdownDiv = document.createElement('div');
    countdownDiv.id = 'game-countdown';
    countdownDiv.style.position = 'absolute';
    countdownDiv.style.top = '50%';
    countdownDiv.style.left = '50%';
    countdownDiv.style.transform = 'translate(-50%, -50%)';
    countdownDiv.style.fontFamily = "'Cormorant Garamond', Georgia, serif";
    countdownDiv.style.fontSize = '4rem';
    countdownDiv.style.fontWeight = 'bold';
    countdownDiv.style.color = '#4c2a4f';
    countdownDiv.style.zIndex = '1000';
    countdownDiv.style.pointerEvents = 'none';
    countdownDiv.textContent = `Game starts in ${countdown}...`;
    canvas.parentElement.style.position = 'relative';
    canvas.parentElement.appendChild(countdownDiv);
    
    const countdownInterval = setInterval(() => {
        countdown--;
        if (countdown > 0) {
            countdownDiv.textContent = `Game starts in ${countdown}...`;
        } else {
            countdownDiv.textContent = 'Go!';
            setTimeout(() => {
                countdownDiv.remove();
                clearInterval(countdownInterval);
            }, 1000);
        }
    }, 1000);
    
    // Timer (starts after countdown)
    setTimeout(() => {
        gameStarted = true;
        timerInterval = setInterval(() => {
            timeLeft--;
            timerDiv.textContent = `Time: ${timeLeft}`;
            
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                gameOver = true;
            
            // Clean up event listeners
            document.removeEventListener('keydown', keyHandler);
            document.removeEventListener('keyup', keyHandler);
            
            // Save score to localStorage
            const scores = JSON.parse(localStorage.getItem('minigameScores') || '[]');
            scores.push({ score: score, date: new Date().toISOString() });
            localStorage.setItem('minigameScores', JSON.stringify(scores));
            
            // Update leaderboard
            if (leaderboardList) {
                updateLeaderboard(leaderboardList);
            }
            
            // Show game over
            ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 36px "Cormorant Garamond", Georgia, serif';
            ctx.textAlign = 'center';
            ctx.fillText('Game Over!', canvas.width / 2, canvas.height / 2 - 40);
            
            ctx.font = '24px "Cormorant Garamond", Georgia, serif';
            ctx.fillText(`Final Score: ${score}`, canvas.width / 2, canvas.height / 2 + 20);
            }
        }, 1000);
    }, 10000); // Start timer after 10 second countdown
    
    // Close modal on outside click
    const closeHandler = (e) => {
        if (e.target === modal) {
            clearInterval(timerInterval);
            document.removeEventListener('keydown', keyHandler);
            document.removeEventListener('keyup', keyHandler);
            document.body.removeChild(modal);
        }
    };
    modal.addEventListener('click', closeHandler);
}

function renderPhoto(selectedSeats, container) {
    container.innerHTML = '';
    container.style.display = 'block';
    
    // Create photo frame with light purple background
    const frame = document.createElement('div');
    frame.style.position = 'relative';
    frame.style.display = 'inline-block';
    frame.style.padding = '3rem 3rem 4rem 3rem'; // Extra bottom padding for flower border
    frame.style.backgroundColor = '#d7c7de'; // Light purple background (matching flower border)
    frame.style.borderRadius = '12px';
    frame.style.boxShadow = '0 4px 20px rgba(0,0,0,0.2)';
    frame.style.maxWidth = '700px';
    frame.style.width = '100%';
    frame.style.margin = '0 auto';
    frame.style.minHeight = '400px';
    
    // Create avatars container - arrange in a line with overlap
    const avatarsDiv = document.createElement('div');
    avatarsDiv.style.display = 'flex';
    avatarsDiv.style.justifyContent = 'center';
    avatarsDiv.style.alignItems = 'flex-end';
    avatarsDiv.style.flexWrap = 'nowrap';
    avatarsDiv.style.marginBottom = '2rem';
    avatarsDiv.style.position = 'relative';
    avatarsDiv.style.zIndex = '2';
    
    // Split guests into left and right of bride/groom
    const guestCount = selectedSeats.length;
    const leftGuests = selectedSeats.slice(0, Math.floor(guestCount / 2));
    const rightGuests = selectedSeats.slice(Math.ceil(guestCount / 2));
    
    // Store all avatar elements to convert to data URLs before download
    const avatarElements = [];
    
    // Add left guests (same size as bride/groom)
    leftGuests.forEach((seat, idx) => {
        const guestImg = createGuestAvatar(seat);
        guestImg.style.width = '120px';
        guestImg.style.height = '120px';
        guestImg.style.marginLeft = idx === 0 ? '0' : '-20px'; // Overlap
        guestImg.style.zIndex = String(10 + idx);
        avatarElements.push(guestImg);
        avatarsDiv.appendChild(guestImg);
    });
    
    // Add bride (left of center)
    const brideImg = document.createElement('img');
    brideImg.src = buildBrideAvatarUrl();
    brideImg.style.width = '120px';
    brideImg.style.height = '120px';
    brideImg.style.objectFit = 'contain';
    brideImg.style.marginLeft = leftGuests.length === 0 ? '0' : '-20px';
    brideImg.style.zIndex = '20';
    avatarElements.push(brideImg);
    avatarsDiv.appendChild(brideImg);
    
    // Add groom (right of bride)
    const groomImg = document.createElement('img');
    groomImg.src = buildGroomAvatarUrl();
    groomImg.style.width = '120px';
    groomImg.style.height = '120px';
    groomImg.style.objectFit = 'contain';
    groomImg.style.marginLeft = '-20px'; // Overlap with bride
    groomImg.style.zIndex = '21';
    avatarElements.push(groomImg);
    avatarsDiv.appendChild(groomImg);
    
    // Add right guests (same size as bride/groom)
    rightGuests.forEach((seat, idx) => {
        const guestImg = createGuestAvatar(seat);
        guestImg.style.width = '120px';
        guestImg.style.height = '120px';
        guestImg.style.marginLeft = '-20px'; // Overlap
        guestImg.style.zIndex = String(22 + idx);
        avatarElements.push(guestImg);
        avatarsDiv.appendChild(guestImg);
    });
    
    // Store avatar elements on frame for download function
    frame.dataset.avatarElements = JSON.stringify(avatarElements.map(img => img.src));
    
    frame.appendChild(avatarsDiv);
    
    // Add flower border at bottom (overlapping with avatar bottoms)
    const flowerBorder = document.createElement('div');
    flowerBorder.style.position = 'absolute';
    flowerBorder.style.bottom = '0';
    flowerBorder.style.left = '0';
    flowerBorder.style.right = '0';
    flowerBorder.style.height = '80px';
    flowerBorder.style.background = '#d7c7de'; // Light lavender/purple for flowers
    flowerBorder.style.borderRadius = '0 0 12px 12px';
    flowerBorder.style.zIndex = '1';
    // Add decorative flower pattern using CSS
    flowerBorder.style.backgroundImage = `
        repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,0.15) 10px, rgba(255,255,255,0.15) 20px),
        repeating-linear-gradient(-45deg, transparent, transparent 10px, rgba(255,255,255,0.1) 10px, rgba(255,255,255,0.1) 20px),
        radial-gradient(circle at 20% 50%, rgba(255,255,255,0.2) 2px, transparent 2px),
        radial-gradient(circle at 80% 50%, rgba(255,255,255,0.2) 2px, transparent 2px),
        radial-gradient(circle at 50% 20%, rgba(255,255,255,0.2) 2px, transparent 2px),
        radial-gradient(circle at 50% 80%, rgba(255,255,255,0.2) 2px, transparent 2px)
    `;
    flowerBorder.style.backgroundSize = '40px 40px, 40px 40px, 20px 20px, 20px 20px, 20px 20px, 20px 20px';
    frame.appendChild(flowerBorder);
    
    // Add message (above flower border)
    const messageDiv = document.createElement('div');
    messageDiv.style.position = 'relative';
    messageDiv.style.zIndex = '3';
    messageDiv.style.paddingTop = '1rem';
    
    const message = document.createElement('p');
    message.textContent = 'Thanks for celebrating our special day!';
    message.style.fontSize = '1.5rem';
    message.style.color = '#ffffff';
    message.style.margin = '0 0 0.5rem 0';
    message.style.fontWeight = '400';
    message.style.textShadow = '0 2px 4px rgba(0,0,0,0.2)';
    messageDiv.appendChild(message);
    
    const signature = document.createElement('p');
    signature.textContent = 'Love, Stephen and Megan';
    signature.style.fontSize = '1.2rem';
    signature.style.color = '#ffffff';
    signature.style.margin = '0';
    signature.style.fontStyle = 'italic';
    signature.style.textShadow = '0 2px 4px rgba(0,0,0,0.2)';
    messageDiv.appendChild(signature);
    
    frame.appendChild(messageDiv);
    
    container.appendChild(frame);
    
    // Add screenshot button (outside the frame so it's not included in the photo)
    const screenshotBtn = document.createElement('button');
    screenshotBtn.textContent = 'Save Picture';
    screenshotBtn.style.marginTop = '1.5rem';
    screenshotBtn.style.padding = '0.75rem 2rem';
    screenshotBtn.style.fontSize = '1rem';
    screenshotBtn.style.backgroundColor = '#4c2a4f';
    screenshotBtn.style.color = '#ffffff';
    screenshotBtn.style.border = 'none';
    screenshotBtn.style.borderRadius = '4px';
    screenshotBtn.style.cursor = 'pointer';
    screenshotBtn.style.fontFamily = 'inherit';
    screenshotBtn.style.fontWeight = 'bold';
    
    screenshotBtn.addEventListener('click', async () => {
        await screenshotPhoto(frame, avatarElements); // Pass frame and avatar elements
    });
    
    container.appendChild(screenshotBtn);
}

// Helper function to convert image URL to data URL for html2canvas
async function imageToDataUrl(url) {
    try {
        const response = await fetch(url);
        const blob = await response.blob();
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    } catch (error) {
        console.error('Error converting image to data URL:', error);
        return url; // Fallback to original URL
    }
}

function createGuestAvatar(seat) {
    const guestImg = document.createElement('img');
    // Use avatar_url from seating data, or generate a default if missing
    if (seat.avatar_url) {
        guestImg.src = seat.avatar_url;
    } else if (seat.config) {
        // Build URL from config if available
        const params = new URLSearchParams();
        params.append("seed", seat.name || "guest");
        params.append("skinColor", seat.config.skin || "edb98a");
        params.append("hairColor", seat.config.hair || "2c1b18");
        params.append("top", seat.config.hairStyle || "shortFlat");
        params.append("clothing", seat.config.clothesType || "collarAndSweater");
        params.append("clothesColor", seat.config.clothesColor || "3c4f5c");
        params.append("eyes", "default");
        params.append("eyebrows", "defaultNatural");
        params.append("mouth", "smile");
        guestImg.src = `https://api.dicebear.com/9.x/avataaars/svg?${params.toString()}`;
    } else {
        // Ultimate fallback
        guestImg.src = `https://api.dicebear.com/9.x/avataaars/svg?seed=${encodeURIComponent(seat.name || 'guest')}`;
    }
    guestImg.style.objectFit = 'contain';
    return guestImg;
}

async function screenshotPhoto(frameElement, avatarElements) {
    const images = frameElement.querySelectorAll('img');
    const totalImages = images.length;
    
    if (totalImages === 0) {
        alert('No photo to screenshot. Please create a photo first.');
        return;
    }
    
    // Show loading message
    const screenshotBtn = frameElement.parentElement.querySelector('button');
    if (screenshotBtn) {
        screenshotBtn.textContent = 'Preparing screenshot...';
        screenshotBtn.disabled = true;
    }
    
    try {
        // Get frame dimensions
        const rect = frameElement.getBoundingClientRect();
        const width = rect.width;
        const height = rect.height;
        const scale = 2; // Higher resolution
        
        // Create canvas
        const canvas = document.createElement('canvas');
        canvas.width = width * scale;
        canvas.height = height * scale;
        const ctx = canvas.getContext('2d');
        
        // Fill background
        ctx.fillStyle = '#d7c7de';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw all images onto canvas
        const imagePromises = Array.from(images).map((img, index) => {
            return new Promise((resolve) => {
                const imgElement = new Image();
                imgElement.crossOrigin = 'anonymous';
                
                imgElement.onload = () => {
                    // Get position of image relative to frame
                    const imgRect = img.getBoundingClientRect();
                    const frameRect = frameElement.getBoundingClientRect();
                    
                    const x = (imgRect.left - frameRect.left) * scale;
                    const y = (imgRect.top - frameRect.top) * scale;
                    const imgWidth = imgRect.width * scale;
                    const imgHeight = imgRect.height * scale;
                    
                    ctx.drawImage(imgElement, x, y, imgWidth, imgHeight);
                    resolve();
                };
                
                imgElement.onerror = () => {
                    console.error('Error loading image:', img.src);
                    resolve(); // Continue even if one fails
                };
                
                // Convert to data URL if needed to avoid CORS
                if (img.src && !img.src.startsWith('data:')) {
                    imageToDataUrl(img.src).then(dataUrl => {
                        imgElement.src = dataUrl;
                    }).catch(() => {
                        imgElement.src = img.src; // Fallback to original
                    });
                } else {
                    imgElement.src = img.src;
                }
            });
        });
        
        // Wait for all images to load and draw
        await Promise.all(imagePromises);
        
        // Draw flower border at bottom first (so text appears on top)
        const flowerBorderHeight = 80 * scale;
        ctx.fillStyle = '#d7c7de';
        ctx.fillRect(0, canvas.height - flowerBorderHeight, canvas.width, flowerBorderHeight);
        
        // Add flower pattern (simplified)
        ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
        for (let i = 0; i < canvas.width; i += 40 * scale) {
            for (let j = canvas.height - flowerBorderHeight; j < canvas.height; j += 40 * scale) {
                ctx.beginPath();
                ctx.arc(i, j, 4 * scale, 0, Math.PI * 2);
                ctx.fill();
            }
        }
        
        // Draw text on top
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        
        // Get text position (center of frame, above flower border)
        // Position text in the lower portion but above the flower border
        const textAreaHeight = (height - (flowerBorderHeight / scale)) * scale;
        const textStartY = textAreaHeight * 0.75; // Start text at 75% down from top (in the lower area)
        
        // First line of text
        ctx.font = `bold ${30 * scale}px 'Cormorant Garamond', Georgia, serif`;
        ctx.fillText('Thanks for celebrating our special day!', canvas.width / 2, textStartY);
        
        // Second line of text (signature) - add more spacing
        ctx.font = `italic ${24 * scale}px 'Cormorant Garamond', Georgia, serif`;
        ctx.fillText('Love, Stephen and Megan', canvas.width / 2, textStartY + (50 * scale));
        ctx.fillStyle = '#d7c7de';
        ctx.fillRect(0, canvas.height - flowerBorderHeight, canvas.width, flowerBorderHeight);
        
        // Add flower pattern (simplified)
        ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
        for (let i = 0; i < canvas.width; i += 40 * scale) {
            for (let j = canvas.height - flowerBorderHeight; j < canvas.height; j += 40 * scale) {
                ctx.beginPath();
                ctx.arc(i, j, 4 * scale, 0, Math.PI * 2);
                ctx.fill();
            }
        }
        
        // Download the canvas as image
        canvas.toBlob((blob) => {
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.download = 'wedding-photo-stephen-megan.png';
            link.href = url;
            link.click();
            URL.revokeObjectURL(url);
            
            // Restore button
            if (screenshotBtn) {
                screenshotBtn.textContent = 'Save Picture';
                screenshotBtn.disabled = false;
            }
        }, 'image/png');
        
    } catch (error) {
        console.error('Error creating screenshot:', error);
        alert('There was an error creating the screenshot. Please try again.');
        
        // Restore button
        if (screenshotBtn) {
            screenshotBtn.textContent = 'Save Picture';
            screenshotBtn.disabled = false;
        }
    }
}

document.addEventListener("DOMContentLoaded", initializeScene);
