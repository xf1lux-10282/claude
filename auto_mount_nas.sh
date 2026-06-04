#!/bin/bash

# NAS自動マウントスクリプト
# パソコン起動時にXF1LUX_NASのpersonal_folderを自動接続します

NAS_SERVER="XF1LUX_NAS"
NAS_SHARE="personal_folder"
NAS_USER="daisuke10282"
MOUNT_POINT="/Volumes/personal_folder"
LOG_FILE="$HOME/Library/Logs/nas_auto_mount.log"

# ログ出力関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "=== NAS自動マウントスクリプト開始 ==="

# 既にマウントされているか確認
if mount | grep -q "$MOUNT_POINT"; then
    log "NASは既にマウントされています: $MOUNT_POINT"
    exit 0
fi

# ネットワークが利用可能になるまで待機（最大60秒）
log "ネットワーク接続を確認中..."
for i in {1..12}; do
    if ping -c 1 -t 2 "$NAS_SERVER" &>/dev/null || ping -c 1 -t 2 "${NAS_SERVER}.local" &>/dev/null; then
        log "ネットワーク接続確認完了"
        break
    fi
    if [ $i -eq 12 ]; then
        log "エラー: NASサーバーに到達できません ($NAS_SERVER)"
        exit 1
    fi
    sleep 5
done

# キーチェーンから認証情報を取得してマウント
log "NASをマウント中: smb://$NAS_SERVER/$NAS_SHARE"

# macOSのopenコマンドでマウント（キーチェーンの認証情報を使用）
open "smb://$NAS_USER@$NAS_SERVER/$NAS_SHARE" 2>&1 | tee -a "$LOG_FILE"

# マウント結果を確認
sleep 3
if mount | grep -q "$MOUNT_POINT"; then
    log "NASのマウントに成功しました: $MOUNT_POINT"
    exit 0
else
    log "エラー: NASのマウントに失敗しました"
    exit 1
fi
