#!/bin/bash
# 執行 Supabase 遷移腳本
# 此腳本會檢查並執行尚未處理的 SQL 遷移檔案

set -e

# 設定變數
MIGRATIONS_DIR="${MIGRATIONS_DIR:-/migrations}"
POSTGRES_HOST="${POSTGRES_HOST:-db}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-postgres}"
POSTGRES_USER="${POSTGRES_USER:-supabase_admin}"
PGPASSWORD="${POSTGRES_PASSWORD}"

export PGPASSWORD

echo "=== Supabase Migration Runner ==="
echo "Host: $POSTGRES_HOST:$POSTGRES_PORT"
echo "Database: $POSTGRES_DB"
echo "Migrations Directory: $MIGRATIONS_DIR"

# 等待資料庫就緒
echo "Waiting for database to be ready..."
until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
    echo "Database is not ready yet, waiting..."
    sleep 2
done
echo "Database is ready!"

# 建立遷移追蹤表（如果不存在）
echo "Creating migration tracking table if not exists..."
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOF
CREATE TABLE IF NOT EXISTS _migrations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    executed_at TIMESTAMPTZ DEFAULT NOW()
);
EOF

# 取得已執行的遷移列表
EXECUTED_MIGRATIONS=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -A -c "SELECT name FROM _migrations ORDER BY name;")

# 遍歷遷移目錄中的 SQL 檔案（按檔名排序）
echo "Checking for pending migrations..."
PENDING_COUNT=0

for migration_file in $(ls -1 "$MIGRATIONS_DIR"/*.sql 2>/dev/null | sort); do
    filename=$(basename "$migration_file")

    # 檢查是否已執行
    if echo "$EXECUTED_MIGRATIONS" | grep -q "^${filename}$"; then
        echo "  [SKIP] $filename (already executed)"
    else
        echo "  [RUN]  $filename"

        # 執行遷移 (ON_ERROR_STOP=1 讓 psql 在遇到錯誤時停止)
        if psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -f "$migration_file"; then
            # 記錄已執行的遷移
            psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
                "INSERT INTO _migrations (name) VALUES ('$filename');"
            echo "  [OK]   $filename executed successfully"
            PENDING_COUNT=$((PENDING_COUNT + 1))
        else
            echo "  [FAIL] $filename failed to execute!"
            exit 1
        fi
    fi
done

if [ $PENDING_COUNT -eq 0 ]; then
    echo "No pending migrations found."
else
    echo "Successfully executed $PENDING_COUNT migration(s)."
fi

echo "=== Migration completed ==="
