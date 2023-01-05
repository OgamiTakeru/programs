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
    order_num = 2  # 極値調査の粒度  gl['p_order']  ⇒基本は３。元プログラムと同じ必要がある（従来Globalで統一＝引数で渡したいけど。。）
    fig = make_subplots(specs=[[{"secondary_y": True}]])  # 二軸の宣言
    # ローソクチャートを表示する
    graph_trace = go.Candlestick(x=mid_df["time_jp"], open=mid_df["open"], high=mid_df["high"],
                                 low=mid_df["low"], close=mid_df["close"], name="OHLC")
    fig.add_trace(graph_trace)
    #PeakValley情報をグラフ化する
    col_name = 'peak_' + str(order_num)
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df['peak_' + str(order_num)], mode="markers",
                               marker={"size": 10, "color": "red", "symbol": "circle"}, name="peak")
        fig.add_trace(add_graph)
    col_name = 'valley_' + str(order_num)
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df['valley_' + str(order_num)], mode="markers",
                               marker={"size": 10, "color": "blue", "symbol": "circle"}, name="valley")
        fig.add_trace(add_graph)
    # 移動平均線を表示する
    col_name = "ema_l"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], name=col_name)
        fig.add_trace(add_graph)
    col_name = "ema_s"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], name=col_name)
        fig.add_trace(add_graph)
    col_name = "cross_price"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name],  mode="markers",
                               marker={"size": 5, "color": "black", "symbol": "cross"}, name=col_name)
        fig.add_trace(add_graph)
    # ボリンジャーバンドを追加する
    col_name = "bb_upper"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], name=col_name)
        fig.add_trace(add_graph)
    col_name = "bb_lower"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], name=col_name)
        fig.add_trace(add_graph)
    col_name = "bb_middle"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], name=col_name)
        fig.add_trace(add_graph)

    #### ↑ここまでは基本的に必須。↓以下は基本的には任意
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
                               marker={"size": 10, "color": "red", "symbol": "triangle-up"}, name=col_name)
        fig.add_trace(add_graph, secondary_y=True)

    col_name = "test_target_price"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], mode="markers",
                               marker={"size": 10, "color": "red", "symbol": "diamond"}, name=col_name)
        fig.add_trace(add_graph)

    col_name = "conti"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], mode="markers",
                               marker={"size": 10, "color": "red", "symbol": "diamond"}, name=col_name)
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



    # col_name = "range_haba"
    # if col_name in mid_df:
    #     add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], mode="markers",
    #                            marker={"size": 10, "color": "Magenta", "symbol": "diamond"}, name=col_name)
    #     fig.add_trace(add_graph, secondary_y=True)


    col_name = "return_half_all"
    if col_name in mid_df:
        add_graph = go.Scatter(x=mid_df["time_jp"], y=mid_df[col_name], mode="markers",
                               marker={"size": 10, "color": "black", "symbol": "diamond"}, name=col_name)
        fig.add_trace(add_graph, secondary_y=True)

    fig.show()
    # 参考＜マーカーの種類＞
    # symbols = ('circle', 'circle-open', 'circle-dot', 'circle-open-dot','square', 'diamond', 'cross', 'triangle-up')


def str_to_time(str_time):
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
    :param data_df:
    :return:
    """
    # 中央値（Inner高値とInner低値の）の動きを確認、何連続で同じ方向に行っているかを確認する（植木算的に、３行の場合は２個）
    p_counter = m_counter = 0
    oldest_price = latest_price = 0
    counter = 0
    flag = 0  # ＋かマイナスかのフラグ（条件分岐）
    # カウントする
    for l in range(len(data_df)):
        if l <= len(data_df) - 2:  # 差分取得のため。－２のインデックスまで
            # 初回の場合
            if counter == 0:
                counter += 1
                if data_df.iloc[l]["middle_price_gap"] > 0:
                    flag = 1
                    # print("初回＋", data_df.iloc[l]["middle_price_gap"], data_df.iloc[l]["inner_high"], data_df.iloc[l]["time_jp"])
                    latest_price = data_df.iloc[l]["inner_high"]  # 最初のスタート値（上がっていくため、最高部分）
                    p_counter += 1
                else:
                    # print("初回－", data_df.iloc[l]["middle_price_gap"], data_df.iloc[l]["inner_low"], data_df.iloc[l]["time_jp"])
                    latest_price = data_df.iloc[l]["inner_low"]  # 最初のスタート値（下がっていくため、最低部分）
                    m_counter += 1
                    flag = -1
            # 初回以降
            else:
                counter += 1
                if flag == 1 and data_df.iloc[l]["middle_price_gap"] > 0:
                    # 初回がプラスで、今回もプラスの場合
                    p_counter += 1
                    oldest_price = data_df.iloc[l+1]["inner_low"] # ひとつ前の行の値になる事に注意
                    # print(" ■連続＋", p_counter, '回目', data_df.iloc[l]["middle_price_gap"], data_df.iloc[l+1]["inner_low"], data_df.iloc[l+1]["time_jp"])
                elif flag == 1 and data_df.iloc[l]["middle_price_gap"] <= 0:
                    # 初回がプラスで、今回もマイナスの場合
                    # print(" 連続＋途絶え", p_counter, "回目", data_df.iloc[l]["middle_price_gap"], data_df.iloc[l]["time_jp"])
                    flag = 0  # flag取り下げ（アンサーにもなる）
                    break
                elif flag == -1 and data_df.iloc[l]["middle_price_gap"] <= 0:
                    # 初回が－で、今回も－の場合
                    oldest_price = data_df.iloc[l+1]["inner_high"]  # ひとつ前の行の値になる事に注意
                    # print(" ■連続－", m_counter, '回目', data_df.iloc[l]["middle_price_gap"], data_df.iloc[l+1]["inner_high"], data_df.iloc[l+1]["time_jp"])
                    m_counter += 1
                elif flag == -1 and data_df.iloc[l]["middle_price_gap"] > 0:
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

    return({
        # "final_time": data_df.iloc[0]["time_jp"],
        # "final_close_price": data_df.iloc[0]["close"],
        "oldest_price": oldest_price,
        "latest_price": latest_price,
        "gap": round(abs(oldest_price - latest_price), 3),
        "middle_price": middle_price,
        "direction": ans,
        "count": ans_count,
        "data_size": len(data_df)
    })
    print(oldest_price, "-", latest_price, ans, ans_count)


def renzoku_gap_compare(oldest_ans, latest_ans, now_price):
    """

    :param oldest_ans:第一引数がOldestであること。直近部より前の部分が、どれだけ同一方向に進んでいるか。
    :param latest_ans:第二引数がLatestであること。直近部がどれだけ連続で同一方向に進んでいるか
    :param now_price: 途中で追加した機能（現在の価格を取得し、成り行きに近いようなオーダーを出す）　230105追加
    :return:
    """
    if latest_ans['direction'] != oldest_ans['direction']:  # 違う方向だった場合 (想定ケース）
        if latest_ans['count'] == latest_ans['data_size'] and oldest_ans['count'] >= 5:  # 行数確認(old区間はt直接指定！）
            # 戻しのパーセンテージを確認
            return_ratio = round((latest_ans['gap'] / oldest_ans['gap']) * 100, 3)
            info = {"return_ratio": return_ratio, "bunbo_gap": oldest_ans['gap']}  # 情報を保持しておく
            # 戻り基準と比較し、基準値以内(N%以下等）であれば、戻り不十分＝エントリーポイントとみなす
            if return_ratio < 40:
                return_flag = 1
            else:
                return_flag = 0

            # エントリーポイントを発見した場合の処理！
            if return_flag == 1:
                print(" ★両方満たし@gfunc", latest_ans['direction'], latest_ans['latest_price'], )
                if latest_ans['direction'] == 1:
                    # 折り返しがプラス方向（谷の形、思想の同方向）
                    target_price = oldest_ans['latest_price'] - 0.015  # 基本ボトム価格。－値でポジションしにくくなる方向。
                    lc_price = oldest_ans['middle_price']  # - 0.025  # ＋値は余裕度（ロスカしにくくなる）、マイナス値は早期LC
                    for_order = {
                        "target_price": target_price,  # 基本はボトム価格。－値でポジションしにくくなる
                        "lc_price": lc_price,  # 参考情報（渡し先では使わない）
                        "lc_range": round(lc_price - target_price, 3),  # 谷形成からの売りポジ。LC価(上がり）>target価
                        "tp_range": 0.1,
                        "type": "STOP",
                        "trail_range": 0.05,
                        "direction": -1,  # 購入方向（１は買い、-1は売り）
                        "mind": 1  # 思想方向（１は思想通り順張り。-1は逆張り方向）
                    }
                    # 折り返しがプラス方向（谷の形、思想と【逆】方向！）
                    target_price_r = latest_ans['latest_price']  # 基本はハーフ値。＋値でポジションしにくくなる
                    target_price_r = now_price + 0.01  # ＋値でポジションしにくくなる
                    # ↑ほぼ成り行きレベルのオーダーを入れたい（数秒の差で、すでにロスカ価格超えているケースあるため、再度価格取得）
                    lc_price_r = latest_ans['oldest_price'] + 0.01  # ー値は余裕度（ロスカしにくくなる）、＋値は早期LC
                    #  ↑谷形状で、上(思想と逆)に行くポジションの場合、TargetがLC価格よりも上にある
                    for_order_r = {
                        "target_price": target_price_r,  # 基本はハーフ値。＋値でポジションしにくくなる
                        "lc_price": lc_price_r,  # 参考情報（渡し先では使わない）
                        "lc_range": 0.02,  # round(target_price_r - lc_price_r, 3),  # 谷形成からの買い。LC価(下）<target価
                        "tp_range": 0.03,  # 思想と逆（逆張り）は少し狭い目で。。
                        "type": "STOP",
                        "trail_range": 0.08,
                        "direction": 1,  # 購入方向（１は買い、-1は売り）
                        "mind": -1  # 思想方向（１は思想通り順張り。-1は逆張り方向）
                    }

                elif latest_ans['direction'] == -1:
                    # 折り返しがマイナス方向（山の形、思想と同方向）
                    target_price = oldest_ans['latest_price'] + 0.015  # 基本ピーク価格。＋値でポジションしにくくなる方向。
                    lc_price = oldest_ans['middle_price']  # + 0.025  # ー値は余裕度（ロスカしにくくなる）、＋値は早期LC
                    for_order = {
                        "target_price": target_price,  # 基本ピーク価格。＋値でポジションしにくくなる方向。
                        "lc_price": lc_price,  # 参考情報（渡し先では使わない）
                        "tp_range": 0.1,
                        "lc_range": round(target_price - lc_price, 3),  # 山形成からの買いポジ。LC価(下げ）< target価
                        "type": "STOP",
                        "trail_range": 0.08,
                        "direction": 1,  # 購入方向（１は買い、-1は売り）
                        "mind": 1  # 思想方向（１は思想通り順張り。-1は逆張り方向）
                    }

                    # 折り返しがプラス方向（山の形、思想と【逆】方向）！
                    target_price_r = latest_ans['latest_price']  # 初期ミドル価格。－値でポジションしにくくなる方向。
                    target_price_r = now_price - 0.01  # －値でポジションしにくくなる。
                    # ↑ほぼ成り行きレベルのオーダーを入れたい（数秒の差で、すでにロスカ価格超えているケースあるため、再度価格取得）
                    lc_price_r = latest_ans['oldest_price'] - 0.01  # - 0.025  # ＋値は余裕度（ロスカしにくくなる）、マイナス値は早期LC
                    for_order_r = {
                        "target_price": target_price_r,  # 基本ミドル価格。－値でポジションしにくくなる方向。
                        "lc_price": lc_price_r,  # 参考情報（渡し先では使わない）
                        "tp_range": 0.03,  # 思想と逆（逆張り）は少し狭い目で。。
                        "lc_range": 0.02,  # round(lc_price_r - target_price_r, 3),  # 山形成からの売り。LC価(上）> target価
                        "type": "STOP",
                        "trail_range": 0.08,
                        "direction": -1,  # 購入方向（１は買い、-1は売り）
                        "mind": -1  # 思想方向（１は思想通り順張り。-1は逆張り方向）
                    }
                    #  ↑谷形状で、上(思想と逆)に行くポジションの場合、TargetがLC価格よりも上にある

                print(" @gfuncEND", for_order, for_order_r)
                return {"forward": for_order, "reverse": for_order_r, "info": info}
            else:
                print(" 戻し幅満たさず（カウントは達成）[率,gap]", return_ratio, oldest_ans['gap'])
                # print(" 戻し幅をみたさず", latest_ans['direction'], latest_ans['latest_price'])
                #  これ、意外と使える可能性も、、、
                # for_order = {"direction": 0}
                # for_order_r = {"direction": 0}
                return 0
        else:
            # print(" 行数未達")
            return 0
    else:
        # print(" 別方向（折り返し）", latest_ans['count'], oldest_ans['count'])
        return 0



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


