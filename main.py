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
        self.crcdo = False  # ポジションを変更履歴があるかどうか(複数回の変更を考えるならIntにすべき？）
        self.crcdo_sec = 0  # ポジション所有から何秒後に、最新のCRCDOを行ったかを記録する。
        self.crcdo_lc = 0  # ロスカ変更後のLCライン
        self.crcdo_tp = 0  # ロスカ変更後のTPライン
        self.pips_max = 0  # 最高プラスが額を記録
        self.pips_min = 0  # 最低のマイナス額を記録
        self.now_price = 0  # 直近の価格を記録しておく（APIを叩かなくて済むように）
        self.api_try_num = 3  # APIのエラー（今回はLC底上げに利用）は３回まで

        # リセット対象外（規定値がある物）
        self.order_timeout = 15  # リセ無。分で指定。この時間が過ぎたらオーダーをキャンセルする
        self.lc_border = 0.03  # リセ無。プラス値でプラス域でロスカットを実施 マイナス値でその分のマイナスを許容する Default=0.03
        self.tp_border = 0.1  # リセ無。プラス値でプラス域でロスカットを実施 マイナス値でその分のマイナスを許容する Default=0.03
        self.lc_range = 0.01  # CDCRO時、最低のライン（プラス値で最低の利益の確保）
        self.tp_range = 0.05

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
        self.api_try_num = 3  # APIのエラー（今回はLC底上げに利用）は３回までself.crcdo = False  # ポジションを変更履歴があるかどうか(複数回の変更を考えるならIntにすべき？）
        self.crcdo_sec = 0  # ポジション所有から何秒後に、最新のCRCDOを行ったかを記録する。
        self.crcdo_lc = 0  # ロスカ変更後のLCライン
        self.crcdo_tp = 0  # ロスカ変更後のTPライン
        self.pips_max = 0  # 最高プラスが額を記録
        self.pips_min = 0  # 最低のマイナス額を記録

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
        print("   <表示>", self.name, datetime.datetime.now().replace(microsecond=0))
        print("　 【LIFE】", self.life)
        print("　 【CRCDO】", self.crcdo)
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
        print("  TIME JD",self.order['time_past_continue'], "<", wait_time_new * 59 , "成立で不可")
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

    def crcdo_set(self, boo):
        # print("  CRCDOフラッグ変化", self.name, boo)
        oa.print_i("  CRCDOフラッグ変化", self.name, boo)
        self.crcdo = boo

    def life_set(self, boo):
        # print("  Life変化", self.name, boo)
        oa.print_i("  　Life変化", self.name, boo)
        self.life = boo

    def make_order(self):
        global gl_trade_win
        # Planを元にオーダーを発行する
        if self.plan['price'] != 999:  # 例外時（price=999)以外は、通常通り実行する
            # print(" 108行テスト", self.plan)
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
                tk.line_send(" 　Order不成立（今後ループの可能性）", order_ans['order_id'])
            else:
                self.life_set(True)  # LIFEのONはここでのみ実施
                pass  # 送信はMainで実施
        else:  # price=999の場合（例外の場合）処理不要・・？
            pass

    def close_order(self):
        # オーダークローズする関数 (情報のリセットは行わなず、Lifeの変更のみ）
        print("OrderCnacel関数", self.order['id'])
        res_dic = oa.OrderDetails_exe(self.order['id'])
        if "order" in res_dic:
            status = res_dic['order']['state']
            if status == "PENDING":  # orderがキャンセルできる状態の場合
                print(" orderCancel検討")
                res = oa.OrderCancel_exe(self.order['id'])
                if type(res) is int:
                    oa.print_i("   存在しないorder（ERROR）")
                    print("   存在しないorder（ERROR）")
                else:
                    self.order['state'] = "CANCELLED"
                    self.life_set(False)
                    oa.print_i(" 注文の為？オーダー解消", self.order['id'])
                    print(" 注文の為？オーダー解消", self.order['id'])
                    # tk.line_send("  オーダー解消", self.order['id'])
            else:  # FIEELDとかCANCELLEDの場合は、lifeにfalseを入れておく
                oa.print_i("   order無し")
                print("   order無し")
        else:
            oa.print_i("  order無し（APIなし）")
            print("  order無し（APIなし）")

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
        global gl_total_pips, gl_now_price_mid, gl_trade_win
        if self.life:  # LifeがTrueの場合は、必ずorderIDが入っている
            oa.print_i(" □□情報を更新します", self.name)
            # ★現在価格を求めておく
            price_dic = oa.NowPrice_exe("USD_JPY")
            if self.plan['ask_bid'] > 0:  # プラス(買い) オーダーの場合
                self.now_price = float(price_dic["ask"])
            else:
                self.now_price = float(price_dic["bid"])
            gl_now_price_mid = self.now_price

            # （０）情報取得 + 変化点キャッチ（ 情報を埋める前に変化点をキャッチする）
            temp = oa.OrderDetailsState_exe(self.order['id'])
            # （1-1)　変化点を算出しSTATEを変更する（ポジションの新規取得等）
            if self.order['state'] == "PENDING" and temp['order_state'] == 'FILLED':  # 現orderあり⇒約定（取得時）
                oa.print_i("  ★position取得！")
                direction_t = self.order['units'] / abs(self.order['units'])
                # tk.line_send("  (取得)", float(temp['position_price']), direction_t, datetime.datetime.now().replace(microsecond=0))
                change_flag = 1  # 結果の可視化フラグ
            elif self.order['state'] == "PENDING" and temp['position_state'] == 'CLOSED':  # 現orderあり⇒ポジクローズ
                oa.print_i("  ★即ポジ即解消済！")
                self.life_set(False)
                tk.line_send("即ポジ即解消！", self.name, datetime.datetime.now().replace(microsecond=0))
                change_flag = 1  # 結果の可視化フラグ
            elif self.position['state'] == "OPEN" and temp['position_state'] == "CLOSED":  # 現ポジあり⇒ポジ無し（終了時）
                oa.print_i("  ★position解消")
                self.life_set(False)
                gl_total_pips = round(gl_total_pips + temp['position_pips'], 3)  # トータル計算
                if temp['position_pips'] >=0 :
                    gl_trade_win += 1  # トータルプラス計算
                for_view_temp = "w" + str(gl_trade_win) + "/" + str(gl_trade_num) + ",TotalPips" + str(gl_total_pips) + ",P-M" + str(self.pips_min) + "," + str(self.pips_max)
                tk.line_send(" ▲解消", temp['position_close_price'], temp['position_pips'], for_view_temp, " time:",
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
            if self.order['time_past'] > self.order_timeout * 60 and self.order['state'] == "PENDING":
                print("時間解消@")
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
        p = self.position
        o = self.order
        if self.crcdo is False and self.position['state'] == "OPEN":  # ポジションのCRCDO歴がない場合⇒ポジションLC調整を行う可能性
            # 初回と長期間保有時のLC変更
            cl_span = 60  # 1分に１回しか更新しない
            if p['pips'] > 0.025:  # ある程度のプラスがあれば、LC底上げを実施する
                self.lc_range = -0.02  # プラス値でプラス域でロスカットを実施。マイナス域でマイナス域でのロスカット
                lc_price = round(p['price'] - self.lc_range if self.plan['ask_bid'] < 0 else p['price'] + self.lc_range, 3)
                tp_price = round(self.now_price - self.tp_range if self.plan['ask_bid'] < 0 else self.now_price + self.tp_range, 3)  # 微＋
                self.crcdo_lc = lc_price  # ロスカ変更後のLCラインを保存
                self.crcdo_tp = tp_price  # ロスカ変更後のTPラインを保存
                data = {
                    "stopLoss": {"price": str(lc_price), "timeInForce": "GTC"},
                    # "takeProfit": {"price": str(tp_price), "timeInForce": "GTC"},
                    # "trailingStopLoss": {"distance": 0.05, "timeInForce": "GTC"},
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
                    # tk.line_send("　(LC底上げ)初回")
        # elif self.crcdo:
        #     # 2回目以降のCRCDO
        #     # プラス方向にLCを広げる処理を実施　（セルフトレールのようなもの）
        #     od = 0.7
        #     print("    CRCDO確認",self.crcdo_sec, p['time_past'])
        #     if p['time_past']-self.crcdo_sec > 10:  # 前回のCRCDOよりN秒以上空いていれば、CRCDOを再検討する
        #         if p['pips'] > 0.04:  # 価値ピップスのod倍の部分で利確を行う
        #             temp_lc_range = p['pips'] * od  # 通常はself.lc_range
        #             lc_price = round(p['price'] - temp_lc_range if self.plan['ask_bid'] < 0 else p['price'] + temp_lc_range, 3)
        #             tp_price = round(self.now_price - self.tp_range if self.plan['ask_bid'] < 0 else self.now_price + self.tp_range, 3)  # 微＋
        #
        #             # 実行判定（向きによって変わるため）
        #             exe_crcdo = 0  # ばあいによってはCRCDOしない可能性があるので、フラグを０に初期化しておく。
        #             if o['direction'] < 1:  # 谷方向の場合
        #                 if self.crcdo_lc > lc_price:
        #                     exe_crcdo = 1  # LCラインを押し下げる場合（プラス拡大）
        #                     print("   CDCRO実行へ　谷　>", self.crcdo_lc, lc_price, p['pips'], temp_lc_range, p['price'],self.plan['ask_bid'])
        #                 else:
        #                     print("  拡大せず（谷） >", self.crcdo_lc, lc_price, p['pips'], temp_lc_range, p['price'],self.plan['ask_bid'])
        #             else:
        #                 if self.crcdo_lc < lc_price:
        #                     exe_crcdo = 1  # LCラインを押し下げる場合（プラス拡大）
        #                     print("   CDCRO実行へ　山　<", self.crcdo_lc, lc_price, p['pips'], temp_lc_range, p['price'],self.plan['ask_bid'])
        #                 else:
        #                     print("  拡大せず（山） <", self.crcdo_lc, lc_price, p['pips'], temp_lc_range, p['price'],self.plan['ask_bid'] )
        #
        #             if exe_crcdo == 1:
        #                 data = {
        #                     "stopLoss": {"price": str(lc_price), "timeInForce": "GTC"},
        #                     # "takeProfit": {"price": str(tp_price), "timeInForce": "GTC"},
        #                     # "trailingStopLoss": {"distance": 0.05, "timeInForce": "GTC"},
        #                 }
        #                 res = oa.TradeCRCDO_exe(p['id'], data)  # ポジションを変更する
        #                 print(res)
        #
        #                 if type(res) is int:
        #                     tk.line_send("CRCDミス", self.api_try_num)
        #                     if self.api_try_num < 0:
        #                         oa.print_i(" ★CRCDC諦め")
        #                         self.crcdo_set(True)  # main本体で、ポジションを取る関数で解除する
        #                     self.api_try_num = self.api_try_num - 1
        #                 else:
        #                     self.crcdo_set(True)  # main本体で、ポジションを取る関数で解除する
        #                     self.crcdo_sec = p['time_past']  # 変更時の経過時点を記録しておく
        #                     oa.print_i("    (LC底上げ)二回目以降")
        #                     # tk.line_send("　(LC底上げ)二回目以降")
        #
        #                 self.crcdo_lc = lc_price  # ロスカ変更後のLCラインを保存
        #                 self.crcdo_tp = tp_price  # ロスカ変更後のTPラインを保存
        #
        #             else:
        #                 # exe_code=0
        #                 pass
        #
        #         else:
        #             print("     CRCRO再実行確認⇒なし",p['pips'])

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

    return round(base_line, 3)


def order_setting(order_info_temp, ans_dic):
    """
    検証し、条件達成でオーダー発行
    :order_info_temp: 色々
    :param ans_dic: ターゲットとなるクラスのインスタンス
    :return:
    """

    global gl_trade_num, gl_now_price_mid
    print(" order_setting", order_info_temp)

    # 代表的なものを変数に入れておく
    gl_trade_num = gl_trade_num + 1
    line_base = order_info_temp['line_base']
    expect_direction = order_info_temp['expect_dir']
    margin = order_info_temp['margin']
    lc = order_info_temp['lc']
    memo_turn = ans_dic['figure_turn_result']['latest_turn_dic']['memo_all']

    # ■価格を決定する
    # 順張り用のオーダー（辞書形式）を作成する　⇒　（別途準備中）　当面は直近価格で。

    line_base = order_line_adjustment_simple(line_base, margin, expect_direction)  # ここでのSTOPは順思想（逆張り）

    # オーダー発行
    order_info = {
        "price": line_base,
        "lc_range": lc,
        "tp_range": 0.09,
        "ask_bid": expect_direction,  # 順思想
        "units": 20000,
        "type": "STOP",  # ここはストップ（順張り）専用！
        "tr_range": 0.2,  # ↑ここまでオーダー
        "memo": ""
    }
    fw.update_information()  # timepast等を埋めるため、まずupdateが必要
    # オーダー発行
    fw.order_registration(order_info)  # プラン自身を代入
    fw.make_order()
    mes = " baseline:" + str(line_base)

    tk.line_send("■折返Position！", gl_trade_num, "回目(", datetime.datetime.now().replace(microsecond=0), ")",
                 "トリガー:", order_info_temp['memo'], "、情報:", mes, memo_turn)


def mode1():
    """
    低頻度モード（条件を検索し、４２検査を実施する）
    :return: なし
    """
    print("Mode1")
    # ポジションを２つ用意するため、二つを初期化する
    fw.update_information()  # 初期値を入れるために一回は必要（まぁ毎回やっていい）
    fw_stop.update_information()  # 初期値を入れるために一回は必要（まぁ毎回やっていい）

    # チャート分析結果を取得する
    inspection_condition = {
        "now_price": gl_now_price_mid,  # 現在価格を渡す
        "data_r": gl_data5r_df,  # 対象となるデータ
        "figure": {"ignore": 1, "latest_n": 2, "oldest_n": 30},
        "macd": {"short": 20, "long": 30},
        "save": True,  # データをCSVで保存するか（検証ではFalse推奨。Trueの場合は下の時刻は必須）
        "time_str": gl_now_str,  # 記録用の現在時刻
    }
    ans_dic = f.inspection_candle(inspection_condition)  # 状況を検査する（買いフラグの確認）

    # 一旦整理。。
    ans = ans_dic['judgment']
    turn_ans_temp = ans_dic['figure_turn_result']['result_dic']['turn_ans']  # 直近のターンがあるかどうか（連続性の考慮無し）
    turn_ans = ans_dic['figure_turn_result']['result_dic']['total_ans']  # 連続性を考慮したうえでのターン判定
    turn_target_price = ans_dic['figure_turn_result']['order_dic']['target_price']
    turn_expect_direction = ans_dic['figure_turn_result']['order_dic']['direction']
    macd_ans = ans_dic['macd_result']['cross']
    latest3_ans = ans_dic['latest3_figure_result']['result']
    latest3_target_price = ans_dic['latest3_figure_result']['order_dic']['target_price']
    latest3_expect_direction = ans_dic['latest3_figure_result']['order_dic']['direction']

    if turn_ans_temp == 1:  # ターンが確認された場合（最優先）
        print("  ターンを確認")
        if turn_ans == 1:  # そのさらに直前のターンが発生がある場合
            print("   その直前にもターンを確認⇒オーダー無し")
            new_jd = fw.input_info_and_judge_new(ans_dic)  # 情報を入れつつ、新規オーダーを入れるかを判定する
            if new_jd:
                tk.line_send("Range状態のターンの為、オーダー無し")
            else:
                print("  時間制約あり")
        else:
            new_jd = fw.input_info_and_judge_new(ans_dic)  # 情報を入れつつ、新規オーダーを入れるかを判定する
            if new_jd:
                print("   ★オーダー発行")
                order_temp = {
                    "line_base": turn_target_price,
                    "expect_dir": turn_expect_direction,
                    "lc": 0.045,  # 少し狭い目のLC
                    "margin": 0.02,
                    "memo": "ターン起点"
                }
                order_setting(order_temp, ans_dic)  # オーダー発行
            else:
                # print(" 時間的制約で発行せず　turn")
                pass
    elif latest3_ans == 1:  # ターン未遂が確認された場合（早い場合）
        print("  ターン未遂を確認　★オーダー発行")
        new_jd = fw.input_info_and_judge_new(ans_dic)  # 情報を入れつつ、新規オーダーを入れるかを判定する
        if new_jd:
            order_temp = {
                "line_base": latest3_target_price,
                "expect_dir": latest3_expect_direction,
                "lc": 0.025,  # 非常に狭いLC
                "margin": 0.02,
                "memo": "ターン未遂起点"
            }
            order_setting(order_temp, ans_dic)  # オーダー発行
        else:
            # print(" 時間的制約で発行せず　figure3")
            pass


def mode2():
    global gl_exe_mode
    # fw.update_information()
    # fw_stop.update_information()
    # rv_stop.update_information()

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
    global gl_midnight_close_flag, gl_now_price_mid, gl_data5r_df, gl_first

    # ■深夜帯は実行しない　（ポジションやオーダーも全て解除）
    if 3 <= time_hour < 6:
        if gl_midnight_close_flag == 0:  # 繰り返し実行しないよう、フラグで管理する
            oa.OrderCancel_All_exe()
            oa.TradeAllClose_exe()
            tk.line_send("■深夜のポジション・オーダー解消を実施")
            gl_midnight_close_flag = 1  # 実施済みフラグを立てる
    # ■実行を行う
    else:
        gl_midnight_close_flag = 0  # 実行可能時には深夜フラグを解除しておく（毎回やってしまうけどいいや）

        # ■時間内でスプレッドが広がっている場合は強制終了し実行しない　（現価を取得しスプレッドを算出する＋グローバル価格情報を取得する）
        price_dic = oa.NowPrice_exe("USD_JPY")
        gl_now_price_mid = price_dic['mid']  # 念のために保存しておく（APIの回数減らすため）
        if price_dic['spread'] > gl_arrow_spread:
            oa.print_i("    ▲スプレッド異常")
            sys.exit()  # 強制終了

        # ■いずれは低頻度モードのみでの取得になるかも
        # ■直近の検討データの取得　　　メモ：data_format = '%Y/%m/%d %H:%M:%S'
        if time_min % 5 == 0 and time_sec == 6:  # キャンドルの確認（５分に一回）
            print("■■■Candle調査", gl_now)  # 表示用（実行時）
            d5_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 30}, 1)  # 時間昇順
            gl_data5r_df = d5_df.sort_index(ascending=False)  # 対象となるデータフレーム（直近が上の方にある＝時間降順）をグローバルに
            d5_df.to_csv(tk.folder_path + 'main_data5.csv', index=False, encoding="utf-8")  # 直近保存用
            mode1()

        elif time_min % 1 == 0 and time_sec % 2 == 0:  # 高頻度での確認事項（キャンドル調査時のみ飛ぶ）
            fw.update_information()  # 初期値を入れるために一回は必要（まぁ毎回やっていい）
            fw_stop.update_information()  # 初期値を入れるために一回は必要（まぁ毎回やっていい）
            if fw.life or fw_stop.life:  # どちらかのオーダーがアクティブな場合【【高頻度モードの条件】】
                # print("■■■", gl_now)  # 表示用（実行時）
                mode2()

        # ■　初回だけ実行と同時に行う
        if gl_first == 0:
            gl_first = 1
            print("■■■初回", gl_now, gl_exe_mode)  # 表示用（実行時）
            d5_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 30}, 1)  # 時間昇順
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

def test_exe():
    for i in range(10):
        print(i)

# ■オアンダクラスの設定
fx_mode = 1  # 1=practice, 0=Live
if fx_mode == 1:  # practice
    oa = oanda_class.Oanda(tk.accountID, tk.access_token, tk.environment)  # インスタンス生成
else:  # Live
    oa = oanda_class.Oanda(tk.accountIDl, tk.access_tokenl, tk.environmentl)  # インスタンス生成

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
gl_data5r_df = 0  # 毎回複数回ローソクを取得は時間無駄なので１回を使いまわす　＠exe_manageで取得
gl_trade_num = 0  # 取引回数をカウントする
gl_trade_win = 0  # プラスの回数を記録する

# ■ポジションクラスの生成
fw = order_information("逆思想", oa)  # 順思想のオーダーを入れるクラス
fw_stop = order_information("順思想", oa)  # 順思想のオーダーを入れるクラス
rv_stop = order_information("rv_stop", oa)  # 順思想のオーダーを入れるクラス

# ■処理の開始
oa.OrderCancel_All_exe()  # 露払い
oa.TradeAllClose_exe()  # 露払い
# main()
exe_loop(1, exe_manage)  # exe_loop関数を利用し、exe_manage関数を1秒ごとに実行
