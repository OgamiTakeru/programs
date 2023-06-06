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
    # 表示等で利用する用（機能としては使わない
    memo_time = oanda_class.str_to_time_hms(ans_df.iloc[-1]["time_jp"]) + "_" + oanda_class.str_to_time_hms(
        ans_df.iloc[0]["time_jp"])
    # 返却用
    ans_dic = {
        "direction": base_direction,
        "count": counter+1,  # 最新時刻からスタートして同じ方向が何回続いているか
        "data": ans_df,  # 対象となるデータフレーム（元のデータフレームではない）
        "data_size": len(data_df),  # (注)元のデータサイズ
        "latest_image_price": latest_image_price,
        "oldest_image_price": oldest_image_price,
        "oldest_time_jp": ans_df.iloc[-1]["time_jp"],
        "latest_time_jp": ans_df.iloc[0]["time_jp"],
        "latest_price": ans_df.iloc[0]["close"],
        "oldest_price": ans_df.iloc[-1]["open"],
        "gap": gap,
        "body_ave": body_ave,
        "move_abs": move_ave,
        "memo_time":memo_time
    }

    # ■　形状を判定する（テスト）
    type_info_dic = figure_turn_each_inspection_support(ans_df, base_direction, ans_dic)  # 対象のデータフレームと、方向を渡す
    ans_dic["support_info"] = type_info_dic
    return ans_dic


def figure_turn_inspection(ins_condition):
    """
    old区間4,latest区間2の場合のジャッジメント
    :param oldest_ans:第一引数がOldestであること。直近部より前の部分が、どれだけ同一方向に進んでいるか。
    :param latest_ans:第二引数がLatestであること。直近部がどれだけ連続で同一方向に進んでいるか
    :param now_price: 途中で追加した機能（現在の価格を取得し、成り行きに近いようなオーダーを出す）　230105追加
    :param ins_condition
    :return:
    """
    #
    # ■直近データの形状の解析
    data_r = ins_condition['data_r']  # データを格納
    now_price = ins_condition['now_price']
    ignore = ins_condition['figure']['ignore']  # ignore=1の場合、タイミング次第では自分を入れずに探索する（正）
    dr_latest_n = ins_condition['figure']['latest_n']  # 2
    dr_oldest_n = ins_condition['figure']['oldest_n']  # 10 ⇒30
    # 各DFを解析
    latest_df = data_r[ignore: dr_latest_n + ignore]  # 直近のn個を取得
    oldest_df = data_r[dr_latest_n + ignore - 1: dr_latest_n + dr_oldest_n + ignore - 1]  # 前半と１行をラップさせる。
    latest_ans = figure_turn_each_inspection(latest_df)  # 何連続で同じ方向に進んでいるか（直近-1まで）# Latestの期間を検証する
    oldest_ans = figure_turn_each_inspection(oldest_df)  # 何連続で同じ方向に進んでいるか（前半部分）# Oldestの期間を検証する

    # 表示用がメインの情報まとめ
    memo_time = oanda_class.str_to_time_hms(oldest_ans['oldest_time_jp']) + "_" + oanda_class.str_to_time_hms(latest_ans['latest_time_jp'])
    memo_price = "(" + str(oldest_ans['oldest_price']) + "_" + str(latest_ans['latest_price']) + "," + str(oldest_ans['direction'])
    memo_all = memo_time + memo_price
    # 初期値があった方がいいもの（エラー対策）
    return_ratio = 0
    # 判定処理
    if latest_ans['direction'] != oldest_ans['direction']:  # 違う方向だった場合 (想定ケース）
        if latest_ans['count'] == latest_ans['data_size'] and oldest_ans['count'] >= 4:  # 行数確認(old区間はt直接指定！）
            # 戻しのパーセンテージを確認
            return_ratio = round((latest_ans['gap'] / oldest_ans['gap']) * 100, 3)
            max_return_ratio = 50
            if return_ratio < max_return_ratio:
                turn_ans = 1  # 達成
                memo = "達成"
            else:
                turn_ans = 0  # 未達
                memo = "戻大" + str(return_ratio)
        else:
            turn_ans = 0  # 未達
            memo = "カウント未達"
    else:
        turn_ans = 0  # 未達
        memo = "同方向"

    memo_info = "@戻り率" + str(return_ratio) + ",向き(old):" + str(oldest_ans['direction']) + ",縦幅(old):" + str(oldest_ans['gap'])
    memo_all = memo_all + memo_info

    # 返却用の辞書を作成
    ans_dic = {
        "turn_ans": turn_ans,
        "latest_ans": latest_ans,
        "oldest_ans": oldest_ans,
        "return_ratio": return_ratio,
        "memo": memo,
        "memo_all": memo_all,
        "price": now_price
    }

    # Return
    return ans_dic


def figure_turn_judge(ins_condition):
    data_r = ins_condition['data_r']
    # 直近のデータの確認　LatestとOldestの関係性を検証する
    turn_ans = figure_turn_inspection(ins_condition)  # ★★引数順注意。ポジ用の価格情報取得（０は取得無し）
    # 初期値の設定
    include_ans = 0  # 最初は０
    include_memo = "0"
    expected_direction = turn_ans['oldest_ans']['direction']  # 購入の初期値は、Oldestと同方向（順思想）
    expected_lc_range = 0  # Range判断の場合に利用するが、共通の辞書返却の為
    expected_tp_range = 0  # Range判断の場合に利用するが、共通の辞書返却の為
    include_ratio = 0
    # もう一つ前のデータの確認　(上記の成立があれば）
    c_o_ans = c_o_memo = c_o_ratio = 0  # 初期化が必要な変数
    turn_ans2 = turn_ans.copy()  # めんどくさいからとりあえず入れておく。。
    turn_ans2['memo'] = "（同値）"
    if turn_ans['turn_ans'] == 1:
        if turn_ans['oldest_ans']['count'] <= 8:  # ８以上の場合は完全にレンジを解消していると判断
            next_inspection_range = ins_condition['figure']['ignore'] + ins_condition['figure']['latest_n'] + \
                                    turn_ans['oldest_ans']['count'] - 2
            next_inspection_r_df = data_r[next_inspection_range-2:]  # 調整した挙句、ー２で丁度よさそう。Nextの調査対象
            ins_condition['data_r'] = next_inspection_r_df  # 調査情報に代入する
            turn_ans2 = figure_turn_inspection(ins_condition)  # ★★ネクストの調査
            if turn_ans2['turn_ans'] == 1:
                include_ratio = round(float(turn_ans['oldest_ans']['gap']) / float(turn_ans2['oldest_ans']['gap']), 1)  # 共通
                if turn_ans2['oldest_ans']['gap'] > turn_ans['oldest_ans']['gap']:
                    include_ans = 1
                    expected_direction = expected_direction * -1  # レンジに入ると予想するため、逆方向
                    oldest_gap = turn_ans['oldest_ans']['gap']
                    latest_gap = turn_ans['latest_ans']['gap']
                    expected_lc_range = latest_gap  # LCはlatest_gap
                    expected_tp_range = round(oldest_gap - latest_gap - (oldest_gap * 0.1), 3)  # 指定方法は、OldestのGapから、latest戻り分(=latestGap)と縮小分(oldestの１割)を引いた数。
                    include_memo = "Turn発生&包括関係の形状発生"
                    print(" 発生&包括されていそう！", expected_direction, expected_tp_range, expected_lc_range)
                else:
                    include_ans = 0
                    include_memo = "Turn発生&前回turnより大きくなっている"
        else:
            include_ans = 0
            include_memo = "Turn発生&前回turnは結構前"
    else:
        include_ans = 0
        include_memo = "現在でTurnの発生無し"

    print("  ", include_memo)

    # 現在と過去の形状で包括関係の情報
    include_result = {
        "total_ans": c_o_ans,
        "total_memo": include_memo,
        "include_ratio": include_ratio,
    }

    # 結果を辞書形式にまとめる
    result_dic = {
        "result_turn": turn_ans['turn_ans'],
        "result_include": include_ans,
    }

    ans = {
        "result_dic": result_dic,
        "latest_turn_dic": turn_ans,
        "oldest_turn_dic": turn_ans2,
        "include_dic": include_result,
        "order_dic": {
            "base_price": turn_ans['latest_ans']['latest_image_price'],
            "direction": expected_direction,
            "tp_range": expected_tp_range,
            "lc_range": expected_lc_range
        }
    }

    return ans


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
    older_line = 0.02
    later_line = 0.02
    if middle == 0:
        middle = 0.0000001

    # print(oldest, oldest_d, middle, middle_d, latest, latest_d)
    # 三つの方向が形式にあっているか（↑↑↓か、↓↓↑）を確認
    if (oldest_d == middle_d) and oldest_d != latest_d:
        d = 1
    else:
        d = 0

    if oldest > older_line and middle > older_line and latest < later_line:  # どっちも5pips以上で同方向
        p = 1
    else:
        p = 0

    if 0.4 < oldest / middle < 2.5:
        r = 1
    else:
        r = 0

    if d == 1 and p == 1 and r == 1:
        # print("   完全 dpr⇒", d, p, r)
        res_memo = "Trun未遂達成"
        latest3_figure = 1
        order = {
            "target_price": data_r.iloc[0]['open'],
            "direction": oldest_d
        }
    else:
        res_memo = "Trun未遂未達"
        latest3_figure = 0
        order = {
            "target_price": 0,
            "direction": 0
        }
        # print("   未達成 dpr⇒", d, p, r)

    memo1 = " ,Dir:" + str(oldest_d) + str(middle_d) + str(latest_d)
    memo2 = " ,Body:" + str(oldest) + str(middle) + str(latest)
    memo3 = " ,body率" + str(round(oldest / middle, 1))
    memo4 = ", TargetPrice:" + str(order['target_price'])
    memo_all = "  " + res_memo + memo4 + memo1 + memo2 + memo3 + memo4
    print(memo_all)

    return {"result": latest3_figure, "order_dic": order, "memo": memo_all}


def inspection_candle(ins_condition):
    """
    オーダーを発行するかどうかの判断。オーダーを発行する場合、オーダーの情報も返却する
    ins_condition:探索条件を辞書形式（ignore:無視する直近足数,latest_n:直近とみなす足数)
    """
    #条件（引数）の取得
    data_r = ins_condition['data_r']

    # ■直近データの形状の解析
    figure_turn_ans = figure_turn_judge(ins_condition)

    # ■直近データの形状の確認（5pip以上の同方向が二つの後に、5pips以内の戻りがあった場合、順張りする）
    figure_latest3_ans = figure_latest3_judge(ins_condition)

    # ■MACDについての解析
    latest_macd_r_df = data_r[0: 30]  # 中間に重複のないデータフレーム
    latest_macd_df = oanda_class.add_macd(latest_macd_r_df)  # macdを追加（データは時間昇順！！！）
    macd_result = macd_judge(latest_macd_df)

    # ■■■■上記内容から、Positionの取得可否を判断する■■■■
    print("　　Fig:", figure_turn_ans['result_dic']['result_turn'], "(", figure_turn_ans['result_dic']['result_include'], ") Macd:"
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
            "latest3_figure_result": figure_latest3_ans
            }




