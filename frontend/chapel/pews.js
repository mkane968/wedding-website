import * as THREE from "three";
import { colors, seatsPerRow, layout } from "./constants.js";

const seatsPerSide = Math.ceil(seatsPerRow / 2);
const seatSpacing = layout.seatSpacing;
const rowSpacing = layout.rowSpacing;
const rowOffset = layout.rowOffset || 0;
const sideCenterOffset =
    layout.aisleHalfWidth + layout.aisleGap + ((seatsPerSide - 1) * seatSpacing) / 2;

export function buildPews(scene, totalRows) {
    const pewDepth = 0.6;
    const pewHeight = 0.55;
    const pewWidth = seatsPerSide * seatSpacing;
    const frameMaterial = new THREE.MeshStandardMaterial({
        color: colors.pewFrame,
        roughness: 0.4,
        metalness: 0.05,
    });
    const cushionMaterial = new THREE.MeshStandardMaterial({
        color: colors.pewCushion,
        roughness: 0.2,
    });
    for (let row = 0; row <= totalRows; row += 1) {
        ["left", "right"].forEach((sideSign) => {
            const baseGeometry = new THREE.BoxGeometry(pewWidth, pewHeight, pewDepth);
            const base = new THREE.Mesh(baseGeometry, frameMaterial);
            const cushionGeometry = new THREE.BoxGeometry(pewWidth - 0.4, 0.2, pewDepth - 0.1);
            const cushion = new THREE.Mesh(cushionGeometry, cushionMaterial);
            const z = -(row + rowOffset) * rowSpacing - 1;
            const xCenter = (sideSign === "left" ? -1 : 1) * sideCenterOffset;
            base.position.set(xCenter, pewHeight / 2, z);
            cushion.position.set(xCenter, pewHeight + 0.05, z);
            scene.add(base);
            scene.add(cushion);
        });
    }
}
