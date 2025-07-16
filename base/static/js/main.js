
// This function toggles the display of a form and clears its inputs when hidden
function toggleForm(id) {
    const formDiv = document.getElementById(id);

    const isActuallyHidden = getComputedStyle(formDiv).display === "none";

    if (isActuallyHidden) {
        formDiv.style.display = "block";
    } else {
        formDiv.style.display = "none";

        // Clear inputs when hiding
        const inputs = formDiv.querySelectorAll('input[type="text"], textarea');
        inputs.forEach(input => input.value = "");
    }
}


// Quiz explanation toggle
function toggleExplanation(index, btn) {
    const elem = document.getElementById(`explanation-${index}`);
    if (elem) {
        const isHidden = elem.style.display === "none";
        elem.style.display = isHidden ? "block" : "none";
        btn.textContent = isHidden ? "Hide Explanation" : "Show Explanation";
    }
}

// Unit Card: Only allows one to be open at a time
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".unit-toggle").forEach((checkbox) => {
        checkbox.addEventListener("change", function () {
            if (checkbox.checked) {
                document.querySelectorAll(".unit-toggle").forEach((other) => {
                    if (other !== checkbox) other.checked = false;
                });
            }
        });
    });
});

// Topic Card: Only allows one to be open at a time
document.querySelectorAll(".topic-toggle").forEach((checkbox) => {
    checkbox.addEventListener("change", function () {
        if (checkbox.checked) {
            document.querySelectorAll(".topic-toggle").forEach((other) => {
                if (other !== checkbox) other.checked = false;
            });
        }
    });
});


// Adds the CSRF token globally for HTMX actions
document.body.addEventListener("htmx:configRequest", function (event) {
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
    if (csrfToken) {
        event.detail.headers["X-CSRFToken"] = csrfToken;
    }
});

/*
    Live Resizing

    Dynamically changes height of textareas when typing
    Needed for forms.py -> MultipleChoiceQuestionForm
*/
function autoResize(el) {
    el.style.height = "0px"; // Force reset
    el.style.height = el.scrollHeight + "px"; // Set new height
}

function autoResizeTextareas(scope) {
    scope.querySelectorAll("textarea").forEach(autoResize);
}

// Live resizing
document.addEventListener("input", function (e) {
    if (e.target.tagName === "TEXTAREA") {
        autoResize(e.target);
    }
});

// After modal content is swapped in
document.body.addEventListener("htmx:afterSwap", function (e) {
    if (e.detail.target.id === "modal-body") {
        requestAnimationFrame(() => {
            autoResizeTextareas(e.detail.target);
        });
    }
});

// Bulk Question Delete --> question_bank_table.html
function initDeleteCheckboxHandlers(tableId) {
    const deleteBtn = document.getElementById(`delete-selected-btn-${tableId}`);
    const checkboxes = document.querySelectorAll(`.question-checkbox-${tableId}`);
    const selectAll = document.getElementById(`select-all-${tableId}`);

    const updateDeleteButton = () => {
        const anyChecked = Array.from(checkboxes).some(checkbox => checkbox.checked);
        deleteBtn.disabled = !anyChecked;
    };

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateDeleteButton);
    });

    if (selectAll) {
        selectAll.addEventListener('change', () => {
            checkboxes.forEach(checkbox => {
                checkbox.checked = selectAll.checked;
            });
            updateDeleteButton();
        });
    }

    updateDeleteButton();
}


// DMOJ Cooldown --> course.html
function initDmojCooldown() {
    const btn = document.getElementById("refresh-dmoj-btn");
    const msg = document.getElementById("dmoj-cooldown-msg");
    const form = btn?.closest("form");
    if (!btn || !msg || !form) {
        console.log("DMOJ elements not found");
        return;
    }

    const cooldownSeconds = 30;
    const key = "dmoj-refresh-timestamp";

    function updateCooldown() {
        const lastClick = parseInt(localStorage.getItem(key)) || 0;
        const now = Date.now();
        const diff = Math.floor((now - lastClick) / 1000);
        const remaining = cooldownSeconds - diff;

        if (remaining > 0) {
            const min = Math.floor(remaining / 60);
            const sec = remaining % 60;
            btn.disabled = true;
            msg.textContent = `Try again in ${min}m ${sec}s`;
        } else {
            btn.disabled = false;
            msg.textContent = "";
        }
    }

    setInterval(updateCooldown, 1000);
    updateCooldown();

    // Save timestamp before form actually submits
    form.addEventListener("submit", () => {
        localStorage.setItem(key, Date.now().toString());
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initDmojCooldown();
});


// Monaco Editor
function initMonacoEditor() {
    const editorMount = document.getElementById("monaco-editor");
    if (!editorMount) {
        console.log("❌ #monaco-editor not found");
        return;
    }

    require.config({
        paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@latest/min/vs' }
    });

    require(['vs/editor/editor.main'], function () {
        const editor = monaco.editor.create(editorMount, {
            value: STARTER_CODE_FROM_DJANGO,
            language: MONACO_LANGUAGE,
            theme:  getMonacoTheme(),
            fontSize: 14,
        });

        const form = document.querySelector("form[action='/submit-code/']");
        const codeInput = document.getElementById("code-input");

        if (!form || !codeInput) {
            console.log("❌ form or code input not found");
            return;
        }


        form.addEventListener("submit", function (e) {
            e.preventDefault();

            const code = editor.getValue();
            console.log("🔥 FINAL SUBMIT VALUE:", code);
            codeInput.value = code;

            setTimeout(() => form.submit(), 50);
        });
    });
}

window.addEventListener("load", initMonacoEditor);

// Update Monaco theme on theme change
const observer = new MutationObserver(() => {
    const newTheme = getMonacoTheme();
    monaco.editor.setTheme(newTheme);
});

observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme"]
});

// Close Modal on Escape
document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
        const modal = document.getElementById('modal-wrapper');
        if (modal && modal.checked) {
            modal.checked = false;
            console.log('Modal closed via Escape key');
        }
    }
});


// Debounce function to limit scroll event frequency
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Save and restore scroll position globally
document.addEventListener("DOMContentLoaded", () => {
  // Target specific scrollable container (e.g., .overflow-auto)
  const container = document.querySelector(".overflow-auto");
  if (container) {
    // Save container scroll position
    container.addEventListener("scroll", debounce(() => {
      const scrollTop = container.scrollTop;
      sessionStorage.setItem("containerScrollY", scrollTop);
      console.log("[Scroll Debug] Saving containerScrollY =", scrollTop);
    }, 100));

    // Restore container scroll position
    const savedContainerScrollY = sessionStorage.getItem("containerScrollY");
    console.log("[Scroll Debug] Retrieved containerScrollY =", savedContainerScrollY);
    if (savedContainerScrollY !== null && savedContainerScrollY !== "0") {
      console.log("[Scroll Debug] Restoring containerScrollY =", savedContainerScrollY);
      container.scrollTop = parseInt(savedContainerScrollY, 10);
    } else {
      console.log("[Scroll Debug] No valid containerScrollY found");
    }
  } else {
    // Fallback to window-level scrolling if no container is found
    window.addEventListener("scroll", debounce(() => {
      const scrollY = window.scrollY;
      sessionStorage.setItem("windowScrollY", scrollY);
      console.log("[Scroll Debug] Saving windowScrollY =", scrollY);
    }, 100));

    // Restore window scroll position
    const savedWindowScrollY = sessionStorage.getItem("windowScrollY");
    console.log("[Scroll Debug] Retrieved windowScrollY =", savedWindowScrollY);
    if (savedWindowScrollY !== null && savedWindowScrollY !== "0") {
      console.log("[Scroll Debug] Restoring windowScrollY =", savedWindowScrollY);
      window.scrollTo(0, parseInt(savedWindowScrollY, 10));
    } else {
      console.log("[Scroll Debug] No valid windowScrollY found");
    }
  }
});


// Gets the appropriate monaco theme based on DaisyUI theme -> main.js
function getMonacoTheme() {
    const theme = document.documentElement.getAttribute("data-theme");
    if (window.VALID_DARK_THEMES.includes(theme)) return "vs-dark";
    if (window.VALID_LIGHT_THEMES.includes(theme)) return "vs";
    return "vs-dark";
}
