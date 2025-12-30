"""
员工管理页面
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.data_manager import (
    get_employees, add_employee, update_employee, delete_employee,
    get_modes, get_mode_by_id
)


def render():
    st.title("👥 员工管理")
    st.markdown("---")

    # 获取数据
    employees = get_employees()
    modes = get_modes()
    mode_options = {m["id"]: m["name"] for m in modes}

    # 添加员工区域
    with st.expander("➕ 添加新员工", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            new_name = st.text_input("姓名", key="new_emp_name")
        with col2:
            new_no = st.text_input("工号（可选）", key="new_emp_no")
        with col3:
            new_mode = st.selectbox(
                "所属模式",
                options=list(mode_options.keys()),
                format_func=lambda x: mode_options.get(x, x),
                key="new_emp_mode"
            )

        if st.button("添加员工", type="primary"):
            if new_name:
                result = add_employee(new_name, new_no or None, new_mode)
                if result:
                    st.success(f"添加成功：{new_name}")
                    st.rerun()
            else:
                st.error("请输入员工姓名")

    st.markdown("---")

    # 员工列表
    st.subheader("员工列表")

    if not employees:
        st.info("暂无员工数据，请添加员工或导入绩效数据")
        return

    # 转换为DataFrame显示
    df_data = []
    for emp in employees:
        mode = get_mode_by_id(emp.get("mode_id", ""))
        df_data.append({
            "系统ID": emp["id"],
            "工号": emp.get("employee_no", ""),
            "姓名": emp["name"],
            "所属模式": mode["name"] if mode else "未指定",
            "创建时间": emp.get("created_at", "")
        })

    df = pd.DataFrame(df_data)

    # 筛选功能
    mode_filter_options = ["全部"] + list(mode_options.values())
    filter_mode = st.segmented_control(
        "按模式筛选",
        options=mode_filter_options,
        default="全部",
        key="filter_mode"
    )

    if filter_mode != "全部":
        df = df[df["所属模式"] == filter_mode]

    # 显示表格
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 编辑/删除区域
    st.subheader("编辑员工")

    if employees:
        # 构建选项列表
        emp_labels = [f"{e['name']} ({e.get('employee_no', '')})" for e in employees]

        # 选择员工
        selected_label = st.selectbox(
            "选择员工",
            options=emp_labels,
            key="emp_selector"
        )

        # 获取选中的员工索引和数据
        selected_idx = emp_labels.index(selected_label)
        selected_emp = employees[selected_idx]
        selected_emp_id = selected_emp["id"]

        # 使用 st.form 包装编辑区域
        with st.form(key=f"form_{selected_emp_id}"):
            col1, col2, col3 = st.columns(3)

            with col1:
                edit_name = st.text_input(
                    "姓名",
                    value=selected_emp["name"],
                    key=f"name_{selected_emp_id}"
                )
            with col2:
                edit_no = st.text_input(
                    "工号",
                    value=selected_emp.get("employee_no", ""),
                    key=f"no_{selected_emp_id}"
                )
            with col3:
                mode_ids = list(mode_options.keys())
                mode_names = list(mode_options.values())
                current_mode_id = selected_emp.get("mode_id", mode_ids[0])
                current_mode_idx = mode_ids.index(current_mode_id) if current_mode_id in mode_ids else 0

                edit_mode_name = st.selectbox(
                    "所属模式",
                    options=mode_names,
                    index=current_mode_idx,
                    key=f"mode_{selected_emp_id}"
                )
                edit_mode_id = mode_ids[mode_names.index(edit_mode_name)]

            # 操作按钮
            col1, col2 = st.columns(2)
            with col1:
                save_clicked = st.form_submit_button("保存修改", type="primary")
            with col2:
                delete_clicked = st.form_submit_button("删除员工")

        # 处理按钮点击
        if save_clicked:
            updates = {
                "name": edit_name,
                "employee_no": edit_no,
                "mode_id": edit_mode_id
            }
            if update_employee(selected_emp_id, updates):
                st.success(f"已保存修改: {edit_name}")
                st.rerun()
            else:
                st.error("保存失败")

        if delete_clicked:
            if delete_employee(selected_emp_id):
                st.success("删除成功")
                st.rerun()
            else:
                st.error("删除失败")
