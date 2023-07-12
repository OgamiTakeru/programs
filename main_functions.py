# import requests
import datetime  # 日付関係
# from scipy.signal import argrelmin, argrelmax  # add_peaks
import pandas as pd  # add_peaks
from plotly.subplots import make_subplots  # draw_graph
import plotly.graph_objects as go  # draw_graph


import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.oanda_class as oanda_class


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


def cal_min(min_value, now_value):
    # 基本的にはnow_valueを返したいが、min_valueよりnow_valueが小さい場合はmin_vauleを返す
    # min_value = 2pips  now_value=3の場合は、３、min_value = 2pips  now_value=1 の場合　２を。
    if now_value >= min_value:
        ans = now_value
    else:
        ans = min_value
    # print(" CAL　MIN", ans)
    return ans


def cal_max(max_value, now_value):
    # 基本的にはnow_valueを返却したいが、max_valueよりnow_vaueが大きい場合はmax_valueを返却
    # max_value = 2pips  now_value=3の場合は2, max_value = 2pips  now_value=1 の場合　1を。
    if now_value >= max_value:
        ans = max_value
    else:
        ans = now_value
    # print(" CAL　MAX", ans)
    return ans


def figure_turn_each_inspection_support(data_df, direction, ans_info):
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


def figure_turn_each_inspection(data_df_origin):
    """
    渡された範囲で、何連続で同方向に進んでいるかを検証する
    :param data_df_origin: 直近が上側（日付降順/リバース）のデータを利用
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
    ans_other_df = data_df[counter:]  # 残りのデータ

    if base_direction == 1:
        # 上り方向の場合、直近の最大価格をlatest_image価格として取得(latest価格とは異なる可能性あり）
        latest_image_price = ans_df.iloc[0]["inner_high"]
        oldest_image_price = ans_df.iloc[-1]["inner_low"]
        latest_peak_price = ans_df.iloc[0]["high"]
        oldest_peak_price = ans_df.iloc[-1]["low"]
    else:
        # 下り方向の場合
        latest_image_price = ans_df.iloc[0]["inner_low"]
        oldest_image_price = ans_df.iloc[-1]["inner_high"]
        latest_peak_price = ans_df.iloc[0]["low"]
        oldest_peak_price = ans_df.iloc[-1]["high"]
    #
    # ■平均移動距離等を考える
    body_ave = round(data_df["body_abs"].mean(),3)
    move_ave = round(data_df["moves"].mean(),3)

    # ■GAPを計算する（０の時は割る時とかに困るので、最低0.001にしておく）
    # gap = round(abs(latest_image_price - oldest_image_price), 3)  # MAXのサイズ感
    gap_close = round(abs(latest_image_price - ans_df.iloc[-1]["close"]), 3)  # 直近の価格（クローズの価格&向き不問）
    if gap_close == 0:
        gap_close = 0.001
    else:
        gap_close = gap_close

    gap = round(abs(latest_image_price - oldest_image_price), 3)  # 直近の価格（クローズの価格&向き不問）
    if gap == 0:
        gap = 0.001
    else:
        gap = gap

    # ■　一旦格納する
    # 表示等で利用する用（機能としては使わない
    memo_time = oanda_class.str_to_time_hms(ans_df.iloc[-1]["time_jp"]) + "_" + oanda_class.str_to_time_hms(
        ans_df.iloc[0]["time_jp"])
    # 返却用
    ans_dic = {
        "direction": base_direction,
        "count": counter+1,  # 最新時刻からスタートして同じ方向が何回続いているか
        "data": ans_df,  # 対象となるデータフレーム（元のデータフレームではない）
        "data_remain": ans_other_df,  # 対象以外の残りのデータフレーム
        "data_size": len(data_df),  # (注)元のデータサイズ
        "latest_image_price": latest_image_price,
        "oldest_image_price": oldest_image_price,
        "oldest_time_jp": ans_df.iloc[-1]["time_jp"],
        "latest_time_jp": ans_df.iloc[0]["time_jp"],
        "latest_price": ans_df.iloc[0]["close"],
        "oldest_price": ans_df.iloc[-1]["open"],
        "latest_peak_price": latest_peak_price,
        "oldest_peak_price": oldest_peak_price,
        "gap": gap,
        "gap_close": gap_close,
        "body_ave": body_ave,
        "move_abs": move_ave,
        "memo_time": memo_time
    }

    # ■　形状を判定する（テスト）
    type_info_dic = figure_turn_each_inspection_support(ans_df, base_direction, ans_dic)  # 対象のデータフレームと、方向を渡す
    ans_dic["support_info"] = type_info_dic  # あくまでメイン解析の要素の一つとして渡す

    # ■　形状からターゲットラインを求める。
    return ans_dic


def figure_turn_each_inspection_skip(df_r):
    """
    渡された範囲で、何連続で同方向に進んでいるかを検証する（ただし、skipありは、２つのみの戻りはスキップして検討する）
    :param df_r: 直近が上側（日付降順/リバース）のデータを利用
    :return: Dict形式のデータを返伽
    """
    for i in range(5):  # とりあえず５回分。。本当は再帰とかがベストだと思う
        if i == 0:  # 初回は実行。一番根本となるデータを取得する
            ans_current = figure_turn_each_inspection(df_r)  # 再起用に０渡しておく。。
            next_from = ans_current['count'] - 1
        else:
            next_from = 0  # NextFromのリセット
        # 次の調査対象（ここの長さは一つの判断材料）
        ans_next_jd = figure_turn_each_inspection(df_r[next_from:])  # 再起用に０渡しておく。。
        next_from = next_from + ans_next_jd['count'] - 1
        # 次の調査対象（ここの区間の開始価格は判断材料）
        ans_next_next_jd = figure_turn_each_inspection(df_r[next_from:])  # 再起用に０渡しておく。。
        next_from = next_from + ans_next_next_jd['count'] - 1

        # 判定(次回の幅が２足分、次々回の方向が現在と同一、次々回のスタート(old)価格が現在のスタート(old)価格より高い)
        merge = 0
        # print("条件", ans_next_jd['count'], ans_next_next_jd['direction'], ans_current['direction'])
        if ans_next_jd['count'] <= 2 and ans_next_next_jd['direction'] == ans_current['direction']:
            if ans_current['direction'] == 1:  # 上向きの場合
                if ans_current['oldest_image_price'] > ans_next_next_jd['data'].iloc[-1]["inner_low"]:  # 価格が昔(調査的には次々回のスタート価格)より上昇
                    # print("SKIP対象　Up")
                    merge = 1
            else:  # 下向きの場合
                if ans_current['oldest_image_price'] < ans_next_next_jd['data'].iloc[-1]["inner_high"]:  # 価格が昔(調査的には次々回のスタート価格)より下落
                    # print("SKIP対象　Down")
                    merge = 1
        # ここからマージ処理
        if merge == 1:  # 現在(currentと次々回調査分(時系列的には過去）は結合して考える（一つ戻りが間にあるだけ）
            # データフレームの結合（一番もとになるans_currentを更新していく）,情報の更新（Oldの部分を更新していく）
            ans_current['data'] = pd.concat([ans_current['data'], ans_next_jd['data']])  # １行ラップするけど
            ans_current['data'] = pd.concat([ans_current['data'], ans_next_next_jd['data']])  # １行ラップするけど
            ans_current['count'] = len(ans_current['data']) - 2  # 2は調整。。これは大まかな数字
            ans_current['oldest_image_price'] = ans_next_next_jd['oldest_image_price']
            ans_current['oldest_time_jp'] = ans_next_next_jd['oldest_time_jp']
            ans_current['oldest_peak_price'] = ans_next_next_jd['oldest_peak_price']
            ans_current['data_remain'] = df_r[next_from:]  # 残りのデータ
            # gapの計算
            gap = round(abs(ans_current['latest_image_price'] - ans_current['oldest_image_price']), 3)
            if gap == 0:
                gap = 0.001
            else:
                gap = gap
            ans_current['gap'] = gap
            # 備忘録用のメモを作っておく
            ans_df = ans_current['data']
            memo_time = oanda_class.str_to_time_hms(ans_df.iloc[-1]["time_jp"]) + "_" + oanda_class.str_to_time_hms(
                        ans_df.iloc[0]["time_jp"])
            ans_current['memo_time'] = memo_time
            # 次のループに向け、dr_fを更新
            df_r = df_r[next_from :]  # 残りのデータ
            # print("次回調査対象",df_r.head(5))
        else:
            # print(" 終了")
            break

    return ans_current


def figure_turn_inspection(figure_condition):
    """
    old区間4,latest区間2の場合のジャッジメント
    :param oldest_ans:第一引数がOldestであること。直近部より前の部分が、どれだけ同一方向に進んでいるか。
    :param latest_ans:第二引数がLatestであること。直近部がどれだけ連続で同一方向に進んでいるか
    :param now_price: 途中で追加した機能（現在の価格を取得し、成り行きに近いようなオーダーを出す）　230105追加
    :param figure_condition
    :return:
    """
    #
    # ■直近データの形状の解析
    data_r = figure_condition['data_r']  # データを格納
    ignore = figure_condition['ignore']  # ignore=1の場合、タイミング次第では自分を入れずに探索する（正）
    dr_latest_n = figure_condition['latest_n']  # 2
    dr_oldest_n = figure_condition['oldest_n']  # 10 ⇒30
    max_return_ratio = figure_condition['return_ratio']
    # now_price = figure_condition['now_price']

    # 各DFを解析
    latest_df = data_r[ignore: dr_latest_n + ignore]  # 直近のn個を取得
    oldest_df = data_r[dr_latest_n + ignore - 1: dr_latest_n + dr_oldest_n + ignore - 1]  # 前半と１行をラップさせる。
    latest_ans = figure_turn_each_inspection(latest_df)  # 何連続で同じ方向に進んでいるか（直近-1まで）# Latestの期間を検証する(主に個のみ）
    oldest_ans_normal = figure_turn_each_inspection(oldest_df)  # 何連続で同じ方向に進んでいるか（前半部分）# Oldestの期間を検証する（MAIN）
    oldest_ans = figure_turn_each_inspection_skip(oldest_df)  # 何連続で同じ方向に進んでいるか（前半部分）# Oldestの期間を検証する（MAIN）

    # 表示用がメインの情報まとめ
    # print("  ", oldest_ans['oldest_time_jp'], latest_ans['latest_time_jp'], oldest_ans['oldest_price'],"@fig_ins")
    # print("  ", oldest_ans_normal['oldest_time_jp'], latest_ans['latest_time_jp'], oldest_ans_normal['oldest_price'], "@fig_ins")
    memo_time = oanda_class.str_to_time_hms(oldest_ans['oldest_time_jp']) + "_" + \
                oanda_class.str_to_time_hms(oldest_ans['latest_time_jp']) + "_" + \
                oanda_class.str_to_time_hms(latest_ans['latest_time_jp'])
    memo_price = "(" + str(oldest_ans['oldest_price']) + "_" + str(oldest_ans['latest_image_price']) + \
                 "_" + str(latest_ans['latest_price']) + "," + str(oldest_ans['direction'])
    # memo_time = memo_time + oanda_class.str_to_time_hms(oldest_ans_normal['oldest_time_jp']) + "_" + \
    #             oanda_class.str_to_time_hms(latest_ans['latest_time_jp'])
    memo_all = memo_time + memo_price
    tc = (datetime.datetime.now().replace(microsecond=0) - oanda_class.str_to_time(latest_ans['latest_time_jp'])).seconds
    if tc > 420:  # 何故か直近の時間がおかしい時がる
        print("★★直近データがおかしい")

    # 初期値があった方がいいもの（エラー対策）
    return_ratio = 0
    # 判定処理
    if latest_ans['direction'] != oldest_ans['direction']:  # 違う方向だった場合 (想定ケース）
        if latest_ans['count'] == latest_ans['data_size'] and oldest_ans['count'] >= 4:  # 行数確認(old区間はt直接指定！）
            # 戻しのパーセンテージを確認
            return_ratio = round((latest_ans['gap_close'] / oldest_ans['gap']) * 100, 3)
            print("  return_ratio", return_ratio, latest_ans['gap_close'], oldest_ans['gap'])
            if return_ratio < max_return_ratio:
                if oldest_ans['gap'] > 0.07:
                    turn_ans = 1  # 達成
                    memo = "達成"
                else:
                    turn_ans = 0
                    memo = "Old小未達"
            else:
                turn_ans = 0  # 未達
                memo = "戻大" + str(return_ratio)
        else:
            turn_ans = 0  # 未達
            memo = "カウント未達 latest" + str(latest_ans['count']) + "," + str(oldest_ans['count'])
    else:
        turn_ans = 0  # 未達
        memo = "同方向"

    memo_info = "'\n'   @戻り率" + str(return_ratio) + ",向き(old):" + str(oldest_ans['direction']) + ",縦幅(old):" + str(oldest_ans['gap'])
    memo_info = memo_info + ",Body平均O-L:" + str(oldest_ans['body_ave']) + "," +str(latest_ans['body_ave'])
    memo_all = memo_all + memo_info + "," + memo
    print("   ", memo_all)

    # ■注文する場合の情報を記載しておく
    oa = oanda_class.Oanda(tk.accountID, tk.access_token, "practice")  # ★現在価格の取得
    now_price = oa.NowPrice_exe("USD_JPY")['data']['mid']  # ★現在価格の取得
    if turn_ans != 0:
        # ★注文（基準情報の収集）
        # ①理論上の理想値
        return_unit_yen = oldest_ans['gap']/100
        rap_margin = 0.004  # ラップ時の余裕度
        # レンジ方向(戻り　＝　逆思想）
        d2 = latest_ans['direction']  # 方向（Tpとmarginの方向。LCの場合は*-1が必要）
        base_price2 = now_price  # now_price or latest_ans['latest_price'] # 基準となる価格（マージン込み）
        margin2 = round(0.030, 3)   # ０の場合は成り行きを意味する
        lc_range2 = cal_min(0.02, round(latest_ans['gap'] * 0.5, 3))  # 最低でも0.02pipsを確保
        lc_range2 = cal_max(0.042, lc_range2)
        tp_range2 = lc_range2 + 0.02  # lc_range2には方向があるので注意！
        cal_target2 = base_price2 + margin2 * d2
        cal_lc_price2 = cal_target2 + (lc_range2 * d2 * -1)  # ここで計算される値
        cal_tp_price2 = cal_target2 + (tp_range2 * d2)  # ここで計算される値
        print("レンジ候補", cal_target2, cal_lc_price2, cal_tp_price2, base_price2, margin2)

        # 順方向
        d = latest_ans['direction'] * -1
        base_price = latest_ans['oldest_image_price']  # 出来るだけ上にするには、NowPriceである必要
        margin = cal_min(0.013, latest_ans['body_ave'] * 0.5)
        lc_range = 0.035
        tp_range = 0.050
        cal_target = round(base_price + margin * d, 3)
        cal_lc_price = round(cal_target + (lc_range * d * -1), 3)  # ここで計算される値
        cal_tp_price = round(cal_target + (tp_range * d), 3)  # ここで計算される値
        # BasePriceを最新価格（現在価格）か、imagepriceかを洗濯する
        if latest_ans['gap'] >= 0.06:  # latestが意外と大きい場合は
            base_price = latest_ans['latest_price']  # 直近価格を利用する
            print("↓　順思想でlatestPriceを利用する")

        print("順方向候補", cal_target, cal_lc_price, cal_tp_price, base_price, margin)
        print("temp_gap", abs(cal_target2 - cal_target))

        # レンジor順思想の互いのLCが、互いのBasePriceと干渉しないようにする
        temp_gap = abs(cal_target2 - cal_target)  # お互いのターゲットプライス + 余裕度0.01を足しておく
        if lc_range2 < temp_gap and lc_range < temp_gap:  # 両方とも満たしている場合⇒何もせず
            print("  マージン調整不要(LC引き延ばす？）", temp_gap, lc_range2, lc_range)
            # 少し大きめにLCをとってみようかなぁ ★けっこうLC幅大きくなっちゃう。。。
            lc_range2 = cal_min(lc_range2, temp_gap * 0.7)
            lc_range = cal_min(lc_range, temp_gap * 0.7)
            lc_range2 = cal_max(0.042, lc_range2)
            lc_range = cal_max(0.042, lc_range)
            pass
        else:
            if lc_range2 > temp_gap and lc_range > temp_gap:
                print(" 両方非成立（LCを短縮する", lc_range2, lc_range, temp_gap)
                min_lc = 0.046  # お互い最低、このLCを取る大きめでもいいか。。
                margin = round(min_lc /2, 3) + 0.001 + margin
                margin2 = round(min_lc / 2, 3) + 0.001 + margin2 + 0.01
                lc_range2 = min_lc
                lc_range = min_lc
                print(" ⇒", lc_range2, lc_range)
            elif lc_range2 > temp_gap:
                print("レンジLC幅収まらず⇒順のtargetをずらす", lc_range2, temp_gap, margin)
                temp = abs(cal_target - cal_lc_price2)  # オーバーしている分を取得
                adj = temp + rap_margin  # 余裕を持たせる
                margin = margin + adj
                print("  ⇒", round(margin, 3), adj)
            elif lc_range > temp_gap:  # 順思想のLCが大きく、条件を満たさない場合
                print("順方向LC幅収まらず⇒レンジのTargetをずらす", lc_range, temp_gap, margin2)
                temp = abs(cal_target2 - cal_lc_price)  # オーバーしている分を取得
                print("over", temp)
                adj = temp + rap_margin + 0.01  # なんかレンジはぎりぎりで入っていることがおおいので、プラス0.01しておく
                margin2 = margin2 + adj
                print("  ⇒", round(margin2, 3), adj)
            else:
                print("　謎状態")

        # ②オーダーを生成
        junc = {
            "name": "レンジ",
            "base_price": base_price2,
            "target_price": cal_target2,  # 基本渡した先では使わない
            "margin": margin2 * d2,  # BasePriceに足せばいい数字（方向もあっている）
            "direction": d2,
            "type": "STOP",
            "lc_range": round(lc_range2 * d2 * -1, 3),
            "tp_range": round(tp_range2 * d2, 3),
            "units": 300,
        }
        main = {  # 順思想（oldest方向同方向へのオーダー）今３００００の方
            "name": "順思想",
            "base_price": base_price,
            "target_price": cal_target,  # 基本渡した先では使わない
            "margin": margin * d,  # BasePriceに足せばいい数字（方向もあっている）
            "direction": d,
            "type": "STOP",
            "lc_range": round(lc_range * d * -1, 3),
            "tp_range": round(tp_range * d, 3),
            "units": 200,
        }
        print(" ★★テスト", round(lc_range2 * d2 * -1, 3), round(lc_range * d * -1, 3))
    else:
        main = {}
        junc = {}


    # 返却用の辞書を作成
    if return_ratio == 0:
        rr = 1
    else:
        rr = return_ratio
    ans_dic = {
        "turn_ans": turn_ans,  # 結果として、ターン認定されるかどうか
        "latest_ans": latest_ans,
        "oldest_ans": oldest_ans,
        "return_ratio": return_ratio,
        "memo": memo,
        "memo_all": memo_all,
        "1percent_range": round(latest_ans['gap']/rr, 3),
        "to_half_percent": round(50-return_ratio),
        "order_dic": {
            "main": main,
            "junc": junc,
        }
    }

    # Return
    return ans_dic


def figure_turn_judge(figure_condition):
    data_r = figure_condition['data_r']
    # 直近のデータの確認　LatestとOldestの関係性を検証する
    turn_ans = figure_turn_inspection(figure_condition)  # ★★引数順注意。ポジ用の価格情報取得（０は取得無し）
    # 初期値の設定
    result_range = 0  # 最初は０
    range_memo = "0"
    expected_direction = turn_ans['oldest_ans']['direction']  # 購入の初期値は、Oldestと同方向（順思想）
    expected_lc_range = 0  # Range判断の場合に利用するが、共通の辞書返却の為
    expected_tp_range = 0  # Range判断の場合に利用するが、共通の辞書返却の為
    range_include_ratio = 0
    # もう一つ前のデータの確認　(上記の成立があれば）
    c_o_ans = 0  # 初期化が必要な変数
    turn_ans2 = turn_ans.copy()  # めんどくさいからとりあえず入れておく。。
    turn_ans2['memo'] = "（同値）"
    # if turn_ans['turn_ans'] == 1:
    #     if turn_ans['oldest_ans']['count'] <= 8:  # ８以上の場合は完全にレンジを解消していると判断
    #         next_inspection_range = figure_condition['ignore'] + figure_condition['latest_n'] + \
    #                                 turn_ans['oldest_ans']['count'] - 2
    #         next_inspection_r_df = data_r[next_inspection_range-2:]  # 調整した挙句、ー２で丁度よさそう。Nextの調査対象
    #         figure_condition['data_r'] = next_inspection_r_df  # 調査情報に代入する
    #         turn_ans2 = figure_turn_inspection(figure_condition)  # ★★ネクスト(一つ前）# の調査
    #         if turn_ans2['turn_ans'] == 1:
    #             range_include_ratio = round(float(turn_ans['oldest_ans']['gap']) / float(turn_ans2['oldest_ans']['gap']), 1)  # 共通
    #             # if turn_ans2['oldest_ans']['gap'] > turn_ans['oldest_ans']['gap']:  # 前>今回　の関係性　⇒　前の1.2倍以内ならインクルード
    #             if turn_ans2['oldest_ans']['gap']*1.2 > turn_ans['oldest_ans']['gap']:  # 前回が、今回の1.2倍以下なら（今回が多少大きくてもレンジ）
    #                 result_range = 1
    #                 expected_direction = expected_direction * -1  # レンジに入ると予想するため、逆方向
    #                 oldest_gap = turn_ans['oldest_ans']['gap']
    #                 latest_gap = turn_ans['latest_ans']['gap']
    #                 expected_lc_range = latest_gap  # LCはlatest_gap
    #                 expected_tp_range = round(oldest_gap - latest_gap - (oldest_gap * 0.1), 3)  # 指定方法は、OldestのGapから、latest戻り分(=latestGap)と縮小分(oldestの１割)を引いた数。
    #                 range_memo = "Turn発生&包括関係の形状発生"
    #                 print(" 発生&包括！", expected_direction, expected_tp_range, expected_lc_range)
    #             else:
    #                 result_range = 0
    #                 range_memo = "Turn発生&前回turnより大きくなっている"
    #     else:
    #         result_range = 0
    #         range_memo = "Turn発生&前回turnは結構前"
    # else:
    #     result_range = 0
    #     range_memo = "現在でTurnの発生無し"
    print("  ", range_memo)



    # 結果を辞書形式にまとめる
    result_dic = {
        "result_turn": turn_ans['turn_ans'],  # ★直近ターンありか
        "result_range": result_range,  # そのターンがインクルードか
    }

    ans = {
        "result_dic": result_dic,  # ターンの有無の情報
        "latest_turn_dic": turn_ans,  # 直近のターンの情報（価格情報等）
        # "oldest_turn_dic": turn_ans2,
        # "range_dic": {  # 包括関係の情報
        #     "result_range": result_range,  # そのターンがインクルードか（後でも同じの入れるけど、念のため）
        #     "range_memo": range_memo,
        #     "range_include_ratio": range_include_ratio,
        #     "order_dic": {  # インクルード時専用のオーダー情報
        #         "base_price": turn_ans['latest_ans']['latest_price'],
        #         "direction": expected_direction,
        #         "tp_range": expected_tp_range,
        #         "lc_range": expected_lc_range,
        #         "margin": 0.0015,
        #     }
        # },
    }

    return ans


# def figure_turn3_judge(figure_condition):
#     # 3足含めて、戻した場合（インクルードは考えない）
#     data_r = figure_condition['data_r']
#     # 直近のデータの確認　LatestとOldestの関係性を検証する
#     turn_ans = figure_turn_inspection(figure_condition)  # ★★引数順注意。ポジ用の価格情報取得（０は取得無し）
#     # 初期値の設定
#     include_ans = 0  # 最初は０
#     include_memo = "0"
#     expected_direction = turn_ans['oldest_ans']['direction']  # 購入の初期値は、Oldestと同方向（順思想）
#     expected_lc_range = 0  # Range判断の場合に利用するが、共通の辞書返却の為
#     expected_tp_range = 0  # Range判断の場合に利用するが、共通の辞書返却の為
#     include_ratio = 0
#
#
#     # 現在と過去の形状で包括関係の情報
#     include_result = {
#         "total_ans": c_o_ans,
#         "total_memo": include_memo,
#         "include_ratio": include_ratio,
#     }
#
#     # 結果を辞書形式にまとめる
#     result_dic = {
#         "result_turn": turn_ans['turn_ans'],
#         "result_include": include_ans,
#     }
#
#     ans = {
#         "result_dic": result_dic,
#         "latest_turn_dic": turn_ans,
#         "oldest_turn_dic": turn_ans2,
#         "include_dic": include_result,
#         "order_dic": {
#             "base_price": turn_ans['latest_ans']['latest_price'],
#             "direction": expected_direction,
#             "tp_range": expected_tp_range,
#             "lc_range": expected_lc_range
#         }
#     }
#
#     return ans


def macd_judge(data_df):
    """
    データフレームをもらい、Macdを付与。
    データは関数内で降順（上が新しい）に変更するので、昇順降順どちらでもよい
    直近からN個以内のクロスの有無、値を算出
    :return:
    """
    n = 5  # n個以内にMacdのクロスがあるかを検討する
    data_r_df = data_df.sort_index(ascending=False)  # 上が新しいデータにする

    # ■直近N行で確認（クロスがあるかを確認する）
    latest_r_5 = data_r_df.head(n)  # 先頭の５列だけを取得する
    cross = 0  # 初期値を入れておく
    counter = 0
    cross_mae = 0
    for index, item in latest_r_5.iterrows():
        if item['macd_cross'] != 0:
            #Crossを発生があった場合、その方向を取得する(０以外で存在があることを確定させる）
            cross = item['macd_cross']
            cross_mae = counter
            break
        counter = counter + 1
    # 先頭のMACD値を取得する
    macd = latest_r_5.iloc[0]['macd']

    # ■直近15行程度で確認 (Ranegeの判定となるか？）
    latest_r_long = data_r_df.head(15)  # 先頭の５列だけを取得する
    range_counter = 0
    range_jg = 0
    counter = 0
    latest_cross_flag = 0
    latest_cross_timing = 0
    for index, item in latest_r_long.iterrows():
        if item['macd_cross'] != 0:
            #Crossを発生があった場合、回数をカウントする（Rangeの場合は頻発する）
            range_counter = range_counter + 1
            if latest_cross_flag == 0:
                # 初回の発見の場合、
                latest_cross_flag = 1
                latest_cross_timing = counter
        counter = counter + 1

    # ■レンジ判定
    if range_counter >=3:
        range_jg = 1  # ３回以上短期間でクロス発生の場合はレンジと判断

    macd_result = {
        "cross": cross,  #N個以内の最初のクロスの有無と向き（１かー１）
        "cross_mae": cross_mae,
        "latest_cross": latest_r_5.iloc[1]['macd_cross'],# 0行目は確立していないはずなので、除外。latestは１を利用する（算出もおかしいかもだけど）
        "latest_cross_time": latest_r_5.iloc[1]['time_jp'],
        "macd": macd,
        "data": data_r_df,
        "range": range_jg,
        "range_counter": range_counter,
        "near_cross_timing": latest_cross_timing
    }

    return macd_result


def figure_latest3_judge(ins_condition):
    # 最初の１行は無視する（現在の行の為）
    data_r_all = ins_condition['data_r']
    ignore = ins_condition['figure']['ignore']
    data_r = data_r_all[ignore:]  # 最初の１行は無視

    # 下らないエラー対策
    if data_r.iloc[2]['body'] == 0:
        oldest_body_temp = 0.0000001
    else:
        oldest_body_temp = data_r.iloc[2]['body']

    if data_r.iloc[1]['body'] == 0:
        middle_body_temp = 0.0000001
    else:
        middle_body_temp = data_r.iloc[1]['body']

    if data_r.iloc[0]['body'] == 0:
        latest_body_temp = 0.0000001
    else:
        latest_body_temp = data_r.iloc[0]['body']

    oldest = round(oldest_body_temp, 3)
    oldest_d = oldest_body_temp / abs(oldest_body_temp)
    middle = round(middle_body_temp, 3)
    middle_d = middle_body_temp / abs(middle_body_temp)
    latest = round(latest_body_temp, 3)
    latest_d = latest_body_temp / abs(latest_body_temp)
    older_line = 0.01
    later_line = 0.006
    if middle == 0:
        middle = 0.0000001

    # print(oldest, oldest_d, middle, middle_d, latest, latest_d)
    # 三つの方向が形式にあっているか（↑↑↓か、↓↓↑）を確認
    if (oldest_d == middle_d) and oldest_d != latest_d:
        d = 1
    else:
        d = 0

    if abs(oldest) > older_line and abs(middle) > older_line and abs(latest) < abs(middle):  # どっちも5pips以上で同方向
        p = 1
    else:
        p = 0

    if 0.4 <= oldest / middle <= 2.5:
        r = 1
    else:
        r = 0

    # 方向によるマージン等の修正に利用する
    if oldest_d == 1:  # old部分が上昇方向の場合
        margin = 1
    else:
        margin = -1

    if d == 1 and p == 1 and r == 1:
        # print("   完全 dpr⇒", d, p, r)
        res_memo = "Trun未遂達成"
        latest3_figure = 1
        order = {
            "base_price": data_r.iloc[0]['open'],
            "direction": oldest_d,
            "margin": 0.008 * oldest_d,  # 方向をもつ
            "units": 200
        }
    else:
        res_memo = "Trun未遂未達"
        latest3_figure = 0
        order = {
            "base_price": 0,
            "direction": 0,
            "margin": 0.008 * oldest_d,
            "units": 200
        }
        # print("   未達成 dpr⇒", d, p, r)
    memo0 = "Oldest" + str(data_r.iloc[2]['time_jp']) + "," + str(data_r.iloc[0]['time_jp'])
    memo1 = " ,Dir:" + str(oldest_d) + str(middle_d) + str(latest_d)
    memo2 = " ,Body:" + str(oldest) + str(middle) + str(latest)
    memo3 = " ,body率" + str(round(oldest / middle, 1))
    memo4 = ", TargetPrice:" + str(order['base_price'])
    memo5 = "結果dir,pip,ratio:" + str(d) + str(p) + str(r)
    memo_all = "  " + res_memo + memo4 + memo1 + memo2 + memo3 + memo4 + memo5
    print(memo_all)

    return {"result": latest3_figure, "order_dic": order, "memo": memo_all}

def range_jd(df_r):
    df_r = df_r[0:6].copy()
    max_price = df_r["inner_high"].max()
    min_price = df_r["inner_low"].min()
    # print(max_price, min_price, max_price - min_price)
    range_gap = max_price - min_price
    if range_gap<= 0.08:
        range_res = 1
    else:
        range_res = 0
    return range_res


def inspection_candle(ins_condition):
    """
    オーダーを発行するかどうかの判断。オーダーを発行する場合、オーダーの情報も返却する
    figure_condition:探索条件を辞書形式（ignore:無視する直近足数,latest_n:直近とみなす足数)
    """
    #条件（引数）の取得
    data_r = ins_condition['data_r']

    # ■直近ターンの形状（２戻し）の解析
    figure_turn_ans = figure_turn_judge(ins_condition['figure'])

    # ■直近ターンの形状（２戻し）スキップ無し　のかいせき
    # figure_turn_ans = figure_turn_judge(ins_condition['figure'])

    # ■直近ターン形状（３戻し）の解析
    # figure_turn3_ans = figure_turn3_judge(ins_condition['figure3'])

    # ■直近データの形状の確認（5pip以上の同方向が二つの後に、5pips以内の戻りがあった場合、順張りする）
    figure_latest3_ans = figure_latest3_judge(ins_condition)

    # ■MACDについての解析
    latest_macd_r_df = data_r[0: 30]  # 中間に重複のないデータフレーム
    latest_macd_df = oanda_class.add_macd(latest_macd_r_df)  # macdを追加（データは時間昇順！！！）
    macd_result = macd_judge(latest_macd_df)

    # ■直近N個の幅調査する（レンジかの判断）
    range_ans = range_jd(data_r)

    # ■■■■上記内容から、Positionの取得可否を判断する■■■■
    print("　　Fig:", figure_turn_ans['result_dic']['result_turn'], "(", figure_turn_ans['result_dic']['result_range'], ") Macd:"
          , macd_result['cross'], "(", macd_result['cross_mae'], ",Range:",macd_result['range'], ",Nturn:", figure_latest3_ans['result'])
    if figure_turn_ans['result_dic']['result_turn'] == 1 or figure_latest3_ans['result'] == 1:  # 条件を満たす(購入許可タイミング）
        ans = 1
        print(macd_result['data'].head(5))
        # 保存が必要な場合は、保存を実施する
        if ins_condition['save']:
            figure_turn_ans['latest_turn_dic']['latest_ans']["data"].to_csv(tk.folder_path + str(ins_condition['time_str']) + 'latest.csv', index=False, encoding="utf-8")
            figure_turn_ans['latest_turn_dic']['oldest_ans']["data"].to_csv(tk.folder_path + str(ins_condition['time_str']) + 'oldest.csv', index=False, encoding="utf-8")
            macd_result["data"].to_csv(tk.folder_path + str(ins_condition['time_str']) + 'macd.csv', index=False, encoding="utf-8")

    elif macd_result['cross'] != 0:  # クロスがある場合、表示だけはしておく
        ans = 0
        print(" クロスのみの発生")
        print(macd_result['data'].head(5))
    else:
        ans = 0

    # print(figure_ans)
    return {"judgment": ans,
            "figure_turn_result": figure_turn_ans,
            "macd_result": macd_result,
            "latest3_figure_result": figure_latest3_ans,
            "range": range_ans
            }




