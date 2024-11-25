# encoding=utf-8
import logging

from config import RELATED_INTENT_THRESHOLD
from scene_processor.impl.common_processor import CommonProcessor
from utils.data_format_utils import extract_continuous_digits, extract_float
from utils.helpers import send_message


class ChatbotModel:
    def __init__(self, scene_templates: dict):
        self.scene_templates: dict = scene_templates
        self.current_purpose: str = ''
        self.processors = {}
        self.self_intro_done = False
        self.slots = {
            "meetingName": None,
            "reserveEndTime": None,
            "reserveStartTime": None,
            "theme": None
        }

    def process_slot_update(self, question):
        # Check if current input is related to the previous intent scene
        # 現在の入力が前回の意図シーンに関連しているかチェック
        if self.is_related_to_last_intent(question):
            pass
        else:
            # If unrelated, re-recognize intent
            # 関連性がない場合、意図を再認識
            self.recognize_intent(question)
        logging.info('current_purpose: %s', self.current_purpose)

        if self.current_purpose in self.scene_templates:
            # Call processing logic based on scene template
            # シーンテンプレートに基づいて処理ロジックを呼び出す
            self.get_processor_for_scene(self.current_purpose)
            # Call abstract class process method
            # 抽象クラスのprocessメソッドを呼び出す
            return self.processors[self.current_purpose].process_slot(question, None)

        # If no scene matches, check if self-introduction is needed
        # シーンが一致しない場合、自己紹介が必要かチェック
        if not self.self_intro_done:
            self.self_intro_done = True
            return self.self_introduction()

        return 'No scene matched and no self-introduction needed'

    def update_slot(self, new_values):
        for item in new_values:
            name = item['name']
            value = item['value']
            if name in self.slots:
                self.slots[name] = value if value else 'none'

    def is_slot_fully_filled(self):
        return all(self.slots[key] is not None for key in self.slots)

    @staticmethod
    def load_scene_processor(self, scene_config):
        try:
            return CommonProcessor(scene_config)
        except (ImportError, AttributeError, KeyError):
            raise ImportError(f"Scene processor not found for scene_config: {scene_config}")

    def is_related_to_last_intent(self, user_input):
        """
        Determine if current input is related to the previous intent scene
        現在の入力が前回の意図シーンに関連しているかを判断する
        """
        if not self.current_purpose:
            return False
        prompt = f"Determine the relevance between current user input and current dialogue scene:\n\nCurrent scene: {self.scene_templates[self.current_purpose]['description']}\nCurrent input: {user_input}\n\nAre these inputs related? (Answer with decimal between 0.0 and 1.0)"
        result = send_message(prompt, None)
        return extract_float(result) > RELATED_INTENT_THRESHOLD

    def recognize_intent(self, user_input):
        # Generate options based on scene templates
        # シーンテンプレートに基づいてオプションを生成
        purpose_options = {}
        purpose_description = {}
        index = 1
        for template_key, template_info in self.scene_templates.items():
            purpose_options[str(index)] = template_key
            purpose_description[str(index)] = template_info["description"]
            index += 1
        options_prompt = "\n".join([f"{key}. {value} - Please reply {key}" for key, value in purpose_description.items()])
        options_prompt += "\n0. Other scenes - Please reply 0"

        # Send options to user
        # オプションをユーザーに送信
        user_choice = send_message(f"There are several scenes below, please judge based on user input, answer only with option number\n{options_prompt}\nUser input: {user_input}\nPlease reply with number:", user_input)

        logging.debug(f'purpose_options: %s', purpose_options)
        logging.debug(f'user_choice: %s', user_choice)

        user_choices = extract_continuous_digits(user_choice)

        # Get corresponding scene based on user choice
        # ユーザーの選択に基づいて対応するシーンを取得
        if user_choices and user_choices[0] != '0':
            self.current_purpose = purpose_options[user_choices[0]]

        if self.current_purpose:
            print(f"User selected scene: {self.scene_templates[self.current_purpose]['name']}")
            return self.current_purpose
        else:
            print("Invalid option, please select again")

    def get_processor_for_scene(self, scene_name):
        if scene_name in self.processors:
            return self.processors[scene_name]

        scene_config = self.scene_templates.get(scene_name)
        if not scene_config:
            raise ValueError(f"Scene configuration named {scene_name} not found")
        
        # Pass the scene description to the processor
        # シーンの説明をプロセッサに渡す
        scene_config['description'] = self.scene_templates[scene_name]['description']

        processor_class = self.load_scene_processor(self, scene_config)
        self.processors[scene_name] = processor_class
        return self.processors[scene_name]

    def self_introduction(self):
        intro_text = "Hello, I am the meeting assistant -- Xiaoyuan, happy to serve you! As an assistant for park meeting reservations and services, I can help you with various meeting-related questions, including meeting reservations, inquiries, and catering services. Feel free to consult me anytime if you encounter any difficulties or questions, and I will do my best to assist you."
        return intro_text

    def process_multi_question(self, user_input):
        """
        Process multi-round Q&A
        複数回の質疑応答を処理する
        """
        # Check if current input is related to the previous intent scene
        # 現在の入力が前回の意図シーンに関連しているかチェック
        if self.is_related_to_last_intent(user_input):
            pass
        else:
            # If unrelated, re-recognize intent
            # 関連性がない場合、意図を再認識
            self.recognize_intent(user_input)
        logging.info('current_purpose: %s', self.current_purpose)

        if self.current_purpose in self.scene_templates:
            # Call processing logic based on scene template
            # シーンテンプレートに基づいて処理ロジックを呼び出す
            self.get_processor_for_scene(self.current_purpose)
            # Call abstract class process method
            # 抽象クラスのprocessメソッドを呼び出す
            return self.processors[self.current_purpose].process(user_input, None)

        # If no scene matches, check if self-introduction is needed
        # シーンが一致しない場合、自己紹介が必要かチェック
        if not self.self_intro_done:
            self.self_intro_done = True
            return self.self_introduction()

        return 'No scene matched and no self-introduction needed'
