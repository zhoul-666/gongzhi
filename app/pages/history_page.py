"""
历史查询页面 - 查看往月绩效数据
样式与绩效计算页面统一，支持点击数据穿透
"""
import streamlit as st
import pandas as pd
import io
import sys
from pathlib import Path
from st_table_select_cell import st_table_select_cell

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.data_manager import get_regions, load_json, unlock_calculation


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
    result = st.session_state.get("history_dialog_result", {})
    clicked_region = st.session_state.get("history_dialog_region")
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
    result = st.session_state.get("history_dialog_result", {})
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
    calculations.sort(key=lambda x: x.get("month", "") or x.get("period", ""), reverse=True)

    # 获取月份列表（兼容month和period字段）
    months = []
    for c in calculations:
        month = c.get("month") or c.get("period", "")
        if month:
            months.append(month)

    # 选择月份
    selected_month = st.selectbox("选择月份", options=months)

    # 获取选中月份的数据（兼容month和period字段）
    selected_calc = next(
        (c for c in calculations if (c.get("month") or c.get("period")) == selected_month),
        None
    )

    if not selected_calc:
        st.warning("未找到该月份数据")
        return

    # 显示锁定状态和解锁按钮
    is_locked = selected_calc.get("locked", False)

    # 初始化解锁确认状态
    if "confirm_unlock_month" not in st.session_state:
        st.session_state.confirm_unlock_month = None

    if is_locked:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"🔒 「{selected_month}」已锁定（锁定时间：{selected_calc.get('locked_at', '')}）")
        with col2:
            if st.button("🔓 解锁", key="unlock_btn"):
                st.session_state.confirm_unlock_month = selected_month

        # 显示确认对话框
        if st.session_state.confirm_unlock_month == selected_month:
            st.warning("⚠️ 解锁后该月数据可被重新计算覆盖，确定要解锁吗？")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("确认解锁", key="confirm_unlock", type="primary"):
                    if unlock_calculation(selected_month):
                        st.session_state.confirm_unlock_month = None
                        st.success("✅ 已解锁")
                        st.rerun()
                    else:
                        st.error("解锁失败")
            with col_no:
                if st.button("取消", key="cancel_unlock"):
                    st.session_state.confirm_unlock_month = None
                    st.rerun()
    else:
        st.info(f"📝 「{selected_month}」未锁定，可在【绩效计算】页面重新计算")

    st.markdown("---")

    results = selected_calc.get("results", [])
    regions = get_regions()

    if results:
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

        st.markdown("**点击金额列（印前金额、印中金额、印后金额、前台金额）查看该区域明细**")

        # 构建表格数据
        table_data = []
        for r in results:
            row = {
                "期间": selected_month,
                "员工ID": r.get("employee_id", ""),
                "姓名": r.get("employee_name", ""),
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

            row["总金额"] = round(r.get("total_salary", 0))
            table_data.append(row)

        df = pd.DataFrame(table_data)

        # 使用支持单元格点击的表格组件
        selected_cell = st_table_select_cell(df)

        # 处理单元格点击事件 - 只有点击金额列才弹出对话框
        if selected_cell:
            row_idx = int(selected_cell.get('rowId', 0))
            col_idx = selected_cell.get('colIndex', 0)
            col_name = df.columns[col_idx] if col_idx < len(df.columns) else ""

            # 判断是否点击了金额列
            clicked_region = None
            if "印前金额" in col_name:
                clicked_region = "region_001"
            elif "印中金额" in col_name:
                clicked_region = "region_002"
            elif "印后金额" in col_name:
                clicked_region = "region_003"
            elif "前台金额" in col_name:
                clicked_region = "region_004"
            elif "总金额" in col_name:
                clicked_region = "total"

            # 只有点击金额列才弹出对话框
            if clicked_region:
                selected_result = results[row_idx]
                st.session_state["history_dialog_result"] = selected_result
                st.session_state["history_dialog_region"] = clicked_region
                if clicked_region == "total":
                    show_total_dialog()
                else:
                    show_detail_dialog()

        # 统计信息
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        total = sum(r.get("total_salary", 0) for r in results)
        with col1:
            st.metric("总人数", len(results))
        with col2:
            st.metric("工资总额", f"¥{total:,.2f}")
        with col3:
            avg = total / len(results) if results else 0
            st.metric("人均工资", f"¥{avg:,.2f}")

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

    # 计算历史（折叠面板）
    st.markdown("---")
    with st.expander(f"📋 计算历史（共{len(calculations)}条）", expanded=False):
        overview_data = []
        for calc in calculations:
            is_locked_item = calc.get("locked", False)
            locked_at = calc.get("locked_at", "")
            month = calc.get("month") or calc.get("period", "")
            overview_data.append({
                "状态": "🔒 已锁定" if is_locked_item else "📝 未锁定",
                "月份": month,
                "计算时间": calc.get("calculated_at", ""),
                "锁定时间": locked_at if is_locked_item else "-",
                "员工人数": calc.get("employee_count", 0),
                "工资总额": f"{calc.get('total_salary', 0):,.2f}"
            })

        overview_df = pd.DataFrame(overview_data)
        st.dataframe(overview_df, use_container_width=True, hide_index=True)

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
            calc1 = next((c for c in calculations if (c.get("month") or c.get("period")) == compare_month1), None)
            calc2 = next((c for c in calculations if (c.get("month") or c.get("period")) == compare_month2), None)

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
