# encoding=utf-8
import csv
import os
from datetime import datetime
from typing import Dict

import requests

class AfterSlotProcessor:
    def __init__(self, slot_data: Dict):
        self.slot_data = slot_data

    def process_park_property_device(self) -> str:
        """处理园区设备过保问题"""
        # 假设从外部 API 获取设备数据
        device_data = self._fetch_device_data(self.slot_data)

        # 检查设备是否过保
        is_overdue = self._check_device_overdue(device_data)

        if is_overdue:
            return f"设备 {device_data['设备名称']} (编号 {device_data['设备编号']}) 已过保,下一次维保日期为 {device_data['下一次维保日期']}"
        else:
            return f"设备 {device_data['设备名称']} (编号 {device_data['设备编号']}) 未过保,下一次维保日期为 {device_data['下一次维保日期']}"

    def process_park_property_abnormal_facilities_and_equipment(self) -> str:
        """处理园区异常设施设备"""
        # 假设从外部 API 获取设施设备数据
        facility_data = self._fetch_facility_data(self.slot_data)

        if facility_data['设施或设备是否处于异常状态']:
            return f"设施/设备 {facility_data['设施或设备的名称']} (编号 {facility_data['设施或设备的编号']}) 处于异常状态: {facility_data['设施或设备的异常状态的具体描述']}"
        else:
            return f"设施/设备 {facility_data['设施或设备的名称']} (编号 {facility_data['设施或设备的编号']}) 运行正常"

    def process_park_property_order_tracking(self) -> str:
        """处理园区工单执行情况查询"""
        # 假设从外部 API 获取工单数据
        order_data = self._fetch_order_data(self.slot_data)

        return f"工单 {order_data['工单编号']} ({order_data['工单名称']}) 状态: {order_data['工单状态']}\n" \
               f"创建时间: {order_data['创建时间']}\n" \
               f"要求开始时间: {order_data['要求开始时间']}\n" \
               f"要求完成时间: {order_data['要求完成时间']}\n" \
               f"实际结束时间: {order_data['实际结束时间']}\n" \
               f"执行人: {order_data['执行人']}"

    def process_park_property_visitor_registration(self) -> str:
        """处理园区访客登记"""
        visitor_data = self.slot_data
        return f"访客登记表\n" \
               f"姓名: {visitor_data['访客姓名']}\n" \
               f"身份证号: {visitor_data['访客身份证号']}\n" \
               f"手机号码: {visitor_data['访客手机号码']}\n" \
               f"拜访企业: {visitor_data['摆放企业']}"

    def process_park_property_surveillance_retrieval(self) -> str:
        """处理园区监控视频调取"""
        # 假设从外部 API 获取监控视频数据
        video_data = self._fetch_surveillance_video(self.slot_data)

        # 保存视频文件
        video_path = self._save_video_file(video_data)

        return f"监控录像已就绪,可以通过以下链接访问: {video_path}"

    def process_park_property_work_order_dispatch(self) -> str:
        """处理园区工单派发"""
        # 假设从外部 API 获取工单派发结果
        dispatch_result = self._dispatch_work_order(self.slot_data)

        return f"工单 {dispatch_result['工单编号']} 已成功派发给 {dispatch_result['工单负责人']}"

    def _fetch_device_data(self, slot_data) -> Dict:
        """模拟从外部 API 获取设备数据"""
        # 这里应该调用真实的 API 端点并获取数据
        # 为了示例,只返回一个模拟的数据字典
        return {
            "设备编号": slot_data["设备编号"],
            "设备名称": slot_data["设备名称"],
            "下一次维保日期": "2023-08-15"
        }

    def _check_device_overdue(self, device_data) -> bool:
        """检查设备是否过保"""
        maintenance_date = datetime.strptime(device_data["下一次维保日期"], "%Y-%m-%d").date()
        today = datetime.now().date()
        return today > maintenance_date

    def _fetch_facility_data(self, slot_data) -> Dict:
        """模拟从外部 API 获取设施设备数据"""
        # 这里应该调用真实的 API 端点并获取数据
        # 为了示例,只返回一个模拟的数据字典
        return {
            "设施或设备的编号": slot_data["设施或设备的编号"],
            "设施或设备的名称": slot_data["设施或设备的名称"],
            "设施或设备是否处于异常状态": True,
            "设施或设备的异常状态的具体描述": "无法正常启动"
        }

    def _fetch_order_data(self, slot_data) -> Dict:
        """模拟从外部 API 获取工单数据"""
        # 这里应该调用真实的 API 端点并获取数据
        # 为了示例,只返回一个模拟的数据字典
        return {
            "工单编号": slot_data["工单编号"],
            "工单名称": slot_data["工单名称"],
            "创建时间": "2023-05-01 08:00",
            "工单类型": slot_data["工单类型"],
            "工单来源": slot_data["工单来源"],
            "工单状态": slot_data["工单状态"],
            "要求开始时间": slot_data["要求开始时间"],
            "要求完成时间": slot_data["要求完成时间"],
            "实际结束时间": slot_data["实际结束时间"],
            "执行人": slot_data["执行人"]
        }

    def _fetch_surveillance_video(self, slot_data) -> bytes:
        """模拟从外部 API 获取监控视频数据"""
        # 这里应该调用真实的 API 端点并获取视频数据
        # 为了示例,只返回一个模拟的视频数据
        video_data = b"THIS IS A MOCK VIDEO DATA"
        return video_data

    def _save_video_file(self, video_data: bytes) -> str:
        """保存视频文件到临时位置"""
        video_path = os.path.join(os.path.dirname(__file__), "tmp_video.mp4")
        with open(video_path, "wb") as f:
            f.write(video_data)
        return video_path

    def _dispatch_work_order(self, slot_data) -> Dict:
        """模拟向外部 API 派发工单"""
        # 这里应该调用真实的 API 端点并派发工单
        # 为了示例,只返回一个模拟的派发结果
        return {
            "工单编号": "1234567890",
            "工单负责人": slot_data["工单负责人"]
        }