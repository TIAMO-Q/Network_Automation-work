from netmiko import ConnectHandler
sw1 = {
    'device_type': 'huawei_vrp',
    'ip': '16.0.0.22',
    'username': 'python',
    'password': 'Huawei@123',
    'fast_cli': False,          # ← 加这行
}
connection = ConnectHandler(**sw1)
print('success connect to', sw1['ip'])