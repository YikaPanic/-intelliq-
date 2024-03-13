# encoding=utf-8
import glob
import json
import re
import requests
import config

from functools import lru_cache
from utils.send_llm import send_local_qwen_message
from utils.send_llm import send_chatgpt_message
from utils.send_llm import send_tongyiqwen_message

send_llm_req = {
    "Qwen": send_local_qwen_message,
    "chatGPT": send_chatgpt_message,
    "tongyiQwen":send_tongyiqwen_message
}

def filename_to_classname(filename):
    """
    Convert a snake_case filename to a CamelCase class name.

    Args:
    filename (str): The filename in snake_case, without the .py extension.

    Returns:
    str: The converted CamelCase class name.
    """
    parts = filename.split('_')
    class_name = ''.join(part.capitalize() for part in parts)
    return class_name


def load_scene_templates(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def load_all_scene_configs():
    # 用于存储所有场景配置的字典
    all_scene_configs = {}

    # 搜索目录下的所有json文件
    for file_path in glob.glob("scene_config/**/*.json", recursive=True):
        current_config = load_scene_templates(file_path)

        for key, value in current_config.items():
            # todo 可以有加载优先级
            # 只有当键不存在时，才添加到all_scene_configs中
            if key not in all_scene_configs:
                all_scene_configs[key] = value

    return all_scene_configs


@lru_cache(maxsize=100)
def send_message(message, user_input):
    """
    请求LLM函数
    """
    return send_llm_req.get(config.USE_MODEL, send_chatgpt_message)(message, user_input)


def is_slot_fully_filled(json_data):
    """
    检查槽位是否完整填充
    """
    # 遍历JSON数据中的每个元素
    for item in json_data:
        # 检查value字段是否为空字符串
        if item.get('value') == '':
            return False  # 如果发现空字符串，返回False
    return True  # 如果所有value字段都非空，返回True


def get_raw_slot(parameters):
    # 创建新的JSON对象
    output_data = []
    for item in parameters:
        new_item = {"name": item["name"], "desc": item["desc"], "type": item["type"], "value": ""}
        output_data.append(new_item)
    return output_data


def get_dynamic_example(scene_config):
    # 创建新的JSON对象
    if 'example' in scene_config:
        return scene_config['example']
    else:
        return '答：{"name":"xx","value":"xx"}'


def get_slot_update_json(slot):
    # 创建新的JSON对象
    output_data = []
    for item in slot:
        new_item = {"name": item["name"], "desc": item["desc"], "value": item["value"]}
        output_data.append(new_item)
    return output_data


def get_slot_query_user_json(slot):
    # 创建新的JSON对象
    output_data = []
    for item in slot:
        if not item["value"]:
            new_item = {"name": item["name"], "desc": item["desc"], "value":  item["value"]}
            output_data.append(new_item)
    return output_data


def update_slot(json_data, dict_target):
    """
    更新槽位slot参数
    """
    # 遍历JSON数据中的每个元素
    for item in json_data:
        # 确保item是字典类型
        if isinstance(item, dict) and item.get('value', '') != '':
            for target in dict_target:
                if target['name'] == item['name']:
                    target['value'] = item['value']
                    break

def format_name_value_for_logging(json_data):
    """
    抽取参数名称和value值
    """
    json_data = prepare_json_data_for_api(json_data)
    log_strings = []
    for item in json_data:
        name = item.get('name', 'Unknown name')  # 获取name，如果不存在则使用'Unknown name'
        value = item.get('value', 'N/A')  # 获取value，如果不存在则使用'N/A'
        log_string = f"name: {name}, Value: {value}"
        log_strings.append(log_string)
    return '\n'.join(log_strings)

def parse_purchase_list(purchase_str):
    """
    解析采购列表字符串，转换为二维数组，每个元素包含商品名称和数量。
    """
    # 定义正则表达式匹配商品和数量
    pattern = re.compile(r"([\u4e00-\u9fa5]+?)\s*(\d+)\s*([支张台个批对打份盒箱]+)")
    
    # 查找所有匹配项
    matches = pattern.findall(purchase_str)
    
    # 提取商品名称和数量
    result = []
    for match in matches:
        item_name = match[0]  # 商品名称
        quantity = match[1]  # 数量
        result.append((item_name, int(quantity)))  # 将商品名称和数量作为元组添加到结果列表中
    
    return result

def prepare_json_data_for_api(json_data):
    """
    修改json_data中特定条目的value格式，准备发送给API。
    """
    updated_json_data = []  # 创建一个新的列表来存储更新后的条目
    for item in json_data:
        if item.get("name") == "采购的内容清单":
            current_value = item.get("value", "")
            if isinstance(current_value, str):
                # 使用 parse_purchase_list 方法解析购买清单字符串
                formatted_list = parse_purchase_list(current_value)
                updated_json_data.append({"name": item["name"], "value": formatted_list})
            elif isinstance(current_value, list):
                updated_json_data.append(item)  # 如果已经是列表格式，则直接添加
        else:
            updated_json_data.append(item)  # 添加不需要修改的条目
    return updated_json_data

# def extract_json_from_string(input_string):
#     """
#     JSON抽取函数
#     返回包含JSON对象的列表
#     """
    
#     try:
#         # 正则表达式假设JSON对象由花括号括起来
#         matches = re.findall(r'\{.*?\}', input_string, re.DOTALL)

#         # 验证找到的每个匹配项是否为有效的JSON
#         valid_jsons = []
#         for match in matches:
#             try:
#                 json_obj = json.loads(match)
#                 valid_jsons.append(json_obj)
#             except json.JSONDecodeError:
#                 try:
#                     valid_jsons.append(fix_json(match))
#                 except json.JSONDecodeError:
#                     continue  # 如果不是有效的JSON，跳过该匹配项
#                 continue  # 如果不是有效的JSON，跳过该匹配项

#         return valid_jsons
#     except Exception as e:
#         print(f"Error occurred: {e}")
#         return []

def extract_json_from_string(input_string):
    try:
        # 使用非贪婪匹配改进提取，避免截断嵌套结构
        matches = re.findall(r'\{.*?\}', input_string, re.DOTALL)
        valid_jsons = []
        for match in matches:
            try:
                json_obj = json.loads(match)
                valid_jsons.append(json_obj)
            except json.JSONDecodeError:
                # 尝试使用修复函数
                fixed_json = fix_json(match)
                print(f"try to fix")
                if fixed_json:
                    # 尝试解析修复后的JSON字符串
                    try:
                        fixed_json_obj = json.loads(fixed_json)
                        valid_jsons.append(fixed_json_obj)
                    except json.JSONDecodeError:
                        continue  # 如果修复失败，跳过当前匹配
    except Exception as e:
        print(f"解析错误: {e}")
        return []
    return valid_jsons

def fix_json(llm_output):
    # 修复可能存在的JSON格式问题，例如替换单引号为双引号
    fixed_output = llm_output.replace("'", '"')
    # 尝试解析修复后的JSON字符串
    try:
        json_object = json.loads(fixed_output)
        return json.dumps(json_object)  # 返回修复并解析成功的JSON字符串
    except json.JSONDecodeError as e:
        print(f"解析错误: {e}。在处理字符串: {fixed_output}")
        return None
    
# def fix_json(input_string):
#     try:
#         # 处理字符串，替换不规范的引号等
#         fixed_string = input_string.replace("\'", "\"").replace('答：', '')
#         # 尝试解析修正后的字符串
#         json_obj = json.loads(fixed_string)
#         # 确保总是返回一个列表
#         return [json_obj] if isinstance(json_obj, dict) else json_obj
#     except json.JSONDecodeError as e:
#         print(f"修正后的解析错误: {e}")
#         return []
