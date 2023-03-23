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
    if price_dic['spread'] > gl['spread']:
        # print("    ▲スプレッド異常")  # スプレッドによっては実行をしない
        oa.print_i("    ▲スプレッド異常")
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
    # print("  LATEST")
    latest_ans = f.renzoku_gap_pm(latest_df)  # 何連続で同じ方向に進んでいるか（直近-1まで）
    # print(latest_ans)
    # print(" OLDEST")
    oldest_ans = f.renzoku_gap_pm(oldest_df)  # 何連続で同じ方向に進んでいるか（前半部分）
    # print(oldest_ans)
    # price_dic = oa.NowPrice_exe("USD_JPY")
    # if latest_ans['direction'] > 0:  # プラス(買い) オーダーの場合
    #     now_price = float(price_dic["ask"])
    # else:
    #     now_price = float(price_dic["bid"])
    ans = f.judgement_42(oldest_ans, latest_ans, price_dic['mid'])  # 引数順注意。ポジ用の価格情報取得（０は取得無し）

    # (2) 不可情報として基本的な情報を付与する（直近３個の平均移動両等）
    temp_df = d5_df.head(3)
    move_body = temp_df['body_abs'].mean()

    return {"ans": ans["ans"], "order_plan": ans['order_plan'], "jd_info": ans["jd_info"], "memo": ans['memo'],
            "body_ave":move_body}


# 個のオーダーの情報を集約するクラス
class order_information:
    total_pips = 0  # クラス変数で管理
    def __init__(self, name, oa):
        self.oa = oa  # クラス変数でもいいが、LiveとPracticeの混在ある？　引数でもらう
        self.name = name  # FwかRvかの表示用。引数でもらう
        self.life = False  # 有効かどうか（オーダー発行からポジションクローズまで）
        self.plan = {}  # plan情報
        self.plan_info = {}  # plan情報をもらった際の付加情報（戻り率等）
        self.order = {"id": 0, "state": "", "time_past": 0}  # オーダー情報 (idとステートは初期値を入れておく）
        self.position = {"id": 0, "state": "", "time_past": 0}  # ポジション情報 (idとステートは初期値を入れておく））
        self.crcdo = False  # ポジションを変更履歴があるかどうか(複数回の変更を考えるならIntにすべき？）
        self.latest_crcdo_sec = 0  # ポジション所有から何秒後に、最新のCRCDOを行ったかを記録する。
        self.reorder_waiting = 0  # リオーダー待ちフラグ
        self.reorder = 1  # ２回まで再オーダーを実施する
        self.reorder_waiting_sec = 0  # リオーダーまで６０秒待つ
        self.reorder_latest = datetime.datetime.now().replace(microsecond=0)
        self.now_price = 0
        self.api_try_num = 3  # APIのエラー（今回はLC底上げに利用）は３回まで
        self.body_ave = 0

    def reset(self):
        # 完全にそのオーダーを削除する ただし、Planは消去せず残す
        #
        oa.print_i("   ◆リセット", self.name)
        self.life_set(False)
        self.crcdo = False
        self.order = {"id": 0, "state": "", "time_past": 0}  # オーダー情報 (idとステートは初期値を入れておく）
        self.position = {"id": 0, "state": "", "time_past": 0}  # ポジション情報 (idとステートは初期値を入れておく））
        self.reorder = 1
        self.reorder_waiting = 0  # リオーダー待ちフラグ
        self.api_try_num = 3  # APIのエラー（今回はLC底上げに利用）は３回まで
        if self.name == "fw_reorder":
            self.name = "fw"  # 名前を元に戻す（名前での処理有）

    def print_i(self):
        oa.print_i("   <表示>", self.name, datetime.datetime.now().replace(microsecond=0))
        oa.print_i("　 【LIFE】", self.life)
        oa.print_i("　 【CRCDO】", self.crcdo)
        oa.print_i("　 【ORDER】", self.order['id'], self.order['state'])
        oa.print_i("　 【POSITIOn】", self.position['id'], self.position['state'])

    def print_all(self):
        oa.print_i("   <表示>", self.name, datetime.datetime.now().replace(microsecond=0))
        oa.print_i("　 【LIFE】", self.life)
        oa.print_i("　 【CRCDO】", self.crcdo)
        oa.print_i("　　【PLAN】", self.plan)
        oa.print_i("　　【ORDER】", self.order)
        oa.print_i("　　【POSITION】", self.position)

    def plan_info_input(self, info):  #
        self.plan_info = info

    def plan_input(self, plan):
        self.reset()
        self.plan = plan
        # r_order = {
        #     "price": r_entry_price,
        #     "lc_price": 0.05,
        #     "lc_range": ave_body,  # 0.03,  # ギリギリまで。。
        #     "tp_range": 0.05,
        #     # latest_ans['low_price']+0 if direction_l == 1 else latest_ans['high_price']-0
        #     "ask_bid": 1 * direction_l,
        #     "units": 20000,
        #     "type": "STOP",
        #     "tr_range": 0.10,  # ↑ここまでオーダー
        #     "mind": -1,
        #     "memo": "reverse",
        # }

    def crcdo_set(self, boo):
        # print("  CRCDOフラッグ変化", self.name, boo)
        oa.print_i("  CRCDOフラッグ変化", self.name, boo)
        self.crcdo = boo

    def life_set(self, boo):
        # print("  Life変化", self.name, boo)
        oa.print_i("  　Life変化", self.name, boo)
        self.life = boo

    def make_order(self):
        # Planを元にオーダーを発行する
        order_ans = oa.OrderCreate_dic_exe(self.plan)  # オーダー発行しローカル変数に結果を格納する
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
        self.order_time = datetime.datetime.now().replace(microsecond=0)

        oa.print_i(" オーダー発行確定", order_ans['order_id'])
        if order_ans['cancel']:  # キャンセルされている場合は、リセットする
            # print("  Cancel発生", self.name)
            oa.print_i("  Cancel発生", self.name)
            oa.print_i(order_ans)
        else:
            self.life_set(True)  # LIFEのONはここでのみ実施
            pass  # 送信はMainで実施

    def close_order(self):
        # オーダークローズする関数 (情報のリセットは行わなず、Lifeの変更のみ）
        if self.life:
            res = oa.OrderCancel_exe(self.order['id'])
            if type(res) is int:
                oa.print_i("   存在しないorder（ERROR）")
            else:
                self.order['state'] = "CANCELLED"
                self.life_set(False)
                oa.print_i(" 注文の為？オーダー解消", self.order['id'])
                # tk.line_send("  オーダー解消", self.order['id'])
        else:
            oa.print_i("   order無し")

    def close_position(self):
        # ポジションをクローズする関数 (情報のリセットは行わなず、Lifeの変更のみ）
        if self.life:
            res = oa.TradeClose_exe(self.position['id'], None, "")
            if type(res) is int:
                # print("   存在しないposition（ERRO）")
                oa.print_i("   存在しないposition（ERRO）")
            else:
                self.position['state'] = "CLOSED"
                self.life_set(False)
                tk.line_send("  注文の為？ポジション解消", self.position['id'])
        else:
            # print("    position無し")
            oa.print_i("    position無し")

    def update_information(self):  # orderとpositionを両方更新する
        # （０）途中からの再起動の場合、lifeがおかしいので。。あと、ポジション解除後についても必要（CLOSEの場合は削除する？）ｓ
        # STATEの種類
        # order "PENDING" "CANCELLED" "FILLED"
        # position "OPEN" "CLOSED"
        if self.life:  # LifeがTrueの場合は、必ずorderIDが入っている
            global gl
            oa.print_i(" □□情報を更新します", self.name)
            # ★現在価格を求めておく
            price_dic = oa.NowPrice_exe("USD_JPY")
            if self.plan['ask_bid'] > 0:  # プラス(買い) オーダーの場合
                self.now_price = float(price_dic["ask"])
            else:
                self.now_price = float(price_dic["bid"])

            # （０）情報取得 + 変化点キャッチ（ 情報を埋める前に変化点をキャッチする）
            temp = oa.OrderDetailsState_exe(self.order['id'])
            # （1-1)　変化点を算出しSTATEを変更する（ポジションの新規取得等）
            if self.order['state'] == "PENDING" and temp['order_state'] == 'FILLED':  # 現orderあり⇒約定（取得時）
                oa.print_i("  ★position取得！")
                # tk.line_send("取得！", self.name, datetime.datetime.now().replace(microsecond=0))
                change_flag = 1  # 結果の可視化フラグ
            elif self.order['state'] == "PENDING" and temp['position_state'] == 'CLOSED':  # 現orderあり⇒ポジクローズ
                oa.print_i("  ★即ポジ即解消済！")
                self.life_set(False)
                tk.line_send("即ポジ即解消！", self.name, datetime.datetime.now().replace(microsecond=0))
                change_flag = 1  # 結果の可視化フラグ
            elif self.position['state'] == "OPEN" and temp['position_state'] == "CLOSED":  # 現ポジあり⇒ポジ無し（終了時）
                oa.print_i("  ★position解消")
                self.life_set(False)
                gl['total_pips'] = round(gl['total_pips'] + temp['position_pips'], 3)
                self.total_pips = round(self.total_pips + temp['position_pips'], 3)
                tk.line_send("  解消", self.name, temp['position_pips'], " Total:", gl['total_pips'], "time:", datetime.datetime.now().replace(microsecond=0))
                change_flag = 1  # 結果の可視化フラグ
            elif self.order['state'] == "PENDING" and temp['order_state'] == 'CANCELLED':  # （取得時）
                # oa.print_i("  ★orderCancel")
                # self.life_set(False)
                # tk.line_send("　　orderCancel！", self.name, datetime.datetime.now().replace(microsecond=0))
                change_flag = 1  # 結果の可視化フラグ
            else:
                # print(" 　　状態変化なし")
                change_flag = 0

            # （３）情報を更新
            # print("Order")
            # print(self.order['time'])
            self.order['id'] = temp['order_id']
            self.order['time_str'] = temp['order_time']  # 日時（日本）の文字列版（時間差を求める場合に利用する）
            self.order['time'] = 0 if type(temp['order_time']) == int else datetime.datetime.strptime(temp['order_time'], '%Y/%m/%d %H:%M:%S')
            self.order['time_past'] = int(temp['order_time_past'])  # 諸事情でプラス２秒程度ある　経過時間を求める（Trueの場合）
            self.order['time_past_continue'] = oa.cal_past_time_single(self.order['time_str'])  # 引数は元データ(文字列時刻)のtemp
            self.order['units'] = int(temp['order_units'])
            self.order['price'] = float(temp['order_price'])
            self.order['state'] = temp['order_state']
            self.order['id'] = temp['order_id']

            # print("Posi")
            self.position['id'] = temp['position_id']
            self.position['time_str'] = temp['position_time']
            self.position['time'] = 0 if type(temp['position_time']) == int else datetime.datetime.strptime(temp['position_time'], '%Y/%m/%d %H:%M:%S')
            self.position['time_past'] = int(temp['position_time_past'])  # 諸事情でプラス２秒程度ある
            self.position['time_past_continue'] = oa.cal_past_time_single(self.position['time_str'])
            self.position['price'] = float(temp['position_price'])
            self.position['units'] = 0  # そのうち導入したい
            self.position['state'] = temp['position_state']
            self.position['realizePL'] = float(temp['position_realizePL'])
            self.position['pips'] = float(temp['position_pips'])
            self.position['close_time'] = temp['position_close_time']

            if change_flag == 1:
                self.print_i()  # 情報の表示

            # (4)矛盾系の状態を解消する（部分解消などが起きた場合に、idがあるのにStateがないなど、矛盾があるケースあり。
            if self.position['id'] != 0 and self.position['state'] == 0:
                # positionIDがあるのにStateが登録されていない⇒エラー
                tk.line_send("  ID矛盾発生⇒強制解消処理", self.position['id'], self.position['state'])
                oa.print_i(oa.TradeDetails_exe(self.position['id']))
                oa.print_i(oa.OrderDetails_exe(self.order['id']))
                self.print_all()  # 何が起きているのか確認用の表示
                self.reset()

            # LCの底上げを行う
            self.lc_change()

        else:
            # LifeがFalseの場合
            # オーダーからの時間は継続して取得する（ただし初期値０だとうまくいかないので除外）
            if "time" in self.order:
                print("")
                self.order['time_past_continue'] = oa.cal_past_time_single(self.order['time_str'])  # 諸事情でプラス２秒程度ある
            else:
                self.order['time_past_continue'] = 0
            if "time" in self.position:
                self.position['time_past_continue'] = oa.cal_past_time_single(self.position['time_str'])
            else:
                self.position['time_past_continue'] = 0

    def accept_new_order(self):
        # 新規オーダーを受け入れるかどうか（時間的[秒指定]な物、リオーダーフラグがあるかどうか）。新規オーケーの場合、Trueを返却
        wait_time_new = 6
        if 0 < self.order['time_past_continue'] < wait_time_new * 60:  # 0の場合はTrueになるので、不等号に＝はNG。
            # print(" □発行直後のオーダー等、発行できない理由あり")
            new_order = False
        elif self.reorder_waiting == 1:
            new_order = False
            oa.print_i(" 　★★★奇遇　リオーダー待ち中の真意オーダータイミング")
        else:
            new_order = True

        return new_order

    def lc_change(self):  # ポジションのLC底上げを実施 (基本的にはUpdateで平行してする形が多いかと）
        if self.crcdo is False and self.position['state'] == "OPEN":  # ポジションのCRCDO歴がない場合⇒ポジションLC調整を行う可能性
        # if self.position['state'] == "OPEN":  # ポジションのCRCDO歴がない場合⇒ポジションLC調整を行う可能性
            if self.name == "fw_reorder":  # 自分がfw_reorderだった場合
                # print("    リオーダーのLC底上げ")
                p = self.position
                o = self.order
                margin = 0.05  # abs(p['pips']) / 2
                cl_line_test = self.now_price + margin if self.plan['ask_bid'] < 0 else self.now_price - margin
                cl_span = 60  # 1分に１回しか更新しない
                reorder_past = (datetime.datetime.now().replace(microsecond=0) - self.reorder_latest).seconds  # 経過時間確認
                if p['pips'] > 0.015 and reorder_past > cl_span:  # ある程度のプラスがあれば、LC底上げを実施する
                    cd_line = cl_line_test + 0 if self.plan['ask_bid'] < 0 else cl_line_test - 0  # 微プラス
                    data = {
                        "stopLoss": {"price": str(cd_line), "timeInForce": "GTC"},
                        # "takeProfit": {"price": str(cd_line), "timeInForce": "GTC"},
                        # "trailingStopLoss": {"distance": 0.05, "timeInForce": "GTC"},
                    }
                    res = oa.TradeCRCDO_exe(p['id'], data)  # ポジションを変更する
                    if type(res) is int:
                        tk.line_send("CRCDミス")
                    else:
                        # tk.line_send("　(ReOrder)LC値底上げ", self.name, p['price'], "⇒", cd_line, o['units'],
                        #              self.plan['ask_bid'], self.position['pips'], reorder_past, self.reorder_latest,
                        #              "margin", margin, " nowprice", self.now_price)
                        self.crcdo_set(True)  # main本体で、ポジションを取る関数で解除する
                        self.reorder_latest = datetime.datetime.now().replace(microsecond=0)
                else:
                    # print("    [ポジ有] (ReOrder)LC底上げ基準プラス未達")
                    oa.print_i("    [ポジ有] (ReOrder)LC底上げ基準プラス未達")

            else:  # 通常のLC底上げ
                p = self.position
                o = self.order
                cl_span = 60  # 1分に１回しか更新しない

                if p['pips'] > 0.015:  # ある程度のプラスがあれば、LC底上げを実施する
                    # cd_line = round(p['price'] - 0.01 if self.plan['ask_bid'] < 0 else p['price'] + 0.01, 3)  # 微＋
                    cd_line = round(p['price'] + 0.03 if self.plan['ask_bid'] < 0 else p['price'] - 0.03, 3)  # マイナスで利確
                    tp_line = round(self.now_price - 0.1 if self.plan['ask_bid'] < 0 else self.now_price + 0.1, 3)  # 微＋
                    # oa.print_i("■", p['price'], o['units'])
                    data = {
                        "stopLoss": {"price": str(cd_line), "timeInForce": "GTC"},
                        "takeProfit": {"price": str(tp_line), "timeInForce": "GTC"},
                        "trailingStopLoss": {"distance": 0.05, "timeInForce": "GTC"},
                    }
                    res = oa.TradeCRCDO_exe(p['id'], data)  # ポジションを変更する

                    if type(res) is int:
                        tk.line_send("CRCDミス", self.api_try_num)
                        if self.api_try_num < 0:
                            # print(" ★CRCDC諦め")
                            oa.print_i(" ★CRCDC諦め")
                            self.crcdo_set(True)  # main本体で、ポジションを取る関数で解除する
                        self.api_try_num = self.api_try_num - 1
                    else:
                        # tk.line_send("　(通常小)LC値底上げ", self.name, p['price'], "⇒", cd_line, o['units'],
                        #              self.plan['ask_bid'])
                        self.crcdo_set(True)  # main本体で、ポジションを取る関数で解除する
                        self.latest_crcdo_sec = p['time_past']  # 変更時の経過時点を記録しておく
                        # print("    [ポジ有] LC底上げ基準プラス未達（小)")
                        oa.print_i("    [ポジ有] LC底上げ基準プラス未達（小)")
                # elif p['pips'] > 0.030:  # ある程度のプラスがあれば、LC底上げを実施する
                #     cd_line = p['price'] - 0.013 if self.plan['ask_bid'] < 0 else p['price'] + 0.013  # 微プラス
                #     # print("■", p['price'], o['units'])
                #     # oa.print_i("■", p['price'], o['units'])
                #     data = {
                #         "stopLoss": {"price": str(cd_line), "timeInForce": "GTC"},
                #         # "takeProfit": {"price": str(cd_line), "timeInForce": "GTC"},
                #         # "trailingStopLoss": {"distance": 0.1, "timeInForce": "GTC"},
                #     }
                #     res = oa.TradeCRCDO_exe(p['id'], data)  # ポジションを変更する
                #     if type(res) is int:
                #         tk.line_send("CRCDミス")
                #         if self.api_try_num < 0:
                #             # print(" ★CRCDC諦め")
                #             oa.print_i(" ★CRCDC諦め")
                #             self.crcdo_set(True)  # main本体で、ポジションを取る関数で解除する
                #         self.api_try_num = self.api_try_num - 1
                #     else:
                #         tk.line_send("　(通常大)LC値底上げ++", self.name, p['price'], "⇒", cd_line, o['units'],
                #                      self.plan['ask_bid'])
                #         self.crcdo_set(True)  # main本体で、ポジションを取る関数で解除する
                #         # print("    [ポジ有] LC底上げ基準プラス未達（大)")
                #         oa.print_i("    [ポジ有] LC底上げ基準プラス未達（大)")
        # elif self.crcdo:
        #     # print("    CRCDO済")
        #     oa.print_i("    CRCDO済")
        elif self.position['state'] != "OPEN":
            # print("  　 ポジション無し")
            pass
        else:
            pass

def inspection_next_action():  # クラスはグローバル関数の為引数で渡される必要なし
    # オーダー希望（基準達成）があった場合、現在のオーダーをどうするか（新オーダー不可　or 全てキャンセルして新オーダーか）
    # 新オーダー不可の場合は、オーダーが二つとも存在＋かつ２０分経過していない場合、fw.reorder_nextが１の場合(リオーダー待ち)
    limit_time_min = 6


    if 0 < fw.order['time_past_continue'] < limit_time_min * 60 or 0 < rv.order['time_past_continue'] < limit_time_min * 60:
        # print(" □発行直後のオーダー等、発行できない理由あり")
        new_order = False
    elif fw.reorder_waiting == 1:
        new_order = False
        oa.print_i(" 　★★★奇遇　リオーダー待ち中の真意オーダータイミング")
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
    oa.print_i(" ", order_judge['memo'])

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
        oa.print_i(" □オーダー条件は達成")
        if next_action['new_order']:
            oa.print_i("  ★エントリー確定 クロース＋オーダー発注")
            # 全てのオーダー、ポジションをクローズする
            for i in range(len(classes)):
                classes[i].close_order()
                classes[i].close_position()
            # オーダー情報を順に格納していく
            for i in range(len(classes)):
                classes[i].plan_info_input(order_judge['jd_info'])
                classes[i].plan_input(order_judge['order_plan'][i])
                # classes[i].body_ave = order_judge['body_ave']
            # オーダーを発行していく
            # for i in range(len(classes)):
            #     classes[i].make_order()
            # 価格情報を仮で求める（複数）
            print(classes[0].plan, classes[0].plan_info)
            test_price_cal(classes[0].plan['price'], classes[0].plan_info)
            classes[0].make_order()  # 人とまずForwardのみ


            # 情報をLINEで送付する
            temp = order_judge['jd_info']
            tk.line_send("■折返Position！", datetime.datetime.now().replace(microsecond=0),
                         ",戻り率:", temp['return_ratio'],
                         ",Memo", order_judge['memo'],
                         "OLDEST範囲", temp["oldest_old"], "-", temp['latest_old'], "(COUNT", temp["oldest_count"],
                         ")LATEST範囲", temp['latest_old'], "-", temp['latest_late'], "(COUNT", temp["latest_count"], ")",
                         )
            # print("  　まとめてオーダー発注")
            oa.print_i("  　まとめてオーダー発注")


    # MAIN LAST
    oa.print_view()
    gl['count'] = gl['count'] + 1


def test_price_cal(base_price, base_info):
    print("　　　test", base_price, base_info['oldest_old'])
    if base_info['direction'] == 1:  # 谷形状(oldest > 今の価格）
        gap = base_info['oldest_old'] - base_info['latest_late']
        temp_gap = gap / 2
        top_candidate = base_info['latest_late'] + temp_gap
    else:  # 山形状（今の価格＞oldest
        gap = base_info['latest_late'] - base_info['oldest_old']
        temp_gap = gap / 2
        top_candidate = base_info['latest_late'] - temp_gap

    tk.line_send("base,old,latest,tops", base_price, base_info['oldest_old'], base_info['latest_late'], top_candidate)



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
    'total_pips': 0,
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
    'jd_info': ans_info_test,
    'memo': "test"
}

# ■出発！
oa.OrderCancel_All_exe()  # 露払い
oa.TradeAllColse_exe()  # 露払い
main()
schedule(gl['schedule_freq'], main)
