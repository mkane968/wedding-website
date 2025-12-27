const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
    testDir: "tests/playwright",
    timeout: 60000,
    use: {
        baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:8000",
        viewport: { width: 1280, height: 720 },
        browserName: "chromium",
    },
});
