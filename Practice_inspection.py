from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
from scipy.signal import argrelmin, argrelmax
from numpy import linalg as LA
import numpy as np
import datetime
import math

import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.oanda_class as oanda_class
import programs.main_functions as f  # とりあえずの関数集


def range_judge(dr):
    '''
    :param dr:　上が新、下が旧のデータ（ ＝リバース状態）
    :return:
    '''
    pass
    # print("Range")
    # print(dr.head(5))


def info_from_df(detail_df, latest_ans, oldest_ans, na, macd_ans):
    """
    与えられた５秒足のデータから、データを取得する
    :param detail_df:test
    :return:
    """
    res_dic = {}  # 初期化
    print(detail_df.head(2))  # 検証データ取得！
    print(detail_df.tail(2))  # 検証データ取得！
    print(" [検証時刻:", detail_df.iloc[0]['time_jp'], "終了", detail_df.iloc[-1]["time_jp"])
    res_dic['inspect_fin_time' + na] = detail_df.iloc[-1]["time_jp"]
    entry_price = detail_df.iloc[0]["open"]
    res_dic['entry_price' + na] = entry_price

    # 検証を開始(検証データの値を収集）
    high_ins = detail_df['high'].max()  # 最高値関係を求める
    max_df = detail_df[detail_df['high'] == high_ins]  # max_dfは一時的な利用
    res_dic['high_price' + na] = high_ins
    res_dic['high_time' + na] = max_df.iloc[0]['time_jp']

    low_ins = detail_df['low'].min()  # 最低価格関係を求める
    min_df = detail_df[detail_df['low'] == low_ins]  # min_dfは一時的な利用
    res_dic['low_price' + na] = low_ins
    res_dic['low_time' + na] = min_df.iloc[0]['time_jp']

    res_dic['latest_latest_image_price' + na] = latest_ans['latest_image_price']

    if latest_ans['direction'] == 1:  # 直近が上り（谷形状の場合）
        # 上方向に折り返し（最高値を求め、そことの距離を求める）
        res_dic['minus' + na] = high_ins - latest_ans['latest_image_price']
        res_dic['plus' + na] = latest_ans['latest_image_price'] - low_ins
    else:  # 直近が下がり（山形状の場合）
        # 下方向に折り返し（最低値を求める）
        res_dic['minus' + na] = latest_ans['latest_image_price'] - low_ins
        res_dic['plus' + na] = high_ins - latest_ans['latest_image_price']

    # どっち（HighかLow）のピークが早かったかを算出する
    high_time_datetime = f.str_to_time(max_df.iloc[0]['time_jp'])  # 時間形式に直す
    low_time_datetime = f.str_to_time(min_df.iloc[0]['time_jp'])  # 時間形式に直す
    if high_time_datetime < low_time_datetime:
        #  maxの方が最初に到達
        res_dic['first_arrive' + na] = "high_price"
    else:
        #  minの方が最初に到達
        res_dic['first_arrive' + na] = "low_price"

    # ★理想として、順思想と逆思想　どっちだったら勝てるかのを推測する
    lc = 0.05
    tp = 0.09

    # LCの価格とTPの価格を求める
    # position_direction = latest_ans['direction'] * -1
    position_direction = macd_ans['cross']
    entry_price = detail_df.iloc[0]["open"]
    if position_direction == 1:  # 買いポジションの場合
        tp_price = entry_price + tp
        lc_price = entry_price - lc
    else:  # 売りポジの場合
        tp_price = entry_price - tp
        lc_price = entry_price + lc

    # LCに達成するタイミングを算出する
    tp_flag = 0
    lc_flag = 0
    tp_timing = lc_timing = '2026/05/22 10:15:00'  # とりあえず先の日付
    for index, item in detail_df.iterrows():  #
        if item['low'] < tp_price < item['high']:
            # tp_priceを含む場合
            if tp_flag == 0:
                tp_timing = item['time_jp']
                tp_flag = 1

        if item['low'] < lc_price < item['high']:
            # lc_price を含み場合
            if lc_flag == 0:
                lc_timing = item['time_jp']
                lc_flag = 1

        if tp_flag == 1 and lc_flag == 1:
            # 両方見つかっている場合、その時点で終了する
            break

    if tp_flag == 0 and lc_flag==0:
        # とっちも満たさない場合
        ans_timing = 0
        ans = 0
        tp_timing = lc_timing = 0
        ans_pips = 0
    elif tp_flag == 1 and lc_flag==1:
        # 両方満たす場合
        if f.str_to_time(tp_timing) < f.str_to_time(lc_timing):
            # TPの方が早い
            ans = 1  # TP
            ans_timing = tp_timing
            ans_pips = tp
        else:
            # LCの方が早い
            ans = -1  # LC
            ans_timing = lc_timing
            ans_pips = lc
    else:
        if tp_flag == 1:  # TPの達成の場合
            ans = 1  # TP
            ans_timing = tp_timing
            lc_timing = 0  # LCには入っていない
            ans_pips = tp
        else:
            ans = -1  # LC
            ans_timing = lc_timing
            tp_timing = 0  # TPには入っていない
            ans_pips = lc
    res_dic['position_direction'] = position_direction
    res_dic['tp_time'] = tp_timing
    res_dic['tp_price'] = tp_price
    res_dic['lc_time'] = lc_timing
    res_dic['lc_price'] = lc_price
    res_dic['ans'] = ans
    res_dic['ans_pips'] = ans_pips
    res_dic['ans_timing'] = ans_timing

    # upper_gap = high_ins - latest_ans['latest_image_price']
    # lower_gap = latest_ans['latest_image_price'] - low_ins
    # #
    # # if latest_ans['direction'] == 1:
    # #     # 谷方向の場合
    # #     if high_time_datetime < low_time_datetime:
    # #         # 最初の到達は、「高い価格」
    # #         if upper_gap >= lc:
    # #             # LCに相当する場合
    # #             # ⇒レンジ方向が正解（谷＋逆思想）
    # #             ans = "Range〇"
    # #         elif upper_gap < lc and lower_gap < tp:
    # #             # LCにもTPにも相当しない場合
    # #             ans = "NoCount"
    # #         elif lower_gap >= tp:
    # #             ans = "Trend〇"
    # #     # 谷方向の場合
    # #     if high_time_datetime > low_time_datetime:
    # #         # 最初の到達は、「低い価格」
    # #         if lower_gap >= lc:
    # #             # LCに相当する場合
    # #             # ⇒レンジ方向が正解（谷＋逆思想）
    # #             ans = "Range〇"
    # #         elif upper_gap < lc and lower_gap < tp:
    # #             # LCにもTPにも相当しない場合
    # #             ans = "NoCount"
    # #         elif lower_gap >= tp:
    # #             ans = "Trend〇"
    # # else:
    # #     # 山方向の場合
    # #     if high_time_datetime < low_time_datetime:
    # #         # 最初の到達はHigh側
    # #         if upper_gap >= lc:
    # #             # upperがLCを超える場合⇒Range
    # #             ans = "Range〇"
    # #         elif upper_gap < lc:
    # #             # LCに最初到達しなかった場合
    # #             if lower_gap < tp:
    # #                 # どっちにも触れない場合
    # #                 ans = "No"
    # #             else:
    # #                 # 最後にTPに触れる場合⇒Range
    # #                 ans = "Range"
    #
    # # 順思想ベースで検討する
    # if latest_ans['direction'] == 1:  # 谷形状の場合
    #     if high_time_datetime < low_time_datetime:  # highの方が先に来る場合
    #         if upper_gap > tp:
    #             ans = "Win1"
    #             ans_time = high_time_datetime
    #         elif upper_gap < tp and lower_gap > lc:
    #             ans = "Lose1"
    #             ans_time = low_time_datetime
    #         elif upper_gap < tp and lower_gap < lc:
    #             ans = "No1"
    #             ans_time = ""
    #         else:
    #             ans = "n"
    #             ans_time = ""
    #     else:
    #         if lower_gap > lc:
    #             ans = "Lose2"
    #             ans_time = low_time_datetime
    #         elif lower_gap < lc and upper_gap > tp:
    #             ans = "Win2"
    #             ans_time = high_time_datetime
    #         elif lower_gap < lc and upper_gap < tp:
    #             ans = "No2"
    #             ans_time = ""
    #         else:
    #             ans = "n2"
    #             ans_time = ""
    # else:
    #     if high_time_datetime < low_time_datetime:  # highの方が先に来る場合
    #         if upper_gap > tp:
    #             ans = "Win3"
    #             ans_time = high_time_datetime
    #         elif upper_gap < tp and lower_gap > lc:
    #             ans = "Lose3"
    #             ans_time = low_time_datetime
    #         elif upper_gap < tp and lower_gap < lc:
    #             ans = "No3"
    #             ans_time = ""
    #         else:
    #             ans = "n3"
    #             ans_time = ""
    #     else:
    #         if lower_gap > lc:
    #             ans = "Lose4"
    #             ans_time = low_time_datetime
    #         elif lower_gap < lc and upper_gap > tp:
    #             ans = "Win4"
    #             ans_time = high_time_datetime
    #         elif lower_gap < lc and upper_gap < tp:
    #             ans = "No4"
    #             ans_time = ""
    #         else:
    #             ans = "n4"
    #             ans_time = ""
    #
    # res_dic["ress"] = ans
    # res_dic['ress_time'] = ans_time

    # oldestRangeをそろえると、どうなるか
    ratio_base = 0.01
    temp_minus_ratio = round((res_dic['minus' + na] * ratio_base) / oldest_ans['gap'], 3)
    temp_plus_ratio = round((res_dic['plus' + na] * ratio_base) / oldest_ans['gap'], 3)
    res_dic['minus_ratio' + na] = temp_minus_ratio
    res_dic['plus_ratio' + na] = temp_plus_ratio

    return res_dic


def main_peak():
    pv_order = gl['p_order']  # 極値算出の幅
    # データの取得 and peak情報付加　＋　グラフ作成
    mid_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": gl['candle_unit'], "count": gl['candle_num']}, gl['num'])
    mid_df.to_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', index=False, encoding="utf-8")
    # print(mid_df)
    # 読み込み
    # mid_df = pd.read_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', sep=",", encoding="utf-8")  # test
    # mid_df = pd.read_csv('C:/Users/taker/Desktop/viewtest_data.csv', sep=",", encoding="utf-8")  # 読み込み

    # 検証時間を確保できない列は削除しておく。(現時刻から30分前が、調査期間の最後。それ以降はデータ取得時のエラーとなる）
    # めんどくさいから、直近の10行（50分分）は消しておく。（時間で計算してもいいが。。）
    # mid_df = mid_df[:-10]
    # mid_df.to_csv('C:/Users/taker/Desktop/Peak_TEST_DATA2.csv', index=False, encoding="utf-8")

    # 調査を行う
    # 調査に利用する変数を定義
    mid_df['entry'] = None
    mid_df['entry_f'] = None
    mid_df['tp'] = None
    entry_count = tp_count = lc_count = 0
    res_dic_arr = []
    inspection_range = 40  # 一回にN行分を取得して検討する
    for i in range(len(mid_df)):
        d = mid_df[len(mid_df)-inspection_range-i: len(mid_df)-i]  # 旧側(index0）を固定。新側をインクリメントしていきたい。最大３０行
        # 対象の範囲を調査する (実際ではdが取得された範囲）
        if len(d) >= inspection_range:
            # 関連情報の取得（必須）]
            # print("★")
            index_graph = d.index.values[-1]  # インデックスを確認
            dr = d.sort_index(ascending=False)  # ★dが毎回の取得と同義⇒それを逆にする（逆を意味するrをつける）

            # 4-2
            ignore = 1  # 最初（現在を意味する）
            dr_latest_n = 2
            dr_oldest_n = 30
            latest_df = dr[ignore: dr_latest_n + ignore]  # 直近のn個を取得
            oldest_df = dr[dr_latest_n + ignore - 1: dr_latest_n + dr_oldest_n + ignore - 1]  # 前半と１行をラップさせる。
            latest_ans = f.range_direction_inspection(latest_df)  # 何連続で同じ方向に進んでいるか（直近-1まで）
            oldest_ans = f.range_direction_inspection(oldest_df)  # 何連続で同じ方向に進んでいるか（前半部分）
            ans_42 = f.compare_ranges(oldest_ans, latest_ans, dr.iloc[0]['open'])  # 引数の順番に注意！（左がOldest）⇒注文価格情報を取得

            # MACDを検討する
            # MACD解析
            latest_macd_r_df = dr[0: 30]  # 中間に重複のないデータフレーム
            latest_macd_df = latest_macd_r_df.sort_index(ascending=True)  # 一回正順に（下が新規に）
            latest_macd_df = oanda_class.add_macd(latest_macd_df)  # macdを追加
            macd_ans = f.macd_judge(latest_macd_df)

            if ans_42["union_ans"] == 0:
                # print("　折り返しの該当なし", dr.iloc[0]['time_jp'])
                pass
            if ans_42["union_ans"] == 1 or macd_ans['cross'] != 0:
                # タイミング発生★★★！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
                print("★★★★")
                print(latest_df.iloc[0]["time_jp"])
                print(latest_ans['data'])

                # ★★★★検証フェーズ
                # 結果格納用
                each_res_dic = {
                    "entry_time": latest_df.iloc[0]["time_jp"],
                    "union_ans": ans_42['union_ans'],
                    "oldest_range": oldest_ans['gap'],
                    "oldest_count": oldest_ans['count'],
                    "oldest_oldest": oldest_ans['oldest_price'],
                    "oldest_latest": oldest_ans['latest_price'],
                    "oldest_oldest_image_price": oldest_ans['oldest_image_price'],
                    "oldest_latest_image_price": oldest_ans['latest_image_price'],
                    "oldest_body": oldest_ans['union_info_support_dic']["body_ave"],
                    "oldest_move": oldest_ans['union_info_support_dic']["move_abs"],
                    # "old_high": oldest_ans['high_price'],
                    # "old_low": oldest_ans['low_price'],
                    "latest_range": latest_ans['gap'],
                    "latest_count": latest_ans['count'],
                    "latest_oldest": latest_ans['oldest_price'],
                    "latest_latest": latest_ans['latest_price'],
                    "latest_oldest_image_price": latest_ans['oldest_image_price'],
                    "latest_latest_image_price": latest_ans['latest_image_price'],
                    "latest_body": latest_ans['union_info_support_dic']["body_ave"],
                    "latest_move": latest_ans['union_info_support_dic']["move_abs"],
                    # "latest_high": latest_ans['high_price'],
                    # "latest_low": latest_ans['low_price'],
                    "direction_latest": latest_ans['direction'],
                    "return_ratio": ans_42['union_info']['return_ratio'],
                    "pattern_num": latest_ans['union_info_support_dic']["pattern_num"],
                    "pattern_num_abs": abs(latest_ans['union_info_support_dic']["pattern_num"]),
                    "pattern": latest_ans['union_info_support_dic']["pattern_comment"],
                    "range_judge": latest_ans['union_info_support_dic']["range_expected"],
                    "macd": macd_ans['macd'],
                    "macd_mae": macd_ans['cross_counter'],
                    "macd_cross": macd_ans['cross'],
                    "macd_cross_latest": macd_ans['latest_cross'],
                    "macd_cross_time": macd_ans['latest_cross_time']
                }
                # 一部の情報を上書きして修正する
                if latest_ans['union_info_support_dic']["range_expected"] == 1:  # 順思想に行く場合
                    if oldest_ans['gap'] > 0.15:  # 15pips以上の変動後の場合
                        each_res_dic['range_judge'] = 0
                        each_res_dic['range_judje_re'] = "Change0"
                    else:
                        each_res_dic['range_judge'] = 1
                        each_res_dic['range_judje_re'] = ""
                else:  # Trend予想＝latestの方向に行く
                    each_res_dic['range_judge'] = 0
                    each_res_dic['range_judje_re'] = ""

                # ■①　検証データの取得や、グラフ化や出力を先に行う
                # print(" entry(検証開始)",  dr.iloc[0]['time_jp'], d.iloc[-1]['time_jp'])
                mid_df.at[index_graph, "entry42"] = dr.iloc[0]['open']  # グラフ用データ追加
                detail_range_sec = 1800  # ★　N行×5S の検証を行う。 30分の場合360 50分の場合3000
                latest_row_time_dt = f.str_to_time(dr.iloc[0]['time'][:26])  # 時刻を変換する
                detail_from_time_dt = latest_row_time_dt + datetime.timedelta(minutes=0)  # 開始時刻は分単位で調整可
                detail_from_time_iso = str(detail_from_time_dt.isoformat()) + ".000000000Z"  # API形式の時刻へ（ISOで文字型。.0z付き）
                # ★★検証データの取得
                detail_df = oa.InstrumentsCandles_exe("USD_JPY",
                                                           {"granularity": 'S5', "count": int(detail_range_sec/5),
                                                            "from": detail_from_time_iso})  # ★★検証範囲の取得★★
                detail_df.drop(columns=['time'], inplace=True)

                # （１）５０分程度での検証結果を取得
                long_dic_ans = info_from_df(detail_df, latest_ans, oldest_ans, "_lo", macd_ans)
                each_res_dic.update(long_dic_ans)  # 辞書同士を結合（個別同士）

                # (2)20分程度で検証結果を取得
                # short_detail_df=detail_df[0:201]  # 20分の場合、20分×60秒÷5 = 240
                # short_dic_ans = info_from_df(short_detail_df, latest_ans, oldest_ans, "_sh")
                # each_res_dic.update(short_dic_ans)  # 辞書同士を結合(個別同士）


                # 最後に全体のに結合
                res_dic_arr.append(each_res_dic)  # 全体に結合


                # print(detail_df.head(3))  # 検証データ取得！
                # print(detail_df.tail(3))  # 検証データ取得！
                # print(" [検証時刻:", detail_df.iloc[0]['time_jp'], "終了", detail_df.iloc[-1]["time_jp"])
                # res_dic['inspect_fin_time'] = detail_df.iloc[-1]["time_jp"]
                #
                # # 検証を開始(検証データの値を収集）
                # high_ins = detail_df['high'].max()  # 最高値関係を求める
                # max_df = detail_df[detail_df['high'] == high_ins]  # max_dfは一時的な利用
                # res_dic['high'] = high_ins
                # res_dic['high_time'] = max_df.iloc[0]['time_jp']
                # low_ins = detail_df['low'].min()  # 最低価格関係を求める
                # min_df = detail_df[detail_df['low'] == low_ins]  # min_dfは一時的な利用
                # res_dic['low'] = low_ins
                # res_dic['low_time'] = min_df.iloc[0]['time_jp']
                #
                # res_dic['latest_latest_image_price'] = latest_ans['latest_image_price']
                #
                # if res_dic['direction_latest'] == 1:  # 直近が上り（谷形状の場合）
                #     # 上方向に折り返し（最高値を求め、そことの距離を求める）
                #     res_dic['minus'] = high_ins - latest_ans['latest_image_price']
                #     res_dic['plus'] = latest_ans['latest_image_price'] - low_ins
                # else:  # 直近が下がり（山形状の場合）
                #     # 下方向に折り返し（最低値を求める）
                #     res_dic['minus'] = latest_ans['latest_image_price'] - low_ins
                #     res_dic['plus'] = high_ins - latest_ans['latest_image_price']
                #
                # # oldestRangeをそろえると、どうなるか
                # ratio_base = 0.01
                # temp_minus_ratio = round((res_dic['minus'] * ratio_base)/res_dic['oldest_range'], 3)
                # temp_plus_ratio = round((res_dic['plus'] * ratio_base)/res_dic['oldest_range'], 3)
                # res_dic['minus_ratio'] = temp_minus_ratio
                # res_dic['plus_ratio'] = temp_plus_ratio

                # res_dic_arr.append(res_dic)
        #
        #         # ■②取得価格と、目標価格を設定
        #         direction = latest_ans['direction']
        #         entry_f_price = latest_ans['oldest_price'] - (0.02 * direction) # 順方向のみ
        #         tp_f_price = entry_f_price - (0.09 * direction)
        #         lc_f_price = entry_f_price + (0.09 * direction)
        #         entry_r_price = ans_42['info']['ref_r_entry']  # rは取り方が特殊
        #
        #         # ##範囲を検討する
        #         arrive_entry_flag = 0
        #         arrive_tp_flag = 0
        #         arrive_lc_flag = 0
        #
        #         # ■③実際の検証を行う
        #         position_flag = 0
        #         counter = 0
        #         for index, data in detail_df.iterrows():  # 検討範囲を検討する
        #             counter = counter + 1
        #             if position_flag == 0:  # ポジションがない場合
        #                 if data['low'] < entry_f_price < data['high']:  # 範囲にエントリー価格があれば
        #                     print(" ポジション取得")
        #                     position_flag = 1
        #                     mid_df.at[index_graph, "entry_f"] = dr.iloc[0]['open']  # グラフ用データ追加
        #                     arrive_tp_flag = 1
        #                     entry_count = entry_count + 1
        #                     res_dic['Position_time'] = data['time_jp']
        #                     res_dic['Position_price'] = entry_f_price
        #                     res_dic['Position_wait_time'] = counter * 5
        #             else:  # ポジションがある場合
        #                 if data['low'] < lc_f_price < data['high']:  # 範囲にLC価格があれば
        #                     print(" LC。。。")
        #                     mid_df.at[index_graph, "f_lc"] = data['low']  # グラフ用データ追加
        #                     res_dic['Res_time'] = data['time_jp']
        #                     res_dic['Res'] = "lc"
        #                     lc_count = lc_count + 1
        #                     break
        #                 elif data['low'] < tp_f_price < data['high']:  # 範囲にLC価格があれば
        #                     print(" TP")
        #                     mid_df.at[index_graph, "f_tp"] = data['low']  # グラフ用データ追加
        #                     res_dic['Res_time'] = data['time_jp']
        #                     res_dic['Res'] = "TP"
        #                     tp_count = tp_count + 1
        #                     break
        #
        #
        #         res_dic_arr.append(res_dic)
        #
        # else:
        #     # サイズ無しの場合
        #     pass


    # 解析用結果の表示
    print(res_dic_arr)
    res_dic_df = pd.DataFrame(res_dic_arr)
    res_dic_df.to_csv(tk.folder_path + 'inspection2.csv', index=False, encoding="utf-8")

    #  通常より伸びた足を取得する（通常の３倍程度の足の後は、戻しが強いので、そこを取りたい）
    # mid_df['big_foot'] = mid_df['body_abs'].apply(lambda x: '1' if x>=0.025 else '0')



gl = {
    # 5分足対象
    "high_v": "high",  # "inner_high"
    "low_v": "low",  # "inner_low"５
    "p_order": 2,  # ピーク検出の幅  1分足だと４くらい？？
    "tiltgap_horizon": 0.0041,  # peak線とvalley線の差が、左記数字以下なら平行と判断。この数値以下なら平行。
    "tiltgap_pending": 0.011,  # peak線とvalley線の差が、左記数値以下なら平行以上-急なクロス以前と判断。それ以上は強いクロスとみなす
    "tilt_horizon": 0.0029,  # 単品の傾きが左記以下の場合、水平と判断。　　0.005だと少し傾き気味。。
    "tilt_pending": 0.03,  # 単品の傾きが左記以下の場合、様子見の傾きと判断。これ以上で急な傾きと判断。
    "candle_num": 500,
    "num": 1,  # candle
    "candle_unit": "M5",
}


def graph():
    pv_order = gl['p_order']  # 極値算出の幅
    # データの取得 and peak情報付加　＋　グラフ作成
    mid_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": gl['candle_unit'], "count": gl['candle_num']}, gl['num'])
    mid_df.to_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', index=False, encoding="utf-8")
    f.draw_graph(mid_df)

oa = oanda_class.Oanda(tk.accountID, tk.access_token, "practice")
main_peak()
# # graph()




mid_df = pd.read_csv('C:/Users/taker/Desktop/main_data5.csv', sep=",", encoding="utf-8")
print(mid_df)
