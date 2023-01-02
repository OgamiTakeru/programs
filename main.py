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
    d5_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 30}, 1 )
    d5_df = f.add_peak(d5_df, gl['p_order'])
    d5_df.to_csv(tk.folder_path + 'main_data5.csv', index=False, encoding="utf-8")
    # d5_df = pd.read_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', sep=",", encoding="utf-8")  # test

    # print(d5_df.head(2))
    # 1分足データの取得
    d1_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M1", "count": 150}, 1 )
    d1_df = f.add_peak(d1_df, gl['p_order'])
    d1_df.to_csv(tk.folder_path + 'main_data1.csv', index=False, encoding="utf-8")
    # d1_df = pd.read_csv('C:/Users/taker/Desktop/Peak_TEST_DATA.csv', sep=",", encoding="utf-8")  # test

    # print(d1_df.head(2))

    # # 直近の極値関係のデータを取得する(ただし直近の極値が、２足以内の場合は無視する（変わる可能性があるため）
    # pv_order = gl['p_order']  # 極値算出の幅
    # pv_df = mid_df[mid_df['pv_flag' + str(pv_order)].notna()]  # 空欄以外を抽出（フィルタ）
    # pv_r_df = pv_df.sort_index(ascending=False)  # 逆向きのデータフレームを取得し、調査する
    #
    # # 前回確認時の直近の極値が消えていないか（変更されていないか）を確認する
    # if glp['before_latest_pv'] == pv_r_df.iloc[0]['time_jp']:
    #     # 前回の極値と、今回の極値が同一の場合
    #     print(" 極値の変更なし")
    # else:
    #     # 異なる場合（消えたor新しく直近の極値が出来た場合）
    #     if glp['before_latest_pv'] > pv_r_df.iloc[0]['time_jp']:
    #         # 極値が超滅している場合（前回の極値時間が22時、今回それが21時となっているような場合。前回＞今回となっている）
    #         # より、前回極値の方向に進んでいることを意味する（peak消滅であれば上昇、valley消滅であれば下落）
    #         print("　極値の消滅")
    #         tk.line_send("極値消滅:", glp['before_latest_pv'], "NOW:", gl["now"] )
    #     else:
    #         # それ以外は、新たな極値
    #         print(" 新規極値の発生")
    #         # tk.line_send("極値発生:", pv_r_df.iloc[0]['time_jp'], "NOW:", gl["now"])
    #
    #     # 共通処理
    #     glp['before_latest_pv'] = pv_r_df.iloc[0]['time_jp']

    # レンジ確認


    # ■RangeをBBから求める
    dr = d5_df.sort_index(ascending=False)
    # print(dr)
    range_bb = 0  # フラグ
    range_gap = 0.28  # アプリだと0.25くらいにしたいけど、少し広め。原因不明。
    if dr.iloc[0]['bb_upper'] - dr.iloc[0]['bb_lower'] < range_gap:
        # print(" BB確認！！", dr.iloc[0]['time_jp'], dr.iloc[0]['bb_upper'] - dr.iloc[0]['bb_lower'])
        # 最新行がボリバン的にレンジと判断されたばあい
        for index, e in dr.iterrows():  # 現在のボリバンが狭い場合、ボリバンが狭い範囲を求める
            if e['bb_upper'] - e['bb_lower'] < range_gap:
                # BBレンジの成立
                d5_df.loc[index, 'range'] = dr.iloc[0]['high']
                range_bb = 1
                range_bb_gap = e['bb_upper'] - e['bb_lower']
    if range_bb == 1:
        print("　BB的レンジあり")
        # tk.line_send(" BBレンジ判定", dr.iloc[0]['time_jp'], "直前BB幅", range_bb_gap)
        gl_bb['range'] = 1
    else:
        print(" BB的レンジ無し")
        if gl_bb['range'] == 1:
            pass
            # もし前回がBBレンジじゃなかった場合（BBレンジ抜けタイミングとなる）
            # tk.line_send(" BBレンジ解消タイミング判定", dr.iloc[0]['time_jp'], "直前BB幅")


    # ■クロスを利用した部分
    print(" クロス確認")
    # ①直近のクロスwを確認(クロスというより、Long線を超えているか）
    # 5分足のデータを取得（最新部と）
    # cross5_df = d5_df[d5_df['cross'] != 0]  # クロスだけのデータフレーム（直近のクロスを拾いたい場合）
    cross5_df = d5_df.copy()
    cross5_only_df = d5_df[d5_df['cross'] != 0]
    latest_cross5 = cross5_df.iloc[-1]['cross']  #
    latest_cross5_time = cross5_df.iloc[-1]['time_jp']
    latest_cross5_time_dt = datetime.datetime.strptime(latest_cross5_time, data_format)  # %Y/%m/%d %H:%M:%S'
    latest_cross5_price = cross5_df.iloc[-1]['cross_price']
    # print(" 5 ", latest_cross5_time, latest_cross5, latest_cross5_price)
    # 1分足のデータを取得（上の５分足の一つ手前のクロス部）
    cross1_r_df = d1_df[d1_df['cross'] != 0].sort_index(ascending=False)  # 空欄以外を抽出（フィルタ）
    latest_cross1 = cross1_r_df.iloc[1]['cross']  # とりあえず初期値を取得
    latest_cross1_time = cross1_r_df.iloc[1]['time_jp']  # とりあえず初期値を取得
    latest_cross1_time_dt = datetime.datetime.strptime(latest_cross1_time, data_format)
    latest_cross1_price = cross1_r_df.iloc[1]['cross_price']  # とりあえず初期値を取得
    update_flag = 0
    # Rangeかどうかを判定する
    range_flag = 0
    if latest_cross5 != 0:
        c = ans = 0
        r = cross5_only_df.sort_index(ascending=False)
        # print(r['time_jp'])
        for index, e in r.iterrows():  # クロスのみを確認する（直近３個のクロスがレンジ判定化を確認する）
            if c == 0:
                before_cross_index = index
                # print(" f", e['time_jp'])
            else:
                # ６足以内でクロスが来ている場合、レンジの可能性
                if abs(before_cross_index - index) <= 7:
                    ans += 1
                    # print(abs(before_cross_index - index), before_cross_index, index)
                else:
                    # print(" e", e['time_jp'])
                    break
            c += 1
        if ans >= 2:
            range_flag = 1
            print(" ★レンジ相場です",r.iloc[0]['time_jp'], ans)
        else:
            print(" レンジ相場とは言えない", ans)

    # 5分足の直前にある１分足を求める
    for i in range(len(cross1_r_df)):
        if datetime.datetime.strptime(cross1_r_df.iloc[i]['time_jp'], data_format) < latest_cross5_time_dt:
            # 5分足でのクロスの直前（何足前からはさておき）であれば、それで更新する
            latest_cross1 = cross1_r_df.iloc[i]['cross']
            latest_cross1_time = cross1_r_df.iloc[i]['time_jp']
            latest_cross1_time_dt = datetime.datetime.strptime(latest_cross1_time, data_format)
            latest_cross1_price = cross1_r_df.iloc[i]['cross_price']
            update_flag = 1
            break
        else:
            pass
            # print(" oute ", datetime.datetime.strptime(cross1_r_df.iloc[i]['time_jp'], '%Y/%m/%d %H:%M:%S'),
            #       latest_cross5_time_dt)
            # update_flag = 99
    # print(" 1 ", latest_cross1_time, latest_cross1, latest_cross1_price, update_flag)


    # ５分足のクロスがある場合は、１分足も確認して直前（３分以内にあれば）そっちの方向に行くのでは、と推定する
    # print(latest_cross5_time_dt, latest_cross1_time_dt)
    # print((latest_cross5_time_dt - latest_cross1_time_dt).seconds)
    gap_second = (latest_cross5_time_dt - latest_cross1_time_dt).seconds  # ５分足クロスと１分足クロスの時間ギャップ
    if latest_cross5 != 0:
        print(" 直前に５分クロスを確認")
        # その場合、ひとつ前のクロスを確認する（クロスがくっついている場合は無効にするため）
        confirm_time = cross5_only_df.iloc[-1]['time_jp']  # 確認用
        second_cross = datetime.datetime.strptime(cross5_only_df.iloc[-2]['time_jp'], data_format)  # ひとつ前
        jd_range = (latest_cross5_time_dt - second_cross).seconds  # ５分足クロスの１つ目と二つ目の間（レンジかどうかの判断）
        print(" Range判定",confirm_time, second_cross, jd_range)
        if gap_second < 480:  # ５分足と１分足の発生タイミングが近い
            if latest_cross5 == latest_cross1 and jd_range > 600:  # 同じ方向のクロス、かつ、５分足がレンジではない
                print("  理想 5分クロス:", latest_cross5, "1分クロス:", latest_cross1, "5分-1分", gap_second, "5分Range", jd_range, "RangeBB:",range_bb, "BBRange2", gl_bb['range'])
                if glc['for_send'] == 0:
                    tk.line_send("ポジ？", latest_cross5, gap_second, latest_cross5_time_dt,"レンジ有無", range_flag, datetime.datetime.now().replace(microsecond=0))
                    glc['for_send'] = 1  # SnedFlag
            else:
                print("  No(別方向) 5分クロス:", latest_cross5, "1分クロス:", latest_cross1, "5分-1分", gap_second, "5分Range", jd_range)
                # tk.line_send("NNo(別方向) 5分クロス:", latest_cross5, "1分クロス:", latest_cross1, "5分-1分", gap_second, "5分Range", jd_range, "RangeBB:",range_bb, "BBRange2", gl_bb['range'])
        else:
            print(" 理想ではない", gap_second)
    else:
        print(" ５分クロス無し")
        glc['for_send'] = 0  # SnedFlag


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
    ans = f.renzoku_gap_compare(oldest_ans, latest_ans)  # 引数の順番に注意！（左がOldest）
    print(" 折返判定", latest_ans['count'], oldest_ans['count'])
    if ans == 0:
        print("0")
    else:
        order_res = oa.OrderCreate_exe(10000, -1, ans['forward']['target_price'],
                                       0.1, ans['forward']['tp_range'], "STOP",
                                       0.08, "")  # 順思想（順張・現より低い位置に注文入れたい）
        order_res_r = oa.OrderCreate_exe(10000, 1, ans['reverse']['target_price'],
                                         0.1, ans['reverse']['lc_range'], "STOP", 0.08,
                                         "remark")  # 逆思想（順張・現より高い位置に注文入れたい）
        print(" 該当有", ans['forward']['direction'], ans, order_res, order_res_r)
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
        # if past_time.seconds > 60 * gl["order_limit_minute"]:
        #     # 12分以上経過している場合、オーダーをキャンセルする
        #     oa.OrderCancel_All_exe()
        #     tk.line_send("12分以上のオーダーを解除します")
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
                if time_min % 1 == 0 and time_sec == 55:
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
    "spread": 0.012,  # 許容するスプレッド practice = 0.004がデフォ。Live0.008がデフォ
    "tp": 0.035,
    "lc": 0.02,
    "p_order": 2,  # 極値の判定幅
    "test_target_price": 0,
}

# ■出発！
main()
schedule(gl['schedule_freq'], main)

