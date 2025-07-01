import re
import time
import json

from mcdreforged.api.all import *

def tr(key, *args):
    return ServerInterface.get_instance().tr(f"ThunderstormAlert.{key}", *args)

def command_register(server: PluginServerInterface):
    builder = SimpleCommandBuilder()
    builder.command('!!thunder', get_status)
    builder.command('!!thunder help', get_help)
    builder.command('!!thunder interval <interval>', set_interval)
    builder.command('!!thunder cooldown <cooldown>', set_cooldown)
    builder.command('!!thunder start', start_weather_check)
    builder.command('!!thunder stop', stop_weather_check)

    builder.arg('interval', Text)
    builder.arg('cooldown', Text)

    builder.register(server)

class Config(Serializable):
    message: str = '§c雷暴来了§r'
    check_interval: str = "20s"
    cooldown: str = "300s"
    def save(self):
        global message, check_interval, cooldown
        message, check_interval, cooldown = get_config()
        dict_config = {
            "message": self.message,
            "check_interval": self.check_interval,
            "cooldown": self.cooldown
        }
        with open('./config/ThunderstormAlert/config.json', 'w', encoding='utf-8') as f:
            json.dump(dict_config, f, ensure_ascii=False, indent=4)

STATUS = True

messages = "§c雷暴来了§r"
check_interval = "20s"
cooldown = "300s"
config: Config

last_alert_time = 0


def on_load(server: PluginServerInterface, old):
    command_register(server)
    global config, check_interval, cooldown,messages, last_alert_time
    config = server.load_config_simple(
        'config.json',
        target_class=Config
    )
    try:
        check_interval, cooldown, message = get_config()

    except Exception as e:
        server.logger.error(tr('error.fail_to_load_config'), e)
        messages = "§c雷暴来了§r"
        check_interval = "20s"
        cooldown = "300s"

    last_alert_time = time.time()

    periodic_weather_check(server)

def get_config():
    global config
    return config.check_interval, config.cooldown, config.message

def parse_time_string(time):
    time_units = {
        's': 1,
        'm': 60,
        'h': 3600
    }
    match = re.match(r'(\d+)([smh])', time)
    if not match:
        ServerInterface.get_instance().logger.error(f"{tr('error.interval_too_short')}:{time}")
    number, unit = match.groups()
    return int(number) * time_units[unit]

@new_thread
def periodic_weather_check(server):
    global STATUS,check_interval
    interval = parse_time_string(check_interval)
    while STATUS:
        time.sleep(interval)
        server.execute_command('weather query')

def get_help(source: CommandSource):
    source.reply(tr("help_message"))

def set_interval(source: CommandSource, context: CommandContext):
    global config
    config.check_interval = context['interval']
    source.reply(tr("success_set_interval"))
    config.save()

def set_cooldown(source: CommandSource, context: CommandContext):
    global config
    config.cooldown = context['cooldown']
    source.reply(tr("success_set_cooldown"))
    config.save()

def start_weather_check(source: CommandSource):
    global STATUS
    if not STATUS:
        STATUS = True
        source.reply(tr("start_weather_check"))
    else:
        source.reply(tr("weather_check_is_running"))

def stop_weather_check(source: CommandSource):
    global STATUS
    if STATUS :
        STATUS = True
        source.reply(tr("stop_weather_check"))
    else:
        source.reply(tr("weather_check_is_not_running"))

def on_info(server, info):
    global last_alert_time
    #  Weather state is: thunder
    if not info.is_user and info.content.startswith('Weather state is'):
        weather = info.content.split(':')[1].strip().lower()
        current_time = time.time()
        cooldown = parse_time_string(config.cooldown)
        if 'thunder' in weather and current_time - last_alert_time >= cooldown:
            last_alert_time = current_time
            server.say(config.message)

def get_status(source: CommandSource):
    global STATUS
    if STATUS:
        source.reply(tr("weather_check_is_running"))
    else:
        source.reply(tr("weather_check_is_not_running"))
    source.reply(f"""
        Check interval: {config.check_interval}
        Cooldown: {config.cooldown}
    """)