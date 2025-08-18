document.addEventListener("DOMContentLoaded", function () {
    setupSaveButtons();
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
