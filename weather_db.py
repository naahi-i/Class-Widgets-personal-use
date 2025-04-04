import datetime
import sqlite3
import json
from loguru import logger

from conf import base_directory
from file import config_center

path = f'{base_directory}/config/data/xiaomi_weather.db'
api_config = json.load(open(f'{base_directory}/config/data/weather_api.json', encoding='utf-8'))


def update_path():
    global path
    path = (f"{base_directory}/config/"
            f"data/{api_config['weather_api_parameters'][config_center.read_conf('Weather', 'api')]['database']}")


def search_by_name(search_term):
    update_path()
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM citys WHERE name LIKE ?', ('%' + search_term + '%',))  # 模糊查询
    cities_results = cursor.fetchall()
    conn.close()
    result_list = []
    for city in cities_results:
        result_list.append(city[2])
    # 返回两个表的搜索结果
    return result_list


def search_code_by_name(search_term):
    if search_term == ('', ''):
        return 101010100
    update_path()
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    logger.info(f"Searching for city: {search_term}")
    search_term = (search_term[0].replace('市',''), search_term[1].replace('区',''))

    cursor.execute('SELECT * FROM citys WHERE name = ?', (f"{search_term[0]}.{search_term[1]}",))
    exact_results = cursor.fetchall()
    
    if not exact_results:
        search_term = search_term[0]
        cursor.execute('SELECT * FROM citys WHERE name LIKE ?', ('%' + f"{search_term}" + '%',))
        cities_results = cursor.fetchall()
    else:
        cities_results = exact_results
    
    conn.close()

    if cities_results:
        # 多结果优先完全匹配,否则返回第一个
        for city in cities_results:
            if city[2] == search_term or city[2] == search_term + '市' or city[2] + '市' == search_term:
                logger.debug(f"找到城市: {city[2]}，代码: {city[3]}")
                return city[3]
        result = cities_results[0][3]
        logger.debug(f"模糊找到城市: {cities_results[0][2]}，代码: {result}")
    else:
        result = "101010100"  # 默认城市代码
        logger.warning(f'未找到城市: {search_term}，使用默认城市代码')

    return result


def search_by_num(search_term):
    update_path()
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM citys WHERE city_num LIKE ?', ('%' + search_term + '%',))  # 模糊查询
    cities_results = cursor.fetchall()

    conn.close()

    if cities_results:
        result = cities_results[0][2]
    else:
        result = '北京'  # 默认城市
    # 返回两个表的搜索结果
    return result


def get_weather_by_code(code):  # 用代码获取天气描述
    weather_status = json.load(
        open(f"{base_directory}/config/data/{config_center.read_conf('Weather', 'api')}_status.json", encoding="utf-8"))
    for weather in weather_status['weatherinfo']:
        if str(weather['code']) == code:
            return weather['wea']
    return '未知'


def get_weather_icon_by_code(code):  # 用代码获取天气图标
    weather_status = json.load(
        open(f"{base_directory}/config/data/{config_center.read_conf('Weather', 'api')}_status.json",
             encoding="utf-8")
    )
    weather_code = None
    current_time = datetime.datetime.now()
    # 遍历获取天气代码
    for weather in weather_status['weatherinfo']:
        if str(weather['code']) == code:
            original_code = weather.get('original_code')
            if original_code is not None:
                weather_code = str(weather['original_code'])
            else:
                weather_code = str(weather['code'])
            break
    if not weather_code:
        logger.error(f'未找到天气代码 {code}')
        return f'{base_directory}/img/weather/99.svg'
    # 根据天气和时间获取天气图标
    if weather_code in ('0', '1', '3', '13'):  # 晴、多云、阵雨、阵雪
        if current_time.hour < 6 or current_time.hour >= 18:  # 如果是夜间
            return f'{base_directory}/img/weather/{weather_code}d.svg'
    return f'{base_directory}/img/weather/{weather_code}.svg'


def get_weather_stylesheet(code):  # 天气背景样式
    current_time = datetime.datetime.now()
    weather_status = json.load(
        open(f"{base_directory}/config/data/{config_center.read_conf('Weather', 'api')}_status.json", encoding="utf-8"))
    weather_code = '99'
    for weather in weather_status['weatherinfo']:
        if str(weather['code']) == code:
            original_code = weather.get('original_code')
            if original_code is not None:
                weather_code = str(weather['original_code'])
            else:
                weather_code = str(weather['code'])
            break
    if weather_code in ('0', '1', '3', '99', '900'):  # 晴、多云、阵雨、未知
        if 6 <= current_time.hour < 18:  # 如果是日间
            # return 'spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(40, 60, 110, 255), stop:1 rgba(75, 175, 245, 255)'
            return 'img/weather/bkg/day.png'
        else:  # 如果是夜间
            return 'img/weather/bkg/night.png'
    # return 'spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(20, 60, 90, 255), stop:1 rgba(10, 20, 29, 255)'
    return 'img/weather/bkg/rain.png'


def get_weather_url():
    if config_center.read_conf('Weather', 'api') in api_config['weather_api_list']:
        return api_config['weather_api'][config_center.read_conf('Weather', 'api')]
    else:
        return api_config['weather_api']['xiaomi_weather']


def get_weather_alert_url():
    if not api_config['weather_api_parameters'][config_center.read_conf('Weather', 'api')]['alerts']:
        return 'NotSupported'
    if config_center.read_conf('Weather', 'api') in api_config['weather_api_list']:
        return api_config['weather_api_parameters'][config_center.read_conf('Weather', 'api')]['alerts']['url']
    else:
        return api_config['weather_api_parameters']['xiaomi_weather']['alerts']['url']


def get_weather_code_by_description(value):
    weather_status = json.load(
        open(f"{base_directory}/config/data/{config_center.read_conf('Weather', 'api')}_status.json", encoding="utf-8"))
    for weather in weather_status['weatherinfo']:
        if str(weather['wea']) == value:
            return str(weather['code'])
    return '99'


def get_alert_image(alert_type):
    alerts_list = api_config['weather_api_parameters'][config_center.read_conf('Weather', 'api')]['alerts']['types']
    return f'{base_directory}/img/weather/alerts/{alerts_list[alert_type]}'


def is_supported_alert():
    if not api_config['weather_api_parameters'][config_center.read_conf('Weather', 'api')]['alerts']:
        return False
    return True


def get_weather_data(key='temp', weather_data=None):  # 获取天气数据
    if weather_data is None:
        logger.error('weather_data is None!')
        return None
    '''
        根据key值获取weather_data中的对应值
        key值可以为：temp、icon
    '''
    # 各个天气api的可访问值
    api_parameters = api_config['weather_api_parameters'][config_center.read_conf('Weather', 'api')]
    if key == 'alert':
        parameter = api_parameters['alerts']['type'].split('.')
    else:
        parameter = api_parameters[key].split('.')
    # 遍历获取值
    value = weather_data
    if config_center.read_conf('Weather', 'api') == 'amap_weather':
        value = weather_data['lives'][0][api_parameters[key]]
    elif config_center.read_conf('Weather', 'api') == 'qq_weather':
        value = str(weather_data['result']['realtime'][0]['infos'][api_parameters[key]])
    else:
        for parameter in parameter:
            if not value:
                logger.warning(f'天气信息值{key}为空')
                return None
            if parameter == '0':
                value = value[0]
                continue
            if parameter in value:
                value = value[parameter]
            else:
                logger.error(f'获取天气参数失败，{parameter}不存在于{config_center.read_conf("Weather", "api")}中')
                return '错误'
    if key == 'temp':
        value += '°'
    elif key == 'icon':  # 修复此代码影响其他天气源的问题
        if api_parameters['return_desc']:  # 如果此api返回的是天气描述而不是代码
            value = get_weather_code_by_description(value)
    return value


def get_weather_hourly_url():
    """获取小时天气URL"""
    if config_center.read_conf('Weather', 'api') in api_config['weather_api_list']:
        api_name = config_center.read_conf('Weather', 'api')
        if 'hourly' in api_config['weather_api_parameters'][api_name]:
            return api_config['weather_api_parameters'][api_name]['hourly']['url']
    return 'NotSupported'

def get_hourly_weather_data(hourly_data, index=0):
    """获取小时天气数据
    
    Args:
        hourly_data: 小时天气数据
        index: 小时索引，0为第一小时，1为第二小时，以此类推
        
    Returns:
        dict: 包含时间、温度、天气图标、天气描述的字典
    """
    if not hourly_data:
        return None
        
    api_name = config_center.read_conf('Weather', 'api')
    if api_name not in api_config['weather_api_parameters']:
        return None
        
    api_params = api_config['weather_api_parameters'][api_name]
    if 'hourly' not in api_params:
        return None
    
    hourly_params = api_params['hourly']
    try:
        result = {}
        # 遍历参数并获取值
        for param_name, param_path in hourly_params['parameters'].items():
            path_parts = param_path.split('.')
            value = hourly_data
            
            # 处理索引，比如 hourly.3.temp
            for part in path_parts:
                if part == 'index':
                    # 替换索引
                    value = value[index]
                elif part.isdigit():
                    # 数字索引
                    value = value[int(part)]
                elif part in value:
                    value = value[part]
                else:
                    logger.error(f"获取小时天气参数失败: {param_path}")
                    value = None
                    break
            
            if value is not None:
                result[param_name] = value
                
        # 处理特定字段
        if 'icon' in result and api_params.get('return_desc', False):
            result['icon'] = get_weather_code_by_description(result['icon'])
            
        if 'time' in result:
            # 格式化时间为 HH:MM
            try:
                time_format = hourly_params.get('time_format', '%H:%M')
                if isinstance(result['time'], str):
                    # 使用正确的 datetime 模块
                    from datetime import datetime
                    time_obj = datetime.strptime(result['time'], hourly_params.get('time_input_format', '%Y-%m-%d %H:%M:%S'))
                    result['time'] = time_obj.strftime(time_format)
                elif isinstance(result['time'], int):
                    # 时间戳处理
                    from datetime import datetime
                    time_obj = datetime.fromtimestamp(result['time'])
                    result['time'] = time_obj.strftime(time_format)
            except Exception as e:
                logger.error(f"格式化小时天气时间失败: {e}")
                
        # Handle temperature formatting with proper units
        if 'temp' in result:
            # Convert to string if it's not already
            if not isinstance(result['temp'], str):
                result['temp'] = str(result['temp'])
            
            # Add degree symbol if not already present
            if not result['temp'].endswith('°'):
                result['temp'] = f"{result['temp']}°"
            
        return result
    except Exception as e:
        logger.error(f"解析小时天气数据失败: {e}")
        return None


if __name__ == '__main__':
    # 测试代码
    try:
        num_results = search_by_num('101310101')  # [2]城市名称
        print(num_results)
        cities_results_ = search_by_name('上海')  # [3]城市代码
        print(cities_results_)
        cities_results_ = search_code_by_name('上海','')  # [3]城市代码
        print(cities_results_)
        get_weather_by_code(3)
    except Exception as e:
        print(e)
