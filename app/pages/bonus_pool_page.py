"""
奖金池管理页面 - 配置排名奖金分配规则
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.data_manager import (
    get_bonus_pools, add_bonus_pool, update_bonus_pool, delete_bonus_pool,
    get_roles, load_json, save_json
)

# 排名依据选项
RANKING_BASIS_OPTIONS = {
    "total_score": "绩效总分",
    "total_salary": "工资总额",
    "region_001": "印前绩效",
    "region_002": "印中绩效",
    "region_003": "印后绩效"
}


def render():
    st.title("🏆 奖金池管理")
    st.markdown("配置排名奖金分配规则")
    st.markdown("---")

    # 获取数据
    pools = get_bonus_pools()
    roles = get_roles()
    role_options = {"": "全部角色"} | {r["id"]: r["name"] for r in roles}

    # 添加奖金池
    with st.expander("➕ 添加奖金池", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            new_name = st.text_input("奖金池名称", key="new_pool_name", placeholder="如：月度绩效排名奖")
        with col2:
            new_amount = st.number_input("奖金总额", min_value=0.0, value=1000.0, key="new_pool_amount")

        col1, col2 = st.columns(2)
        with col1:
            new_basis = st.selectbox(
                "排名依据",
                options=list(RANKING_BASIS_OPTIONS.keys()),
                format_func=lambda x: RANKING_BASIS_OPTIONS.get(x, x),
                key="new_pool_basis"
            )
        with col2:
            new_filter_role = st.selectbox(
                "限定角色",
                options=list(role_options.keys()),
                format_func=lambda x: role_options.get(x, "全部"),
                key="new_pool_filter",
                help="只有该角色的员工参与排名"
            )

        new_desc = st.text_input("描述", key="new_pool_desc")

        # 分配规则
        st.markdown("**分配规则：**")
        st.caption("配置每个排名获得的奖金金额")

        new_rules = []
        for i in range(1, 6):  # 默认配置前5名
            cols = st.columns([1, 2, 3])
            with cols[0]:
                st.text(f"第{i}名")
            with cols[1]:
                amount = st.number_input(
                    "金额",
                    min_value=0.0,
                    value=0.0,
                    key=f"new_rule_{i}",
                    label_visibility="collapsed"
                )
            with cols[2]:
                desc = st.text_input(
                    "说明",
                    key=f"new_rule_desc_{i}",
                    label_visibility="collapsed",
                    placeholder="如：冠军"
                )

            if amount > 0:
                new_rules.append({
                    "rank": i,
                    "amount": amount,
                    "description": desc or f"第{i}名"
                })

        if st.button("添加奖金池", type="primary"):
            if new_name and new_rules:
                result = add_bonus_pool(
                    name=new_name,
                    total_amount=new_amount,
                    distribution_rules=new_rules
                )
                if result:
                    # 更新额外配置
                    data = load_json("bonus_pools.json")
                    for pool in data.get("pools", []):
                        if pool["id"] == result["id"]:
                            pool["description"] = new_desc
                            pool["ranking_basis"] = new_basis
                            pool["filter_roles"] = [new_filter_role] if new_filter_role else []
                            pool["enabled"] = True
                    save_json("bonus_pools.json", data, backup=False)

                    st.success(f"添加成功：{new_name}")
                    st.rerun()
            else:
                st.error("请输入名称并配置至少一个分配规则")

    # 编辑奖金池
    with st.expander("✏️ 编辑奖金池", expanded=False):
        if pools:
            pool_labels = [f"{p['name']} (¥{p.get('total_amount', 0):,.0f})" for p in pools]

            selected_label = st.selectbox(
                "选择奖金池",
                options=pool_labels,
                key="pool_selector"
            )

            selected_idx = pool_labels.index(selected_label)
            selected_pool = pools[selected_idx]
            selected_pool_id = selected_pool["id"]

            with st.form(key=f"form_{selected_pool_id}"):
                col1, col2 = st.columns(2)

                with col1:
                    edit_name = st.text_input(
                        "奖金池名称",
                        value=selected_pool["name"],
                        key=f"name_{selected_pool_id}"
                    )
                with col2:
                    edit_amount = st.number_input(
                        "奖金总额",
                        min_value=0.0,
                        value=float(selected_pool.get("total_amount", 0)),
                        key=f"amount_{selected_pool_id}"
                    )

                col1, col2 = st.columns(2)
                with col1:
                    basis_keys = list(RANKING_BASIS_OPTIONS.keys())
                    current_basis = selected_pool.get("ranking_basis", "total_score")
                    current_idx = basis_keys.index(current_basis) if current_basis in basis_keys else 0

                    edit_basis = st.selectbox(
                        "排名依据",
                        options=basis_keys,
                        index=current_idx,
                        format_func=lambda x: RANKING_BASIS_OPTIONS.get(x, x),
                        key=f"basis_{selected_pool_id}"
                    )

                with col2:
                    role_keys = list(role_options.keys())
                    current_filter = selected_pool.get("filter_roles", [])
                    current_filter_id = current_filter[0] if current_filter else ""
                    current_filter_idx = role_keys.index(current_filter_id) if current_filter_id in role_keys else 0

                    edit_filter = st.selectbox(
                        "限定角色",
                        options=role_keys,
                        index=current_filter_idx,
                        format_func=lambda x: role_options.get(x, "全部"),
                        key=f"filter_{selected_pool_id}"
                    )

                edit_desc = st.text_input(
                    "描述",
                    value=selected_pool.get("description", ""),
                    key=f"desc_{selected_pool_id}"
                )

                edit_enabled = st.checkbox(
                    "启用",
                    value=selected_pool.get("enabled", True),
                    key=f"enabled_{selected_pool_id}"
                )

                # 分配规则编辑
                st.markdown("**分配规则：**")
                current_rules = selected_pool.get("distribution_rules", [])

                edit_rules = []
                for i in range(1, 11):  # 支持前10名
                    existing_rule = next((r for r in current_rules if r.get("rank") == i), None)

                    cols = st.columns([1, 2, 3])
                    with cols[0]:
                        st.text(f"第{i}名")
                    with cols[1]:
                        amount = st.number_input(
                            "金额",
                            min_value=0.0,
                            value=float(existing_rule.get("amount", 0)) if existing_rule else 0.0,
                            key=f"edit_rule_{selected_pool_id}_{i}",
                            label_visibility="collapsed"
                        )
                    with cols[2]:
                        desc = st.text_input(
                            "说明",
                            value=existing_rule.get("description", "") if existing_rule else "",
                            key=f"edit_rule_desc_{selected_pool_id}_{i}",
                            label_visibility="collapsed"
                        )

                    if amount > 0:
                        edit_rules.append({
                            "rank": i,
                            "amount": amount,
                            "description": desc or f"第{i}名"
                        })

                # 操作按钮
                col1, col2 = st.columns(2)
                with col1:
                    save_clicked = st.form_submit_button("保存修改", type="primary")
                with col2:
                    delete_clicked = st.form_submit_button("删除奖金池")

            if save_clicked:
                updates = {
                    "name": edit_name,
                    "total_amount": edit_amount,
                    "description": edit_desc,
                    "ranking_basis": edit_basis,
                    "filter_roles": [edit_filter] if edit_filter else [],
                    "distribution_rules": edit_rules,
                    "enabled": edit_enabled
                }
                if update_bonus_pool(selected_pool_id, updates):
                    st.success(f"已保存修改: {edit_name}")
                    st.rerun()
                else:
                    st.error("保存失败")

            if delete_clicked:
                if delete_bonus_pool(selected_pool_id):
                    st.success("删除成功")
                    st.rerun()
                else:
                    st.error("删除失败")
        else:
            st.info("暂无奖金池可编辑")

    st.markdown("---")

    # 奖金池列表
    st.subheader("奖金池列表")

    if not pools:
        st.info("暂无奖金池配置，请添加")
        return

    # 转换为表格显示
    df_data = []
    for pool in pools:
        rules = pool.get("distribution_rules", [])
        rules_str = ", ".join([f"第{r['rank']}名:{r['amount']}元" for r in rules[:3]])
        if len(rules) > 3:
            rules_str += f" ... 共{len(rules)}名"

        filter_roles = pool.get("filter_roles", [])
        filter_str = ", ".join([role_options.get(r, r) for r in filter_roles]) if filter_roles else "全部"

        df_data.append({
            "名称": pool["name"],
            "总额": f"¥{pool.get('total_amount', 0):,.0f}",
            "排名依据": RANKING_BASIS_OPTIONS.get(pool.get("ranking_basis", "total_score"), "-"),
            "限定角色": filter_str,
            "分配规则": rules_str,
            "状态": "✅ 启用" if pool.get("enabled", True) else "⏸️ 停用"
        })

    df = pd.DataFrame(df_data)
    st.table(df)

    # 说明
    st.markdown("---")
    st.subheader("📌 使用说明")
    st.markdown("""
    1. **排名依据**：选择用什么指标来排名员工
    2. **限定角色**：只有该角色的员工参与排名，留空表示全部员工参与
    3. **分配规则**：配置每个排名获得的具体金额
    4. 奖金池会在绩效计算时自动应用
    """)
