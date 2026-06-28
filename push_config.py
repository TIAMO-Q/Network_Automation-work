"""
企业网配置批量推送脚本
================================
功能：从 CSV 读取设备清单 -> Jinja2 渲染配置 -> Netmiko SSH 推送

支持两种设备角色：
  - gateway（三层汇聚）：推送 Vlanif 网关接口
  - access（二层接入）：推送 Access/Trunk 端口

        当前拓扑：
         Cloud1 -> LSW1(S3700,汇聚) -> LSW2(S3700,接入) / LSW3(S3700,接入)
  管理网段 VLAN1: 16.0.0.x（通过 Cloud1 桥接本机）
  业务 VLAN10(办公): 192.168.10.0/24  网关 192.168.10.254
  业务 VLAN20(服务器): 192.168.20.0/24  网关 192.168.20.254

依赖：pip install netmiko jinja2
运行：python push_config.py

作者：王玉强
日期：2026-06-22
"""

import csv
import os
from jinja2 import Template
from netmiko import ConnectHandler
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, 'network_template.j2')
CSV_PATH = os.path.join(SCRIPT_DIR, 'network_devices.csv')


# 1. 加载模板
with open(TEMPLATE_PATH, encoding='utf-8') as f:
    template = Template(f.read())

# 2. 读取 CSV
with open(CSV_PATH, encoding='utf-8') as f:
    devices = list(csv.DictReader(f))

print(f"共读取 {len(devices)} 台设备")
print(f"开始时间：{datetime.now()}\n")


# 3. 解析工具函数
def parse_access_ports(s):
    """解析 Access 端口
    输入：'Eth0/0/2:10|Eth0/0/3:20'
    输出：[{'name': 'Eth0/0/2', 'vlan': '10'}, ...]
    """
    result = []
    if not s.strip():
        return result
    for item in s.split('|'):
        name, vlan = item.split(':')
        result.append({'name': name.strip(), 'vlan': vlan.strip()})
    return result


def parse_trunk_ports(s, vlans):
    """解析 Trunk 端口
    输入：'Eth0/0/1|GE0/0/2'  vlans=['10','20']
    输出：[{'name': 'Eth0/0/1', 'vlans': ['10','20']}, ...]
    说明：所有 trunk 口统一放行所有业务 VLAN
    """
    result = []
    if not s.strip():
        return result
    for name in s.split('|'):
        result.append({'name': name.strip(), 'vlans': vlans})
    return result


def parse_gateway_vlans(s):
    """解析网关 Vlanif
    输入：'10:192.168.10.254:255.255.255.0|20:192.168.20.254:255.255.255.0'
    输出：[{'vlan': '10', 'ip': '192.168.10.254', 'mask': '255.255.255.0'}, ...]
    """
    result = []
    if not s.strip():
        return result
    for item in s.split('|'):
        vlan, ip, mask = item.split(':')
        result.append({'vlan': vlan.strip(), 'ip': ip.strip(), 'mask': mask.strip()})
    return result


# 4. 遍历每台设备：渲染 + 推送
for row in devices:
    vlans = row['vlans'].split('|')           # ['10', '20']
    access_ports = parse_access_ports(row['access_ports'])
    trunk_ports = parse_trunk_ports(row['trunk_ports'], vlans)
    gateway_vlans = parse_gateway_vlans(row.get('gateway_vlans', ''))

    # 渲染模板
    config = template.render(
        hostname=row['hostname'],
        role=row['role'],
        vlans=vlans,
        access_ports=access_ports,
        trunk_ports=trunk_ports,
        gateway_vlans=gateway_vlans,
        stp_mode=row['stp_mode'],
    )
    # 过滤空行（Jinja2 循环/条件为空时会产生空行）
    config_set = [cmd for cmd in config.split('\n') if cmd.strip()]

    print('=' * 60)
    print(f"设备：{row['hostname']} ({row['ip']}) 角色：{row['role']}")
    print('=' * 60)
    print("生成配置：")
    print('\n'.join(config_set))
    print()

    # 5. 推送到设备
    device = {
        'device_type': 'huawei_vrp',
        'host': row['ip'],
        'username': row['username'],
        'password': row['password'],
        'session_log': os.path.join(SCRIPT_DIR, f"{row['hostname']}_session.txt"),
        'fast_cli': False,              # 关闭快速模式，eNSP 设备性能弱
        'global_delay_factor': 2,       # 命令间延迟加倍
        'timeout': 30,                  # 连接/读取超时从默认提到 30s
    }

    try:
        conn = ConnectHandler(**device)
        output = conn.send_config_set(config_set, cmd_verify=False)
        print(f"[{row['hostname']}] 推送结果：")
        print(output)
        conn.save_config()   # save 到 flash
        conn.disconnect()
        print(f"[{row['hostname']}] 配置已保存 OK\n")
    except Exception as e:
        print(f"[{row['hostname']}] 推送失败：{e}\n")

print(f"全部完成：{datetime.now()}")
