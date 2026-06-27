// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

var state = {
    mode: "standby",
    records: [],
    styli: [],
    currentRecordId: null,
    playbackTime: null,
    boardlessElapsedSeconds: null,
    manualPlaybackOffsetSeconds: 0,
    currentTrackIndex: 0,
    currentSideIndex: 0,
    linkRecordIndex: 0,
    reLinkRecordIndex: 0,
    stylusIndex: 0,
    stylusHours: {},
    temperature: null,
    linkError: false,
    pendingLinkRecordId: null,
    pendingLinkMode: null,
    retainedLinkRecordId: null,
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
        setMode("standby");
    } else {
        var i = MODE_BUTTON_CYCLE.indexOf(current);
        if (i === -1) i = 0; // fallback to standby
        setMode(MODE_BUTTON_CYCLE[(i + 1) % MODE_BUTTON_CYCLE.length]);
    }
    state.linkError = false;
    state.standbyError = null;
    render();
}

function clearPendingLink() {
    state.pendingLinkRecordId = null;
    state.pendingLinkMode = null;
}

function requestKioskExit(event) {
    if (event) {
        event.preventDefault();
    }
    if (!window.confirm("Exit kiosk mode?")) return;

    fetch("/kiosk/exit", { method: "POST" }).catch(function () {
        // The kiosk process may stop before the browser receives the response.
    });
}

function addKioskExitListener(button) {
    var eventName = window.PointerEvent ? "pointerup" : "click";
    button.addEventListener(eventName, requestKioskExit);
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
    if (!side) return "A";
    return side.id || side.side_label || "A";
}

function getCurrentSideButtonLabel(record) {
    var side = getSideForIndex(record, state.currentSideIndex);
    return "Side " + getSideLabel(side);
}

function updateCurrentSideButtonLabel() {
    var record = getCurrentRecord();
    var label = getCurrentSideButtonLabel(record);
    var standbyButton;
    var playButton;

    if (typeof document === "undefined") return;

    standbyButton = document.getElementById("btn-side-standby");
    playButton = document.getElementById("btn-side-label");

    if (standbyButton) {
        standbyButton.textContent = label;
    }
    if (playButton) {
        playButton.textContent = label;
    }
}

function clearActiveRecord(standbyError) {
    state.currentRecordId = null;
    state.playbackTime = null;
    resetBoardlessPlaybackTiming();
    state.currentTrackIndex = 0;
    state.currentSideIndex = 0;
    state.standbyRecordVisible = false;
    state.standbyError = standbyError || null;
}

function setMode(nextMode) {
    if (state.mode !== nextMode) {
        clearPendingLink();
        state.retainedLinkRecordId = null;
    }
    state.mode = nextMode;
    if (nextMode !== "play") {
        state.playbackTime = null;
        resetBoardlessPlaybackTiming();
    }
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
    resetBoardlessPlaybackTiming();

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
    var retained;
    if (state.retainedLinkRecordId) {
        retained = state.records.find(function (r) {
            return r.id === state.retainedLinkRecordId;
        }) || null;
        if (retained) return retained;
        state.retainedLinkRecordId = null;
    }
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
    var linked = getLinkedRecords();
    if (linked.length === 0) return null;
    return linked[state.reLinkRecordIndex % linked.length] || null;
}

function isPendingLinkFor(record, mode) {
    return Boolean(
        record &&
        state.pendingLinkRecordId === record.id &&
        state.pendingLinkMode === mode
    );
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

function normalizeTrackLabelValue(value) {
    return typeof value === "string" ? value.trim() : "";
}

function getPlaybackTimeValue(value) {
    return typeof value === "string" && /^\d{2}:\d{2}$/.test(value) ? value : null;
}

function parseDurationSeconds(value) {
    var match;

    if (typeof value !== "string") return 0;

    match = value.match(/^(\d+):(\d{2})$/);
    if (!match) return 0;

    return (parseInt(match[1], 10) * 60) + parseInt(match[2], 10);
}

function getTrackDurationValue(track) {
    return track ? (track.duration || track.time) : null;
}

function getSideDurationSeconds(side) {
    var tracks = side && side.tracks ? side.tracks : [];
    var total = 0;

    for (var i = 0; i < tracks.length; i++) {
        total += parseDurationSeconds(getTrackDurationValue(tracks[i]));
    }

    return total;
}

function getSideStartSeconds(record, sideIndex) {
    var sides = record && record.sides ? record.sides : [];
    var clampedIndex = clampSideIndex(record, sideIndex);
    var total = 0;

    for (var i = 0; i < clampedIndex; i++) {
        total += getSideDurationSeconds(sides[i]);
    }

    return total;
}

function getTrackStartSeconds(record, sideIndex, trackIndex) {
    var side = getSideForIndex(record, sideIndex);
    var tracks = side && side.tracks ? side.tracks : [];
    var clampedTrackIndex = clampTrackIndex(record, sideIndex, trackIndex);
    var total = getSideStartSeconds(record, sideIndex);

    for (var i = 0; i < clampedTrackIndex; i++) {
        total += parseDurationSeconds(getTrackDurationValue(tracks[i]));
    }

    return total;
}

function getTotalRecordDurationSeconds(record) {
    var sides = record && record.sides ? record.sides : [];
    var total = 0;

    for (var i = 0; i < sides.length; i++) {
        total += getSideDurationSeconds(sides[i]);
    }

    return total;
}

function clampSideIndex(record, sideIndex) {
    var sides = record && record.sides ? record.sides : [];
    var index = Number.isFinite(sideIndex) ? sideIndex : 0;

    if (sides.length === 0) return 0;
    return Math.min(Math.max(index, 0), sides.length - 1);
}

function wrapSideIndex(record, sideIndex) {
    var sides = record && record.sides ? record.sides : [];

    if (sides.length === 0) return 0;
    return ((sideIndex % sides.length) + sides.length) % sides.length;
}

function clampTrackIndex(record, sideIndex, trackIndex) {
    var side = getSideForIndex(record, sideIndex);
    var tracks = side && side.tracks ? side.tracks : [];
    var index = Number.isFinite(trackIndex) ? trackIndex : 0;

    if (tracks.length === 0) return 0;
    return Math.min(Math.max(index, 0), tracks.length - 1);
}

function resolvePlaybackPosition(record, effectiveSeconds) {
    var sides = record && record.sides ? record.sides : [];
    var elapsed = Math.max(effectiveSeconds || 0, 0);
    var sideStart = 0;
    var sideIndex;
    var trackIndex;
    var side;
    var tracks;
    var sideDuration;
    var trackStart;
    var trackDuration;

    if (sides.length === 0) {
        return { sideIndex: 0, trackIndex: 0 };
    }

    for (sideIndex = 0; sideIndex < sides.length; sideIndex++) {
        side = sides[sideIndex];
        sideDuration = getSideDurationSeconds(side);
        if (elapsed < sideStart + sideDuration || sideIndex === sides.length - 1) {
            tracks = side && side.tracks ? side.tracks : [];
            trackStart = sideStart;
            if (tracks.length === 0) {
                return { sideIndex: sideIndex, trackIndex: 0 };
            }
            for (trackIndex = 0; trackIndex < tracks.length; trackIndex++) {
                trackDuration = parseDurationSeconds(getTrackDurationValue(tracks[trackIndex]));
                if (elapsed < trackStart + trackDuration || trackIndex === tracks.length - 1) {
                    return { sideIndex: sideIndex, trackIndex: trackIndex };
                }
                trackStart += trackDuration;
            }
        }
        sideStart += sideDuration;
    }

    return { sideIndex: sides.length - 1, trackIndex: 0 };
}

function getEffectivePlaybackSeconds() {
    if (state.boardlessElapsedSeconds === null) return null;
    return Math.max(state.boardlessElapsedSeconds + state.manualPlaybackOffsetSeconds, 0);
}

function resetBoardlessPlaybackTiming() {
    state.boardlessElapsedSeconds = null;
    state.manualPlaybackOffsetSeconds = 0;
}

function setManualPlaybackOffset(targetEffectiveSeconds) {
    var elapsed = state.boardlessElapsedSeconds === null ? 0 : state.boardlessElapsedSeconds;
    state.manualPlaybackOffsetSeconds = Math.max(targetEffectiveSeconds, 0) - elapsed;
}

function preserveCurrentSelectionForPlayStart() {
    var record = getCurrentRecord();

    if (!record || !record.sides || record.sides.length === 0) return;

    state.currentSideIndex = clampSideIndex(record, state.currentSideIndex);
    state.currentTrackIndex = clampTrackIndex(record, state.currentSideIndex, state.currentTrackIndex);
    state.manualPlaybackOffsetSeconds = getTrackStartSeconds(record, state.currentSideIndex, state.currentTrackIndex);
}

function advanceSideIfStoppedNearCurrentSideEnd() {
    var record = getCurrentRecord();
    var effectiveSeconds = getEffectivePlaybackSeconds();
    var currentSideIndex;
    var side;
    var sideEnd;

    if (!record || !record.sides || record.sides.length === 0 || effectiveSeconds === null) return false;

    currentSideIndex = clampSideIndex(record, state.currentSideIndex);
    side = getSideForIndex(record, currentSideIndex);
    sideEnd = getSideStartSeconds(record, currentSideIndex) + getSideDurationSeconds(side);

    if (effectiveSeconds < sideEnd - 20) return false;

    state.currentSideIndex = wrapSideIndex(record, currentSideIndex + 1);
    state.currentTrackIndex = 0;
    updateCurrentSideButtonLabel();
    return true;
}

function refreshBoardlessPlaybackSelection() {
    var record = getCurrentRecord();
    var effectiveSeconds = getEffectivePlaybackSeconds();
    var side;
    var sideEnd;
    var sideStart;
    var trackIndex;
    var trackStart;
    var trackDuration;
    var currentSideIndex;

    if (!record || !record.sides || record.sides.length === 0 || effectiveSeconds === null) return;

    currentSideIndex = clampSideIndex(record, state.currentSideIndex);
    side = getSideForIndex(record, currentSideIndex);
    sideStart = getSideStartSeconds(record, currentSideIndex);
    sideEnd = sideStart + getSideDurationSeconds(side);

    state.currentSideIndex = currentSideIndex;
    if (!side || !side.tracks || side.tracks.length === 0) {
        state.currentTrackIndex = 0;
        return;
    }

    if (effectiveSeconds <= sideStart) {
        state.currentTrackIndex = 0;
        return;
    }

    trackStart = sideStart;
    for (trackIndex = 0; trackIndex < side.tracks.length; trackIndex++) {
        trackDuration = parseDurationSeconds(getTrackDurationValue(side.tracks[trackIndex]));
        if (effectiveSeconds < trackStart + trackDuration || trackIndex === side.tracks.length - 1) {
            state.currentTrackIndex = trackIndex;
            return;
        }
        trackStart += trackDuration;
    }

    state.currentTrackIndex = clampTrackIndex(record, currentSideIndex, side.tracks.length - 1);
}

function getPlayTrackLabel(record, track) {
    var trackTitle = normalizeTrackLabelValue(track && track.title);
    var trackArtist = normalizeTrackLabelValue(track && track.artist);
    var recordArtist = normalizeTrackLabelValue(record && record.artist);

    if (!trackTitle) {
        return "";
    }

    if (!trackArtist || trackArtist === recordArtist) {
        return trackTitle;
    }

    return trackTitle + " (" + trackArtist + ")";
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

    if (state.mode === "play") {
        return state.playbackTime ? "Play " + state.playbackTime : "Play";
    }

    return { standby: "Standby", stylus: "Stylus", sync: "Sync" }[state.mode] || state.mode;
}

function getActiveActionGroupId() {
    switch (state.mode) {
        case "standby":
            return "actions-standby";
        case "play":
            return getCurrentRecord() ? "actions-play" : null;
        case "link":
            return getLinkRecord() ? "actions-link" : "actions-standby";
        case "re-link":
            return getLinkedRecords().length > 0 ? "actions-re-link" : "actions-standby";
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
                trackTitle: getPlayTrackLabel(record, track),
            };
        case "link":
            record = getLinkRecord();
            return {
                mode: state.mode,
                linkError: state.linkError,
                unlinkedCount: getUnlinkedRecords().length,
                retainedLinkRecordId: state.retainedLinkRecordId,
                pendingLinkRecordId: state.pendingLinkRecordId,
                pendingLinkMode: state.pendingLinkMode,
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
                linkedCount: getLinkedRecords().length,
                pendingLinkRecordId: state.pendingLinkRecordId,
                pendingLinkMode: state.pendingLinkMode,
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
            sideBtn.textContent = getCurrentSideButtonLabel(record);
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
    var trackLabel = getPlayTrackLabel(record, track);

    cover.src = coverImageUrl(record);
    idEl.textContent = String(record.id).padStart(2, "0");
    setMetaText(artistEl, record.artist);
    setMetaText(titleEl, record.title);
    setMetaText(trackEl, trackLabel);
    sideLabel.textContent = getCurrentSideButtonLabel(record);
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
    var pendingEl = document.getElementById("link-pending");
    var errorEl = document.getElementById("link-error");

    if (!record) {
        grid.style.display = "none";
        emptyGrid.style.display = "";
        pendingEl.style.display = "none";
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
        pendingEl.style.display = "none";
        errorEl.style.display = "";
    } else {
        statusEl.textContent = record.linked ? "Linked" : "Not Linked";
        statusEl.style.display = "";
        pendingEl.style.display = isPendingLinkFor(record, "link") ? "inline-block" : "none";
        errorEl.style.display = "none";
    }
}

function renderReLink() {
    var record = getReLinkRecord();
    var grid = document.getElementById("re-link-grid");
    var emptyGrid = document.getElementById("re-link-empty-grid");
    var cover = document.getElementById("re-link-cover");
    var artist = document.getElementById("re-link-artist");
    var title = document.getElementById("re-link-title");
    var idEl = document.getElementById("re-link-id");
    var statusEl = document.getElementById("re-link-status");
    var pendingEl = document.getElementById("re-link-pending");
    var errorEl = document.getElementById("re-link-error");

    if (record) {
        grid.style.display = "";
        emptyGrid.style.display = "none";
        cover.src = coverImageUrl(record);
        idEl.textContent = String(record.id).padStart(2, "0");
        setMetaText(artist, record.artist);
        setMetaText(title, record.title);

        if (state.linkError) {
            statusEl.style.display = "none";
            pendingEl.style.display = "none";
            errorEl.style.display = "";
        } else {
            statusEl.textContent = "Linked";
            statusEl.style.display = "";
            pendingEl.style.display = isPendingLinkFor(record, "re-link") ? "inline-block" : "none";
            errorEl.style.display = "none";
        }
    } else {
        grid.style.display = "none";
        emptyGrid.style.display = "";
        statusEl.style.display = "none";
        pendingEl.style.display = "none";
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

function linkRecord() {
    var record = getLinkRecord();
    if (!record) return;

    state.pendingLinkRecordId = record.id;
    state.pendingLinkMode = "link";
    state.linkError = false;
    render();
}

function reLinkRecord() {
    var record = getReLinkRecord();
    if (!record) return;

    state.pendingLinkRecordId = record.id;
    state.pendingLinkMode = "re-link";
    state.linkError = false;
    render();
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
    state.retainedLinkRecordId = null;
    var unlinked = getUnlinkedRecords();
    if (unlinked.length === 0) return;
    state.linkRecordIndex = (state.linkRecordIndex - 1 + unlinked.length) % unlinked.length;
    state.linkError = false;
    render();
}

function nextRecord() {
    state.retainedLinkRecordId = null;
    var unlinked = getUnlinkedRecords();
    if (unlinked.length === 0) return;
    state.linkRecordIndex = (state.linkRecordIndex + 1) % unlinked.length;
    state.linkError = false;
    render();
}

function prevReLinkRecord() {
    var linked = getLinkedRecords();
    if (linked.length === 0) return;
    state.reLinkRecordIndex = (state.reLinkRecordIndex - 1 + linked.length) % linked.length;
    state.linkError = false;
    render();
}

function nextReLinkRecord() {
    var linked = getLinkedRecords();
    if (linked.length === 0) return;
    state.reLinkRecordIndex = (state.reLinkRecordIndex + 1) % linked.length;
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
    if (state.mode === "play") {
        setManualPlaybackOffset(getTrackStartSeconds(record, state.currentSideIndex, state.currentTrackIndex));
        updateCurrentSideButtonLabel();
    }
    render({ force: state.mode === "play" });
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
    if (state.mode === "play") {
        setManualPlaybackOffset(getTrackStartSeconds(record, state.currentSideIndex, state.currentTrackIndex));
        updateCurrentSideButtonLabel();
    }
    render({ force: state.mode === "play" });
}

function switchSide() {
    var record = getCurrentRecord();
    var selectedTrackIndex = state.currentTrackIndex;
    var previousSideIndex = state.currentSideIndex;
    var previousEffectiveSeconds = getEffectivePlaybackSeconds();
    var previousSideEnd;
    if (!record || !record.sides || record.sides.length === 0) return;

    state.currentSideIndex = (state.currentSideIndex + 1) % record.sides.length;
    if (state.mode === "play") {
        previousSideEnd = getSideStartSeconds(record, previousSideIndex) + getSideDurationSeconds(getSideForIndex(record, previousSideIndex));
        if (previousEffectiveSeconds !== null && previousEffectiveSeconds >= previousSideEnd) {
            state.manualPlaybackOffsetSeconds = getSideStartSeconds(record, state.currentSideIndex);
            refreshBoardlessPlaybackSelection();
        } else {
            state.currentTrackIndex = clampTrackIndex(record, state.currentSideIndex, selectedTrackIndex);
            setManualPlaybackOffset(getTrackStartSeconds(record, state.currentSideIndex, state.currentTrackIndex));
        }
        updateCurrentSideButtonLabel();
    } else {
        state.currentTrackIndex = 0;
    }
    render({ force: state.mode === "play" });
}

// ---------------------------------------------------------------------------
// WebSocket
// ---------------------------------------------------------------------------

function connectWebSocket() {
    var protocol = location.protocol === "https:" ? "wss:" : "ws:";
    var ws = new WebSocket(protocol + "//" + location.host + "/ws");

    ws.onmessage = function (event) {
        var msg = JSON.parse(event.data);
        var msgData = msg.data || {};

        switch (msg.event) {
            case "current_record":
                activateRecord(msgData.record_id, { clearStandbyError: false });
                render();
                break;
            case "scan":
                if (msgData.record_id === null) {
                    clearActiveRecord("nfc");
                } else {
                    if (!activateRecord(msgData.record_id, { showInStandby: true })) {
                        clearActiveRecord("not-found");
                    }
                }
                setMode("standby");
                render();
                break;
            case "stylus_hours":
                var currentStylus = getCurrentStylus();
                state.stylusHours[msgData.stylus_id] = msgData.hours;
                render({
                    topBar: true,
                    visibility: false,
                    section: state.mode === "stylus" && currentStylus && currentStylus.id === msgData.stylus_id,
                });
                break;
            case "status":
                if (!location.hash) {
                    if (msgData.status === "play") {
                        var wasPlaying = state.mode === "play";
                        state.playbackTime = getPlaybackTimeValue(msgData.time);
                        state.boardlessElapsedSeconds = state.playbackTime ? parseDurationSeconds(state.playbackTime) : null;

                        if (!wasPlaying) {
                            setMode("play");
                            preserveCurrentSelectionForPlayStart();
                        }
                        refreshBoardlessPlaybackSelection();
                        render();
                    } else if (msgData.status === "stop" && state.mode === "play") {
                        advanceSideIfStoppedNearCurrentSideEnd();
                        state.currentTrackIndex = 0;
                        setMode("standby");
                        render();
                    }
                }
                break;
            case "temperature_c":
                state.temperature = msgData.temp_c;
                render({ topBar: true, visibility: false, section: false });
                break;
            case "link_success":
                var visibleLinkRecord = state.mode === "link" ? getLinkRecord() : null;
                state.records.forEach(function (record) {
                    if (record.id === msgData.record_id) {
                        record.linked = true;
                    }
                });
                if (state.pendingLinkRecordId === msgData.record_id) {
                    clearPendingLink();
                }
                if (visibleLinkRecord && visibleLinkRecord.id === msgData.record_id) {
                    state.retainedLinkRecordId = msgData.record_id;
                }
                state.linkError = false;
                render();
                break;
            case "link_error":
                clearPendingLink();
                if (state.mode === "link" || state.mode === "re-link") {
                    state.linkError = true;
                }
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

    setMode(mode);
    state.linkError = false;
    state.retainedLinkRecordId = null;
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
    addKioskExitListener(document.getElementById("kiosk-exit-button"));

    document.getElementById("btn-side-standby").addEventListener("click", switchSide);

    document.getElementById("btn-prev-song").addEventListener("click", prevSong);
    document.getElementById("btn-next-song").addEventListener("click", nextSong);
    document.getElementById("btn-side-label").addEventListener("click", switchSide);

    document.getElementById("btn-prev-record").addEventListener("click", prevRecord);
    document.getElementById("btn-next-record").addEventListener("click", nextRecord);
    document.getElementById("btn-link").addEventListener("click", linkRecord);

    document.getElementById("btn-prev-re-link").addEventListener("click", prevReLinkRecord);
    document.getElementById("btn-next-re-link").addEventListener("click", nextReLinkRecord);
    document.getElementById("btn-re-link").addEventListener("click", reLinkRecord);

    document.getElementById("btn-prev-stylus").addEventListener("click", prevStylus);
    document.getElementById("btn-next-stylus").addEventListener("click", nextStylus);
    document.getElementById("btn-reset-stylus").addEventListener("click", resetStylus);

    // Mode buttons
    ["btn-mode-standby", "btn-mode-link", "btn-mode-re-link", "btn-mode-stylus", "btn-mode-sync"].forEach(function (id) {
        document.getElementById(id).addEventListener("click", nextMode);
    });

    // Sync button
    document.getElementById("btn-sync").addEventListener("click", startSync);
});
