import argparse
import configparser
import os
import subprocess

# Создаем объект-парсер для анализа аргументов командной строки
parser = argparse.ArgumentParser()

# Добавляем аргумент для указания пути к файлу настроек
parser.add_argument("-s", "--settings", help="Путь к файлу настроек", required=True)

# Добавляем аргумент для указания IP-адреса
parser.add_argument("-ip", "--ip_address", help="IP-адрес для проверки в правилах брандмауэра", required=True)

# Добавляем аргумент для указания действия (удалить или пропустить)
parser.add_argument("-a", "--action",
                    help="Действия, которые необходимо предпринять, если IP-адрес найден (delete или skip)",
                    choices=["delete", "skip"], default="skip")

# Парсим аргументы командной строки
args = parser.parse_args()

# Читаем файл настроек
config = configparser.ConfigParser()
config.read(args.settings)

# Получаем список правил брандмауэра из файла настроек
firewall_rules = config["FirewallRules"]["rules"].split(",")

# Создаем список правил, содержащих указанный IP-адрес
rules_with_ip = []
for rule in firewall_rules:
    # Выполняем команду PowerShell в CMD Windows и сохраняем ее вывод в переменной
    result = subprocess.run(
        ["cmd", "/c", "powershell", "-Command", f"Get-NetFirewallRule -DisplayName {rule} | Get-NetFirewallAddressFilter -RemoteAddress | Where-Object {{ $_ -match '{args.ip_address}' }}"],
        stdout=subprocess.PIPE,
    )

    # Если вывод не пустой, добавляем правило в список
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
                    ["cmd", "/c", "powershell", "-Command", f"Get-NetFirewallRule -DisplayName {rule} | Get-NetFirewallAddressFilter -RemoteAddress"],
                    stdout=subprocess.PIPE,
                ).stdout.decode("utf-8").splitlines()

                # Удаляем указанный IP-адрес из списка
                new_ips = [ip for ip in current_ips if ip != args.ip_address]

                # Обновляем правило новым списком IP-адресов.
                subprocess.run(
                    ["cmd", "/c", "powershell", "-Command", f"Get-NetFirewallrule -DisplayName {rule} | Set-NetFirewallRule -RemoteAddress {new_ips}"],
                )
                print(f"IP-адрес из правила: {rule} --- УДАЛЕН")
        else:
            print("Пропускаем удаление.")
else:
    print("Указанный IP-адрес не найден ни в одном из правил брандмауэра..")

# Добавляем поддержку ОС Windows начиная с версии 2008 R2
if os.name == "nt":
    os_version = os.getenv("OSVERSION", "").split(".")[0]
    if int(os_version) >= 6:
        # Выполняем команды в повышенном режиме
        subprocess.run(["cmd", "/c", "net stop winmgmt"], shell=True)
        subprocess.run(["cmd", "/c", "sc config winmgmt start= auto"], shell=True)
        subprocess.run(["cmd", "/c", "net start winmgmt"], shell=True)
