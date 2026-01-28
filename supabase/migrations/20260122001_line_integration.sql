-- ============================================
-- Line 整合 - 用戶綁定表
-- ============================================

-- Line 綁定狀態
CREATE TYPE line_binding_status AS ENUM ('pending', 'active', 'unlinked');

-- Line 頻道類型（用於區分不同角色的通知頻道）
CREATE TYPE line_channel_type AS ENUM ('student', 'teacher', 'employee');

-- Line 用戶綁定表
-- 注意：同一個用戶可能在不同頻道有不同的綁定（一人多角色情境）
CREATE TABLE line_user_bindings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    line_user_id VARCHAR(50) NOT NULL,
    line_display_name VARCHAR(100),
    line_picture_url TEXT,
    line_email VARCHAR(255),
    binding_status line_binding_status DEFAULT 'active',

    -- 頻道類型（學生/老師/員工使用不同的 Line Channel）
    channel_type line_channel_type NOT NULL DEFAULT 'student',

    -- 通知偏好設定
    notify_booking_confirmation BOOLEAN DEFAULT TRUE,
    notify_booking_reminder BOOLEAN DEFAULT TRUE,
    notify_status_update BOOLEAN DEFAULT TRUE,

    -- 綁定時間記錄
    bound_at TIMESTAMPTZ DEFAULT NOW(),
    unbound_at TIMESTAMPTZ,

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 同一用戶在同一頻道只能綁定一個 Line 帳號
    CONSTRAINT unique_user_channel UNIQUE(user_id, channel_type),
    -- 同一 Line 帳號在同一頻道只能綁定一個用戶
    CONSTRAINT unique_line_channel UNIQUE(line_user_id, channel_type)
);

-- 索引
CREATE INDEX idx_line_bindings_user ON line_user_bindings(user_id);
CREATE INDEX idx_line_bindings_user_channel ON line_user_bindings(user_id, channel_type);
CREATE INDEX idx_line_bindings_line_user ON line_user_bindings(line_user_id);
CREATE INDEX idx_line_bindings_line_channel ON line_user_bindings(line_user_id, channel_type);
CREATE INDEX idx_line_bindings_email ON line_user_bindings(line_email) WHERE line_email IS NOT NULL;
CREATE INDEX idx_line_bindings_status ON line_user_bindings(binding_status);
CREATE INDEX idx_line_bindings_channel_type ON line_user_bindings(channel_type);

-- 自動更新 updated_at
CREATE OR REPLACE FUNCTION update_line_binding_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_line_bindings_updated_at
    BEFORE UPDATE ON line_user_bindings
    FOR EACH ROW
    EXECUTE FUNCTION update_line_binding_updated_at();

-- ============================================
-- RLS 政策
-- ============================================

ALTER TABLE line_user_bindings ENABLE ROW LEVEL SECURITY;

-- 用戶可查看自己的 Line 綁定
CREATE POLICY "Users can view own line binding"
    ON line_user_bindings FOR SELECT
    USING (user_id = auth.uid());

-- 用戶可管理自己的 Line 綁定
CREATE POLICY "Users can insert own line binding"
    ON line_user_bindings FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own line binding"
    ON line_user_bindings FOR UPDATE
    USING (user_id = auth.uid());

CREATE POLICY "Users can delete own line binding"
    ON line_user_bindings FOR DELETE
    USING (user_id = auth.uid());

-- 員工可查看所有 Line 綁定
CREATE POLICY "Staff can view all line bindings"
    ON line_user_bindings FOR SELECT
    USING (auth.is_staff());

-- 授予權限
GRANT SELECT, INSERT, UPDATE, DELETE ON line_user_bindings TO authenticated;

-- ============================================
-- 輔助函數
-- ============================================

-- 透過 Line User ID 和頻道類型取得用戶 ID
CREATE OR REPLACE FUNCTION get_user_by_line_id(
    p_line_user_id VARCHAR,
    p_channel_type line_channel_type DEFAULT 'student'
)
RETURNS UUID AS $$
    SELECT user_id FROM line_user_bindings
    WHERE line_user_id = p_line_user_id
    AND channel_type = p_channel_type
    AND binding_status = 'active';
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 檢查用戶在特定頻道是否已綁定 Line
CREATE OR REPLACE FUNCTION is_line_bound(
    p_user_id UUID,
    p_channel_type line_channel_type DEFAULT NULL
)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM line_user_bindings
        WHERE user_id = p_user_id
        AND binding_status = 'active'
        AND (p_channel_type IS NULL OR channel_type = p_channel_type)
    );
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 透過 email 查找已綁定 Line 的用戶
CREATE OR REPLACE FUNCTION find_user_by_line_email(p_email VARCHAR)
RETURNS UUID AS $$
    SELECT id FROM auth.users
    WHERE email = p_email;
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 取得用戶在特定頻道的 Line User ID
CREATE OR REPLACE FUNCTION get_line_user_id_by_channel(
    p_user_id UUID,
    p_channel_type line_channel_type
)
RETURNS VARCHAR AS $$
    SELECT line_user_id FROM line_user_bindings
    WHERE user_id = p_user_id
    AND channel_type = p_channel_type
    AND binding_status = 'active';
$$ LANGUAGE sql SECURITY DEFINER STABLE;
