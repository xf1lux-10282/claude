// Rental Manager JavaScript

let currentYear = 2026;
let currentMonth = 4; // May (0-indexed)
let rentalData = [];
let pendingChanges = []; // Track unsaved changes
let hasUnsavedChanges = false;
let currentFilter = 'all';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadRentalData();
    renderCalendar();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Calendar navigation
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

    // Filter buttons
    document.querySelectorAll('[data-filter]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            currentFilter = e.target.dataset.filter;
            renderBookingList();

            // Update button states
            document.querySelectorAll('[data-filter]').forEach(b => {
                b.classList.remove('btn-primary');
                b.classList.add('btn-secondary');
            });
            e.target.classList.remove('btn-secondary');
            e.target.classList.add('btn-primary');
        });
    });

    // Excel export button
    document.getElementById('export-excel-btn').addEventListener('click', exportToExcel);

    // Save calendar changes button
    document.getElementById('save-calendar-btn').addEventListener('click', saveCalendarChanges);
}

// Load rental data from server
async function loadRentalData() {
    try {
        const response = await fetch('http://localhost:3000/api/rentals');
        if (response.ok) {
            rentalData = await response.json();
            await autoClosePastDates();
            renderCalendar();
            renderBookingList();
        } else {
            console.log('No rental data available yet');
            rentalData = getSampleData();
            await autoClosePastDates();
            renderCalendar();
            renderBookingList();
        }
    } catch (error) {
        console.log('Using offline mode - loading sample data');
        rentalData = getSampleData();
        await autoClosePastDates();
        renderCalendar();
        renderBookingList();
    }
}

// Automatically set past dates to 'closed' status
async function autoClosePastDates() {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    let hasChanges = false;

    rentalData.forEach(rental => {
        const rentalDate = new Date(rental.date);
        rentalDate.setHours(0, 0, 0, 0);

        // If the date is in the past and not already closed
        if (rentalDate < today && rental.status !== 'closed') {
            rental.status = 'closed';
            hasChanges = true;
        }
    });

    // Save to server if there were any changes
    if (hasChanges) {
        await saveRentalData();
    }
}

// Get sample rental data for demonstration
function getSampleData() {
    // Return empty array - no sample data
    return [];
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
        let isDisabled = false;

        // Check if past date
        if (currentDate < today) {
            classes.push('past');
            isDisabled = true;
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
            // No status set - allow admin to set status for future dates
            if (!isDisabled) {
                classes.push('no-status');
                // Don't disable - allow clicking to set status
            } else {
                classes.push('closed');
            }
        }

        const dayElement = createDayElement(day, classes.join(' '), statusSymbol, dateString, isDisabled);
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
function createDayElement(day, classes = '', statusSymbol = '', dateString = '', isDisabled = false) {
    const dayElement = document.createElement('div');
    dayElement.className = `calendar-day ${classes}`;
    dayElement.style.position = 'relative';

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

    // Add click handler for editing (only if not disabled)
    if (dateString && !classes.includes('other-month') && !isDisabled) {
        dayElement.addEventListener('click', (e) => {
            e.stopPropagation();
            showStatusDropdown(dayElement, dateString);
        });
    }

    return dayElement;
}

// Show status dropdown menu
function showStatusDropdown(dayElement, dateString) {
    // Close any existing dropdown
    const existingDropdown = document.querySelector('.status-dropdown');
    if (existingDropdown) {
        existingDropdown.remove();
    }

    const rental = rentalData.find(r => r.date === dateString);
    const currentStatus = rental ? rental.status : null;

    // Create dropdown
    const dropdown = document.createElement('div');
    dropdown.className = 'status-dropdown show';

    const statusOptions = [
        { value: 'available', label: '○ 予約可能' },
        { value: 'pending', label: '△ 仮予約' },
        { value: 'booked', label: '× 予約確定' },
        { value: 'closed', label: '- 休業日' }
    ];

    statusOptions.forEach(option => {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'status-option';
        if (option.value === currentStatus) {
            optionDiv.classList.add('selected');
        }
        optionDiv.textContent = option.label;

        optionDiv.addEventListener('click', (e) => {
            e.stopPropagation();
            updateRentalStatus(dateString, option.value);
            dropdown.remove();
        });

        dropdown.appendChild(optionDiv);
    });

    dayElement.appendChild(dropdown);

    // Close dropdown when clicking outside
    setTimeout(() => {
        document.addEventListener('click', function closeDropdown(e) {
            if (!dropdown.contains(e.target)) {
                dropdown.remove();
                document.removeEventListener('click', closeDropdown);
            }
        });
    }, 0);
}

// Get status label
function getStatusLabel(status) {
    switch (status) {
        case 'available':
            return '○ 予約可能';
        case 'pending':
            return '△ 仮予約';
        case 'booked':
            return '× 予約確定';
        case 'closed':
        default:
            return '- 休業日';
    }
}

// Update rental status (without saving to server)
function updateRentalStatus(dateString, status) {
    const rental = rentalData.find(r => r.date === dateString);

    if (rental) {
        rental.status = status;
    } else {
        const newRental = {
            id: Date.now().toString(),
            date: dateString,
            status: status
        };
        rentalData.push(newRental);
    }

    // Mark as having unsaved changes
    hasUnsavedChanges = true;
    updateSaveButtonState();

    renderCalendar();
    renderBookingList();
}

// Update save button state
function updateSaveButtonState() {
    const saveBtn = document.getElementById('save-calendar-btn');
    if (hasUnsavedChanges) {
        saveBtn.classList.remove('btn-secondary');
        saveBtn.classList.add('btn-primary');
        saveBtn.textContent = '💾 カレンダーを保存 *';
        saveBtn.style.animation = 'pulse 2s infinite';
    } else {
        saveBtn.classList.remove('btn-primary');
        saveBtn.classList.add('btn-secondary');
        saveBtn.textContent = '💾 カレンダーを保存';
        saveBtn.style.animation = 'none';
    }
}

// Save calendar changes
async function saveCalendarChanges() {
    if (!hasUnsavedChanges) {
        alert('保存する変更がありません。');
        return;
    }

    const saveBtn = document.getElementById('save-calendar-btn');
    saveBtn.disabled = true;
    saveBtn.textContent = '保存中...';

    await saveRentalData();

    hasUnsavedChanges = false;
    updateSaveButtonState();

    saveBtn.disabled = false;
    alert('カレンダーの変更を保存しました。');
}

// Save rental data to server
async function saveRentalData() {
    try {
        const response = await fetch('http://localhost:3000/api/rentals/bulk', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(rentalData)
        });

        if (!response.ok) {
            throw new Error('Server error');
        }
    } catch (error) {
        console.log('Offline mode - saving to localStorage');
        localStorage.setItem('rentalData', JSON.stringify(rentalData));
    }
}

// Render booking list
function renderBookingList() {
    const bookingList = document.getElementById('booking-list');

    // Filter bookings
    let filteredData = rentalData;
    if (currentFilter !== 'all') {
        filteredData = rentalData.filter(r => r.status === currentFilter);
    }

    // Filter bookings that have customer info
    const bookings = filteredData.filter(r => r.customerName);

    // Sort by date
    bookings.sort((a, b) => new Date(a.date) - new Date(b.date));

    if (bookings.length === 0) {
        bookingList.innerHTML = '<p style="color: #ccc; text-align: center; padding: 2rem;">予約がありません</p>';
        return;
    }

    bookingList.innerHTML = bookings.map(booking => createBookingCard(booking)).join('');

    // Add event listeners
    bookings.forEach(booking => {
        // Approve button
        const approveBtn = document.getElementById(`approve-${booking.id}`);
        if (approveBtn) {
            approveBtn.addEventListener('click', () => approveBooking(booking.id));
        }

        // Cancel button
        const cancelBtn = document.getElementById(`cancel-${booking.id}`);
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => cancelBooking(booking.id));
        }

        // Delete button
        const deleteBtn = document.getElementById(`delete-${booking.id}`);
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => deleteBooking(booking.id));
        }
    });
}

// Create booking card HTML
function createBookingCard(booking) {
    const itemNames = getItemNames(booking.items || []);

    return `
        <div class="booking-card ${booking.status}">
            <div class="booking-header">
                <div class="booking-date">${formatDate(booking.date)}</div>
                <div class="booking-status ${booking.status}">${getStatusLabel(booking.status)}</div>
            </div>

            <div class="booking-info">
                <div class="info-item">
                    <div class="info-label">お名前</div>
                    <div class="info-value">${booking.customerName}</div>
                </div>

                <div class="info-item">
                    <div class="info-label">メールアドレス</div>
                    <div class="info-value">${booking.customerEmail}</div>
                </div>

                <div class="info-item">
                    <div class="info-label">電話番号</div>
                    <div class="info-value">${booking.customerPhone}</div>
                </div>

                <div class="info-item">
                    <div class="info-label">利用目的</div>
                    <div class="info-value">${booking.usagePurpose || '未記入'}</div>
                </div>
            </div>

            ${booking.items && booking.items.length > 0 ? `
                <div class="booking-items">
                    <div class="info-label">レンタル機材</div>
                    <ul>
                        ${itemNames.map(name => `<li>• ${name}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}

            ${booking.message ? `
                <div class="info-item" style="margin-top: 1rem;">
                    <div class="info-label">備考・質問</div>
                    <div class="info-value">${booking.message}</div>
                </div>
            ` : ''}

            <div class="booking-actions">
                ${booking.status === 'pending' ? `
                    <button class="btn btn-approve btn-small" id="approve-${booking.id}">
                        入金確認・予約確定
                    </button>
                    <button class="btn btn-cancel btn-small" id="cancel-${booking.id}">
                        キャンセル（予約可能に戻す）
                    </button>
                ` : ''}
                ${booking.status === 'booked' ? `
                    <button class="btn btn-cancel btn-small" id="cancel-${booking.id}">
                        キャンセル（予約可能に戻す）
                    </button>
                ` : ''}
                <button class="btn btn-delete btn-small" id="delete-${booking.id}">
                    削除
                </button>
            </div>
        </div>
    `;
}

// Approve booking (pending -> booked)
async function approveBooking(id) {
    if (confirm('入金を確認し、予約を確定しますか？')) {
        const booking = rentalData.find(r => r.id === id);
        if (booking) {
            booking.status = 'booked';
            await saveRentalData();
            renderCalendar();
            renderBookingList();
        }
    }
}

// Cancel booking (return to available)
async function cancelBooking(id) {
    if (confirm('予約をキャンセルし、予約可能に戻しますか？')) {
        const booking = rentalData.find(r => r.id === id);
        if (booking) {
            booking.status = 'available';
            // Keep the customer info for record, but mark as canceled
            booking.canceled = true;
            await saveRentalData();
            renderCalendar();
            renderBookingList();
        }
    }
}

// Delete booking
async function deleteBooking(id) {
    if (confirm('この予約を完全に削除しますか？')) {
        const index = rentalData.findIndex(r => r.id === id);
        if (index !== -1) {
            rentalData.splice(index, 1);
            await saveRentalData();
            renderCalendar();
            renderBookingList();
        }
    }
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

// Format date to Japanese format
function formatDate(dateString) {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const dayOfWeek = ['日', '月', '火', '水', '木', '金', '土'][date.getDay()];

    return `${year}年${month}月${day}日（${dayOfWeek}）`;
}

// Export to Excel (CSV format)
function exportToExcel() {
    // Filter bookings (exclude status-only entries without customer info)
    const bookingsOnly = rentalData.filter(rental =>
        rental.customerName || rental.customerEmail || rental.customerPhone
    );

    if (bookingsOnly.length === 0) {
        alert('エクスポートする予約データがありません。');
        return;
    }

    // Sort by date (newest first)
    bookingsOnly.sort((a, b) => new Date(b.date) - new Date(a.date));

    // CSV header
    const headers = [
        '予約日',
        'ステータス',
        '利用開始時間',
        '利用終了時間',
        'お名前',
        'メールアドレス',
        '電話番号',
        '利用目的',
        '使用技法',
        'オプション機材',
        '備考',
        '予約受付日時'
    ];

    // CSV rows
    const rows = bookingsOnly.map(booking => {
        const statusText = getStatusLabel(booking.status);
        const optionItems = booking.items && booking.items.length > 0
            ? getItemNames(booking.items).join('、')
            : 'なし';

        return [
            booking.date || '',
            statusText || '',
            booking.startTime || '',
            booking.endTime || '',
            booking.customerName || '',
            booking.customerEmail || '',
            booking.customerPhone || '',
            booking.usagePurpose || '',
            booking.technique || '',
            optionItems,
            booking.message || '',
            booking.createdAt ? new Date(booking.createdAt).toLocaleString('ja-JP') : ''
        ].map(value => {
            // Escape quotes and wrap in quotes if contains comma or newline
            const stringValue = String(value);
            if (stringValue.includes(',') || stringValue.includes('\n') || stringValue.includes('"')) {
                return `"${stringValue.replace(/"/g, '""')}"`;
            }
            return stringValue;
        }).join(',');
    });

    // Combine header and rows
    const csv = [headers.join(','), ...rows].join('\n');

    // Add BOM for Excel UTF-8 recognition
    const bom = '\uFEFF';
    const blob = new Blob([bom + csv], { type: 'text/csv;charset=utf-8;' });

    // Create download link
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    // Generate filename with current date
    const now = new Date();
    const filename = `暗室レンタル予約リスト_${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}.csv`;

    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    console.log(`Exported ${bookingsOnly.length} bookings to ${filename}`);
}
