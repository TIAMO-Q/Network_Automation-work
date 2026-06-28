# 企业网络设备批量配置与审计系统

基于 Python + Netmiko + Jinja2 的华为网络设备自动化管理工具，支持配置下发、备份、变更检测、合规审计四大功能。

## 功能特性

- 📋 **CSV 驱动**：设备信息、端口、VLAN、网关统一管理
- 🔁 **Jinja2 模板**：按设备角色（gateway/access）自动生成配置
- 🚀 **批量推送**：通过 SSH 批量登录设备并下发配置
- 💾 **配置备份**：自动备份设备配置到本地，按设备名+时间戳命名
- 🔍 **变更检测**：使用 difflib 对比两次备份，生成 HTML 可视化变更报告
- 🔒 **合规审计**：基于基线规则检查配置安全性，生成审计报告
- 📝 **会话日志**：每次推送保存完整 SSH 会话，便于排查

## 项目结构

```
net-backup-audit/
├── main.py                # 主程序入口（整合所有功能）
├── push_config.py         # 批量配置推送
├── backup.py              # 配置备份
├── config_diff.py         # 配置变更检测
├── compliance_audit.py   # 合规审计
├── network_devices.csv    # 设备清单
├── network_template.j2   # Jinja2 配置模板
├── backups/              # 配置备份目录（自动创建）
└── .gitignore
```

## 环境依赖

```bash
# 创建虚拟环境（推荐）
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install netmiko jinja2
```

## 使用方法

### 方式一：使用主程序（推荐）

```bash
# 推送配置到所有设备
python main.py push

# 备份所有设备配置
python main.py backup

# 对比两个配置文件（生成 HTML 报告）
python main.py diff backups/LSW1_20260628_113000.txt backups/LSW1_20260628_143000.txt

# 审计单个配置文件
python main.py audit backups/LSW1_20260628_113000.txt

# 审计多个配置文件
python main.py audit backups/*.txt
```

### 方式二：直接运行单个脚本

```bash
# 配置下发
python push_config.py

# 配置备份
python backup.py

# 配置变更检测
python config_diff.py backups/LSW1_20260628_113000.txt backups/LSW1_20260628_143000.txt

# 合规审计
python compliance_audit.py backups/LSW1_20260628_113000.txt
```

## 配置说明

### 1. 准备设备清单（network_devices.csv）

```csv
hostname,ip,username,password,role,vlans,access_ports,trunk_ports,gateway_vlans,stp_mode
LSW1,16.0.0.11,python,Huawei@123,gateway,1|10|20,,Eth0/0/1|Eth0/0/2,10:192.168.10.254:255.255.255.0|20:192.168.20.254:255.255.255.0,rstp
LSW2,16.0.0.22,python,Huawei@123,access,10|20,Eth0/0/2:10|Eth0/0/3:20,Eth0/0/1,,rstp
LSW3,16.0.0.33,python,Huawei@123,access,10|20,Eth0/0/2:10|Eth0/0/3:20,Eth0/0/1,,rstp
```

**字段说明：**
- `hostname`：设备主机名
- `ip`：设备管理 IP
- `username/password`：SSH 登录凭据
- `role`：设备角色（`gateway` 或 `access`）
- `vlans`：设备包含的 VLAN 列表（用 `|` 分隔）
- `access_ports`：Access 端口配置（`端口名:VLAN|...`）
- `trunk_ports`：Trunk 端口列表（用 `|` 分隔）
- `gateway_vlans`：网关 VLAN 配置（`VLAN:IP:掩码|...`）
- `stp_mode`：生成树协议模式（`rstp`/`stp`/`mstp`）

### 2. 配置 Jinja2 模板（network_template.j2）

模板按角色自动渲染不同配置，支持：
- 系统配置（sysname、STP）
- Access 端口配置
- Trunk 端口配置
- 网关 VLAN 接口配置（仅 gateway 角色）

### 3. 运行脚本

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

## 合规审计规则

系统内置 8 条基线规则（可在 `compliance_audit.py` 中自定义扩展）：

| 规则ID | 规则名称 | 级别 |
|--------|----------|------|
| R001 | SSH 服务必须启用 | HIGH |
| R002 | Telnet 服务应禁用 | MEDIUM |
| R003 | 必须配置 AAA 本地用户 | HIGH |
| R004 | 密码必须使用 cipher 加密存储 | HIGH |
| R005 | 必须配置闲置超时 | MEDIUM |
| R006 | 不应使用默认 VLAN 1 作为管理 VLAN | LOW |
| R007 | 必须配置 SSH 用户认证类型 | HIGH |
| R008 | 必须配置 SSH 服务类型 | HIGH |

## 实验拓扑

```
PC1(vlan10) ── LSW2 ──┐
PC2(vlan20) ── LSW2    ├── LSW1(gateway) ── Cloud1(管理网)
PC3(vlan10) ── LSW3 ──┘
PC4(vlan20) ── LSW3
```

**管理网段：** 16.0.0.x/24（通过 Cloud1 桥接本机）  
**业务 VLAN10：** 192.168.10.0/24，网关 192.168.10.254  
**业务 VLAN20：** 192.168.20.0/24，网关 192.168.20.254

## 踩坑记录

| 问题 | 原因 | 解决 |
|------|------|------|
| `device_type` 报错 | 写了 `'huawei'`，正确是 `'huawei_vrp'` | 改用 `huawei_vrp` |
| eNSP 推送超时 | 模拟器性能弱，命令间隔太短 | 加 `fast_cli=False`、`global_delay_factor=2` |
| Trunk 隔断管理 VLAN | Trunk 未放行 VLAN 1 | `port trunk allow-pass vlan 1 10 20` |
| 端口改 link-type 报错 | 端口有旧配置 | 先 `undo` 再重配 |
| SSH 服务假死 | eNSP 模拟器 bug | 重新生成 RSA 密钥或重启设备 |
| `read_timeout` 参数报错 | 不是 ConnectHandler 的有效参数 | 改用 `timeout` 参数 |

## 后续计划

- [x] 配置下发（push_config.py）
- [x] 配置备份（backup.py）
- [x] 配置变更检测（config_diff.py）
- [x] 合规审计（compliance_audit.py）
- [ ] Web 可视化界面
- [ ] 数据库存储（MySQL/SQLite）
- [ ] 邮件告警功能

## 作者

王玉强 — 网络工程专业，方向 NetDevOps / 自动化网络工程师  

GitHub：https://github.com/TIAMO-Q/Network_Automation-work
