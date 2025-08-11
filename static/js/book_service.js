// Wait for both DOM and jQuery to be ready
$(document).ready(function() {
    // Initialize Bootstrap Select Picker first
    $('.selectpicker').selectpicker();
    
    // Then set up your table filtering
    const tableBody = $("table.table tbody");
    if (!tableBody.length) return;

    const nameInput = $("#filter-name");
    const yearFilter = $("#filter-year");


    const filters = {
        name: "",
        year: "all",
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
        applyFilters();
    }

    const debouncedUpdateFilters = debounce(updateFilters, 300);

function applyFilters() {
    const rows = $("tbody tr");

    rows.each(function() {
        const row = $(this);

        const name = row.find("td:eq(0)").text().toLowerCase().trim();
        const year = row.find("td:eq(1)").text().trim();

        const matchName = filters.name === "" || name.includes(filters.name);
        const matchYear = filters.year === "all" || year === filters.year;

        row.css("display", (matchName && matchYear) ? "" : "none");
    });
}

    nameInput.on("input", debouncedUpdateFilters);
    yearFilter.on("change", updateFilters);
    
    // Apply filters initially
    updateFilters();
});