import threading  # 定時実行用
import time
import datetime

# 自作ファイルインポート
import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.classOanda as oanda_class
import programs.classPosition2 as classPosition
import programs.fTurnInspection as f  # とりあえずの関数集
import programs.fPeakLineInspection as p


def peakLineInspection():
    print("test")


def mode1():
    print("■■■■Mode1")
    info_r = {
        "name": "test",
        "units": 5,
        "direction": -1,
        "tp_range": 0,
        "lc_range": 0,
        "type": "MARKET",
        "price": 145.500,
        "order_permission": True,
        "margin": 0
    }
    info_r = {
        "name": "test",
        "units": 10,
        "direction": 1,
        "tp_range": 0,
        "lc_range": 0,
        "type": "STOP",
        "price": 147.600,
        "order_permission": True,
        "margin": 0
    }
    cTest.order_plan_registration(info_r)
    cTest.print_info()

    # チャート分析セクション
    # global gl_peak_memo
    # # チャート分析結果を取得する
    # inspection_condition = {
    #     "now_price": gl_now_price_mid,  # 現在価格を渡す
    #     "data_r": gl_data5r_df,  # 対象となるデータ
    #     "turn_2": {"data_r": gl_data5r_df, "ignore": 1, "latest_n": 2, "oldest_n": 30, "return_ratio": 30},
    #     "turn_3": {"data_r": gl_data5r_df, "ignore": 2, "latest_n": 2, "oldest_n": 30, "return_ratio": 30},
    #     "time_str": gl_now_str,  # 記録用の現在時刻
    # }
    # # (5) ピーク情報（連続のLINE送信を抑える必要あり）
    # ans_dic = p.mainInspectionPeakLine(inspection_condition)
    # if ans_dic['para_send'] == 1:  # 送信フラグの場合
    #     if gl_peak_memo["send1"] != ans_dic['para_memo']:  # 古いのと変化点探す
    #         tk.line_send(ans_dic['para_memo'])  # 送信
    #         gl_peak_memo["send1"] = ans_dic['para_memo']  # 古いのを入れ替え
    # if ans_dic['ans_send'] == 1:  # 送信フラグの場合
    #     if gl_peak_memo["send2"] != ans_dic['ans_memo']:  # 古いのと変化点探す
    #         tk.line_send(ans_dic['ans_memo'])  # 送信
    #         gl_peak_memo["send2"] = ans_dic['ans_memo']  # 古いのを入れ替え


def mode2():
    global gl_exe_mode
    print("■■■■Mode2")
    cTest.update_information()
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
    global gl_midnight_close_flag, gl_now_price_mid, gl_data5r_df, gl_first, gl_first_time, gl_latest_exe_time

    # ■深夜帯は実行しない　（ポジションやオーダーも全て解除）
    if 3 <= time_hour <= 6:
        if gl_midnight_close_flag == 0:  # 繰り返し実行しないよう、フラグで管理する
            gl_midnight_close_flag = 1  # 実施済みフラグを立てる
    # ■実行を行う
    else:
        gl_midnight_close_flag = 0  # 実行可能時には深夜フラグを解除しておく（毎回やってしまうけどいいや）

        # ■時間内でスプレッドが広がっている場合は強制終了し実行しない　（現価を取得しスプレッドを算出する＋グローバル価格情報を取得する）
        price_dic = oa.NowPrice_exe("USD_JPY")
        if price_dic['error'] == -1:  # APIエラーの場合はスキップ
            return -1  # APIエラーによる終了　print("API異常発生の可能性", gl_now)
        else:
            if price_dic['data']['spread'] > gl_arrow_spread:
                return -1  # スプレッド以上における終了　print("    ▲スプレッド異常", gl_now, price_dic['spread'])
        price_dic = price_dic['data']
        gl_now_price_mid = price_dic['mid']  # 念のために保存しておく（APIの回数減らすため）

        # ■直近の実行からどのくらい経過したかを計測する
        if gl_latest_exe_time == 0:
            past_time = 66   # 初回のみテキトーな値でごまかす
        else:
            past_time = (datetime.datetime.now().replace(microsecond=0) - gl_latest_exe_time).seconds

        if time_min % 5 == 0 and 15 <= time_sec < 30 and past_time > 60:  # キャンドルの確認　秒指定だと飛ぶので、前回から●秒経過&秒数に余裕を追加
            d5_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 30}, 1)  # 時間昇順
            if d5_df['error'] == -1:
                return -1
            d5_df = d5_df['data']  # データの取得
            gl_data5r_df = d5_df.sort_index(ascending=False)  # 対象となるデータフレーム（直近が上の方にある＝時間降順）をグローバルに
            d5_df.to_csv(tk.folder_path + 'main_data5.csv', index=False, encoding="utf-8")  # 直近保存用
            mode1()
            gl_latest_exe_time = datetime.datetime.now().replace(microsecond=0)  # 最終実行時間の取得
        elif time_min % 1 == 0 and time_sec % 2 == 0:  # 高頻度での確認事項（キャンドル調査時のみ飛ぶ）
            mode2()

        # ■　初回だけ実行と同時に行う
        if gl_first == 0:
            gl_first = 1
            gl_first_time = gl_now
            print("■■■初回", gl_now, gl_exe_mode, gl_live)  # 表示用（実行時）
            d5_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 30}, 1)  # 時間昇順
            if d5_df['error'] == -1:
                return -1
            else:
                d5_df = d5_df['data']
            # ↓時間指定
            # jp_time = datetime.datetime(2023, 7, 14, 11, 16, 0)
            # euro_time_datetime = jp_time - datetime.timedelta(hours=9)
            # euro_time_datetime_iso = str(euro_time_datetime.isoformat()) + ".000000000Z"  # ISOで文字型。.0z付き）
            # param = {"granularity": "M5", "count": 30, "to": euro_time_datetime_iso}
            # d5_df = oa.InstrumentsCandles_exe("USD_JPY", param)['data']
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
gl_latest_exe_time = 0
temp_magnification = 1  # 基本本番環境で動かす。unitsを低めに設定している為、ここで倍率をかけれる。
gl_peak_memo = {"send1": "", "send2": "", "send3": ""}

# ■オアンダクラスの設定
fx_mode = 0  # 1=practice, 0=Live
if fx_mode == 1:  # practice
    oa = oanda_class.Oanda(tk.accountID, tk.access_token, tk.environment)  # インスタンス生成
    gl_live = "Pra"
else:  # Live
    oa = oanda_class.Oanda(tk.accountIDl, tk.access_tokenl, tk.environmentl)  # インスタンス生成
    gl_live = "Live"


price_dic = oa.NowPrice_exe("USD_JPY")['data']
print("【現在価格live】", price_dic['mid'], price_dic['ask'], price_dic['bid'], price_dic['spread'])
now_price = oa.NowPrice_exe("USD_JPY")['data']['mid']

tk.line_send("■■新規スタート", gl_live)
# main()
oa.OrderCancel_All_exe()  # 露払い(classesに依存せず、オアンダクラスで全部を消す）
oa.TradeAllClose_exe()  # 露払い(classesに依存せず、オアンダクラスで全部を消す）
cTest = classPosition.order_information("6", oa)
exe_loop(1, exe_manage)  # exe_loop関数を利用し、exe_manage関数を1秒ごとに実行