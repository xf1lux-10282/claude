// Rental Calendar JavaScript

let currentYear = 2026;
let currentMonth = 4; // May (0-indexed)
let selectedDate = null;
let rentalData = [];

// Initialize calendar
document.addEventListener('DOMContentLoaded', () => {
    loadRentalData();
    renderCalendar();

    document.getElementById('prev-month').addEventListener('click', () => {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        renderCalendar();
    });

    document.getElementById('next-month').addEventListener('click', () => {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        renderCalendar();
    });
});

// Load rental booking data from server
async function loadRentalData() {
    try {
        const response = await fetch('http://localhost:3000/api/rentals');
        if (response.ok) {
            rentalData = await response.json();
            renderCalendar();
        } else {
            console.log('No rental data available yet');
            rentalData = [];
        }
    } catch (error) {
        console.log('Using offline mode - server not connected');
        // Use sample data for demonstration
        rentalData = getSampleData();
        renderCalendar();
    }
}

// Get sample rental data for demonstration
function getSampleData() {
    return [
        {
            date: '2026-05-15',
            status: 'available'
        },
        {
            date: '2026-05-16',
            status: 'available'
        },
        {
            date: '2026-05-20',
            status: 'pending'
        },
        {
            date: '2026-05-22',
            status: 'booked'
        },
        {
            date: '2026-05-23',
            status: 'available'
        },
        {
            date: '2026-05-29',
            status: 'available'
        },
        {
            date: '2026-05-30',
            status: 'available'
        },
        {
            date: '2026-06-05',
            status: 'available'
        },
        {
            date: '2026-06-06',
            status: 'available'
        },
        {
            date: '2026-06-12',
            status: 'available'
        }
    ];
}

// Render calendar
function renderCalendar() {
    const monthNames = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
    document.getElementById('current-month').textContent = `${currentYear}年${monthNames[currentMonth]}`;

    const firstDay = new Date(currentYear, currentMonth, 1);
    const lastDay = new Date(currentYear, currentMonth + 1, 0);
    const prevLastDay = new Date(currentYear, currentMonth, 0);

    const firstDayOfWeek = firstDay.getDay();
    const lastDate = lastDay.getDate();
    const prevLastDate = prevLastDay.getDate();

    const calendarGrid = document.getElementById('calendar-grid');

    // Remove all existing day elements (keep only the headers)
    const dayElements = calendarGrid.querySelectorAll('.calendar-day, .calendar-day.other-month');
    dayElements.forEach(el => el.remove());

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Previous month days
    for (let i = firstDayOfWeek - 1; i >= 0; i--) {
        const day = prevLastDate - i;
        const dayElement = createDayElement(day, 'other-month');
        calendarGrid.appendChild(dayElement);
    }

    // Current month days
    for (let day = 1; day <= lastDate; day++) {
        const dateString = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const currentDate = new Date(currentYear, currentMonth, day);

        let classes = [];
        let status = 'closed';
        let statusSymbol = '-';

        // Check if date is in the past
        if (currentDate < today) {
            classes.push('past');
        }

        // Check if today
        if (currentDate.getTime() === today.getTime()) {
            classes.push('today');
        }

        // Check rental status
        const rental = rentalData.find(r => r.date === dateString);
        if (rental) {
            status = rental.status;
            classes.push(status);

            switch (status) {
                case 'available':
                    statusSymbol = '○';
                    break;
                case 'pending':
                    statusSymbol = '△';
                    break;
                case 'booked':
                    statusSymbol = '×';
                    break;
                case 'closed':
                    statusSymbol = '-';
                    break;
            }
        } else {
            // No status set - treat as booked (not available for booking)
            status = 'booked';
            statusSymbol = '×';
            classes.push('booked');
        }

        const dayElement = createDayElement(day, classes.join(' '), statusSymbol, dateString, status);
        calendarGrid.appendChild(dayElement);
    }

    // Next month days
    const totalCells = calendarGrid.querySelectorAll('.calendar-day, .calendar-day-header').length;
    const remainingCells = 42 - totalCells; // 6 rows x 7 days

    for (let day = 1; day <= remainingCells; day++) {
        const dayElement = createDayElement(day, 'other-month');
        calendarGrid.appendChild(dayElement);
    }
}

// Create day element
function createDayElement(day, classes = '', statusSymbol = '', dateString = '', status = '') {
    const dayElement = document.createElement('div');
    dayElement.className = `calendar-day ${classes}`;

    const dayNumber = document.createElement('div');
    dayNumber.className = 'day-number';
    dayNumber.textContent = day;

    dayElement.appendChild(dayNumber);

    if (statusSymbol) {
        const dayStatus = document.createElement('div');
        dayStatus.className = 'day-status';
        dayStatus.textContent = statusSymbol;
        dayElement.appendChild(dayStatus);
    }

    // Add click handler for all future dates (not just available)
    // This allows users to inquire about any future date regardless of current status
    if (!classes.includes('past')) {
        dayElement.style.cursor = 'pointer';
        dayElement.addEventListener('click', () => {
            selectDate(dateString, day, status);
        });
    }

    return dayElement;
}

// Select date
function selectDate(dateString, day, status) {
    selectedDate = dateString;

    const selectedInfo = document.getElementById('selected-date-info');
    const selectedTitle = document.getElementById('selected-date-title');
    const selectedMessage = document.getElementById('selected-date-message');
    const bookingBtn = document.getElementById('booking-btn');

    const monthNames = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
    const formattedDate = `${currentYear}年${monthNames[currentMonth]}${day}日`;

    selectedTitle.textContent = `選択日: ${formattedDate}`;

    // Display appropriate message based on status
    let message = '';
    let showBookingBtn = false;

    switch(status) {
        case 'available':
            message = 'この日は予約可能です。下のボタンから予約申込フォームへお進みください。';
            showBookingBtn = true;
            break;
        case 'pending':
            message = 'この日は現在仮予約（キャンセル待ち）です。キャンセルが出た場合に予約可能となります。お問い合わせをご希望の場合は下のボタンからお進みください。';
            showBookingBtn = true;
            break;
        case 'booked':
            message = 'この日は予約済みです。別の日程をご検討いただくか、キャンセル待ちをご希望の場合はお問い合わせください。';
            showBookingBtn = true;
            break;
        case 'closed':
            message = 'この日は休業日です。別の日程をご検討ください。';
            showBookingBtn = false;
            break;
        default:
            message = 'この日についてのお問い合わせは、予約申込フォームよりご連絡ください。';
            showBookingBtn = true;
    }

    selectedMessage.textContent = message;

    // Store selected date in session storage for booking form
    sessionStorage.setItem('selectedRentalDate', dateString);

    // Show/hide booking button based on status
    if (showBookingBtn) {
        bookingBtn.style.display = 'inline-block';
    } else {
        bookingBtn.style.display = 'none';
    }

    selectedInfo.classList.add('show');
    selectedInfo.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Status symbol mapping
function getStatusSymbol(status) {
    switch (status) {
        case 'available':
            return '○';
        case 'pending':
            return '△';
        case 'booked':
            return '×';
        case 'closed':
        default:
            return '-';
    }
}

// Date formatting helper
function formatDate(dateString) {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const dayOfWeek = ['日', '月', '火', '水', '木', '金', '土'][date.getDay()];

    return `${year}年${month}月${day}日（${dayOfWeek}）`;
}
