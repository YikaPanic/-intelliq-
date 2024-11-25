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
        """Process park device warranty issues
        園区設備の保証期限問題を処理する"""
        # Assume fetching device data from external API
        # 外部APIからデバイスデータを取得すると仮定
        device_data = self._fetch_device_data(self.slot_data)

        # Check if device warranty is expired
        # デバイスの保証期限が切れているかチェック
        is_overdue = self._check_device_overdue(device_data)

        if is_overdue:
            return f"Device {device_data['device_name']} (ID {device_data['device_id']}) warranty expired, next maintenance date: {device_data['next_maintenance_date']}"
        else:
            return f"Device {device_data['device_name']} (ID {device_data['device_id']}) warranty valid, next maintenance date: {device_data['next_maintenance_date']}"

    def process_park_property_abnormal_facilities_and_equipment(self) -> str:
        """Process abnormal park facilities and equipment
        園区の異常な施設と設備を処理する"""
        # Assume fetching facility data from external API
        # 外部APIから施設データを取得すると仮定
        facility_data = self._fetch_facility_data(self.slot_data)

        if facility_data['is_facility_abnormal']:
            return f"Facility/Equipment {facility_data['facility_name']} (ID {facility_data['facility_id']}) is abnormal: {facility_data['abnormal_description']}"
        else:
            return f"Facility/Equipment {facility_data['facility_name']} (ID {facility_data['facility_id']}) is operating normally"

    def process_park_property_order_tracking(self) -> str:
        """Process park work order execution query
        園区の工單実行状況照会を処理する"""
        # Assume fetching order data from external API
        # 外部APIから工單データを取得すると仮定
        order_data = self._fetch_order_data(self.slot_data)

        return f"Work order {order_data['work_order_id']} ({order_data['work_order_name']}) status: {order_data['work_order_status']}\n" \
               f"Created time: {order_data['created_time']}\n" \
               f"Required start time: {order_data['required_start_time']}\n" \
               f"Required completion time: {order_data['required_completion_time']}\n" \
               f"Actual completion time: {order_data['actual_completion_time']}\n" \
               f"Executor: {order_data['executor']}"

    def process_park_property_visitor_registration(self) -> str:
        """Process park visitor registration
        園区の訪問者登録を処理する"""
        visitor_data = self.slot_data
        return f"Visitor registration form\n" \
               f"Name: {visitor_data['visitor_name']}\n" \
               f"ID number: {visitor_data['visitor_id_number']}\n" \
               f"Phone number: {visitor_data['visitor_phone_number']}\n" \
               f"Visiting company: {visitor_data['visiting_company']}"

    def process_park_property_surveillance_retrieval(self) -> str:
        """Process park surveillance video retrieval
        園区の監視カメラ映像取得を処理する"""
        # Assume fetching surveillance video data from external API
        # 外部APIから監視カメラ映像データを取得すると仮定
        video_data = self._fetch_surveillance_video(self.slot_data)

        # Save video file
        # 映像ファイルを保存する
        video_path = self._save_video_file(video_data)

        return f"Surveillance video is ready, you can access it via the following link: {video_path}"

    def process_park_property_work_order_dispatch(self) -> str:
        """Process park work order dispatch
        園区の工單派遣を処理する"""
        # Assume fetching work order dispatch result from external API
        # 外部APIから工單派遣結果を取得すると仮定
        dispatch_result = self._dispatch_work_order(self.slot_data)

        return f"Work order {dispatch_result['work_order_id']} has been successfully dispatched to {dispatch_result['work_order_manager']}"

    def _fetch_device_data(self, slot_data) -> Dict:
        """Mock fetching device data from external API
        外部APIからのデバイスデータ取得をモック"""
        # Should call actual API endpoint to get data
        # 実際のAPIエンドポイントを呼び出してデータを取得する必要がある
        return {
            "device_id": slot_data["device_id"],
            "device_name": slot_data["device_name"],
            "next_maintenance_date": "2023-08-15"
        }

    def _check_device_overdue(self, device_data) -> bool:
        """Check if device warranty is expired
        デバイスの保証期限が切れているかチェック"""
        maintenance_date = datetime.strptime(device_data["next_maintenance_date"], "%Y-%m-%d").date()
        today = datetime.now().date()
        return today > maintenance_date

    def _fetch_facility_data(self, slot_data) -> Dict:
        """Mock fetching facility data from external API
        外部APIからの施設データ取得をモック"""
        # Should call actual API endpoint to get data
        # 実際のAPIエンドポイントを呼び出してデータを取得する必要がある
        return {
            "facility_id": slot_data["facility_id"],
            "facility_name": slot_data["facility_name"],
            "is_facility_abnormal": True,
            "abnormal_description": "Unable to start normally"
        }

    def _fetch_order_data(self, slot_data) -> Dict:
        """Mock fetching order data from external API
        外部APIからの工單データ取得をモック"""
        # Should call actual API endpoint to get data
        # 実際のAPIエンドポイントを呼び出してデータを取得する必要がある
        return {
            "work_order_id": slot_data["work_order_id"],
            "work_order_name": slot_data["work_order_name"],
            "created_time": "2023-05-01 08:00",
            "work_order_type": slot_data["work_order_type"],
            "work_order_source": slot_data["work_order_source"],
            "work_order_status": slot_data["work_order_status"],
            "required_start_time": slot_data["required_start_time"],
            "required_completion_time": slot_data["required_completion_time"],
            "actual_completion_time": slot_data["actual_completion_time"],
            "executor": slot_data["executor"]
        }

    def _fetch_surveillance_video(self, slot_data) -> bytes:
        """Mock fetching surveillance video data from external API
        外部APIからの監視カメラ映像データ取得をモック"""
        # Should call actual API endpoint to get video data
        # 実際のAPIエンドポイントを呼び出して映像データを取得する必要がある
        # ここではモックデータを返す
        video_data = b"THIS IS A MOCK VIDEO DATA"
        return video_data

    def _save_video_file(self, video_data: bytes) -> str:
        """Save video file to temporary location
        映像ファイルを一時的な場所に保存する"""
        video_path = os.path.join(os.path.dirname(__file__), "tmp_video.mp4")
        with open(video_path, "wb") as f:
            f.write(video_data)
        return video_path

    def _dispatch_work_order(self, slot_data) -> Dict:
        """Mock dispatching work order to external API
        外部APIに工單派遣をモック"""
        # Should call actual API endpoint to dispatch work order
        # 実際のAPIエンドポイントを呼び出して工單派遣を行う必要がある
        # ここではモックの派遣結果を返す
        return {
            "work_order_id": "1234567890",
            "work_order_manager": slot_data["work_order_manager"]
        }