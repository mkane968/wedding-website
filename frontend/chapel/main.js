import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

import { colors, seatsPerRow } from "./constants.js";
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

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 200);
    camera.position.set(0, 10, -28);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 2, 5);
    controls.enableDamping = true;

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
    buildPews(scene, Math.max(6, Math.ceil(seating.length / seatsPerRow)));
    addAvatars(scene, seating);
    addBrideAndGroom(scene);
    const animatePetals = addFloatingPetals(scene);

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
    }
    animate();
}

document.addEventListener("DOMContentLoaded", initializeScene);
