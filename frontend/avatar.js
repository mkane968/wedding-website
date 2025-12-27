const FIELD_NAMES = [
    "avatar_skin_tone",
    "avatar_hair_color",
    "avatar_hair_style",
    "avatar_outfit_color",
    "avatar_accent",
    "full_name",
];

const SKIN_MAP = {
    porcelain: "eeb4a4",
    rosy: "e7a391",
    sienna: "d78774",
    amber: "b16a5b",
    espresso: "92594b",
};

const HAIR_COLORS = {
    midnight: "362c47",
    espresso: "3b2315",
    chestnut: "6c4545",
    copper: "b45b3e",
    honey: "f29c65",
    platinum: "dee1f5",
    "rose-quartz": "e16381",
};

const HAIR_STYLES = {
    short: "shortCombover",
    long: "extraLong",
};

const BACKGROUND_MAP = {
    champagne: "f7e8d8",
    lavender: "b19acb",
    midnight: "1c1c3c",
    sage: "b8c4ae",
    rose: "f3c0c6",
};

const ACCENT_EYES = {
    na: "open",
    floral: "happy",
    veil: "sleep",
    "pocket-square": "wink",
    "bow-tie": "glasses",
};

function getFieldValue(name) {
    const field = document.querySelector(`[name="${name}"]`);
    return field ? field.value : "";
}

function buildAvatarUrl() {
    const params = new URLSearchParams();
    const name = getFieldValue("full_name") || "";
    const seedBase = name.trim() || "guest-avatar";

    params.append("seed", seedBase);
    params.append("skinColor[]", SKIN_MAP[getFieldValue("avatar_skin_tone")] || SKIN_MAP.porcelain);
    params.append("hair[]", HAIR_STYLES[getFieldValue("avatar_hair_style")] || HAIR_STYLES.short);
    params.append("hairColor[]", HAIR_COLORS[getFieldValue("avatar_hair_color")] || HAIR_COLORS.espresso);
    params.append("eyes[]", ACCENT_EYES[getFieldValue("avatar_accent")] || ACCENT_EYES.na);
    params.append("mouth[]", getFieldValue("avatar_accent") === "bow-tie" ? "smirk" : "smile");
    params.append("nose[]", "mediumRound");
    params.append("backgroundColor[]", BACKGROUND_MAP[getFieldValue("avatar_outfit_color")] || BACKGROUND_MAP.lavender);
    params.append("size", "240");
    params.append("translateY", "-6");

    return `https://api.dicebear.com/9.x/personas/svg?${params.toString()}`;
}

function initAvatarStudio() {
    const preview = document.querySelector("[data-avatar-preview]");
    if (!preview) {
        return;
    }

    const update = () => {
        preview.src = buildAvatarUrl();
    };

    FIELD_NAMES.forEach((name) => {
        const input = document.querySelector(`[name='${name}']`);
        if (!input) {
            return;
        }
        const event = input.tagName === "SELECT" ? "change" : "input";
        input.addEventListener(event, update);
    });

    update();
}

document.addEventListener("DOMContentLoaded", initAvatarStudio);
