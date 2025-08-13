$(document).ready(function() {
    
    $('.selectpicker').selectpicker();

    const tableBody = $("table.table tbody");
    if (!tableBody.length) return;

    const yearFilter = $("#filter-year");
    const afsFilter = $("#filter-afs");
    const itr14Filter = $("#filter-itr14");
    const invoiceFilter = $("#filter-invoice");

    const filters = {
        year: "all",
        afs: "all",
        itr14: "all",
        invoice: "all"
    };

    function debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }

    function updateFilters() {
        filters.year = yearFilter.val();
        filters.afs = afsFilter.val();
        filters.itr14 = itr14Filter.val();
        filters.invoice = invoiceFilter.val();

        applyFilters();
    }

    const debouncedUpdateFilters = debounce(updateFilters, 300);

    function applyFilters() {
        const rows = $("tbody tr");
        let countFiltered = 0;
        rows.each(function() {
            const row = $(this);
            
            if (row.hasClass("summary-row")) {
                row.css("display", "");
                return;
            }

            if (row.children().length < 6) {
                row.css("display", "none");
                return;
            }

            const year = row.find("td:eq(1)").text().trim();
            const afsStatus = row.find("td:eq(3) button").text().toLowerCase().trim();
            const itr14Status = row.find("td:eq(4) button").text().toLowerCase().trim();
            const invoiceStatus = row.find("td:eq(5) button").text().toLowerCase().trim();

            const matchYear = filters.year === "all" || year === filters.year;
            const matchAFS = filters.afs === "all" || (filters.afs === "completed" && afsStatus === "completed") || (filters.afs === "incomplete" && afsStatus === "incomplete");
            const matchITR = filters.itr14 === "all" || (filters.itr14 === "completed" && itr14Status === "completed") || (filters.itr14 === "incomplete" && itr14Status === "incomplete");
            const matchINV = filters.invoice === "all" || (filters.invoice === "invoiced" && invoiceStatus === "invoiced") || (filters.invoice === "pending" && invoiceStatus === "pending");
            const allMatch = matchYear && matchAFS && matchITR && matchINV;
            row.css("display", (allMatch) ? "" : "none");
            if(allMatch) countFiltered++;
        });
        updateRowCount(countFiltered, rows.length)
    }

   
    yearFilter.on("change", updateFilters);
    afsFilter.on("change", updateFilters);
    itr14Filter.on("change", updateFilters);
    invoiceFilter.on("change", updateFilters);

    // Apply filters initially
    updateFilters();
});

    function updateRowCount(visible, total) {
        
        let countDisplay = document.getElementById("filtered-row-count");

        countDisplay.textContent = `Showing ${visible} of ${total} records`;
        countDisplay.style.margin = "10px 0";
        countDisplay.style.fontWeight = "bold";
        countDisplay.style.backgroundColor = '#f8f9fa';
        countDisplay.style.padding = '8px 15px';
        countDisplay.style.borderRadius = '4px';
        countDisplay.style.margin = '10px 0';
        countDisplay.style.fontWeight = 'bold';
        countDisplay.style.borderLeft = '4px solid #0d6efd';
    }