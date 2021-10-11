# -*- coding: utf-8 -*-
"""
Created on Wed Dec  9 22:53:13 2020

@author: Yu-ri
"""

import tkinter as tk

import data
import window as wd
import p_event as pe


class App():
    def __init__(self):
        self.root = tk.Tk()
        self._get_windows_instance()
        self._create_windows()
        self.root.mainloop()
        print("finished")
        
    def _get_windows_instance(self):
        """ウィンドウクラスの子クラスのインスタンスを取得する"""
        self.mw = wd.MainWindow.get_instance(self.root)
        self.iniw = wd.InitWindow.get_instance(self.root)
        self.iw = wd.IdleWindow.get_instance(self.root)
        self.aw = wd.AnalysisWindow.get_instance(self.root)
        self.tw = wd.TimerWindow.get_instance(self.root)
        self.tfw = wd.TaskFinishWindow.get_instance(self.root)
        self.rfw = wd.RestFinishWindow.get_instance(self.root)
        self.wdw = wd.TaskSwitchWindow.get_instance(self.root)
        
    def _create_windows(self):
        """
        アプリ上で用いるウィンドウ全てを作成する。
        Windowクラスの特性上、アクティブでないウィンドウは隠れているだけ。
        """
        self.mw.create_window()
        self.iniw .create_window()
        self.iw.create_window()
        self.aw.create_window()
        self.tw.create_window()
        self.tfw.create_window()
        self.rfw.create_window()
        self.wdw.create_window()


if __name__ == "__main__":
    app = App()
