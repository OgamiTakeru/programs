import threading  # 定時実行用
import time, datetime  # dateutil.parser, pytz  # 日付関係
import sys
import requests
import programs.tokens as tk
# 自作ファイルインポート
import programs.oanda_class as oanda_class


def swith_order_exe(units, ask_bid, price, tp_range, lc_range, meth, remark):
    global skip_counter
    global skip_flag
    tp_price = str(round(price + (tp_range * ask_bid), 3))
    lc_price = str(round(price - (lc_range * ask_bid), 3))
    t=remark["time"]
    p_time = datetime.datetime(int(t[0:4]), int(t[5:7]), int(t[8:10]), int(t[11:13]), int(t[14:16]),int(t[17:19]))
    print(p_time)
    print(remark['time'])
    #                            int(t[17:19]))
    # オーダーを同様の形式で練習と本番両方に出せるように切り替える関数
    global gl
    global stocks
    # フラグのアップ
    gl["test_posi"] = 1
    # ログの取得
    print("★★position")
    logs = {
        "units":units,
        "dirction": ask_bid,
        "price": price,
        "tp": tp_range,
        "lc": lc_range,
        "meth": meth,
        "time": remark["time_jp"],
        "remark":remark["remark"]
    }
    posi_data = {
        "time":remark["time_jp"],
        "time_from":remark['time'],
        "tp_price": tp_price,
        "lc_price": lc_price,
    }
    res = close_position(posi_data)
    skip_counter = int(round(res['index']/12,0)+1)
    skip_flag = 1
    print(round(res['index']/12,0)+1)
    print(logs)
    print("test")


#
#
# def switch_CRCDO_exe(p_id, data):
#     # オーダーを同様の形式で練習と本番両方に出せるように切り替える関数
#     global gl
#     # 本番環境＋練習環境で実施するとき
#     if gl["p_l_switch"] == 1:
#         print("       BothCRCDO")
#         oa.TradeCRCDO_exe(p_id, data)
#         oap.TradeCRCDO_exe(p_id, data)
#     # 練習環境のみで実施するとき(情報取得は本番環境であるoaクラスで処理を行う）
#     else:
#         print("       SingleCRCDO")
#         oap.TradeCRCDO_exe(p_id, data)
#
#
# def switch_close_exe(p_id, nones, remark):
#     # オーダーを同様の形式で練習と本番両方に出せるように切り替える関数
#     global gl
#     # 本番環境＋練習環境で実施するとき
#     if gl["p_l_switch"] == 1:
#         print("       BothCancel")
#         oa.TradeClose_exe(p_id, None, "cancel")
#         oap.TradeClose_exe(p_id, None, "cancel")
#     # 練習環境のみで実施するとき(情報取得は本番環境であるoaクラスで処理を行う）
#     else:
#         print("       SingleCancel")
#         oa.TradeClose_exe(p_id, None, "cancel")
#
#
def main_function(mid_df):
    global gl
    # ポジション有、かつ、時間的な制限を解除した場合、ポジション検討へ
    if gl['test_posi'] == 0: # and datetime.datetime.now() >= gl["latest_get"] + datetime.timedelta(minutes=3):
        make_position(mid_df)
    # elif len(oa.OpenTrades_exe()) == 0 and datetime.datetime.now() < gl["latest_get"] + datetime.timedelta(minutes=3):
    #     print("△ロスカ後待機時間", gl['now_hms'], "待機目標⇒", gl["latest_get"] + datetime.timedelta(minutes=4))
    else:
        pass
        # close_position()


def make_position_jd(ins_range, ans):
    # 今度、上がるか下がるかの一つの要素の計算を行う
    # 最初がポイントをチェックする（中央の場合は除外、それ以外はそこまでのカウントを取得）ここでのデータは「日時降順」が基準。
    if ans[0]["ans"] == 1 or ans[0]["ans"] == -1:
        # (1)直前のポイントがBB、かつ、BB超えが３連続以上であるかを確認する（３連続の場合は、対象）
        counter = 0
        jd = first = ans[0]["count_inc_me"]
        for item in ans:
            if (item["ans"] == -1 or item["ans"] == 1) and jd == item["count_inc_me"]:
                counter += 1
                jd = int(item["count_inc_me"]) + 1  # 一つ先のindexを入れておく（連番か確認用）
                last = int(item["count_inc_me"])  # ポイント連続の最後
            else:
                break
        bb_jd_df = ins_range[ans[0]["count_inc_me"] - 1:last]  # 途中経過（行数を求めるために利用するだけ）
        # 直前のポイントが2連続以上の場合
        if len(bb_jd_df) >= 2:
            # 　(2)下か上かで基準価格の取得、比較方法が異なる
            end_of_bb = ans[0]["count_inc_me"]
            target_df = ins_range[:end_of_bb - 1]  # 個々の動きが肝心なデータフレーム
            print("割合調査対象", target_df)
            # 下の場合
            count = 1
            nots = 0
            if ans[0]["ans"] == -1:  # もともとitem['ans'] == -1 だったけど、おかしいくない？？
                jd_base_price = bb_jd_df.head(1).iloc[-1]["low"]
                print("　　　　-1BB")
                for index, data in target_df.iterrows():
                    if float(data["close"]) > jd_base_price:
                        count += 1  # 戻し戻し (この一時戻しが多ければ、更に順に行く！）
                    else:
                        nots += 1  # 順方向
            elif ans[0]["ans"] == 1:
                jd_base_price = bb_jd_df.head(1).iloc[-1]["high"]
                print("　　　　BB1")
                for index, data in target_df.iterrows():
                    if float(data["close"]) < jd_base_price:
                        count += 1  # 戻し (こっちが多ければ、更に順に行く！）
                    else:
                        nots += 1  # 順方向
            else:
                jd_base_price = 0
                print("   ★★何か変なことが起きている(BBoverなのに、中間？）", item[ans])
            # 以上の情報から折り返し率を求める
            print(bb_jd_df)

            pm_jd = round(nots / (count + nots), 3)  # この値が小さい(0.2以下）の場合、急な反転を意味し、直後に更に落ちると推定
            print("　　　　", jd_base_price)
            print("　　　　", count, nots, pm_jd)

        else:
            pm_jd = -1
            print("　　　　2連未満(-1)", bb_jd_df)
    else:
        pm_jd = -2
        print("　　　　直前は中間でした(-2))")
    return pm_jd



def make_position_latestpoint(ins_range):
    # 与えられたDataTable（下に行けば行くほど最新のDataTalbe＝取った状態）から、直近のポイントを検索してDictで返却する
    # 与えられるDataFrameは１行目から探索の対象。
    ins_range = ins_range.reset_index()  # indexを再振り分け（降順にして受け取る関係で、インデックスがおかしい）
    # print(ins_range)
    # 配列の準備
    res_arr = []
    # 1 ループ準備
    body_total = count = m_body_count = p_body_count = timing = 0
    # 探索開始
    for index, data in ins_range.iterrows():
        # ①ポイントまでの情報を取得する
        body_total += float(data['body_abs'])
        count += 1
        if data['body'] < 0:
            m_body_count += 1
        elif data['body'] > 0:
            p_body_count += 1
        # ②ポイントを探索。BB上超え、BB下抜け、中央マタギがある場合、記録を取る。
        # print(data["time_jp"], data["bb_over_ratio"], data["bb_under_ratio"])
        if float(data["high"]) > float(data["bb_upper"]) or float(data["low"]) < float(data["bb_lower"]) or data[
            "low"] < data["bb_middle"] < data["high"]:
            timing = data["time_jp"]
            # 過去にBB上超えている場合
            if float(data["high"]) > float(data["bb_upper"]):
                ans = 1
                ans_r = "BBover"  # 1
                lower_price = float(data["bb_lower"])
                upper_price = float(data["bb_upper"])  # main
                middle_price = float(data["bb_middle"])
            # 過去にBB下を超えている場合
            elif float(data["low"]) < float(data["bb_lower"]):
                ans = -1
                ans_r = "BBlower"  # -1
                lower_price = float(data["bb_lower"])  # main
                upper_price = float(data["bb_upper"])
                middle_price = float(data["bb_middle"])
            # 過去に中央を超えている場合
            elif float(data["low"]) < float(data["bb_middle"]) < float(data["high"]):
                ans = 99
                ans_r = "middle"  # 99
                lower_price = float(data["bb_lower"])
                upper_price = float(data["bb_upper"])
                middle_price = float(data["bb_middle"])
            # 条件のいずれかを満たしているので、Break
            res = {
                "ans": ans,
                "ans_r": ans_r,
                "body_total": round(body_total, 3),
                "timing": timing,
                "upper_price": round(upper_price, 3),
                "lower_price": round(lower_price, 3),
                "middle_price": round(middle_price, 3),
                "high_price": round(data["high"], 3),
                "low_price": round(data["low"], 3),
                "count_inc_me": count,
                "m_body_count": m_body_count,
                "p_body_count": p_body_count
            }
            res_arr.append(res)
            # break  # 一つポイントを発見したらループを抜ける
    else:
        # 全てに当てはまらないとき
        pass

    # 空の場合は、最低限のダミーを入れておく？
    if len(res_arr) == 0:
        res = {
            "count_inc_me": -1,
            "ans":"test",
            "timing":"timing"
        }
        res_arr.append(res)

    # 返却する
    return res_arr


def make_position(mid_df):
    global skip_flag
    global skip_counter
    now_index = 0  # 途中までやった時
    for index, data in mid_df.iterrows():
        if skip_flag == 0:
            print(data['time_jp'])
            # ■現在価格を取得する
            now_price_bid_p = data['close']

            # ■売買用情報の取得.算出　(最初の方はBBは空欄であるので注意が必要）
            recent_df = mid_df[index-5:index]  # 自分から見て５行前まで参照（自分自身は含まない）

            recent_range = round(recent_df['bb_upper'].mean() - recent_df['bb_lower'].mean(), 3)
            print("      BB幅平均", recent_df['bb_upper'].mean(), recent_df['bb_lower'].mean())
            if recent_range < 0.05:
                range_str = "[極小0.05未満 " + str(round(recent_range, 3)) + "]"
                adj_r = gl['adj3']  # Tp,LCの幅の調整
            elif 0.05 <= recent_range < 0.1:
                range_str = "[中0.05-0.1　@×0.7 " + str(round(recent_range, 3)) + "]"
                adj_r = gl['adj2']
            elif 0.1 <= recent_range < 0.2:
                range_str = "[大0.1-0.2　@×1 " + str(round(recent_range, 3)) + "]"
                adj_r = gl['adj']
            else:
                range_str = "無"
                adj_r = 1
            print("   ", range_str, adj_r, recent_range)


            # ■現在のローソクがどんな状況にあるかを判断する（現状をnow_lに格納）　　testデータ用
            now_l = "異常なことが・？"
            ld = mid_df.tail(1)
            ld = data  # test用！！これが対象となる
            # 大分類①　BB上限を跨いでいる場合
            if float(ld["low"]) <= float(ld["bb_upper"]) <= float(ld["high"]):
                # 小分類①　赤か青か
                if float(ld["body"]) > 0:
                    now_l = 10
                    print("    10")
                elif float(ld["body"]) < 0:
                    now_l = 11
                    print("    11")
            # 大分類②　BB下限を跨いでいる場合
            elif float(ld["low"]) <= float(ld["bb_lower"]) <= float(ld["high"]):
                # 小分類①　赤か青か
                if float(ld["body"]) > 0:
                    now_l = -10
                    print("    -10")
                elif float(ld["body"]) < 0:
                    now_l = -11
                    print("    -11")
            # 大分類③　BB中央を跨いでいる場合
            elif float(ld["low"]) < float(ld["bb_middle"]) < float(ld["high"]):
                # 小分類①　赤か青か
                if float(ld["body"]) > 0:
                    now_l = 20
                    print("    20")
                elif float(ld["body"]) < 0:
                    now_l = 21
                    print("    21")
            # 大分類④　宙に浮いている場合
            else:
                # 小分類　上側か下側か
                if float(ld["bb_middle"]) < float(ld["close"]) < float(ld['bb_upper']):  # 中央はnow_price_middle
                    now_l = 30  # 上側
                    print("    30")
                elif float(ld["bb_middle"]) > float(ld["close"]) > float(ld['bb_lower']):
                    now_l = 31  # 下側
                    print("    30")
                else:
                    now_l = 99999
                    print("    999")
            print("  　　現在", now_l, gl['now_hms'])


            # ■過去のローソクと比べてポジション可否の判定する
            inspect_range = 20
            ins_range = mid_df[index - 6:index].sort_index(ascending=False)  # 自身を含まない直前20行データ
            temp_ans = make_position_latestpoint(ins_range)
            print(temp_ans)
            # パターン①　宙に浮いている場合、何分間その状態が継続しているかを判定する（上）
            if now_l == 30:
                # mid_df[index - 5:index]
                # inspect_range = 20
                # ins_range = mid_df[index - 5:index].sort_index(ascending=False)  # 自身を含まない直前20行データ
                # temp_ans = make_position_latestpoint(ins_range)
                if temp_ans[0]["count_inc_me"] >= gl["wait_range"]:
                    print("  　　★中間上")
                    # 1 アップダウンの基準を一つ求める
                    jd = make_position_jd(ins_range, temp_ans)  # 日時降順のDF(indexはどうでもいい)を、日時降順のAns
                    # 2 処理を行う
                    # jdが小さい(0.2以下)場合 または、特に無し（直前が中間）の場合(0)は順方向（元々の思想）+ 最後のポイントは５分前以内
                    if jd <= 0.25 and temp_ans[0]["count_inc_me"] < gl["ng_wait_range"]:
                        direction = "1Cj"  # 順方向
                        print("  TP調整", gl["tp"] * adj_r, gl["lc_c"] * adj_r)
                        data['remark']="1Cj"
                        swith_order_exe(gl["units"], 1, data['close'], gl["tp"]*adj_r, gl["lc_c"]*adj_r, "Market", data)
                    else:
                        direction = -1
                        print("  TP調整", gl["tp"] * adj_r, gl["lc_c"] * adj_r)
                        data['remark'] = "-1"
                        swith_order_exe(gl["units"], -1, data['close'], gl["tp"]*adj_r, gl["lc"]*adj_r, "Market", data)
                    gl["latest_get"] = datetime.datetime.now()
                else:
                    print("  　　中間上（短）", temp_ans[0]["count_inc_me"])

            # パターン②　宙に浮いている場合、何分間その状態が継続しているかを判定する（下）
            elif now_l == 31:
                # inspect_range = 20
                # ins_range = mid_df.tail(inspect_range).head(inspect_range - 1).sort_index(ascending=False)  # 最新は抜いて渡す！
                # temp_ans = make_position_latestpoint(ins_range)
                if temp_ans[0]["count_inc_me"] >= gl["wait_range"]:
                    print("  　　★中間下")
                    # 1 アップダウンの基準を一つ求める〝
                    jd = make_position_jd(ins_range, temp_ans)  # 日時降順のDF(indexはどうでもいい)を、日時降順のAns
                    # 2 処理を行う
                    # jdが小さい(0.2以下)場合 または、特に無し（直前が中間）の場合(0)は順方向（元々の思想）,かつ、経ちすぎていない場合
                    if jd <= 0.25 and temp_ans[0]["count_inc_me"] < gl["ng_wait_range"]:
                        direction = "-1Cj"  # 順張り
                        print("  TP調整", gl["tp"]*adj_r, gl["lc_c"]*adj_r)
                        data['remark'] = "-1Cj"
                        swith_order_exe(gl["units"], -1, data['close'], gl["tp"]*adj_r, gl["lc_c"]*adj_r, "Market", data)
                    else:
                        direction = "1"  # 逆張り
                        print("  TP調整", gl["tp"] * adj_r, gl["lc_c"] * adj_r)
                        data['remark'] = "1"
                        swith_order_exe(gl["units"], 1, data['close'], gl["tp"]*adj_r, gl["lc"]*adj_r, "Market", data)
                    gl["latest_get"] = datetime.datetime.now()
                else:
                    print("  　　中間下（短）", temp_ans[0]["count_inc_me"])

            # パターン③　中央線状にいる場合、何連続で中央線上にいるかを判定し、買いかの判断を行う
            elif now_l == 20 or now_l == 21:
                # inspect_range = 20
                # ins_range = mid_df.tail(inspect_range).head(inspect_range - 1).sort_index(ascending=False)  # 最新は抜いて渡す！
                # temp_ans = make_position_latestpoint(ins_range)
                # 連続して中央線にいるかどうかを判定する(１つの間隔なら許容?）
                jd = 2  # カウントの判定に利用
                count = upper_part = lower_part = 0
                for item in temp_ans:
                    # 過去に中央線を跨いでいるand２個以内（１つ目の場合、それ以降は更新）場合
                    if item["ans"] == 99 and item["count_inc_me"] < jd:
                        jd = item["count_inc_me"] + 2
                        count += 1  # カウント用
                        print("   MidDJ", item["timing"], jd)
                        upper_part += (item["high_price"] - item['middle_price'])
                        lower_part += (item['middle_price'] - item["low_price"])
                    # それ以外はループは終了
                    else:
                        print("   MidDJ Break", item["timing"], jd)
                # 何連続で、Upper寄りかLower寄りかを判定する
                p_m = " [Mid連]" + str(jd) + ",upper:" + str(round(upper_part, 3)) + ",lower:" + str(
                    round(lower_part, 3))  # Line用
                # ★連続している場合、注文の対象
                if count > 3:
                    # upper寄りの場合は買い
                    if upper_part > lower_part:
                        print("  　　★中間連上", count)
                        print("  TP調整", gl["tp"] * adj_r, gl["lc_c"] * adj_r)
                        data['remark'] = "1中間連上"
                        swith_order_exe(gl["units"], 1, data['close'], gl["tp"]*adj_r, gl["lc"]*adj_r, "Market", data)
                        gl["latest_get"] = datetime.datetime.now()
                    elif upper_part < lower_part:
                        print("  　　★中間連下", count)
                        print("  TP調整", gl["tp"] * adj_r, gl["lc_c"] * adj_r)
                        data['remark'] = "-1中間連下"
                        swith_order_exe(gl["units"], -1, data['close'], gl["tp"]*adj_r, gl["lc"]*adj_r, "Market", data)
                        gl["latest_get"] = datetime.datetime.now()
        elif skip_flag == 1:
            # 指定の数だけ進める
            print("SKIP",skip_counter)
            skip_counter -= 1
            if skip_counter <= 0:
                skip_flag = 0
                print("SKIP2", skip_counter)
            continue

        # 最初はこっちに入る
        if skip_flag == 1:
            # 指定の数だけ進める
            if skip_counter == 0:
                skip_flag = 0
                print("SKIP4", skip_counter)
            print("SKIP33", skip_counter)
            skip_counter -= 1
            print("SKIP3", skip_counter)
            continue



def close_position(p_data):
    global gl

    print("　　　【ポジションあり状態】")
    # # ■　強制的なロスカにつながる（両建て不可の為）ので、オーダーは解除する
    # oa.OrderCancel_All_exe()  # ポジション取得検討時は、まず既存のオーダーをキャンセルする
    # ポジションを持っている場合、ポジションの情報を取得
    # price = float(position_df.head(1).iloc[0]["price"])
    # pl = float(position_df.head(1).iloc[0]["unrealizedPL"])
    # p_id = int(position_df.head(1).iloc[0]["id"])
    # t = position_df.head(1).iloc[0]["order_time_jp"]
    # unit = float(position_df.head(1).iloc[0]["currentUnits"])
    # print("    ポジション", t, price, unit, pl, p_id)
    # # 分岐で表示
    # if pl < 0:
    #     print("　　　＠含み損ポジあり", pl, t, p_id, price)
    # else:
    #     print("　　　＠含み益ポジあり", pl, t, p_id, price)
    print(p_data['time'])
    params = {
        "granularity": "S5",
        "count": 1012,  # 1分足懸賞の場合、最初の１２は捨て。
        "from": p_data['time_from'],
    }
    i_df = oa.InstrumentsCandles_multi_exe("USD_JPY", params, 1)
    i_df = i_df[12:].reset_index()
    print(i_df)

    for index, data in i_df.iterrows():
        # ①取得後１5分以上経過している場合
        # if past_time.seconds > 900:
        #     print("　　　10分以上経過のポジション/キャンセルします", past_time.seconds)
        # elif past_time.seconds > 600:
        #シンプル解除(ロスカ優先）
        if float(data["low"]) <= float(p_data["lc_price"]) <= float(data["high"]):
            res={"res":"lc", "res_time":data["time_jp"], "index":index}
            print(res)
            break
        elif float(data["low"]) <= float(p_data["tp_price"]) <= float(data["high"]):
            res = {"res": "lc", "res_time": data["time_jp"], "index": index}
            print(res)
            break
        else:
            res = {"res": "None", "res_time": "none", "index": 0}
    return res


    # ■長時間のポジションはキャンセル/条件変更する
    # t=p_data['time']
    # p_time = datetime.datetime(int(t[0:4]), int(t[5:7]), int(t[8:10]), int(t[11:13]), int(t[14:16]),
    #                            int(t[17:19]))
    # past_time = datetime.datetime.now() - p_time  # 何分保持しているポジションかを算出する
    # print("　　　経過時間", past_time.seconds, t)
    # # パータン①　取得後１5分以上経過している場合
    # if past_time.seconds > 900:
    #     print("　　　10分以上経過のポジション/キャンセルします", past_time.seconds)
    #     switch_close_exe(p_id, None, "cancel")
    #     # LINE通知用
    #     requests.post(api_url, headers=TOKEN_dic, data={'message': "長期ポジションを処理します"})
    # # パターン②　取得後２分経過時
    # elif past_time.seconds > 600:
    #     # マイナスへ発信した場合の対処
    #     if gl['tp_func'] == 0:
    #         # ■マイナスであれば、ぎりぎりの利確を狙う
    #         gl['tp_func'] = 1  # 二回目以降は処理しないようにする
    #         # 利確ラインを「０確」にする
    #         if unit < 0:
    #             # 売りのポジションの場合、買いの価格で決済(0以上になった場合に利確を行ってしまう）
    #             line = price - 0.001  # 本当はスプレッド分ほしいけど。。
    #         else:
    #             line = price + 0.001
    #         data = {
    #             "takeProfit": {
    #                 "price": str(round(line, 3)),
    #                 "timeInForce": "GTC",
    #             },
    #         }
    #         print("CD工程", round(line, 3))
    #         switch_CRCDO_exe(p_id, data)
    #         # 取得後2分以上経過している場合、最低限０で止めたい
    #         print("　　　2分以上かつマイナスのポジションの利確幅を縮めます", past_time.seconds, "price", str(line))
    #         # LINE通知用
    #         requests.post(api_url, headers=TOKEN_dic,
    #                       data={'message': "利確目指す（現在マイナス）" + str(pl) + "," + str(past_time.seconds)})
    #     else:
    #         print("　　　CD済(tp_func済フラグ有）")
    # # パターン③　取得後数分経過時
    # # elif past_time.seconds > 600:
    # #     if gl['tp_func'] == 0:
    # #         if pl > 0:
    # #             # ■プラスの状態だったら、TPしてしまう？
    # #             gl['tp_func'] = 1  # 二回目以降は処理しないようにする
    # #             if unit < 0:
    # #                 # 売りのポジションの場合、買いの価格で決済(0以上になった場合に利確を行ってしまう）
    # #                 line = price - 0.008
    # #             else:
    # #                 line = price + 0.008
    # #             data = {
    # #                 "stopLoss": {
    # #                     "price": str(round(line, 3)),
    # #                     "timeInForce": "GTC",
    # #                 },
    # #             }
    # #             print("　　CD工程？", round(line, 3))
    # #             # oa.TradeCRCDO_exe(p_id, data)
    # #             # LINE通知用
    # #             requests.post(api_url, headers=TOKEN_dic,
    # #                           data={'message': "完全利確(ロスカで利確短縮設定＠休止）" + str(pl) + "," + str(past_time.seconds)})
    # #     else:
    # #         print("　　　CD済(tp_func済フラグ有）")
    # else:
    #     print("     待機範囲のポジション")



gl = {
    "p_l_switch": 1,  #0 = practiceだけ。１＝practice + live
    "spred": 0.012,  # 許容するスプレッド practice = 0.004がデフォ。Live0.008がデフォ
    "wait_range": 6,  # 基準となる判断期間（N足分、ふらふらしていたら）
    "ng_wait_range": 8,  #基準となる判断期間（以内の方）一部で利用
    "freq": 1,  # 間隔指定の秒数
    "main_counter": 0,
    "exe_mode": 0,
    "test_posi": 0,  # テスト用のポジション保持フラグ
    "tp_func": 0,  # ポジションに対する調整を行うかのフラグ
    "order_time": datetime.datetime.now() + datetime.timedelta(minutes=-20),
    "now": datetime.datetime.now(),
    'now_hms': datetime.datetime.now().replace(microsecond=0),
    "over_continue": 0,  # 使ってない？
    "wait_counter": 0,  # 使ってない？
    "now_h": 0,
    "now_m": 0,
    "now_s": 0,
    "latest_get": datetime.datetime.now() + datetime.timedelta(minutes=-20),  # 初期値は現時刻ー２０分
    "tp": 0.06,
    "lc": 0.03,
    "tp_c": 0.06,
    "lc_c": 0.04,
    "adj": 1,
    "adj2": 0.7,
    "adj3": 0.5,
    "units": 10000
}
print("開始")
oa = oanda_class.Oanda(t.accountIDl, t.access_tokenl, "live")  # インスタンス生成(本番用　データはこちらから取得！！）
stocks = []
skip_counter = 0
skip_flag = 0
# data を取得する
mid_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": 'M1', "count": 100}, 1)
print(mid_df)
# positionを取るかの判定を行う
main_function(mid_df)

