"""
绩效核算系统 - 主程序入口
版本: 2.0.0

运行方式: streamlit run app/main.py

更新记录:
- 2.0.0: 界面改造 - 首页卡片式导航 + 蓝色活力配色
- 1.1.0: 添加密码保护功能
- 1.0.0: 初始版本
"""
__version__ = "2.0.0"

import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 页面配置
st.set_page_config(
    page_title="绩效核算系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"  # 默认收起侧边栏
)

# ==================== 自定义样式 ====================
def inject_custom_css():
    """注入自定义CSS样式"""
    st.markdown("""
    <style>
    /* 隐藏侧边栏 */
    [data-testid="stSidebar"] {
        display: none;
    }

    /* 主容器样式 */
    .main-header {
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(30, 136, 229, 0.3);
    }

    .main-header h1 {
        margin: 0;
        font-size: 2.5em;
        font-weight: 600;
    }

    .main-header p {
        margin: 10px 0 0 0;
        opacity: 0.9;
        font-size: 1.1em;
    }

    /* 卡片容器 */
    .card-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 20px;
        padding: 20px 0;
    }

    /* 功能卡片 */
    .feature-card {
        background: white;
        border-radius: 15px;
        padding: 30px 25px;
        width: 200px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        cursor: pointer;
        border: 2px solid transparent;
    }

    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(30, 136, 229, 0.25);
        border-color: #1E88E5;
    }

    .feature-card .icon {
        font-size: 3em;
        margin-bottom: 15px;
    }

    .feature-card .title {
        font-size: 1.1em;
        font-weight: 600;
        color: #333;
        margin: 0;
    }

    .feature-card .desc {
        font-size: 0.85em;
        color: #666;
        margin-top: 8px;
    }

    /* 统计卡片 */
    .stat-card {
        background: linear-gradient(135deg, #1E88E5 0%, #1976D2 100%);
        color: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(30, 136, 229, 0.3);
    }

    .stat-card .number {
        font-size: 2.5em;
        font-weight: 700;
        margin: 0;
    }

    .stat-card .label {
        font-size: 0.95em;
        opacity: 0.9;
        margin-top: 5px;
    }

    /* 返回按钮 */
    .back-button {
        background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
        color: white !important;
        border: none;
        padding: 10px 25px;
        border-radius: 25px;
        font-size: 1em;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        text-decoration: none;
        box-shadow: 0 3px 10px rgba(30, 136, 229, 0.3);
        transition: all 0.3s ease;
    }

    .back-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(30, 136, 229, 0.4);
    }

    /* 页面标题样式 */
    .page-title {
        color: #1E88E5;
        border-bottom: 3px solid #1E88E5;
        padding-bottom: 10px;
        margin-bottom: 25px;
    }

    /* 美化按钮 */
    .stButton > button {
        background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 25px;
        font-weight: 500;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(30, 136, 229, 0.4);
    }

    /* 美化输入框 */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 2px solid #E3F2FD;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #1E88E5;
        box-shadow: 0 0 0 3px rgba(30, 136, 229, 0.1);
    }

    /* 美化expander */
    .streamlit-expanderHeader {
        background: #E3F2FD;
        border-radius: 8px;
    }

    /* 美化metric */
    [data-testid="stMetricValue"] {
        color: #1E88E5;
    }

    /* 禁用 selectbox 输入编辑功能 - 只能选择不能输入 */
    div[data-baseweb="select"] input {
        caret-color: transparent !important;
        pointer-events: none !important;
    }

    /* 顶部方案工具栏 - 固定定位 */
    .scheme-toolbar {
        position: fixed;
        top: 60px;
        left: 0;
        right: 0;
        z-index: 999;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-bottom: 2px solid #1E88E5;
        padding: 8px 20px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        gap: 15px;
    }

    .scheme-toolbar .scheme-label {
        font-weight: 600;
        color: #1565C0;
        white-space: nowrap;
    }

    .scheme-toolbar .scheme-name {
        background: white;
        padding: 6px 15px;
        border-radius: 20px;
        border: 2px solid #1E88E5;
        font-weight: 500;
        color: #1565C0;
    }

    .scheme-toolbar .modified-badge {
        background: #ff9800;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: 500;
    }

    /* 为工具栏留出顶部空间 */
    .main-content-with-toolbar {
        padding-top: 60px;
    }

    /* 工具栏按钮样式 */
    .toolbar-btn {
        background: #1E88E5;
        color: white !important;
        border: none;
        padding: 6px 15px;
        border-radius: 6px;
        font-size: 0.9em;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
    }

    .toolbar-btn:hover {
        background: #1565C0;
        transform: translateY(-1px);
    }

    .toolbar-btn-secondary {
        background: white;
        color: #1E88E5 !important;
        border: 2px solid #1E88E5;
    }

    .toolbar-btn-secondary:hover {
        background: #E3F2FD;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== 顶部方案工具栏 ====================
def render_scheme_toolbar():
    """渲染顶部方案工具栏"""
    from app.data_manager import get_active_scheme, get_schemes, is_config_modified, save_as_scheme, update_scheme_snapshot

    # 获取当前方案信息
    active_scheme = get_active_scheme()
    schemes = get_schemes()
    is_modified = is_config_modified()

    # 使用 Streamlit 容器
    toolbar = st.container()

    with toolbar:
        cols = st.columns([1.5, 3, 1, 1, 1, 2])

        with cols[0]:
            st.markdown("**当前方案：**")

        with cols[1]:
            # 方案选择下拉框
            scheme_options = {s["id"]: s["name"] for s in schemes}
            scheme_ids = list(scheme_options.keys())
            scheme_names = list(scheme_options.values())

            current_idx = 0
            if active_scheme:
                try:
                    current_idx = scheme_ids.index(active_scheme["id"])
                except ValueError:
                    current_idx = 0

            # 显示方案名称和修改状态
            display_name = active_scheme["name"] if active_scheme else "无方案"
            if is_modified:
                display_name += " ⚠️已修改"

            selected_name = st.selectbox(
                "方案",
                scheme_names,
                index=current_idx,
                key="scheme_selector",
                label_visibility="collapsed"
            )

            # 处理方案切换
            selected_idx = scheme_names.index(selected_name)
            selected_id = scheme_ids[selected_idx]

            if active_scheme and selected_id != active_scheme["id"]:
                # 切换方案前检查是否有未保存的修改
                if is_modified:
                    st.session_state.pending_scheme_switch = selected_id
                    st.session_state.show_switch_confirm = True
                else:
                    from app.data_manager import load_scheme_to_current
                    load_scheme_to_current(selected_id)
                    st.rerun()

        with cols[2]:
            # 保存按钮
            if st.button("💾 保存", key="toolbar_save", help="保存到当前方案"):
                if active_scheme:
                    update_scheme_snapshot(active_scheme["id"])
                    st.success("已保存!")
                    st.rerun()

        with cols[3]:
            # 另存为按钮
            if st.button("📑 另存为", key="toolbar_save_as", help="另存为新方案"):
                st.session_state.show_save_as_dialog = True

        with cols[4]:
            # 管理方案按钮
            if st.button("⚙️ 管理", key="toolbar_manage", help="管理所有方案"):
                st.session_state.current_page = "scheme"
                st.rerun()

        with cols[5]:
            # 显示修改状态
            if is_modified:
                st.markdown('<span style="color: #ff9800; font-weight: 500;">● 有未保存的修改</span>', unsafe_allow_html=True)

    # 分隔线
    st.markdown("---")

    # 另存为对话框
    if st.session_state.get("show_save_as_dialog"):
        with st.expander("📑 另存为新方案", expanded=True):
            new_name = st.text_input("方案名称", key="new_scheme_name", placeholder="例如：2025年2月测试版")
            new_desc = st.text_input("方案描述（可选）", key="new_scheme_desc", placeholder="简要描述此方案")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("确定保存", key="confirm_save_as"):
                    if new_name:
                        save_as_scheme(new_name, new_desc)
                        st.session_state.show_save_as_dialog = False
                        st.success(f"已保存为：{new_name}")
                        st.rerun()
                    else:
                        st.warning("请输入方案名称")
            with col2:
                if st.button("取消", key="cancel_save_as"):
                    st.session_state.show_save_as_dialog = False
                    st.rerun()

    # 切换确认对话框
    if st.session_state.get("show_switch_confirm"):
        st.warning("⚠️ 当前有未保存的修改，切换方案后将丢失！")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("保存后切换", key="save_then_switch"):
                if active_scheme:
                    update_scheme_snapshot(active_scheme["id"])
                from app.data_manager import load_scheme_to_current
                load_scheme_to_current(st.session_state.pending_scheme_switch)
                st.session_state.show_switch_confirm = False
                st.rerun()
        with col2:
            if st.button("放弃修改并切换", key="discard_and_switch"):
                from app.data_manager import load_scheme_to_current
                load_scheme_to_current(st.session_state.pending_scheme_switch)
                st.session_state.show_switch_confirm = False
                st.rerun()
        with col3:
            if st.button("取消切换", key="cancel_switch"):
                st.session_state.show_switch_confirm = False
                st.rerun()


# ==================== 密码验证 ====================
def check_password():
    """检查用户是否已通过密码验证"""
    try:
        require_password = st.secrets.get("require_password", False)
    except:
        require_password = False

    if not require_password:
        return True

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # 登录界面
    st.markdown("""
    <div class="main-header">
        <h1>🔐 绩效核算系统</h1>
        <p>请输入访问密码</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("密码", type="password", key="password_input")
        if st.button("登录", type="primary", use_container_width=True):
            try:
                correct_password = st.secrets.get("password", "123456")
            except:
                correct_password = "123456"

            if password == correct_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ 密码错误，请重试")

    return False

# ==================== 首页 ====================
def render_home():
    """渲染首页"""
    from app.data_manager import get_employees, get_skills, load_json
    from datetime import datetime

    # 顶部标题
    st.markdown("""
    <div class="main-header">
        <h1>📊 绩效核算系统</h1>
        <p>高效、便捷的绩效工资计算工具</p>
    </div>
    """, unsafe_allow_html=True)

    # 获取数据统计
    employees = get_employees()
    skills = get_skills()
    history = load_json("calculation_history.json")
    calculations = history.get("calculations", []) if history else []
    current_month = datetime.now().strftime("%Y-%m")
    calculated_this_month = any(c.get("month") == current_month for c in calculations)

    # 统计卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <p class="number">{len(employees)}</p>
            <p class="label">👥 员工总数</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <p class="number">{len(skills)}</p>
            <p class="label">🔧 技能总数</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <p class="number">{len(calculations)}</p>
            <p class="label">📜 历史记录</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        status = "✅" if calculated_this_month else "⏳"
        st.markdown(f"""
        <div class="stat-card">
            <p class="number">{status}</p>
            <p class="label">📅 本月核算</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 功能卡片
    st.markdown("### 🚀 功能入口")

    # 第一行：4个卡片
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("👥\n\n员工管理", key="btn_employee", use_container_width=True, help="添加、编辑、删除员工信息"):
            st.session_state.current_page = "employee"
            st.rerun()

    with col2:
        if st.button("🗺️\n\n工作区域", key="btn_region", use_container_width=True, help="配置区域的阶梯规则"):
            st.session_state.current_page = "region"
            st.rerun()

    with col3:
        if st.button("🔧\n\n工作技能", key="btn_skill", use_container_width=True, help="管理技能和工资标准"):
            st.session_state.current_page = "skill"
            st.rerun()

    with col4:
        if st.button("📋\n\n技能指派", key="btn_assignment", use_container_width=True, help="给员工分配技能"):
            st.session_state.current_page = "assignment"
            st.rerun()

    # 第二行：4个卡片
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📥\n\n绩效导入", key="btn_import", use_container_width=True, help="从ERP导入绩效数据"):
            st.session_state.current_page = "import"
            st.rerun()

    with col2:
        if st.button("🧮\n\n绩效计算", key="btn_calculate", use_container_width=True, help="一键计算绩效工资"):
            st.session_state.current_page = "calculate"
            st.rerun()

    with col3:
        if st.button("📜\n\n历史查询", key="btn_history", use_container_width=True, help="查看往月计算数据"):
            st.session_state.current_page = "history"
            st.rerun()

    with col4:
        if st.button("📁\n\n方案管理", key="btn_scheme", use_container_width=True, help="管理配置方案"):
            st.session_state.current_page = "scheme"
            st.rerun()

# ==================== 返回按钮 ====================
def render_back_button():
    """渲染返回首页按钮"""
    if st.button("⬅️ 返回首页", key="back_home"):
        st.session_state.current_page = "home"
        st.rerun()
    st.markdown("---")

# ==================== 主程序 ====================
# 注入自定义样式
inject_custom_css()

# 密码验证
if not check_password():
    st.stop()

# 初始化页面状态
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

# 根据页面状态显示内容
current_page = st.session_state.current_page

# 在所有页面（除首页外）显示顶部方案工具栏
if current_page != "home":
    render_scheme_toolbar()

if current_page == "home":
    render_home()

elif current_page == "employee":
    render_back_button()
    from app.pages import employee_page
    employee_page.render()

elif current_page == "region":
    render_back_button()
    from app.pages import region_page
    region_page.render()

elif current_page == "skill":
    render_back_button()
    from app.pages import skill_page
    skill_page.render()

elif current_page == "assignment":
    render_back_button()
    from app.pages import assignment_page
    assignment_page.render()

elif current_page == "import":
    render_back_button()
    from app.pages import import_page
    import_page.render()

elif current_page == "calculate":
    render_back_button()
    from app.pages import calculate_page
    calculate_page.render()

elif current_page == "history":
    render_back_button()
    from app.pages import history_page
    history_page.render()

elif current_page == "scheme":
    render_back_button()
    from app.pages import scheme_page
    scheme_page.render()

else:
    st.session_state.current_page = "home"
    st.rerun()
