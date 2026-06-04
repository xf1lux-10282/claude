#!/bin/bash

# iCloud to NAS Backup Script
# iCloudを優先し、NASにバックアップを作成します

ICLOUD_DIR="/Users/daisukekinoshita/Library/Mobile Documents/iCloud~md~obsidian/Documents"
NAS_DIR="/Volumes/obsidian"
LOG_DIR="$ICLOUD_DIR/sync_logs"
LOG_FILE="$LOG_DIR/sync_$(date +%Y%m%d_%H%M%S).log"

# ログディレクトリの作成
mkdir -p "$LOG_DIR"

# ログ出力関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# NASがマウントされているか確認
if [ ! -d "$NAS_DIR" ]; then
    log "エラー: NAS ($NAS_DIR) がマウントされていません"
    exit 1
fi

log "=== 同期開始 ==="
log "iCloud: $ICLOUD_DIR"
log "NAS: $NAS_DIR"

# NASにしか存在しないファイルをリストアップ
log ""
log "=== NASにのみ存在するファイル・ディレクトリの確認 ==="
NAS_ONLY_FILE="$LOG_DIR/nas_only_files_$(date +%Y%m%d_%H%M%S).txt"

# obsidianディレクトリの比較
diff -rq "$ICLOUD_DIR/obsidian" "$NAS_DIR/obsidian" 2>/dev/null | grep "Only in $NAS_DIR" > "$NAS_ONLY_FILE"

if [ -s "$NAS_ONLY_FILE" ]; then
    log "警告: NASにのみ存在するファイルが見つかりました"
    log "詳細は以下のファイルを確認してください: $NAS_ONLY_FILE"
    cat "$NAS_ONLY_FILE" | tee -a "$LOG_FILE"
else
    log "NASにのみ存在するファイルはありません"
    rm "$NAS_ONLY_FILE"
fi

# rsyncでiCloudからNASへバックアップ
log ""
log "=== rsyncによる同期開始 ==="

# rsyncオプション:
# -a: アーカイブモード（パーミッション、タイムスタンプなど保持）
# -v: 詳細出力
# -h: 人間が読みやすい形式
# --delete: iCloudにないファイルをNASから削除（コメントアウトしています。必要に応じて有効化してください）
# --exclude: 除外パターン

rsync -avh \
    --exclude='.DS_Store' \
    --exclude='._*' \
    --exclude='.Spotlight-V100' \
    --exclude='.Trashes' \
    --exclude='.TemporaryItems' \
    --exclude='.fseventsd' \
    --exclude='.DocumentRevisions-V100' \
    --exclude='sync_logs/' \
    "$ICLOUD_DIR/obsidian/" "$NAS_DIR/obsidian/" 2>&1 | tee -a "$LOG_FILE"

RSYNC_EXIT_CODE=${PIPESTATUS[0]}

if [ $RSYNC_EXIT_CODE -eq 0 ]; then
    log ""
    log "=== 同期完了 ==="
    log "iCloudのデータがNASに正常にバックアップされました"
else
    log ""
    log "エラー: rsyncが終了コード $RSYNC_EXIT_CODE で終了しました"
    exit $RSYNC_EXIT_CODE
fi

# .claudeディレクトリとWEBディレクトリも同期
log ""
log "=== .claudeディレクトリの同期 ==="
if [ -d "$ICLOUD_DIR/.claude" ]; then
    rsync -avh --exclude='.DS_Store' "$ICLOUD_DIR/.claude/" "$NAS_DIR/.claude/" 2>&1 | tee -a "$LOG_FILE"
fi

log ""
log "=== WEBディレクトリの同期 ==="
if [ -d "$ICLOUD_DIR/WEB" ]; then
    rsync -avh --exclude='.DS_Store' "$ICLOUD_DIR/WEB/" "$NAS_DIR/WEB/" 2>&1 | tee -a "$LOG_FILE"
fi

log ""
log "すべての同期が完了しました"
log "ログファイル: $LOG_FILE"
