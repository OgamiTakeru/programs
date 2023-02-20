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
    inc_units = 5000  # 毎回増えていく用（インクリーズさせる用）
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
            "time_out": order_dic["time_out"],  # 時間を過ぎたら解除するオーダー
            "order_edit_flag": 0,  # オーダーを変更したフラグ
            "order_id": 0,  # オーダーを発行した場合、オーダーIDを取得しておく
            "position_id": 0,  # オーダーがポジションした場合、ポジションIDを取得しておく（可能か・・？）
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
                        "mid_price": now_price, "oldest_count": oldest_ans["count"], "latest_count":latest_ans['count']}

            # 戻り率次第で、色々処理を変える
            max_return_ratio = 45  # 初期値の設定（最大戻り率）
            direction_l = latest_ans['direction']  #
            if return_ratio < max_return_ratio:
                print("  オーダー準備")
                # 順方向（４２の場合）
                entry_price = latest_ans["oldest_price"] if direction_l == 1 else latest_ans["oldest_price"]
                rep = {"price": entry_price, "lap": 0.005, "lc": 0.03, "tp": 0.04, "num": 2,
                       "ask_bid": -1 * direction_l, "units": 5420, "type": "STOP", "mind": -1, "time_out": 10 * 60,
                       "order_edit_flag": 0, "order_id": 0, "position_id": 0, "memo": "戻り半端"
                       }
                repeat_arr = make_repeat_order(rep)  # 0はデータ、1は次期オーダーの参考値
                order_arr = repeat_arr[0]  # 0はデータ

                # 逆方向（４２の場合）
                gap = abs(entry_price - now_price) * 1.7  # 順方向に達成する幅をそのまま流用する(1.5倍くらいしておくか。。。）
                pr = latest_ans['latest_price'] + gap if direction_l == 1 else latest_ans['latest_price'] - gap
                print("  テスト価格表示42", entry_price, pr, gap, latest_ans['latest_price'])
                r_order = {
                    "price": pr,
                    "lc_price": 0.05,
                    "lc_range": 0.03,  # ギリギリまで。。
                    "tp_range": 0.05,  # latest_ans['low_price']+0 if direction_l == 1 else latest_ans['high_price']-0
                    "ask_bid": 1 * direction_l,
                    "units": 10421,
                    "type": "STOP",
                    "tr_range": 0.10,  # ↑ここまでオーダー
                    "mind": 1,
                    "time_out": 10*60,  # 時間を過ぎたら解除するオーダー
                    "order_edit_flag": 0,  # オーダーを変更したフラグ
                    "order_id": 0,  # オーダーを発行した場合、オーダーIDを取得しておく
                    "position_id": 0,  # オーダーがポジションした場合、ポジションIDを取得しておく（可能か・・？）
                    "memo": "first_f",
                }
                ans_info['ref_r_entry'] = pr  # テスト用
                # オーダーをひとまとめにする
                order_arr.append(r_order)
                # 返却する
                return {"ans": 42, "orders": order_arr, "info": ans_info, "memo": "42成立"}
            else:
                print("  戻り率大（４２）", return_ratio)
                return {"ans": 0}
        else:
            print("  行数未達（４２）")
            return {"ans": 0}
    else:
        print("  方向同方向４２")
        return {"ans": 0}


def judgement_43(oldest_ans, latest_ans, now_price):
    """
    old区間4,latest区間3の場合のジャッジメント
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
                        "mid_price": now_price, "oldest_count": oldest_ans["count"], "latest_count":latest_ans['count']}


            # 戻り率次第で、色々処理を変える
            max_return_ratio = 50  # 初期値の設定（最大戻り率）
            direction_l = latest_ans['direction']  #
            if return_ratio < max_return_ratio:
                print("  オーダー準備")
                # 順方向（４3の場合）
                entry_price = latest_ans["oldest_price"] if direction_l == 1 else latest_ans["oldest_price"]
                rep = {"price": entry_price, "lap": 0, "lc": 0.03, "tp": 0.018, "num": 2,
                       "ask_bid": -1 * direction_l, "units": 5430, "type": "STOP", "mind": -1, "time_out": 10 * 60,
                       "order_edit_flag": 0, "order_id": 0, "position_id": 0, "memo": "戻り半端"
                       }
                repeat_arr = make_repeat_order(rep)  # 0はデータ、1は次期オーダーの参考値
                order_arr = repeat_arr[0]  # 0はデータ

                # 逆方向（４3の場合）
                gap = abs(entry_price - now_price) * 1.5  # 順方向に達成する幅をそのまま流用する(1.5倍くらいしておくか。。。）
                pr = latest_ans['latest_price'] + gap if direction_l == 1 else latest_ans['latest_price'] - gap
                print("  テスト価格表示43", entry_price, pr, gap, latest_ans['oldest_price'], oldest_ans['oldest_price'])
                r_order = {
                    "price": pr,
                    "lc_price": 0.05,
                    "lc_range": 0.05,  # ギリギリまで。。
                    "tp_range": 0.04,  # latest_ans['low_price']+0 if direction_l == 1 else latest_ans['high_price']-0
                    "ask_bid": 1 * direction_l,
                    "units": 10431,
                    "type": "STOP",
                    "tr_range": 0.10,  # ↑ここまでオーダー
                    "mind": 1,
                    "time_out": 10*60,  # 時間を過ぎたら解除するオーダー
                    "order_edit_flag": 0,  # オーダーを変更したフラグ
                    "order_id": 0,  # オーダーを発行した場合、オーダーIDを取得しておく
                    "position_id": 0,  # オーダーがポジションした場合、ポジションIDを取得しておく（可能か・・？）
                    "memo": "first_f",
                }
                ans_info['ref_r_entry'] = pr  # テスト用
                # オーダーをひとまとめにする
                order_arr.append(r_order)
                # 返却する
                return {"ans": 43, "orders": order_arr, "info": ans_info, "memo": "42成立"}
            else:
                print("  戻り率大（４３）")
                return {"ans": 0}
        else:
            print("  行数未達（４３）")
            return {"ans": 0}
    else:
        print("  方向同方向４３")
        return {"ans": 0}

# def renzoku_gap_compare(oldest_ans, latest_ans, now_price):
#     """
#     :param oldest_ans:第一引数がOldestであること。直近部より前の部分が、どれだけ同一方向に進んでいるか。
#     :param latest_ans:第二引数がLatestであること。直近部がどれだけ連続で同一方向に進んでいるか
#     :param now_price: 途中で追加した機能（現在の価格を取得し、成り行きに近いようなオーダーを出す）　230105追加
#     :return:
#     """
#     if latest_ans['direction'] != oldest_ans['direction']:  # 違う方向だった場合 (想定ケース）
#         if latest_ans['count'] == latest_ans['data_size'] and oldest_ans['count'] >= 4:  # 行数確認(old区間はt直接指定！）
#             # 戻しのパーセンテージを確認
#             return_ratio = round((latest_ans['gap'] / oldest_ans['gap']) * 100, 3)
#             info = {"return_ratio": return_ratio, "bunbo_gap": oldest_ans['gap']}  # 情報を保持しておく
#             # 戻り基準と比較し、基準値以内(N%以下等）であれば、戻り不十分＝エントリーポイントとみなす
#             max_return_ratio = 99
#             direction_l = latest_ans['direction']
#             if 80 <= return_ratio < max_return_ratio:
#                 print("  戻り大", oldest_ans['inner_high_price'], oldest_ans['inner_low_price'])
#                 entry_price = oldest_ans['inner_high_price'] if direction_l == 1 else oldest_ans['inner_low_price']
#                 rep = {"price": entry_price, "lap": 0.005, "lc": 0.03, "tp": 0.018, "num": 4,
#                        "ask_bid": direction_l, "units": 10020, "type": "STOP", "mind": -1, "time_out": 10 * 60,
#                        "order_edit_flag": 0, "order_id": 0, "position_id": 0, "memo": "戻り半端"
#                        }
#                 r_repeat_arr = make_repeat_order(rep)
#                 return {"r_repeat": r_repeat_arr[0], "info": info, "memo": 1}
#             elif 40 < return_ratio < 80:
#                 print("  戻り中途半端")
#                 return_price = latest_ans['gap'] * (return_ratio + 10 / 100)  # 60%戻し
#                 entry_price = latest_ans['latest_price'] + return_price if direction_l == 1 else latest_ans['latest_price'] - return_price
#                 rep = {"price": entry_price, "lap": 0.005, "lc": 0.03, "tp": 0.018, "num": 4,
#                        "ask_bid": direction_l, "units": 10020, "type": "STOP", "mind": -1, "time_out": 10 * 60,
#                        "order_edit_flag": 0, "order_id": 0, "position_id": 0, "memo": "戻り半端"
#                        }
#                 r_repeat_arr = make_repeat_order(rep)
#                 return {"r_repeat": r_repeat_arr[0], "info": info, "memo": 1}
#
#             elif return_ratio <= 40:
#                 # 微戻りを考える
#                 moves = latest_ans['data']['moves'].mean()  # 直近の移動量
#                 lcs = 0.1 if moves > 0.1 else moves
#                 # 4:2探索時は幅が狭いことがあるので、latestのinner_highとinner_lowの差分をエントリー価格に反映
#                 high_low_gap = latest_ans['inner_high_price'] - latest_ans['inner_low_price']
#                 min_gap = 0.02
#                 if high_low_gap < min_gap:
#                     # 差分が小さすぎる場合、元々の幅に、上下に均等にクライテリアを設定する(4pipsを超えるように）
#                     adjuster = round((min_gap - high_low_gap) / 2, 3)
#                     t_latest_inner_high_price = latest_ans['inner_high_price'] + adjuster
#                     t_latest_inner_low_price = latest_ans['inner_low_price'] - adjuster
#                     t_gap = min_gap
#                     print(" 差分小", adjuster,t_latest_inner_high_price,t_latest_inner_low_price, t_gap, high_low_gap)
#                     print(" 差分小Data", latest_ans['inner_high_price'], latest_ans['inner_low_price'], adjuster)
#                 else:
#                     t_latest_inner_high_price = latest_ans['inner_high_price']
#                     t_latest_inner_low_price = latest_ans['inner_low_price']
#                     t_gap = high_low_gap
#                     print(" 差分大", t_latest_inner_high_price, t_latest_inner_low_price, t_gap, high_low_gap)
#
#                 # ★①　下にいく本命用（このオーダーはまれにしか入らない。ただし入るときは勢いがあると推定する）
#                 temp = t_latest_inner_low_price + 0.015 if direction_l == 1 else t_latest_inner_high_price - 0.015
#                 rep = {"price": temp, "lap": -0.005, "lc": 0.03, "tp": 0.018, "num": 4,
#                      "ask_bid": -1 * direction_l, "units": 10010, "type": "STOP", "mind": -1, "time_out": 10*60,
#                      "order_edit_flag": 0, "order_id": 0, "position_id": 0,
#                      }
#                 f_repeat_arr = make_repeat_order(rep)
#                 base_price = f_repeat_arr[1]  # 0はデータ、１はBasePrice
#                 f_order = {
#                     "price": base_price,
#                     "lc_price": 0.05,
#                     "lc_range": t_gap - 0.007,  # ギリギリまで。。
#                     "tp_range": 0.08,  # latest_ans['low_price']+0 if direction_l == 1 else latest_ans['high_price']-0
#                     "ask_bid": -1 * direction_l,
#                     "units": 10011,
#                     "type": "STOP",
#                     "tr_range": 0.05,  # ↑ここまでオーダー
#                     "mind": 1,
#                     "memo": "first_f",
#                     "time_out": 10*60,  # 時間を過ぎたら解除するオーダー
#                     "order_edit_flag": 0,  # オーダーを変更したフラグ
#                     "order_id": 0,  # オーダーを発行した場合、オーダーIDを取得しておく
#                     "position_id": 0,  # オーダーがポジションした場合、ポジションIDを取得しておく（可能か・・？）
#                 }
#
#                 # ★②ちょっと上に行く（逆思想）のを取りに行く。LCの関係で
#                 temp = t_latest_inner_high_price+0.01 if direction_l == 1 else t_latest_inner_low_price-0.01
#                 if direction_l == 1:  # 谷の場合
#                     if now_price > temp:
#                         entry_price = now_price
#                         print("now超え", entry_price)
#                     else:
#                         entry_price = temp
#                         print("now超え無し", entry_price)
#                 else:  # 山の場合
#                     if now_price < temp:
#                         entry_price = now_price
#                         print("now以下", entry_price)
#                     else:
#                         entry_price = temp
#                         print("now以下なし", entry_price)
#                 # トラリピ系
#                 rep = {"price": entry_price, "lap": 0.005, "lc": 0.03, "tp": 0.018, "num": 4,
#                      "ask_bid": direction_l, "units": 10020, "type": "STOP", "mind": -1, "time_out": 10*60,
#                      "order_edit_flag": 0, "order_id": 0, "position_id": 0,
#                      }
#                 r_repeat_arr = make_repeat_order(rep)
#                 # 最後はロングのオーダーを出す
#                 base_price = r_repeat_arr[1]  # 0はデータ、１はBasePrice
#                 r_order = {
#                     "price": base_price,  # トラリピ後の価格を取得（トラリピは最後にインクリメントしていく）
#                     "lc_price": 0.03,
#                     "lc_range": t_gap - 0.007,  # ギリギリまで。
#                     "tp_range": 0.08,  # latest_ans['low_price']+0 if direction_l == 1 else latest_ans['high_price']-0
#                     "ask_bid": 1 * direction_l,
#                     "units": 10021,
#                     "type": "STOP",
#                     "tr_range": 0.05,
#                     "mind": 1,
#                     "memo": "first",
#                     "time_out": 10 * 60,  # 時間を過ぎたら解除するオーダー
#                     "order_edit_flag": 0,  # オーダーを変更したフラグ
#                     "order_id": 0,  # オーダーを発行した場合、オーダーIDを取得しておく
#                     "position_id": 0,  # オーダーがポジションした場合、ポジションIDを取得しておく（可能か・・？）
#                 }
#
#                 return {"f_order": f_order, "f_repeat":f_repeat_arr[0], "r_order": r_order, "r_repeat": r_repeat_arr[0],
#                         "info": info, "memo": 0, "res":0}
#             else:
#                 print(" 戻し幅NG[率,gap]", return_ratio, ",", latest_ans['gap'], "/", oldest_ans['gap']
#                       ," 開始位置", oldest_ans['oldest_price'], "count:", oldest_ans['count'], ",", latest_ans['count'],
#                       latest_ans['latest_time'])
#                 ans = {"res": -1, "remark": "戻し率NG"}
#                 return ans
#         else:
#             print("  行数未達")
#             ans = {"res": -1, "remark": "行数未達"}
#             return ans
#     else:
#         print("  同方向", oldest_ans['count'], latest_ans['count'], latest_ans['direction'], oldest_ans['direction'])
#         ans = {"res": -1, "remark": "同方向"}
#         return ans
#



def range_base(data_df, base_price):  # 引数 データ、基準価格
    """
    複雑。ある指定の価格（BasePrice）の周辺を、ふらふらしているかどうかを確認する。
    通貨回数等で確認している
    :param data_df: 確認したい範囲のデータフレーム
    :param base_price: 指定の価格
    :return:
    """
    # 各変数の設定等
    temp_data_df = data_df.head(50).copy()  # 範囲を指定してDFをコピーしておく（計算用）
    colname = "close"  # 現在のclose価格を基準価格する。
    if base_price == 999:  # 999が呼ばれた場合、データ内の最新の価格を利用する
        now_price = temp_data_df.head(1).iloc[-1][colname]  # 現在価格の取得
    else:  # base_priceが指定がある場合は、それを利用する
        now_price = base_price

    switch_flag = 0
    mnt_count = vly_count = sp_count = fin_row = fin_time = 0
    high = 0
    low = 999
    range_info_arr = []  # 結果格納用の変数（配列）
    # データフレームを過去方向に巡回し、基準価格を含む足をスタート、基準価格を含まなくなるとそれ以降を山(谷）、
    # 　　再度一度基準価格を含む足を発見したところを山(谷)の終了と考える。
    for index, item in temp_data_df.iterrows():
        if item['low'] <= now_price and now_price <= item['high']:  # 基準価格を含む足の場合
            if switch_flag == 1:
                # 山or谷からの切り替わり時（山谷情報を記録する）
                switch_flag = 0  # 同価格モードに切り替え
                res_dict = {"SameCount": sp_count, "MountCount": mnt_count, "High": high, "ValleyCount": vly_count,
                            "Low": low, "fin_row": fin_row, "fin": fin_time}
                range_info_arr.append(res_dict)
                mnt_count = vly_count = high = 0  # 各カウンターの初期化
                low = 999  # Low値のリセット
            # 共通処理
            fin_time = item['time_jp']
            fin_row = index
            sp_count += 1
            if item['inner_high'] > high:
                high = item['inner_high']
            if item['inner_low'] < low:
                low = item['inner_low']
        # 現価格を含まない場合、上か下かを判定する(山または谷に相当する部分。その際の、最高or最低価格も取得する)
        else:
            if switch_flag == 0:
                # 同価格の連続から、移行してきた場合(記録）
                switch_flag = 1  # 山谷モードに切り替え
                res_dict = {"SameCount": sp_count, "MountCount": mnt_count, "High": high, "ValleyCount": vly_count,
                            "Low": low, "fin_row": fin_row, "fin": fin_time}
                range_info_arr.append(res_dict)
                sp_count = high = 0  # 各カウンターの初期化
                low = 999
            # 共通処理
            fin_time = item['time_jp']
            fin_row = index
            if item[colname] < now_price:  # 現価格より低い価格の場合、谷としての情報を残す
                vly_count = vly_count + 1
                if item['inner_low'] < low:
                    low = item['inner_low']
            else:  # 現価格より高い場合、山としての情報を残す
                mnt_count = mnt_count + 1
                if item['inner_high'] > high:
                    high = item['inner_high']
    # print(range_info_arr)
    # 集計値の算出
    UpDown_count = 0
    res2 = []
    if len(range_info_arr) > 0:
        # 配列が０でなければ
        for index, item in enumerate(range_info_arr):
            if item['MountCount'] > 45 or item['ValleyCount'] > 45:
                # print(item['fin'],"範囲外")
                break
            else:
                res2.append(item)
                if item['MountCount'] > 0 or item['ValleyCount'] > 0:
                    UpDown_count += 1
    else:
        UpDown_count = 0
    ans_dict = {"MVcount": UpDown_count, "data": range_info_arr}
    return ans_dict


