# encoding=utf-8
import logging

from scene_config import scene_prompts
from scene_processor.scene_processor import SceneProcessor
from utils.helpers import get_raw_slot, update_slot, format_name_value_for_logging, is_slot_fully_filled, send_message, \
    extract_json_from_string, get_dynamic_example
from utils.prompt_utils import get_slot_update_message, get_slot_query_user_message
from utils.send_llm import fetch_decision_from_api


class CommonProcessor(SceneProcessor):
    def __init__(self, scene_config):
        parameters = scene_config["parameters"]
        self.scene_config = scene_config
        self.scene_name = scene_config["name"]
        self.slot_template = get_raw_slot(parameters)
        self.slot_dynamic_example = get_dynamic_example(scene_config)
        self.slot = get_raw_slot(parameters)
        self.scene_prompts = scene_prompts

    def process(self, user_input, context):
        # 处理用户输入，更新槽位，检查完整性，以及与用户交互
        # 先检查本次用户输入是否有信息补充，保存补充后的结果   编写程序进行字符串value值diff对比，判断是否有更新
        message = get_slot_update_message(self.scene_name, self.slot_dynamic_example, self.slot_template, user_input)  # 优化封装一下 .format  入参只要填input
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
                return self.fetch_data_from_api(self.slot)
            else:
                # 默认行为或错误处理
                return "无法确定下一步行动，请手动检查数据。"

    def respond_with_complete_data(self):
        # 当所有数据都准备好后的响应
        logging.debug(f'%s ------ 参数已完整，详细参数如下', self.scene_name)
        logging.debug(format_name_value_for_logging(self.slot))
        logging.debug(f'正在请求%sAPI，请稍后……', self.scene_name)
        return format_name_value_for_logging(self.slot) + '\n正在请求{}API，请稍后……'.format(self.scene_name)

    def ask_user_for_missing_data(self, user_input):
        message = get_slot_query_user_message(self.scene_name, self.slot, user_input)
        # 请求用户填写缺失的数据
        result = send_message(message, user_input)
        return result
    
    # def fetch_data_from_external_source(self, slot_name, context):

    # #根据槽位名称和上下文调用外部API获取数据
    # # 根据slot_name和context确定要调用的API以及所需的参数
    # api_config = self.determine_api_config(slot_name, context)
    # if api_config is None:
    #     return None

    # # 调用API并获取数据
    # response_data = self.call_external_api(api_config)
    # if response_data:
    #     # 处理响应数据并更新槽位
    #     self.update_slot_with_external_data(response_data, slot_name)
    #     return True
    # else:
    #     return False

    def decide_next_action(self, slot, user_input):
        result = fetch_decision_from_api(self, slot, user_input)
        logging.info(f"Decided next action: {result}")
        return result

    def fetch_data_from_api(self, slot):
        # 具体调用api的方法
        pass