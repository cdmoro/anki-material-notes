const NOTE_DARK_THEME_KEY = "note-dark-theme";
const NOTE_SIDE_KEY = "note-side";
const NOTE_VARIANT_KEY = "note-variant";
const NOTE_CENTERED_KEY = "note-centered";
const NOTE_MARKED_KEY = "note-marked";
const NOTE_FLAG_KEY = "note-flag";

const variants = Array.from(document.querySelectorAll("#variant option"))
    .map((opt) => opt.value)
    .filter(Boolean);

function setTheme(isDark) {
    document.getElementById("dark").classList.toggle("active", isDark);

    document
        .querySelectorAll(".card")
        .forEach((el) => el.classList.toggle("nightMode", isDark));

    document.body.classList.toggle("nightMode", isDark);

    localStorage.setItem(NOTE_DARK_THEME_KEY, isDark);
}

function toggleTheme() {
    setTheme(localStorage?.getItem(NOTE_DARK_THEME_KEY) !== "true");
}

function setSide(side) {
    document.getElementById("side").classList.toggle("active", side === 'back');

    document
        .querySelector(".card")
        .classList.toggle("front-side", side === "front");

    localStorage.setItem(NOTE_SIDE_KEY, side);
}

function toggleSide() {
    setSide(localStorage.getItem(NOTE_SIDE_KEY) === 'front' ? 'back' : 'front');
}

function setVariant(variant) {
    document.querySelectorAll(".note").forEach((el) => {
        variants.forEach(variant => {
            el.classList.remove(`Material::${variant}`);
        });

        if (variant) {
            el.classList.add(`Material::${variant}`);
        }
    });

    localStorage.setItem(NOTE_VARIANT_KEY, variant);
}

function setCentered(isCentered) {
    document.getElementById("centered").classList.toggle("active", isCentered);

    document.querySelectorAll(".note").forEach((el) => {
        el.classList.toggle("Material::note-centered", isCentered);
    });

    localStorage.setItem(NOTE_CENTERED_KEY, isCentered);
}

function toggleCentered() {
    setCentered(localStorage?.getItem(NOTE_CENTERED_KEY) !== 'true');
}

// function toggleMarked(isMarked) {
//     document.querySelectorAll("#_mark").forEach((el) => {
//         if (isMarked) {
//             el.removeAttribute("hidden");
//         } else {
//             el.setAttribute("hidden", "");
//         }
//     });

//     localStorage.setItem(NOTE_MARKED_KEY, isMarked);
// }

// function setFlag(flag) {
//     document.querySelectorAll("#_flag").forEach((el) => {
//         if (flag == 0) {
//             el.removeAttribute("style");
//             el.setAttribute("hidden", "");
//         } else {
//             el.setAttribute("style", `color: var(--flag-${flag});`);
//             el.removeAttribute("hidden");
//         }
//     });

//     localStorage.setItem(NOTE_FLAG_KEY, flag);
// }

// const isDark = JSON.parse(localStorage?.getItem(NOTE_DARK_THEME_KEY)) || false;
// document.getElementById("dark").checked = isDark;
// toggleTheme(isDark);

const variant = localStorage.getItem(NOTE_VARIANT_KEY) || "";
document.getElementById("variant").value = variant;
setVariant(variant);

// const side = localStorage.getItem(NOTE_SIDE_KEY) || "front";
// document.querySelector(`input[name=side][value=${side}]`).checked = true;
// toggleSide(side);

// const isCentered =
//     JSON.parse(localStorage?.getItem(NOTE_CENTERED_KEY)) || false;
// document.getElementById("centered").checked = isCentered;
// toggleCentered();
setSide(localStorage?.getItem(NOTE_SIDE_KEY));
setTheme(localStorage?.getItem(NOTE_DARK_THEME_KEY) === 'true');
setCentered(localStorage?.getItem(NOTE_CENTERED_KEY) === 'true');

// const isMarked = JSON.parse(localStorage?.getItem(NOTE_MARKED_KEY)) || false;
// document.getElementById("marked").checked = isMarked;
// toggleMarked(isMarked);

// const flag = localStorage.getItem(NOTE_FLAG_KEY) || "0";
// document.getElementById("flag").value = flag;
// setFlag(flag);