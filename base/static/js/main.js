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



// Handles the toggling of details elements and saves the last opened one in localStorage
document.addEventListener("DOMContentLoaded", function () {
    // Restore last open unit first
    const lastOpenUnitId = localStorage.getItem("lastOpenUnit");
    if (lastOpenUnitId) {
        const unit = document.getElementById(lastOpenUnitId);
        if (unit) {
            unit.setAttribute("open", "open");
        }
    }

    // Then restore last open topic
    const lastOpenTopicId = localStorage.getItem("lastOpenTopic");
    if (lastOpenTopicId) {
        const topic = document.getElementById(lastOpenTopicId);
        if (topic) {
            topic.setAttribute("open", "open");
        }
    }

    // Accordion for units
    const unitDetails = document.querySelectorAll("details[id^='unit-']");
    unitDetails.forEach(unit => {
        unit.addEventListener("toggle", function () {
            if (unit.open) {
                unitDetails.forEach(other => {
                    if (other !== unit) {
                        other.removeAttribute("open");
                    }
                });
                localStorage.setItem("lastOpenUnit", unit.id);
            } else {
                localStorage.removeItem("lastOpenUnit");

                // Also close any open topic when unit closes
                localStorage.removeItem("lastOpenTopic");
            }
        });
    });

    // Accordion for topics (only inside open unit)
    const topicDetails = document.querySelectorAll("details[id^='topic-']");
    topicDetails.forEach(topic => {
        topic.addEventListener("toggle", function () {
            if (topic.open) {
                topicDetails.forEach(other => {
                    if (other !== topic) {
                        other.removeAttribute("open");
                    }
                });
                localStorage.setItem("lastOpenTopic", topic.id);
            } else {
                localStorage.removeItem("lastOpenTopic");
            }
        });
    });
});

// Quiz explanation toggle
function toggleExplanation(index, btn) {
    const elem = document.getElementById(`explanation-${index}`);
    if (elem) {
        const isHidden = elem.style.display === "none";
        elem.style.display = isHidden ? "block" : "none";
        btn.textContent = isHidden ? "Hide Explanation" : "Show Explanation";
    }
}

// Opens modal for adding units or topics
function openModal(type, unitId = null) {
    const modalTitle = document.getElementById("modal-title");
    const formType = document.getElementById("form-type");
    const unitInput = document.getElementById("unit-id");
    const formFields = document.getElementById("form-fields");

    if (type === "unit") {
        modalTitle.textContent = "Add Unit";
        formType.value = "unit";
        unitInput.value = "";

        formFields.innerHTML = `
        <input name="title" placeholder="Unit title" class="input input-bordered w-full" required>
        <textarea name="description" placeholder="Unit description" class="textarea textarea-bordered w-full"></textarea>
    `;
    } else if (type === "topic") {
        modalTitle.textContent = "Add Topic";
        formType.value = "topic";
        unitInput.value = unitId;

        formFields.innerHTML = `
        <input name="title" placeholder="Topic title" class="input input-bordered w-full" required>
        <textarea name="description" placeholder="Topic description" class="textarea textarea-bordered w-full"></textarea>
    `;
    }
}