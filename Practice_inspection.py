from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
from scipy.signal import argrelmin, argrelmax
from numpy import linalg as LA
import numpy as np
import datetime

import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.oanda_class as oanda_class
import programs.main_functions as f  # とりあえずの関数集




def main_peak():
    pv_order = gl['p_order']  # 極値算出の幅
    # データの取得 and peak情報付加　＋　グラフ作成
    mid_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": gl['candle_unit'], "count": gl['candle_num']}, gl['num'])
    mid_df = f.add_peak(mid_df, pv_order)
    mid_df.to_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', index=False, encoding="utf-8")
    # print("tttt")
    # print(mid_df)
    # 読み込み
    # mid_df = pd.read_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', sep=",", encoding="utf-8")  # test
    # mid_df = pd.read_csv('C:/Users/taker/Desktop/viewtest_data.csv', sep=",", encoding="utf-8")  # 読み込み


    # 折り返し未遂判定（直近を「含まない」３足が、連続上昇している、かつ、その３足目が極値となるようなVじを描いている場合
    # mid_df['middle_price'] = round(mid_df['inner_low'] + (mid_df['body_abs'] / 2), 3)
    mid_df['middle_price_gap'] = mid_df['middle_price'] - mid_df['middle_price'].shift(1)  # 時間的にひとつ前からいくら変動があったか
    mid_df.to_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', index=False, encoding="utf-8")
    mid_df['entry'] = None
    res_dic_arr = []
    inspection_range = 15  #
    now_time_from_df = f.str_to_time(mid_df.iloc[-1]['time'][:26])  # 【検証時】今何時（英国時間）のデータが最新かを所持しておく
    TEST_ans_arr = []  # 【検証時】
    for i in range(len(mid_df)):
        d = mid_df[len(mid_df)-inspection_range-i: len(mid_df)-i]  # 旧側(index0）を固定。新側をインクリメントしていきたい。最大３０行
        # 対象の範囲を調査する (実際ではdが取得された範囲）
        if len(d) >= inspection_range:
            index_graph = d.index.values[-1]  # インデックスを確認
            dr = d.sort_index(ascending=False)  # ★dが毎回の取得と同義⇒それを逆にする（逆を意味するrをつける）

            dr_latest_n = 3  # 直近、何連続で同一方向への変化か（InnerHighとInnerLowの中央値の推移で検証）
            dr_oldest_n = 10  # その前に何連続で同方向への変化があるかの最大値。この中で最長何連続で同方向に行くかが大事。
            latest_df = dr[1: dr_latest_n+1] # 直近の３個を取得
            oldest_df = dr[dr_latest_n: dr_latest_n + dr_oldest_n]  # 前半と１行をラップさせて、古い期間の範囲を求める
            latest_ans = f.renzoku_gap_pm(latest_df)  # 直近何連続で同方向に行くかの結果を取得
            oldest_ans = f.renzoku_gap_pm(oldest_df)  # その後何連続で同じ方向に行くのかの結果を取得
            ans = f.renzoku_gap_compare(oldest_ans, latest_ans, dr.iloc[0]['open'])  # 引数の順番に注意！（左がOldest）⇒注文価格情報を取得
            if ans == 0:
                # print("　折り返しの該当なし", dr.iloc[0]['time_jp'])
                pass
            else:
                # タイミング発生！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
                # グラフ化や出力を先に行う
                # mid_df.iloc[i]["entry"] = 1
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
                    "return_ratio": ans['info']['return_ratio'],
                    "pattern_c": latest_ans['pattern_comment'],
                    "pattern": latest_ans['pattern']
                }
                # print("　該当有", dr.iloc[0]['time_jp'], ans['forward']['direction'], ans)
                print(" ", d.iloc[-1]['time_jp'], "↑")
                print("　検証開始")
                # ■折り返し後の検証用のデータを取得し、増減の結果を算出する
                # ■（１）検証用の後続データの取得（dの直近が「8:00:00」の５分足の場合、8:05:00以降の５秒足を取得する
                foot_minute = 5  # 元データとみなすdが何分足だったかを記録（将来的にはM5とかから５だけを抽出したい）
                detail_range_sec = 2400  # N行×5S の検証を行う。 30分の場合360
                # 折り返し調査対象の最新行の時刻(time)をdatetimeに変換する（.fromisoformatが使えずやむなく関数を用意）
                latest_row_time_dt = f.str_to_time(dr.iloc[0]['time'][:26])
                # 足分を加算して、検証開始時刻の取得（今回に限っては、プラス２足分！！（latestが自分を含まないため、調査開始は実質２足後）
                detail_from_time_dt = latest_row_time_dt + datetime.timedelta(minutes=0)  # (minutes=foot_minute)
                detail_from_time_iso = str(detail_from_time_dt.isoformat()) + ".000000000Z"  # API形式の時刻へ（ISOで文字型。.0z付き）
                print(latest_row_time_dt)
                print(detail_from_time_dt + datetime.timedelta(seconds=detail_range_sec), now_time_from_df)
                # 検証範囲の取得（inspe_df)（検証開始時刻　＋　５秒×１０００）が、現時刻より前の場合（未来のデータは取得時エラーとなる為注意。）
                if detail_from_time_dt + datetime.timedelta(seconds=detail_range_sec) < now_time_from_df:
                    # 正常に取得できる場合
                    print(" 検証可能（検証データ取得可能）")
                    detail_df = oa.InstrumentsCandles_each_exe("USD_JPY",
                                                               {"granularity": 'S5', "count": int(detail_range_sec/5),
                                                                "from": detail_from_time_iso})  # ★検証範囲の取得する
                    print(detail_df.head(3))  # 検証データ取得！
                    print(detail_df.tail(3))  # 検証データ取得！
                    print(" [検証時刻:", detail_df.iloc[0]['time_jp'], "終了", detail_df.iloc[-1]["time_jp"])
                    # print(latest_df)
                    # print(detail_df.head(10))
                    # 検証用の変数
                    f_flag = r_flag = position_flag = 0
                    fr_flag = 0
                    position_time = 0
                    # 検証データで検証開始
                    # 【保存】　ピークポイントを丁寧に抽出する
                    v_count = 99
                    v_price = 999
                    m_price = 0

                    res_dic['low'] = detail_df["low"].min()
                    res_dic['high'] = detail_df["high"].max()

                    for index, data in detail_df.iterrows():
                        if data['low'] == res_dic['low']:
                            res_dic['low_time'] = data['time_jp']
                        if data['high'] == res_dic['high']:
                            res_dic['high_time'] = data['time_jp']

                else:
                    # detailが未来になってしまう場合(最後の数行で発生)
                    print(" 未来取得不可 検証開始時刻:", detail_from_time_dt, " 検証必要時刻",
                          detail_from_time_dt + datetime.timedelta(seconds=detail_range_sec))
                    detail_df = []

                # 解析用の結果の追加
                res_dic_arr.append(res_dic)



    # 結果の表示
    # print(TEST_ans_arr)
    res_df = pd.DataFrame(TEST_ans_arr)
    print(res_df)
    # print("結果", res_df['res_gap'].sum(), "取引回数", len(res_df))
    res_df.to_csv(tk.folder_path + 'inspection.csv', index=False, encoding="utf-8")
    # 解析用結果の表示
    print(res_dic_arr)
    res_dic_df = pd.DataFrame(res_dic_arr)
    res_dic_df.to_csv(tk.folder_path + 'inspection2.csv', index=False, encoding="utf-8")


    # ★結果表示等
    #  通常より伸びた足を取得する（通常の３倍程度の足の後は、戻しが強いので、そこを取りたい）
    mid_df['big_foot'] = mid_df['body_abs'].apply(lambda x: '1' if x>=0.025 else '0')
    mid_df.to_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', index=False, encoding="utf-8")

    # 下がり時の旧戻し(2足以上）⇒また下がる　の検証
    # mid_df['conti'] = None
    # mid_df['birds'] = None
    # for i in range(len(mid_df)):
    #     d = mid_df[i-30: i+1]  # 旧側(index0）を固定。新側をインクリメントしていきたい。⇒模擬テスト情報
    #     # 対象の範囲を調査する (実際ではdが取得された範囲）
    #     check_flag = 0
    #     if len(d) >= 10:
    #         print(" ↓　調査対象")
    #         # ①直近で３羽カラスを探す（逆順の方がいい＝新しい順に探していくため）
    #         dr = d.sort_index(ascending=False)
    #         ans = f.streak_pm(dr)
    #         # print(dr)
    #         # print(ans)
    #         if 3 <= ans['count'] <= 4:  # 結果を表示する(現時刻からみて、現時点を含む
    #             mid_df.loc[i,'birds'] = dr.iloc[0]['high']
    #             print(i)
    #             check_flag = 1
    #         # ②何連続で上がっていくかを確認する（上の３羽烏以前の分が対象）
    #         if check_flag == 1:  # 折り返しの可能性（３羽烏）があった場
    #             # 上が折り返しの場合、折り返し金額を何個分で達成するかを確認する
    #             print(" ★", ans['price'])
    #             dr_first = dr[ans['count']:]  # 三羽烏以前の部分で、スロープが確認できるかを確かめる対象
    #             bodys = c = 0
    #             for index, e in dr_first.iterrows():  # bodyを累積していく
    #                 if e['inner_low'] <= ans['price'] <= e['inner_high']:
    #                     # 三羽カラスの開始の価格を超える場合
    #                     c += 1  # この行も含めるため
    #                     break
    #                 else:
    #                     c += 1
    #             dr_first[:c+1]  # body累積が折り返しを超えた地点
    #             print(dr_first[:c+1])
    #             print("★★",ans['count'], c)
    #         else:
    #             print("何もなし")

    # f.draw_graph(mid_df)


gl_cross = {
    "b_price":0,
    "b_time":datetime.datetime.now() + datetime.timedelta(minutes=-20),
    "b_cross":0,
}
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
    "num": 1,  # candle
    "candle_unit": "M5",
}

oa = oanda_class.Oanda(tk.accountID, tk.access_token, "practice")
main_peak()
