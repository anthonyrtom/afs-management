document.addEventListener("DOMContentLoaded", function () {

    //Get the elements on the DOM
    const isAllDaySelect = document.querySelector("#id_is_all_day");
    const form = document.querySelector('#recurring-event-form');
    const startTimeInput = document.querySelector('#id_event_start_time');
    const endTimeInput = document.querySelector('#id_event_end_time');
    const startContainer = startTimeInput.closest('.col-md-6');
    const endContainer = endTimeInput.closest('.col-md-6');
    const recurringTypeInput = document.querySelector("#id_recurring_type");
    const recurringContainer = recurringTypeInput.closest(".col-md-6");
    const sepcountInput = document.querySelector("#id_separation_count");
    const endbyInput = document.querySelector("#id_end");
    const endbyContainer = endbyInput.closest(".col-md-6");
    const numbOccurencesInput = document.querySelector("#id_number_of_occurences");
    const numbOccurencesContainer = numbOccurencesInput.closest(".col-md-6");
    const startDateInput = document.querySelector("#id_event_start_date");
    const startDateContainer = startDateInput.closest(".col-md-6");
    const endDateInput = document.querySelector("#id_event_end_date");
    const endDateContainer = endDateInput.closest(".col-md-6");
    const monthInput = document.querySelector("#id_yearly_event_month");
    const monthContainer = monthInput.closest(".col-md-6");
    const dayofmonthInput = document.querySelector("#id_day_of_month");
    const dayofmonthContainer = dayofmonthInput.closest(".col-md-6");
    const weekofmonthInput = document.querySelector("#id_week_of_month");
    const weekofmonthContainer = weekofmonthInput.closest(".col-md-6");
    const dayofweekInput = document.querySelector("#id_day_of_week");
    const dayofweekContainer = dayofweekInput.closest(".col-md-6");

    //array of all inout elements
    const arrAllInput = [startDateInput, isAllDaySelect, recurringTypeInput, sepcountInput, endbyInput, numbOccurencesInput, endDateInput, monthInput, dayofmonthInput, weekofmonthInput, dayofweekInput];

    //Event listeners
    isAllDaySelect.addEventListener('change', () => {
        toggleTimeFields(isAllDaySelect, startContainer, endContainer, startTimeInput, endTimeInput);
    });
    form.addEventListener('submit', (event) => {
        validateTimeOrder(event, isAllDaySelect, startTimeInput, endTimeInput);
    });
    recurringTypeInput.addEventListener('change', () => {
        hideorUnhideInputs(arrAllInput);
    });

    //First time call
    toggleTimeFields(isAllDaySelect, startContainer, endContainer, startTimeInput, endTimeInput);
    hideorUnhideInputs(arrAllInput);
});

function toggleTimeFields(isAllDaySelect, startContainer, endContainer, startTimeInput, endTimeInput) {
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

function hideorUnhideInputs(arrayofInputElements) {
    const [startDateInput, isAllDayInput, recurringInput, separationcountInput, endInput, numbOccInput, endDateInput, monthInput, dayofmonthInput, weekofmonthInput, dayofweekInput] = arrayofInputElements;
    let inputsTobeClosed;
    if (recurringInput.value == "daily") {
        inputsTobeClosed = [dayofweekInput, weekofmonthInput, dayofmonthInput, monthInput];

        if (endInput.value == "never") {
            inputsTobeClosed.push(endDateInput);
            inputsTobeClosed.push(numbOccInput);
            enableorDisableInputs(inputsTobeClosed, false);
        }
    }
}

function enableorDisableInputs(arrayOfInputs, makeVisible = true) {
    if (makeVisible) {
        arrayOfInputs.forEach(el => {
            el.closest(".col-md-6").style.display = 'block';
        })
    } else {
        arrayOfInputs.forEach(el => {
            el.closest(".col-md-6").style.display = 'none';
            if ('value' in el) {
                el.value = '';
            }
        })

    }
}