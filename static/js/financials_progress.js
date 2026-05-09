/**
 * financial_progress.js
 * Handles client-side filtering for the Financial Statements Progress table.
 */

$(document).ready(function () {
    const yearFilter = $("#filter-year");
    const afsFilter = $("#filter-afs");
    const secFilter = $("#filter-sec"); // New
    const itr14Filter = $("#filter-itr14");
    const invoiceFilter = $("#filter-invoice");
    const searchInput = $("input[name='searchterm']");

    function applyFilters() {
        const filters = {
            year: yearFilter.val(),
            afs: afsFilter.val(),
            sec: secFilter.val(),
            itr14: itr14Filter.val(),
            invoice: invoiceFilter.val(),
            search: searchInput.val() ? searchInput.val().toLowerCase().trim() : ""
        };

        const rows = $("table.table tbody tr");
        let visibleCount = 0;

        rows.each(function () {
            const row = $(this);
            if (row.children('td').length < 7) return; // Updated for 7 columns

            const name = row.find("td:eq(0)").text().toLowerCase();
            const year = row.find("td:eq(1)").text().trim();
            const afs = row.find("td:eq(3) button").text().toLowerCase().trim();
            const sec = row.find("td:eq(4) button").text().toLowerCase().trim(); // New
            const itr = row.find("td:eq(5) button").text().toLowerCase().trim();
            const inv = row.find("td:eq(6) button").text().toLowerCase().trim();

            const matchSearch = !filters.search || name.includes(filters.search);
            const matchYear = filters.year === "all" || year === filters.year;
            const matchAFS = filters.afs === "all" || afs === filters.afs;
            const matchSEC = filters.sec === "all" || sec === filters.sec;
            const matchITR = filters.itr14 === "all" || itr === filters.itr14;

            // Special case for invoice status text
            const matchINV = filters.invoice === "all" ||
                (filters.invoice === "invoiced" && inv === "invoiced") ||
                (filters.invoice === "pending" && inv === "pending");

            const isVisible = matchSearch && matchYear && matchAFS && matchSEC && matchITR && matchINV;
            row.toggle(isVisible);
            if (isVisible) visibleCount++;
        });

        $("#filtered-row-count").html(`Showing <strong>${visibleCount}</strong> records`);
    }

    // Listen for changes
    [yearFilter, afsFilter, secFilter, itr14Filter, invoiceFilter].forEach(el => el.on("change", applyFilters));
    searchInput.on("input", applyFilters);

    applyFilters();
});

/**
 * Utility: Debounce function to limit how often a function executes.
 */
function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

/**
 * Updates the "Total Found" header text to reflect filtered results.
 */
function updateRowCount(visible, total) {
    const countDisplay = document.getElementById("filtered-row-count");
    if (countDisplay) {
        countDisplay.innerHTML = `Showing <strong>${visible}</strong> of <strong>${total}</strong> records`;

        // Optional: Add a subtle highlight if results are filtered
        if (visible < total) {
            countDisplay.classList.add("text-primary");
        } else {
            countDisplay.classList.remove("text-primary");
        }
    }
}