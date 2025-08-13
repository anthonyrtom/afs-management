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
        let visibleCount = 0;
        const totalCount = rows.length;

        rows.each(function() {
            const row = $(this);
            const name = row.find("td:eq(0)").text().toLowerCase().trim();
            const year = row.find("td:eq(1)").text().trim();

            const matchName = filters.name === "" || name.includes(filters.name);
            const matchYear = filters.year === "all" || year === filters.year;
            const shouldShow = matchName && matchYear;

            row.css("display", shouldShow ? "" : "none");
            if (shouldShow) visibleCount++;
        });

        updateRowCount(visibleCount, totalCount);
    }

    function updateRowCount(visible, total) {
        let countDisplay = $("#filtered-row-count");
        
        // Create the element if it doesn't exist
        if (countDisplay.length === 0) {
            countDisplay = $('<div id="filtered-row-count"></div>');
            $("table.table").before(countDisplay);
        }

        countDisplay.text(`Showing ${visible} of ${total} records`);
        countDisplay.css({
            'margin': '10px 0',
            'font-weight': 'bold',
            'background-color': '#f8f9fa',
            'padding': '8px 15px',
            'border-radius': '4px',
            'border-left': '4px solid #0d6efd'
        });
    }

    nameInput.on("input", debouncedUpdateFilters);
    yearFilter.on("change", updateFilters);
    
    // Apply filters initially
    updateFilters();
});