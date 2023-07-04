import datetime  # 日付関係
import json
import pytz
import numpy as np
import oandapyV20
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.transactions as trans
import pandas as pd
from numpy import linalg as LA
from oandapyV20 import API
from oandapyV20.endpoints.orders import OrderCreate, OrderDetails, OrdersPending, OrderCancel
from oandapyV20.endpoints.positions import OpenPositions, PositionDetails, PositionClose
from oandapyV20.endpoints.pricing import PricingInfo
from oandapyV20.endpoints.trades import TradeCRCDO, TradeDetails, TradeClose, OpenTrades
import oandapyV20.endpoints.transactions as trans


class Oanda:
    # ■クラス内の主な関数
    # (1)現在価格を取得する　NowPrice_exe
    # (2)キャンドルデータを取得(5000行以内)　InstrumentsCandles_exe
    # (3)キャンドルデータを取得(5000行以上 / 現在から)　InstrumentsCandles_multi_support_exe
    # (4)キャンドルデータを取得(サポート専用。通常利用無し）
    # (5)オーダーの発行を実施　OrderCreate_dic_exe
    # (6)指定のオーダーのキャンセル　OrderCancel_exe
    # (7)オーダーを全てキャンセル　OrderCancel_All_exe
    # (8)指定のオーダーの内容詳細の取得　OrderDetails_exe
    # (9)指定のオーダーのステータス（オーダーとトレードの詳細）を取得　OrderDetailsState_exe
    # (10)オーダーの一覧（全て）を取得　OrdersPending_exe
    # (11)オーダーの一覧（新規トレード待ちのみ）を取得　OrdersWaitPending_exe
    # (12)トレードの一覧を取得　OpenTrades_exe
    # (13)指定のトレードの詳細を取得　TradeDetails_exe
    # (14)指定のトレードの変更　TradeCRCDO_exe
    # (15)指定のトレードの決済　TradeClose_exe
    # (16)トレードを全て決済　TradeAllClose_exe
    # (17)ポジションの一覧を取得　OpenPositions_exe [注]ポジションはトレードを通貨でひとまとめにしたもの。あんま使わん。
    # (18)指定のポジションの詳細　PositionDetails_exe
    # (19)指定のポジションの決済　PositionClose_exe
    # (20)口座残高の取得　GetBalance_exe
    # (21)トランザクション(取引履歴)の取得　GetActPrice_exe
    # (22)オーダーブックを取得する　OrderBook_exe
    #
    # ■サポート関数（クラス外。コード的には約700行目以降）
    # キャンドルデータに情報を付与する関数 (時系列降順のデータフレームに追加。おもに(2)~(4)で活用）
    #  add_basic_data：基本的情報列を付与（これに関係する関数l_func等も存在）
    #  add_macd：Macd情報列を付与
    #  add_ema_data：指数移動平均線の列を付与
    #  add_bb_data：ボリンジャーバンドの列を付与
    # その他、
    #  iso_to_jstdt_single / iso_to_jstdt：ISO時刻規格をJST時刻に変換（DateFrame用、個別用）
    #  str_to_time：文字列時刻（2023/5/24  21:55:00）をDateTimeに変換（大小比較や加減算が可能になる）
    #  cal_past_time_single：経過時間の算出
    #  等の関数有

    def __init__(self, accountID, access_token, env):
        self.accountID = accountID  # インスタンス生成時に、引数で受け取る
        self.access_token = access_token  # インスタンス生成時に、引数で受け取る
        self.environment = env  # インスタンス生成時に、引数で受け取る
        self.api = API(access_token=access_token, environment=self.environment)  # API基盤の準備
        self.print_words = ""  # 表示用。。
        self.print_words_bef = ""  # 表示用。。

    def print_i(self, *msg):
        # 関数は可変複数のコンマ区切りの引数を受け付ける
        # temp = ""
        # 複数の引数を一つにする（数字が含まれる場合があるため、STRで文字化しておく）
        for item in msg:
            self.print_words = self.print_words + " " + str(item)
        self.print_words = self.print_words + "\n"  # 改行する

    def print_view(self):
        if self.print_words != self.print_words_bef:
            print(self.print_words)
            self.print_words_bef = self.print_words
            self.print_words = ""
        else:
            self.print_words = ""

    ############################################################
    # # Oanda操作系API 以下本チャン
    ############################################################
    # (1)現在価格を取得する
    def NowPrice_exe(self, instrument):
        """
        呼び出し:oa.NowPrice_exe("USD_JPY")
        返却値:Bid価格、Ask価格、Mid価格、スプレッド、左記４つを辞書形式で返却。
        """
        try:
            params = {"instruments": instrument}
            ep = PricingInfo(accountID=self.accountID, params=params)
            res_json = json.dumps(self.api.request(ep), indent=2)
            res_json = json.loads(res_json)  # 何故かこれだけevalが使えないのでloadsで文字列⇒jsonを実施
            res_dic = {
                'bid': res_json['prices'][0]['bids'][0]['price'],
                'ask': res_json['prices'][0]['asks'][0]['price'],
                'mid': round((float(res_json['prices'][0]['asks'][0]['price']) +
                              float(res_json['prices'][0]['bids'][0]['price'])) / 2, 3),
                'spread': round(float(res_json['prices'][0]['asks'][0]['price']) -
                                float(res_json['prices'][0]['bids'][0]['price']), 3),
            }
            return res_dic

        except Exception as e:
            print("API_Error（価格情報取得)", datetime.datetime.now().replace(microsecond=0))
            return {"error": e}

    # (2)キャンドルデータを取得(5000行以内/指定複雑)
    def InstrumentsCandles_exe(self, instrument, params):
        """
        過去情報（ローソク）の取得 （これが基本的にAPIを叩く関数）
        呼び出し方:oa.InstrumentsCandles_exe("USD_JPY",{"granularity": "M15","count": 30})　Countは最大5000。
        返却値:Dataframe[time,open.close,high,low,time_jp]の4列
        :param instrument:"USD_JPY"
        :param params:引数はそのままAPIに渡される。辞書形式となる。
            granularity:足幅。M1,M5,M15等。最小はS5（五秒足）
            count: 何行とるか。以下のtoを指定しない場合、直近からcount行を取得する
            price: 指定なし可。指定なしの場合AskとBidの中央価格（Mid）を取得。"A"でAsk価格、"B"でBid価格を取得
            to:2023-01-02T10:30:00.000000000Z の形式(ISOのEuro時間 JST-9)で指定。この時間"まで"のcount行のデータを取得する。
            from:2023-01-02T10:30:00.000000000Z の形式(ISOのEuro時間)で指定。この時間"から"のcount行のデータを取得する。
        :return:ここではmid列が辞書形式のままのデータフレーム
        <参考>
        ①指定した日本時刻をEuro時間に変更
        euro_time_datetime = datetime.datetime(2021, 4, 1, 20, 22, 33) - datetime.timedelta(hours=9)
        ②DateTime⇒ISOへの変換は以下のように実施
        euro_time_datetime_iso = str(euro_time_datetime.isoformat()) + ".000000000Z"  # ISOで文字型。.0z付き）
        ③Json例
        param = {"granularity": "M5", "count": 10, "to": euro_time_datetime_iso}
        oa.InstrumentsCandles_exe("USD_JPY", param)
        """
        ep = instruments.InstrumentsCandles(instrument=instrument, params=params)
        res_json = self.api.request(ep)  # 結果をjsonで取得
        data_df = pd.DataFrame(res_json['candles'])  # Jsonの一部(candles)をDataframeに変換
        data_df['time_jp'] = data_df.apply(lambda x: iso_to_jstdt(x, 'time'), axis=1)  # 日本時刻の表示
        data_df = add_basic_data(data_df)  # 【関数/必須】基本項目を追加する
        # 返却
        return data_df

    # (3)キャンドルデータを取得(5000行以上/現在から/指定簡単（現在USD固定）)
    def InstrumentsCandles_multi_exe(self, pair, params, roop):
        """
        呼び出し方：oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 30}, 1)
        過去情報をまとめて持ってくる【基本的にはこれを呼び出して過去の情報を取得する。InstrumentsCandles_exeとセット利用】
        なお、基本的にはMidの価格を取得する。AskやBidがほしい場合、
         oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 50, "price": "B" }
         のように、priceで指定する（指定なし＝mid B＝bid A=ask ただし、221030日時点、Mid前提のクラスの為注意）
        返却値:Dataframe[time,open.close,high,low,time_jp]　＋　add_information関数達で情報追加
        :param pair: "USD_JPY" のような形式
        :param params:{"granularity": 'M5', "count": 5000}のように、足単位と何行取得するか(Max5000)。
                        デフォルトではmidlle価格（askとbidの中間）を取得。Ask/Bidを取得する場合、"price":"B"or"A"を追加。
        :param roop: 上記情報が何セット欲しいか(5000行以上欲しい場合に有効。5000以下は、この数は１の方が当然動きが早い）
        :return:
        """
        candles = None  # dataframeの準備
        for i in range(roop):
            df = self.InstrumentsCandles_multi_support_exe(pair, params)  # 【関数】データ取得＋基本５項目のDFに変換（dataframeが返り値）
            params["to"] = df["time"].iloc[0]  # ループ用（次回情報取得の期限を決める）
            candles = pd.concat([df, candles])  # 結果用DataFrameに蓄積（時間はテレコ状態）
        # 情報を成型する（取得した情報をtime_jpで並び替える等）
        candles.sort_values('time_jp', inplace=True)  # 時間順に並び替え
        temp_df = candles.reset_index()  # インデックスをリセットし、ML用のデータフレームへ
        temp_df.drop(['index'], axis=1, inplace=True)  # 不要項目の削除
        # 解析用の列を追加する（不要列の削除も含む）
        data_df = add_basic_data(temp_df)  # 【関数/必須】基本項目を追加する
        data_df = add_ema_data(data_df)
        data_df = add_bb_data(data_df)
        # data_df = self.add_peak(data_df)

        # 返却
        return data_df

    # (4)キャンドルデータを取得(サポート専用。通常利用無し）
    def InstrumentsCandles_multi_support_exe(self, instrument, params):
        """
        過去情報（ローソク）の取得 （これが基本的にAPIを叩く関数）
        InstrumentsCandles_multi_exeから呼び出される専用
        """
        ep = instruments.InstrumentsCandles(instrument=instrument, params=params)
        res_json = self.api.request(ep)  # 結果をjsonで取得
        data_df = pd.DataFrame(res_json['candles'])  # Jsonの一部(candles)をDataframeに変換
        data_df['time_jp'] = data_df.apply(lambda x: iso_to_jstdt(x, 'time'), axis=1)  # 日本時刻の表示
        # 返却
        return data_df

    # (5)オーダーの発行を実施
    def OrderCreate_dic_exe(self, info):
        """
        オーダーを発行する。以下の形式でInfo（辞書形式）を受け付ける。
        :param info{
            units: 購入するユニット数。大体1万とか。
            ask_bid: 1の場合買い(Ask)、-1の場合売り(Bid)
            price: 130.150のような小数点三桁で指定。（メモ：APIで渡す際は小数点３桁のStr型である必要がある。本関数内で自動変換）
                    成り行き注文であっても、LCやTPを設定する上では必要
            tp_range: 利確の幅を、0.01（1pips)単位で指定。0.06　のように指定する。指定しない場合０を渡す。負の値は正の値に変換
            lc_range: ロスカの幅を、0.01(1pips)単位で指定。 0.06　のように指定する（負号を付ける必要はない）。指定しない場合０。　負の値は正の値に変換
            type: 下記参照
            tr_range: トレール幅を指定。0.01単位で指定。OANDAの仕様上0.05以上必須。指定しない場合は０を渡す
            remark: 今は使っていないが、引数としては残してある。何かしら文字列をテキトーに渡す。
        :return: 上記の情報をまとめてDic形式で返却。オーダーミス発生(オーダー入らず)した場合は、辞書内cancelがTrueとなる。
        ■オーダー種類について
          STOP:指値。順張り（現価格より高い値段で買い、現価格より低い値段で売りの指値）、また、ロスカット
          LIMIT:指値。逆張り（現価格より低い値段で買い、現価格より高い値段で売りの指値）、また、利確
          MARKET:成り行き。この場合、priceは設定しても無視される（ただし引数としてはテキトーな数字を入れる必要あり）。
        """
        # try:
            # 念のため、初期値を入れておく。

        # 初期値を入れておく
        tp_range = 0
        lc_range = 0

        data = {  # ロスカ、利確ありのオーダー
            "order": {
                "instrument": "USD_JPY",
                "units": 10,
                "type": "",  # "STOP(逆指)" or "LIMIT"
                "positionFill": "DEFAULT",
                "price": "999",  # 指値の時のみ、後で上書きされる。成り行きの時は影響しない為、初期値でテキトーな値を入れておく。
            }
        }
        data['order']['units'] = str(info['units'] * info['ask_bid'])  # 必須　units数 askはマイナス、bidはプラス値
        data['order']['type'] = info['type']  # 必須
        if info['type'] != "MARKET":
            # 成り行き注文以外
            data['order']['price'] = str(round(info['price'], 3))  # 指値の場合は必須
        else:
            # 成り行き注文時は、現在価格を取得する⇒注文には不要だが、LCやTPを計算するうえで必要。(ミドル値）
            info['price'] = self.NowPrice_exe("USD_JPY")['mid']
            print("現在価格", info['price'])

        if info['tp_range'] != 0:
            # 利確設定ありの場合
            tp_range = abs(info['tp_range'])
            data['order']['takeProfitOnFill'] = {}
            data['order']['takeProfitOnFill']['price'] = str(round(info['price'] +
                                                                   (tp_range * info['ask_bid']), 3))  # 利確
            data['order']['takeProfitOnFill']['timeInForce'] = "GTC"
        if info['lc_range'] != 0:
            # ロスカ設定ありの場合
            lc_range = abs(info['lc_range'])
            data['order']['stopLossOnFill'] = {}
            data['order']['stopLossOnFill']['price'] = str(round(info['price'] -
                                                                 (lc_range * info['ask_bid']), 3))  # ロスカット
            data['order']['stopLossOnFill']['timeInForce'] = "GTC"
        if info['tr_range'] != 0:
            # トレールストップロス設定ありの場合
            data['order']['trailingStopLossOnFill'] = {}
            data['order']['trailingStopLossOnFill']['distance'] = str(round(info['tr_range'], 3))  # ロスカット
            data['order']['trailingStopLossOnFill']['timeInForce'] = "GTC"

        print(data['order'])

        # 実行
        ep = OrderCreate(accountID=self.accountID, data=data)  #
        res_json = eval(json.dumps(self.api.request(ep), indent=2))
        if 'orderCancelTransaction' in res_json:
            print("   ■■■CANCELあり")
            print(res_json)
            canceled = True
            order_id = 0
            order_time = 0
        else:
            # 正確にオーダーが入ったためオーダーIDを取得
            canceled = False
            order_id = res_json['orderCreateTransaction']['id']
            order_time = res_json['orderCreateTransaction']['time']

        # オーダー情報履歴をまとめておく
        order_info = {"price": str(round(info['price'], 3)),
                      "unit": str(info['units'] * info['ask_bid']),  # units数。基本10000 askはマイナス、bidはプラス値
                      "tp_price": str(round(info['price'] + (tp_range * info['ask_bid']), 3)),
                      "lc_price": str(round(info['price'] - (lc_range * info['ask_bid']), 3)),
                      "tp_range_base": round(info['tp_range'], 3),
                      "lc_range_base": round(info['lc_range'], 3),
                      "tp_range": tp_range,
                      "lc_range": lc_range,
                      "type": info['type'],
                      "cancel": canceled,
                      "order_id": order_id,
                      "order_time": order_time
                      }
        return order_info

        # except Exception as e:
        #     print(e)
        #     print("★★APIエラー★★orderCreate")

    # (6)オーダーのキャンセル
    def OrderCancel_exe(self, order_id):
        """
        注文（単品）キャンセルする。 a.OrderCancel_exe(order_id,"remark")
        ＜参考＞ロスカ注文やTP注文、通常の指値等、一つ一つにIDがある。ロスカIDのみのキャンセルが可能。
        :param order_id: キャンセルしたいオーダーのID（ポジションではなくオーダー）
        :return:基本的にはJsonで返却
        """
        detail_json = self.OrderDetails_exe(order_id)  # 存在を確認（無駄なAPI発行を防ぐため）
        if "error" in detail_json:
            print("　★★オーダー存在確認不可(not cancel)★★", order_id)
            return {"error": "No"}
        else:
            if detail_json['order']['state'] == "PENDING":
                try:
                    ep = OrderCancel(accountID=self.accountID, orderID=order_id)
                    res_json = eval(json.dumps(self.api.request(ep), indent=2))
                    # res_df = self.func_make_dic(res_json)  # DataFrameで返却すると、扱いにくいのでコメントアウトした
                    return res_json
                except Exception as e:
                    print("　★★APIエラー★★ orderCancel", order_id)
                    print(e)
                    return {"error": e}
            else:
                print("　★★Cancel不可オーダー（既にCancelや約定済み）", order_id)
                return {"error": "No"}

    # (7)オーダーを全てキャンセル
    def OrderCancel_All_exe(self):
        """
        現在発行している、「新規にポジションを取るための注文」を全てキャンセルする。
        すでに所持しているポジションへのロスカ、利確、トレールの注文はキャンセルされない。
        (各ポジションのロスカや利確注文は削除しない（TPとLCを指値時に設定した場合、ポジションと同時にTP/LCオーダーが入る。）
        APIで「新規ポジションを取るための注文」はtypeがLimitかStopとなっており、それで上記を判定している）
        :return:
        """
        open_df = self.OrdersPending_exe()
        close_df = None
        if len(open_df) == 0:
            print("     @オーダーキャンセル(対象無し)")
            return None
        else:
            print("     cancel order", len(open_df))
            print(open_df)
            for index, row in open_df.iterrows():
                # たまに変わるため注意。23年１月現在、利確ロスカ注文はtype = STOP_LOSS TAKE_PROFIT
                # 新規ポジション取得は、順張り逆張り問わず、MARKET_IF_TOUCHED
                if row['type'] == 'MARKET_IF_TOUCHED' or row['type'] == 'STOP' or row['type'] == 'LIMIT':
                    # tpyeがMARKET_IF_TOUCHEDの場合（いわゆるポジションを取るための注文）
                    self.OrderCancel_exe(row["id"])  # 【関数】単品をクローズする
                    # close_df = pd.concat([close_df , res_df])#新決済情報を縦結合
                else:  # LIMIT注文、STOP注文の場合（ここでいうLIMITは利確、STOPはロスカ トレールもこっち
                    pass

            return close_df

    # (8)オーダーの内容詳細の確認
    def OrderDetails_exe(self, order_id):
        """
        単品の注文内容の詳細を確認する
        :param order_id: 注文のID
        :return: あまり利用しないので、Jsonのままで返却
        """
        start_time = datetime.datetime.now().replace(microsecond=0)  # エラー頻発の為、ログ

        try:
            ep = OrderDetails(accountID=self.accountID, orderID=order_id)
            res_json = eval(json.dumps(self.api.request(ep), indent=2))
            # print("   (Detail実行時間)", (datetime.datetime.now().replace(microsecond=0)-start_time).seconds)
            return res_json
        except Exception as e:
            print("★★APIエラー（Detail）", order_id, (datetime.datetime.now().replace(microsecond=0)-start_time).seconds)
            return {"error": e, "id": order_id}

    # (9)指定のオーダーのステータス（オーダーとトレードの詳細）を取得
    def OrderDetailsState_exe(self, order_id):
        """
        単品の注文番号を渡すと、ポジションまで（ある場合）の情報を返却する
        :param order_id: 注文のID
        :return: あまり利用しないので、Jsonのままで返却
        """
        res_json = self.OrderDetails_exe(order_id)

        if "error" in res_json:
            # わかりやすいJsonを作っておく
            print("   ★OrderDatailState- orderDetail ミス", order_id)
            return {"error": -1, "part": "OrderDetail"}  # エラーの返却
        else:
            order_state = res_json['order']['state']  # オーダーのステータスを確認

            if "price" in res_json['order']:  # MARKET注文の場合、orderPriceが表示されない
                order_price = res_json['order']['price']
            else:
                order_price = 0

            # 返却用の項目追加を実施
            position_id = 0
            pips = 0
            position_time = 0
            position_close_time = 0
            position_price = 0
            position_state = 0
            position_realize_pl = 0
            position_close_price = 0
            if order_state == 'PENDING' or order_state == 'CANCELLED':  # 注文中
                pass  # 初期値のまま（全て０）でOK
            else:  # order_state == 'FILLED':  # オーダー約定済み⇒オーダーIDを取得して情報を取得
                # ポジションの詳細を取得
                if "tradeClosedIDs" in res_json['order']:  # 既にクローズまで行っている場合、これがPositionID
                    print("  Closeあり　今までのAPIエラーケース")
                    position_id = res_json['order']['tradeClosedIDs'][0]  # PositionIDを取得
                else:
                    position_id = res_json['order']['fillingTransactionID']  # PositionIDを取得
                position_js = self.TradeDetails_exe(position_id)  # PositionIDから詳細を取得
                if "error" in position_js:
                    # わかりやすいJsonを作っておく
                    print("   ★OrderDatailState- positionDetail ミス", position_id,"(", order_id, ")")
                    return {"error": -1, "part": "OrderDetail"}  # エラーの返却
                else:
                    if position_js['trade']['state'] == 'CLOSED':  # すでに閉じたポジションの場合
                        pips = round(float(position_js['trade']['realizedPL']) / abs(
                            float(position_js['trade']['initialUnits'])), 3)
                        position_realize_pl = position_js['trade']['realizedPL']
                        position_time = iso_to_jstdt_single(position_js['trade']['openTime'])  # ポジションした時間がうまる
                        position_close_time = iso_to_jstdt_single(
                            position_js['trade']['closeTime'])  # ポジションがクローズした時間がうまる
                        position_price = position_js['trade']['price']
                        position_state = position_js['trade']['state']
                        position_close_price = position_js['trade']['averageClosePrice']
                    elif position_js['trade']['state'] == 'OPEN':  # 所持中しているポジションの場合
                        pips = round(float(position_js['trade']['unrealizedPL']) / abs(
                            float(position_js['trade']['initialUnits'])), 3)
                        position_realize_pl = position_js['trade']['unrealizedPL']
                        position_time = iso_to_jstdt_single(position_js['trade']['openTime'])  # ポジションした時間がうまる
                        position_close_time = 0
                        position_price = position_js['trade']['price']
                        position_state = position_js['trade']['state']
                        position_close_price = 0
            # わかりやすいJsonを作っておく
            res = {
                "func_complete": 0,  # APIエラーなく完了しているかどうか
                "order_id": order_id,
                "order_time_original": res_json['order']['createTime'],
                "order_time": iso_to_jstdt_single(res_json['order']['createTime']),
                "order_time_past": cal_past_time_single(iso_to_jstdt_single(res_json['order']['createTime'])),
                "order_units": res_json['order']['units'],
                "order_price": order_price,  # Marketでは存在しない
                "order_state": res_json['order']['state'],
                "position_id": position_id,
                "position_time": position_time,
                "position_time_past": cal_past_time_single(position_time) if position_time != 0 else 0,
                "position_price": position_price,
                "position_state": position_state,
                "position_realize_pl": position_realize_pl,
                "position_pips": pips,
                "position_close_time": position_close_time,
                "position_close_price": position_close_price
            }
            return res

    # オーダーの一覧（全て）を取得
    def OrdersPending_exe(self):
        """
        注文中の一覧を取得する。
        APIからの返却情報に加え、オーダーの発行から現在までの経過時間（秒）も追加する。
        :return: データフレーム形式
        """
        ep = OrdersPending(accountID=self.accountID)
        res_json = eval(json.dumps(self.api.request(ep), indent=2))
        res_df = pd.DataFrame(res_json['orders'])  # DFに変換
        # print(res_df)
        if len(res_df) == 0:
            # 注文中がない場合、何もしない
            return res_df
        else:
            # いくつか情報を付与する
            res_df['order_time_jp'] = res_df.apply(lambda x: iso_to_jstdt(x, 'createTime'), axis=1)  # 日本時刻の表示
            res_df['past_time_sec'] = res_df.apply(lambda x: cal_past_time(x), axis=1)  # 経過時刻の算出
            return res_df

    # (11)オーダーの一覧（新規トレード待ちのみ）を取得
    def OrdersWaitPending_exe(self):
        """
        注文の一覧を取得。
        ただし、新規にポジションを取得するための注文(typeがLimitかStopの物)のみ。
        typeがそれ以外の場合、ロスカット注文や利確注文の為、削除しない。
        ＜参考＞「新規のポジションを取得するための注文」は、APIではtypeがLimitかStopとなっている
        :return:
        """
        ep = OrdersPending(accountID=self.accountID)
        res_json = eval(json.dumps(self.api.request(ep), indent=2))
        res_df = pd.DataFrame(res_json['orders'])  # DFに変換
        if len(res_df) == 0:
            # 注文中がない場合、何もしない
            return res_df
        else:
            res_df['order_time_jp'] = res_df.apply(lambda x: iso_to_jstdt(x, 'createTime'), axis=1)  # 日本時刻の表示
            # 注文からの経過時間を秒で算出する
            res_df['past_time_sec'] = res_df.apply(lambda x: cal_past_time(x), axis=1)  # 経過時刻の算出

            del_target = []
            for index, row in res_df.iterrows():
                if row['type'] == 'MARKET_IF_TOUCHED' or row['type'] == 'STOP' or row['type'] == 'LIMIT':
                    # LIMITとSTOPが対象。
                    pass
                else:
                    # typeが利確やロスカ、トレール注文の場合は一覧には乗せない
                    del_target.append(index)  # 消す対象をリスト化
            res_df.drop(index=del_target, inplace=True)  # 不要な行を削除（IMITとSTOPのみが対象）

            return res_df

    # (12)トレードの一覧を取得　OpenTrades_exe
    def OpenTrades_exe(self):
        """
        取引中の全ポジション一覧で取得。
        APIからの返却情報に加え、
        ・日本時間
        ・取得からの経過時間
        ・pips単位での含み損益（API返却値は円の為、ユニット数で商算したもの）
        を列に加える。
        :return: データフレーム形式
        """
        try:
            ep = OpenTrades(accountID=self.accountID)
            res_json = eval(json.dumps(self.api.request(ep), indent=2))
            # print(res_json)
            res_df = pd.DataFrame(res_json["trades"])
            if len(res_df) == 0:
                return res_df
            else:
                res_df['order_time_jp'] = res_df.apply(lambda x: iso_to_jstdt(x, 'openTime'), axis=1)  # 日本時刻の表示
                # 注文からの経過時間を秒で算出する
                res_df['past_time_sec'] = res_df.apply(lambda x: cal_past_time(x), axis=1)  # 経過時刻の算出
                res_df['unrealizedPL_pips'] = round(res_df['unrealizedPL'].astype('float') /
                                                    res_df['currentUnits'].astype('float'), 3)
                return res_df
        except Exception as e:
            print(e)
            print("★★APIエラー★★Open_Trade")

    # (13)指定のトレードの詳細
    def TradeDetails_exe(self, trade_id):
        try:
            ep = TradeDetails(accountID=self.accountID, tradeID=trade_id)
            res_json = eval(json.dumps(self.api.request(ep), indent=2))
            return res_json  # 単品が対象なので、Jsonで返した方がよい（DataFrameで返すと、単品なのに行の指定が必要）
        except Exception as e:
            print("★★APIエラー★★(指定トレードの詳細)")
            return {"error": -1, "part": "TraildDetail"}  # エラーの返却

    # (14)指定のトレードの変更
    def TradeCRCDO_exe(self, trade_id, data):
        """
        :param trade_id:
        :param data:　以下の形式
            data = {
                "takeProfit": {"price": str(round(line, 3)),"timeInForce": "GTC",},
                "stopLoss": {"price": str(round(line, 3)),"timeInForce": "GTC",},
                "trailingStopLoss": {"distance": 0.05, "timeInForce": "GTC"},
            }
        :return:
        """
        # データの価格情報をStrに変更しておく（priceがstrでもfloatで来ても、いいように。。）
        if 'stopLoss' in data:
            data['stopLoss']['price'] = str(round(float(data['stopLoss']['price']), 3))
        if 'takeProfit' in data:
            data['takeProfit']['price'] = str(round(float(data['takeProfit']['price']), 3))
        if 'trailingStopLoss' in data:
            data['trailingStopLoss']['distance'] = str(round(float(data['trailingStopLoss']['distance']), 3))

        try:
            ep = TradeCRCDO(accountID=self.accountID, tradeID=trade_id, data=data)
            res_json = eval(json.dumps(self.api.request(ep), indent=2))
            return res_json
        except Exception as e:
            print("★★APIエラー★★　CRCDO")
            print(e)
            return 0

    # (15)指定のトレードの決済
    def TradeClose_exe(self, trade_id, data):
        """
        :param trade_id: 閉じたい対象のトレードID（数字）
        :param data: data=None　の場合は対象トレードを決済。部分決済したい場合は、色々書く（忘れた）
        :return:
        """
        try:
            # 呼び出し:oa.TradeClose_exe(trade_id , data(基本はNoneで全数決済)))
            ep = TradeClose(accountID=self.accountID, tradeID=trade_id, data=data)
            res_json = eval(json.dumps(self.api.request(ep), indent=2))
            res_df = func_make_dic(res_json)  # 必要項目の抜出
            return res_df
        except Exception as e:
            print("★★APIエラー★★ 指定トレードの決済")
            return 0

    # (16)トレードを全て決済
    def TradeAllClose_exe(self):
        """
        引数無し。現在あるトレードを一括で消去する
        :return:
        """
        open_df = self.OpenTrades_exe()
        if len(open_df) == 0:
            print("     @ポジションキャンセル(対象無し/trade)")
            return None
        else:
            count = 0
            close_df = None
            for index, row in open_df.iterrows():
                res_df = self.TradeClose_exe(row["id"], None)  # 【関数】単品をクローズする
                close_df = pd.concat([close_df, res_df])  # 新決済情報を縦結合
                count = count + 1
            print("   @PositionClear:", count, "個(@all close func)")
            return close_df

    # (17)ポジションの一覧を取得
    def OpenPositions_exe(self):
        try:
            ep = OpenPositions(accountID=self.accountID)
            res_json = eval(json.dumps(self.api.request(ep), indent=2))
            res_df = func_make_dic(res_json)  # 必要項目の抜出
            return res_df
        except Exception as e:
            print("★★APIエラー★★", e)
            return 0

    # (18)指定のポジションの詳細 instrument = "USD_JPY"
    def PositionDetails_exe(self, instrument):
        try:
            ep = PositionDetails(accountID=self.accountID, instrument=instrument)
            res_json = eval(json.dumps(self.api.request(ep), indent=2))
            return res_json
        except Exception as e:
            print("★★APIエラー★★", e)
            return 0

    # (19)指定のポジションの決済
    def PositionClose_exe(self, data):
        try:
            # 昔は引数が(self, instrument, data)　だった。instrumentを削除した
            ep = PositionClose(accountID=self.accountID, instrument="USD_JPY", data=data)
            res_json = eval(json.dumps(self.api.request(ep), indent=2))
            print(res_json)
            return res_json  # oa = Oanda(accountID, access_token)
        except Exception as e:
            print("★★APIエラー★★", e)
            return 0

    # (20)口座残高の取得
    def GetBalance_exe(self):
        client = oandapyV20.API(access_token=self.access_token)
        r = accounts.AccountSummary(self.accountID)
        response = client.request(r)
        res = response["account"]["balance"]
        return res  # oa = Oanda(accountID, access_token)

    # (21)トランザクション(取引履歴)の取得
    def GetActPrice_exe(self, transactionID):
        ep = trans.TransactionDetails(accountID=self.accountID, transactionID=transactionID)
        res_json = eval(json.dumps(self.api.request(ep), indent=2))
        print(res_json)
        if "price" in res_json:
            act_price = res_json['price']
        else:
            act_price = 99999999
        return act_price

    # (22)オーダーブックを取得する
    def OrderBook_exe(self, target_price):
        ep = instruments.InstrumentsOrderBook(instrument="USD_JPY")
        res_json = self.api.request(ep)  # 結果をjsonで取得
        df = pd.DataFrame(res_json["orderBook"]["buckets"])
        # 集計
        price = target_price

        from_price = price - 0.2
        from_price = from_price - (from_price % 0.05)
        from_price3 = '{:.3f}'.format(from_price)
        from_index = df[df['price'] == from_price3].index.values[0]  # 一つのはず

        to_price = price + 0.2
        to_price = to_price - (to_price % 0.05)
        to_price3 = '{:.3f}'.format(to_price)
        to_index = df[df['price'] == to_price3].index.values[0]

        df = df[from_index:to_index]
        df = df.sort_index(ascending=False)
        return df

    # (23) トランザクションデータを取得する（N　×　Row分）
    def get_base_data_multi(self, roop, num):
        """
        最新のデータから、N個さかのぼった分のデータをトランザクションデータを取得する。
        処理としては、まず最新の取引IDを取得し、そこからnum個分のデータを、roop回数取得する。
        numの最大値は、500(OandaのAPIの仕様上限。get_base_dataを利用してAPIを叩く事になる）
        例えば、num=3でroop=5とした場合、直近から３回分の取引データを５回分、ようするに直近１５回分の取引データを取得する。
        :param roop: N
        :param num:
        :return:
        """
        # 返却用DF
        for_ans = None
        # 最も新しいIDを取得する（TOに入れる用）
        ep = trans.TransactionIDRange(accountID=self.accountID, params={"to": 40746, "from": 40746})
        resp = self.api.request(ep)
        latestT = resp['lastTransactionID']

        for i in range(roop):
            params_temp = {
                "to": int(latestT),
                "from": int(latestT) - num + 1
            }
            ep = trans.TransactionIDRange(accountID=self.accountID, params=params_temp)
            resp = self.api.request(ep)
            # params内、toの変更
            latestT = int(latestT) - num

            # transactionの内の配列データを取得する
            transactions = resp['transactions']
            print(len(transactions))

            all_info = []
            for item in transactions:
                print("id=", item["id"])
                # print(item)
                # 考えるのめんどいので、必要項目だけ辞書形式にしてしまう
                dict = {
                    "id": item["id"],
                    "time": item["time"],
                    "type": item["type"],
                    # "reason": item["reason"],
                }
                # たまにreasonがないのが存在する。。41494とか
                if "reason" in item:
                    dict["reason"] = item["reason"]
                else:
                    dict["reason"] = 0
                #
                if "units" in item:
                    dict["units"] = item["units"]
                else:
                    dict["units"] = 0
                # ポジションオーダー時にある項目
                if "takeProfitOnFill" in item:
                    if "price" in item["takeProfitOnFill"]:
                        dict["price_tp"] = item["takeProfitOnFill"]["price"]
                    else:
                        dict["price_tp"] = "N"
                else:
                    dict["price_tp"] = 0

                if "stopLossOnFill" in item:
                    if "price" in item["stopLossOnFill"]:
                        dict["price_lc"] = item["stopLossOnFill"]["price"]
                    else:
                        dict["price_lc"] = "N"
                else:
                    dict["price_lc"] = 0
                # priceを含む場合（オーダーのキャンセル以外はpriceが入る）
                if "price" in item:
                    dict['price'] = item['price']
                else:
                    dict['price'] = 0
                # ポジション解消時にある項目
                if "pl" in item:
                    dict["pl"] = item["pl"]
                else:
                    dict["pl"] = 0

                # 配列に追加する
                all_info.append(dict)

            t_df = pd.DataFrame(all_info)
            t_df['time_jp'] = t_df.apply(lambda x: iso_to_jstdt(x, 'time'), axis=1)  # 日本時刻を追加する

            for_ans = pd.concat([t_df, for_ans])  # 結果用dataframeに蓄積（時間はテレコ状態）

        print("トランザクションデータ取得完了")
        return for_ans

    # 【Roll等を使い、過去足との平均値等を算出】
    # def add_roll_info(self, data_df):
    #     # IBM 当月と前月の差、当月と２か月前の差　直近３カ月比重（これどうしよう）
    #     data_df['body_pass1'] = data_df['body'] - data_df['body'].shift(1)  # 自身と、一つ前足との差分（自身ーひとつ前）
    #     data_df['body_pass2'] = data_df['body'] - data_df['body'].shift(2)  # 自身と、二つ前足との差分（自身ーふたつ前）
    #     data_df['body_pass3'] = data_df['body'] - data_df['body'].shift(3)  # 自身と、二つ前足との差分（自身ーふたつ前）
    #     # data_df['body1'] = data_df['body'].shift(1)  # 自身と、一つ前足との差分（自身ーひとつ前）
    #     # data_df['body2'] = data_df['body'].shift(2)  # 自身と、二つ前足との差分（自身ーふたつ前）
    #     # data_df['body3'] = data_df['body'].shift(3)  # 自身と、二つ前足との差分（自身ーふたつ前）
    #
    #     data_df['body_abspass1'] = data_df['body_abs'] - data_df['body_abs'].shift(1)  # 自身と、一つ前足との差分（自身ーひとつ前）
    #     data_df['body_abspass2'] = data_df['body_abs'] - data_df['body_abs'].shift(2)  # 自身と、二つ前足との差分（自身ーふたつ前）
    #     data_df['body_abspass3'] = data_df['body_abs'] - data_df['body_abs'].shift(3)  # 自身と、二つ前足との差分（自身ーふたつ前）
    #
    #     # data_df['up_rod1'] = data_df['up_rod'].shift(1)  # 自身と、一つ前足との差分（自身ーひとつ前）
    #     # data_df['up_rod2'] = data_df['up_rod'].shift(2)  # 自身と、二つ前足との差分（自身ーふたつ前）
    #     # data_df['up_rod3'] = data_df['up_rod'].shift(3)  # 自身と、二つ前足との差分（自身ーふたつ前）
    #     # data_df['low_rod1'] = data_df['low_rod'].shift(1)  # 自身と、一つ前足との差分（自身ーひとつ前）
    #     # data_df['low_rod2'] = data_df['low_rod'].shift(2)  # 自身と、二つ前足との差分（自身ーふたつ前）
    #     # data_df['low_rod3'] = data_df['low_rod'].shift(3)  # 自身と、二つ前足との差分（自身ーふたつ前）
    #
    #     # 直近３個の平均値を求める
    #     data_df['body_3mean'] = data_df['body'].rolling(3, min_periods=1).mean()
    #
    #     # 当足と３足前のクローズ価格の変化率（傾き）
    #     data_df['tilt_close1'] = data_df['close'] - data_df['close'].shift(1)
    #     data_df['tilt_close2'] = data_df['close'] - data_df['close'].shift(2)  # 自身と、二つ足前のクローズ価格の差分（傾きに近い）
    #     data_df['tilt_close3'] = data_df['close'] - data_df['close'].shift(3)
    #     data_df['tilt_close6'] = data_df['close'] - data_df['close'].shift(6)
    #     data_df['tile_3_6'] = data_df['tilt_close3'] + data_df['tilt_close6']
    #
    #     # 当月のbodyのBB占有率と、１つ前の占有率の差分
    #     data_df['tilt_bb_body_ratio1'] = data_df['bb_body_ratio'] - data_df['bb_body_ratio'].shift(1)
    #     data_df['tilt_bb_body_ratio2'] = data_df['bb_body_ratio'] - data_df['bb_body_ratio'].shift(2)  # 自身と、二つ足前の差分
    #     data_df['bb_body_ratio1'] = data_df['bb_body_ratio'].shift(1)
    #     data_df['bb_body_ratio2'] = data_df['bb_body_ratio'].shift(2)
    #
    #     # 当月のBB内比率の推移bb_over_ratio
    #     data_df['bb_over_ratio_1'] = data_df['bb_over_ratio'] - data_df['bb_over_ratio'].shift(1)  # 一つ前足との差分
    #     data_df['bb_over_ratio_2'] = data_df['bb_over_ratio'] - data_df['bb_over_ratio'].shift(2)  #
    #     data_df['bb_under_ratio_1'] = data_df['bb_under_ratio'] - data_df['bb_under_ratio'].shift(1)
    #     data_df['bb_under_ratio_2'] = data_df['bb_under_ratio'] - data_df['bb_under_ratio'].shift(2)  #
    #
    #     # Volumeについて
    #     data_df['volume_tilt1'] = data_df['volume'] - data_df['volume'].shift(1)  # 自身と、二つ足前のクローズ価格の差分（傾きに近い）
    #     data_df['volume_tilt2'] = data_df['volume'] - data_df['volume'].shift(2)  # 自身と、二つ足前のクローズ価格の差分（傾きに近い）
    #     # data_df['volume_pass2'] = data_df['volume'].shift(1)
    #     # data_df['volume_pass2'] = data_df['volume'].shift(2)
    #
    #     # ema関係について
    #     data_df['cross_pass1'] = data_df['cross'].shift(1)  # 自身と、二つ足前のクローズ価格の差分（傾きに近い）
    #     data_df['cross_pass2'] = data_df['cross'].shift(2)  # 自身と、二つ足前のクローズ価格の差分（傾きに近い）
    #     data_df['cross_pass3'] = data_df['cross'].shift(3)
    #     data_df['ema_gap_pass1'] = data_df['ema_gap'].shift(1)  # 自身と、二つ足前のクローズ価格の差分（傾きに近い）
    #     data_df['ema_gap_pass2'] = data_df['ema_gap'].shift(2)  # 自身と、二つ足前のクローズ価格の差分（傾きに近い）
    #     data_df['ema_gap_pass3'] = data_df['ema_gap'].shift(3)
    #     data_df['ema_gap_tilt3'] = data_df['ema_gap'] - data_df['ema_gap'].shift(3)
    #     return data_df


############################################################
# # 関連する関数
############################################################
# 細々した関数たち
def o_func(x):
    temp = x.mid
    return float(temp['o'])


def c_func(x):
    temp = x.mid
    return float(temp['c'])


def h_func(x):
    temp = x.mid
    return float(temp['h'])


def l_func(x):
    try:
        temp = x.ask
    except:
        try:
            temp = x.bid
        except:
            temp = x.mid
    return float(temp['l'])


def ih_func(x):
    if x.open > x.close:
        return x.open
    else:
        return x.close


def il_func(x):
    if x.open < x.close:
        return x.open
    else:
        return x.close


def for_upper(x):
    if x.body > 0:
        return x.high - x.close
    else:
        return x.high - x.open


def for_lower(x):
    if x.body > 0:
        return x.open - x.low
    else:
        return x.close - x.low


def func_d(t_dic, t_list):
    ans = len(t_list)
    # t1が指定のJsonにあれば
    if t_list[0] in t_dic:
        t_dic = t_dic[t_list[0]]
        # t2が指定のjsonにあれば
        if t_list[1] in t_dic:
            t_dic = t_dic[t_list[1]]
            if ans == 2:
                return t_dic
            else:
                # t3が指定のjsonにあれば
                if t_list[2] in t_dic:
                    t_dic = t_dic[t_list[2]]
                    return t_dic
                else:
                    return 0
        else:
            return 0
    else:  # 最初からなければ
        return 0


# クロス時の価格のみを抽出する
def cal_cross_price(x):
    """
    OandaClass内のadd_ema_data　から呼び出される。ゴールデンやデッドクロス時点の価格を求める関数
    """
    if x.cross != 0:  # cross がある場合
        ans = x.ema_s
    else:
        ans = None
    return ans


# 2直線のなす角度を求める
def cal_angle(x):
    """
    OandaClass内のadd_ema_data　から呼び出される。ゴールデンやデッドクロスの角度を算出する。あんまり使う数字ではない
    """
    sample1 = x.ema_l_tilt
    sample2 = x.ema_s_tilt
    u = np.array([sample1, 1])  # ベクトルの設定
    v = np.array([sample2, 1])
    i = np.inner(u, v)  # 内積
    n = LA.norm(u) * LA.norm(v)  # 長さ算出して掛け算
    c = i / n
    a = np.rad2deg(np.arccos(np.clip(c, -1.0, 1.0)))
    a_res = round(a, 1)  # 小数点以下１桁を表示（小数点２桁を切り上げ）
    if x.ema_l > x.ema_s:  # 角度に正負を持たせたい時
        a_res = a_res * -1
    return a_res


def func_make_dic(res_json):
    res = [{  # []でくくると、dataframeに変換しやすい
        'instrument': func_d(res_json, ["orderCreateTransaction", "instrument"]),
        'order_id': int(func_d(res_json, ["orderCreateTransaction", "id"])),
        'order_time': str(func_d(res_json, ["orderCreateTransaction", "time"])),
        'order_price': func_d(res_json, ["orderCreateTransaction", "price"]),  # 指値の場合のみ？
        'order_units': float(func_d(res_json, ["orderCreateTransaction", "units"])),
        'order_type': func_d(res_json, ["orderCreateTransaction", "type"]),
        'order_reason': func_d(res_json, ["orderCreateTransaction", "reason"]),
        'order_price_sl': float(func_d(res_json, ["orderCreateTransaction", "stopLossOnFill", "price"])),
        'order_price_tp': float(func_d(res_json, ["orderCreateTransaction", "takeProfitOnFill", "price"])),
        'position_instrument': func_d(res_json, ["orderFillTransaction", "instrument"]),
        'position_id': float(func_d(res_json, ["orderFillTransaction", "id"])),
        'position_time': str(func_d(res_json, ["orderFillTransaction", "time"])),
        'position_price': float(func_d(res_json, ["orderFillTransaction", "price"])),
        'position_unit': float(func_d(res_json, ["orderFillTransaction", "units"])),
        'position_type': func_d(res_json, ["orderFillTransaction", "type"]),
        'position_reason': func_d(res_json, ["orderFillTransaction", "reason"]),
        'close_targetorder_id': func_d(res_json, ["orderFillTransaction", "tradeClose", "tradeID"]),
        'cancel_id': func_d(res_json, ["orderCancelTransaction", "id"]),
        'cancel_time': func_d(res_json, ["orderCancelTransaction", "time"]),
        'cancel_targetorder_id': func_d(res_json, ["orderCancelTransaction", "orderID"]),
        'cancel_reason': func_d(res_json, ["orderCancelTransaction", "reason"]),
        'cancel_type': func_d(res_json, ["orderCancelTransaction", "type"]),
        'remark': "remark",  # 過去の遺産
    }]
    res_df = pd.DataFrame(res)  # DFに変換
    res_df['order_time_jp'] = res_df.apply(lambda x: iso_to_jstdt(x, 'order_time'), axis=1)  # 日本時刻の表示
    res_df['position_time_jp'] = res_df.apply(lambda x: iso_to_jstdt(x, 'position_time'), axis=1)  # 日本時刻の表示

    res_df = res_df.drop(['order_time', 'position_time'], axis=1)  # unixtime?を削除
    return res_df


# 【他からもよく使わる関数】
def iso_to_jstdt(x, colname):
    """
    引数colname⇒変換したい時間の有る列を指定。opentimeを列の時間を変換したければ、opentimeと指定する。
    目的：timeを日本時間に変換する（ISO8601→JST変換関数 従来の引数⇒iso_to_jstdt(iso_str)）
    基本的には引数は「価格情報のデータフレーム」。
    返り値は、引数のデータフレームに「time_jp」を付与したデータフレーム
    """
    iso_str = x[colname]  # 関数内の変数変えるのめんどいので、強引に。
    dt = None
    split_timedate = iso_str.rsplit(".", 8)  # ここでマイクロ病以下を切り落とし
    iso_str = split_timedate[0]
    try:
        dt = datetime.datetime.strptime(iso_str, '%Y-%m-%dT%H:%M:%S')
        dt = pytz.utc.localize(dt).astimezone(pytz.timezone("Asia/Tokyo"))
    except ValueError:
        try:
            dt = datetime.datetime.strptime(iso_str, '%Y-%m-%dT%H:%M:%S')
            dt = dt.astimezone(pytz.timezone("Asia/Tokyo"))
        except ValueError:
            # print("@@@@@@日付変換一部できず（空欄等の可能性）")
            pass
    if dt is None:
        df = ""
        return df
    return dt.strftime('%Y/%m/%d %H:%M:%S')  # 文字列に再変換


def iso_to_jstdt_single(iso_str):  # ISO8601→JST変換関数
    dt = None
    split_timedate = iso_str.rsplit(".", 8)  # ここでマイクロ病以下を切り落とし
    iso_str = split_timedate[0]
    try:
        dt = datetime.datetime.strptime(iso_str, '%Y-%m-%dT%H:%M:%S')
        dt = pytz.utc.localize(dt).astimezone(pytz.timezone("Asia/Tokyo"))
    except ValueError:
        try:
            dt = datetime.datetime.strptime(iso_str, '%Y-%m-%dT%H:%M:%S')
            dt = dt.astimezone(pytz.timezone("Asia/Tokyo"))
        except ValueError:
            print("変換できてない")
            pass
    if dt is None:
        df = ""
        return df

    return dt.strftime('%Y/%m/%d %H:%M:%S')  # 文字列に再変換


def str_to_time(str_time):
    """
    時刻（文字列：2023/5/24  21:55:00　形式）をDateTimeに変換する。
    何故かDFないの日付を扱う時、isoformat関数系が使えない。。なぜだろう。
    :param str_time:
    :return:
    """
    time_dt = datetime.datetime(int(str_time[0:4]),
                                int(str_time[5:7]),
                                int(str_time[8:10]),
                                int(str_time[11:13]),
                                int(str_time[14:16]),
                                int(str_time[17:19]))
    return time_dt


def str_to_time_hms(str_time):
    """
    時刻（文字列：2023/5/24  21:55:00　形式）をDateTimeに変換する。
    基本的には表示用。時刻だけにする。
    :param str_time:
    :return:
    """
    time_str = str_time[11:13] + ":" + str_time[14:16] + ":" + str_time[17:19]

    return time_str


# 注文系や確認系で利用する関数
def cal_past_time(x):
    """
    OpenTrades_exe等、いくつかの関数から呼び出され、ポジション取得やオーダー時間からの経過秒数を計算する関数
    order_time_jpと比較した秒数。（order_time_jpという列名でとりあえず固定する）
    order_time_jpはAPIでの返却は存在しないため、この関数を呼ぶ以前で、作成されている必要がある。
    """
    target_col = x['order_time_jp']  # 関数内の変数変えるのめんどいので、強引に。
    time_dt = datetime.datetime(int(target_col[0:4]),
                                int(target_col[5:7]),
                                int(target_col[8:10]),
                                int(target_col[11:13]),
                                int(target_col[14:16]),
                                int(target_col[17:19]))
    time_past = (datetime.datetime.now() - time_dt).seconds  # 差分を秒で求める
    return time_past


# 注文系や確認系で利用する関数(single版）
def cal_past_time_single(x):
    """
    OpenTrades_exe等、いくつかの関数から呼び出され、ポジション取得やオーダー時間からの経過秒数を計算する関数
    引数の形式は、分割できる文字列であること(APIで取得したままの時刻）
    order_time_jpと比較した秒数。（order_time_jpという列名でとりあえず固定する）
    order_time_jpはAPIでの返却は存在しないため、この関数を呼ぶ以前で、作成されている必要がある。
    """
    try:
        target_col = x
        time_dt = datetime.datetime(int(target_col[0:4]),
                                    int(target_col[5:7]),
                                    int(target_col[8:10]),
                                    int(target_col[11:13]),
                                    int(target_col[14:16]),
                                    int(target_col[17:19]))
        # 差分を秒で求める（タイミングで-値になるので、現在時刻-2秒)
        time_past = (datetime.datetime.now() + datetime.timedelta(seconds=2) - time_dt).seconds
        return time_past
    except Exception as e:
        # print("  時刻形式が異なります", e)
        return 0


# 【ローソクへの情報追加】 ★★基本的なデータの追加
def add_basic_data(data_df):
    """
    InstrumentsCandles_exeで取得したデータ（最新時刻が下にある降順データ）に情報を付与する。
    引数はInstrumentsCandles_exeで取得したデータフレーム。返却値は、それに下記列を付与した情報
    """
    data_df = data_df.copy()  # 謎のスライスウォーニング対策
    data_df['open'] = data_df.apply(lambda x: o_func(x), axis=1)  # open価格
    data_df['close'] = data_df.apply(lambda x: c_func(x), axis=1)
    data_df['high'] = data_df.apply(lambda x: h_func(x), axis=1)
    data_df['low'] = data_df.apply(lambda x: l_func(x), axis=1)
    data_df['mid_outer'] = round((data_df['high'] + data_df['low']) / 2, 3)  # 最高値と再低値の長さ
    data_df['inner_high'] = data_df.apply(lambda x: ih_func(x), axis=1)  # ローソク本体で高い方（OpenかClose価格）
    data_df['inner_low'] = data_df.apply(lambda x: il_func(x), axis=1)  # ローソク本体で低い方（OpenかClose価格）
    data_df['body'] = data_df['close'] - data_df['open']  # 胴体の長さ（正負あり）
    data_df['body_abs'] = abs(data_df['close'] - data_df['open'])  # 胴体の長さ
    data_df['moves'] = data_df['high'] - data_df['low']
    data_df['up_rod'] = data_df.apply(lambda x: for_upper(x), axis=1)  # 上髭の長さを取得
    data_df['low_rod'] = data_df.apply(lambda x: for_lower(x), axis=1)  # 下髭の長さを取得
    data_df['highlow'] = data_df['high'] - data_df['low']  # 最高値と再低値の長さ
    data_df['middle_price'] = round(data_df['inner_low'] + (data_df['body_abs'] / 2), 3)  # 最高値と再低値の長さ

    # 不要項目の削除（timeは連続取得時に利用するため、削除+ない）
    # print(data_df.columns.values)
    data_df.drop(['complete'], axis=1, inplace=True)  # 不要項目の削除（volumeってなに）
    data_df.drop(['mid'], axis=1, inplace=True)
    # JIT時刻を非表示にしたいけれど。。
    # data_df.drop(['time'], axis=1, inplace=True)
    # 返却zf
    return data_df


# 【ローソクへの情報追加】 MACD情報を追加する
def add_macd(data_df):
    """
    InstrumentsCandles_exeで取得したデータ（最新時刻が下にある降順データ）に情報を付与する。
    引数はInstrumentsCandles_exeで取得したデータフレーム。返却値は、それに下記列を付与した情報
    データが時間降順(最維が上）だとおかしくなるので、最初に必ず時間の昇順（直近が下＝取得時まま）に直す
    よって、返り値は昇順（最新が下）のデータ
    """
    data_df = data_df.copy()  # 謎のスライスウォーニング対策
    data_df = data_df.sort_index(ascending=True)  # 一回正順に（下が新規に）
    data_df['macd_ema_s'] = data_df['close'].ewm(span=12).mean()  # 初期値３
    data_df['macd_ema_l'] = data_df['close'].ewm(span=26).mean()  # 初期値６
    data_df['macd'] = data_df['macd_ema_s'] - data_df['macd_ema_l']
    data_df['macd_signal'] = data_df['macd'].ewm(span=9).mean()  # 初期値 2
    data_df['macd_gap'] = data_df['macd'] - data_df['macd_signal']
    data_df['macd_bool'] = data_df['macd'] > data_df['macd_signal']
    dead = (data_df['macd_bool'] != data_df['macd_bool'].shift(1)) & (data_df['macd_bool'] == False)  # ==はisで代用不可
    gold = (data_df['macd_bool'] != data_df['macd_bool'].shift(1)) & (data_df['macd_bool'] == True)
    data_df['macd_cross'] = [x + y * -1 for x, y in zip(gold, dead)]
    return data_df


# 【ローソクへの情報追加】 EMA情報を追加する
def add_ema_data(data_df):
    """
    InstrumentsCandles_exeで取得したデータ（最新時刻が下にある降順データ）に情報を付与する。（EMA＝移動平均線加重平均）
    引数はInstrumentsCandles_exeで取得したデータフレーム。返却値は、それに下記列を付与した情報
    """
    data_df = data_df.copy()  # 謎のスライスウォーニング対策
    longspan = 23  # ema算出時の長期線のスパン
    shortspan = 2  # ema算出時の短期線のスパン
    t_num = 3  # 各emaの傾きを求める（n点間の平均傾き）
    # gap = 3  # n足前を正解とするか（機械学習前提値）
    # emaクロス判定
    data_df['ema_l'] = data_df['close'].ewm(span=longspan).mean()
    data_df['ema_s'] = data_df['close'].ewm(span=shortspan).mean()
    data_df['ema_gap'] = data_df['ema_s'] - data_df['ema_l']
    data_df['ema_bool'] = data_df['ema_s'] > data_df['ema_l']
    dead = (data_df['ema_bool'] != data_df['ema_bool'].shift(1)) & (data_df['ema_bool'] == False)  # ==はisで代用不可
    gold = (data_df['ema_bool'] != data_df['ema_bool'].shift(1)) & (data_df['ema_bool'] == True)
    data_df['cross'] = [x + y * -1 for x, y in zip(gold, dead)]
    data_df['cross_price'] = data_df.apply(lambda x: cal_cross_price(x), axis=1)
    data_df['close_tilt'] = (data_df['close'] - data_df['close'].shift(t_num - 1)) / t_num
    data_df['ema_l_tilt'] = (data_df['ema_l'] - data_df['ema_l'].shift(t_num - 1)) / t_num
    data_df['ema_s_tilt'] = (data_df['ema_s'] - data_df['ema_s'].shift(t_num - 1)) / t_num
    data_df['cross_tilt'] = data_df.apply(lambda x: cal_angle(x), axis=1)

    # data_df.drop(['ema_l', 'ema_s', 'ema_bool'], axis=1, inplace=True)
    # data_df.drop(['ema_bool'], axis=1, inplace=True)
    return data_df


# 【ローソクへの情報追加】ボリンジャーバンドを追加する関数
def add_bb_data(data_df):
    """
    InstrumentsCandles_exeで取得したデータ（最新時刻が下にある降順データ）に情報を付与する。（ボリンジャーバンド）
    引数はInstrumentsCandles_exeで取得したデータフレーム。返却値は、それに下記列を付与した情報
    """
    data_df = data_df.copy()  # 謎のスライスウォーニング対策
    # ボリバン基本項目
    data_df['mean'] = data_df['close'].rolling(window=20).mean()  # BB用(直後に削除）
    data_df['std'] = data_df['close'].rolling(window=20).std()  # BB用（直後に削除）
    data_df['bb_upper'] = data_df['mean'] + (data_df['std'] * 2)  # BB用
    data_df['bb_lower'] = data_df['mean'] - (data_df['std'] * 2)  # BB用
    data_df['bb_middle'] = round((data_df['bb_lower'] + data_df['bb_upper']) / 2, 3)
    data_df['bb_range'] = data_df['bb_upper'] - data_df['bb_lower']  # BB幅
    # 不要項目の削除（timeは連続取得時に利用するため、削除しない）
    data_df.drop(['mean', 'std'], axis=1, inplace=True)  # 不要項目の削除

    # ボリバン参考項目
    # data_df['bb_body_ratio'] = round(abs(data_df['body']) / data_df['bb_range'] * 100, 0)  # bb幅とbody幅の割合
    # data_df['bb_over'] = data_df['bb_upper'] - data_df['high']
    # data_df['bb_under'] = data_df['bb_upper'] - data_df['low']
    # data_df['bb_close'] = data_df['bb_upper'] - data_df['close']
    # # bb_upper(0%)-bb_lower(100%)として、最高値と再低値が何%の位置にあるかを計算。マイナス値はupper越、100以上はlower越。
    # data_df['bb_over_ratio'] = round((data_df['bb_upper'] - data_df['high']) / data_df['bb_range'] * 100, 0)
    # data_df['bb_under_ratio'] = round((data_df['bb_upper'] - data_df['low']) / data_df['bb_range'] * 100, 0)
    # data_df['bb_close_ratio'] = round((data_df['bb_upper'] - data_df['close']) / data_df['bb_range'] * 100, 0)
    # # ローソクのbody がBBをどれだけ超えているか
    # data_df['bb_upper_body_over'] = data_df['inner_high'] - data_df["bb_upper"]
    # data_df['bb_lower_body_over'] = data_df['bb_lower'] - data_df["inner_low"]

    # 返却
    return data_df

