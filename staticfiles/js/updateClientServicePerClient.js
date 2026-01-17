document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".save-service").forEach(button => {
        button.addEventListener("click", () => {
            const row = button.closest("tr");
            const serviceId = row.dataset.serviceId;

            const data = new FormData();
            data.append("start_date", row.querySelector(".start-date").value);
            data.append("end_date", row.querySelector(".end-date").value);
            data.append("comment", row.querySelector(".comment").value);

            fetch(`/client/${CLIENT_ID}/service/${serviceId}/save/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("meta[name='csrf-token']").content
                },
                body: data
            })
                .then(r => r.json())
                .then(() => {
                    const msg = row.querySelector(".save-message");
                    msg.style.display = "inline";
                    setTimeout(() => msg.style.display = "none", 2000);
                });
        });
    });
});
