import datetime  # 日付関係
import pandas as pd  # add_peaks
import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.classOanda as classOanda
import programs.fGeneric as g


def turn_each_support(data_df, direction, ans_info):
    """
    ここでのデータは、０行目が最新データ
    :param data_df:
    :param direction:
    :param ans_info:
    :return:
    """
    # パターン買いの一部
    ratio = 0.6
    back_slash = ans_info['gap'] * ratio  # トリガとなる戻り分を算出

    if len(data_df) == 2:
        # (1) latestのパターンを計算
        if direction == 1:  # プラスの連荘＝谷の場合　（折り返し部のみの話）
            if data_df.iloc[1]['body'] >= 0 and data_df.iloc[0]['body'] >= 0:
                pattern_comment = "afterV:UpUp"
                pattern = 10
                order_line = round(ans_info['latest_image_price'], 3)
                type = "LIMIT"  # 順張りか逆張りかに注意　"LIMIT"  "STOP"
            elif data_df.iloc[1]['body'] >= 0 and data_df.iloc[0]['body'] <= 0:
                pattern_comment = "afterV:UpDownss"
                pattern = 11
                order_line = round(ans_info['oldest_image_price'], 3)
                type = "LIMIT"  # 逆張り
            elif data_df.iloc[1]['body'] <= 0 and data_df.iloc[0]['body'] >= 0:
                pattern_comment = "afterV:DownUp"
                pattern = 12
                order_line = round(ans_info['latest_image_price'], 3)  # - back_slash, 3)
                type = "LIMIT"  # 逆張り
            else:
                pattern_comment = "afterV:Error"
                pattern = 13
                order_line = type = 999

        elif direction == -1:  # マイナスの連荘＝山の場合　（折り返し部の話）
            if data_df.iloc[1]['body'] <= 0 and data_df.iloc[0]['body'] <= 0:
                pattern_comment = "afterM:DownDown"
                pattern = -10
                order_line = round(ans_info['latest_image_price'], 3)
                type = "LIMIT"  # 順張り
            elif data_df.iloc[1]['body'] <= 0 and data_df.iloc[0]['body'] >= 0:
                pattern_comment = "afterM:DownUpss"
                pattern = -11
                order_line = round(ans_info['latest_image_price'], 3)
                type = "LIMIT"  # 逆張り
            elif data_df.iloc[1]['body'] >=0 and data_df.iloc[0]['body'] <=0:
                pattern_comment = "afterM:UpDown"
                pattern = -12
                order_line = round(ans_info['latest_image_price'], 3)  # + back_slash, 3)
                type = "LIMIT"  # 順張り
            else:
                pattern_comment = "afterM:Error"
                pattern = -13
                order_line = type = 999

        # （２）latestの中のoldとlatestどっちがサイズが大きいかの判別
        older = data_df.iloc[1]['body_abs']
        later = data_df.iloc[0]['body_abs']
        if older <= later:
            range_expected = 1  # レンジの予感
        else:
            range_expected = 0


    else:
        # ここは全部を網羅しておくこと（初期値的に）
        pattern = -99
        pattern_comment = "NoComment2足分以上"
        order_line = type = 999
        range_expected = 0

    # LCrangeを計算する(MAX7pips, Min 3pips)
    lc_range = round(ans_info['gap'] / 2, 3)
    if lc_range > 0.07:
        lc_range = 0.07
    elif lc_range < 0.03:
        lc_range = 0.03

    # Body長、移動長の平均値を算出する
    body_ave = data_df["body_abs"].mean()
    move_ave = data_df["moves"].mean()

    return {
        "pattern_comment": pattern_comment,
        "pattern_num": pattern,
        "order_line": round(order_line,3),
        "order_type": type,
        "back_slash": back_slash,
        "lc_range": lc_range,
        "gap": ans_info['gap'],
        'body_ave': body_ave,
        "move_abs": move_ave,
        "range_expected": range_expected
    }


def turn_each_inspection(data_df_origin):
    """
    渡された範囲で、何連続で同方向に進んでいるかを検証する
    :param data_df_origin: 直近が上側（日付降順/リバース）のデータを利用
    :return: Dict形式のデータを返伽
    """
    # コピーウォーニングのための入れ替え
    data_df = data_df_origin.copy()

    if len(data_df) >=1:  # データが存在していれば実施
        # 処理の開始
        base_direction = 0
        counter = 0
        for i in range(len(data_df)-1):
            tilt = data_df.iloc[i]['middle_price'] - data_df.iloc[i+1]['middle_price']
            if tilt == 0:
                # tiltが０になるケースは、商不可の為仮値を代入する
                # print("  TILT0発生", data_df.iloc[i]['middle_price'], data_df.iloc[i]['time_jp'], data_df.iloc[i+1]['time_jp'])
                # print(data_df)
                tilt = 0.001
            tilt_direction = round(tilt / abs(tilt), 0)  # 方向のみ（念のためラウンドしておく）
            # ■初回の場合の設定。１行目と２行目の変化率に関する情報を取得、セットする
            if counter == 0:
                base_direction = tilt_direction
            else:
                # print(" 初回ではありません")
                pass

            # ■カウントを進めていく
            if tilt_direction == base_direction:  # 今回の検証変化率が、初回と動きの方向が同じ場合
                counter += 1
            else:
                break  # 連続が途切れた場合、ループを抜ける
        # ■対象のDFを取得し、情報を格納していく
        ans_df = data_df[0:counter+1]  # 同方向が続いてる範囲のデータを取得する
        ans_other_df = data_df[counter:]  # 残りのデータ

        if base_direction == 1:
            # 上り方向の場合、直近の最大価格をlatest_image価格として取得(latest価格とは異なる可能性あり）
            latest_image_price = ans_df.iloc[0]["inner_high"]
            oldest_image_price = ans_df.iloc[-1]["inner_low"]
            latest_peak_price = ans_df.iloc[0]["high"]
            oldest_peak_price = ans_df.iloc[-1]["low"]
        else:
            # 下り方向の場合

            latest_image_price = ans_df.iloc[0]["inner_low"]
            oldest_image_price = ans_df.iloc[-1]["inner_high"]
            latest_peak_price = ans_df.iloc[0]["low"]
            oldest_peak_price = ans_df.iloc[-1]["high"]
        #
        # ■平均移動距離等を考える
        body_ave = round(data_df["body_abs"].mean(),3)
        move_ave = round(data_df["moves"].mean(),3)

        # ■GAPを計算する（０の時は割る時とかに困るので、最低0.001にしておく）
        # gap = round(abs(latest_image_price - oldest_image_price), 3)  # MAXのサイズ感
        gap_close = round(abs(latest_image_price - ans_df.iloc[-1]["close"]), 3)  # 直近の価格（クローズの価格&向き不問）
        if gap_close == 0:
            gap_close = 0.001
        else:
            gap_close = gap_close

        gap = round(abs(latest_image_price - oldest_image_price), 3)  # 直近の価格（クローズの価格&向き不問）
        if gap == 0:
            gap = 0.001
        else:
            gap = gap

        # ■　一旦格納する
        # 表示等で利用する用（機能としては使わない
        memo_time = classOanda.str_to_time_hms(ans_df.iloc[-1]["time_jp"]) + "_" + classOanda.str_to_time_hms(
            ans_df.iloc[0]["time_jp"])
        # 返却用
        ans_dic = {
            "direction": base_direction,
            "count": counter+1,  # 最新時刻からスタートして同じ方向が何回続いているか
            "data": ans_df,  # 対象となるデータフレーム（元のデータフレームではない）
            "data_remain": ans_other_df,  # 対象以外の残りのデータフレーム
            "data_size": len(data_df),  # (注)元のデータサイズ
            "latest_image_price": latest_image_price,
            "oldest_image_price": oldest_image_price,
            "oldest_time_jp": ans_df.iloc[-1]["time_jp"],
            "latest_time_jp": ans_df.iloc[0]["time_jp"],
            "latest_price": ans_df.iloc[0]["close"],
            "oldest_price": ans_df.iloc[-1]["open"],
            "latest_peak_price": latest_peak_price,
            "oldest_peak_price": oldest_peak_price,
            "gap": gap,
            "gap_close": gap_close,
            "body_ave": body_ave,
            "move_abs": move_ave,
            "memo_time": memo_time
        }

        # ■　形状を判定する（テスト）
        type_info_dic = turn_each_support(ans_df, base_direction, ans_dic)  # 対象のデータフレームと、方向を渡す
        ans_dic["support_info"] = type_info_dic  # あくまでメイン解析の要素の一つとして渡す
    else:  # データがEmptyの場合
        # 返却用
        ans_dic = {
            "direction": 1,
            "count": 0,  # 最新時刻からスタートして同じ方向が何回続いているか
            "data": data_df,  # 対象となるデータフレーム（元のデータフレームではない）
            "data_remain": data_df,  # 対象以外の残りのデータフレーム
            "data_size": len(data_df),  # (注)元のデータサイズ
            "latest_image_price": 0,
            "oldest_image_price": 0,
            "oldest_time_jp": 0,
            "latest_time_jp": 0,
            "latest_price": 0,
            "oldest_price": 0,
            "latest_peak_price": 0,
            "oldest_peak_price": 0,
            "gap": 0.0001,
            "gap_close": 0.00001,
            "body_ave": 0.000001,
            "move_abs": 0.00001,
            "memo_time": 0,
            "support_info":{}
        }
    # ■　形状からターゲットラインを求める。
    return ans_dic


def turn_each_inspection_skip(df_r):
    """
    最低でも５０行程度渡さないとエラー発生。
    渡された範囲で、何連続で同方向に進んでいるかを検証する（ただし、skipありは、２つのみの戻りはスキップして検討する）
    :param df_r: 直近が上側（日付降順/リバース）のデータを利用
    :return: Dict形式のデータを返伽
    """
    if len(df_r) == 0:
        return 0
    for i in range(5):  # とりあえず５回分。。本当は再帰とかがベストだと思う
        if i == 0:  # 初回は実行。一番根本となるデータを取得する
            ans_current = turn_each_inspection(df_r)  # 再起用に０渡しておく。。
            next_from = ans_current['count'] - 1
        else:
            next_from = 0  # NextFromのリセット
        # 次の調査対象（ここの長さは一つの判断材料）
        ans_next_jd = turn_each_inspection(df_r[next_from:])  # 再起用に０渡しておく。。
        next_from = next_from + ans_next_jd['count'] - 1

        ans_next_next_jd = turn_each_inspection(df_r[next_from:])  # 再起用に０渡しておく。。
        next_from = next_from + ans_next_next_jd['count'] - 1


        # 判定(次回の幅が２足分、次々回の方向が現在と同一、次々回のスタート(old)価格が現在のスタート(old)価格より高い)
        merge = 0
        # print("条件", ans_next_jd['count'], ans_next_next_jd['direction'], ans_current['direction'])

        if ans_next_jd['count'] <= 2 and ans_next_next_jd['direction'] == ans_current['direction'] and abs(
                ans_next_jd['latest_peak_price'] - ans_next_jd['oldest_peak_price']) < 0.03:
            if ans_current['direction'] == 1:  # 上向きの場合
                if ans_current['oldest_image_price'] > ans_next_next_jd['data'].iloc[-1]["inner_low"]:  # 価格が昔(調査的には次々回のスタート価格)より上昇、
                    # print("上向き")
                    # print(ans_next_next_jd)
                    # print(ans_current['oldest_image_price'], ans_next_next_jd['data'].iloc[-1]["inner_low"])
                    if ans_current['latest_image_price'] > ans_next_next_jd['data'].iloc[0]["inner_high"]:  # 直近価格を超えるような乱高下でもNG
                        # print(ans_current['latest_image_price'], ans_next_next_jd['data'].iloc[0]["inner_high"])
                        merge = 1
            else:  # 下向きの場合
                if ans_current['oldest_image_price'] < ans_next_next_jd['data'].iloc[-1]["inner_high"]:  # 価格が昔(調査的には次々回のスタート価格)より下落
                    # print("上向き")
                    # print(ans_next_next_jd)
                    # print(ans_current['oldest_image_price'], ans_next_next_jd['data'].iloc[-1]["inner_low"])
                    if ans_current['latest_image_price'] < ans_next_next_jd['data'].iloc[0]["inner_low"]:  # 直近価格を超えるような乱高下でもNG
                        # print(ans_current['latest_image_price'], ans_next_next_jd['data'].iloc[0]["inner_low"])
                        merge = 1
        # ここからマージ処理
        if merge == 1:  # 現在(currentと次々回調査分(時系列的には過去）は結合して考える（一つ戻りが間にあるだけ）
            # データフレームの結合（一番もとになるans_currentを更新していく）,情報の更新（Oldの部分を更新していく）
            ans_current['data'] = pd.concat([ans_current['data'], ans_next_jd['data']])  # １行ラップするけど
            ans_current['data'] = pd.concat([ans_current['data'], ans_next_next_jd['data']])  # １行ラップするけど
            ans_current['count'] = len(ans_current['data']) - 2  # 2は調整。。これは大まかな数字
            ans_current['oldest_image_price'] = ans_next_next_jd['oldest_image_price']
            ans_current['oldest_time_jp'] = ans_next_next_jd['oldest_time_jp']
            ans_current['oldest_peak_price'] = ans_next_next_jd['oldest_peak_price']
            ans_current['data_remain'] = df_r[next_from:]  # 残りのデータ
            # gapの計算
            gap = round(abs(ans_current['latest_image_price'] - ans_current['oldest_image_price']), 3)
            if gap == 0:
                gap = 0.001
            else:
                gap = gap
            ans_current['gap'] = gap
            # 備忘録用のメモを作っておく
            ans_df = ans_current['data']
            memo_time = classOanda.str_to_time_hms(ans_df.iloc[-1]["time_jp"]) + "_" + classOanda.str_to_time_hms(
                        ans_df.iloc[0]["time_jp"])
            ans_current['memo_time'] = memo_time
            # 次のループに向け、dr_fを更新
            df_r = df_r[next_from :]  # 残りのデータ
            # print("次回調査対象",df_r.head(5))
        else:
            # print(" 終了")
            break

    return ans_current


def turn_merge_inspection(figure_condition):
    """
    old区間4,latest区間2の場合のジャッジメント
    :param oldest_ans:第一引数がOldestであること。直近部より前の部分が、どれだけ同一方向に進んでいるか。
    :param latest_ans:第二引数がLatestであること。直近部がどれだけ連続で同一方向に進んでいるか
    :param now_price: 途中で追加した機能（現在の価格を取得し、成り行きに近いようなオーダーを出す）　230105追加
    :param figure_condition
    :return:
    """
    #
    # ■直近データの形状の解析
    data_r = figure_condition['data_r']  # データを格納
    ignore = figure_condition['ignore']  # ignore=1の場合、タイミング次第では自分を入れずに探索する（正）
    dr_latest_n = figure_condition['latest_n']  # 2
    dr_oldest_n = figure_condition['oldest_n']  # 10 ⇒30
    max_return_ratio = figure_condition['return_ratio']
    # now_price = inspection_condition['now_price']

    # 各DFを解析
    latest_df = data_r[ignore: dr_latest_n + ignore]  # 直近のn個を取得
    oldest_df = data_r[dr_latest_n + ignore - 1: dr_latest_n + dr_oldest_n + ignore - 1]  # 前半と１行をラップさせる。
    latest_ans = turn_each_inspection(latest_df)  # 何連続で同じ方向に進んでいるか（直近-1まで）# Latestの期間を検証する(主に個のみ）
    oldest_ans_normal = turn_each_inspection(oldest_df)  # 何連続で同じ方向に進んでいるか（前半部分）# Oldestの期間を検証する（MAIN）
    oldest_ans = turn_each_inspection_skip(oldest_df)  # 何連続で同じ方向に進んでいるか（前半部分）# Oldestの期間を検証する（MAIN）

    # 表示用がメインの情報まとめ
    # print("  ", oldest_ans['oldest_time_jp'], latest_ans['latest_time_jp'], oldest_ans['oldest_price'],"@fig_ins")
    # print("  ", oldest_ans_normal['oldest_time_jp'], latest_ans['latest_time_jp'], oldest_ans_normal['oldest_price'], "@fig_ins")
    memo_time = classOanda.str_to_time_hms(oldest_ans['oldest_time_jp']) + "_" + \
                classOanda.str_to_time_hms(oldest_ans['latest_time_jp']) + "_" + \
                classOanda.str_to_time_hms(latest_ans['latest_time_jp'])
    memo_price = "(" + str(oldest_ans['oldest_price']) + "_" + str(oldest_ans['latest_image_price']) + \
                 "_" + str(latest_ans['latest_price']) + "," + str(oldest_ans['direction'])
    # memo_time = memo_time + classOanda.str_to_time_hms(oldest_ans_normal['oldest_time_jp']) + "_" + \
    #             classOanda.str_to_time_hms(latest_ans['latest_time_jp'])
    memo_all = memo_time + memo_price

    # 初期値があった方がいいもの（エラー対策）
    return_ratio = 0
    # 判定処理
    if latest_ans['direction'] != oldest_ans['direction']:  # 違う方向だった場合 (想定ケース）
        if latest_ans['count'] == latest_ans['data_size'] and oldest_ans['count'] >= 3:  # 行数確認(old区間はt直接指定！）
            # 戻しのパーセンテージを確認
            return_ratio = round((latest_ans['gap_close'] / oldest_ans['gap']) * 100, 3)
            print("  return_ratio", return_ratio, latest_ans['gap_close'], oldest_ans['gap'])
            if return_ratio < max_return_ratio:
                if oldest_ans['gap'] > 0.08:
                    turn_ans = 1  # 達成
                    memo = "★達成"
                else:
                    turn_ans = 0
                    memo = "Old小未達" + str(oldest_ans['gap'])
            else:
                turn_ans = 0  # 未達
                memo = "戻大" + str(return_ratio)
        else:
            turn_ans = 0  # 未達
            memo = "カウント未達 latest" + str(latest_ans['count']) + "," + str(oldest_ans['count'])
    else:
        turn_ans = 0  # 未達
        memo = "同方向"

    memo_info = " \n   @戻り率" + str(return_ratio) + ",向き(old):" + str(oldest_ans['direction']) + ",縦幅(old):" + str(oldest_ans['gap'])
    memo_info = memo_info + ",Body平均Old-Late:" + str(oldest_ans['body_ave']) + "," +str(latest_ans['body_ave'])
    memo_all = memo_all + memo_info + "," + memo
    print("   ", memo_all)

    return{
        "oldest_ans": oldest_ans,
        "latest_ans": latest_ans,
        "memo_all": memo_all,
        "return_ratio": return_ratio,
        "turn_peak": latest_ans["oldest_image_price"],  # ターンの底値（
        "turn_peak_bigin": oldest_ans['oldest_image_price'],  # ターン開始の価格
        "turn_ans": turn_ans
    }


def turn2_cal(inspection_condition):
    # 直近のデータの確認　LatestとOldestの関係性を検証する
    turn_ans_dic = turn_merge_inspection(inspection_condition)  # ★★引数順注意。ポジ用の価格情報取得（０は取得無し）
    oldest_ans = turn_ans_dic['oldest_ans']
    latest_ans = turn_ans_dic['latest_ans']
    turn_ans = turn_ans_dic['turn_ans']
    return_ratio = turn_ans_dic['return_ratio']
    memo_all = turn_ans_dic['memo_all']

    # 結果をもとに、価格を決定していく
    oa = classOanda.Oanda(tk.accountIDl, tk.access_tokenl, tk.environmentl)  # ★environmentl現在価格の取得
    now_price = oa.NowPrice_exe("USD_JPY")['data']['mid']  # ★現在価格の取得
    print("  nowPrice", now_price)

    # 注文情報を算出する
    main = {}  # 初期値を入れておく
    junc = {}  # 初期値を入れておく
    if turn_ans != 0:
        # ★注文（基準情報の収集）
        # （１）順思想の値の計算
        # ① 方向の設定
        trend_d = latest_ans['direction'] * -1
        # ②　margin候補1
        at_least_margin = 0.018  # 最低でも0.2を確保する
        margin_pattern1 = g.cal_at_least_most(at_least_margin, latest_ans['body_ave'] / 0.7, 0.05)  # 最低でも2.5pipsを確保する
        # margin候補2　同方向二つの場合、最低でも、最新のボディ分は戻る可能性を見る
        data = latest_ans['data']
        if data.iloc[1]['body'] >= 0 and data.iloc[0]['body'] >= 0:
            margin_pattern2 = data.iloc[1]['body_abs'] + 0.005  # 直近のBody分を取得する
            # tk.line_send("■たて 1 0 /", data.iloc[1]['body'], data.iloc[0]['body'])
        elif data.iloc[1]['body'] <= 0 and data.iloc[0]['body'] <= 0:
            margin_pattern2 = data.iloc[1]['body_abs'] + 0.005
            # tk.line_send("■した 1 0 /", data.iloc[1]['body'], data.iloc[0]['body'])
        else:
            margin_pattern2 = 0
        # marginの決定(基本はmargin_pattern2 だが、margin_pattern1[latestが２連続同方向の場合]がある場合は大きな方を取得する
        if margin_pattern2 == 0:  # 直近２つが同方向ではない場合
            margin_abs = margin_pattern1  # 基本的なmarginを利用
        else:
            if margin_pattern1 > margin_pattern2:  # 基本の方が大きい場合、基本を採択
                margin_abs = margin_pattern1
            else:
                margin_abs = margin_pattern2

        # ③ base price(システム利用値) & target price(参考値=システム不使用)の調整
        if latest_ans['gap'] >= 0.06:  # Gapが意外と大
            base_price = latest_ans['latest_price']  # ベースとなる価格を取得
        else:
            base_price = latest_ans['latest_price']  # ベースとなる価格を取得
        target_price = round(base_price + margin_abs * trend_d, 3)  # target_priceを念のために取得しておく

        # ④　LC_rangeの検討
        max_range_abs = oldest_ans['gap']  # 一番の理想はoldestのGap。ただ大きすぎる場合も。。
        middle_range_abs = oldest_ans['gap'] * 0.6  #  0.15  # 現実的にはこのくらい？
        min_range_abs = 0.06  # 最低でもこのくらい。
        lc_range_abs = g.cal_at_most(0.12, middle_range_abs)

        # ⑤ TP_rangeの検討
        tp_range_abs = 0.050

        # ⑥ 格納
        main = {  # 順思想（この以下の過程で、LCやMarginに方向を持たせる）（oldest方向同方向へのオーダー）今３００００の方
            "name": "順思想",
            "base_price": base_price,
            "target_price": target_price,  # 基本渡した先では使わない
            "margin": round(margin_abs * trend_d, 3),  # BasePriceに足せばいい数字（方向もあっている）
            "direction": trend_d,
            "type": "STOP",
            "lc_range": round(lc_range_abs * trend_d * -1, 3),
            "tp_range": round(tp_range_abs * trend_d, 3),
            "units": 40,
            "max_lc_range": max_range_abs * trend_d * -1,  # 最大LCの許容値（LCとイコールの場合もあり）
            "trigger": "ターン",
            "memo": memo_all,
            'data': turn_ans_dic
        }

        # （2）逆思想(range)の値の計算
        # ① 方向の設定
        range_d = latest_ans['direction']  # 方向（Tpとmarginの方向。LCの場合は*-1が必要）

        # ②marginの検討
        at_least_margin2 = 0.02
        if oldest_ans['gap'] > 0.15:
            margin2 = g.cal_at_least_most(at_least_margin2, oldest_ans['body_ave'] / 0.7, 0.05)
        else:
            margin2 = g.cal_at_least_most(at_least_margin2, oldest_ans['body_ave'] / 0.7, 0.05)

        # ③ base price(システム利用値) & target price(参考値=システム不使用)の調整
        # パターン１
        # if latest_ans['gap'] >= 0.06:  # Gapが意外と大きい場合、
        #     base_price2 = latest_ans['latest_price']  # 直近価格を利用する
        # else:
        #     base_price2 = latest_ans['latest_price']
        # target_price2 = round(base_price + (margin2 * trend_d), 3)  # target_priceを念のために取得しておく
        # パターン２
        if oldest_ans['gap'] >= 0.10:  # レンジを取るにはこのくらいほしい。。
            # 6割戻しタイミングに設置する
            remain_pips = oldest_ans['gap'] * 0.5  # 4割分の幅を計算
            base_price2 = oldest_ans['oldest_image_price'] + (remain_pips * oldest_ans['direction'])  # 頂点から４割戻り
            print(" 4割戻りレンジ")
        else:
            # 小さい場合は、Oldのピーク部分に設定する
            base_price2 = oldest_ans['oldest_image_price']
            print(" 頂上レンジ")
        target_price2 = round(base_price + (margin2 * trend_d), 3)  # target_priceを念のために取得しておく

        # ④　LC_rangeの検討
        cal_lc = abs(target_price2 - oldest_ans['latest_image_price'])  # ピークまで戻ったらLC
        max_range2_abs = oldest_ans['gap']  # 一番の理想はoldestのGap。ただ大きすぎる場合も。。
        middle_range2_abs = oldest_ans['gap'] * 0.6   #0.06  # 現実的にはこのくらい？
        min_range2_abs = 0.06  # 最低でもこのくらい。
        lc_range2_abs = g.cal_at_most(0.13, cal_lc)  # middle_range_abs

        # ⑤ TP_rangeの検討
        tp_range2_abs = 0.050

        # ⑥　格納
        junc = {
            "name": "レンジ",
            "base_price": base_price2,
            "target_price": target_price2,  # 基本渡した先では使わない
            "margin": round(margin2 * range_d, 3),  # BasePriceに足せばいい数字（方向もあっている）
            "direction": range_d,
            "type": "STOP",
            "lc_range": round(lc_range2_abs * range_d * -1, 3),
            "tp_range": round(tp_range2_abs * range_d, 3),
            "units": 40,
            "max_lc_range": max_range2_abs * range_d * -1,  # round(lc_range2 * range_d * -1, 3)  # 最大LCの許容値（LCとイコールになる場合もあり）
            "trigger": "ターン",
            "memo": memo_all,
            "data": turn_ans_dic
        }

    # (３)返却用データの作成
    ans_dic = {
        "turn_ans": turn_ans,  # 結果として、ターン認定されるかどうか
        "latest_ans": latest_ans,  # oldest部分の情報
        "oldest_ans": oldest_ans,  # latest部分の詳細
        "return_ratio": return_ratio,
        "memo_all": memo_all,
        "to_half_percent": round(50 - return_ratio),
        "order_dic": {
            "main": main,
            "junc": junc,
        }
    }

    # Return
    return ans_dic


def turnNotReached(ins_condition):
    # 最初の１行は無視する（現在の行の為）
    data_r_all = ins_condition['data_r']
    ignore = ins_condition['turn_2']['ignore']
    data_r = data_r_all[ignore:]  # 最初の１行は無視

    # 下らないエラー対策
    if data_r.iloc[2]['body'] == 0:
        oldest_body_temp = 0.0000001
    else:
        oldest_body_temp = data_r.iloc[2]['body']

    if data_r.iloc[1]['body'] == 0:
        middle_body_temp = 0.0000001
    else:
        middle_body_temp = data_r.iloc[1]['body']

    if data_r.iloc[0]['body'] == 0:
        latest_body_temp = 0.0000001
    else:
        latest_body_temp = data_r.iloc[0]['body']

    # gapサイズを求める（小さい最場合は無効にするため）
    gap = round(data_r.iloc[2]['body_abs'] + data_r.iloc[1]['body_abs'], 3)

    oldest = round(oldest_body_temp, 3)
    oldest_d = oldest_body_temp / abs(oldest_body_temp)
    middle = round(middle_body_temp, 3)
    middle_d = middle_body_temp / abs(middle_body_temp)
    latest = round(latest_body_temp, 3)
    latest_d = latest_body_temp / abs(latest_body_temp)
    older_line = 0.01
    later_line = 0.006
    if middle == 0:
        middle = 0.0000001

    # print(oldest, oldest_d, middle, middle_d, latest, latest_d)
    # 三つの方向が形式にあっているか（↑↑↓か、↓↓↑）を確認
    if (oldest_d == middle_d) and oldest_d != latest_d:
        d = 1
    else:
        d = 0

    if abs(oldest) > older_line and abs(middle) > older_line and abs(latest) < abs(middle):  # どっちも5pips以上で同方向
        p = 1
    else:
        p = 0

    if 0.2 <= oldest / middle <= 3.5:
        r = 1
    else:
        r = 0

    # 方向によるマージン等の修正に利用する
    if oldest_d == 1:  # old部分が上昇方向の場合
        margin = 1
    else:
        margin = -1

    if d == 1 and p == 1 and r == 1:
        if gap <= 0.08:
            res_memo = "Trun未遂形状〇サイズ×"
            print(" Trun未遂形状　ただしGap小 gap= ", gap)
            latest3_figure = 0
            order = {
                "base_price": 0,
                "direction": 0,
                "margin": 0.008 * oldest_d,
                "units": 20,
                "lc": 0.035,
                "tp": 0.075,
                "max_lc_range": 0.05,
                "trigger": "ターン未遂",
                "memo": " "
            }
        else:
            # print("   完全 dpr⇒", d, p, r)
            res_memo = "Trun未遂達成"
            latest3_figure = 1
            order = {
                "name": "ターン未遂",
                "base_price": data_r.iloc[0]['open'],
                "target_price": 0,
                "margin": round(0.008 * oldest_d, 3),  # 方向をもつ
                "direction": oldest_d,
                "type": "STOP",
                "units": 20,
                "lc_range": round(0.035 * oldest_d * -1, 3),
                "tp_range": round(0.075 * oldest_d, 3),
                "max_lc_range": 0.05,
                "trigger": "ターン未遂",
                "memo": " "
            }
    else:
        res_memo = "Trun未遂未達"
        latest3_figure = 0
        order = {
            "base_price": 0,
            "direction": 0,
            "margin": 0.008 * oldest_d,
            "units": 200
        }
        # print("   未達成 dpr⇒", d, p, r)
    memo0 = "Oldest" + str(data_r.iloc[2]['time_jp']) + "," + str(data_r.iloc[0]['time_jp'])
    memo1 = " ,Dir:" + str(oldest_d) + str(middle_d) + str(latest_d)
    memo2 = " ,Body:" + str(oldest) + str(middle) + str(latest)
    memo3 = " ,body率" + str(round(oldest / middle, 1))
    memo4 = ", TargetPrice:" + str(order['base_price'])
    memo5 = "結果dir,pip,ratio:" + str(d) + str(p) + str(r)
    memo_all = "  " + res_memo + memo4 + memo1 + memo2 + memo3 + memo4 + memo5
    print(memo_all)

    return {"result": latest3_figure, "order_dic": order, "memo": memo_all}


def inspection_candle(ins_condition):
    """
    オーダーを発行するかどうかの判断。オーダーを発行する場合、オーダーの情報も返却する
    inspection_condition:探索条件を辞書形式（ignore:無視する直近足数,latest_n:直近とみなす足数)
    """
    #条件（引数）の取得
    data_r = ins_condition['data_r']

    # ■直近ターンの形状（２戻し）の解析
    turn2_ans = turn2_cal(ins_condition['turn_2'])

    # ■ターン未遂の判定
    turnNotReached_ans = turnNotReached(ins_condition)

    # ■■■■上記内容から、Positionの取得可否を判断する■■■■
    if turn2_ans['turn_ans'] == 1:  # 条件を満たす(購入許可タイミング）
        ans = 1
    else:
        ans = 0

    return {"judgment": ans,  # judeentは必須（planで利用する。とりあえず
            "turn2_ans": turn2_ans,
            "latest3_figure_result": turnNotReached_ans,
            }



