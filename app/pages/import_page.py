"""
绩效导入页面 - 从ERP导入绩效数据
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.data_manager import (
    get_employees, add_employee, get_regions,
    save_json, load_json
)


def parse_erp_excel(uploaded_file):
    """解析ERP导出的Excel文件"""
    try:
        # 尝试不同的读取方式
        try:
            # 先尝试HTML格式（ERP常用）
            dfs = pd.read_html(uploaded_file)
            if dfs:
                df = dfs[0]
                print("[读取] 使用HTML格式解析成功")
            else:
                raise ValueError("无法解析HTML")
        except:
            try:
                # 尝试xlsx格式
                df = pd.read_excel(uploaded_file, engine='openpyxl')
                print("[读取] 使用openpyxl解析成功")
            except:
                try:
                    # 尝试xls格式
                    df = pd.read_excel(uploaded_file, engine='xlrd')
                    print("[读取] 使用xlrd解析成功")
                except Exception as e:
                    return None, f"无法解析文件格式: {e}"

        return df, None
    except Exception as e:
        return None, f"解析失败: {e}"


def render():
    st.title("📥 绩效导入")
    st.markdown("---")

    # 获取区域配置
    regions = get_regions()
    region_columns = {r["erp_column"]: r for r in regions if r.get("erp_column")}

    st.markdown("""
    ### 使用说明
    1. 从ERP系统导出绩效统计Excel文件
    2. 上传文件，系统会自动识别员工和绩效数据
    3. 新员工会自动创建，已有员工会匹配更新
    """)

    # 显示当前配置的ERP列名
    with st.expander("当前区域-ERP列名映射"):
        for region in regions:
            col = region.get("erp_column", "未配置")
            st.text(f"{region['name']} → {col or '未配置'}")

    st.markdown("---")

    # 文件上传
    uploaded_file = st.file_uploader(
        "上传ERP绩效文件",
        type=['xls', 'xlsx'],
        help="支持.xls和.xlsx格式"
    )

    if uploaded_file:
        st.success(f"已上传: {uploaded_file.name}")

        # 解析文件
        with st.spinner("正在解析文件..."):
            df, error = parse_erp_excel(uploaded_file)

        if error:
            st.error(error)
            return

        if df is None or df.empty:
            st.error("文件为空或无法解析")
            return

        # 显示数据预览
        st.subheader("数据预览")
        st.dataframe(df.head(10), use_container_width=True)
        st.caption(f"共 {len(df)} 行数据")

        # 列名映射
        st.subheader("列名映射")

        columns = df.columns.tolist()

        col1, col2 = st.columns(2)

        with col1:
            # 员工姓名列
            name_col_options = ["自动识别"] + columns
            name_col_default = 0

            # 尝试自动匹配
            for i, col in enumerate(columns):
                if "人员" in str(col) or "姓名" in str(col) or "员工" in str(col):
                    name_col_default = i + 1
                    break

            name_column = st.selectbox(
                "员工姓名列",
                options=name_col_options,
                index=name_col_default,
                key="name_col"
            )

        with col2:
            # 选择月份
            current_month = datetime.now().strftime("%Y-%m")
            import_month = st.text_input(
                "导入月份",
                value=current_month,
                help="格式: YYYY-MM"
            )

        # 绩效分值列映射
        st.markdown("**绩效分值列映射：**")

        score_mapping = {}
        cols = st.columns(len(regions))

        for i, region in enumerate(regions):
            with cols[i]:
                # 尝试自动匹配
                default_idx = 0
                erp_col = region.get("erp_column", "")
                for j, col in enumerate(columns):
                    if erp_col and erp_col in str(col):
                        default_idx = j + 1
                        break

                selected = st.selectbox(
                    f"{region['name']}",
                    options=["不导入"] + columns,
                    index=default_idx,
                    key=f"region_col_{region['id']}"
                )

                if selected != "不导入":
                    score_mapping[region["id"]] = selected

        st.markdown("---")

        # 导入按钮
        if st.button("🚀 开始导入", type="primary"):
            # 确定员工姓名列
            if name_column == "自动识别":
                # 尝试自动识别
                for col in columns:
                    if "人员" in str(col) or "姓名" in str(col) or "员工" in str(col):
                        name_column = col
                        break
                else:
                    st.error("无法自动识别员工姓名列，请手动选择")
                    return

            if not score_mapping:
                st.error("请至少映射一个绩效分值列")
                return

            # 开始导入
            with st.spinner("正在导入数据..."):
                import_result = do_import(df, name_column, score_mapping, import_month, regions)

            if import_result["success"]:
                st.success(f"""
                导入完成！
                - 新增员工: {import_result['new_employees']} 人
                - 更新记录: {import_result['updated_records']} 条
                - 导入月份: {import_month}
                """)

                # 显示导入详情
                with st.expander("查看导入详情"):
                    if import_result.get("details"):
                        detail_df = pd.DataFrame(import_result["details"])
                        st.dataframe(detail_df, use_container_width=True)
            else:
                st.error(f"导入失败: {import_result.get('error', '未知错误')}")


def do_import(df, name_column, score_mapping, import_month, regions):
    """执行导入操作"""
    try:
        employees = get_employees()
        emp_name_map = {e["name"]: e for e in employees}

        # 加载绩效数据
        perf_data = load_json("performance.json")
        if not perf_data:
            perf_data = {"records": [], "imports": []}

        records = perf_data.get("records", [])
        imports = perf_data.get("imports", [])

        new_employees = 0
        updated_records = 0
        details = []

        region_map = {r["id"]: r["name"] for r in regions}

        for idx, row in df.iterrows():
            name = str(row[name_column]).strip()

            if not name or name == "nan" or name == "NaN":
                continue

            # 查找或创建员工
            if name in emp_name_map:
                emp = emp_name_map[name]
            else:
                # 新增员工
                emp = add_employee(name, None, "mode_002")  # 默认中央工厂
                emp_name_map[name] = emp
                new_employees += 1

            # 提取绩效分值
            scores = {}
            for region_id, col_name in score_mapping.items():
                try:
                    value = row[col_name]
                    if pd.notna(value):
                        scores[region_id] = float(value)
                    else:
                        scores[region_id] = 0
                except:
                    scores[region_id] = 0

            # 创建或更新记录
            record = {
                "employee_id": emp["id"],
                "employee_name": name,
                "month": import_month,
                "scores": scores,
                "imported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # 检查是否已存在该月记录
            existing_idx = None
            for i, r in enumerate(records):
                if r["employee_id"] == emp["id"] and r["month"] == import_month:
                    existing_idx = i
                    break

            if existing_idx is not None:
                records[existing_idx] = record
            else:
                records.append(record)

            updated_records += 1

            # 记录详情
            detail = {"姓名": name, "状态": "新增" if name not in emp_name_map else "更新"}
            for region_id, score in scores.items():
                detail[region_map.get(region_id, region_id)] = f"{score:,.0f}"
            details.append(detail)

        # 记录导入历史
        imports.append({
            "month": import_month,
            "imported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "record_count": updated_records,
            "new_employees": new_employees
        })

        perf_data["records"] = records
        perf_data["imports"] = imports

        save_json("performance.json", perf_data)

        return {
            "success": True,
            "new_employees": new_employees,
            "updated_records": updated_records,
            "details": details
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
