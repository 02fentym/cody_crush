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


// Adds the CSRF token globally for HTMX actions
document.body.addEventListener("htmx:configRequest", function (event) {
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
    if (csrfToken) {
        event.detail.headers["X-CSRFToken"] = csrfToken;
    }
});