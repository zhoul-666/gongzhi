"""
工作技能管理页面 - 支持批量编辑
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.data_manager import (
    get_skills, add_skill, update_skill, batch_update_skills,
    get_modes, get_mode_by_id, get_regions, get_region_by_id,
    save_json, load_json
)


def render():
    st.title("🔧 工作技能管理")
    st.markdown("---")

    skills = get_skills()
    modes = get_modes()
    regions = get_regions()

    mode_options = {m["id"]: m["name"] for m in modes}
    region_options = {r["id"]: r["name"] for r in regions}

    # 添加新技能
    with st.expander("➕ 添加新技能", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("技能名称", key="new_skill_name")
            new_mode = st.selectbox(
                "所属模式",
                options=list(mode_options.keys()),
                format_func=lambda x: mode_options.get(x, x),
                key="new_skill_mode"
            )
        with col2:
            new_region = st.selectbox(
                "所属大区域",
                options=list(region_options.keys()),
                format_func=lambda x: region_options.get(x, x),
                key="new_skill_region"
            )
            col_a, col_b = st.columns(2)
            with col_a:
                new_on_duty = st.number_input("在岗工资", value=200, min_value=0, key="new_on_duty")
            with col_b:
                new_off_duty = st.number_input("不在岗工资", value=100, min_value=0, key="new_off_duty")

        if st.button("添加技能", type="primary"):
            if new_name:
                result = add_skill(new_name, new_mode, new_region, new_on_duty, new_off_duty)
                if result:
                    st.success(f"添加成功：{new_name}")
                    st.rerun()
            else:
                st.error("请输入技能名称")

    st.markdown("---")

    # 筛选条件
    st.subheader("技能列表")

    mode_filter_options = ["全部"] + [m["name"] for m in modes]
    filter_mode = st.segmented_control(
        "按模式筛选",
        options=mode_filter_options,
        default="全部",
        key="filter_skill_mode"
    )

    region_filter_options = ["全部"] + [r["name"] for r in regions]
    filter_region = st.segmented_control(
        "按区域筛选",
        options=region_filter_options,
        default="全部",
        key="filter_skill_region"
    )

    # 筛选数据
    filtered_skills = skills.copy()
    if filter_mode != "全部":
        mode_id = next((m["id"] for m in modes if m["name"] == filter_mode), None)
        filtered_skills = [s for s in filtered_skills if s.get("mode_id") == mode_id]
    if filter_region != "全部":
        region_id = next((r["id"] for r in regions if r["name"] == filter_region), None)
        filtered_skills = [s for s in filtered_skills if s.get("region_id") == region_id]

    if not filtered_skills:
        st.info("暂无技能数据，请添加技能")
        return

    # 初始化选中状态
    if "selected_skills" not in st.session_state:
        st.session_state.selected_skills = set()
    if "checkbox_version" not in st.session_state:
        st.session_state.checkbox_version = 0

    # 批量操作区
    st.markdown("**批量操作：**")

    # 第一行：全选/取消全选
    col1, col2 = st.columns(2)
    with col1:
        if st.button("全选", use_container_width=True):
            st.session_state.selected_skills = set(s["id"] for s in filtered_skills)
            st.session_state.checkbox_version += 1
            st.rerun()
    with col2:
        if st.button("取消全选", use_container_width=True):
            st.session_state.selected_skills = set()
            st.session_state.checkbox_version += 1
            st.rerun()

    # 第二行：批量设置工资（四列对齐）
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        batch_on_duty = st.number_input("批量在岗", value=200, min_value=0, key="batch_on")
    with col2:
        if st.button("应用在岗", use_container_width=True):
            if st.session_state.selected_skills:
                count = batch_update_skills(
                    list(st.session_state.selected_skills),
                    {"salary_on_duty": batch_on_duty}
                )
                st.success(f"已更新 {count} 个技能的在岗工资")
                st.rerun()
            else:
                st.warning("请先选择技能")
    with col3:
        batch_off_duty = st.number_input("批量不在岗", value=100, min_value=0, key="batch_off")
    with col4:
        if st.button("应用不在岗", use_container_width=True):
            if st.session_state.selected_skills:
                count = batch_update_skills(
                    list(st.session_state.selected_skills),
                    {"salary_off_duty": batch_off_duty}
                )
                st.success(f"已更新 {count} 个技能的不在岗工资")
                st.rerun()
            else:
                st.warning("请先选择技能")

    st.markdown("---")

    # 技能列表（三列网格布局）
    cols = st.columns(3)
    for idx, skill in enumerate(filtered_skills):
        col_idx = idx % 3

        with cols[col_idx]:
            with st.container(border=True):
                # 第一行：勾选框 + 技能名
                c1, c2 = st.columns([0.15, 0.85])
                with c1:
                    is_selected = skill["id"] in st.session_state.selected_skills
                    version = st.session_state.checkbox_version
                    if st.checkbox("", value=is_selected, key=f"check_v{version}_{skill['id']}", label_visibility="collapsed"):
                        st.session_state.selected_skills.add(skill["id"])
                    else:
                        st.session_state.selected_skills.discard(skill["id"])
                with c2:
                    st.markdown(f"**{skill['name']}**")

                # 第二行：在岗/不在岗 + 保存按钮
                c1, c2, c3 = st.columns([1, 1, 0.6])
                with c1:
                    new_on = st.number_input(
                        "在岗",
                        value=skill.get("salary_on_duty", 200),
                        min_value=0,
                        step=50,
                        key=f"on_{skill['id']}",
                        label_visibility="collapsed"
                    )
                with c2:
                    new_off = st.number_input(
                        "不在岗",
                        value=skill.get("salary_off_duty", 100),
                        min_value=0,
                        step=50,
                        key=f"off_{skill['id']}",
                        label_visibility="collapsed"
                    )
                with c3:
                    if st.button("保存", key=f"save_{skill['id']}"):
                        update_skill(skill["id"], {
                            "salary_on_duty": new_on,
                            "salary_off_duty": new_off
                        })
                        st.rerun()

        # 每三个重新创建列
        if col_idx == 2 and idx < len(filtered_skills) - 1:
            cols = st.columns(3)

    # 统计信息
    st.markdown("---")
    st.caption(f"共 {len(filtered_skills)} 个技能，已选中 {len(st.session_state.selected_skills)} 个")
