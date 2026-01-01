"""
绩效核算系统 - 主程序入口
版本: 1.1.0

运行方式: streamlit run app/main.py

更新记录:
- 1.1.0: 添加密码保护功能
- 1.0.0: 初始版本
"""
__version__ = "1.1.0"

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
    initial_sidebar_state="expanded"
)

# ==================== 密码验证 ====================
def check_password():
    """
    检查用户是否已通过密码验证
    返回 True 表示已验证，False 表示未验证

    本地开发时：secrets.toml 中设置 require_password = false，跳过密码
    线上部署时：Streamlit Cloud 的 Secrets 中设置 require_password = true
    """
    # 检查是否需要密码验证
    try:
        require_password = st.secrets.get("require_password", False)
    except:
        require_password = False

    # 本地开发不需要密码
    if not require_password:
        print("本地模式，跳过密码验证")
        return True

    # 初始化登录状态
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # 如果已登录，直接返回
    if st.session_state.authenticated:
        return True

    # 显示登录界面
    st.title("🔐 绩效核算系统")
    st.markdown("---")
    st.markdown("### 请输入访问密码")

    password = st.text_input("密码", type="password", key="password_input")

    if st.button("登录", type="primary"):
        # 从 secrets 获取密码
        try:
            correct_password = st.secrets.get("password", "123456")
        except:
            correct_password = "123456"

        if password == correct_password:
            st.session_state.authenticated = True
            print("用户登录成功")
            st.rerun()
        else:
            st.error("❌ 密码错误，请重试")
            print("用户输入了错误的密码")

    st.markdown("---")
    st.caption("如忘记密码，请联系管理员")
    return False

# 密码验证未通过则停止
if not check_password():
    st.stop()

# ==================== 主界面 ====================

# 侧边栏导航
st.sidebar.title("📊 绩效核算系统")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "功能菜单",
    [
        "🏠 首页",
        "👥 员工管理",
        "🗺️ 大区域管理",
        "🔧 小技能管理",
        "📋 员工技能指派",
        "📥 绩效导入",
        "🧮 绩效计算",
        "📜 历史查询"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(f"版本: {__version__}")

# 根据选择显示不同页面
if page == "🏠 首页":
    from app.data_manager import get_employees, get_skills, load_json
    from datetime import datetime

    st.title("绩效核算系统")
    st.markdown("---")

    # 获取真实数据
    employees = get_employees()
    skills = get_skills()
    history = load_json("calculation_history.json")
    calculations = history.get("calculations", []) if history else []

    current_month = datetime.now().strftime("%Y-%m")
    calculated_this_month = any(c.get("month") == current_month for c in calculations)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("员工总数", len(employees))
    with col2:
        st.metric("技能总数", len(skills))
    with col3:
        st.metric("本月已核算", "是" if calculated_this_month else "否")

    st.markdown("---")
    st.markdown("""
    ### 系统功能

    - **员工管理**：添加、编辑、删除员工信息
    - **大区域管理**：配置印前/印中/印后等区域的阶梯规则
    - **小技能管理**：管理各模式下的技能和工资标准
    - **员工技能指派**：给员工分配技能，设置考核状态
    - **绩效导入**：从ERP导入绩效数据
    - **绩效计算**：一键计算绩效工资
    - **历史查询**：查看往月数据
    """)

elif page == "👥 员工管理":
    from app.pages import employee_page
    employee_page.render()

elif page == "🗺️ 大区域管理":
    from app.pages import region_page
    region_page.render()

elif page == "🔧 小技能管理":
    from app.pages import skill_page
    skill_page.render()

elif page == "📋 员工技能指派":
    from app.pages import assignment_page
    assignment_page.render()

elif page == "📥 绩效导入":
    from app.pages import import_page
    import_page.render()

elif page == "🧮 绩效计算":
    from app.pages import calculate_page
    calculate_page.render()

elif page == "📜 历史查询":
    from app.pages import history_page
    history_page.render()
