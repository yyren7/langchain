--使用するタイムゾーンを明示しないとPostgreSQL上で問題なくてもgrafanaで表示がおかしくなる場合あるのでここは絶対に必要
SET TIMEZONE='UTC';

--定数を定義するWITH句
WITH constant_definition AS(
	SELECT
		$_shift_period ::double precision AS shift_period, --1シフトの時間を入力(単位：時間)
		'MNC-832' AS machine_no, --MachineNoを入力
		(SELECT shift_work FROM shift_info()) AS shift_work, --2シフト制 or 3シフト制を定義する
		timestamp $__timeFrom() AT TIME ZONE 'UTC' AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AS timefrom, --表示対象期間の最初の時刻(現地時間で条件分岐するために一時的にタイムゾーンを変更)
		timestamp $__timeTo() AT TIME ZONE 'UTC' AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AS timeto --表示対象期間の最後の時刻(現地時間で条件分岐するために一時的にタイムゾーンを変更)
),

--検索対象の装置を絞り込むWITH句
equipment_extract AS(
	SELECT equipment_id, site, factory, model, line, assy, process, equipment, machine_no
	FROM m_equipment
	WHERE machine_no IN (SELECT machine_no FROM constant_definition)
),

--検索対象の装置が属するラインの装置全てを抽出するWITH句
line_extract AS(
	SELECT equipment_id, site, factory, model, line, assy, process, equipment, m_equipment.machine_no
	FROM m_equipment
	WHERE site IN (SELECT site FROM equipment_extract)
		AND factory IN (SELECT factory FROM equipment_extract)
		AND model IN (SELECT model FROM equipment_extract)
		AND line IN (SELECT line FROM equipment_extract)
),

--Grafanaで指定した時間から起点とする時間をシフト開始時間に分岐するためのWITH句
shift_calc AS(
	SELECT
		--3シフト制の場合
		CASE WHEN (SELECT shift_work FROM constant_definition) = 3 THEN
			--1シフトor任意の期間を表示
			CASE WHEN '$_display_term' = '1shift' THEN
				--昼勤
				CASE WHEN (SELECT timeto FROM constant_definition) BETWEEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT day_shift_start FROM public.shift_info())) AND (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT day_shift_end FROM public.shift_info()) - INTERVAL '1 second')
					THEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT day_shift_start FROM public.shift_info())) AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC'
				--準夜勤
				WHEN (SELECT timeto FROM constant_definition) BETWEEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT evening_shift_start FROM public.shift_info())) AND (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT evening_shift_end FROM public.shift_info()) - INTERVAL '1 second')
					THEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT evening_shift_start FROM public.shift_info())) AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC'
				--夜勤(日付変わる前)
				WHEN (SELECT timeto FROM constant_definition) BETWEEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT night_shift_start FROM public.shift_info())) AND (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + interval '1 day' + time '00:00:00' - INTERVAL '1 second')
					THEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT night_shift_start FROM public.shift_info())) AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC'
				--夜勤(日付変わった後)
				WHEN (SELECT timeto FROM constant_definition) BETWEEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + time '00:00:00') AND (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT night_shift_end FROM public.shift_info()) - INTERVAL '1 second')
					THEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) - interval '1 day' + (SELECT night_shift_start FROM public.shift_info())) AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC'
				END
			ELSE timestamp $__timeFrom() --任意のfromを表示する
			END

		--2シフト制の場合
		ELSE
			--1シフトor任意の期間を表示
			CASE WHEN '$_display_term' = '1shift' THEN
				--昼勤
				CASE WHEN (SELECT timeto FROM constant_definition) BETWEEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT day_shift_start FROM public.shift_info())) AND (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT day_shift_end FROM public.shift_info()) - INTERVAL '1 second')
					THEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT day_shift_start FROM public.shift_info())) AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC'
				--夜勤(日付変わる前)
				WHEN (SELECT timeto FROM constant_definition) BETWEEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT night_shift_start FROM public.shift_info())) AND (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + interval '1 day' + time '00:00:00' - INTERVAL '1 second')
					THEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT night_shift_start FROM public.shift_info())) AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC'
				--夜勤(日付変わった後)
				WHEN (SELECT timeto FROM constant_definition) BETWEEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + time '00:00:00') AND (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT night_shift_end FROM public.shift_info()) - INTERVAL '1 second')
					THEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) - interval '1 day' + (SELECT night_shift_start FROM public.shift_info())) AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC'
				END
			ELSE timestamp $__timeFrom() --任意のfromを表示する
			END
		END AS shift_start,

		--3シフト制の場合
		CASE WHEN (SELECT shift_work FROM constant_definition) = 3 THEN
			--1シフトor任意の期間を表示
			CASE WHEN '$_display_term' = '1shift' THEN
				--昼勤
				CASE WHEN (SELECT timeto FROM constant_definition) BETWEEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT day_shift_start FROM public.shift_info())) AND (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT day_shift_end FROM public.shift_info()) - INTERVAL '1 second')
					THEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT day_shift_end FROM public.shift_info()) - INTERVAL '1 second') AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC'
				--準夜勤
				WHEN (SELECT timeto FROM constant_definition) BETWEEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT evening_shift_start FROM public.shift_info())) AND (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT evening_shift_end FROM public.shift_info()) - INTERVAL '1 second')
					THEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT evening_shift_end FROM public.shift_info()) - INTERVAL '1 second') AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC'
				--夜勤(日付変わる前)
				WHEN (SELECT timeto FROM constant_definition) BETWEEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT night_shift_start FROM public.shift_info())) AND (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + interval '1 day' + time '00:00:00' - INTERVAL '1 second')
					THEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + interval '1 day' + (SELECT night_shift_end FROM public.shift_info()) - INTERVAL '1 second') AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC'
				--夜勤(日付変わった後)
				WHEN (SELECT timeto FROM constant_definition) BETWEEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + time '00:00:00') AND (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT night_shift_end FROM public.shift_info()) - INTERVAL '1 second')
					THEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT night_shift_end FROM public.shift_info()) - INTERVAL '1 second') AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC'
				END
			--任意のtoを表示する
			ELSE (SELECT timeto FROM constant_definition) AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC'
			END

		--2シフト制の場合
		ELSE
			--1シフトor任意の期間を表示
			CASE WHEN '$_display_term' = '1shift' THEN
				--昼勤
				CASE WHEN (SELECT timeto FROM constant_definition) BETWEEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT day_shift_start FROM public.shift_info())) AND (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT day_shift_end FROM public.shift_info()) - INTERVAL '1 second')
					THEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT day_shift_end FROM public.shift_info()) - INTERVAL '1 second') AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC'
				--夜勤(日付変わる前)
				WHEN (SELECT timeto FROM constant_definition) BETWEEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT night_shift_start FROM public.shift_info())) AND (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + interval '1 day' + time '00:00:00' - INTERVAL '1 second')
					THEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + interval '1 day' + (SELECT night_shift_end FROM public.shift_info()) - INTERVAL '1 second') AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC'
				--夜勤(日付変わった後)
				WHEN (SELECT timeto FROM constant_definition) BETWEEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + time '00:00:00') AND (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT night_shift_end FROM public.shift_info()) - INTERVAL '1 second')
					THEN (DATE_TRUNC('day', (SELECT timeto FROM constant_definition)) + (SELECT night_shift_end FROM public.shift_info()) - INTERVAL '1 second') AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC'
				END
			--任意のtoを表示する
			ELSE (SELECT timeto FROM constant_definition) AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC'
			END
		END AS shift_end
),

--部品ごとに生産時間を抽出するWITH句
production_time_per_parts AS(
	SELECT
		process_at AS production_start_time --検索範囲の最初の時間
	FROM(
		SELECT process_at
		FROM public.t_record_progress
		WHERE process_at <= (SELECT timeto AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' FROM constant_definition) --最新データを1つ取得する
			AND	equipment_id = (SELECT equipment_id FROM equipment_extract)
			AND data_type = 'productno'
		ORDER BY process_at DESC
		LIMIT 1
	)AS production_time_per_parts
),

--シフト開始時刻と部品の生産開始時刻を比較し起点とする時刻を演算するためのWITH句
calc_timefrom AS(
	SELECT
		CASE WHEN shift_start >= production_start_time THEN shift_start --シフト開始以降に生産部品が切り替わっていなければシフト開始を起点とする
		WHEN production_start_time > shift_start THEN production_start_time --シフト開始以降に生産部品が切り替わっていればその時刻を起点とする
		ELSE shift_start
		END AS timefrom
	FROM shift_calc, production_time_per_parts
),

--timefromからの経過時間を表示するためのWITH句
elapsed_time_from_timefrom AS(
	SELECT EXTRACT(epoch FROM (SELECT timeto FROM constant_definition) AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' - timefrom) AS elapsed_time
	FROM(
		SELECT timefrom
		FROM calc_timefrom
	)AS start_time
),

--manualworkの値の前処理(設定画面に登録されていない場合は0として扱う)
preprocessing_manualwork AS(
	SELECT equipment_id, COALESCE(manualwork, 0) AS manualwork
	FROM(
		SELECT equipment_id, text::integer AS manualwork
		FROM public.m_address
		WHERE data_type = 'manualwork'
			AND equipment_id = (SELECT equipment_id FROM equipment_extract)
	)AS preprocessing_manualwork
),

--standardcycleの値の前処理(登録されていない場合は0として扱う)
preprocessing_st_cycle AS(
	SELECT
		CASE WHEN search_st_cycle_manual.equipment_id IS NULL THEN search_st_cycle_t_record_status.equipment_id
		WHEN search_st_cycle_t_record_status.equipment_id IS NULL THEN search_st_cycle_manual.equipment_id
		ELSE search_st_cycle_manual.equipment_id
		END AS equipment_id, --MANUALに入力した値を優先的に使う

		CASE WHEN shift_st_cycle IS NULL AND manual_st_cycle IS NOT NULL THEN manual_st_cycle
		WHEN manual_st_cycle IS NULL AND shift_st_cycle IS NOT NULL THEN shift_st_cycle
		ELSE COALESCE(manual_st_cycle, 0)
		END AS st_cycle --MANUALに入力した値を優先的に使う

	FROM(
		SELECT DISTINCT
			equipment_id,
			LAST_VALUE(value) OVER(ORDER BY process_at RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS shift_st_cycle
		FROM public.t_record_status
		WHERE process_at BETWEEN (SELECT timefrom FROM calc_timefrom) AND (SELECT timeto AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' FROM constant_definition)
			AND data_type = 'standardcycle'
			AND equipment_id = (SELECT equipment_id FROM equipment_extract)
	)AS search_st_cycle_t_record_status
	FULL JOIN( --片方しか存在しない場合を考慮しFULL JOIN
		SELECT equipment_id, text::integer AS manual_st_cycle
		FROM public.m_address
		WHERE data_type = 'standardcycle'
			AND device = 'MANUAL'
			AND equipment_id = (SELECT equipment_id FROM equipment_extract)
	)AS search_st_cycle_manual
	ON search_st_cycle_t_record_status.equipment_id = search_st_cycle_manual.equipment_id
),

--日毎の生産目標数を抽出する
extract_product_plan AS(
	SELECT equipment_id, shift_start_time,
		COALESCE(SUM(value), 0) AS product_plan_value --1シフト目標値に換算するため数値を1/2にする
		-- COALESCE(SUM(value / 2), 0) AS product_plan_value --1シフト目標値に換算するため数値を1/2にする
	FROM(
		SELECT
			equipment_id,
			--現在時刻が昼/夜シフトのどちらに該当するかによってシフト開始時刻を切り替える
			CASE WHEN day_shift_start = (SELECT shift_start FROM shift_calc) THEN day_shift_start -- 1shiftを選択し、シフト開始時間と完全一致する場合
			WHEN night_shift_start = (SELECT shift_start FROM shift_calc) THEN night_shift_start -- 1shiftを選択し、シフト開始時間と完全一致する場合
			WHEN day_shift_start > (SELECT shift_start FROM shift_calc) THEN day_shift_start -- Anyを選択し、昼シフト開始時間よりも後の場合
			WHEN night_shift_start > (SELECT shift_start FROM shift_calc) THEN night_shift_start -- Anyを選択し、夜シフト開始時間よりも後の場合
			ELSE NULL
			END AS shift_start_time,
			value
		FROM(
			SELECT
				equipment_id,
				(date + (SELECT day_shift_start FROM public.shift_info())) AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AS day_shift_start,
				(date + (SELECT night_shift_start FROM public.shift_info())) AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AS night_shift_start,
				value
			FROM manual.t_product_plan
			WHERE equipment_id IN (SELECT equipment_id FROM line_extract)
				AND data_type = 'productplan'
				AND isvalid IS True
		)AS preprocessing_product_plan
	)AS preprocessing_product_plan
	WHERE shift_start_time IS NOT NULL
	GROUP BY equipment_id, shift_start_time
),

--outputtargetの値の前処理(登録されていない場合は0として扱う)
preprocessing_output_target AS(
	SELECT

		--equipment_extractとline_extractが一致していない場合はequipment_extractに置き換える
		CASE WHEN equipment_id = (SELECT equipment_id FROM equipment_extract) THEN equipment_id
		WHEN equipment_id != (SELECT equipment_id FROM equipment_extract) THEN (SELECT equipment_id FROM equipment_extract)
		ELSE equipment_id
		END AS equipment_id,

		output_target

	FROM(
		SELECT

			--優先順位 product_plan → manual value → t_record_status
			CASE WHEN search_output_target_product_plan.equipment_id IS NOT NULL THEN search_output_target_product_plan.equipment_id
			-- WHEN search_output_target_manual.equipment_id IS NOT NULL THEN search_output_target_manual.equipment_id
			-- WHEN search_output_target_t_record_status.equipment_id IS NOT NULL THEN search_output_target_t_record_status.equipment_id
			ELSE search_output_target_product_plan.equipment_id
			END AS equipment_id,

			CASE WHEN product_plan_output_target IS NOT NULL THEN product_plan_output_target
			-- WHEN manual_output_target IS NOT NULL THEN manual_output_target
			-- WHEN shift_output_target IS NOT NULL THEN shift_output_target
			ELSE COALESCE(product_plan_output_target, 0)
			END AS output_target

		FROM(
			SELECT DISTINCT
				equipment_id,
				LAST_VALUE(value) OVER(ORDER BY process_at RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS shift_output_target
			FROM t_record_status
			WHERE process_at BETWEEN (SELECT timefrom FROM calc_timefrom) AND (SELECT timeto AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' FROM constant_definition)
				AND data_type = 'outputtarget'
				AND equipment_id IN (SELECT equipment_id FROM line_extract)
		)AS search_output_target_t_record_status
		-- FULL JOIN( --片方しか存在しない場合を考慮しFULL JOIN
		-- 	SELECT equipment_id, text::integer AS manual_output_target
		-- 	FROM m_address
		-- 	WHERE data_type = 'outputtarget'
		-- 		AND device = 'MANUAL'
		-- 		AND equipment_id IN (SELECT equipment_id FROM line_extract)
		-- )AS search_output_target_manual
		-- ON search_output_target_t_record_status.equipment_id = search_output_target_manual.equipment_id
		FULL JOIN(
			SELECT equipment_id,
				CASE WHEN '$_display_term' = '1shift' THEN SUM(product_plan_value) / (SELECT shift_work FROM constant_definition)
				ELSE SUM(product_plan_value)
				END AS product_plan_output_target
			FROM extract_product_plan
			WHERE shift_start_time BETWEEN (SELECT timefrom FROM calc_timefrom) AND (SELECT timeto AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' FROM constant_definition)
			GROUP BY equipment_id
		)AS search_output_target_product_plan
		-- ON search_output_target_manual.equipment_id = search_output_target_product_plan.equipment_id
		ON search_output_target_t_record_status.equipment_id = search_output_target_product_plan.equipment_id
	)AS preprocessing_output_target
),

--不良数を抽出する
preprocessing_defect_product_count AS(
	SELECT equipment_id, value::integer
	FROM manual.t_manual
	WHERE (date + (SELECT day_shift_start FROM public.shift_info())) AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' BETWEEN (SELECT timefrom FROM calc_timefrom) AND (SELECT timeto AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' FROM constant_definition)
		AND equipment_id IN (SELECT equipment_id FROM line_extract)
		AND data_type = 'NG QUANTITY'
		AND isvalid IS True
		AND value > 0
),

--計画停止時間を抽出し、前処理を実施
preprocessing_planned_downtime AS(
	SELECT
		--equipment_extractとline_extractが一致していない場合はequipment_extractに置き換える
		CASE WHEN equipment_id = (SELECT equipment_id FROM equipment_extract) THEN equipment_id
		WHEN equipment_id != (SELECT equipment_id FROM equipment_extract) THEN (SELECT equipment_id FROM equipment_extract)
		ELSE equipment_id
		END AS equipment_id,

		--シフト開始時刻よりも前の場合はシフト開始時刻に置き換える
		CASE WHEN start_time < (SELECT timefrom FROM calc_timefrom)
			THEN (SELECT timefrom FROM calc_timefrom)
		--シフト開始時刻よりも後の場合はそのまま
		WHEN start_time > (SELECT timefrom FROM calc_timefrom)
			THEN start_time
		ELSE start_time
		END AS start_time,

		--現時刻よりも後の場合は現時刻に置き換える
		CASE WHEN end_time > (SELECT timeto AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' FROM constant_definition)
			THEN (SELECT timeto AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' FROM constant_definition)
		--現時刻よりも前の場合はそのまま
		WHEN end_time < (SELECT timeto AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' FROM constant_definition)
			THEN end_time
		--nullの場合、start_timeに置き換えることで差分を計算すると0になる
		WHEN end_time IS NULL
			THEN start_time
		ELSE end_time
		END AS end_time

	FROM manual.t_planned_downtime_range
	WHERE (start_time BETWEEN (SELECT timefrom FROM calc_timefrom) AND (SELECT timeto AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' FROM constant_definition)
			OR end_time BETWEEN (SELECT timefrom FROM calc_timefrom) AND (SELECT shift_end FROM shift_calc))
		--start_time, end_timeどちらかが、選択期間に含まれていれば計算対象とする
		AND equipment_id IN (SELECT equipment_id FROM line_extract)
		AND data_type = 'planned_downtime'
		AND isvalid IS True
		AND start_time < end_time --誤入力でend_timeよりもstart_timeに大きな時刻が入力されている場合を除外する
),

--計画停止中のplantimeの増加量を集計する(OEE計算時に減算する)
extract_planned_downtime AS(
	SELECT COALESCE(SUM(planned_downtime), 0) AS planned_downtime
	FROM(
		SELECT DISTINCT
			last_value_planned_downtime - first_value_planned_downtime AS planned_downtime
		FROM(
			SELECT
				extract_plantime.equipment_id, process_at, value,
				--計画停止期間中の最初と最後のplantimeを抽出する
				FIRST_VALUE(value) OVER(PARTITION BY start_time ORDER BY process_at ASC) AS first_value_planned_downtime,
				LAST_VALUE(value) OVER(PARTITION BY start_time ORDER BY process_at RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS last_value_planned_downtime
			FROM(
				SELECT
					equipment_id, process_at, value
				FROM public.t_record_status
				WHERE process_at BETWEEN (SELECT timefrom FROM calc_timefrom) AND (SELECT timeto AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' FROM constant_definition)
					AND t_record_status.equipment_id = (SELECT equipment_id FROM equipment_extract)
					AND data_type = 'plantime'
			)AS extract_plantime
			LEFT JOIN(
				SELECT equipment_id, start_time, end_time
				FROM preprocessing_planned_downtime
			)AS preprocessing_planned_downtime
			ON extract_plantime.equipment_id = preprocessing_planned_downtime.equipment_id
			WHERE process_at BETWEEN start_time AND end_time
		)AS aggregation_planned_downtime
	)AS aggregation_planned_downtime
)


SELECT

	machine_no,

	--文字数が多すぎる場合は一定数以上の文字を「..」に置き換える
	CASE WHEN LENGTH(parts) > 20 THEN LEFT(parts, 20) || '..'
	ELSE parts
	END AS parts,

	status,
	output,
	uph,

	--Qualityの値が100%を超えないようにする
	CASE WHEN yield > 1 THEN performance * availability * 1
	ELSE performance * availability * yield
	END AS OEE,

	--起点とする時刻を表示する(タイムゾーンの変換はGrafana側で対応)
	(SELECT timefrom FROM calc_timefrom) AS start_time

FROM(

	SELECT

		machine_no,
		parts_info.text AS parts,
		equipment_status.text AS status,

		-- --目標の達成率に応じて背景色を切り替えるための文字列を結合
		-- CASE WHEN (output.value - output.min_value)::double precision / NULLIF((target_value.target_value::double precision / 3600 * (SELECT elapsed_time FROM elapsed_time_from_timefrom)), 0) >= 0.95
		-- 	THEN to_char(output.value - output.min_value, '999999') || '   /   ' || to_char(target_value.target_value::double precision / 3600 * (SELECT elapsed_time FROM elapsed_time_from_timefrom), '999999') || ' G'
		-- WHEN (output.value - output.min_value)::double precision / NULLIF((target_value.target_value::double precision / 3600 * (SELECT elapsed_time FROM elapsed_time_from_timefrom)), 0) >= 0.9
		-- 	THEN to_char(output.value - output.min_value, '999999') || '   /   ' || to_char(target_value.target_value::double precision / 3600 * (SELECT elapsed_time FROM elapsed_time_from_timefrom), '999999') || ' Y'
		-- WHEN (output.value - output.min_value)::double precision / NULLIF((target_value.target_value::double precision / 3600 * (SELECT elapsed_time FROM elapsed_time_from_timefrom)), 0) < 0.9
		-- 	THEN to_char(output.value - output.min_value, '999999') || '   /   ' || to_char(target_value.target_value::double precision / 3600 * (SELECT elapsed_time FROM elapsed_time_from_timefrom), '999999') || ' R'
		-- ELSE to_char(output.value - output.min_value, '999999') || '   /   ' || to_char(target_value.target_value::double precision / 3600 * (SELECT elapsed_time FROM elapsed_time_from_timefrom), '999999')
		-- END AS OUTPUT,
		CASE WHEN (output.value - output.min_value)::double precision / NULLIF(target_value.target_value ::double precision, 0) >= 0.95
			THEN to_char(output.value - output.min_value, '999999') || '   /   ' || to_char(target_value.target_value ::double precision, '999999') || ' G'
		WHEN (output.value - output.min_value)::double precision / NULLIF(target_value.target_value ::double precision, 0) >= 0.9
			THEN to_char(output.value - output.min_value, '999999') || '   /   ' || to_char(target_value.target_value ::double precision, '999999') || ' Y'
		WHEN (output.value - output.min_value)::double precision / NULLIF(target_value.target_value ::double precision, 0) < 0.9
			THEN to_char(output.value - output.min_value, '999999') || '   /   ' || to_char(target_value.target_value ::double precision, '999999') || ' R'
		ELSE to_char(output.value - output.min_value, '999999') || '   /   ' || to_char(target_value.target_value ::double precision, '999999')
		END AS OUTPUT,

		--目標の達成率に応じて背景色を切り替えるための文字列を結合
		-- CASE WHEN (output.value - output.uph_previous_value ::double precision) / NULLIF(target_value.target_value ::double precision, 0) >= 0.95
		-- 	THEN to_char(output.value - output.uph_previous_value, '999999') || '   /   ' || to_char(target_value.target_value, '999999') || ' G'
		-- WHEN (output.value - output.uph_previous_value ::double precision) / NULLIF(target_value.target_value ::double precision, 0) >= 0.9
		-- 	THEN to_char(output.value - output.uph_previous_value, '999999') || '   /   ' || to_char(target_value.target_value, '999999') || ' Y'
		-- WHEN (output.value - output.uph_previous_value ::double precision) / NULLIF(target_value.target_value ::double precision, 0) < 0.9
		-- 	THEN to_char(output.value - output.uph_previous_value, '999999') || '   /   ' || to_char(target_value.target_value, '999999') || ' R'
		-- ELSE to_char(output.value - output.uph_previous_value, '999999') || '   /   ' || to_char(target_value.target_value, '999999')
		-- END AS UPH,
		CASE WHEN (output.value - output.uph_previous_value ::double precision) / NULLIF(target_value.target_value_for_uph ::double precision, 0) >= 0.95
			THEN to_char(output.value - output.uph_previous_value, '999999') || '   /   ' || to_char(target_value.target_value_for_uph ::double precision, '999999') || ' G'
		WHEN (output.value - output.uph_previous_value ::double precision) / NULLIF(target_value.target_value_for_uph ::double precision, 0) >= 0.9
			THEN to_char(output.value - output.uph_previous_value, '999999') || '   /   ' || to_char(target_value.target_value_for_uph ::double precision, '999999') || ' Y'
		WHEN (output.value - output.uph_previous_value ::double precision) / NULLIF(target_value.target_value_for_uph ::double precision, 0) < 0.9
			THEN to_char(output.value - output.uph_previous_value, '999999') || '   /   ' || to_char(target_value.target_value_for_uph ::double precision, '999999') || ' R'
		ELSE to_char(output.value - output.uph_previous_value, '999999') || '   /   ' || to_char(target_value.target_value_for_uph ::double precision, '999999')
		END AS UPH,
		((output.value - output.min_value) - COALESCE(defect_product_count, 0)) ::double precision / NULLIF(((input.value - input.min_value)::double precision), 0) AS yield,
		((input.value - input.min_value)::double precision * (st_cycle + manualwork)::double precision) / (NULLIF((actualtime.value - actualtime.min_value + (manualwork * (output.value - output.min_value)))::double precision, 0)) AS performance,

		--シフト以降計画停止が続いている場合は0とする
		CASE WHEN plantime.value - plantime.min_value = (SELECT planned_downtime FROM extract_planned_downtime) THEN 0
		ELSE (actualtime.value - actualtime.min_value + (manualwork * (output.value - output.min_value)))::double precision / NULLIF((plantime.value - plantime.min_value) - (SELECT planned_downtime FROM extract_planned_downtime)::double precision, 0)
		END AS availability

	--設備情報をJOINで優先するテーブルとする
	FROM(
		SELECT equipment_id, site, factory, model, line, assy, process, equipment, machine_no
		FROM equipment_extract
	)AS equipment_info

	--outputのデータを抽出
	LEFT JOIN(
		SELECT
			equipment_id, process_at,
			FIRST_VALUE(value) OVER(ORDER BY process_at ASC) AS min_value, --選択期間の最初の値を取得
			FIRST_VALUE(value) OVER(ORDER BY process_at RANGE BETWEEN '1 HOUR' PRECEDING AND CURRENT ROW) AS uph_previous_value, --現在の行から1時間前までを検索対象とし、最初の値を取得
			value --選択期間の最新の値を取得
		FROM public.t_record_status
		WHERE process_at BETWEEN (SELECT timefrom FROM calc_timefrom) AND (SELECT timeto AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' FROM constant_definition)
			AND equipment_id = (SELECT equipment_id FROM equipment_extract)
			AND data_type = 'output'
		ORDER BY process_at DESC
		LIMIT 1
	)AS output
	ON equipment_info.equipment_id = output.equipment_id

	--inputのデータを抽出
	LEFT JOIN(
		SELECT
			equipment_id, process_at,
			FIRST_VALUE(value) OVER (ORDER BY process_at ASC) AS min_value,
			value --選択期間の最新の値を取得
		FROM public.t_record_status
		WHERE process_at BETWEEN (SELECT timefrom FROM calc_timefrom) AND (SELECT timeto AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' FROM constant_definition)
			AND equipment_id = (SELECT equipment_id FROM equipment_extract)
			AND data_type = 'input'
		ORDER BY process_at DESC
		LIMIT 1
	)AS input
	ON equipment_info.equipment_id = input.equipment_id

	--plantimeのデータを抽出
	LEFT JOIN(
		SELECT
			equipment_id, process_at,
			FIRST_VALUE(value) OVER (ORDER BY process_at ASC) AS min_value,
			value --選択期間の最新の値を取得
		FROM public.t_record_status
		WHERE process_at BETWEEN (SELECT timefrom FROM calc_timefrom) AND (SELECT timeto AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' FROM constant_definition)
			AND equipment_id = (SELECT equipment_id FROM equipment_extract)
			AND data_type = 'plantime'
		ORDER BY process_at DESC
		LIMIT 1
	)AS plantime
	ON equipment_info.equipment_id = plantime.equipment_id

	--actualtimeのデータを抽出
	LEFT JOIN(
		SELECT
			equipment_id, process_at,
			FIRST_VALUE(value) OVER (ORDER BY process_at ASC) AS min_value,
			value --選択期間の最新の値を取得
		FROM public.t_record_status
		WHERE process_at BETWEEN (SELECT timefrom FROM calc_timefrom) AND (SELECT timeto AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' FROM constant_definition)
			AND equipment_id = (SELECT equipment_id FROM equipment_extract)
			AND data_type = 'actualtime'
		ORDER BY process_at DESC
		LIMIT 1
	)AS actualtime
	ON equipment_info.equipment_id = actualtime.equipment_id

	--生産目標数を抽出
	LEFT JOIN(
		-- SELECT equipment_id, (output_target) / (SELECT shift_period FROM constant_definition) ::double precision AS target_value
		-- FROM preprocessing_output_target
		SELECT equipment_id,
            CASE WHEN '$_display_term' = '1shift' THEN (output_target) / (SELECT shift_period FROM constant_definition) / 3600 * (SELECT elapsed_time FROM elapsed_time_from_timefrom) ::double precision
            ELSE output_target::double precision
            END AS target_value,
			CASE WHEN (SELECT EXTRACT(EPOCH FROM (SELECT timeto AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' FROM constant_definition)) - (SELECT EXTRACT(EPOCH FROM(SELECT timefrom FROM calc_timefrom)))) / 3600 <= ((SELECT shift_period FROM constant_definition) * (SELECT shift_work FROM constant_definition)) THEN (output_target / ((SELECT shift_period FROM constant_definition) * (SELECT shift_work FROM constant_definition))) :: double precision
			ELSE ((output_target) / ((SELECT EXTRACT(EPOCH FROM (SELECT timeto AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' FROM constant_definition)) - (SELECT EXTRACT(EPOCH FROM(SELECT timefrom FROM calc_timefrom))) ) / 3600)) :: double precision
			END AS target_value_for_uph
		FROM preprocessing_output_target
	)AS target_value
	ON equipment_info.equipment_id = target_value.equipment_id

	--標準サイクルタイムを抽出
	LEFT JOIN(
		SELECT equipment_id, st_cycle
		FROM preprocessing_st_cycle
	)AS st_cycle
	ON equipment_info.equipment_id = st_cycle.equipment_id

	--手作業時間を抽出
	LEFT JOIN(
		SELECT equipment_id, manualwork
		FROM preprocessing_manualwork
	)AS manualwork
	ON equipment_info.equipment_id = manualwork.equipment_id

	--生産中の部品名を抽出
	LEFT JOIN(
		SELECT
			progress_info.equipment_id,
			address_info.text
		FROM(
			SELECT equipment_id, process_at, data_type, value, text
			FROM public.t_record_progress
			WHERE process_at BETWEEN (SELECT production_start_time FROM production_time_per_parts) AND (SELECT timeto AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' FROM constant_definition)
				AND equipment_id = (SELECT equipment_id FROM equipment_extract)
				AND data_type = 'productno'
				ORDER BY process_at DESC
				LIMIT 1
		)AS progress_info
		LEFT JOIN(
			SELECT equipment_id, data_type, value, text
			FROM public.m_address
			WHERE equipment_id = (SELECT equipment_id FROM equipment_extract)
				AND data_type = 'productno'
		)AS address_info
		ON progress_info.equipment_id = address_info.equipment_id
			AND progress_info.value = address_info.value
	)AS parts_info
	ON equipment_info.equipment_id = parts_info.equipment_id

	--現時刻の設備の稼働状況を抽出
	LEFT JOIN(
		SELECT equipment_id, text --green, yellow, redのいずれかを抽出
		FROM public.t_record_process
		WHERE process_at <= (SELECT timeto FROM constant_definition) AT TIME ZONE (SELECT time_zone FROM public.shift_info()) AT TIME ZONE 'UTC' --最新データを1つ取得する
			AND equipment_id = (SELECT equipment_id FROM equipment_extract)
			AND data_type = 'status'
		ORDER BY process_at DESC
		LIMIT 1
	)AS equipment_status
	ON equipment_info.equipment_id = equipment_status.equipment_id

	--選択期間内の不良数を抽出(合計値)
	LEFT JOIN(
		SELECT equipment_id, SUM(value) AS defect_product_count
		FROM preprocessing_defect_product_count
		GROUP BY equipment_id
	)AS defect_product_count
	ON equipment_info.equipment_id = defect_product_count.equipment_id

)AS calc_oee
LIMIT 1
;