const { addMatchImageSnapshotCommand } = require("cypress-image-snapshot/command");

addMatchImageSnapshotCommand({
    failureThreshold: 0.7,
    failureThresholdType: "percent",
    customDiffConfig: { threshold: 0.2 },
});
