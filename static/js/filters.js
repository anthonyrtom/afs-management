
document.addEventListener("DOMContentLoaded", function () {
    const afsFilter = document.getElementById("filter-afs");
    const itr14Filter = document.getElementById("filter-itr14");
    const invoiceFilter = document.getElementById("filter-invoice");

    const filters = {
        afs: "all",
        itr14: "all",
        invoice: "all"
    };

    [afsFilter, itr14Filter, invoiceFilter].forEach(filter => {
        filter.addEventListener("change", () => {
            filters.afs = afsFilter.value;
            filters.itr14 = itr14Filter.value;
            filters.invoice = invoiceFilter.value;

            // Optionally store filters
            localStorage.setItem("scheduledFilters", JSON.stringify(filters));

            applyFilters();
        });
    });

    function applyFilters() {
        const rows = document.querySelectorAll("tbody tr");
        rows.forEach(row => {
            if (row.querySelectorAll("td").length < 6) return; // Skip header rows

            const afsStatus = row.children[3].innerText.trim().toLowerCase();
            const itr14Status = row.children[4].innerText.trim().toLowerCase();
            const invoiceStatus = row.children[5].innerText.trim().toLowerCase();

            const matchAFS = (filters.afs === "all" || afsStatus.includes(filters.afs));
            const matchITR = (filters.itr14 === "all" || itr14Status.includes(filters.itr14));
            const matchINV = (filters.invoice === "all" || invoiceStatus.includes(filters.invoice));

            if (matchAFS && matchITR && matchINV) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
    }

    // Load filters from localStorage if available
    const storedFilters = localStorage.getItem("scheduledFilters");
    if (storedFilters) {
        const parsed = JSON.parse(storedFilters);
        afsFilter.value = parsed.afs || "all";
        itr14Filter.value = parsed.itr14 || "all";
        invoiceFilter.value = parsed.invoice || "all";
        filters.afs = afsFilter.value;
        filters.itr14 = itr14Filter.value;
        filters.invoice = invoiceFilter.value;
        applyFilters();
    }
});

