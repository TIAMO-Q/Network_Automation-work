# 企业网络设备批量配置系统

基于 Python + Netmiko + Jinja2 的华为网络设备批量配置推送工具，支持从 CSV 设备清单读取信息，按角色自动生成配置并批量下发。

## 功能特性

- 📋 **CSV 驱动**：设备信息、端口、VLAN、网关统一管理
- 🔁 **Jinja2 模板**：按设备角色（gateway/access）自动生成对应配置
- 🚀 **批量推送**：通过 SSH 批量登录设备并下发配置
- 📝 **会话日志**：每次推送保存完整 SSH 会话，便于排查

## 项目结构

```
net-backup-audit/
├── push_config.py        # 批量配置推送主脚本
├── backup.py             # 配置备份脚本
├── network_devices.csv   # 设备清单（IP、角色、VLAN、端口等）
├── network_template.j2  # Jinja2 配置模板
└── .gitignore
```

## 环境依赖

```bash
pip install netmiko jinja2 pandas
```

## 使用方法

### 1. 准备设备清单

编辑 `network_devices.csv`，填写设备信息：

```csv
hostname,ip,username,password,role,vlans,access_ports,trunk_ports,gateway_vlans,stp_mode
LSW1,16.0.0.11,python,Huawei@123,gateway,1|10|20,,Eth0/0/1|Eth0/0/2,10:192.168.10.254:255.255.255.0|20:192.168.20.254:255.255.255.0,rstp
LSW2,16.0.0.22,python,Huawei@123,access,10|20,Eth0/0/2:10|Eth0/0/3:20,Eth0/0/1,,rstp
```

### 2. 配置 Jinja2 模板

编辑 `network_template.j2`，按角色定义配置模板（支持 `gateway` 和 `access` 两种角色）。

### 3. 运行推送脚本

```bash
python push_config.py
```

## 适用设备

- 华为 S 系列交换机（S3700、S5700 等）
- 设备需提前配置 SSH（stelnet）

## 华为设备 SSH 配置参考

```bash
system-view
aaa
 local-user python password cipher Huawei@123
 local-user python service-type ssh
 local-user python privilege level 15
quit
rsa local-key-pair create
stelnet server enable
ssh user python authentication-type password
ssh user python service-type stelnet
user-interface vty 0 4
 authentication-mode aaa
 protocol inbound ssh
quit
save
```

## 实验拓扑

```
PC1(vlan10) ── LSW2 ──┐
PC2(vlan20) ── LSW2    ├── LSW1(gateway) ── 上行链路
PC3(vlan10) ── LSW3 ──┘
PC4(vlan20) ── LSW3
```

## 踩坑记录

| 问题 | 原因 | 解决 |
|------|------|------|
| `device_type` 报错 | 写了 `'huawei'`，正确是 `'huawei_vrp'` | 改用 `huawei_vrp` |
| eNSP 推送超时 | 模拟器性能弱，命令间隔太短 | 加 `fast_cli=False`、`global_delay_factor=2` |
| Trunk 隔断管理 VLAN | Trunk 未放行 VLAN 1 | `port trunk allow-pass vlan 1 10 20` |
| 端口改 link-type 报错 | 端口有旧配置 | 先 `undo` 再重配 |

## 后续计划

- [ ] 配置备份（自动 `display current-configuration` 存本地）
- [ ] 配置变更检测（difflib 对比版本差异）
- [ ] 合规审计（检查配置是否符合基线）

## 作者

王玉强 — 网络工程专业，方向 NetDevOps / 自动化网络工程师
