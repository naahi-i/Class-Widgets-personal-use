import json
import os
import shutil
import zipfile  # 解压插件zip
from datetime import datetime

import requests
from PyQt5.QtCore import QThread, pyqtSignal, QEventLoop
from loguru import logger
from packaging.version import Version

import conf
import utils
import weather_db as db
from conf import base_directory
from file import config_center

headers = {"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"}  # 设置请求头
# proxies = {"http": "http://127.0.0.1:10809", "https": "http://127.0.0.1:10809"}  # 加速访问
proxies = {"http": None, "https": None}

MIRROR_PATH = f"{base_directory}/config/mirror.json"
PLAZA_REPO_URL = "https://raw.githubusercontent.com/Class-Widgets/plugin-plaza/"
PLAZA_REPO_DIR = "https://api.github.com/repos/Class-Widgets/plugin-plaza/contents/"
threads = []

# 读取镜像配置
mirror_list = []
try:
    with open(MIRROR_PATH, 'r', encoding='utf-8') as file:
        mirror_dict = json.load(file).get('gh_mirror')
except Exception as e:
    logger.error(f"读取镜像配置失败: {e}")

for name in mirror_dict:
    mirror_list.append(name)

if config_center.read_conf('Plugin', 'mirror') not in mirror_list:  # 如果当前配置不在镜像列表中，则设置为默认镜像
    logger.warning(f"当前配置不在镜像列表中，设置为默认镜像: {mirror_list[0]}")
    config_center.write_conf('Plugin', 'mirror', mirror_list[0])


class getRepoFileList(QThread):  # 获取仓库文件目录
    repo_signal = pyqtSignal(dict)

    def __init__(
            self, url='https://raw.githubusercontent.com/Class-Widgets/plugin-plaza/main/Banner/banner.json'
    ):
        super().__init__()
        self.download_url = url

    def run(self):
        try:
            plugin_info_data = self.get_plugin_info()
            self.repo_signal.emit(plugin_info_data)
        except Exception as e:
            logger.error(f"触发banner信息失败: {e}")

    def get_plugin_info(self):
        try:
            mirror_url = mirror_dict[config_center.read_conf('Plugin', 'mirror')]
            url = f"{mirror_url}{self.download_url}"
            response = requests.get(url, proxies=proxies, headers=headers)  # 禁用代理
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logger.error(f"获取banner信息失败：{response.status_code}")
                return {"error": response.status_code}
        except Exception as e:
            logger.error(f"获取banner信息失败：{e}")
            return {"error": e}


class getPluginInfo(QThread):  # 获取插件信息(json)
    repo_signal = pyqtSignal(dict)

    def __init__(
            self, url='https://raw.githubusercontent.com/Class-Widgets/plugin-plaza/main/Plugins/plugin_list.json'
    ):
        super().__init__()
        self.download_url = url

    def run(self):
        try:
            plugin_info_data = self.get_plugin_info()
            self.repo_signal.emit(plugin_info_data)
        except Exception as e:
            logger.error(f"触发插件信息失败: {e}")

    def get_plugin_info(self):
        try:
            mirror_url = mirror_dict[config_center.read_conf('Plugin', 'mirror')]
            url = f"{mirror_url}{self.download_url}"
            response = requests.get(url, proxies=proxies, headers=headers)  # 禁用代理
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logger.error(f"获取插件信息失败：{response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"获取插件信息失败：{e}")
            return {}


class getTags(QThread):  # 获取插件标签(json)
    repo_signal = pyqtSignal(dict)

    def __init__(
            self, url='https://raw.githubusercontent.com/Class-Widgets/plugin-plaza/main/Plugins/plaza_detail.json'
    ):
        super().__init__()
        self.download_url = url

    def run(self):
        try:
            plugin_info_data = self.get_plugin_info()
            self.repo_signal.emit(plugin_info_data)
        except Exception as e:
            logger.error(f"触发Tag信息失败: {e}")

    def get_plugin_info(self):
        try:
            mirror_url = mirror_dict[config_center.read_conf('Plugin', 'mirror')]
            url = f"{mirror_url}{self.download_url}"
            response = requests.get(url, proxies=proxies, headers=headers)  # 禁用代理
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logger.error(f"获取Tag信息失败：{response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"获取Tag信息失败：{e}")
            return {}


class getImg(QThread):  # 获取图片
    repo_signal = pyqtSignal(bytes)

    def __init__(self, url='https://raw.githubusercontent.com/Class-Widgets/plugin-plaza/main/Banner/banner_1.png'):
        super().__init__()
        self.download_url = url

    def run(self):
        try:
            banner_data = self.get_banner()
            if banner_data is not None:
                self.repo_signal.emit(banner_data)
            else:
                with open(f"{base_directory}/img/plaza/banner_pre.png", 'rb') as default_img:  # 读取默认图片
                    self.repo_signal.emit(default_img.read())
        except Exception as e:
            logger.error(f"触发图片失败: {e}")

    def get_banner(self):
        try:
            mirror_url = mirror_dict[config_center.read_conf('Plugin', 'mirror')]
            url = f"{mirror_url}{self.download_url}"
            response = requests.get(url, proxies=proxies, headers=headers)
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"获取图片失败：{response.status_code}")
                return None
        except Exception as e:
            logger.error(f"获取图片失败：{e}")
            return None


class getReadme(QThread):  # 获取README
    html_signal = pyqtSignal(str)

    def __init__(self, url='https://raw.githubusercontent.com/Class-Widgets/Class-Widgets/main/README.md'):
        super().__init__()
        self.download_url = url

    def run(self):
        try:
            readme_data = self.get_readme()
            self.html_signal.emit(readme_data)
        except Exception as e:
            logger.error(f"触发README失败: {e}")

    def get_readme(self):
        try:
            mirror_url = mirror_dict[config_center.read_conf('Plugin', 'mirror')]
            url = f"{mirror_url}{self.download_url}"
            # print(url)
            response = requests.get(url, proxies=proxies)
            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"获取README失败：{response.status_code}")
                return ''
        except Exception as e:
            logger.error(f"获取README失败：{e}")
            return ''

class getCity(QThread):

    def __init__(self, url='https://qifu-api.baidubce.com/ip/local/geo/v1/district'):
        super().__init__()
        self.download_url = url

    def run(self):
        try:
            city_data = self.get_city()
            config_center.write_conf('Weather', 'city', db.search_code_by_name(city_data))
        except Exception as e:
            logger.error(f"获取城市失败: {e}")

    def get_city(self):
        try:
            req = requests.get(self.download_url, proxies=proxies)
            if req.status_code == 200:
                data = req.json()
                # {"code":"Success","data":{"continent":"","country":"中国","zipcode":"","owner":"","isp":"","adcode":"","prov":"","city":"","district":""},"ip":"45.192.96.246"}
                if data['code'] == 'Success':
                    data = data['data']
                    logger.info(f"获取城市成功：{data['city']}, {data['district']}")
                    return (data['city'], data['district'])
                else:
                    logger.error(f"获取城市失败：{data['message']}")
                    return ('', '')
            else:
                logger.error(f"获取城市失败：{req.status_code}")    
                return ('', '')
            
        except Exception as e:
            logger.error(f"获取城市失败：{e}")
            return ('', '')

class VersionThread(QThread):  # 获取最新版本号
    version_signal = pyqtSignal(dict)
    _instance_running = False

    def __init__(self):
        super().__init__()
    def run(self):
        version = self.get_latest_version()
        self.version_signal.emit(version)
    
    @classmethod
    def is_running(cls):
        return cls._instance_running

    @staticmethod
    def get_latest_version():
        url = "https://classwidgets.rinlit.cn/version.json"
        try:
            logger.info(f"正在获取版本信息")
            response = requests.get(url, proxies=proxies, timeout=30)
            logger.debug(f"更新请求响应: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logger.error(f"无法获取版本信息 错误代码：{response.status_code}，响应内容: {response.text}")
                return {'error': f"请求失败，错误代码：{response.status_code}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败，错误详情：{str(e)}")
            return {"error": f"请求失败\n{str(e)}"}


class getDownloadUrl(QThread):
    # 定义信号，通知下载进度或完成
    geturl_signal = pyqtSignal(str)

    def __init__(self, username, repo):
        super().__init__()
        self.username = username
        self.repo = repo

    def run(self):
        try:
            url = f"https://api.github.com/repos/{self.username}/{self.repo}/releases/latest"
            response = requests.get(url, proxies=proxies)
            if response.status_code == 200:
                data = response.json()
                for asset in data['assets']:  # 遍历下载链接
                    if isinstance(asset, dict) and 'browser_download_url' in asset:
                        asset_url = asset['browser_download_url']
                        self.geturl_signal.emit(asset_url)
            elif response.status_code == 403:  # 触发API限制
                logger.warning("到达Github API限制，请稍后再试")
                response = requests.get('https://api.github.com/users/octocat', proxies=proxies)
                reset_time = response.headers.get('X-RateLimit-Reset')
                reset_time = datetime.fromtimestamp(int(reset_time))
                self.geturl_signal.emit(f"ERROR: 由于请求次数过多，到达Github API限制，请在{reset_time.minute}分钟后再试")
            else:
                logger.error(f"网络连接错误：{response.status_code}")
        except Exception as e:
            logger.error(f"获取下载链接错误: {e}")
            self.geturl_signal.emit(f"获取下载链接错误: {e}")


class DownloadAndExtract(QThread):  # 下载并解压插件
    progress_signal = pyqtSignal(float)  # 进度
    status_signal = pyqtSignal(str)  # 状态

    def __init__(self, url, plugin_name='test_114'):
        super().__init__()
        self.download_url = url
        print(self.download_url)
        self.cache_dir = "cache"
        self.plugin_name = plugin_name
        self.extract_dir = conf.PLUGINS_DIR  # 插件目录

    def run(self):
        try:
            enabled_plugins = conf.load_plugin_config()  # 加载启用的插件

            os.makedirs(self.cache_dir, exist_ok=True)
            os.makedirs(self.extract_dir, exist_ok=True)

            zip_path = os.path.join(self.cache_dir, f'{self.plugin_name}.zip')

            self.status_signal.emit("DOWNLOADING")
            self.download_file(zip_path)
            self.status_signal.emit("EXTRACTING")
            self.extract_zip(zip_path)
            os.remove(zip_path)
            print(enabled_plugins)

            if (
                self.plugin_name not in enabled_plugins['enabled_plugins']
                and config_center.read_conf('Plugin', 'auto_enable_plugin') == '1'
            ):
                logger.info(f"自动启用插件: {self.plugin_name}")
                enabled_plugins['enabled_plugins'].append(self.plugin_name)
                conf.save_plugin_config(enabled_plugins)

            self.status_signal.emit("DONE")
        except Exception as e:
            self.status_signal.emit(f"错误: {e}")
            logger.error(f"插件下载/解压失败: {e}")

    def stop(self):
        self._running = False
        self.terminate()

    def download_file(self, file_path):
        # time.sleep(555)  # 模拟下载时间
        try:
            self.download_url = mirror_dict[config_center.read_conf('Plugin', 'mirror')] + self.download_url
            print(self.download_url)
            response = requests.get(self.download_url, stream=True, proxies=proxies)
            if response.status_code != 200:
                logger.error(f"插件下载失败，错误代码: {response.status_code}")
                self.status_signal.emit(f'ERROR: 网络连接错误：{response.status_code}')
                return

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    progress = (downloaded_size / total_size) * 100 if total_size > 0 else 0  # 计算进度
                    self.progress_signal.emit(progress)
        except Exception as e:
            self.status_signal.emit(f'ERROR: {e}')
            logger.error(f"插件下载错误: {e}")

    def extract_zip(self, zip_path):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.extract_dir)

            for p_dir in os.listdir(self.extract_dir):
                if p_dir.startswith(self.plugin_name) and len(p_dir) > len(self.plugin_name):
                    new_name = p_dir.rsplit('-', 1)[0]
                    if os.path.exists(os.path.join(self.extract_dir, new_name)):
                        shutil.copytree(
                            os.path.join(self.extract_dir, p_dir), os.path.join(self.extract_dir, new_name),
                            dirs_exist_ok=True)
                        shutil.rmtree(os.path.join(self.extract_dir, p_dir))
                    else:
                        os.rename(os.path.join(self.extract_dir, p_dir), os.path.join(self.extract_dir, new_name))
        except Exception as e:
            logger.error(f"解压失败: {e}")


def check_update():
    global threads

    if VersionThread.is_running():
        logger.debug("已存在版本检查线程在运行，跳过本检查")
        return
    
    # 清理已终止的线程
    threads = [t for t in threads if t.isRunning()]
    
    # 创建新的版本检查线程
    version_thread = VersionThread()
    threads.append(version_thread)
    version_thread.version_signal.connect(check_version)
    version_thread.start()


def check_version(version):  # 检查更新
    global threads
    for thread in threads:
        thread.terminate()
    threads = []
    if 'error' in version:
        utils.tray_icon.push_error_notification(
            "检查更新失败！",
            f"检查更新失败！\n{version['error']}"
        )
        return False
    
    channel = int(config_center.read_conf("Other", "version_channel"))
    server_version = version['version_release' if channel == 0 else 'version_beta']
    local_version = config_center.read_conf("Other", "version")
    logger.debug(f"服务端版本: {Version(server_version)}，本地版本: {Version(local_version)}")
    if Version(server_version) > Version(local_version):
        utils.tray_icon.push_update_notification(f"新版本速递：{server_version}\n请在“设置”中了解更多。")

class weatherReportThread(QThread):  # 获取最新天气信息
    weather_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            weather_data = self.get_weather_data()
            self.weather_signal.emit(weather_data)
        except Exception as e:
            logger.error(f"触发天气信息失败: {e}")
        finally:
            self.deleteLater()

    @staticmethod
    def get_weather_data():
        location_key = config_center.read_conf('Weather', 'city')
        if location_key == '0':
            city_thread = getCity()
            loop = QEventLoop()
            city_thread.finished.connect(loop.quit)
            city_thread.start()
            loop.exec_()  # 阻塞到完成
            location_key = config_center.read_conf('Weather', 'city')
            if location_key == '0' or not location_key:
                location_key = 101010100
        days = 1
        key = config_center.read_conf('Weather', 'api_key')
        url = db.get_weather_url().format(location_key=location_key, days=days, key=key)
        hourly_url = db.get_weather_hourly_url()
        alert_url = db.get_weather_alert_url()
        try:
            data_group = {'now': {}, 'alert': {}, 'hourly': {}}
            response_now = requests.get(url, proxies=proxies)  # 禁用代理
            
            # 获取小时预报数据
            if hourly_url and hourly_url != 'NotSupported':
                try:
                    hourly_url = hourly_url.format(location_key=location_key, key=key)
                    response_hourly = requests.get(hourly_url, proxies=proxies)
                    if response_hourly.status_code == 200:
                        hourly_data = response_hourly.json()
                        data_group['hourly'] = hourly_data
                    else:
                        logger.error(f"获取小时天气信息失败：{response_hourly.status_code}")
                except Exception as e:
                    logger.error(f"获取小时天气信息异常：{e}")
            
            if alert_url == 'NotSupported':
                logger.warning(f"当前API不支持天气预警信息")
            elif alert_url is None:
                logger.warning(f"无单独天气预警信息API")
            else:
                alert_url = alert_url.format(location_key=location_key, key=key)
                response_alert = requests.get(alert_url, proxies=proxies)

                if response_alert.status_code == 200:
                    data_alert = response_alert.json()
                    data_group['alert'] = data_alert
                else:
                    logger.error(f"获取天气预警信息失败：{response_alert.status_code}")

            if response_now.status_code == 200:
                data = response_now.json()
                data_group['now'] = data
                return data_group
            else:
                logger.error(f"获取天气信息失败：{response_now.status_code}")
                return {'error': {'info': {'value': '错误', 'unit': response_now.status_code}}}
        except requests.exceptions.RequestException as e:  # 请求失败
            logger.error(f"获取天气信息失败：{e}")
            return {'error': {'info': {'value': '错误', 'unit': ''}}}
        except Exception as e:
            logger.error(f"获取天气信息失败：{e}")
            return {'error': {'info': {'value': '错误', 'unit': ''}}}
