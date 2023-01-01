#### よく使う基本公文のまとめ


import threading  # 定時実行用
import time
import datetime
import sys
import pandas as pd
import ast
import numpy as np

#####エクセルの読み込み
rescsv_path = tk.folder_path + 'test.xlsb.csv'
mid_df = pd.read_csv(rescsv_path, sep=",", encoding="utf-8")

#####エクセルの吐き出し
mid_df.to_csv(tk.folder_path + 'mid_df.csv', index=False, encoding="utf-8")

#### indexを取得する
pv_df.index  # データフレームの場合(リスト形式で取得）
pd.Series(data=peak_sr.index)  # シリーズの場合、シリーズでインデックスを作成する
p_df.index.values  # 結果をNumpy.arrayで取得する
p_df['ind_diff'] = pd.Series(data=pd.Series(p_df.index.values).diff(-1).values, index=p_df.index)  # index差（大変!?）


#####インデックスの取得
pv_latest_index = pv_r_df.index.values[0]  # 直近の極値のインデックス

#####データフレームループ
for index, item in mid_df.iterrows():　# ★★★indexは、データが連番でない場合、連番ではないことに注意！！
    arr = ast.literal_eval(item['datas'])]

# データフレーム　列削除
    data_df.drop(['mid'], axis=1, inplace=True)

# データフレームに項目があれば
for target in targets:  # 対象を削除する
    if　target in df:

#空欄の判定
math.isnan()　　#Nanの場合

# 文字列を日付に変更する
datetime.datetime.strptime(now_cross5_time, '%Y/%m/%d %H:%M:%S')
# 日付の差分を求める



# ループでのDataFrameの中の書き換え
for index, data in both_df.iterrows():
    both_df.iloc[0とか1とか]['こうもくめい'] = -1  # ilocはインデックス番号でしてい（0,1,2,3,の連番）
    both_df.loc[index,'high'] = 1  # locはインデックスで指定（indexが飛び版の時はこちらを利用） ★ループ中に書き込むときはこっちじゃないとWarning出る！

# データフレームのNan以外を抽出する
peak_only_df = mid_df[mid_df['4peak_b0'].notna()]  # 空欄以外を抽出（フィルタ）

#####データフレーム内の指定個所の値を取得する
mid_df.head(1).iloc[0]["order_time_jp"]  # オーダーした時刻

##### はんいの最大値、最小値
efore5_cross_df["high"].max()


#####データフレームのインデックスを振りなおす
ins_range = ins_range.reset_index()  # indexを再振り分け（降順にして受け取る関係で、インデックスがおかしい）

# dataFrame並び替え
reverse_latest_peak_df = latest_peak_df.sort_index(ascending=False)

#####データフレームへの列追加（関数呼び出し）
res_df['order_time_jp'] = res_df.apply(lambda x: iso_to_jstdt(x, 'createTime'), axis=1)  # 日本時刻の表示
def iso_to_jstdt(x, colname):  # ISO8601→JST変換関数 従来の引数⇒iso_to_jstdt(iso_str)
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

data_df['low_rod'] = data_df.apply(lambda x: for_lower(x), axis=1)
def for_lower(self, x):
    if x.body > 0:
        return (x.open - x.low)
    else:
        return (x.close - x.low)


##### 配列（文字列）を配列に変換
ast.literal_eval("文字列配列")

