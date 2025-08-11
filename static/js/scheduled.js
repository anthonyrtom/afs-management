document.addEventListener("DOMContentLoaded", function () {
    const tableBody = document.querySelector("table.table tbody");
    if (!tableBody) {
        return;
    }

    // const nameInput = document.getElementById("filter-name");
    const yearFilter = document.getElementById("filter-year");
    const afsFilter = document.getElementById("filter-afs");
    const itr14Filter = document.getElementById("filter-itr14");
    const invoiceFilter = document.getElementById("filter-invoice");

    const filters = {
        // name: "",
        year: "all",
        afs: "all",
        itr14: "all",
        invoice: "all"
    };

    function updateFilters() {
        // if (nameInput) filters.name = nameInput.value.toLowerCase().trim();
        if (yearFilter) filters.year = yearFilter.value;
        if (afsFilter) filters.afs = afsFilter.value;
        if (itr14Filter) filters.itr14 = itr14Filter.value;
        if (invoiceFilter) filters.invoice = invoiceFilter.value;

        applyFilters();
    }

    function applyFilters() {
        const rows = document.querySelectorAll("tbody tr");
        rows.forEach(row => {
            if (row.classList.contains("summary-row")) {
                row.style.display = "";
                return;
            }

            if (row.children.length < 6) {
                row.style.display = "none";
                return;
            }

            // const name = row.children[0].innerText.toLowerCase().trim();
            const year = row.children[1].innerText.trim();
            const afsStatus = row.children[3].querySelector('button').innerText.toLowerCase().trim();
            const itr14Status = row.children[4].querySelector('button').innerText.toLowerCase().trim();
            const invoiceStatus = row.children[5].querySelector('button').innerText.toLowerCase().trim();

            // const matchName = filters.name === "" || name.includes(filters.name);
            const matchYear = filters.year === "all" || year === filters.year;
            const matchAFS = filters.afs === "all" || 
                (filters.afs === "completed" && afsStatus === "completed") || 
                (filters.afs === "incomplete" && afsStatus === "incomplete");
            const matchITR = filters.itr14 === "all" || 
                (filters.itr14 === "completed" && itr14Status === "completed") || 
                (filters.itr14 === "incomplete" && itr14Status === "incomplete");
            const matchINV = filters.invoice === "all" || 
                (filters.invoice === "invoiced" && invoiceStatus === "invoiced") || 
                (filters.invoice === "pending" && invoiceStatus === "pending");

            row.style.display = ( matchYear && matchAFS && matchITR && matchINV) ? "" : "none";
        });
    }

    // Debounce helper
    function debounce(fn, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => fn.apply(this, args), delay);
        };
    }

    // Attach listeners
    // if (nameInput) nameInput.addEventListener("input", debounce(updateFilters, 300));
    if (yearFilter) yearFilter.addEventListener("change", updateFilters);
    if (afsFilter) afsFilter.addEventListener("change", updateFilters);
    if (itr14Filter) itr14Filter.addEventListener("change", updateFilters);
    if (invoiceFilter) invoiceFilter.addEventListener("change", updateFilters);

    applyFilters();
});
