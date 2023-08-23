import time
import pandas as pd
import datetime
import programs.tokens as tk
import programs.oanda_class as oanda_class


class order_information:
    total_pips = 0  # クラス変数で管理
    total_yen = 0
    position_times = 0

    def __init__(self, name, oa):
        self.oa = oa  # クラス変数でもいいが、LiveとPracticeの混在ある？　引数でもらう
        # リセ対象群
        self.name = name  # FwかRvかの表示用。引数でもらう
        self.order_permission = False  # updateやOrder時に、即時オーダーを入れるか（False時はTrueになったUpdateで入れる）
        self.life = False  # 有効かどうか（オーダー発行からポジションクローズまで）
        self.plan_life = False
        self.plan = {}  # plan情報
        self.order = {"id": 0, "state": "", "time_past": 0}  # オーダー情報 (一部初期値必要）
        self.position = {"id": 0, "state": "", "time_past": 0, "pips": 0}  # ポジション情報 (一部初期値必要）
        self.pips_res = 0
        self.crcdo_history = False  # ポジションを変更履歴があるかどうか(複数回の変更を考えるならIntにすべき？）
        self.crcdo_sec_counter = 0  # ポジション所有から何秒後に、最新のCRCDOを行ったかを記録する。
        self.crcdo_border = 0  # ロスカや利確を変更するライン
        self.crcdo_guarantee = 0  # 最低限確保する利益を指定（マイナスだとマイナス範囲でせり上げる）
        self.crcdo_self_trail_exe = False  # 二回目以降の自動トレール（Oanda機能ではなく自作）をおこなうかどうか（Trueで実施）
        self.crcdo_lc_price = 0  # ロスカ変更後のLCライン
        self.crcdo_tp_price = 0  # ロスカ変更後のTPライン
        self.crcdo_trail_ratio = 0.5  # トレール幅を勝ちPipsの何割にLINEを引くか
        self.crcdo_history_by_time = False  # 時間経過によるポジショん変更履歴があるかどうか
        self.crcdo_target_lc_by_time = 0
        self.crcdo_border_by_time = 0
        self.crcdo_max_lc_by_time = 0
        self.pips_win_max = 0  # 最高プラスが額を記録
        self.pips_lose_max = 0  # 最低のマイナス額を記録
        self.pips_res_arr = []  # 過去の結果を登録しておく
        self.now_price = 0  # 直近の価格を記録しておく（APIを叩かなくて済むように）
        self.api_try_num = 3  # APIのエラー（今回はLC底上げに利用）は３回まで
        self.pip_win_hold_time = 0
        self.pip_lose_hold_time = 0

        # リセット対象外（規定値がある物）
        self.order_timeout = 20  # リセ無。分で指定。この時間が過ぎたらオーダーをキャンセルする
        self.position_timeout = 15
        self.lc_border = 0.03  # リセ無。プラス値でプラス域でロスカットを実施 マイナス値でその分のマイナスを許容する Default=0.03
        self.tp_border = 0.1  # リセ無。プラス値でプラス域でロスカットを実施 マイナス値でその分のマイナスを許容する Default=0.03
        self.lc_range = 0.01  # CDCRO時、最低のライン（プラス値で最低の利益の確保）
        self.tp_range = 0.05
        # アップデートで初期値を入れておく。。やりたくはないけど
        self.update_information()
        self.print_info()

    def reset(self):
        # 完全にそのオーダーを削除する ただし、Planは消去せず残す
        #
        # tself.print_i("   ◆リセット", self.name)
        self.name = "None"  # 一度リセットされるとNoneになる。一番最初は数字の名前がついている（インスタンス生成時）
        self.life_set(False)
        self.plan_life = False
        self.crcdo_history = False
        self.crcdo_history_by_time = False
        self.crcdo_self_trail_exe = False
        self.plan = {}
        self.order = {"id": 0, "state": "", "time_past": 0}  # オーダー情報 (idとステートは初期値を入れておく）
        self.position = {"id": 0, "state": "", "time_past": 0, "pips": 0}  # ポジション情報 (idとステートは初期値を入れておく））
        self.api_try_num = 3  # APIのエラー（今回はLC底上げに利用）は３回までself.crcdo_history = False
        self.order_permission = False
        self.crcdo_sec_counter = 0  # ポジション所有から何秒後に、最新のCRCDOを行ったかを記録する。
        self.crcdo_lc_price = 0  # ロスカ変更後のLCライン
        self.crcdo_tp_price = 0  # ロスカ変更後のTPライン
        self.pips_win_max = 0  # 最高プラスが額を記録
        self.pips_lose_max = 0  # 最低のマイナス額を記録
        self.order_timeout = 20  # リセ無。分で指定。この時間が過ぎたらオーダーをキャンセルす
        self.update_information()

    def print_info(self):
        print("   <表示>", self.name, datetime.datetime.now().replace(microsecond=0))
        print("　 【life】", self.life)
        print("   【name】", self.name)
        print("   【order_permission】", self.order_permission)
        print("   【plan_life】", self.plan_life)
        print("　 【crcdo_history】", self.crcdo_history)
        print("　 【order】", self.order['id'], self.order)
        print("　 【position】", self.position['id'], self.position)
        print("   【plan】", self.plan)

    def order_plan_registration(self, plan):
        """
        【最重要】
        【最初】オーダー計画情報をクラスに登録する（保存する）。名前やCDCRO情報があれば、その登録含めて行っていく。
        :param plan:units,ask_bid,price,tp_range,lc_range,type,tr_range は必須。それ以外は任意。
        :return:
        """
        self.reset()  # 一旦リセットする
        self.plan = plan  # 受け取ったプラン情報(そのままOrderできる状態が基本）
        self.plan_life = True  # プランフラグを有効にする）

        # (1)クラスの名前を付ける (引数で指定されている場合）
        if 'name' in plan:
            self.name = plan['name']  # 名前を入れる(クラス内の変更）

        # (2)各フラグを指定しておく
        self.order_permission = plan['order_permission']  # 即時のオーダー判断に利用する

        # (3-1) 付加情報１　各便利情報を格納しておく
        self.plan['lc_price'] = round(self.plan['price'] -
                                      (abs(self.plan['lc_range']) * self.plan['direction']), 3)
        self.plan['tp_price'] = round(self.plan['price'] +
                                      (abs(self.plan['tp_range']) * self.plan['direction']), 3)
        self.plan['target_price'] = self.plan['margin'] + self.plan['price']

        self.plan['time'] = datetime.datetime.now()

        if 'order_timeout' in plan:
            self.order_timeout = plan['order_timeout']

        if 'crcdo' in plan:
            p = plan['crcdo']
            # 単純LC
            self.crcdo_border = p['crcdo_border']
            self.crcdo_guarantee = p['crcdo_guarantee']
            # LC Trail
            self.crcdo_trail_ratio = p['crcdo_trail_ratio']
            self.crcdo_self_trail_exe = p['crcdo_self_trail_exe']
        else:
            # アウトプット用に、入れておく。
            p = {}
            # 単純LC
            self.crcdo_border = 0
            self.crcdo_guarantee = 0
            # LC Trail
            self.crcdo_trail_ratio = 0
            self.crcdo_self_trail_exe = False

        # (4)オーダーを発行する
        if self.order_permission:
            self.make_order()

    def life_set(self, boo):
        self.life = boo
        if boo:
            pass
        else:
            # Life終了時（＝能動オーダークローズ、能動ポジションクローズ、市場で発生した成り行きのポジションクローズで発動）
            print(" LIFE 終了", self.name)
            self.output_res()  # 解析用にポジション情報を収集しておく

    def make_order(self):
        # Planを元にオーダーを発行する

        # 異常な数のオーダーを防御する
        # (1)　ポジション数の確認
        position_num_dic = self.oa.TradeAllCount_exe()
        position_num = position_num_dic['data']  # 現在のオーダー数を取得
        if position_num >= 6:
            # エラー等で大量のオーダーが入るのを防ぐ
            print(" 大量ポジション入る可能性", position_num_dic, datetime.datetime.now().replace(microsecond=0))
            tk.line_send(" 【注】大量ポジション入る可能性", position_num_dic, datetime.datetime.now().replace(microsecond=0))
            return 0
        # (2)オーダー数の確認
        order_num = self.oa.OrderCount_All_exe()
        if order_num >= 6:
            # エラー等で大量のオーダーが入るのを防ぐ
            print(" 大量オーダー入る可能性", order_num, datetime.datetime.now().replace(microsecond=0))
            tk.line_send(" 【注】大量オーダー入る可能性", order_num, datetime.datetime.now().replace(microsecond=0))
            return 0

        # (3)実処理
        if self.order_permission:
            if self.plan['price'] != 999:  # 例外時（price=999)以外は、通常通り実行する
                order_ans_dic = self.oa.OrderCreate_dic_exe(self.plan)  # Plan情報からオーダー発行しローカル変数に結果を格納する
                order_ans = order_ans_dic['data']  # エラーはあんまりないから、いいわ。
                self.order = {  # 成立情報を取り込む
                    "price": order_ans['price'],  # オーダー価格はここでのみ取得
                    "id": order_ans['order_id'],
                    "time": order_ans['order_time'],
                    "cancel": order_ans['cancel'],
                    "state": "PENDING",  # 強引だけど初期値にPendingを入れておく
                    "tp_price": float(order_ans['tp_price']),
                    "lc_price": float(order_ans['lc_price']),
                    "units": float(order_ans['unit']),
                    # ↓plan Directionじゃだめなの？
                    "direction": float(order_ans['unit']) / abs(float(order_ans['unit'])),
                    "tp_range": order_ans['tp_range'],
                    "lc_range": order_ans['lc_range']
                }
                if order_ans['cancel']:  # キャンセルされている場合は、リセットする
                    # print("      ↑オーダーキャンセル発生", self.name)
                    print(" 　Order不成立（今後ループの可能性）", self.name, order_ans['order_id'], datetime.datetime.now().replace(microsecond=0))
                    tk.line_send(" 　Order不成立（今後ループの可能性）", self.name, order_ans['order_id'], datetime.datetime.now().replace(microsecond=0))
                    self.life_set(True)  # LIFEのONはここでのみ実施⇒出力時の謎の無限ループ対策で暫定的にここでもLIFEをONする
                else:
                    print("      オーダー発行完了", self.name, )
                    self.life_set(True)  # LIFEのONはここでのみ実施
            else:  # price=999の場合（例外の場合）処理不要・・？
                pass

    def close_order(self):
        # オーダークローズする関数 (情報のリセットは行わなず、Lifeの変更のみ）
        if self.life:
            self.life_set(False)  # まずはクローズ状態にする　（エラー時の反復を防ぐため。ただし毎回保存される？？）
            res_dic_dic = self.oa.OrderDetails_exe(self.order['id'])
            res_dic = res_dic_dic["data"]
            if "order" in res_dic:
                print(" 　OrderClose関数", self.name)
                status = res_dic['order']['state']
                if status == "PENDING":  # orderがキャンセルできる状態の場合
                    # print(" orderCancel検討")
                    res = self.oa.OrderCancel_exe(self.order['id'])
                    if res['error'] == -1:
                        print("   存在しないorder（ERROR）")
                    else:
                        self.order['state'] = "CANCELLED"
                        print("   注文の為？オーダー解消", self.order['id'])
                else:  # FIEELDとかCANCELLEDの場合は、lifeにfalseを入れておく
                    print("   order無し")
            else:
                print("   order無し（APIなし）")
        else:
            print("  order既にないが、CloseOrder指示あり", self.name)

    def close_position(self):
        # ポジションをクローズする関数 (情報のリセットは行わなず、Lifeの変更のみ）
        if self.life:
            print(" 　PositionClose関数", self.name)
            res_dic = self.oa.TradeClose_exe(self.position['id'], None)
            self.life_set(False)
            if res_dic['error'] == -1:
                pass
            else:
                self.position['state'] = "CLOSED"
                # tk.line_send("  ポジション強制解消", self.position['id'], self.position['pips'])
        else:
             print("    position既にないが、Close関数呼び出しあり", self.name)
            # tself.oa.print_i("    position無し")

    def update_information(self):  # orderとpositionを両方更新する
        # （０）途中からの再起動の場合、lifeがおかしいので。。あと、ポジション解除後についても必要（CLOSEの場合は削除する？）ｓ
        # STATEの種類
        # order "PENDING" "CANCELLED" "FILLED"
        # position "OPEN" "CLOSED"
        if self.life:  # LifeがTrueの場合は、必ずorderIDが入っている(初期値の0の時もあるけど、、形式整えのために呼ぶ場合有）
            # （０）情報取得 + 変化点キャッチ（ 情報を埋める前に変化点をキャッチする ★APIエラーの場合終了）
            temp = self.oa.OrderDetailsState_exe(self.order['id'])
            if temp['error'] == -1:  # APIエラーの場合はスキップ
                print("update Error", self.name)
                return -1
            else:
                temp = temp['data']
            # （1-1)　変化点を算出しSTATEを変更する（ポジションの新規取得等）
            if self.order['state'] == "PENDING" and temp['order_state'] == 'FILLED':  # オーダー達成（Pending⇒Filled）
                if temp['position_state'] == 'OPEN':  # ポジション所持状態
                    order_information.position_times = order_information.position_times + 1
                    # tk.line_send("  (取得)", self.name, order_information.position_times, "個目", datetime.datetime.now().replace(microsecond=0))
                elif temp['position_state'] == 'CLOSED':  # ポジションクローズ（ポジション取得とほぼ同時?にクローズしている場合）
                    # tk.line_send("即ポジ即解消！", self.name,datetime.datetime.now().replace(microsecond=0))
                    if int(temp['position_initial_units']) != int(temp['position_current_units']):
                        # tk.line_send("★　両建て解除（部分含む）発生の可能性")
                        pass
                    self.life_set(False)
            elif self.position['state'] == "OPEN" and temp['position_state'] == "CLOSED":  # 現ポジあり⇒ポジ無し（終了時）
                print(" 成り行きClose", self.name)
                self.life_set(False)
                self.pips_res_arr.insert(0, temp['position_pips'])  # 先頭に、結果を追加していく（先頭からの方が後々集計しやすい）
                self.pips_res = temp['position_pips']
                if "W" in self.name:
                    # Wケースの場合、Pipsは追加しないでおく
                    pass  # total_pipsを変更しない
                else:
                    order_information.total_pips = round(order_information.total_pips + temp['position_pips'], 3)
                temp_yen_result = int(temp['position_pips'] * abs(self.order['units']))  # トータルの円（plだと上手く表示されないので計算する）
                order_information.total_yen = int(order_information.total_yen + temp_yen_result)

                res1 = "【Unit】" + str(self.order['units'])
                id_info = "【orderID】" + str(self.order['id'])
                res2 = "【決:" + str(temp['position_close_price']) + ", " + "取:" + str(self.order['price']) + "】"
                res3 = "【ポジション期間の最大/小の振れ幅】 ＋域:" + str(self.pips_lose_max) + "/ー域:" + str(self.pips_win_max)
                res4 = "【今回結果】" + str(temp['position_pips']) + "," + str(temp_yen_result) + "円\n"
                res5 = "【合計】計" + str(order_information.total_pips) + ",計" + str(order_information.total_yen) + "円"
                now_time_only = oanda_class.str_to_time_hms(str(datetime.datetime.now().replace(microsecond=0)))
                tk.line_send(" ▲解消:", self.name, '\n', now_time_only, '\n',
                             res4, res5, res1, id_info, res2, res3)
            elif self.order['state'] == "PENDING" and temp['order_state'] == 'CANCELLED':  # （取得時）
                pass
            else:
                pass

            # （３）情報を更新(Order発行済み以上では、常に同じ物が返ってくる） これ移し替える必要あるかな・・・？
            # print("Order", temp['order_time'])
            self.order['id'] = temp['order_id']
            self.order['time'] = temp['order_time']  # 日時（日本）の文字列版（時間差を求める場合に利用する）
            self.order['units'] = int(temp['order_units'])
            self.order['state'] = temp['order_state']
            self.order['time_past'] = int(temp['order_time_past'])  # 諸事情でプラス２秒程度ある　経過時間を求める（Trueの場合）
            # ↑ 引数は元データ(文字列時刻)。オーダーを解除しても継続してカウントする秒数
            self.position['id'] = temp['position_id']
            self.position['type'] = temp['position_type']
            self.position['initial_units'] = temp['position_initial_units']
            self.position['current_units'] = temp['position_current_units']
            self.position['time'] = temp['position_time']
            self.position['time_past'] = int(temp['position_time_past'])  # 諸事情でプラス２秒程度ある
            self.position['price'] = float(temp['position_price'])
            self.position['state'] = temp['position_state']
            self.position['realize_pl'] = temp['position_realize_pl']
            self.position['pips'] = float(temp['position_pips'])
            self.position['close_time'] = temp['position_close_time']
            self.position['close_price'] = temp['position_close_price']

            # pip情報の推移を記録する
            temp_pips = float(temp['position_pips'])  # 一時的にプラスマイナスを取得する
            if temp_pips >= 0 and self.position['pips'] < 0:
                # 今回プラスだが、前回はマイナスだった場合、何もしない
                self.pip_win_hold_time = 0
                self.pip_lose_hold_time = 0
            elif temp_pips >= 0 and self.position['pips'] > 0:
                # 今回も前回プラスの場合
                self.pip_win_hold_time = self.pip_win_hold_time + 2  # ２秒ごとの実行なのでプラス２
                self.pip_lose_hold_time = 0
            elif temp_pips < 0 and self.position['pips'] >= 0:
                # 今回マイナスだが、前回プラスの場合
                self.pip_win_hold_time = 0
                self.pip_lose_hold_time = 0
            elif temp_pips < 0 and self.position['pips'] <= 0:
                # 今回も前回もマイナスの場合
                self.pip_win_hold_time = 0
                self.pip_lose_hold_time = self.pip_lose_hold_time + 2  # ２秒ごとの実行なのでプラス２
            self.position['pips'] = float(temp['position_pips'])  # 結果値を更新する
            # プラスマイナス情報を取得しておく
            if self.pips_lose_max < self.position['pips']:  # 最小値更新時
                self.pips_lose_max = self.position['pips']
            if self.pips_win_max > self.position['pips']:  # 最小値更新時
                self.pips_win_max = self.position['pips']

            # (4)矛盾系の状態を解消する（部分解消などが起きた場合に、idがあるのにStateがないなど、矛盾があるケースあり。
            if self.position['id'] != 0 and self.position['state'] == 0:
                # positionIDがあるのにStateが登録されていない⇒エラー
                tk.line_send("  ID矛盾発生⇒強制解消処理", self.position['id'], self.position['state'])
                self.reset()

            #  状況に応じてCRCDO系の処理を実施する
            if "W" in self.name:  # ウォッチ用のポジションは時間で消去。ただしCRCDOはしない
                if self.position['time_past'] > 1200 and self.position['state'] == "OPEN":
                    print("   PositionW限定時間解消@")
                    # tk.line_send("   時間解消W@", self.name, self.position['time_past'])
                    self.close_position()
            else:  #通常のオーダーの場合
                # 時間によるLC底上げを行う
                # self.lc_change_by_time()
                # LCの底上げを行う
                self.lc_change()
                # トレールの実施を行う
                self.trail()
                # 時間による解消を行う（オーダー状態）
                if self.order['time_past'] > self.order_timeout * 60 and self.order['state'] == "PENDING":
                    print("   時間解消@")
                    # tk.line_send("   時間解消@", self.name, self.order['time_past'], self.order_timeout)
                    self.close_order()

        else:
            # LifeがFalseの場合、Update処理を行わない
            pass
            return 0

    def lc_change(self):  # ポジションのLC底上げを実施 (基本的にはUpdateで平行してする形が多いかと）
        p = self.position  # ポジションの情報
        guarantee = self.crcdo_guarantee

        if self.crcdo_history is False and self.position['state'] == "OPEN":  # ポジションのCRCDO歴がない場合
            if p['time_past'] - self.crcdo_sec_counter > 60:  # N秒以上経過している場合、ロスカ引き上げ
                # （１）ある程度プラスになった場合、LCを引き上げて最低限のプラスを確保する（微マイナスでとどめる場合もあり）
                if p['pips'] > self.crcdo_border != 0:  # crcdo_borderが０ではない（トレール有効）、borderより超えている場合
                    self.crcdo_lc_price = round(
                        p['price'] - guarantee if self.plan['ask_bid'] < 0 else p['price'] + guarantee, 3)
                    data = {
                        "stopLoss": {"price": str(self.crcdo_lc_price), "timeInForce": "GTC"},
                        # "takeProfit": {"price": str(tp_price), "timeInForce": "GTC"},
                        # "trailingStopLoss": {"distance": 0.05, "timeInForce": "GTC"},
                    }
                    res = self.oa.TradeCRCDO_exe(p['id'], data)  # ポジションを変更する
                    # CDCRO結果の判定
                    if res['error'] == -1:
                        tk.line_send("CRCDミス", self.api_try_num, res['past_sec'])
                    else:
                        self.crcdo_sec_counter = p['time_past']  # 変更時の経過時点を記録しておく
                        self.crcdo_history = True
                        tk.line_send("　(LC底上げ)", self.name, self.order['lc_price'], "⇒", self.crcdo_lc_price,
                                     "Border:", self.crcdo_border, "保証", self.crcdo_guarantee)
                # （２）深いマイナスから復帰した場合
                if abs(self.pips_lose_max) > 0.05 and self.position['pips'] > 0.03:
                    lc = 0.01
                    self.crcdo_lc_price = round(p['price'] - lc if self.plan['ask_bid'] < 0 else p['price'] + lc, 3)
                    data = {
                        "stopLoss": {"price": str(self.crcdo_lc_price), "timeInForce": "GTC"},
                    }
                    res = self.oa.TradeCRCDO_exe(p['id'], data)  # ポジションを変更する
                    # CDCRO結果の判定
                    if res['error'] == -1:
                        tk.line_send("CRCDミス", self.api_try_num, res['past_sec'])
                    else:
                        self.crcdo_sec_counter = p['time_past']  # 変更時の経過時点を記録しておく
                        self.crcdo_history = True
                        tk.line_send("　(LC底上げ★)", self.name, self.order['lc_price'], "⇒", self.crcdo_lc_price,
                                     "Border:", self.crcdo_border, "保証", self.crcdo_guarantee)

    def trail(self):  # ポジションのトレールを設定（LCの底上げとは別に考える）
        if self.crcdo_self_trail_exe and self.crcdo_history:  # 一回すでにCDCRO実施済みが前提。
            p = self.position  # ポジションの情報
            o = self.order  # オーダーの情報
            if p['time_past'] - self.crcdo_sec_counter > 10:  # 前回のCRCDOよりN秒以上空いていれば、CRCDOを再検討する
                if p['pips'] > 0.001:  # 勝ちpipsがＮ以上の場合、利確底上げ（トレール）を行う
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
                        res = self.oa.TradeCRCDO_exe(p['id'], data)  # ポジションを変更する
                        # before_lc_price = self.crcdo_lc_price  # Line送信用に取っておく
                        self.crcdo_lc_price = temp_lc_price  # ロスカ変更後のLCラインを保存
                        # CDCRO結果の判定
                        if res['error'] == -1:
                            tk.line_send("CRCDミス", self.api_try_num, res['past_sec'])
                        else:
                            self.crcdo_set = True  # main本体で、ポジションを取る関数で解除する
                            self.crcdo_sec_counter = p['time_past']  # 変更時の経過時点を記録しておく
                            print("[TR]" + self.name + str(self.crcdo_lc_price))
                            # tk.line_send("　(TR)", self.name)
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

    def output_res(self):
        """
        情報をアウトプットする
        planなし⇒何もせず終了
        planあり以上の場合、CSVに吐き出していく
        :return:
        """
        can_do = 1  # エラー対策。スマホからキャンセルできる用
        if can_do == 1:
            return 0

        # アウトプット用のファイルのパスを準備する
        log_csv_path = tk.folder_path + 'order_log.csv'
        # アウトプット用のデータを生成
        # print("■　表示")
        # self.print_info()
        # ■planDate(基本） 入ってない場合が存在
        if "time" in self.plan:  # planが生成されていれば進む（timeがあれば、プラン格納済と判断する）
            pass
        else:  # planが生成されていなければ、返却する
            return 0

        # ■orderが発行されてない場合もキャンセル(unitsが入っているかで判断）
        if "units" in self.order:
            pass
        else:
            return 0

        # ■辞書形式の場合、名前が同じだとエラーになるので、やむ負えず入れ替える。。
        output = {}
        output['order_id'] = self.order['id']
        output['order_time'] = self.order['time']
        output['order_units'] = self.order['units']
        output['order_state'] = self.order['state']
        output['order_time_past'] = self.order['time_past']
        # ↑ 引数は元データ(文字列時刻)。オーダーを解除しても継続してカウントする秒数
        output['position_id'] = self.position['id']
        output['position_type'] = self.position['type']
        output['position_initial_units'] = self.position['initial_units']
        output['position_current_units'] = self.position['current_units']
        output['position_time'] = self.position['time']
        output['position_time_past'] = self.position['time_past']
        output['position_price'] = self.position['price']
        output['position_state'] = self.position['state']
        output['position_realize_pl'] = self.position['realize_pl']
        output['position_pips'] = self.position['pips']
        output['position_close_time'] = self.position['close_time']
        output['position_close_price'] = self.position['close_price']

        # OrderとPosition情報等を結合する（OrderとPosition情報はUpdatede取得する）
        # output_data_dic = dict(**self.plan, **self.order, **self.position)  # 3つの辞書を合体する
        output_data_dic = dict(**self.plan, **output)  # 3つの辞書を合体する
        print(output_data_dic)
        output_data_df = pd.DataFrame.from_dict(output_data_dic, orient='index').T  # DFに変換する

        try:
            # 既存のファイルがある場合、読み込み⇒追記⇒上書き
            output_data_df.to_csv(log_csv_path, index=False, encoding="cp932", mode='a', header=False)  # 直近保存用
            print(" ファイルに結果出力")  # 恐ら？く初回に発生
        except Exception as e:
            print(" ファイル無しエラー⇒作成の実(初回に発生)")  # 恐ら？く初回に発生
            # output_data_df.to_csv(log_csv_path, index=False, encoding="cp932")  # 直近保存用 cp932


def error_end(info):
    print("  ★■★APIエラー発生")
    # print(" ")
    # sys.exit()  # 強制終了


def all_update_information(classes):
    """
    全ての情報を更新する
    :return:
    """
    for item in classes:
        if item.life:
            # print("個別", item.life)
            item.update_information()


def reset_all_position(classes):
    """
    全てのオーダー、ポジションをリセットして、更新する
    :return:
    """
    oa = classes[0].oa  # とりあえずクラスの一つから。オアンダのクラスを取っておく
    oa.OrderCancel_All_exe()  # 露払い(classesに依存せず、オアンダクラスで全部を消す）
    oa.TradeAllClose_exe()  # 露払い(classesに依存せず、オアンダクラスで全部を消す）
    all_update_information(classes)  # 関数呼び出し（アップデート）


def life_check(classes):
    """
    オーダーが生きているかを確認する
    :return:
    """
    main_c = classes[0]
    second_c = classes[1]
    third_c = classes[2]
    fourth_c = classes[3]
    watch1_c = classes[4]
    watch2_c = classes[5]
    # print(main_c.life, second_c.life, third_c.life, fourth_c.life, watch1_c.life, watch2_c.life)
    if main_c.life or second_c.life or third_c.life or fourth_c.life or watch1_c.life or watch2_c.life:
        ans = True
    else:
        ans = False
    # print(main_c.life, second_c.life, third_c.life, fourth_c.life)
    # print(ans)
    return ans

