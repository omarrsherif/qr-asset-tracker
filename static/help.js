const helpButton = document.querySelector(".help-button");
const helpPanel = document.getElementById("help-panel");
const helpCloseButton = document.querySelector(".help-close");

function setHelpOpen(isOpen) {
    if (!helpButton || !helpPanel) {
        return;
    }

    helpButton.setAttribute("aria-expanded", String(isOpen));
    helpPanel.hidden = !isOpen;
    document.body.style.overflow = isOpen ? "hidden" : "";
}

if (helpButton && helpPanel) {
    helpButton.addEventListener("click", () => {
        const isOpen = helpButton.getAttribute("aria-expanded") === "true";
        setHelpOpen(!isOpen);
    });
}

if (helpCloseButton) {
    helpCloseButton.addEventListener("click", () => setHelpOpen(false));
}

if (helpPanel) {
    helpPanel.addEventListener("click", (event) => {
        if (event.target === helpPanel) {
            setHelpOpen(false);
        }
    });
}

window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        setHelpOpen(false);
    }
});
