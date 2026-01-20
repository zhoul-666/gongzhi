"""
绩效计算页面 - 核心计算引擎
"""
import streamlit as st
import pandas as pd
import sys
import io
from pathlib import Path
from datetime import datetime
from st_table_select_cell import st_table_select_cell

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.data_manager import (
    get_employees, get_regions, get_skills,
    get_employee_skills, get_mode_by_id,
    save_json, load_json,
    is_calculation_locked, lock_calculation,
    get_roles, get_role_by_id, get_employee_threshold,
    get_external_data, get_income_rules, get_bonus_pools
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


def get_employee_role_info(emp_id: str, employees: list) -> dict:
    """获取员工的角色信息"""
    emp = next((e for e in employees if e["id"] == emp_id), None)
    if not emp:
        return None

    role_id = emp.get("role_id")
    if not role_id:
        return None

    return get_role_by_id(role_id)


def calculate_employee_threshold(emp_id: str, region_id: str, base_threshold: float, employees: list) -> float:
    """
    计算员工在指定区域的个性化达标线
    优先级：员工自定义 > 角色倍率 > 区域默认值
    """
    emp = next((e for e in employees if e["id"] == emp_id), None)
    if not emp:
        return base_threshold

    # 检查员工是否有自定义达标线
    custom_settings = emp.get("custom_settings", {})
    if custom_settings.get("custom_threshold"):
        custom = custom_settings.get("thresholds", {}).get(region_id)
        if custom is not None:
            return custom

    # 检查角色倍率
    role_id = emp.get("role_id")
    if role_id:
        role = get_role_by_id(role_id)
        if role:
            multiplier = role.get("threshold_multiplier", 1.0)
            return base_threshold * multiplier

    return base_threshold


def calculate_employee_salary(emp_id: str, emp_name: str, scores: dict, mid_detail: dict,
                               regions: list, skills: list, emp_skills: list,
                               employees: list = None, external_data: dict = None) -> dict:
    """
    计算单个员工的绩效工资（支持角色达标线和多元收入）

    返回:
    {
        "employee_id": ...,
        "employee_name": ...,
        "role_name": ...,  # 新增：角色名称
        "regions": {
            "region_001": {
                "score": 绩效分,
                "threshold": 个性化达标线,  # 新增
                "is_on_duty": 是否在岗,
                "skill_salary": 技能工资,
                "skill_details": [{"name": ..., "on_duty": ..., "salary": ...}],
                "ladder_bonus": 阶梯奖金,
                "total": 小计
            },
            ...
        },
        "mid_detail": {"drawing": ..., "digital": ...},
        "extra_income": {...},  # 新增：额外收入明细
        "total_salary": 总工资
    }
    """
    employees = employees or get_employees()
    emp = next((e for e in employees if e["id"] == emp_id), None)

    # 获取角色信息
    role = None
    role_name = "未指定"
    income_types = ["skill_salary", "ladder_bonus"]  # 默认收入类型
    role_settings = {}

    if emp and emp.get("role_id"):
        role = get_role_by_id(emp["role_id"])
        if role:
            role_name = role.get("name", "未指定")
            income_types = role.get("income_types", income_types)
            role_settings = role.get("settings", {})

    result = {
        "employee_id": emp_id,
        "employee_name": emp_name,
        "role_name": role_name,
        "regions": {},
        "mid_detail": mid_detail or {"drawing": 0, "digital": 0},
        "extra_income": {},
        "total_salary": 0
    }

    # 获取该员工的技能关联
    my_skills = [es for es in emp_skills if es["employee_id"] == emp_id]
    my_skill_ids = [es["skill_id"] for es in my_skills]

    # 按区域计算
    for region in regions:
        region_id = region["id"]
        score = scores.get(region_id, 0)
        base_threshold = region.get("threshold", 30000)
        ladder_rules = region.get("ladder_rules", [])

        # 计算个性化达标线
        threshold = calculate_employee_threshold(emp_id, region_id, base_threshold, employees)

        # 判断是否在岗
        is_on_duty = score >= threshold

        # 计算技能工资（记录明细）
        skill_salary = 0
        skill_details = []

        if "skill_salary" in income_types:
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
        ladder_bonus = 0
        if "ladder_bonus" in income_types:
            ladder_bonus = calculate_ladder_bonus(score, ladder_rules)

        # 区域小计
        region_total = skill_salary + ladder_bonus

        result["regions"][region_id] = {
            "name": region["name"],
            "score": score,
            "threshold": threshold,
            "is_on_duty": is_on_duty,
            "skill_salary": skill_salary,
            "skill_details": skill_details,
            "ladder_bonus": ladder_bonus,
            "total": region_total
        }

        result["total_salary"] += region_total

    # 计算额外收入（基于角色配置）
    extra_income = {}

    # 开单奖励
    if "order_bonus" in income_types and external_data:
        order_count = external_data.get("order_count", 0)
        bonus_per_unit = role_settings.get("order_bonus_per_unit", 2)
        order_bonus = order_count * bonus_per_unit
        extra_income["order_bonus"] = {
            "name": "开单奖励",
            "count": order_count,
            "unit_price": bonus_per_unit,
            "amount": order_bonus
        }
        result["total_salary"] += order_bonus

    # 管理津贴
    if "management_allowance" in income_types:
        allowance = role_settings.get("management_allowance", 0)
        if allowance > 0:
            extra_income["management_allowance"] = {
                "name": "管理津贴",
                "amount": allowance
            }
            result["total_salary"] += allowance

    # 业绩提成
    if "revenue_commission" in income_types and external_data:
        revenue = external_data.get("store_revenue", 0)
        rate = role_settings.get("commission_rate", 0.01)
        commission = revenue * rate
        extra_income["revenue_commission"] = {
            "name": "业绩提成",
            "revenue": revenue,
            "rate": rate,
            "amount": commission
        }
        result["total_salary"] += commission

    result["extra_income"] = extra_income
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


def calculate_ranking_bonus(results: list, employees: list) -> list:
    """
    计算排名奖金
    根据奖金池配置，按排名分配奖金
    """
    bonus_pools = get_bonus_pools()

    for pool in bonus_pools:
        if not pool.get("enabled", True):
            continue

        pool_name = pool.get("name", "排名奖金")
        ranking_basis = pool.get("ranking_basis", "total_score")
        filter_roles = pool.get("filter_roles", [])
        distribution_rules = pool.get("distribution_rules", [])

        if not distribution_rules:
            continue

        # 筛选参与排名的员工
        eligible_results = []
        for r in results:
            emp_id = r["employee_id"]
            emp = next((e for e in employees if e["id"] == emp_id), None)

            # 检查角色筛选
            if filter_roles:
                emp_role = emp.get("role_id") if emp else None
                if emp_role not in filter_roles:
                    continue

            # 计算排名分数
            if ranking_basis == "total_score":
                # 绩效总分
                score = sum(rd.get("score", 0) for rd in r.get("regions", {}).values())
            elif ranking_basis == "total_salary":
                # 工资总额（不含排名奖金）
                score = r.get("total_salary", 0) - sum(
                    v.get("amount", 0) for k, v in r.get("extra_income", {}).items()
                    if k == "ranking_bonus"
                )
            elif ranking_basis.startswith("region_"):
                # 指定区域绩效
                score = r.get("regions", {}).get(ranking_basis, {}).get("score", 0)
            else:
                score = 0

            eligible_results.append({
                "result": r,
                "score": score
            })

        # 按分数排序
        eligible_results.sort(key=lambda x: x["score"], reverse=True)

        # 分配奖金
        for rule in distribution_rules:
            rank = rule.get("rank", 0)
            amount = rule.get("amount", 0)
            desc = rule.get("description", f"第{rank}名")

            if rank <= 0 or rank > len(eligible_results):
                continue

            winner = eligible_results[rank - 1]["result"]

            # 添加排名奖金到额外收入
            if "ranking_bonus" not in winner["extra_income"]:
                winner["extra_income"]["ranking_bonus"] = {
                    "name": "排名奖金",
                    "details": [],
                    "amount": 0
                }

            winner["extra_income"]["ranking_bonus"]["details"].append({
                "pool_name": pool_name,
                "rank": rank,
                "description": desc,
                "amount": amount
            })
            winner["extra_income"]["ranking_bonus"]["amount"] += amount
            winner["total_salary"] += amount
            winner["total_salary"] = round(winner["total_salary"], 2)

    return results


def do_calculate(period_records: list, period: str) -> list:
    """执行计算（支持角色达标线和多元收入）"""
    regions = get_regions()
    skills = get_skills()
    emp_skills = get_employee_skills()
    employees = get_employees()

    # 获取外部数据（如果有）
    external_records = get_external_data(period)
    external_data_map = {}
    for ext in external_records:
        external_data_map[ext.get("employee_id")] = ext

    results = []

    for record in period_records:
        emp_id = record["employee_id"]
        emp_name = record["employee_name"]
        scores = record.get("scores", {})
        mid_detail = record.get("mid_detail", {"drawing": 0, "digital": 0})

        # 获取该员工的外部数据
        ext_data = external_data_map.get(emp_id)

        result = calculate_employee_salary(
            emp_id, emp_name, scores, mid_detail,
            regions, skills, emp_skills,
            employees=employees,
            external_data=ext_data
        )
        result["period"] = period
        results.append(result)

    # 计算排名奖金（在基础工资计算完成后）
    results = calculate_ranking_bonus(results, employees)

    # 按总工资排序
    results.sort(key=lambda x: x["total_salary"], reverse=True)

    return results


def display_region_detail(region: dict, rd: dict, result: dict):
    """显示单个区域的明细 - 紧凑横向布局"""
    region_id = region["id"]

    score = rd.get("score", 0)
    threshold = rd.get("threshold", region.get("threshold", 30000))
    is_on_duty = rd.get("is_on_duty", False)
    skill_salary = rd.get("skill_salary", 0)
    ladder_bonus = rd.get("ladder_bonus", 0)
    skill_details = rd.get("skill_details", [])

    # 使用小号字体的样式
    st.markdown('<style>.small-text { font-size: 0.85em; }</style>', unsafe_allow_html=True)

    # 达标线状态
    duty_status = "✅ 在岗" if is_on_duty else "⚠️ 不在岗"
    st.markdown(f'<p class="small-text"><b>【达标线】</b> {threshold:,.0f}分 | {duty_status}</p>', unsafe_allow_html=True)

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
    """显示员工总金额构成弹窗 - 紧凑版（支持额外收入）"""
    result = st.session_state.get("dialog_result", {})
    regions = get_regions()

    emp_name = result.get("employee_name", "")
    role_name = result.get("role_name", "未指定")
    total_salary = result.get("total_salary", 0)
    extra_income = result.get("extra_income", {})

    st.markdown(f"**{emp_name}** ({role_name})")

    # 区域收入
    st.markdown("**【区域收入】**")
    parts = []
    region_total = 0
    for region in regions:
        rd = result.get("regions", {}).get(region["id"], {})
        amount = rd.get("total", 0)
        if amount > 0:
            parts.append(f"{region['name']}:{amount:.0f}")
            region_total += amount

    if parts:
        line = " + ".join(parts) + f" = **{region_total:.0f}元**"
        st.markdown(f'<p style="font-size:0.9em;">{line}</p>', unsafe_allow_html=True)
    else:
        st.markdown("无区域收入")

    # 额外收入
    if extra_income:
        st.markdown("**【额外收入】**")
        extra_parts = []
        for key, value in extra_income.items():
            name = value.get("name", key)
            amount = value.get("amount", 0)
            if amount > 0:
                extra_parts.append(f"{name}:{amount:.0f}")

        if extra_parts:
            extra_line = " + ".join(extra_parts)
            st.markdown(f'<p style="font-size:0.9em;">{extra_line}</p>', unsafe_allow_html=True)

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
            "角色": r.get("role_name", "未指定"),
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

        # 额外收入
        extra_income = r.get("extra_income", {})
        extra_total = sum(v.get("amount", 0) for v in extra_income.values())
        if extra_total > 0:
            row["额外收入"] = round(extra_total)
        else:
            row["额外收入"] = 0

        row["总金额"] = round(r["total_salary"])
        table_data.append(row)

    df = pd.DataFrame(table_data)

    # 使用 st_table_select_cell 支持单元格点击
    st.markdown("**点击金额列查看该区域明细：**")

    # 构建列名到区域ID的映射
    col_to_region = {}
    for region in regions:
        col_to_region[f"{region['name']}金额"] = region["id"]
    col_to_region["总金额"] = "total"

    # 获取所有列名
    columns = df.columns.tolist()

    # 使用 st_table_select_cell 组件
    cell_clicked = st_table_select_cell(df)

    # 处理单元格点击事件
    if cell_clicked:
        row_idx = int(cell_clicked.get("rowId", 0))
        col_idx = cell_clicked.get("colIndex")

        if col_idx is not None and row_idx < len(results):
            col_name = columns[col_idx] if col_idx < len(columns) else None

            # 只有点击金额列才弹窗
            if col_name in col_to_region:
                selected_result = results[row_idx]
                clicked_region_id = col_to_region[col_name]

                # 存储数据到 session_state
                st.session_state.dialog_result = selected_result
                st.session_state.dialog_region = clicked_region_id

                # 调用弹窗
                if clicked_region_id == "total":
                    show_total_dialog()
                else:
                    show_detail_dialog()

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
