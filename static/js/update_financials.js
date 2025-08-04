document.addEventListener("DOMContentLoaded", function () {
    setupFiltering();
    setupSaveButtons();
});

function setupFiltering() {
    const nameInput = document.getElementById("filter-name");
    const yearFilter = document.getElementById("filter-year");

    function applyFilters() {
        const name = nameInput.value.toLowerCase().trim();
        const year = yearFilter.value;

        document.querySelectorAll("tbody tr.data-row").forEach(row => {
            const nameCell = row.querySelector("td:nth-child(1)");
            const yearCell = row.querySelector("td:nth-child(2)");

            const matchName = !name || nameCell.textContent.toLowerCase().includes(name);
            const matchYear = year === "all" || yearCell.textContent.trim() === year;

            row.style.display = (matchName && matchYear) ? "" : "none";
        });
    }

    nameInput?.addEventListener("input", applyFilters);
    yearFilter?.addEventListener("change", applyFilters);
    applyFilters();
}

function setupSaveButtons() {
    document.querySelectorAll(".save-btn").forEach(button => {
        button.addEventListener("click", function () {
            const row = button.closest("tr");
            const rowId = row.dataset.id;
            const csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]').value;

            const finishDate = row.querySelector('input[name="finish_date"]').value;
            const itr14Date = row.querySelector('input[name="itr14_date"]').value;
            const invoiceDate = row.querySelector('input[name="invoice_date"]').value;

            const formData = new FormData();
            formData.append("financial_year_id", rowId);
            formData.append("finish_date", finishDate);
            formData.append("itr14_date", itr14Date);
            formData.append("invoice_date", invoiceDate);

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
                    setTimeout(() => msg.style.display = "none", 2000);
                } else {
                    alert("Save failed: " + (data.error || "Unknown error"));
                }
            })
            .catch(err => {
                console.error("Error saving row", err);
                alert("Unexpected error saving");
            })
            .finally(() => {
                button.disabled = false;
            });
        });
    });
}
