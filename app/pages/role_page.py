"""
角色管理页面 - 配置岗位角色、收入类型、达标线倍率
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.data_manager import (
    get_roles, add_role, update_role, delete_role, get_role_by_id
)

# 收入类型选项
INCOME_TYPE_OPTIONS = {
    "skill_salary": "技能工资",
    "ladder_bonus": "阶梯奖金",
    "order_bonus": "开单奖励",
    "management_allowance": "管理津贴",
    "revenue_commission": "业绩提成",
    "ranking_bonus": "排名奖金"
}


def render():
    st.title("🎭 角色管理")
    st.markdown("配置不同岗位角色的达标线倍率和收入类型")
    st.markdown("---")

    # 获取数据
    roles = get_roles()

    # 添加角色区域
    with st.expander("➕ 添加新角色", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            new_name = st.text_input("角色名称", key="new_role_name", placeholder="如：前台文员")
        with col2:
            new_multiplier = st.number_input(
                "达标线倍率",
                min_value=0.0,
                max_value=2.0,
                value=1.0,
                step=0.1,
                key="new_role_multiplier",
                help="相对于系统达标线的倍率，如0.4表示达标线为系统的40%"
            )

        new_desc = st.text_input("角色描述", key="new_role_desc", placeholder="简要描述该角色的职责")

        # 收入类型选择
        st.markdown("**选择收入类型：**")
        new_income_types = []
        cols = st.columns(3)
        for i, (type_id, type_name) in enumerate(INCOME_TYPE_OPTIONS.items()):
            with cols[i % 3]:
                if st.checkbox(type_name, key=f"new_income_{type_id}",
                               value=(type_id in ["skill_salary", "ladder_bonus"])):
                    new_income_types.append(type_id)

        # 收入类型配置
        new_settings = {}
        if "order_bonus" in new_income_types:
            new_settings["order_bonus_per_unit"] = st.number_input(
                "开单奖励单价（元/单）", min_value=0.0, value=2.0, key="new_order_bonus"
            )
        if "management_allowance" in new_income_types:
            new_settings["management_allowance"] = st.number_input(
                "管理津贴（元/月）", min_value=0.0, value=500.0, key="new_mgmt_allowance"
            )
        if "revenue_commission" in new_income_types:
            new_settings["commission_rate"] = st.number_input(
                "业绩提成比例", min_value=0.0, max_value=1.0, value=0.01,
                step=0.001, format="%.3f", key="new_commission_rate"
            )

        if st.button("添加角色", type="primary"):
            if new_name:
                if not new_income_types:
                    new_income_types = ["skill_salary", "ladder_bonus"]
                result = add_role(
                    name=new_name,
                    description=new_desc,
                    threshold_multiplier=new_multiplier,
                    income_types=new_income_types,
                    settings=new_settings
                )
                if result:
                    st.success(f"添加成功：{new_name}")
                    st.rerun()
            else:
                st.error("请输入角色名称")

    # 编辑角色区域
    with st.expander("✏️ 编辑角色", expanded=False):
        if roles:
            role_labels = [f"{r['name']} (倍率: {r.get('threshold_multiplier', 1.0)})" for r in roles]

            selected_label = st.selectbox(
                "选择角色",
                options=role_labels,
                key="role_selector"
            )

            selected_idx = role_labels.index(selected_label)
            selected_role = roles[selected_idx]
            selected_role_id = selected_role["id"]

            with st.form(key=f"form_{selected_role_id}"):
                col1, col2 = st.columns(2)

                with col1:
                    edit_name = st.text_input(
                        "角色名称",
                        value=selected_role["name"],
                        key=f"name_{selected_role_id}"
                    )
                with col2:
                    edit_multiplier = st.number_input(
                        "达标线倍率",
                        min_value=0.0,
                        max_value=2.0,
                        value=float(selected_role.get("threshold_multiplier", 1.0)),
                        step=0.1,
                        key=f"multiplier_{selected_role_id}"
                    )

                edit_desc = st.text_input(
                    "角色描述",
                    value=selected_role.get("description", ""),
                    key=f"desc_{selected_role_id}"
                )

                # 收入类型选择
                st.markdown("**选择收入类型：**")
                current_income_types = selected_role.get("income_types", ["skill_salary", "ladder_bonus"])
                edit_income_types = []
                cols = st.columns(3)
                for i, (type_id, type_name) in enumerate(INCOME_TYPE_OPTIONS.items()):
                    with cols[i % 3]:
                        if st.checkbox(type_name, key=f"edit_income_{selected_role_id}_{type_id}",
                                       value=(type_id in current_income_types)):
                            edit_income_types.append(type_id)

                # 收入配置
                current_settings = selected_role.get("settings", {})
                edit_settings = {}

                if "order_bonus" in edit_income_types:
                    edit_settings["order_bonus_per_unit"] = st.number_input(
                        "开单奖励单价（元/单）",
                        min_value=0.0,
                        value=float(current_settings.get("order_bonus_per_unit", 2.0)),
                        key=f"order_bonus_{selected_role_id}"
                    )
                if "management_allowance" in edit_income_types:
                    edit_settings["management_allowance"] = st.number_input(
                        "管理津贴（元/月）",
                        min_value=0.0,
                        value=float(current_settings.get("management_allowance", 500.0)),
                        key=f"mgmt_allowance_{selected_role_id}"
                    )
                if "revenue_commission" in edit_income_types:
                    edit_settings["commission_rate"] = st.number_input(
                        "业绩提成比例",
                        min_value=0.0,
                        max_value=1.0,
                        value=float(current_settings.get("commission_rate", 0.01)),
                        step=0.001,
                        format="%.3f",
                        key=f"commission_{selected_role_id}"
                    )

                # 操作按钮
                col1, col2 = st.columns(2)
                with col1:
                    save_clicked = st.form_submit_button("保存修改", type="primary")
                with col2:
                    delete_clicked = st.form_submit_button("删除角色")

            if save_clicked:
                if not edit_income_types:
                    edit_income_types = ["skill_salary", "ladder_bonus"]
                updates = {
                    "name": edit_name,
                    "description": edit_desc,
                    "threshold_multiplier": edit_multiplier,
                    "income_types": edit_income_types,
                    "settings": edit_settings
                }
                if update_role(selected_role_id, updates):
                    st.success(f"已保存修改: {edit_name}")
                    st.rerun()
                else:
                    st.error("保存失败")

            if delete_clicked:
                if delete_role(selected_role_id):
                    st.success("删除成功")
                    st.rerun()
                else:
                    st.error("删除失败")
        else:
            st.info("暂无角色可编辑")

    st.markdown("---")

    # 角色列表
    st.subheader("角色列表")

    if not roles:
        st.info("暂无角色数据，请添加角色")
        return

    # 转换为DataFrame显示
    df_data = []
    for role in roles:
        income_types = role.get("income_types", [])
        income_names = [INCOME_TYPE_OPTIONS.get(t, t) for t in income_types]
        settings = role.get("settings", {})

        # 构建配置说明
        config_parts = []
        if settings.get("order_bonus_per_unit"):
            config_parts.append(f"开单{settings['order_bonus_per_unit']}元/单")
        if settings.get("management_allowance"):
            config_parts.append(f"津贴{settings['management_allowance']}元")
        if settings.get("commission_rate"):
            config_parts.append(f"提成{settings['commission_rate']*100:.1f}%")

        df_data.append({
            "角色名称": role["name"],
            "达标线倍率": f"{role.get('threshold_multiplier', 1.0):.1f}x",
            "收入类型": "、".join(income_names),
            "配置": "、".join(config_parts) if config_parts else "-",
            "描述": role.get("description", "-")
        })

    df = pd.DataFrame(df_data)
    st.table(df)

    # 达标线说明
    st.markdown("---")
    st.subheader("📌 达标线说明")
    st.markdown("""
    - **达标线倍率**：相对于区域默认达标线的倍率
    - 例如：印前区域达标线是 30000，倍率 0.4 表示该角色达标线为 12000
    - **收入类型**：该角色可获得的收入种类
    - 配置优先级：**员工自定义 > 角色配置 > 区域默认**
    """)
