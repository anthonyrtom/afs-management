
function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            func.apply(this, args);
        }, delay);
    };
}
function setupFiltering() {
    const nameInput = document.querySelector("input[name='searchterm']");
    
    if (!nameInput) return; 
    
    function applyFilters() {
        const name = nameInput.value.toLowerCase().trim();
        const table = document.querySelector("table.table");
        
        if (!table) return;
    
        const rows = table.querySelectorAll("tbody tr");
        
        rows.forEach(row => {
            const nameCell = row.querySelector("td:nth-child(1)"); 
            const emailCell = row.querySelector("td:nth-child(2)"); 
            if (!nameCell) return;
            if (!emailCell) return;
            
            const matchName = !name || nameCell.textContent.toLowerCase().includes(name);
            const matchEmail = !name || emailCell.textContent.toLowerCase().includes(name);
            row.style.display = (matchName || matchEmail) ? "" : "none";
        });
    }
    setTimeout(applyFilters, 0);
    
    nameInput.addEventListener("input", debounce(applyFilters, 300));
}


document.addEventListener("DOMContentLoaded", function () {
    setupFiltering();
});
