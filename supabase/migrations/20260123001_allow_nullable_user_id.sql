-- ============================================
-- 允許 line_user_bindings.user_id 為 NULL
-- 用於解除綁定時保留 Line UUID 記錄
-- ============================================

-- 移除 user_id 的 NOT NULL 約束
ALTER TABLE line_user_bindings
    ALTER COLUMN user_id DROP NOT NULL;

-- 移除原有的 unique_user_channel 約束（因為 NULL 值需要特殊處理）
ALTER TABLE line_user_bindings
    DROP CONSTRAINT IF EXISTS unique_user_channel;

-- 建立新的唯一約束（僅當 user_id 不為 NULL 時生效）
-- 使用 partial unique index 而非 constraint
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_user_channel_active
    ON line_user_bindings(user_id, channel_type)
    WHERE user_id IS NOT NULL;

-- 更新 RLS 政策以處理 NULL user_id 的情況
-- 刪除舊政策
DROP POLICY IF EXISTS "Users can view own line binding" ON line_user_bindings;
DROP POLICY IF EXISTS "Users can insert own line binding" ON line_user_bindings;
DROP POLICY IF EXISTS "Users can update own line binding" ON line_user_bindings;
DROP POLICY IF EXISTS "Users can delete own line binding" ON line_user_bindings;

-- 重新建立政策（處理 NULL user_id）
CREATE POLICY "Users can view own line binding"
    ON line_user_bindings FOR SELECT
    USING (user_id IS NOT NULL AND user_id = auth.uid());

CREATE POLICY "Users can insert own line binding"
    ON line_user_bindings FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own line binding"
    ON line_user_bindings FOR UPDATE
    USING (user_id IS NOT NULL AND user_id = auth.uid());

CREATE POLICY "Users can delete own line binding"
    ON line_user_bindings FOR DELETE
    USING (user_id IS NOT NULL AND user_id = auth.uid());

-- 員工政策保持不變（已在原始遷移中定義）
