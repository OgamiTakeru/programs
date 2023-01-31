import threading  # 定時実行用
import time
import datetime
import sys
import pandas as pd
# import requests

# 自作ファイルインポート
import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.oanda_class as oanda_class
import programs.main_functions_Prac as f  # とりあえずの関数集
from time import sleep


# import programs.mp_functions as mp  # MakePositionに関する関数群


def make_order():
    """
    ポジション取得のメイン
    """
    global gl

    # ■現在価格を取得（スプレッド異常の場合は強制終了）
    price_dic = oa.NowPrice_exe("USD_JPY")
    print("【現在価格live】", price_dic['mid'], price_dic['ask'], price_dic['bid'], price_dic['spread'])
    if price_dic['spread'] > gl['spread']:
        print("    ▲スプレッド異常")  # スプレッドによっては実行をしない
        sys.exit()

    # ■直近の検討データの取得
    data_format = '%Y/%m/%d %H:%M:%S'
    # 5分足データの取得
    d5_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 30}, 1)
    d5_df = f.add_peak(d5_df, gl['p_order'])
    d5_df.to_csv(tk.folder_path + 'main_data5.csv', index=False, encoding="utf-8")
    # d5_df = pd.read_csv(tk.folder_path + 'main_data5.csv', sep=",", encoding="utf-8")  # test
    # print(d5_df.tail(3))

    # print(d5_df.head(2))
    # 1分足データの取得
    d1_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M1", "count": 150}, 1)
    d1_df = f.add_peak(d1_df, gl['p_order'])
    d1_df.to_csv(tk.folder_path + 'main_data1.csv', index=False, encoding="utf-8")
    # d1_df = pd.read_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', sep=",", encoding="utf-8")  # test

    # ##### 折り返し判定
    d5_df['middle_price_gap'] = d5_df['middle_price'] - d5_df['middle_price'].shift(1)  # 時間的にひとつ前からいくら変動があったか
    dr = d5_df.sort_index(ascending=False)  # 対象となるデータフレーム（直近が上の方にある）
    # ３：６の場合
    ignore = 1  # 最初（現在を意味する）
    dr_latest_n = 2
    dr_oldest_n = 10
    # latest_df = dr[1: dr_latest_n + 1]  # 直近の３個を取得
    # oldest_df = dr[dr_latest_n: dr_latest_n + dr_oldest_n]
    latest_df = dr[ignore: dr_latest_n + ignore]  # 直近の３個を取得
    oldest_df = dr[dr_latest_n + ignore -1: dr_latest_n + dr_oldest_n + ignore -1]  # 前半と１行をラップさせて、古い期間の範囲を求める
    latest_ans = f.renzoku_gap_pm(latest_df)  # 何連続で同じ方向に進んでいるか（直近-1まで）
    oldest_ans = f.renzoku_gap_pm(oldest_df)  # 何連続で同じ方向に進んでいるか（前半部分）
    ans = f.renzoku_gap_compare(oldest_ans, latest_ans, price_dic['mid'])  # 引数の順番に注意！　ポジ用の価格情報を取得する。

    if ans == 0:
        print(" 折返判定o-l", oldest_ans['count'], latest_ans['count'])
    else:
        print(" 折返判定o-l", oldest_ans['count'], latest_ans['count'], ans['info']['return_ratio'], ans['info']['bunbo_gap'])

        if ans['memo'] == 0:  # 通常の両側に入れるオーダー
            # オーダーを代入しておく（よく名前が変るため。。）
            f_order = ans["f_order"]
            f_repeat = ans["f_repeat"]
            r_order = ans["r_order"]
            r_repeat = ans["r_repeat"]

            # 順思想 オーダー実行
            gl['orders'] = []  # オーダー情報記録用
            f_res = oa.OrderCreate_dic_exe(f_order)  # オーダー実行（ロング）
            for i in range(len(f_repeat)):  # オーダー実行（トラリピ）
                oa.OrderCreate_dic_exe(f_repeat[i])
            gl['orders'].append(f_order)  # 単品ロングオーダーを記録
            gl['orders'].append(ans['f_repeat'])  # トラリピオーダーを記録
            print(" 　順オーダー")
            print(f_order)
            print(f_repeat)
            # 逆思想　オーダー実行
            r_res = oa.OrderCreate_dic_exe(r_order)
            for i in range(len(r_repeat)):
                oa.OrderCreate_dic_exe(r_repeat[i])
            print("  逆オーダー")
            print(r_order)
            print(r_repeat)
            gl['orders'].append(r_order)  # 単品ロングオーダーを記録
            gl['orders'].append(ans['r_repeat'])  # トラリピオーダーを記録

            # LINE送信用情報(表示用はLCとTPを場合分けしないと。。）
            t = round(f_order['price'], 3)
            tp = round(t + float(f_order['tp_range']) * float(f_order['ask_bid']), 3)  # ans['forward']['lc_price']と同義？
            lc = round(t - float(f_order['lc_range']) * float(f_order['ask_bid']), 3)
            gl['position_f_direction'] = f_order['ask_bid']  # 順方向のポジションがどっち方向かを記録する

            tk.line_send("■折返Position！", datetime.datetime.now().replace(microsecond=0),
                         ",現価格:", price_dic['mid'],
                         "順方向:", f_order['ask_bid'],
                         ",戻り率:", ans["info"]["return_ratio"], "(", ans['info']['bunbo_gap'], ")",
                         "latest範囲", latest_ans['inner_low_price'], "-", latest_ans['inner_high_price'],
                         "oldest範囲", oldest_ans['inner_low_price'], "-", oldest_ans['inner_high_price'], oldest_ans['count'],
                         ",順思想:", f_order['ask_bid'], t, "(", tp, "[", f_order['tp_range'], "]-",
                         lc, "[", round(f_order['lc_range'], 3), "]", ")",
                     )
        elif ans['memo'] == 1:
            # オーダーを代入しておく（よく名前が変るため。。）
            r_repeat = ans["r_repeat"]

            # 順思想 オーダー実行
            gl['orders'] = []  # オーダー情報記録用
            # 逆思想　オーダー実行
            for i in range(len(r_repeat)):
                oa.OrderCreate_dic_exe(r_repeat[i])
            print("  逆オーダー")
            print(r_repeat)
            gl['orders'].append(ans['r_repeat'])  # トラリピオーダーを記録

            # LINE送信用情報(表示用はLCとTPを場合分けしないと。。）　代表して最初の物
            info_t= r_repeat[0]
            t = round(info_t['price'], 3)
            tp = round(t + float(info_t['tp_range']) * float(info_t['ask_bid']), 3)  # ans['forward']['lc_price']と同義？
            lc = round(t - float(info_t['lc_range']) * float(info_t['ask_bid']), 3)
            gl['position_f_direction'] = info_t['ask_bid']  # 順方向のポジションがどっち方向かを記録する

            tk.line_send("■戻り大。折返Position！", datetime.datetime.now().replace(microsecond=0),
                         ",現価格:", price_dic['mid'],
                         "順方向:", info_t['ask_bid'],
                         ",戻り率:", ans["info"]["return_ratio"], "(", ans['info']['bunbo_gap'], ")",
                         "latest範囲", latest_ans['inner_low_price'], "-", latest_ans['inner_high_price'],
                         "oldest範囲", oldest_ans['inner_low_price'], "-", oldest_ans['inner_high_price'], oldest_ans['count'],
                         ",順思想:", info_t['ask_bid'], t, "(", tp, "[", info_t['tp_range'], "]-",
                         lc, "[", round(info_t['lc_range'], 3), "]", ")",
                     )
        # # オーダーIDを取得する（テスト。オーダー処理を待つため、１秒待機する）
        # sleep(1)
        # pending_new_df = oa.OrdersWaitPending_exe()
        # dummy = []
        # for i in range(len(gl['orders'])):
        #     if type(gl['orders'][i]) != type(dummy):  # listじゃなかったら実行！
        #         for index, item in pending_new_df.iterrows():
        #             if gl['orders'][i]["units"] == abs(int(item['units'])):  # dfはUnitにマイナスが付いている可能性あり！
        #                 print(" 発見&オーダーあり")
        #                 gl['orders'][i]['order_id'] = item['id']
        #                 print(gl['orders'][i])

    # mid_df.loc[index_graph, 'return_half_all'] = 1  # ★グラフ用


def close_order(pending_new_df):
    global gl

    for index, item in pending_new_df.iterrows():
        if item['units'] == 10000:  # and item['type'] == "STOP":
            if item['past_time_sec'] > gl["orders"][0]["time_out"]:
                print(" 時刻による解消！　１０分！")
                tk.line_send("個別解消", item['units'],item['past_time_sec'], ">", gl["orders"][0]["time_out"])



def close_position():
    global gl

    position_df = oa.OpenTrades_exe()  # positionを取得（ループタイミングの関係で、ここでもポジション数を確認する！）
    # ■ポジション有の場合　（解消後初回のみ、mainからこっちに入ってくるため、対策が必要）
    if len(position_df) > 0:  # ポジション有
        print("　　　【ポジションあり状態】", len(position_df))
        for i in range(len(position_df)):  # 複数ポジションがある場合があるため、ループ回す
            # ポジションを持っている場合、ポジションの情報を取得
            price = float(position_df.iloc[i]["price"])  # 取得時点の価格
            pl = float(position_df.iloc[i]["unrealizedPL"])  # 含み損益価格
            p_id = int(position_df.iloc[i]["id"])  # ポジションのID
            t = position_df.iloc[i]["order_time_jp"]  # 注文時刻
            unit = float(position_df.iloc[i]["currentUnits"])  # 保持枚数
            past_time_sec = float(position_df.iloc[i]["past_time_sec"])  # 経過時間秒
            pl_pips = round(pl / abs(unit), 3)  # 含み損益（0.0１円単位）名前はピップスだが、１００分の１円単位表示

            # 情報を表示
            if pl < 0:
                print("　　　＠含み損ポジあり", pl, t, p_id, price, pl_pips, past_time_sec)
            else:
                print("　　　＠含み益ポジあり", pl, t, p_id, price, pl_pips, past_time_sec)
            gl['latest_res_pips'] = pl_pips

            # 取り合えず長時間の保持は、切る。
            if past_time_sec > 40 * 60:
                # N分以上のポジションは、切る(本当は、オーダー時刻からの考慮である必要あり？）
                print(" 時間によるポジション解消")
                gl['cd_flag'] = 1
                oa.TradeClose_exe(p_id, None, "cancel")

            # 場合によってはCRCDOのパターンを変更する（ポジションの枚数で、どのポジションかを判断する）
            if gl['cd_flag'] == 0:  # 過去の変更履歴がない場合は、以下の変更を実施する
                # ポジション取得後、数分（５分足2個分）は含み損を認める。それ以降、プラス域4pips以上いった場合、最低2pipsの利確注文
                print(" 　　　ポジションの見直し", unit)
                if unit == 10001:
                    if past_time_sec > 50 and pl_pips > 0.01:
                        print(" 　　　レンジ向けのポジション", unit)
                        #BOX(逆思想方向）
                        cd_line = price - 0.005 if unit < 0 else price + 0.005  # -はプラス確保、＋は容認マイナス
                        data = {
                            "stopLoss": {"price": str(cd_line), "timeInForce": "GTC",},
                            "trailingStopLoss": {"distance": 0.05, "timeInForce": "GTC",},
                        }
                        oa.TradeCRCDO_exe(p_id, data)  # ポジションを変更する
                        tk.line_send("■(BOX)LC値底上げ", price, "⇒", cd_line)
                        gl['cd_flag'] = 1  # main本体で、ポジションを取る関数で解除する
                elif unit == 10000:
                    print("   変種要素無し(価格違い）")



def main():
    global gl
    gl["main_counter"] += 1
    print(gl["now"])
    # 現状の把握
    position_df = oa.OpenTrades_exe()  # ポジション情報の取得
    pending_new_df = oa.OrdersWaitPending_exe()  # ペンディングオーダーの取得(利確注文等は含まない）
    pending_df = oa.OrdersPending_exe()  # ペンディングオーダーの取得（利確注文等も含む）

    # ★ポジション所持時は、ポジションの情報を取得する
    if len(position_df) != 0:
        # ポジション所持時！
        if gl["position_flag"] == 0:
            # ポジション無しから、初めてポジションありになった時
            unit = float(position_df.head(1).iloc[0]["currentUnits"])  # 保持枚数（ポジションの方向を確認するため）
            d = unit / abs(unit)  # 1か-1にする
            if gl['position_f_direction'] == d:  # ポジションの方向と、順思想のポジション方向が一致する場合⇒順方向のポジション
                gl['position_mind'] = 1  # 1は順方向
            else:
                gl['position_mind'] = -1  # -1は逆方向
            tk.line_send("■ポジションを取得しました(思想方向:", gl['position_mind'], d)
            gl['position_flag'] = 1  # ポジションフラグの成立
    elif len(position_df) == 0:
        # ポジション無し時
        if gl["position_flag"] == 1:
            # 前実行時にポジションを持っていた場合（今は持っていない）
            tk.line_send("■ポジションを解消しました", gl['latest_res_pips'])  # latest_res_pips は前回実行時の物（数秒前）
            gl['exe_mode'] = 0
            gl['position_flag'] = 0  # ポジションフラグのリセット
            gl['position_f_direction'] = 0  # 順思想のポジション方向のリセット
            if gl['latest_res_pips'] >= 0:
                # 結果がプラスの場合（第二の矢が入る可能性あり）
                # make_position_second()
                pass
            else:
                # 結果がマイナスの場合、第二の矢の可能性はない！
                pass

    # ★ペンディング所持時！
    if len(pending_new_df) != 0:
        # 注文中のデータが存在する場合
        print("    ◇未確定注文有", len(pending_new_df), gl['now'])
        past_time = pending_df.head(1).iloc[0]["past_time_sec"]  # オーダーした時刻３3
        print("  orderあり（保持中）", past_time)
        close_order(pending_new_df)  # 個別解除

        limit_time_min = 14
        if past_time > 60 * limit_time_min:  # 60*指定の分
            # 12分以上経過している場合、オーダーをキャンセルする
            oa.OrderCancel_All_exe()
            tk.line_send(str(limit_time_min), "以上のオーダーを解除します■")

    # ★メインとなる分岐
    if len(position_df) != 0:
        # ★ポジションがある場合（ポジション解消検討処理へ）
        gl['exe_mode'] = 1
        print("    ◇ポジション有", gl['now'], gl['exe_mode'])
        close_position()
    elif len(position_df) == 0 and len(pending_new_df) == 0:
        # ★ポジションがない場合
        gl['cd_flag'] = 0
        make_order()


def schedule(interval, f, wait=True):
    global gl
    base_time = time.time()
    while True:
        # 現在時刻の取得
        now = gl['now'] = datetime.datetime.now().replace(microsecond=0)  # 現在の時刻を取得
        time_hour = gl['now_h'] = now.hour  # 現在時刻の「時」のみを取得
        time_min = gl['now_m'] = now.minute  # 現在時刻の「分」のみを取得
        time_sec = gl['now_s'] = now.second  # 現在時刻の「秒」のみを取得
        gl['now_hms'] = datetime.datetime.now().replace(microsecond=0)  # ミリsecのない時刻を取得

        # 【時間帯による実施無し】
        if 3 <= time_hour < 8:
            # 3時～７時の間はスプレッドを考慮していかなる場合も実行しない⇒ポジションや注文も全て解消
            if gl['midnight_close'] == 0:  # 深夜にポジションが残っている場合は解消
                oa.OrderCancel_All_exe()
                oa.TradeAllColse_exe("try")
                tk.line_send("■深夜のポジション・オーダー解消を実施")
                gl['midnight_close'] = 1  # 解消済みフラグ

        # 【実施時間】
        else:
            gl['midnight_close'] = 0  # 深夜のポジションオーダー解消フラグの解消
            # ★基本的な実行関数。基本的にgl['schedule_freq']は１秒で実行を行う。（〇〇分〇秒に実行等）
            if gl["exe_mode"] == 0:
                # [2の倍数分、15秒に処理に定期処理実施
                if time_min % 1 == 0 and time_sec == 9:
                    t = threading.Thread(target=f)
                    t.start()
                    if wait:  # 時間経過待ち処理？
                        t.join()
            # 数秒ごとの実施要（ポジション所持時等に利用する場合有。基本は利用無しで[exe_mode=0]が基本）
            elif gl["exe_mode"] == 1:
                # N秒ごとに実施
                if time_min % 1 == 0 and time_sec % 10 == 0:  # (time_sec == 9 or time_sec == 39):
                    # print("  2秒ごと実施",time_hour,time_min,time_sec)
                    t = threading.Thread(target=f)
                    t.start()
                    if wait:  # 時間経過待？
                        t.join()
        # 待機処理
        next_time = ((base_time - time.time()) % gl['schedule_freq']) or gl['schedule_freq']
        time.sleep(next_time)


# 開始
print("開始")
# グローバル変数の定義
gl = {
    # "pending": 0,
    "main_counter": 0,
    "exe_mode": 0,  # 実行頻度モードの変更（基本的は０）
    "schedule_freq": 1,  # 間隔指定の秒数（N秒ごとにスケジュールで処理を実施する）
    "order_time": datetime.datetime.now() + datetime.timedelta(minutes=-20),
    "now_h": 0,
    "now_m": 0,
    "now_s": 0,
    'now': datetime.datetime.now().replace(microsecond=0),
    "latest_get": datetime.datetime.now() + datetime.timedelta(minutes=-20),  # 初期値は現時刻ー２０分
    "spread": 0.012,  # 0.012,  # 許容するスプレッド practice = 0.004がデフォ。Live0.008がデフォ
    "p_order": 2,  # 極値の判定幅
    "position_flag": 0,  # ポジションが消えたタイミングを取得するためのフラグ
    "position_f_direction": 0,  # ポジションが買いか売りか
    "position_mind": 0,  # ポジションが順思想が、逆思想が
    "orders": [],
    "cd_flag": 0,  # 利確幅を途中で変えた時のフラグ
    "add_flag": 0,  # 途中でポジションを追加しに行く処理
    "midnight_close": 0,
    "order_num": 30000,  # トータルでどのくらいポジション持つか
    "trail_num": 20000,  # トレール分。
    "latest_res_pips": 0,  # 最終的なマイナス（最後の数行は推定になるが）
    "second_order": 0,  # secondオーダーを格納
}

# ■練習か本番かの分岐
fx_mode = 0  # 0=practice, 1=Live

if fx_mode == 0:  # practice
    env = tk.environment
    acc = tk.accountID
    tok = tk.access_token
else:
    env = tk.environmentl
    acc = tk.accountIDl
    tok = tk.access_tokenl
# ■クラスインスタンスの作成
oa = oanda_class.Oanda(acc, tok, env)  # インスタンス生成(練習用　練習時はオーダーのみこちらから）
print(env)
# ■出発！
main()
schedule(gl['schedule_freq'], main)
