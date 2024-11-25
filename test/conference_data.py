import pandas as pd

# Define the columns for the CSV file in English
columns = ["Booker's Name", "Meeting Room", "Room Capacity", "Booking Time", "Meeting Duration", "Meeting Theme", "Meeting Name"]

# Create example data with English room names
data = [
    ["Li Jie", "Meeting Room 1", 10, "2024-05-28 19:30", "1 hour", "Project", "Project Meeting"],
    ["Wang Fang", "Meeting Room 2", 10, "2024-05-29 10:00", "2 hours", "Finance", "Finance Meeting"],
    ["Zhang Wei", "Meeting Room 3", 20, "2024-05-30 14:00", "1 hour", "Requirement", "Requirement Meeting"]
]

# Create a DataFrame
df = pd.DataFrame(data, columns=columns)

# Save DataFrame to CSV
df.to_csv("meeting_reservations.csv", index=False)