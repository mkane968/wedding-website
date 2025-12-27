import * as THREE from "three";
import { colors, layout } from "./constants.js";

export function addEnvironment(scene) {
    const floorGeometry = new THREE.PlaneGeometry(60, 80);
    const floorMaterial = new THREE.MeshStandardMaterial({
        color: colors.warmWood,
        roughness: 0.6,
        metalness: 0.1,
    });
    const floor = new THREE.Mesh(floorGeometry, floorMaterial);
    floor.rotation.x = -Math.PI / 2;
    scene.add(floor);

    const aisleGeometry = new THREE.PlaneGeometry(layout.aisleHalfWidth * 2, 70);
    const aisleMaterial = new THREE.MeshStandardMaterial({
        color: colors.lavender,
        transparent: true,
        opacity: 0.45,
    });
    const aisle = new THREE.Mesh(aisleGeometry, aisleMaterial);
    aisle.rotation.x = -Math.PI / 2;
    aisle.position.set(0, 0.01, -15);
    scene.add(aisle);

    const runnerGeometry = new THREE.PlaneGeometry(layout.aisleHalfWidth * 1.4, 70);
    const runnerMaterial = new THREE.MeshStandardMaterial({
        color: 0xffffff,
        roughness: 0.3,
    });
    const runner = new THREE.Mesh(runnerGeometry, runnerMaterial);
    runner.rotation.x = -Math.PI / 2;
    runner.position.set(0, 0.02, -15);
    scene.add(runner);

    const stageGeometry = new THREE.BoxGeometry(22, 0.8, 16);
    const stageMaterial = new THREE.MeshStandardMaterial({ color: colors.stageWood, roughness: 0.5 });
    const stage = new THREE.Mesh(stageGeometry, stageMaterial);
    stage.position.set(0, 0.4, 6);
    scene.add(stage);

    const choirRiserGeometry = new THREE.BoxGeometry(22, 3, 4);
    const choirRiser = new THREE.Mesh(choirRiserGeometry, stageMaterial);
    choirRiser.position.set(0, 2.2, 11);
    scene.add(choirRiser);
}

export function addTrusses(scene) {
    const trussMaterial = new THREE.MeshStandardMaterial({
        color: colors.warmWood,
        roughness: 0.6,
    });
    const span = 30;
    for (let i = -15; i <= 10; i += 10) {
        const torus = new THREE.Mesh(new THREE.TorusGeometry(span, 0.6, 12, 80, Math.PI), trussMaterial);
        torus.rotation.z = Math.PI / 2;
        torus.position.set(0, 8.5, i);
        scene.add(torus);
    }
}

export function addWindows(scene) {
    const windowMaterial = new THREE.MeshBasicMaterial({
        color: 0xffffff,
        opacity: 0.85,
        transparent: true,
    });
    const frameMaterial = new THREE.MeshStandardMaterial({ color: 0xf4f4f4 });
    for (let i = -25; i <= 10; i += 7) {
        const panel = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 5.5), windowMaterial);
        panel.position.set(-12.8, 3.5, i);
        scene.add(panel);
        const frame = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 6), frameMaterial);
        frame.position.set(-13, 3.3, i - 0.1);
        scene.add(frame);

        const panel2 = panel.clone();
        panel2.position.set(12.8, 3.5, i);
        scene.add(panel2);
        const frame2 = frame.clone();
        frame2.position.set(13, 3.3, i - 0.1);
        scene.add(frame2);
    }
}

export function addOrgan(scene) {
    const organGroup = new THREE.Group();
    const casingMaterial = new THREE.MeshStandardMaterial({ color: colors.stageWood, roughness: 0.5 });
    const base = new THREE.Mesh(new THREE.BoxGeometry(22, 3.5, 1), casingMaterial);
    base.position.set(0, 3, 13);
    organGroup.add(base);

    const tiers = [
        { x: 0, height: 7.5, count: 4 },
        { x: -4, height: 6.5, count: 3 },
        { x: 4, height: 6.5, count: 3 },
        { x: -7, height: 5.5, count: 3 },
        { x: 7, height: 5.5, count: 3 },
        { x: -10, height: 4.5, count: 2 },
        { x: 10, height: 4.5, count: 2 },
    ];

    tiers.forEach(({ x, height, count }) => {
        for (let i = 0; i < count; i += 1) {
            const offset = (i - (count - 1) / 2) * 0.45;
            const pipe = new THREE.Mesh(
                new THREE.CylinderGeometry(0.15, 0.15, height, 16),
                new THREE.MeshStandardMaterial({ color: colors.pipeMetal, metalness: 0.9, roughness: 0.2 })
            );
            pipe.position.set(x + offset, 3 + height / 2, 13.3);
            organGroup.add(pipe);
        }
    });

    scene.add(organGroup);
}

export function addPulpit(scene) {
    const podiumMaterial = new THREE.MeshStandardMaterial({
        color: 0xf8f3eb,
        roughness: 0.4,
    });
    const podium = new THREE.Mesh(new THREE.BoxGeometry(2.6, 4.8, 1.2), podiumMaterial);
    podium.position.set(0, 2.4, 4.2);
    scene.add(podium);

    const top = new THREE.Mesh(
        new THREE.BoxGeometry(2.8, 0.15, 1.4),
        new THREE.MeshStandardMaterial({ color: colors.stageWood, roughness: 0.3 })
    );
    top.position.set(0, 4.1, 4.2);
    scene.add(top);

    const crossMaterial = new THREE.MeshStandardMaterial({ color: 0xd9b24c, metalness: 0.6, roughness: 0.3 });
    const vertical = new THREE.Mesh(new THREE.BoxGeometry(0.12, 3.4, 0.06), crossMaterial);
    vertical.position.set(0, 2.6, 3.95);
    const horizontal = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.12, 0.06), crossMaterial);
    horizontal.position.set(0, 3.4, 3.95);
    scene.add(vertical);
    scene.add(horizontal);
}
