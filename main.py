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
from time import sleep


def make_order(inspection_ans):
    """
    ポジション取得のメイン
    """
    global gl
    print(" MAKE ORDER")

    # オーダーや情報の取得
    order_dic = inspection_ans['datas']['orders']
    info = inspection_ans['datas']['info']

    # オーダーの実行
    for i in range(len(order_dic)):  # オーダー実行（トラリピ）
        print("各")
        print(order_dic[i])
        oa.OrderCreate_dic_exe(order_dic[i])
    print("  オーダー実行")
    tk.line_send("■折返Position！", datetime.datetime.now().replace(microsecond=0),
                 ",現価格:", info['mid_price'],
                 ",順方向:", info['direction'],
                 ",戻り率:", info["return_ratio"], "(", info['bunbo_gap'], ")",
                 "OLDEST範囲", info["oldest_old"], "-", info['latest_old'], "(COUNT", info["oldest_count"], ")"
                 "LATEST範囲", info['latest_old'], "-", info['latest_late'], "(COUNT", info["latest_count"], ")",
                 )


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
                if pl_pips > 0.025:
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


def inspection_candle():
    """
    オーダーを発行するかどうかの判断。
    オーダーを発行する場合、オーダーの情報も返却する
    返却値：辞書形式
    inspection_ans: オーダー発行有無（０は発行無し。０以外は発行あり）
    datas: 更に辞書形式が入っている
            ans: ０がオーダーなし
            orders: オーダーが一括された辞書形式
            info: 戻り率等、共有の情報
            memo: メモ
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
    d5_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 30}, 1)
    d5_df = f.add_peak(d5_df, gl['p_order'])  # 念のためピーク情報を追加しておく（基本使ってないけど）
    d5_df['middle_price_gap'] = d5_df['middle_price'] - d5_df['middle_price'].shift(1)  # 時間的にひとつ前からいくら変動があったか
    dr = d5_df.sort_index(ascending=False)  # 対象となるデータフレーム（直近が上の方にある）
    d5_df.to_csv(tk.folder_path + 'main_data5.csv', index=False, encoding="utf-8")

    # 直近データの解析（４：２）
    ignore = 1  # 最初（現在を意味する）
    dr_latest_n = 2
    dr_oldest_n = 10
    latest_df = dr[ignore: dr_latest_n + ignore]  # 直近のn個を取得
    oldest_df = dr[dr_latest_n + ignore -1: dr_latest_n + dr_oldest_n + ignore -1]  # 前半と１行をラップさせる。
    latest_ans = f.renzoku_gap_pm(latest_df)  # 何連続で同じ方向に進んでいるか（直近-1まで）
    oldest_ans = f.renzoku_gap_pm(oldest_df)  # 何連続で同じ方向に進んでいるか（前半部分）
    ans_42 = f.judgement_42(oldest_ans, latest_ans, price_dic['mid'])  # 引数順注意。ポジ用の価格情報取得（０は取得無し）

    # 直近のデータの解析（４：３）
    ignore = 1  # 最初（現在を意味する）
    dr_latest_n = 3
    dr_oldest_n = 10
    latest_df = dr[ignore: dr_latest_n + ignore]  # 直近のn個を取得
    oldest_df = dr[dr_latest_n + ignore -1: dr_latest_n + dr_oldest_n + ignore -1]  # 前半と１行をラップさせる。
    latest_ans = f.renzoku_gap_pm(latest_df)  # 何連続で同じ方向に進んでいるか（直近-1まで）
    oldest_ans = f.renzoku_gap_pm(oldest_df)  # 何連続で同じ方向に進んでいるか（前半部分）
    ans_43 = f.judgement_43(oldest_ans, latest_ans, price_dic['mid'])  # 引数順注意。ポジ用の価格情報取得（０は取得無し）

    # 同じ価格が過去の何分にあったかを検討する


    # 上記のansが両方とも成立する（０じゃない）事はない!
    if ans_42["ans"] == 0 and ans_43["ans"] == 0:
        print(" どちらとも成立せず")
        return {"inspection_ans": 0}
    elif ans_42["ans"] != 0:
        print(" 4:2が成立(最初）⇒注文価格情報を返却")
        return {"inspection_ans": 2, "datas": ans_42}
    elif ans_43["ans"] != 0:
        print(" 4:3が成立（次順)⇒注文価格情報を返却")
        return {"inspection_ans": 3, "datas": ans_43}
    elif ans_42["ans"] != 0 and ans_43["ans"] != 0:
        print(" エラー！！！！！両方成立")


def main():
    global gl
    print("■■■", gl["now"])

    price_dic = oa.NowPrice_exe("USD_JPY") # ここでも求めておく（createOrderとは少し異なるかも）

    # 現状の把握
    position_df = oa.OpenTrades_exe()  # ポジション情報の取得
    pending_new_df = oa.OrdersWaitPending_exe()  # ペンディングオーダーの取得(利確注文等は含まない）
    inspection_ans = inspection_candle()  # 直近のローソクデータを解析して、注文の有無を確認する

    # 【オーダー発生とは無関係の部分】ポジション所持時は、ポジションの情報を取得する
    if len(position_df) != 0:
        # ポジション所持時！
        if gl["position_flag"] == 0:
            # ポジション無しから、初めてポジションありになった時
            tk.line_send("■ポジションを取得しました")
            gl['position_flag'] = 1  # ポジションフラグの成立
    elif len(position_df) == 0:
        # ポジション無し時
        if gl["position_flag"] == 1:
            # 前実行時にポジションを持っていた場合（今は持っていない）
            tk.line_send("■ポジションを解消しました", gl['latest_res_pips'])  # latest_res_pips は前回実行時の物（数秒前）
            gl['exe_mode'] = 0
            gl['position_flag'] = 0  # ポジションフラグのリセット

    # 【長期オーダーの削除専用】ペンディング所持時！
    if len(pending_new_df) != 0:
        # 注文中のデータが存在する場合
        past_time = pending_new_df.head(1).iloc[0]["past_time_sec"]  # オーダーした時刻３3
        print("  orderあり（保持中）", past_time)

        limit_time_min = 25
        if past_time > 60 * limit_time_min:  # 60*指定の分
            # 12分以上経過している場合、オーダーをキャンセルする
            oa.OrderCancel_All_exe()
            tk.line_send(str(limit_time_min), "以上のオーダーを解除します■")

    # ★★★メインとなる分岐
    if len(position_df) != 0:
        # ★ポジションがある場合（ポジションがある場合は動かない)
        gl['exe_mode'] = 1
        print("    ポジション有", gl['now'], gl['exe_mode'])
        close_position()
    elif len(position_df) == 0:
        # ★ポジションがない場合
        if len(pending_new_df) == 0:
            # オーダーもなし（ポジションもなし）
            gl['cd_flag'] = 0
            if inspection_ans['inspection_ans'] != 0:
                make_order(inspection_ans)
                oa.OrderBook_exe( price_dic['mid'])
        else:
            # オーダーあり（ポジションはなし）⇒オーダーを取り消してから、ポジションを取得
            # if inspection_ans['inspection_ans'] != 0:
            #     make_order(inspection_ans)
            pass


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
fx_mode = 1  # 1=practice, 0=Live

if fx_mode == 1:  # practice
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
