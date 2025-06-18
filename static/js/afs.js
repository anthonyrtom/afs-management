
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
    const container = document.getElementById("ajax-urls");
    return {
        updateStatusURL: container?.dataset.updateStatusUrl || "",
        updateCommentURL: container?.dataset.updateCommentUrl || ""
    };
}

function sendUpdate({ clientId, field, value, url, clientName }) {
   
    fetch(url, {
        method: "POST",
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({ client_id: clientId, field, value })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(`Updated ${field} for client ${clientName}`);
        } else {
            showToast(`Failed: ${data.error}`, false);
        }
    })
    .catch(err => showToast("Error updating: " + err, false));
}

function sendCommentUpdate({ clientId, comment, url, clientName}) {
    const scheduleInput = document.querySelector(`.date-control[data-client-id='${clientId}']`);
    const scheduleDate = scheduleInput ? scheduleInput.value : ''; 
    const finishInput = document.querySelector(`.finish-date-control[data-client-id='${clientId}']`);
    const finishDate = finishInput ? finishInput.value : '';
    fetch(url, {
        method: "POST",
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({ client_id: clientId, comment, scheduleDate, finishDate })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(`Save successful for client ${clientName}`);
        } else {
            showToast(`Failed: ${data.error}`, false);
        }
    })
    .catch(err => showToast("Error: " + err, false));
}

function bindFieldCheckboxes(updateStatusURL) {
    document.querySelectorAll(".update-field").forEach(checkbox => {
        checkbox.addEventListener("change", function () {
            sendUpdate({
                clientId: this.dataset.clientId,
                field: this.dataset.field,
                value: this.checked,
                url: updateStatusURL,
                clientName : this.dataset.clientName
            });
        });
    });
}

function bindCommentButtons(updateCommentURL) {
    document.querySelectorAll(".update-comment-button").forEach(button => {
        button.addEventListener("click", function () {
            const clientId = this.dataset.clientId;
            // const clientName = this.dataset.clientName; 
            const textarea = document.querySelector(`.update-comment[data-client-id='${clientId}']`);
            const clientName = textarea.dataset.clientName; 
            if (textarea) {
                sendCommentUpdate({
                    clientId,
                    comment: textarea.value,
                    url: updateCommentURL,
                    clientName: clientName || 'Unknown'
                });
            }
        });
    });
}


function bindMarkComplete(updateStatusURL) {
    document.querySelectorAll(".mark-complete").forEach(checkbox => {
        checkbox.addEventListener("change", function () {
            const clientId = this.dataset.clientId;
            const clientName = this.dataset.clientName;
            const checked = this.checked;
            const fields = ['wp_done', 'afs_done', 'posting_done', 'itr34c_issued'];

            // Update UI checkboxes
            fields.forEach(field => {
                const box = document.querySelector(`[data-client-id='${clientId}'][data-field='${field}']`);
                if (box) box.checked = checked;
            });

            // Send AJAX with correct fields
            const params = new URLSearchParams({ client_id: clientId });
            fields.forEach(field => {
                params.append(field, checked); // sends true or false
            });

            fetch(updateStatusURL, {
                method: "POST",
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: params
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(`All marked ${checked ? "complete" : "incomplete"} for client ${clientName}`);
                } else {
                    showToast("Failed to update mark complete", false);
                }
            })
            .catch(err => {
                showToast("Error: " + err, false);
            });
        });
    });
}

document.addEventListener("DOMContentLoaded", function () {
    const { updateStatusURL, updateCommentURL } = getAjaxUrls();
    bindFieldCheckboxes(updateStatusURL);
    bindCommentButtons(updateCommentURL);
    bindMarkComplete(updateStatusURL);
});

