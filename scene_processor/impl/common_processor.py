# encoding=utf-8
import logging
import csv
import requests
from datetime import datetime, timedelta

from scene_config import scene_prompts
from scene_processor.scene_processor import SceneProcessor
from utils.helpers import get_raw_slot, update_slot, format_name_value_for_logging, is_slot_fully_filled, send_message, \
    extract_json_from_string, get_dynamic_example
from utils.prompt_utils import get_slot_update_message, get_slot_query_user_message
from utils.send_llm import fetch_decision_from_api
from scene_processor.impl.after_slot_processor import AfterSlotProcessor

def get_slot_value(slot, name):
    for item in slot:
        if item['name'] == name:
            return item['value']
    return None
class CommonProcessor(SceneProcessor):
    def __init__(self, scene_config):
        parameters = scene_config["parameters"]
        self.scene_config = scene_config
        self.scene_name = scene_config["name"]
        self.scene_description = scene_config.get('description', '')
        self.slot_template = get_raw_slot(parameters)
        self.slot_dynamic_example = get_dynamic_example(scene_config)
        self.slot = get_raw_slot(parameters)
        self.scene_prompts = scene_prompts
        # 新增数据结构存放当前需要的JSON输出信息
        self.meeting_info = {
            "meetingName": "",
            "reserveEndTime": None,
            "reserveStartTime": None,
            "theme": ""
        }

    def process(self, user_input, context):
        # 处理用户输入，更新槽位，检查完整性，以及与用户交互
        message = get_slot_update_message(self.scene_name, self.slot_dynamic_example, self.slot_template, user_input)
        new_info_json_raw = send_message(message, user_input)
        current_values = extract_json_from_string(new_info_json_raw)
        logging.debug('current_values: %s', current_values)
        logging.debug('slot update before: %s', self.slot)
        update_slot(current_values, self.slot)
        logging.debug('slot update after: %s', self.slot)
        # 判断参数是否已经全部补全
        if is_slot_fully_filled(self.slot):
            return self.respond_with_complete_data()
        else:
            # 分析缺失的数据，并决定是向用户询问还是调用API
            missing_data_action = self.decide_next_action(self.slot, user_input)
            if missing_data_action == "ask_user":
                return self.ask_user_for_missing_data(user_input)
            elif missing_data_action == "call_api":
                return self.fetch_data_from_api(self.slot, self.scene_name)
            else:
                # 默认行为或错误处理
                return "无法确定下一步行动，请手动检查数据。"
    
    def process_slot(self, user_input, context):
        # 处理用户输入，更新槽位，并返回完整的数据
        message = get_slot_update_message(self.scene_name, self.slot_dynamic_example, self.slot_template, user_input)
        new_info_json_raw = send_message(message, user_input)
        current_values = extract_json_from_string(new_info_json_raw)
        logging.debug('current_values: %s', current_values)

        # 更新槽位信息
        slot_mapping = {
            '会议名称': 'meetingName',
            '会议预订的具体时间': 'reserveStartTime',
            '会议结束时间': 'reserveEndTime',
            '会议主题': 'theme'
        }

        for item in current_values:
            name = item['name']
            value = item['value']
            if name in slot_mapping:
                if "时间" in name and value:  # 检查是否为时间相关的槽位并进行转换
                    value = self.convert_time_format(value)
                self.meeting_info[slot_mapping[name]] = value if value else ''

        return self.meeting_info

        # # 检查槽位信息是否完整
        # if is_slot_fully_filled(self.meeting_info):
        #     return self.meeting_info
        # else:
        #     return self.meeting_info

    
    def convert_time_format(self, time_str):
        """
        转换时间格式从 "2024/05/23 15:00" 到 "2024-06-11 14:52:34"
        :param time_str: 原始时间字符串
        :return: 转换后的时间字符串
        """
        try:
            dt = datetime.strptime(time_str, "%Y/%m/%d %H:%M")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            logging.error(f"时间格式转换错误: {e}")
            return time_str

    def respond_with_complete_data(self):
        after_slot_processor = AfterSlotProcessor(self.slot)
        # 当所有数据都准备好后的响应
        logging.debug(f'%s ------ 参数已完整，详细参数如下', self.scene_name)
        logging.debug(format_name_value_for_logging(self.slot))
        logging.debug(f'正在请求%sAPI，请稍后……', self.scene_name)

        if self.scene_name == "客户会议预订":
            return self.check_and_book_meeting_room()
        elif self.scene_name == "order_query":
            # Placeholder for order query logic
            pass
        else:
            return "未找到对应的处理方法"

    def respond_with_complete_data(self):
        after_slot_processor = AfterSlotProcessor(self.slot)
        # 当所有数据都准备好后的响应
        logging.debug(f'%s ------ 参数已完整，详细参数如下', self.scene_name)
        logging.debug(format_name_value_for_logging(self.slot))
        logging.debug(f'正在请求%sAPI，请稍后……', self.scene_name)
        logging.debug(self.slot)

        if self.scene_name == "客户会议预订":
            return self.check_and_book_meeting_room()
        elif self.scene_name == "order_query":
            # Placeholder for order query logic
            pass
        else:
            return "未找到对应的处理方法"

    def check_and_book_meeting_room(self):
        meeting_date_time = datetime.strptime(get_slot_value(self.slot, '会议预订的具体时间'), "%Y/%m/%d %H:%M")
        meeting_duration = get_slot_value(self.slot, '会议时长')
        meeting_end_time = self.calculate_end_time(meeting_date_time, meeting_duration)
        required_capacity = int(get_slot_value(self.slot, '会议室容量').replace('人', ''))

        available_room = None
        with open('meeting_reservations.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            room_occupancies = {room: [] for room in ["会议室1", "会议室2", "会议室3"]}

            for row in reader:
                room = row["会议室"]
                start_time_str = row["会议时间段"]
                try:
                    start_time = datetime.strptime(start_time_str, "%Y/%m/%d %H:%M")
                    end_time = self.calculate_end_time(start_time, row['会议时长'])
                    room_occupancies[room].append((start_time, end_time))
                except ValueError as e:
                    logging.error(f"Error parsing date: {e}")

            for room, times in room_occupancies.items():
                if not times:
                    available_room = room
                    break

                for start, end in times:
                    if meeting_end_time <= start or meeting_date_time >= end:
                        available_room = room
                        break
                if available_room:
                    break

        if available_room:
            self.slot.append({'name': '会议室', 'value': available_room})
            self.save_reservation()
            # api调用在这里
            return f"会议预订成功，会议室：{available_room}。会议时间：{get_slot_value(self.slot, '会议预订的具体时间')}，会议主题：{get_slot_value(self.slot, '会议主题')}。"
        else:
            return "很抱歉，当前时间段没有可用的会议室。请尝试其他时间。"

    def calculate_end_time(self, start_time, duration):
        if duration == "半小时":
            return start_time + timedelta(minutes=30)
        elif duration == "1小时":
            return start_time + timedelta(hours=1)
        elif duration == "2小时":
            return start_time + timedelta(hours=2)
        else:
            raise ValueError("无效的会议时长")

    def save_reservation(self):
        reservation_data = {
            "预约人姓名": get_slot_value(self.slot, '会议预约人的姓名'),
            "会议室": get_slot_value(self.slot, '会议室'),
            "会议室容量": get_slot_value(self.slot, '会议室容量'),
            "会议时间段": get_slot_value(self.slot, '会议预订的具体时间'),
            "会议时长": get_slot_value(self.slot, '会议时长'),
            "会议主题": get_slot_value(self.slot, '会议主题'),
            "会议名称": get_slot_value(self.slot, '会议名称')
        }

        with open('meeting_reservations.csv', 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["预约人姓名", "会议室", "会议室容量", "会议时间段", "会议时长",
                                                         "会议主题", "会议名称"])
            writer.writerow(reservation_data)

    def ask_user_for_missing_data(self, user_input):
        message = get_slot_query_user_message(self.scene_name, self.slot, user_input)
        # 请求用户填写缺失的数据
        result = send_message(message, user_input)
        return result

    def decide_next_action(self, slot, user_input):
        result = fetch_decision_from_api(self, slot, user_input, self.scene_description)
        logging.info(f"Decided next action: {result}")
        return result

    def fetch_data_from_api(self, slot, scene_name):
        api_config = self.get_api_config(scene_name)
        if api_config:
            try:
                api_url = api_config["url"]
                api_method = api_config["method"]
                api_params = self.prepare_params(api_config["params"], slot)
                api_headers = api_config.get("headers", {})

                response = requests.request(api_method, api_url, params=api_params, headers=api_headers)
                # 检查响应是否成功
                response.raise_for_status()

                data = response.json()
                result = self.process_response(data, api_config["processor"])
                return result
            except requests.exceptions.RequestException as e:
                logging.error(f"Error fetching data from API: {e}")
        else:
            logging.warning(f"No API configuration found for scene: {scene_name}")
        return None

    def get_api_config(self, scene_name):
        return self.api_configs.get(scene_name)

    def prepare_params(self, param_config, slot):
        params = {}
        for param in param_config:
            param_name = param["name"]
            param_value = slot.get(param_name)
            if param_value:
                params[param_name] = param_value
        return params

    def process_response(self, response_data, processor_config):
        if response_data is None:
            logging.error("API response is empty")
            return None

        try:
            # 假设API返回JSON格式数据
            response_json = response_data.json()
        except ValueError:
            # 如果API返回字符串格式数据
            response_json = extract_json_from_string(response_data.text)

        # 从响应数据中提取所需的槽位数据
        slot_data = []
        for param in processor_config["params"]:
            param_name = param["name"]
            param_value = response_json.get(param_name)
            if param_value:
                slot_data.append({"name": param_name, "value": param_value})

        # 记录槽位数据变化前后的情况
        logging.debug('slot update before: %s', self.slot)

        # 更新槽位数据
        update_slot(slot_data, self.slot)

        logging.debug('slot update after: %s', self.slot)

        # 如果所有必需的槽位都已填充,则返回成功消息
        if is_slot_fully_filled(self.slot):
            return "已从API获取所有必需信息,槽位数据已更新。"
        else:
            # 否则返回需要补充的槽位信息
            missing_slots = [param["name"] for param in self.slot_template if
                             param["required"] and self.slot.get(param["name"]) is None]
            return f"已从API获取部分信息,但以下槽位仍需补充: {', '.join(missing_slots)}"

    ## 针对预设场景分别传入不同的参数来请求api
    api_configs = {
        "Park_property_device": {
            "url": "https://api.example.com/device-warranty",
            "method": "GET",
            "params": [
                {"name": "设备编号"},
                {"name": "设备名称"},
                {"name": "位置"},
                {"name": "设备类型"},
                {"name": "设备状态"},
                {"name": "生产厂家"},
                {"name": "设备型号"},
                {"name": "下一次维保日期"}
            ],
            "processor": {
                # 处理响应数据的配置
            }
        },
        "Park_property_abnormal_facilities_and_equipment": {
            "url": "https://api.example.com/abnormal-facilities",
            "method": "GET",
            "params": [
                {"name": "设施或设备的编号"},
                {"name": "设施或设备的名称"},
                {"name": "设施或设备的位置"},
                {"name": "设施或设备是否处于异常状态"},
                {"name": "设施或设备的异常状态的具体描述"}
            ],
            "processor": {
                # 处理响应数据的配置
            }
        },
        "Park_property_order_tracking": {
            "url": "https://api.example.com/order-tracking",
            "method": "GET",
            "params": [
                {"name": "工单编号"},
                {"name": "工单名称"},
                {"name": "创建时间"},
                {"name": "工单类型"},
                {"name": "工单来源"},
                {"name": "工单状态"},
                {"name": "要求开始时间"},
                {"name": "要求完成时间"},
                {"name": "实际结束时间"},
                {"name": "执行人"}
            ],
            "processor": {
                # 处理响应数据的配置
            }
        }
    }
