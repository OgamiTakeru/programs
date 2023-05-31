from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
from scipy.signal import argrelmin, argrelmax
from numpy import linalg as LA
import numpy as np
import datetime
import math
import matplotlib.pyplot as plt

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


def info_from_df(detail_df, ans_dic, na):
    """
    与えられた５秒足のデータから、データを取得する
    :param detail_df:test
    :param ans_dic 情報
    :return:
    """
    # 変数の変換
    latest_ans = ans_dic['figure_turn_result']['latest_turn_dic']['latest_ans']
    oldest_ans = ans_dic['figure_turn_result']['latest_turn_dic']['oldest_ans']
    # figure_union = ans_dic['figure_result']
    macd_ans = ans_dic['macd_result']

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
            dr = d.sort_index(ascending=False)  # ★dが毎回の取得と同義⇒それを逆(最新が上)にする（逆を意味するrをつける）

            # ■直近のデータから、分析を実施する
            inspection_condition = {
                "now_price": dr.iloc[0]['open'],  # 現在価格を渡す
                "data_r": dr,  # 時刻降順（直近が上）のデータを渡す
                "figure": {"ignore": 1, "latest_n": 2, "oldest_n": 30},
                "macd": {"short": 20, "long": 30},
                "save": False,  # データをCSVで保存するか（検証ではFalse推奨。Trueの場合は以下は必須）
                "time_str": "",  # 記録用の現在時刻
            }
            ans_dic = f.inspection_candle(inspection_condition)  # 状況を検査する（買いフラグの確認）
            # ignore = 1  # 最初（現在を意味する）
            # dr_latest_n = 2
            # dr_oldest_n = 30
            # latest_df = dr[ignore: dr_latest_n + ignore]  # 直近のn個を取得
            # oldest_df = dr[dr_latest_n + ignore - 1: dr_latest_n + dr_oldest_n + ignore - 1]  # 前半と１行をラップさせる。
            # latest_ans = f.range_direction_inspection(latest_df)  # 何連続で同じ方向に進んでいるか（直近-1まで）
            # oldest_ans = f.range_direction_inspection(oldest_df)  # 何連続で同じ方向に進んでいるか（前半部分）
            # ans_42 = f.compare_ranges(oldest_ans, latest_ans, dr.iloc[0]['open'])  # 引数の順番に注意！（左がOldest）⇒注文価格情報を取得
            #
            # # MACDを検討する
            # # MACD解析
            # latest_macd_r_df = dr[0: 30]  # 中間に重複のないデータフレーム
            # latest_macd_df = latest_macd_r_df.sort_index(ascending=True)  # 一回正順に（下が新規に）
            # latest_macd_df = oanda_class.add_macd(latest_macd_df)  # macdを追加
            # macd_ans = f.macd_judge(latest_macd_df)

            # if ans_42["turn_ans"] == 0:
            #     # print("　折り返しの該当なし", dr.iloc[0]['time_jp'])
            #     pass

            if ans_dic['judgment'] != 0:
                # タイミング発生★★★！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
                print("★★★★")
                # ★★★★変数の入れ替え（深くなるため、コード短縮化の為）
                print(ans_dic['figure_turn_result'])
                latest_turn = ans_dic['figure_turn_result']['latest_turn_dic']
                figure_latest = ans_dic['figure_turn_result']['latest_turn_dic']['latest_ans']
                figure_oldest = ans_dic['figure_turn_result']['latest_turn_dic']['oldest_ans']
                line_base = ans_dic['figure_turn_result']['order_dic']['target_price']  # 基準となる価格（=直近のクローズ価格）
                expect_direction = ans_dic['figure_turn_result']['order_dic']['direction']
                macd = ans_dic['macd_result']
                # ★★★★検証
                each_res_dic = {
                    "entry_time": figure_latest['data'].iloc[0]["time_jp"],
                    "turn_ans": ans_dic['figure_turn_result']['result_dic']['turn_ans'],  # ★変更時注意
                    "oldest_range": figure_oldest['gap'],
                    "oldest_count": figure_oldest['count'],
                    "oldest_oldest": figure_oldest['oldest_price'],
                    "oldest_latest": figure_oldest['latest_price'],
                    "oldest_oldest_image_price": figure_oldest['oldest_image_price'],
                    "oldest_latest_image_price": figure_oldest['latest_image_price'],
                    "oldest_body": figure_oldest['support_info']["body_ave"],
                    "oldest_move": figure_oldest['support_info']["move_abs"],
                    "latest_range": figure_latest['gap'],
                    "latest_count": figure_latest['count'],
                    "latest_oldest": figure_latest['oldest_price'],
                    "latest_latest": figure_latest['latest_price'],
                    "latest_oldest_image_price": figure_latest['oldest_image_price'],
                    "latest_latest_image_price": figure_latest['latest_image_price'],
                    "latest_body": figure_latest['support_info']["body_ave"],
                    "latest_move": figure_latest['support_info']["move_abs"],
                    "direction_latest": figure_latest['direction'],
                    "return_ratio": latest_turn['return_ratio'],  # ★変更時注意
                    "pattern_num": figure_latest['support_info']["pattern_num"],
                    "pattern_num_abs": abs(figure_latest['support_info']["pattern_num"]),
                    "pattern": figure_latest['support_info']["pattern_comment"],
                    "range_judge": figure_latest['support_info']["range_expected"],
                    "macd": macd['macd'],
                    "macd_mae": macd['cross_mae'],
                    "macd_cross": macd['cross'],
                    "macd_cross_latest": macd['latest_cross'],
                    "macd_cross_time": macd['latest_cross_time'],
                    "macd_range": macd['range'],
                    "macd_range_counter": macd['range_counter']
                }
                # 一部の情報を上書きして修正する
                if figure_latest['support_info']["range_expected"] == 1:  # 順思想に行く場合
                    if figure_oldest['gap'] > 0.15:  # 15pips以上の変動後の場合
                        each_res_dic['range_judge'] = 0
                        each_res_dic['range_judje_re'] = "Change0"
                    else:
                        each_res_dic['range_judge'] = 1
                        each_res_dic['range_judje_re'] = ""
                else:  # Trend予想＝latestの方向に行く
                    each_res_dic['range_judge'] = 0
                    each_res_dic['range_judje_re'] = ""

                print(figure_latest['data'].iloc[0]["time_jp"])
                print(figure_latest['data'])

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
                # long_dic_ans = info_from_df(detail_df, latest_ans, oldest_ans, "_lo", macd_ans)
                # ceach_res_dic.update(long_dic_ans)  # 結果の辞書同士を結合（個別同士）

                # (2)20分程度で検証結果を取得
                short_detail_df=detail_df[0:361]  # 20分の場合、20分×60秒÷5 = 240
                short_dic_ans = info_from_df(short_detail_df, ans_dic, "_sh")
                each_res_dic.update(short_dic_ans)  # 結果の辞書同士を結合(個別同士）


                # 最後に全体のに結合
                res_dic_arr.append(each_res_dic)  # 全体に結合


    # 解析用結果の表示
    print(res_dic_arr)
    res_dic_df = pd.DataFrame(res_dic_arr)
    res_dic_df.to_csv(tk.folder_path + 'inspection.csv', index=False, encoding="utf-8")

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
    "candle_num": 300,
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
