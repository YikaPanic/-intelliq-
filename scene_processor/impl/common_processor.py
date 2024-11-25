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
from scene_processor.impl.meeting_booking import check_and_book_meeting_room

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
        # Data structure to store the current required JSON output information
        # 現在必要なJSON出力情報を格納するデータ構造
        self.meeting_info = {
            "meetingName": "",
            "reserveEndTime": None,
            "reserveStartTime": None,
            "theme": ""
        }

    def process(self, user_input, context):
        # Process user input, update slots, check completeness, and interact with the user
        # ユーザー入力を処理し、スロットを更新し、完全性を確認し、ユーザーと対話する
        message = get_slot_update_message(self.scene_name, self.slot_dynamic_example, self.slot_template, user_input)
        new_info_json_raw = send_message(message, user_input)
        current_values = extract_json_from_string(new_info_json_raw)
        logging.debug('current_values: %s', current_values)
        logging.debug('slot update before: %s', self.slot)
        update_slot(current_values, self.slot)
        logging.debug('slot update after: %s', self.slot)
        # Check if all parameters are fully filled
        # すべてのパラメータが完全に入力されているか確認する
        if is_slot_fully_filled(self.slot):
            return self.respond_with_complete_data()
        else:
            # Analyze missing data and decide whether to ask the user or call the API
            # 欠落データを分析し、ユーザーに尋ねるかAPIを呼び出すかを決定する
            missing_data_action = self.decide_next_action(self.slot, user_input)
            if missing_data_action == "ask_user":
                return self.ask_user_for_missing_data(user_input)
            elif missing_data_action == "call_api":
                return self.fetch_data_from_api(self.slot, self.scene_name)
            else:
                # Default behavior or error handling
                # デフォルトの動作またはエラー処理
                return "Unable to determine the next action, please check the data manually."
    
    def process_slot(self, user_input, context):
        # Process user input, update slots, and return complete data
        # ユーザー入力を処理し、スロットを更新し、完全なデータを返す
        message = get_slot_update_message(self.scene_name, self.slot_dynamic_example, self.slot_template, user_input)
        new_info_json_raw = send_message(message, user_input)
        current_values = extract_json_from_string(new_info_json_raw)
        logging.debug('current_values: %s', current_values)

        # Update slot information
        # スロット情報を更新する
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
                if "时间" in name and value:  # Check if it is a time-related slot and convert
                    # 時間関連のスロットかどうかを確認し、変換する
                    value = self.convert_time_format(value)
                self.meeting_info[slot_mapping[name]] = value if value else ''

        return self.meeting_info

        # # Check if slot information is complete
        # # スロット情報が完全かどうかを確認する
        # if is_slot_fully_filled(self.meeting_info):
        #     return self.meeting_info
        # else:
        #     return self.meeting_info

    
    def convert_time_format(self, time_str):
        """
        Convert time format from "2024/05/23 15:00" to "2024-06-11 14:52:34"
        "2024/05/23 15:00"から"2024-06-11 14:52:34"に時間形式を変換する
        :param time_str: Original time string
        :return: Converted time string
        """
        try:
            dt = datetime.strptime(time_str, "%Y/%m/%d %H:%M")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            logging.error(f"Time format conversion error: {e}")
            return time_str

    def respond_with_complete_data(self):
        after_slot_processor = AfterSlotProcessor(self.slot)
        # Response when all data is ready
        # すべてのデータが準備できたときの応答
        logging.debug(f'%s ------ Parameters are complete, detailed parameters are as follows', self.scene_name)
        logging.debug(format_name_value_for_logging(self.slot))
        logging.debug(f'Requesting %s API, please wait...', self.scene_name)

        if self.scene_name == "Client Meeting Booking":
            return check_and_book_meeting_room(self.slot)
        elif self.scene_name == "Meeting Meal Booking":
            # Placeholder for order query logic
            # 注文クエリロジックのプレースホルダー
            pass
        elif self.scene_name == "Weather Inquiry":
            return "Calling Weather Inspect......"
        else:
            return "No corresponding processing method found"

    def ask_user_for_missing_data(self, user_input):
        message = get_slot_query_user_message(self.scene_name, self.slot, user_input)
        # Request the user to fill in missing data
        # ユーザーに欠落データを入力するよう依頼する
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
                # Check if the response is successful
                # 応答が成功したかどうかを確認する
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
            # Assume API returns JSON format data
            # APIがJSON形式のデータを返すと仮定する
            response_json = response_data.json()
        except ValueError:
            # If API returns string format data
            # APIが文字列形式のデータを返す場合
            response_json = extract_json_from_string(response_data.text)

        # Extract required slot data from response data
        # 応答データから必要なスロットデータを抽出する
        slot_data = []
        for param in processor_config["params"]:
            param_name = param["name"]
            param_value = response_json.get(param_name)
            if param_value:
                slot_data.append({"name": param_name, "value": param_value})

        # Log the state of slot data before and after the update
        # 更新前後のスロットデータの状態を記録する
        logging.debug('slot update before: %s', self.slot)

        # Update slot data
        # スロットデータを更新する
        update_slot(slot_data, self.slot)

        logging.debug('slot update after: %s', self.slot)

        # If all required slots are filled, return success message
        # すべての必須スロットが埋められている場合、成功メッセージを返す
        if is_slot_fully_filled(self.slot):
            return "All required information has been obtained from the API, slot data has been updated."
        else:
            # Otherwise, return the slots that still need to be filled
            # それ以外の場合は、まだ埋める必要のあるスロットを返す
            missing_slots = [param["name"] for param in self.slot_template if
                             param["required"] and self.slot.get(param["name"]) is None]
            return f"Partial information has been obtained from the API, but the following slots still need to be filled: {', '.join(missing_slots)}"

    ## Different parameters are passed to the API for different preset scenes
    ## 異なるプリセットシーンに対して異なるパラメータがAPIに渡される
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
                # Configuration for processing response data
                # 応答データを処理するための設定
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
                # Configuration for processing response data
                # 応答データを処理するための設定
            }
        },
        "Park_property_order_tracking": {
            "url": "https://api.example.com/order-tracking",
            "method": "GET",
            "params": [
                {"name": "工单号"},
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
                # Configuration for processing response data
                # 応答データを処理するための設定
            }
        }
    }
