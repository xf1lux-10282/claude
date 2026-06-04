// Rental Booking Form JavaScript

document.addEventListener('DOMContentLoaded', () => {
    // Check if a date was selected from the calendar
    const selectedDate = sessionStorage.getItem('selectedRentalDate');
    if (selectedDate) {
        // Format and display the date in a readable format
        const formattedDate = formatDate(selectedDate);
        document.getElementById('rental-date').value = formattedDate;
        displaySelectedDate(selectedDate);
    } else {
        // Redirect to calendar if no date is selected
        alert('予約カレンダーから予約可能な日を選択してください');
        window.location.href = 'rental-calendar.html';
        return;
    }

    // Form submission
    const bookingForm = document.getElementById('booking-form');
    bookingForm.addEventListener('submit', handleFormSubmit);

    // Email confirmation validation
    const emailInput = document.getElementById('customer-email');
    const emailConfirmInput = document.getElementById('customer-email-confirm');

    emailConfirmInput.addEventListener('blur', () => {
        validateEmailMatch();
    });

    // Reset button
    const resetBtn = document.getElementById('reset-btn');
    resetBtn.addEventListener('click', () => {
        bookingForm.reset();
        sessionStorage.removeItem('selectedRentalDate');
        document.getElementById('selected-date-display').style.display = 'none';
        document.getElementById('status-message').style.display = 'none';
    });

    // Date input change handler
    document.getElementById('rental-date').addEventListener('change', (e) => {
        const date = e.target.value;
        if (date) {
            displaySelectedDate(date);
        }
    });

    // Time validation
    const startHourSelect = document.getElementById('start-hour');
    const startMinuteSelect = document.getElementById('start-minute');
    const endHourSelect = document.getElementById('end-hour');
    const endMinuteSelect = document.getElementById('end-minute');

    startHourSelect.addEventListener('change', () => {
        validateTimeRange();
    });

    startMinuteSelect.addEventListener('change', () => {
        validateTimeRange();
    });

    endHourSelect.addEventListener('change', () => {
        validateTimeRange();
    });

    endMinuteSelect.addEventListener('change', () => {
        validateTimeRange();
    });
});

// Display selected date
function displaySelectedDate(dateString) {
    const display = document.getElementById('selected-date-display');
    const text = document.getElementById('selected-date-text');

    const formattedDate = formatDate(dateString);
    text.textContent = formattedDate;
    display.style.display = 'block';
}

// Format date to Japanese format
function formatDate(dateString) {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const dayOfWeek = ['日', '月', '火', '水', '木', '金', '土'][date.getDay()];

    return `${year}年${month}月${day}日（${dayOfWeek}）`;
}

// Validate email match
function validateEmailMatch() {
    const email = document.getElementById('customer-email').value;
    const emailConfirm = document.getElementById('customer-email-confirm').value;

    if (!emailConfirm) {
        return true; // Skip if confirmation field is empty
    }

    if (email !== emailConfirm) {
        showMessage('メールアドレスが一致しません。もう一度ご確認ください。', 'error');
        return false;
    }

    return true;
}

// Validate time range (minimum 4 hours)
function validateTimeRange() {
    const startHour = document.getElementById('start-hour').value;
    const startMinute = document.getElementById('start-minute').value;
    const endHour = document.getElementById('end-hour').value;
    const endMinute = document.getElementById('end-minute').value;

    if (!startHour || !startMinute || !endHour || !endMinute) {
        return true; // If any field is empty, let HTML5 validation handle it
    }

    // Combine hours and minutes
    const startTime = `${startHour}:${startMinute}`;
    const endTime = `${endHour}:${endMinute}`;

    // Convert time strings to minutes since midnight
    const startMinutes = timeToMinutes(startTime);
    const endMinutes = timeToMinutes(endTime);

    const durationHours = (endMinutes - startMinutes) / 60;

    if (durationHours < 4) {
        showMessage('利用時間は最低4時間からとなります。終了時間を調整してください。', 'error');
        return false;
    }

    return true;
}

// Convert time string (HH:MM) to minutes since midnight
function timeToMinutes(timeString) {
    const [hours, minutes] = timeString.split(':').map(Number);
    return hours * 60 + minutes;
}

// Handle form submission
async function handleFormSubmit(e) {
    e.preventDefault();

    const formData = new FormData(e.target);

    // Validate email match
    if (!validateEmailMatch()) {
        return;
    }

    // Validate time range
    if (!validateTimeRange()) {
        return;
    }

    // Get optional items (no longer required)
    const items = formData.getAll('items');

    // Combine time fields
    const startHour = formData.get('startHour');
    const startMinute = formData.get('startMinute');
    const endHour = formData.get('endHour');
    const endMinute = formData.get('endMinute');
    const startTime = `${startHour}:${startMinute}`;
    const endTime = `${endHour}:${endMinute}`;

    // Get the actual date from session storage (in YYYY-MM-DD format)
    const actualDate = sessionStorage.getItem('selectedRentalDate');

    // Prepare booking data
    const bookingData = {
        date: actualDate,
        startTime: startTime,
        endTime: endTime,
        items: items,
        customerName: formData.get('customerName'),
        customerEmail: formData.get('customerEmail'),
        customerPhone: formData.get('customerPhone'),
        usagePurpose: formData.get('usagePurpose') || '未記入',
        technique: formData.get('technique') || '未記入',
        message: formData.get('message') || '',
        status: 'pending', // Automatically set to pending (キャンセル待ち)
        createdAt: new Date().toISOString()
    };

    try {
        // Try to submit to server
        const response = await fetch('http://localhost:3000/api/rentals', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(bookingData)
        });

        if (response.ok) {
            const result = await response.json();
            showMessage(
                '予約申込を受け付けました。確認メールをお送りしますので、ご確認ください。3営業日以内に予約可否をご連絡いたします。',
                'success'
            );

            // Clear form after successful submission
            setTimeout(() => {
                e.target.reset();
                sessionStorage.removeItem('selectedRentalDate');
                document.getElementById('selected-date-display').style.display = 'none';
            }, 2000);
        } else {
            throw new Error('Server error');
        }
    } catch (error) {
        console.log('Server not available - showing offline message');
        // Show message for offline/demo mode
        showMessage(
            '【デモモード】予約申込を受け付けました。実際の運用では、確認メールが送信され、3営業日以内に予約可否をご連絡いたします。',
            'success'
        );

        // Store in localStorage for demo purposes
        saveBookingToLocalStorage(bookingData);

        // Clear form
        setTimeout(() => {
            e.target.reset();
            sessionStorage.removeItem('selectedRentalDate');
            document.getElementById('selected-date-display').style.display = 'none';
        }, 3000);
    }
}

// Save booking to localStorage (for demo mode)
function saveBookingToLocalStorage(bookingData) {
    let bookings = JSON.parse(localStorage.getItem('rentalBookings') || '[]');
    bookingData.id = Date.now().toString();
    bookings.push(bookingData);
    localStorage.setItem('rentalBookings', JSON.stringify(bookings));
}

// Show status message
function showMessage(message, type) {
    const statusMessage = document.getElementById('status-message');
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
    statusMessage.style.display = 'block';

    // Scroll to message
    statusMessage.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    // Auto-hide error messages after 5 seconds
    if (type === 'error') {
        setTimeout(() => {
            statusMessage.style.display = 'none';
        }, 5000);
    }
}

// Calculate total price based on selected items
function calculateTotalPrice(items) {
    const prices = {
        'uv-exposure': 3000,
        'darkroom': 2000,
        'digital-negative': 2000
    };

    let total = 0;
    items.forEach(item => {
        total += prices[item] || 0;
    });

    return total;
}

// Get item names in Japanese
function getItemNames(items) {
    const names = {
        'uv-exposure': '紫外線露光機',
        'darkroom': '暗室スペース',
        'digital-negative': 'デジタルネガ作成サポート'
    };

    return items.map(item => names[item] || item);
}
