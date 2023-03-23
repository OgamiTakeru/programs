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
import programs.main_functions_Prac as f  # とりあえずの関数集


def range_judge(dr):
    '''
    :param dr:　上が新、下が旧のデータ（ ＝リバース状態）
    :return:
    '''
    pass
    # print("Range")
    # print(dr.head(5))


def main_peak():
    pv_order = gl['p_order']  # 極値算出の幅
    # データの取得 and peak情報付加　＋　グラフ作成
    mid_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": gl['candle_unit'], "count": gl['candle_num']}, gl['num'])
    mid_df = f.add_peak(mid_df, pv_order)
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
    inspection_range = 24  # 一回に15行分を取得して検討する
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
            dr_oldest_n = 10
            latest_df = dr[ignore: dr_latest_n + ignore]  # 直近のn個を取得
            oldest_df = dr[dr_latest_n + ignore - 1: dr_latest_n + dr_oldest_n + ignore - 1]  # 前半と１行をラップさせる。
            latest_ans = f.renzoku_gap_pm(latest_df)  # 何連続で同じ方向に進んでいるか（直近-1まで）
            # print(latest_ans)
            oldest_ans = f.renzoku_gap_pm(oldest_df)  # 何連続で同じ方向に進んでいるか（前半部分）
            # print(oldest_ans)
            ans_42 = f.judgement_42(oldest_ans, latest_ans, dr.iloc[0]['open'])  # 引数の順番に注意！（左がOldest）⇒注文価格情報を取得

            if ans_42["ans"] == 0:
                # print("　折り返しの該当なし", dr.iloc[0]['time_jp'])
                pass
            else:
                # タイミング発生★★★！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
                # 事前判定
                # （１）酒田法
                # print(latest_ans['pattern_low'], latest_ans['pattern_high'])
                if abs(int(latest_ans['pattern'])) == 10 and oldest_ans['pattern_high_old'] > latest_ans[
                    'pattern_high'] and oldest_ans['pattern_low_old'] > latest_ans['pattern_low']:
                    # print("◆REVERSE")
                    pass
                else:
                    pass
                    # print("")

                # (2)レンジ判断
                latest_peak = latest_ans['oldest_price']  # 今の折り返しを「ピーク」として記憶
                if latest_ans['direction'] == 1:  # latestがプラス（谷）の場合、以後は底値をカウントする
                    check_col = "valley_2"
                else:
                    check_col = "peak_2"

                print("★★★★")
                print(latest_df.iloc[0]["time_jp"], latest_peak)
                # print(latest_ans['pattern_comment'])
                # print(check_col)

                between_count = 0
                range_judge(dr)

                # ★★★★検証フェーズ
                # 結果格納用
                res_dic = {
                    "entry_time": latest_df.iloc[0]["time_jp"],
                    "old_range": oldest_ans['gap'],
                    "old_count": oldest_ans['count'],
                    "old_oldest": oldest_ans['oldest_price'],
                    "old_latest": oldest_ans['latest_price'],
                    "old_high": oldest_ans['high_price'],
                    "old_low": oldest_ans['low_price'],
                    "latest_range": latest_ans['gap'],
                    "latest_count": latest_ans['count'],
                    "latest_oldest": latest_ans['oldest_price'],
                    "laetst_latest": latest_ans['latest_price'],
                    "latest_high": latest_ans['high_price'],
                    "latest_low": latest_ans['low_price'],
                    "direction_latest": latest_ans['direction'],
                    "return_ratio": ans_42['jd_info']['return_ratio'],
                    "pattern_c": latest_ans['pattern_comment'],
                    "pattern": latest_ans['pattern']
                }

                print(res_dic['latest_oldest'])

                # ■①　検証データの取得や、グラフ化や出力を先に行う
                # print(" entry(検証開始)",  dr.iloc[0]['time_jp'], d.iloc[-1]['time_jp'])
                mid_df.at[index_graph, "entry42"] = dr.iloc[0]['open']  # グラフ用データ追加
                detail_range_sec = 3000  # ★　N行×5S の検証を行う。 30分の場合360 50分の場合3000
                latest_row_time_dt = f.str_to_time(dr.iloc[0]['time'][:26])  # 時刻を変換する
                detail_from_time_dt = latest_row_time_dt + datetime.timedelta(minutes=0)  # 開始時刻は分単位で調整可
                detail_from_time_iso = str(detail_from_time_dt.isoformat()) + ".000000000Z"  # API形式の時刻へ（ISOで文字型。.0z付き）
                # ★★検証データの取得
                detail_df = oa.InstrumentsCandles_each_exe("USD_JPY",
                                                           {"granularity": 'S5', "count": int(detail_range_sec/5),
                                                            "from": detail_from_time_iso})  # ★★検証範囲の取得★★
                print(detail_df.head(3))  # 検証データ取得！
                print(detail_df.tail(3))  # 検証データ取得！
                print(" [検証時刻:", detail_df.iloc[0]['time_jp'], "終了", detail_df.iloc[-1]["time_jp"])
                res_dic['inspect_fin_time'] = detail_df.iloc[-1]["time_jp"]

                # 検証を開始
                if res_dic['direction_latest'] == 1:  # 直近が上り（谷形状の場合）
                    # 上方向に折り返し（最高値を求め、そことの距離を求める）
                    temp_high = detail_df['high'].max()
                    res_dic['backlash_range'] = temp_high - res_dic['old_latest']
                    temp_high_inner = detail_df['inner_high'].max()
                    res_dic['backlash_range_inner'] = temp_high_inner - res_dic['old_latest']
                    res_dic['peak_point'] = temp_high
                    max_df = detail_df[detail_df['high'] == detail_df['high'].max()]
                    res_dic['peak_time'] = max_df.iloc[0]['time_jp']
                else:  # 直近が下がり（山形状の場合）
                    # 下方向に折り返し（最低値を求める）
                    temp_low = detail_df['low'].min()
                    res_dic['backlash_range'] = abs(temp_low - res_dic['old_latest'])
                    temp_low_inner = detail_df['inner_low'].min()
                    res_dic['backlash_range_inner'] = abs(temp_low_inner - res_dic['old_latest'])
                    res_dic['peak_point'] = temp_low
                    max_df = detail_df[detail_df['low'] == detail_df['low'].min()]
                    res_dic['peak_time'] = max_df.iloc[0]['time_jp']

                res_dic_arr.append(res_dic)
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

    f.draw_graph(mid_df)


gl = {
    # 5分足対象
    "high_v": "high",  # "inner_high"
    "low_v": "low",  # "inner_low"５
    "p_order": 2,  # ピーク検出の幅  1分足だと４くらい？？
    "tiltgap_horizon": 0.0041,  # peak線とvalley線の差が、左記数字以下なら平行と判断。この数値以下なら平行。
    "tiltgap_pending": 0.011,  # peak線とvalley線の差が、左記数値以下なら平行以上-急なクロス以前と判断。それ以上は強いクロスとみなす
    "tilt_horizon": 0.0029,  # 単品の傾きが左記以下の場合、水平と判断。　　0.005だと少し傾き気味。。
    "tilt_pending": 0.03,  # 単品の傾きが左記以下の場合、様子見の傾きと判断。これ以上で急な傾きと判断。
    "candle_num": 5000,
    "num": 10,  # candle
    "candle_unit": "M5",
}


def graph():
    pv_order = gl['p_order']  # 極値算出の幅
    # データの取得 and peak情報付加　＋　グラフ作成
    mid_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": gl['candle_unit'], "count": gl['candle_num']}, gl['num'])
    mid_df = f.add_peak(mid_df, pv_order)
    mid_df.to_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', index=False, encoding="utf-8")
    f.draw_graph(mid_df)

oa = oanda_class.Oanda(tk.accountID, tk.access_token, "practice")
main_peak()
# graph()
