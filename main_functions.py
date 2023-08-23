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
    時刻（文字列 yyyy/mm/dd hh:mm:mm）をDateTimeに変換する。
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


def cal_at_least(min_value, now_value):
    # 基本的にはnow_valueを返したいが、min_valueよりnow_valueが小さい場合はmin_vauleを返す
    # min_value = 2pips  now_value=3の場合は、３、min_value = 2pips  now_value=1 の場合　２を。
    if now_value >= min_value:
        ans = now_value
    else:
        ans = min_value
    # print(" CAL　MIN", ans)
    return ans


def cal_at_most(max_value, now_value):
    # 基本的にはnow_valueを返却したいが、max_valueよりnow_vaueが大きい場合はmax_valueを返却
    # max_value = 2pips  now_value=3の場合は2, max_value = 2pips  now_value=1 の場合　1を。
    if now_value >= max_value:
        ans = max_value
    else:
        ans = now_value
    # print(" CAL　MAX", ans)
    return ans


def cal_at_least_most(min_value, now_value, most_value):
    temp = cal_at_least(min_value, now_value)
    ans = cal_at_most(most_value, temp)
    return ans


def turn_each_support(data_df, direction, ans_info):
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


def turn_each_inspection(data_df_origin):
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
    type_info_dic = turn_each_support(ans_df, base_direction, ans_dic)  # 対象のデータフレームと、方向を渡す
    ans_dic["support_info"] = type_info_dic  # あくまでメイン解析の要素の一つとして渡す

    # ■　形状からターゲットラインを求める。
    return ans_dic


def turn_each_inspection_skip(df_r):
    """
    最低でも５０行程度渡さないとエラー発生。
    渡された範囲で、何連続で同方向に進んでいるかを検証する（ただし、skipありは、２つのみの戻りはスキップして検討する）
    :param df_r: 直近が上側（日付降順/リバース）のデータを利用
    :return: Dict形式のデータを返伽
    """
    for i in range(5):  # とりあえず５回分。。本当は再帰とかがベストだと思う
        if i == 0:  # 初回は実行。一番根本となるデータを取得する
            ans_current = turn_each_inspection(df_r)  # 再起用に０渡しておく。。
            next_from = ans_current['count'] - 1
        else:
            next_from = 0  # NextFromのリセット
        # 次の調査対象（ここの長さは一つの判断材料）
        ans_next_jd = turn_each_inspection(df_r[next_from:])  # 再起用に０渡しておく。。
        next_from = next_from + ans_next_jd['count'] - 1
        # 次の調査対象（ここの区間の開始価格は判断材料）
        ans_next_next_jd = turn_each_inspection(df_r[next_from:])  # 再起用に０渡しておく。。
        next_from = next_from + ans_next_next_jd['count'] - 1

        # 判定(次回の幅が２足分、次々回の方向が現在と同一、次々回のスタート(old)価格が現在のスタート(old)価格より高い)
        merge = 0
        # print("条件", ans_next_jd['count'], ans_next_next_jd['direction'], ans_current['direction'])
        if ans_next_jd['count'] <= 2 and ans_next_next_jd['direction'] == ans_current['direction']:
            if ans_current['direction'] == 1:  # 上向きの場合
                if ans_current['oldest_image_price'] > ans_next_next_jd['data'].iloc[-1]["inner_low"]:  # 価格が昔(調査的には次々回のスタート価格)より上昇、
                    # print("上向き")
                    # print(ans_next_next_jd)
                    # print(ans_current['oldest_image_price'], ans_next_next_jd['data'].iloc[-1]["inner_low"])
                    if ans_current['latest_image_price'] > ans_next_next_jd['data'].iloc[0]["inner_high"]:  # 直近価格を超えるような乱高下でもNG
                        # print(ans_current['latest_image_price'], ans_next_next_jd['data'].iloc[0]["inner_high"])
                        merge = 1
            else:  # 下向きの場合
                if ans_current['oldest_image_price'] < ans_next_next_jd['data'].iloc[-1]["inner_high"]:  # 価格が昔(調査的には次々回のスタート価格)より下落
                    # print("上向き")
                    # print(ans_next_next_jd)
                    # print(ans_current['oldest_image_price'], ans_next_next_jd['data'].iloc[-1]["inner_low"])
                    if ans_current['latest_image_price'] < ans_next_next_jd['data'].iloc[0]["inner_low"]:  # 直近価格を超えるような乱高下でもNG
                        # print(ans_current['latest_image_price'], ans_next_next_jd['data'].iloc[0]["inner_low"])
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


def turn_merge_inspection(figure_condition):
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
    # now_price = inspection_condition['now_price']

    # 各DFを解析
    latest_df = data_r[ignore: dr_latest_n + ignore]  # 直近のn個を取得
    oldest_df = data_r[dr_latest_n + ignore - 1: dr_latest_n + dr_oldest_n + ignore - 1]  # 前半と１行をラップさせる。
    latest_ans = turn_each_inspection(latest_df)  # 何連続で同じ方向に進んでいるか（直近-1まで）# Latestの期間を検証する(主に個のみ）
    oldest_ans_normal = turn_each_inspection(oldest_df)  # 何連続で同じ方向に進んでいるか（前半部分）# Oldestの期間を検証する（MAIN）
    oldest_ans = turn_each_inspection_skip(oldest_df)  # 何連続で同じ方向に進んでいるか（前半部分）# Oldestの期間を検証する（MAIN）

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

    # 初期値があった方がいいもの（エラー対策）
    return_ratio = 0
    # 判定処理
    if latest_ans['direction'] != oldest_ans['direction']:  # 違う方向だった場合 (想定ケース）
        if latest_ans['count'] == latest_ans['data_size'] and oldest_ans['count'] >= 3:  # 行数確認(old区間はt直接指定！）
            # 戻しのパーセンテージを確認
            return_ratio = round((latest_ans['gap_close'] / oldest_ans['gap']) * 100, 3)
            print("  return_ratio", return_ratio, latest_ans['gap_close'], oldest_ans['gap'])
            if return_ratio < max_return_ratio:
                if oldest_ans['gap'] > 0.02:
                    turn_ans = 1  # 達成
                    memo = "★達成"
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

    memo_info = " \n   @戻り率" + str(return_ratio) + ",向き(old):" + str(oldest_ans['direction']) + ",縦幅(old):" + str(oldest_ans['gap'])
    memo_info = memo_info + ",Body平均Old-Late:" + str(oldest_ans['body_ave']) + "," +str(latest_ans['body_ave'])
    memo_all = memo_all + memo_info + "," + memo
    print("   ", memo_all)

    return{
        "oldest_ans": oldest_ans,
        "latest_ans": latest_ans,
        "memo_all": memo_all,
        "return_ratio": return_ratio,
        "turn_peak": latest_ans["oldest_image_price"],  # ターンの底値（
        "turn_peak_bigin": oldest_ans['oldest_image_price'],  # ターン開始の価格
        "turn_ans": turn_ans
    }


def turn2_cal(inspection_condition):
    # 直近のデータの確認　LatestとOldestの関係性を検証する
    turn_ans_dic = turn_merge_inspection(inspection_condition)  # ★★引数順注意。ポジ用の価格情報取得（０は取得無し）
    oldest_ans = turn_ans_dic['oldest_ans']
    latest_ans = turn_ans_dic['latest_ans']
    turn_ans = turn_ans_dic['turn_ans']
    return_ratio = turn_ans_dic['return_ratio']
    memo_all = turn_ans_dic['memo_all']

    # 結果をもとに、価格を決定していく
    oa = oanda_class.Oanda(tk.accountID, tk.access_token, "practice")  # ★現在価格の取得
    now_price = oa.NowPrice_exe("USD_JPY")['data']['mid']  # ★現在価格の取得
    print("  nowPrice", now_price)

    # 注文情報を算出する
    main = {}  # 初期値を入れておく
    junc = {}  # 初期値を入れておく
    if turn_ans != 0:
        # ★注文（基準情報の収集）
        # （１）順思想の値の計算
        # ① 方向の設定
        trend_d = latest_ans['direction'] * -1
        # ②　margin候補1
        at_least_margin = 0.018  # 最低でも0.2を確保する
        margin_pattern1 = cal_at_least_most(at_least_margin, latest_ans['body_ave'] / 0.7, 0.05)  # 最低でも2.5pipsを確保する
        # margin候補2　同方向二つの場合、最低でも、最新のボディ分は戻る可能性を見る
        data = latest_ans['data']
        if data.iloc[1]['body'] >= 0 and data.iloc[0]['body'] >= 0:
            margin_pattern2 = data.iloc[1]['body_abs'] + 0.005  # 直近のBody分を取得する
            # tk.line_send("■たて 1 0 /", data.iloc[1]['body'], data.iloc[0]['body'])
        elif data.iloc[1]['body'] <= 0 and data.iloc[0]['body'] <= 0:
            margin_pattern2 = data.iloc[1]['body_abs'] + 0.005
            # tk.line_send("■した 1 0 /", data.iloc[1]['body'], data.iloc[0]['body'])
        else:
            margin_pattern2 = 0
        # marginの決定(基本はmargin_pattern2 だが、margin_pattern1[latestが２連続同方向の場合]がある場合は大きな方を取得する
        if margin_pattern2 == 0:  # 直近２つが同方向ではない場合
            margin_abs = margin_pattern1  # 基本的なmarginを利用
        else:
            if margin_pattern1 > margin_pattern2:  # 基本の方が大きい場合、基本を採択
                margin_abs = margin_pattern1
            else:
                margin_abs = margin_pattern2
        # tk.line_send(margin_abs)

        # ③ base price(システム利用値) & target price(参考値=システム不使用)の調整
        if latest_ans['gap'] >= 0.06:  # Gapが意外と大
            base_price = latest_ans['latest_price']  # ベースとなる価格を取得
        else:
            base_price = latest_ans['latest_price']  # ベースとなる価格を取得
        target_price = round(base_price + margin_abs * trend_d, 3)  # target_priceを念のために取得しておく

        # ④　LC_rangeの検討
        max_range_abs = oldest_ans['gap']  # 一番の理想はoldestのGap。ただ大きすぎる場合も。。
        middle_range_abs = 0.15  # 現実的にはこのくらい？
        min_range_abs = 0.06  # 最低でもこのくらい。
        lc_range_abs = middle_range_abs

        # ⑤ TP_rangeの検討
        tp_range_abs = 0.050

        # ⑥ 格納
        main = {  # 順思想（この以下の過程で、LCやMarginに方向を持たせる）（oldest方向同方向へのオーダー）今３００００の方
            "name": "順思想",
            "base_price": base_price,
            "target_price": target_price,  # 基本渡した先では使わない
            "margin": round(margin_abs * trend_d, 3),  # BasePriceに足せばいい数字（方向もあっている）
            "direction": trend_d,
            "type": "STOP",
            "lc_range": round(lc_range_abs * trend_d * -1, 3),
            "tp_range": round(tp_range_abs * trend_d, 3),
            "units": 400,
            "max_lc_range": max_range_abs * trend_d * -1,  # 最大LCの許容値（LCとイコールの場合もあり）
            "trigger": "ターン",
            "memo": memo_all
        }

        # （2）逆思想(range)の値の計算
        # ① 方向の設定
        range_d = latest_ans['direction']  # 方向（Tpとmarginの方向。LCの場合は*-1が必要）

        # ②marginの検討
        at_least_margin2 = 0.02
        if oldest_ans['gap'] > 0.15:
            margin2 = cal_at_least_most(at_least_margin2, oldest_ans['body_ave'] / 0.7, 0.05)
        else:
            margin2 = cal_at_least_most(at_least_margin2, oldest_ans['body_ave'] / 0.7, 0.05)

        # ③ base price(システム利用値) & target price(参考値=システム不使用)の調整
        if latest_ans['gap'] >= 0.06:  # Gapが意外と大きい場合、
            base_price2 = latest_ans['latest_price']  # 直近価格を利用する
        else:
            base_price2 = latest_ans['latest_price']
        target_price2 = round(base_price + (margin2 * trend_d), 3)  # target_priceを念のために取得しておく

        # ④　LC_rangeの検討
        cal_lc = abs(target_price2 - oldest_ans['latest_image_price'])  # ピークまで戻ったらLC
        max_range2_abs = oldest_ans['gap']  # 一番の理想はoldestのGap。ただ大きすぎる場合も。。
        middle_range2_abs = 0.06  # 現実的にはこのくらい？
        min_range2_abs = 0.06  # 最低でもこのくらい。
        lc_range2_abs = cal_lc  # middle_range_abs

        # ⑤ TP_rangeの検討
        tp_range2_abs = 0.050

        # ⑥　格納
        junc = {
            "name": "レンジ",
            "base_price": base_price2,
            "target_price": target_price2,  # 基本渡した先では使わない
            "margin": round(margin2 * range_d, 3),  # BasePriceに足せばいい数字（方向もあっている）
            "direction": range_d,
            "type": "STOP",
            "lc_range": round(lc_range2_abs * range_d * -1, 3),
            "tp_range": round(tp_range2_abs * range_d, 3),
            "units": 400,
            "max_lc_range": max_range2_abs * range_d * -1,  # round(lc_range2 * range_d * -1, 3)  # 最大LCの許容値（LCとイコールになる場合もあり）
            "trigger": "ターン",
            "memo": memo_all
        }

    # (３)返却用データの作成
    ans_dic = {
        "turn_ans": turn_ans,  # 結果として、ターン認定されるかどうか
        "latest_ans": latest_ans,  # oldest部分の情報
        "oldest_ans": oldest_ans,  # latest部分の詳細
        "return_ratio": return_ratio,
        "memo_all": memo_all,
        "to_half_percent": round(50 - return_ratio),
        "order_dic": {
            "main": main,
            "junc": junc,
        }
    }

    # Return
    return ans_dic


def turn3_cal(inspection_condition):
    # 直近のデータの確認　LatestとOldestの関係性を検証する
    data_r = inspection_condition['turn_3']['data_r']
    turn_ans_dic = turn_merge_inspection(inspection_condition['turn_3'])  # ★★引数順注意。ポジ用の価格情報取得（０は取得無し）
    oldest_ans = turn_ans_dic['oldest_ans']
    latest_ans = turn_ans_dic['latest_ans']
    turn_ans = turn_ans_dic['turn_ans']
    return_ratio = turn_ans_dic['return_ratio']
    memo_all = turn_ans_dic['memo_all']

    # 結果をもとに、価格を決定していく
    oa = oanda_class.Oanda(tk.accountID, tk.access_token, "practice")  # ★現在価格の取得
    now_price = oa.NowPrice_exe("USD_JPY")['data']['mid']  # ★現在価格の取得
    print("  nowPrice", now_price)

    # レンジを入れるには、現在価格がOldestの６割以下（残り４割が５pips程度ある状況が必要）
    peak_price = oldest_ans['latest_image_price']
    latest_return_ratio = round(peak_price / oldest_ans['gap'], 3)
    print("　　直近の戻り状況", latest_return_ratio)
    # さらにPeakPriceよりも外側にいる場合、許容しない


    if turn_ans != 0:
        # ★注文（基準情報の収集）
        # (1)理論上の理想値
        # ①レンジ方向(戻り　＝　逆思想）
        d2 = latest_ans['direction']  # 方向（Tpとmarginの方向。LCの場合は*-1が必要）
        base_price2 = now_price  # now_price or latest_ans['latest_price'] # 基準となる価格（マージン込み）
        marin2_temp = oldest_ans['body_ave'] / 0.7  # 試しにOldGapの７割にする（大体0.4程度を見込む）
        margin2 = cal_at_least(0.02, round(marin2_temp, 3))  # 最低でも2.5pipsを確保する
        lc_range2 = cal_at_least(0.02, round(latest_ans['gap'] * 0.5, 3))  # 最低でも0.02pipsを確保
        tp_range2 = lc_range2 + 0.02  # lc_range2には方向があるので注意！
        junc = {
            "name": "レンジ",
            "base_price": base_price2,
            "target_price": base_price2 + margin2,  # 基本渡した先では使わない
            "margin": margin2 * d2,  # BasePriceに足せばいい数字（方向もあっている）
            "direction": d2,
            "type": "STOP",
            "lc_range": round(lc_range2 * d2 * -1, 3),
            "tp_range": round(tp_range2 * d2, 3),
            "units": 300,
            "max_lc_range": round(lc_range2 * d2 * -1, 3)  # 最大LCの許容値（LCとイコールになる場合もあり）
        }

        # ②順方向
        d = latest_ans['direction'] * -1
        if latest_ans['gap'] >= 0.06:  # latestが意外と大きい場合は
            base_price = latest_ans['latest_price']  # 直近価格を利用する
            print(" ↓　順思想でlatestPriceを利用する")
        else:
            print(" ↓　順思想でoldestImagePriceを利用する")
            base_price = latest_ans['oldest_image_price']  # 出来るだけ上にするには、NowPriceである必要
        margin = cal_at_least(0.018, latest_ans['body_ave'] * 0.5)
        lc_range = 0.035
        tp_range = 0.050
        main = {  # 順思想（この以下の過程で、LCやMarginに方向を持たせる）（oldest方向同方向へのオーダー）今３００００の方
            "name": "順思想",
            "base_price": base_price,
            "target_price": round(base_price + margin * d, 3),  # 基本渡した先では使わない
            "margin": margin * d,  # BasePriceに足せばいい数字（方向もあっている）
            "direction": d,
            "type": "STOP",
            "lc_range": round(lc_range * d * -1, 3),
            "tp_range": round(tp_range * d, 3),
            "units": 200,
            "max_lc_range": round(lc_range * d * -1, 3)  # 最大LCの許容値（LCとイコールの場合もあり）
        }
        orders_dic = no_cross_adjust(main, junc)  # 互いのLCが、互いのTargetPriceにかからないように調整する
        main = orders_dic['o1']
        junc = orders_dic['o2']

    else:
        # turn_ans == 0 の場合を意味する
        main = {}
        junc = {}

    # 返却用の辞書を作成
    if return_ratio == 0:
        rr = 1
    else:
        rr = return_ratio

    ans_dic = {
        "turn_ans": turn_ans,  # 結果として、ターン認定されるかどうか
        "latest_ans": latest_ans,  # oldest部分の情報
        "oldest_ans": oldest_ans,  # latest部分の詳細
        "return_ratio": return_ratio,
        "memo_all": memo_all,
        "1percent_range": round(latest_ans['gap'] / rr, 3),
        "to_half_percent": round(50 - return_ratio),
        "order_dic": {
            "main": main,
            "junc": junc,
        }
    }

    # Return
    return ans_dic


def no_cross_adjust(o1, o2):
    """
    逆方向に二つのオーダーを発した場合、互いのLC範囲が干渉しないようにする（両建てが出来ず、取り消しにならないようにする）
    :param o1: 一つのオーダー
    :param o2: もう一つのオーダー情報
    :return:
    """

    # o1のオーダー情報を取得する
    base_price = o1['base_price']
    margin = abs(o1['margin'])
    lc_range = abs(o1['lc_range'])
    tp_range = abs(o1['tp_range'])
    d = o1['direction']
    cal_target = base_price + margin * d
    cal_lc_price = cal_target + (lc_range * d * -1)  # ここで計算される値
    cal_tp_price = cal_target + (tp_range * d)

    # o2のオーダー情報を取得する
    base_price2 = o2['base_price']
    margin2 = abs(o2['margin'])
    lc_range2 = abs(o2['lc_range'])
    tp_range2 = abs(o2['tp_range'])
    d2 = o2['direction']
    cal_target2 = base_price2 + margin2 * d2
    cal_lc_price2 = cal_target2 + (lc_range2 * d2 * -1)  # ここで計算される値
    cal_tp_price2 = cal_target2 + (tp_range2 * d2)  # ここで計算される値

    # 互いのTargetPrice間を求める（＝互いの最大のlc_range)
    gap_target_price = round(abs(cal_target2 - cal_target) * 0.8, 3)
    # 互いのTargetPrice間に収まらないLCの場合（LCはどちらとも大きさが異なる）
    if lc_range2 < gap_target_price and lc_range < gap_target_price:  # 両方とも満たしている場合⇒何もせず
        print("  マージン調整不要(LC引き延ばす？）", gap_target_price, lc_range2, lc_range)
        # 適切なLCを選択する（Gapより狭くなくてはいけない）
        lc_range2 = cal_at_most(0.04, gap_target_price)  # 幅が最大LCママ
        lc_range = gap_target_price
        pass
    else:
        # 互いに干渉（片一方の可能性もあるが）する場合、lcを最低確保し、Marginを均等に増やすことにより回避する。
        if lc_range2 > gap_target_price and lc_range > gap_target_price:
            print(" 両方非成立（LCを固定値に短縮。それに合わせMarinも調整）", lc_range2, lc_range, gap_target_price)
            min_lc = 0.046  # お互い最低、このLCを取る大きめでもいいか。。
            margin = round(min_lc / 2, 3) + 0.004  # 互いにmin_lcの半分をMarginに取ればいい！
            margin2 = round(min_lc / 2, 3) + 0.004
            lc_range2 = min_lc
            lc_range = min_lc
            lc_range2_max = min_lc  # 最大値としても設定しておく（今後lc_range幅を減らすかもしれない）
            lc_range_max = min_lc
            print(" ⇒", lc_range2, lc_range)
            # tk.line_send("見てみたい条件　両方非成立 lc2,lc,gap", lc_range2, lc_range, gap_target_price, lc_range2_max, lc_range_max
            #              , margin2, margin)
        elif lc_range2 > gap_target_price:
            print("レンジLC幅収まらず⇒順のtargetをずらす(LC変えずMarginを増やす）)", lc_range2, gap_target_price, margin)
            temp = abs(cal_target - cal_lc_price2)  # オーバーしている分を取得
            adj = temp  # 余裕を持たせる
            margin = margin + adj
            print("  ⇒", round(margin, 3), adj)
            # tk.line_send("見てみたい条件　レンジLCの為順をずらず lc2,lc,gap", lc_range2, lc_range, gap_target_price, margin2, margin)
        elif lc_range > gap_target_price:  # 順思想のLCが大きく、条件を満たさない場合
            print("順方向LC幅収まらず⇒レンジのTargetをずらす（LC変えずMarginを増やす）", lc_range, gap_target_price, margin2)
            # tk.line_send("見てみたい条件　順LCの為レンジをずらず lc2,lc,gap", lc_range2, lc_range, gap_target_price)
            temp = abs(cal_target2 - cal_lc_price)  # オーバーしている分を取得
            print("over", temp)
            adj = temp + 0.01  # なんかレンジはぎりぎりで入っていることがおおいので、プラス0.01しておく
            margin2 = margin2 + adj
            print("  ⇒", round(margin2, 3), adj)
            # tk.line_send("見てみたい条件　順LCの為レンジをずらず lc2,lc,gap", lc_range2, lc_range, gap_target_price, margin2, margin)
        else:
            print("　謎状態")

    o1['margin'] = round(0.026 * d, 3)
    o1['lc_range'] = round(lc_range * d * -1, 3)
    o1['max_lc_range'] = round(0.1 * d * -1, 3)
    o2['margin'] = round(margin2 * d2, 3)
    o2['lc_range'] = round(lc_range * d2 * -1, 3)
    o2['max_lc_range'] = round(0.1 * d2 * -1, 3)

    return {"o1":o1, "o2":o2}


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
    ignore = ins_condition['turn_2']['ignore']
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

    # gapサイズを求める（小さい最場合は無効にするため）
    gap = round(data_r.iloc[2]['body_abs'] + data_r.iloc[1]['body_abs'], 3)

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
        if gap <= 0.08:
            res_memo = "Trun未遂形状〇サイズ×"
            print(" Trun未遂形状　ただしGap小 gap= ", gap)
            latest3_figure = 0
            order = {
                "base_price": 0,
                "direction": 0,
                "margin": 0.008 * oldest_d,
                "units": 200,
                "lc": 0.035,
                "tp": 0.075,
                "max_lc_range": 0.05,
                "trigger": "ターン未遂",
                "memo": " "
            }
        else:
            # print("   完全 dpr⇒", d, p, r)
            res_memo = "Trun未遂達成"
            latest3_figure = 1
            order = {
                "name": "ターン未遂",
                "base_price": data_r.iloc[0]['open'],
                "target_price": 0,
                "margin": round(0.008 * oldest_d, 3),  # 方向をもつ
                "direction": oldest_d,
                "type": "STOP",
                "units": 200,
                "lc_range": round(0.035 * oldest_d * -1, 3),
                "tp_range": round(0.075 * oldest_d, 3),
                "max_lc_range": 0.05,
                "trigger": "ターン未遂",
                "memo": " "
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


def rap_jd(figure_condition):
    data_r = figure_condition['data_r']  # データを格納
    ignore = figure_condition['ignore']  # ignore=1の場合、タイミング次第では自分を入れずに探索する（正）

    # 各DFを解析
    df_r = data_r[ignore: 3 + ignore].copy()  # 直近のn個を取得
    # df_r = df_r[0:3].copy()
    df_r = df_r.reset_index()
    # print(df_r)
    count = 0
    # bodyサイズ感がそろっているかを確かめる（そろっている＝レンジの可能性）
    body_ave = df_r.iloc[0]['body_abs']

    # Bodyサイズのサイズ感の統一感
    for index, data in df_r.iterrows():
        # print(index)
        if body_ave * 0.4 <= df_r.iloc[index]['body_abs'] <= body_ave * 2.3:
            count = count + 1
        else:
            # print("out", df_r.iloc[index]['time_jp'])
            break
    if count == len(df_r):
        # print("Body OK")
        body = 1
    else:
        body = 0

    # Rapの判断
    rap_count = 0
    for index, data in df_r.iterrows():
        if index + 1 < len(df_r):
            # print("latest", df_r.iloc[index]['time_jp'], df_r.iloc[index+1]['time_jp'])
            # ラップ状態を計算する
            latest_high = df_r.iloc[index]['inner_high']
            latest_low = df_r.iloc[index]['inner_low']
            oldest_high = df_r.iloc[index+1]['inner_high']
            oldest_low = df_r.iloc[index+1]['inner_low']
            # print(latest_high,latest_low,oldest_high,oldest_low)
            if latest_high > oldest_high:
                high = latest_high
                mid_high = oldest_high
            else:
                high = oldest_high
                mid_high = latest_high

            if latest_low < oldest_low:
                low = latest_low
                mid_low = oldest_low
            else:
                low = oldest_low
                mid_low = latest_low

            rap = mid_high - mid_low
            if rap == 0:
                rap = 1
                print(" 0はおかしいけれど", mid_high, mid_low)
            else:
                rap = rap
            rap_ratio = round(body_ave / rap, 3)
            # print(rap, rap_ratio)

            if rap_ratio >= 0.8:
                # print(" RAPあり")
                rap_flag = 1
                rap_count = rap_count + 1
            else:
                # print("END RAP", df_r.iloc[index]['time_jp'])
                rap_flag = 0
                break
    # print("RAP　RAIO", rap_count, len(df_r))
    len_kai = len(df_r)- 1  # 比較は植木算的には間なので、len-1が必要
    if rap_count == len_kai:
        rap_ans = 1
    else:
        rap_ans = 0

    if body == 1 and rap_ans == 1:
        print("成立")
        # tk.line_send("もみあい")
        return 1
    else:
        # print("非成立")
        return 0


def peaks_collect(df_r):
    """
    リバースされたデータフレーム（直近が上）から、極値をN回分求める
    基本的にトップとボトムが交互になる
    :return:
    """
    peaks = []
    for i in range(20):
        # print(" 各調査")
        ans = turn_each_inspection_skip(df_r)
        df_r = df_r[ans['count']-1:]
        if ans['direction'] == 1:
            # 上向きの場合
            peak_latest = ans['data'].iloc[0]["inner_high"]
            peak_oldest = ans['data'].iloc[-1]["inner_low"]

        else:
            # 下向きの場合
            peak_latest = ans['data'].iloc[0]["inner_low"]
            peak_oldest = ans['data'].iloc[-1]["inner_high"]

        temp_all = {
            'time': ans['data'].iloc[0]['time_jp'],
            'peak': peak_latest,
            'time_oldest': ans['data'].iloc[-1]['time_jp'],
            'peak_oldest': peak_oldest,
            'direction': ans['direction'],
            'body_ave': ans['body_ave'],
            'count': len(ans["data"])
            # 'data': ans['data'],
            # 'ans': ans,
        }
        peaks.append(temp_all)  # 全部のピークのデータを取得する

    # 一番先頭[0]に格納されたピークは、現在＝自動的にピークになる物となるため、
    # print(peaks)
    # print(peaks[1:])
    # 直近のピークまでのカウント（足数）を求める
    from_last_peak = peaks[0]
    # 最新のは除外しておく（余計なことになる可能性もあるため）
    peaks = peaks[1:]
    # 上、下のピークをグルーピングする
    top_peaks = []
    bottom_peaks = []
    for i in range(len(peaks)):
        if peaks[i]['direction'] == 1:
            # TopPeakの場合
            top_peaks.append(peaks[i])  # 新規に最後尾に追加する
        else:
            # bottomPeakの場合
            bottom_peaks.append(peaks[i])

    if from_last_peak['direction'] == 1:
        latest_peak_group = bottom_peaks  # 最新を含む方向性が上向きの場合、直近のピークは谷方向となる
        second_peak_group = top_peaks
    else:
        latest_peak_group = top_peaks
        second_peak_group = bottom_peaks

    return {
        "all_peaks": peaks,
        "tops": top_peaks,
        "bottoms": bottom_peaks,
        "from_last_peak":  from_last_peak,  # 最後のPeakから何分経っているか(自身[最新]を含み、lastPeakを含まない）
        "latest_peak_group": latest_peak_group,  # 直近からみて直近のグループ
        "second_peak_group": second_peak_group
    }


# def filter_peaks(peaks, d, n):
#     """
#     引数１はTopBottom情報が混合のPeaks
#     :param d:direction　１かー１。１の場合はトップ、ー１の場合はボトムの抽出
#     :param n:直近何個分のピークを取るか
#     :return:
#     """
#     ans = []
#     max_counter = 0
#     for i in range(len(peaks)):
#         if max_counter >= n:
#             break
#
#         if peaks[i]['direction'] == d:
#             t = {  # 基礎データ
#                 'time_latest': peaks[i]['time_latest'],
#                 'time_oldest': peaks[i]['time_oldest'],
#                 'peak_latest': peaks[i]['peak_latest'],
#                 'peak_oldest': peaks[i]['peak_oldest'],
#                 'direction': peaks[i]['direction'],
#                 'data': peaks[i]['data'],
#                 'body_ave': peaks[i]['body_ave'],
#                 'count': len(peaks[i]['data']) - 1
#             }
#             # print(peaks[i]['data'])
#             if i+1 < len(peaks):
#                 if peaks[i+1]['direction'] == (d * -1):
#                     # 情報を追加する
#                     t['time_oldest'] = peaks[i+1]['time_oldest']
#                     t['peak_oldest'] = peaks[i+1]['peak_oldest']
#                     t['data'] = pd.concat([t['data'], peaks[i+1]['data']], axis=0, ignore_index=True)
#                     t['count'] = t['count'] + len(peaks[i+1]['data'])
#                     # tilt
#                     gap = t['peak_latest']-t['peak_oldest']
#                     t['gap'] = gap
#                     t['tilt'] = round(gap/t['count'], 3)
#             # 結果を格納する
#             ans.append(t)
#             max_counter = max_counter + 1
#     # 表示用
#     # print("極値表示")
#     ans  # ansは現状上が新しい、下が古いもの ⇒
#     counter = 0#
#     double_ans = {}
#     for i in range(len(ans)):
#         p = ans[i]
#         counter = counter + p['count']
#         if i + 1 < len(ans):
#             # if abs(p['peak_latest'] - ans[i+1]['peak_latest']) < p['body_ave'] * 1.2 and p['count'] < 15:
#             if abs(ans[i]['peak_latest'] - ans[i + 1]['peak_latest']) < 0.015 and p['count'] < 15:
#                 # print("ダブルトップ")
#                 # print(p['peak_latest'] - ans[i+1]['peak_latest'])
#                 # print(p['body_ave'], p['count'])
#                 if "time" in double_ans:   # 一回やったら次は入れない（直近のみを抽出）
#                     # pass
#                     break
#                 else:
#                     # 見つかった場合
#                     double_ans['time'] = p['time_latest']
#                     double_ans['peak'] = p['peak_latest']
#                     double_ans['counter_from_latest'] = counter
#                     double_ans['direction'] = p['direction']
#                     double_ans['time_past'] = (datetime.datetime.now() - str_to_time(p['time_latest'])).seconds
#                     memo = str(p['time_latest']) + "(" + str(ans[i]['peak_latest']) + ")-" \
#                            + str(ans[i + 1]['time_latest'])+ "(" + str(ans[i + 1]['peak_latest']) + ")" \
#                            + "timepast"+ str(round(double_ans['time_past']/60, 0)) + "分"
#                     # print("極値探索")
#                     # print(double_ans['time_past'])
#                     # print(memo)
#                     if double_ans['time_past'] < 1200:
#                         # tk.line_send("Peak発見用", double_ans['direction'], memo)
#                         memo = ""
#         if "time_oldest" in p:  # 最後？にはtime_oldestがない（処理されてない）事があるので。
#             # print(p)
#             pass
#             # print(p['time_latest'], p['peak_latest'], "-", p['time_oldest'], p['peak_oldest'], p['count'], p['body_ave'], )
#     return {"ans": ans, "double": double_ans}
#
#
# def search_peaks(peaks, d, n, price):
#     """
#     引数１はTopBottom情報が混合のPeaks
#     :param d:direction　１かー１。１の場合はトップ、ー１の場合はボトムの抽出
#     :param n:直近何個分のピークを取るか
#     :return:
#     """
#     ans = []
#     max_counter = 0
#     for i in range(len(peaks)):
#         if max_counter >= n:
#             break
#
#         if peaks[i]['direction'] == d:
#             t = {  # 基礎データ
#                 'time_latest': peaks[i]['time_latest'],
#                 'time_oldest': peaks[i]['time_oldest'],
#                 'peak_latest': peaks[i]['peak_latest'],
#                 'peak_oldest': peaks[i]['peak_oldest'],
#                 'direction': peaks[i]['direction'],
#                 # 'data': peaks[i]['data'],
#                 'body_ave': peaks[i]['body_ave'],
#                 # 'count': len(peaks[i]['data']) - 1
#             }
#             # print(peaks[i]['data'])
#             if i+1 < len(peaks):
#                 if peaks[i+1]['direction'] == (d * -1):
#                     # 情報を追加する
#                     t['time_oldest'] = peaks[i+1]['time_oldest']
#                     t['peak_oldest'] = peaks[i+1]['peak_oldest']
#                     # t['data'] = pd.concat([t['data'], peaks[i+1]['data']], axis=0, ignore_index=True)
#                     # t['count'] = t['count'] + len(peaks[i+1]['data'])
#                     # tilt
#                     gap = t['peak_latest']-t['peak_oldest']
#                     t['gap'] = gap
#                     # t['tilt'] = round(gap/t['count'], 3)
#             # 結果を格納する
#             ans.append(t)
#             max_counter = max_counter + 1
#     # 表示用
#     # print("極値表示")
#     # print(ans)  # ansは現状上が新しい、下が古いもの ⇒
#     res = 0  # 過去に同一の下限有
#     bef = 0  # 何回前か？　（２[数字的には１]回目が直近。１[数字的には０]回目は自身。）
#     bef_peak = 0
#     bef_time = 0
#     ans_dic = {"res": res}  # 初期値を入れておく（ansは必須）
#     for i in range(len(ans)):
#         if i == 0:
#             # 初回は実行しない（探索元（引数）自体の可能性があるあため
#             pass
#         else:
#             mt = price - 0.02  # 下限
#             lt = price + 0.02  # 上限
#             ans_target = ans[i]
#             # if i == 1:
#             #     print("korekorekorekore")
#             #     print(ans_target['time_latest'])
#             if mt <= ans_target['peak_latest'] <= lt:
#                 res = 1  # 過去に同一の下限有
#                 bef = i  # 何回前か？　（２[数字的には１]回目が直近。１[数字的には０]回目は自身。）
#                 bef_peak = ans_target['peak_latest']
#                 bef_time = ans_target['time_latest']
#                 ans_dic = {
#                     "res": res,
#                     "bef": bef,  # N回前か
#                     "bef_peak": bef_peak,
#                     "bef_time": bef_time
#                 }
#     return {"res": res, "ans_dic": ans_dic}
#

def inspection_candle(ins_condition):
    """
    オーダーを発行するかどうかの判断。オーダーを発行する場合、オーダーの情報も返却する
    inspection_condition:探索条件を辞書形式（ignore:無視する直近足数,latest_n:直近とみなす足数)
    """
    #条件（引数）の取得
    data_r = ins_condition['data_r']

    # ■直近ターンの形状（２戻し）の解析
    turn2_ans = turn2_cal(ins_condition['turn_2'])

    # ■ダブルトップやボトムを探す['direction']
    e = 0  # 1で処理キャンセル
    if e == 0 and turn2_ans['turn_ans'] == 1:  # スマホからエラーの時に簡単に飛ばせるように
        print(" ■PeakChek")
        peaks = peaks_collect(data_r)
        print(" 直近の数", len(peaks['from_last_peak']))
        print(" 直近の数とサイズ 直近:",peaks['from_last_peak']['count'], peaks['from_last_peak']['time'],  peaks['from_last_peak']['time_oldest'],
              "次", )
    else:
        print(" ■Peakcheckなし", e, turn2_ans['turn_ans'])

    # ■直近ターン形状（３戻し）の解析
    # turn3_ans = turn3_cal(ins_condition)

    # ■直近ターンの形状（２戻し）スキップ無し　のかいせき
    # figure_turn_ans = figure_turn_judge(ins_condition['figure'])

    # ■直近データの形状の確認（5pip以上の同方向が二つの後に、5pips以内の戻りがあった場合、順張りする）
    figure_latest3_ans = figure_latest3_judge(ins_condition)

    # ■MACDについての解析
    latest_macd_r_df = data_r[0: 30]  # 中間に重複のないデータフレーム
    latest_macd_df = oanda_class.add_macd(latest_macd_r_df)  # macdを追加（データは時間昇順！！！）
    macd_result = macd_judge(latest_macd_df)

    # ■直近N個の幅調査する（レンジかの判断）
    rap_ans = rap_jd(ins_condition['turn_2'])

    # ■■■■上記内容から、Positionの取得可否を判断する■■■■
    if turn2_ans['turn_ans'] == 1 or figure_latest3_ans['result'] == 1:  # 条件を満たす(購入許可タイミング）
        ans = 1
        print(macd_result['data'].head(5))
        # 保存が必要な場合は、保存を実施する
        if ins_condition['save']:
            pass
            # turn2_ans['latest_ans']["data"].to_csv(tk.folder_path + str(ins_condition['time_str']) + 'latest.csv', index=False, encoding="utf-8")
            # turn2_ans['oldest_ans']["data"].to_csv(tk.folder_path + str(ins_condition['time_str']) + 'oldest.csv', index=False, encoding="utf-8")
            # macd_result["data"].to_csv(tk.folder_path + str(ins_condition['time_str']) + 'macd.csv', index=False, encoding="utf-8")

    elif macd_result['cross'] != 0:  # クロスがある場合、表示だけはしておく
        ans = 0
        print(" クロスのみの発生")
        print(macd_result['data'].head(5))
    else:
        ans = 0

    # print(figure_ans)
    return {"judgment": ans,  # judeentは必須（planで利用する。とりあえず
            "turn2_ans": turn2_ans,
            # "turn3_ans": turn3_ans,
            "macd_result": macd_result,
            "latest3_figure_result": figure_latest3_ans,
            "rap_ans": rap_ans
            }




