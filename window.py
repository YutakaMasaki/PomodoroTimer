# -*- coding: utf-8 -*-
"""
Created on Wed Dec  9 22:55:59 2020

@author: Yu-ri
"""

import abc
import datetime
import tkinter as tk
import tkinter.scrolledtext as tkst
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Lock

import data
import p_event
import plot

class Window(metaclass = abc.ABCMeta):
    """
    全てのWubdiwの親クラス。
    シングルトンクラスのため、子クラスも全て、インスタンスは1つしか存在しない。
    """
    instance={}#子クラスのインスタンスへのアクセスを行うためのdict
    
    ##<< シングルトンの実装 >>##
    __singleton = None
    __lock = Lock()  # クラスロック
    def __new__(cls,*args,**kargs):
        raise "このクラス'{}'のインスタンス化は、get_instance()でのみ行えます".format(str(__class__))
    @classmethod
    def get_instance(cls, root=None):
        with cls.__lock:
            if cls.__singleton == None:
                if root==None:
                    raise RuntimeError("Windowのインスタンスエラー")
                cls.__singleton = super().__new__(cls)
                cls.__singleton.__init__(root)
            return cls.__singleton
    ##<< シングルトン実装コード終了 >>##
    
    def __init__(self, root):
        self.root = root#子クラスから直接rootＷｉｎｄｏｗにアクセスしたい時に使う。

    def create_window(self, DEBUG=False):
        ###Tkinterの登録###
        if self.TYPE=="MAIN":
            self.win = self.root
        else:
            self.win = tk.Toplevel(self.root)
            #右上の×を押してもウィンドウが削除されない。
            self.win.protocol('WM_DELETE_WINDOW', lambda :"pass")
        
        ## 必須インスタンスの用意
        self._vi = ValidateInput()
        self.windata = data.WindowData.get_instance()
        if DEBUG==False:
            self.ev = p_event.Event.get_instance()
        
        #ウィンドウの作成
        self._make_window()
        self._register_roster()
        if DEBUG == False:
            self._refresh()


    @abc.abstractmethod
    def _register_roster(self):
        """
        親クラスのクラス変数"instance"に、インスタンス化したウィンドウのクラスをまとめる作業。
        親クラスで実装してると、selfが親クラスを指すので、子クラスで走らせる必要がある。
        """
        #子クラスでは、コピーして↓のコードのコメント外すだけでＯＫ。
        #Window.instance[str(__class__.__name__)]=self
        pass
    
    @abc.abstractmethod
    def _make_window(self, win):
        pass
    
    @abc.abstractmethod
    def _prepare_variable(self):#Widget変数を定義する
        pass
    
    @abc.abstractmethod
    def save_params_to_sharememory(self):#Widget変数→共有データ　の方向にデータを書き込むコマンド
        pass
    
    @abc.abstractmethod
    def set_params_from_sharememory(self):#共有データ→Widget変数　の方向にデータを書き込むコマンド
        pass
    
    @classmethod
    def update_all_windows(*args, **kwargs):
        """全てのウィンドウで、ステータスと表示を更新"""
        for instance in Window.instance.values():
            instance._refresh()
    
    def _refresh(self):
        """Windowのステータスが変更されたのを、反映させる関数"""
        #1 自身が次に表示するべきウィンドウなら、表示して浮上させる。データのアップデートも行う。
        if self.windata.state in self.SURVIVABLE_STATUS:
            self._window_update()
            self.win.deiconify()#表示させる
            self.win.lift()#最前面に移動させて固定
        #2 自身が直前まで表示されていたウィンドウなら、更新してから隠す
        elif self.windata.preview_state in self.SURVIVABLE_STATUS:
            self._window_update()
            self.win.withdraw()#ウィンドウを非表示にする
        #3 関係ないウィンドウは非表示
        else:
            self.win.withdraw()#ウィンドウを非表示にする
    
    def _window_update(self):
        """
        Window のステータスが更新される時の処理。
        必要に応じて子クラスで実装する
        """
        pass
    

class MainWindow(Window):
    """アプリ起動時に表示されるウィンドウ"""
    TYPE = "MAIN"
    SURVIVABLE_STATUS = ("MAIN",)
    def _make_window(self):
        self.win.title("PomTime")
        self.win.resizable(width=0, height=0)#画面の拡大縮小禁止
        self._prepare_variable()#Widget変数の定義
        self._make_widget()#ウィジェットの配置
        if self.windata.hold_tm_window_top == True:#configファイルで設定
            self.win.attributes("-topmost", True)#ウィンドウの固定
    
    
    ###Widget変数の定義###
    def _prepare_variable(self):
        pass
    
    ###ウィジェットの配置###
    def _make_widget(self):
        self.win.geometry("{}x{}".format(240,230))
        ###画像フレームの作成###
        global bg_img
        bg_img = tk.PhotoImage(file="img/tomato_red_s.png")
        bg = tk.Canvas(self.win)
        bg.pack()
        bg.create_image(120, 120, image=bg_img)
        ###テキスト素材###
        main_message = tk.Label(self.win, text="さあ、今日の仕事を始めましょう！")
        button_task = tk.Button(self.win, text="はたらく", bg="#6af")
        button_analysis = tk.Button(self.win, text="分析する", bg="#6f6")
        #button_config = tk.Button(self.win, text="コンフィグ", bg="#fa6")
        ###メインフレーム配置###
        main_message.place(x=40, y=5)#span=2で、grid2つ分を確保            
        button_task.place(x=98, y=90)
        button_analysis.place(x=95, y=120)
        ###イベントの設定###
        button_task.bind("<Button-1>",lambda event:self.ev.m_work_start(self.ev))#第一引数としてインスタンスを渡さなければ、呼び出した関数がselfを使えない
        button_analysis.bind("<Button-1>",lambda event:self.ev.m_analysis(self.ev))
        
    
    def _register_roster(self):
        Window.instance[str(__class__.__name__)]=self
        
    def save_params_to_sharememory(self):
        """　Widget変数→共有データ　の方向にデータを書き込むコマンド　"""
        pass
        
    def set_params_from_sharememory(self):
        """ 共有データ→Widget変数　の方向にデータを書き込むコマンド """
        pass
        


class InitWindow(Window):
    """1日で初めてタイマーを起動する時に表示されるWindow"""
    TYPE = "SUB"
    SURVIVABLE_STATUS = ("INIT",)
    def _make_window(self):
        self.win.title("Init")
        self.win.resizable(width=0, height=0)#画面の拡大縮小禁止
        self._prepare_variable()#Widget変数の定義
        self._make_widget()#ウィジェットの配置
        if self.windata.hold_tm_window_top == True:
            self.win.attributes("-topmost", True)#ウィンドウの固定
    
    ###Widget変数の定義###
    def _prepare_variable(self):
        self.var_sleep_time = tk.DoubleVar()#時間表記用
        self.var_sleep_time.set(7)
        self.var_have_breakfast = tk.BooleanVar()#朝食を食べたかどうかの☑
    
    ###ウィジェットの配置###
    def _make_widget(self):
        ###メッセージ###
        message_label = tk.Label(self.win, text="\n１日の始めに、ステータスを入力します\n")
        ###睡眠時間（Spinbox）###
        sleep_label = tk.Label(self.win, text="睡眠時間：")
        sleep_spin = tk.Spinbox(self.win,
                   textvariable=self.var_sleep_time,
                   from_ = 0,
                   to = 15,
                   increment=0.5
                   )
        ###朝食のチェックボックス###
        bf_label = tk.Label(self.win, text="　　朝食：")
        bf_chkbox = tk.Checkbutton(
            self.win,
            variable=self.var_have_breakfast,
            text='朝食を食べた')
        ###ボタン作成###
        frame_bt = tk.Frame(self.win)
        button1 = tk.Button(frame_bt, text="Let's work!!")
        button1.pack(side=tk.RIGHT)
        button1.bind("<Button-1>",lambda event:self.ev.ini_work_start(self.ev))
        button2 = tk.Button(frame_bt, text=" Home ")
        button2.pack(side=tk.RIGHT)
        button2.bind("<Button-1>",lambda event:self.ev.ini_home(self.ev))
        ###メモ作成###
        frame_memo = tk.Frame(self.win,width=18,height=3)
        tk.Label(frame_memo, text="メモ:").pack(side=tk.LEFT)
        self.widget_memo = tkst.ScrolledText(frame_memo,width=25,height=7)
        self.widget_memo.pack()
        ###要素の配置###
        message_label.grid(row=0, column=0, columnspan=2)
        sleep_label.grid(row=1, column=0)
        sleep_spin.grid(row=1, column=1)
        bf_label.grid(row=2, column=0)
        bf_chkbox.grid(row=2, column=1)
        frame_memo.grid(row=3, column=0, columnspan=2)
        tk.Label(self.win, text="").grid(row=4, column=1)#改行用
        frame_bt.grid(row=5,column=1,sticky="E")
    
    def _register_roster(self):
        Window.instance[str(__class__.__name__)]=self
    
    def save_params_to_sharememory(self):
        """Widget変数→共有データ　の方向にデータを書き込む関数"""
        self.windata.sleep_time = self.var_have_breakfast
        self.windata.task_data.dayly_memo = self.widget_memo.get("1.0",tk.END)#"end-1c")
        
    
    def set_params_from_sharememory(self):
        """共有データ→Widget変数　の方向にデータを書き込む関数"""
        pass
    
    

class IdleWindow(Window):
    """タスク関連ウィンドウの、トップウィンドウ"""
    TYPE = "SUB"
    SURVIVABLE_STATUS = ("IDLE",)
    def _make_window(self):
        self.win.title("Idle")
        self.win.resizable(width=0, height=0)#画面の拡大縮小禁止
        self._prepare_variable()#Widget変数の定義
        self._make_widget()#ウィジェットの配置
        self.set_params_from_sharememory()#IdleWindowは初期状態で値を代入したいから、ここで代入する
        if self.windata.hold_tm_window_top == True:
            self.win.attributes("-topmost", True)#ウィンドウの固定
            
    ###ウィンドウで使うWidget変数###
    def _prepare_variable(self):
        self.tags = self.windata.task_tags#タグの一覧 <- list
        self.var_taskname = tk.StringVar()
        self.var_subname = tk.StringVar()
        self.var_tag = tk.StringVar()
        self.var_tag.set(self.tags[0])#初期値セット。しなくてもよさげ。
        #self.var_memo = tk.StringVar()#メモ用。ScrolledText系は、Var使えない？
        self.widget_memo = None#あとからメモのウィジェットを作る
        self.var_hour = tk.IntVar()#時間表記用
        self.var_min = tk.IntVar()
        self.var_sec = tk.IntVar()
    
    ###ウィジェットの配置###
    def _make_widget(self):
        ###メインフレーム作成###
        frame_task = tk.Frame(self.win)
        label_message = tk.Label(frame_task, text="\nタスク情報を入力し、タスクを始めましょう！\n")
        label_taskname = tk.Label(frame_task, text="タスク名:")
        entry_taskname = tk.Entry(frame_task, width=30, validate="key", textvariable=self.var_taskname, validatecommand=(frame_task.register(self._vi.check_str), "%P"))
        label_subname  = tk.Label(frame_task, text="サブタスク名:")
        entry_subname  = tk.Entry(frame_task, width=30, validate="key", textvariable=self.var_subname, validatecommand=(frame_task.register(self._vi.check_str), "%P"))
        label_tags = tk.Label(frame_task, text="タグ:")
        option_tags = tk.OptionMenu(frame_task, self.var_tag, *self.tags)
        option_tags.configure(width=12)
        ###メインフレーム配置###
        label_message.grid(row=0,column=0,columnspan=2)#span=2で、grid2つ分を確保            
        label_taskname.grid(row=1,column=0,sticky="W")
        entry_taskname.grid(row=1,column=1)          
        label_subname.grid(row=2,column=0,sticky="W")
        entry_subname.grid(row=2,column=1)
        label_tags.grid(row=3,column=0,sticky="W")
        option_tags.grid(row=3,column=1,sticky="W")
        frame_task.grid(row=0,column=0,sticky="W")
        ###メモ###
        frame_memo = tk.Frame(self.win)
        label_memo = tk.Label(frame_memo, text="メモ:")
        label_memo.pack(side=tk.LEFT)
        self.widget_memo = tkst.ScrolledText(frame_memo, width=30,height=7)#Textクラスを親に持つ場合、Variableは割り付けられなさそう
        self.widget_memo.pack()
        frame_memo.grid(row=1,column=0,sticky="W")
        ###時間素材の素材###
        frame_time = tk.Frame(self.win)
        entry_h = tk.Entry(frame_time, width=2, textvariable=self.var_hour, validate="key", validatecommand=(frame_time.register(self._vi.check_time), "%P"))
        entry_m = tk.Entry(frame_time, width=2, textvariable=self.var_min, validate="key", validatecommand=(frame_time.register(self._vi.check_time), "%P"))
        entry_s = tk.Entry(frame_time, width=2, textvariable=self.var_sec, validate="key", validatecommand=(frame_time.register(self._vi.check_time), "%P"), state="readonly")
        label_colon_1 = tk.Label(frame_time, text=":")
        label_colon_2 = tk.Label(frame_time, text=":")
        ###時間素材の配置###
        entry_h.pack(side=tk.LEFT)
        label_colon_1.pack(side=tk.LEFT)
        entry_m.pack(side=tk.LEFT)
        label_colon_2.pack(side=tk.LEFT)
        entry_s.pack(side=tk.LEFT)
        frame_time.grid(row=2,column=0)
        #ボタンの作成・配置
        frame_bt = tk.Frame(self.win)
        frame_bt.grid(row=3,column=0,sticky="E")
        button1 = tk.Button(frame_bt, text="Timer start!!")
        button1.pack(side=tk.RIGHT)
        button2 = tk.Button(frame_bt, text=" Home ")
        button2.pack(side=tk.RIGHT)
        #イベントのバインド
        button1.bind("<Button-1>",lambda event:self.ev.i_timer_start(self.ev))#第一引数としてインスタンスを渡さなければ、呼び出した関数がselfを使えない
        button2.bind("<Button-1>",lambda event:self.ev.i_fin_work(self.ev))
        
    
    def save_params_to_sharememory(self):
        """Widget変数→共有データ　の方向にデータを書き込む関数"""
        self.windata.task_data.start_datetime = datetime.datetime.now()
        self.windata.task_data.name    = self.var_taskname.get()
        self.windata.task_data.subname = self.var_subname.get()
        self.windata.task_data.tag     = self.var_tag.get()
        self.windata.task_data.memo    = self.widget_memo.get("1.0",tk.END)#"end-1c")
        self.windata.task_data.hour = int(self.var_hour.get())
        self.windata.task_data.minute = int(self.var_min.get())
        self.windata.task_data.sec = 0
        
        
    def set_params_from_sharememory(self):
        """共有データ→Widget変数　の方向にデータを書き込む関数"""
        self.var_taskname.set(self.windata.task_data.name)
        self.var_subname.set(self.windata.task_data.subname)
        self.var_tag.set(self.windata.task_data.tag)
        self.var_hour.set(str(self.windata.TASK_TIME["hour"]))
        self.var_min.set(str(self.windata.TASK_TIME["minute"]))
        self.widget_memo.delete("1.0",tk.END)
        
    def _register_roster(self):
        Window.instance[str(__class__.__name__)]=self



class AnalysisWindow(Window):
    """タスク情報を解析するためのWindow"""
    TYPE = "SUB"
    SURVIVABLE_STATUS = ("ANALYSIS",)
    def _make_window(self):
        self.win.title("Analysis")
        self.win.resizable(width=0, height=0)#画面の拡大縮小禁止
        self._prepare_variable()#Widget変数の定義
        self._make_widget()#ウィジェットの配置
        if self.windata.hold_tm_window_top == True:
            self.win.attributes("-topmost", True)#ウィンドウの固定
            
    ###ウィンドウで使うWidget変数###
    def _prepare_variable(self):
        # グラフに関する内部変数
        #self._graph_mode = "sleep_time-concentrate"
        self._graph_mode = plot.Plot.validate_mode[0]
        self.pl = plot.Plot()
        self.canvas = None
    
    ###ウィジェットの配置###
    def _make_widget(self):
        ###グラフ描画###
        _fig = self.pl.get_fig(self._graph_mode)
        self.canvas = FigureCanvasTkAgg(_fig, self.win)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0,column=0)
        ###ボタンの配置###
        bt_change_graph = tk.Button(self.win, text=" change graph 🔄 ", bg="#f94")
        bt_change_graph.grid(row=1,column=0)
        padding = tk.Label(self.win, text="")
        padding.grid(row=2,column=0)
        bt_home = tk.Button(self.win, text=" Home ",bg="#88c")
        bt_home.grid(row=3,column=0,sticky="E")
        ###イベントのバインド###
        bt_change_graph.bind("<Button-1>",lambda event:self._change_graph())
        bt_home.bind("<Button-1>",lambda event:self.ev.a_go_home(self.ev))
        
    ###表示されるグラフの種類を変更する###
    def _change_graph(self):
        mode_list = plot.Plot.validate_mode
        mode_index = mode_list.index(self._graph_mode)
        next_mode_index = mode_index+1
        if len(mode_list) <= next_mode_index:#リスト長をはみ出ていたら0にする
            next_mode_index = 0
        self._graph_mode = mode_list[next_mode_index]
        _fig = self.pl.get_fig(self._graph_mode)
        self.canvas.figure = _fig
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0,column=0)
        
        
    def save_params_to_sharememory(self):
        """Widget変数→共有データ　の方向にデータを書き込む関数"""
        pass
    
    def set_params_from_sharememory(self):
        """共有データ→Widget変数　の方向にデータを書き込む関数"""
        pass
        
    def _register_roster(self):
        Window.instance[str(__class__.__name__)]=self        
        
        
class TimerWindow(Window):
    """タイマー機能を持つ、小さなウィンドウ"""
    TYPE = "SUB"
    SURVIVABLE_STATUS = ("TASK","REST","LONG_REST", "TASK_STOP","REST_STOP","LONG_REST_STOP")
    
    def _make_window(self):
        self.win.title("timer")
        self.win.geometry("{}x{}".format(210,30))
        self.win.resizable(width=0, height=0)#画面の拡大縮小禁止
        self._prepare_variable()
        self._make_widget()
        if self.windata.hold_tm_window_top == True:
            self.win.attributes("-topmost", True)#ウィンドウの固定

        
    ###ウィンドウで使うWidget変数###
    def _prepare_variable(self):
        self.var_time = tk.StringVar()
        self.var_time.set("00:00:00")
        self.counter = Counter()#タイマーカウント用クラスのインスタンス化
        self.counter.set_hms(4, 6, 49)#時間表記用
        self._timer_live_flag=False
        self._count_on_flag=False
        
    ###ウィジェットの配置###
    def _make_widget(self):
        ###フレームの作成###
        frame = tk.Frame(self.win)
        frame.pack()
        ###ボタンと時間表示部の作成###
        self.button1_pouse = tk.Button(frame, text="■", bg="#f44")#動作中に編集されるため、インスタンス変数にしてる
        button2_distracted = tk.Button(frame, text="❗", bg="#dd4")
        button3_switch     = tk.Button(frame, text="🔄",bg="#f94")
        button4_force_fin  = tk.Button(frame, text="🔜",bg="#d0d")
        label_time = tk.Label(frame,textvariable=self.var_time)
        ###ボタンと時間表示部の配置###
        self.button1_pouse.grid(row=0, column=0, padx=5, pady=5)
        button2_distracted.grid(row=0, column=1, padx=5, pady=5)
        label_time.grid(row=0, column=2)
        button3_switch.grid(row=0, column=3, padx=5, pady=5)
        button4_force_fin.grid(row=0, column=4, padx=5, pady=5)
        ###関数のバインド###
        self.button1_pouse.bind("<Button-1>",lambda event:self.ev.tm_stop(self.ev))
        button2_distracted.bind("<Button-1>",lambda event:self.ev.tm_got_distracted(self.ev))
        button3_switch.bind("<Button-1>",lambda event:self.ev.tm_change_task(self.ev))
        button4_force_fin.bind("<Button-1>",lambda event:self.ev.tm_force_fin(self.ev))

    def save_params_to_sharememory(self):
        """Widget変数→共有データ　の方向にデータを書き込む関数"""
        self.windata.task_data.remain_sec=self.counter.get_totalsec()

    def set_params_from_sharememory(self):
        """共有データ→Widget変数　の方向にデータを書き込む関数"""
        self._setup_timer()

    ###ウィンドウステータス更新時、直前のステータスを参照して、タイマーの挙動を決める##
    def _window_update(self):
        #タイマーが動かないステート
        if self.windata.state in ["TASK_STOP","REST_STOP","LONG_REST_STOP","SWITCH"]:
            self._timer_stop()
            self.button1_pouse.configure(text="▶", bg="#6f6")
        #タイマーが動くステート
        elif self.windata.state in ["TASK","REST","LONG_REST"]:
            #前のステータスがタイマー始動前なら、セッティングから行う。
            if self.windata.preview_state in ["IDLE","TASK_FIN","REST_FIN"]:
                self._timer_start()
            #前のステータスがタイマーの一時停止なら、再開させる
            elif self.windata.preview_state in ["TASK_STOP","REST_STOP","LONG_REST_STOP","SWITCH"]:
                self._timer_resume()
            self.button1_pouse.configure(text="■", bg="#f66")
        #それ以外のステータスの場合、タイマーを停止する。
        else:
            self._timer_break()

    def _timer_start(self):
        self._timer_live_flag=True
        self._count_on_flag = True
        self._update_timer()

    def _timer_stop(self):
        self._count_on_flag = False

    def _timer_resume(self):
        self._count_on_flag = True

    def _timer_break(self):
        #情報の保存などの必要があれば、行う。
        self._count_on_flag = False
        self._timer_live_flag=False
        
    def _setup_timer(self):
        self.counter.set_hms(
            self.windata.task_data.hour,
            self.windata.task_data.minute,
            self.windata.task_data.second
            )
        
    ### 1秒ごとに、タイマーの表記と内部時間の更新を行う ###
    def _update_timer(self):
        # タイマーが notLive なら、もう更新しない
        if self._timer_live_flag==False:
            return
        # タイマーが Live なら、1秒後にもう一回同じ処理。
        self.root.after(1000, self._update_timer)
        #カウントフラグがFalseの時はカウントダウンしない
        if self._count_on_flag == False:
            return
        # カウントフラグが True の時のカウント処理
        self.counter.countdown()
        # ウィンドウの表示更新
        hms_str = self.counter.get_hms_str()
        self.var_time.set(hms_str)
        # タイマーが0になったとき、イベントを呼び出す。
        if self.counter.total_sec <= 0:
            self.timer_on_flag = False
            self.ev.tm_timeup(self.ev)
    
    def _register_roster(self):
        Window.instance[str(__class__.__name__)]=self



class TaskFinishWindow(Window):
    """タスクが終了したときに表示されるウィンドウ"""
    TYPE = "SUB"
    SURVIVABLE_STATUS = ("TASK_FIN",)
    def _make_window(self):
        self.win.title("task finish")
        self.win.resizable(width=0, height=0)#画面の拡大縮小禁止
        self._prepare_variable()
        self._make_widgets()
        if self.windata.hold_other_window_top == True:
            self.win.attributes("-topmost", True)
    
    ###ウィンドウで使うWidget変数###
    def _prepare_variable(self):
        self.tags = self.windata.task_tags#タグの一覧 <- list
        self.var_taskname = tk.StringVar()
        self.var_subname = tk.StringVar()
        self.var_tag = tk.StringVar()
        self.var_distracted = tk.IntVar()
        self.var_progress = tk.IntVar()
        self.var_concentrate = tk.StringVar()
        self.widget_memo = None#widget。後から入れる。
        
    ###ウィジェットの配置###
    def _make_widgets(self):
        """
    配置図
           0             1
  0     message
  1     now_task    distoracted
  2     subname     achievement
  3     tag         concentrate
  4     memo        
  5      ↓          
  6      ↓              
  7                     buttons
        """
        ###メッセージテキストの作成・配置###
        frame_message = tk.Frame(self.win)
        frame_message.grid(row=0)#, sticky="e")
        label_message_1 = tk.Label(frame_message, text="タスクが終了しました。")
        label_message_1.pack(anchor=tk.W)
        label_message_2 = tk.Label(frame_message, text="作業情報を入力して休憩に入ってください。")
        label_message_2.pack(anchor=tk.W)
        ###現在のタスクの作成・配置###
        frame_taskname = tk.Frame(self.win,width=15,height=5)
        frame_taskname.grid(row=1, column=0)
        label_taskname = tk.Label(frame_taskname, text="タスク名:")
        label_taskname.pack()
        entry_taskname = tk.Entry(frame_taskname, width=30, validate="key",textvariable=self.var_taskname, validatecommand=(frame_taskname.register(self._vi.check_str), "%P"))
        entry_taskname.pack()
        ###現在のサブタスク作成・配置###
        frame_subname = tk.Frame(self.win,width=15,height=5)
        frame_subname.grid(row=2, column=0)
        label_subname = tk.Label(frame_subname, text="サブタスク名:")
        label_subname.pack()
        entry_subname = tk.Entry(frame_subname, width=30, validate="key",textvariable=self.var_subname, validatecommand=(frame_subname.register(self._vi.check_str), "%P"))
        entry_subname.pack()
        ###現在のタグの作成・配置###
        frame_tag = tk.Frame(self.win,width=15,height=5)
        frame_tag.grid(row=3, column=0)
        label_tag = tk.Label(frame_tag, text="タグ名:")
        label_tag.pack()
        tags = self.windata.task_tags
        option_tags = tk.OptionMenu(frame_tag, self.var_tag, *tags)
        option_tags.configure(width=12)
        option_tags.pack()
        ###メモの作成・配置###
        frame_memo = tk.Frame(self.win,width=18,height=3)
        frame_memo.grid(row=4, column=0, rowspan=3)
        label_work = tk.Label(frame_memo, text="メモ:")
        label_work.pack()
        self.widget_memo = tkst.ScrolledText(frame_memo,width=25,height=7)
        self.widget_memo.pack()
        ###気が散った回数の作成・配置###
        frame_distracted = tk.Frame(self.win,width=15,height=5)
        frame_distracted.grid(row=1, column=1)
        tk.Label(frame_distracted, text="気が散った回数:").pack()
        tk.Entry(frame_distracted, 
                 width=5, 
                 validate="key", 
                 textvariable=self.var_distracted, 
                 validatecommand=(frame_distracted.register(self._vi.check_int), "%P")
                 ).pack()
        ###進捗度(スピンボックス)の作成・配置###
        frame_progress = tk.Frame(self.win)
        frame_progress.grid(row=2, column=1)
        tk.Label(frame_progress, text="進捗率").pack()
        tk.Spinbox(frame_progress,
                   textvariable=self.var_progress,
                   from_ = 0,
                   to = 100,
                   increment=10
                   ).pack()
        #集中度(ラジオボタン)の作成・配置
        frame_concentrate = tk.Frame(self.win)
        frame_concentrate.grid(row=3, column=1)
        tk.Label(frame_concentrate, text="集中度").pack()
        concentrate_state = ["1.完全にダメ",
                             "2.ほぼダメ",
                             "3.途切れがち",
                             "4.いつも通り",
                             "5.普通にイイ感じ",
                             "6.ほぼ集中できた",
                             "7.完全集中できた"]
        tk.Spinbox(frame_concentrate,
                   textvariable = self.var_concentrate,
                   values=concentrate_state,
                   state="readonly"
                   ).pack()
        
        ###ボタン作成###
        bt_frame = tk.Frame(self.win)
        button1 = tk.Button(bt_frame, text="休憩")
        button2 = tk.Button(bt_frame, text="休憩(長)")
        button3 = tk.Button(bt_frame, text="終了")
        button4 = tk.Button(bt_frame, text="保存しないで終了")
        ## ボタン配置 ##
        button4.pack(side=tk.RIGHT)
        button3.pack(side=tk.RIGHT)
        button2.pack(side=tk.RIGHT)
        button1.pack(side=tk.RIGHT)
        bt_frame.grid(row=7, column=1)
        ## イベントのバインド ##
        button1.bind("<Button-1>",lambda event:self.ev.tf_rest(self.ev))
        button2.bind("<Button-1>",lambda event:self.ev.tf_long_rest(self.ev))
        button3.bind("<Button-1>",lambda event:self.ev.tf_fin(self.ev))
        button4.bind("<Button-1>",lambda event:self.ev.tf_non_record_fin(self.ev))
        
        
    def save_params_to_sharememory(self):
        """Widget変数→共有データ　の方向にデータを書き込む関数"""
        self.windata.task_data.start_datetime = datetime.datetime.now()
        self.windata.task_data.name    = self.var_taskname.get()
        self.windata.task_data.subname = self.var_subname.get()
        self.windata.task_data.tag     = self.var_tag.get()
        self.windata.task_data.memo    = self.widget_memo.get("1.0",tk.END)#"end-1c")
        self.windata.task_data.distracted  = self.var_distracted.get()
        self.windata.task_data.progress    = self.var_progress.get()
        self.windata.task_data.concentrate = self.var_concentrate.get()

    def set_params_from_sharememory(self):
        """共有データ→Widget変数　の方向にデータを書き込む関数"""
        self.var_taskname.set(self.windata.task_data.name)
        self.var_subname.set(self.windata.task_data.subname)
        self.var_tag.set(self.windata.task_data.tag)
        self.widget_memo.delete("1.0",tk.END)
        self.widget_memo.insert("1.0",self.windata.task_data.memo)
        self.var_distracted.set(self.windata.task_data.distracted) 
        self.var_progress.set(self.windata.task_data.progress)
        self.var_concentrate.set(self.windata.task_data.concentrate)

    def _register_roster(self):
        Window.instance[str(__class__.__name__)]=self
        


class RestFinishWindow(Window):
    """休憩時間が終了した時に表示されるウィンドウ"""
    TYPE = "SUB"
    SURVIVABLE_STATUS = ("REST_FIN",)
    def _make_window(self):
        self.win.title("rest finish")
        self.win.resizable(width=0, height=0)#画面の拡大縮小禁止
        self._prepare_variable()
        self._make_widgets()
        if self.windata.hold_other_window_top == True:
            self.win.attributes("-topmost", True)
    
    ### ウィンドウで使うWidget変数を用意 ###
    def _prepare_variable(self):
        self.tags = self.windata.task_tags#タグの一覧 <- list
        self.var_taskname = tk.StringVar()
        self.var_subname = tk.StringVar()
        self.var_tag = tk.StringVar()
        self.widget_memo = None#あとからメモのウィジェットを作る
        self.var_hour = tk.IntVar()#時間表記用
        self.var_min = tk.IntVar()
        self.var_sec = tk.IntVar()
    
    ### ウィジェットの配置を行う ###
    def _make_widgets(self):
        """      配置図
               0          1
         0  message
         1  next_task   time
         2  memo        
         3             buttons
        """
        
        #テキストの作成・配置
        frame_message = tk.Frame(self.win)
        frame_message.grid(row=0)#, sticky="e")
        tk.Label(frame_message, text="休憩が終了しました。").pack(anchor=tk.W)
        tk.Label(frame_message, text="次の作業情報を入力して休憩に入ってください。").pack(anchor=tk.W)
        #次のタスクの作成・配置
        frame_taskname = tk.Frame(self.win,width=15,height=5)
        frame_taskname.grid(row=1, column=0)
        tk.Label(frame_taskname, text="タスク名:").pack()
        self.nt_entry = tk.Entry(
            frame_taskname,
            width=30,
            validate="key",
            textvariable=self.var_taskname,
            validatecommand=(frame_taskname.register(self._vi.check_str), "%P")
            ).pack()
        #次のサブタスク作成・配置
        frame_subname = tk.Frame(self.win,width=15,height=5)
        frame_subname.grid(row=2, column=0)
        tk.Label(frame_subname, text="サブタスク名:").pack()
        nt_entry_sub = tk.Entry(
            frame_subname,
            width=30,
            validate="key",
            textvariable= self.var_subname,
            validatecommand=(frame_subname.register(self._vi.check_str), "%P")
            ).pack()
        #次のタスクのタグ作成・配置
        frame_tag = tk.Frame(self.win,width=15,height=5)
        frame_tag.grid(row=3, column=0)
        tk.Label(frame_tag, text="タグ名:").pack()
        option_tags = tk.OptionMenu(frame_tag, self.var_tag, *self.tags)
        option_tags.configure(width=12)
        option_tags.pack()
        #タスクのメモを作成・配置
        frame_memo = tk.Frame(self.win,width=18,height=3)
        frame_memo.grid(row=4, column=0)
        tk.Label(frame_memo, text="メモ:").pack()
        self.widget_memo = tkst.ScrolledText(frame_memo,width=25,height=7)
        self.widget_memo.pack()
        
        #時間の素材の作成
        frame_time = tk.Frame(self.win)
        entry_h = tk.Entry(frame_time, width=2, textvariable=self.var_hour, validate="key", validatecommand=(frame_time.register(self._vi.check_time), "%P"))
        entry_m = tk.Entry(frame_time, width=2, textvariable=self.var_min, validate="key", validatecommand=(frame_time.register(self._vi.check_time), "%P"))
        entry_s = tk.Entry(frame_time, width=2, textvariable=self.var_sec, validate="key", validatecommand=(frame_time.register(self._vi.check_time), "%P"), state="readonly")
        label_colon_1 = tk.Label(frame_time, text=":")
        label_colon_2 = tk.Label(frame_time, text=":")
        #時間部分の配置
        entry_h.pack(side=tk.LEFT)
        label_colon_1.pack(side=tk.LEFT)
        entry_m.pack(side=tk.LEFT)
        label_colon_2.pack(side=tk.LEFT)
        entry_s.pack(side=tk.LEFT)
        frame_time.grid(row=4, column=1)
        #ボタンの作成・配置
        bt_frame = tk.Frame(self.win)
        button2 = tk.Button(bt_frame, text="終了")
        button2.pack(side=tk.RIGHT)
        button2.bind("<Button-1>",lambda event:self.ev.rf_fin(self.ev))
        button1 = tk.Button(bt_frame, text="開始！")
        button1.pack(side=tk.RIGHT)
        button1.bind("<Button-1>",lambda event:self.ev.rf_timer_start(self.ev))
        bt_frame.grid(row=5, column=1)
        
        
    def save_params_to_sharememory(self):
        """Widget変数→共有データ　の方向にデータを書き込む関数"""
        self.windata.task_data.start_datetime = datetime.datetime.now()
        self.windata.task_data.name    = self.var_taskname.get()
        self.windata.task_data.subname = self.var_subname.get()
        self.windata.task_data.tag     = self.var_tag.get()
        self.windata.task_data.memo    = self.widget_memo.get("1.0",tk.END)#"end-1c")
        self.windata.task_data.hour = int(self.var_hour.get())
        self.windata.task_data.hour = int(self.var_min.get())
        self.windata.task_data.hour = 0
    
    def set_params_from_sharememory(self):
        """共有データ→Widget変数　の方向にデータを書き込む関数"""
        self.var_taskname.set(self.windata.task_data.name)
        self.var_subname.set(self.windata.task_data.subname)
        self.var_tag.set(self.windata.task_data.tag)
        self.var_hour.set(str(self.windata.TASK_TIME["hour"]))
        self.var_min.set(str(self.windata.TASK_TIME["minute"]))
        self.widget_memo.delete("1.0",tk.END)
        
    def _register_roster(self):
        Window.instance[str(__class__.__name__)]=self




class TaskSwitchWindow(Window):
    """タスク内容を切り替えるためのウィンドウ"""
    TYPE = "SUB"
    SURVIVABLE_STATUS = ("SWITCH",)
    
    def _make_window(self):
        self.win.title("task change")
        #self.win.geometry("{}x{}".format(320,225))
        #self.win.resizable(width=0, height=0)#画面の拡大縮小禁止
        self._prepare_variable()
        self._make_widgets()
        if self.windata.hold_other_window_top == True:
            self.win.attributes("-topmost", True)
    
    ### ウィンドウで使うWidget変数を用意 ###
    def _prepare_variable(self):
        self.tags = self.windata.task_tags#タグの一覧 <- list
        self.var_taskname = tk.StringVar()
        self.var_subname = tk.StringVar()
        self.var_tag = tk.StringVar()
        self.widget_memo = None#あとからメモのウィジェットを作る
        self.var_next_taskname = tk.StringVar()
        self.var_next_subname = tk.StringVar()
        self.var_next_tag = tk.StringVar()
        self.widget_next_memo = None#あとからメモのウィジェットを作る
        self.var_hour = tk.IntVar()#時間表記用
        self.var_min = tk.IntVar()
        self.var_sec = tk.IntVar()
    
    ### ウィジェットの配置を行う ###
    def _make_widgets(self):
        """
    配置図
            0         1         2          3    Column
     0    message
     ------------------------------------
     1           |現在のタスク|        |変更後のタスク|
     ------------------------------------
     2  'タスク名' |now_task |        | next_task |
        'サブ名'  |now_sub  | change | next_sub  |
        'タグ名'  |now_tag  |  →→→→  | next_tag  |
        'メモ'　　 |now_memo |        | next_memo |
     ------------------------------------
     2               　　  | Time   |
     3                　　 |  　 　　　|　 buttons
   row
        """
        ## messageの作成・配置
        ts_label_message = tk.Label(self.win, text="タスクを切り替えます")
        ts_label_message.grid(row=0, column=0)
        
        ## タスク名、サブ名、などの、ラベル名のみを作成・配置 ##
        frame_index = tk.Frame(self.win)
        frame_index.grid(row=2, column=0, sticky=tk.N)
        tk.Label(frame_index, text="タスク名").pack(anchor=tk.NE)
        tk.Label(frame_index, text="サブタスク名").pack(anchor=tk.NE)
        tk.Label(frame_index, text="タグ").pack(anchor=tk.NE)
        tk.Label(frame_index, text="メモ").pack(anchor=tk.NE) 
        ## 「現在のタスク」の文字列をセット ##
        tk.Label(self.win, text="現在のタスク").grid(row=1, column=1)
        ## now_taskのフレームと各ラベルを作成 ##
        frame_taskname = tk.Frame(self.win, relief="ridge")
        frame_taskname.grid(row=2, column=1)
        tk.Entry(
            frame_taskname,
            textvariable=self.var_taskname,
            width=32
            ).pack(anchor=tk.W)
        tk.Entry(
            frame_taskname,
            textvariable=self.var_subname,
            width=32
            ).pack(anchor=tk.W)
        option_tag = tk.OptionMenu(frame_taskname, self.var_tag, *self.tags)
        option_tag.configure(width=12)
        option_tag.pack()
        self.widget_memo = tkst.ScrolledText(frame_taskname,width=30,height=7)
        self.widget_memo.pack(anchor=tk.W)
        ## chenge →→→→　の文字列のセット ##
        tk.Label(self.win, text="Change\n→→→→").grid(row=2, column=2)
        ## 「変更後のタスク」の文字列をセット ##
        tk.Label(self.win, text="変更後のタスク").grid(row=1, column=3)
        
        ### next_taskのフレームと各ラベルを作成 ###
        frame_next_task = tk.Frame(self.win, relief="ridge")
        frame_next_task.grid(row=2, column=3)
        tk.Entry(
            frame_next_task,
            width=32,
            validate="key",
            textvariable=self.var_next_taskname,
            validatecommand=(frame_next_task.register(self._vi.check_str), "%P")
            ).pack(anchor=tk.W)
        tk.Entry(
            frame_next_task,
            width=32,
            validate="key",
            textvariable=self.var_next_subname,
            validatecommand=(frame_next_task.register(self._vi.check_str), "%P")
            ).pack(anchor=tk.W)
        option_next_tag = tk.OptionMenu(frame_next_task, self.var_next_tag, *self.tags)
        option_next_tag.configure(width=12)
        option_next_tag.pack()
        self.widget_next_memo = tkst.ScrolledText(frame_next_task,width=30,height=7)
        self.widget_next_memo.pack(anchor=tk.W)
        
        ##時間の素材##
        frame_time = tk.Frame(self.win)
        entry_h = tk.Entry(frame_time, width=2, textvariable=self.var_hour, validate="key", validatecommand=(frame_time.register(self._vi.check_time), "%P"))
        entry_m = tk.Entry(frame_time, width=2, textvariable=self.var_min, validate="key", validatecommand=(frame_time.register(self._vi.check_time), "%P"))
        entry_s = tk.Entry(frame_time, width=2, textvariable=self.var_sec, validate="key", validatecommand=(frame_time.register(self._vi.check_time), "%P"), state="readonly")
        label_colon_1 = tk.Label(frame_time, text=":")
        label_colon_2 = tk.Label(frame_time, text=":")
        ###時間部の配置###
        entry_h.pack(side=tk.LEFT)
        label_colon_1.pack(side=tk.LEFT)
        entry_m.pack(side=tk.LEFT)
        label_colon_2.pack(side=tk.LEFT)
        entry_s.pack(side=tk.LEFT)
        frame_time.grid(row=3, column=2)
        
        ## ボタンの作成・配置 ##
        frame_button = tk.Frame(self.win)
        frame_button.grid(row=3, column=3, sticky=tk.SE)
        button_resume = tk.Button(frame_button, text="中止")
        button_resume.pack(side=tk.RIGHT)
        button_switch_start = tk.Button(frame_button, text="保存＆変更！")
        button_switch_start.pack(side=tk.RIGHT)#イベントのバインド
        ## イベントのバインド ##
        button_resume.bind("<Button-1>",lambda event:self.ev.ts_resume(self.ev))
        button_switch_start.bind("<Button-1>",lambda event:self.ev.ts_switch_start(self.ev))
    
    
    def save_params_to_sharememory(self):
        """Widget変数→共有データ　の方向にデータを書き込む関数"""
        self.windata.task_data.start_datetime = datetime.datetime.now()
        self.windata.task_data.name    = self.var_next_taskname.get()
        self.windata.task_data.subname = self.var_next_subname.get()
        self.windata.task_data.tag     = self.var_next_tag.get()
        self.windata.task_data.memo    = self.widget_next_memo.get("1.0",tk.END)#"end-1c")
        self.windata.task_data.hour    = self.var_hour.get()
        self.windata.task_data.minute  = self.var_min.get()
        self.windata.task_data.second  = self.var_sec.get()


    def set_params_from_sharememory(self):
        """共有データ→Widget変数　の方向にデータを書き込む関数"""
        self.var_taskname.set(self.windata.task_data.name)
        self.var_subname.set(self.windata.task_data.subname)
        self.var_tag.set(self.windata.task_data.tag)
        self.widget_memo.delete("1.0",tk.END)
        self.widget_memo.insert("1.0",self.windata.task_data.memo)
        self.var_next_taskname.set("")
        self.var_next_subname.set("")
        self.var_next_tag.set("")
        self.widget_next_memo.delete("1.0",tk.END)
        
        remain_sec = self.windata.task_data.remain_sec
        self.var_hour.set(remain_sec//3600)
        self.var_min.set((remain_sec%3600)//60)
        self.var_sec.set(((remain_sec%3600)%60)%60)
        
    
    def _register_roster(self):
        Window.instance[str(__class__.__name__)]=self



class NoteWindow(Window):
    #未実装
    pass



class ValidateInput():
    """入力値を制限する関数をまとめたクラス。"""
    
    def check_str(self, val, max_str=30):
        """文字列が30文字以下の入力規制"""
        if len(val)<=max_str:#長さ30以上ならNG
            return True
        else:
            return False
        
    def check_int(self, val):
        """数字の入力規制"""
        if val=="":#空白ならオーケー
            return True
        if val.isdecimal() == True:#数字ならOK
            return True
        else:#そうでなければ入力無効
            return False
            
    def check_time(self, val):
        """時間部分の入力規制"""
        if val=="":#空白ならオーケー
            return True
        if len(val)>=3:#長さ3以上ならNG
            return False
        if val.isdecimal() == True:#数値であればOK
            if 0 <= int(val) < 60:#数値の入力範囲は、0~59
                return True
        return False #そうでなければNG


class Counter:
    """
    TimerWindowで使われる、時間情報をつかさどるためのクラス
    時分秒、秒、文字列、の変換や、カウントダウンを行う。
    """
    def __init__(self):
        """時分秒 ⇔ 秒 の変換関数を登録。"""
        self._hms_to_totalsec = lambda h,m,s: h*3600+m*60+s
        self._totalsec_to_hms = lambda rem:[rem//3600,(rem%3600)//60,((rem%3600)%60)%60]
    
    def set_hms(self,h,m,s):
        self.hour = h
        self.minute = m
        self.second = s
        self.total_sec = self._hms_to_totalsec(h,m,s)
        
    def set_totalsec(self, ts):
        self.total_sec = ts
        self.hour,self.minute,self.second = self._totalsec_to_hms(ts)
        
    def get_totalsec(self):
        return self.total_sec
    
    def get_hms_int(self):
        return self.hour, self.minute, self.second
        
    def get_hms_str(self, print_sec=True):
        """ 4 → 04 のように、タイマー表記の文字列で返却"""
        if self.hour < 10:
            H = "0"+str(self.hour)
        else:
            H = str(self.hour)
        if self.minute < 10:
            M = "0"+str(self.minute)
        else:
            M = str(self.minute)
        if print_sec == False:#秒数を表記しない場合。Configで設定可
            S = "xx"
        elif self.second < 10:
            S = "0"+str(self.second)
        else:
            S = str(self.second)
        return H+":"+M+":"+S
        
    def countdown(self):
        """この関数を呼び出すと、時間が1秒経過する"""
        self.total_sec -= 1
        self.hour,self.minute,self.second = self._totalsec_to_hms(self.total_sec)
        


# test code
if __name__ == "__main__":
    #app_class = MainWindow
    #app_class = InitWindow
    #app_class = IdleWindow
    app_class = AnalysisWindow
    #app_class = TimerWindow
    #app_class = TaskFinishWindow
    #app_class = RestFinishWindow
    #app_class = TaskSwitchWindow
    app_class.TYPE="MAIN"
    root = tk.Tk()
    app = app_class.get_instance(root)
    app.create_window(DEBUG=True)
    root.mainloop()

