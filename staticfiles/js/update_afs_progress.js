document.addEventListener("DOMContentLoaded", function () {
    setupSaveButtons();
    setupClearButtons();
});


function setupSaveButtons() {
    document.querySelectorAll(".save-btn").forEach(button => {
        button.addEventListener("click", function () {
            const row = button.closest("tr");
            const rowId = row.dataset.id;
            const csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]').value;

            const startDate = row.querySelector('input[name="start_date"]').value;
            const finishDate = row.querySelector('input[name="finish_date"]').value;
            const departmentId = document.querySelector('#id_service').value;

            const formData = new FormData();
            formData.append("financial_year_id", rowId);
            formData.append("finish_date", finishDate);
            formData.append("start_date", startDate);
            formData.append("department", departmentId);
            
            button.disabled = true;

            const url = row.dataset.url;
            
            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                const msg = row.querySelector(".save-message");
                if (data.success) {
                    msg.style.display = "inline";
                    setTimeout(() => msg.style.display = "none", 10000);
                } else {
                    msg.classList.remove("text-success");
                    msg.classList.add("text-warning")
                    // alert("Save failed: " + (data.message || "Unknown error"));
                    msg.textContent = data.message
                    msg.style.display = "inline";
                    setTimeout(() => msg.style.display = "none", 10000);
                }
            })
            .catch(err => {
                
                alert("Unexpected error saving");
            })
            .finally(() => {
                button.disabled = false;
            });
        });
    });
}

function setupClearButtons() {
    document.querySelectorAll(".clear-btn").forEach(button => {
        button.addEventListener("click", function () {
            const row = button.closest("tr");
            const rowId = row.dataset.id;
            const csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]').value;
            const departmentId = document.querySelector('#id_service').value;

            const formData = new FormData();
            formData.append("financial_year_id", rowId);
            formData.append("start_date", "");
            formData.append("finish_date", "");
            formData.append("department", departmentId);
            formData.append("clear", "true");  // flag for the backend

            button.disabled = true;

            const url = row.dataset.url;
            debugger;
            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                const msg = row.querySelector(".save-message");
                if (data.success) {
                    // Clear the inputs in the UI
                    row.querySelector('input[name="start_date"]').value = "";
                    row.querySelector('input[name="finish_date"]').value = "";

                    msg.classList.remove("text-warning");
                    msg.classList.add("text-success");
                    msg.textContent = "Cleared!";
                    msg.style.display = "inline";
                    setTimeout(() => msg.style.display = "none", 10000);
                } else {
                    msg.classList.remove("text-success");
                    msg.classList.add("text-warning");
                    msg.textContent = data.message || "Clear failed";
                    msg.style.display = "inline";
                    setTimeout(() => msg.style.display = "none", 10000);
                }
            })
            .catch(err => {
                alert("Unexpected error clearing");
            })
            .finally(() => {
                button.disabled = false;
            });
        });
    });
}
