import datetime  # 日付関係
import json
import pytz
from scipy.signal import argrelmin, argrelmax  # 極値探索に利用
import math
import time

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
from scipy.signal import argrelmin, argrelmax


class Oanda:
    def __init__(self, accountID, access_token, env):
        self.accountID = accountID
        self.access_token = access_token
        self.environment = env  # デモ口座
        self.api = API(access_token=access_token, environment=self.environment)

    def dummy(self, **params):
        """
        機能なし。Pycharmの注意分（PEP）を消すためだけに用意した物
        """
        return self.environment

    def iso_to_jstdt(self, x, colname):
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

    def o_func(self, x):
        temp = x.mid
        return float(temp['o'])

    def c_func(self, x):
        temp = x.mid
        return float(temp['c'])

    def h_func(self, x):
        temp = x.mid
        return float(temp['h'])

    def l_func(self, x):
        try:
            temp = x.ask
        except:
            try:
                temp = x.bid
            except:
                temp = x.mid
        return float(temp['l'])

    def ih_func(self, x):
        if x.open > x.close:
            return x.open
        else:
            return x.close

    def il_func(self, x):
        if x.open < x.close:
            return x.open
        else:
            return x.close

    def for_upper(self, x):
        if x.body > 0:
            return x.high - x.close
        else:
            return x.high - x.open
        # 【DF作成時の関数】下足の長さを取得

    def for_lower(self, x):
        if x.body > 0:
            return x.open - x.low
        else:
            return x.close - x.low

    def func_d(self, t_dic, t_list):
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

    def func_make_dic(self, res_json, remark):
        res = [{  # []でくくると、dataframeに変換しやすい
            'instrument': self.func_d(res_json, ["orderCreateTransaction", "instrument"]),
            'order_id': int(self.func_d(res_json, ["orderCreateTransaction", "id"])),
            'order_time': str(self.func_d(res_json, ["orderCreateTransaction", "time"])),
            'order_price': self.func_d(res_json, ["orderCreateTransaction", "price"]),  # 指値の場合のみ？
            'order_units': float(self.func_d(res_json, ["orderCreateTransaction", "units"])),
            'order_type': self.func_d(res_json, ["orderCreateTransaction", "type"]),
            'order_reason': self.func_d(res_json, ["orderCreateTransaction", "reason"]),
            'order_price_sl': float(self.func_d(res_json, ["orderCreateTransaction", "stopLossOnFill", "price"])),
            'order_price_tp': float(self.func_d(res_json, ["orderCreateTransaction", "takeProfitOnFill", "price"])),
            'position_instrument': self.func_d(res_json, ["orderFillTransaction", "instrument"]),
            'position_id': float(self.func_d(res_json, ["orderFillTransaction", "id"])),
            'position_time': str(self.func_d(res_json, ["orderFillTransaction", "time"])),
            'position_price': float(self.func_d(res_json, ["orderFillTransaction", "price"])),
            'position_unit': float(self.func_d(res_json, ["orderFillTransaction", "units"])),
            'position_type': self.func_d(res_json, ["orderFillTransaction", "type"]),
            'position_reason': self.func_d(res_json, ["orderFillTransaction", "reason"]),
            'close_targetorder_id': self.func_d(res_json, ["orderFillTransaction", "tradeClose", "tradeID"]),
            'cancel_id': self.func_d(res_json, ["orderCancelTransaction", "id"]),
            'cancel_time': self.func_d(res_json, ["orderCancelTransaction", "time"]),
            'cancel_targetorder_id': self.func_d(res_json, ["orderCancelTransaction", "orderID"]),
            'cancel_reason': self.func_d(res_json, ["orderCancelTransaction", "reason"]),
            'cancel_type': self.func_d(res_json, ["orderCancelTransaction", "type"]),
            'remark': remark,  # 色々なフラグを入れておく場所
        }]
        res_df = pd.DataFrame(res)  # DFに変換
        res_df['order_time_jp'] = res_df.apply(lambda x: self.iso_to_jstdt(x, 'order_time'), axis=1)  # 日本時刻の表示
        res_df['position_time_jp'] = res_df.apply(lambda x: self.iso_to_jstdt(x, 'position_time'), axis=1)  # 日本時刻の表示

        res_df = res_df.drop(['order_time', 'position_time'], axis=1)  # unixtime?を削除
        # self.position_df = pd.concat([self.position_df, res_df])  # 履歴を追記
        # print(self.position_path,self.position_df)
        # self.position_df.to_csv(self.position_path, index=False, encoding="utf-8")
        return res_df

    ############################################################
    # # Oanda操作系API
    ############################################################
    def NowPrice_exe(self, instrument):
        """
        ★現在価格の取得
        呼び出し:oa.NowPrice_exe("USD_JPY")
        返却値:Bid価格、Ask価格、Mid価格、スプレッドを、まとめて辞書形式で返却。
        """
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

    def InstrumentsCandles_exe(self, instrument, params):
        """
        過去情報（ローソク）の取得
        呼び出し:oa.InstrumentsCandles_exe("USD_JPY",{"granularity": "M15","count": 30})　Countは最大5000。
        返却値:Dataframe[time,open.close,high,low,time_jp]の4列
        """
        ep = instruments.InstrumentsCandles(instrument=instrument, params=params)
        res_json = self.api.request(ep)  # 結果をjsonで取得
        data_df = pd.DataFrame(res_json['candles'])  # Jsonの一部(candles)をDataframeに変換
        data_df['time_jp'] = data_df.apply(lambda x: self.iso_to_jstdt(x, 'time'), axis=1)  # 日本時刻の表示
        # 返却
        return data_df

    def InstrumentsCandles_multi_exe(self, pair, params, roop):
        """
        過去情報をまとめて持ってくる【基本的にはこれを呼び出して過去の情報を取得する。InstrumentsCandles_exeとセット利用】
        呼び出し例 :oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 50}, roop(何セットか))
                ↑取れる行数は、50×roop行
        なお、基本的にはMidの価格を取得する。AskやBidがほしい場合、
         oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 50, "price": "B" }
         のように、priceで指定する（指定なし＝mid B＝bid A=ask ただし、221030日時点、Mid前提のクラスの為注意）
        返却値:Dataframe[time,open.close,high,low,time_jp]　＋　add_information関数達で情報追加
        """
        candles = None  # dataframeの準備
        for i in range(roop):
            df = self.InstrumentsCandles_exe(pair, params)  # 【関数】データ取得＋基本５項目のDFに変換（dataframeが返り値）
            params["to"] = df["time"].iloc[0]  # ループ用（次回情報取得の期限を決める）
            # print("    GetCandleData", i)
            candles = pd.concat([df, candles])  # 結果用dataframeに蓄積（時間はテレコ状態）
        # 取得した情報をtime_jpで並び替える
        candles.sort_values('time_jp', inplace=True)  # 時間順に並び替え
        temp_df = candles.reset_index()  # インデックスをリセットし、ML用のデータフレームへ
        temp_df.drop(['index'], axis=1, inplace=True)  # 不要項目の削除（volumeってなに）
        # 解析用の列を追加する（不要な場合はここは削除する。機械学習等で利用する）
        data_df = self.add_basic_data(temp_df)  # 【関数/必須】基本項目を追加する
        data_df = self.add_ema_data(data_df)
        data_df = self.add_bb_data(data_df)

        # 返却
        return data_df

    # 【基本的なデータ取得時の処理のメイン】
    def add_basic_data(self, data_df):
        """
        InstrumentsCandles_exeで取得したデータに基本情報を付与する
        引数はInstrumentsCandles_exeで取得した情報。返却値は、それに下記列を付与した情報
        """
        data_df['open'] = data_df.apply(lambda x: self.o_func(x), axis=1)  # open価格
        data_df['close'] = data_df.apply(lambda x: self.c_func(x), axis=1)
        data_df['high'] = data_df.apply(lambda x: self.h_func(x), axis=1)
        data_df['low'] = data_df.apply(lambda x: self.l_func(x), axis=1)
        data_df['mid_outer'] = round((data_df['high'] + data_df['low']) / 2, 3)  # 最高値と再低値の長さ
        data_df['inner_high'] = data_df.apply(lambda x: self.ih_func(x), axis=1)  # ローソク本体で高い方（OpenかClose価格）
        data_df['inner_low'] = data_df.apply(lambda x: self.il_func(x), axis=1)  # ローソク本体で低い方（OpenかClose価格）
        data_df['body'] = data_df['close'] - data_df['open']  # 胴体の長さ（正負あり）
        data_df['body_abs'] = abs(data_df['close'] - data_df['open'])  # 胴体の長さ
        data_df['up_rod'] = data_df.apply(lambda x: self.for_upper(x), axis=1)  # 上髭の長さを取得
        data_df['low_rod'] = data_df.apply(lambda x: self.for_lower(x), axis=1)  # 下髭の長さを取得
        data_df['highlow'] = data_df['high'] - data_df['low']  # 最高値と再低値の長さ
        data_df['middle_price'] = round(data_df['inner_low'] + (data_df['body_abs'] / 2), 3)  # 最高値と再低値の長さ

        # 不要項目の削除（timeは連続取得時に利用するため、削除+ない）
        # print(data_df.columns.values)
        data_df.drop(['complete'], axis=1, inplace=True)  # 不要項目の削除（volumeってなに）
        data_df.drop(['mid'], axis=1, inplace=True)
        # 返却zf
        return data_df

    # 【ボリバン情報を追加する】
    def add_bb_data(self, data_df):
        """
        InstrumentsCandles_exeで取得したデータに基本情報を付与する（ボリンジャーバンドの情報を付与する）
        引数はInstrumentsCandles_exeで取得した情報。返却値は、それに下記列を付与した情報
        """
        self.dummy()  # ただpycharmの波戦警告を消したいだけ。。。なんの機能もない呼び出し
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

    # 【EMA情報を追加する】
    def add_ema_data(self, data_df):
        """
        InstrumentsCandles_exeで取得したデータに基本情報を付与する（EMA＝移動平均線加重平均）
        引数はInstrumentsCandles_exeで取得した情報。返却値は、それに下記列を付与した情報
        """
        longspan = 23  # ema算出時の長期線のスパン
        shortspan = 2  # ema算出時の短期線のスパン
        t_num = 3  # 各emaの傾きを求める（n点間の平均傾き）
        # gap = 3  # n足前を正解とするか（機械学習前提値）
        # emaクロス判定
        data_df['ema_l'] = data_df['close'].ewm(span=longspan).mean()
        data_df['ema_s'] = data_df['close'].ewm(span=shortspan).mean()
        data_df['ema_gap'] = data_df['ema_s'] - data_df['ema_l']
        data_df['ema_bool'] = data_df['ema_s'] > data_df['ema_l']
        dead = (data_df['ema_bool'] != data_df['ema_bool'].shift(1)) & (data_df['ema_bool'] == False)  # is Falseは不可！
        gold = (data_df['ema_bool'] != data_df['ema_bool'].shift(1)) & (data_df['ema_bool'] == True)
        data_df['cross'] = [x + y * -1 for x, y in zip(gold, dead)]
        data_df['cross_price'] = data_df.apply(lambda x: self.cal_cross_price(x), axis=1)
        data_df['close_tilt'] = (data_df['close'] - data_df['close'].shift(t_num - 1)) / t_num
        data_df['ema_l_tilt'] = (data_df['ema_l'] - data_df['ema_l'].shift(t_num - 1)) / t_num
        data_df['ema_s_tilt'] = (data_df['ema_s'] - data_df['ema_s'].shift(t_num - 1)) / t_num
        data_df['cross_tilt'] = data_df.apply(lambda x: self.cal_angle(x), axis=1)

        # data_df.drop(['ema_l', 'ema_s', 'ema_bool'], axis=1, inplace=True)
        # data_df.drop(['ema_bool'], axis=1, inplace=True)
        return data_df

    # クロス時の価格のみを抽出する
    def cal_cross_price(self, x):
        """
        add_ema_data　から呼び出される。ゴールデンやデッドクロス時点の価格を求める関数
        """
        self.dummy()  # ただpycharmの波戦警告を消したいだけ。。。なんの機能もない呼び出し
        if x.cross != 0:  # cross がある場合
            ans = x.ema_s
        else:
            ans = None
        return ans

    # 2直線のなす角度を求める
    def cal_angle(self, x):
        """
        add_ema_data　から呼び出される。ゴールデンやデッドクロスの角度を算出する。あんまり使う数字ではない
        """
        self.dummy()  # ただpycharmの波戦警告を消したいだけ。。。なんの機能もない呼び出し
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

    # 【MACD情報を追加する】
    def add_macd(self, data_df):
        """
        InstrumentsCandles_exeで取得したデータに基本情報を付与する（EMA＝移動平均線加重平均）
        引数はInstrumentsCandles_exeで取得した情報。返却値は、それに下記列を付与した情報
        """
        self.dummy()  # ただpycharmの波戦警告を消したいだけ。。。なんの機能もない呼び出し
        data_df['macd_ema_s'] = data_df['close'].ewm(span=3).mean()
        data_df['macd_ema_l'] = data_df['close'].ewm(span=6).mean()
        data_df['macd'] = data_df['macd_ema_s'] - data_df['macd_ema_l']
        data_df['macd_signal'] = data_df['macd'].ewm(span=2).mean()
        data_df['macd_gap'] = data_df['macd'] - data_df['macd_signal']
        data_df['macd_bool'] = data_df['macd'] > data_df['macd_signal']
        dead = (data_df['macd_bool'] != data_df['macd_bool'].shift(1)) & (data_df['macd_bool'] is False)  # is は ==も可
        gold = (data_df['macd_bool'] != data_df['macd_bool'].shift(1)) & (data_df['macd_bool'] is True)
        data_df['macd_cross'] = [x + y * -1 for x, y in zip(gold, dead)]
        return data_df

    # 注文系や確認系で利用する関数
    def cal_past_time(self, x):
        """
        OpenTrades_exe等、いくつかの関数から呼び出され、ポジション取得やオーダー時間からの経過秒数を計算する関数
        order_time_jpと比較した秒数。（order_time_jpという列名でとりあえず固定する）
        order_time_jpはAPIでの返却は存在しないため、この関数を呼ぶ以前で、作成されている必要がある。
        """
        self.dummy()  # ただpycharmの波戦警告を消したいだけ。。。なんの機能もない呼び出し
        target_col = x['order_time_jp']  # 関数内の変数変えるのめんどいので、強引に。
        time_dt = datetime.datetime(int(target_col[0:4]),
                                int(target_col[5:7]),
                                int(target_col[8:10]),
                                int(target_col[11:13]),
                                int(target_col[14:16]),
                                int(target_col[17:19]))
        time_past = (datetime.datetime.now() - time_dt).seconds  # 差分を秒で求める
        return time_past

    # (3)-1 オーダーを発行する（指値+LC/TP有）
    def OrderCreate_exe(self, units, ask_bid, price, tp_range, lc_range, type, tr_range, remark):
        """
        オーダーを発行する。
        :param units: 購入するユニット数。大体
        :param ask_bid: 1の場合買い、-1の場合売り
        :param price: 130.150のような小数点三桁で指定。（メモ：APIで渡す際は小数点３桁のStr型である必要がある。本関数内で自動変換）
        :param tp_range: 利確の幅を、0.01（1pips)単位で指定。0.06　のように指定する。指定しない場合０を渡す。
        :param lc_range: ロスカの幅を、0.01(1pips)単位で指定。 0.06　のように指定する（負号を付ける必要はない）。指定しない場合０。
        :param type: 下記参照
        :param tr_range: トレール幅を指定。0.01単位で指定。OANDAの仕様上0.05以上必須。指定しない場合は０を渡す
        :param remark: 今は使っていないが、引数としては残してある。何かしら文字列をテキトーに渡す。
        :return: 上記の情報をまとめてDic形式で返却。オーダーミス発生(オーダー入らず)した場合は、辞書内cancelがTrueとなる。
        ■オーダー種類について
          STOP:指値。順張り（現価格より高い値段で買い、現価格より低い値段で売りの指値）、また、ロスカット
          LIMIT:指値。逆張り（現価格より低い値段で買い、現価格より高い値段で売りの指値）、また、利確
          MARKET:成り行き。この場合、priceは設定しても無視される（ただし引数としてはテキトーな数字を入れる必要あり）。
        """
        self.dummy()  # ただpycharmの波戦警告を消したいだけ。。。なんの機能もない呼び出し
        # 念のため、初期値を入れておく。
        data = {  # ロスカ、利確ありのオーダー
            "order": {
                "instrument": "USD_JPY",
                "units": 100000,
                "type": "",  # "STOP(逆指)" or "LIMIT"
                "positionFill": "DEFAULT",
                "price": "999",
            }
        }
        data['order']['units'] = str(units * ask_bid)  # 必須　units数。基本10000 askはマイナス、bidはプラス値
        data['order']['type'] = type  # 必須
        if type != "MARKET":
            # 成り行き注文以外
            data['order']['price'] = str(round(price, 3))  # 指値の場合は必須
        if tp_range != 0:
            # 利確設定ありの場合
            data['order']['takeProfitOnFill'] = {}
            data['order']['takeProfitOnFill']['price'] = str(round(price + (tp_range * ask_bid), 3))  # 利確 (0.015)
            data['order']['takeProfitOnFill']['timeInForce'] = "GTC"
        if lc_range != 0:
            # ロスカ設定ありの場合
            data['order']['stopLossOnFill'] = {}
            data['order']['stopLossOnFill']['price'] = str(round(price - (lc_range * ask_bid), 3))  # ロスカット
            data['order']['stopLossOnFill']['timeInForce'] = "GTC"
        if tr_range != 0:
            # トレールストップロス設定ありの場合
            data['order']['trailingStopLossOnFill'] = {}
            data['order']['trailingStopLossOnFill']['distance'] = str(round(tr_range, 3))  # ロスカット
            data['order']['trailingStopLossOnFill']['timeInForce'] = "GTC"

        # 実行
        ep = OrderCreate(accountID=self.accountID, data=data)  #
        res_json = eval(json.dumps(self.api.request(ep), indent=2))
        if 'orderCancelTransaction' in res_json:
            print("   ■■■CANCELあり")
            canceled = True
        else:
            canceled = False

        # res_df = self.func_make_dic(res_json, remark)  # 必要項目の抜出　不要？？？221030
        # 実行結果の中から、約定価格を取得する（Marketの場合のみとなる）
        # if 'orderFillTransaction' in res_json:
        #     if 'price' in res_json['orderFillTransaction']:
        #         act_price = res_json['orderFillTransaction']['price']
        #     else:
        #         act_price = 99999
        # else:
        #     act_price = 8888
        # オーダー情報履歴をまとめておく
        order_info = {"price": str(round(price, 3)),
                      "unit": str(units * ask_bid),  # units数。基本10000 askはマイナス、bidはプラス値
                      "tp": str(round(price + (tp_range * ask_bid), 3)),
                      "lc": str(round(price - (lc_range * ask_bid), 3)),
                      "type": type,
                      "remark": remark,
                      "cancel": canceled
                      }
        return order_info

    # (4)-1 注文（単品）キャンセル
    def OrderCancel_exe(self, order_id, remark="cancel"):
        """
        注文（単品）キャンセルする。
        ＜参考＞ロスカ注文やTP注文、通常の指値等、一つ一つにIDがある。ロスカIDのみのキャンセルが可能。
        :param order_id: キャンセルしたいオーダーのID（ポジションではなくオーダー）
        :param remark:今は利用していないが、、、念のためにとってある
        :return:
        """
        # 呼び出し:oa.OrderCancel_exe(order_id,"remark")
        # remarkは引数には不要！
        # 返却値:Dataframe
        ep = OrderCancel(accountID=self.accountID, orderID=order_id)
        res_json = eval(json.dumps(self.api.request(ep), indent=2))
        res_df = self.func_make_dic(res_json, remark)  # 必要項目の抜出
        return res_df

    # (4)-2 注文の全解除(各ポジションのロスカや利確注文は削除しない（TPとLCを指値時に設定した場合、ポジションと同時にTP/LCオーダーが入る。）
    def OrderCancel_All_exe(self):
        """
        現在発行している、「新規にポジションを取るための注文」を全てキャンセルする。
        すでに所持しているポジションへのロスカ、利確、トレールの注文はキャンセルされない。
        APIで「新規ポジションを取るための注文」はtypeがLimitかStopとなっており、それで上記を判定している）
        :return:
        """
        # 呼び出し:oa.OrderCancel_All_exe()
        # 返却値:Dataframe
        open_df = self.OrdersPending_exe()
        close_df = None
        if len(open_df) == 0:
            print("     @NoPendingClosefunc)")
            return None
        else:
            for index, row in open_df.iterrows():
                if row['type'] == 'LIMIT' or row['type'] == 'STOP':
                    pass
                    # res_df = self.OrderCancel_exe(row["id"])  # 【関数】単品をクローズする　　不要なの？
                # close_df = pd.concat([close_df , res_df])#新決済情報を縦結合
            return close_df

    # (5) 注文（単品）確認
    def OrderDetails_exe(self, order_id):
        """
        単品の注文内容の詳細を確認する
        :param order_id: 注文のID
        :return: あまり利用しないので、Jsonのままで返却
        """
        ep = OrderDetails(accountID=self.accountID, orderID=order_id)
        res_json = eval(json.dumps(self.api.request(ep), indent=2))
        return res_json

    # (6) 注文（保留中）の一覧
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
            res_df['order_time_jp'] = res_df.apply(lambda x: self.iso_to_jstdt(x, 'createTime'), axis=1)  # 日本時刻の表示
            res_df['past_time_sec'] = res_df.apply(lambda x: self.cal_past_time(x), axis=1)  # 経過時刻の算出

            return res_df

    # (6-2) 注文（保留中）の一覧（ただし、typeがLimitかStopの物。それ以外の注文である、ロスカットや利確注文は消したくない）
    def OrdersWaitPending_exe(self):
        """
        注文の一覧を取得。
        ただし、新規にポジションを取得するための注文のみ。
        ＜参考＞「新規のポジションを取得するための注文」は、APIではtypeがLimitかStopとなっている
        :return:
        """
        ep = OrdersPending(accountID=self.accountID)
        res_json = eval(json.dumps(self.api.request(ep), indent=2))
        res_df = pd.DataFrame(res_json['orders'])  # DFに変換
        # print(res_df)
        if len(res_df) == 0:
            # 注文中がない場合、何もしない
            return res_df
        else:
            res_df['order_time_jp'] = res_df.apply(lambda x: self.iso_to_jstdt(x, 'createTime'), axis=1)  # 日本時刻の表示
            # 注文からの経過時間を秒で算出する
            res_df['past_time_sec'] = res_df.apply(lambda x: self.cal_past_time(x), axis=1)  # 経過時刻の算出

            del_target = []
            for index, row in res_df.iterrows():
                if row['type'] == 'LIMIT' or row['type'] == 'STOP':
                    # LIMITとSTOPが対象。
                    pass
                else:
                    # typeが利確やロスカ、トレール注文の場合は一覧には乗せない
                    del_target.append(index)
            res_df.drop(index=del_target, inplace=True)  # 不要な行を削除（IMITとSTOPのみが対象）

            return res_df

    # (8)取引中の全トレード(データフレームを返却)
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
        ep = OpenTrades(accountID=self.accountID)
        res_json = eval(json.dumps(self.api.request(ep), indent=2))
        # print(res_json)
        res_df = pd.DataFrame(res_json["trades"])
        if len(res_df) == 0:
            return res_df
        else:
            res_df['order_time_jp'] = res_df.apply(lambda x: self.iso_to_jstdt(x, 'openTime'), axis=1)  # 日本時刻の表示
            # 注文からの経過時間を秒で算出する
            res_df['past_time_sec'] = res_df.apply(lambda x: self.cal_past_time(x), axis=1)  # 経過時刻の算出
            res_df['unrealizedPL_pips'] = round(res_df['unrealizedPL'].astype('float') /
                                                res_df['currentUnits'].astype('float'), 3)
            return res_df

    # (9)トレードIDの詳細（トレード毎 今うまく使えない。）
    def TradeDetails_exe(self, trade_id):
        ep = TradeDetails(accountID=self.accountID, tradeID=trade_id)
        res_json = eval(json.dumps(self.api.request(ep), indent=2))
        # print(res_json["trade"])
        res_df = pd.DataFrame(res_json["trade"], index=[0, ])
        return res_df  # res_json

    # (10) トレードの変更等
    def TradeCRCDO_exe(self, trade_id, data):
        ep = TradeCRCDO(accountID=self.accountID, tradeID=trade_id, data=data)
        res_json = eval(json.dumps(self.api.request(ep), indent=2))
        return res_json

    # (11)トレードの決済 data=Noneの場合はポジション一括（部分決済ではない）
    def TradeClose_exe(self, trade_id, data, remark):
        # 呼び出し:oa.TradeClose_exe(trade_id , data(基本はNoneで全数決済),remark(何かメモ[使わないが必要]))
        ep = TradeClose(accountID=self.accountID, tradeID=trade_id, data=data)
        res_json = eval(json.dumps(self.api.request(ep), indent=2))
        res_df = self.func_make_dic(res_json, remark)  # 必要項目の抜出
        return res_df

    # (12) 取引中の全トレードを一個づつ決済（データ取得あり）
    def TradeAllColse_exe(self, remark):
        # 呼び出し:oa.TradeAllColse_exe(remark(何かメモ[使わないが必要]))
        open_df = self.OpenTrades_exe()
        if len(open_df) == 0:
            print("  @NoPosition (@all close func)")
            return None
        else:
            count = 0
            # res_df = None  # dataframe初期化
            close_df = None
            for index, row in open_df.iterrows():
                res_df = self.TradeClose_exe(row["id"], None, remark)  # 【関数】単品をクローズする
                close_df = pd.concat([close_df, res_df])  # 新決済情報を縦結合
                count = count + 1
            print("   @PositionClear:", count, "個(@all close func)")
            # merge_df = pd.merge(open_df, close_df, left_on='id', right_on='link_id')  # Open時とCloseを横結合
            return close_df

    # (13) 全ポジションの取得(ポジション＝通貨毎。tradeを通貨毎にまとめた感じ)
    def OpenPositions_exe(self):
        ep = OpenPositions(accountID=self.accountID)
        res_json = eval(json.dumps(self.api.request(ep), indent=2))
        res_df = self.func_make_dic(res_json, "OpenList")  # 必要項目の抜出
        return res_df

    # (14)ポジションの詳細を取得 instrument = "USD_JPY"
    def PositionDetails_exe(self, instrument):
        ep = PositionDetails(accountID=self.accountID, instrument=instrument)
        res_json = eval(json.dumps(self.api.request(ep), indent=2))
        return res_json

    # (15)ポジションの決済(ALLで全決済)
    def PositionClose_exe(self, data):
        # 昔は引数が(self, instrument, data)　だった。instrumentを削除した
        ep = PositionClose(accountID=self.accountID, instrument="USD_JPY", data=data)
        res_json = eval(json.dumps(self.api.request(ep), indent=2))
        print(res_json)
        return res_json  # oa = Oanda(accountID, access_token)

    # (16)残金を取得する
    def GetBalance_exe(self):
        client = oandapyV20.API(access_token=self.access_token)
        r = accounts.AccountSummary(self.accountID)
        response = client.request(r)
        res = response["account"]["balance"]
        return res  # oa = Oanda(accountID, access_token)

    # (17)トランザクションを取得(トランザクションから実際の取引価格を取得する
    def GetActPrice_exe(self, transactionID):
        ep = trans.TransactionDetails(accountID=self.accountID, transactionID=transactionID)
        res_json = eval(json.dumps(self.api.request(ep), indent=2))
        print(res_json)
        if "price" in res_json:
            act_price = res_json['price']
        else:
            act_price = 99999999
        return act_price

    # 【Roll等を使い、過去足との平均値等を算出】
    def add_roll_info(self, data_df):
        # IBM 当月と前月の差、当月と２か月前の差　直近３カ月比重（これどうしよう）
        data_df['body_pass1'] = data_df['body'] - data_df['body'].shift(1)  # 自身と、一つ前足との差分（自身ーひとつ前）
        data_df['body_pass2'] = data_df['body'] - data_df['body'].shift(2)  # 自身と、二つ前足との差分（自身ーふたつ前）
        data_df['body_pass3'] = data_df['body'] - data_df['body'].shift(3)  # 自身と、二つ前足との差分（自身ーふたつ前）
        # data_df['body1'] = data_df['body'].shift(1)  # 自身と、一つ前足との差分（自身ーひとつ前）
        # data_df['body2'] = data_df['body'].shift(2)  # 自身と、二つ前足との差分（自身ーふたつ前）
        # data_df['body3'] = data_df['body'].shift(3)  # 自身と、二つ前足との差分（自身ーふたつ前）

        data_df['body_abspass1'] = data_df['body_abs'] - data_df['body_abs'].shift(1)  # 自身と、一つ前足との差分（自身ーひとつ前）
        data_df['body_abspass2'] = data_df['body_abs'] - data_df['body_abs'].shift(2)  # 自身と、二つ前足との差分（自身ーふたつ前）
        data_df['body_abspass3'] = data_df['body_abs'] - data_df['body_abs'].shift(3)  # 自身と、二つ前足との差分（自身ーふたつ前）

        # data_df['up_rod1'] = data_df['up_rod'].shift(1)  # 自身と、一つ前足との差分（自身ーひとつ前）
        # data_df['up_rod2'] = data_df['up_rod'].shift(2)  # 自身と、二つ前足との差分（自身ーふたつ前）
        # data_df['up_rod3'] = data_df['up_rod'].shift(3)  # 自身と、二つ前足との差分（自身ーふたつ前）
        # data_df['low_rod1'] = data_df['low_rod'].shift(1)  # 自身と、一つ前足との差分（自身ーひとつ前）
        # data_df['low_rod2'] = data_df['low_rod'].shift(2)  # 自身と、二つ前足との差分（自身ーふたつ前）
        # data_df['low_rod3'] = data_df['low_rod'].shift(3)  # 自身と、二つ前足との差分（自身ーふたつ前）

        # 直近３個の平均値を求める
        data_df['body_3mean'] = data_df['body'].rolling(3, min_periods=1).mean()

        # 当足と３足前のクローズ価格の変化率（傾き）
        data_df['tilt_close1'] = data_df['close'] - data_df['close'].shift(1)
        data_df['tilt_close2'] = data_df['close'] - data_df['close'].shift(2)  # 自身と、二つ足前のクローズ価格の差分（傾きに近い）
        data_df['tilt_close3'] = data_df['close'] - data_df['close'].shift(3)
        data_df['tilt_close6'] = data_df['close'] - data_df['close'].shift(6)
        data_df['tile_3_6'] = data_df['tilt_close3'] + data_df['tilt_close6']

        # 当月のbodyのBB占有率と、１つ前の占有率の差分
        data_df['tilt_bb_body_ratio1'] = data_df['bb_body_ratio'] - data_df['bb_body_ratio'].shift(1)
        data_df['tilt_bb_body_ratio2'] = data_df['bb_body_ratio'] - data_df['bb_body_ratio'].shift(2)  # 自身と、二つ足前の差分
        data_df['bb_body_ratio1'] = data_df['bb_body_ratio'].shift(1)
        data_df['bb_body_ratio2'] = data_df['bb_body_ratio'].shift(2)

        # 当月のBB内比率の推移bb_over_ratio
        data_df['bb_over_ratio_1'] = data_df['bb_over_ratio'] - data_df['bb_over_ratio'].shift(1)  # 一つ前足との差分
        data_df['bb_over_ratio_2'] = data_df['bb_over_ratio'] - data_df['bb_over_ratio'].shift(2)  #
        data_df['bb_under_ratio_1'] = data_df['bb_under_ratio'] - data_df['bb_under_ratio'].shift(1)
        data_df['bb_under_ratio_2'] = data_df['bb_under_ratio'] - data_df['bb_under_ratio'].shift(2)  #

        # Volumeについて
        data_df['volume_tilt1'] = data_df['volume'] - data_df['volume'].shift(1)  # 自身と、二つ足前のクローズ価格の差分（傾きに近い）
        data_df['volume_tilt2'] = data_df['volume'] - data_df['volume'].shift(2)  # 自身と、二つ足前のクローズ価格の差分（傾きに近い）
        # data_df['volume_pass2'] = data_df['volume'].shift(1)
        # data_df['volume_pass2'] = data_df['volume'].shift(2)

        # ema関係について
        data_df['cross_pass1'] = data_df['cross'].shift(1)  # 自身と、二つ足前のクローズ価格の差分（傾きに近い）
        data_df['cross_pass2'] = data_df['cross'].shift(2)  # 自身と、二つ足前のクローズ価格の差分（傾きに近い）
        data_df['cross_pass3'] = data_df['cross'].shift(3)
        data_df['ema_gap_pass1'] = data_df['ema_gap'].shift(1)  # 自身と、二つ足前のクローズ価格の差分（傾きに近い）
        data_df['ema_gap_pass2'] = data_df['ema_gap'].shift(2)  # 自身と、二つ足前のクローズ価格の差分（傾きに近い）
        data_df['ema_gap_pass3'] = data_df['ema_gap'].shift(3)
        data_df['ema_gap_tilt3'] = data_df['ema_gap'] - data_df['ema_gap'].shift(3)
        return data_df

    # たまにある０で割るのを防ぐため、０を消す（列単位）
    def zero_cut(self, x):
        self.dummy()  # ただpycharmの波戦警告を消したいだけ。。。なんの機能もない呼び出し
        if x.mid_past_1 == 0:
            return 0.001
        else:
            return x.mid_past_1

    # # 【極値情報を取得する】
    # def peak_flag(self, x):
    #     self.dummy()  # ただpycharmの波戦警告を消したいだけ。。。なんの機能もない呼び出し
    #     if math.isnan(x["peak"]):
    #     # if math.isnan(x):
    #         return 0
    #     else:
    #         return 1
    #
    # def gap_vector(self, x):
    #     if x.ans > 0.10:
    #         return 0
    #     else:
    #         return 1
    #
    # def valley_flag(self, x):
    #     self.dummy()  # ただpycharmの波戦警告を消したいだけ。。。なんの機能もない呼び出し
    #     if math.isnan(x["valley"]):
    #         return 0
    #     else:
    #         return 1
    #
    # # def add_peak(self, data_df):
    # #     # ####peak関数を使うケース
    # #     order_num = 4  # ピーク探索の粒度
    # #     peak = data_df['high'].loc[argrelmfax(data_df["high"].values, order=order_num)]
    # #     valley = data_df['low'].loc[argrelmin(data_df["low"].values, order=order_num)]
    # #
    # #     # データに過去のピーク情報を付属させる（個数が多くなるかもしれないので、ループを作成する）
    # #     for i in range(3):
    # #         # peak情報
    # #         data_df['4peak_b' + str(i)] = peak.shift(i)
    # #         temp_series = pd.Series(data=peak.index)
    # #         temp_series_index = pd.Series(data=temp_series.shift(i).values, index=temp_series)
    # #         data_df['4peak_b_index' + str(i)] = temp_series_index
    # #
    # #         # valley情報
    # #         data_df['4valley_b' + str(i)] = valley.shift(i)
    # #         temp_series = pd.Series(data=valley.index)
    # #         temp_series_index = pd.Series(data=temp_series.shift(i).values, index=temp_series)
    # #         data_df['4valley_b_index' + str(i)] = temp_series_index
    # #
    # #     # order_num = 5  # ピーク探索の粒度
    # #     # peak = data_df['high'].loc[argrelmax(data_df["high"].values, order=order_num)]
    # #     # valley = data_df['low'].loc[argrelmin(data_df["low"].values, order=order_num)]
    # #     # # データに過去のピーク情報を付属させる（個数が多くなるかもしれないので、ループを作成する）
    # #     # for i in range(3):
    # #     #     # peak情報
    # #     #     data_df['7peak_b' + str(i)] = peak.shift(i)
    # #     #     temp_series = pd.Series(data=peak.index)
    # #     #     temp_series_index = pd.Series(data=temp_series.shift(i).values, index=temp_series)
    # #     #     data_df['7peak_b_index' + str(i)] = temp_series_index
    # #     #
    # #     #     # valley情報
    # #     #     data_df['7valley_b' + str(i)] = valley.shift(i)
    # #     #     temp_series = pd.Series(data=valley.index)
    # #     #     temp_series_index = pd.Series(data=temp_series.shift(i).values, index=temp_series)
    # #     #     data_df['7valley_b_index' + str(i)] = temp_series_index
    # #
    # #     # peakの機械学習用
    # #     # data_df['peak'] = peak  # この時点では「価格」を含んだ情報  なおindexに紐ついて結合ざれる
    # #     # data_df['valley'] = valley  # この時点では「価格」を含んだ情報
    # #     # data_df['peak_tf'] = data_df.apply(lambda x: self.peak_flag(x), axis=1)
    # #     # data_df['valley_tf'] = data_df.apply(lambda x: self.valley_flag(x), axis=1)
    # #
    # #     return data_df
    #
    #
    # def add_peak_ml(self, data_df):
    #     # フォルムを検討する為の情報を不可（ランダムフォレスト用）
    #     for v in range(1, 15):
    #         # if v % 3 == 0 or v == 1:
    #             data_df['mid_past_' + str(v)] = data_df['mid_outer'] - data_df['mid_outer'].shift(v)
    #             data_df['mid_past_' + str(v)] = data_df['high'] - data_df['high'].shift(v)  # 中身のみ、highに変更
    #             data_df['mid_past_1'] = data_df.apply(lambda x: self.zero_cut(x), axis=1)
    #             # 過去データの付与
    #             data_df['mid_past_ratio' + str(v)] = round(data_df['mid_past_' + str(v)] / data_df['mid_past_1'], 3)
    #
    #     # 不要データは削除する
    #     for v in range(1,3):
    #         data_df.drop(['mid_past_' + str(v)], axis=1, inplace=True)
    #     # 念のための処理
    #     data_df.fillna(0, inplace=True)  # 0埋めしておく
    #
    #     # ####peak関数を使うケース
    #     order_num = 4  # ピーク探索の粒度
    #     peak = data_df['high'].loc[argrelmax(data_df["high"].values, order=order_num)]
    #     valley = data_df['low'].loc[argrelmin(data_df["low"].values, order=order_num)]
    #
    #     # peakの機械学習用
    #     data_df['peak'] = peak  # この時点では「価格」を含んだ情報  なおindexに紐ついて結合ざれる
    #     data_df['valley'] = valley  # この時点では「価格」を含んだ情報
    #     data_df['peak_tf'] = data_df.apply(lambda x: self.peak_flag(x), axis=1)
    #     data_df['valley_tf'] = data_df.apply(lambda x: self.valley_flag(x), axis=1)
    #
    #     #  増減数についての検討
    #     # data_df['mid_up'] = data_df['mid_outer'].shift(-3)  # 教師データを付与する
    #     # data_df['mid_up'] = data_df.apply(lambda x: self.gap_vector(data_df['mid_up']), axis=1)
    #     # 極値合計的な物
    #     # data_df['peak_tf_future'] = data_df['peak_tf'].shift(-1)
    #     # data_df['valley_tf_future'] = data_df['valley_tf'].shift(-1)
    #     # data_df['ans'] = data_df['peak_tf_future'] + data_df['valley_tf_future']
    #     return data_df
    #
    # def ml_delete_price_time(self, df):
    #     """
    #     機械学習のために、直接的な価格や時刻情報を削除する
    #     """
    #     self.dummy()  # ただpycharmの波戦警告を消したいだけ。。。なんの機能もない呼び出し
    #
    #     # 定型項目の削除
    #     targets = ['time', 'time_jp']  # 時間関係の削除
    #     targets.extend(['open', 'close', 'high', 'low', 'inner_high', 'inner_low', 'mid_outer'])  # 直接価格の削除
    #     targets.extend(['body', 'body_abs', 'up_rod', 'low_rod', ])  # 不要？情報の削除
    #     targets.extend(['peak', 'valley'])  # 直接価格の削除(極値）
    #     targets.extend(['bb_upper', 'bb_lower', 'bb_middle'])  # 直接価格の削除(極値）
    #     targets.extend(['body', 'body_abs', 'up_rod', 'low_rod'])  # 直接価格の削除(極値）
    #
    #     for target in targets:  # 対象を削除する
    #         if target in df:
    #             df.drop([target], axis=1, inplace=True)  # , inplace=Trueはせず?
    #
    #     # 一部機械学習データの削除
    #     # for v in range(1, 9):
    #     #     if 'mid_past_' + str(v) in df:
    #     #         df.drop(['mid_past_' + str(v)], axis=1, inplace=True)
    #
    #     df.fillna(0, inplace=True)  # 0埋めしておく
    #     return df
    #
    # # 機械学習で使う用
    # # (2)-3 過去情報をまとめて持ってくる【項目がシンプルのバージョン。(2)-1とセット利用】
    # def InstrumentsCandles_multi_ml_exe(self, pair, params, roop):
    #     # 呼び出し:oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 50}, roop(何セットか))
    #     # 取れる行数は、50×roop行
    #     # 返却値:Dataframe[time,open.close,high,low,time_jp]　＋　add_information関数達で情報追加
    #     candles = None  # dataframeの準備
    #     for i in range(roop):
    #         df = self.InstrumentsCandles_exe(pair, params)  # 【関数】データ取得＋基本５項目のDFに変換（dataframeが返り値）
    #         params["to"] = df["time"].iloc[0]  # ループ用（次回情報取得の期限を決める）
    #         candles = pd.concat([df, candles])  # 結果用dataframeに蓄積（時間はテレコ状態）
    #     # 取得した情報をtime_jpで並び替える
    #     candles.sort_values('time_jp', inplace=True)  # 時間順に並び替え
    #     temp_df = candles.reset_index()  # インデックスをリセットし、ML用のデータフレームへ
    #     temp_df.drop(['index'], axis=1, inplace=True)  # 不要項目の削除（volumeってなに）
    #     # 解析用の列を追加する（不要な場合はここは削除する。機械学習等で利用する）
    #     data_df = self.add_basic_data(temp_df)  # 【関数/必須】基本項目を追加する
    #     # data_df = self.add_bb_data(data_df)  # 【関数】ボリンジャーバンド情報を追加
    #     data_df = self.add_peak_ml(data_df)
    #     # data_df = self.add_ema_data(data_df)  # 【関数】指数平均情報を追加
    #     # data_df = self.add_roll_info(data_df)  # 【関数】過去の情報（roll)にて学習データを付与するd
    #     # data_df = self.add_macd(data_df)
    #
    #     # 返却
    #     return data_df