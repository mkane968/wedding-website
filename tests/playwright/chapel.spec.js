const { test, expect } = require("@playwright/test");
const fs = require("fs");
const path = require("path");
const pixelmatchModule = require("pixelmatch");
const pixelmatch = pixelmatchModule.default || pixelmatchModule;
const { PNG } = require("pngjs");

test.describe("Chapel visual regression", () => {
    const referencePath = path.resolve(__dirname, "../reference/chapel-reference.png");
    const captureDir = path.resolve(__dirname, "../../assets/playwright-captures");
    const actualPath = path.join(captureDir, "chapel-latest.png");
    const diffPath = path.join(captureDir, "chapel-diff.png");

    test.beforeAll(() => {
        if (!fs.existsSync(referencePath)) {
            throw new Error(
                `Missing reference image at ${referencePath}. Convert IMG_8663.jpg to 1280x720 PNG before running tests.`
            );
        }
        fs.mkdirSync(captureDir, { recursive: true });
    });

    test("matches sanctuary reference silhouette", async ({ page }) => {
        await page.setViewportSize({ width: 1280, height: 720 });
        await page.goto("/chapel/");
        await page.waitForTimeout(3000);
        const screenshotBuffer = await page.screenshot({
            clip: { x: 0, y: 0, width: 1280, height: 720 },
        });

        fs.writeFileSync(actualPath, screenshotBuffer);
        const screenshot = PNG.sync.read(screenshotBuffer);
        const reference = PNG.sync.read(fs.readFileSync(referencePath));

        if (screenshot.width !== reference.width || screenshot.height !== reference.height) {
            throw new Error(
                `Screenshot dimensions ${screenshot.width}x${screenshot.height} do not match reference ${reference.width}x${reference.height}`
            );
        }

        const diff = new PNG({ width: reference.width, height: reference.height });
        const diffPixels = pixelmatch(
            reference.data,
            screenshot.data,
            diff.data,
            reference.width,
            reference.height,
            { threshold: 0.2 }
        );
        fs.writeFileSync(diffPath, PNG.sync.write(diff));

        const totalPixels = reference.width * reference.height;
        const diffRatio = diffPixels / totalPixels;
        expect(
            diffRatio,
            `Chapel render diverges too far from photo reference (difference ratio: ${diffRatio.toFixed(2)})`
        ).toBeLessThan(0.95);
    });
});
