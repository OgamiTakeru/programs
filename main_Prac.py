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
        self.life = False  # 有効かどうか（オーダー発行からポジションクローズまで）
        self.plan = {}  # plan情報
        self.plan_info = {}  # plan情報をもらった際の付加情報（戻り率等）
        self.order = {"id": 0, "state": 0}  # オーダー情報 (idとステートは初期値を入れておく）
        self.position = {"id": 0, "state": 0}  # ポジション情報 (idとステートは初期値を入れておく））
        self.crcdo = False  # ポジションを変更履歴があるかどうか(複数回の変更を考えるならIntにすべき？）
        self.reorder_next = 0  # リオーダープラン
        self.reorder = 1  # ２回まで再オーダーを実施する
        self.reorder_time = 0  # リオーダーまで６０秒待つ

    def reset(self):
        # 完全にそのオーダーを削除する
        self.life = False
        self.order = {"id": 0, "state": 0}  # オーダー情報 (idとステートは初期値を入れておく）
        self.position = {"id": 0, "state": 0}  # ポジション情報 (idとステートは初期値を入れておく））

    def print_i(self):
        print("   <表示>", self.name, datetime.datetime.now().replace(microsecond=0))
        print("　 【LIFE】", self.life)
        print("　 【CRCDO】", self.crcdo)
        print("　 【ORDER】", self.order['id'], self.order['state'])
        print("　 【POSITIOn】", self.position['id'], self.position['state'])
        # print("　【PLAN】", self.plan)
        # print("　【ORDER】", self.order)
        # print("　【POSITION】", self.position)

    def plan_info_input(self, info):  #
        self.plan_info = info
        self.life = True  # 始まったフラグ

    def plan_input(self, plan):  # ここから始まる！
        self.plan = plan
        self.life = True  # 始まったフラグ

    def make_order(self):
        # Planを元にオーダーを発行する
        order_ans = oa.OrderCreate_dic_exe(self.plan)  # オーダーをセットしローカル変数に結果を格納する
        # print(order_ans)
        self.order = {
            "id": order_ans['order_id'],
            "time": order_ans['order_time'],
            "cancel": order_ans['cancel'],
            "state": "PENDING",  # 強引だけど初期値にPendingを入れておく
            "tp_price": float(order_ans['tp']),
            "lc_price": float(order_ans['lc']),
            "units": float(order_ans['unit']),
            "direction": float(order_ans['unit'])/abs(float(order_ans['unit']))
        }
        self.plan['tp_price'] = float(order_ans['tp'])  # 念のため入れておく（元々計算で入れられるけど。。）
        self.plan['lc_price'] = float(order_ans['lc'])  # 念のため入れておく（元々計算で入れられるけど。。）
        print(" オーダー発行確定", order_ans['order_id'])
        if order_ans['cancel'] == True:  #　キャンセルされている場合は、リセットする
            print("  Cancel発生", self.name)
            self.life = False
            self.reset()
        else:
            self.life = True
            pass  # 送信はMainで実施

    def close_order(self):
        # オーダークローズする関数
        res = oa.OrderCancel_exe(self.order['id'])
        if type(res) is int:
            print("   存在しないorder")
        else:
            self.order['state'] = "CANCELLED"
            self.life = False
            tk.line_send("  オーダー解消", self.order['id'])

    def close_position(self):
        # ポジションをクローズする関数
        res = oa.TradeClose_exe(self.position['id'],None,"")
        if type(res) is int:
            print("   存在しないposition")
        else:
            self.position['state'] = "CLOSED"
            self.life = False
            tk.line_send("  ポジション解消", self.position['id'])

    def update_information(self):  # orderとpositionを両方更新する
        # どちらか一つでもOpenなPlanがある場合は、exemode=1を維持する！！！

        # （０）途中からの再起動の場合、lifeがおかしいので。。あと、ポジション解除後についても必要（CLOSEの場合は削除する？）ｓ
        print(" □□情報を更新します", self.name)
        if self.life == True:
            # （０）情報取得 + 変化点キャッチ（情報を埋める前に変化点をキャッチする）
            temp = oa.OrderDetailsState_exe(self.order['id'])
            # （1-1)　変化点を算出（ポジションの新規取得等）
            if self.order['state'] == "PENDING" and temp['order_state'] == 'FILLED':  # 現orderあり⇒約定（取得時）
                print("  ★position取得！")
                tk.line_send("取得！", self.name, datetime.datetime.now().replace(microsecond=0))
            elif self.position['state'] == "OPEN" and temp['position_state'] == "CLOSED":  # 現ポジあり⇒ポジ無し（終了時）
                print("  ★position解消")
                tk.line_send("  解消", self.name, temp['position_pips'], datetime.datetime.now().replace(microsecond=0))
                self.life = False
            elif self.order['state'] == "PENDING" and temp['order_state'] == 'CANCELLED':  # （取得時）
                print("  ★order消滅")
                self.life = False


            # （３）情報を更新
            self.order['id'] = temp['order_id']
            self.order['time'] = temp['order_time']
            self.order['time_past'] = float(temp['order_time_past'])
            self.order['units'] = float(temp['order_units'])
            self.order['price'] = float(temp['order_price'])
            self.order['state'] = temp['order_state']
            self.order['id'] = temp['order_id']

            self.position['id'] = temp['position_id']
            self.position['time'] = temp['position_time']
            self.position['time_past'] = float(temp['position_time_past'])
            self.position['price'] = float(temp['position_time_past'])
            self.position['units'] = 0  # そのうち導入したい
            self.position['state'] = temp['position_state']
            self.position['realizePL'] = float(temp['position_realizePL'])
            self.position['pips'] = float(temp['position_pips'])
            self.position['close_time'] = temp['position_close_time']

            self.print_i()  # 情報の表示
            print("    order保持時間", self.order['time_past'])

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
                    self.crcdo = True  # main本体で、ポジションを取る関数で解除する
                print("    [ポジ有] LC底上げ基準プラス未達")
            elif self.crcdo == True:
                print("    CRCDO済")
            elif self.position['state'] != "OPEN":
                print("  　ポジション無し")

        else:
            pass
            # print("  LIFE = FALSE")


def inspection_next_action():  # クラスはグローバル関数の為引数で渡される必要なし
    # オーダー希望（基準達成）があった場合、現在のオーダーをどうするか（新オーダー不可　or 全てキャンセルして新オーダーか）
    # 新オーダー不可の場合は、オーダーが二つとも存在＋かつ２０分経過指定いない場合、fw.reorder_nextが１の場合(リオーダー待ち)
    limit_time_min = 20
    if (fw.order['state'] == "PENDING" and fw.order['time_past'] < 60 * limit_time_min) and (
            rv.order['state'] == "PENDING" and rv.order['time_past'] < 60 * limit_time_min):
        new_order = False
    elif fw.reorder_next == 1:
        new_order = False
        print(" ★★★奇遇　リオーダー待ち中の真意オーダータイミング")
    else:
        new_order = True

    # モードの検討
    # モード１（随時確認モード）は、いずれかのオーダーのlifeがTrueの場合
    if fw.life == True or rv.life == True:
        exe_mode = 1
    else:
        exe_mode = 0

    return {"exe_mode": exe_mode, "new_order": new_order}


def main():
    global gl
    print("■■■", gl["now"], gl["exe_mode"])

    # ★最新の情報にアップデートする
    # 状況の確認(オーダーを入れるかの判断用）
    order_judge = inspection_candle()  # [return] ans(int), order_plan(dic&arr), jd_info(dic)
    # if gl['count'] == 0:  # testモード
    #     order_judge = order_judge_test

    # 状況の確認(LC底上げや、オーダーの時間切れ判定はここで行う）
    fw.update_information()
    rv.update_information()

    # next_actionの確認
    next = inspection_next_action()  # exe_mode, new_order

    #ExeModeの設定
    gl['exe_mode'] = next['exe_mode']  #exe_modeを設定する


    # 初のオーダーの発行
    if order_judge['ans'] == 0:
        pass
        print("  オーダーしない")
    else:
        print("  オーダー条件は達成")
        if next['new_order']:
            print("  ★エントリー確定 クロース＋オーダー発注")
            # 全てのオーダー、ポジションをクローズする
            for i in range(len(classes)):
                classes[i].close_order()
                classes[i].close_position()
            # オーダー情報を順に格納していく
            for i in range(len(classes)):
                classes[i].plan_info_input(order_judge['jd_info'])
                classes[i].plan_input(order_judge['order_plan'][i])
            # オーダーを発行していく
            for i in range(len(classes)):
                classes[i].make_order()
            # 情報をLINEで送付する
            temp = order_judge['jd_info']
            tk.line_send("■折返Position！", datetime.datetime.now().replace(microsecond=0),
                         ",戻り率:", temp['return_ratio'],
                         "OLDEST範囲", temp["oldest_old"], "-", temp['latest_old'], "(COUNT", temp["oldest_count"],
                         ")LATEST範囲",temp['latest_old'], "-", temp['latest_late'], "(COUNT", temp["latest_count"], ")",
                         )
            print("  　まとめてオーダー発注")




    # Next判断
    # 1 fwが利確している場合、Rvオーダーは削除
    # 2 fwがロスカしてる場合、rvオーダーを維持し、リオーダーを入れる(fwのロスカ部分に逆張り?現在価格基準？）
    if fw.position['state'] == "CLOSED" and fw.position['pips'] >= 0:
        if rv.life==True:
            tk.line_send("  FW利確済⇒RVオーダー解消で今回終了")
            rv.close_order()
            rv.reset()  # 完全終了(中身も消去）
    elif fw.position['state'] == "CLOSED" and fw.position['pips'] <= 0:
        if fw.reorder != 0:  # リオーダー回数が余っている場合
            if fw.reorder_time == 0:
                print(" リオーダー受付")
                # 初めてリオーダーを受け付ける場合
                fw.reorder_time = datetime.datetime.now().replace(microsecond=0)
                fw.reorder_next = 1  # リオーダー待ちフラグ（新規オーダーに阻害されない）
                tk.line_send("  リオーダー受付！！", fw.reorder_time)
            else:  # リオーダー設定後、待ち状態
                time_past = (datetime.datetime.now().replace(microsecond=0) - fw.reorder_time).seconds
                if time_past > 30:  # ３０秒後にリオーダー実施
                    oa.OrderCancel_All_exe()  # 露払い
                    oa.TradeAllColse_exe()  # 露払い
                    tk.line_send("  リオーダー実施！！", fw.order['lc_price'], fw.order['direction'])
                    fw.reset()  # リセット ポジションもリセットされる⇒ここには入らなくなる(LC情報も消えるので注意）
                    fw.reorder = fw.reorder - 1
                    # 設定価格の入れ替え（LC価格をリオーダー価格に） 他のオーダーとの兼ね合いも考えないと。。
                    fw.plan['price'] = fw.plan['lc_price'] + (fw.plan['ask_bid'] * 0.05)  # 余裕度を入れる
                    fw.plan['units'] = 80005
                    fw.plan['tp_range'] = 0.05  # 余裕度を入れる
                    fw.plan['lc_range'] = 0.05
                    fw.plan['type'] = 'STOP'
                    print(fw.plan)
                    fw.make_order()
                    # rvもキャンセルしておく
                    rv.close_order()
                    fw.close_position()
                else:
                    print(" リオーダー待機中")
        else:
            print(" □リオーダー実施ずみ")

    print("")
    gl['count'] = gl['count'] + 1






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
        if 3 <= time_hour < 6:
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
    "count": 0,
    "exe_mode": 0,  # 実行頻度モードの変更（基本的は０）
    "exe_mode_sec": 2,  # 実行頻度モードの変更（基本的は０）
    "schedule_freq": 1,  # 間隔指定の秒数（N秒ごとにスケジュールで処理を実施する）
    "now_h": 0,
    "now_m": 0,
    "now_s": 0,
    'now': datetime.datetime.now().replace(microsecond=0),
    "spread": 0.02,  # 0.012,  # 許容するスプレッド practice = 0.004がデフォ。Live0.008がデフォ
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
classes = [fw, rv]  # クラスをセットで持つ
print(env)

price_dic = oa.NowPrice_exe("USD_JPY")

test_f_order = {
    "price": price_dic['mid'],
    "lc_price": 0.05,
    "lc_range": 0.005,  # ギリギリまで。。
    "tp_range": 0.012,  # latest_ans['low_price']+0 if direction_l == 1 else latest_ans['high_price']-0
    "ask_bid": -1,
    "units": 6000,
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
    "units": 5000,
    "type": "STOP",
    "tr_range": 0.10,  # ↑ここまでオーダー
    "mind": 1,
    "memo": "forward"
}
ans_info_test = {"return_ratio": 0, "bunbo_gap": 0,"oldest_old": 0, "latest_late": 0,
            "latest_old": 0, "direction": 0,"mid_price": 0, "oldest_count": 0, "latest_count": 0}
order_judge_test = {
    "ans": 1,
    'order_plan':[test_f_order, test_r_order],
    'jd_info': ans_info_test
}

# ■出発！
oa.OrderCancel_All_exe()  # 露払い
oa.TradeAllColse_exe()  # 露払い
main()
schedule(gl['schedule_freq'], main)
