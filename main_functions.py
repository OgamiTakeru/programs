import requests
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
    引数のデータフレームを先頭(０行目)から確認し、何行連続で同じ方向に進んでいるかを確認。（ローソク方向ではない！）
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
        "oldest_price": oldest_price,
        "latest_price": latest_price,
        "middle_price": middle_price,
        "direction": ans,
        "count": ans_count,
        "data_size": len(data_df)
    })
    print(oldest_price, "-", latest_price, ans, ans_count)


def renzoku_gap_compare(oldest_ans, latest_ans):
    """

    :param oldest_ans:
    :param latest_ans:
    :return:
    """
    if latest_ans['direction'] != oldest_ans['direction']:  # 同違う方向だった場合
        if latest_ans['count'] == latest_ans['data_size'] and oldest_ans['count'] >= 5:  # 行数確認(old区間はt直接指定！）
            # 戻しの度合いを確認（長い方の移動幅の最大３分の２以内の戻しであるかを確認
            # 戻し量の設定（old区間移動量の、３分の２戻しの場合、partition_ratio=3 , return_ratio=2と設定）
            partition_ratio = 2
            return_ratio = 1
            # 戻り量判定の基準作成する（分母に相当する部分）
            unit = abs((oldest_ans['oldest_price'] - oldest_ans['latest_price']) / partition_ratio)
            # 戻り基準価格を求め、比較を行う
            if oldest_ans['direction'] == 1:  # oldが上り方向の場合（山形状）
                # 折り返し価格を計算（山形状の場合、この価格以上で戻り範囲が収まっていれば）
                border_line = round(latest_ans['oldest_price'] - (unit * return_ratio), 3)
                if latest_ans['latest_price'] > border_line:
                    return_flag = 1  # 折り返しが中途半端な場合
                else:
                    return_flag = 0  # 幅が未完成の場合
            elif oldest_ans['direction'] == -1:  # oldが下り方向の場合（谷形状）
                # 折り返し価格を計算（山形状の場合、この価格以上で戻り範囲が収まっていれば）
                border_line = round(latest_ans['oldest_price'] + (unit * return_ratio), 3)
                if latest_ans['latest_price'] < border_line:
                    return_flag = 1  # 折り返しが中途半端な場合
                else:
                    return_flag = 0  # 幅が未完成の場合

            if return_flag == 1:
                print(" ★両方満たし", latest_ans['direction'], latest_ans['latest_price'], border_line)
                if latest_ans['direction'] == 1:
                    # 折り返しがプラス方向（谷の形)、middle_priceでショート！　ロスカはlatestにする？
                    target_price = oldest_ans['latest_price']
                    lc_price = oldest_ans['middle_price']
                    lc_pips = round(lc_price - target_price, 3)  # 谷形状で、下に行くポジションの場合、LC価格がTargetよりも上にある
                    order = "谷TGT:" + str(oldest_ans['latest_price']) + "ロスカ" + str(oldest_ans['middle_price']) + "," + str(lc_pips)
                    # ORDER
                    # 折り返しがプラス方向（谷の形)、middle_priceでショート！（逆方向）！
                    target_price_r = oldest_ans['middle_price']
                    lc_price_r = latest_ans['oldest_price']
                    lc_pips_r = round(target_price_r - lc_price_r, 3)  # 谷形状で、上(思想と逆)に行くポジションの場合、TargetがLC価格よりも上にある
                    # #　注文実施(関数化したため内容のみ返却）
                    for_order = {"target_price": target_price, "tp_range": 0.1, "lc_range": lc_pips, "type": "STOP",
                                 "trail_range": 0.08, "direction": -1}
                    for_order_r = {"target_price": target_price_r, "tp_range": 0.1, "lc_range": lc_pips_r,
                                   "type": "STOP", "trail_range": 0.08, "direction": 1}
                    # order_res = oa.OrderCreate_exe(10000, -1, target_price, 0.1, lc_pips, "STOP", 0.08, "remark")  # 順思想（順張・現より低い位置に注文入れたい）
                    # order_res_r = oa.OrderCreate_exe(10000, 1, target_price_r, 0.1, lc_pips_r, "STOP", 0.08, "remark")  # 逆思想（順張・現より高い位置に注文入れたい）
                elif latest_ans['direction'] == -1:
                    # 折り返しがマイナス方向（山の形)、middle_priceでロング！　ロスカはLatestにする？
                    target_price = oldest_ans['latest_price']
                    lc_price = oldest_ans['middle_price']
                    lc_pips = round(target_price - lc_price, 3)  # 山形状で、上に行くポジションの場合、Target価格がLC価格より上にある
                    order = "山TGT:" + str(oldest_ans['latest_price']) + "ロスカ" + str(oldest_ans['middle_price']) + "," + str(lc_pips)
                    # order
                    # 折り返しがプラス方向（山の形)、middle_priceでショート！（逆方向）！
                    target_price_r = oldest_ans['middle_price']
                    lc_price_r = latest_ans['oldest_price']
                    lc_pips_r = round(lc_price_r - target_price_r, 3)  # 山形状で、下(思想と逆)に行くポジションの場合、LC価格がTargetよりも上にある
                    # 注文実施(関数化したため内容のみ返却）
                    for_order = {"target_price": target_price, "tp_range": 0.1, "lc_range": lc_pips, "type": "STOP",
                                 "trail_range": 0.08, "direction": 1}
                    for_order_r = {"target_price": target_price_r, "tp_range": 0.1, "lc_range": lc_pips_r,
                                   "type": "STOP", "trail_range": 0.08, "direction": 1}
                    # order_res = oa.OrderCreate_exe(10000, 1, target_price, 0.05, lc_pips, "STOP", 0, "remark")  # 順思想（順張・現より低い位置に注文入れたい）
                    # order_res_r = oa.OrderCreate_exe(10000, -1, target_price_r, 0.05, lc_pips_r, "STOP", 0, "remark")  #逆思想（順張り・現より高い位置に注文入れたい）
            else:
                print(" 幅のみみたさず", latest_ans['direction'], latest_ans['latest_price'])
                for_order = {"direction": 0}
                for_order_r = {"direction": 0}
            return {"forward": for_order, "reverse":for_order_r}
        else:
            print(" 行数未達")
            return 0
    else:
        print(" 別方向（折り返し）", latest_ans['count'], oldest_ans['count'])
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


