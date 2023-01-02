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
    print("tttt")
    print(mid_df)
    # 読み込み
    # mid_df = pd.read_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', sep=",", encoding="utf-8")  # test
    # mid_df = pd.read_csv('C:/Users/taker/Desktop/viewtest_data.csv', sep=",", encoding="utf-8")  # 読み込み

    # # Range判断（６個の間にクロスがあるかどうか）
    # cross_df = mid_df[mid_df['cross'] != 0]
    # cross_r_df = cross_df.sort_index(ascending=False)
    # for i in range(len(cross_r_df)):
    #     c = ans = 0
    #     r = cross_r_df[i:]
    #     # print(r['time_jp'])
    #     for index, e in r.iterrows():  # クロスのみを確認する（直近３個のクロスがレンジ判定化を確認する）
    #         if c == 0:
    #             before_cross_index = index
    #             # print(" f", e['time_jp'])
    #         else:
    #             # ６足以内でクロスが来ている場合、レンジの可能性
    #             if abs(before_cross_index - index) <= 7:
    #                 ans += 1
    #                 # print(abs(before_cross_index - index), before_cross_index, index)
    #             else:
    #                 # print(" e", e['time_jp'])
    #                 break
    #         c += 1
    #     if ans > 0:
    #         pass
    #         # print(" ★",r.iloc[0]['time_jp'])

    # # Range判定２
    # mid_df['range'] = None
    # for i in range(len(mid_df)):
    #     d = mid_df[i-30:i + 1]  # 旧側(index0）を固定。新側をインクリメントしていきたい。最大３０行
    #     # 対象の範囲を調査する (実際ではdが取得された範囲）
    #     check_flag = 0
    #     range_gap = 0.25  # アプリだと0.25くらいにしたいけど、少し広め。原因不明。
    #     if len(d) >= 10:
    #         dr = d.sort_index(ascending=False)
    #         # print(dr)
    #         # 最新行がボリバン的にレンジと判断された場合（BB上下幅による）
    #         # if dr.iloc[0]['bb_upper'] - dr.iloc[0]['bb_lower'] < range_gap:
    #         #     for index, e in dr.iterrows():  # 現在のボリバンが狭い場合、ボリバンが狭い範囲を求める
    #         #         # bb幅でクロスを確認する場合
    #         #         if e['bb_upper'] - e['bb_lower'] < range_gap:
    #         #             mid_df.loc[i, 'range'] = dr.iloc[0]['high']
    #         # 最新行がボリバン的にレンジと判断される場合（BB中央線による）
    #         bb_middle_gap = 0.1
    #         h0_gap = abs(dr.iloc[0]['inner_high'] - dr.iloc[0]['bb_middle'])
    #         l0_gap = abs(dr.iloc[0]['bb_middle'] - dr.iloc[0]['inner_low'])
    #         if h0_gap > l0_gap:
    #             far_gap = h0_gap
    #         else:
    #             far_gap = l0_gap
    #         # print(" GAP_RANGE", h0_gap, l0_gap)
    #         if far_gap < bb_middle_gap:
    #             for index, e in dr.iterrows():  # 現在のボリバンが狭い場合、ボリバンが狭い範囲を求める
    #                 # bb中央力の距離でレンジを確認する場合
    #                 upper_gap = abs(e['inner_high']-e['bb_middle'])
    #                 lower_gap = abs(e['bb_middle'] - e['inner_low'])
    #                 if upper_gap > lower_gap:
    #                     far_gap = upper_gap
    #                 else:
    #                     far_gap = lower_gap
    #                 if far_gap < bb_middle_gap:
    #                     mid_df.loc[i, 'range'] = dr.iloc[0]['high']
    #
    # mid_df.to_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', index=False, encoding="utf-8")

    # Range判定３
    # （直近１０個の足の平均値を算出、その平均値からの距離が5pips以内に収まっている足が８割以上の場合⇒レンジ。前回の結果とも比較がいい？
    # かつ、上下の幅が１０pips以内の条件も追加する？（今は無し）
    # mid_df['range_ratio'] = None
    # inspection_range = 4
    # for i in range(len(mid_df)):
    #     d = mid_df[i-inspection_range:i + 1]  # 旧側(index0）を固定。新側をインクリメントしていきたい。最大３０行
    #     # 対象の範囲を調査する (実際ではdが取得された範囲）
    #     check_flag = 0
    #     range_gap = 0.25  # アプリだと0.25くらいにしたいけど、少し広め。原因不明。
    #     if len(d) >= inspection_range:
    #         dr = d.sort_index(ascending=False)
    #         dr['ave_cal'] = (dr['inner_high'] - dr['inner_low']) + dr['inner_low']
    #         ave = dr['ave_cal'].mean()
    #         range_setting = 0.03  # 平均値の±0.5に収まっているかどうか
    #         counter = 0
    #         for index, e in dr.iterrows():  # 範囲
    #             # HighとLowどちらが離れているかを検証し、比較対象を算出
    #             high_gap = abs(e['inner_high'] - ave)
    #             low_gap = abs(e['inner_low'] - ave)
    #             if high_gap > low_gap:
    #                 target = high_gap  # 差が大きいほうが、比較対象
    #             else:
    #                 target = low_gap
    #             # レンジ判定内の場合、カウントする
    #             if target <= range_setting:
    #                 counter += 1
    #             # 結果を算出(10個（正確には１１個）中何個がレンジといえる範囲に入っているか）
    #             range_ratio = counter / len(dr)
    #         # 結果をDataFrameに入れる
    #         if range_ratio >= 0.9:
    #             print(" ★time", dr.iloc[0]['time_jp'], range_ratio)
    #             print(dr)
    #             mid_df.loc[i, 'range_ratio'] = dr.iloc[0]['high']
    #         else:
    #             print(" time", dr.iloc[0]['time_jp'], range_ratio)

    # #Range判定４
    # inspection_range = 10
    # mid_df['range_haba'] = None
    # for i in range(len(mid_df)):
    #     print(i, len(mid_df))
    #     d = mid_df[len(mid_df)-inspection_range-i : len(mid_df)-i]  # 旧側(index0）を固定。新側をインクリメントしていきたい。最大３０行
    #     print(i-inspection_range, i+1)
    #     # print(d)
    #     if len(d) >= inspection_range:
    #         # 対象の範囲を調査する (実際ではdが取得された範囲）
    #         index_graph = d.index.values[-1]
    #         dr = d.sort_index(ascending=False).copy()
    #         max_price = 0
    #         min_price = 999
    #         max_price_temp = min_price_temp = 0
    #         range_count = 0
    #         latest_time = dr.iloc[0]['time_jp']  # 逆順にしたとき、[0]だと最終行が取れてしまう。。やむおえず[-1]に。
    #         # print(dr.iloc[-1]['time_jp'])
    #         # print(dr.iloc[0]['time_jp'])
    #         for index, e in dr.iterrows():  # 範囲
    #             # まず最高値と最低値を更新する
    #             if e['inner_high'] > max_price:  # 最高値を更新する場合
    #                 max_price_temp = e['inner_high']
    #             if e['inner_low'] < min_price:  # 最低値を更新する場合
    #                 min_price_temp = e['inner_low']
    #
    #             # 更新値（最高最低）の差が0.15以内の場合、レンジとする
    #             if max_price_temp - min_price_temp <= 0.15:  # 継続する場合
    #                 # print(" レンジ継続", max_price - min_price, e['time_jp'])
    #                 max_price = max_price_temp  # 最高値を更新する
    #                 min_price = min_price_temp
    #                 range_count += 1
    #             else:  # それ以外
    #                 break
    #
    #         # 結果
    #         if range_count <= 4:  # レンジに入っているのが４個以下の場合⇒レンジとはみなさない
    #             print(" レンジに至らず", latest_time, max_price - min_price, e['time_jp'], range_count, max_price, min_price)
    #         else:
    #             print(" レンジ可能性", latest_time, max_price - min_price, e['time_jp'], range_count, max_price, min_price)
    #             # 繰り返しがあるかを判定
    #             middle_price = round(min_price + ((max_price - min_price)/2),3)
    #             ans_num = f.range_base(dr, middle_price)
    #             # print(dr, ans_num['MVcount'])
    #             # 一回でもうねり、同価格帯が続く事がレンジ条件
    #             if ans_num['MVcount'] >= 1 or ans_num['data'][0]['SameCount']>=3:
    #                 mid_df.loc[index_graph, 'range_haba'] = 1
    #                 print(" レンジ確定", ans_num['MVcount'], index_graph)
    #             else:
    #                 print(" レンジならず", ans_num['MVcount'], ans_num)


    # 折り返し未遂判定（直近を「含まない」３足が、連続上昇している、かつ、その３足目が極値となるようなVじを描いている場合
    inspection_range = 15  # 実際はそれより一つ多いDFが取得される（９の場合１０行）
    # 計算用の列を追加する
    # mid_df['middle_price'] = round(mid_df['inner_low'] + (mid_df['body_abs'] / 2), 3)
    mid_df['middle_price_gap'] = mid_df['middle_price'] - mid_df['middle_price'].shift(1)  # 時間的にひとつ前からいくら変動があったか
    mid_df.to_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', index=False, encoding="utf-8")
    mid_df['return_half'] = None
    mid_df['return_half_all'] = None
    for i in range(len(mid_df)):
        d = mid_df[len(mid_df)-inspection_range-i : len(mid_df)-i]  # 旧側(index0）を固定。新側をインクリメントしていきたい。最大３０行
        # 対象の範囲を調査する (実際ではdが取得された範囲）
        if len(d) >= inspection_range:
            index_graph = d.index.values[-1]  # インデックスを確認
            dr = d.sort_index(ascending=False)
            dr_latest_n = 3
            dr_oldest_n = 10
            latest_df = dr[1: dr_latest_n+1] # 直近の３個を取得
            oldest_df = dr[dr_latest_n: dr_latest_n + dr_oldest_n]  # 前半と１行をラップさせて、古い期間の範囲を求める
            # print(" All")
            # print(dr)
            print(dr.iloc[0]['time_jp'])
            # print(latest_df)
            # print(oldest_df)

            latest_ans = f.renzoku_gap_pm(latest_df)
            oldest_ans = f.renzoku_gap_pm(oldest_df)
            ans = f.renzoku_gap_compare(latest_ans, oldest_ans)
            ans = f.renzoku_gap_compare(oldest_ans, latest_ans)  # 引数の順番に注意！（左がOldest）
            if ans == 0:
                print("0")
            else:
                print(" 該当有", ans['forward']['direction'], ans)
                # print(" 該当あり", ans)
                mid_df.loc[index_graph, 'return_half_all'] = 1  # ★グラフ用

    ###
    ### クロスポイントの位置から、戻りを取得するプログラム
    # 前回のクロスポイントと極値の関係を確認する(クロス一回につき１回となるのかな？）
    # c = 0
    # counter = 0
    # vacant_flag = 0
    # mid_df['test_target_price'] = None  # 項目の追加
    # mid_df['test_target_price_v'] = None  # 項目の追加
    # for i in range(len(mid_df)):
    #     d = mid_df[:i]  # 旧側(index0）を固定。新側をインクリメントしていきたい。⇒模擬テスト情報
    #     print(" ")
    #     if len(d) >= 2:
    #         # 模擬テスト（ここのDは、ある一回分のデータ）　元々TOPが旧、Bottomが新のデータ。新から見て最新のCrossを見つけるところから
    #         cross_df = d[d['cross'] != 0]  # 空欄以外を抽出（フィルタ）
    #         cross_r_df = cross_df.sort_index(ascending=False)  # 逆向きのデータフレームを取得し、調査する
    #         # print(d)
    #         # クロスタイムの更新があれば
    #         if gl_cross['b_time'] != cross_r_df.iloc[0]['time_jp']:
    #             print(" Cross点更新有")
    #             gl_cross['b_price'] = cross_r_df.iloc[0]['ema_l']
    #             gl_cross['b_cross'] = cross_r_df.iloc[0]['cross']
    #             gl_cross['b_time'] = cross_r_df.iloc[0]['time_jp']
    #             if gl_cross['b_cross'] == 1:
    #                 # goldenの場合
    #                 target_price = gl_cross['b_price'] + 0.06  # この価格を二回通過したら（往復）
    #             elif gl_cross['b_cross'] == -1:
    #                 # dead
    #                 target_price = gl_cross['b_price'] - 0.06  # この価格を二回通過したら（往復）
    #             else:
    #                 # 0の場合
    #                 target_price = 0
    #                 print("nazo",gl_cross['b_price'],gl_cross['b_time'],gl_cross['b_cross'])
    #             # 共通
    #             mid_df.loc[i - 1, 'test_target_price'] = target_price  # グラフ用
    #             counter = 0  # カウンターのリセット
    #             vacant_flag = 0  # 空白（何もない期間のカウント。連続ではカウントされない）
    #             print("Target", target_price, gl_cross['b_cross'], gl_cross['b_price'], gl_cross['b_time'], counter)
    #         else:
    #             # print(" Cross更新無し")
    #             # 通過したのかを確認（本番ではリアルタイムだが、練習で足の中に入っているかどうか）
    #             print(d.iloc[-1]["time_jp"], d.iloc[-1]["low"], target_price, d.iloc[-1]["high"])
    #             if d.iloc[-1]["low"] <= target_price <= d.iloc[-1]["high"]:
    #                 if counter >= 1:
    #                     # 二回目の通貨の場合（取引開始） インクリメントのタイミング上、1の場合２回通過って感じ
    #                     if gl_cross['b_cross'] == 1:
    #                         # 前回がゴールデンの場合、上にいって帰ってきたところを取る⇒ショート方向に入れる
    #                         print(" 取引開始（ショート）", target_price, d.iloc[-1]["time_jp"])
    #                         position = 1  # 解消しないと
    #                     elif gl_cross['b_cross'] == -1:
    #                         # 前回がデッドの場合、下に行って帰ってきたところを取る⇒ロング方向に入れる
    #                         print(" 取引開始（ロング）", target_price, d.iloc[-1]["time_jp"])
    #                         position = 1  # 解消しないと。。
    #                     counter = 0  # ここでリセット？
    #                 else:
    #                     # 二かいい目以前の場合（最大１回だけど）
    #                     counter += 1
    #                     print(" 通貨", counter)
    #             else:
    #                 # 価格を含まない場合
    #                 if counter > 0:
    #                     # すでに範囲のカウントが始まってるばあい、
    #                     vacant_flag = 1  # 対象の行が、価格を含まない場合は空きフラグを立てておく。（範囲関係なく）



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

    f.draw_graph(mid_df)


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
    "candle_num": 150,
    "num": 1,
    "candle_unit": "M5",
}

oa = oanda_class.Oanda(tk.accountID, tk.access_token, "practice")
main_peak()
