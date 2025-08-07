// Wait for both DOM and jQuery to be ready
$(document).ready(function() {
    // Initialize Bootstrap Select Picker first
    $('.selectpicker').selectpicker();
    
    // Then set up your table filtering
    const tableBody = $("table.table tbody");
    if (!tableBody.length) return;

    const nameInput = $("#filter-name");
    const yearFilter = $("#filter-year");
    const afsFilter = $("#filter-afs");
    const itr14Filter = $("#filter-itr14");
    const invoiceFilter = $("#filter-invoice");

    const filters = {
        name: "",
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
        filters.name = nameInput.val().toLowerCase().trim();
        filters.year = yearFilter.val();
        filters.afs = afsFilter.val();
        filters.itr14 = itr14Filter.val();
        filters.invoice = invoiceFilter.val();

        applyFilters();
    }

    const debouncedUpdateFilters = debounce(updateFilters, 300);

    function applyFilters() {
        const rows = $("tbody tr");

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

            const name = row.find("td:eq(0)").text().toLowerCase().trim();
            const year = row.find("td:eq(1)").text().trim();
            const afsStatus = row.find("td:eq(3) button").text().toLowerCase().trim();
            const itr14Status = row.find("td:eq(4) button").text().toLowerCase().trim();
            const invoiceStatus = row.find("td:eq(5) button").text().toLowerCase().trim();

            const matchName = filters.name === "" || name.includes(filters.name);
            const matchYear = filters.year === "all" || year === filters.year;
            const matchAFS = filters.afs === "all" || (filters.afs === "completed" && afsStatus === "completed") || (filters.afs === "incomplete" && afsStatus === "incomplete");
            const matchITR = filters.itr14 === "all" || (filters.itr14 === "completed" && itr14Status === "completed") || (filters.itr14 === "incomplete" && itr14Status === "incomplete");
            const matchINV = filters.invoice === "all" || (filters.invoice === "invoiced" && invoiceStatus === "invoiced") || (filters.invoice === "pending" && invoiceStatus === "pending");

            row.css("display", (matchName && matchYear && matchAFS && matchITR && matchINV) ? "" : "none");
        });
    }

    nameInput.on("input", debouncedUpdateFilters);
    yearFilter.on("change", updateFilters);
    afsFilter.on("change", updateFilters);
    itr14Filter.on("change", updateFilters);
    invoiceFilter.on("change", updateFilters);

    // Apply filters initially
    updateFilters();
});