// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

var state = {
    mode: "standby",
    records: [],
    styli: [],
    currentRecordId: null,
    currentTrackIndex: 0,
    currentSideIndex: 0,
    linkRecordIndex: 0,
    reLinkRecordIndex: 0,
    stylusIndex: 0,
    stylusHours: {},
    temperature: null,
    linkError: false,
    standbyError: "not-found", // null | "nfc" | "not-found"
    standbyRecordVisible: false,
};

var lastRendered = {
    topBar: null,
    visibility: null,
    section: null,
};

// ---------------------------------------------------------------------------
// Mode switching
// ---------------------------------------------------------------------------

var MODES = ["standby", "play", "link", "re-link", "stylus", "sync"];

// Mode button cycle order (play is not reachable via button)
var MODE_BUTTON_CYCLE = ["standby", "sync", "link", "re-link", "stylus"];

function nextMode() {
    // Map error sub-states to their parent mode for cycle lookup
    var current = state.mode;
    if (current === "play") {
        state.mode = "standby";
    } else {
        var i = MODE_BUTTON_CYCLE.indexOf(current);
        if (i === -1) i = 0; // fallback to standby
        state.mode = MODE_BUTTON_CYCLE[(i + 1) % MODE_BUTTON_CYCLE.length];
    }
    state.linkError = false;
    state.standbyError = null;
    render();
}

// ---------------------------------------------------------------------------
// Data helpers
// ---------------------------------------------------------------------------

function getCurrentRecord() {
    if (!state.currentRecordId || state.records.length === 0) return null;
    return state.records.find(function (r) { return r.id === state.currentRecordId; }) || null;
}

function getStandbyRecord() {
    return state.standbyRecordVisible ? getCurrentRecord() : null;
}

function getSideForIndex(record, sideIndex) {
    if (!record || !record.sides || record.sides.length === 0) return null;
    return record.sides[sideIndex] || record.sides[0] || null;
}

function getSideLabel(side) {
    return side && side.id ? side.id : "A";
}

function clearActiveRecord(standbyError) {
    state.currentRecordId = null;
    state.currentTrackIndex = 0;
    state.currentSideIndex = 0;
    state.standbyRecordVisible = false;
    state.standbyError = standbyError || null;
}

function activateRecord(recordId, options) {
    var scope = options || {};
    var record;

    if (!recordId) return false;

    record = state.records.find(function (candidate) {
        return candidate.id === recordId;
    }) || null;

    if (!record) return false;

    state.currentRecordId = record.id;
    state.currentTrackIndex = 0;
    state.currentSideIndex = 0;

    if (scope.showInStandby !== undefined) {
        state.standbyRecordVisible = scope.showInStandby;
    }
    if (scope.clearStandbyError !== false) {
        state.standbyError = null;
    }

    return true;
}

function getLinkRecord() {
    var unlinked = getUnlinkedRecords();
    if (unlinked.length === 0) return null;
    return unlinked[state.linkRecordIndex % unlinked.length] || null;
}

function getLinkedRecords() {
    return state.records.filter(function (r) { return r.linked; });
}

function getUnlinkedRecords() {
    return state.records.filter(function (r) { return !r.linked; });
}

function getReLinkRecord() {
    if (state.records.length === 0) return null;
    return state.records[state.reLinkRecordIndex] || null;
}

function getCurrentStylus() {
    if (state.styli.length === 0) return null;
    return state.styli[state.stylusIndex] || null;
}

function coverImageUrl(record) {
    if (!record || !record.cover_image) return "";
    return "/" + record.cover_image.replace(/^ui\//, "");
}

function getStylusHours(stylus) {
    if (!stylus) return 0;
    return state.stylusHours[stylus.id] !== undefined ? state.stylusHours[stylus.id] : stylus.hours;
}

function getBarFillRatio(hours, capacityMax) {
    return Math.min(hours / capacityMax, 1);
}

function getBarColor(hours, capacityMin) {
    return hours < capacityMin ? "--ink-soft" : "--amber-deep";
}

// ---------------------------------------------------------------------------
// Render
// ---------------------------------------------------------------------------

function measureMetaOverflow(trackEl) {
    var fieldEl = trackEl.parentElement;
    var primaryEl = trackEl.querySelector('.marquee-copy--primary');
    var value = primaryEl.textContent;

    fieldEl.classList.remove('is-marquee');

    if (!value) {
        return;
    }

    if (primaryEl.scrollWidth > fieldEl.clientWidth) {
        fieldEl.classList.add('is-marquee');
    }
}

function setMetaText(trackEl, text) {
    var primaryEl = trackEl.querySelector('.marquee-copy--primary');
    var duplicateEl = trackEl.querySelector('.marquee-copy--duplicate');
    var value = text || '';

    if (primaryEl.textContent === value && duplicateEl.textContent === value) {
        return false;
    }

    primaryEl.textContent = value;
    duplicateEl.textContent = value;

    measureMetaOverflow(trackEl);
    return true;
}

function getModeLabel() {
    if (state.mode === "link") {
        var record = getLinkRecord();
        if (record && record.linked) return "Re-Link";
        return "Link";
    }
    if (state.mode === "re-link") return "Re-Link";
    return { standby: "Standby", play: "Play", stylus: "Stylus", sync: "Sync" }[state.mode] || state.mode;
}

function getActiveActionGroupId() {
    switch (state.mode) {
        case "standby":
            return "actions-standby";
        case "play":
            return getCurrentRecord() ? "actions-play" : null;
        case "link":
            return getUnlinkedRecords().length > 0 ? "actions-link" : "actions-standby";
        case "re-link":
            return state.records.length > 0 ? "actions-re-link" : "actions-standby";
        case "stylus":
            return state.styli.length > 0 ? "actions-stylus" : "actions-standby";
        case "sync":
            return "actions-sync";
        default:
            return null;
    }
}

function getTopBarInputs() {
    var topStylus = state.styli.length > 0 ? state.styli[0] : null;
    var topHours = topStylus ? getStylusHours(topStylus) : null;

    return {
        modeLabel: getModeLabel(),
        topStylusId: topStylus ? topStylus.id : null,
        topHours: topHours,
        topCapacityMax: topStylus ? topStylus.capacity_max : null,
        topCapacityMin: topStylus ? topStylus.capacity_min : null,
        temperature: state.temperature,
    };
}

function getVisibilityInputs() {
    return {
        mode: state.mode,
        actionGroupId: getActiveActionGroupId(),
    };
}

function getActiveSectionInputs() {
    var record;
    var side;
    var track;
    var stylus;

    switch (state.mode) {
        case "standby":
            record = getStandbyRecord();
            side = getSideForIndex(record, state.currentSideIndex);
            return {
                mode: state.mode,
                standbyError: state.standbyError,
                recordId: record ? record.id : null,
                recordArtist: record ? record.artist : "",
                recordTitle: record ? record.title : "",
                recordCover: coverImageUrl(record),
                sideId: side ? getSideLabel(side) : null,
            };
        case "play":
            record = getCurrentRecord();
            side = getSideForIndex(record, state.currentSideIndex);
            track = side && side.tracks ? (side.tracks[state.currentTrackIndex] || side.tracks[0]) : null;
            return {
                mode: state.mode,
                recordId: record ? record.id : null,
                recordArtist: record ? record.artist : "",
                recordTitle: record ? record.title : "",
                recordCover: coverImageUrl(record),
                sideId: side ? getSideLabel(side) : null,
                trackIndex: state.currentTrackIndex,
                trackTitle: track ? track.title : "",
            };
        case "link":
            record = getLinkRecord();
            return {
                mode: state.mode,
                linkError: state.linkError,
                unlinkedCount: getUnlinkedRecords().length,
                recordId: record ? record.id : null,
                recordArtist: record ? record.artist : "",
                recordTitle: record ? record.title : "",
                recordCover: coverImageUrl(record),
                recordLinked: record ? record.linked : null,
            };
        case "re-link":
            record = getReLinkRecord();
            return {
                mode: state.mode,
                linkError: state.linkError,
                recordCount: state.records.length,
                recordId: record ? record.id : null,
                recordArtist: record ? record.artist : "",
                recordTitle: record ? record.title : "",
                recordCover: coverImageUrl(record),
            };
        case "stylus":
            stylus = getCurrentStylus();
            return {
                mode: state.mode,
                stylusId: stylus ? stylus.id : null,
                stylusName: stylus ? stylus.name : "",
                stylusHours: stylus ? getStylusHours(stylus) : null,
                stylusCapacityMax: stylus ? stylus.capacity_max : null,
                stylusCapacityMin: stylus ? stylus.capacity_min : null,
                stylusCount: state.styli.length,
            };
        case "sync":
            return {
                mode: state.mode,
            };
        default:
            return {
                mode: state.mode,
            };
    }
}

function getVisibleMarqueeTracks() {
    switch (state.mode) {
        case "standby":
            return state.standbyError || !getStandbyRecord() ? [] : [
                document.getElementById("standby-artist"),
                document.getElementById("standby-title"),
            ];
        case "play":
            return !getCurrentRecord() ? [] : [
                document.getElementById("play-artist"),
                document.getElementById("play-title"),
                document.getElementById("play-track"),
            ];
        case "link":
            return !getLinkRecord() ? [] : [
                document.getElementById("link-artist"),
                document.getElementById("link-title"),
            ];
        case "re-link":
            return !getReLinkRecord() ? [] : [
                document.getElementById("re-link-artist"),
                document.getElementById("re-link-title"),
            ];
        default:
            return [];
    }
}

function remeasureActiveMarquees() {
    var tracks = getVisibleMarqueeTracks();
    for (var i = 0; i < tracks.length; i++) {
        measureMetaOverflow(tracks[i]);
    }
}

function didInputsChange(previousInputs, nextInputs) {
    return JSON.stringify(previousInputs) !== JSON.stringify(nextInputs);
}

function renderTopBar() {
    var compactBar = document.getElementById("stylus-bar-compact");
    var compactFill = document.getElementById("stylus-bar-compact-fill");
    var tempDisplay = document.getElementById("temperature-display");
    var topStylus = state.styli.length > 0 ? state.styli[0] : null;

    document.getElementById("mode-label").textContent = getModeLabel();

    if (topStylus) {
        var topHours = getStylusHours(topStylus);
        var topRatio = getBarFillRatio(topHours, topStylus.capacity_max);
        var topColor = getBarColor(topHours, topStylus.capacity_min);
        compactBar.style.display = "";
        compactFill.style.width = (topRatio * 100) + "%";
        compactFill.style.background = "var(" + topColor + ")";
    } else {
        compactBar.style.display = "none";
    }

    tempDisplay.textContent = state.temperature !== null ? Math.round(state.temperature) + " °C" : "N/A";
}

function renderVisibility() {
    var sections = document.querySelectorAll(".mode-section");
    var groups = document.querySelectorAll(".action-group");
    var actionGroupId = getActiveActionGroupId();
    var i;

    for (i = 0; i < sections.length; i++) {
        sections[i].classList.remove("active");
    }
    for (i = 0; i < groups.length; i++) {
        groups[i].classList.remove("active");
    }

    document.getElementById("mode-" + state.mode).classList.add("active");
    if (actionGroupId) {
        document.getElementById(actionGroupId).classList.add("active");
    }
}

function renderActiveSection() {
    switch (state.mode) {
        case "standby":
            renderStandby();
            break;
        case "play":
            renderPlay();
            break;
        case "link":
            renderLink();
            break;
        case "re-link":
            renderReLink();
            break;
        case "stylus":
            renderStylus();
            break;
        case "sync":
            renderSync();
            break;
    }

    remeasureActiveMarquees();
}

function render(options) {
    var scope = options || {};
    var shouldCheckTopBar = scope.topBar !== false;
    var shouldCheckVisibility = scope.visibility !== false;
    var shouldCheckSection = scope.section !== false;
    var force = scope.force === true;
    var visibilityChanged = false;
    var topBarInputs;
    var visibilityInputs;
    var sectionInputs;

    if (shouldCheckTopBar) {
        topBarInputs = getTopBarInputs();
        if (force || didInputsChange(lastRendered.topBar, topBarInputs)) {
            renderTopBar();
            lastRendered.topBar = topBarInputs;
        }
    }

    if (shouldCheckVisibility) {
        visibilityInputs = getVisibilityInputs();
        if (force || didInputsChange(lastRendered.visibility, visibilityInputs)) {
            renderVisibility();
            lastRendered.visibility = visibilityInputs;
            visibilityChanged = true;
        }
    }

    if (shouldCheckSection) {
        sectionInputs = getActiveSectionInputs();
        if (force || visibilityChanged || didInputsChange(lastRendered.section, sectionInputs)) {
            renderActiveSection();
            lastRendered.section = sectionInputs;
        }
    }
}

function renderStandby() {
    var record = getStandbyRecord();
    var grid = document.getElementById("standby-grid");
    var errorGrid = document.getElementById("standby-error-grid");
    var notFoundGrid = document.getElementById("standby-not-found-grid");
    var sideBtn = document.getElementById("btn-side-standby");

    grid.style.display = "none";
    errorGrid.style.display = "none";
    notFoundGrid.style.display = "none";
    sideBtn.style.visibility = "hidden";

    if (state.standbyError === "nfc") {
        errorGrid.style.display = "";
    } else if (state.standbyError === "not-found") {
        notFoundGrid.style.display = "";
    } else if (record) {
        grid.style.display = "";
        sideBtn.style.visibility = "visible";
        document.getElementById("standby-cover").src = coverImageUrl(record);
        document.getElementById("standby-id").textContent = String(record.id).padStart(2, "0");
        setMetaText(document.getElementById("standby-artist"), record.artist);
        setMetaText(document.getElementById("standby-title"), record.title);
        if (record.sides && record.sides.length > 0) {
            var side = getSideForIndex(record, state.currentSideIndex);
            sideBtn.textContent = "Side " + getSideLabel(side);
        }
    } else {
        notFoundGrid.style.display = "";
    }
}

function renderPlay() {
    var record = getCurrentRecord();
    var grid = document.getElementById("play-grid");
    var notFoundGrid = document.getElementById("play-not-found-grid");
    var cover = document.getElementById("play-cover");
    var artistEl = document.getElementById("play-artist");
    var titleEl = document.getElementById("play-title");
    var idEl = document.getElementById("play-id");
    var trackEl = document.getElementById("play-track");
    var sideLabel = document.getElementById("btn-side-label");

    if (!record) {
        grid.style.display = "none";
        notFoundGrid.style.display = "";
        cover.src = "";
        idEl.textContent = "";
        setMetaText(artistEl, "");
        setMetaText(titleEl, "");
        setMetaText(trackEl, "");
        sideLabel.textContent = "Side A";
        return;
    }

    grid.style.display = "";
    notFoundGrid.style.display = "none";

    var side = getSideForIndex(record, state.currentSideIndex);
    var track = side && side.tracks ? (side.tracks[state.currentTrackIndex] || side.tracks[0]) : null;

    cover.src = coverImageUrl(record);
    idEl.textContent = String(record.id).padStart(2, "0");
    setMetaText(artistEl, record.artist);
    setMetaText(titleEl, record.title);
    setMetaText(trackEl, track ? track.title : "");
    sideLabel.textContent = "Side " + getSideLabel(side);
}

function renderLink() {
    var record = getLinkRecord();
    var grid = document.getElementById("link-grid");
    var emptyGrid = document.getElementById("link-empty-grid");
    var cover = document.getElementById("link-cover");
    var artist = document.getElementById("link-artist");
    var title = document.getElementById("link-title");
    var idEl = document.getElementById("link-id");
    var statusEl = document.getElementById("link-status");
    var errorEl = document.getElementById("link-error");

    if (!record) {
        grid.style.display = "none";
        emptyGrid.style.display = "";
        return;
    }

    grid.style.display = "";
    emptyGrid.style.display = "none";

    cover.src = coverImageUrl(record);
    idEl.textContent = String(record.id).padStart(2, "0");
    setMetaText(artist, record.artist);
    setMetaText(title, record.title);

    if (state.linkError) {
        statusEl.style.display = "none";
        errorEl.style.display = "";
    } else {
        statusEl.textContent = record.linked ? "Linked" : "Not Linked";
        statusEl.style.display = "";
        errorEl.style.display = "none";
    }
}

function renderReLink() {
    var record = getReLinkRecord();
    var cover = document.getElementById("re-link-cover");
    var artist = document.getElementById("re-link-artist");
    var title = document.getElementById("re-link-title");
    var idEl = document.getElementById("re-link-id");
    var statusEl = document.getElementById("re-link-status");
    var errorEl = document.getElementById("re-link-error");

    if (record) {
        cover.src = coverImageUrl(record);
        idEl.textContent = String(record.id).padStart(2, "0");
        setMetaText(artist, record.artist);
        setMetaText(title, record.title);

        if (state.linkError) {
            statusEl.style.display = "none";
            errorEl.style.display = "";
        } else {
            statusEl.textContent = "Linked";
            statusEl.style.display = "";
            errorEl.style.display = "none";
        }
    } else {
        statusEl.style.display = "none";
        errorEl.style.display = "none";
    }
}

function renderStylus() {
    var stylus = getCurrentStylus();
    var nameEl = document.getElementById("stylus-mode-name");
    var hoursEl = document.getElementById("stylus-mode-hours");
    var barFill = document.getElementById("stylus-bar-full-fill");
    var bar = document.getElementById("stylus-bar-full");
    var empty = document.getElementById("stylus-empty");

    if (stylus) {
        var hours = getStylusHours(stylus);
        var ratio = getBarFillRatio(hours, stylus.capacity_max);
        var color = getBarColor(hours, stylus.capacity_min);

        nameEl.textContent = stylus.name;
        nameEl.style.display = "";
        hoursEl.textContent = hours + " h";
        hoursEl.style.display = "";
        bar.style.display = "";
        barFill.style.width = (ratio * 100) + "%";
        barFill.style.background = "var(" + color + ")";
        empty.style.display = "none";
    } else {
        nameEl.style.display = "none";
        hoursEl.style.display = "none";
        bar.style.display = "none";
        empty.style.display = "";
    }
}

function renderSync() {
    fetch("/sync/status")
        .then(function (res) { return res.json(); })
        .then(function (data) {
            var text = data.last_sync ? "Last updated " + data.last_sync : "Last updated never";
            document.getElementById("sync-status").textContent = text;
        })
        .catch(function () {
            document.getElementById("sync-status").textContent = "Last updated never";
        });
}

function startSync() {
    var statusEl = document.getElementById("sync-status");
    statusEl.classList.add("syncing");
    fetch("/sync", { method: "POST" }).then(function (response) {
        var reader = response.body.getReader();
        var decoder = new TextDecoder();
        var buffer = "";

        function read() {
            reader.read().then(function (result) {
                if (result.done) {
                    statusEl.classList.remove("syncing");
                    return;
                }
                buffer += decoder.decode(result.value, { stream: true });
                var lines = buffer.split("\n");
                buffer = lines.pop();
                for (var i = 0; i < lines.length; i++) {
                    var line = lines[i];
                    if (line.indexOf("data: ") === 0) {
                        var payload = JSON.parse(line.slice(6));
                        statusEl.textContent = payload.status;
                        if (payload.status === "Sync complete" || payload.status === "Sync error") {
                            statusEl.classList.remove("syncing");
                            fetchRecords().then(function () { fetchStyli(); });
                        }
                    }
                }
                read();
            });
        }
        read();
    }).catch(function () {
        statusEl.textContent = "Sync error";
        statusEl.classList.remove("syncing");
    });
}

// ---------------------------------------------------------------------------
// REST API
// ---------------------------------------------------------------------------

function fetchRecords() {
    return fetch("/records")
        .then(function (res) { return res.json(); })
        .then(function (data) { state.records = data; })
        .catch(function (e) { console.error("Failed to fetch records:", e); });
}

function fetchStyli() {
    return fetch("/styli")
        .then(function (res) { return res.json(); })
        .then(function (data) { state.styli = data; })
        .catch(function (e) { console.error("Failed to fetch styli:", e); });
}

function fetchTemperature() {
    return fetch("/temperature")
        .then(function (res) { return res.json(); })
        .then(function (data) {
            state.temperature = data.celsius;
            render({ topBar: true, visibility: false, section: false });
        })
        .catch(function () {
            state.temperature = null;
            render({ topBar: true, visibility: false, section: false });
        });
}

function linkRecord() {
    var record = getLinkRecord();
    if (!record) return;

    fetch("/records/" + record.id + "/link", { method: "POST" })
        .then(function (res) {
            if (res.ok) {
                record.linked = true;
                state.linkError = false;
            } else {
                state.linkError = true;
            }
            render();
        })
        .catch(function () {
            state.linkError = true;
            render();
        });
}

function resetStylus() {
    var stylus = getCurrentStylus();
    if (!stylus) return;

    fetch("/styli/" + stylus.id + "/reset", { method: "POST" })
        .then(function (res) {
            if (res.ok) {
                stylus.hours = 0;
                state.stylusHours[stylus.id] = 0;
            }
            render();
        })
        .catch(function (e) {
            console.error("Failed to reset stylus:", e);
        });
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------

function prevRecord() {
    var unlinked = getUnlinkedRecords();
    if (unlinked.length === 0) return;
    state.linkRecordIndex = (state.linkRecordIndex - 1 + unlinked.length) % unlinked.length;
    state.linkError = false;
    render();
}

function nextRecord() {
    var unlinked = getUnlinkedRecords();
    if (unlinked.length === 0) return;
    state.linkRecordIndex = (state.linkRecordIndex + 1) % unlinked.length;
    state.linkError = false;
    render();
}

function prevReLinkRecord() {
    if (state.records.length === 0) return;
    state.reLinkRecordIndex = (state.reLinkRecordIndex - 1 + state.records.length) % state.records.length;
    state.linkError = false;
    render();
}

function nextReLinkRecord() {
    if (state.records.length === 0) return;
    state.reLinkRecordIndex = (state.reLinkRecordIndex + 1) % state.records.length;
    state.linkError = false;
    render();
}

function prevStylus() {
    if (state.styli.length === 0) return;
    state.stylusIndex = (state.stylusIndex - 1 + state.styli.length) % state.styli.length;
    render();
}

function nextStylus() {
    if (state.styli.length === 0) return;
    state.stylusIndex = (state.stylusIndex + 1) % state.styli.length;
    render();
}

function prevSong() {
    var record = getCurrentRecord();
    if (!record || !record.sides || record.sides.length === 0) return;

    state.currentTrackIndex--;
    if (state.currentTrackIndex < 0) {
        state.currentSideIndex = (state.currentSideIndex - 1 + record.sides.length) % record.sides.length;
        state.currentTrackIndex = record.sides[state.currentSideIndex].tracks.length - 1;
    }
    render();
}

function nextSong() {
    var record = getCurrentRecord();
    if (!record || !record.sides || record.sides.length === 0) return;

    var side = record.sides[state.currentSideIndex];
    state.currentTrackIndex++;
    if (state.currentTrackIndex >= side.tracks.length) {
        state.currentSideIndex = (state.currentSideIndex + 1) % record.sides.length;
        state.currentTrackIndex = 0;
    }
    render();
}

function switchSide() {
    var record = getCurrentRecord();
    if (!record || !record.sides || record.sides.length === 0) return;

    state.currentSideIndex = (state.currentSideIndex + 1) % record.sides.length;
    state.currentTrackIndex = 0;
    render();
}

// ---------------------------------------------------------------------------
// WebSocket
// ---------------------------------------------------------------------------

function connectWebSocket() {
    var protocol = location.protocol === "https:" ? "wss:" : "ws:";
    var ws = new WebSocket(protocol + "//" + location.host + "/ws");

    ws.onmessage = function (event) {
        var msg = JSON.parse(event.data);

        switch (msg.event) {
            case "current_record":
                activateRecord(msg.data.record_id, { clearStandbyError: false });
                render();
                break;
            case "scan":
                if (msg.data.record_id === null) {
                    clearActiveRecord("nfc");
                } else {
                    if (!activateRecord(msg.data.record_id, { showInStandby: true })) {
                        clearActiveRecord("not-found");
                    }
                }
                state.mode = "standby";
                render();
                break;
            case "stylus_hours":
                var currentStylus = getCurrentStylus();
                state.stylusHours[msg.data.stylus_id] = msg.data.hours;
                render({
                    topBar: true,
                    visibility: false,
                    section: state.mode === "stylus" && currentStylus && currentStylus.id === msg.data.stylus_id,
                });
                break;
            case "status":
                if (!location.hash) {
                    if (msg.data.status === "play" && state.mode !== "play") {
                        state.mode = "play";
                        render();
                    } else if (msg.data.status === "stop" && state.mode === "play") {
                        state.mode = "standby";
                        render();
                    }
                }
                break;
            case "temperature_c":
                state.temperature = msg.data.temp_c;
                render({ topBar: true, visibility: false, section: false });
                break;
            case "link_error":
                state.linkError = true;
                render();
                break;
        }
    };

    ws.onclose = function () {
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = function () {
        ws.close();
    };
}

// ---------------------------------------------------------------------------
// Dev mode — URL hash navigation
// ---------------------------------------------------------------------------

function applyHash() {
    var hash = location.hash.replace(/^#/, "");
    if (!hash) return false;

    // Handle re-link as a mode
    var mode;
    var rest;
    if (hash === "re-link" || hash.indexOf("re-link-") === 0) {
        mode = "re-link";
        rest = hash.slice("re-link-".length);
    } else {
        var parts = hash.split("-");
        mode = parts[0];
        rest = parts.slice(1).join("-");
    }

    var isError = rest === "error";

    if (MODES.indexOf(mode) === -1) return false;

    state.mode = mode;
    state.linkError = false;
    clearActiveRecord(mode === "standby" ? "not-found" : null);

    if ((mode === "standby" || mode === "play") && state.records.length > 0) {
        activateRecord(state.records[0].id, { showInStandby: true });
    }

    if (isError) {
        switch (mode) {
            case "standby":
                clearActiveRecord("nfc");
                break;
            case "link":
                state.linkError = true;
                break;
            case "stylus":
                state.styli = [];
                break;
        }
    }

    // For re-link mode, mark all records as linked for demo
    if (mode === "re-link") {
        state.records.forEach(function (r) { r.linked = true; });
    }

    // Handle standby-not-found hash
    if (mode === "standby" && rest === "not-found") {
        clearActiveRecord("not-found");
    }

    render();
    return true;
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", function () {
    Promise.all([fetchRecords(), fetchStyli()]).then(function () {
        if (!applyHash()) {
            render();
        }
        connectWebSocket();
        fetchTemperature();
        setInterval(fetchTemperature, 30000);

        // Recompute overflow state after fonts finish loading without rewriting text.
        if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(function () { remeasureActiveMarquees(); });
        }
    });

    // Recompute overflow state on window resize without rerendering the active section.
    var resizeTimer;
    window.addEventListener('resize', function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () { remeasureActiveMarquees(); }, 150);
    });

    window.addEventListener("hashchange", function () {
        // Re-fetch data to reset any error overrides before applying hash
        Promise.all([fetchRecords(), fetchStyli()]).then(function () {
            if (!applyHash()) {
                render();
            }
        });
    });

    // Button event listeners
    document.getElementById("btn-side-standby").addEventListener("click", switchSide);

    document.getElementById("btn-prev-song").addEventListener("click", prevSong);
    document.getElementById("btn-next-song").addEventListener("click", nextSong);
    document.getElementById("btn-side-label").addEventListener("click", switchSide);

    document.getElementById("btn-prev-record").addEventListener("click", prevRecord);
    document.getElementById("btn-next-record").addEventListener("click", nextRecord);

    document.getElementById("btn-prev-re-link").addEventListener("click", prevReLinkRecord);
    document.getElementById("btn-next-re-link").addEventListener("click", nextReLinkRecord);

    document.getElementById("btn-prev-stylus").addEventListener("click", prevStylus);
    document.getElementById("btn-next-stylus").addEventListener("click", nextStylus);

    // Mode buttons
    ["btn-mode-standby", "btn-mode-link", "btn-mode-re-link", "btn-mode-stylus", "btn-mode-sync"].forEach(function (id) {
        document.getElementById(id).addEventListener("click", nextMode);
    });

    // Sync button
    document.getElementById("btn-sync").addEventListener("click", startSync);
});
