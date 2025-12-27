import { seatsPerRow } from "./constants.js";

export function loadSeating() {
    const dataEl = document.getElementById("chapel-seating-data");
    if (!dataEl) {
        return [];
    }
    try {
        return JSON.parse(dataEl.textContent) || [];
    } catch (err) {
        console.error("Unable to parse seating chart data", err);
        return [];
    }
}

export function seatPosition(rowIndex, seatIndex) {
    const rowSpacing = 3.5;
    const seatSpacing = 2.4;
    const z = -rowIndex * rowSpacing;
    const x = (seatIndex - (seatsPerRow - 1) / 2) * seatSpacing;
    return { x, z };
}
