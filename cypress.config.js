const { defineConfig } = require("cypress");
const { addMatchImageSnapshotPlugin } = require("cypress-image-snapshot/plugin");

module.exports = defineConfig({
    screenshotsFolder: "cypress/snapshots/actual",
    videosFolder: "cypress/videos",
    trashAssetsBeforeRuns: false,
    e2e: {
        baseUrl: process.env.CYPRESS_BASE_URL || "http://127.0.0.1:8000",
        viewportWidth: 1280,
        viewportHeight: 720,
        setupNodeEvents(on, config) {
            addMatchImageSnapshotPlugin(on, config);
        },
    },
});
