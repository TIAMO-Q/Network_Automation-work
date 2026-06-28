"""
企业网配置备份脚本
================================
功能：从 CSV 读取设备清单 -> Netmiko SSH 登录 -> 执行 display current-configuration -> 保存配置到本地

配置文件名格式：backups/{hostname}_{timestamp}.txt
备份目录：backups/（自动创建）

依赖：pip install netmiko
运行：python backup.py

作者：王玉强
日期：2026-06-28
"""

import csv
import os
import time
from datetime import datetime
from netmiko import ConnectHandler


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, 'network_devices.csv')
BACKUP_DIR = os.path.join(SCRIPT_DIR, 'backups')


def ensure_backup_dir():
    """确保备份目录存在"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"创建备份目录：{BACKUP_DIR}")


def get_timestamp():
    """生成时间戳字符串，用于文件名"""
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def backup_device(row):
    """备份单台设备的配置"""
    hostname = row['hostname']
    ip = row['ip']
    
    device = {
        'device_type': 'huawei_vrp',
        'host': ip,
        'username': row['username'],
        'password': row['password'],
        'fast_cli': False,
        'global_delay_factor': 2,
        'timeout': 30,
    }
    
    timestamp = get_timestamp()
    filename = f"{hostname}_{timestamp}.txt"
    filepath = os.path.join(BACKUP_DIR, filename)
    
    print(f"[{hostname}] 开始备份 {ip} ...")
    
    try:
        conn = ConnectHandler(**device)
        print(f"[{hostname}] SSH 连接成功")
        
        # 执行 display current-configuration 获取完整配置
        print(f"[{hostname}] 正在读取配置...")
        output = conn.send_command(
            'display current-configuration',
            read_timeout=60  # 配置长，超时设长一点
        )
        
        # 保存到文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"! 设备：{hostname} ({ip})\n")
            f.write(f"! 备份时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"! {'=' * 60}\n\n")
            f.write(output)
            f.write(f"\n\n! {'=' * 60}\n")
            f.write(f"! 备份完成\n")
        
        print(f"[{hostname}] 配置已保存：{filename}")
        print(f"[{hostname}] 文件大小：{os.path.getsize(filepath)} 字节\n")
        
        conn.disconnect()
        return True, filepath
        
    except Exception as e:
        print(f"[{hostname}] 备份失败：{e}\n")
        return False, None


def main():
    # 确保备份目录存在
    ensure_backup_dir()
    
    # 读取设备清单
    with open(CSV_PATH, encoding='utf-8') as f:
        devices = list(csv.DictReader(f))
    
    print(f"共读取 {len(devices)} 台设备")
    print(f"开始时间：{datetime.now()}\n")
    
    # 备份统计
    success_count = 0
    fail_list = []
    
    # 遍历每台设备
    for row in devices:
        ok, filepath = backup_device(row)
        if ok:
            success_count += 1
        else:
            fail_list.append(row['hostname'])
        
        # 设备之间稍微间隔，避免并发问题
        time.sleep(1)
    
    # 输出统计
    print('=' * 60)
    print(f"备份完成：{datetime.now()}")
    print(f"成功：{success_count}/{len(devices)} 台")
    if fail_list:
        print(f"失败设备：{', '.join(fail_list)}")
    print('=' * 60)
    
    return success_count, fail_list


if __name__ == '__main__':
    main()
