-- ============================================
-- Line 通知日誌表
-- ============================================

-- 通知類型
CREATE TYPE notification_type AS ENUM (
    'booking_confirmation',  -- 預約確認
    'booking_reminder',      -- 預約提醒
    'booking_cancelled',     -- 預約取消
    'status_update',         -- 狀態更新
    'general'                -- 一般通知
);

-- 通知狀態
CREATE TYPE notification_status AS ENUM (
    'pending',   -- 待發送
    'sent',      -- 已發送
    'failed',    -- 發送失敗
    'skipped'    -- 略過（用戶關閉通知）
);

-- Line 通知日誌表
CREATE TABLE line_notification_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    line_user_id VARCHAR(50) NOT NULL,

    -- 頻道類型（記錄透過哪個頻道發送）
    channel_type line_channel_type NOT NULL DEFAULT 'student',

    -- 通知內容
    notification_type notification_type NOT NULL,
    reference_id UUID,                    -- 關聯的實體 ID（如 booking_id）
    reference_type VARCHAR(50),           -- 關聯的實體類型（如 'booking'）
    message_template VARCHAR(100),        -- 使用的訊息模板
    message_content TEXT,                 -- 實際發送的訊息內容

    -- 發送狀態
    notification_status notification_status DEFAULT 'pending',
    line_message_id VARCHAR(100),         -- Line API 回傳的訊息 ID
    error_message TEXT,                   -- 錯誤訊息（如果發送失敗）
    retry_count INT DEFAULT 0,            -- 重試次數
    sent_at TIMESTAMPTZ,                  -- 實際發送時間

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_notification_logs_user ON line_notification_logs(user_id);
CREATE INDEX idx_notification_logs_line_user ON line_notification_logs(line_user_id);
CREATE INDEX idx_notification_logs_channel ON line_notification_logs(channel_type);
CREATE INDEX idx_notification_logs_status ON line_notification_logs(notification_status);
CREATE INDEX idx_notification_logs_type ON line_notification_logs(notification_type);
CREATE INDEX idx_notification_logs_reference ON line_notification_logs(reference_type, reference_id);
CREATE INDEX idx_notification_logs_created ON line_notification_logs(created_at DESC);

-- 待發送通知索引
CREATE INDEX idx_notification_logs_pending
    ON line_notification_logs(notification_status, created_at)
    WHERE notification_status = 'pending';

-- 自動更新 updated_at
CREATE TRIGGER trg_notification_logs_updated_at
    BEFORE UPDATE ON line_notification_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_line_binding_updated_at();

-- ============================================
-- RLS 政策
-- ============================================

ALTER TABLE line_notification_logs ENABLE ROW LEVEL SECURITY;

-- 用戶可查看自己的通知記錄
CREATE POLICY "Users can view own notifications"
    ON line_notification_logs FOR SELECT
    USING (user_id = auth.uid());

-- 員工可查看所有通知記錄
CREATE POLICY "Staff can view all notifications"
    ON line_notification_logs FOR SELECT
    USING (auth.is_staff());

-- 員工可管理通知記錄
CREATE POLICY "Staff can manage notifications"
    ON line_notification_logs FOR ALL
    USING (auth.is_staff());

-- 系統可插入通知記錄（透過 service role）
GRANT SELECT ON line_notification_logs TO authenticated;
GRANT INSERT, UPDATE ON line_notification_logs TO service_role;

-- ============================================
-- 通知統計視圖
-- ============================================

CREATE OR REPLACE VIEW v_notification_stats AS
SELECT
    channel_type,
    notification_type,
    notification_status,
    COUNT(*) as count,
    DATE_TRUNC('day', created_at) as date
FROM line_notification_logs
GROUP BY channel_type, notification_type, notification_status, DATE_TRUNC('day', created_at);

-- 用戶通知偏好視圖（按頻道類型）
CREATE OR REPLACE VIEW v_user_notification_preferences AS
SELECT
    u.id as user_id,
    u.email,
    lb.channel_type,
    lb.line_user_id,
    lb.notify_booking_confirmation,
    lb.notify_booking_reminder,
    lb.notify_status_update,
    lb.binding_status
FROM auth.users u
LEFT JOIN line_user_bindings lb ON u.id = lb.user_id;
