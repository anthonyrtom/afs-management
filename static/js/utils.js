    function updateRowCount(visible, total) {
        
        let countDisplay = document.getElementById("filtered-row-count");

        if(countDisplay){
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

    }

function getCSRFTokenUtils() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

function getAjaxUrlsUtils() {
    const urlContainer = document.getElementById("ajax-urls");
    if(urlContainer)
        return urlContainer.dataset.updateCipcprovUrl;
    return "";
}