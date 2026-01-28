-- ============================================
-- 員工權限層級系統
-- ============================================

-- 權限等級對照表
CREATE TABLE employee_permission_levels (
    employee_type employee_type PRIMARY KEY,
    permission_level INT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 插入權限等級資料
-- 等級越高，權限越大
INSERT INTO employee_permission_levels (employee_type, permission_level, description) VALUES
    ('intern', 10, '工讀生 - 基本讀取權限'),
    ('part_time', 20, '兼職員工 - 有限的寫入權限'),
    ('full_time', 30, '正式員工 - 完整操作權限'),
    ('admin', 100, '管理員 - 系統完整權限');

-- ============================================
-- user_profiles 新增員工子類型欄位
-- ============================================

-- 新增欄位
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS employee_subtype employee_type;

-- 同步員工子類型的觸發器
CREATE OR REPLACE FUNCTION sync_employee_subtype()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.employee_id IS NOT NULL THEN
        SELECT employee_type INTO NEW.employee_subtype
        FROM employees
        WHERE id = NEW.employee_id;
    ELSE
        NEW.employee_subtype = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 建立或替換觸發器
DROP TRIGGER IF EXISTS trg_sync_employee_subtype ON user_profiles;
CREATE TRIGGER trg_sync_employee_subtype
    BEFORE INSERT OR UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION sync_employee_subtype();

-- 回填現有資料
UPDATE user_profiles up
SET employee_subtype = e.employee_type
FROM employees e
WHERE up.employee_id = e.id
AND up.employee_subtype IS NULL;

-- ============================================
-- 權限相關函數
-- ============================================

-- 取得當前用戶的員工子類型
CREATE OR REPLACE FUNCTION auth.get_employee_type()
RETURNS employee_type AS $$
    SELECT employee_subtype FROM user_profiles WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 取得當前用戶的權限等級
CREATE OR REPLACE FUNCTION auth.get_employee_permission_level()
RETURNS INT AS $$
DECLARE
    v_employee_type employee_type;
    v_level INT;
BEGIN
    -- 取得員工子類型
    SELECT employee_subtype INTO v_employee_type
    FROM user_profiles
    WHERE id = auth.uid();

    -- 如果不是員工，返回 0
    IF v_employee_type IS NULL THEN
        RETURN 0;
    END IF;

    -- 查詢權限等級
    SELECT permission_level INTO v_level
    FROM employee_permission_levels
    WHERE employee_type = v_employee_type;

    RETURN COALESCE(v_level, 0);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- 檢查是否有指定的最低權限等級
CREATE OR REPLACE FUNCTION auth.has_permission_level(required_level INT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN auth.get_employee_permission_level() >= required_level;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- 檢查是否為工讀生以上（等級 >= 10）
CREATE OR REPLACE FUNCTION auth.is_intern_or_above()
RETURNS BOOLEAN AS $$
    SELECT auth.has_permission_level(10);
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 檢查是否為兼職以上（等級 >= 20）
CREATE OR REPLACE FUNCTION auth.is_part_time_or_above()
RETURNS BOOLEAN AS $$
    SELECT auth.has_permission_level(20);
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 檢查是否為正職以上（等級 >= 30）
CREATE OR REPLACE FUNCTION auth.is_full_time_or_above()
RETURNS BOOLEAN AS $$
    SELECT auth.has_permission_level(30);
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 更新 is_staff 函數以考慮員工活躍狀態
CREATE OR REPLACE FUNCTION auth.is_staff()
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM user_profiles up
        LEFT JOIN employees e ON up.employee_id = e.id
        WHERE up.id = auth.uid()
        AND up.role IN ('admin', 'employee')
        AND up.is_active = TRUE
        AND (e.id IS NULL OR e.is_active = TRUE)
    );
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- ============================================
-- RLS 政策（權限等級控制）
-- ============================================

-- 員工權限等級表的 RLS
ALTER TABLE employee_permission_levels ENABLE ROW LEVEL SECURITY;

-- 所有已認證用戶可查看權限等級定義
CREATE POLICY "Authenticated users can view permission levels"
    ON employee_permission_levels FOR SELECT
    TO authenticated
    USING (true);

-- 只有管理員可修改權限等級定義
CREATE POLICY "Only admins can manage permission levels"
    ON employee_permission_levels FOR ALL
    USING (auth.is_admin());

GRANT SELECT ON employee_permission_levels TO authenticated;

-- ============================================
-- 員工權限視圖
-- ============================================

CREATE OR REPLACE VIEW v_employee_permissions AS
SELECT
    e.id as employee_id,
    e.employee_no,
    e.name,
    e.employee_type,
    epl.permission_level,
    epl.description as permission_description,
    e.is_active,
    up.id as user_profile_id,
    up.role as user_role
FROM employees e
JOIN employee_permission_levels epl ON e.employee_type = epl.employee_type
LEFT JOIN user_profiles up ON up.employee_id = e.id
WHERE e.is_deleted = FALSE;
