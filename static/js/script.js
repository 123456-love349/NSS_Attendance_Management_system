document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // Student Form Validation
    // -------------------------------------------------------------
    const studentForm = document.getElementById('student-attendance-form');
    if (studentForm) {
        const inputs = studentForm.querySelectorAll('.form-control[required]');
        
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                validateField(input);
            });
            input.addEventListener('blur', () => {
                validateField(input);
            });
        });

        studentForm.addEventListener('submit', (e) => {
            let isValid = true;
            inputs.forEach(input => {
                if (!validateField(input)) {
                    isValid = false;
                }
            });

            if (!isValid) {
                e.preventDefault();
                const firstInvalid = studentForm.querySelector('.is-invalid');
                if (firstInvalid) {
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    }

    function validateField(input) {
        const value = input.value.trim();
        let isValid = true;
        let errorMessage = '';

        if (!value) {
            isValid = false;
            errorMessage = 'This field is required.';
        } else {
            if (input.id === 'phone') {
                const phonePattern = /^[6-9]\d{9}$/;
                if (!phonePattern.test(value)) {
                    isValid = false;
                    errorMessage = 'Please enter a valid 10-digit mobile number.';
                }
            } else if (input.id === 'urn') {
                const urnPattern = /^\d+$/;
                if (!urnPattern.test(value)) {
                    isValid = false;
                    errorMessage = 'URN should consist of digits only.';
                } else if (value.length < 5) {
                    isValid = false;
                    errorMessage = 'URN must be at least 5 digits.';
                }
            } else if (input.id === 'crn') {
                const crnPattern = /^\d+$/;
                if (!crnPattern.test(value)) {
                    isValid = false;
                    errorMessage = 'CRN should consist of digits only.';
                }
            }
        }

        const feedbackElement = document.getElementById(`${input.id}-feedback`);
        if (feedbackElement) {
            if (!isValid) {
                input.classList.add('is-invalid');
                input.style.borderColor = 'var(--error)';
                feedbackElement.textContent = errorMessage;
                feedbackElement.style.display = 'block';
            } else {
                input.classList.remove('is-invalid');
                input.style.borderColor = 'var(--border)';
                feedbackElement.style.display = 'none';
            }
        }

        return isValid;
    }

    // -------------------------------------------------------------
    // Live Search & Multi-Filter in Results Page
    // -------------------------------------------------------------
    const searchInput = document.getElementById('search-input');
    const branchFilter = document.getElementById('filter-branch');
    const eventFilter = document.getElementById('filter-event');
    const modeFilter = document.getElementById('filter-mode');
    const volunteerFilter = document.getElementById('filter-volunteer');
    const tableBody = document.getElementById('attendance-table-body');
    const noRecordsMsg = document.getElementById('no-records-message');

    if (tableBody) {
        const rows = Array.from(tableBody.getElementsByClassName('attendance-row'));

        function filterTable() {
            const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
            const selectedBranch = branchFilter ? branchFilter.value.toLowerCase() : '';
            const selectedEvent = eventFilter ? eventFilter.value.toLowerCase() : '';
            const selectedMode = modeFilter ? modeFilter.value.toLowerCase() : '';
            const selectedVolunteer = volunteerFilter ? volunteerFilter.value.toLowerCase() : '';

            let visibleCount = 0;

            rows.forEach(row => {
                const cells = Array.from(row.getElementsByTagName('td'));
                if (cells.length === 0) return;

                // Extract fields
                const name = cells[0].textContent.toLowerCase();
                const branch = cells[1].textContent.toLowerCase();
                const section = cells[2].textContent.toLowerCase();
                const crn = cells[3].textContent.toLowerCase();
                const urn = cells[4].textContent.toLowerCase();
                const phone = cells[5].textContent.toLowerCase();
                const volunteer = cells[6].textContent.trim().toLowerCase(); // "yes" or "no"
                const event = cells[7].textContent.toLowerCase();
                const mode = cells[8].textContent.toLowerCase();

                // Search query matches name, URN, CRN, phone, event, branch
                const matchesQuery = !query || 
                                     name.includes(query) || 
                                     urn.includes(query) || 
                                     crn.includes(query) || 
                                     phone.includes(query) ||
                                     branch.includes(query) ||
                                     event.includes(query);

                const matchesBranch = !selectedBranch || branch === selectedBranch;
                const matchesEvent = !selectedEvent || event === selectedEvent;
                const matchesMode = !selectedMode || mode === selectedMode;
                
                // Matches volunteer status
                let matchesVolunteer = true;
                if (selectedVolunteer) {
                    matchesVolunteer = volunteer === selectedVolunteer;
                }

                if (matchesQuery && matchesBranch && matchesEvent && matchesMode && matchesVolunteer) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            if (noRecordsMsg) {
                if (visibleCount === 0) {
                    noRecordsMsg.style.display = 'block';
                } else {
                    noRecordsMsg.style.display = 'none';
                }
            }
        }

        if (searchInput) searchInput.addEventListener('input', filterTable);
        if (branchFilter) branchFilter.addEventListener('change', filterTable);
        if (eventFilter) eventFilter.addEventListener('change', filterTable);
        if (modeFilter) modeFilter.addEventListener('change', filterTable);
        if (volunteerFilter) volunteerFilter.addEventListener('change', filterTable);
    }
});
