// Event Manager JavaScript
class EventManager {
    constructor() {
        this.events = this.loadEvents();
        this.currentEditId = null;
        this.init();
    }

    init() {
        this.renderEventList();
        this.attachEventListeners();
    }

    // Load events from localStorage
    loadEvents() {
        const stored = localStorage.getItem('ap2lab_events');
        return stored ? JSON.parse(stored) : [];
    }

    // Save events to localStorage
    saveEvents() {
        localStorage.setItem('ap2lab_events', JSON.stringify(this.events));
    }

    // Generate unique ID
    generateId() {
        return 'event_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Attach event listeners
    attachEventListeners() {
        // Form submission
        document.getElementById('event-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFormSubmit();
        });

        // Reset button
        document.getElementById('reset-form').addEventListener('click', () => {
            this.resetForm();
        });

        // Export JSON
        document.getElementById('export-json').addEventListener('click', () => {
            this.exportJSON();
        });

        // Export HTML
        document.getElementById('export-html').addEventListener('click', () => {
            this.exportHTML();
        });

        // Import JSON
        document.getElementById('import-json').addEventListener('change', (e) => {
            this.importJSON(e);
        });

        // Date display update
        document.getElementById('event-date').addEventListener('change', (e) => {
            this.updateDateDisplay(e.target.value);
        });
    }

    // Update date display with day of week
    updateDateDisplay(dateString) {
        const dateDisplay = document.getElementById('date-display');
        if (!dateString) {
            dateDisplay.textContent = '';
            return;
        }

        const date = new Date(dateString + 'T00:00:00');
        const daysOfWeek = ['日曜日', '月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日'];
        const dayOfWeek = daysOfWeek[date.getDay()];

        const year = date.getFullYear();
        const month = date.getMonth() + 1;
        const day = date.getDate();

        dateDisplay.textContent = `${year}年${month}月${day}日（${dayOfWeek}）`;
    }

    // Handle form submission
    handleFormSubmit() {
        const formData = new FormData(document.getElementById('event-form'));

        // Get selected techniques
        const techniques = Array.from(
            document.querySelectorAll('input[name="techniques"]:checked')
        ).map(cb => cb.value);

        // Build time string
        const startHour = formData.get('startHour');
        const startMinute = formData.get('startMinute');
        const endHour = formData.get('endHour');
        const endMinute = formData.get('endMinute');

        let timeString = '';
        if (startHour && startMinute) {
            timeString = `${startHour}:${startMinute}`;
            if (endHour && endMinute) {
                timeString += `-${endHour}:${endMinute}`;
            }
        }

        // Get date with day of week
        const eventDate = formData.get('date');
        const dateDisplay = this.formatDateWithDayOfWeek(eventDate);

        const eventData = {
            id: this.currentEditId || this.generateId(),
            title: formData.get('title'),
            type: formData.get('type'),
            status: formData.get('status'),
            date: eventDate,
            dateDisplay: dateDisplay,
            time: timeString,
            startHour: startHour || '',
            startMinute: startMinute || '',
            endHour: endHour || '',
            endMinute: endMinute || '',
            techniques: techniques,
            description: formData.get('description'),
            capacity: formData.get('capacity') || '',
            applyUrl: formData.get('applyUrl') || '',
            image: formData.get('image') || this.getDefaultImage(formData.get('type')),
            createdAt: this.currentEditId ?
                this.events.find(e => e.id === this.currentEditId).createdAt :
                new Date().toISOString()
        };

        if (this.currentEditId) {
            // Update existing event
            const index = this.events.findIndex(e => e.id === this.currentEditId);
            this.events[index] = eventData;
        } else {
            // Add new event
            this.events.push(eventData);
        }

        // Sort events by date
        this.events.sort((a, b) => new Date(a.date) - new Date(b.date));

        this.saveEvents();
        this.renderEventList();
        this.resetForm();

        alert(this.currentEditId ? 'イベントを更新しました' : 'イベントを追加しました');
    }

    // Get default image based on event type
    getDefaultImage(type) {
        return type === 'workshop' ? 'workshop-placeholder.jpg' : 'seminar-placeholder.jpg';
    }

    // Format date with day of week
    formatDateWithDayOfWeek(dateString) {
        if (!dateString) return '';

        const date = new Date(dateString + 'T00:00:00');
        const daysOfWeek = ['日', '月', '火', '水', '木', '金', '土'];
        const dayOfWeek = daysOfWeek[date.getDay()];

        const year = date.getFullYear();
        const month = date.getMonth() + 1;
        const day = date.getDate();

        return `${year}年${month}月${day}日（${dayOfWeek}）`;
    }

    // Render event list
    renderEventList() {
        const listContainer = document.getElementById('event-list');

        if (this.events.length === 0) {
            listContainer.innerHTML = '<p style="text-align: center; color: #999;">イベントが登録されていません</p>';
            return;
        }

        listContainer.innerHTML = this.events.map(event => this.createEventItemHTML(event)).join('');

        // Attach action button listeners
        this.events.forEach(event => {
            document.getElementById(`edit-${event.id}`).addEventListener('click', () => {
                this.editEvent(event.id);
            });
            document.getElementById(`delete-${event.id}`).addEventListener('click', () => {
                this.deleteEvent(event.id);
            });
        });
    }

    // Create event item HTML
    createEventItemHTML(event) {
        const typeLabels = {
            'workshop': 'Workshop',
            'seminar': 'Seminar',
            'other': 'Other'
        };

        const statusLabels = {
            'recruiting': '募集中',
            'waiting': 'キャンセル待ち',
            'closed': '募集終了'
        };

        // Format date display
        const dateDisplay = event.dateDisplay || this.formatDateWithDayOfWeek(event.date);
        const fullDateTime = event.time ? `${dateDisplay} ${event.time}` : dateDisplay;

        return `
            <div class="event-item">
                <div class="event-item-info">
                    <h3 class="event-item-title">${event.title}</h3>
                    <div class="event-item-meta">
                        <span class="event-item-badge badge-${event.type}">${typeLabels[event.type]}</span>
                        <span class="event-item-badge badge-${event.status}">${statusLabels[event.status]}</span>
                        <span>📅 ${fullDateTime}</span>
                        ${event.capacity ? `<span>👥 ${event.capacity}名</span>` : ''}
                    </div>
                    <p class="event-item-description">${event.description}</p>
                    ${event.techniques.length > 0 ?
                        `<p class="event-item-techniques">技法: ${event.techniques.join(', ')}</p>` :
                        ''}
                    ${event.applyUrl ?
                        `<p class="event-item-apply-url">🔗 申込URL: <a href="${event.applyUrl}" target="_blank">${event.applyUrl}</a></p>` :
                        ''}
                </div>
                <div class="event-item-actions">
                    <button class="btn btn-edit" id="edit-${event.id}">編集</button>
                    <button class="btn btn-danger" id="delete-${event.id}">削除</button>
                </div>
            </div>
        `;
    }

    // Edit event
    editEvent(id) {
        const event = this.events.find(e => e.id === id);
        if (!event) return;

        this.currentEditId = id;

        // Fill form with event data
        document.getElementById('event-id').value = event.id;
        document.getElementById('event-title').value = event.title;
        document.getElementById('event-type').value = event.type;
        document.getElementById('event-status').value = event.status;
        document.getElementById('event-date').value = event.date;
        document.getElementById('event-description').value = event.description;
        document.getElementById('event-capacity').value = event.capacity || '';
        document.getElementById('event-apply-url').value = event.applyUrl || '';
        document.getElementById('event-image').value = event.image;

        // Set time selects
        document.getElementById('start-hour').value = event.startHour || '';
        document.getElementById('start-minute').value = event.startMinute || '';
        document.getElementById('end-hour').value = event.endHour || '';
        document.getElementById('end-minute').value = event.endMinute || '';

        // Update date display
        this.updateDateDisplay(event.date);

        // Check technique checkboxes
        document.querySelectorAll('input[name="techniques"]').forEach(cb => {
            cb.checked = event.techniques.includes(cb.value);
        });

        // Scroll to form
        document.querySelector('.form-section').scrollIntoView({ behavior: 'smooth' });
    }

    // Delete event
    deleteEvent(id) {
        if (!confirm('このイベントを削除してもよろしいですか?')) return;

        this.events = this.events.filter(e => e.id !== id);
        this.saveEvents();
        this.renderEventList();

        alert('イベントを削除しました');
    }

    // Reset form
    resetForm() {
        document.getElementById('event-form').reset();
        document.getElementById('event-id').value = '';
        document.getElementById('date-display').textContent = '';
        this.currentEditId = null;
    }

    // Export to JSON
    exportJSON() {
        const dataStr = JSON.stringify(this.events, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `ap2lab_events_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        URL.revokeObjectURL(url);
    }

    // Import from JSON
    importJSON(e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const importedEvents = JSON.parse(event.target.result);
                if (!Array.isArray(importedEvents)) {
                    alert('無効なJSONファイルです');
                    return;
                }

                if (confirm('現在のイベントデータを上書きしますか？')) {
                    this.events = importedEvents;
                    this.saveEvents();
                    this.renderEventList();
                    alert('インポートが完了しました');
                }
            } catch (error) {
                alert('JSONファイルの読み込みに失敗しました: ' + error.message);
            }
        };
        reader.readAsText(file);

        // Reset file input
        e.target.value = '';
    }

    // Export to HTML (for event.html)
    exportHTML() {
        const html = this.generateEventCardsHTML();
        const blob = new Blob([html], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `event_cards_${new Date().toISOString().split('T')[0]}.html`;
        link.click();
        URL.revokeObjectURL(url);

        alert('HTMLコードを生成しました。event.htmlのイベントカード部分に貼り付けてください。');
    }

    // Generate event cards HTML
    generateEventCardsHTML() {
        const typeLabels = {
            'workshop': 'Workshop',
            'seminar': 'Seminar',
            'other': 'Other'
        };

        const statusLabels = {
            'recruiting': '募集中',
            'waiting': 'キャンセル待ち',
            'closed': '募集終了'
        };

        return this.events.map(event => {
            // Format date display with day of week
            const dateDisplay = event.dateDisplay || this.formatDateWithDayOfWeek(event.date);
            const fullDateTime = event.time ? `${dateDisplay} ${event.time}` : dateDisplay;

            // Truncate description to 100 characters
            const shortDescription = event.description.length > 100
                ? event.description.substring(0, 100) + '...'
                : event.description;

            return `
                        <!-- Event Card: ${event.title} -->
                        <div class="event-card" data-technique="${event.techniques.join(' ')}" data-type="${event.type}" data-date="${event.date}">
                            <div class="event-card-image">
                                <img src="${event.image}" alt="${event.title}">
                                <span class="event-type-badge ${event.type}">${typeLabels[event.type]}</span>
                            </div>
                            <div class="event-card-content">
                                <h4 class="event-card-title">${event.title}</h4>
                                <p class="event-card-date">開催日：${fullDateTime}</p>
                                ${event.capacity ? `<p class="event-card-capacity">募集人数：${event.capacity}名</p>` : ''}
                                <p class="event-card-status ${event.status}">${statusLabels[event.status]}</p>
                                <p class="event-card-description">
                                    ${shortDescription}
                                </p>
                                <p class="event-card-link">
                                    <a href="event-detail.html?id=${event.id}" class="btn-detail">詳細を見る</a>
                                </p>
                            </div>
                        </div>
`;
        }).join('\n');
    }
}

// Initialize Event Manager
const eventManager = new EventManager();
