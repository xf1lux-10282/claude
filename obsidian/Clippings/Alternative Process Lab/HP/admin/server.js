// AP2 Lab Event Management Server
// Node.js server for automatic FTP upload

const express = require('express');
const cors = require('cors');
const fs = require('fs').promises;
const path = require('path');
const ftp = require('basic-ftp');
const multer = require('multer');
const crypto = require('crypto');

const app = express();
const PORT = 3000;

// Simple authentication storage (in production, use a proper database)
const adminCredentials = [
    {
        username: 'd.kinoshita@altphotolab.com',
        passwordHash: crypto.createHash('sha256').update('10282Newyork!').digest('hex'),
        displayName: 'Daisuke Kinoshita'
    },
    {
        username: 'y.inomata@altphotolab.com',
        passwordHash: crypto.createHash('sha256').update('y4f3Inomata!').digest('hex'),
        displayName: 'Yuki Inomata'
    },
    {
        username: 'admin@altphotolab.com',
        passwordHash: crypto.createHash('sha256').update('ap2Lab2026!').digest('hex'),
        displayName: 'Administrator'
    }
];

// Store active sessions
const activeSessions = new Map();

// Generate session token
function generateToken() {
    return crypto.randomBytes(32).toString('hex');
}

// Image storage configuration
const IMAGES_DIR = path.join(__dirname, '..', 'images', 'events');

// Ensure images directory exists
async function ensureImagesDir() {
    try {
        await fs.access(IMAGES_DIR);
    } catch {
        await fs.mkdir(IMAGES_DIR, { recursive: true });
        console.log('✓ Created images directory:', IMAGES_DIR);
    }
}

// Configure multer for file upload
const storage = multer.diskStorage({
    destination: async (req, file, cb) => {
        await ensureImagesDir();
        cb(null, IMAGES_DIR);
    },
    filename: (req, file, cb) => {
        // Generate unique filename: timestamp_originalname
        const timestamp = Date.now();
        const ext = path.extname(file.originalname);
        const basename = path.basename(file.originalname, ext)
            .replace(/[^a-zA-Z0-9]/g, '_'); // Replace special chars with underscore
        cb(null, `${timestamp}_${basename}${ext}`);
    }
});

const upload = multer({
    storage: storage,
    limits: { fileSize: 10 * 1024 * 1024 }, // 10MB limit
    fileFilter: (req, file, cb) => {
        const allowedTypes = /jpeg|jpg|png|gif|webp/;
        const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
        const mimetype = allowedTypes.test(file.mimetype);

        if (extname && mimetype) {
            cb(null, true);
        } else {
            cb(new Error('画像ファイルのみアップロード可能です（JPEG, PNG, GIF, WebP）'));
        }
    }
});

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '..')));
app.use('/images', express.static(path.join(__dirname, '..', 'images')));

// Data storage path
const DATA_FILE = path.join(__dirname, 'events-data.json');
const RENTAL_DATA_FILE = path.join(__dirname, 'rental-data.json');

// FTP Configuration (will be loaded from config file)
let ftpConfig = {
    host: '',
    user: '',
    password: '',
    secure: false,
    remotePath: '/public_html/' // Adjust to your server path
};

// Load FTP config
async function loadFTPConfig() {
    try {
        const configPath = path.join(__dirname, 'ftp-config.json');
        const data = await fs.readFile(configPath, 'utf8');
        ftpConfig = JSON.parse(data);
        console.log('✓ FTP設定を読み込みました');
    } catch (error) {
        console.log('⚠ FTP設定ファイルが見つかりません。ftp-config.jsonを作成してください。');
    }
}

// Load events data
async function loadEvents() {
    try {
        const data = await fs.readFile(DATA_FILE, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        return [];
    }
}

// Save events data
async function saveEvents(events) {
    await fs.writeFile(DATA_FILE, JSON.stringify(events, null, 2));
}

// Load rental data
async function loadRentals() {
    try {
        const data = await fs.readFile(RENTAL_DATA_FILE, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        return [];
    }
}

// Save rental data
async function saveRentals(rentals) {
    await fs.writeFile(RENTAL_DATA_FILE, JSON.stringify(rentals, null, 2));
}

// Generate event.html content
function generateEventHTML(events) {
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

    function formatDateWithDayOfWeek(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString + 'T00:00:00');
        const daysOfWeek = ['日', '月', '火', '水', '木', '金', '土'];
        const dayOfWeek = daysOfWeek[date.getDay()];
        const year = date.getFullYear();
        const month = date.getMonth() + 1;
        const day = date.getDate();
        return `${year}年${month}月${day}日（${dayOfWeek}）`;
    }

    const eventCards = events.map(event => {
        const dateDisplay = event.dateDisplay || formatDateWithDayOfWeek(event.date);
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
                        </div>`;
    }).join('\n');

    return eventCards;
}

// Upload to FTP
async function uploadToFTP(localPath, remotePath) {
    const client = new ftp.Client();
    client.ftp.verbose = true;

    try {
        await client.access(ftpConfig);
        console.log('✓ FTPサーバーに接続しました');

        // Ensure remote directory exists
        const remoteDir = path.dirname(remotePath);
        try {
            await client.ensureDir(remoteDir);
            console.log(`✓ ディレクトリを確認/作成: ${remoteDir}`);
        } catch (dirError) {
            console.log(`⚠ ディレクトリ作成スキップ: ${dirError.message}`);
        }

        await client.uploadFrom(localPath, remotePath);
        console.log(`✓ アップロード完了: ${remotePath}`);

        return { success: true };
    } catch (error) {
        console.error('✗ FTPアップロードエラー:', error.message);
        return { success: false, error: error.message };
    } finally {
        client.close();
    }
}

// API Routes

// Get all events
app.get('/api/events', async (req, res) => {
    try {
        const events = await loadEvents();
        res.json(events);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Save events and update HTML
app.post('/api/events', async (req, res) => {
    try {
        const events = req.body;

        // Save to data file
        await saveEvents(events);

        // Generate new HTML
        const eventCardsHTML = generateEventHTML(events);

        // Read current event.html
        const eventHTMLPath = path.join(__dirname, '..', 'event.html');
        let eventHTML = await fs.readFile(eventHTMLPath, 'utf8');

        // Replace event cards section
        const startMarker = '<!-- Event Grid -->';
        const endMarker = '<!-- No Results Message -->';
        const startIndex = eventHTML.indexOf(startMarker);
        const endIndex = eventHTML.indexOf(endMarker);

        if (startIndex !== -1 && endIndex !== -1) {
            const beforeCards = eventHTML.substring(0, startIndex);
            const afterCards = eventHTML.substring(endIndex);

            eventHTML = beforeCards +
                        startMarker + '\n' +
                        '                <div class="event-grid-container">\n' +
                        '                    <div class="event-count">\n' +
                        '                        <span id="event-count-text">全 ' + events.length + ' 件</span>\n' +
                        '                    </div>\n' +
                        '                    <div class="event-grid">\n' +
                        eventCardsHTML + '\n' +
                        '                    </div>\n\n' +
                        '                    ' + afterCards;

            // Save updated HTML
            await fs.writeFile(eventHTMLPath, eventHTML);
            console.log('✓ event.htmlを更新しました');
        }

        res.json({
            success: true,
            message: 'イベントを保存しました',
            autoUploadEnabled: ftpConfig.host !== ''
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Upload to FTP
app.post('/api/upload', async (req, res) => {
    try {
        if (!ftpConfig.host) {
            return res.status(400).json({
                error: 'FTP設定が未設定です。ftp-config.jsonを作成してください。'
            });
        }

        const eventHTMLPath = path.join(__dirname, '..', 'event.html');
        const remotePath = ftpConfig.remotePath + 'event.html';

        const result = await uploadToFTP(eventHTMLPath, remotePath);

        if (result.success) {
            res.json({ success: true, message: 'FTPアップロード完了' });
        } else {
            res.status(500).json({ error: result.error });
        }
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Upload all files to FTP
app.post('/api/upload-all', async (req, res) => {
    try {
        if (!ftpConfig.host) {
            return res.status(400).json({
                error: 'FTP設定が未設定です。ftp-config.jsonを作成してください。'
            });
        }

        const baseDir = path.join(__dirname, '..');
        const results = [];
        const errors = [];

        // Files to upload (excluding admin directory)
        const filesToUpload = [
            // HTML files
            'index.html',
            'about.html',
            'about-intro.html',
            'about-staff.html',
            'about-access.html',
            'access.html',
            'event.html',
            'event-detail.html',
            'event-workshop.html',
            'event-seminar.html',
            'technique-platinum.html',
            'technique-cyanotype.html',
            'technique-digitalnegative.html',
            'technique-albumen.html',
            'technique-wetplate.html',
            'technique-gum.html',
            'technique-kallitype.html',
            'technique-daguerreotype.html',
            'technique-silver.html',
            'technique-dryplate.html',

            // CSS files
            'style.css',
            'about-style.css',
            'access-style.css',
            'event-style.css',
            'event-detail-style.css',
            'technique-style.css',

            // JavaScript files
            'event-detail.js',

            // Images
            'AP2lab-white.png',
            'AP2lab-insta.png',
            'instagram-icon.png',
            'x-icon.png',
            'note-icon.svg',
            'staff-placeholder.jpg',

            // Videos
            'AP2intro.mp4',
            'AP2intro (Vertical).mp4'
        ];

        console.log('\n=== 一括FTPアップロード開始 ===');

        for (const file of filesToUpload) {
            const localPath = path.join(baseDir, file);
            const remotePath = ftpConfig.remotePath + file;

            try {
                // Check if file exists
                await fs.access(localPath);

                console.log(`アップロード中: ${file}...`);
                const result = await uploadToFTP(localPath, remotePath);

                if (result.success) {
                    results.push({ file, success: true });
                    console.log(`✓ 成功: ${file}`);
                } else {
                    errors.push({ file, error: result.error });
                    console.log(`✗ 失敗: ${file} - ${result.error}`);
                }
            } catch (error) {
                console.log(`⚠ スキップ: ${file} (ファイルが存在しません)`);
            }
        }

        console.log('\n=== アップロード完了 ===');
        console.log(`成功: ${results.length}件`);
        console.log(`失敗: ${errors.length}件\n`);

        res.json({
            success: true,
            message: `${results.length}件のファイルをアップロードしました`,
            results: results,
            errors: errors,
            total: filesToUpload.length,
            uploaded: results.length,
            failed: errors.length
        });

    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Test FTP connection
app.get('/api/test-ftp', async (req, res) => {
    const client = new ftp.Client();

    try {
        if (!ftpConfig.host) {
            return res.status(400).json({
                success: false,
                message: 'FTP設定が未設定です'
            });
        }

        await client.access(ftpConfig);
        client.close();

        res.json({
            success: true,
            message: 'FTP接続テスト成功',
            config: {
                host: ftpConfig.host,
                user: ftpConfig.user,
                remotePath: ftpConfig.remotePath
            }
        });
    } catch (error) {
        res.json({
            success: false,
            message: 'FTP接続テスト失敗: ' + error.message
        });
    }
});

// Image Management APIs

// Get all images
app.get('/api/images', async (req, res) => {
    try {
        await ensureImagesDir();
        const files = await fs.readdir(IMAGES_DIR);

        const images = [];
        for (const file of files) {
            const filePath = path.join(IMAGES_DIR, file);
            const stats = await fs.stat(filePath);

            if (stats.isFile() && /\.(jpg|jpeg|png|gif|webp)$/i.test(file)) {
                images.push({
                    filename: file,
                    url: `images/events/${file}`,
                    size: stats.size,
                    uploadedAt: stats.mtime
                });
            }
        }

        // Sort by upload date (newest first)
        images.sort((a, b) => b.uploadedAt - a.uploadedAt);

        res.json(images);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Upload image
app.post('/api/images/upload', upload.single('image'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: '画像ファイルが選択されていません' });
        }

        const imageUrl = `images/events/${req.file.filename}`;

        res.json({
            success: true,
            message: '画像をアップロードしました',
            image: {
                filename: req.file.filename,
                url: imageUrl,
                size: req.file.size
            }
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Delete image
app.delete('/api/images/:filename', async (req, res) => {
    try {
        const filename = req.params.filename;
        const filePath = path.join(IMAGES_DIR, filename);

        // Check if file exists
        try {
            await fs.access(filePath);
        } catch {
            return res.status(404).json({ error: '画像が見つかりません' });
        }

        // Delete file
        await fs.unlink(filePath);

        res.json({
            success: true,
            message: '画像を削除しました'
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// ========================================
// Rental Management APIs
// ========================================

// Get all rental bookings
app.get('/api/rentals', async (req, res) => {
    try {
        const rentals = await loadRentals();
        res.json(rentals);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Create new rental booking (status automatically set to 'pending')
app.post('/api/rentals', async (req, res) => {
    try {
        const rentals = await loadRentals();

        const newRental = {
            id: Date.now().toString(),
            ...req.body,
            status: 'pending', // Automatically set to pending (キャンセル待ち)
            createdAt: new Date().toISOString()
        };

        rentals.push(newRental);
        await saveRentals(rentals);

        res.json({
            success: true,
            message: '予約を受け付けました',
            rental: newRental
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Update rental booking status
app.put('/api/rentals/:id', async (req, res) => {
    try {
        const rentals = await loadRentals();
        const rentalId = req.params.id;
        const { status } = req.body;

        const rentalIndex = rentals.findIndex(r => r.id === rentalId);
        if (rentalIndex === -1) {
            return res.status(404).json({ error: '予約が見つかりません' });
        }

        // Update status
        rentals[rentalIndex].status = status;
        rentals[rentalIndex].updatedAt = new Date().toISOString();

        await saveRentals(rentals);

        res.json({
            success: true,
            message: 'ステータスを更新しました',
            rental: rentals[rentalIndex]
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Delete rental booking
app.delete('/api/rentals/:id', async (req, res) => {
    try {
        const rentals = await loadRentals();
        const rentalId = req.params.id;

        const rentalIndex = rentals.findIndex(r => r.id === rentalId);
        if (rentalIndex === -1) {
            return res.status(404).json({ error: '予約が見つかりません' });
        }

        rentals.splice(rentalIndex, 1);
        await saveRentals(rentals);

        res.json({
            success: true,
            message: '予約を削除しました'
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Bulk update rentals (for admin calendar management)
app.post('/api/rentals/bulk', async (req, res) => {
    try {
        const rentals = req.body;
        await saveRentals(rentals);

        res.json({
            success: true,
            message: 'レンタルデータを保存しました'
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// ========================================
// Admin Authentication APIs
// ========================================

// Admin login
app.post('/api/admin/login', (req, res) => {
    try {
        const { username, password } = req.body;

        // Validate credentials
        const passwordHash = crypto.createHash('sha256').update(password).digest('hex');

        // Find matching user in credentials array
        const user = adminCredentials.find(u =>
            u.username === username && u.passwordHash === passwordHash
        );

        if (user) {
            // Generate session token
            const token = generateToken();

            // Store session (expires in 24 hours)
            const expiresAt = Date.now() + (24 * 60 * 60 * 1000);
            activeSessions.set(token, {
                username: user.username,
                displayName: user.displayName,
                expiresAt
            });

            res.json({
                success: true,
                token,
                username: user.username,
                displayName: user.displayName
            });
        } else {
            res.status(401).json({
                success: false,
                error: 'ユーザー名またはパスワードが正しくありません'
            });
        }
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Verify admin token
app.get('/api/admin/verify', (req, res) => {
    try {
        const authHeader = req.headers.authorization;
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({ error: '認証トークンが必要です' });
        }

        const token = authHeader.substring(7);
        const session = activeSessions.get(token);

        if (!session) {
            return res.status(401).json({ error: '無効なトークンです' });
        }

        if (Date.now() > session.expiresAt) {
            activeSessions.delete(token);
            return res.status(401).json({ error: 'トークンの有効期限が切れています' });
        }

        res.json({
            success: true,
            username: session.username
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Admin logout
app.post('/api/admin/logout', (req, res) => {
    try {
        const authHeader = req.headers.authorization;
        if (authHeader && authHeader.startsWith('Bearer ')) {
            const token = authHeader.substring(7);
            activeSessions.delete(token);
        }

        res.json({ success: true, message: 'ログアウトしました' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Start server
app.listen(PORT, async () => {
    console.log('=====================================');
    console.log('  AP2 Lab Event Management Server');
    console.log('=====================================');
    console.log(`✓ サーバー起動: http://localhost:${PORT}`);
    console.log(`✓ 管理画面: http://localhost:${PORT}/admin/event-manager-auto.html`);

    await loadFTPConfig();

    console.log('=====================================');
    console.log('サーバーを停止するには Ctrl+C を押してください');
});
