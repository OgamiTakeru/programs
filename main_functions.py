# import requests
import datetime  # 日付関係
# from scipy.signal import argrelmin, argrelmax  # add_peaks
import pandas as pd  # add_peaks
from plotly.subplots import make_subplots  # draw_graph
import plotly.graph_objects as go  # draw_graph


import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.oanda_class as oanda_class
import programs.main_functions as f  # とりあえずの関数集


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


def range_direction_inspection_pattern(data_df, direction, ans_info):
    """
    ここでのデータは、０行目が最新データ
    :param data_df:
    :param direction:
    :param ans_info:
    :return:
    """
    # パターン買いの一部
    ratio = 0.6
    back_slash = ans_info['gap'] * ratio  # トリガとなる戻り分を算出

    if len(data_df) == 2:
        # (1) latestのパターンを計算
        if direction == 1:  # プラスの連荘＝谷の場合　（折り返し部のみの話）
            if data_df.iloc[1]['body'] >= 0 and data_df.iloc[0]['body'] >= 0:
                pattern_comment = "afterV:UpUp"
                pattern = 10
                order_line = round(ans_info['latest_image_price'], 3)
                type = "LIMIT"  # 順張りか逆張りかに注意　"LIMIT"  "STOP"
            elif data_df.iloc[1]['body'] >= 0 and data_df.iloc[0]['body'] <= 0:
                pattern_comment = "afterV:UpDownss"
                pattern = 11
                order_line = round(ans_info['oldest_image_price'], 3)
                type = "LIMIT"  # 逆張り
            elif data_df.iloc[1]['body'] <= 0 and data_df.iloc[0]['body'] >= 0:
                pattern_comment = "afterV:DownUp"
                pattern = 12
                order_line = round(ans_info['latest_image_price'], 3)  # - back_slash, 3)
                type = "LIMIT"  # 逆張り
            else:
                pattern_comment = "afterV:Error"
                pattern = 13
                order_line = type = 999

        elif direction == -1:  # マイナスの連荘＝山の場合　（折り返し部の話）
            if data_df.iloc[1]['body'] <= 0 and data_df.iloc[0]['body'] <= 0:
                pattern_comment = "afterM:DownDown"
                pattern = -10
                order_line = round(ans_info['latest_image_price'], 3)
                type = "LIMIT"  # 順張り
            elif data_df.iloc[1]['body'] <= 0 and data_df.iloc[0]['body'] >= 0:
                pattern_comment = "afterM:DownUpss"
                pattern = -11
                order_line = round(ans_info['latest_image_price'], 3)
                type = "LIMIT"  # 逆張り
            elif data_df.iloc[1]['body'] >=0 and data_df.iloc[0]['body'] <=0:
                pattern_comment = "afterM:UpDown"
                pattern = -12
                order_line = round(ans_info['latest_image_price'], 3)  # + back_slash, 3)
                type = "LIMIT"  # 順張り
            else:
                pattern_comment = "afterM:Error"
                pattern = -13
                order_line = type = 999

        # （２）latestの中のoldとlatestどっちがサイズが大きいかの判別
        older = data_df.iloc[1]['body_abs']
        later = data_df.iloc[0]['body_abs']
        if older <= later:
            range_expected = 1  # レンジの予感
        else:
            range_expected = 0


    else:
        # ここは全部を網羅しておくこと（初期値的に）
        pattern = -99
        pattern_comment = "NoComment2足分以上"
        order_line = type = 999
        range_expected = 0

    # LCrangeを計算する(MAX7pips, Min 3pips)
    lc_range = round(ans_info['gap'] / 2, 3)
    if lc_range > 0.07:
        lc_range = 0.07
    elif lc_range < 0.03:
        lc_range = 0.03

    # Body長、移動長の平均値を算出する
    body_ave = data_df["body_abs"].mean()
    move_ave = data_df["moves"].mean()

    return {
        "pattern_comment": pattern_comment,
        "pattern_num": pattern,
        "order_line": round(order_line,3),
        "order_type": type,
        "back_slash": back_slash,
        "lc_range": lc_range,
        "gap": ans_info['gap'],
        'body_ave': body_ave,
        "move_abs": move_ave,
        "range_expected": range_expected
    }


def range_direction_inspection(data_df_origin):
    """
    渡された範囲で、何連続で同方向に進んでいるかを検証する
    :param data_df: 直近が上側（日付降順/リバース）のデータを利用
    :return: Dict形式のデータを返伽
    """
    # コピーウォーニングのための入れ替え
    data_df = data_df_origin.copy()

    # 処理の開始
    base_direction = 0
    counter = 0
    for i in range(len(data_df)-1):
        tilt = data_df.iloc[i]['middle_price'] - data_df.iloc[i+1]['middle_price']
        if tilt == 0:
            # tiltが０になるケースは、商不可の為仮値を代入する
            # print("  TILT0発生", data_df.iloc[i]['middle_price'], data_df.iloc[i]['time_jp'], data_df.iloc[i+1]['time_jp'])
            # print(data_df)
            tilt = 0.001
        tilt_direction = round(tilt / abs(tilt), 0)  # 方向のみ（念のためラウンドしておく）
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
    #
    # ■平均移動距離等を考える
    body_ave = round(data_df["body_abs"].mean(),3)
    move_ave = round(data_df["moves"].mean(),3)

    # ■GAPを計算する（０の時は割る時とかに困るので、最低0.001にしておく）
    gap = round(abs(latest_image_price - oldest_image_price), 3)
    if gap == 0:
        gap = 0.001
    else:
        gap = gap

    # ■　一旦格納する
    ans_dic = {
        "direction": base_direction,
        "count": counter+1,  # 最新時刻からスタートして同じ方向が何回続いているか
        "data": ans_df,  # 対象となるデータフレーム（元のデータフレームではない）
        "data_size": len(data_df),  # (注)元のデータサイズ
        "latest_image_price": latest_image_price,
        "oldest_image_price": oldest_image_price,
        "oldest_time_jp": ans_df.iloc[-1]["time_jp"],
        "latest_price": ans_df.iloc[0]["close"],
        "oldest_price": ans_df.iloc[-1]["open"],
        "gap": gap,
        "body_ave": body_ave,
        "move_abs": move_ave,
    }

    # ■　形状を判定する（テスト）
    type_info_dic = range_direction_inspection_pattern(ans_df, base_direction, ans_dic)  # 対象のデータフレームと、方向を渡す
    ans_dic["union_info_support_dic"] = type_info_dic

    return(ans_dic)


def compare_ranges(oldest_ans, latest_ans, now_price):
    """
    old区間4,latest区間2の場合のジャッジメント
    :param oldest_ans:第一引数がOldestであること。直近部より前の部分が、どれだけ同一方向に進んでいるか。
    :param latest_ans:第二引数がLatestであること。直近部がどれだけ連続で同一方向に進んでいるか
    :param now_price: 途中で追加した機能（現在の価格を取得し、成り行きに近いようなオーダーを出す）　230105追加
    :return:
    """
    if latest_ans['direction'] != oldest_ans['direction']:  # 違う方向だった場合 (想定ケース）
        if latest_ans['count'] == latest_ans['data_size'] and oldest_ans['count'] >= 4:  # 行数確認(old区間はt直接指定！）
            # 戻しのパーセンテージを確認
            return_ratio = round((latest_ans['gap'] / oldest_ans['gap']) * 100, 3)
            ans_info = {"return_ratio": return_ratio, "mid_price": now_price,
                        "oldest_ans": oldest_ans, "latest_ans": latest_ans}
            max_return_ratio = 50
            if return_ratio < max_return_ratio:
                # print("  達成")
                return {"union_ans": 1, "union_info": ans_info, "memo": "達成"}
            else:
                # print("  戻りNG")
                return {"union_ans": 0, "union_info": ans_info, "memo": "戻り大"}
        else:
            # print("  カウント未達")
            # ↓検証テスト用
            ans_info = {"return_ratio": 0, "mid_price": now_price,
                        "oldest_ans": oldest_ans, "latest_ans": latest_ans}

            return {"union_ans": 0, "union_info": ans_info, "memo": "カウント未達"}
    else:
        # print("  同方向")
        # ↓検証テスト用
        ans_info = {"return_ratio": 0, "mid_price": now_price,
                    "oldest_ans": oldest_ans, "latest_ans": latest_ans}
        return {"union_ans": 0, "union_info": ans_info, "memo": "同方向"}


def macd_judge(data_df):
    """
    データフレームをもらい、Macdを付与。
    直近からN個以内のクロスの有無、値を算出
    :return:
    """
    n = 5  # n個以内にMacdのクロスがあるかを検討する
    data_r_df = data_df.sort_index(ascending=False)  # 上が新しいデータにする
    # data_r_df.to_csv(tk.folder_path + 'macd52.csv', index=False, encoding="utf-8")  # 直近保存用
    latest_r_5 = data_r_df.head(n)  # 先頭の５列だけを取得する
    # クロスがあるかを確認する
    cross = 0  # 初期値を入れておく
    counter = 0
    for index, item in latest_r_5.iterrows():
        if item['macd_cross'] != 0:
            #Crossを発生があった場合、その方向を取得する(０以外で存在があることを確定させる）
            cross = item['macd_cross']
            cross_mae = counter
            break
        counter = counter + 1
    # 先頭のMACD値を取得する
    macd = latest_r_5.iloc[0]['macd']

    res = {
        # 0行目は確立していないはずなので、除外。latestは１を利用する（算出もおかしいかもだけど）
        "cross": cross,
        "latest_cross": latest_r_5.iloc[1]['macd_cross'],
        "latest_cross_time": latest_r_5.iloc[1]['time_jp'],
        "cross_counter": counter,
        "macd": macd,
        "data": latest_r_5
    }

    return res






