"""
绩效导入页面 - 从ERP导入明细数据并自动汇总
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
    """解析ERP导出的Excel文件（支持HTML格式）"""
    try:
        # 尝试不同的读取方式
        try:
            # 先尝试HTML格式（ERP常用）
            dfs = pd.read_html(uploaded_file)
            if dfs:
                df = dfs[0]
            else:
                raise ValueError("无法解析HTML")
        except:
            try:
                # 尝试xlsx格式
                df = pd.read_excel(uploaded_file, engine='openpyxl')
            except:
                try:
                    # 尝试xls格式
                    df = pd.read_excel(uploaded_file, engine='xlrd')
                except Exception as e:
                    return None, f"无法解析文件格式: {e}"

        return df, None
    except Exception as e:
        return None, f"解析失败: {e}"


def summarize_performance(df, period):
    """
    汇总绩效数据

    按姓名分组，汇总：
    - 印前 = 工序"印前处理"的绩效分合计
    - 图纸印中 = 工序"印中制作" + 业务类别为"蓝图"或"工程图纸"
    - 数码印中 = 工序"印中制作" + 其他业务类别
    - 印后 = 工序"印后加工"的绩效分合计
    """
    # 确保必要的列存在
    required_cols = ['姓名', '工序', '业务类别', '绩效分']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return None, f"缺少必要的列: {', '.join(missing_cols)}"

    # 获取所有员工姓名
    employees = df['姓名'].unique().tolist()

    summary = []
    raw_details = []  # 保存原始明细用于穿透查询

    for emp_name in employees:
        if not emp_name or pd.isna(emp_name) or str(emp_name).strip() == '':
            continue

        emp_name = str(emp_name).strip()
        emp_df = df[df['姓名'] == emp_name]

        # 汇总各工序绩效分
        # 印前
        pre_press = emp_df[emp_df['工序'] == '印前处理']['绩效分'].sum()

        # 印中 - 需要细分
        mid_press_df = emp_df[emp_df['工序'] == '印中制作']
        # 图纸印中：蓝图、工程图纸
        drawing_mid = mid_press_df[mid_press_df['业务类别'].isin(['蓝图', '工程图纸'])]['绩效分'].sum()
        # 数码印中：其他业务类别
        digital_mid = mid_press_df[~mid_press_df['业务类别'].isin(['蓝图', '工程图纸'])]['绩效分'].sum()

        # 印后
        post_press = emp_df[emp_df['工序'] == '印后加工']['绩效分'].sum()

        # 汇总记录
        summary.append({
            'employee_name': emp_name,
            'period': period,
            'pre_press': float(pre_press),           # 印前
            'drawing_mid': float(drawing_mid),       # 图纸印中
            'digital_mid': float(digital_mid),       # 数码印中
            'mid_press': float(drawing_mid + digital_mid),  # 印中合计
            'post_press': float(post_press),         # 印后
        })

        # 保存原始明细
        for _, row in emp_df.iterrows():
            raw_details.append({
                'period': period,
                'employee_name': emp_name,
                'order_no': str(row.get('订单编号', '')),
                'customer': str(row.get('客户名称', '')),
                'process': str(row.get('工序', '')),
                'business_type': str(row.get('业务类别', '')),
                'item': str(row.get('制作项', '')),
                'quantity': float(row.get('数量', 0)) if pd.notna(row.get('数量')) else 0,
                'score': float(row.get('绩效分', 0)) if pd.notna(row.get('绩效分')) else 0,
                'register_time': str(row.get('登记时间', '')),
            })

    return {
        'summary': summary,
        'raw_details': raw_details
    }, None


def render():
    st.title("📥 绩效导入")
    st.markdown("---")

    st.markdown("""
    ### 使用说明
    1. 从ERP系统导出**绩效明细**Excel文件
    2. 输入导入期间（如 2025-12）
    3. 上传文件，系统会自动：
       - 按员工姓名汇总绩效分
       - 区分印前/图纸印中/数码印中/印后
       - 匹配现有员工或自动创建新员工
    """)

    st.markdown("---")

    # 期间输入
    col1, col2 = st.columns([1, 2])
    with col1:
        current_month = datetime.now().strftime("%Y-%m")
        import_period = st.text_input(
            "导入期间",
            value=current_month,
            help="格式: YYYY-MM，如 2025-12"
        )

    st.markdown("---")

    # 文件上传
    uploaded_file = st.file_uploader(
        "上传ERP绩效明细文件",
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
        st.subheader("原始数据预览")
        st.dataframe(df.head(10), use_container_width=True)
        st.caption(f"共 {len(df)} 条明细记录")

        # 显示列信息
        with st.expander("查看数据列"):
            st.write(df.columns.tolist())

        st.markdown("---")

        # 预览汇总结果
        if st.button("📊 预览汇总结果", type="secondary"):
            with st.spinner("正在汇总数据..."):
                result, error = summarize_performance(df, import_period)

            if error:
                st.error(error)
                return

            summary = result['summary']

            # 显示汇总预览
            st.subheader("汇总预览")

            preview_data = []
            for item in summary:
                preview_data.append({
                    '姓名': item['employee_name'],
                    '期间': item['period'],
                    '印前': f"{item['pre_press']:,.0f}",
                    '图纸印中': f"{item['drawing_mid']:,.0f}",
                    '数码印中': f"{item['digital_mid']:,.0f}",
                    '印中合计': f"{item['mid_press']:,.0f}",
                    '印后': f"{item['post_press']:,.0f}",
                })

            preview_df = pd.DataFrame(preview_data)
            st.dataframe(preview_df, use_container_width=True)
            st.caption(f"共 {len(summary)} 名员工")

            # 保存到session_state供导入使用
            st.session_state['pending_import'] = result
            st.session_state['pending_period'] = import_period

        # 导入按钮
        st.markdown("---")

        if st.button("🚀 确认导入", type="primary"):
            # 检查是否已预览
            if 'pending_import' not in st.session_state:
                # 先执行汇总
                with st.spinner("正在汇总数据..."):
                    result, error = summarize_performance(df, import_period)

                if error:
                    st.error(error)
                    return
            else:
                result = st.session_state['pending_import']
                # 更新期间（以防用户修改了）
                if st.session_state.get('pending_period') != import_period:
                    # 期间变了，重新汇总
                    with st.spinner("正在汇总数据..."):
                        result, error = summarize_performance(df, import_period)
                    if error:
                        st.error(error)
                        return

            # 开始导入
            with st.spinner("正在导入数据..."):
                import_result = do_import(result, import_period)

            if import_result["success"]:
                st.success(f"""
                ✅ 导入完成！
                - 导入期间: {import_period}
                - 新增员工: {import_result['new_employees']} 人
                - 导入记录: {import_result['imported_records']} 条
                - 明细记录: {import_result['detail_records']} 条
                """)

                # 清理session_state
                if 'pending_import' in st.session_state:
                    del st.session_state['pending_import']
                if 'pending_period' in st.session_state:
                    del st.session_state['pending_period']

                # 显示导入详情
                with st.expander("查看导入详情"):
                    if import_result.get("details"):
                        detail_df = pd.DataFrame(import_result["details"])
                        st.dataframe(detail_df, use_container_width=True)
            else:
                st.error(f"导入失败: {import_result.get('error', '未知错误')}")


def do_import(result, import_period):
    """执行导入操作"""
    try:
        employees = get_employees()
        emp_name_map = {e["name"]: e for e in employees}

        summary = result['summary']
        raw_details = result['raw_details']

        # 加载绩效数据
        perf_data = load_json("performance.json")
        if not perf_data:
            perf_data = {"records": [], "imports": [], "raw_details": []}

        records = perf_data.get("records", [])
        imports = perf_data.get("imports", [])
        existing_raw = perf_data.get("raw_details", [])

        new_employees = 0
        imported_records = 0
        details = []

        # 移除该期间的旧记录
        records = [r for r in records if r.get("period") != import_period]
        existing_raw = [r for r in existing_raw if r.get("period") != import_period]

        for item in summary:
            emp_name = item['employee_name']

            # 查找或创建员工
            if emp_name in emp_name_map:
                emp = emp_name_map[emp_name]
                status = "匹配"
            else:
                # 新增员工
                emp = add_employee(emp_name, None, "mode_002")  # 默认中央工厂
                emp_name_map[emp_name] = emp
                new_employees += 1
                status = "新增"

            # 创建绩效记录（新格式，包含印中细分）
            record = {
                "employee_id": emp["id"],
                "employee_name": emp_name,
                "period": import_period,
                "scores": {
                    "region_001": item['pre_press'],      # 印前
                    "region_002": item['mid_press'],       # 印中合计
                    "region_003": item['post_press'],      # 印后
                    "region_004": 0,                       # 前台（暂无）
                },
                "mid_detail": {
                    "drawing": item['drawing_mid'],        # 图纸印中
                    "digital": item['digital_mid'],        # 数码印中
                },
                "imported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            records.append(record)
            imported_records += 1

            # 记录详情
            details.append({
                "姓名": emp_name,
                "状态": status,
                "印前": f"{item['pre_press']:,.0f}",
                "图纸印中": f"{item['drawing_mid']:,.0f}",
                "数码印中": f"{item['digital_mid']:,.0f}",
                "印中合计": f"{item['mid_press']:,.0f}",
                "印后": f"{item['post_press']:,.0f}",
            })

        # 添加原始明细（用于穿透查询）
        # 为每条明细关联员工ID
        for detail in raw_details:
            emp_name = detail['employee_name']
            if emp_name in emp_name_map:
                detail['employee_id'] = emp_name_map[emp_name]['id']
            existing_raw.append(detail)

        # 记录导入历史
        imports.append({
            "period": import_period,
            "imported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "record_count": imported_records,
            "detail_count": len(raw_details),
            "new_employees": new_employees
        })

        perf_data["records"] = records
        perf_data["imports"] = imports
        perf_data["raw_details"] = existing_raw

        save_json("performance.json", perf_data)

        return {
            "success": True,
            "new_employees": new_employees,
            "imported_records": imported_records,
            "detail_records": len(raw_details),
            "details": details
        }

    except Exception as e:
        import traceback
        return {"success": False, "error": f"{str(e)}\n{traceback.format_exc()}"}
