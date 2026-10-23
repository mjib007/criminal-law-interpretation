"""案件工時紀錄器：虛構教學資料，單位為整數分鐘。"""


def total_minutes(minutes):
    """加總非負整數分鐘；空清單回傳 0。"""
    total = 0
    for value in minutes:  # 一筆一筆檢查
        # True／False 在 Python 裡會被當成 1／0，所以要另外擋下來
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("分鐘必須是整數，不能是文字或小數。")
        if value < 0:
            raise ValueError("分鐘不能是負數。")
        total += value  # 通過檢查，才加進總數
    return total


def main():
    # 學生可修改這一行的活動名稱及分鐘。
    records = [("會議", 45), ("整理資料", 30)]
    # 只取出每筆的分鐘數，交給 total_minutes 加總
    total = total_minutes([minutes for activity, minutes in records])
    for activity, minutes in records:
        print(f"{activity}：{minutes} 分鐘")
    hours, remaining = divmod(total, 60)  # 換算成幾小時又幾分鐘
    print(f"總計：{total} 分鐘（{hours} 小時 {remaining} 分鐘）")


# 直接執行這個檔案時（python worklog.py），才啟動 main()
if __name__ == "__main__":
    main()
