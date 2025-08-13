document.addEventListener("DOMContentLoaded", function(){
    appFilters();
});

function debounce(func, delay){
    let timeoutID;
    return function(...args){
        clearTimeout(timeoutID);
        timeoutID = setTimeout(()=>{
            func.apply(this, args)
        }, delay);
    };
}

function appFilters(){
    // Get filter elements
    const finYear = document.getElementById("filter-year");
    const afsDays = document.getElementById("filter-afs-days");
    const afsComplete = document.getElementById("filter-afs");
    const secDays = document.getElementById("filter-secretarial-days");
    const secComplete = document.getElementById("filter-secretarial");
    const taxDays = document.getElementById("filter-tax-days");
    const taxComplete = document.getElementById("filter-tax");
    const invoiceDays = document.getElementById("filter-invoicing-days");
    const invoiceComplete = document.getElementById("filter-invoicing");
    
    const filters = {
        financialYearFilter: "all",
        afsDaysFilter: "all",
        afsFilter: "all",
        secDaysFilter: "all",
        secFilter: "all",
        taxDaysFilter: "all",
        taxFilter: "all",
        invoiceDaysFilter: "all",
        invoiceFilter: "all",
    }

    function applyFilters(){
        filters.financialYearFilter = finYear.value;
        filters.afsDaysFilter = afsDays.value;
        filters.afsFilter = afsComplete.value;
        filters.secDaysFilter = secDays.value;
        filters.secFilter = secComplete.value;
        filters.taxDaysFilter = taxDays.value;
        filters.taxFilter = taxComplete.value;
        filters.invoiceDaysFilter = invoiceDays.value;
        filters.invoiceFilter = invoiceComplete.value;

        const rows = document.querySelectorAll("tbody tr");
        let visibleCount = 0;
        rows.forEach(row => {
            const year = row.children[1].textContent.trim();
            const accDays = row.children[2].textContent.trim();
            const accComplete = row.children[3].querySelector("button").textContent.toLowerCase().trim();
            
            const secDays = row.children[4].textContent.trim();
            const secComplete = row.children[5].querySelector("button").textContent.toLowerCase().trim();
            
            const taxDays = row.children[6].textContent.trim();
            const taxComplete = row.children[7].querySelector("button").textContent.toLowerCase().trim();
            
            const invoiceDays = row.children[8].textContent.trim();
            const invoiceComplete = row.children[9].querySelector("button").textContent.toLowerCase().trim();

            const matchYear = filters.financialYearFilter === "all" || year === filters.financialYearFilter;
            const matchAccDays = filters.afsDaysFilter === "all" || accDays === filters.afsDaysFilter;
            const matchAccComplete = filters.afsFilter === "all" || accComplete === filters.afsFilter;
            
            const matchSecDays = filters.secDaysFilter === "all" || secDays === filters.secDaysFilter;
            const matchSecComplete = filters.secFilter === "all" || secComplete === filters.secFilter;
            
            const matchTaxDays = filters.taxDaysFilter === "all" || taxDays === filters.taxDaysFilter;
            const matchTaxComplete = filters.taxFilter === "all" || taxComplete === filters.taxFilter;
            
            const matchInvoiceDays = filters.invoiceDaysFilter === "all" || invoiceDays === filters.invoiceDaysFilter;
            const matchInvoiceComplete = filters.invoiceFilter === "all" || invoiceComplete === filters.invoiceFilter;

            // Show row only if all conditions match
            const shouldShow = matchYear && matchAccDays && matchAccComplete && 
                              matchSecDays && matchSecComplete && 
                              matchTaxDays && matchTaxComplete && 
                              matchInvoiceDays && matchInvoiceComplete;
            
            row.style.display = shouldShow ? "" : "none";
            if(shouldShow) visibleCount++;
        });
        updateRowCount(visibleCount, rows.length);
    }

    // Debounce the filter function for performance
    const debouncedFilter = debounce(applyFilters, 300);

    // Add event listeners
    if (finYear) finYear.addEventListener("change", debouncedFilter);
    if (afsDays) afsDays.addEventListener("change", debouncedFilter);
    if (afsComplete) afsComplete.addEventListener("change", debouncedFilter);
    if (secDays) secDays.addEventListener("change", debouncedFilter);
    if (secComplete) secComplete.addEventListener("change", debouncedFilter);
    if (taxDays) taxDays.addEventListener("change", debouncedFilter);
    if (taxComplete) taxComplete.addEventListener("change", debouncedFilter);
    if (invoiceDays) invoiceDays.addEventListener("change", debouncedFilter);
    if (invoiceComplete) invoiceComplete.addEventListener("change", debouncedFilter);

    // Apply filters initially
    applyFilters();
}

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