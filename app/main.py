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

# ==================== 修复第三方库样式问题 ====================
import os

def fix_table_select_cell_style():
    """修复 streamlit-table-select-cell 组件的白底白字问题

    该组件在打包时硬编码了白色背景，导致在深色主题下不可见。
    此函数在应用启动时自动检测并修复。
    """
    try:
        import st_table_select_cell
        js_dir = os.path.join(os.path.dirname(st_table_select_cell.__file__),
                              'frontend/build/static/js')

        # 查找 main.*.js 文件
        for filename in os.listdir(js_dir):
            if filename.startswith('main.') and filename.endswith('.js'):
                js_path = os.path.join(js_dir, filename)

                with open(js_path, 'r') as f:
                    content = f.read()

                # 检查是否已经修复过
                if 'var(--background-color' in content:
                    return  # 已修复

                # 执行替换
                content = content.replace('"white"', '"var(--background-color,white)"')
                content = content.replace('#bbb', 'var(--secondary-background-color,#bbb)')
                content = content.replace('"yellow"', '"#666"')

                with open(js_path, 'w') as f:
                    f.write(content)

    except Exception as e:
        pass  # 静默失败，不影响应用启动

# 应用启动时执行修复
fix_table_select_cell_style()

# ==================== 主程序导入 ====================
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

# ==================== 禁用 Chrome 翻译 ====================
def disable_chrome_translate():
    """
    禁用 Chrome 自动翻译功能
    - 修改 html 标签的 lang 属性为 zh-CN
    - 添加 translate="no" 和 notranslate class
    - 注入 meta 标签告诉 Google 不要翻译
    """
    import streamlit.components.v1 as components

    # 使用零高度的 HTML 组件注入脚本
    # 注意：components.html 是在 iframe 中运行的，需要用 parent.document 访问主页面
    components.html("""
        <script>
            // 立即执行：修改主页面的 html 标签属性
            (function() {
                try {
                    // 访问父页面（主 Streamlit 页面）的 document
                    var html = parent.document.documentElement;
                    html.setAttribute('lang', 'zh-CN');
                    html.setAttribute('translate', 'no');
                    html.classList.add('notranslate');

                    // 添加 meta 标签到父页面的 head
                    var head = parent.document.head;

                    // 检查是否已经添加过，避免重复
                    if (!head.querySelector('meta[name="google"][content="notranslate"]')) {
                        var meta1 = parent.document.createElement('meta');
                        meta1.name = 'google';
                        meta1.content = 'notranslate';
                        head.appendChild(meta1);
                    }

                    if (!head.querySelector('meta[http-equiv="Content-Language"]')) {
                        var meta2 = parent.document.createElement('meta');
                        meta2.httpEquiv = 'Content-Language';
                        meta2.content = 'zh-CN';
                        head.appendChild(meta2);
                    }

                    console.log('Chrome translate disabled successfully');
                } catch (e) {
                    console.error('Failed to disable Chrome translate:', e);
                }
            })();
        </script>
    """, height=0)

# ==================== 自定义样式 ====================
def inject_custom_css():
    """注入自定义CSS样式 - Apple Dark Mode"""
    st.markdown("""
    <style>
    /* 禁止翻译 - 全局 */
    * {
        translate: no;
    }
    .notranslate {
        translate: no;
    }
    /* ==================== Apple Dark Mode 设计系统 ==================== */

    /* 全局字体 - San Francisco / System UI */
    * {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text",
                     "Helvetica Neue", Helvetica, Arial, sans-serif !important;
    }

    /* 全局背景色 - 纯黑 */
    .stApp {
        background-color: #000000 !important;
    }

    [data-testid="stAppViewContainer"] {
        background-color: #000000 !important;
    }

    .main .block-container {
        background-color: #000000 !important;
        padding-top: 2rem;
    }

    [data-testid="stHeader"] {
        background-color: #000000 !important;
    }

    /* 隐藏侧边栏 */
    [data-testid="stSidebar"] {
        display: none;
    }

    /* ==================== 卡片样式 - 深色卡片 ==================== */

    .apple-card {
        background: #1C1C1E;
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }

    /* 主容器样式 - 深色头部 */
    .main-header {
        text-align: center;
        padding: 40px 30px;
        background: #1C1C1E;
        color: #FFFFFF;
        border-radius: 18px;
        margin-bottom: 30px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }

    .main-header h1 {
        margin: 0;
        font-size: 2.5em;
        font-weight: 600;
        color: #FFFFFF;
        letter-spacing: -0.5px;
    }

    .main-header p {
        margin: 12px 0 0 0;
        color: #8E8E93;
        font-size: 1.15em;
        font-weight: 400;
    }

    /* 统计卡片 - 深色风格 */
    .stat-card {
        background: #1C1C1E;
        color: #FFFFFF;
        border-radius: 18px;
        padding: 24px 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
    }

    .stat-card .number {
        font-size: 2.8em;
        font-weight: 600;
        margin: 0;
        color: #0A84FF;
        letter-spacing: -1px;
    }

    .stat-card .label {
        font-size: 0.95em;
        color: #8E8E93;
        margin-top: 8px;
        font-weight: 500;
    }

    /* ==================== 按钮样式 - 胶囊形状 ==================== */

    /* 主要操作按钮 - Apple Blue (Dark Mode) */
    .stButton > button {
        background: #0A84FF !important;
        color: white !important;
        border: none !important;
        border-radius: 20px !important;
        padding: 12px 28px !important;
        font-weight: 500 !important;
        font-size: 0.95em !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
    }

    .stButton > button:hover {
        background: #409CFF !important;
        transform: scale(1.02) !important;
        box-shadow: 0 4px 12px rgba(10, 132, 255, 0.4) !important;
    }

    .stButton > button:active {
        transform: scale(0.98) !important;
    }

    /* 次要按钮样式 */
    .stButton > button[kind="secondary"] {
        background: #2C2C2E !important;
        color: #FFFFFF !important;
        border: 1.5px solid #3A3A3C !important;
    }

    .stButton > button[kind="secondary"]:hover {
        background: #3A3A3C !important;
        border-color: #48484A !important;
    }

    /* ==================== 输入框样式 ==================== */

    /* 文本输入框 */
    .stTextInput > div > div > input {
        border-radius: 12px !important;
        border: 1.5px solid #3A3A3C !important;
        padding: 12px 16px !important;
        font-size: 1em !important;
        background: #1C1C1E !important;
        color: #FFFFFF !important;
        transition: all 0.2s ease !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #0A84FF !important;
        box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.2) !important;
        outline: none !important;
    }

    .stTextInput > div > div > input::placeholder {
        color: #636366 !important;
    }

    /* 数字输入框 */
    .stNumberInput > div > div > input {
        border-radius: 12px !important;
        border: 1.5px solid #3A3A3C !important;
        padding: 12px 16px !important;
        background: #1C1C1E !important;
        color: #FFFFFF !important;
    }

    .stNumberInput > div > div > input:focus {
        border-color: #0A84FF !important;
        box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.2) !important;
    }

    /* 下拉选择框 */
    .stSelectbox > div > div {
        border-radius: 12px !important;
        border: 1.5px solid #3A3A3C !important;
        background: #1C1C1E !important;
    }

    .stSelectbox > div > div:focus-within {
        border-color: #0A84FF !important;
        box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.2) !important;
    }

    /* 下拉框文字颜色 */
    .stSelectbox [data-baseweb="select"] {
        color: #FFFFFF !important;
    }

    .stSelectbox [data-baseweb="select"] > div {
        background: #1C1C1E !important;
        color: #FFFFFF !important;
    }

    /* 禁用 selectbox 输入编辑功能 */
    div[data-baseweb="select"] input {
        caret-color: transparent !important;
        pointer-events: none !important;
        color: #FFFFFF !important;
    }

    /* ==================== 表格样式 ==================== */

    .stDataFrame {
        background: #1C1C1E !important;
        border-radius: 18px !important;
        padding: 8px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    }

    [data-testid="stDataFrame"] > div {
        border-radius: 12px !important;
        overflow: hidden !important;
    }

    /* 表格内部样式 */
    .stDataFrame [data-testid="stDataFrameResizable"] {
        background: #1C1C1E !important;
    }

    /* ==================== Expander 样式 ==================== */

    .streamlit-expanderHeader {
        background: #1C1C1E !important;
        border-radius: 12px !important;
        border: 1.5px solid #3A3A3C !important;
        font-weight: 500 !important;
        color: #FFFFFF !important;
    }

    .streamlit-expanderContent {
        background: #1C1C1E !important;
        border: 1.5px solid #3A3A3C !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
    }

    /* ==================== Metric 样式 ==================== */

    [data-testid="stMetricValue"] {
        color: #0A84FF !important;
        font-weight: 600 !important;
    }

    [data-testid="stMetricLabel"] {
        color: #8E8E93 !important;
    }

    [data-testid="stMetric"] {
        background: #1C1C1E;
        padding: 20px;
        border-radius: 18px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }

    /* ==================== 警告/提示框样式 ==================== */

    .stAlert {
        border-radius: 12px !important;
        border: none !important;
    }

    /* ==================== 分隔线样式 ==================== */

    hr {
        border: none !important;
        height: 1px !important;
        background: #3A3A3C !important;
        margin: 24px 0 !important;
    }

    /* ==================== 页面标题样式 ==================== */

    h1, h2, h3 {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        letter-spacing: -0.3px !important;
    }

    h1 { font-size: 2em !important; }
    h2 { font-size: 1.5em !important; }
    h3 { font-size: 1.2em !important; }

    /* 普通文字颜色 */
    p, span, label, .stMarkdown {
        color: #FFFFFF !important;
    }

    /* 次要文字 */
    .stCaption, small {
        color: #8E8E93 !important;
    }

    /* ==================== 工具栏样式 ==================== */

    .scheme-toolbar {
        background: #1C1C1E;
        border-bottom: 1px solid #3A3A3C;
        padding: 12px 24px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }

    .scheme-toolbar .scheme-label {
        font-weight: 600;
        color: #FFFFFF;
    }

    .scheme-toolbar .scheme-name {
        background: #2C2C2E;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 500;
        color: #FFFFFF;
    }

    .scheme-toolbar .modified-badge {
        background: #FF9F0A;
        color: #000000;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: 600;
    }

    /* ==================== 复选框样式 ==================== */

    .stCheckbox > label {
        font-weight: 400 !important;
        color: #FFFFFF !important;
    }

    .stCheckbox > label > span {
        color: #FFFFFF !important;
    }

    /* ==================== 文件上传样式 ==================== */

    .stFileUploader > div {
        background: #1C1C1E !important;
        border-radius: 18px !important;
        border: 2px dashed #3A3A3C !important;
        padding: 30px !important;
    }

    .stFileUploader > div:hover {
        border-color: #0A84FF !important;
        background: #2C2C2E !important;
    }

    /* ==================== 滚动条样式 ==================== */

    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #1C1C1E;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb {
        background: #3A3A3C;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #48484A;
    }

    /* ==================== 表单容器 ==================== */

    .stForm {
        background: #1C1C1E !important;
        padding: 24px !important;
        border-radius: 18px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    }

    /* ==================== Radio 按钮样式 ==================== */

    .stRadio > div {
        background: #1C1C1E;
        padding: 16px;
        border-radius: 12px;
    }

    .stRadio label {
        color: #FFFFFF !important;
    }

    /* ==================== 多选框样式 ==================== */

    .stMultiSelect > div > div {
        border-radius: 12px !important;
        border: 1.5px solid #3A3A3C !important;
        background: #1C1C1E !important;
    }

    /* ==================== Info/Warning/Error 框 ==================== */

    [data-testid="stNotification"] {
        background: #1C1C1E !important;
        border-radius: 12px !important;
    }

    /* ==================== Tab 标签样式 ==================== */

    .stTabs [data-baseweb="tab-list"] {
        background: #1C1C1E;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        color: #8E8E93 !important;
    }

    .stTabs [aria-selected="true"] {
        color: #0A84FF !important;
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
# 禁用 Chrome 翻译（必须在最前面执行）
disable_chrome_translate()

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
