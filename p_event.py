# -*- coding: utf-8 -*-

"""
Created on Wed Dec  9 22:54:10 2020
@author: Yu-ri
"""

import datetime
from threading import Lock
from time import time as float_time

import data
import window


class Event():
    """
    イベントクラス。
    役割としては、
    １．ウィンドウで発生したイベントを受け取り、ステータスを変更してWindowDataに書きこむこと、
    ２．Windowクラス全体に対して、画面表示の更新を命令すること
    の二つ。
    これら以外の処理は基本的にWindowクラス側で行う
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
        self._ev_lock = Lock()
        self.rec = data.Record()
        self._get_other_singleton_class_instance()
        self._recent_event_time=0
    
    def _get_other_singleton_class_instance(self):
        self.windata = data.WindowData.get_instance()
        self.win_instance = dict()
        self.win_instance["init"]     = window.InitWindow.get_instance()
        self.win_instance["idle"]     = window.IdleWindow.get_instance()
        self.win_instance["timer"]    = window.TimerWindow.get_instance()
        self.win_instance["task_fin"] = window.TaskFinishWindow.get_instance()
        self.win_instance["rest_fin"] = window.RestFinishWindow.get_instance()
        self.win_instance["task_sw"]  = window.TaskSwitchWindow.get_instance()


    
    def __lock_checker(func):
        """
        以下、イベントロック用の関数
        2つ以上のイベントを同時に発生させないため、lock-releaseで予防する。
        この__lock_checker関数を各イベントのデコレータとして使用する。
        """
        #i しかし、Tkinterは非同期ではないため、実質的にボタンの連続押下禁止のみを行っている。
        
        def inner(self, *args, **kwargs):
            wait_release = kwargs.get("wait_release")
            block_succession_event = kwargs.get("allow_succession_event")
            #指定があった場合、前イベント発生可能になるまで待ち続ける
            if type(wait_release)=="bool" and wait_release==True:
                event_key = self._ev_lock.acquire(blocking=True)
            else:
                #前のイベントから0.5秒以内なら、即リターン
                passed_time = float_time() - self._recent_event_time
                if passed_time < 0.5:
                    return
                event_key = self._ev_lock.acquire(blocking=False)
            
            #以下、イベントコマンドの実施
            if event_key==True:
                try:
                    self._recent_event_time = float_time()
                    func(*args, **kwargs)
                finally:
                    self._ev_lock.release()
            return event_key
        return inner
    
    
    ###ステートを更新し、すべてのウィンドウに更新の指令を出す。
    def _update_windows(self, next_state, forced_fin=False):
        self.windata.preview_state = self.windata.state
        self.windata.state = next_state
        print(next_state)
        window.Window.update_all_windows()
    
        
    ###タスク情報をcsvに保存する関数。2通りのデータを扱う
    def _record_task_info(self, is_taskdata=True):
        if is_taskdata:
            remain_sec = self.windata.task_data.get_duty_time()
            if self.windata.state in ["TASK_FIN","SWITCH"]:
                tor             = "作業"
            elif self.windata.state in ["REST_FIN"]:
                tor             = "休憩"
            else:
                raise RuntimeError("レコードを呼び出せるっステータスではありません")
            self.rec.add_row({
                    "日時"         :self.windata.task_data.start_datetime,
                    "作業/休憩"    :tor,
                    "タスク名"       :self.windata.task_data.name,
                    "サブタスク名"      :self.windata.task_data.subname,
                    "タグ名"          :self.windata.task_data.tag,
                    "所要時間"     :remain_sec,
                    "集中度"       :self.windata.task_data.concentrate,
                    "進捗率"       :self.windata.task_data.progress,
                    "気散回数"     :self.windata.task_data.distracted,
                    "Switched"    :self.windata.task_data.switched,
                    "Stopped"     :self.windata.task_data.stopped,
                    "メモ"          :self.windata.task_data.memo
                }
            )
        else:
            self.rec.add_row({
                    "日時"         :datetime.date.today(),
                    "睡眠時間"      :self.windata.task_data.sleep_time,
                    "朝食"         :self.windata.task_data.have_breakfast,
                    "メモ"          :self.windata.task_data.dayly_memo
                },
                data_type="dayinfo"
            )
            
        
        
    """
    MainWindowからのイベント
    """
    @__lock_checker
    def m_work_start(self):
        if self.windata.state == "MAIN":
            if self.rec._today_already_worked()==False:
                #今日初めての起動なら、日時情報を格納する。
                self._update_windows("INIT");
            else:
                self._update_windows("IDLE");
        else:
            self._update_windows("MAIN")
    
    @__lock_checker
    def m_analysis(self):
        if self.windata.state == "MAIN":
            self._update_windows("ANALYSIS")
        else:
            self._update_windows("MAIN");
        
        
    """
    InitWindowからのイベント
    """    
    @__lock_checker
    def ini_work_start(self):
        self.win_instance["init"].save_params_to_sharememory()
        self._record_task_info(is_taskdata=False)
        self._update_windows("IDLE")
    
    @__lock_checker
    def ini_home(self):
        self._update_windows("MAIN")
    
    
    
    """
    IdleWindowからのイベント
    """
    @__lock_checker
    def i_timer_start(self):
        if self.windata.state == "IDLE":
            self.win_instance["idle"].save_params_to_sharememory()#パラメータ保存
            self.win_instance["timer"].set_params_from_sharememory()#ウィンドウ準備
            self._update_windows("TASK")
        else:
            self._update_windows("IDLE")
    
    @__lock_checker
    def i_fin_work(self):
        if self.windata.state == "IDLE":
            self._update_windows("MAIN")
        else:
            self._update_windows("IDLE")
    
    
    """
    AnalysisWindowからのイベント
    """
    @__lock_checker
    def a_go_home(self):
        if self.windata.state == "ANALYSIS":
            self._update_windows("MAIN")
        else:
            self._update_windows("MAIN")
    
    
    """
    TimerWindowからのイベント
    """
    @__lock_checker
    def tm_timeup(self, wait_release=True):
        self.win_instance["timer"].save_params_to_sharememory()#パラメータ保存
        next_status = self._next_status()
        if next_status == "TASK_FIN":
            self.win_instance["task_fin"].set_params_from_sharememory()#ウィンドウ準備
        elif next_status == "REST_FIN":
            self.win_instance["rest_fin"].set_params_from_sharememory()#ウィンドウ準備
        self._update_windows(next_status)
    
    @__lock_checker
    def tm_stop(self):
        if "_STOP" in self.windata.state:
            self._update_windows(self.windata.state.replace("_STOP",""))
        elif self.windata.state in ["TASK","REST","LONG_REST"]:
            self.windata.task_data.stopped += 1
            self._update_windows(self.windata.state+"_STOP")
        else:
            self._update_windows("IDLE")
        
    @__lock_checker
    def tm_change_task(self):
        if self.windata.state == "TASK":
            self.win_instance["timer"].save_params_to_sharememory()
            self.win_instance["task_sw"].set_params_from_sharememory()
            self._update_windows("SWITCH")

    @__lock_checker
    def tm_got_distracted(self):
        self.windata.task_data.distracted += 1

    @__lock_checker
    def tm_force_fin(self):
        self.win_instance["timer"].save_params_to_sharememory()#パラメータ保存
        next_status = self._next_status()
        if next_status == "TASK_FIN":
            self.win_instance["task_fin"].set_params_from_sharememory()#ウィンドウ準備
        elif next_status == "REST_FIN":
            self.win_instance["rest_fin"].set_params_from_sharememory()#ウィンドウ準備
        self._update_windows(next_status)
        
    def _next_status(self):
        if self.windata.state in ["TASK","TASK_STOP"]:
            return "TASK_FIN"
        elif self.windata.state in ["REST","REST_STOP","LONG_REST","LONG_REST_STOP"]:
            return "REST_FIN"
        else:
            return "IDLE"
            

    """
    タスクfinウィンドウからのイベント
    タスクが終わって各種情報を入力したので、ここでデータ保存する。
    """
    @__lock_checker
    def tf_rest(self):
        self.win_instance["task_fin"].save_params_to_sharememory()
        self._record_task_info()
        self.windata.task_backup()#直前のタスクデータを保存
        self.windata.set_rest_time()
        self.win_instance["timer"].set_params_from_sharememory()#windataの情報をWindowに反映(ウィンドウ準備)
        self._update_windows("REST")

    @__lock_checker
    def tf_long_rest(self):
        self.win_instance["task_fin"].save_params_to_sharememory()#Windowの情報を、Windataに格納する(入力値反映)
        self._record_task_info()
        self.windata.ta = self.windata.task_data#直前のタスクデータを保存
        self.windata.set_long_rest_time()
        self.win_instance["timer"].set_params_from_sharememory()#windataの情報をWindowに反映(ウィンドウ準備)
        self._update_windows("LONG_REST")

    @__lock_checker
    def tf_fin(self):
        self.win_instance["task_fin"].save_params_to_sharememory()#Windowの情報を、Windataに格納する(入力値反映)
        self._record_task_info()
        self.windata.task_backup()#直前のタスクデータを、Preview_Taskに保存
        self.win_instance["idle"].set_params_from_sharememory()#windataの情報をWindowに反映(ウィンドウ準備)
        self._update_windows("IDLE")
    
    @__lock_checker
    def tf_non_record_fin(self):
        self._update_windows("IDLE")
        

    """
    レストfinウィンドウからのイベント
    休憩が終わって各種データがそろってから、データ保存をする。
    """
    @__lock_checker
    def rf_timer_start(self):
        self._record_task_info()#休憩を記録
        self.win_instance["rest_fin"].save_params_to_sharememory()#Windowの情報を、Windataに格納する(入力値反映)
        self.win_instance["timer"].set_params_from_sharememory()#windataの情報をWindowに反映(ウィンドウ準備)
        self.windata.task_data.distracted=0
        self._update_windows("TASK")

    @__lock_checker
    def rf_fin(self):
        self._record_task_info()#休憩を記録
        self.win_instance["idle"].set_params_from_sharememory()#ウィンドウ準備
        self._update_windows("IDLE")
        
    """
    タスクSwitchウィンドウからのイベント
    """
    @__lock_checker
    def ts_resume(self):
        next_state = self.windata.preview_state
        self.windata.preview_state = "SWITCH"
        self._update_windows(next_state)

    @__lock_checker
    def ts_switch_start(self):
        self._record_task_info()#これまでのタスクを記録
        self.win_instance["task_sw"].save_params_to_sharememory()#Windowの情報を、Windataに格納する(入力値反映)
        self.win_instance["timer"].set_params_from_sharememory()#windataの情報をWindowに反映(ウィンドウ準備)
        next_state = self.windata.preview_state
        self._update_windows(next_state)
        
        
        