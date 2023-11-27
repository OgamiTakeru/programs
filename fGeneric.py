import datetime  # 日付関係
import json


def str_to_time(str_time):
    """
    時刻（文字列 yyyy/mm/dd hh:mm:mm）をDateTimeに変換する。
    何故かDFないの日付を扱う時、isoformat関数系が使えない。。なぜだろう。
    :param str_time:
    :return:
    """
    time_dt = datetime.datetime(int(str_time[0:4]),
                                int(str_time[5:7]),
                                int(str_time[8:10]),
                                int(str_time[11:13]),
                                int(str_time[14:16]),
                                int(str_time[17:19]))
    return time_dt


def now():
    now_str = f'{datetime.datetime.now():%Y/%m/%d %H:%M:%S}'
    day = now_str[5:10]  # 0101
    day = day.replace("0", "")  # 1/1
    time = now_str[11:19]  # 09:10
    day_time = day + "_" + time
    return day_time  # 文字列型の日付（秒まであり）を返す


def delYear(original_time):
    # 2023/01/01 09:10:12
    day = original_time[5:10]  # 01/01
    day = day.replace("0", "")  # 1/1
    time = original_time[11:16]  # 09:10
    day_time = day + "_" + time
    return str(day_time)


def delYearDay(original_time):
    # 2023/01/01 09:10:12
    day = original_time[5:10]  # 01/01
    day = day.replace("0", "")  # 1/1
    time = original_time[11:16]  # 09:10
    return str(time)


def cal_at_least(min_value, now_value):
    # 基本的にはnow_valueを返したいが、min_valueよりnow_valueが小さい場合はmin_vauleを返す
    # min_value = 2pips  now_value=3の場合は、３、min_value = 2pips  now_value=1 の場合　２を。
    if now_value >= min_value:
        ans = now_value
    else:
        ans = min_value
    # print(" CAL　MIN", ans)
    return ans


def cal_at_most(max_value, now_value):
    # 基本的にはnow_valueを返却したいが、max_valueよりnow_vaueが大きい場合はmax_valueを返却
    # max_value = 2pips  now_value=3の場合は2, max_value = 2pips  now_value=1 の場合　1を。
    if now_value >= max_value:
        ans = max_value
    else:
        ans = now_value
    # print(" CAL　MAX", ans)
    return ans


def cal_at_least_most(min_value, now_value, most_value):
    temp = cal_at_least(min_value, now_value)
    ans = cal_at_most(most_value, temp)
    return ans


def print_arr(arr):
    for i in range(len(arr)):
        # print("ー", i, "ーーーーーーーーーーーーーーーーー")
        print(arr[i])
    # print("↑ーーーーーーーーーーーーーーーーーーーーーーー")


def print_json(dic):
    print(json.dumps(dic, indent=2, ensure_ascii=False))

