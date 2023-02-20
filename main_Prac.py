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


def make_order(inspection_ans):
    """
    ポジション取得のメイン
    オーダー発行し、結果を返却
    結果には、オーダー予定情報からオーダーIDまでが付属している
    """
    print(" MAKE ORDER")

    # オーダーや情報の取得
    order_dic_arr = inspection_ans['order_plan']
    info = inspection_ans['jd_info']

    ref_id = []

    # オーダーの実行
    for i in range(len(order_dic_arr)):  # オーダー実行（トラリピ）
        res = oa.OrderCreate_dic_exe(order_dic_arr[i])
        order_dic_arr[i]['order_id'] = res['order_id']  # ★オーダーIDを追記（０はミスorder）
    print("  オーダー実行")
    tk.line_send("■折返Position！", datetime.datetime.now().replace(microsecond=0),
                 ref_id,
                 ",現価格:", info['mid_price'],
                 ",順方向:", info['direction'],
                 ",戻り率:", info["return_ratio"], "(", info['bunbo_gap'], ")",
                 "OLDEST範囲", info["oldest_old"], "-", info['latest_old'], "(COUNT", info["oldest_count"], ")"
                 "LATEST範囲", info['latest_old'], "-", info['latest_late'], "(COUNT", info["latest_count"], ")",
                 )
    return order_dic_arr


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
    ans = f.judgement_42(oldest_ans, latest_ans, price_dic['mid'])  # 引数順注意。ポジ用の価格情報取得（０は取得無し）

    return {"ans": ans["ans"], "order_plan": ans['order_plan'], "jd_info": ans["jd_info"]}


# 個のオーダーの情報を集約するクラス
class order_information:
    def __init__(self, name, oa):
        self.oa = oa  # クラス変数でもいいが、LiveとPracticeの混在ある？　引数でもらう
        self.name = name  # FwかRvかの表示用。引数でもらう
        self.life = False  # 有効かどうか
        self.plan = {}  # plan情報
        self.plan_info = {}  # plan情報をもらった際の付加情報（戻り率等）
        self.order = {"id": 0, "state": 0}  # オーダー情報 (idとステートは初期値を入れておく）
        self.position = {"id": 0, "state": 0}  # ポジション情報 (idとステートは初期値を入れておく））
        self.crcdo = False  # ポジションを変更履歴があるかどうか(複数回の変更を考えるならIntにすべき？）
        self.reorder = 2  # ２回まで再オーダーを実施する

    def reset(self):
        self.life = False
        self.order = {"id": 0, "state": 0}  # オーダー情報 (idとステートは初期値を入れておく）
        self.position = {"id": 0, "state": 0}  # ポジション情報 (idとステートは初期値を入れておく））

    def print_i(self):
        print("  <表示>", self.name, datetime.datetime.now().replace(microsecond=0))
        print("【LIFE】", self.life)
        print("【PLAN】", self.plan)
        print("【ORDER】", self.order)
        print("【POSITION】", self.position)

    def plan_info_input(self, info):  #
        self.plan_info = info
        self.life = True  # 始まったフラグ

    def plan_input(self, plan):  # ここから始まる！
        self.plan = plan
        self.life = True  # 始まったフラグ

    def make_order(self):
        order_ans = oa.OrderCreate_dic_exe(self.plan)  # オーダーをセットしローカル変数に結果を格納する
        gl['exe_mode'] = 1
        # print(order_ans)
        self.order = {
            "id": order_ans['order_id'],
            "time": order_ans['order_time'],
            "cancel": order_ans['cancel'],
            "state": "PENDING",  # 強引だけど初期値にPendingを入れておく
        }
        if order_ans['cancel'] == True:  #　キャンセルされている場合は、リセットする
            print("  Cancel発生", self.name)
            self.life = False
            self.reset()
        else:
            pass  # 送信はMainで実施

    def update_information(self):  # orderとpositionを両方更新する
        # どちらか一つでもOpenなPlanがある場合は、exemode=1を維持する！！！

        # （０）途中からの再起動の場合、lifeがおかしいので。。あと、ポジション解除後についても必要（CLOSEの場合は削除する？）ｓ
        print(" □□情報を更新します", self.name)
        if self.life == True:
            # （０）情報取得 + 変化点キャッチ（情報を埋める前に変化点をキャッチする）
            temp = oa.OrderDetailsState_exe(self.order['id'])
            # （1)　変化点を算出（ポジションの新規取得等）
            # print(" ★確認用 ORDE", self.order['state'], temp['order_state'], "POSI", self.position['state'], temp['position_state'])
            if self.order['state'] == "PENDING" and temp['order_state'] == 'FILLED':  # 現ポジ無し⇒ポジ有（取得時）
                print("  ★position取得！")
                tk.line_send("取得！", self.name)
                gl['exe_mode'] = 1  # これは基本不要かも
            elif self.position['state'] == "OPEN" and temp['position_state'] == "CLOSED":  # 現ポジあり⇒ポジ無し（終了時）
                print("  ★position解消")
                tk.line_send("  解消", self.name)
                gl['exe_mode'] = 0
                self.life == False

            # （３）情報を更新
            self.order = {  # オーダー情報登録
                "id": temp['order_id'],
                "time": temp['order_time'],
                "time_past": float(temp['order_time_past']),
                "units": float(temp['order_units']),
                "price": float(temp['order_price']),  # Planの価格と同じ（はず）
                "state": temp['order_state'],
            }
            self.position = {  # ポジション情報登録
                "id": temp['position_id'],
                "time": temp['position_time'],
                "time_past": float(temp['position_time_past']),
                "price": float(temp['position_price']),  # 約定時にorder価格とはずれる可能性
                "units": 0,  # そのうち導入したい
                "state": temp['position_state'],
                "realizePL": float(temp['position_realizePL']),
                "pips": float(temp['position_pips']),
                "close_time": temp['position_close_time']
            }
            self.print_i()  # 情報の表示
            print("   order保持時間", self.order['time_past'])

            # （４）オーダーの解消の実施
            limit_time_min = 25
            if self.order['time_past'] > 60 * limit_time_min:  # 60*指定の分 かつ orderOpenだったら
                if self.order['state'] == 'PENDING':  # 注文が生きている場合はキャンセル
                    oa.OrderCancel_exe(self.order['id'])  # オーダーキャンセル
                    tk.line_send(str(limit_time_min), "以上のオーダーを解除します", self.name)
                    self.life = False
                    self.reset()
                    print("　★CANCEl後")
                    self.print_i()  # 情報の表示
                else:  # CANCELEDかFILLEDの場合はオーダーは無効
                    print(" 　オーダー解除不要（すでに解除済）")

            # (５) ポジションのLC底上げを実施
            if self.crcdo == False and self.position['state'] == "OPEN":  # ポジションのCRCDO歴がない場合⇒ポジションLC調整を行う可能性
                p = self.position
                o = self.order
                if p['pips'] > 0.015:  # ある程度のプラスがあれば、LC底上げを実施する
                    cd_line = p['price'] - 0.005 if o['units'] < 0 else p['price'] + 0.005
                    data = {
                        "stopLoss": {"price": str(cd_line), "timeInForce": "GTC",},
                        "trailingStopLoss": {"distance": 0.05, "timeInForce": "GTC",},
                    }
                    oa.TradeCRCDO_exe(p['id'], data)  # ポジションを変更する
                    tk.line_send("■(BOX)LC値底上げ", self.name, p['price'], "⇒", cd_line)
                    self.crcdo == True  # main本体で、ポジションを取る関数で解除する
                else:
                    print("  [ポジ有]LC底上げ基準プラス未達")
            else:
                print("  CRCDO済 or ポジション無し")

        else:
            print("  LIFE = FALSE")



def main():
    global gl
    print("■■■", gl["now"], gl["exe_mode"])

    # オーダー状況を確認
    position_df = oa.OpenTrades_exe()  # ポジション情報の取得
    orders_df = oa.OrdersWaitPending_exe()  # ペンディングオーダーの取得(利確注文等は含まない）

    # 状況の確認(オーダーを入れるかの判断用）
    order_judge = inspection_candle()  # [return] ans(int), order_plan(dic&arr), jd_info(dic)
    # order_judge = order_judge_test

    # 初のオーダーの発行
    if order_judge['ans'] == 0:
        print("  オーダーしない")
    else:
        print("  オーダー条件は達成")
        # print(order_judge)
        if len(position_df) == 0 and len(orders_df) == 0:  # 何もない場合はオーダー基準で確実に
            print("  ★エントリー確定")
            fw.plan_info_input(order_judge['jd_info'])
            fw.plan_input(order_judge['order_plan'][0])  # 順思想クラスに、順方向の予定を追加
            rv.plan_info_input(order_judge['jd_info'])
            rv.plan_input(order_judge['order_plan'][1])  # 逆思想クラスに、逆思想の予定を追加
            temp = order_judge['jd_info']
            tk.line_send("■折返Position！", datetime.datetime.now().replace(microsecond=0),
                         ",戻り率:", temp['return_ratio'],
                         "OLDEST範囲", temp["oldest_old"], "-", temp['latest_old'], "(COUNT", temp["oldest_count"],
                         ")LATEST範囲",temp['latest_old'], "-", temp['latest_late'], "(COUNT", temp["latest_count"], ")",
                         )
            # for i in range(len(gl['classes'])):
            #     print(" 巡回表示")
            #     gl["classes"][i].printf()
            print("  　まとめてオーダー発注")
            fw.make_order()
            rv.make_order()
        else:
            print("  　オーダーかポジションあり")
            pass

    # 状況の確認(LC底上げや、オーダーの時間切れ判定はここで行う）
    fw.update_information()
    rv.update_information()

    # Next判断
    # 1 fwが利確している場合、Rvオーダーは削除
    # 2 fwがロスカしてる場合、rvオーダーを維持し、



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
                if time_min % 1 == 0 and time_sec % gl["exe_mode_sec"] == 0:  # (time_sec == 9 or time_sec == 39):
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
    "exe_mode_sec": 2,  # 実行頻度モードの変更（基本的は０）
    "schedule_freq": 1,  # 間隔指定の秒数（N秒ごとにスケジュールで処理を実施する）
    "now_h": 0,
    "now_m": 0,
    "now_s": 0,
    'now': datetime.datetime.now().replace(microsecond=0),
    "spread": 0.3,  # 0.012,  # 許容するスプレッド practice = 0.004がデフォ。Live0.008がデフォ
    "p_order": 2,  # 極値の判定幅
    "position_flag": 0,  # ポジションが消えたタイミングを取得するためのフラグ
    "position_f_direction": 0,  # ポジションが買いか売りか
    "position_mind": 0,  # ポジションが順思想が、逆思想が
    "orders": [],
    "ag_orders": [],
    "cd_flag": 0,  # 利確幅を途中で変えた時のフラグ
    "add_flag": 0,  # 途中でポジションを追加しに行く処理
    "midnight_close": 0,
    "latest_res_pips": 0,  # 最終的なマイナス（最後の数行は推定になるが）
    "ids": [],
    "classes":[],
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
fw = order_information("fw ", oa)  # 順思想のオーダーを入れるクラス
rv = order_information("rv ", oa)  # 逆思想のオーダーを入れるクラス
gl['classes'] = [fw, rv]  # クラスをセットで持つ
print(env)

price_dic = oa.NowPrice_exe("USD_JPY")

test_f_order = {
    "price": price_dic['mid'],
    "lc_price": 0.05,
    "lc_range": 0.012,  # ギリギリまで。。
    "tp_range": 0.012,  # latest_ans['low_price']+0 if direction_l == 1 else latest_ans['high_price']-0
    "ask_bid": -1,
    "units": 5000,
    "type": "MARKET",
    "tr_range": 0.10,  # ↑ここまでオーダー
    "mind": 1,
    "memo": "forward"
}
test_r_order = {
    "price": price_dic['mid']+0.1,
    "lc_price": 0.05,
    "lc_range": 0.028,  # ギリギリまで。。
    "tp_range": 0.022,  # latest_ans['low_price']+0 if direction_l == 1 else latest_ans['high_price']-0
    "ask_bid": 1,
    "units": 6000,
    "type": "STOP",
    "tr_range": 0.10,  # ↑ここまでオーダー
    "mind": 1,
    "memo": "forward"
}
order_judge_test = {
    "ans": 1,
    'order_plan':[test_f_order, test_r_order]
}
# ■出発！
oa.OrderCancel_All_exe()  # 露払い
oa.TradeAllColse_exe()  # 露払い
main()
schedule(gl['schedule_freq'], main)
