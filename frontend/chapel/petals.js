import * as THREE from "three";
import { colors } from "./constants.js";

/**
 * Creates floating rose petals in the chapel scene
 * @param {THREE.Scene} scene - The Three.js scene to add petals to
 * @returns {Function} An animation function to update petals each frame
 */
export function addFloatingPetals(scene) {
    const petalGroup = new THREE.Group();
    const petalCount = 30;
    const petals = [];

    // Create petal geometry - simple flat plane
    const petalGeometry = new THREE.PlaneGeometry(0.15, 0.2, 1, 1);
    
    // Create petal material - rose/pink color with transparency
    const petalMaterial = new THREE.MeshBasicMaterial({
        color: 0xf3c0c6, // Rosewater color
        transparent: true,
        opacity: 0.7,
        side: THREE.DoubleSide,
    });

    // Create individual petal meshes
    for (let i = 0; i < petalCount; i++) {
        const petal = new THREE.Mesh(petalGeometry, petalMaterial.clone());
        
        // Random starting position in the chapel space
        petal.position.set(
            (Math.random() - 0.5) * 30, // x: -15 to 15
            Math.random() * 15 + 5,      // y: 5 to 20
            (Math.random() - 0.5) * 50 - 10  // z: -35 to 15 (pews to stage)
        );
        
        // Random rotation
        petal.rotation.set(
            Math.random() * Math.PI,
            Math.random() * Math.PI,
            Math.random() * Math.PI
        );
        
        // Store animation properties
        const petalData = {
            mesh: petal,
            velocity: new THREE.Vector3(
                (Math.random() - 0.5) * 0.02, // x drift
                -0.01 - Math.random() * 0.02,  // y fall
                (Math.random() - 0.5) * 0.02   // z drift
            ),
            rotationSpeed: new THREE.Vector3(
                (Math.random() - 0.5) * 0.02,
                (Math.random() - 0.5) * 0.02,
                (Math.random() - 0.5) * 0.02
            ),
            startY: petal.position.y,
        };
        
        petals.push(petalData);
        petalGroup.add(petal);
    }

    scene.add(petalGroup);

    // Return animation function
    return function animatePetals() {
        petals.forEach((petalData) => {
            const { mesh, velocity, rotationSpeed, startY } = petalData;
            
            // Update position
            mesh.position.add(velocity);
            
            // Reset position if it falls too low or drifts too far
            if (mesh.position.y < 0) {
                mesh.position.y = startY;
                mesh.position.x = (Math.random() - 0.5) * 30;
                mesh.position.z = (Math.random() - 0.5) * 50 - 10;
            }
            
            // Keep petals within bounds
            if (Math.abs(mesh.position.x) > 20) {
                velocity.x *= -1;
            }
            if (Math.abs(mesh.position.z) > 30) {
                velocity.z *= -1;
            }
            
            // Rotate petals
            mesh.rotation.x += rotationSpeed.x;
            mesh.rotation.y += rotationSpeed.y;
            mesh.rotation.z += rotationSpeed.z;
        });
    };
}
