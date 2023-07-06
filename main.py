import threading  # 定時実行用
import time
import datetime
import sys
import pandas as pd

# 自作ファイルインポート
import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.oanda_class as oanda_class
import programs.main_functions as f  # とりあえずの関数集


class order_information:
    total_pips = 0  # クラス変数で管理
    def __init__(self, name, oa):
        self.oa = oa  # クラス変数でもいいが、LiveとPracticeの混在ある？　引数でもらう
        # リセ対象群
        self.name = name  # FwかRvかの表示用。引数でもらう
        self.life = False  # 有効かどうか（オーダー発行からポジションクローズまで）
        self.plan = {}  # plan情報
        self.plan_info = {}  # plan情報をもらった際の付加情報（戻り率等）⇒この情報は基本上書きされるまで消去せず
        self.plan_info_before = {}  # ひとつ前のInfo情報も所持しておく（plan_info代入時にのみ更新=注文時のみの更新）
        self.order = {"id": 0, "state": "", "time_past": 0}  # オーダー情報 (idとステートは初期値を入れておく）
        self.position = {"id": 0, "state": "", "time_past": 0}  # ポジション情報 (idとステートは初期値を入れておく））
        self.crcdo_history = False  # ポジションを変更履歴があるかどうか(複数回の変更を考えるならIntにすべき？）
        self.crcdo_sec_counter = 0  # ポジション所有から何秒後に、最新のCRCDOを行ったかを記録する。
        self.crcdo_border = 0  # ロスカや利確を変更するライン
        self.crcdo_guarantee = 0  # 最低限確保する利益を指定（マイナスだとマイナス範囲でせり上げる）
        self.crcdo_self_trail_exe = False  # 二回目以降の自動トレール（Oanda機能ではなく自作）をおこなうかどうか（Trueで実施）
        self.crcdo_lc_price = 0  # ロスカ変更後のLCライン
        self.crcdo_tp_price = 0  # ロスカ変更後のTPライン
        self.crcdo_trail_ratio = 0.5  # トレール幅を勝ちPipsの何割にLINEを引くか
        self.pips_max = 0  # 最高プラスが額を記録
        self.pips_min = 0  # 最低のマイナス額を記録
        self.pips_res_arr = []  # 過去の結果を登録しておく
        self.now_price = 0  # 直近の価格を記録しておく（APIを叩かなくて済むように）
        self.api_try_num = 3  # APIのエラー（今回はLC底上げに利用）は３回まで

        # リセット対象外（規定値がある物）
        self.order_timeout = 20  # リセ無。分で指定。この時間が過ぎたらオーダーをキャンセルする
        self.lc_border = 0.03  # リセ無。プラス値でプラス域でロスカットを実施 マイナス値でその分のマイナスを許容する Default=0.03
        self.tp_border = 0.1  # リセ無。プラス値でプラス域でロスカットを実施 マイナス値でその分のマイナスを許容する Default=0.03
        self.lc_range = 0.01  # CDCRO時、最低のライン（プラス値で最低の利益の確保）
        self.tp_range = 0.05

    def reset(self):
        # 完全にそのオーダーを削除する ただし、Planは消去せず残す
        #
        oa.print_i("   ◆リセット", self.name)
        self.life_set(False)
        self.crcdo_history = False
        self.order = {"id": 0, "state": "", "time_past": 0}  # オーダー情報 (idとステートは初期値を入れておく）
        self.position = {"id": 0, "state": "", "time_past": 0}  # ポジション情報 (idとステートは初期値を入れておく））
        self.reorder = 1
        self.reorder_waiting = 0  # リオーダー待ちフラグ
        self.api_try_num = 3  # APIのエラー（今回はLC底上げに利用）は３回までself.crcdo_history = False  # ポジションを変更履歴があるかどうか(複数回の変更を考えるならIntにすべき？）
        self.crcdo_sec_counter = 0  # ポジション所有から何秒後に、最新のCRCDOを行ったかを記録する。
        self.crcdo_lc_price = 0  # ロスカ変更後のLCライン
        self.crcdo_tp_price = 0  # ロスカ変更後のTPライン
        self.pips_max = 0  # 最高プラスが額を記録
        self.pips_min = 0  # 最低のマイナス額を記録

        if self.name == "fw_reorder":
            self.name = "fw"  # 名前を元に戻す（名前での処理有）

    def print_i(self):
        oa.print_i("   <表示>", self.name, datetime.datetime.now().replace(microsecond=0))
        oa.print_i("　 【LIFE】", self.life)
        oa.print_i("　 【CRCDO】", self.crcdo_history)
        oa.print_i("　 【ORDER】", self.order['id'], self.order['state'])
        oa.print_i("　 【POSITIOn】", self.position['id'], self.position['state'])

    def print_all(self):
        oa.print_i("   <表示>", self.name, datetime.datetime.now().replace(microsecond=0))
        oa.print_i("　 【LIFE】", self.life)
        oa.print_i("　 【CRCDO】", self.crcdo_history)
        oa.print_i("　　【PLAN】", self.plan)
        oa.print_i("　　【ORDER】", self.order)
        oa.print_i("　　【POSITION】", self.position)
        print("   <表示>", self.name, datetime.datetime.now().replace(microsecond=0))
        print("　 【LIFE】", self.life)
        print("　 【CRCDO】", self.crcdo_history)
        print("　　【PLAN】", self.plan)
        print("　　【ORDER】", self.order)
        print("　　【POSITION】", self.position)

    def plan_info_input(self, info):  # plan_info を更新する＋過去の情報を保存しておく(plan_input_and_judge_newからのみ呼ばれる）
        # ■初回は何も入っていない
        if "judgment" in self.plan_info:
            print(" NOT初")
        else:
            self.plan_info = info
            print(" 初回★★")

        # ■重大処理
        self.plan_info_before = self.plan_info  # 過去情報を保存しておく
        self.plan_info = info  # 現在情報新規の情報を記入する
        # 新規のオーダーを受け入れるかを、過去の情報(Info)を元に検討する

    def input_info_and_judge_new(self, new_info):  # accept_new_order
        """
        新規オーダーのエントリーとみなされたタイミングで呼び出される関数。実施事項は以下の通り
        ①前回のオーダーから時間的な意味で、新規オーダーを入れてもいいかの判断を行う
        ②新規オーダーが時間的にOKの場合、オーダー情報を最新に更新。　さらに、詳細を確認して新規を入れるかを検討する。
        """
        # ■時間的な制約で連続して入らないように(こっちは必須的な条件⇒同一足で毎回発生する可能性があるため)
        wait_time_new = 5  # ６分以上で、上書きオーダーの受け入れが可能のフラグを出せる。
        if 0 < self.order['time_past_continue'] < wait_time_new * 59:  # 0の場合はTrueなるので、不等号に＝はNG。オーダー発行時比較
            # print(" □発行直後のオーダー等、発行できない理由あり")
            print("時間不可")
            new_order = False
        else:
            self.plan_info_input(new_info)  # 時間的に問題なければ、入れておく（2023時点、ひとつ前の山と比較するため、必要）
            new_order = True  # 最初はこっちに行く（初期では基本こっち）
        return new_order

    def judge_new(self):
        # ■時間的な制約で連続して入らないように(こっちは必須的な条件⇒同一足で毎回発生する可能性があるため)
        wait_time_new = 5  # ６分以上で、上書きオーダーの受け入れが可能のフラグを出せる。
        # print("  TIME JD",self.order['time_past_continue'], "<", wait_time_new * 59 , "成立で不可")
        if 0 < self.order['time_past_continue'] < wait_time_new * 59:  # 0の場合はTrueなるので、不等号に＝はNG。オーダー発行時比較
            # print(" □発行直後のオーダー等、発行できない理由あり")
            print("時間不可")
            new_order = False
        else:
            new_order = True  # 最初はこっちに行く（初期では基本こっち）
        return new_order

    def order_registration(self, plan):
        """
        オーダー情報をクラスに登録する（保存する）
        :param plan:
        :return:
        """
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

    # def crcdo_set(self, boo):
    #     # print("  CRCDOフラッグ変化", self.name, boo)
    #     oa.print_i("  CRCDOフラッグ変化", self.name, boo)
    #     self.crcdo_history = boo

    def life_set(self, boo):
        # print("  Life変化", self.name, boo)
        oa.print_i("  　Life変化", self.name, boo)
        self.life = boo

    def make_order(self):
        global gl_trade_win
        # Planを元にオーダーを発行する
        if self.plan['price'] != 999:  # 例外時（price=999)以外は、通常通り実行する
            order_ans = oa.OrderCreate_dic_exe(self.plan)  # Plan情報からオーダー発行しローカル変数に結果を格納する
            self.order = {  # 成立情報を取り込む
                "id": order_ans['order_id'],
                "time": order_ans['order_time'],
                "cancel": order_ans['cancel'],
                "state": "PENDING",  # 強引だけど初期値にPendingを入れておく
                "tp_price": float(order_ans['tp_price']),
                "lc_price": float(order_ans['lc_price']),
                "units": float(order_ans['unit']),
                "direction": float(order_ans['unit'])/abs(float(order_ans['unit'])),
                "tp_range": order_ans['tp_range'],
                "lc_range": order_ans['lc_range']
            }
            self.plan['tp_price'] = float(order_ans['tp_price'])  # 念のため入れておく（元々計算で入れられるけど。。）
            self.plan['lc_price'] = float(order_ans['lc_price'])  # 念のため入れておく（元々計算で入れられるけど。。）

            oa.print_i(" オーダー発行確定", order_ans['order_id'])
            if order_ans['cancel']:  # キャンセルされている場合は、リセットする
                # print("  Cancel発生", self.name)
                print("  ★オーダーキャンセル発生", self.name)
                tk.line_send(" 　Order不成立（今後ループの可能性）", order_ans['order_id'])
            else:
                self.life_set(True)  # LIFEのONはここでのみ実施
                pass  # 送信はMainで実施
        else:  # price=999の場合（例外の場合）処理不要・・？
            pass

    def close_order(self):
        # オーダークローズする関数 (情報のリセットは行わなず、Lifeの変更のみ）
        # print("OrderCnacel関数", self.order['id'])
        res_dic = oa.OrderDetails_exe(self.order['id'])
        if "order" in res_dic:
            status = res_dic['order']['state']
            if status == "PENDING":  # orderがキャンセルできる状態の場合
                # print(" orderCancel検討")
                res = oa.OrderCancel_exe(self.order['id'])
                if type(res) is int:
                    oa.print_i("   存在しないorder（ERROR）")
                    print("   存在しないorder（ERROR）")
                else:
                    self.order['state'] = "CANCELLED"
                    self.life_set(False)
                    oa.print_i("   注文の為？オーダー解消", self.order['id'])
                    print("   注文の為？オーダー解消", self.order['id'])
                    # tk.line_send("  オーダー解消", self.order['id'])
            else:  # FIEELDとかCANCELLEDの場合は、lifeにfalseを入れておく
                oa.print_i("   order無し")
                print("   order無し")
        else:
            oa.print_i("   order無し（APIなし）")
            print("   order無し（APIなし）")

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
                tk.line_send("  ポジション解消", self.position['id'], self.position['pips'])
        else:
            # print("    position無し")
            oa.print_i("    position無し")

    def update_information(self):  # orderとpositionを両方更新する
        # （０）途中からの再起動の場合、lifeがおかしいので。。あと、ポジション解除後についても必要（CLOSEの場合は削除する？）ｓ
        # STATEの種類
        # order "PENDING" "CANCELLED" "FILLED"
        # position "OPEN" "CLOSED"
        global gl_total_pips, gl_now_price_mid, gl_trade_win, gl_total_yen
        res = 0  # APIのエラーが多い為、エラーがない場合は０を返す。
        if self.life:  # LifeがTrueの場合は、必ずorderIDが入っている
            # print(" □□情報を更新します", self.name)
            # ★現在価格を求めておく　★APIエラーの場合終了
            price_dic = oa.NowPrice_exe("USD_JPY")
            if "error" in price_dic:  # APIエラーの場合はスキップ
                print(" APIエラーの為情報更新せず終了（ロスカ底上げも出来ないけど）", gl_now)
                exit()
            else:
                if self.plan['ask_bid'] > 0:  # プラス(買い) オーダーの場合
                    self.now_price = float(price_dic["bid"])  # 元もと　Ask
                else:
                    self.now_price = float(price_dic["bid"])
                gl_now_price_mid = self.now_price

            # （０）情報取得 + 変化点キャッチ（ 情報を埋める前に変化点をキャッチする ★APIエラーの場合終了）
            temp = oa.OrderDetailsState_exe(self.order['id'])
            if "error" in temp:  # APIエラーの場合はスキップ
                print(" APIエラーの為情報更新せず終了2（ロスカ底上げも出来ないけど）", gl_now)
                exit()
            # （1-1)　変化点を算出しSTATEを変更する（ポジションの新規取得等）
            if self.order['state'] == "PENDING" and temp['order_state'] == 'FILLED':  # 現orderあり⇒約定（取得時）
                oa.print_i("  ★position取得！", self.name, self.order['direction'])
                direction_t = self.order['units'] / abs(self.order['units'])
                tk.line_send("  (取得)", self.name, datetime.datetime.now().replace(microsecond=0))
                change_flag = 1  # 結果の可視化フラグ
            elif self.order['state'] == "PENDING" and temp['position_state'] == 'CLOSED':  # 現orderあり⇒ポジクローズ
                oa.print_i("  ★即ポジ即解消済！")
                self.life_set(False)
                tk.line_send("即ポジ即解消！", self.name, datetime.datetime.now().replace(microsecond=0))
                change_flag = 1  # 結果の可視化フラグ
            elif self.position['state'] == "OPEN" and temp['position_state'] == "CLOSED":  # 現ポジあり⇒ポジ無し（終了時）
                oa.print_i("  ★position解消")
                self.life_set(False)
                self.pips_res_arr.insert(0, temp['position_pips'])  # 先頭に、結果を追加していく（先頭からの方が後々集計しやすい）
                gl_total_pips = round(gl_total_pips + temp['position_pips'], 3)  # トータル計算 abs(int(self.order['units']))
                temp_yen_result = int(temp['position_pips'] * abs(self.order['units']))  # トータルの円（plだと上手く表示されないので計算する）
                gl_total_yen = int(gl_total_yen + temp_yen_result)
                if temp['position_pips'] >=0 :
                    gl_trade_win += 1  # トータルプラス計算
                res1 = "【Unit】" + str(self.order['units']) + "," + self.name + "【結果】" + str(temp['position_pips']) + "(決済価格:" + str(temp['position_close_price']) + ", "
                res5 = "取得価格:" + str(self.order['price'])
                res2 = "【Total】" + str(gl_total_pips) + "," + "【Win/All】" + str(gl_trade_win) + "/" + str(gl_trade_num)
                res3 = "【ポジション期間の最大/小の振れ幅】 ＋域:" + str(self.pips_min) + "/ー域:" + str(self.pips_max)
                res4 = "【今回損益/合計損益】" + str(temp_yen_result) + "円,計" + str(gl_total_yen) + "円"
                id_info = "【orderID】" + str(self.order['id'])
                tk.line_send(" ▲解消:", datetime.datetime.now().replace(microsecond=0), res1, res5, res2, res3, id_info, res4)
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
            # print("Order", temp['order_time'])
            self.order['id'] = temp['order_id']
            self.order['time_str'] = temp['order_time']  # 日時（日本）の文字列版（時間差を求める場合に利用する）
            self.order['time_past'] = int(temp['order_time_past'])  # 諸事情でプラス２秒程度ある　経過時間を求める（Trueの場合）
            self.order['time_past_continue'] = oanda_class.cal_past_time_single(self.order['time_str'])
            # ↑ 引数は元データ(文字列時刻)。オーダーを解除しても継続してカウントする秒数
            self.order['units'] = int(temp['order_units'])
            self.order['price'] = float(temp['order_price'])
            self.order['state'] = temp['order_state']
            self.order['id'] = temp['order_id']

            # print("Posi", temp['position_time'])
            self.position['id'] = temp['position_id']
            self.position['time_str'] = temp['position_time']
            self.position['time_past'] = int(temp['position_time_past'])  # 諸事情でプラス２秒程度ある
            self.position['time_past_continue'] = oanda_class.cal_past_time_single(self.position['time_str'])
            self.position['price'] = float(temp['position_price'])
            self.position['units'] = 0  # そのうち導入したい
            self.position['state'] = temp['position_state']
            self.position['realizePL'] = float(temp['position_realize_pl'])
            self.position['pips'] = float(temp['position_pips'])
            self.position['close_time'] = temp['position_close_time']
            if self.pips_min < self.position['pips']:  # 最小値更新時
                self.pips_min = self.position['pips']
            if self.pips_max > self.position['pips']:  # 最小値更新時
                self.pips_max = self.position['pips']

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
            # トレールの実施を行う
            self.trail()
            # 時間による解消を行う
            if self.order['time_past'] > self.order_timeout * 60 and self.order['state'] == "PENDING":
                print("   時間解消@")
                tk.line_send("   時間解消@", self.name, self.order['time_past'])
                self.close_order()
        else:
            # LifeがFalseの場合
            # オーダーからの時間は継続して取得する（ただし初期値０だとうまくいかないので除外）
            if "time_str" in self.order:
                # print("")
                self.order['time_past_continue'] = oanda_class.cal_past_time_single(self.order['time_str'])  # 諸事情で＋２秒程度ある
            else:
                self.order['time_past_continue'] = 0
            if "time_str" in self.position:
                self.position['time_past_continue'] = oanda_class.cal_past_time_single(self.position['time_str'])
            else:
                self.position['time_past_continue'] = 0

    def lc_change(self):  # ポジションのLC底上げを実施 (基本的にはUpdateで平行してする形が多いかと）
        p = self.position  # ポジションの情報
        o = self.order  # オーダーの情報
        guarantee = self.crcdo_guarantee

        if self.crcdo_history is False and self.position['state'] == "OPEN":  # ポジションのCRCDO歴がない場合⇒ポジションLC調整を行う可能性
            # 初回のLC変更（最低限のLC幅の設定）
            if p['time_past'] - self.crcdo_sec_counter > 60:  # N秒以上経過している場合、ロスカ引き上げ
                if p['pips'] > self.crcdo_border != 0:  # crcdo_borderが０ではない（トレール有効）、borderより超えている場合
                    self.crcdo_lc_price = round(p['price'] - guarantee if self.plan['ask_bid'] < 0 else p['price'] + guarantee, 3)
                    # self.crcdo_tp_price = round(self.now_price - self.tp_range if self.plan['ask_bid'] < 0 else self.now_price + self.tp_range, 3)  # 微＋
                    data = {
                        "stopLoss": {"price": str(self.crcdo_lc_price), "timeInForce": "GTC"},
                        # "takeProfit": {"price": str(tp_price), "timeInForce": "GTC"},
                        # "trailingStopLoss": {"distance": 0.05, "timeInForce": "GTC"},
                    }
                    res = oa.TradeCRCDO_exe(p['id'], data)  # ポジションを変更する
                    # CDCRO結果の判定
                    if type(res) is int:
                        tk.line_send("CRCDミス", self.api_try_num)
                    else:
                        self.crcdo_sec_counter = p['time_past']  # 変更時の経過時点を記録しておく
                        self.crcdo_history = True
                        # tk.line_send("　(LC底上げ)", self.name, self.order['lc_price'],  "⇒", self.crcdo_lc_price,
                        #              "Border:", self.crcdo_border, "保証", self.crcdo_guarantee)

    def trail(self):  # ポジションのトレールを設定（LCの底上げとは別に考える）
        if self.crcdo_self_trail_exe and self.crcdo_history:  # 一回すでにCDCRO実施済みが前提。
            p = self.position  # ポジションの情報
            o = self.order  # オーダーの情報
            if p['time_past']-self.crcdo_sec_counter > 10:  # 前回のCRCDOよりN秒以上空いていれば、CRCDOを再検討する
                if p['pips'] > 0.04:  # 勝ちpipsがＮ以上の場合、利確底上げ（トレール）を行う
                    temp_lc_range = float(p['pips']) * self.crcdo_trail_ratio  # 含み益の７割（３割戻り）までを目標の戻り幅とする
                    temp_lc_price = round(p['price'] + (temp_lc_range * self.plan['ask_bid']), 3)  # 仮のLC価格を算出する
                    # 実行判定（ temp_lc_priceを更新する場合、更新していく。）
                    exe_crcdo = 0  # ばあいによってはCRCDOしない可能性があるので、フラグを０に初期化しておく。
                    if o['direction'] < 1:  # 谷方向の場合
                        if self.crcdo_lc_price > temp_lc_price:
                            exe_crcdo = 1  # LCラインを押し下げる場合（プラス拡大）
                    else:
                        if self.crcdo_lc_price < temp_lc_price:
                            exe_crcdo = 1  # LCラインを押し下げる場合（プラス拡大）

                    if exe_crcdo == 1:
                        data = {
                            "stopLoss": {"price": str(temp_lc_price), "timeInForce": "GTC"},
                            # "takeProfit": {"price": str(tp_price), "timeInForce": "GTC"},
                            # "trailingStopLoss": {"distance": 0.05, "timeInForce": "GTC"},
                        }
                        res = oa.TradeCRCDO_exe(p['id'], data)  # ポジションを変更する
                        before_lc_price = self.crcdo_lc_price  # Line送信用に取っておく
                        self.crcdo_lc_price = temp_lc_price  # ロスカ変更後のLCラインを保存
                        # CDCRO結果の判定
                        if type(res) is int:
                            tk.line_send("CRCDミス", self.api_try_num)
                        else:
                            self.crcdo_set = True  # main本体で、ポジションを取る関数で解除する
                            self.crcdo_sec_counter = p['time_past']  # 変更時の経過時点を記録しておく
                            # tk.line_send("　(TR)", self.name, before_lc_price, "⇒", self.crcdo_lc_price, ",確保:",
                            #              round(temp_lc_range, 3), ",全:", p['pips'],
                            #              datetime.datetime.now().replace(microsecond=0))
                    else:
                        # exe_code=0
                        pass

                else:
                    # print("     CRCRO再実行確認⇒なし", p['pips'], self.name)
                    pass

        elif self.position['state'] != "OPEN":
            # print("  　 ポジション無し")
            pass
        else:
            pass


def order_line_adjustment(base_line, margin, now_d, type):
    """
    ベース価格にマージンを付けた額（＝希望価格）を計算。
    希望価格と現在価格を比較し、適正な価格を、正式な希望価格とする
    コードは順張りの買い方向を基準とする。
    ①買い　順張り⇒逆思想。現在価格が、line+marginより低い位置にある事が必須
    ②買い　逆張り⇒順思想。現在価格が、line+marginより高い位置にある事が必須
    ③売り　順張り⇒逆思想。現在価格が、line+marginより高い位置にある事が必須
    ④売り　逆張り⇒順思想。現在価格が、line+marginより低い位置にある事が必須
    :param baseline: 基準となる価格。値動きが激しいorマージンの考慮により、この価格基準ではなく、現在価格を基準にする場合有
    :param margin: 指定の価格に、すこし下駄をはかせたところにオーラーラインを引く場合。０でマージン無し。
    :param d　直近の方向 (ポジションを取りたい方向ではない）
    :param type STOP or LIMIT
    :return:
    """
    old_dir = now_d * -1  # 逆にする
    if type == "STOP":  # 大局(Old)への順張りの場合（＝順思想)
        base_line = base_line + (margin * old_dir)
    else:  # 大局への逆張りの場合
        base_line = base_line - (margin * old_dir)

    return round(base_line, 3)


def order_line_adjustment_simple(base_line, margin, direction):
    """
    シンプルに利食いする方向に、エントリーラインを動かす
    140で売り、マージンを１円とした場合、１３９円をエントリーとする
    140で買い、マージンを１円として場合、１４１円とエントリーとする
    :param margin: 指定の価格に、すこし下駄をはかせたところにオーラーラインを引く場合。０でマージン無し。
    :return:
    """
    if direction == 1:  # 買いの場合
        base_line = base_line + margin
    else:  # 売りの場合
        base_line = base_line - margin

    base_line = round(base_line, 3)
    return base_line


def order_setting(class_order_arr, info_l):
    """
    検証し、条件達成でオーダー発行。クラスへのオーダー作成に関するアクセスはこの関数からのみ行う。
    :param class_order_arr: 対象のクラスと、そこへの注文情報
    :param info: その他の情報（今は負け傾向の強さ）
    :return:
    """
    global gl_trade_num, gl_now_price_mid

    gl_trade_num = gl_trade_num + 1
    o_memo = ""

    for i in range(len(class_order_arr)):
        # 変数に入れ替えする
        class_order_pair = class_order_arr[i]
        order_info_temp = class_order_pair['order']
        target_class = class_order_pair['class']
        # 代表的なものを変数に入れておく
        base_price = round(order_info_temp['base_price'], 3)
        expect_direction = order_info_temp['expect_dir']
        margin = order_info_temp['margin']
        lc = order_info_temp['lc']
        tp = order_info_temp['tp']  # order_info_temp['lc']
        memo = order_info_temp['memo']
        units = order_info_temp['units']
        trigger = order_info_temp['trigger']
        order_type = order_info_temp['type']
        name = order_info_temp['name']
        crcdo_trail_ratio = order_info_temp['crcdo_trail_ratio']

        # ■通常オーダー発行
        # price = order_line_adjustment_simple(base_price, margin, expect_direction)  # Margin込みの値段を計算して格納
        price = round(base_price + margin, 3)  # marginの方向は調整済み？
        print(base_price, "+", margin, "=", base_price + margin)
        order_info = {
            "price": price,  # Margin込みの値段を計算して格納
            "lc_range": lc,
            "tp_range": tp,
            "ask_bid": expect_direction,  # 順思想
            "units": units,
            "type": order_type,  #order_type,  # ここはストップ（順張り）専用！
            "tr_range": 0.2,  # ↑ここまでオーダー
            "memo": ""
        }
        target_class.name = name  # 名前を入れる(クラス内の変更）
        target_class.crcdo_trail_ratio = crcdo_trail_ratio
        target_class.order_registration(order_info)  # プラン自身を代入
        target_class.make_order()
        # 送信用
        o = target_class.order
        memo_each = "【" + target_class.name + "】:" + str(price) + ",tp-lc:" + str(o['tp_price']) + "-" + str(
            o['lc_price']) + "(" + str(o['tp_range']) + "-" + str(o['lc_range']) + ")," + str(o['units'])

        o_memo = o_memo + memo_each + '\n'
        # その他条件をインプットする(本当はクラスメソッドで入れたいけど）
        target_class.crcdo_border = order_info_temp['crcdo_border']
        target_class.crcdo_guarantee = order_info_temp['crcdo_guarantee']
        target_class.order_timeout = order_info_temp['order_timeout']
        target_class.crcdo_self_trail_exe = order_info_temp["crcdo_self_trail_exe"]  # トレールは実施しない

    # 送信は一回だけにしておく。
    if target_class.name != "mini":  # 連続にならないように、Miniの場合は送付しない
        mes = ""  #  targetline:" + str(base_price)
        tk.line_send("■折返Position！", gl_live, gl_trade_num, "回目(", datetime.datetime.now().replace(microsecond=0), ")",
                     "トリガー:", trigger, "指定価格",price, "情報:", memo, ",オーダー:", '\n' , o_memo,
                     "初回時間", gl_first_time)


def mode1():
    """
    低頻度モード（条件を検索し、４２検査を実施する）
    :return: なし
    """
    print("  Mode1")

    # チャート分析結果を取得する
    inspection_condition = {
        "now_price": gl_now_price_mid,  # 現在価格を渡す
        "data_r": gl_data5r_df,  # 対象となるデータ
        "figure": {"data_r": gl_data5r_df, "ignore": 1, "latest_n": 2, "oldest_n": 30, "return_ratio": 50},
        "figure3": {"data_r": gl_data5r_df, "ignore": 1, "latest_n": 3, "oldest_n": 30, "return_ratio": 50},
        "macd": {"short": 20, "long": 30},
        "save": True,  # データをCSVで保存するか（検証ではFalse推奨。Trueの場合は下の時刻は必須）
        "time_str": gl_now_str,  # 記録用の現在時刻
    }
    ans_dic = f.inspection_candle(inspection_condition)  # 状況を検査する（買いフラグの確認）

    # 一旦整理。。
    result_turn = ans_dic['figure_turn_result']['result_dic']['result_turn']  # 直近のターンがあるかどうか（連続性の考慮無し）
    result_range_turn = ans_dic['figure_turn_result']['result_dic']['result_range']  # 連続性を考慮したうえでのターン判定
    rename_latest3 = ans_dic['latest3_figure_result']['result']

    # 最近の負け傾向を見る
    info_lose = recent_trends()  # 直近のプラス状況を見る

    # ■パターンでオーダーのベースを組み立てておく（発行可否は別途判断。パターンをとりあえず作っておく）
    if result_turn == 1:  # ターンが確認された場合（最優先）
        print("  ターンを確認")
        if result_range_turn == 1:  # そのさらに直前のターンが発生がある場合
            print("   ★オーダー発行(RangeTurnパターン)⇒一つだけにする？")
            order_info_temp = ans_dic['figure_turn_result']['range_dic']['order_dic']  # RangeTurnのオーダー
            # メインオーダーの作成
            order = {  # ターン起点（インクルードパターン）
                "name": "レンジ",
                "target_class": main_c,  # 対象となるクラス
                "base_price": order_info_temp['base_price'],
                "expect_dir": order_info_temp['direction'],
                "lc": order_info_temp['lc_range'],  # 計算通りのLC
                "tp": order_info_temp['tp_range'] + 0.04,  # 計算通りのTP
                "units": 20000,
                "type": "MARKET",  # 順張り
                "margin": order_info_temp['margin'],
                "memo": ans_dic['figure_turn_result']['latest_turn_dic']['memo_all'],  # 直近ターンの情報
                "trigger": "ターン（インクルード）",
                "kinds": 1,
                "macd": ans_dic['macd_result']['cross'],
                "crcdo_border": 0.05,  # 0.05を超えたらCRCDOでcrcdo_guarantee
                "crcdo_guarantee": -0.03,  # crcdoLINEを超えた場合、このラインを最低の利確ラインとする
                "order_timeout": 20,  # 20分経過でオーダーを解除する
                "crcdo_trail_ratio": 0.7,  # トレール時、勝ちのN%ラインにトレールする
                "crcdo_self_trail_exe": False,  # トレールは実施しない
            }
            # MINIオーダーの作成
            # order_mini = order.copy()
            # order_mini['name'] = order['name'] + "mini"
            # order_mini['units'] = 25000
            # order_mini['lc'] = order['lc'] * 0.7
            # order_mini['crcdo_border'] = 0.025
            # order_mini['crcdo_guarantee'] = 0.01
            # order_mini['crcdo_self_trail_exe'] = True
            # オーダーの集約
            # order_pair = [{"class": main_c, "order": order},
            #               {"class": second_c, "order": order_mini}]
            order_pair = [{"class": main_c, "order": order}]

        else:
            print("   ★オーダー発行（ターン起点）")
            order_info_temp = ans_dic['figure_turn_result']['latest_turn_dic']['order_dic']  # RangeTurnのオーダー
            # メインオーダーの作成
            main_order = order_info_temp['main']
            order = {  # ターン起点(順か逆か、状況で変る。)
                "name": main_order['name'] + "N",
                "target_class": second_c,  # 対象となるクラス
                "base_price": main_order['base_price'],
                "expect_dir": main_order['direction'],
                "lc": main_order['lc_range'],   # 0.055,  # 少し狭い目のLC
                "tp": 0.07,  # round(main_order['tp_range'] + 0.04, 3),
                "units": main_order['units'],
                "type": main_order['type'],  # 順張り
                "margin": main_order['margin'],
                "memo": ans_dic['figure_turn_result']['latest_turn_dic']['memo_all'],
                "trigger": "ターン",
                "kinds": 1,
                "macd": ans_dic['macd_result']['cross'],
                "crcdo_border": 0.02,  # 0.05を超えたらCRCDOでcrcdo_guarantee
                "crcdo_guarantee": -0.01,
                "order_timeout": 20,
                "crcdo_trail_ratio": 0.3,  # トレール時、勝ちのN%ラインにトレールする
                "crcdo_self_trail_exe": True,  # トレールは実施有無（Trueは実施）
            }
            # MINIオーダーの作成
            order_mini = order.copy()
            order_mini['name'] = main_order['name'] + "m"
            order_mini['units'] = round(order['units'] / 2, 0)
            order_mini['tp'] = 0.03
            order_mini['crcdo_border'] = 0.025
            order_mini['crcdo_guarantee'] = 0.01
            order_mini["crcdo_trail_ratio"] = 0.7,  # トレール時、勝ちのN%ラインにトレールする
            order_mini['crcdo_self_trail_exe'] = False

            # 可変オーダーの作成
            junc_order = order_info_temp['junc']
            order2 = {  # ターン起点(Reverse)
                "name": junc_order['name'] + "N",
                "target_class": main_c,  # 対象となるクラス
                "base_price": junc_order['base_price'],
                "expect_dir": junc_order['direction'],
                "lc": junc_order['lc_range'],  # 0.046,  # 少し狭い目のLC
                "tp": junc_order['tp_range'],
                "units": junc_order['units'],
                "type": junc_order['type'],  # 逆張りで試してみようかな。。
                "margin": junc_order['margin'],
                "memo": ans_dic['figure_turn_result']['latest_turn_dic']['memo_all'],
                "trigger": "ターン",
                "kinds": 1,
                "macd": ans_dic['macd_result']['cross'],
                "crcdo_border": 0.02,  # 0.05を超えたらCRCDOでcrcdo_guarantee
                "crcdo_guarantee": -0.02,
                "order_timeout": 20,
                "crcdo_trail_ratio": 0.6,  # トレール時、勝ちのN%ラインにトレールする
                "crcdo_self_trail_exe": True,  # トレールは実施しない
            }
            # miniオーダーの作成
            order2_mini = order2.copy()
            order2_mini['name'] = junc_order['name'] + "m"
            order2_mini['units'] = round(order2['units'] / 2, 0)
            # order2_mini['lc'] = 0.03
            order2_mini['tp'] = 0.03
            order2_mini['crcdo_border'] = 0.025
            order2_mini['crcdo_guarantee'] = 0.01
            order2_mini["crcdo_trail_ratio"] =  0.7,  # トレール時、勝ちのN%ラインにトレールする
            order2_mini['crcdo_self_trail_exe'] = True
            # オーダーの集約
            order_pair = [{"class": main_c, "order": order},
                          {"class": second_c, "order": order_mini},
                          {"class": third_c, "order": order2},
                          {"class": fourth_c, "order": order2_mini}
                          ]

    elif rename_latest3 == 1:  # ターン未遂が確認された場合（早い場合）
        print("  ★オーダー発行 ターン未遂を確認　", )
        order_info_temp = ans_dic['latest3_figure_result']['order_dic']
        # メインオーダーの作成
        print(order_info_temp['margin'])
        order = {
            "name": "順思想（ターン未遂）",
            "target_class": main_c,  # 対象となるクラス
            "base_price": order_info_temp['base_price'],
            "expect_dir": order_info_temp['direction'],
            "lc": 0.035,  # 非常に狭いLC(ターンミスの場合は、ストレートに下がることを期待しているため）
            "tp": 0.05+ 0.04,
            "margin": order_info_temp['margin'],
            "units": 20000,
            "type": "STOP",  # 順張り
            "memo": ans_dic['latest3_figure_result']['memo'],
            "trigger": "ターン未遂",
            "kinds": 2,
            "macd": ans_dic['macd_result']['cross'],
            "crcdo_border": 0.05,  # 0.05を超えたらCRCDOでcrcdo_guarantee
            "crcdo_guarantee": 0.02,
            "crcdo_trail_ratio": 0.7,  # トレール時、勝ちのN%ラインにトレールする
            "order_timeout": 6,  # 分で指定
            "crcdo_self_trail_exe": True,  # トレールは実施しない
        }
        # MINIオーダーの作成
        order_mini = order.copy()
        order_mini['name'] = order['name'] + "mini"
        order_mini['units'] = round(order['units']/2, 0)
        order_mini['lc'] = 0.03
        order_mini['tp'] = 0.03
        order_mini['crcdo_border'] = 0.02
        order_mini['crcdo_guarantee'] = 0.01
        order_mini['crcdo_self_trail_exe'] = False
        # オーダーの集約
        order_pair = [{"class": main_c, "order": order},
                      {"class": second_c, "order": order_mini},
                      ]

    # ■実際の発行が可能かを判断し、オーダーを作成する
    new_jd = main_c.judge_new()
    #  ★★
    gap_jd = ans_dic['figure_turn_result']['latest_turn_dic']['oldest_ans']['gap']
    if new_jd:
        if result_turn == 1:  # ターンが確認された場合（最優先）
            reset_all_position()  # ポジションのリセット&情報アップデート
            order_setting(order_pair, info_lose)  # オーダー発行
        elif rename_latest3 == 1:  # ターン未遂が確認された場合（早い場合）
            order_setting(order_pair, info_lose)  # オーダー発行
    else:
        if result_turn == 1:  # ターンが確認された場合（最優先）
            print("  ターンを確認（時間で不可）　こんなことある？")
        elif rename_latest3 == 1:  # ターン未遂が確認された場合（早い場合）
            print("  ターン未遂を確認（時間で不可）こんなことある？")


def mode2():
    global gl_exe_mode

    # print(" Mode2")


def exe_manage():
    """
    時間やモードによって、実行関数等を変更する
    :return:
    """
    # 時刻の分割（処理で利用）
    time_hour = gl_now.hour  # 現在時刻の「時」のみを取得
    time_min = gl_now.minute  # 現在時刻の「分」のみを取得
    time_sec = gl_now.second  # 現在時刻の「秒」のみを取得

    # グローバル変数の宣言（編集有分のみ）
    global gl_midnight_close_flag, gl_now_price_mid, gl_data5r_df, gl_first, gl_first_time

    # ■深夜帯は実行しない　（ポジションやオーダーも全て解除）
    if 3 <= time_hour < 6:
        if gl_midnight_close_flag == 0:  # 繰り返し実行しないよう、フラグで管理する
            reset_all_position()
            tk.line_send("■深夜のポジション・オーダー解消を実施")
            gl_midnight_close_flag = 1  # 実施済みフラグを立てる
    # ■実行を行う
    else:
        gl_midnight_close_flag = 0  # 実行可能時には深夜フラグを解除しておく（毎回やってしまうけどいいや）

        # ■時間内でスプレッドが広がっている場合は強制終了し実行しない　（現価を取得しスプレッドを算出する＋グローバル価格情報を取得する）
        price_dic = oa.NowPrice_exe("USD_JPY")
        if "error" in price_dic:  # APIエラーの場合はスキップ
            print("API異常発生の可能性")
            sys.exit()  # 強制終了
        gl_now_price_mid = price_dic['mid']  # 念のために保存しておく（APIの回数減らすため）
        if price_dic['spread'] > gl_arrow_spread:
            oa.print_i("    ▲スプレッド異常")
            sys.exit()  # 強制終了

        # ■いずれは低頻度モードのみでの取得になるかも
        # ■直近の検討データの取得　　　メモ：data_format = '%Y/%m/%d %H:%M:%S'
        if time_min % 5 == 0 and time_sec == 6:  # キャンドルの確認（５分に一回）
            print("■■■Candle調査", gl_live, gl_now)  # 表示用（実行時）
            all_update_information()  # 情報アップデート
            d5_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 30}, 1)  # 時間昇順
            gl_data5r_df = d5_df.sort_index(ascending=False)  # 対象となるデータフレーム（直近が上の方にある＝時間降順）をグローバルに
            d5_df.to_csv(tk.folder_path + 'main_data5.csv', index=False, encoding="utf-8")  # 直近保存用

            mode1()

        elif time_min % 1 == 0 and time_sec % 2 == 0:  # 高頻度での確認事項（キャンドル調査時のみ飛ぶ）
            all_update_information()  # 情報アップデート
            if life_check():  # いずれかのオーダーのLifeが生きている場合【【高頻度モードの条件】】
                # print("■■", gl_live, gl_now)  # 表示用（実行時）
                mode2()

        # ■　初回だけ実行と同時に行う
        if gl_first == 0:
            gl_first = 1
            gl_first_time = gl_now
            print("■■■初回", gl_now, gl_exe_mode, gl_live)  # 表示用（実行時）
            all_update_information()  # 情報アップデート
            d5_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 30}, 1)  # 時間昇順
            # ↓時間指定
            # jp_time = datetime.datetime(2023, 7, 6, 11, 1, 0)
            # euro_time_datetime = jp_time - datetime.timedelta(hours=9)
            # euro_time_datetime_iso = str(euro_time_datetime.isoformat()) + ".000000000Z"  # ISOで文字型。.0z付き）
            # param = {"granularity": "M5", "count": 30, "to": euro_time_datetime_iso}
            # d5_df = oa.InstrumentsCandles_exe("USD_JPY", param)
            # ↑時間指定
            gl_data5r_df = d5_df.sort_index(ascending=False)  # 対象となるデータフレーム（直近が上の方にある＝時間降順）をグローバルに
            d5_df.to_csv(tk.folder_path + 'main_data5.csv', index=False, encoding="utf-8")  # 直近保存用
            mode1()


def exe_loop(interval, fun, wait=True):
    """
    :param interval: 何秒ごとに実行するか
    :param fun: 実行する関数（この関数への引数は与えることが出来ない）
    :param wait: True固定
    :return: なし
    """
    global gl_now, gl_now_str
    base_time = time.time()
    while True:
        # 現在時刻の取得
        gl_now = datetime.datetime.now().replace(microsecond=0)  # 現在の時刻を取得
        gl_now_str = str(gl_now.month).zfill(2) + str(gl_now.day).zfill(2) + "_" + \
                     str(gl_now.hour).zfill(2) + str(gl_now.minute).zfill(2) + "_" + str(gl_now.second).zfill(2)
        t = threading.Thread(target=fun)
        t.start()
        if wait:  # 時間経過待ち処理？
            t.join()
        # 待機処理
        next_time = ((base_time - time.time()) % 1) or 1
        time.sleep(next_time)


def all_update_information():
    """
    全ての情報を更新する
    :return:
    """
    main_c.update_information()  # 露払い時の変更を取得しておく（エラーが出たら、、どうしよう）
    second_c.update_information()
    third_c.update_information()
    fourth_c.update_information()


def reset_all_position():
    """
    全てのオーダー、ポジションをリセットして、更新する
    :return:
    """
    oa.OrderCancel_All_exe()  # 露払い
    oa.TradeAllClose_exe()  # 露払い
    all_update_information()  # 関数呼び出し（アップデート）


def life_check():
    """
    オーダーが生きているかを確認する
    :return:
    """
    if main_c.life or second_c.life or third_c.life or fourth_c.life:
        ans = True
    else:
        ans = False
    # print(main_c.life, second_c.life, third_c.life, fourth_c.life)
    # print(ans)
    return ans


def recent_trends():
    """
    直近の勝ち負けの傾向を把握する（各、直近取引の３回の勝敗）
    :return:
    """
    total_pips = 0
    total_m = 0
    # 計算していく
    ans = recent_trends_support(main_c.pips_res_arr)
    total_m = total_m + ans['count']
    total_pips = total_pips + ans['total']

    ans = recent_trends_support(second_c.pips_res_arr)
    total_m = total_m + ans['count']
    total_pips = total_pips + ans['total']

    ans = recent_trends_support(third_c.pips_res_arr)
    total_m = total_m + ans['count']
    total_pips = total_pips + ans['total']

    if total_m >= 4:
        # 負け越し
        result = -1
        comment = "負け越し中"
    else:
        result = 1
        comment = "負け注意"

    return {"result": result, "count": total_m, "total_pips": total_pips, "comment": comment}


def recent_trends_support(arr):
    m_count = 0
    pip_total = 0
    for i in range(len(arr)):
        if i >=2:
            # 直近の二つまで
            break
        else:
            if arr[i] < 0:
                m_count += 1
                pip_total = pip_total + arr[i]
    return {"count": m_count, "total": pip_total}


# ■グローバル変数の宣言等
# 変更なし群
gl_peak_range = 2  # ピーク値算出用　＠ここ以外で変更なし
gl_arrow_spread = 0.008  # 実行を許容するスプレッド　＠ここ以外で変更なし
gl_first = 0
# 変更あり群
gl_now = 0  # 現在時刻（ミリ秒無し） @exe_loopのみで変更あり
gl_now_str = ""
gl_now_price_mid = 0  # 現在価格（念のための保持）　@ exe_manageでのみ変更有
gl_midnight_close_flag = 0  # 深夜突入時に一回だけポジション等の解消を行うフラグ　＠time_manageのみで変更あり
gl_exe_mode = 0  # 実行頻度のモード設定　＠
gl_total_pips = 0  # totalの合計値
gl_total_yen = 0  # Unit含めたトータル損益（円の完全）
gl_data5r_df = 0  # 毎回複数回ローソクを取得は時間無駄なので１回を使いまわす　＠exe_manageで取得
gl_trade_num = 0  # 取引回数をカウントする
gl_trade_win = 0  # プラスの回数を記録する
gl_live = "Pra"
gl_first_time = ""  # 初回の時間を抑えておく（LINEで見やすくするためだけ）

# ■オアンダクラスの設定
fx_mode = 1  # 1=practice, 0=Live
if fx_mode == 1:  # practice
    oa = oanda_class.Oanda(tk.accountID, tk.access_token, tk.environment)  # インスタンス生成
    gl_live = "Pra"
else:  # Live
    oa = oanda_class.Oanda(tk.accountIDl, tk.access_tokenl, tk.environmentl)  # インスタンス生成
    gl_live = "Live"

# ■ポジションクラスの生成
main_c = order_information("1", oa)  # 順思想のオーダーを入れるクラス
second_c = order_information("2", oa)  # 順思想のオーダーを入れるクラス
third_c = order_information("3", oa)  # 順思想のオーダーを入れるクラス
fourth_c = order_information("4", oa)  # 順思想のオーダーを入れるクラス

# ■処理の開始
reset_all_position()  # 開始時は全てのオーダーを解消し、初期アップデートを行う
tk.line_send("■■新規スタート", gl_live)
# main()
exe_loop(1, exe_manage)  # exe_loop関数を利用し、exe_manage関数を1秒ごとに実行
