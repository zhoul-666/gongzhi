"""
历史查询页面 - 查看往月绩效数据
"""
import streamlit as st
import pandas as pd
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.data_manager import get_regions, load_json


def display_employee_detail(result: dict, regions: list):
    """显示单个员工的计算明细"""
    emp_name = result.get("employee_name", "")
    total_salary = result.get("total_salary", 0)

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


def render():
    st.title("📜 历史查询")
    st.markdown("---")

    # 加载历史数据
    history_data = load_json("calculation_history.json")
    calculations = history_data.get("calculations", []) if history_data else []

    if not calculations:
        st.info("暂无历史计算记录")
        st.markdown("请先在【绩效计算】页面完成计算")
        return

    # 按月份排序
    calculations.sort(key=lambda x: x.get("month", ""), reverse=True)

    # 显示历史记录概览
    st.subheader("计算历史")

    overview_data = []
    for calc in calculations:
        overview_data.append({
            "月份": calc.get("month", ""),
            "计算时间": calc.get("calculated_at", ""),
            "员工人数": calc.get("employee_count", 0),
            "工资总额": f"{calc.get('total_salary', 0):,.2f}"
        })

    overview_df = pd.DataFrame(overview_data)
    st.dataframe(overview_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 选择查看详情
    st.subheader("查看详情")

    months = [c.get("month", "") for c in calculations]
    selected_month = st.selectbox("选择月份", options=months)

    # 获取选中月份的数据
    selected_calc = next((c for c in calculations if c.get("month") == selected_month), None)

    if selected_calc:
        results = selected_calc.get("results", [])
        regions = get_regions()

        if results:
            # 构建表格数据
            display_data = []
            for r in results:
                row = {"姓名": r.get("employee_name", "")}
                for region in regions:
                    region_id = region["id"]
                    region_name = region["name"]
                    if region_id in r.get("regions", {}):
                        rd = r["regions"][region_id]
                        row[f"{region_name}绩效分"] = rd.get("score", 0)
                        row[f"{region_name}小计"] = rd.get("total", 0)
                row["总工资"] = r.get("total_salary", 0)
                display_data.append(row)

            df = pd.DataFrame(display_data)

            # 使用原生表格显示
            st.dataframe(df, use_container_width=True, hide_index=True)

            # 展开查看详情
            st.markdown("---")
            st.subheader("查看明细")

            emp_names = [r.get("employee_name", "") for r in results]
            selected_emp = st.selectbox("选择员工", options=emp_names, key="history_detail_emp")

            if selected_emp:
                result = next((r for r in results if r.get("employee_name") == selected_emp), None)
                if result:
                    with st.expander(f"📋 {selected_emp} 的计算明细", expanded=True):
                        detail_data = []
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
                                status = "在岗" if rd.get("is_on_duty") else "不在岗"

                                if total > 0:
                                    detail_data.append({
                                        "项目": f"{region_name}小计",
                                        "计算公式": f"技能 {skill_salary:.0f} + 阶梯 {ladder_bonus:.0f}",
                                        "绩效分": f"{score:,.0f}",
                                        "状态": status,
                                        "金额": f"{total:.0f}"
                                    })
                                    total_parts.append(f"{region_name} {total:.0f}")

                        if detail_data:
                            detail_df = pd.DataFrame(detail_data)
                            st.dataframe(detail_df, use_container_width=True, hide_index=True)

                            total_formula = " + ".join(total_parts)
                            st.markdown(f"**总工资 {result.get('total_salary', 0):.2f}** = {total_formula}")
                        else:
                            st.info("该员工无绩效数据")

            # 统计信息
            col1, col2, col3 = st.columns(3)
            total = sum(r.get("total_salary", 0) for r in results)
            with col1:
                st.metric("总人数", len(results))
            with col2:
                st.metric("工资总额", f"{total:,.2f}")
            with col3:
                avg = total / len(results) if results else 0
                st.metric("人均工资", f"{avg:,.2f}")

            # 导出功能
            st.markdown("---")

            # 准备导出数据
            export_data = []
            for r in results:
                row = {
                    "员工ID": r.get("employee_id", ""),
                    "姓名": r.get("employee_name", ""),
                    "月份": selected_month,
                }

                for region in regions:
                    region_id = region["id"]
                    region_name = region["name"]
                    if region_id in r.get("regions", {}):
                        rd = r["regions"][region_id]
                        row[f"{region_name}_绩效分"] = rd.get("score", 0)
                        row[f"{region_name}_在岗"] = "是" if rd.get("is_on_duty") else "否"
                        row[f"{region_name}_技能工资"] = rd.get("skill_salary", 0)
                        row[f"{region_name}_阶梯奖金"] = rd.get("ladder_bonus", 0)
                        row[f"{region_name}_小计"] = rd.get("total", 0)

                row["总工资"] = r.get("total_salary", 0)
                export_data.append(row)

            export_df = pd.DataFrame(export_data)

            # 生成Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                export_df.to_excel(writer, sheet_name=f'{selected_month}绩效工资', index=False)

            buffer.seek(0)

            st.download_button(
                label="📥 导出Excel",
                data=buffer,
                file_name=f"绩效工资_{selected_month}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # 月度对比功能
    st.markdown("---")
    st.subheader("月度对比")

    if len(calculations) >= 2:
        col1, col2 = st.columns(2)

        with col1:
            compare_month1 = st.selectbox("月份1", options=months, key="compare1")
        with col2:
            compare_month2 = st.selectbox(
                "月份2",
                options=months,
                index=1 if len(months) > 1 else 0,
                key="compare2"
            )

        if compare_month1 and compare_month2 and compare_month1 != compare_month2:
            calc1 = next((c for c in calculations if c.get("month") == compare_month1), None)
            calc2 = next((c for c in calculations if c.get("month") == compare_month2), None)

            if calc1 and calc2:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"**{compare_month1}**")
                    st.write(f"人数: {calc1.get('employee_count', 0)}")
                    st.write(f"总额: {calc1.get('total_salary', 0):,.2f}")

                with col2:
                    st.markdown(f"**{compare_month2}**")
                    st.write(f"人数: {calc2.get('employee_count', 0)}")
                    st.write(f"总额: {calc2.get('total_salary', 0):,.2f}")

                with col3:
                    st.markdown("**变化**")
                    diff_count = calc1.get('employee_count', 0) - calc2.get('employee_count', 0)
                    diff_total = calc1.get('total_salary', 0) - calc2.get('total_salary', 0)
                    st.write(f"人数: {'+' if diff_count >= 0 else ''}{diff_count}")
                    st.write(f"总额: {'+' if diff_total >= 0 else ''}{diff_total:,.2f}")
    else:
        st.info("需要至少两个月的数据才能进行对比")
