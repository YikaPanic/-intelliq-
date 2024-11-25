import csv
from datetime import datetime, timedelta
import logging

def get_slot_value(slot, name):
    for item in slot:
        if item['name'] == name:
            return item['value']
    return None

def check_and_book_meeting_room(slot):
    meeting_date_time = datetime.strptime(get_slot_value(slot, 'Specific Time for Meeting Booking'), "%Y/%m/%d %H:%M")
    meeting_duration = get_slot_value(slot, 'Meeting Duration')
    meeting_end_time = calculate_end_time(meeting_date_time, meeting_duration)
    required_capacity = int(get_slot_value(slot, 'Number of participants'))

    available_room = None
    with open('meeting_reservations.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        room_occupancies = {room: [] for room in ["Meeting Room 1", "Meeting Room 2", "Meeting Room 3"]}

        for row in reader:
            room = row["Meeting Room"]
            start_time_str = row["Booking Time"]
            try:
                start_time = datetime.strptime(start_time_str, "%Y/%m/%d %H:%M")
                end_time = calculate_end_time(start_time, row['Meeting Duration'])
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
        slot.append({'name': 'Meeting Room', 'value': available_room})
        save_reservation(slot)
        return f"Meeting successfully booked, room: {available_room}. Meeting time: {get_slot_value(slot, 'Specific Time for Meeting Booking')}, theme: {get_slot_value(slot, 'Meeting Theme')}."
    else:
        return "Sorry, no available meeting rooms at the current time. Please try another time."

def calculate_end_time(start_time, duration):
    if duration == "half an hour":
        return start_time + timedelta(minutes=30)
    elif duration == "1 hour":
        return start_time + timedelta(hours=1)
    elif duration == "2 hours":
        return start_time + timedelta(hours=2)
    else:
        raise ValueError("Invalid meeting duration")

def save_reservation(slot):
    reservation_data = {
        "Booker's Name": get_slot_value(slot, 'Meeting Booker'),
        "Meeting Room": get_slot_value(slot, 'Meeting Room'),
        "Room Capacity": get_slot_value(slot, 'Number of participants'),
        "Booking Time": get_slot_value(slot, 'Specific Time for Meeting Booking'),
        "Meeting Duration": get_slot_value(slot, 'Meeting Duration'),
        "Meeting Theme": get_slot_value(slot, 'Meeting Theme'),
        "Meeting Name": get_slot_value(slot, 'Meeting Name')
    }

    with open('meeting_reservations.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["Booker's Name", "Meeting Room", "Room Capacity", "Booking Time", "Meeting Duration", "Meeting Theme", "Meeting Name"])
        
        if csvfile.tell() == 0:
            writer.writeheader()
        
        writer.writerow(reservation_data) 