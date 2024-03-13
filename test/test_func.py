import re

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

json_data = [{"name": "采购的内容清单", "value": "打印机1台，a4纸20张，水笔5支"}]
parsed_list = prepare_json_data_for_api(json_data)
print(format_name_value_for_logging(parsed_list))


