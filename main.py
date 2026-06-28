#!/usr/bin/env python3
"""
企业网络设备管理系统 - 主程序
=====================================
功能整合：
  1. push   - 配置下发（push_config.py）
  2. backup - 配置备份（backup.py）
  3. diff   - 配置变更检测（config_diff.py）
  4. audit  - 合规审计（compliance_audit.py）

使用方式：
  python main.py <命令> [选项]

示例：
  python main.py push              # 推送配置到所有设备
  python main.py backup            # 备份所有设备配置
  python main.py diff old.txt new.txt   # 对比两个配置文件
  python main.py audit config.txt       # 审计单个配置文件

作者：王玉强
日期：2026-06-28
"""

import sys
import os
import argparse
from pathlib import Path

# 获取脚本目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_push():
    """运行配置下发"""
    print("=" * 60)
    print("配置下发模式")
    print("=" * 60 + "\n")
    
    # 导入 push_config 模块
    sys.path.insert(0, SCRIPT_DIR)
    import push_config
    
    # 执行推送
    push_config.main()


def run_backup():
    """运行配置备份"""
    print("=" * 60)
    print("配置备份模式")
    print("=" * 60 + "\n")
    
    sys.path.insert(0, SCRIPT_DIR)
    import backup
    
    backup.main()


def run_diff(args):
    """运行配置变更检测"""
    print("=" * 60)
    print("配置变更检测模式")
    print("=" * 60 + "\n")
    
    if len(args) < 2:
        print("错误：需要提供两个配置文件")
        print("用法：python main.py diff <旧配置文件> <新配置文件>")
        sys.exit(1)
    
    old_file = args[0]
    new_file = args[1]
    
    if not os.path.exists(old_file):
        print(f"错误：旧配置文件不存在 - {old_file}")
        sys.exit(1)
    if not os.path.exists(new_file):
        print(f"错误：新配置文件不存在 - {new_file}")
        sys.exit(1)
    
    # 导入 config_diff 模块
    sys.path.insert(0, SCRIPT_DIR)
    import config_diff
    
    # 生成文本摘要
    config_diff.generate_diff_text(old_file, new_file)
    
    # 生成 HTML 报告
    output_file = None
    if len(args) > 2:
        output_file = args[2]
    
    config_diff.generate_diff_html(old_file, new_file, output_file)


def run_audit(args):
    """运行合规审计"""
    print("=" * 60)
    print("合规审计模式")
    print("=" * 60 + "\n")
    
    if len(args) < 1:
        print("错误：需要提供配置文件")
        print("用法：python main.py audit <配置文件1> [配置文件2] ...")
        sys.exit(1)
    
    config_files = args
    
    # 检查文件是否存在
    for config_file in config_files:
        if not os.path.exists(config_file):
            print(f"错误：配置文件不存在 - {config_file}")
            sys.exit(1)
    
    # 导入 compliance_audit 模块
    sys.path.insert(0, SCRIPT_DIR)
    import compliance_audit
    
    # 执行审计（传入文件列表）
    compliance_audit.main(config_files)


def main():
    parser = argparse.ArgumentParser(
        description='企业网络设备管理系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python main.py push                    # 推送配置到所有设备
  python main.py backup                  # 备份所有设备配置
  python main.py diff old.txt new.txt   # 对比两个配置文件
  python main.py audit config.txt       # 审计单个配置文件
  python main.py audit backups/*.txt    # 审计多个配置文件
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # push 命令
    push_parser = subparsers.add_parser('push', help='推送配置到设备')
    
    # backup 命令
    backup_parser = subparsers.add_parser('backup', help='备份设备配置')
    
    # diff 命令
    diff_parser = subparsers.add_parser('diff', help='对比配置文件')
    diff_parser.add_argument('files', nargs='+', help='配置文件列表（至少2个）')
    
    # audit 命令
    audit_parser = subparsers.add_parser('audit', help='审计配置文件')
    audit_parser.add_argument('files', nargs='+', help='配置文件列表')
    
    # 解析参数
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # 根据命令执行对应功能
    if args.command == 'push':
        run_push()
    elif args.command == 'backup':
        run_backup()
    elif args.command == 'diff':
        run_diff(args.files)
    elif args.command == 'audit':
        run_audit(args.files)


if __name__ == '__main__':
    main()
