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
    # data_format = '%Y/%m/%d %H:%M:%S'
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
    oldest_df = dr[dr_latest_n + ignore - 1: dr_latest_n + dr_oldest_n + ignore - 1]  # 前半と１行をラップさせる。
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
        self.order = {"id": 0, "state": "", "time_past": 0}  # オーダー情報 (idとステートは初期値を入れておく）
        self.position = {"id": 0, "state": "", "time_past": 0}  # ポジション情報 (idとステートは初期値を入れておく））
        self.crcdo = False  # ポジションを変更履歴があるかどうか(複数回の変更を考えるならIntにすべき？）
        self.reorder_next = 0  # リオーダープラン
        self.reorder = 1  # ２回まで再オーダーを実施する
        self.reorder_time = 0  # リオーダーまで６０秒待つ
        self.reorder_latest = datetime.datetime.now().replace(microsecond=0)
        self.now_price = 0

    def reset(self):
        # 完全にそのオーダーを削除する
        self.life = False
        self.order = {"id": 0, "state": "", "time_past": 0}  # オーダー情報 (idとステートは初期値を入れておく）
        self.position = {"id": 0, "state": "", "time_past": 0}  # ポジション情報 (idとステートは初期値を入れておく））
        if self.name == "fw_reorder":
            self.name = "fw"  # 名前を元に戻す（名前での処理有）

    def print_i(self):
        print("   <表示>", self.name, datetime.datetime.now().replace(microsecond=0))
        print("　 【LIFE】", self.life)
        print("　 【CRCDO】", self.crcdo)
        print("　 【ORDER】", self.order['id'], self.order['state'])
        print("　 【POSITIOn】", self.position['id'], self.position['state'])
        # print("　【PLAN】", self.plan)
        # print("　【ORDER】", self.order)
        # print("　【POSITION】", self.position)

    def print_all(self):
        print("   <表示>", self.name, datetime.datetime.now().replace(microsecond=0))
        print("　 【LIFE】", self.life)
        print("　 【CRCDO】", self.crcdo)
        print("　　【PLAN】", self.plan)
        print("　　【ORDER】", self.order)
        print("　　【POSITION】", self.position)

    def plan_info_input(self, info):  #
        self.plan_info = info

    def plan_input(self, plan):
        self.plan = plan

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
            # "ask_bid": order_ans['ask_bid'],

            "direction": float(order_ans['unit'])/abs(float(order_ans['unit']))
        }
        self.plan['tp_price'] = float(order_ans['tp'])  # 念のため入れておく（元々計算で入れられるけど。。）
        self.plan['lc_price'] = float(order_ans['lc'])  # 念のため入れておく（元々計算で入れられるけど。。）
        print(" オーダー発行確定", order_ans['order_id'])
        if order_ans['cancel']:  # キャンセルされている場合は、リセットする
            print("  Cancel発生", self.name)
            self.life = False
            self.reset()
        else:
            self.life = True  # LIFEのONはここでのみ実施
            pass  # 送信はMainで実施

    def close_order(self):
        # オーダークローズする関数
        if self.life:
            res = oa.OrderCancel_exe(self.order['id'])
            if type(res) is int:
                print("   存在しないorder（ERROR）")
            else:
                self.order['state'] = "CANCELLED"
                self.life = False
                tk.line_send("  オーダー解消", self.order['id'])
        else:
            print("   order無し")

    def close_position(self):
        # ポジションをクローズする関数
        if self.life:
            res = oa.TradeClose_exe(self.position['id'], None, "")
            if type(res) is int:
                print("   存在しないposition（ERRO）")
            else:
                self.position['state'] = "CLOSED"
                self.life = False
                tk.line_send("  ポジション解消", self.position['id'])
        else:
            print("    position無し")

    def update_information(self):  # orderとpositionを両方更新する

        # （０）途中からの再起動の場合、lifeがおかしいので。。あと、ポジション解除後についても必要（CLOSEの場合は削除する？）ｓ
        # STATEの種類
        # order "PENDING" "CANCELLED" "FILLED"
        # position "OPEN" "CLOSED"
        print(" □□情報を更新します", self.name)
        if self.life:  # LifeがTrueの場合は、必ずorderIDが入っている
            print(" □□", self.order['id'], self.position['id'])
            # 現在価格を求めておく
            price_dic_reorder = oa.NowPrice_exe("USD_JPY")
            if self.plan['ask_bid'] > 0:  # プラス(買い) オーダーの場合
                self.now_price = float(price_dic_reorder["ask"])
            else:
                self.now_price = float(price_dic_reorder["bid"])

            # （０）情報取得 + 変化点キャッチ（情報を埋める前に変化点をキャッチする）
            temp = oa.OrderDetailsState_exe(self.order['id'])
            # （1-1)　変化点を算出しSTATEを変更する（ポジションの新規取得等）
            if self.order['state'] == "PENDING" and temp['order_state'] == 'FILLED':  # 現orderあり⇒約定（取得時）
                print("  ★position取得！")
                tk.line_send("取得！", self.name, datetime.datetime.now().replace(microsecond=0))
            elif self.position['state'] == "OPEN" and temp['position_state'] == "CLOSED":  # 現ポジあり⇒ポジ無し（終了時）
                print("  ★position解消")
                tk.line_send("  解消", self.name, temp['position_pips'], datetime.datetime.now().replace(microsecond=0))
                self.life = False
                self.print_all()
                self.reset()  # ここでリセットする必要があるかどうか？
            elif self.order['state'] == "PENDING" and temp['order_state'] == 'CANCELLED':  # （取得時）
                print("  ★order消滅")
                tk.line_send("　　order消滅！", self.name, datetime.datetime.now().replace(microsecond=0))
                self.life = False
                self.print_all()
                self.reset()
            else:
                print(" 　　状態変化なし")

            # （３）情報を更新
            # print("   ★エラーテスト", temp['order_time'], type(temp['position_time']))
            self.order['id'] = temp['order_id']
            self.order['time'] = 0 if type(temp['order_time']) == int else datetime.datetime.strptime(temp['order_time'], '%Y/%m/%d %H:%M:%S')
            self.order['time_past'] = int(temp['order_time_past'])  # 諸事情でプラス２秒程度ある
            self.order['units'] = int(temp['order_units'])
            self.order['price'] = float(temp['order_price'])
            self.order['state'] = temp['order_state']
            self.order['id'] = temp['order_id']

            self.position['id'] = temp['position_id']
            self.position['time'] = 0 if type(temp['position_time']) == int else datetime.datetime.strptime(temp['position_time'], '%Y/%m/%d %H:%M:%S')
            self.position['time_past'] = int(temp['position_time_past'])  # 諸事情でプラス２秒程度ある
            self.position['price'] = float(temp['position_price'])
            self.position['units'] = 0  # そのうち導入したい
            self.position['state'] = temp['position_state']
            self.position['realizePL'] = float(temp['position_realizePL'])
            self.position['pips'] = float(temp['position_pips'])
            self.position['close_time'] = temp['position_close_time']

            self.print_i()  # 情報の表示
            # print("    order保持時間", self.order['time_past'])

            # (4)矛盾系の状態を解消する（部分解消などが起きた場合に、idがあるのにStateがないなど、矛盾があるケースあり。
            if self.position['id'] != 0 and self.position['state'] == 0:
                # IDがあるのにStateが登録されていない⇒エラー
                tk.line_send("  ID矛盾発生⇒強制解消処理", self.position['id'], self.position['state'])
                self.reset()


            # (５) ポジションのLC底上げを実施
            if self.crcdo is False and self.position['state'] == "OPEN":  # ポジションのCRCDO歴がない場合⇒ポジションLC調整を行う可能性
                if self.name == "fw_reorder":  # 自分がfw_reorderだった場合
                    print("    リオーダーのLC底上げ")
                    p = self.position
                    o = self.order
                    margin = abs(p['pips'])/2
                    cl_line_test = self.now_price + margin if self.plan['ask_bid'] < 0 else self.now_price - margin
                    cl_span = 60  # 1分に１回しか更新しない
                    reorder_past = (datetime.datetime.now().replace(microsecond=0) - self.reorder_latest).seconds  # 経過時間確認
                    if p['pips'] > 0.015 and reorder_past > cl_span:  # ある程度のプラスがあれば、LC底上げを実施する
                        cd_line = cl_line_test + 0 if self.plan['ask_bid'] < 0 else cl_line_test - 0  # 微プラス
                        print("■", p['price'], o['units'])
                        data = {
                            "stopLoss": {"price": str(cd_line), "timeInForce": "GTC"},
                            "trailingStopLoss": {"distance": 0.05, "timeInForce": "GTC"},
                        }
                        oa.TradeCRCDO_exe(p['id'], data)  # ポジションを変更する
                        tk.line_send("■(ReOrder)LC値底上げ", self.name, p['price'], "⇒", cd_line, o['units'],
                                     self.plan['ask_bid'], self.position['pips'], reorder_past, self.reorder_latest,
                                     "margin", margin, " nowprice", self.now_price)
                        self.crcdo = True  # main本体で、ポジションを取る関数で解除する
                        self.reorder_latest = datetime.datetime.now().replace(microsecond=0)
                    print("    [ポジ有] (ReOrder)LC底上げ基準プラス未達")

                else:  # 通常のLC底上げ
                    p = self.position
                    o = self.order
                    if p['pips'] > 0.015:  # ある程度のプラスがあれば、LC底上げを実施する
                        # cd_line = p['price'] - 0.005 if self.plan['ask_bid'] < 0 else p['price'] + 0.005  # 微プラス
                        cd_line = p['price'] + 0.005 if self.plan['ask_bid'] < 0 else p['price'] - 0.005  # 微プラス
                        print("■", p['price'], o['units'])
                        data = {
                            "stopLoss": {"price": str(cd_line), "timeInForce": "GTC"},
                            "trailingStopLoss": {"distance": 0.05, "timeInForce": "GTC"},
                        }
                        oa.TradeCRCDO_exe(p['id'], data)  # ポジションを変更する
                        tk.line_send("■(通常)LC値底上げ", self.name, p['price'], "⇒", cd_line, o['units'], self.plan['ask_bid'])
                        self.crcdo = True  # main本体で、ポジションを取る関数で解除する
                    print("    [ポジ有] LC底上げ基準プラス未達")
            elif self.crcdo:
                print("    CRCDO済")
            elif self.position['state'] != "OPEN":
                print("  　ポジション無し")
            else:
                pass


def inspection_next_action():  # クラスはグローバル関数の為引数で渡される必要なし
    # オーダー希望（基準達成）があった場合、現在のオーダーをどうするか（新オーダー不可　or 全てキャンセルして新オーダーか）
    # 新オーダー不可の場合は、オーダーが二つとも存在＋かつ２０分経過指定いない場合、fw.reorder_nextが１の場合(リオーダー待ち)
    limit_time_min = 6
    now = datetime.datetime.now().replace(microsecond=0)
    # オーダーが完結した後も、オーダー発行時点からの時間を計測する
    if fw.order['id'] == 0:  # まだない
        fw_time_past_for_jd = 0
    else:
        print("    ", fw.order['time'], type(fw.order['time']))
        fw_time_past_for_jd = (now-fw.order['time']).seconds
    if rv.order['id'] == 0:  # まだない
        rv_time_past_for_jd = 0
    else:
        print("    ", rv.order['time'], type(rv.order['time']))
        rv_time_past_for_jd = (now-rv.order['time']).seconds

    print(fw.order['state'], fw.order['time_past'], rv.order['state'], rv.order['time_past'],
          fw_time_past_for_jd, rv_time_past_for_jd, "@inspectionFunc")
    # if 0 < fw.order['time_past'] < 60 * limit_time_min or 0 < rv.order['time_past'] < 60 * limit_time_min:
    if 0 < fw_time_past_for_jd < limit_time_min * 60 or 0 < rv_time_past_for_jd < limit_time_min * 60:
        print(" 　直後のオーダーの可能性あり")
        new_order = False
    elif fw.reorder_next == 1:
        new_order = False
        print(" 　★★★奇遇　リオーダー待ち中の真意オーダータイミング")
    else:
        new_order = True

    # モードの検討
    # モード１（随時確認モード）は、いずれかのオーダーのlifeがTrueの場合
    if fw.life or rv.life:
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
    next_action = inspection_next_action()  # exe_mode, new_order

    # ExeModeの設定
    gl['exe_mode'] = next_action['exe_mode']  # exe_modeを設定する

    # 初のオーダーの発行
    if order_judge['ans'] == 0:
        pass
        # print("  オーダーしない")
    else:
        print("  オーダー条件は達成")
        if next_action['new_order']:
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
                         ")LATEST範囲", temp['latest_old'], "-", temp['latest_late'], "(COUNT", temp["latest_count"], ")",
                         )
            print("  　まとめてオーダー発注")

    # Next判断
    # 1 fwが利確している場合、Rvオーダーは削除
    # 2 fwがロスカしてる場合、rvオーダーを維持し、リオーダーを入れる(fwのロスカ部分に逆張り?現在価格基準？）
    if fw.position['state'] == "CLOSED" and fw.position['pips'] >= 0:
        if rv.life:
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
                    fw.reset()  # リセット ポジションもリセットされる⇒ここには入らなくなる(LC情報も消えるので注意）
                    fw.reorder = fw.reorder - 1
                    # 設定価格の入れ替え（LC価格をリオーダー価格に） 他のオーダーとの兼ね合いも考えないと。。
                    price_dic_reorder = oa.NowPrice_exe("USD_JPY")
                    if fw.plan['ask_bid'] > 0:  # プラス(買い) オーダーの場合
                        now_price = float(price_dic_reorder["ask"])
                    else:
                        now_price = float(price_dic_reorder["bid"])
                    print("    ReOrder価格", now_price, fw.plan['ask_bid'])

                    # 参考価格を求める
                    d5_re_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 2}, 1)
                    high_temp = d5_re_df["high"].max()
                    low_temp = d5_re_df["low"].min()
                    if fw.plan['ask_bid'] < 0:
                        target_price = high_temp  # 売りの場合は、Max値
                    else:
                        target_price = low_temp  # 売りの場合は、Max値

                    # fw.plan['price'] = fw.plan['lc_price'] - (fw.plan['ask_bid'] * 0.01)  # 余裕度を入れる
                    fw.name = "fw_reorder"
                    fw.plan['price'] = now_price - (int(fw.plan['ask_bid']) * 0.04)  # 余裕度を入れる
                    fw.plan['units'] = 60000
                    fw.plan['type'] = "LIMIT"  # 'MARKET'
                    fw.plan['tp_range'] = 0.10  # 余裕度を入れる
                    fw.plan['lc_range'] = 0.06

                    print(fw.plan)
                    fw.reorder_next = 0
                    fw.make_order()
                    fw.print_all()
                    tk.line_send("  リオーダー実施", high_temp, low_temp, target_price)
                    tk.line_send("  リオーダー実施！！", fw.plan['lc_price'], fw.plan['ask_bid'], now_price,
                                 datetime.datetime.now().replace(microsecond=0))

                    # rvもキャンセルしておく
                    # rv.close_order()
                    # fw.close_position()
                    # rv.print_all()
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
                if time_min % 1 == 0 and (time_sec == 9 or time_sec == 39):
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
    "now_h": 0,  # グローバルの必要ある？
    "now_m": 0,  # グローバルの必要ある？
    "now_s": 0,  # グローバルの必要ある？
    'now': datetime.datetime.now().replace(microsecond=0),  # グローバルの必要ある？
    "spread": 0.02,  # 0.012,  # 許容するスプレッド practice = 0.004がデフォ。Live0.008がデフォ
    "p_order": 2,  # 極値の判定幅
    "midnight_close": 0,
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
