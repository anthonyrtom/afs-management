document.addEventListener("DOMContentLoaded", function () {
    setupSaveButtons();
});

function getAjaxUrl() {
    const urlContainer = document.getElementById("ajax-urls");
    if(urlContainer)
        return urlContainer.dataset.updateIndividualUrl;
    return "";
}

function setupSaveButtons() {
    document.querySelectorAll(".save-btn").forEach(button => {
        button.addEventListener("click", function () {
            const row = button.closest("tr");
            const rowId = row.dataset.rowId;
            const csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]').value;
            const financialYear = row.querySelector("[name='start_year']").value;
            const formData = new FormData();
            
            formData.append("transId", rowId);
            formData.append("financialYear", financialYear);
            
            button.disabled = true;

            const url = getAjaxUrl();
            // console.log(financialYear);
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
                console.log(msg);
                if (data.success) {
                    msg.style.display = "inline";
                    setTimeout(() => msg.style.display = "none", 5000);
                } else {
                    msg.classList.remove("text-success");
                    msg.classList.add("text-warning")
                    // alert("Save failed: " + (data.message || "Unknown error"));
                    msg.textContent = data.message
                    msg.style.display = "inline";
                    setTimeout(() => msg.style.display = "none", 5000);
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
