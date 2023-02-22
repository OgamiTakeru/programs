import requests
import datetime  # 日付関係
from scipy.signal import argrelmin, argrelmax  # add_peaks
import pandas as pd  # add_peaks
from plotly.subplots import make_subplots  # draw_graph
import plotly.graph_objects as go  # draw_graph
import programs.oanda_class as oanda_class


def draw_graph(mid_df):
    """
    ローソクチャーを表示する関数。
    引数にはDataFrameをとり、最低限Open,hitg,low,Close,Time_jp,が必要。その他は任意。
    """
    order_num = 3  # 極値調査の粒度  gl['p_order']  ⇒基本は３。元プログラムと同じ必要がある（従来Globalで統一＝引数で渡したいけど。。）
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


def add_peak(data_df, order_num):
    """
    引数として与えられたデータに、極値データを付与する。いつか、Classに移動させるべきもの。
    もう一つの引数order_numは、「極値求める際の、粒度」。おおむね３から２程度。
    返り値は、各列が付属したデータフレーム
    """
    # order_num = 3  #gl['p_order']
    high_v = "ema_s"  # "inner_high"  "high"  ema_s
    low_v = "ema_s"  # "inner_low"  "low" ema_s
    peak_sr = data_df[high_v].loc[argrelmax(data_df[high_v].values, order=order_num)]  # ①peak専用列
    peak_pd = pd.DataFrame(peak_sr)  # pandasに変換（列名を変えたいだけ１、、、　renameが上手くいかない）
    peak_pd.rename(columns={high_v: 'high'}, inplace=True)  # 列名を変変!
    valley_sr = data_df[low_v].loc[argrelmin(data_df[low_v].values, order=order_num)]  # ②valley専用列
    valley_pd = pd.DataFrame(valley_sr)  # pandasに変換（列名を変えたいだけ１、、、　renameが上手くいかない）
    valley_pd.rename(columns={low_v: 'low'}, inplace=True)  # 列名を変変!
    pv_df = pd.concat([peak_pd, valley_pd], axis=1)  # ピークとバレーをマージする
    for index, data in pv_df.iterrows():  # １行ごとループ以外の方法がわからん。。
        # ピークorバレーのフラグを付ける（初回のみ）
        if pd.isna(data['low']):
            pv_df.loc[index, 'pv_flag'] = 1  # Low(valley)が空欄の場合は、そのままpeakを採用する(peakフラグ）
        else:
            pv_df.loc[index, 'pv_flag'] = -1  # Lowありの場合は、valleyを採用（valleyフラグ）
            pv_df.loc[index, 'high'] = data['low']
    pv_df.drop(['low'], axis=1, inplace=True)  # highにデータを移した後、low列は不要の為削除
    pv_df.rename(columns={'high': 'pv'}, inplace=True)  # 列名を変変（high⇒pv_flag)　③peak/valley 混合dfの完成
    data_df['peak_' + str(order_num)] = peak_pd
    data_df['valley_' + str(order_num)] = valley_pd
    data_df['pv_' + str(order_num)] = pv_df['pv']
    data_df['pv_flag' + str(order_num)] = pv_df['pv_flag']
    return data_df


# def streak_pm(data_df):
#     """
#     引数１はデータフレーム。
#     引数のデータフレームの先頭から、何回連続で「同じ方向のローソク」が続くかを算出する
#     （いわゆる、三羽ガラス。関数名のstreakは連続という意味らしい）
#     引数２は許容する飛び分（１つだけ別方向でも、連荘とみなす場合、１の引数が来る）
#     返り値は、何連続同じ方向のローソクが続き、どの程度の価格変動があるかどうか
#     """
#     counter = 0
#     up_down = 0
#     for index, e in data_df.iterrows():
#         # 1行目は情報収集
#         if counter == 0:
#             counter += 1
#             up_down += abs(e['body'])
#             if e['body'] < 0:  # 最初がマイナスの場合、マイナスがどれだけ続くか
#                 direction = -1
#                 price = e['low']
#             elif e['body'] >= 0:
#                 direction = 1
#                 price = e['high']
#         # 2行目以降は連続性を判断する
#         else:
#             if direction == 1:  # 初回プラスの場合
#                 if e['body'] >= 0:  # 連続＋の場合
#                     up_down += abs(e['body'])
#                     counter += 1
#                 else:  # 連続＋終了
#                     break
#             elif direction == -1:  # 初回マイナスの場合
#                 if e['body'] < 0:  # 連続-の場合
#                     up_down += abs(e['body'])
#                     counter += 1
#                 else:  # 連続-終了
#                     break
#     return {"count": counter, "price": price}


def renzoku_gap_pm(data_df):
    """
    引数のデータフレームを先頭(０行目)から確認し、何行連続で同じ方向に進んでいるかを確認。（ローソク方向ではないく以下の方法）
    基本的にはこのデータフレームは、先頭が最新のデータとなる「リバースデータ」であること。
    確認方法は、各行（各足）の中央値（inner_highとinner_lowとの中央値。highとlowの中央値ではない）が、
    連続して下がっているか（or上がっているか）を確認。
    返り値は
    ・何回連続で同じ方向に進んでいるか（足の数）
    ・どっちの方向に進んでいるか
    ・値段の動き　等
    を辞書形式で返却する
    :param data_df: 調査したい範囲のデータフレーム。230101時点では、3足分、６足分がそれぞれ呼ばれる
    :return:
    """
    # 中央値（Inner高値とInner低値の）の動きを確認、何連続で同じ方向に行っているかを確認する（植木算的に、３行の場合は２個）
    # print("  Practice　")
    p_counter = m_counter = 0
    oldest_price = latest_price = 0
    counter = 0
    flag = 0  # ＋かマイナスかのフラグ（条件分岐）
    # カウントする
    for ln in range(len(data_df)):
        if ln <= len(data_df) - 2:  # 差分取得のため。－２のインデックスまで
            # 初回の場合
            if counter == 0:
                if len(data_df) - 2 == 0:  # 二行しかない場合（指定が２つのDFの場合、一回で完結する
                    # print(data_df)
                    # data_df.to_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', index=False, encoding="utf-8")
                    if data_df.iloc[0]["middle_price_gap"] > 0:  # 先頭の行(時系列が新)が、次行(時系列が古）との比較。
                        # 上り方向
                        p_counter = 1
                        m_counter = 0
                        oldest_price = data_df.iloc[-1]["inner_low"]  # 上がりGapなので、開始は２行目（古）のLow = 低い
                        latest_price = data_df.iloc[0]["inner_high"]  # 上がりGapなので、終了は1行目（新）のhigh　＝高い
                        middle_price = round(oldest_price + (latest_price - oldest_price) / 2, 3)  # oldが低いところにいる
                    else:
                        p_counter = 0
                        m_counter = 1
                        oldest_price = data_df.iloc[-1]["inner_high"]  # 下がりGapなので、開始は２行目（古）のhigh　＝　高い
                        latest_price = data_df.iloc[0]["inner_low"]  # 下がりGapなので、終了は1行目（新）のlow　＝低い
                        middle_price = round(oldest_price - (oldest_price - latest_price) / 2, 3)  # oldが高いところにいる
                else:  # 通常（従来の6:3等、２以上の判定を使う方法の場合）
                    # print("g", len(data_df))
                    counter += 1
                    if data_df.iloc[ln]["middle_price_gap"] > 0:
                        flag = 1
                        # print("初回＋", data_df.iloc[l]["middle_price_gap"],
                        # data_df.iloc[l]["inner_high"], data_df.iloc[l]["time_jp"])
                        latest_price = data_df.iloc[ln]["inner_high"]  # 最初のスタート値（上がっていくため、最高部分）
                        p_counter += 1
                    else:
                        # print("初回－", data_df.iloc[l]["middle_price_gap"],
                        # data_df.iloc[l]["inner_low"], data_df.iloc[l]["time_jp"])
                        latest_price = data_df.iloc[ln]["inner_low"]  # 最初のスタート値（下がっていくため、最低部分）
                        m_counter += 1
                        flag = -1
            # 初回以降
            else:
                counter += 1
                if flag == 1 and data_df.iloc[ln]["middle_price_gap"] > 0:
                    # 初回がプラスで、今回もプラスの場合
                    p_counter += 1
                    oldest_price = data_df.iloc[ln+1]["inner_low"] # ひとつ前の行の値になる事に注意
                    # print(" ■連続＋", p_counter, '回目', data_df.iloc[l]["middle_price_gap"], data_df.iloc[l+1]["inner_low"], data_df.iloc[l+1]["time_jp"])
                elif flag == 1 and data_df.iloc[ln]["middle_price_gap"] <= 0:
                    # 初回がプラスで、今回もマイナスの場合
                    # print(" 連続＋途絶え", p_counter, "回目", data_df.iloc[l]["middle_price_gap"], data_df.iloc[l]["time_jp"])
                    flag = 0  # flag取り下げ（アンサーにもなる）
                    break
                elif flag == -1 and data_df.iloc[ln]["middle_price_gap"] <= 0:
                    # 初回が－で、今回も－の場合
                    oldest_price = data_df.iloc[ln+1]["inner_high"]  # ひとつ前の行の値になる事に注意
                    # print(" ■連続－", m_counter, '回目', data_df.iloc[l]["middle_price_gap"], data_df.iloc[l+1]["inner_high"], data_df.iloc[l+1]["time_jp"])
                    m_counter += 1
                elif flag == -1 and data_df.iloc[ln]["middle_price_gap"] > 0:
                    # 初回が－で、今回もプラスの場合
                    # print(" 連続－途絶え", m_counter, '回目', data_df.iloc[l]["middle_price_gap"], data_df.iloc[l]["time_jp"])
                    flag = 0  # flag取り下げ（アンサーにもなる）
                    break

    # 答えのまとめ
    if m_counter > p_counter:
        ans = -1  # マイナスの連荘
        ans_count = m_counter + 1
        middle_price = round(oldest_price - (oldest_price - latest_price)/2, 3)  # oldが高いところにいる
    elif p_counter >= m_counter:
        ans = 1  # プラスの連荘
        ans_count = p_counter + 1
        middle_price = round(oldest_price + (latest_price - oldest_price) / 2, 3)  # oldが低いところにいる

    # ３個(or２個）の場合、ローソクの関係性を求める
    # ３個の場合、３パターンのいずれか。谷の場合(折り返し部が＋）、古い順に1,1,1/1,-1,1/1,1,-1
    if len(data_df) == 3:
        if ans == 1:  # プラスの連荘＝谷の場合　（折り返し部のみの話）
            if data_df.iloc[2]['body'] >=0 and data_df.iloc[1]['body'] >=0 and data_df.iloc[0]['body'] >=0:
                pattern_comment = "afterV:all plus"
                pattern = 10
            elif data_df.iloc[2]['body'] >=0 and data_df.iloc[1]['body'] <=0 and data_df.iloc[0]['body'] >=0:
                pattern_comment = "afterV:middle Down"
                pattern = 11
            elif data_df.iloc[2]['body'] >=0 and data_df.iloc[1]['body'] >=0 and data_df.iloc[0]['body'] <=0:
                pattern_comment = "afterV:last Down"
                pattern = 12
            else:
                pattern_comment = "afterV:first Down"
                pattern = 13
        elif ans == -1:  # マイナスの連荘＝山の場合　（折り返し部の話）
            if data_df.iloc[2]['body'] <=0 and data_df.iloc[1]['body'] <=0 and data_df.iloc[0]['body'] <=0:
                pattern_comment = "afterM:all minus"
                pattern = -10
            elif data_df.iloc[2]['body'] <=0 and data_df.iloc[1]['body'] >=0 and data_df.iloc[0]['body'] <=0:
                pattern_comment = "afterM:middle Up"
                pattern = -11
            elif data_df.iloc[2]['body'] <=0 and data_df.iloc[1]['body'] <=0 and data_df.iloc[0]['body'] >=0:
                pattern_comment = "afterM:last Up"
                pattern = -12
            else:
                pattern_comment = "afterM:first Up"
                pattern = -13
    else:
        pattern = -99
        pattern_comment = "NoComment"

    return({
        # "final_time": data_df.iloc[0]["time_jp"],
        # "final_close_price": data_df.iloc[0]["close"],
        "oldest_price": oldest_price,
        "oldest_time": data_df.iloc[-1]["time_jp"],
        "latest_price": latest_price,
        "latest_time": data_df.iloc[0]["time_jp"],
        "inner_high_price": data_df["inner_high"].max(),
        "inner_low_price": data_df["inner_low"].min(),
        "high_price": data_df["high"].max(),  # 範囲の最高価格(innerではない）（将来的にLC/利確価格になるかも）
        "low_price": data_df["low"].min(),  # 範囲の最高価格(innerではない）（将来的にLC/利確価格になるかも）
        "gap": round(abs(oldest_price - latest_price), 3),
        "middle_price": middle_price,
        "direction": ans,
        "count": ans_count,
        "data_size": len(data_df),
        "pattern": pattern,  # 3この場合のみ
        "pattern_comment": pattern_comment,  # 3個の場合のみ
        "data": data_df,
    })
    print(oldest_price, "-", latest_price, ans, ans_count)


def make_repeat_order(order_dic):
    """
    :param order_dic: {"base_price": entry_price, "lap":-0.01, "lc":0.03, "tp": 0.015, "num":4,
                     "ask_bid": 1 * direction_l, "units": 10001, "type":"STOP", "mind":-1, "time_out": 10*60,
                     "order_edit_flag": 0, "order_id": 0, "position_id": 0,"memo":"memo"
                     }
                     なおlapは-値の場合、TP価格とかぶる。プラスの価格で、隙間の空いた注文となる
    :return: トラリピのオーダーを作成し、①辞書の配列と②最終的にいくらの価格でリピートを入れた（Base価格）を返却。辞書は以下の通り
                    {"price": temp,"lc_price": 0.05,"lc_range": t_gap - 0.007, "tp_range": 0.08,
                    "ask_bid": -1 * direction_l,"units": 10000,"type": "STOP","tr_range": 0.05,"mind": 1,
                    "memo": "first_f","time_out": 10*60,"order_edit_flag": 0,"order_id": 0,"position_id": 0}
                    の配列を却下
    """
    base_price = order_dic["price"]
    units = order_dic["units"]
    lap = order_dic["lap"]  # 前のTPとのラップ（マイナス値でTP範囲とラップさせる）
    lc = order_dic["lc"]
    tp = order_dic["tp"]
    num = order_dic["num"]
    direction_l = order_dic["ask_bid"]  # direction_lと同義
    reorder_units = order_dic["reoeder_units"]
    inc_units = -5000  # 毎回増えていく用（インクリーズさせる用）
    inc_lc = 0.03  #　毎回増えていくよう
    inc_tp = 0.04  # 毎回増えていくよう
    order_arr = []
    for i in range(num):
        temp_rep = {
            "price": base_price,
            "lc_price": 100,
            "lc_range": lc,  # ギリギリまで。
            "tp_range": tp,
            "ask_bid": 1 * order_dic["ask_bid"],
            "units": units,
            "type":  order_dic["type"],
            "tr_range": 0,
            "mind": order_dic["mind"],
            "memo": "trap",
        }
        # 参考情報計算
        tp_price = round(base_price + (tp * direction_l), 3)  #
        base_price = round(tp_price + (lap * direction_l), 3)  # 次期トラリピやオーダーの参考用（トラリピの最終オーダー箇所）
        order_arr.append(temp_rep)
        # インクリーズ計算
        units = units + inc_units
        lc = lc + inc_lc
        tp = tp + inc_tp
    return order_arr, base_price


def judgement_42(oldest_ans, latest_ans, now_price):
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
            ans_info = {"return_ratio": return_ratio, "bunbo_gap": oldest_ans['gap'],
                        "oldest_old": oldest_ans["oldest_price"], "latest_late": latest_ans["latest_price"],
                        "latest_old": latest_ans["oldest_price"], "direction": latest_ans["direction"],
                        "mid_price": now_price, "oldest_count": oldest_ans["count"], "latest_count": latest_ans['count']}

            # 戻り率次第で、色々処理を変える
            order_arr = []
            max_return_ratio = 56  # 初期値の設定（最大戻り率）
            direction_l = latest_ans['direction']  #
            if return_ratio < max_return_ratio:
                # print("  オーダー準備")
                # 順方向（４２の場合）
                entry_price = latest_ans["oldest_price"] if direction_l == 1 else latest_ans["oldest_price"]
                f_order = {
                    "price": entry_price,
                    "lc_price": 0.05,
                    "lc_range": 0.022,  # ギリギリまで。。
                    "tp_range": 0.035,  # latest_ans['low_price']+0 if direction_l == 1 else latest_ans['high_price']-0
                    "ask_bid": -1 * direction_l,
                    "units": 60000,
                    "type": "STOP",
                    "tr_range": 0.10,  # ↑ここまでオーダー
                    "mind": 1,
                    "memo": "forward"
                }
                order_arr.append(f_order)  # 0はデータ

                # 逆方向（４２の場合）
                gap = abs(entry_price - now_price) * 1.4  # 順方向に達成する幅をそのまま流用する(1.5倍くらいしておくか。。。）
                pr = latest_ans['latest_price'] + gap if direction_l == 1 else latest_ans['latest_price'] - gap
                # print("  テスト価格表示42", entry_price, pr, gap, latest_ans['latest_price'])
                r_order = {
                    "price": pr,
                    "lc_price": 0.05,
                    "lc_range": 0.03,  # ギリギリまで。。
                    "tp_range": 0.05,  # latest_ans['low_price']+0 if direction_l == 1 else latest_ans['high_price']-0
                    "ask_bid": 1 * direction_l,
                    "units": 50000,
                    "type": "STOP",
                    "tr_range": 0.10,  # ↑ここまでオーダー
                    "mind": -1,
                    "memo": "reverse",
                }
                # ans_info['ref_r_entry'] = pr  # テスト用
                # オーダーをひとまとめにする
                order_arr.append(r_order)
                # 返却する
                return {"ans": 42, "order_plan": order_arr, "jd_info": ans_info, "memo": "42成立"}
            else:
                print("  戻り率大（４２）", return_ratio)
                return {"ans": 0, "order_plan": order_arr, "jd_info": ans_info, "memo": "戻り大"}
        else:
            print("  行数未達（４２）")
            return {"ans": 0, "order_plan": 0, "jd_info": 0, "memo": "行数未達"}
    else:
        print("  方向同方向４２")
        return {"ans": 0, "order_plan": 0, "jd_info": 0, "memo": "同方向"}
