// Run with playwright-cli run-code against a disposable boardless server with
// at least two saved styli. This exercises real activation and /events routes.
async page => {
    const origin = await page.evaluate(() => location.origin);
    const check = (condition, message) => { if (!condition) throw new Error(message); };
    const errors = [];
    page.on("pageerror", error => errors.push(error.message));
    const status = async value => {
        const result = await page.request.post(origin + "/events", { data: { event: "status", data: { status: value, time: "00:00" } } });
        check(result.ok(), "Could not publish status");
        await page.waitForFunction(value => state.playbackStatus === value, value);
    };
    const selected = () => page.evaluate(() => getActiveStylus().id);
    const bars = () => page.evaluate(() => ({
        compact: document.getElementById("stylus-bar-compact-fill").style.width,
        full: document.getElementById("stylus-bar-full-fill").style.width,
        compactColor: document.getElementById("stylus-bar-compact-fill").style.background,
        fullColor: document.getElementById("stylus-bar-full-fill").style.background,
    }));
    await page.unrouteAll();
    await page.goto(origin + "/#stylus");
    await page.reload();
    await page.waitForFunction(() => state.styli.length >= 2 && state.playbackStatus !== null);
    await page.evaluate(() => document.fonts.ready);
    await status("stop");
    const initialId = await selected();
    const ids = await page.evaluate(() => state.styli.map(s => s.id));
    const checks = [];
    try {
        for (let i = 0; i < ids.length; i++) {
            const before = await selected();
            const target = ids[(ids.indexOf(before) + 1) % ids.length];
            await page.locator("#btn-next-stylus").click();
            await page.waitForFunction(id => !state.stylusActivationPending && getActiveStylus().id === id, target);
            const wear = await bars();
            check(wear.compact === wear.full && wear.compactColor === wear.fullColor, "Wear bars disagree");
            const saved = await (await page.request.get(origin + "/styli")).json();
            check(saved.find(s => s.active).id === target, "Navigation did not persist");
        }
        await page.reload();
        await page.waitForFunction(id => state.styli.length && getActiveStylus().id === id, initialId);
        checks.push("persisted navigation, wraparound, both bars, and reload");

        await status("play");
        for (const hash of ["#sync", "#stylus", "#play", "#stylus"]) {
            await page.goto(origin + "/" + hash);
            await page.waitForFunction(() => state.playbackStatus === "play");
            check(await page.locator("#btn-next-stylus").isDisabled(), "Playback guard lost through hash");
        }
        const rejected = await page.request.post(origin + `/styli/${ids.find(id => id !== initialId)}/activate`);
        check(rejected.status() === 409, "Backend did not guard direct activation");
        check(await selected() === initialId, "Rejected activation changed selection");
        await status("stop");
        check(await page.locator("#btn-next-stylus").isEnabled(), "Navigation did not recover after stop");
        checks.push("backend playback guard through modes/hashes and direct requests");

        let held;
        const activationPattern = /\/styli\/[^/]+\/activate$/;
        await page.route(activationPattern, route => { held = route; });
        await page.locator("#btn-next-stylus").click();
        await page.waitForFunction(() => state.stylusActivationPending);
        for (const id of ["btn-prev-stylus", "btn-next-stylus", "btn-reset-stylus"]) {
            check(await page.locator("#" + id).isDisabled(), "Pending control enabled: " + id);
        }
        check(await selected() === initialId, "Optimistic selection changed before response");
        await held.fulfill({ status: 500, contentType: "application/json", body: '{"error":"save refused"}' });
        await page.waitForFunction(() => !state.stylusActivationPending);
        check(await page.getByRole("alert").isVisible(), "Error is not accessible/visible");
        check(await page.getByRole("alert").textContent() === "An error occurred!", "Error message changed");
        for (const id of ["stylus-mode-name", "stylus-mode-hours", "stylus-bar-full", "stylus-empty", "btn-reset-stylus"]) {
            await page.locator("#" + id).waitFor({ state: "hidden" });
        }
        check(await page.locator("#btn-prev-stylus").isEnabled() && await page.locator("#btn-next-stylus").isEnabled(), "Navigation cannot retry");
        check(await page.locator("#btn-retry-stylus, #stylus-selection-feedback").count() === 0, "Old retry/banner remains");
        check(await selected() === initialId, "Failed activation changed selection");
        checks.push("pending controls and empty-style generic error with Prev/Next retry");

        const layouts = [];
        for (const [width, height] of [[800, 480], [1280, 800], [420, 252]]) {
            await page.setViewportSize({ width, height });
            await page.evaluate(([width]) => {
                document.documentElement.style.fontSize = (Math.min(width, 800) / 50) + "px";
            }, [width]);
            layouts.push(await page.evaluate(() => {
                const screen = document.getElementById("app-screen").getBoundingClientRect();
                const alert = document.getElementById("stylus-error").getBoundingClientRect();
                const box = document.getElementById("mode-stylus").getBoundingClientRect();
                const action = document.getElementById("action-bar").getBoundingClientRect();
                return {
                    width: screen.width, height: screen.height,
                    fits: alert.left >= box.left && alert.right <= box.right && alert.bottom <= action.top,
                    centered: Math.abs((alert.left + alert.right) / 2 - (box.left + box.right) / 2) < 1,
                };
            }));
            check(layouts.at(-1).fits && layouts.at(-1).centered, "Error does not fit the empty-state layout");
        }
        await page.setViewportSize({ width: 800, height: 480 });
        await page.evaluate(() => { document.documentElement.style.fontSize = "16px"; });
        await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        await page.screenshot({ path: "/private/tmp/now-spinning-selection-error.png", animations: "disabled" });

        await page.unroute(activationPattern);
        await page.route(activationPattern, async route => {
            await route.fetch(); // Commit, then lose the acknowledgement.
            await route.abort("connectionreset");
        });
        const nextId = ids[(ids.indexOf(initialId) + 1) % ids.length];
        await page.locator("#btn-next-stylus").click();
        await page.waitForFunction(id => !state.stylusActivationPending && getActiveStylus().id === id, nextId);
        check(!await page.locator("#btn-next-stylus").isDisabled(), "Recovered selection still guarded");
        check(await page.getByRole("alert").isVisible(), "Unconfirmed request should show generic error");
        await page.unroute(activationPattern);
        await page.locator("#btn-prev-stylus").click();
        await page.waitForFunction(id => !state.stylusActivationPending && !state.stylusError && getActiveStylus().id === id, initialId);
        check((await bars()).compact === (await bars()).full, "Retried bars differ");
        checks.push("lost acknowledgement refreshes saved selection and Prev retries successfully");

        let loseNextResponse = true;
        await page.route(activationPattern, async route => {
            if (!loseNextResponse) return route.continue();
            loseNextResponse = false;
            await route.fetch();
            await route.abort("connectionreset");
        });
        let failNextRead = true;
        await page.route(/\/styli$/, route => {
            if (!failNextRead) return route.continue();
            failNextRead = false;
            return route.abort("connectionreset");
        });
        await page.locator("#btn-next-stylus").click();
        await page.waitForFunction(() => !state.stylusActivationPending && state.stylusSelectionUnconfirmed);
        check(await page.getByRole("alert").isVisible(), "Failed recovery should show generic error");
        check(await page.locator("#btn-prev-stylus").isEnabled(), "Failed recovery cannot be retried");
        await page.locator("#btn-prev-stylus").click();
        await page.waitForFunction(id => !state.stylusActivationPending && !state.stylusError && getActiveStylus().id === id, initialId);
        check((await bars()).compact === (await bars()).full, "Bars differ after recovery and retry");
        checks.push("failed recovery is reloaded and navigated with one Prev click");
        await page.unrouteAll();
        await page.route(activationPattern, route => route.fulfill({ status: 500, contentType: "application/json", body: '{"error":"preview failure"}' }));
        await page.locator("#btn-next-stylus").click();
        await page.waitForFunction(() => state.stylusError && !state.stylusActivationPending);
        await page.bringToFront();
        check(errors.length === 0, "Browser errors: " + errors.join(", "));
        return { passed: checks, layouts, pageErrors: errors };
    } finally {
        await page.unroute(/\/styli\/[^/]+\/activate$/);
        await page.request.post(origin + "/events", { data: { event: "status", data: { status: "stop" } } });
        await page.request.post(origin + `/styli/${initialId}/activate`);
    }
}
