import requests
import datetime  # 日付関係
from scipy.signal import argrelmin, argrelmax  # add_peaks
import pandas as pd  # add_peaks
from plotly.subplots import make_subplots  # draw_graph
import plotly.graph_objects as go  # draw_graph
import programs.oanda_class as oa
def draw_graph(mid_df):
    """
    ローソクチャーを表示する関数。
    引数にはDataFrameをとり、最低限Open,hitg,low,Close,Time_jp,が必要。その他は任意。
    """
    order_num = 2  # 極値調査の粒度  gl['p_order']  ⇒基本は３。元プログラムと同じ必要がある（従来Globalで統一＝引数で渡したいけど。。）
    fig = make_subplots(specs=[[{"secondary_y": True}]])  # 二軸の宣言
    # ローソクチャートを表示する
    graph_trace = go.Candlestick(x=mid_df["time_jp"], open=mid_df["open"], high=mid_df["high"],
                                 low=mid_df["low"], close=mid_df["close"], name="OHLC")
    fig.add_trace(graph_trace)

    # PeakValley情報をグラフ化する
    col_name = 'peak_' + str(order_num)
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df['peak_' + str(order_num)], mode="markers",
                               marker={"size": 10, "color": "orange", "symbol": "circle"}, name="peak")
        fig.add_trace(add_graph)
    col_name = 'valley_' + str(order_num)
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df['valley_' + str(order_num)], mode="markers",
                               marker={"size": 10, "color": "skyblue", "symbol": "circle"}, name="valley")
        fig.add_trace(add_graph)
    # 移動平均線を表示する
    col_name = "ema_l"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], name=col_name, line={"color": "silver"})
        fig.add_trace(add_graph)
    col_name = "ema_s"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], name=col_name, line={"color": "darkgray"})
        fig.add_trace(add_graph)
    col_name = "cross_price"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name],  mode="markers",
                               marker={"size": 5, "color": "blue", "symbol": "cross"}, name=col_name)
        fig.add_trace(add_graph)
    # ボリンジャーバンドを追加する
    col_name = "bb_upper"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], name=col_name, line={"color": "wheat"})
        fig.add_trace(add_graph)
    col_name = "bb_lower"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], name=col_name, line={"color": "wheat"})
        fig.add_trace(add_graph)
    col_name = "bb_middle"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], name=col_name, line={"color": "khaki"})
        fig.add_trace(add_graph)

    # ↑ここまでは基本的に必須。↓以下は基本的には任意
    # 調査関連を表示する
    if 'range_start_peak' in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df['range_start_peak'], mode="markers",
                               marker={"size": 8, "color": "green", "symbol": "square"}, name="range_start_peak")
        fig.add_trace(add_graph, secondary_y=True)
    if 'range_end_peak' in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df['range_end_peak'], mode="markers",
                               marker={"size": 6, "color": "aqua", "symbol": "square"}, name="range_end_peak")
        fig.add_trace(add_graph, secondary_y=True)

    col_name = "range_start_valley"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], mode="markers",
                               marker={"size": 8, "color": "green", "symbol": "square"}, name=col_name)
        fig.add_trace(add_graph, secondary_y=True)

    col_name = "range_end_valley"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], mode="markers",
                               marker={"size": 6, "color": "aqua", "symbol": "square"}, name=col_name)
        fig.add_trace(add_graph, secondary_y=True)

    col_name = "birds"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], mode="markers",
                               marker={"size": 10, "color": "yellow", "symbol": "cross"}, name=col_name)
        fig.add_trace(add_graph)

    col_name = "hige_no"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], mode="markers",
                               marker={"size": 8, "color": "red", "symbol": "triangle-up"}, name=col_name)
        fig.add_trace(add_graph, secondary_y=True)

    col_name = "test_target_price"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], mode="markers",
                               marker={"size": 8, "color": "red", "symbol": "diamond"}, name=col_name)
        fig.add_trace(add_graph)

    col_name = "conti"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], mode="markers",
                               marker={"size": 8, "color": "red", "symbol": "diamond"}, name=col_name)
        fig.add_trace(add_graph)

    # col_name = "range"
    # if col_name in mid_df:
    #     add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], mode="markers",
    #                            marker={"size": 10, "color": "Magenta", "symbol": "diamond"}, name=col_name)
    #     fig.add_trace(add_graph)

    col_name = "range_ratio"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], mode="markers",
                               marker={"size": 10, "color": "Magenta", "symbol": "diamond"}, name=col_name)
        fig.add_trace(add_graph, secondary_y=True)

    col_name = "entry42"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], mode="markers",
                               marker={"size": 10, "color": "black", "symbol": "diamond"}, name=col_name)
        fig.add_trace(add_graph)

    col_name = "entry43"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], mode="markers",
                               marker={"size": 10, "color": "black", "symbol": "square"}, name=col_name)
        fig.add_trace(add_graph)

    col_name = "f_lc"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], mode="markers",
                               marker={"size": 10, "color": "red", "symbol": "triangle-up"}, name=col_name)
        fig.add_trace(add_graph)

    col_name = "f_tp"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], mode="markers",
                               marker={"size": 10, "color": "blue", "symbol": "triangle-up"}, name=col_name)
        fig.add_trace(add_graph)

    fig.show()
    # 参考＜マーカーの種類＞
    # symbols = ('circle', 'circle-open', 'circle-dot', 'circle-open-dot','square', 'diamond', 'cross', 'triangle-up')


def str_to_time(str_time):
    """
    時刻（文字列）をDateTimeに変換する。
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


# def renzoku_gap_pm(data_df):
#     """
#     引数のデータフレームを先頭(０行目)から確認し、何行連続で同じ方向に進んでいるかを確認。（ローソク方向のみではないく以下の方法）
#     基本的にはこのデータフレームは、先頭が最新のデータとなる「リバースデータ」であること。
#     確認方法は、各行（各足）の中央値（inner_highとinner_lowとの中央値。highとlowの中央値ではない）が、
#     連続して下がっているか（or上がっているか）を確認。
#     返り値は
#     ・何回連続で同じ方向に進んでいるか（足の数）
#     ・どっちの方向に進んでいるか
#     ・値段の動き　等
#     を辞書形式で返却する
#     :param data_df: 調査したい範囲のデータフレーム。230101時点では、3足分、６足分がそれぞれ呼ばれる
#     :return:
#     """
#     # 中央値（Inner高値とInner低値の）の動きを確認、何連続で同じ方向に行っているかを確認する（植木算的に、３行の場合は２個）
#     # print("  Practice　")
#     p_counter = m_counter = 0
#     oldest_price = latest_price = 0
#     counter = 0
#     flag = 0  # ＋かマイナスかのフラグ（条件分岐）
#     # カウントする
#     for ln in range(len(data_df)):
#         if ln <= len(data_df) - 2:  # 差分取得のため。－２のインデックスまで
#             # 初回の場合
#             if counter == 0:
#                 if len(data_df) - 2 == 0:  # 二行しかない場合（指定が２つのDFの場合、一回で完結する
#                     # print(data_df)
#                     # data_df.to_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', index=False, encoding="utf-8")
#                     if data_df.iloc[0]["middle_price_gap"] > 0:  # 先頭の行(時系列が新)が、次行(時系列が古）との比較。
#                         # 上り方向
#                         p_counter = 1
#                         m_counter = 0
#                         oldest_price = data_df.iloc[-1]["inner_low"]  # 上がりGapなので、開始は２行目（古）のLow = 低い
#                         latest_price = data_df.iloc[0]["inner_high"]  # 上がりGapなので、終了は1行目（新）のhigh　＝高い
#                         middle_price = round(oldest_price + (latest_price - oldest_price) / 2, 3)  # oldが低いところにいる
#                     else:
#                         p_counter = 0
#                         m_counter = 1
#                         oldest_price = data_df.iloc[-1]["inner_high"]  # 下がりGapなので、開始は２行目（古）のhigh　＝　高い
#                         latest_price = data_df.iloc[0]["inner_low"]  # 下がりGapなので、終了は1行目（新）のlow　＝低い
#                         middle_price = round(oldest_price - (oldest_price - latest_price) / 2, 3)  # oldが高いところにいる
#                 else:  # 通常（従来の6:3等、２以上の判定を使う方法の場合）
#                     # print("g", len(data_df))
#                     counter += 1
#                     if data_df.iloc[ln]["middle_price_gap"] > 0:
#                         flag = 1
#                         # print("初回＋", data_df.iloc[l]["middle_price_gap"],
#                         # data_df.iloc[l]["inner_high"], data_df.iloc[l]["time_jp"])
#                         latest_price = data_df.iloc[ln]["inner_high"]  # 最初のスタート値（上がっていくため、最高部分）
#                         p_counter += 1
#                     else:
#                         # print("初回－", data_df.iloc[l]["middle_price_gap"],
#                         # data_df.iloc[l]["inner_low"], data_df.iloc[l]["time_jp"])
#                         latest_price = data_df.iloc[ln]["inner_low"]  # 最初のスタート値（下がっていくため、最低部分）
#                         m_counter += 1
#                         flag = -1
#             # 初回以降
#             else:
#                 counter += 1
#                 if flag == 1 and data_df.iloc[ln]["middle_price_gap"] > 0:
#                     # 初回がプラスで、今回もプラスの場合
#                     p_counter += 1
#                     oldest_price = data_df.iloc[ln+1]["inner_low"] # ひとつ前の行の値になる事に注意
#                     # print(" ■連続＋", p_counter, '回目', data_df.iloc[l]["middle_price_gap"], data_df.iloc[l+1]["inner_low"], data_df.iloc[l+1]["time_jp"])
#                 elif flag == 1 and data_df.iloc[ln]["middle_price_gap"] <= 0:
#                     # 初回がプラスで、今回もマイナスの場合
#                     # print(" 連続＋途絶え", p_counter, "回目", data_df.iloc[l]["middle_price_gap"], data_df.iloc[l]["time_jp"])
#                     flag = 0  # flag取り下げ（アンサーにもなる）
#                     break
#                 elif flag == -1 and data_df.iloc[ln]["middle_price_gap"] <= 0:
#                     # 初回が－で、今回も－の場合
#                     oldest_price = data_df.iloc[ln+1]["inner_high"]  # ひとつ前の行の値になる事に注意
#                     # print(" ■連続－", m_counter, '回目', data_df.iloc[l]["middle_price_gap"], data_df.iloc[l+1]["inner_high"], data_df.iloc[l+1]["time_jp"])
#                     m_counter += 1
#                 elif flag == -1 and data_df.iloc[ln]["middle_price_gap"] > 0:
#                     # 初回が－で、今回もプラスの場合
#                     # print(" 連続－途絶え", m_counter, '回目', data_df.iloc[l]["middle_price_gap"], data_df.iloc[l]["time_jp"])
#                     flag = 0  # flag取り下げ（アンサーにもなる）
#                     break
#
#     # 答えのまとめ
#     if m_counter > p_counter:
#         ans = -1  # マイナスの連荘
#         ans_count = m_counter + 1
#         middle_price = round(oldest_price - (oldest_price - latest_price)/2, 3)  # oldが高いところにいる
#     elif p_counter >= m_counter:
#         ans = 1  # プラスの連荘
#         ans_count = p_counter + 1
#         middle_price = round(oldest_price + (latest_price - oldest_price) / 2, 3)  # oldが低いところにいる
#
#     # ３個(or２個）の場合、「折り返し直後（メインはLatestの最初2つを知りたい）」のローソクの関係性を求める
#     # ３個の場合、３パターンのいずれか。谷の場合(折り返し部が＋）、古い順に1,1,1/1,-1,1/1,1,-1
#     if len(data_df) == 2:
#         if ans == 1:  # プラスの連荘＝谷の場合　（折り返し部のみの話）
#             if data_df.iloc[1]['body'] >= 0 and data_df.iloc[0]['body'] >= 0:
#                 pattern_comment = "afterV:UpUp"
#                 pattern = 10
#                 pattern_high = data_df.iloc[0]['inner_high']
#                 pattern_low = data_df.iloc[1]['inner_low']
#             elif data_df.iloc[1]['body'] >= 0 and data_df.iloc[0]['body'] <= 0:
#                 pattern_comment = "afterV:UpDown"
#                 pattern = 11
#                 pattern_high = data_df.iloc[1]['inner_high']
#                 pattern_low = data_df.iloc[1]['inner_low']
#             elif data_df.iloc[1]['body'] <= 0 and data_df.iloc[0]['body'] >= 0:
#                 pattern_comment = "afterV:DownUp"
#                 pattern = 12
#                 pattern_high = data_df.iloc[0]['inner_high']
#                 pattern_low = data_df.iloc[0]['inner_low']
#             else:
#                 pattern_comment = "afterV:Error"
#                 pattern = 13
#                 pattern_high = 0
#                 pattern_low = 0
#         elif ans == -1:  # マイナスの連荘＝山の場合　（折り返し部の話）
#             if data_df.iloc[1]['body'] <= 0 and data_df.iloc[0]['body'] <= 0:
#                 pattern_comment = "afterM:DownDown"
#                 pattern = -10
#                 pattern_high = data_df.iloc[1]['inner_high']
#                 pattern_low = data_df.iloc[0]['inner_low']
#             elif data_df.iloc[1]['body'] <= 0 and data_df.iloc[0]['body'] >= 0:
#                 pattern_comment = "afterM:DownUp"
#                 pattern = -11
#                 pattern_high = data_df.iloc[1]['inner_high']
#                 pattern_low = data_df.iloc[1]['inner_low']
#             elif data_df.iloc[1]['body'] >=0 and data_df.iloc[0]['body'] <=0:
#                 pattern_comment = "afterM:UpDown"
#                 pattern = -12
#                 pattern_high = data_df.iloc[0]['inner_high']
#                 pattern_low = data_df.iloc[0]['inner_low']
#             else:
#                 pattern_comment = "afterM:Error"
#                 pattern = -13
#                 pattern_high = 0
#                 pattern_low = 0
#     else:
#         pattern = -99
#         pattern_comment = "NoComment"
#         pattern_high = 0
#         pattern_low = 0
#
#     # 移動の平均量を求める
#     inner_size = data_df['body_abs'].mean()
#     # print(data_df)
#     # print(data_df.head(ans_count))
#     # 範囲のみに絞ってしまう
#     data_df = data_df.head(ans_count)
#     # mid_df.to_csv(tk.save_folder + 'mid_df.csv', index=False, encoding="utf-8")
#     # print(data_df.iloc[0]["time_jp"])
#     # print(data_df.iloc[-1]["time_jp"])
#     # print(pattern_high)  # 2個の場合のみ
#     # print(pattern_low)
#     # print(data_df.iloc[-1]["inner_high"])
#     # print(data_df.iloc[-1]["inner_low"])
#     # print(data_df.iloc[0]["inner_high"])
#     # print(data_df.iloc[0]["inner_low"])
#     # print(ans_count,data_df)
#
#
#     return({
#         # "final_time": data_df.iloc[0]["time_jp"],
#         # "final_close_price": data_df.iloc[0]["close"],
#         "oldest_price": oldest_price,
#         "oldest_time": data_df.iloc[-1]["time_jp"],
#         "oldest_body": data_df.iloc[-1]["body"],
#         "oldest_body2": data_df.iloc[-2]["body"],
#         "latest_price": latest_price,
#         "latest_time": data_df.iloc[0]["time_jp"],
#         "latest_body": data_df.iloc[0]["body"],
#         "latest_body2": data_df.iloc[1]["body"],
#         "inner_high_price": data_df["inner_high"].max(),
#         "inner_low_price": data_df["inner_low"].min(),
#         "high_price": data_df["high"].max(),  # 範囲の最高価格(innerではない）（将来的にLC/利確価格になるかも）
#         "low_price": data_df["low"].min(),  # 範囲の最高価格(innerではない）（将来的にLC/利確価格になるかも）
#         "gap": round(abs(oldest_price - latest_price), 3),
#         "middle_price": middle_price,
#         "direction": ans,
#         "count": ans_count,
#         "data_size": len(data_df),
#         "pattern": pattern,  # 3この場合のみ
#         "pattern_comment": pattern_comment,  # 2個の場合のみ
#         "pattern_high": pattern_high,  # 2個の場合のみ
#         "pattern_low": pattern_low,  # 2個の場合のみ
#         "pattern_high_old": data_df.iloc[-1]["inner_high"],
#         "pattern_low_old": data_df.iloc[-1]["inner_low"],
#         "pattern_high_latest": data_df.iloc[0]["inner_high"],
#         "pattern_low_latest": data_df.iloc[0]["inner_low"],
#         "data": data_df,
#         "inner_size": inner_size,
#     })
#     print(oldest_price, "-", latest_price, ans, ans_count)


def range_direction_inspection(data_df):
    """
    渡された範囲で、何連続で同方向に進んでいるかを検証する
    :param data_df: 直近が上側（日付降順/リバース）のデータを利用
    :return: Dict形式のデータを返伽
    """
    base_direction = 0
    counter = 0
    for i in range(len(data_df)-1):
        tilt = data_df.iloc[i]['middle_price'] - data_df.iloc[i+1]['middle_price']
        if tilt == 0:
            # tiltが０になるケースは、商不可の為仮値を代入する
            print(" ■■TILT0発生", data_df.iloc[i]['middle_price'], "-", data_df.iloc[i+1]['middle_price'])
            tilt = 0.001
        tilt_direction = round(tilt / abs(tilt), 0)  # 方向のみ（念のためラウンドしておく）
        # print(" ", latest_df.iloc[i]['time_jp'], "-", latest_df.iloc[i + 1]['time_jp'])
        # print(" ", latest_df.iloc[i]['middle_price'], "-", latest_df.iloc[i + 1]['middle_price'])
        # print(tilt, tilt_direction)
        # print("")
        # ■初回の場合の設定。１行目と２行目の変化率に関する情報を取得、セットする
        if counter == 0:
            base_direction = tilt_direction
        else:
            # print(" 初回ではありません")
            pass

        # ■カウントを進めていく
        if tilt_direction == base_direction:  # 今回の検証変化率が、初回と動きの方向が同じ場合
            counter += 1
        else:
            break  # 連続が途切れた場合、ループを抜ける
    # ■対象のDFを取得し、情報を格納していく
    ans_df = data_df[0:counter+1]  # 同方向が続いてる範囲のデータを取得する
    if base_direction == 1:
        # 上り方向の場合、直近の最大価格をlatest_image価格として取得(latest価格とは異なる可能性あり）
        latest_image_price = ans_df.iloc[0]["inner_high"]
        oldest_image_price = ans_df.iloc[-1]["inner_low"]
    else:
        # 下り方向の場合
        latest_image_price = ans_df.iloc[0]["inner_low"]
        oldest_image_price = ans_df.iloc[-1]["inner_high"]

    return({
        "direction": base_direction,
        "count": counter+1,
        "data": ans_df,
        "data_size": len(ans_df),
        "latest_image_price": latest_image_price,
        "oldest_image_price": oldest_image_price,
        "oldest_time_jp": ans_df.iloc[-1]["time_jp"],
        "latest_price": ans_df.iloc[0]["close"],
        "oldest_price": ans_df.iloc[-1]["open"],
        "gap": round(abs(latest_image_price - oldest_image_price), 3),
    })


def compare_ranges(oldest_ans, latest_ans, now_price):
    """
    old区間4,latest区間2の場合のジャッジメント
    :param oldest_ans:第一引数がOldestであること。直近部より前の部分が、どれだけ同一方向に進んでいるか。
    :param latest_ans:第二引数がLatestであること。直近部がどれだけ連続で同一方向に進んでいるか
    :param now_price: 途中で追加した機能（現在の価格を取得し、成り行きに近いようなオーダーを出す）　230105追加
    :return:
    """
    if latest_ans['direction'] != oldest_ans['direction']:  # 違う方向だった場合 (想定ケース）
        if latest_ans['count'] == latest_ans['data_size'] and oldest_ans['count'] >= 3:  # 行数確認(old区間はt直接指定！）
            # 戻しのパーセンテージを確認
            return_ratio = round((latest_ans['gap'] / oldest_ans['gap']) * 100, 3)
            ans_info = {"return_ratio": return_ratio, "bunbo_gap": oldest_ans['gap'],
                        "oldest_old": oldest_ans["oldest_price"], "oldest_late": oldest_ans["latest_price"],
                        "latest_old": latest_ans["oldest_price"], "latest_late": latest_ans["latest_price"],
                        "latest_old_img": latest_ans["oldest_image_price"], "latest_late_img": latest_ans["latest_image_price"],
                        "oldest_old_img": latest_ans["oldest_image_price"], "oldest_late_img": latest_ans["latest_image_price"],
                        "direction": latest_ans["direction"],
                        "mid_price": now_price, "oldest_count": oldest_ans["count"], "latest_count": latest_ans['count']}
            max_return_ratio = 60
            if return_ratio < max_return_ratio:
                # print("  達成")
                return {"ans": 1, "ans_info": ans_info, "memo": "達成"}
            else:
                # print("  戻りNG")
                return {"ans": 0, "ans_info": ans_info, "memo": "戻り大"}
        else:
            # print("  カウント未達")
            return {"ans": 0, "ans_info": {}, "memo": "カウント未達"}
    else:
        # print("  同方向")
        return {"ans": 0, "ans_info": {}, "memo": "同方向"}


def judgement_42(oldest_ans, latest_ans, now_price):
    """
    old区間4,latest区間2の場合のジャッジメント
    :param oldest_ans:第一引数がOldestであること。直近部より前の部分が、どれだけ同一方向に進んでいるか。
    :param latest_ans:第二引数がLatestであること。直近部がどれだけ連続で同一方向に進んでいるか
    :param now_price: 途中で追加した機能（現在の価格を取得し、成り行きに近いようなオーダーを出す）　230105追加
    :return:
    """

    if latest_ans['direction'] != oldest_ans['direction']:  # 違う方向だった場合 (想定ケース）
        if latest_ans['count'] == latest_ans['data_size'] and oldest_ans['count'] >= 3:  # 行数確認(old区間はt直接指定！）
            # 戻しのパーセンテージを確認
            return_ratio = round((latest_ans['gap'] / oldest_ans['gap']) * 100, 3)
            ans_info = {"return_ratio": return_ratio, "bunbo_gap": oldest_ans['gap'],
                        "oldest_old": oldest_ans["oldest_price"], "latest_late": latest_ans["latest_price"],
                        "latest_old": latest_ans["oldest_price"], "direction": latest_ans["direction"],
                        "mid_price": now_price, "oldest_count": oldest_ans["count"], "latest_count": latest_ans['count']}

            # 戻り率次第で、色々処理を変える
            order_arr = []
            max_return_ratio = 56  # 初期値の設定（最大戻り率）
            ave_body = round(latest_ans["inner_size"], 3)
            direction_l = latest_ans['direction']  #
            if return_ratio < max_return_ratio:
                # 判定基準
                jds = abs(int(latest_ans['pattern']))
                latest_bodys = abs(latest_ans['oldest_body']) + abs(latest_ans['oldest_body2'])
                if jds == 10 and oldest_ans['pattern_high_latest'] > latest_ans['pattern_high'] and oldest_ans['pattern_low_latest'] > latest_ans['pattern_low']: # RVに行く可能性が高い場合
                    print(oldest_ans['pattern_low_latest'], oldest_ans['pattern_high_latest'], latest_ans['pattern_low'],
                          latest_ans['pattern_high'])
                    # 順方向（４２の場合rv）
                    entry_price = latest_ans["oldest_price"] if direction_l == 1 else latest_ans["oldest_price"]
                    f_order = {
                        "price": entry_price,
                        "lc_price": 0.05,
                        "lc_range": 0.029,  # ave_body,  # 0.022,  # ギリギリまで。。
                        "tp_range": 0.10,
                        # latest_ans['low_price']+0 if direction_l == 1 else latest_ans['high_price']-0
                        "ask_bid": -1 * direction_l,
                        "units": 20000,
                        "type": "STOP",
                        "tr_range": 0.06,  # ↑ここまでオーダー
                        "mind": 1,
                        "memo": "forward"
                    }
                    # 返却する
                    return {"ans": 42, "order_plan": f_order, "jd_info": ans_info, "memo": "42成立RV"}

                else:  # その他通常
                    # print("  オーダー準備")
                    fw_entry = latest_ans["oldest_price"] if direction_l == 1 else latest_ans["oldest_price"]
                    # 順方向（４２の場合）
                    entry_price = latest_ans["oldest_price"] if direction_l == 1 else latest_ans["oldest_price"]
                    lc = 0.17 if oldest_ans['gap']>0.17 else oldest_ans['gap']
                    # print("lc:", lc, oldest_ans['gap'])
                    f_order = {
                        "price": entry_price,
                        "lc_price": 0.05,
                        "lc_range": 0.029,  #lc, # 0.022,  # ギリギリまで。。
                        "tp_range": 0.10,  # latest_ans['low_price']+0 if direction_l == 1 else latest_ans['high_price']-0
                        "ask_bid": -1 * direction_l,
                        "units": 30000,
                        "type": "STOP",
                        "tr_range": 0.06,  # ↑ここまでオーダー
                        "mind": 1,
                        "memo": "forward"
                    }

                    # 返却する
                    return {"ans": 42, "order_plan": f_order, "jd_info": ans_info, "memo": "42成立"}
            else:
                # print("  戻り率大（４２）", return_ratio)
                return {"ans": 0, "order_plan": 0, "jd_info": ans_info, "memo": "戻り大"}
        else:
            # print("  行数未達（４２）")
            return {"ans": 0, "order_plan": 0, "jd_info": {}, "memo": "行数未達"}
    else:
        # print("  方向同方向４２")
        return {"ans": 0, "order_plan": 0, "jd_info": {}, "memo": "同方向"}
