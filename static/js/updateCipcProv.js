document.addEventListener("DOMContentLoaded", function(){
    setupFilteringOnDocument();
    clearSaveRow();
})

function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

function getAjaxUrls() {
    const urlContainer = document.getElementById("ajax-urls");
    if(urlContainer)
        return urlContainer.dataset.updateCipcprovUrl;
    return "";
}

function setupFilteringOnDocument(){
    const cipcProvFilter = document.querySelector("#cipcprov-filter");
    const invoicingFilter = document.querySelector("#invoicing-filter");
    
    const filters = {
        cipcprov:"all",
        invoicing:"all",
    };
    
    function updateFilters(){
        filters.cipcprov = cipcProvFilter.value;
        filters.invoicing = invoicingFilter.value;
        applyFilters()
    }

    function applyFilters(){
        rows = document.querySelectorAll("tbody tr");
        let rowsCounter = 0;
        const rowsLength = rows.length;
        // debugger;
        rows.forEach(row =>{
            const isAFSFilter = row.children[3].querySelector("button").textContent.toLowerCase().trim();
            const isinvoicingFilter = row.children[5].querySelector("button").textContent.toLowerCase().trim();
            const afsMatch = filters.cipcprov==="all" || isAFSFilter === filters.cipcprov;
            const invoicingMatch = filters.invoicing == "all" || isinvoicingFilter === filters.invoicing;
            const bothMatch = afsMatch && invoicingMatch;
            row.style.display = bothMatch ? "" : "none";
            if(bothMatch) rowsCounter++;
            // console.log(isAFSFilter);
        })
        updateRowCount(rowsCounter,rowsLength);
    }

    if(cipcProvFilter) cipcProvFilter.addEventListener("change",updateFilters);
    if(invoicingFilter) invoicingFilter.addEventListener("change",updateFilters);
}

function clearSaveRow() {
    const clearElement = document.querySelectorAll(".dropdown-item.clear-action");
    const saveElement = document.querySelectorAll(".dropdown-item.save-action");
    
    clearElement.forEach(oneElement => {
        oneElement.addEventListener("click", function(e) {
            e.preventDefault();
            // const clientId = oneElement.dataset.client;
            const url = getAjaxUrls();
            const transId = oneElement.closest("tr").dataset.rowId;
            const returnType = oneElement.closest("tr").dataset.returnType;
            const msg = oneElement.closest("tr").querySelector(".save-message");
            
            fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRFToken": getCSRFToken(),
                },
                body: new URLSearchParams({
                    transId: transId,
                    returnType: returnType,
                    buttonClicked: "cancel",
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    msg.style.display = "inline";
                    setTimeout(() => msg.style.display = "none", 10000);
                } else {
                    msg.classList.remove("text-success");
                    msg.classList.add("text-warning");
                    msg.textContent = data.message;
                    msg.style.display = "inline";
                    setTimeout(() => msg.style.display = "none", 10000);
                }
            })
            .catch(err => {
                console.error("Error:", err);
                alert("Unexpected error saving");
            });
        });
    });
    // End of clearing
    saveElement.forEach(oneElement => {
        oneElement.addEventListener("click", function(e) {
            e.preventDefault();
            
            const parentRow = oneElement.closest("tr");
            const url = getAjaxUrls();
            const transId = parentRow.dataset.rowId;
            const returnType = parentRow.dataset.returnType;
            const msg = parentRow.querySelector(".save-message");
            // debugger;
            const comment = parentRow.querySelector("textarea").value;
            const finishDate = parentRow.querySelector("input[name='finish_date']").value;
            const invoiceDate = parentRow.querySelector("input[name='invoice_date']").value;
            fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRFToken": getCSRFToken(),
                },
                body: new URLSearchParams({
                    transId: transId,
                    returnType: returnType,
                    buttonClicked: "save",
                    "comment":comment,
                    "finishDate":finishDate,
                    "invoiceDate":invoiceDate,
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    msg.style.display = "inline";
                    setTimeout(() => msg.style.display = "none", 10000);
                } else {
                    msg.classList.remove("text-success");
                    msg.classList.add("text-warning");
                    msg.textContent = data.message;
                    msg.style.display = "inline";
                    setTimeout(() => msg.style.display = "none", 10000);
                }
            })
            .catch(err => {
                console.error("Error:", err);
                alert("Unexpected error saving");
            });
        });
    });
}