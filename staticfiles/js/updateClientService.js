document.addEventListener("DOMContentLoaded", function(){
    clearSaveRow();
})

function clearSaveRow() {
    const tableRows = document.querySelectorAll("tbody tr");
    
    tableRows.forEach(tableRow => {
        tableRow.querySelector("button").addEventListener("click", function(e) {
            e.preventDefault();
            const url = getAjaxUrlsUtils();
            const transId = tableRow.dataset.rowId;
            const msg = tableRow.querySelector(".save-message");
            
            const comment = tableRow.querySelector("textarea").value;
            const finishDate = tableRow.querySelector("input[name='finish_date']").value;
            const startDate = tableRow.querySelector("input[name='start_date']").value;
            console.log(comment);
            fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRFToken": getCSRFTokenUtils(),
                },
                body: new URLSearchParams({
                    transId: transId,
                    "comment":comment,
                    "finishDate":finishDate,
                    "startDate":startDate,
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    msg.style.display = "inline";
                    setTimeout(() => msg.style.display = "none", 5000);
                } else {
                    msg.classList.remove("text-success");
                    msg.classList.add("text-warning");
                    msg.textContent = data.message;
                    msg.style.display = "inline";
                    setTimeout(() => msg.style.display = "none", 5000);
                }
            })
            .catch(err => {
                console.error("Error:", err);
                alert("Unexpected error saving");
            });
        });
    });
}