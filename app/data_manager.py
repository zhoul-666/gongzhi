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

# 数据目录
DATA_DIR = Path(__file__).parent.parent / "data"
BACKUP_DIR = Path(__file__).parent.parent / "backup"


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


def load_json(filename: str) -> dict:
    """读取JSON文件"""
    file_path = DATA_DIR / filename
    if not file_path.exists():
        print(f"[警告] 文件不存在: {filename}")
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"[读取] 成功读取: {filename}")
            return data
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
            print(f"[保存] 成功保存: {filename}")
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


if __name__ == "__main__":
    # 测试
    print("=== 数据管理模块测试 ===")
    print(f"数据目录: {DATA_DIR}")
    print(f"备份目录: {BACKUP_DIR}")
    print(f"模式列表: {get_modes()}")
    print(f"区域列表: {get_regions()}")
