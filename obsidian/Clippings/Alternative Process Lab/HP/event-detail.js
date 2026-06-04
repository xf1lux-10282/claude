// Event Detail Page JavaScript

class EventDetail {
    constructor() {
        this.eventId = this.getEventIdFromURL();
        this.init();
    }

    init() {
        if (this.eventId) {
            this.loadEventDetail();
        } else {
            this.showError('イベントIDが指定されていません。');
        }
    }

    // Get event ID from URL parameter
    getEventIdFromURL() {
        const params = new URLSearchParams(window.location.search);
        return params.get('id');
    }

    // Load event detail
    async loadEventDetail() {
        try {
            // Try to load from server API first (if Node.js server is running)
            const response = await fetch('http://localhost:3000/api/events');
            if (response.ok) {
                const events = await response.json();
                const event = events.find(e => e.id === this.eventId);

                if (event) {
                    this.renderEventDetail(event);
                } else {
                    this.showError('イベントが見つかりませんでした。');
                }
                return;
            }
        } catch (error) {
            console.log('Server API not available, trying localStorage...');
        }

        // Fallback to localStorage
        try {
            const storedEvents = localStorage.getItem('events');
            if (storedEvents) {
                const events = JSON.parse(storedEvents);
                const event = events.find(e => e.id === this.eventId);

                if (event) {
                    this.renderEventDetail(event);
                } else {
                    this.showError('イベントが見つかりませんでした。');
                }
            } else {
                this.showError('イベントデータが見つかりませんでした。');
            }
        } catch (error) {
            this.showError('データの読み込みに失敗しました。');
        }
    }

    // Render event detail
    renderEventDetail(event) {
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

        // Set page title
        document.title = `${event.title} - ap2lab`;
        document.getElementById('breadcrumb-title').textContent = event.title;

        // Format date display
        const dateDisplay = event.dateDisplay || this.formatDateWithDayOfWeek(event.date);
        const fullDateTime = event.time ? `${dateDisplay} ${event.time}` : dateDisplay;

        // Render detail HTML
        const detailHTML = `
            <div class="event-detail-header">
                <img src="${event.image}" alt="${event.title}" class="event-detail-image">
                <span class="event-detail-type-badge ${event.type}">${typeLabels[event.type]}</span>
            </div>

            <div class="event-detail-body">
                <h1 class="event-detail-title">${event.title}</h1>

                <div class="event-detail-meta">
                    <div class="event-detail-meta-item">
                        <span class="icon">📅</span>
                        <span>${fullDateTime}</span>
                    </div>
                    ${event.capacity ? `
                    <div class="event-detail-meta-item">
                        <span class="icon">👥</span>
                        <span>募集人数：${event.capacity}名</span>
                    </div>
                    ` : ''}
                    <div class="event-detail-meta-item">
                        <span class="event-detail-status ${event.status}">${statusLabels[event.status]}</span>
                    </div>
                </div>

                <div class="event-detail-section">
                    <h2 class="event-detail-section-title">イベント詳細</h2>
                    <p class="event-detail-description">${event.description}</p>
                </div>

                ${event.techniques && event.techniques.length > 0 ? `
                <div class="event-detail-section">
                    <h2 class="event-detail-section-title">技法</h2>
                    <div class="event-detail-techniques">
                        ${event.techniques.map(tech => `<span class="technique-tag">${this.formatTechniqueName(tech)}</span>`).join('')}
                    </div>
                </div>
                ` : ''}

                ${this.renderApplySection(event)}
            </div>
        `;

        document.getElementById('event-detail-content').innerHTML = detailHTML;
    }

    // Render apply section based on event status
    renderApplySection(event) {
        if (!event.applyUrl) {
            return '';
        }

        switch (event.status) {
            case 'recruiting':
                // 募集中：申し込みボタンを表示
                return `
                <div class="event-detail-apply">
                    <p class="event-detail-apply-title">参加をご希望の方は、下記のフォームよりお申し込みください。</p>
                    <a href="${event.applyUrl}" target="_blank" rel="noopener noreferrer" class="btn-apply">申込フォームへ</a>
                </div>
                `;

            case 'waiting':
                // キャンセル待ち：コンタクトフォームへのリンクを表示
                return `
                <div class="event-detail-apply">
                    <p class="event-detail-apply-title">現在キャンセル待ちを受け付けております。</p>
                    <p class="event-detail-apply-subtitle">キャンセル待ちをご希望の方は、コンタクトフォームよりお問い合わせください。</p>
                    <a href="contact.html?subject=キャンセル待ち: ${encodeURIComponent(event.title)}" class="btn-apply btn-waiting">キャンセル待ちを申し込む</a>
                </div>
                `;

            case 'closed':
                // 募集終了：クリックできないボタンを表示
                return `
                <div class="event-detail-apply">
                    <p class="event-detail-apply-title event-closed-message">こちらのイベントは受付を終了いたしました。</p>
                    <button class="btn-apply btn-disabled" disabled>受付終了</button>
                </div>
                `;

            default:
                return '';
        }
    }

    // Format technique name for display
    formatTechniqueName(tech) {
        const techNames = {
            'platinum-print': 'Platinum Print',
            'cyanotype': 'Cyanotype',
            'digital-negative': 'Digital Negative',
            'albumen-print': 'Albumen Print',
            'wet-plate': 'Wet Plate',
            'gum-print': 'Gum Print',
            'kallitype': 'Kallitype',
            'alternative-process': 'Alternative Process'
        };
        return techNames[tech] || tech;
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

    // Show error message
    showError(message) {
        document.getElementById('event-detail-content').innerHTML = `
            <div class="error-message">
                <p>${message}</p>
                <p><a href="event.html">イベント一覧に戻る</a></p>
            </div>
        `;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new EventDetail();
});
