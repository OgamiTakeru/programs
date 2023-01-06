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
    # 計算用の列を追加する
    # mid_df['middle_price'] = round(mid_df['inner_low'] + (mid_df['body_abs'] / 2), 3)
    mid_df['middle_price_gap'] = mid_df['middle_price'] - mid_df['middle_price'].shift(1)  # 時間的にひとつ前からいくら変動があったか
    mid_df.to_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', index=False, encoding="utf-8")
    mid_df['return_half'] = None
    mid_df['return_half_all'] = None
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
                # print("　該当有", dr.iloc[0]['time_jp'], ans['forward']['direction'], ans)
                print(" ", d.iloc[-1]['time_jp'], "↑")
                print("　検証開始")
                mid_df.loc[index_graph, 'return_half_all'] = 1  # ★グラフ用
                # ■折り返し後の検証用のデータを取得し、増減の結果を算出する
                # ■（１）検証用の後続データの取得（dの直近が「8:00:00」の５分足の場合、8:05:00以降の５秒足を取得する
                foot_minute = 5  # 元データとみなすdが何分足だったかを記録（将来的にはM5とかから５だけを抽出したい）
                detail_range = 360  # N行×5S の検証を行う。 30分の場合360
                # 折り返し調査対象の最新行の時刻(time)をdatetimeに変換する（.fromisoformatが使えずやむなく関数を用意）
                latest_row_time_dt = f.str_to_time(dr.iloc[0]['time'][:26])
                # 足分を加算して、検証開始時刻の取得（今回に限っては、プラス２足分！！（latestが自分を含まないため、調査開始は実質２足後）
                detail_from_time_dt = latest_row_time_dt + datetime.timedelta(minutes=0)  # (minutes=foot_minute)
                detail_from_time_iso = str(detail_from_time_dt.isoformat()) + ".000000000Z"  # API形式の時刻へ（ISOで文字型。.0z付き）
                # 検証範囲の取得（inspe_df)（検証開始時刻　＋　５秒×１０００）が、現時刻より前の場合（未来のデータは取得時エラーとなる為注意。）
                if detail_from_time_dt + datetime.timedelta(seconds=5 * detail_range) < now_time_from_df:
                    # 正常に取得できる場合
                    print(" 検証可能（検証データ取得可能）")
                    detail_df = oa.InstrumentsCandles_each_exe("USD_JPY",
                                                               {"granularity": 'S5', "count": detail_range,
                                                                "from": detail_from_time_iso})  # ★検証範囲の取得する
                    print(detail_df.head(5))
                else:
                    # detailが未来になってしまう場合
                    print(" 未来取得不可 検証開始時刻:", detail_from_time_dt, " 検証必要時刻",
                          detail_from_time_dt + datetime.timedelta(seconds=5 * detail_range))
                    detail_df = []
                # ■（２）以下検証開始
                if len(detail_df) >= detail_range:  # 検証可能な場合、ざっくりとした検証を実施する
                    print(" [検証時刻:", detail_df.iloc[0]['time_jp'], "終了", detail_df.iloc[-1]["time_jp"])
                    # print(latest_df)
                    # print(detail_df.head(10))
                    # 検証用の変数
                    f_flag = r_flag = position_flag = 0
                    fr_flag = 0
                    position_time = 0
                    for index, item in detail_df.iterrows():
                        if position_flag == 0: # ■ポジションを持っていない場合
                            # Position候補（順思想と逆思想）を所持
                            position_price = ans['forward']['target_price']
                            position_price_r = ans['reverse']['target_price']
                            if item['low'] < ans['forward']['target_price'] < item['high']:
                                base_info = ans['forward']  # 順方向のデータ（コード短縮化のための置き換え）
                                print(" 順方向へのポジションを取得", item['time_jp'], item['low'], item['high'])
                                f_flag = 1  # 順方向への持ちがあるフラグ
                                fr_flag = "forward &" + str(base_info['direction'])  # 順方向であることを示す履歴
                                target_price = base_info['target_price']
                                if base_info['direction'] == 1:  # 買い方向へのオーダーの場合
                                    lc_price = round(base_info['target_price'] - base_info['lc_range'], 3)  # LCは－！
                                    tp_price = round(base_info['target_price'] + base_info['tp_range'], 3)
                                elif base_info['direction'] == -1:  # 売り方向へのオーダーの場合
                                    lc_price = round(base_info['target_price'] + base_info['lc_range'], 3)  # LCはプラス！
                                    tp_price = round(base_info['target_price'] - base_info['tp_range'], 3)
                            if item['low'] < ans['reverse']['target_price'] < item['high']:
                                print(" 逆方向へのポジションを取得", item['time_jp'], item['low'], item['high'])
                                base_info = ans['reverse']  # 逆方向のデータ（コード短縮化のための置き換え）
                                r_flag = 1  # 逆方向への持ちがあるフラグ
                                fr_flag = "reverse &" + str(base_info['direction'])  # 逆方向であることを示すフラグ
                                target_price = base_info['target_price']
                                if base_info['direction'] == 1:  # 買い方向へのオーダーの場合
                                    lc_price = round(base_info['target_price'] - base_info['lc_range'], 3)  # LCは－！
                                    tp_price = round(base_info['target_price'] + base_info['tp_range'], 3)
                                elif base_info['direction'] == -1:  # 売り方向へのオーダーの場合
                                    lc_price = round(base_info['target_price'] + base_info['lc_range'], 3)  # LCはプラス！
                                    tp_price = round(base_info['target_price'] - base_info['tp_range'], 3)
                            # ポジション条件のいずれかを満たしている場合、ポジションフラグを立てて次の行へ。
                            if f_flag == 1 or r_flag == 1:
                                if f_flag == 1 and r_flag == 1:
                                    double_flag = 1  # 5秒間(5S足)の間に、逆も順も取る場合（乱高下や、狭いレンジでの発生か）
                                else:
                                    double_flag = 0  # 大抵はこっちだと思う
                                position_flag = 1  # ポジションフラグ成立
                                position_time = item['time_jp']
                                print(" Po", item['time_jp'], fr_flag, base_info['target_price'], lc_price, tp_price)
                        else:  # ■ポジションを持っている場合、利確ロスカに当たっているかを確認(各価格はポジション時に格納される）
                            # print(" Positionあり", item['low'] ,item['high'], lc_price, tp_price)
                            ans_dic ={
                                "find_time_ref": dr.iloc[0]['time_jp'],  # mainの実行時間の考え方次第。各分05秒実行の場合、５秒のずれ程度。
                                "find_price_ref": dr.iloc[0]['open'],  # 参考値。13:00:00のCloseの場合、13:04:59時点価格。となってしまう。その為、Open価格がここでは適正。
                                                                        # それにあわせ、mainのトリガーも毎分05秒に変更
                                "find_time_sub":  detail_df.iloc[0]['time_jp'],  #
                                "find_price_sub": detail_df.iloc[0]['open'],  # 確認用。気づいた時のM5のCloseと、調査開始5SのOpenの差（０が正）
                                "flag": fr_flag,
                                "time_to_posi": (f.str_to_time(position_time) - f.str_to_time(dr.iloc[0]['time_jp'])).seconds,
                                "posi_time": position_time,
                                "posi_price": position_price,
                                "posi_price_r": position_price_r,
                                "type": base_info['type'],
                                "double": double_flag,
                                "lc_price": lc_price,
                                "tp_price": tp_price,
                                "lc_pips": base_info['lc_range'],
                                "tp_range": base_info['tp_range'],
                                "res_time": item['time_jp'],
                                "res": "",
                                "hold_time": (f.str_to_time(item['time_jp']) - f.str_to_time(position_time)).seconds,
                                "latest_high": latest_ans['high_price'],
                                "latest_low": latest_ans['low_price'],
                                "oldest_high": oldest_ans['high_price'],
                                "oldest_low": oldest_ans['low_price'],
                                "res_gap": 0,
                            }
                            # ロスカにひっかかている場合
                            if item['low'] < lc_price < item['high']:
                                print(" LC")
                                ans_dic['res'] = "LC"
                                ans_dic['res_gap'] = abs(lc_price - base_info['target_price']) * -1  # base_info['lc_range'] * -1
                                TEST_ans_arr.append(ans_dic)
                                # print(TEST_ans_arr)
                                break
                            # 利確に引っかかっている場合
                            if item['low'] < tp_price < item['high']:
                                print(" TP")
                                ans_dic['res'] = "TP"
                                ans_dic['res_gap'] = abs(tp_price - base_info['target_price'])
                                TEST_ans_arr.append(ans_dic)
                                print(TEST_ans_arr)
                                break
                            # 揉んでしまって、期間内にポジションを解消できていない場合
                            if index == len(detail_df)-1:
                                print(" NoSide", index, item['time_jp'])
                                print(detail_df.head(3))
                                print(detail_df.tail(3))
                                ans_dic['res'] = "NoSide"
                                ans_dic['res_gap'] = 0
                                TEST_ans_arr.append(ans_dic)
                                # print(TEST_ans_arr)
    # 結果の表示
    print(TEST_ans_arr)
    res_df = pd.DataFrame(TEST_ans_arr)
    print(res_df)
    print("結果", res_df['res_gap'].sum(), "取引回数", len(res_df))
    res_df.to_csv(tk.folder_path + 'inspection.csv', index=False, encoding="utf-8")

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
