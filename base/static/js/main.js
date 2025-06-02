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
