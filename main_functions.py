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
    for l in range(len(data_df)):
        if l <= len(data_df) - 2:  # 差分取得のため。－２のインデックスまで
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
                else: # 通常（従来の6:3等、２以上の判定を使う方法の場合）
                    # print("g", len(data_df))
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

    # ３個(or２個）の場合、ローソクの関係性を求める
    # ３個の場合、３パターンのいずれか。谷の場合(折り返し部が＋）、古い順に1,1,1/1,-1,1/1,1,-1
    if len(data_df) == 3:
        if ans==1:  # プラスの連荘＝谷の場合　（折り返し部のみの話）
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
        pattern_comment = "何もなし"


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
        "pattern": pattern,
        "pattern_comment": pattern_comment,
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
        print(latest_ans['count'],latest_ans['data_size'])
        if latest_ans['count'] == latest_ans['data_size'] and oldest_ans['count'] >= 4:  # 行数確認(old区間はt直接指定！）
            # 戻しのパーセンテージを確認
            return_ratio = round((latest_ans['gap'] / oldest_ans['gap']) * 100, 3)
            info = {"return_ratio": return_ratio, "bunbo_gap": oldest_ans['gap']}  # 情報を保持しておく
            # 戻り基準と比較し、基準値以内(N%以下等）であれば、戻り不十分＝エントリーポイントとみなす
            max_return_ratio = 45
            if return_ratio <= max_return_ratio:
                return_flag = 1
            else:
                return_flag = 0

            if return_flag == 1:
                print(" ★両方満たし@gfunc", latest_ans['direction'], latest_ans['latest_price'], return_ratio )
                # 以下谷方向の式の負号が元になっているので注意。(谷方向[直近3↑]でdirection=1、山方向[直近3↓]でdirection=-1)

                # ■順思想（谷方向基準[売りポジを取る]の式）directionで負号調整あり
                direction_l = latest_ans['direction']  # 谷の場合１、山の場合-1　これoldestの方が直観的だったなぁ。
                base_adjuster = 0.06
                if direction_l == 1:  # 谷形状 底の髭より少し余裕を持った位置に！（順に行くときは、ガッツリ行くと信じて）
                    print("谷", oldest_ans['inner_low_price'] - oldest_ans['low_price'])
                    if oldest_ans['inner_low_price'] - oldest_ans['low_price'] > base_adjuster:
                        # 髭が短い過ぎる場合、アジャスターに最低限の0.15を設定
                        adjuster = oldest_ans['inner_low_price'] - oldest_ans['low_price']
                    else:
                        adjuster = base_adjuster
                    # adjuster = 0.15
                    temp_entry = oldest_ans['inner_low_price'] - adjuster  # adjusterをマイナスし、ポジションしにくくする
                elif direction_l == -1:  # 山形状
                    print("山", oldest_ans['high_price'] - oldest_ans['inner_high_price'])
                    if oldest_ans['high_price'] - oldest_ans['inner_high_price'] >base_adjuster:
                        # 髭が短い過ぎる場合、アジャスターに最低限の0.15を設定
                        adjuster = oldest_ans['high_price'] - oldest_ans['inner_high_price']
                    else:
                        adjuster = base_adjuster
                    # adjuster = 0.15
                    temp_entry = oldest_ans['inner_high_price'] + adjuster
                f_entry_price = round(temp_entry, 3)
                # f_entry_price = oldest_ans['low_price'] if direction_l == 1 else oldest_ans['high_price']  # ★
                f_lc_price = latest_ans['latest_price']  # 短めのロスカ（直近価格まで程度にする 短すぎる場合、どうしよう）
                f_lc_range = round(abs(f_entry_price - f_lc_price), 3)
                f_tp_price = oldest_ans['middle_price']  # 今後使うかも？
                f_tp_price = 0.15 if f_tp_price > 0.15 else f_tp_price  #（最大値撤廃時以外、コメントアウト不要）ロスカの最大値を調整する
                f_tp_range = 0.05 # round(abs(f_entry_price - f_lc_price), 3)  # ★直接指定でも可(direction関係しない）
                f_trail_range = 0
                remark = "20以下順強"

                # ■逆思想（谷方向[買いポジを取る]基準の式。directionで負号調整あり）
                if direction_l == 1:  # 谷形状
                    temp_entry = oldest_ans['low_price']
                elif direction_l == -1:  # 山形状
                    temp_entry = oldest_ans['high_price']
                r_entry_price = temp_entry  # 数字部プラス値でエントリーしにくい方向
                # r_entry_price = oldest_ans['latest_price']
                r_lc_price = round(0.01 * direction_l + f_entry_price, 3)  # 数字部＋値は早期LC 順思想のPrice取り入れ
                # r_lc_price = oldest_ans['low_price'] if direction_l == 1 else oldest_ans['high_price']  # high low 切替
                r_lc_range = round(abs(r_entry_price - r_lc_price), 3)  # 順思想の時の髭の長さ寄りも少し短め（＝最低0.15より少し短め）
                r_tp_price = oldest_ans['oldest_price']  # high low 切替
                r_tp_range = round(abs(r_entry_price - r_tp_price), 3)  # 直接指定でも可(direction関係しない）
                # r_tp_range = 0.03  # 0.15 if r_tp_range > 0.15 else r_tp_range
                r_trail_range = 0

                # 結果の格納と表示
                for_order = {
                    "adjuster": round(adjuster, 3),
                    "price": f_entry_price,  # 注文で直接利用
                    "lc_price": f_lc_price,  # 参考情報
                    "lc_range": f_lc_range,  # 注文で直接利用
                    "tp_range": f_tp_range,  # 注文で直接利用
                    "type": "STOP",  # 注文で直接利用
                    "tr_range": 0,  # f_trail_range,  # 注文を直接利用
                    "ask_bid": -1 * direction_l,  # 注文で直接利用。購入方向。１は買(山の順思想)、-1は売(谷の順思想[基準])
                    "mind": 1  # 思想方向（１は思想通り順張り。-1は逆張り方向）
                }
                for_order_r = {
                    "adjuster": adjuster,
                    "price": r_entry_price,  # 基本はハーフ値。＋値でポジションしにくくなる
                    "lc_price": r_lc_price,  # 参考情報（渡し先では使わない）
                    "lc_range": r_lc_range,  # round(target_price_r - lc_price_r, 3),  # 谷形成からの買い。LC価(下）<target価
                    "tp_range": r_tp_range,  # 思想と逆（逆張り）は少し狭い目で。。
                    "type": "LIMIT",  # ★逆思想の取り方を変えると、ここはLIMITだ！
                    "tr_range": r_trail_range,
                    "ask_bid": 1 * direction_l,  # 購入方向。１は買い(谷の逆思想[式基準])、-1は売り(山の逆思想)
                    "mind": -1  # 思想方向（１は思想通り順張り。-1は逆張り方向）
                }
                print(" @gfuncEND", for_order, for_order_r)
                return {"forward": for_order, "reverse": for_order_r, "info": info}
            else:
                print(" 戻し幅NG[率,gap]", return_ratio, ",", latest_ans['gap'], "/", oldest_ans['gap']
                      ," 開始位置", oldest_ans['oldest_price'], "count:", oldest_ans['count'], ",", latest_ans['count'],
                      latest_ans['latest_time'])
                # print(" 戻し幅をみたさず", latest_ans['direction'], latest_ans['latest_price'])
                return 0
        else:
            print("  行数未達")
            return 0
    else:
        print("  同方向", oldest_ans['count'], latest_ans['count'], latest_ans['direction'], oldest_ans['direction'])
        return 0


# ## こちらは最大値算出用！””””
# def renzoku_gap_compare(oldest_ans, latest_ans, now_price):
#     """
#
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
#             max_return_ratio = 40
#             if return_ratio <= max_return_ratio:
#                 return_flag = 1
#             else:
#                 return_flag = 0
#
#             ####   最大値算出用
#             if return_flag == 1:
#                 print(" ★両方満たし@gfunc", latest_ans['direction'], latest_ans['latest_price'], return_ratio )
#                 # 以下谷方向の式の負号が元になっているので注意。(谷方向[直近3↑]でdirection=1、山方向[直近3↓]でdirection=-1)
#                 # ■順思想（谷方向基準[売りポジを取る]の式）directionで負号調整あり
#                 direction_l = latest_ans['direction']  # 谷の場合１、山の場合-1　これoldestの方が直観的だったなぁ。。
#                 f_entry_price = round(oldest_ans['latest_price'] - 0.015 * direction_l, 3)  # 数字＋値でエントリーしにくい方向
#                 # f_entry_price = oldest_ans['low_price'] if direction_l == 1 else oldest_ans['high_price']  # ★
#                 f_lc_price = oldest_ans['middle_price']  # 初期思想では、ミドルまで折り返し(direction関係しない）
#                 f_lc_range = 0.07  # round(abs(f_entry_price - f_lc_price), 3)  # ★直接指定0.09程度でも可(direction関係無)
#                 f_tp_price = oldest_ans['middle_price']  # 今後使うかも？
#                 f_tp_price = 0.15 if f_tp_price > 0.15 else f_tp_price  #（最大値撤廃時以外、コメントアウト不要）ロスカの最大値を調整する
#                 f_tp_range = 0.09  # round(abs(f_entry_price - f_tp_price), 3)  # ★直接指定でも可(direction関係しない）
#                 f_trail_range = 0
#
#                 # ■逆思想（谷方向[買いポジを取る]基準の式。directionで負号調整あり）
#                 r_entry_price = round(0.017 * direction_l + now_price, 3)  # 数字部プラス値でエントリーしにくい方向
#                 # r_entry_price = temp_entry  # 数字部プラス値でエントリーしにくい方向
#                 r_lc_price = round(0.01 * direction_l + latest_ans['oldest_price'], 3)  # 数字部＋値は早期LC
#                 # r_lc_price = oldest_ans['low_price'] if direction_l == 1 else oldest_ans['high_price']  # high low 切替
#                 r_lc_range = 0.04  # round(abs(r_entry_price - r_lc_price), 3)  # ★直接指定でも可(direction関係しない）
#                 r_tp_price = oldest_ans['high_price'] if direction_l == 1 else oldest_ans['low_price']  # high low 切替
#                 r_tp_range = round(abs(r_entry_price - r_tp_price), 3)  # 直接指定でも可(direction関係しない）
#                 r_tp_range = 0.04  # 0.15 if r_tp_range > 0.15 else r_tp_range
#                 r_trail_range = 0
#
#                 # 結果の格納と表示
#                 for_order = {
#                     "target_price": f_entry_price,  # 基本はボトム価格。－値でポジションしにくくなる
#                     "lc_price": f_lc_price,  # 参考情報（渡し先では使わない）
#                     "lc_range": f_lc_range,  # 谷形成からの売りポジ。LC価(上がり）>target価
#                     "tp_range": f_tp_range,
#                     "type": "STOP",
#                     "trail_range": f_trail_range,
#                     "direction": -1 * direction_l,  # 購入方向。１は買い(山の順思想)、-1は売り(谷の順思想[式基準])
#                     "mind": 1  # 思想方向（１は思想通り順張り。-1は逆張り方向）
#                 }
#                 for_order_r = {
#                     "target_price": r_entry_price,  # 基本はハーフ値。＋値でポジションしにくくなる
#                     "lc_price": r_lc_price,  # 参考情報（渡し先では使わない）
#                     "lc_range": r_lc_range,  # round(target_price_r - lc_price_r, 3),  # 谷形成からの買い。LC価(下）<target価
#                     "tp_range": r_tp_range,  # 思想と逆（逆張り）は少し狭い目で。。
#                     "type": "STOP",
#                     "trail_range": r_trail_range,
#                     "direction": 1 * direction_l,  # 購入方向。１は買い(谷の逆思想[式基準])、-1は売り(山の逆思想)
#                     "mind": -1  # 思想方向（１は思想通り順張り。-1は逆張り方向）
#                 }
#                 print(" @gfuncEND", for_order, for_order_r)
#                 return {"forward": for_order, "reverse": for_order_r, "info": info}
#             else:
#                 print(" 戻し幅NG[率,gap]", return_ratio, ",", latest_ans['gap'], "/", oldest_ans['gap']
#                       ," 開始位置", oldest_ans['oldest_price'], "count:", oldest_ans['count'], ",", latest_ans['count'],
#                       latest_ans['latest_time'])
#                 # print(" 戻し幅をみたさず", latest_ans['direction'], latest_ans['latest_price'])
#                 return 0
#         else:
#             # print(" 行数未達")
#             return 0
#     else:
#         # print(" 別方向（折り返し）", latest_ans['count'], oldest_ans['count'])
#         return 0


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


