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

    # 选择员工
    emp_options = {e["id"]: f"{e['name']} ({e.get('employee_no', '')})" for e in employees}

    col1, col2 = st.columns([2, 3])
    with col1:
        selected_emp_id = st.selectbox(
            "选择员工",
            options=list(emp_options.keys()),
            format_func=lambda x: emp_options.get(x, x),
            key="assign_emp_select"
        )

    selected_emp = next((e for e in employees if e["id"] == selected_emp_id), None)

    if not selected_emp:
        return

    # 显示员工基本信息
    mode = get_mode_by_id(selected_emp.get("mode_id", ""))

    with col2:
        if mode:
            st.info(f"所属模式：**{mode['name']}**")
        else:
            st.warning("该员工尚未指定所属模式，请先在员工管理中设置")
            return

    st.markdown("---")

    # 获取该员工可用的技能（根据模式）
    available_skills = get_skills_by_mode(selected_emp.get("mode_id", ""))

    # 获取已分配的技能
    assigned = get_employee_skills(selected_emp_id)
    assigned_skill_ids = [a["skill_id"] for a in assigned]

    # 分两列显示
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("已分配技能")

        if not assigned:
            st.info("该员工暂未分配任何技能")
        else:
            for assignment in assigned:
                skill = next((s for s in all_skills if s["id"] == assignment["skill_id"]), None)
                if not skill:
                    continue

                region = get_region_by_id(skill.get("region_id", ""))
                region_name = region["name"] if region else "-"
                system_threshold = region.get("threshold", 30000) if region else 30000
                current_use_system = assignment.get("use_system_threshold", True)
                current_custom = assignment.get("custom_threshold") or system_threshold

                with st.container():
                    # 技能信息
                    st.markdown(f"**{skill['name']}** ({region_name})")
                    st.caption(f"在岗: {skill.get('salary_on_duty', 0)}元 | 不在岗: {skill.get('salary_off_duty', 0)}元")

                    col1, col2, col3 = st.columns([1.5, 2, 1.5])

                    with col1:
                        # 考核状态
                        passed = assignment.get("passed_exam", False)
                        new_passed = st.checkbox(
                            "已通过考核",
                            value=passed,
                            key=f"exam_{selected_emp_id}_{skill['id']}"
                        )
                        if new_passed != passed:
                            update_employee_skill(
                                selected_emp_id,
                                skill["id"],
                                {"passed_exam": new_passed}
                            )
                            st.rerun()

                    with col2:
                        # 达标值设置
                        threshold_option = st.radio(
                            "达标值",
                            options=[f"系统({system_threshold:,})", "自定义"],
                            index=0 if current_use_system else 1,
                            key=f"threshold_{selected_emp_id}_{skill['id']}",
                            horizontal=True,
                            label_visibility="collapsed"
                        )
                        use_system = threshold_option.startswith("系统")

                    with col3:
                        # 自定义达标值输入
                        custom_val = st.number_input(
                            "自定义值",
                            value=current_custom,
                            min_value=0,
                            step=5000,
                            key=f"custom_{selected_emp_id}_{skill['id']}",
                            disabled=use_system,
                            label_visibility="collapsed"
                        )

                    # 检测变化并保存
                    if use_system != current_use_system or (not use_system and custom_val != current_custom):
                        if use_system:
                            update_employee_skill(selected_emp_id, skill["id"],
                                {"use_system_threshold": True, "custom_threshold": None})
                        else:
                            update_employee_skill(selected_emp_id, skill["id"],
                                {"use_system_threshold": False, "custom_threshold": custom_val})
                        st.rerun()

                    st.divider()

    with col_right:
        st.subheader("可分配技能")

        # 未分配的技能
        unassigned_skills = [s for s in available_skills if s["id"] not in assigned_skill_ids]

        if not unassigned_skills:
            st.info("已分配所有可用技能")
        else:
            # 按区域分组显示
            skills_by_region = {}
            for skill in unassigned_skills:
                region_id = skill.get("region_id", "unknown")
                if region_id not in skills_by_region:
                    skills_by_region[region_id] = []
                skills_by_region[region_id].append(skill)

            for region_id, skills in skills_by_region.items():
                region = get_region_by_id(region_id)
                region_name = region["name"] if region else "未分类"

                with st.expander(f"📁 {region_name} ({len(skills)}个)", expanded=True):
                    for skill in skills:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{skill['name']}**")
                            st.caption(f"在岗: {skill.get('salary_on_duty', 0)}元 | 不在岗: {skill.get('salary_off_duty', 0)}元")
                        with col2:
                            if st.button("分配", key=f"assign_{selected_emp_id}_{skill['id']}"):
                                assign_skill_to_employee(
                                    selected_emp_id,
                                    skill["id"],
                                    passed_exam=False
                                )
                                st.success(f"已分配: {skill['name']}")
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

