import pandas as pd

# Define the columns for the CSV file
columns = ["预约人姓名", "会议室", "会议室容量", "会议时间段", "会议时长", "会议主题", "会议名称"]

# Create example data
data = [
    ["李杰", "会议室1", 10, "2024-05-28 19:30", "1小时", "项目", "项目会议"],
    ["王芳", "会议室2", 10, "2024-05-29 10:00", "2小时", "财务", "财务会议"],
    ["张伟", "会议室3", 20, "2024-05-30 14:00", "1小时", "需求", "需求会议"]
]

# Create a DataFrame
df = pd.DataFrame(data, columns=columns)

# Save DataFrame to CSV
df.to_csv("meeting_reservations.csv", index=False)
