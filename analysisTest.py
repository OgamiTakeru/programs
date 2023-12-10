import programs.fTurnInspection as f  # とりあえずの関数集
import pandas as pd
import json
import datetime
import matplotlib.pyplot as plt
import numpy as np
import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.classOanda as oanda_class
import programs.fTurnInspection as t  # とりあえずの関数集
import programs.fPeakLineInspection as p  # とりあえずの関数集
import programs.fTurnInspection as fTurn
import programs.fGeneric as f
import statistics

# グローバルでの宣言
oa = oanda_class.Oanda(tk.accountIDl, tk.access_tokenl, "live")  # クラスの定義

# 結果確認用関数
def check_main(df_r):
    """
    受け取ったデータフレームを解析部と結果部に分割し、それぞれの結果をマージする
    :param df_r:
    :return:
    """
    # 各数の定義
    res_part_low = 50  # 解析には50行必要(逆順DFでの直近R行が対象の為、[0:R]
    analysis_part_low = 200  # 解析には200行必要(逆順DFで直近N行を結果パートに取られた後の為、[R:R+A])

    # データフレームの切り分け
    res_part_df = df_r[: res_part_low]
    analysis_part_df = df_r[res_part_low: res_part_low + analysis_part_low]
    print("　結果照合パート")
    print(res_part_df.head(2))
    print(res_part_df.tail(2))
    print("　検証パート")
    print(analysis_part_df.head(2))
    print(analysis_part_df.tail(2))




def main():
    """
    メイン関数　全てここからスタートする。ここではデータを取得する
    :return:
    """
    # (１)情報の取得
    now_time = False  # 現在時刻実行するかどうか False True
    count = 260  # 取得する行数
    if now_time:
        # 直近の時間で検証
        df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": count}, 1)
    else:
        # 時間を指定して検証
        jp_time = datetime.datetime(2023, 11, 24, 15, 20, 6)
        euro_time_datetime = jp_time - datetime.timedelta(hours=9)
        euro_time_datetime_iso = str(euro_time_datetime.isoformat()) + ".000000000Z"  # ISOで文字型。.0z付き）
        param = {"granularity": "M5", "count": count, "to": euro_time_datetime_iso}  # 最低５０行
        df = oa.InstrumentsCandles_exe("USD_JPY", param)  # 時間指定
    # データの成型と表示
    df = df["data"]  # data部のみを取得
    df.to_csv(tk.folder_path + 'analisysTEST.csv', index=False, encoding="utf-8")  # 直近保存用
    df_r = df.sort_index(ascending=False)  # 逆順に並び替え（直近が上側に来るように）
    print("全", len(df_r), "行")
    print(df_r.head(2))
    print(df_r.tail(2))

    # （２）検証データを渡していく（ループ　or 単発）
    loop = False
    if loop:
        # ループ設定True（繰り返し検証の場合）
    else:
        # 単発検証の場合
    check_main(df_r)



main()


