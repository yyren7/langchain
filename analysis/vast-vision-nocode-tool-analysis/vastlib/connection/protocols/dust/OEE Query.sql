-- 設備id
WITH equipment_extract AS (
    SELECT
        m.line_id,
        m.machine_id,
        l.factory_id
    FROM masters.m_machine m
    LEFT JOIN (
        SELECT line_id, factory_id, project_id
        FROM masters.m_line
        WHERE is_valid is true
    ) AS l
    ON m.line_id = l.line_id
    WHERE m.is_valid is true
    AND m.machine_id in ('1', '6', '7')
    AND m.line_id in ('1','4','5')
)
-- 設備別タイムゾーン
, time_zone AS (
    SELECT machine_id, ml.*
    FROM masters.m_machine mm
    LEFT JOIN (
        SELECT line_id, mf.*
        FROM masters.m_line ml
        LEFT JOIN (
            SELECT f.timezone, pgtz.utc_offset, factory_id
            FROM masters.m_factory f
            LEFT JOIN (
                SELECT
                    name,
                    utc_offset
                FROM pg_timezone_names
            ) AS pgtz
            ON f.timezone = pgtz.name
            WHERE f.is_valid is true
            AND factory_id in (SELECT factory_id FROM equipment_extract)
        ) AS mf
        ON ml.factory_id = mf.factory_id
        WHERE is_valid is True
    ) AS ml
    ON mm.line_id = ml.line_id
    WHERE is_valid is True
)


-- 設定した設備別のシフト時間 + timezone
, machine_shifttime AS (
    SELECT mm.machine_id, mts.*, tz.timezone
    FROM masters.m_machine mm
    LEFT JOIN (
        SELECT *
        FROM masters.m_time_shifttime
        WHERE is_valid is True
    ) AS mts
    ON mm.line_id = mts.line_id
    LEFT JOIN (
        SELECT * FROM time_zone
    ) AS tz
    ON mm.machine_id = tz.machine_id
    WHERE mts.is_valid is true
)
-- 設定した設備別の基本休憩時間 + timezone
, machine_resttime_default AS (
    SELECT mm.machine_id, mtr.*, tz.timezone
    FROM masters.m_machine mm
    LEFT JOIN (
        SELECT *
        FROM masters.m_time_resttime_default
        WHERE is_valid is True
    ) AS mtr
    ON mm.line_id = mtr.line_id
    LEFT JOIN (
        SELECT * FROM time_zone
    ) AS tz
    ON mm.machine_id = tz.machine_id
    WHERE mtr.is_valid is true
)


-- 設備別シフト開始/終了タイムスタンプ
, machine_shift_datetime AS (
    SELECT *
    FROM (
        -- 1日分前
        SELECT
            *,
            (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + start_time::interval - interval '1 day') AT TIME ZONE timezone AS start_datetime,
            CASE
                WHEN end_time >= start_time
                    THEN (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + end_time::interval - interval '1 day') AT TIME ZONE timezone
                ELSE  (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + end_time::interval) AT TIME ZONE timezone
            END AS end_datetime
        FROM machine_shifttime
        -- 当日
        UNION ALL
        SELECT
            *,
            (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + start_time::interval) AT TIME ZONE timezone AS start_datetime,
            CASE
                WHEN end_time >= start_time
                    THEN (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + end_time::interval) AT TIME ZONE timezone
                ELSE  (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + end_time::interval + interval '1 day') AT TIME ZONE timezone
            END AS end_datetime
        FROM machine_shifttime
        -- 1日後
        UNION ALL
        SELECT
            *,
            (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + start_time::interval + interval '1 day') AT TIME ZONE timezone AS start_datetime,
            CASE
                WHEN end_time >= start_time
                    THEN (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + end_time::interval + interval '1 day') AT TIME ZONE timezone
                ELSE  (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + end_time::interval + interval '2 day') AT TIME ZONE timezone
            END AS end_datetime
        FROM machine_shifttime
    )
    WHERE is_valid is true
    AND '2024-06-19T10:59:59Z'::timestamptz    BETWEEN start_datetime AND end_datetime
)

-- 設備別の基本休憩開始/終了タイムスタンプ
, machine_rest_default_datetime AS (
    SELECT
        mrd.*
    FROM (
        -- 1日分前
        SELECT
            *,
            (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + start_time::interval - interval '1 day') AT TIME ZONE timezone AS start_datetime,
            CASE
                WHEN end_time >= start_time
                    THEN (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + end_time::interval - interval '1 day') AT TIME ZONE timezone
                ELSE  (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + end_time::interval) AT TIME ZONE timezone
            END AS end_datetime
        FROM machine_resttime_default
        -- 当日
        UNION ALL
        SELECT
            *,
            (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + start_time::interval) AT TIME ZONE timezone AS start_datetime,
            CASE
                WHEN end_time >= start_time
                    THEN (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + end_time::interval) AT TIME ZONE timezone
                ELSE  (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + end_time::interval + interval '1 day') AT TIME ZONE timezone
            END AS end_datetime
        FROM machine_resttime_default
        -- 1日後
        UNION ALL
        SELECT
            *,
            (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + start_time::interval + interval '1 day') AT TIME ZONE timezone AS start_datetime,
            CASE
                WHEN end_time >= start_time
                    THEN (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + end_time::interval + interval '1 day') AT TIME ZONE timezone
                ELSE  (DATE_TRUNC('day', '2024-06-19T10:59:59Z' AT TIME ZONE 'UTC') + end_time::interval + interval '2 day') AT TIME ZONE timezone
            END AS end_datetime
        FROM machine_resttime_default
    ) AS mrd
    LEFT JOIN (
        SELECT * FROM machine_shift_datetime
    ) AS msd
    ON mrd.machine_id = msd.machine_id
    AND (mrd.start_datetime BETWEEN msd.start_datetime AND msd.end_datetime
        OR mrd.start_datetime BETWEEN msd.start_datetime AND msd.end_datetime)
    WHERE mrd.is_valid is true
)

--     設備別の手動入力の休憩時間
, machine_manual_planned_rest_time AS (
    SELECT
        ame.machine_id,
        ame.line_id,
        ame.name,
        CASE
            --シフト開始時刻よりも前の場合はシフト開始時刻に置き換える
            WHEN ame.start_time <= msd.start_datetime
                THEN msd.start_datetime
            --シフト開始時刻よりも後の場合はそのまま
            ELSE ame.start_time
        END AS start_datetime,
        CASE
            --現時刻よりも後の場合は現時刻に置き換える
            WHEN ame.end_time >= msd.end_datetime
                THEN msd.end_datetime
            --現時刻よりも前の場合はそのまま
            WHEN ame.end_time < msd.end_datetime
                THEN ame.end_time
            --nullの場合、start_timeに置き換えることで差分を計算するとき0にする
            WHEN ame.end_time IS NULL
                THEN ame.start_time
            ELSE ame.end_time
        END AS end_datetime
    FROM (
        -- TODO カテゴリ別でデータ入力がある場合、休憩時間のみを取得するようにする
        SELECT
            COALESCE(ame.machine_id, mm.machine_id) as machine_id,
            ame.line_id,
            comment as name,
            start_time,
            end_time
        FROM addons.t_manual_event ame
        LEFT JOIN (
            SELECT * FROM masters.m_machine
        ) AS mm
        ON ame.line_id = mm.line_id
        WHERE ame.is_valid is True
    ) AS ame
    LEFT JOIN (
        SELECT * FROM machine_shift_datetime
    ) AS msd
    ON ame.machine_id = msd.machine_id
)

-- 重複含む休憩時間
, union_planned_rest_time AS (
    SELECT
        row_number() over() as id, *
    FROM (
        SELECT machine_id, line_id, name, start_datetime, end_datetime
        FROM machine_rest_default_datetime
        UNION ALL
        SELECT machine_id, line_id, name, start_datetime, end_datetime
        FROM machine_manual_planned_rest_time
    )
)

-- 休憩時間の重複分
, overlap_union_planned_rest_time AS (
    SELECT
        x.id,
        x.line_id,
        x.machine_id,
        CASE
            WHEN x.start_datetime <= y.start_datetime THEN x.start_datetime
            WHEN x.start_datetime > y.start_datetime THEN y.start_datetime
        END as start_datetime,
        CASE
            WHEN x.end_datetime >= y.end_datetime THEN x.end_datetime
            WHEN x.end_datetime < y.end_datetime THEN y.end_datetime
        END as end_datetime
    FROM union_planned_rest_time as x, union_planned_rest_time as y
    WHERE x.machine_id = y.machine_id
    AND (x.start_datetime BETWEEN y.start_datetime AND y.end_datetime
           OR x.end_datetime BETWEEN y.start_datetime AND y.end_datetime
           OR x.start_datetime < y.start_datetime AND x.end_datetime > y.end_datetime)
    AND x.id <> y.id
)

-- 重複含まない休憩時間の合算
, planned_rest_time AS (
    SELECT
        line_id, machine_id, start_datetime, end_datetime
    FROM union_planned_rest_time
    WHERE id not in (
        -- 重複分を削除
        SELECT id FROM overlap_union_planned_rest_time
    )
    UNION ALL
    SELECT DISTINCT line_id, machine_id, start_datetime, end_datetime
    FROM overlap_union_planned_rest_time
    ORDER BY machine_id, start_datetime ASC
)


-- 生産モデルの変化
, product_model_status AS (
    SELECT
        rpm.machine_id,
        data_type,
        product_model,
        start_datetime,
        CASE
            WHEN end_datetime is null THEN now()
            ELSE end_datetime
        END AS end_datetime
    FROM (
        SELECT
            rs.machine_id,
            data_type,
            COALESCE(product_model_name, value) AS product_model,
            time AS start_datetime,
            LEAD(time) OVER (PARTITION BY rs.machine_id ORDER BY time, created_at asc) AS end_datetime
        FROM records.t_record_status rs
        LEFT JOIN (
            SELECT
                mcc.machine_id,
                trigger_value,
                product_model_name
            FROM (
                SELECT
                    controller_connection_id,
                    data_type,
                    trigger_value,
                    COALESCE(name, item_value) AS product_model_name
                FROM masters.m_datalocation md
                LEFT JOIN (
                    SELECT product_model_id, name FROM masters.m_product_model
                    WHERE is_valid is true
                ) AS mpm
                ON md.item_value::text = mpm.product_model_id::text
                WHERE is_valid is True
                AND replace(data_type, ' ', '') ILIKE '%productmodel%'
            ) AS md
            LEFT JOIN (
                SELECT * FROM masters.m_controller_connection
                WHERE is_valid is True
            ) AS mcc
            ON md.controller_connection_id = mcc.controller_connection_id
        ) AS mpm
        ON rs.machine_id = mpm.machine_id
        AND rs.value::text = mpm.trigger_value::text
        WHERE is_valid is true
        AND rs.machine_id in (1, 6, 7)
        AND replace(data_type, ' ', '') ILIKE '%productmodel%'
        AND time BETWEEN '2024-06-19 00:00:00' AND '2024-06-20 00:00:00'
        ORDER BY time, created_at ASC
    ) AS rpm
)

-- 設備毎の休憩時間の生産数
-- 製品モデル毎の休憩時間の生産数
, planned_rest_output AS (
    SELECT
        DISTINCT
            machine_id,
--             COALESCE(SUM(diff_value) OVER (PARTITION BY machine_id), 0) AS value_machine
            product_model,
--             COALESCE(SUM(diff_value) OVER (PARTITION BY product_model), 0) AS value_product
            COALESCE(SUM(diff_value) OVER (PARTITION BY machine_id, product_model), 0) AS value
    FROM(
        SELECT
            DISTINCT
                machine_id,
                line_id,
                product_model,
                lastvalue,
                firstvalue,
                lastvalue - firstvalue AS diff_value
        FROM(
            SELECT
                *,
                -- machine_id, product_model毎の期間中の最初と最後のvalueを抽出する
                FIRST_VALUE(value) OVER(PARTITION BY machine_id, product_model, start_datetime ORDER BY time ASC) AS firstvalue,
                LAST_VALUE(value) OVER(PARTITION BY machine_id, product_model, start_datetime ORDER BY time RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS lastvalue
            FROM (
                SELECT
                    extract_value.machine_id,
                    extract_value.line_id,
                    extract_value.time,
                    extract_value.value,
                    pm.product_model,
                    -- 製品モデル切替情報を休憩時間内に収める。
                    CASE
                        WHEN pm.start_datetime BETWEEN planned_rest_value.start_datetime AND planned_rest_value.end_datetime THEN pm.start_datetime
                        WHEN pm.start_datetime < planned_rest_value.start_datetime THEN planned_rest_value.start_datetime
                        ELSE null
                    END AS start_datetime,
                    CASE
                        WHEN pm.end_datetime BETWEEN planned_rest_value.start_datetime AND planned_rest_value.end_datetime THEN pm.end_datetime
                        WHEN pm.end_datetime > planned_rest_value.end_datetime THEN planned_rest_value.end_datetime
                        ELSE null
                    END AS end_datetime
                FROM(
                    SELECT
                        t.machine_id, t.time, t.value, e.line_id
                    FROM records.t_record_count as t
                    LEFT JOIN (
                        SELECT machine_id, line_id FROM equipment_extract
                    ) AS e
                    ON t.machine_id = e.machine_id
                    WHERE is_valid is true
                    AND t.machine_id in (SELECT machine_id FROM equipment_extract)
                    AND replace(t.data_type, ' ', '') ILIKE '%output%'
                )AS extract_value

                -- 製品モデルの切り替わり時間情報
                LEFT JOIN (
                    SELECT * FROM product_model_status
                ) AS pm
                ON extract_value.machine_id = pm.machine_id

                -- 休憩時間の情報
                LEFT JOIN(
                    SELECT * FROM planned_rest_time
                )AS planned_rest_value
                ON extract_value.machine_id = planned_rest_value.machine_id

                WHERE extract_value.time BETWEEN pm.start_datetime AND pm.end_datetime
                AND extract_value.time BETWEEN planned_rest_value.start_datetime AND planned_rest_value.end_datetime
            )
        )AS aggregation_planned_rest_value
    )AS aggregation_planned_rest_value
)


-- 設備毎の生産数
-- 生産モデル毎の生産数
, output AS (
    SELECT
        DISTINCT
            machine_id,
    --         COALESCE(SUM(diff_value) OVER (PARTITION BY machine_id), 0) AS value_machine
            product_model,
    --         COALESCE(SUM(diff_value) OVER (PARTITION BY product_model), 0) AS value_product
            COALESCE(SUM(diff_value) OVER (PARTITION BY machine_id, product_model), 0) AS value
    FROM (
        SELECT
            DISTINCT
                machine_id,
                product_model,
                firstvalue,
                lastvalue,
                lastvalue - firstvalue AS diff_value
        FROM (
            SELECT
                machine_id,
                product_model,
                FIRST_VALUE(value) OVER(PARTITION BY machine_id, product_model, start_datetime ORDER BY time ASC) AS firstvalue,
                LAST_VALUE(value) OVER(PARTITION BY machine_id, product_model, start_datetime ORDER BY time RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS lastvalue
            FROM (
                SELECT
                    extract_value.machine_id,
                    pm.product_model,
                    time,
                    value,
                    -- 製品モデル切替情報をシフト時間内に収める。
                    CASE
                        WHEN pm.start_datetime BETWEEN machine_shift_datetime.start_datetime AND machine_shift_datetime.end_datetime THEN pm.start_datetime
                        WHEN pm.start_datetime < machine_shift_datetime.start_datetime THEN machine_shift_datetime.start_datetime
                        ELSE null
                    END AS start_datetime,
                    CASE
                        WHEN pm.end_datetime BETWEEN machine_shift_datetime.start_datetime AND machine_shift_datetime.end_datetime THEN pm.end_datetime
                        WHEN pm.end_datetime > machine_shift_datetime.end_datetime THEN machine_shift_datetime.end_datetime
                        ELSE null
                    END AS end_datetime
                FROM (
                    SELECT *
                    FROM records.t_record_count
                    WHERE is_valid is True
                    AND replace(data_type, ' ', '') ILIKE '%output%'
                ) AS extract_value

                -- 製品モデルの切り替わり時間情報
                LEFT JOIN (
                    SELECT * FROM product_model_status
                ) AS pm
                ON extract_value.machine_id = pm.machine_id

                -- シフト時間情報
                LEFT JOIN(
                    SELECT * FROM machine_shift_datetime
                ) AS machine_shift_datetime
                ON extract_value.machine_id = machine_shift_datetime.machine_id

                WHERE extract_value.is_valid is True
                AND extract_value.time BETWEEN pm.start_datetime AND pm.end_datetime
                AND extract_value.time BETWEEN machine_shift_datetime.start_datetime AND machine_shift_datetime.end_datetime
            )
        )
    )
)

-- 休憩時間の増加分を差し引いた生産数
    SELECT
        COALESCE(value.machine_id, rest_value.machine_id) AS machine_id,
        COALESCE(value.product_model, rest_value.product_model) AS product_model,
--         value.value AS increase,
--         rest_value.value AS rest_increase,
        value.value - rest_value.value AS value
    FROM output AS value
    LEFT JOIN (
        SELECT *
        FROM planned_rest_output
    ) AS rest_value
    ON value.machine_id = rest_value.machine_id
    AND value.product_model = rest_value.product_model

SELECT
    machine_id,
    COALESCE(name, value) as product_model
FROM (
    SELECT
        DISTINCT
            machine_id,
            last_value(value) OVER (PARTITION BY machine_id ORDER BY time ASC) AS value
    --         last(value, time) as value
    FROM records.t_record_status
    WHERE is_valid is TRUE
    AND machine_id in (1,6,7)
    AND replace(data_type, ' ', '') ILIKE '%productmodel%'
--     AND time <= $__timeTo()
) AS r_pm
LEFT JOIN (
    SELECT
        product_model_id,
        name
    FROM masters.m_product_model pm
    WHERE is_valid is true
) AS m_pm
ON r_pm.value::text = m_pm.product_model_id::text