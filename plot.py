# -*- coding: utf-8 -*-
"""
Created on Fri Oct  1 15:19:13 2021

@author: Yu-ri
"""

###使命
#与えられたキーワードに対応したグラフを作成
#グラフのインスタンス(fig)を返却する
#
import datetime
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import pandas as pd

class Plot:
    """AnalysisWindowに置ける、グラフの描画を担当する"""
    
    #現在実装されているグラフ描画モードは2つ。
    validate_mode = ("sleep_time-concentrate", "hour-distracted")

    def __init__(self):
        #csvファイルの読み出し
        self.pd_data = pd.read_csv("data\data_test.csv", encoding="utf_8_sig")
        self.pd_dayly_data = pd.read_csv("data\dayinfo_test.csv", encoding="utf_8_sig")
        #日時情報をdatetimeおよびdate型に変換
        self.pd_data["日時"]       = pd.to_datetime(self.pd_data["日時"]) 
        self.pd_dayly_data["日時"] = pd.to_datetime(self.pd_dayly_data["日時"])
        self.pd_dayly_data["日時"] = self.pd_dayly_data.apply(lambda x: x["日時"].date(), axis=1)

    def get_fig(self, glaph_mode):
        """描画モードを指定して、それに応じたFigureのオブジェクトを返す。"""
        fig = Figure()
        ax = fig.add_subplot(111)
        plot_data = {"x":[], "y":[]}
        ## 睡眠時間と集中力のグラフを作成
        if glaph_mode=="sleep_time-concentrate":
            #以下4行、睡眠時間の最小～最大まで
            maximam_sleep_time = self.pd_dayly_data["睡眠時間"].max()
            minimam_sleep_time = self.pd_dayly_data["睡眠時間"].min()
            stime_list_x2 = list(range(int(minimam_sleep_time*2), int(maximam_sleep_time*2)+1))
            stime_list = list(map(lambda x: x/2, stime_list_x2))
            ave=0
            for stime in stime_list:
                #指定の睡眠時間のデータ列を取得
                st_rows = self.pd_dayly_data[self.pd_dayly_data["睡眠時間"]==stime]
                value_sum = 0
                len_sum = 0
                for date_ in st_rows["日時"]:
                    #タスクデータから、作業時のみ抜き出す
                    data_x1 = self.pd_data[self.pd_data["作業/休憩"]=="作業"]
                    #該当する日付を抽出（エラーで「コピーしてんぞ」と言われるので、回りくどい処理してる）
                    data_x2 = data_x1.copy()
                    a = data_x1["日時"].map(lambda x: x.date()).copy()
                    data_x2["日時"] = a
                    data_x3 = data_x2[data_x2["日時"]==date_]
                    concentraet_list = data_x3["集中度"]
                    value_sum += sum(concentraet_list)
                    len_sum += len(concentraet_list)
                if len_sum==0:
                    continue
                ave = value_sum/len_sum
                plot_data["x"].append(stime)
                plot_data["y"].append(ave)
            #棒グラフを描画
            ax.bar(plot_data["x"], plot_data["y"], width=0.2)
            ax.set_title("睡眠時間-集中力 のグラフ", fontname="MS Gothic")
            ax.set_xlabel("睡眠時間[h]", fontname="MS Gothic")
            ax.set_ylabel("集中度の平均", fontname="MS Gothic")

        ## 時刻と気が散る回数のグラフを描画。朝食の有無も評価に入れる
        elif glaph_mode=="hour-distracted":
            plot_data_bf = {"x":[], "y":[]}#bf...break fast
            plot_data_nbf = {"x":[], "y":[]}#nbf...non break fast
            #朝食ありの日と無しの日で日付リストを作成
            date_with_bf = []
            date_with_nbf=[]
            for index, row in self.pd_dayly_data.iterrows():
                if row["朝食"]==1:
                    date_with_bf.append(row["日時"])
                else:
                    date_with_nbf.append(row["日時"])
                
            #作業時のみ抜き出す
            data_task = self.pd_data[self.pd_data["作業/休憩"]=="作業"]
            #計算用に、列を1つ追加し、日時が一致している列のみを取り出す
            day_row = data_task["日時"].copy()
            day_row = day_row.apply(lambda x: x.date())
            data_task = data_task.assign(日 = day_row)
            data_task_with_bf = data_task[data_task["日"].isin(date_with_bf)]
            data_task_with_nbf = data_task[data_task["日"].isin(date_with_nbf)]
            #時間(hour)と気が散った回数のみを、新しいデータフレームとして作成
            pd_hour_distructed_with_bf = pd.DataFrame({
                "hour":map(lambda series: series.hour, data_task_with_bf["日時"]),
                "distructed":data_task_with_bf["気散回数"]
                })
            pd_hour_distructed_with_nbf = pd.DataFrame({
                "hour":map(lambda series: series.hour, data_task_with_nbf["日時"]),
                "distructed":data_task_with_nbf["気散回数"]
                })
            #タスク開始時間の、最大値と最小値を取得する
            maximam_hour_1 = max(pd_hour_distructed_with_bf["hour"])
            maximam_hour_2 = max(pd_hour_distructed_with_nbf["hour"])
            maximam_hour = max(maximam_hour_1, maximam_hour_2)
            minimam_hour_1 = min(pd_hour_distructed_with_bf["hour"])
            minimam_hour_2 = min(pd_hour_distructed_with_nbf["hour"])
            minimam_hour = min(minimam_hour_1, minimam_hour_2)
            
            hour = minimam_hour
            while hour <= maximam_hour:#最小時間⇒最大時間まで計算
                #朝食ありの時
                df_with_bf = pd_hour_distructed_with_bf[pd_hour_distructed_with_bf["hour"]==hour]
                if len(df_with_bf)==0:
                    hour+=1
                    pass
                else:
                    value_sum = sum(df_with_bf["distructed"])
                    len_sum = len(df_with_bf["hour"])
                    ave = value_sum/len_sum
                    plot_data_bf["x"].append(str(hour))#+"-"+str(hour+1))
                    plot_data_bf["y"].append(ave)
                #朝食なしの時
                df_with_nbf = pd_hour_distructed_with_nbf[pd_hour_distructed_with_nbf["hour"]==hour]
                if len(df_with_bf)==0:
                    hour+=1
                    pass
                else:
                    value_sum = sum(df_with_nbf["distructed"])
                    len_sum = len(df_with_nbf["hour"])
                    ave = value_sum/len_sum
                    plot_data_nbf["x"].append(str(hour))#+"-"+str(hour+1))
                    plot_data_nbf["y"].append(ave)
                hour+=1
            
            ## 折れ線グラフを描画
            axis_bottom_bf  = max(min(plot_data_bf["y"])-0.5, 0)#0より小さくしない
            axis_bottom_nbf = max(min(plot_data_nbf["y"])-0.5, 0)#0より小さくしない
            axis_bottom     = min(axis_bottom_bf, axis_bottom_nbf)
            axis_top_bf     = max(plot_data_bf["y"])+0.5
            axis_top_nbf    = max(plot_data_nbf["y"])+0.5
            axis_top        = max(axis_top_bf, axis_top_nbf)
            ax.plot(plot_data_bf["x"], plot_data_bf["y"], color="red", label="朝食あり")
            ax.plot(plot_data_nbf["x"], plot_data_nbf["y"], color="blue", label="朝食なし")
            ax.legend(loc=0, prop={'family':'Yu Gothic'})
            ax.set_ylim(axis_bottom, axis_top)
            ax.set_title("時刻-気が散った回数 のグラフ", fontname="MS Gothic")
            ax.set_xlabel("時刻", fontname="MS Gothic")
            ax.set_ylabel("気が散った回数の平均[回]", fontname="MS Gothic")
        
        else:
            raise RuntimeError("許容されていないテーブルキーワード")
        
        return fig #Figureのインスタンスを返す。これをCanvasに塗りつければいい。
        
        

if __name__ == "__main__":
    p = Plot()
    fig = p.get_fig("hour-distracted")
    #fig.show()
        
        
    
    