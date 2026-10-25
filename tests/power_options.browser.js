// Run with a boardless server: playwright-cli -s=power-options run-code --filename=tests/power_options.browser.js
async page => {
    const origin = "http://127.0.0.1:5000";
    const results = [];
    const check = (condition, message) => { if (!condition) throw new Error(message); };
    const dialog = page.locator("#power-options-dialog"), panel = page.locator("#power-options-panel"), trigger = page.locator("#kiosk-exit-button");
    const open = async () => { await trigger.click(); await dialog.waitFor({ state: "visible" }); };
    const hidden = () => dialog.waitFor({ state: "hidden" });
    const pattern = /\/(shutdown|kiosk\/exit)$/;
    let destructiveRequests = 0;
    await page.route(pattern, async route => { destructiveRequests++; await route.abort(); });
    await page.goto(origin + "/#power-options");
    await page.reload();
    await dialog.waitFor({ state: "visible" });
    await page.evaluate(() => document.fonts.ready);
    check(await page.locator("#power-cancel").evaluate(el => el === document.activeElement), "Cancel initial focus");
    check(await dialog.getAttribute("aria-labelledby") === "power-options-description", "Accessible dialog name");
    check(await page.locator("#power-options-description").textContent() === "Are you sure you want to exit?", "Confirmation wording");
    check(await dialog.locator("h1, #power-options-status").count() === 0, "Heading or status remains");
    await page.keyboard.press("Shift+Tab");
    check(await page.locator("#power-shutdown").evaluate(el => el === document.activeElement), "Reverse focus wrap");
    await page.keyboard.press("Tab");
    const focusStyle = await page.locator("#power-cancel").evaluate(el => ({ outline: getComputedStyle(el).outlineStyle, decoration: getComputedStyle(el).textDecorationLine }));
    check(focusStyle.outline === "none" && focusStyle.decoration === "none", "Unexpected focus border or underline");
    for (let i = 0; i < 7; i++) {
        await page.keyboard.press("Tab");
        check(await dialog.evaluate(el => el.contains(document.activeElement)), "Focus escaped dialog");
    }
    await page.locator("#power-options-description").click();
    check(await dialog.isVisible(), "Inside click dismissed dialog");
    await page.locator("#power-cancel").click(); await hidden();
    check(await trigger.evaluate(el => el === document.activeElement), "Trigger focus not restored");
    await trigger.press("Enter"); await dialog.waitFor({ state: "visible" });
    await page.keyboard.press("Escape"); await hidden();
    await trigger.press("Space"); await dialog.waitFor({ state: "visible" });
    await page.mouse.click(2, 2); await hidden(); await open();
    const bounds = await panel.boundingBox();
    await page.mouse.move(bounds.x + 10, bounds.y + 10); await page.mouse.down();
    await page.mouse.move(2, 2); await page.mouse.up();
    check(await dialog.isVisible(), "Drag out dismissed dialog");
    results.push("safe dismissal, keyboard activation, focus containment/restoration, no focus border or underline");

    for (const scale of ["wide-browser", "boardless", "800x480"]) {
        if (scale === "wide-browser") await page.setViewportSize({ width: 1600, height: 1000 });
        else if (scale === "boardless") await page.setViewportSize(await page.evaluate(() => ({ width: Math.ceil(document.body.getBoundingClientRect().width), height: Math.ceil(document.body.getBoundingClientRect().height) })));
        else {
            await page.setViewportSize({ width: 800, height: 480 });
            await page.addStyleTag({ content: 'html[data-boardless-mode="true"] { font-size: 16px !important; }' });
        }
        const layout = await page.evaluate(() => {
            const box = id => document.getElementById(id).getBoundingClientRect().toJSON();
            const panel = document.getElementById("power-options-panel");
            return {
                screen: box("app-screen"), overlay: box("power-options-dialog"), panel: box("power-options-panel"),
                promptAlign: getComputedStyle(document.getElementById("power-options-description")).textAlign,
                fills: ["power-cancel", "power-exit", "power-shutdown"].map(id => getComputedStyle(document.getElementById(id)).backgroundColor),
                colors: ["power-cancel", "power-exit", "power-shutdown"].map(id => getComputedStyle(document.getElementById(id)).color),
                overflow: panel.scrollHeight > panel.clientHeight,
                root: getComputedStyle(document.documentElement).fontSize,
                parent: panel.closest("#app-screen") !== null,
            };
        });
        for (const key of ["x", "y", "width", "height"]) check(Math.abs(layout.screen[key] - layout.overlay[key]) < 1, "Overlay outside app: " + key);
        check(Math.abs(layout.panel.x + layout.panel.width / 2 - (layout.screen.x + layout.screen.width / 2)) < 1, "Panel not centered horizontally");
        check(Math.abs(layout.panel.y + layout.panel.height / 2 - (layout.screen.y + layout.screen.height / 2)) < 1, "Panel not centered vertically");
        check(layout.parent && !layout.overflow && layout.promptAlign === "center", "Panel structure/text layout");
        check(layout.fills.join() === "rgb(239, 230, 212),rgb(239, 230, 212),rgb(154, 46, 31)", "Incorrect fills");
        check(layout.colors.join() === "rgb(26, 20, 16),rgb(154, 46, 31),rgb(239, 230, 212)", "Incorrect text colors");
        results.push({ scale, root: layout.root, app: [layout.screen.width, layout.screen.height], panel: [layout.panel.width, layout.panel.height] });
    }
    for (const action of ["exit", "shutdown"]) {
        if (!await dialog.isVisible()) await open();
        await page.locator("#power-" + action).click(); await hidden();
        check(await trigger.evaluate(el => el === document.activeElement), "Action did not restore focus");
    }
    check(destructiveRequests === 0, "Boardless action sent request");
    results.push("both boardless actions close immediately without text or destructive requests");

    await open();
    await page.evaluate(() => document.documentElement.removeAttribute("data-boardless-mode"));
    await page.unroute(pattern);
    const requests = [];
    await page.route(pattern, route => { requests.push(route); });
    const waitRequests = async count => {
        for (let i = 0; i < 100 && requests.length < count; i++) await new Promise(resolve => setTimeout(resolve, 10));
        check(requests.length === count, "Unexpected request count");
    };
    await page.locator("#power-shutdown").click(); await hidden(); await waitRequests(1);
    await trigger.click();
    await page.evaluate(() => { submitPowerAction("exit"); submitPowerAction("shutdown"); });
    check(await dialog.isHidden() && requests.length === 1, "Pending action reopened or duplicated");
    check(requests[0].request().url().endsWith("/shutdown"), "Shutdown endpoint changed");
    await requests[0].fulfill({ status: 403, contentType: "application/json", body: '{"error":"Mock shutdown disabled"}' });
    await page.waitForFunction(() => !powerActionPending);
    check(await dialog.isHidden(), "Failure reopened modal");
    await open(); await page.locator("#power-exit").click(); await waitRequests(2);
    check(requests[1].request().url().endsWith("/kiosk/exit"), "Exit endpoint changed");
    await requests[1].abort("connectionreset");
    await page.waitForFunction(() => !powerActionPending);
    check(await dialog.isHidden() && requests.length === 2, "Connection loss reopened or retried");
    await open(); await page.locator("#power-exit").click(); await waitRequests(3);
    await requests[2].fulfill({ status: 200, contentType: "application/json", body: '{"success":true}' });
    check(await dialog.isHidden(), "Accepted action reopened modal");
    results.push("mocked actions close immediately, duplicates blocked, failures stay closed, no automatic retries");

    await page.goto(origin + "/#play"); await page.reload();
    await page.waitForFunction(() => state.mode === "play");
    await page.clock.install();
    await page.clock.pauseAt(await page.evaluate(() => Date.now() + 1000));
    await page.evaluate(() => {
        state.records = [{ id: "preview", artist: "Preview artist", title: "Preview album", sides: [{ id: "A", tracks: [{ title: "Preview song" }] }] }];
        state.currentRecordId = "preview"; state.currentSideIndex = 0; state.currentTrackIndex = 0;
        screensaverPlayStartedAt = Date.now(); screensaverLastInteractionAt = Date.now(); scheduleScreensaverActivation();
    });
    await open(); await page.clock.fastForward(12000);
    await page.evaluate(() => renderScreensaver());
    check(await page.locator("#play-screensaver").isHidden(), "Screensaver opened over modal");
    await page.locator("#power-exit").click(); await hidden(); await page.clock.fastForward(9999);
    check(await page.locator("#play-screensaver").isHidden(), "Screensaver resumed early");
    await page.clock.fastForward(1);
    check(await page.locator("#play-screensaver").isVisible(), "Screensaver failed to resume");
    await page.clock.resume();
    results.push("screensaver suspended while open, fresh ten seconds after action dismissal");

    const touchContext = await page.context().browser().newContext({ viewport: { width: 800, height: 480 }, hasTouch: true });
    const touchPage = await touchContext.newPage();
    let touchRequests = 0;
    await touchPage.route(pattern, async route => { touchRequests++; await route.abort(); });
    await touchPage.goto(origin);
    for (const action of ["exit", "shutdown", "cancel"]) {
        await touchPage.locator("#kiosk-exit-button").tap(); await touchPage.locator("#power-" + action).tap();
        await touchPage.locator("#power-options-dialog").waitFor({ state: "hidden" });
    }
    check(touchRequests === 0, "Touch preview sent destructive requests");
    await touchContext.close();
    results.push("touch trigger and all three dismissals, zero destructive requests");
    await page.goto(origin + "/#power-options"); await page.reload();
    await dialog.waitFor({ state: "visible" });
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.addStyleTag({ content: 'html[data-boardless-mode="true"] { font-size: 16px !important; }' });
    await page.evaluate(() => document.fonts.ready); await page.bringToFront();
    return { passed: results, finalPreview: page.url(), destructiveRequestsForwarded: 0 };
}
