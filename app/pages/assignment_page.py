"""
员工技能指派页面 - 管理员工的技能分配和考核状态
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.data_manager import (
    get_employees, get_skills, get_skills_by_mode,
    get_employee_skills, assign_skill_to_employee, update_employee_skill,
    remove_employee_skill, batch_assign_skills_to_employee,
    get_modes, get_mode_by_id, get_regions, get_region_by_id,
    save_json, load_json
)


def render():
    st.title("📋 员工技能指派")
    st.markdown("---")

    employees = get_employees()
    modes = get_modes()
    regions = get_regions()
    all_skills = get_skills()

    if not employees:
        st.warning("暂无员工数据，请先添加员工或导入绩效数据")
        return

    # 两列布局：所属模式筛选 + 选择员工
    col1, col2 = st.columns(2)

    with col1:
        # 模式筛选选项
        mode_options = {"all": "全部模式"}
        for m in modes:
            mode_options[m["id"]] = m["name"]

        selected_mode_filter = st.selectbox(
            "所属模式",
            options=list(mode_options.keys()),
            format_func=lambda x: mode_options.get(x, x),
            key="mode_filter"
        )

    # 根据模式筛选员工列表
    if selected_mode_filter == "all":
        filtered_employees = employees
    else:
        filtered_employees = [e for e in employees if e.get("mode_id") == selected_mode_filter]

    with col2:
        if not filtered_employees:
            st.warning("该模式下暂无员工")
            return

        emp_options = {e["id"]: f"{e['name']} ({e.get('employee_no', '')})" for e in filtered_employees}
        selected_emp_id = st.selectbox(
            "选择员工",
            options=list(emp_options.keys()),
            format_func=lambda x: emp_options.get(x, x),
            key="assign_emp_select"
        )

    selected_emp = next((e for e in employees if e["id"] == selected_emp_id), None)

    if not selected_emp:
        return

    # 获取员工所属模式
    mode = get_mode_by_id(selected_emp.get("mode_id", ""))
    if not mode:
        st.warning("该员工尚未指定所属模式，请先在员工管理中设置")
        return

    st.markdown("---")

    # 获取该员工可用的技能（根据模式）
    available_skills = get_skills_by_mode(selected_emp.get("mode_id", ""))

    # 获取已分配的技能
    assigned = get_employee_skills(selected_emp_id)
    assigned_skill_ids = [a["skill_id"] for a in assigned]

    # 未分配的技能
    unassigned_skills = [s for s in available_skills if s["id"] not in assigned_skill_ids]

    # 使用 Tab 切换已分配和可分配
    tab1, tab2 = st.tabs([f"已分配技能 ({len(assigned)}个)", f"可分配技能 ({len(unassigned_skills)}个)"])

    with tab1:
        if not assigned:
            st.info("该员工暂未分配任何技能")
        else:
            # 按区域分组
            assigned_by_region = {}
            for assignment in assigned:
                skill = next((s for s in all_skills if s["id"] == assignment["skill_id"]), None)
                if not skill:
                    continue
                region_id = skill.get("region_id", "unknown")
                if region_id not in assigned_by_region:
                    assigned_by_region[region_id] = []
                assigned_by_region[region_id].append((assignment, skill))

            for region_id, items in assigned_by_region.items():
                region = get_region_by_id(region_id)
                region_name = region["name"] if region else "未分类"
                system_threshold = region.get("threshold", 30000) if region else 30000

                st.markdown(f"**{region_name}** ({len(items)}个)")

                # 三列网格布局
                cols = st.columns(3)
                for idx, (assignment, skill) in enumerate(items):
                    col_idx = idx % 3
                    current_use_system = assignment.get("use_system_threshold", True)
                    current_custom = assignment.get("custom_threshold") or system_threshold

                    with cols[col_idx]:
                        with st.container(border=True):
                            # 考核状态 + 技能名称
                            passed = assignment.get("passed_exam", False)
                            new_passed = st.checkbox(
                                skill['name'],
                                value=passed,
                                key=f"exam_{selected_emp_id}_{skill['id']}"
                            )
                            if new_passed != passed:
                                update_employee_skill(selected_emp_id, skill["id"], {"passed_exam": new_passed})
                                st.rerun()

                            # 获取当前价格设置
                            current_use_system_price = assignment.get("use_system_price", True)
                            default_price = skill.get('salary_on_duty', 0)
                            current_custom_price = assignment.get("custom_price_on_duty") or default_price

                            # 工资信息
                            st.caption(f"默认: 在岗{default_price} / 不在岗{skill.get('salary_off_duty', 0)}")

                            # 分值设置
                            threshold_option = st.radio(
                                "分值",
                                options=["默认", "自定义"],
                                index=0 if current_use_system else 1,
                                key=f"th_{selected_emp_id}_{skill['id']}",
                                horizontal=True
                            )
                            use_system = threshold_option == "默认"

                            if not use_system:
                                custom_val = st.number_input(
                                    "自定义分值",
                                    value=current_custom,
                                    min_value=0,
                                    step=5000,
                                    key=f"cv_{selected_emp_id}_{skill['id']}",
                                    label_visibility="collapsed"
                                )
                            else:
                                custom_val = current_custom

                            # 检测达标值变化并保存
                            if use_system != current_use_system or (not use_system and custom_val != current_custom):
                                if use_system:
                                    update_employee_skill(selected_emp_id, skill["id"],
                                        {"use_system_threshold": True, "custom_threshold": None})
                                else:
                                    update_employee_skill(selected_emp_id, skill["id"],
                                        {"use_system_threshold": False, "custom_threshold": custom_val})
                                st.rerun()

                            # 奖金设置
                            price_option = st.radio(
                                "奖金",
                                options=["默认", "自定义"],
                                index=0 if current_use_system_price else 1,
                                key=f"price_{selected_emp_id}_{skill['id']}",
                                horizontal=True
                            )
                            use_system_price = price_option == "默认"

                            if not use_system_price:
                                custom_price = st.number_input(
                                    "自定义奖金",
                                    value=current_custom_price,
                                    min_value=0,
                                    step=50,
                                    key=f"cp_{selected_emp_id}_{skill['id']}",
                                    label_visibility="collapsed"
                                )
                            else:
                                custom_price = current_custom_price

                            # 检测价格变化并保存
                            if use_system_price != current_use_system_price or (not use_system_price and custom_price != current_custom_price):
                                if use_system_price:
                                    update_employee_skill(selected_emp_id, skill["id"],
                                        {"use_system_price": True, "custom_price_on_duty": None})
                                else:
                                    update_employee_skill(selected_emp_id, skill["id"],
                                        {"use_system_price": False, "custom_price_on_duty": custom_price})
                                st.rerun()

                            # 取消分配按钮
                            if st.button("取消分配", key=f"remove_{selected_emp_id}_{skill['id']}", type="secondary"):
                                remove_employee_skill(selected_emp_id, skill["id"])
                                st.rerun()

                    # 每3个重新创建列
                    if col_idx == 2 and idx < len(items) - 1:
                        cols = st.columns(3)

                st.markdown("")  # 区域之间的间隔

    with tab2:
        if not unassigned_skills:
            st.info("已分配所有可用技能")
        else:
            # 准备表格数据
            table_data = []
            for skill in unassigned_skills:
                region = get_region_by_id(skill.get("region_id"))
                table_data.append({
                    "选择": False,
                    "技能名称": skill['name'],
                    "区域": region["name"] if region else "未分类",
                    "在岗工资": skill.get('salary_on_duty', 0),
                    "不在岗工资": skill.get('salary_off_duty', 0),
                    "_skill_id": skill['id']
                })

            df = pd.DataFrame(table_data)

            # 主操作按钮（表格上方）
            col1, col2 = st.columns([1, 4])
            with col1:
                confirm_btn = st.button("✅ 确认分配所选", type="primary", use_container_width=True)
            with col2:
                st.caption("💡 勾选左侧复选框，然后点击按钮批量分配")

            # 数据表格
            edited_df = st.data_editor(
                df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "选择": st.column_config.CheckboxColumn("选择", default=False),
                    "技能名称": st.column_config.TextColumn("技能名称", disabled=True),
                    "区域": st.column_config.TextColumn("区域", disabled=True),
                    "在岗工资": st.column_config.NumberColumn("在岗工资", disabled=True),
                    "不在岗工资": st.column_config.NumberColumn("不在岗工资", disabled=True),
                    "_skill_id": None  # 隐藏
                }
            )

            # 处理批量分配
            if confirm_btn:
                selected = edited_df[edited_df["选择"]]["_skill_id"].tolist()
                if not selected:
                    st.warning("请先选择要分配的技能")
                else:
                    results = batch_assign_skills_to_employee(selected_emp_id, selected)
                    if results["success"]:
                        st.success(f"✅ 已分配 {len(results['success'])} 个技能")
                    if results["skipped"]:
                        st.info(f"⏭️ 跳过已存在的 {len(results['skipped'])} 个技能")
                    st.rerun()

    # 批量分配功能
    st.markdown("---")
    st.subheader("批量操作")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("一键分配所有可用技能", type="secondary"):
            count = 0
            for skill in unassigned_skills:
                assign_skill_to_employee(selected_emp_id, skill["id"], passed_exam=False)
                count += 1
            if count > 0:
                st.success(f"已批量分配 {count} 个技能")
                st.rerun()

    with col2:
        if st.button("一键通过所有已分配技能考核"):
            count = 0
            for assignment in assigned:
                if not assignment.get("passed_exam", False):
                    update_employee_skill(
                        selected_emp_id,
                        assignment["skill_id"],
                        {"passed_exam": True}
                    )
                    count += 1
            if count > 0:
                st.success(f"已通过 {count} 个技能的考核")
                st.rerun()
