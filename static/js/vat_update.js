function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

function showToast(message, isSuccess = true) {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white ${isSuccess ? 'bg-success' : 'bg-danger'} border-0 position-fixed m-3`;
    toast.style.top = '60px';
    toast.style.right = '20px';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    document.body.appendChild(toast);
    new bootstrap.Toast(toast).show();
    setTimeout(() => toast.remove(), 4000);
}

function getAjaxUrls() {
    const urlContainer = document.getElementById("ajax-urls");
    return {
        updateStatusURL: urlContainer?.dataset.updateStatusUrl || "",
        updateCommentURL: urlContainer?.dataset.updateCommentUrl || ""
    };
}

function sendUpdate(clientId, field, value, updateStatusURL, clientName) {
    let headerObject = null;
    if (field == "submitted") {
        headerObject = document.querySelector(".submit-label");
    }
    else if (field == "client_notified") {
        headerObject = document.querySelector(".client-notified-label");
    }
    else if (field == "paid") {
        headerObject = document.querySelector(".paid-label");
    }

    if (!headerObject) return; // Prevent errors if header element does not exist

    const contentList = headerObject.textContent.trim().split(" ");
    fetch(updateStatusURL, {
        method: "POST",
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({ client_id: clientId, field: field, value: value })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast(`Updated ${field} for client ${clientName}`);
                let newAmount = value ? parseInt(contentList[0]) + 1 : parseInt(contentList[0]) - 1;
                let newLabel = String(newAmount) + " " + contentList[1] + " " + contentList[2];
                headerObject.textContent = newLabel;
            } else {
                showToast(`Failed: ${data.error}`, false);
            }
        })
        .catch(err => {
            console.error("AJAX error:", err);
            showToast("Failed to update: " + err, false);
        });
}

function sendCommentUpdate(clientId, comment, updateCommentURL, clientName) {
    fetch(updateCommentURL, {
        method: "POST",
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({ client_id: clientId, comment: comment })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast(`Save successful for client ${clientName}`);
            } else {
                showToast(`Failed: ${data.error}`, false);
            }
        })
        .catch(err => showToast("Failed to update comment: " + err, false));
}

function bindFieldCheckboxes(updateStatusURL) {
    document.querySelectorAll(".update-field").forEach(checkbox => {
        checkbox.addEventListener("change", function () {
            sendUpdate(this.dataset.clientId, this.dataset.field, this.checked, updateStatusURL, this.dataset.clientName);
        });
    });
}

function bindCommentButtons(updateCommentURL) {
    document.querySelectorAll(".update-comment-button").forEach(button => {
        button.addEventListener("click", function () {
            const clientId = this.dataset.clientId;
            const textarea = document.querySelector(`.update-comment[data-client-id='${clientId}']`);
            const clientName = textarea?.dataset.clientName || 'Unknown';
            sendCommentUpdate(clientId, textarea.value, updateCommentURL, clientName);
        });
    });
}

function getLabel(elementText, incrementVal = true) {
    const elementList = elementText.trim().split(" ");
    const firstElement = elementList[0];
    let newElement = incrementVal ? parseInt(firstElement) + 1 : parseInt(firstElement) - 1;
    return String(newElement) + " " + elementList[1] + " " + elementList[2];
}

function bindMarkComplete(updateStatusURL) {
    document.querySelectorAll(".mark-complete").forEach(checkbox => {
        checkbox.addEventListener("change", function () {
            const clientId = this.dataset.clientId;
            const checked = this.checked;
            const clientName = this.dataset.clientName;

            let submittedLabel = document.querySelector(".submit-label");
            let clientNotifiedLabel = document.querySelector(".client-notified-label");
            let paidLabel = document.querySelector(".paid-label");

            // Only update paid field if the paid input exists on the page
            const fields = ['submitted', 'client_notified'];
            if (document.querySelector(`[data-client-id='${clientId}'][data-field='paid']`)) {
                fields.push('paid');
            }

            const payload = new URLSearchParams({ client_id: clientId });

            fields.forEach(field => {
                const box = document.querySelector(`[data-client-id='${clientId}'][data-field='${field}']`);
                if (box) box.checked = checked;
                payload.append(field, String(checked));
            });

            fetch(updateStatusURL, {
                method: "POST",
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: payload
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        showToast(`Marked all as ${checked ? 'complete' : 'incomplete'} for client ${clientName}`);

                        if (submittedLabel) submittedLabel.textContent = getLabel(submittedLabel.textContent, checked);
                        if (clientNotifiedLabel) clientNotifiedLabel.textContent = getLabel(clientNotifiedLabel.textContent, checked);
                        if (paidLabel) paidLabel.textContent = getLabel(paidLabel.textContent, checked);
                    } else {
                        showToast(`Failed: ${data.error}`, false);
                    }
                })
                .catch(err => showToast("Failed to update: " + err, false));
        });
    });
}

function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            func.apply(this, args);
        }, delay);
    };
}

function setupFiltering() {
    const nameInput = document.querySelector("input[name='search']");
    if (!nameInput) return;

    function applyFilters() {
        const name = nameInput.value.toLowerCase().trim();
        const table = document.querySelector("table.table");
        if (!table) return;

        const rows = table.querySelectorAll("tbody tr.data-row");
        let rowsCounter = 0;
        rows.forEach(row => {
            const nameCell = row.querySelector("td:nth-child(2) a");
            if (!nameCell) return;

            const matchName = !name || nameCell.textContent.toLowerCase().includes(name);
            row.style.display = matchName ? "" : "none";
            if (matchName) rowsCounter++;
        });
        if (typeof updateRowCount === "function") {
            updateRowCount(rowsCounter, rows.length);
        }
    }
    setTimeout(applyFilters, 0);
    nameInput.addEventListener("input", debounce(applyFilters, 300));
}

document.addEventListener("DOMContentLoaded", function () {
    const { updateStatusURL, updateCommentURL } = getAjaxUrls();
    bindFieldCheckboxes(updateStatusURL);
    bindCommentButtons(updateCommentURL);
    bindMarkComplete(updateStatusURL);
    setupFiltering();
});