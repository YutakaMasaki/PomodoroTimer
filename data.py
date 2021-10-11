# -*- coding: utf-8 -*-
"""
Created on Wed Dec  9 23:02:26 2020

@author: Yu-ri
"""

import pandas as pd
from os import path
from threading import Lock
import os
import shutil
import datetime


class Config():
    """
    設定を展開したクラス。
    """
    cfg_pd          = pd.read_csv("data/config.csv",index_col=0)
    cfg_pd2         = cfg_pd.fillna("")#欠損値を空白で埋める
    cfg             = cfg_pd2.to_dict()
    TASK_HOUR       = int(cfg["cfg_1"]["TASK_HOUR"])
    TASK_MIN        = int(cfg["cfg_1"]["TASK_MIN"])
    REST_HOUR       = int(cfg["cfg_1"]["REST_HOUR"])
    REST_MIN        = int(cfg["cfg_1"]["REST_MIN"])
    LONG_REST_HOUR  = int(cfg["cfg_1"]["LONG_REST_HOUR"])
    LONG_REST_MIN   = int(cfg["cfg_1"]["LONG_REST_MIN"])
    
    ###タスクタグの読み込み＆リスト化###
    TASK_TAGS = list()
    for num in range(0,10):
        if not cfg["cfg_1"]["TASK_TAGS_"+str(num)] == "":
            TASK_TAGS.append(cfg["cfg_1"]["TASK_TAGS_"+str(num)])

    
    RECORD_FOLDER_PATH = str(cfg["cfg_1"]["RECORD_FOLDER_PATH"])
    
    HOLD_TM_WINDOW_TOP = int(cfg["cfg_1"]["HOLD_TM_WINDOW_TOP"])
    DISPLY_TM_WINDOW_SEC = int(cfg["cfg_1"]["DISPLY_TM_WINDOW_SEC"])
    DISPLY_OTHER_WINDOW_SEC = int(cfg["cfg_1"]["DISPLY_OTHER_WINDOW_SEC"])
    
    
class Record():
    """
    作業内容をCSVに記録するクラス
    """
    def __init__(self):
        self.cfg = Config()
        self.daily_backup()#1日ごとにバックアップを作成
        self.task_filepath  = path.join(self.cfg.RECORD_FOLDER_PATH, "data\data.csv")
        self.dayinfo_filepath = path.join(self.cfg.RECORD_FOLDER_PATH, "data\dayinfo.csv")
    
    def add_row(self, data_dict, data_type="task"):
        """csvファイルに、1列分データを追加する関数"""
        if data_type == "task":
            filepath = self.task_filepath
            df = pd.read_csv(filepath, encoding="utf_8_sig")
            df_a = df.append({
                    "日時":data_dict["日時"],
                    "作業/休憩":data_dict["作業/休憩"],
                    "タスク名":data_dict["タスク名"],
                    "サブタスク名":data_dict["サブタスク名"],
                    "タグ名":data_dict["タグ名"],
                    "所要時間":data_dict["所要時間"],
                    "集中度":data_dict["集中度"],
                    "進捗率":data_dict["進捗率"],
                    "気散回数":data_dict["気散回数"],
                    "Switched":data_dict["Switched"],
                    "Stopped":data_dict["Stopped"],
                    "メモ":data_dict["メモ"].strip("\n")},
                    ignore_index=True)
            
        elif data_type == "dayinfo":
            filepath = self.dayinfo_filepath
            df = pd.read_csv(filepath, encoding="utf_8_sig")
            df_a = df.append({
                    "日時":data_dict["日時"],
                    "睡眠時間":data_dict["睡眠時間"],
                    "朝食":int(data_dict["朝食"]),
                    "メモ":data_dict["メモ"].strip("\n")},
                    ignore_index=True)
            
        
        ### 以下、ファイルのチェックと一時バックアップ処理。
        if not os.access(filepath, os.W_OK):
            raise FileNotFoundError()
        try:
            #元のファイルを一時コピー
            tmp_filepath = filepath.rstrip(".csv") + "_backup.csv"#一時コピー用
            shutil.copy(filepath, tmp_filepath)
            #ファイルを保存
            df_a.to_csv(filepath, encoding="utf_8_sig", index=False)
        except Exception as e:
           #エラーが起きた時、復元する
            os.remove(filepath)
            os.rename(tmp_filepath, filepath)
        else:
            df = df_a#メモリ上のファイルを更新
            os.remove(tmp_filepath)#一時コピーしたファイルを元に戻す
    
    
    def daily_backup(self):
        """アプリ立ち上げ時に、データをバックアップする処理"""
        try:
            if not path.isdir("backups"):
                os.mkdir("backups")
            dt = datetime.datetime.now()
            today_str = str(dt.year)+"_"+str(dt.month)+"_"+str(dt.day)
            backup_filename = self.task_filepath.rstrip(".csv") + today_str + ".csv"
            folder_name = "backups"
            backup_path = path.join(folder_name, backup_filename)
            #1日に1回しか起動させない。ファイルが既に存在していたら無視する。
            if path.isfile(backup_path):
                return
            shutil.copy(self.task_filepath, backup_filename)
            shutil.move(backup_filename, path.join(backup_path,""))
        except Exception as e:
            pass
            
    
    ### 今日、すでにタスクを保存していたかを確認する。
    def _today_already_worked(self):
        filepath = self.dayinfo_filepath
        df = pd.read_csv(filepath, encoding="utf_8_sig")
        if len(df.index)==0:
            return False
        latest_work = df.iloc[-1]["日時"]
        latest_work_date = pd.to_datetime(latest_work).date()
        
        now = datetime.date.today()
        if latest_work_date.day != now.day:
            return False
        elif latest_work_date.month != now.month:
            return False
        if latest_work_date.year != now.year:
            return False
        return True
            
    


class WindowData():
    """
    全体が共有する変数をまとめてあるクラス
    共有データ。
    """
    
    ##<< 以下、シングルトンの実装 >>##
    __singleton = None
    __lock = Lock()  # クラスロック   
    def __new__(cls,*args,**kargs):
        raise "このクラス'{}'のインスタンス化は、getinstance()でのみ行えます".format(str(__class__))
    
    @classmethod
    def get_instance(cls):
        with cls.__lock:
            if cls.__singleton == None:
                cls.__singleton = super().__new__(cls)
                cls.__singleton.__init__()
            return cls.__singleton
    ##<< シングルトン実装コード終了 >>##

    def __init__(self):
        self.state = "MAIN"
        self.preview_state = "None"
        self.__read_config()
        #タスク管理用のクラスをインスタンス
        self.preview_task = TaskParams(self.disply_tm_window_sec)
        self.task_data = TaskParams(self.disply_tm_window_sec)
        
    def __read_config(self):
        config = Config()
        #設定値を共有データとして、展開
        self.hold_tm_window_top = config.HOLD_TM_WINDOW_TOP
        self.disply_tm_window_sec = config.DISPLY_TM_WINDOW_SEC
        self.hold_other_window_top = config.DISPLY_OTHER_WINDOW_SEC
        self.TASK_TIME = {
            "hour":config.TASK_HOUR,
            "minute":config.TASK_MIN,
            "second":0}
        self.REST_TIME = {
            "hour":config.REST_HOUR,
            "minute":config.REST_MIN,
            "second":0}
        self.LONG_REST_TIME = {
            "hour":config.LONG_REST_HOUR,
            "minute":config.LONG_REST_MIN,
            "second":0}
        self.task_tags = config.TASK_TAGS
        
    def task_backup(self):
        #未使用
        self.preview_task = self.task_data
        
    def set_rest_time(self):
        self.task_data.hour   = self.REST_TIME["hour"]
        self.task_data.minute = self.REST_TIME["minute"]
        self.task_data.second = self.REST_TIME["second"]
        
    def set_long_rest_time(self):
        self.task_data.hour   = self.LONG_REST_TIME["hour"]
        self.task_data.minute = self.LONG_REST_TIME["minute"]
        self.task_data.second = self.LONG_REST_TIME["second"]

    

class TaskParams:
    """
    タスクに関する変数をまとめた、構造体的クラス。
    WindowDataの下に付く。
    """
    def __init__(self, disply_tm_window_sec):
        self.print_sec = disply_tm_window_sec
        ### 時分秒 合計時間の返還関数 ###
        self._hms_to_totalsec = lambda h,m,s: h*3600+m*60+s
        self._totalsec_to_hms = lambda rem:[rem//3600,(rem%3600)//60,((rem%3600)%60)%60]
        ### 初期化 ###
        self.initialize()
        
    def initialize(self):
        ###タスク情報###
        self.name=""
        self.subname=""
        self.tag=""
        self.memo=""
        self.hour=0
        self.minute=0
        self.second=0
        self.remain_sec=0
        self.distracted=0#気が散った
        self.progress=0#進捗
        self.concentrate=0#集中度
        self.switched = False#Switchウィンドウでタスクを切り替えた場合
        self.stopped = 0
        ###日ごとのデータ###
        self.sleep_time=7
        self.have_breakfast=False;
        self.dayly_memo = ""
        ###日付情報###
        self.start_datetime=datetime.datetime(2004,1,1)
        
    def get_duty_time(self):
        """タイマーがカウントした秒数、つまり働いた時間を返す"""
        total_sec = self.hour*3600 + self.minute*60 + self.second
        duty_sec = total_sec - self.remain_sec
        return duty_sec
    
    
    
#以下、テスト用
if __name__ == "__main__":
    #import datetime
    #d = datetime.datetime(2020,12,24,20,15,53)
    r = Record()
    r._today_already_worked()
    #add_dict = {
    #            "日時":d,
    #            "作業/休憩":"休憩",
    #            "タスク名":"ddd",
    #            "所要時間":90,
    #            "集中度":97,
    #            "進捗率":15,
    #            "メモ":"シャワー室がスケスケでした。"
    #    }
    #rd = Record()
    #rd.add_row(add_dict)

