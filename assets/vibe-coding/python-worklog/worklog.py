"""案件工時紀錄器：虛構教學資料，單位為整數分鐘。"""


def total_minutes(minutes):
    """加總非負整數分鐘；空清單回傳 0。"""
    total = 0
    for value in minutes:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("分鐘必須是整數，不能是文字或小數。")
        if value < 0:
            raise ValueError("分鐘不能是負數。")
        total += value
    return total


def main():
    # 學生可修改這一行的活動名稱及分鐘。
    records = [("會議", 45), ("整理資料", 30)]
    total = total_minutes([minutes for activity, minutes in records])
    for activity, minutes in records:
        print(f"{activity}：{minutes} 分鐘")
    hours, remaining = divmod(total, 60)
    print(f"總計：{total} 分鐘（{hours} 小時 {remaining} 分鐘）")


if __name__ == "__main__":
    main()
