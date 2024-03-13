# encoding=utf-8
import json
import requests
import config
import dashscope


def send_local_qwen_message(message, user_input):
    """
    请求Qwen函数
    """
    print('--------------------------------------------------------------------')
    if config.DEBUG:
        print('prompt输入:', message)
    elif user_input:
        print('用户输入:', user_input)
    print('----------------------------------')
    headers = {
        # "Authorization": f"Bearer {config.API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "prompt": message,
        "history": [
            [
                "You are a helpful assistant.", ""
            ]
        ]
    }

    try:
        response = requests.post(config.Qwen_URL, headers=headers, json=data, verify=False)
        if response.status_code == 200:
            answer = response.json()['data']
            print('LLM输出:', answer)
            print('--------------------------------------------------------------------')
            return answer
        else:
            print(f"Error: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None


def send_chatgpt_message(message, user_input):
    """
    请求chatGPT函数
    """
    print('--------------------------------------------------------------------')
    if config.DEBUG:
        print('prompt输入:', message)
    elif user_input:
        print('用户输入:', user_input)
    print('----------------------------------')
    headers = {
        "Authorization": f"Bearer {config.API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "gpt-4-1106-preview",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"{message}"}
        ]
    }

    try:
        response = requests.post(config.GPT_URL, headers=headers, json=data, verify=False)
        if response.status_code == 200:
            answer = response.json()["choices"][0]["message"]['content']
            print('LLM输出:', answer)
            print('--------------------------------------------------------------------')
            return answer
        else:
            print(f"Error: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None


def send_tongyiqwen_message(message, user_input):
    """
    请求通义千问api函数
    """
    print("--------------------------------------------------------------------")
    if config.DEBUG:
        print("prompt输入:", message)
    elif user_input:
        print("用户输入:", user_input)
    print("----------------------------------")
    # 配置qwen的key
    dashscope.api_key = config.DASHSCOPE_API_KEY
    try:
        response = dashscope.Generation.call(
            model=dashscope.Generation.Models.qwen_turbo, prompt=message
        )
        if response.status_code == 200:
            answer = response.output["text"]
            print("LLM输出:", answer)
            print(
                "--------------------------------------------------------------------"
            )
            return answer
        else:
            print(f"Error: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None

def fetch_decision_from_api(self, slot, user_input, scene_description):
        # 构建请求GPT的消息
        message = build_api_decision_prompt(slot, user_input, scene_description)

        # 构建请求数据
        data = {
            "model": "gpt-4-1106-preview",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message}
            ]
        }

        # 设置请求头，包括认证
        headers = {
           "Authorization": f"Bearer {config.API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            # 发起请求
            response = requests.post(config.GPT_URL, headers=headers, json=data)    
            if response.status_code == 200:
                # 解析响应
                answer = response.json()["choices"][0]["message"]['content'].strip()
                # 根据GPT的回答更新槽位或调用外部API
                if answer.lower() == "ask_user" or answer.lower() == "call_api":
                    result = answer.lower()
                else:
                    # 如果GPT的回答不是预期中的，可以选择重试或采取其他策略
                    result = "unexpected_response"
                return result
            else:
                print(f"Error: {response.status_code}")
                return "error"
        except requests.RequestException as e:
            print(f"Request error: {e}")
            return "request_error"
        
def build_api_decision_prompt(slot, user_input, scene_description):
    """
    构建用于询问GPT是否应该询问用户或调用API的提示
    """
    prompt = f"Given the current conversation context, the scene description '{scene_description}', and the following slot information: {json.dumps(slot, ensure_ascii=False)}, with the user's last input being: '{user_input}', should the next action be to 'ask_user' for more information or 'call_api' to automatically fill the missing slot data? Please respond with either 'ask_user' or 'call_api' only."
    return prompt