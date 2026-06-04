// AP2 Lab Event Manager - Auto Upload Version
// Connects to Node.js server for automatic FTP upload

class EventManagerAuto {
    constructor() {
        this.events = [];
        this.currentEditId = null;
        this.apiBaseUrl = 'http://localhost:3000/api';

        this.init();
    }

    async init() {
        // Load events from server
        await this.loadEvents();

        // Setup event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Form submission
        document.getElementById('event-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFormSubmit();
        });

        // Reset button
        document.getElementById('reset-form').addEventListener('click', () => {
            this.resetForm();
        });

        // Date display update
        document.getElementById('event-date').addEventListener('change', (e) => {
            this.updateDateDisplay(e.target.value);
        });

        // Image management buttons
        document.getElementById('select-image-btn').addEventListener('click', () => {
            this.openImageGallery();
        });

        document.getElementById('upload-image-btn').addEventListener('click', () => {
            this.openImageUpload();
        });

        // Modal close buttons
        document.getElementById('close-gallery').addEventListener('click', () => {
            this.closeImageGallery();
        });

        document.getElementById('close-upload').addEventListener('click', () => {
            this.closeImageUpload();
        });

        // Image upload
        document.getElementById('choose-file-btn').addEventListener('click', () => {
            document.getElementById('image-file-input').click();
        });

        document.getElementById('image-file-input').addEventListener('change', (e) => {
            this.handleFileSelect(e);
        });

        document.getElementById('upload-file-btn').addEventListener('click', () => {
            this.uploadImage();
        });

        // Image URL input change
        document.getElementById('event-image').addEventListener('input', (e) => {
            this.updateImagePreview(e.target.value);
        });

        // Close modals on outside click
        window.addEventListener('click', (e) => {
            const galleryModal = document.getElementById('image-gallery-modal');
            const uploadModal = document.getElementById('image-upload-modal');
            if (e.target === galleryModal) {
                this.closeImageGallery();
            }
            if (e.target === uploadModal) {
                this.closeImageUpload();
            }
        });
    }

    // Load events from server
    async loadEvents() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/events`);
            if (response.ok) {
                this.events = await response.json();
                this.renderEventList();
            } else {
                console.error('Failed to load events');
                this.events = [];
            }
        } catch (error) {
            console.error('Error loading events:', error);
            this.events = [];
        }
    }

    // Save events to server and automatically upload to FTP
    async saveEvents() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/events`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.events)
            });

            if (response.ok) {
                const result = await response.json();
                console.log('✓ サーバーに保存しました');

                // Automatically upload to FTP after saving
                try {
                    const uploadResponse = await fetch(`${this.apiBaseUrl}/upload`, {
                        method: 'POST'
                    });

                    if (uploadResponse.ok) {
                        console.log('✓ FTPアップロード完了');
                        return { ...result, uploaded: true };
                    } else {
                        console.warn('FTPアップロードに失敗しましたが、データは保存されています');
                        return { ...result, uploaded: false };
                    }
                } catch (uploadError) {
                    console.warn('FTPアップロードエラー:', uploadError);
                    return { ...result, uploaded: false };
                }
            } else {
                throw new Error('Failed to save events');
            }
        } catch (error) {
            console.error('Error saving events:', error);
            throw error;
        }
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
    async handleFormSubmit() {
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
            const index = this.events.findIndex(e => e.id === this.currentEditId);
            this.events[index] = eventData;
        } else {
            this.events.push(eventData);
        }

        try {
            const result = await this.saveEvents();
            this.renderEventList();
            this.resetForm();

            const statusDiv = document.getElementById('upload-status');
            if (result.uploaded) {
                statusDiv.textContent = '✓ イベントを保存し、本番サイトに反映しました！';
                statusDiv.className = 'status-message status-success';
                alert(this.currentEditId ? 'イベントを更新し、本番サイトに反映しました！' : 'イベントを追加し、本番サイトに反映しました！');
            } else {
                statusDiv.textContent = '✓ イベントを保存しました（FTPアップロードは手動で実行してください）';
                statusDiv.className = 'status-message status-warning';
                alert(this.currentEditId ? 'イベントを更新しました（FTPアップロードは手動で実行してください）' : 'イベントを追加しました（FTPアップロードは手動で実行してください）');
            }
        } catch (error) {
            alert(`エラー: ${error.message}`);
        }
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

        listContainer.innerHTML = this.events.map(event => this.renderEventItem(event)).join('');

        // Add edit/delete event listeners
        this.events.forEach(event => {
            document.getElementById(`edit-${event.id}`).addEventListener('click', () => {
                this.editEvent(event.id);
            });
            document.getElementById(`delete-${event.id}`).addEventListener('click', () => {
                this.deleteEvent(event.id);
            });
        });
    }

    renderEventItem(event) {
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
                    <button class="btn btn-delete" id="delete-${event.id}">削除</button>
                </div>
            </div>
        `;
    }

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
        this.updateImagePreview(event.image);

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

    async deleteEvent(id) {
        if (!confirm('このイベントを削除してもよろしいですか？')) return;

        this.events = this.events.filter(e => e.id !== id);

        try {
            const result = await this.saveEvents();
            this.renderEventList();

            if (result.uploaded) {
                alert('イベントを削除し、本番サイトに反映しました！');
            } else {
                alert('イベントを削除しました（FTPアップロードは手動で実行してください）');
            }
        } catch (error) {
            alert(`エラー: ${error.message}`);
        }
    }

    // Reset form
    resetForm() {
        document.getElementById('event-form').reset();
        document.getElementById('event-id').value = '';
        document.getElementById('date-display').textContent = '';
        this.currentEditId = null;
    }

    // Generate unique ID
    generateId() {
        return 'event_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Image Management Methods

    // Open image gallery modal
    async openImageGallery() {
        const modal = document.getElementById('image-gallery-modal');
        modal.classList.add('active');
        await this.loadImageGallery();
    }

    // Close image gallery modal
    closeImageGallery() {
        const modal = document.getElementById('image-gallery-modal');
        modal.classList.remove('active');
    }

    // Open image upload modal
    openImageUpload() {
        const modal = document.getElementById('image-upload-modal');
        modal.classList.add('active');
        // Reset upload form
        document.getElementById('image-file-input').value = '';
        document.getElementById('selected-file-name').textContent = '';
        document.getElementById('upload-file-btn').style.display = 'none';
        document.getElementById('upload-status').textContent = '';
        document.getElementById('upload-status').className = 'upload-status';
    }

    // Close image upload modal
    closeImageUpload() {
        const modal = document.getElementById('image-upload-modal');
        modal.classList.remove('active');
    }

    // Load image gallery
    async loadImageGallery() {
        const gallery = document.getElementById('image-gallery');
        gallery.innerHTML = '<p style="text-align: center;">読み込み中...</p>';

        try {
            const response = await fetch(`${this.apiBaseUrl}/images`);
            if (response.ok) {
                const images = await response.json();

                if (images.length === 0) {
                    gallery.innerHTML = '<p style="text-align: center; color: #999;">画像がありません</p>';
                    return;
                }

                gallery.innerHTML = images.map(img => this.renderGalleryItem(img)).join('');

                // Add click listeners
                images.forEach(img => {
                    const item = document.querySelector(`[data-image-url="${img.url}"]`);
                    if (item) {
                        item.addEventListener('click', () => {
                            this.selectImage(img.url);
                        });

                        const deleteBtn = item.querySelector('.btn-delete-image');
                        if (deleteBtn) {
                            deleteBtn.addEventListener('click', (e) => {
                                e.stopPropagation();
                                this.deleteImage(img.filename);
                            });
                        }
                    }
                });
            } else {
                gallery.innerHTML = '<p style="text-align: center; color: #d32f2f;">画像の読み込みに失敗しました</p>';
            }
        } catch (error) {
            console.error('Error loading images:', error);
            gallery.innerHTML = `
                <p style="text-align: center; color: #d32f2f;">サーバーに接続できません</p>
                <p style="text-align: center; color: #999; font-size: 0.9em; margin-top: 1rem;">
                    画像URLを直接入力してください<br>
                    （例: images/events/example.jpg）
                </p>
            `;
        }
    }

    // Render gallery item
    renderGalleryItem(image) {
        const sizeKB = Math.round(image.size / 1024);
        return `
            <div class="gallery-item" data-image-url="${image.url}">
                <img src="${image.url}" alt="${image.filename}" class="gallery-item-image">
                <div class="gallery-item-info">
                    <div>${image.filename}</div>
                    <div>${sizeKB} KB</div>
                </div>
                <div class="gallery-item-actions">
                    <button class="btn-delete-image" title="削除">×</button>
                </div>
            </div>
        `;
    }

    // Select image from gallery
    selectImage(imageUrl) {
        document.getElementById('event-image').value = imageUrl;
        this.updateImagePreview(imageUrl);
        this.closeImageGallery();
    }

    // Update image preview
    updateImagePreview(imageUrl) {
        const preview = document.getElementById('selected-image-preview');
        if (imageUrl) {
            preview.innerHTML = `<img src="${imageUrl}" alt="選択された画像">`;
        } else {
            preview.innerHTML = '';
        }
    }

    // Handle file select
    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            document.getElementById('selected-file-name').textContent = file.name;
            document.getElementById('upload-file-btn').style.display = 'inline-block';
        }
    }

    // Upload image
    async uploadImage() {
        const fileInput = document.getElementById('image-file-input');
        const file = fileInput.files[0];

        if (!file) {
            alert('ファイルを選択してください');
            return;
        }

        const uploadBtn = document.getElementById('upload-file-btn');
        const statusDiv = document.getElementById('upload-status');

        uploadBtn.disabled = true;
        uploadBtn.textContent = 'アップロード中...';
        statusDiv.textContent = '';
        statusDiv.className = 'upload-status';

        const formData = new FormData();
        formData.append('image', file);

        try {
            const response = await fetch(`${this.apiBaseUrl}/images/upload`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                statusDiv.textContent = '✓ アップロード完了！';
                statusDiv.className = 'upload-status success';

                // Auto-select uploaded image
                setTimeout(() => {
                    this.selectImage(result.image.url);
                    this.closeImageUpload();
                }, 1000);
            } else {
                const error = await response.json();
                throw new Error(error.error || 'アップロードに失敗しました');
            }
        } catch (error) {
            console.error('Upload error:', error);
            statusDiv.textContent = `✗ ${error.message}`;
            statusDiv.className = 'upload-status error';
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'アップロード';
        }
    }

    // Delete image
    async deleteImage(filename) {
        if (!confirm(`画像「${filename}」を削除してもよろしいですか？`)) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/images/${filename}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                alert('画像を削除しました');
                await this.loadImageGallery();
            } else {
                const error = await response.json();
                throw new Error(error.error || '削除に失敗しました');
            }
        } catch (error) {
            console.error('Delete error:', error);
            alert(`エラー: ${error.message}`);
        }
    }
}

// Initialize Event Manager
const eventManager = new EventManagerAuto();
