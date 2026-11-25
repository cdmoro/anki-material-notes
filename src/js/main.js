const card = document.querySelector(".card");
const examples = document.querySelectorAll(".card-example");
const notes = document.querySelectorAll(".card-example .note");
const exampleSelect = document.querySelector("#example");
const colorSelect = document.querySelector("#color");
const finishes = document.querySelectorAll("[data-finish]");
const templatePreviews = new Map();
const optionLabelPreference = "note-mc2-option-labels";
const answerFeedbackPreference = "note-mc2-answer-feedback";
const optionLayoutPreference = "note-mc2-option-layout";
const initialOptionCount = 4;
const savedAnswerFeedback = readPreference(answerFeedbackPreference);
let currentAnswerFeedback = ["all", "mistakes"].includes(savedAnswerFeedback) ? savedAnswerFeedback : "all";
const labelStyleValues = ["upper-alpha", "decimal", "arabic-indic", "lower-roman", "lower-greek", "georgian", "armenian", "cjk-ideographic", "hebrew", "japanese-informal", "none"];
const savedOptionLabels = readPreference(optionLabelPreference);
const initialOptionLabels = labelStyleValues.includes(savedOptionLabels) ? savedOptionLabels : "upper-alpha";
const keys = {
    example: "note-example",
    style: "note-card-style",
    theme: "note-dark-theme",
    view: "note-view",
    centered: "note-centered",
    templateStyle: "note-template-style",
};
let templateStyle = readPreference(keys.templateStyle) === "tags" ? "tags" : "classes";

async function updateProjectVersion() {
    try {
        const response = await fetch("./manifest.json", { cache: "no-cache" });
        if (!response.ok) return;

        const { version } = await response.json();
        if (typeof version === "string" && version) {
            document.getElementById("project-link").textContent = `Project (v${version})`;
        }
    } catch {
        // Keep the project link available if the manifest cannot be loaded.
    }
}

updateProjectVersion();

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
    if (exampleSelect.value.startsWith("multiple-choice-2")) setAnswerVisible(false);
    savePreference(keys.example, exampleSelect.value);
    window.scrollTo(0, 0);
});

function availableFinishes(color) {
    return ["base", "filled", "outlined"];
}

const savedVariant = readPreference(keys.style) ?? readPreference("note-variant") ?? "";
const savedStyle = /^note-(.+)-(base|filled|outlined)$/.exec(savedVariant);
const savedPalette = savedStyle?.[1] || savedVariant.replace(/^note-/, "");
colorSelect.value = (savedPalette === "white" ? "inverted" : savedPalette) || "base";

let finish = (colorSelect.value && savedStyle?.[2]) || "base";
if (!colorSelect.value) colorSelect.value = "base";
let appliedVariant = "";

function updateTemplatePreviews() {
    for (const [note, { code, content, raw }] of templatePreviews) {
        if (raw) {
            const classes = styleClasses(note);
            const standalone = content
                .replace(/\{\{mfc_shuffle_default\}\}/g, "false")
                .replace(/const optionLabels = "[^"]+";/, `const optionLabels = "${selectedOptionLabelStyle()}";`)
                .replace(/const defaultOptionLayout = \d+;/, `const defaultOptionLayout = ${selectedOptionLayout(note)};`)
                .replace(/const answerColoring = "[^"]+";/, `const answerColoring = "${currentAnswerFeedback}";`);
            const styled = standalone.replace(/\{\{Tags\}\}/g, templateStyle === "tags" ? "{{Tags}}" : classes);
            code.textContent = note.closest(".multiple-choice-js-example") ? limitMultipleChoiceTemplate(styled) : styled;
        } else {
            const classes = templateClassName(note);
            const optionStyle = note.closest(".multiple-choice-js-example")
                ? selectedOptionLabelStyle() : null;
            const configuredContent = optionStyle
                ? content.replace(/<ol type="A"[^>]*>/, `<ol type="A" style="list-style-type: ${optionStyle};"${optionStyle === "none" ? ' class="mc2-no-labels"' : ""}>`)
                : content;
            code.textContent = '<div class="' + classes + '">\n' + configuredContent + '\n</div>';
        }
    }
}

function limitMultipleChoiceTemplate(template) {
    const count = selectedOptionCount();
    let limited = template;
    for (let index = count; index < 10; index++) {
        const letter = String.fromCharCode(65 + index);
        const field = `Option ${letter}`;
        limited = limited.replace(new RegExp(`\\s*\\{\\{#${field}\\}\\}[\\s\\S]*?\\{\\{/${field}\\}\\}`, "g"), "");
    }
    return limited;
}

function styleClasses(note) {
    return Array.from(note.classList)
        .filter(name => name.startsWith("note-") || name.startsWith("Material::note-"))
        .join(" ");
}

function templateClassName(note) {
    const classes = Array.from(note.classList);
    const structural = classes.filter(name => name !== "mc2-base-default" && !name.startsWith("note-") && !name.startsWith("Material::note-"));
    const styles = classes.filter(name => name.startsWith("note-") || name.startsWith("Material::note-"));
    if (templateStyle === "tags") structural.push("{{Tags}}");
    else structural.push(...styles);
    return structural.join(" ");
}

function selectedOptionLabelStyle() {
    return document.querySelector("[data-mc2-label-select]")?.value || initialOptionLabels || "upper-alpha";
}

function selectedOptionLayout(note) {
    const value = note.closest(".card-example")?.querySelector("[data-mc2-layout-select]")?.value;
    return value === "2" ? 2 : 1;
}

function selectedOptionCount() {
    return Number(document.querySelector("[data-mc2-count-select]")?.value) || initialOptionCount;
}

function updateVariant() {
    const color = colorSelect.value;
    const allowed = availableFinishes(color);
    if (!allowed.includes(finish)) finish = "base";

    const variant = color.startsWith("flag-") && finish === "base" ? "note-" + color
        : color === "base" && finish === "base" ? ""
        : "note-" + color + "-" + finish;
    notes.forEach(note => {
        if (appliedVariant) note.classList.remove(appliedVariant);
        note.classList.toggle("mc2-base-default", !variant);
        if (variant) note.classList.add(variant);
    });
    appliedVariant = variant;
    updateTemplatePreviews();

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
    function select(enabled) {
        update(enabled);
        savePreference(key, enabled);
    }
    update(initialValue);
    button.addEventListener("click", () => {
        select(button.getAttribute("aria-pressed") !== "true");
    });
    return select;
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
    notes.forEach(note => note.classList.toggle("note-centered", enabled));
    updateTemplatePreviews();
});

const storedView = readPreference(keys.view) ?? readPreference("note-side");
const showAnswer = storedView === "true" || storedView === "back";
const wrongChoices = document.querySelectorAll("[data-preview-wrong-choice]");
const multipleChoicePreviewSelections = new Map();
const setAnswerVisible = setupToggle("side", keys.view, showAnswer, enabled => {
    card.classList.toggle("front-side", !enabled);
    wrongChoices.forEach(choice => choice.classList.toggle("wrong-answer", enabled));
    updateMultipleChoice2Preview(enabled);
});

function normalizeMultipleChoiceAnswers(raw, available) {
    const text = raw.trim();
    const answerPattern = /^(?:[A-Z]|\d+)(?:(?:\s*,\s*|\s+)(?:[A-Z]|\d+))*$/i;
    if (!text || !answerPattern.test(text)) return [];
    return (text.toUpperCase().match(/[A-Z]|\d+/g) || []).map(token => {
        if (/^[A-Z]$/.test(token)) return token;
        const number = Number(token);
        return number >= 1 && number <= 10 ? String.fromCharCode(64 + number) : null;
    }).filter(choice => choice && available.has(choice));
}

function updateMultipleChoice2Preview(showAnswer) {
    document.querySelectorAll(".multiple-choice-js-example").forEach(example => {
        const count = selectedOptionCount();
        const answers = example.querySelector('[data-example-field="Correct Answers"]')?.textContent.trim() || "";
        const allOptions = Array.from(example.querySelectorAll("[data-choice]"));
        const options = allOptions.slice(0, count);
        allOptions.forEach((option, index) => { option.hidden = index >= count; });
        const available = new Set(options.map(option => option.dataset.choice));
        const correct = new Set(normalizeMultipleChoiceAnswers(answers, available));
        const selected = multipleChoicePreviewSelections.get(example.id) || new Set();
        options.forEach(option => {
            const input = option.querySelector("input");
            if (!input) return;
            if (showAnswer) input.checked = selected.has(option.dataset.choice);
            const isCorrect = correct.has(option.dataset.choice);
            const wasSelected = input.checked;
            const highlightCorrect = isCorrect && (currentAnswerFeedback === "all" || !wasSelected);
            const highlightWrong = !isCorrect && (currentAnswerFeedback === "all" || wasSelected);
            option.classList.toggle("correct-answer", showAnswer && highlightCorrect);
            option.classList.toggle("wrong-answer", showAnswer && highlightWrong);
            option.classList.toggle("missed-answer", showAnswer && !wasSelected && isCorrect);
            input.disabled = showAnswer;
        });
        const feedback = example.querySelector("[data-mc2-feedback]");
        if (feedback) feedback.hidden = true;
    });
}

const optionLabelSelects = document.querySelectorAll("[data-mc2-label-select]");
optionLabelSelects.forEach(select => {
    select.value = initialOptionLabels;
    select.addEventListener("change", () => {
        optionLabelSelects.forEach(other => { other.value = select.value; });
        savePreference(optionLabelPreference, select.value);
        updateMultipleChoice2Labels(select.value);
        updateTemplatePreviews();
    });
});

const optionCountSelects = document.querySelectorAll("[data-mc2-count-select]");
optionCountSelects.forEach(select => {
    select.value = String(initialOptionCount);
    select.addEventListener("change", () => {
        optionCountSelects.forEach(other => { other.value = select.value; });
        document.querySelectorAll(".multiple-choice-js-example").forEach(example => {
            multipleChoicePreviewSelections.set(example.id, new Set());
            example.querySelectorAll(".question-options input").forEach(input => { input.checked = false; });
        });
        document.querySelectorAll(".multiple-choice-js-example").forEach(ensureMultipleChoicePreviewOptions);
        updateMultipleChoice2Preview(card.classList.contains("front-side") === false);
        updateTemplatePreviews();
        updateMultipleChoice2Fields();
    });
});

const answerFeedbackSelects = document.querySelectorAll("[data-mc2-feedback-select]");
answerFeedbackSelects.forEach(select => {
    select.value = currentAnswerFeedback;
    select.addEventListener("change", () => {
        answerFeedbackSelects.forEach(other => { other.value = select.value; });
        currentAnswerFeedback = select.value;
        savePreference(answerFeedbackPreference, select.value);
        updateMultipleChoice2Preview(card.classList.contains("front-side") === false);
        updateTemplatePreviews();
    });
});

const optionLayoutSelects = document.querySelectorAll("[data-mc2-layout-select]");
optionLayoutSelects.forEach(select => {
    const example = select.closest(".card-example");
    const preference = `${optionLayoutPreference}-${example?.id || "default"}`;
    const saved = readPreference(preference);
    select.value = saved === "2" ? "2" : "1";
    example?.querySelectorAll(".question-options ol").forEach(list => {
        list.classList.toggle("mc2-two-columns", select.value === "2");
        list.classList.toggle("mc2-no-labels", select.value === "2" || selectedOptionLabelStyle() === "none");
    });
    select.addEventListener("change", () => {
        const layout = select.value === "2" ? "2" : "1";
        savePreference(preference, layout);
        example?.querySelectorAll(".question-options ol").forEach(list => {
            list.classList.toggle("mc2-two-columns", layout === "2");
            list.classList.toggle("mc2-no-labels", layout === "2" || selectedOptionLabelStyle() === "none");
        });
        updateTemplatePreviews();
    });
});

function updateMultipleChoice2Labels(style) {
    document.querySelectorAll(".multiple-choice-js-example .question-options ol").forEach(list => {
        list.style.listStyleType = style;
        list.style.removeProperty("--mc2-list-style");
        list.classList.toggle("mc2-no-labels", style === "none" || selectedOptionLayout(list) === 2);
    });
    templatePreviews.forEach(({ code, content, raw }, note) => {
        if (!raw && note.closest(".multiple-choice-js-example")) {
            const configuredContent = content.replace(/<ol type="A">/, `<ol type="A" style="list-style-type: ${style};" class="${style === "none" ? "mc2-no-labels" : ""}">`);
            code.textContent = '<div class="' + note.className + '">\n' + configuredContent + '\n</div>';
        }
    });
}

function ensureMultipleChoicePreviewOptions(example) {
    const list = example.querySelector(".question-options ol");
    if (!list) return;
    const optionSamples = example.id === "multiple-choice-2-single"
        ? ["Jupiter", "Mercury", "Earth", "Saturn", "Uranus", "Neptune", "Kepler-22b", "Proxima Centauri b"]
        : ["Saturn", "Neptune", "Earth", "Mars", "Venus", "Mercury", "Kepler-22b", "Proxima Centauri b"];
    const present = new Set(Array.from(list.querySelectorAll("[data-choice]"), option => option.dataset.choice));
    for (let index = 2; index < 10; index++) {
        const letter = String.fromCharCode(65 + index);
        if (present.has(letter)) continue;
        const option = document.createElement("li");
        option.dataset.choice = letter;
        option.dataset.exampleField = `Option ${letter}`;
        option.dataset.exampleIf = `Option ${letter}`;
        option.textContent = optionSamples[index - 2];
        list.append(option);

        const input = document.createElement("input");
        const correctCount = new Set(normalizeMultipleChoiceAnswers(
            example.querySelector('[data-example-field="Correct Answers"]')?.textContent.trim() || "",
            new Set(Array.from(list.querySelectorAll("[data-choice]"), item => item.dataset.choice))
        )).size;
        input.type = correctCount > 1 ? "checkbox" : "radio";
        input.name = example.id + "-preview-answer";
        input.value = letter;
        input.addEventListener("change", () => {
            const selected = multipleChoicePreviewSelections.get(example.id) || new Set();
            if (input.type === "radio") selected.clear();
            if (input.checked) selected.add(letter);
            else selected.delete(letter);
            multipleChoicePreviewSelections.set(example.id, selected);
            updateMultipleChoice2Preview(false);
        });
        const label = document.createElement("label");
        label.append(input, document.createTextNode(" "), document.createTextNode(optionSamples[index - 2]));
        option.replaceChildren(label);
    }
}

function updateMultipleChoice2Fields() {
    const count = selectedOptionCount();
    templatePreviews.forEach(({ code, content, raw }, note) => {
        if (raw && note.closest(".multiple-choice-js-example")) {
            code.textContent = limitMultipleChoiceTemplate(content
                .replace(/const optionLabels = "[^"]+";/, `const optionLabels = "${selectedOptionLabelStyle()}";`)
                .replace(/const answerColoring = "[^"]+";/, `const answerColoring = "${currentAnswerFeedback}";`));
        }
    });
    document.querySelectorAll(".multiple-choice-js-example [data-example-field^='Option ']").forEach(field => {
        const index = field.dataset.exampleField.charCodeAt(7) - 65;
        field.hidden = index >= count;
    });
    document.querySelectorAll(".multiple-choice-js-example .question-options li[data-example-if]").forEach(field => {
        field.hidden = field.dataset.exampleIf.charCodeAt(7) - 65 >= count;
    });
    document.querySelectorAll(".multiple-choice-js-example .example-fields").forEach(panel => {
        const example = panel.closest(".card-example");
        const rows = panel.querySelectorAll("dl > div");
        rows.forEach(row => {
            const name = row.querySelector("dt code")?.textContent || "";
            const match = /^Option ([A-J])$/.exec(name);
            if (match) row.hidden = match[1].charCodeAt(0) - 65 >= count;
        });
        const help = panel.querySelector("p");
        if (help) {
            const optionNames = Array.from({ length: Math.max(0, count - 2) }, (_, index) => `Option ${String.fromCharCode(67 + index)}`);
            const names = new Intl.ListFormat("en").format(optionNames);
            help.textContent = `Create a note type with the fields listed below. Optional fields can be left blank on individual notes. ${example.dataset.fieldsHelp}`;
            const fieldInstruction = count > 2 ? `Add ${names} as optional fields.` : "";
            help.textContent = `${fieldInstruction} ${help.textContent}`.trim();
        }
    });
}

document.querySelectorAll(".multiple-choice-js-example").forEach(example => {
    ensureMultipleChoicePreviewOptions(example);
    const answers = example.querySelector('[data-example-field="Correct Answers"]')?.textContent.trim() || "";
    const options = Array.from(example.querySelectorAll("[data-choice]"));
    const available = new Set(options.map(option => option.dataset.choice));
    const correctCount = new Set(normalizeMultipleChoiceAnswers(answers, available)).size;
    const list = example.querySelector(".question-options ol");
    list?.classList.add("mc2-labeled");
    list?.classList.toggle("mc2-two-columns", selectedOptionLayout(example) === 2);
    if (list) {
        list.style.listStyleType = initialOptionLabels;
    }
    list?.classList.toggle("mc2-no-labels", initialOptionLabels === "none" || selectedOptionLayout(example) === 2);
    options.forEach(option => {
        if (option.querySelector("input")) return;
        const label = document.createElement("label");
        const input = document.createElement("input");
        input.type = correctCount > 1 ? "checkbox" : "radio";
        input.name = example.id + "-preview-answer";
        input.value = option.dataset.choice;
        input.addEventListener("change", () => {
            const selected = multipleChoicePreviewSelections.get(example.id) || new Set();
            if (input.type === "radio") selected.clear();
            if (input.checked) selected.add(option.dataset.choice);
            else selected.delete(option.dataset.choice);
            multipleChoicePreviewSelections.set(example.id, selected);
            updateMultipleChoice2Preview(false);
        });
        label.append(input, document.createTextNode(" "), ...Array.from(option.childNodes));
        option.replaceChildren(label);
    });
});
updateMultipleChoice2Labels(initialOptionLabels);
updateMultipleChoice2Fields();
updateMultipleChoice2Preview(showAnswer);

document.querySelectorAll("[data-hint-field] .hint").forEach(link => {
    const hint = document.getElementById(link.getAttribute("aria-controls"));
    link.addEventListener("click", event => {
        event.preventDefault();
        link.hidden = true;
        hint.hidden = false;
        hint.focus();
    });
});

function dedent(html) {
    const lines = html.replace(/^\s*\n/, "").trimEnd().split("\n");
    const indent = Math.min(...lines.filter(line => line.trim()).map(line => line.match(/^ */)[0].length));
    return lines.map(line => line.slice(indent)).join("\n");
}

function templateContent(element) {
    return dedent(element.innerHTML).replace(/^(?=.)/gm, "    ");
}

function readExampleTemplates(preview) {
    const back = preview.cloneNode(true);
    back.querySelectorAll(".mc2-base-default").forEach(note => note.classList.remove("mc2-base-default"));
    const front = back.querySelector(".note.front");
    const fields = [];

    back.querySelectorAll("img[loading]").forEach(image => image.removeAttribute("loading"));
    back.querySelectorAll("[data-example-sound]").forEach(button => {
        button.replaceWith("[sound:" + button.dataset.exampleSound + "]");
    });
    back.querySelectorAll("[data-example-field], [data-hint-field]").forEach(element => {
        const hint = element.dataset.hintField;
        const name = hint ?? element.dataset.exampleField;
        const html = element.hasAttribute("data-example-html");
        const optional = Boolean(hint) || element.closest("[data-example-if]")?.dataset.exampleIf === name;
        const image = element.matches("img");
        element.removeAttribute("data-example-field");
        element.removeAttribute("data-example-html");

        const content = hint ? element.querySelector("[aria-controls] + span").textContent.trim()
            : image ? element.outerHTML
            : html ? dedent(element.innerHTML)
            : element.textContent.trim();
        fields.push({ name, html, optional, content });

        if (hint || image) {
            element.replaceWith(hint ? "{{hint:" + name + "}}" : "{{" + name + "}}");
        } else {
            element.textContent = "{{" + name + "}}";
        }
    });
    back.querySelectorAll("[data-example-if]").forEach(element => {
        const name = element.dataset.exampleIf;
        const indent = element.previousSibling.textContent.match(/ *$/)[0];
        element.removeAttribute("data-example-if");
        element.before("{{#" + name + "}}\n" + indent);
        element.after("\n" + indent + "{{/" + name + "}}");
    });

    const frontContent = templateContent(front);
    front.replaceWith("{{FrontSide}}");
    const divider = back.querySelector(".answer-divider");
    divider.removeAttribute("class");
    divider.id = "answer";
    return { fields, frontContent, backContent: templateContent(back) };
}

function codeBlock(content) {
    const pre = document.createElement("pre");
    const code = document.createElement("code");
    pre.tabIndex = 0;
    code.textContent = content;
    pre.append(code);
    return pre;
}

function copyAction(label, getText, failureMessage) {
    const controls = document.createElement("div");
    const button = document.createElement("button");
    const status = document.createElement("span");
    controls.className = "copy-controls";
    button.type = "button";
    button.textContent = label;
    status.setAttribute("role", "status");
    controls.append(button, status);

    let resetStatus;
    button.addEventListener("click", async () => {
        window.clearTimeout(resetStatus);
        status.textContent = "";
        try {
            await navigator.clipboard.writeText(getText());
            status.textContent = "Copied!";
            resetStatus = window.setTimeout(() => { status.textContent = ""; }, 2500);
        } catch {
            status.textContent = failureMessage;
        }
    });

    return { controls, button, status };
}

function renderTemplatePreview(panel, label, note, content) {
    const pre = codeBlock("");
    const code = pre.firstElementChild;
    const { controls, button, status } = copyAction("Copy " + label.toLowerCase(), () => code.textContent,
        "Couldn’t copy. Select the code below to copy it manually.");
    panel.append(controls, pre);

    const directory = note.closest(".card-example").dataset.templateDirectory;
    if (!directory) {
        templatePreviews.set(note, { code, content });
        return;
    }

    const templateName = directory.split("/").pop();
    const localTemplate = window.materialNotesSources?.templates?.[templateName]?.[label.toLowerCase()];
    if (localTemplate) {
        templatePreviews.set(note, { code, content: localTemplate.trim(), raw: true });
        updateTemplatePreviews();
        return;
    }

    button.disabled = true;
    fetch(directory + "/" + label.toLowerCase() + ".html").then(async response => {
        if (!response.ok) throw new Error("Template unavailable");
        const template = (await response.text()).trim();
        const body = template.slice(template.indexOf("\n") + 1, template.lastIndexOf("\n"));
        templatePreviews.set(note, { code, content: body });
        updateTemplatePreviews();
        button.disabled = false;
    }).catch(() => {
        status.textContent = "Couldn’t load the template.";
        pre.hidden = true;
    });
}

function renderExampleFields(panel, example, fields) {
    const list = document.createElement("dl");
    panel.classList.add("example-fields");
    panel.tabIndex = 0;

    const instructions = [];
    if (fields.some(({ name }) => name === "Front")) {
        const custom = fields.filter(({ name }) => name !== "Front" && name !== "Back").map(({ name }) => name);
        if (custom.length) {
            const names = new Intl.ListFormat("en").format(custom);
            instructions.push("Add " + names + " to the Basic note type’s fields.");
        }
    } else {
        instructions.push("Create a note type with the fields listed below.");
    }
    if (fields.some(({ optional }) => optional)) {
        instructions.push("Optional fields can be left blank on individual notes.");
    }
    if (fields.some(({ html }) => html)) {
        instructions.push("Paste HTML values into Anki’s field HTML editor.");
    }
    if (example.dataset.fieldsHelp) {
        instructions.push(example.dataset.fieldsHelp);
    }
    if (example.querySelector("[data-example-sound]")) {
        instructions.push("Replace each sample sound filename with the corresponding audio file in your Anki collection.");
    }
    if (instructions.length) {
        const description = document.createElement("p");
        description.textContent = instructions.join(" ");
        panel.append(description);
    }

    fields.forEach(({ name, html, optional, content }) => {
        const row = document.createElement("div");
        const term = document.createElement("dt");
        const fieldName = document.createElement("code");
        const format = document.createElement("span");
        const value = document.createElement("dd");
        fieldName.textContent = name;
        format.textContent = html ? "HTML" : "Text";
        if (optional) format.textContent += " · Optional";
        term.append(fieldName, format);
        if (html) {
            const { controls, button } = copyAction("Copy HTML", () => content,
                "Couldn’t copy. Select the code below to copy it manually.");
            button.setAttribute("aria-label", "Copy HTML for " + name);
            value.append(controls, codeBlock(content));
        } else {
            value.textContent = content;
        }
        row.append(term, value);
        list.append(row);
    });
    panel.append(list);
}

const stylesheetUrl = document.getElementById("card-styles").href;
const stylesheetText = window.materialNotesSources?.styles
    ? Promise.resolve(window.materialNotesSources.styles)
    : fetch(stylesheetUrl).then(response => {
        if (!response.ok) throw new Error("Couldn’t load the stylesheet.");
        return response.text();
    });

function renderStylePanel(panel) {
    const description = document.createElement("p");
    const guide = document.createElement("a");
    guide.href = "https://github.com/cdmoro/anki-material-notes/blob/main/docs/using-style-tags.md";
    guide.textContent = "How to use style tags";
    description.append(
        "In Anki, open Cards… and paste this CSS into Styling. All examples, palettes, and finishes use the same stylesheet. ",
        guide
    );
    const { controls, button, status } = copyAction("Copy style", () => css,
        "Couldn’t copy. Use Download CSS to get the stylesheet.");
    const download = document.createElement("a");
    download.href = stylesheetUrl;
    download.download = "styles.css";
    download.textContent = "Download CSS";
    controls.insertBefore(download, status);
    panel.classList.add("example-style");
    panel.append(description, controls);

    let css;
    button.disabled = true;
    stylesheetText.then(text => {
        css = text;
        button.disabled = false;
    }, () => {
        status.textContent = "Couldn’t load the stylesheet. Try Download CSS.";
    });
}

function setupTabIcon(pathData) {
    const namespace = "http://www.w3.org/2000/svg";
    const icon = document.createElementNS(namespace, "svg");
    const path = document.createElementNS(namespace, "path");
    icon.setAttribute("viewBox", "0 0 16 16");
    icon.setAttribute("aria-hidden", "true");
    path.setAttribute("d", pathData);
    icon.append(path);
    return icon;
}

const reviewWindowTemplate = document.getElementById("review-window-template");
examples.forEach(example => {
    const preview = example.querySelector(".note.back");
    const reviewWindow = reviewWindowTemplate.content.cloneNode(true);
    const reviewContent = reviewWindow.querySelector(".review-content");
    const showAnswerButton = reviewWindow.querySelector(".review-show-answer");
    const goodButton = reviewWindow.querySelector(".review-good");
    showAnswerButton.addEventListener("click", () => {
        setAnswerVisible(true);
        goodButton.focus();
    });
    reviewWindow.querySelectorAll(".review-ratings button").forEach(button => {
        button.addEventListener("click", () => {
            setAnswerVisible(false);
            showAnswerButton.focus();
        });
    });
    preview.before(reviewWindow);
    reviewContent.append(preview);

    const { fields, frontContent, backContent } = readExampleTemplates(preview);
    const setup = document.createElement("section");
    const heading = document.createElement("h3");
    setup.className = "example-setup";
    heading.id = example.id + "-setup-title";
    heading.textContent = "Card setup";
    setup.setAttribute("aria-labelledby", heading.id);
    setup.append(heading);

    const styleControl = document.createElement("label");
    const styleCheckbox = document.createElement("input");
    styleControl.className = "template-style-toggle";
    styleCheckbox.type = "checkbox";
    styleCheckbox.checked = templateStyle === "tags";
    styleCheckbox.setAttribute("role", "switch");
    styleControl.append(styleCheckbox, document.createTextNode(" Use {{Tags}} instead of classes in templates"));
    styleCheckbox.addEventListener("change", () => {
        templateStyle = styleCheckbox.checked ? "tags" : "classes";
        document.querySelectorAll(".template-style-toggle input").forEach(input => {
            input.checked = styleCheckbox.checked;
        });
        savePreference(keys.templateStyle, templateStyle);
        updateTemplatePreviews();
    });
    setup.append(styleControl);

    const tabList = document.createElement("div");
    tabList.className = "example-setup-tabs";
    tabList.setAttribute("role", "tablist");
    tabList.setAttribute("aria-labelledby", heading.id);
    setup.append(tabList);

    const tabs = [
        ["Front", "M3 3.5h10a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1v-7a1 1 0 0 1 1-1Zm2 3h6",
            panel => renderTemplatePreview(panel, "Front", preview.querySelector(".note.front"), frontContent)],
        ["Back", "M3 3.5h10a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1v-7a1 1 0 0 1 1-1Zm2 6h6",
            panel => renderTemplatePreview(panel, "Back", preview, backContent)],
        ["Style", "M3 2.5h10v5H3zm2 5v1.25h6V7.5M7 8.75V13a1 1 0 0 0 2 0V8.75M6 2.5v2",
            renderStylePanel],
        ["Fields", "M5.5 4h8m-8 4h8m-8 4h8M2.5 4h.1m-.1 4h.1m-.1 4h.1",
            panel => renderExampleFields(panel, example, fields)],
    ].map(([label, iconPath, renderPanel]) => {
        const tab = document.createElement("button");
        const panel = document.createElement("div");
        const id = example.id + "-setup-" + label.toLowerCase();

        tab.type = "button";
        tab.id = id + "-tab";
        tab.append(setupTabIcon(iconPath), label);
        tab.setAttribute("role", "tab");
        tab.setAttribute("aria-controls", id);
        tabList.append(tab);

        panel.id = id;
        panel.setAttribute("role", "tabpanel");
        panel.setAttribute("aria-labelledby", tab.id);
        renderPanel(panel);
        setup.append(panel);
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
    example.append(setup);
});
updateMultipleChoice2Fields();
updateTemplatePreviews();
