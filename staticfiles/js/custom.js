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

function bindMarkComplete(updateStatusURL) {
    document.querySelectorAll(".mark-complete").forEach(checkbox => {
        checkbox.addEventListener("change", function () {
            const clientId = this.dataset.clientId;
            const checked = this.checked;
            const clientName = this.dataset.clientName;

            const fields = ['submitted', 'client_notified', 'paid'];
            fields.forEach(field => {
                const box = document.querySelector(`[data-client-id='${clientId}'][data-field='${field}']`);
                if (box) box.checked = checked;
            });

            fetch(updateStatusURL, {
                method: "POST",
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    client_id: clientId,
                    submitted: String(checked),
                    client_notified: String(checked),
                    paid: String(checked)
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(`Marked all as ${checked ? 'complete' : 'incomplete'} for client ${clientName}`);
                } else {
                    showToast(`Failed: ${data.error}`, false);
                }
            })
            .catch(err => showToast("Failed to update: " + err, false));
        });
    });
}



document.addEventListener("DOMContentLoaded", function () {
    const { updateStatusURL, updateCommentURL } = getAjaxUrls();
    bindFieldCheckboxes(updateStatusURL);
    bindCommentButtons(updateCommentURL);
    bindMarkComplete(updateStatusURL);
});
