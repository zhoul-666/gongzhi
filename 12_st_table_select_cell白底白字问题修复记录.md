# st_table_select_cell 白底白字问题修复记录

> **重要**：此问题已发生两次，本文档详细记录问题原因和解决方案，供后续参考。

---

## 问题概述

| 项目 | 说明 |
|------|------|
| **问题现象** | 线上 Streamlit Cloud 部署后，表格组件显示为白底白字，完全看不清内容 |
| **影响组件** | `st_table_select_cell`（第三方表格选择组件） |
| **本地表现** | 正常（深色背景 + 白色文字） |
| **线上表现** | 异常（白色背景 + 白色文字） |
| **发生次数** | 2 次 |

---

## 问题根本原因

### 1. 技术背景

`st_table_select_cell` 是一个 Streamlit 自定义组件，其前端部分运行在 **iframe** 中。

组件的样式使用了 CSS 变量来适配 Streamlit 主题：
```css
background-color: var(--background-color, white);
```

### 2. 问题根源

**CSS 变量的 fallback 机制**：

```
var(--background-color, white)
         ↑                 ↑
    CSS变量名          fallback值（当变量不存在时使用）
```

- **本地开发**：Streamlit 正确传递主题变量到 iframe → 使用深色背景 → 正常显示
- **线上部署**：Streamlit Cloud 环境下，CSS 变量可能未正确传递到 iframe → 使用 fallback 值 `white` → 白底白字

### 3. 为什么本地正常、线上异常？

| 环境 | CSS 变量传递 | 实际背景色 | 文字颜色 | 结果 |
|------|-------------|-----------|---------|------|
| 本地 | ✅ 成功 | `#1C1C1E`（深色） | 白色 | ✅ 正常 |
| 线上 | ❌ 失败 | `white`（fallback） | 白色 | ❌ 白底白字 |

可能原因：
- Streamlit Cloud 的 iframe 安全策略更严格
- 主题变量注入时机不同
- 跨域限制导致 CSS 变量无法继承

---

## 解决方案

### 核心思路

**将 CSS fallback 值从亮色改为深色**，这样即使 CSS 变量传递失败，也能保证深色背景。

### 修改文件

```
st_table_select_cell/frontend/build/static/js/main.8cd7a845.js
```

### 修改内容

| 原值 | 修改为 | 说明 |
|------|--------|------|
| `var(--background-color,white)` | `var(--background-color,#1C1C1E)` | 主背景色 fallback 改为深灰 |
| `var(--secondary-background-color,#bbb)` | `var(--secondary-background-color,#3A3A3C)` | 次要背景色 fallback 改为深灰 |

### 修改命令

```bash
# 替换主背景色 fallback
sed -i '' 's/var(--background-color,white)/var(--background-color,#1C1C1E)/g' \
    st_table_select_cell/frontend/build/static/js/main.8cd7a845.js

# 替换次要背景色 fallback
sed -i '' 's/var(--secondary-background-color,#bbb)/var(--secondary-background-color,#3A3A3C)/g' \
    st_table_select_cell/frontend/build/static/js/main.8cd7a845.js
```

### 验证修改

```bash
# 确认新值存在
grep -o 'var(--background-color,#1C1C1E)' st_table_select_cell/frontend/build/static/js/main.8cd7a845.js

# 确认旧值已移除
grep -o 'var(--background-color,white)' st_table_select_cell/frontend/build/static/js/main.8cd7a845.js
# 应该无输出
```

---

## 部署验证

1. **提交代码**
   ```bash
   git add st_table_select_cell/
   git commit -m "修复: 更改 CSS fallback 颜色为深色，解决线上白底白字问题"
   git push
   ```

2. **等待 Streamlit Cloud 自动部署**（通常 1-3 分钟）

3. **强制刷新页面**（Ctrl+Shift+R 或 Cmd+Shift+R）

4. **检查表格显示**：应该看到深色背景 + 白色文字

---

## 项目结构说明

本项目使用**本地修改版**的 `st_table_select_cell`，而非 pip 安装版本：

```
gongzhi/
├── st_table_select_cell/          # 本地修改版组件（已修复）
│   ├── __init__.py
│   └── frontend/
│       └── build/
│           └── static/
│               └── js/
│                   └── main.8cd7a845.js  # ← 修改此文件
├── app/
│   └── main.py                    # 引用本地组件
└── requirements.txt               # 不包含 st-table-select-cell
```

**为什么使用本地版本**：
- 可以直接修改前端构建文件
- 不受 pip 包更新影响
- 修复可以立即生效

---

## 颜色参考

| 颜色代码 | 预览 | 用途 |
|---------|------|------|
| `#1C1C1E` | 深灰色 | 主背景色（接近黑色） |
| `#3A3A3C` | 中灰色 | 次要背景色（表头、选中行等） |
| `white` | 白色 | 文字颜色 |

这些颜色与 Streamlit 深色主题保持一致。

---

## 历史修复记录

| 日期 | 问题 | 解决方案 | 提交 |
|------|------|---------|------|
| 2026-01-17 | 首次发现白底白字 | 使用本地修复版组件 | d78c9d8 |
| 2026-01-18 | 问题再次出现 | 修改 fallback 为深色 | ec2decb |

---

## 预防措施

### 如果问题再次发生

1. **首先检查** `main.8cd7a845.js` 中的 fallback 值是否被覆盖
2. **搜索关键词**：
   ```bash
   grep -E 'var\(--background-color,[^)]+\)' st_table_select_cell/frontend/build/static/js/*.js
   ```
3. **确保 fallback 为深色**（`#1C1C1E`），而非 `white`

### 如果升级组件

如果未来需要升级 `st_table_select_cell`：
1. 下载新版本
2. **必须**修改 `main.*.js` 中的 CSS fallback 值
3. 本地测试后再部署

---

## 相关文件

- 修复的 JS 文件：`st_table_select_cell/frontend/build/static/js/main.8cd7a845.js`
- 组件入口：`st_table_select_cell/__init__.py`
- 主程序：`app/main.py`

---

## 总结

**问题本质**：Streamlit Cloud 环境下 CSS 变量未能正确传递到 iframe 组件，导致使用了亮色 fallback 值。

**解决方法**：将 CSS fallback 值从亮色改为深色，确保在任何情况下都能正确显示。

**关键点**：修改的是 **fallback 值**，不影响 CSS 变量正常工作时的表现。
