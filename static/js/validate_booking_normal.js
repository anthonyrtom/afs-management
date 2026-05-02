document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('#normal-event-form');
    const isAllDaySelect = document.querySelector('select[name="is_all_day"]');
    const startTimeInput = document.querySelector('input[name="event_start_time"]');
    const endTimeInput = document.querySelector('input[name="event_end_time"]');

    const startContainer = startTimeInput.closest('.col-md-6');
    const endContainer = endTimeInput.closest('.col-md-6');

    function toggleTimeFields() {
        if (isAllDaySelect.value === 'yes') {
            startContainer.style.display = 'none';
            endContainer.style.display = 'none';
            startTimeInput.required = false;
            endTimeInput.required = false;
            startTimeInput.value = '';
            endTimeInput.value = '';
        } else {
            startContainer.style.display = 'block';
            endContainer.style.display = 'block';
            startTimeInput.required = true;
            endTimeInput.required = true;
        }
    }

    function validateTimeOrder(event) {
        if (isAllDaySelect.value === 'no') {
            const startTime = startTimeInput.value;
            const endTime = endTimeInput.value;

            if (startTime && endTime) {
                const start = new Date(`1970-01-01T${startTime}`);
                const end = new Date(`1970-01-01T${endTime}`);

                if (start > end) {
                    event.preventDefault();
                    alert("Start time cannot be after end time");
                }
            }
        }
    }

    form.addEventListener('submit', validateTimeOrder);
    isAllDaySelect.addEventListener('change', toggleTimeFields);

    toggleTimeFields();
});