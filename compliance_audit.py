"""
配置合规审计脚本
================================
功能：检查设备配置是否符合安全基线
    基线规则（可自定义扩展）：
    1. SSH 必须启用（stelnet server enable）
    2. Telnet 必须禁用（telnet server disable）
    3. 必须配置 AAA 本地用户
    4. 密码必须加密存储（password cipher）
    5. 必须配置闲置超时（idle-timeout）
    6. 管理 VLAN 不应使用默认 VLAN 1

使用方式：
    python compliance_audit.py <配置文件1> [配置文件2] ...

示例：
    python compliance_audit.py backups/LSW1_20260628_113000.txt
    python compliance_audit.py backups/*.txt

作者：王玉强
日期：2026-06-28
"""

import sys
import os
import re


# ===== 基线规则定义 =====
BASELINE_RULES = [
    {
        'id': 'R001',
        'name': 'SSH 服务必须启用',
        'check': lambda config: 'stelnet server enable' in config,
        'level': 'HIGH',
        'fix': '系统视图下执行：stelnet server enable'
    },
    {
        'id': 'R002',
        'name': 'Telnet 服务应禁用',
        'check': lambda config: 'telnet server enable' not in config,
        'level': 'MEDIUM',
        'fix': '系统视图下执行：undo telnet server enable'
    },
    {
        'id': 'R003',
        'name': '必须配置 AAA 本地用户',
        'check': lambda config: 'local-user' in config and 'aaa' in config,
        'level': 'HIGH',
        'fix': '系统视图下进入 aaa，配置 local-user'
    },
    {
        'id': 'R004',
        'name': '密码必须使用 cipher 加密存储',
        'check': lambda config: 'password cipher' in config or 'local-user password cipher' in config,
        'level': 'HIGH',
        'fix': '创建用户时使用：local-user <name> password cipher <密码>'
    },
    {
        'id': 'R005',
        'name': '必须配置闲置超时',
        'check': lambda config: 'idle-timeout' in config,
        'level': 'MEDIUM',
        'fix': '用户界面下配置：idle-timeout 10'
    },
    {
        'id': 'R006',
        'name': '不应使用默认 VLAN 1 作为管理 VLAN',
        'check': lambda config: 'interface Vlanif1' not in config,
        'level': 'LOW',
        'fix': '创建独立的设备管理 VLAN，不要用 VLAN 1'
    },
    {
        'id': 'R007',
        'name': '必须配置 SSH 用户认证类型',
        'check': lambda config: 'ssh user' in config and 'authentication-type' in config,
        'level': 'HIGH',
        'fix': '系统视图下执行：ssh user <用户名> authentication-type password'
    },
    {
        'id': 'R008',
        'name': '必须配置 SSH 服务类型',
        'check': lambda config: 'ssh user' in config and 'service-type stelnet' in config,
        'level': 'HIGH',
        'fix': '系统视图下执行：ssh user <用户名> service-type stelnet'
    },
]


def audit_config_file(config_file):
    """审计单个配置文件"""
    print(f"\n{'=' * 60}")
    print(f"审计文件：{os.path.basename(config_file)}")
    print(f"{'=' * 60}\n")
    
    # 读取配置
    with open(config_file, 'r', encoding='utf-8') as f:
        config = f.read()
    
    # 统计
    pass_count = 0
    fail_count = 0
    results = []
    
    # 逐条检查规则
    for rule in BASELINE_RULES:
        rule_id = rule['id']
        rule_name = rule['name']
        rule_level = rule['level']
        check_func = rule['check']
        fix_cmd = rule['fix']
        
        # 执行检查
        passed = check_func(config)
        
        if passed:
            status = '✅ 通过'
            pass_count += 1
        else:
            status = '❌ 不通过'
            fail_count += 1
        
        # 记录结果
        result = {
            'id': rule_id,
            'name': rule_name,
            'level': rule_level,
            'status': status,
            'passed': passed,
            'fix': fix_cmd
        }
        results.append(result)
        
        # 打印结果
        print(f"[{rule_id}] {rule_name}")
        print(f"  级别：{rule_level}")
        print(f"  结果：{status}")
        if not passed:
            print(f"  修复：{fix_cmd}")
        print()
    
    # 打印汇总
    total = len(BASELINE_RULES)
    print(f"{'=' * 60}")
    print(f"审计汇总：")
    print(f"  总规则数：{total}")
    print(f"  通过：{pass_count}")
    print(f"  不通过：{fail_count}")
    print(f"  合规率：{pass_count / total * 100:.1f}%")
    print(f"{'=' * 60}\n")
    
    return results, pass_count, fail_count


def generate_audit_report(all_results, output_file):
    """生成审计报告（Markdown 格式）"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 配置合规审计报告\n\n")
        f.write(f"生成时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"审计规则数：{len(BASELINE_RULES)}\n\n")
        f.write("---\n\n")
        
        for device_name, results in all_results.items():
            f.write(f"## 设备：{device_name}\n\n")
            
            # 统计
            pass_count = sum(1 for r in results if r['passed'])
            fail_count = sum(1 for r in results if not r['passed'])
            total = len(results)
            compliance_rate = pass_count / total * 100 if total > 0 else 0
            
            f.write(f"**合规率：{compliance_rate:.1f}%** ({pass_count}/{total})\n\n")
            
            # 表格
            f.write("| 规则ID | 规则名称 | 级别 | 结果 | 修复建议 |\n")
            f.write("|--------|----------|------|------|----------|\n")
            
            for r in results:
                status_icon = '✅' if r['passed'] else '❌'
                f.write(f"| {r['id']} | {r['name']} | {r['level']} | {status_icon} | {r['fix'] if not r['passed'] else '-'} |\n")
            
            f.write("\n---\n\n")
        
        f.write("\n*报告结束*\n")
    
    print(f"审计报告已生成：{output_file}")


def main(config_files=None):
    """
    合规审计主函数
    :param config_files: 配置文件路径列表（可选，不传则读 sys.argv）
    """
    # 如果不传参数，从命令行读取
    if config_files is None:
        if len(sys.argv) < 2:
            print("用法：python compliance_audit.py <配置文件1> [配置文件2] ...")
            print("\n示例：")
            print("  python compliance_audit.py backups/LSW1_20260628_113000.txt")
            print("  python compliance_audit.py backups/*.txt")
            sys.exit(1)
        config_files = sys.argv[1:]
    
    all_results = {}
    
    print(f"\n开始审计 {len(config_files)} 个配置文件...")
    
    for config_file in config_files:
        if not os.path.exists(config_file):
            print(f"警告：文件不存在 - {config_file}")
            continue
        
        device_name = os.path.basename(config_file).split('_')[0]
        results, _, _ = audit_config_file(config_file)
        all_results[device_name] = results
    
    # 生成汇总报告
    if all_results:
        timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
        # 报告保存到第一个配置文件所在目录
        output_dir = os.path.dirname(config_files[0]) if os.path.dirname(config_files[0]) else '.'
        output_file = os.path.join(output_dir, f"audit_report_{timestamp}.md")
        generate_audit_report(all_results, output_file)
        print(f"\n汇总报告：{output_file}")


if __name__ == '__main__':
    main()
