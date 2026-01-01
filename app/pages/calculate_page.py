"""
绩效计算页面 - 核心计算引擎
"""
import streamlit as st
import pandas as pd
import sys
import io
import json
from pathlib import Path
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.data_manager import (
    get_employees, get_regions, get_skills,
    get_employee_skills, get_mode_by_id,
    save_json, load_json
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
            # 还没到这个区间
            break
        elif score >= max_val:
            # 完全超过这个区间，拿全额
            total_bonus += bonus
        else:
            # 在这个区间内，按比例计算
            if max_val > min_val:
                ratio = (score - min_val) / (max_val - min_val)
                total_bonus += bonus * ratio
            break

    return round(total_bonus, 2)


def calculate_employee_salary(emp_id: str, emp_name: str, scores: dict,
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
                "ladder_bonus": 阶梯奖金,
                "total": 小计
            },
            ...
        },
        "total_salary": 总工资
    }
    """
    result = {
        "employee_id": emp_id,
        "employee_name": emp_name,
        "regions": {},
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

        # 计算技能工资
        skill_salary = 0
        region_skills = [s for s in skills if s.get("region_id") == region_id]

        for skill in region_skills:
            if skill["id"] in my_skill_ids:
                # 找到对应的员工技能关联
                es = next((e for e in my_skills if e["skill_id"] == skill["id"]), None)
                if es and es.get("passed_exam", False):
                    # 通过考核才算工资
                    if is_on_duty:
                        skill_salary += skill.get("salary_on_duty", 200)
                    else:
                        skill_salary += skill.get("salary_off_duty", 100)

        # 计算阶梯奖金
        ladder_bonus = calculate_ladder_bonus(score, ladder_rules)

        # 区域小计
        region_total = skill_salary + ladder_bonus

        result["regions"][region_id] = {
            "name": region["name"],
            "score": score,
            "is_on_duty": is_on_duty,
            "skill_salary": skill_salary,
            "ladder_bonus": ladder_bonus,
            "total": region_total
        }

        result["total_salary"] += region_total

    result["total_salary"] = round(result["total_salary"], 2)
    return result


def render():
    st.title("🧮 绩效计算")
    st.markdown("---")

    # 获取数据
    perf_data = load_json("performance.json")
    records = perf_data.get("records", [])
    imports = perf_data.get("imports", [])

    if not records:
        st.warning("暂无绩效数据，请先导入绩效")
        return

    # 获取可选月份
    months = sorted(set(r["month"] for r in records), reverse=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        selected_month = st.selectbox("选择计算月份", options=months)

    # 获取该月数据
    month_records = [r for r in records if r["month"] == selected_month]
    st.info(f"该月共 {len(month_records)} 条绩效记录")

    # 保存名称输入框
    save_name = st.text_input(
        "保存名称",
        value=selected_month,
        help="计算结果的保存名称，可自定义（如：2024-12-方案一）"
    )

    st.markdown("---")

    # 计算按钮
    if st.button("🚀 开始计算", type="primary"):
        with st.spinner("正在计算..."):
            results = do_calculate(month_records, save_name)

        if results:
            st.success(f"计算完成！共 {len(results)} 人，保存为：{save_name}")

            # 显示结果
            display_results(results, save_name)

            # 保存结果
            save_results(results, save_name)


def do_calculate(month_records: list, month: str) -> list:
    """执行计算"""
    regions = get_regions()
    skills = get_skills()
    emp_skills = get_employee_skills()

    results = []

    for record in month_records:
        emp_id = record["employee_id"]
        emp_name = record["employee_name"]
        scores = record.get("scores", {})

        result = calculate_employee_salary(
            emp_id, emp_name, scores,
            regions, skills, emp_skills
        )
        result["month"] = month
        results.append(result)

    # 按总工资排序
    results.sort(key=lambda x: x["total_salary"], reverse=True)

    return results


def display_employee_detail(result: dict, regions: list):
    """显示单个员工的计算明细"""
    emp_name = result["employee_name"]
    total_salary = result["total_salary"]

    st.markdown(f"### 📋 {emp_name} 的计算明细")

    detail_lines = []
    total_parts = []

    for region in regions:
        region_id = region["id"]
        region_name = region["name"]

        if region_id in result.get("regions", {}):
            rd = result["regions"][region_id]
            score = rd.get("score", 0)
            skill_salary = rd.get("skill_salary", 0)
            ladder_bonus = rd.get("ladder_bonus", 0)
            total = rd.get("total", 0)

            if total > 0:
                status = "在岗" if rd.get("is_on_duty") else "不在岗"
                detail_lines.append(
                    f"**{region_name}小计** {total:.0f} = 技能工资 {skill_salary:.0f} + 阶梯奖金 {ladder_bonus:.0f}（绩效 {score:,.0f}，{status}）"
                )
                total_parts.append(f"{region_name} {total:.0f}")
            else:
                detail_lines.append(f"**{region_name}小计** 0（无绩效）")

    for line in detail_lines:
        st.markdown(line)

    st.markdown("---")
    if total_parts:
        total_formula = " + ".join(total_parts)
        st.markdown(f"**总工资 {total_salary:.2f}** = {total_formula}")
    else:
        st.markdown("**总工资 0**")


def display_results(results: list, month: str):
    """显示计算结果"""
    regions = get_regions()

    st.subheader("计算结果（双击某行展开/收起明细）")

    # 构建表格数据，包含详情信息
    display_data = []
    for r in results:
        # 构建详情数据
        detail_rows = []
        total_parts = []
        for region in regions:
            region_id = region["id"]
            region_name = region["name"]
            if region_id in r.get("regions", {}):
                rd = r["regions"][region_id]
                score = rd.get("score", 0)
                skill_salary = rd.get("skill_salary", 0)
                ladder_bonus = rd.get("ladder_bonus", 0)
                total = rd.get("total", 0)
                status = "在岗" if rd.get("is_on_duty") else "不在岗"

                if total > 0:
                    detail_rows.append({
                        "项目": f"{region_name}小计",
                        "计算公式": f"技能工资 {skill_salary:.0f} + 阶梯奖金 {ladder_bonus:.0f}",
                        "绩效分": f"{score:,.0f}",
                        "状态": status,
                        "金额": f"{total:.0f}"
                    })
                    total_parts.append(f"{region_name} {total:.0f}")

        # 添加总计行
        total_formula = " + ".join(total_parts) if total_parts else "无"
        detail_rows.append({
            "项目": "【总工资】",
            "计算公式": total_formula,
            "绩效分": "",
            "状态": "",
            "金额": f"{r.get('total_salary', 0):.2f}"
        })

        # 主行数据
        row = {"姓名": r["employee_name"]}
        for region in regions:
            region_id = region["id"]
            region_name = region["name"]
            if region_id in r.get("regions", {}):
                rd = r["regions"][region_id]
                row[f"{region_name}绩效分"] = rd.get("score", 0)
                row[f"{region_name}小计"] = rd.get("total", 0)
        row["总工资"] = r.get("total_salary", 0)
        row["detail_data"] = detail_rows  # 详情数据
        display_data.append(row)

    df = pd.DataFrame(display_data)

    # 配置 AgGrid - 使用 columnDefs 直接定义列
    column_defs = [
        {
            "field": "姓名",
            "cellRenderer": "agGroupCellRenderer",  # 显示展开箭头
            "width": 150,
            "pinned": "left"
        }
    ]

    # 添加区域列
    for region in regions:
        region_name = region["name"]
        column_defs.append({"field": f"{region_name}绩效分", "width": 100})
        column_defs.append({"field": f"{region_name}小计", "width": 100})

    column_defs.append({"field": "总工资", "width": 100, "pinned": "right"})

    # 配置 grid options
    grid_options = {
        "columnDefs": column_defs,
        "rowData": display_data,
        "masterDetail": True,
        "detailRowHeight": 150,
        "detailCellRendererParams": {
            "detailGridOptions": {
                "columnDefs": [
                    {"field": "项目", "width": 120},
                    {"field": "计算公式", "width": 250},
                    {"field": "绩效分", "width": 100},
                    {"field": "状态", "width": 80},
                    {"field": "金额", "width": 100},
                ],
                "defaultColDef": {"flex": 1},
            },
            "getDetailRowData": JsCode("""function(params) {
                params.successCallback(params.data.detail_data);
            }"""),
        },
        "defaultColDef": {
            "resizable": True,
            "sortable": True,
        }
    }

    # 显示 AgGrid
    AgGrid(
        df.drop(columns=["detail_data"]),
        gridOptions=grid_options,
        height=400,
        allow_unsafe_jscode=True,
        theme="streamlit"
    )

    # 汇总统计
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    total_all = sum(r["total_salary"] for r in results)
    with col1:
        st.metric("总人数", len(results))
    with col2:
        st.metric("工资总额", f"¥{total_all:,.2f}")
    with col3:
        avg = total_all / len(results) if results else 0
        st.metric("人均工资", f"¥{avg:,.2f}")

    # 导出Excel
    st.markdown("---")
    st.subheader("导出结果")

    # 准备导出数据
    export_df = prepare_export_data(results, regions)

    # 生成Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        export_df.to_excel(writer, sheet_name=f'{month}绩效工资', index=False)

    buffer.seek(0)

    st.download_button(
        label="📥 下载Excel",
        data=buffer,
        file_name=f"绩效工资_{month}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def prepare_export_data(results: list, regions: list) -> pd.DataFrame:
    """准备导出数据"""
    export_data = []

    for r in results:
        row = {
            "员工ID": r["employee_id"],
            "姓名": r["employee_name"],
            "月份": r.get("month", ""),
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

        row["总工资"] = r["total_salary"]
        export_data.append(row)

    return pd.DataFrame(export_data)


def save_results(results: list, month: str):
    """保存计算结果"""
    # 加载历史数据
    history_data = load_json("calculation_history.json")
    if not history_data:
        history_data = {"calculations": []}

    calculations = history_data.get("calculations", [])

    # 移除该月已有记录
    calculations = [c for c in calculations if c.get("month") != month]

    # 添加新记录
    calculations.append({
        "month": month,
        "calculated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "employee_count": len(results),
        "total_salary": sum(r["total_salary"] for r in results),
        "results": results
    })

    history_data["calculations"] = calculations
    save_json("calculation_history.json", history_data, backup=False)
