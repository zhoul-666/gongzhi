"""
外部数据导入页面 - 导入营业额、开单量等数据
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.data_manager import (
    get_employees, get_external_data, save_external_data,
    load_json, save_json
)


def render():
    st.title("📊 外部数据导入")
    st.markdown("导入门店营业额、开单量等数据，用于计算额外收入")
    st.markdown("---")

    # 期间选择
    col1, col2 = st.columns([1, 2])
    with col1:
        current_month = datetime.now().strftime("%Y-%m")
        month = st.text_input("数据期间", value=current_month, help="格式：YYYY-MM")

    # 选择数据类型
    st.subheader("📥 数据录入方式")

    tab1, tab2, tab3 = st.tabs(["手动录入", "Excel导入", "门店营业额"])

    # Tab 1: 手动录入
    with tab1:
        st.markdown("### 员工外部数据录入")

        employees = get_employees()
        if not employees:
            st.warning("暂无员工数据")
            return

        # 获取已有数据
        existing_data = get_external_data(month)
        existing_map = {d["employee_id"]: d for d in existing_data}

        # 显示录入表格
        st.markdown("输入员工的开单量、关联门店等数据：")

        with st.form("manual_input_form"):
            data_rows = []

            for emp in employees:
                emp_id = emp["id"]
                emp_name = emp["name"]
                existing = existing_map.get(emp_id, {})

                cols = st.columns([2, 2, 2, 2])

                with cols[0]:
                    st.text(emp_name)

                with cols[1]:
                    order_count = st.number_input(
                        "开单数",
                        min_value=0,
                        value=int(existing.get("order_count", 0)),
                        key=f"order_{emp_id}",
                        label_visibility="collapsed"
                    )

                with cols[2]:
                    store_revenue = st.number_input(
                        "关联营业额",
                        min_value=0.0,
                        value=float(existing.get("store_revenue", 0)),
                        key=f"revenue_{emp_id}",
                        label_visibility="collapsed"
                    )

                with cols[3]:
                    store_id = st.text_input(
                        "门店",
                        value=existing.get("store_id", ""),
                        key=f"store_{emp_id}",
                        label_visibility="collapsed",
                        placeholder="门店ID"
                    )

                data_rows.append({
                    "employee_id": emp_id,
                    "employee_name": emp_name,
                    "month": month,
                    "order_count": order_count,
                    "store_revenue": store_revenue,
                    "store_id": store_id
                })

            # 表头说明
            st.markdown("---")
            st.caption("列说明：员工姓名 | 开单数量 | 关联营业额 | 所属门店")

            if st.form_submit_button("保存数据", type="primary"):
                # 过滤有数据的行
                valid_rows = [r for r in data_rows if r["order_count"] > 0 or r["store_revenue"] > 0]

                if valid_rows:
                    save_external_data(valid_rows, month)
                    st.success(f"已保存 {len(valid_rows)} 条记录")
                    st.rerun()
                else:
                    st.warning("没有有效数据需要保存")

    # Tab 2: Excel导入
    with tab2:
        st.markdown("### Excel 批量导入")

        st.markdown("""
        **Excel格式要求：**
        - 第1列：员工姓名或工号
        - 第2列：开单数量
        - 第3列：关联营业额（可选）
        - 第4列：门店ID（可选）
        """)

        uploaded_file = st.file_uploader("选择Excel文件", type=["xlsx", "xls"])

        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.dataframe(df.head(10))

                # 列映射
                st.markdown("### 列映射")
                cols = df.columns.tolist()

                col1, col2 = st.columns(2)
                with col1:
                    name_col = st.selectbox("员工姓名/工号列", options=cols)
                    order_col = st.selectbox("开单数量列", options=["不导入"] + cols)
                with col2:
                    revenue_col = st.selectbox("营业额列", options=["不导入"] + cols)
                    store_col = st.selectbox("门店列", options=["不导入"] + cols)

                if st.button("执行导入", type="primary"):
                    employees = get_employees()
                    emp_name_map = {e["name"]: e["id"] for e in employees}
                    emp_no_map = {e.get("employee_no", ""): e["id"] for e in employees}

                    imported = []
                    skipped = []

                    for _, row in df.iterrows():
                        name_or_no = str(row[name_col]).strip()

                        # 匹配员工
                        emp_id = emp_name_map.get(name_or_no) or emp_no_map.get(name_or_no)

                        if not emp_id:
                            skipped.append(name_or_no)
                            continue

                        record = {
                            "employee_id": emp_id,
                            "employee_name": name_or_no,
                            "month": month,
                            "order_count": int(row[order_col]) if order_col != "不导入" else 0,
                            "store_revenue": float(row[revenue_col]) if revenue_col != "不导入" else 0,
                            "store_id": str(row[store_col]) if store_col != "不导入" else ""
                        }
                        imported.append(record)

                    if imported:
                        save_external_data(imported, month)
                        st.success(f"成功导入 {len(imported)} 条记录")

                    if skipped:
                        st.warning(f"跳过 {len(skipped)} 条未匹配记录：{', '.join(skipped[:5])}...")

            except Exception as e:
                st.error(f"读取文件失败：{e}")

    # Tab 3: 门店营业额
    with tab3:
        st.markdown("### 门店营业额录入")

        # 获取门店列表
        ext_data = load_json("external_data.json")
        stores = ext_data.get("stores", [])

        if not stores:
            st.info("暂无门店配置，请先在下方添加门店")

        # 添加门店
        with st.expander("➕ 添加门店", expanded=not stores):
            col1, col2 = st.columns(2)
            with col1:
                new_store_name = st.text_input("门店名称", key="new_store_name")
            with col2:
                new_store_desc = st.text_input("门店描述", key="new_store_desc")

            if st.button("添加门店"):
                if new_store_name:
                    new_store = {
                        "id": f"store_{len(stores)+1:03d}",
                        "name": new_store_name,
                        "description": new_store_desc
                    }
                    stores.append(new_store)
                    ext_data["stores"] = stores
                    save_json("external_data.json", ext_data, backup=False)
                    st.success(f"已添加门店：{new_store_name}")
                    st.rerun()

        # 门店营业额录入
        if stores:
            st.markdown("### 录入门店营业额")

            # 获取已有的门店营业额数据
            store_revenue_data = ext_data.get("store_revenues", {}).get(month, {})

            with st.form("store_revenue_form"):
                store_revenues = {}

                for store in stores:
                    store_id = store["id"]
                    store_name = store["name"]

                    col1, col2 = st.columns([2, 3])
                    with col1:
                        st.text(store_name)
                    with col2:
                        revenue = st.number_input(
                            "营业额",
                            min_value=0.0,
                            value=float(store_revenue_data.get(store_id, 0)),
                            key=f"store_rev_{store_id}",
                            label_visibility="collapsed"
                        )
                        store_revenues[store_id] = revenue

                if st.form_submit_button("保存门店营业额", type="primary"):
                    if "store_revenues" not in ext_data:
                        ext_data["store_revenues"] = {}
                    ext_data["store_revenues"][month] = store_revenues
                    save_json("external_data.json", ext_data, backup=False)
                    st.success("门店营业额已保存")

    # 显示已有数据
    st.markdown("---")
    st.subheader("📋 已导入数据")

    existing_data = get_external_data(month)
    if existing_data:
        df_data = []
        for record in existing_data:
            df_data.append({
                "员工": record.get("employee_name", record.get("employee_id")),
                "开单数": record.get("order_count", 0),
                "关联营业额": f"¥{record.get('store_revenue', 0):,.0f}",
                "门店": record.get("store_id", "-")
            })

        df = pd.DataFrame(df_data)
        st.table(df)

        # 删除按钮
        if st.button("清空本期数据", type="secondary"):
            save_external_data([], month)
            st.success("已清空")
            st.rerun()
    else:
        st.info(f"{month} 暂无外部数据")
