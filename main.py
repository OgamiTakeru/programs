import threading  # 定時実行用
import time
import datetime
import sys
import pandas as pd
# import requests

# 自作ファイルインポート
import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.oanda_class as oanda_class
import programs.main_functions as f  # とりあえずの関数集


# import programs.mp_functions as mp  # MakePositionに関する関数群


def make_position():
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
    # d5_df = pd.read_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', sep=",", encoding="utf-8")  # test

    # print(d5_df.head(2))
    # 1分足データの取得
    d1_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M1", "count": 150}, 1)
    d1_df = f.add_peak(d1_df, gl['p_order'])
    d1_df.to_csv(tk.folder_path + 'main_data1.csv', index=False, encoding="utf-8")
    # d1_df = pd.read_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', sep=",", encoding="utf-8")  # test


    # ★５分足のクロスがある場合は、１分足も確認して直前（３分以内にあれば）そっちの方向に行くのでは、と推定する
    # print(latest_cross5_time_dt, latest_cross1_time_dt)
    # # print((latest_cross5_time_dt - latest_cross1_time_dt).seconds)
    # gap_second = (latest_cross5_time_dt - latest_cross1_time_dt).seconds  # ５分足クロスと１分足クロスの時間ギャップ
    # if latest_cross5 != 0:
    #     print(" 直前に５分クロスを確認")
    #     # その場合、ひとつ前のクロスを確認する（クロスがくっついている場合は無効にするため）
    #     confirm_time = cross5_only_df.iloc[-1]['time_jp']  # 確認用
    #     second_cross = datetime.datetime.strptime(cross5_only_df.iloc[-2]['time_jp'], data_format)  # ひとつ前
    #     jd_range = (latest_cross5_time_dt - second_cross).seconds  # ５分足クロスの１つ目と二つ目の間（レンジかどうかの判断）
    #     print(" Range判定",confirm_time, second_cross, jd_range)
    #     if gap_second < 480:  # ５分足と１分足の発生タイミングが近い
    #         if latest_cross5 == latest_cross1 and jd_range > 600:  # 同じ方向のクロス、かつ、５分足がレンジではない
    #             print("  理想 5分クロス:", latest_cross5, "1分クロス:", latest_cross1, "5分-1分", gap_second, "5分Range", jd_range, "RangeBB:",range_bb, "BBRange2", gl_bb['range'])
    #             if glc['for_send'] == 0:
    #                 tk.line_send("ポジ？", latest_cross5, gap_second, latest_cross5_time_dt,"レンジ有無", range_flag, datetime.datetime.now().replace(microsecond=0))
    #                 glc['for_send'] = 1  # SnedFlag
    #         else:
    #             print("  No(別方向) 5分クロス:", latest_cross5, "1分クロス:", latest_cross1, "5分-1分", gap_second, "5分Range", jd_range)
    #             # tk.line_send("NNo(別方向) 5分クロス:", latest_cross5, "1分クロス:", latest_cross1, "5分-1分", gap_second, "5分Range", jd_range, "RangeBB:",range_bb, "BBRange2", gl_bb['range'])
    #     else:
    #         print(" 理想ではない", gap_second)
    # else:
    #     print(" ５分クロス無し")
    #     glc['for_send'] = 0  # SnedFlag

    # ##### 折り返し判定
    d5_df['middle_price_gap'] = d5_df['middle_price'] - d5_df['middle_price'].shift(1)  # 時間的にひとつ前からいくら変動があったか
    dr = d5_df.sort_index(ascending=False)  # 対象となるデータフレーム（直近が上の方にある）
    # ３：６の場合
    ignore_latest = 1  # 最初（現在を意味する）
    dr_latest_n = 3
    dr_oldest_n = 10
    latest_df = dr[1: dr_latest_n + 1]  # 直近の３個を取得
    oldest_df = dr[dr_latest_n: dr_latest_n + dr_oldest_n]  # 前半と１行をラップさせて、古い期間の範囲を求める
    latest_ans = f.renzoku_gap_pm(latest_df)  # 何連続で同じ方向に進んでいるか（直近-1まで）
    oldest_ans = f.renzoku_gap_pm(oldest_df)  # 何連続で同じ方向に進んでいるか（前半部分）
    ans = f.renzoku_gap_compare(oldest_ans, latest_ans, price_dic['mid'])  # 引数の順番に注意！　ポジ用の価格情報を取得する。
    if ans == 0:
        print(" 折返判定o-l", oldest_ans['count'], latest_ans['count'])
    else:
        print(" 折返判定o-l", oldest_ans['count'], latest_ans['count'], ans['info']['return_ratio'], ans['info']['bunbo_gap'])
        # 思想と順方向は必須で入れる
        order_res = oa.OrderCreate_exe(10000, ans['forward']["direction"], ans['forward']['target_price'],
                                       ans['forward']['tp_range'], ans['forward']['tp_range'], ans['forward']['type'],
                                       0, "順思想")  # 順思想（順張・現より低い位置に注文入れたい）
        # 思想と逆方向は、ほぼほぼマーケットで入れるが、すでに動いている場合があるため、少し余裕を持って入れる。
        order_res_r = oa.OrderCreate_exe(10000, ans['reverse']["direction"], ans['reverse']['target_price'],
                                         ans['reverse']['tp_range'], ans['reverse']['lc_range'], ans['reverse']['type'],
                                         0, "逆思想")  # 逆思想（順張・現より高い位置に注文入れたい）
        print(" 該当有", ans['forward']['direction'], ans, order_res, order_res_r)
        # LINE送信用情報(表示用はLCとTPを場合分けしないと。。）
        t = round(float(ans['forward']['target_price']), 3)
        tp = round(t + float(ans['forward']['tp_range']) * float(ans['forward']['direction']), 3)
        lc = round(t - float(ans['forward']['lc_range']) * float(ans['forward']['direction']), 3)
        tr = round(float(ans['reverse']['target_price']), 3)
        tpr = round(tr + float(ans['reverse']['tp_range']) * float(ans['reverse']['direction']), 3)
        lcr = round(tr - float(ans['reverse']['lc_range']) * float(ans['reverse']['direction']), 3)
        tk.line_send("折返Position！", datetime.datetime.now().replace(microsecond=0),
                     ",現価格:", price_dic['mid'],
                     ",基本方向", ans['forward']['mind'],
                     ",順思想:", ans['forward']['direction'], t, "(", tp, "-", lc, ")",
                     ",逆思想:", ans['reverse']['direction'], tr, "(", tpr, "-", lcr, ")",
                     "参考", oldest_ans['high_price'], oldest_ans['low_price'],
                     latest_ans['high_price'], latest_ans['low_price']
                     )

        # print(" 該当あり", ans)
        # mid_df.loc[index_graph, 'return_half_all'] = 1  # ★グラフ用


def close_position():
    global gl

    position_df = oa.OpenTrades_exe()  # positionを取得（ループタイミングの関係で、ここでもポジション数を確認する！）
    # ■ポジション有の場合　（解消後初回のみ、mainからこっちに入ってくるため、対策が必要）
    if len(position_df) > 0:
        print("　　　【ポジションあり状態】")
        # # ■　強制的なロスカにつながる（両建て不可の為）ので、オーダーは解除する
        # oa.OrderCancel_All_exe()  # ポジション取得検討時は、まず既存のオーダーをキャンセルする
        # ポジションを持っている場合、ポジションの情報を取得
        price = float(position_df.head(1).iloc[0]["price"])  # 取得時点の価格
        pl = float(position_df.head(1).iloc[0]["unrealizedPL"])  # 含み損益価格
        p_id = int(position_df.head(1).iloc[0]["id"])  # ポジションのID
        t = position_df.head(1).iloc[0]["order_time_jp"]  # 注文時刻
        unit = float(position_df.head(1).iloc[0]["currentUnits"])  # 保持枚数
        past_time_sec = float(position_df.head(1).iloc[0]["past_time_sec"])  # 経過時間秒
        print("    ポジション", t, price, unit, pl, p_id)
        # 分岐で表示
        if pl < 0:
            print("　　　＠含み損ポジあり", pl, t, p_id, price)
        else:
            print("　　　＠含み益ポジあり", pl, t, p_id, price)

        # ■長時間のポジションはキャンセル/条件変更する
        print("　　　経過時間", past_time_sec, t)
        # パータン①　取得後１5分以上経過している場合
        if past_time_sec > 900:
            print("　　　９００秒以上経過のポジション/キャンセルします", past_time_sec)
            oa.TradeClose_exe(p_id, None, "cancel")
        # パターン②　取得後２分経過時
        # elif past_time.seconds > 480:  # 結構480は方向転換としては良いタイミングな気がする！（22/07/20)
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
        #         # 取得後2分以上経過している場合、最低限０で止めたい
        #         print("　　　規定の分以上かつ利確幅を縮めます", past_time.seconds, "price", str(line))
        #     else:
        #         print("　　　CD済(tp_func済フラグ有）")


def main():
    global gl
    gl["main_counter"] += 1
    print(gl["now"])
    # 現状の把握
    position_df = oa.OpenTrades_exe()  # ポジション情報の取得
    pending_new_df = oa.OrdersWaitPending_exe()  # ペンディングオーダーの取得(利確注文等は含まない）
    pending_df = oa.OrdersPending_exe()  # ペンディングオーダーの取得（利確注文等も含む）

    # ★ポジション解除時のデータ送信。
    if gl["exe_mode"] == 1 and len(position_df) == 0:
        # ポジション有からポジションなしに切り替わった場合、持っていた（今は解消済み）ポジションの情報を送信する
        pass
    # ★ペンディングは時間的に解消を実施する
    if len(pending_new_df) != 0:
        # 注文中のデータが存在する場合
        print("    ◇未確定注文有", gl['now'])
        past_time = pending_df.head(1).iloc[0]["past_time_sec"]  # オーダーした時刻３3
        print("  orderあり（保持中）", past_time)
        limit_time_min = 20
        if past_time > 60 * limit_time_min:  # 60*指定の分
            # 12分以上経過している場合、オーダーをキャンセルする
            oa.OrderCancel_All_exe()
            tk.line_send(str(limit_time_min), "以上のオーダーを解除します")
    # ★メインとなる分岐
    if len(position_df) != 0:
        # ★ポジションがある場合（ポジション解消検討処理へ）
        print("    ◇ポジション有", gl['now'])
        close_position()
    elif len(position_df) == 0 and len(pending_new_df) == 0:
        # ★ポジションがない場合
        make_position()


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
            # 3時～７時の間はスプレッドを考慮していかなる場合も実行しない
            pass
        # 【実施時間】
        else:
            # ★基本的な実行関数。基本的にgl['schedule_freq']は１秒で実行を行う。（〇〇分〇秒に実行等）
            if gl["exe_mode"] == 0:
                # [2の倍数分、15秒に処理に定期処理実施
                if time_min % 1 == 0 and time_sec == 5:
                    t = threading.Thread(target=f)
                    t.start()
                    if wait:  # 時間経過待ち処理？
                        t.join()
            # 数秒ごとの実施要（ポジション所持時等に利用する場合有。基本は利用無しで[exe_mode=0]が基本）
            elif gl["exe_mode"] == 1:
                # N秒ごとに実施
                if time_min % 1 == 0 and (
                        time_sec == 55 or time_sec == 25 or time_sec == 10 or time_sec == 40):
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
# ■クラスインスタンス生成 (処理は今後opが正規で動く９
oa = oanda_class.Oanda(tk.accountID, tk.access_token, "practice")  # インスタンス生成(練習用　練習時はオーダーのみこちらから）

# グローバル変数の定義
glp = {
    "before_latest_pv": "2022/12/16  16:38:00",  # 初期値はテキトーな時刻
}
glc = {
    "for_send": 0,
    "before_time": "2022/12/16  16:38:00",
}
gl_bb = {
    "range": 0,
}
gl = {
    "main_counter": 0,
    "exe_mode": 0,  # 実行頻度モードの変更（基本的は０）
    "schedule_freq": 1,  # 間隔指定の秒数（N秒ごとにスケジュールで処理を実施する）
    "order_time": datetime.datetime.now() + datetime.timedelta(minutes=-20),
    "now_h": 0,
    "now_m": 0,
    "now_s": 0,
    'now': datetime.datetime.now().replace(microsecond=0),
    "latest_get": datetime.datetime.now() + datetime.timedelta(minutes=-20),  # 初期値は現時刻ー２０分
    "spread": 0.8,  # 0.012,  # 許容するスプレッド practice = 0.004がデフォ。Live0.008がデフォ
    "tp": 0.035,
    "lc": 0.02,
    "p_order": 2,  # 極値の判定幅
    "test_target_price": 0,
}

# ■出発！
main()
schedule(gl['schedule_freq'], main)
