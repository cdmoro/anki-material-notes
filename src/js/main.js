const card = document.querySelector(".card");
const examples = document.querySelectorAll(".card-example");
const notes = document.querySelectorAll(".card-example .note");
const exampleSelect = document.querySelector("#example");
const colorSelect = document.querySelector("#color");
const finishes = document.querySelectorAll("[data-finish]");
const keys = {
    example: "note-example",
    style: "note-card-style",
    theme: "note-dark-theme",
    view: "note-view",
    centered: "note-centered",
};

function readPreference(key) {
    try {
        return localStorage.getItem(key);
    } catch {
        return null;
    }
}

function savePreference(key, value) {
    try {
        localStorage.setItem(key, value);
    } catch {
        // The preview still works when storage is unavailable.
    }
}

function showSelectedExample() {
    examples.forEach(example => {
        example.hidden = example.id !== exampleSelect.value;
    });
}

exampleSelect.value = readPreference(keys.example) ?? exampleSelect.value;
if (!exampleSelect.value) exampleSelect.selectedIndex = 0;
showSelectedExample();
exampleSelect.disabled = false;
exampleSelect.addEventListener("change", () => {
    showSelectedExample();
    savePreference(keys.example, exampleSelect.value);
    window.scrollTo(0, 0);
});

function availableFinishes(color) {
    if (color === "base") return ["base", "outlined"];
    if (color === "white") return ["base"];
    return ["base", "filled", "outlined"];
}

const savedVariant = readPreference(keys.style) ?? readPreference("note-variant") ?? "";
const savedStyle = /^note-(.+)-(base|filled|outlined)$/.exec(savedVariant);
colorSelect.value = savedStyle?.[1] || savedVariant.replace(/^note-/, "") || "base";

let finish = (colorSelect.value && savedStyle?.[2]) || "base";
if (!colorSelect.value) colorSelect.value = "base";
let appliedTag = "";

function updateVariant() {
    const color = colorSelect.value;
    const allowed = availableFinishes(color);
    if (!allowed.includes(finish)) finish = "base";

    const variant = color.startsWith("flag-") && finish === "base" ? "note-" + color
        : color === "base" && finish === "base" ? ""
        : "note-" + color + "-" + finish;
    const tag = variant && "Material::" + variant;

    notes.forEach(note => {
        if (appliedTag) note.classList.remove(appliedTag);
        if (tag) note.classList.add(tag);
    });
    appliedTag = tag;

    finishes.forEach(button => {
        button.disabled = !allowed.includes(button.dataset.finish);
        button.setAttribute("aria-pressed", button.dataset.finish === finish);
    });
    savePreference(keys.style, variant);
}

colorSelect.addEventListener("change", updateVariant);
finishes.forEach(button => {
    button.addEventListener("click", () => {
        finish = button.dataset.finish;
        updateVariant();
    });
});
updateVariant();

function setupToggle(id, key, initialValue, apply) {
    const button = document.getElementById(id);
    function update(enabled) {
        button.setAttribute("aria-pressed", enabled);
        apply(enabled);
    }
    update(initialValue);
    button.addEventListener("click", () => {
        const enabled = button.getAttribute("aria-pressed") !== "true";
        update(enabled);
        savePreference(key, enabled);
    });
}

const themeButton = document.getElementById("theme-toggle");
const themeIcons = themeButton.querySelectorAll("[data-theme-icon]");
const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");
const themes = ["system", "light", "dark"];
const themeLabels = { system: "System", light: "Light", dark: "Dark" };
const savedTheme = readPreference(keys.theme);
const previousThemes = new Map([["true", "dark"], ["false", "light"]]);
let theme = themes.includes(savedTheme) ? savedTheme : previousThemes.get(savedTheme) ?? "system";

function nextTheme() {
    return themes[(themes.indexOf(theme) + 1) % themes.length];
}

function updateTheme() {
    const isDark = theme === "dark" || (theme === "system" && systemTheme.matches);
    card.classList.toggle("nightMode", isDark);
    document.body.classList.toggle("nightMode", isDark);
    themeIcons.forEach(icon => {
        icon.setAttribute("display", icon.dataset.themeIcon === theme ? "inline" : "none");
    });
    themeButton.title = "Theme: " + themeLabels[theme] + ". Switch to " + themeLabels[nextTheme()];
    themeButton.setAttribute("aria-label", themeButton.title);
}

themeButton.addEventListener("click", () => {
    theme = nextTheme();
    savePreference(keys.theme, theme);
    updateTheme();
});
systemTheme.addEventListener("change", updateTheme);
updateTheme();

setupToggle("centered", keys.centered, readPreference(keys.centered) === "true", enabled => {
    notes.forEach(note => note.classList.toggle("Material::note-centered", enabled));
});

const storedView = readPreference(keys.view) ?? readPreference("note-side");
const showAnswer = storedView !== "false" && storedView !== "front";
setupToggle("side", keys.view, showAnswer, enabled => {
    card.classList.toggle("front-side", !enabled);
});

document.querySelectorAll("[data-hint-field] .hint").forEach(link => {
    const hint = document.getElementById(link.getAttribute("aria-controls"));
    link.addEventListener("click", event => {
        event.preventDefault();
        link.hidden = true;
        hint.hidden = false;
        hint.focus();
    });
});

function indentExample(element, baseIndent) {
    const lines = element.innerHTML.trimEnd().split("\n")
        .filter((line, index) => index > 0 || line.trim());
    const indent = baseIndent ?? (lines[0]?.match(/^ */)[0].length ?? 0);
    const leadingIndent = new RegExp("^ {" + indent + "}");
    return lines.map(line => line.replace(leadingIndent, "")).join("\n");
}

examples.forEach(example => {
    const back = example.querySelector(".note.back").cloneNode(true);
    const front = back.querySelector(".note.front");
    const divider = back.querySelector(".answer-divider");
    const source = document.createElement("div");
    const heading = document.createElement("h3");
    source.className = "example-source";
    heading.id = example.id + "-source-title";
    heading.textContent = "Source code";
    source.append(heading);

    const fields = Array.from(back.querySelectorAll("[data-example-html]"), element => [
        element.dataset.exampleField, indentExample(element),
    ]);
    back.querySelectorAll("[data-hint-field]").forEach(hint => {
        hint.replaceWith("{{hint:" + hint.dataset.hintField + "}}");
    });
    back.querySelectorAll("[data-example-field]").forEach(element => {
        element.textContent = "{{" + element.dataset.exampleField + "}}";
        element.removeAttribute("data-example-field");
        element.removeAttribute("data-example-html");
    });
    const frontClass = front.classList.contains("question-card") ? "note front question-card" : "note front";
    const frontHTML = '<div class="' + frontClass + ' {{Tags}}">\n' +
        indentExample(front, 16) + '\n</div>';
    front.replaceWith("{{FrontSide}}");
    divider.removeAttribute("class");
    divider.id = "answer";
    const backHTML = '<div class="note back {{Tags}}">\n' +
        indentExample(back, 16) + '\n</div>';

    const tabList = document.createElement("div");
    tabList.className = "example-source-tabs";
    tabList.setAttribute("role", "tablist");
    tabList.setAttribute("aria-labelledby", heading.id);
    source.append(tabList);

    const tabs = [["Front", frontHTML], ["Back", backHTML], ...fields].map(([label, html]) => {
        const tab = document.createElement("button");
        const panel = document.createElement("div");
        const code = document.createElement("code");
        const pre = document.createElement("pre");
        const id = example.id + "-source-" + label.toLowerCase().replaceAll(" ", "-");

        tab.type = "button";
        tab.id = id + "-tab";
        tab.textContent = label;
        tab.setAttribute("role", "tab");
        tab.setAttribute("aria-controls", id);
        tabList.append(tab);

        panel.id = id;
        panel.setAttribute("role", "tabpanel");
        panel.setAttribute("aria-labelledby", tab.id);
        pre.tabIndex = 0;
        code.textContent = html;
        pre.append(code);
        panel.append(pre);
        source.append(panel);
        return { tab, panel };
    });

    function selectTab(selectedIndex) {
        tabs.forEach(({ tab, panel }, index) => {
            const selected = index === selectedIndex;
            tab.setAttribute("aria-selected", selected);
            tab.tabIndex = selected ? 0 : -1;
            panel.hidden = !selected;
        });
    }

    tabs.forEach(({ tab }, index) => {
        tab.addEventListener("click", () => selectTab(index));
        tab.addEventListener("keydown", event => {
            let nextIndex;
            switch (event.key) {
                case "ArrowRight": nextIndex = (index + 1) % tabs.length; break;
                case "ArrowLeft": nextIndex = (index - 1 + tabs.length) % tabs.length; break;
                case "Home": nextIndex = 0; break;
                case "End": nextIndex = tabs.length - 1; break;
                default: return;
            }
            event.preventDefault();
            selectTab(nextIndex);
            tabs[nextIndex].tab.focus();
        });
    });
    selectTab(0);
    example.append(source);
});
