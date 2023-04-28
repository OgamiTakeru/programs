### 情報取得のテスト

import threading  # 定時実行用
import time
import datetime
import sys
import os
# import requests
import pandas as pd
# 自作ファイルインポート
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import programs.main_functions as f  # とりあえずの関数集
import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.oanda_class as oanda_class
from time import sleep
import pytz

class order_information:
    total_pips = 0  # クラス変数で管理
    def __init__(self, name, oa):
        self.oa = oa  # クラス変数でもいいが、LiveとPracticeの混在ある？　引数でもらう
        # リセ対象群
        self.name = name  # FwかRvかの表示用。引数でもらう
        self.life = False  # 有効かどうか（オーダー発行からポジションクローズまで）
        self.plan = {}  # plan情報
        self.plan_info = {}  # plan情報をもらった際の付加情報（戻り率等）⇒この情報は基本上書きされるまで消去せず
        self.order = {"id": 0, "state": "", "time_past": 0}  # オーダー情報 (idとステートは初期値を入れておく）
        self.position = {"id": 0, "state": "", "time_past": 0}  # ポジション情報 (idとステートは初期値を入れておく））
        self.crcdo = False  # ポジションを変更履歴があるかどうか(複数回の変更を考えるならIntにすべき？）
        self.crcdo_sec = 0  # ポジション所有から何秒後に、最新のCRCDOを行ったかを記録する。
        self.now_price = 0  # 直近の価格を記録しておく（APIを叩かなくて済むように）
        self.api_try_num = 3  # APIのエラー（今回はLC底上げに利用）は３回まで


        # リセット対象外（規定値がある物）
        self.order_timeout = 60  # リセ無。分で指定。この時間が過ぎたらオーダーをキャンセルする
        self.lc_border = 0.03  # リセ無。プラス値でプラス域でロスカットを実施 マイナス値でその分のマイナスを許容する Default=0.03
        self.tp_border = 0.1  # リセ無。プラス値でプラス域でロスカットを実施 マイナス値でその分のマイナスを許容する Default=0.03

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
        if self.plan['price'] != 999:  # 例外時（price=999)以外は、通常通り実行する
            order_ans = oa.OrderCreate_dic_exe(self.plan)  # Plan情報からオーダー発行しローカル変数に結果を格納する
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

            oa.print_i(" オーダー発行確定", order_ans['order_id'])
            if order_ans['cancel']:  # キャンセルされている場合は、リセットする
                # print("  Cancel発生", self.name)
                oa.print_i("  Cancel発生", self.name)
                oa.print_i(order_ans)
            else:
                self.life_set(True)  # LIFEのONはここでのみ実施
                pass  # 送信はMainで実施
        else:  # price=999の場合（例外の場合）処理不要・・？
            pass

    def close_order(self):
        # オーダークローズする関数 (情報のリセットは行わなず、Lifeの変更のみ）
        print("OrderCnacel関数")
        res_dic = oa.OrderDetails_exe(self.order['id'])
        if "order" in res_dic:
            status = res_dic['order']['state']
            if status == "PENDING":  # orderがキャンセルできる状態の場合
                print(" orderCancel検討")
                res = oa.OrderCancel_exe(self.order['id'])
                if type(res) is int:
                    oa.print_i("   存在しないorder（ERROR）")
                else:
                    self.order['state'] = "CANCELLED"
                    self.life_set(False)
                    oa.print_i(" 注文の為？オーダー解消", self.order['id'])
                    # tk.line_send("  オーダー解消", self.order['id'])
            else:  # FIEELDとかCANCELLEDの場合は、lifeにfalseを入れておく
                oa.print_i("   order無し")
        else:
            oa.print_i("  order無し（APIなし）")

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
        global gl_total_pips
        if self.life:  # LifeがTrueの場合は、必ずorderIDが入っている
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
                gl_total_pips = round(gl_total_pips + temp['position_pips'], 3)
                self.total_pips = round(self.total_pips + temp['position_pips'], 3)
                tk.line_send("  解消", self.name, temp['position_pips'], " Total:", gl_total_pips, "time:",
                             datetime.datetime.now().replace(microsecond=0))
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
            self.order['id'] = temp['order_id']
            self.order['time_str'] = temp['order_time']  # 日時（日本）の文字列版（時間差を求める場合に利用する）
            self.order['time_past'] = int(temp['order_time_past'])  # 諸事情でプラス２秒程度ある　経過時間を求める（Trueの場合）
            self.order['time_past_continue'] = oa.cal_past_time_single(self.order['time_str'])  # 引数は元データ(文字列時刻)
            self.order['units'] = int(temp['order_units'])
            self.order['price'] = float(temp['order_price'])
            self.order['state'] = temp['order_state']
            self.order['id'] = temp['order_id']

            # print("Posi")
            self.position['id'] = temp['position_id']
            self.position['time_str'] = temp['position_time']
            self.position['time'] = 0 if type(temp['position_time']) == int else \
                datetime.datetime.strptime(temp['position_time'], '%Y/%m/%d %H:%M:%S')
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

            #  状況に応じて処理を実施する
            # LCの底上げを行う
            self.lc_change()
            # 時間による解消を行う
            if self.order['time_past'] > self.order_timeout * 60:
                self.close_order()


        else:
            # LifeがFalseの場合
            # オーダーからの時間は継続して取得する（ただし初期値０だとうまくいかないので除外）
            if "time" in self.order:
                # print("")
                self.order['time_past_continue'] = oa.cal_past_time_single(self.order['time_str'])  # 諸事情で＋２秒程度ある
            else:
                self.order['time_past_continue'] = 0
            if "time" in self.position:
                self.position['time_past_continue'] = oa.cal_past_time_single(self.position['time_str'])
            else:
                self.position['time_past_continue'] = 0

    def accept_new_order(self):
        # 新規オーダーを受け入れるかどうか（時間的[秒指定]な物、リオーダーフラグがあるかどうか）。新規オーケーの場合、Trueを返却
        wait_time_new = 6  # ６分以内はキャンセルしない。６分以上で、上書きオーダーの受け入れが可能のフラグを出せる。
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
            p = self.position
            o = self.order
            cl_span = 60  # 1分に１回しか更新しない

            if p['pips'] > 0.015:  # ある程度のプラスがあれば、LC底上げを実施する
                lc_border = 0.01  # プラス値でプラス域でロスカットを実施
                cd_line = round(
                    p['price'] - self.lc_border if self.plan['ask_bid'] < 0 else p['price'] + self.lc_border, 3)
                tp_line = round(
                    self.now_price - self.tp_border if self.plan['ask_bid'] < 0 else self.now_price + self.tp_border,
                    3)  # 微＋
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
                        oa.print_i(" ★CRCDC諦め")
                        self.crcdo_set(True)  # main本体で、ポジションを取る関数で解除する
                    self.api_try_num = self.api_try_num - 1
                else:
                    self.crcdo_set(True)  # main本体で、ポジションを取る関数で解除する
                    self.crcdo_sec = p['time_past']  # 変更時の経過時点を記録しておく
                    oa.print_i("    [ポジ有] LC底上げ基準プラス未達（小)")
                    tk.line_send("　(通常小)LC値底上げ")

        elif self.position['state'] != "OPEN":
            # print("  　 ポジション無し")
            pass
        else:
            pass


# ★必須。Tokenの設定、クラスの実体化⇒これ以降、oa.関数名で呼び出し可能
print("Start")
oa = oanda_class.Oanda(tk.accountID, tk.access_token, "practice")
# oa = oanda_class.Oanda(tk.accountIDl, tk.access_tokenl, "live")

# # ★現在価格の取得
price_dic = oa.NowPrice_exe("USD_JPY")
print("【現在価格live】", price_dic['mid'], price_dic['ask'], price_dic['bid'], price_dic['spread'])
print(oa.NowPrice_exe("USD_JPY")['mid'])



# data = {
#     "stopLoss": {"price": 132.151, "timeInForce": "GTC"},
#     # "takeProfit": {"price": 132.006, "timeInForce": "GTC"},
#     # "trailingStopLoss": {"distance": 0.05, "timeInForce": "GTC"},
# }
# res = oa.TradeCRCDO_exe(104959, data)  # ポジションを変更する
# print(res)


print(oa.OrderDetailsState_exe(108428))


# print("test")
# オーダー番号から、オーダーの行く末を取得する
# order_id = 88169  # pending
# # order_id = ans['order_id']
# order_detail = oa.OrderDetailsState_exe(order_id)  # 詳細の取得
# print(order_detail)
#
# test = oa.OrderCancel_exe(order_id)
#
# print(type(test))
# if type(test) is int:
#     print("の")
# else:
#     print("OK")

# temp = oa.OrderDetails_exe(88169)  # 88169  97483
# print(temp)

# temp = oa.OrderCancel_exe(88169)
# print(temp)





# print(time_jp)

# オーダーブックの取得
# ans = oa.OrderBook_exe(price_dic['mid'])
# print(ans)

# オーダー全部キャンセル（必要な時あり）
# oa.OrderCancel_All_exe()

# オーダー一覧取得(TP/LCなし）
# orders = oa.OrdersWaitPending_exe()

#         print("80")

#
# # オーダー一覧取得（TP/LC含む）
# orders_all = oa.OrdersPending_exe()
# print(orders_all)

# print(oa.OpenTrades_exe())




# ★データの取得（複数一括）
# mid_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": 'M5', "count": 100}, 1)
# mid_df.to_csv(tk.folder_path + 'TEST_DATA.csv', index=False, encoding="utf-8")
# f.draw_graph(mid_df)  # グラフ化
# print(mid_df)

# オーダー状況確認用
# pending_new_df = oa.OrdersWaitPending_exe()  # ペンディングオーダーの取得(利確注文等は含まない）
# print(pending_new_df)
# pending_new_df.to_csv(tk.folder_path + 'TEST_DATA.csv', index=False, encoding="utf-8")


# # ★データの取得（単品・Param確認用）
# mid_each_df = oa.InstrumentsCandles_exe("USD_JPY",
#                                         {"granularity": 'S5', "count": 10, "from": "2023-01-03T02:10:00.000000000Z"})
# print(" EACH CANDLE")
# print(mid_each_df)



# # ★注文を発行
oa.OrderCreate_exe(10000, 1, price_dic['mid'], 0.05, 0.09, "STOP", 0.05, " ")



# print(orders)
# bef_order = pd.read_csv(tk.folder_path + 'orders.csv', sep=",", encoding="utf-8")
# print(bef_order)
# ans_dic_arr = []
# counter = 0
# if len(orders) != 0:
#     for index, item in bef_order.iterrows():
#         if len(orders[orders['id'].str.contains(str(item['id']))]) == 0:
#             temp_dic = {
#                 "id": item['id'],
#                 "price": item['price'],
#                 "units": item['units']
#             }
#             ans_dic_arr.append(temp_dic)
#
# print(len(ans_dic_arr))
# for i in range(len(ans_dic_arr)):
#     if ans_dic_arr[i]['units'] == -80:
