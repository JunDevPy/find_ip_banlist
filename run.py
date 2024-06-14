import argparse
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("-ip", "--ip_address", help="IP-адрес для проверки в правилах брандмауэра", required=True)
parser.add_argument("-a", "--action",
                    help="Действия, которые необходимо предпринять, если IP-адрес найден (delete или skip)",
                    choices=["delete", "skip"], default="skip")
args = parser.parse_args()

# Получаем список правил брандмауэра, в которых надо искать
firewall_rules = [
    "IPBan_Block_0",
    "IPBan_EmergingThreats_0",
    "IPBan_EmergingThreats_1000",
    "IPBan_GlobalBlacklist_0",
]
rules_with_ip = []
for rule in firewall_rules:
    result = subprocess.run(
        ['@powershell', '-Command', 'Get-NetFirewallRule', '-DisplayName', rule, '|',
         'Get-NetFirewallAddressFilter', '-RemoteAddress', '|', 'Where-Object',
         '{ $_ -match \'' + args.ip_address + '\' }'],
        stdout=subprocess.PIPE,
    )
    if result.stdout:
        rules_with_ip.append(rule)

# Распечатать список правил, содержащих указанный IP-адрес
if rules_with_ip:
    print("Следующие правила брандмауэра содержат указанный IP-адрес:")
    for rule in rules_with_ip:
        print(f"  - {rule}")

    # Запрашиваем у пользователя подтверждение, следует ли удалять IP-адрес из правил
    if args.action == "delete":
        confirm = input(f"Хотите удалить IP-адрес из этих правил? (y/n) ")
        if confirm.lower() == "y":
            for rule in rules_with_ip:
                # Получаем текущий список удаленных IP-адресов для правила
                current_ips = subprocess.run(
                    ['@powershell', '-Command', 'Get-NetFirewallRule', '-DisplayName', rule, '|',
                     'Get-NetFirewallAddressFilter', '-RemoteAddress'],
                    stdout=subprocess.PIPE,
                ).stdout.decode("utf-8").splitlines()

                # Удаляем указанный IP-адрес из списка
                new_ips = [ip for ip in current_ips if ip != args.ip_address]

                # Обновляем правило новым списком IP-адресов.
                subprocess.run(
                    ['@powershell', '-Command', '"', 'Get-NetFirewallrule', '-DisplayName', rule, '|', 'Set-NetFirewallRule',
                     '-RemoteAddress', new_ips, '"'],
                )
                print(f"IP-адрес из правила: {rule} --- УДАЛЕН")
        else:
            print("Пропускаем удаление.")
else:
    print("Указанный IP-адрес не найден ни в одном из правил брандмауэра..")
