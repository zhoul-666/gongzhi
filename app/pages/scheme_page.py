"""
方案管理页面 - 管理配置方案
"""
import streamlit as st
from app.data_manager import (
    get_schemes, get_active_scheme, get_scheme_by_id,
    save_as_scheme, update_scheme_info, delete_scheme,
    load_scheme_to_current, set_active_scheme, update_scheme_snapshot
)


def render():
    """渲染方案管理页面"""
    st.markdown("## 📁 方案管理")
    st.markdown("管理不同的工资配置方案，方便测算对比")

    # 获取数据
    schemes = get_schemes()
    active_scheme = get_active_scheme()

    # 新建方案区域
    with st.expander("➕ 新建方案", expanded=False):
        col1, col2 = st.columns([2, 1])
        with col1:
            new_name = st.text_input("方案名称", key="new_scheme_name_page", placeholder="例如：2025年2月测试版")
            new_desc = st.text_input("方案描述", key="new_scheme_desc_page", placeholder="简要描述此方案的用途")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("创建方案", key="create_scheme", use_container_width=True):
                if new_name:
                    new_scheme = save_as_scheme(new_name, new_desc)
                    st.success(f"已创建方案：{new_name}")
                    st.rerun()
                else:
                    st.warning("请输入方案名称")

    st.markdown("---")

    # 方案列表
    st.markdown("### 📋 方案列表")

    if not schemes:
        st.info("暂无方案，请点击上方创建新方案")
        return

    # 两列布局
    cols = st.columns(2)
    for idx, scheme in enumerate(schemes):
        is_active = scheme.get("is_active", False)
        scheme_id = scheme["id"]

        with cols[idx % 2]:
            with st.container(border=True):
                # 标题和状态
                status_icon = "✅" if is_active else "○"
                st.markdown(f"**{status_icon} {scheme['name']}**")

                if is_active:
                    st.caption("当前使用中")
                if scheme.get("description"):
                    st.caption(scheme["description"])

                st.caption(f"更新: {scheme.get('updated_at', '-')[:10]}")

                # 按钮行
                if is_active:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("更新快照", key=f"update_{scheme_id}", use_container_width=True):
                            update_scheme_snapshot(scheme_id)
                            st.success("快照已更新")
                            st.rerun()
                    with c2:
                        if st.button("重命名", key=f"rename_{scheme_id}", use_container_width=True):
                            st.session_state[f"editing_{scheme_id}"] = True
                else:
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("切换", key=f"switch_{scheme_id}", use_container_width=True):
                            load_scheme_to_current(scheme_id)
                            st.success(f"已切换到：{scheme['name']}")
                            st.rerun()
                    with c2:
                        if st.button("重命名", key=f"rename_{scheme_id}", use_container_width=True):
                            st.session_state[f"editing_{scheme_id}"] = True
                    with c3:
                        if st.button("删除", key=f"delete_{scheme_id}", use_container_width=True):
                            st.session_state[f"confirm_delete_{scheme_id}"] = True

                # 重命名对话框
                if st.session_state.get(f"editing_{scheme_id}"):
                    new_name = st.text_input("新名称", value=scheme["name"], key=f"new_name_{scheme_id}")
                    new_desc = st.text_input("新描述", value=scheme.get("description", ""), key=f"new_desc_{scheme_id}")
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        if st.button("确定", key=f"confirm_rename_{scheme_id}", use_container_width=True):
                            update_scheme_info(scheme_id, {"name": new_name, "description": new_desc})
                            st.session_state[f"editing_{scheme_id}"] = False
                            st.success("已更新")
                            st.rerun()
                    with bc2:
                        if st.button("取消", key=f"cancel_rename_{scheme_id}", use_container_width=True):
                            st.session_state[f"editing_{scheme_id}"] = False
                            st.rerun()

                # 删除确认对话框
                if st.session_state.get(f"confirm_delete_{scheme_id}"):
                    st.warning(f"确定删除「{scheme['name']}」？")
                    dc1, dc2 = st.columns(2)
                    with dc1:
                        if st.button("确定删除", key=f"do_delete_{scheme_id}", use_container_width=True):
                            delete_scheme(scheme_id)
                            st.session_state[f"confirm_delete_{scheme_id}"] = False
                            st.success("已删除")
                            st.rerun()
                    with dc2:
                        if st.button("取消", key=f"cancel_delete_{scheme_id}", use_container_width=True):
                            st.session_state[f"confirm_delete_{scheme_id}"] = False
                            st.rerun()

    # 使用说明
    with st.expander("💡 使用说明", expanded=False):
        st.markdown("""
        **什么是方案？**
        - 方案是一套完整的工资配置快照，包括：技能工资、阶梯规则、员工技能指派
        - 可以保存多个方案用于测算对比

        **如何使用？**
        1. **创建方案**：点击「新建方案」，输入名称和描述
        2. **切换方案**：点击「切换到此方案」，当前配置会被替换为该方案的内容
        3. **更新快照**：修改配置后，点击「更新快照」保存到当前方案
        4. **对比测算**：在绩效计算页面，切换不同方案分别计算，对比结果

        **注意事项**
        - 切换方案会覆盖当前配置，请先保存
        - 不能删除当前使用中的方案
        - 删除操作不可恢复
        """)
