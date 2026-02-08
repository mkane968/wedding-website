import * as THREE from "three";
import { create3DAvatar } from "./chapel/avatars.js";

/**
 * Render a 3D avatar preview in the given container
 */
function renderAvatarPreview(containerElement, config = {}) {
    // Clear container
    containerElement.innerHTML = '';
    
    const width = 240;
    const height = 240;
    
    // Create scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf7f1ee);
    
    // Create camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 1, 3);
    camera.lookAt(0, 0.6, 0);
    
    // Create renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    containerElement.appendChild(renderer.domElement);
    
    // Add lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.6);
    directionalLight.position.set(5, 10, 5);
    scene.add(directionalLight);
    
    // Create and add avatar
    const avatar = create3DAvatar(config);
    avatar.position.set(0, 0, 0);
    scene.add(avatar);
    
    // Add rotation animation
    function animate() {
        requestAnimationFrame(animate);
        avatar.rotation.y += 0.005; // Slow rotation
        renderer.render(scene, camera);
    }
    animate();
    
    // Return cleanup function
    return () => {
        renderer.dispose();
        scene.clear();
    };
}

// Export for IIFE bundle - set window.AvatarPreview directly
if (typeof window !== 'undefined') {
    window.AvatarPreview = {
        renderAvatarPreview: renderAvatarPreview
    };
}

