import programs.fTurnInspection as f  # とりあえずの関数集
import pandas as pd
import json
import datetime
import matplotlib.pyplot as plt
import numpy as np
import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.classOanda as oanda_class
import programs.fPractice as prac
import programs.fTurnInspection as t  # とりあえずの関数集
import programs.fPeakLineInspection as p  # とりあえずの関数集
import programs.fTurnInspection as fTurn
import programs.fGeneric as f
import statistics

# グローバルでの宣言
oa = oanda_class.Oanda(tk.accountIDl, tk.access_tokenl, "live")  # クラスの定義


# 検証パート
def analysis_part(df_r):
    print("★★検証パート")
    print(df_r.head(2))
    print(df_r.tail(2))

    prac.turn_inspection_main(df_r)


# チェック関数のメイン用
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
    # print("　結果照合パート用データ")
    # print(res_part_df.head(2))
    # print(res_part_df.tail(2))
    # print("　検証パート用データ")
    # print(analysis_part_df.head(2))
    # print(analysis_part_df.tail(2))

    # 検証パート　todo
    analysis_part(analysis_part_df)
    # 結果照合パート todo
    # 検証と結果の関係性の確認　todo


def main():
    """
    メイン関数　全てここからスタートする。ここではデータを取得する
    :return:
    """
    # (１)情報の取得
    now_time = True  # 現在時刻実行するかどうか False True
    count = 300  # 取得する行数
    if now_time:
        # 直近の時間で検証
        df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": count}, 1)
    else:
        # 時間を指定して検証
        jp_time = datetime.datetime(2023, 12, 15, 22, 55, 6)
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

    # ■■調査用のDFの行数の指定
    res_part_low = 50  # 解析には50行必要(逆順DFでの直近R行が対象の為、[0:R]。check_mainと同値であること。
    analysis_part_low = 200  # 解析には200行必要(逆順DFで直近N行を結果パートに取られた後の為、[R:R+A])。check_mainと同値であること。
    need_analysis_num = res_part_low + analysis_part_low  # 検証パートと結果参照パートの合計。count<=need_analysis_num。

    # （2）単発調査用！！　直近N行で検証パートのテストの実を行う場合はここでTrue
    test_only = True  # Falseにすると連続調査に入る
    if test_only:
        print("Do Only Inspection")
        analysis_part(df_r[:analysis_part_low])  # 取得したデータ（直近上位順）をそのまま渡す。検証に必要なのは現在200行
        exit()

    # （3）連続検証データを渡していく（ループ　or 単発）
    loop = True  # 過去をループ処理で検証する
    if loop:
        # ループ設定True（繰り返し検証の場合）
        print("ループ処理")
        for i, item in enumerate(df_r):
            print("■", i)
            if i + need_analysis_num <= len(df_r):  # 検証用の行数が確保できていれば,検証へ進む
                check_main(df_r[i: i+need_analysis_num])  # ★チェック関数呼び出し
            else:
                break  # 検証用の行数が確保できない場合は終了
    else:
        # 単発検証
        check_main(df_r[:need_analysis_num])  # 直近からN行　# ★チェック関数呼び出し


main()


