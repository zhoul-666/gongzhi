"""
数据管理模块 - 负责JSON文件的读写和备份
版本: 1.0.0
"""
__version__ = "1.0.0"

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
import streamlit as st

# 数据目录
DATA_DIR = Path(__file__).parent.parent / "data"
BACKUP_DIR = Path(__file__).parent.parent / "backup"


def clear_cache():
    """清除所有 Streamlit 数据缓存"""
    st.cache_data.clear()


def ensure_dirs():
    """确保数据目录和备份目录存在"""
    DATA_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)


def backup_file(file_path: Path, version: str = None):
    """
    备份文件
    命名格式：原文件名_YYYYMMDD_HHMMSS_v版本.扩展名
    """
    if not file_path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    version_str = f"_v{version}" if version else ""
    backup_name = f"{file_path.stem}_{timestamp}{version_str}{file_path.suffix}"
    backup_path = BACKUP_DIR / backup_name

    shutil.copy2(file_path, backup_path)
    print(f"[备份] 已备份文件: {backup_name}")
    return backup_path


@st.cache_data(ttl=300)  # 缓存5分钟
def load_json(filename: str) -> dict:
    """读取JSON文件（带Streamlit缓存）"""
    file_path = DATA_DIR / filename
    if not file_path.exists():
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[错误] JSON格式错误: {filename} - {e}")
        return {}
    except Exception as e:
        print(f"[错误] 读取失败: {filename} - {e}")
        return {}


def save_json(filename: str, data: dict, backup: bool = True):
    """保存JSON文件，默认先备份"""
    ensure_dirs()
    file_path = DATA_DIR / filename

    # 备份现有文件
    if backup and file_path.exists():
        backup_file(file_path, __version__)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # 清除缓存，确保下次读取是最新数据
        clear_cache()
        return True
    except Exception as e:
        print(f"[错误] 保存失败: {filename} - {e}")
        return False


# ============ 员工管理 ============

def get_employees() -> list:
    """获取所有员工"""
    data = load_json("employees.json")
    return data.get("employees", [])


def add_employee(name: str, employee_no: str = None, mode_id: str = None) -> dict:
    """添加员工

    Args:
        name: 员工姓名
        employee_no: 工号（可选）
        mode_id: 所属模式ID
    """
    data = load_json("employees.json")
    employees = data.get("employees", [])
    next_id = data.get("next_id", 1)

    # 检查是否已存在同名员工
    for emp in employees:
        if emp["name"] == name:
            print(f"[提示] 员工已存在: {name}")
            return emp

    new_employee = {
        "id": f"emp_{next_id:04d}",
        "name": name,
        "employee_no": employee_no or f"E{next_id:04d}",
        "mode_id": mode_id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    employees.append(new_employee)
    data["employees"] = employees
    data["next_id"] = next_id + 1

    save_json("employees.json", data)
    print(f"[添加] 新增员工: {name}")
    return new_employee


def update_employee(emp_id: str, updates: dict) -> bool:
    """更新员工信息"""
    data = load_json("employees.json")
    employees = data.get("employees", [])

    for emp in employees:
        if emp["id"] == emp_id:
            emp.update(updates)
            emp["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_json("employees.json", data)
            print(f"[更新] 已更新员工: {emp['name']}")
            return True

    print(f"[错误] 未找到员工: {emp_id}")
    return False


def delete_employee(emp_id: str) -> bool:
    """删除员工"""
    data = load_json("employees.json")
    employees = data.get("employees", [])

    for i, emp in enumerate(employees):
        if emp["id"] == emp_id:
            deleted = employees.pop(i)
            save_json("employees.json", data)
            print(f"[删除] 已删除员工: {deleted['name']}")
            return True

    print(f"[错误] 未找到员工: {emp_id}")
    return False


# ============ 模式管理 ============

def get_modes() -> list:
    """获取所有模式"""
    data = load_json("modes.json")
    return data.get("modes", [])


def get_mode_by_id(mode_id: str) -> dict:
    """根据ID获取模式"""
    modes = get_modes()
    for mode in modes:
        if mode["id"] == mode_id:
            return mode
    return None


# ============ 大区域管理 ============

def get_regions() -> list:
    """获取所有大区域"""
    data = load_json("regions.json")
    return data.get("regions", [])


def get_region_by_id(region_id: str) -> dict:
    """根据ID获取大区域"""
    regions = get_regions()
    for region in regions:
        if region["id"] == region_id:
            return region
    return None


def update_region(region_id: str, updates: dict) -> bool:
    """更新大区域信息"""
    data = load_json("regions.json")
    regions = data.get("regions", [])

    for region in regions:
        if region["id"] == region_id:
            region.update(updates)
            save_json("regions.json", data)
            print(f"[更新] 已更新区域: {region['name']}")
            return True

    return False


def add_region(name: str, erp_column: str = None) -> dict:
    """添加大区域"""
    data = load_json("regions.json")
    regions = data.get("regions", [])

    # 生成新ID
    max_num = 0
    for r in regions:
        num = int(r["id"].split("_")[1])
        if num > max_num:
            max_num = num

    new_region = {
        "id": f"region_{max_num + 1:03d}",
        "name": name,
        "erp_column": erp_column,
        "threshold": 30000,
        "ladder_rules": [],
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }

    regions.append(new_region)
    data["regions"] = regions
    save_json("regions.json", data)
    print(f"[添加] 新增区域: {name}")
    return new_region


# ============ 小技能管理 ============

def get_skills() -> list:
    """获取所有小技能"""
    data = load_json("skills.json")
    return data.get("skills", [])


def get_skills_by_mode(mode_id: str) -> list:
    """获取指定模式下的技能"""
    skills = get_skills()
    return [s for s in skills if s.get("mode_id") == mode_id]


def get_skills_by_region(region_id: str) -> list:
    """获取指定区域下的技能"""
    skills = get_skills()
    return [s for s in skills if s.get("region_id") == region_id]


def add_skill(name: str, mode_id: str, region_id: str,
              salary_on_duty: int = 200, salary_off_duty: int = 100) -> dict:
    """添加小技能"""
    data = load_json("skills.json")
    skills = data.get("skills", [])
    next_id = data.get("next_id", 1)

    new_skill = {
        "id": f"skill_{next_id:03d}",
        "name": name,
        "mode_id": mode_id,
        "region_id": region_id,
        "salary_on_duty": salary_on_duty,
        "salary_off_duty": salary_off_duty,
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }

    skills.append(new_skill)
    data["skills"] = skills
    data["next_id"] = next_id + 1

    save_json("skills.json", data)
    print(f"[添加] 新增技能: {name}")
    return new_skill


def update_skill(skill_id: str, updates: dict) -> bool:
    """更新技能信息"""
    data = load_json("skills.json")
    skills = data.get("skills", [])

    for skill in skills:
        if skill["id"] == skill_id:
            skill.update(updates)
            save_json("skills.json", data)
            print(f"[更新] 已更新技能: {skill['name']}")
            return True

    return False


def batch_update_skills(skill_ids: list, updates: dict) -> int:
    """批量更新技能"""
    data = load_json("skills.json")
    skills = data.get("skills", [])
    count = 0

    for skill in skills:
        if skill["id"] in skill_ids:
            skill.update(updates)
            count += 1

    if count > 0:
        save_json("skills.json", data)
        print(f"[批量更新] 已更新 {count} 个技能")

    return count


# ============ 员工-技能关联 ============

def get_employee_skills(emp_id: str = None) -> list:
    """获取员工技能关联"""
    data = load_json("employee_skills.json")
    all_skills = data.get("employee_skills", [])

    if emp_id:
        return [s for s in all_skills if s.get("employee_id") == emp_id]
    return all_skills


def assign_skill_to_employee(emp_id: str, skill_id: str, passed_exam: bool = False,
                              custom_threshold: int = None) -> dict:
    """给员工分配技能"""
    data = load_json("employee_skills.json")
    emp_skills = data.get("employee_skills", [])

    # 检查是否已存在
    for es in emp_skills:
        if es["employee_id"] == emp_id and es["skill_id"] == skill_id:
            print(f"[提示] 技能已分配")
            return es

    new_assignment = {
        "employee_id": emp_id,
        "skill_id": skill_id,
        "passed_exam": passed_exam,
        "use_system_threshold": custom_threshold is None,
        "custom_threshold": custom_threshold,
        "use_system_price": True,  # 默认使用系统价格
        "custom_price_on_duty": None,  # 自定义在岗价格
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    emp_skills.append(new_assignment)
    data["employee_skills"] = emp_skills
    save_json("employee_skills.json", data)
    print(f"[分配] 已分配技能")
    return new_assignment


def batch_assign_skills_to_employee(emp_id: str, skill_ids: list, passed_exam: bool = False) -> dict:
    """批量分配技能给员工

    Args:
        emp_id: 员工ID
        skill_ids: 技能ID列表
        passed_exam: 是否通过考核，默认False

    Returns:
        dict: {"success": [...], "skipped": [...]} 分配结果
    """
    data = load_json("employee_skills.json")
    emp_skills = data.get("employee_skills", [])

    results = {"success": [], "skipped": []}

    for skill_id in skill_ids:
        # 检查是否已存在
        exists = any(es["employee_id"] == emp_id and es["skill_id"] == skill_id for es in emp_skills)
        if exists:
            results["skipped"].append(skill_id)
            continue

        new_assignment = {
            "employee_id": emp_id,
            "skill_id": skill_id,
            "passed_exam": passed_exam,
            "use_system_threshold": True,
            "custom_threshold": None,
            "use_system_price": True,
            "custom_price_on_duty": None,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        emp_skills.append(new_assignment)
        results["success"].append(skill_id)

    if results["success"]:
        data["employee_skills"] = emp_skills
        save_json("employee_skills.json", data)
        print(f"[批量分配] 成功分配 {len(results['success'])} 个技能")

    return results


def update_employee_skill(emp_id: str, skill_id: str, updates: dict) -> bool:
    """更新员工技能关联"""
    data = load_json("employee_skills.json")
    emp_skills = data.get("employee_skills", [])

    for es in emp_skills:
        if es["employee_id"] == emp_id and es["skill_id"] == skill_id:
            es.update(updates)
            save_json("employee_skills.json", data)
            return True

    return False


def remove_employee_skill(emp_id: str, skill_id: str) -> bool:
    """取消员工的技能分配"""
    data = load_json("employee_skills.json")
    emp_skills = data.get("employee_skills", [])

    for i, es in enumerate(emp_skills):
        if es["employee_id"] == emp_id and es["skill_id"] == skill_id:
            emp_skills.pop(i)
            data["employee_skills"] = emp_skills
            save_json("employee_skills.json", data)
            return True

    return False


# ============ 方案管理 ============

def get_schemes() -> list:
    """获取所有方案"""
    data = load_json("schemes.json")
    return data.get("schemes", [])


def get_active_scheme() -> dict:
    """获取当前激活的方案"""
    schemes = get_schemes()
    for scheme in schemes:
        if scheme.get("is_active"):
            return scheme
    return None


def get_scheme_by_id(scheme_id: str) -> dict:
    """根据ID获取方案"""
    schemes = get_schemes()
    for scheme in schemes:
        if scheme["id"] == scheme_id:
            return scheme
    return None


def create_config_snapshot() -> dict:
    """创建当前配置的快照"""
    return {
        "skills": get_skills(),
        "regions": get_regions(),
        "employee_skills": get_employee_skills()
    }


def save_as_scheme(name: str, description: str = "") -> dict:
    """将当前配置保存为新方案"""
    data = load_json("schemes.json")
    schemes = data.get("schemes", [])
    next_id = data.get("next_id", 1)

    # 创建快照
    snapshot = create_config_snapshot()

    new_scheme = {
        "id": f"scheme_{next_id:03d}",
        "name": name,
        "is_active": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "description": description,
        "snapshot": snapshot
    }

    schemes.append(new_scheme)
    data["schemes"] = schemes
    data["next_id"] = next_id + 1

    save_json("schemes.json", data, backup=False)
    print(f"[方案] 已保存方案: {name}")
    return new_scheme


def update_scheme_snapshot(scheme_id: str) -> bool:
    """更新方案的快照为当前配置"""
    data = load_json("schemes.json")
    schemes = data.get("schemes", [])

    for scheme in schemes:
        if scheme["id"] == scheme_id:
            scheme["snapshot"] = create_config_snapshot()
            scheme["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_json("schemes.json", data, backup=False)
            print(f"[方案] 已更新方案快照: {scheme['name']}")
            return True

    return False


def load_scheme_to_current(scheme_id: str) -> bool:
    """将方案加载到当前配置（覆盖当前数据）"""
    scheme = get_scheme_by_id(scheme_id)
    if not scheme or not scheme.get("snapshot"):
        print(f"[错误] 方案不存在或无快照: {scheme_id}")
        return False

    snapshot = scheme["snapshot"]

    # 恢复技能数据
    skills_data = load_json("skills.json")
    skills_data["skills"] = snapshot.get("skills", [])
    save_json("skills.json", skills_data)

    # 恢复区域数据
    regions_data = load_json("regions.json")
    regions_data["regions"] = snapshot.get("regions", [])
    save_json("regions.json", regions_data)

    # 恢复员工技能数据
    emp_skills_data = load_json("employee_skills.json")
    emp_skills_data["employee_skills"] = snapshot.get("employee_skills", [])
    save_json("employee_skills.json", emp_skills_data)

    # 设置为激活方案
    set_active_scheme(scheme_id)

    print(f"[方案] 已加载方案: {scheme['name']}")
    return True


def set_active_scheme(scheme_id: str) -> bool:
    """设置激活方案"""
    data = load_json("schemes.json")
    schemes = data.get("schemes", [])

    found = False
    for scheme in schemes:
        if scheme["id"] == scheme_id:
            scheme["is_active"] = True
            found = True
        else:
            scheme["is_active"] = False

    if found:
        save_json("schemes.json", data, backup=False)
        return True
    return False


def update_scheme_info(scheme_id: str, updates: dict) -> bool:
    """更新方案基本信息（名称、描述）"""
    data = load_json("schemes.json")
    schemes = data.get("schemes", [])

    for scheme in schemes:
        if scheme["id"] == scheme_id:
            if "name" in updates:
                scheme["name"] = updates["name"]
            if "description" in updates:
                scheme["description"] = updates["description"]
            scheme["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_json("schemes.json", data, backup=False)
            print(f"[方案] 已更新方案信息: {scheme['name']}")
            return True

    return False


def delete_scheme(scheme_id: str) -> bool:
    """删除方案"""
    data = load_json("schemes.json")
    schemes = data.get("schemes", [])

    for i, scheme in enumerate(schemes):
        if scheme["id"] == scheme_id:
            # 不允许删除激活的方案
            if scheme.get("is_active"):
                print(f"[错误] 不能删除当前使用中的方案")
                return False
            deleted = schemes.pop(i)
            save_json("schemes.json", data, backup=False)
            print(f"[方案] 已删除方案: {deleted['name']}")
            return True

    return False


def get_config_hash() -> str:
    """获取当前配置的哈希值（用于判断是否修改）"""
    import hashlib
    snapshot = create_config_snapshot()
    content = json.dumps(snapshot, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(content.encode()).hexdigest()[:8]


def is_config_modified() -> bool:
    """检查当前配置是否与激活方案不同"""
    active = get_active_scheme()
    if not active or not active.get("snapshot"):
        return False

    current_hash = get_config_hash()

    # 计算激活方案的哈希
    import hashlib
    snapshot_content = json.dumps(active["snapshot"], sort_keys=True, ensure_ascii=False)
    active_hash = hashlib.md5(snapshot_content.encode()).hexdigest()[:8]

    return current_hash != active_hash


# ============ 计算历史锁定管理 ============

def is_calculation_locked(month: str) -> bool:
    """检查指定月份是否已锁定"""
    data = load_json("calculation_history.json")
    calculations = data.get("calculations", [])

    for calc in calculations:
        # 兼容 month 和 period 字段
        if calc.get("month") == month or calc.get("period") == month:
            return calc.get("locked", False)
    return False


def lock_calculation(month: str) -> bool:
    """锁定指定月份的计算结果"""
    data = load_json("calculation_history.json")
    if not data:
        return False

    calculations = data.get("calculations", [])

    for calc in calculations:
        # 兼容 month 和 period 字段
        if calc.get("month") == month or calc.get("period") == month:
            calc["locked"] = True
            calc["locked_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            active_scheme = get_active_scheme()
            if active_scheme:
                calc["locked_scheme_name"] = active_scheme.get("name", "")
            save_json("calculation_history.json", data, backup=False)
            print(f"[锁定] 已锁定: {month}")
            return True

    print(f"[错误] 未找到记录: {month}")
    return False


def unlock_calculation(month: str) -> bool:
    """解锁指定月份的计算结果"""
    data = load_json("calculation_history.json")
    if not data:
        return False

    calculations = data.get("calculations", [])

    for calc in calculations:
        # 兼容 month 和 period 字段
        if calc.get("month") == month or calc.get("period") == month:
            calc["locked"] = False
            calc.pop("locked_at", None)
            save_json("calculation_history.json", data, backup=False)
            print(f"[解锁] 已解锁: {month}")
            return True

    print(f"[错误] 未找到记录: {month}")
    return False


# ============ 角色管理 ============

def get_roles() -> list:
    """获取所有角色"""
    data = load_json("roles.json")
    return data.get("roles", [])


def get_role_by_id(role_id: str) -> dict:
    """根据ID获取角色"""
    roles = get_roles()
    for role in roles:
        if role["id"] == role_id:
            return role
    return None


def add_role(name: str, description: str = "", threshold_multiplier: float = 1.0,
             income_types: list = None, settings: dict = None) -> dict:
    """添加新角色"""
    data = load_json("roles.json")
    roles = data.get("roles", [])
    next_id = data.get("next_id", 1)

    new_role = {
        "id": f"role_{next_id:03d}",
        "name": name,
        "description": description,
        "threshold_multiplier": threshold_multiplier,
        "income_types": income_types or ["skill_salary", "ladder_bonus"],
        "settings": settings or {},
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }

    roles.append(new_role)
    data["roles"] = roles
    data["next_id"] = next_id + 1

    save_json("roles.json", data)
    print(f"[添加] 新增角色: {name}")
    return new_role


def update_role(role_id: str, updates: dict) -> bool:
    """更新角色信息"""
    data = load_json("roles.json")
    roles = data.get("roles", [])

    for role in roles:
        if role["id"] == role_id:
            role.update(updates)
            role["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_json("roles.json", data)
            print(f"[更新] 已更新角色: {role['name']}")
            return True

    return False


def delete_role(role_id: str) -> bool:
    """删除角色"""
    data = load_json("roles.json")
    roles = data.get("roles", [])

    for i, role in enumerate(roles):
        if role["id"] == role_id:
            deleted = roles.pop(i)
            save_json("roles.json", data)
            print(f"[删除] 已删除角色: {deleted['name']}")
            return True

    return False


# ============ 外部数据管理 ============

def get_external_data(month: str = None) -> list:
    """获取外部数据（营业额、开单量等）"""
    data = load_json("external_data.json")
    records = data.get("records", [])

    if month:
        return [r for r in records if r.get("month") == month]
    return records


def save_external_data(records: list, month: str) -> bool:
    """保存外部数据"""
    data = load_json("external_data.json")
    if not data:
        data = {"records": []}

    existing = data.get("records", [])
    # 移除该月的旧数据
    existing = [r for r in existing if r.get("month") != month]
    # 添加新数据
    existing.extend(records)

    data["records"] = existing
    return save_json("external_data.json", data)


# ============ 收入规则管理 ============

def get_income_rules() -> list:
    """获取所有收入类型规则"""
    data = load_json("income_rules.json")
    return data.get("rules", [])


def get_income_rule_by_type(income_type: str) -> dict:
    """根据类型获取收入规则"""
    rules = get_income_rules()
    for rule in rules:
        if rule["type"] == income_type:
            return rule
    return None


# ============ 奖金池管理 ============

def get_bonus_pools() -> list:
    """获取所有奖金池配置"""
    data = load_json("bonus_pools.json")
    return data.get("pools", [])


def get_bonus_pool_by_id(pool_id: str) -> dict:
    """根据ID获取奖金池"""
    pools = get_bonus_pools()
    for pool in pools:
        if pool["id"] == pool_id:
            return pool
    return None


def add_bonus_pool(name: str, total_amount: float, distribution_rules: list) -> dict:
    """添加奖金池"""
    data = load_json("bonus_pools.json")
    if not data:
        data = {"pools": [], "next_id": 1}

    pools = data.get("pools", [])
    next_id = data.get("next_id", 1)

    new_pool = {
        "id": f"pool_{next_id:03d}",
        "name": name,
        "total_amount": total_amount,
        "distribution_rules": distribution_rules,
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }

    pools.append(new_pool)
    data["pools"] = pools
    data["next_id"] = next_id + 1

    save_json("bonus_pools.json", data)
    print(f"[添加] 新增奖金池: {name}")
    return new_pool


def update_bonus_pool(pool_id: str, updates: dict) -> bool:
    """更新奖金池"""
    data = load_json("bonus_pools.json")
    if not data:
        return False

    pools = data.get("pools", [])

    for pool in pools:
        if pool["id"] == pool_id:
            pool.update(updates)
            pool["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_json("bonus_pools.json", data)
            print(f"[更新] 已更新奖金池: {pool['name']}")
            return True

    return False


def delete_bonus_pool(pool_id: str) -> bool:
    """删除奖金池"""
    data = load_json("bonus_pools.json")
    if not data:
        return False

    pools = data.get("pools", [])

    for i, pool in enumerate(pools):
        if pool["id"] == pool_id:
            deleted = pools.pop(i)
            save_json("bonus_pools.json", data)
            print(f"[删除] 已删除奖金池: {deleted['name']}")
            return True

    return False


# ============ 员工达标线计算 ============

def get_employee_threshold(emp_id: str, region_id: str) -> float:
    """
    获取员工在指定区域的达标线
    优先级：员工自定义 > 角色倍率 > 区域默认值
    """
    from app.data_manager import get_employees, get_role_by_id, get_region_by_id

    # 获取区域默认达标线
    region = get_region_by_id(region_id)
    if not region:
        return 30000  # 默认值

    base_threshold = region.get("threshold", 30000)

    # 查找员工
    employees = get_employees()
    emp = next((e for e in employees if e["id"] == emp_id), None)
    if not emp:
        return base_threshold

    # 检查员工是否有自定义达标线
    custom_settings = emp.get("custom_settings", {})
    if custom_settings.get("custom_threshold"):
        custom = custom_settings.get("thresholds", {}).get(region_id)
        if custom is not None:
            return custom

    # 检查角色倍率
    role_id = emp.get("role_id")
    if role_id:
        role = get_role_by_id(role_id)
        if role:
            multiplier = role.get("threshold_multiplier", 1.0)
            return base_threshold * multiplier

    return base_threshold


if __name__ == "__main__":
    # 测试
    print("=== 数据管理模块测试 ===")
    print(f"数据目录: {DATA_DIR}")
    print(f"备份目录: {BACKUP_DIR}")
    print(f"模式列表: {get_modes()}")
    print(f"区域列表: {get_regions()}")
    print(f"角色列表: {get_roles()}")
