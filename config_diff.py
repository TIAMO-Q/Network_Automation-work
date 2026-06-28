"""
配置变更检测脚本
================================
功能：对比两次备份的配置文件，使用 difflib 生成变更报告（HTML格式）
    高亮显示新增、删除、修改的配置行

使用方式：
    python config_diff.py <旧配置文> <新配置文件> [输出HTML文]

示例：
    python config_diff.py backups/LSW1_20260628_113000.txt backups/LSW1_20260628_143000.txt

作者：王玉强
日期：2026-06-28
"""

import sys
import os
import difflib
from datetime import datetime


def read_config_file(filepath):
    """读取配置文件，返回行列表"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return lines


def generate_diff_html(old_file, new_file, output_file=None):
    """
    生成 HTML 格式的变更报告
    - 红色：删除的行（旧配置有，新配置没有）
    - 绿色：新增的行（新配置有，旧配置没有）
    - 白色：未改变的行
    """
    # 读取文件
    old_lines = read_config_file(old_file)
    new_lines = read_config_file(new_file)
    
    # 生成差异
    diff = difflib.HtmlDiff().make_file(
        old_lines, new_lines,
        fromdesc=f"旧配置：{os.path.basename(old_file)}",
        todesc=f"新配置：{os.path.basename(new_file)}",
        context=True,  # 只显示有变化的上下文
        numlines=3     # 上下文行数
    )
    
    # 确定输出文件名
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        basename = os.path.basename(old_file).split('_')[0]  # 取主机名
        output_file = os.path.join(os.path.dirname(old_file), f"diff_{basename}_{timestamp}.html")
    
    # 保存 HTML
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(diff)
    
    print(f"变更报告已生成：{output_file}")
    print(f"请用浏览器打开查看")
    
    return output_file


def generate_diff_text(old_file, new_file):
    """生成文本格式的变更摘要（用于命令行快速查看）"""
    old_lines = read_config_file(old_file)
    new_lines = read_config_file(new_file)
    
    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile=os.path.basename(old_file),
        tofile=os.path.basename(new_file),
        lineterm=''
    )
    
    changes = list(diff)
    if not changes:
        print("配置无变化")
        return []
    
    print(f"\n配置变更摘要：")
    print('=' * 60)
    for line in changes:
        print(line, end='')
    print('=' * 60)
    
    return changes


def main():
    if len(sys.argv) < 3:
        print("用法：python config_diff.py <旧配置文件> <新配置文件> [输出HTML文件]")
        print("\n示例：")
        print("  python config_diff.py backups/LSW1_20260628_113000.txt backups/LSW1_20260628_143000.txt")
        sys.exit(1)
    
    old_file = sys.argv[1]
    new_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # 检查文件是否存在
    if not os.path.exists(old_file):
        print(f"错误：旧配置文件不存在 - {old_file}")
        sys.exit(1)
    if not os.path.exists(new_file):
        print(f"错误：新配置文件不存在 - {new_file}")
        sys.exit(1)
    
    print(f"对比配置：")
    print(f"  旧配置：{old_file}")
    print(f"  新配置：{new_file}\n")
    
    # 生成文本摘要
    generate_diff_text(old_file, new_file)
    
    # 生成 HTML 详细报告
    html_file = generate_diff_html(old_file, new_file, output_file)
    
    print(f"\n详细报告（HTML）：{html_file}")


if __name__ == '__main__':
    main()
