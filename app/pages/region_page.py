"""
大区域管理页面 - 含阶梯规则配置
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.data_manager import get_regions, update_region, add_region, save_json, load_json


def render():
    st.title("🗺️ 大区域管理")
    st.markdown("---")

    regions = get_regions()

    # 添加新区域
    with st.expander("➕ 添加新区域", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("区域名称", key="new_region_name")
        with col2:
            new_column = st.text_input("对应ERP列名（可选）", key="new_region_column")

        if st.button("添加区域", type="primary"):
            if new_name:
                result = add_region(new_name, new_column or None)
                if result:
                    st.success(f"添加成功：{new_name}")
                    st.rerun()
            else:
                st.error("请输入区域名称")

    st.markdown("---")

    # 区域列表和配置
    if not regions:
        st.info("暂无区域数据")
        return

    # 选择要配置的区域
    region_options = {r["id"]: r["name"] for r in regions}
    region_names = [r["name"] for r in regions]

    selected_region_name = st.segmented_control(
        "选择区域进行配置",
        options=region_names,
        default=region_names[0] if region_names else None,
        key="select_region"
    )

    # 根据名称找到对应的ID
    selected_region_id = next(
        (r["id"] for r in regions if r["name"] == selected_region_name),
        regions[0]["id"] if regions else None
    )

    selected_region = next((r for r in regions if r["id"] == selected_region_id), None)

    if selected_region:
        st.subheader(f"配置：{selected_region['name']}")

        # 基本信息
        col1, col2 = st.columns(2)
        with col1:
            erp_column = st.text_input(
                "对应ERP列名",
                value=selected_region.get("erp_column", "") or "",
                key="edit_erp_column",
                help="导入绩效时匹配的Excel列名"
            )
        with col2:
            threshold = st.number_input(
                "达标值（判断在岗）",
                value=selected_region.get("threshold", 30000),
                min_value=0,
                step=10000,
                key="edit_threshold",
                help="绩效分达到此值算在岗"
            )

        st.markdown("---")

        # 阶梯规则配置
        st.subheader("阶梯规则配置")
        st.caption("按绩效分区间设置奖金金额")

        ladder_rules = selected_region.get("ladder_rules", [])

        # 显示现有规则
        if ladder_rules:
            st.markdown("**当前规则：**")

            # 使用表格编辑
            rules_data = []
            for i, rule in enumerate(ladder_rules):
                rules_data.append({
                    "序号": i + 1,
                    "最小值": rule.get("min", 0),
                    "最大值": rule.get("max", 0),
                    "奖金": rule.get("bonus", 0),
                    "说明": rule.get("description", "")
                })

            df = pd.DataFrame(rules_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

        # 编辑规则
        st.markdown("**编辑阶梯规则：**")

        # 使用session_state管理编辑状态
        if f"editing_rules_{selected_region_id}" not in st.session_state:
            st.session_state[f"editing_rules_{selected_region_id}"] = ladder_rules.copy()

        editing_rules = st.session_state[f"editing_rules_{selected_region_id}"]

        # 显示每条规则的编辑器
        rules_to_delete = []
        for i, rule in enumerate(editing_rules):
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 3, 1])

            with col1:
                new_min = st.number_input(
                    "从",
                    value=rule.get("min", 0),
                    min_value=0,
                    step=10000,
                    key=f"rule_min_{selected_region_id}_{i}"
                )
                editing_rules[i]["min"] = new_min

            with col2:
                new_max = st.number_input(
                    "到",
                    value=rule.get("max", 0),
                    min_value=0,
                    step=10000,
                    key=f"rule_max_{selected_region_id}_{i}"
                )
                editing_rules[i]["max"] = new_max

            with col3:
                new_bonus = st.number_input(
                    "奖金",
                    value=rule.get("bonus", 0),
                    min_value=0,
                    step=50,
                    key=f"rule_bonus_{selected_region_id}_{i}"
                )
                editing_rules[i]["bonus"] = new_bonus

            with col4:
                new_desc = st.text_input(
                    "说明",
                    value=rule.get("description", ""),
                    key=f"rule_desc_{selected_region_id}_{i}"
                )
                editing_rules[i]["description"] = new_desc

            with col5:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_rule_{selected_region_id}_{i}"):
                    rules_to_delete.append(i)

        # 删除标记的规则
        if rules_to_delete:
            for idx in sorted(rules_to_delete, reverse=True):
                editing_rules.pop(idx)
            st.rerun()

        # 添加新规则
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("➕ 添加规则"):
                last_max = editing_rules[-1]["max"] if editing_rules else 0
                editing_rules.append({
                    "min": last_max,
                    "max": last_max + 100000,
                    "bonus": 100,
                    "description": ""
                })
                st.rerun()

        st.markdown("---")

        # 保存按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 保存所有修改", type="primary"):
                updates = {
                    "erp_column": erp_column or None,
                    "threshold": threshold,
                    "ladder_rules": editing_rules
                }

                if update_region(selected_region_id, updates):
                    st.success("保存成功！")
                    # 清除编辑状态
                    del st.session_state[f"editing_rules_{selected_region_id}"]
                    st.rerun()
                else:
                    st.error("保存失败")

        with col2:
            if st.button("🔄 重置修改"):
                del st.session_state[f"editing_rules_{selected_region_id}"]
                st.rerun()

    # 显示所有区域概览
    st.markdown("---")
    st.subheader("区域概览")

    overview_data = []
    for r in regions:
        overview_data.append({
            "区域名称": r["name"],
            "ERP列名": r.get("erp_column", "") or "-",
            "达标值": f"{r.get('threshold', 0):,}",
            "阶梯级数": len(r.get("ladder_rules", []))
        })

    df = pd.DataFrame(overview_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
