"""
绩效计算页面 - 核心计算引擎
"""
import streamlit as st
import pandas as pd
import sys
import io
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.data_manager import (
    get_employees, get_regions, get_skills,
    get_employee_skills, get_mode_by_id,
    save_json, load_json,
    is_calculation_locked, lock_calculation
)


def calculate_ladder_bonus(score: float, ladder_rules: list) -> float:
    """
    计算阶梯奖金
    按区间累计计算，在区间内按比例
    """
    if not ladder_rules:
        return 0

    total_bonus = 0

    for rule in ladder_rules:
        min_val = rule.get("min", 0)
        max_val = rule.get("max", 0)
        bonus = rule.get("bonus", 0)

        if score <= min_val:
            break
        elif score >= max_val:
            total_bonus += bonus
        else:
            if max_val > min_val:
                ratio = (score - min_val) / (max_val - min_val)
                total_bonus += bonus * ratio
            break

    return round(total_bonus, 2)


def calculate_employee_salary(emp_id: str, emp_name: str, scores: dict, mid_detail: dict,
                               regions: list, skills: list, emp_skills: list) -> dict:
    """
    计算单个员工的绩效工资

    返回:
    {
        "employee_id": ...,
        "employee_name": ...,
        "regions": {
            "region_001": {
                "score": 绩效分,
                "is_on_duty": 是否在岗,
                "skill_salary": 技能工资,
                "skill_details": [{"name": ..., "on_duty": ..., "salary": ...}],
                "ladder_bonus": 阶梯奖金,
                "total": 小计
            },
            ...
        },
        "mid_detail": {"drawing": ..., "digital": ...},
        "total_salary": 总工资
    }
    """
    result = {
        "employee_id": emp_id,
        "employee_name": emp_name,
        "regions": {},
        "mid_detail": mid_detail or {"drawing": 0, "digital": 0},
        "total_salary": 0
    }

    # 获取该员工的技能关联
    my_skills = [es for es in emp_skills if es["employee_id"] == emp_id]
    my_skill_ids = [es["skill_id"] for es in my_skills]

    # 按区域计算
    for region in regions:
        region_id = region["id"]
        score = scores.get(region_id, 0)
        threshold = region.get("threshold", 30000)
        ladder_rules = region.get("ladder_rules", [])

        # 判断是否在岗
        is_on_duty = score >= threshold

        # 计算技能工资（记录明细）
        skill_salary = 0
        skill_details = []
        region_skills = [s for s in skills if s.get("region_id") == region_id]

        for skill in region_skills:
            if skill["id"] in my_skill_ids:
                es = next((e for e in my_skills if e["skill_id"] == skill["id"]), None)
                if es and es.get("passed_exam", False):
                    if is_on_duty:
                        if es.get("use_system_price", True):
                            salary = skill.get("salary_on_duty", 200)
                        else:
                            salary = es.get("custom_price_on_duty") or skill.get("salary_on_duty", 200)
                    else:
                        salary = skill.get("salary_off_duty", 100)

                    skill_salary += salary
                    skill_details.append({
                        "name": skill["name"],
                        "on_duty": is_on_duty,
                        "salary": salary
                    })

        # 计算阶梯奖金
        ladder_bonus = calculate_ladder_bonus(score, ladder_rules)

        # 区域小计
        region_total = skill_salary + ladder_bonus

        result["regions"][region_id] = {
            "name": region["name"],
            "score": score,
            "is_on_duty": is_on_duty,
            "skill_salary": skill_salary,
            "skill_details": skill_details,
            "ladder_bonus": ladder_bonus,
            "total": region_total
        }

        result["total_salary"] += region_total

    result["total_salary"] = round(result["total_salary"], 2)
    return result


def render():
    st.title("绩效计算")
    st.markdown("---")

    # 获取数据
    perf_data = load_json("performance.json")
    records = perf_data.get("records", [])

    if not records:
        st.warning("暂无绩效数据，请先导入绩效")
        return

    # 获取可选期间（兼容旧数据的month字段和新数据的period字段）
    periods = set()
    for r in records:
        if r.get("period"):
            periods.add(r["period"])
        elif r.get("month"):
            periods.add(r["month"])
    periods = sorted(periods, reverse=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        selected_period = st.selectbox("选择计算期间", options=periods)

    # 获取该期间数据（兼容period和month字段）
    period_records = [r for r in records if r.get("period") == selected_period or r.get("month") == selected_period]
    st.info(f"该期间共 {len(period_records)} 条绩效记录")

    # 保存名称输入框
    save_name = st.text_input(
        "保存名称",
        value=selected_period,
        help="计算结果的保存名称，可自定义（如：2024-12-方案一）"
    )

    # 检查是否已锁定
    is_locked = is_calculation_locked(save_name)
    if is_locked:
        st.warning(f"「{save_name}」已锁定，无法重新计算。如需修改请先在【历史查询】页面解锁。")

    st.markdown("---")

    # 计算按钮
    if st.button("开始计算", type="primary", disabled=is_locked):
        with st.spinner("正在计算..."):
            results = do_calculate(period_records, save_name)

        if results:
            # 保存结果到 session_state（避免 rerun 后数据丢失）
            st.session_state["calc_results"] = results
            st.session_state["calc_period"] = save_name

            st.success(f"计算完成！共 {len(results)} 人，保存为：{save_name}")

            # 保存结果到文件
            save_results(results, save_name)

    # 如果有已计算的结果，显示它
    if "calc_results" in st.session_state and st.session_state.get("calc_period") == save_name:
        results = st.session_state["calc_results"]
        display_results_v3(results, save_name)

        # 锁定按钮
        st.markdown("---")
        st.subheader("锁定确认")
        st.info("锁定后该期间数据将不可被覆盖，确保计算结果安全。")

        if st.button("锁定本期", type="secondary"):
            if lock_calculation(save_name):
                st.success(f"已锁定「{save_name}」，数据已成为静态快照。")
                # 清除 session_state
                if "calc_results" in st.session_state:
                    del st.session_state["calc_results"]
                st.rerun()
            else:
                st.error("锁定失败，请稍后重试")


def do_calculate(period_records: list, period: str) -> list:
    """执行计算"""
    regions = get_regions()
    skills = get_skills()
    emp_skills = get_employee_skills()

    results = []

    for record in period_records:
        emp_id = record["employee_id"]
        emp_name = record["employee_name"]
        scores = record.get("scores", {})
        mid_detail = record.get("mid_detail", {"drawing": 0, "digital": 0})

        result = calculate_employee_salary(
            emp_id, emp_name, scores, mid_detail,
            regions, skills, emp_skills
        )
        result["period"] = period
        results.append(result)

    # 按总工资排序
    results.sort(key=lambda x: x["total_salary"], reverse=True)

    return results


def display_region_detail(region: dict, rd: dict, result: dict):
    """显示单个区域的明细 - 紧凑横向布局"""
    region_id = region["id"]

    score = rd.get("score", 0)
    skill_salary = rd.get("skill_salary", 0)
    ladder_bonus = rd.get("ladder_bonus", 0)
    skill_details = rd.get("skill_details", [])

    # 使用小号字体的样式
    st.markdown('<style>.small-text { font-size: 0.85em; }</style>', unsafe_allow_html=True)

    # 技能工资 - 横向排列
    st.markdown('<p class="small-text"><b>【技能工资】</b></p>', unsafe_allow_html=True)
    if skill_details:
        # 构建横向显示：A:200 + B:100 = 300元
        parts = [f"{sd['name']}:{sd['salary']:.0f}" for sd in skill_details]
        skill_line = " + ".join(parts) + f" = **{skill_salary:.0f}元**"
        st.markdown(f'<p class="small-text">{skill_line}</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="small-text">无技能 = 0元</p>', unsafe_allow_html=True)

    # 绩效工资 - 一行显示
    st.markdown('<p class="small-text"><b>【绩效工资】</b></p>', unsafe_allow_html=True)
    if region_id == "region_002":
        # 印中特殊：显示图纸+数码
        mid_detail = result.get("mid_detail", {})
        drawing = mid_detail.get("drawing", 0)
        digital = mid_detail.get("digital", 0)
        perf_line = f"图纸:{drawing:,.0f}分 + 数码:{digital:,.0f}分 = {score:,.0f}分 → 阶梯奖金:**{ladder_bonus:.0f}元**"
    else:
        perf_line = f"绩效分:{score:,.0f}分 → 阶梯奖金:**{ladder_bonus:.0f}元**"
    st.markdown(f'<p class="small-text">{perf_line}</p>', unsafe_allow_html=True)


@st.dialog("绩效明细", width="small")
def show_detail_dialog():
    """显示员工指定区域的工资明细弹窗 - 紧凑版"""
    result = st.session_state.get("dialog_result", {})
    clicked_region = st.session_state.get("dialog_region")
    regions = get_regions()

    emp_name = result.get("employee_name", "")
    region = next((r for r in regions if r["id"] == clicked_region), None)

    if region:
        rd = result.get("regions", {}).get(clicked_region, {})
        region_total = rd.get("total", 0)

        st.markdown(f"**{emp_name} - {region['name']}**")
        display_region_detail(region, rd, result)
        st.markdown("---")
        st.markdown(f"**合计：¥{region_total:,.2f}**")


@st.dialog("总金额明细", width="small")
def show_total_dialog():
    """显示员工总金额构成弹窗 - 紧凑版"""
    result = st.session_state.get("dialog_result", {})
    regions = get_regions()

    emp_name = result.get("employee_name", "")
    total_salary = result.get("total_salary", 0)

    st.markdown(f"**{emp_name} - 总金额构成**")

    # 构建横向显示，只显示金额>0的区域
    parts = []
    for region in regions:
        rd = result.get("regions", {}).get(region["id"], {})
        amount = rd.get("total", 0)
        if amount > 0:
            parts.append(f"{region['name']}:{amount:.0f}")

    if parts:
        line = " + ".join(parts) + f" = **{total_salary:.0f}元**"
        st.markdown(f'<p style="font-size:0.9em;">{line}</p>', unsafe_allow_html=True)
    else:
        st.markdown("无数据")

    st.markdown("---")
    st.markdown(f"**总计：¥{total_salary:,.2f}**")


def display_results_v3(results: list, period: str):
    """显示计算结果 - 表格样式，选择行后显示明细"""
    regions = get_regions()

    st.subheader("计算结果")

    # 汇总统计
    col1, col2, col3 = st.columns(3)
    total_all = sum(r["total_salary"] for r in results)
    with col1:
        st.metric("总人数", len(results))
    with col2:
        st.metric("工资总额", f"¥{total_all:,.2f}")
    with col3:
        avg = total_all / len(results) if results else 0
        st.metric("人均工资", f"¥{avg:,.2f}")

    st.markdown("---")

    # 弹窗宽度样式
    st.markdown("""
    <style>
    /* 扩大弹窗宽度 */
    div[data-testid="stModal"] > div {
        max-width: 90vw !important;
        width: 90vw !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 构建表格数据
    table_data = []
    for r in results:
        row = {
            "期间": period,
            "员工ID": r["employee_id"],
            "姓名": r["employee_name"],
        }

        for region in regions:
            region_id = region["id"]
            region_name = region["name"]
            if region_id in r.get("regions", {}):
                rd = r["regions"][region_id]
                row[f"{region_name}绩效"] = round(rd.get("score", 0))
                row[f"{region_name}金额"] = round(rd.get("total", 0))
            else:
                row[f"{region_name}绩效"] = 0
                row[f"{region_name}金额"] = 0

        row["总金额"] = round(r["total_salary"])
        table_data.append(row)

    df = pd.DataFrame(table_data)

    # 使用 st.dataframe 的行选择功能
    st.markdown("**选择一行查看明细：**")
    selection = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    # 处理行选择事件
    if selection and selection.selection and selection.selection.rows:
        row_idx = selection.selection.rows[0]
        selected_result = results[row_idx]
        emp_name = selected_result.get("employee_name", "")

        st.markdown("---")
        st.markdown(f"### 📋 {emp_name} 的工资明细")

        # 显示区域选择和明细
        region_options = ["总金额构成"] + [r["name"] for r in regions]
        selected_region_name = st.selectbox("查看区域", options=region_options, key="calc_region_select")

        if selected_region_name == "总金额构成":
            # 显示总金额构成
            total_salary = selected_result.get("total_salary", 0)
            parts = []
            for region in regions:
                rd = selected_result.get("regions", {}).get(region["id"], {})
                amount = rd.get("total", 0)
                if amount > 0:
                    parts.append(f"{region['name']}:{amount:.0f}")
            if parts:
                line = " + ".join(parts) + f" = **{total_salary:.0f}元**"
                st.markdown(line)
            st.markdown(f"**总计：¥{total_salary:,.2f}**")
        else:
            # 显示指定区域的明细
            region = next((r for r in regions if r["name"] == selected_region_name), None)
            if region:
                rd = selected_result.get("regions", {}).get(region["id"], {})
                region_total = rd.get("total", 0)
                display_region_detail(region, rd, selected_result)
                st.markdown("---")
                st.markdown(f"**{selected_region_name}合计：¥{region_total:,.2f}**")

    # 导出Excel
    st.markdown("---")
    st.subheader("导出结果")

    export_df = prepare_export_data(results, regions)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, sheet_name=f'{period}绩效工资', index=False)
    buffer.seek(0)

    st.download_button(
        label="下载Excel",
        data=buffer,
        file_name=f"绩效工资_{period}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def prepare_export_data(results: list, regions: list) -> pd.DataFrame:
    """准备导出数据"""
    export_data = []

    for r in results:
        row = {
            "期间": r.get("period", ""),
            "员工ID": r["employee_id"],
            "姓名": r["employee_name"],
        }

        for region in regions:
            region_id = region["id"]
            region_name = region["name"]
            if region_id in r["regions"]:
                rd = r["regions"][region_id]
                row[f"{region_name}_绩效分"] = rd["score"]
                row[f"{region_name}_在岗"] = "是" if rd["is_on_duty"] else "否"
                row[f"{region_name}_技能工资"] = rd["skill_salary"]
                row[f"{region_name}_阶梯奖金"] = rd["ladder_bonus"]
                row[f"{region_name}_小计"] = rd["total"]

                # 印中特殊处理
                if region_id == "region_002":
                    mid_detail = r.get("mid_detail", {})
                    row["印中_图纸印中"] = mid_detail.get("drawing", 0)
                    row["印中_数码印中"] = mid_detail.get("digital", 0)

        row["总工资"] = r["total_salary"]
        export_data.append(row)

    return pd.DataFrame(export_data)


def save_results(results: list, period: str):
    """保存计算结果"""
    history_data = load_json("calculation_history.json")
    if not history_data:
        history_data = {"calculations": []}

    calculations = history_data.get("calculations", [])

    # 移除该期间已有记录
    calculations = [c for c in calculations if c.get("month") != period and c.get("period") != period]

    # 添加新记录
    calculations.append({
        "period": period,
        "calculated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "employee_count": len(results),
        "total_salary": sum(r["total_salary"] for r in results),
        "results": results
    })

    history_data["calculations"] = calculations
    save_json("calculation_history.json", history_data, backup=False)
