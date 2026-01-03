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
    </style>
    """, unsafe_allow_html=True)

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
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; color: #666;">
            <p style="font-size: 0.9em;">版本 {__version__}</p>
        </div>
        """, unsafe_allow_html=True)

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

else:
    st.session_state.current_page = "home"
    st.rerun()
