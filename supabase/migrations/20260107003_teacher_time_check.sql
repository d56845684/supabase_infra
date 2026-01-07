-- ============================================
-- 教師授課時段不重複約束
-- ============================================

-- 1. 啟用 btree_gist 擴展 (Supabase 需在 Dashboard 啟用)
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- 2. 添加時間範圍欄位 (方便進行範圍比較)
ALTER TABLE teacher_available_slots 
ADD COLUMN IF NOT EXISTS time_range TSRANGE;

-- 3. 建立函數: 自動計算時間範圍
CREATE OR REPLACE FUNCTION calculate_slot_time_range()
RETURNS TRIGGER 
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.time_range := tsrange(
        (NEW.slot_date + NEW.start_time)::timestamp,
        (NEW.slot_date + NEW.end_time)::timestamp,
        '[)'
    );
    RETURN NEW;
END;
$$;

-- 4. 建立觸發器: 在 INSERT/UPDATE 前自動計算時間範圍
DROP TRIGGER IF EXISTS trg_calculate_slot_time_range ON teacher_available_slots;
CREATE TRIGGER trg_calculate_slot_time_range
    BEFORE INSERT OR UPDATE ON teacher_available_slots
    FOR EACH ROW
    EXECUTE FUNCTION calculate_slot_time_range();

-- 5. 添加排除約束: 防止同一教師的時段重疊
ALTER TABLE teacher_available_slots
DROP CONSTRAINT IF EXISTS excl_teacher_slot_overlap;

ALTER TABLE teacher_available_slots
ADD CONSTRAINT excl_teacher_slot_overlap
EXCLUDE USING gist (
    teacher_id WITH =,
    time_range WITH &&
) WHERE (is_deleted = FALSE);

-- 6. 更新現有資料的 time_range (如果有舊資料)
UPDATE teacher_available_slots
SET time_range = tsrange(
    (slot_date + start_time)::timestamp,
    (slot_date + end_time)::timestamp,
    '[)'
)
WHERE time_range IS NULL;

-- ============================================
-- 7. 驗證觸發器: 提供詳細的中文錯誤訊息
-- ============================================

CREATE OR REPLACE FUNCTION check_teacher_slot_overlap()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_conflict_id UUID;
    v_conflict_date DATE;
    v_conflict_start TIME;
    v_conflict_end TIME;
BEGIN
    SELECT id, slot_date, start_time, end_time
    INTO v_conflict_id, v_conflict_date, v_conflict_start, v_conflict_end
    FROM teacher_available_slots
    WHERE teacher_id = NEW.teacher_id
      AND id != COALESCE(NEW.id, '00000000-0000-0000-0000-000000000000'::uuid)
      AND is_deleted = FALSE
      AND slot_date = NEW.slot_date
      AND (
          (NEW.start_time >= start_time AND NEW.start_time < end_time)
          OR
          (NEW.end_time > start_time AND NEW.end_time <= end_time)
          OR
          (NEW.start_time <= start_time AND NEW.end_time >= end_time)
      )
    LIMIT 1;
    
    IF v_conflict_id IS NOT NULL THEN
        RAISE EXCEPTION '時段衝突：該教師在 % 已有 % - % 的授課時段，無法建立重疊時段',
            v_conflict_date,
            v_conflict_start::TEXT,
            v_conflict_end::TEXT;
    END IF;
    
    RETURN NEW;
END;
$$;

-- 建立檢查觸發器
DROP TRIGGER IF EXISTS trg_check_teacher_slot_overlap ON teacher_available_slots;
CREATE TRIGGER trg_check_teacher_slot_overlap
    BEFORE INSERT OR UPDATE ON teacher_available_slots
    FOR EACH ROW
    EXECUTE FUNCTION check_teacher_slot_overlap();

-- ============================================
-- 8. 查詢函數: 檢視教師某日所有時段
-- ============================================

CREATE OR REPLACE FUNCTION get_teacher_daily_slots(
    p_teacher_id UUID,
    p_date DATE
)
RETURNS TABLE (
    slot_id UUID,
    slot_start_time TIME,
    slot_end_time TIME,
    slot_is_available BOOLEAN,
    slot_is_booked BOOLEAN
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        tas.id,
        tas.start_time,
        tas.end_time,
        tas.is_available,
        tas.is_booked
    FROM teacher_available_slots tas
    WHERE tas.teacher_id = p_teacher_id
      AND tas.slot_date = p_date
      AND tas.is_deleted = FALSE
    ORDER BY tas.start_time;
END;
$$;

-- ============================================
-- 9. 查詢函數: 檢查特定時段是否可用
-- ============================================

CREATE OR REPLACE FUNCTION check_slot_availability(
    p_teacher_id UUID,
    p_date DATE,
    p_start_time TIME,
    p_end_time TIME
)
RETURNS TABLE (
    slot_available BOOLEAN,
    conflict_message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_conflict_date DATE;
    v_conflict_start TIME;
    v_conflict_end TIME;
    v_found BOOLEAN := FALSE;
BEGIN
    SELECT tas.slot_date, tas.start_time, tas.end_time
    INTO v_conflict_date, v_conflict_start, v_conflict_end
    FROM teacher_available_slots tas
    WHERE tas.teacher_id = p_teacher_id
      AND tas.slot_date = p_date
      AND tas.is_deleted = FALSE
      AND (
          (p_start_time >= tas.start_time AND p_start_time < tas.end_time)
          OR (p_end_time > tas.start_time AND p_end_time <= tas.end_time)
          OR (p_start_time <= tas.start_time AND p_end_time >= tas.end_time)
      )
    LIMIT 1;
    
    v_found := FOUND;
    
    IF v_found THEN
        RETURN QUERY SELECT 
            FALSE::BOOLEAN,
            FORMAT('與現有時段衝突: %s %s-%s', 
                   v_conflict_date, 
                   v_conflict_start::TEXT, 
                   v_conflict_end::TEXT)::TEXT;
    ELSE
        RETURN QUERY SELECT TRUE::BOOLEAN, NULL::TEXT;
    END IF;
END;
$$;

-- ============================================
-- 10. 測試範例
-- ============================================

-- 測試: 先插入一個時段
-- INSERT INTO teacher_available_slots (teacher_id, slot_date, start_time, end_time)
-- VALUES ('teacher-uuid-here', '2024-01-15', '09:00', '10:00');

-- 測試: 嘗試插入重疊時段 (應該失敗)
-- INSERT INTO teacher_available_slots (teacher_id, slot_date, start_time, end_time)
-- VALUES ('teacher-uuid-here', '2024-01-15', '09:30', '10:30');

-- 測試: 插入連續時段 (應該成功)
-- INSERT INTO teacher_available_slots (teacher_id, slot_date, start_time, end_time)
-- VALUES ('teacher-uuid-here', '2024-01-15', '10:00', '11:00');

-- 查詢教師某日時段
-- SELECT * FROM get_teacher_daily_slots('teacher-uuid', '2024-01-15');

-- 檢查時段是否可用
-- SELECT * FROM check_slot_availability('teacher-uuid', '2024-01-15', '14:00', '15:00');