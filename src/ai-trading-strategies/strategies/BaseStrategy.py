import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.widgets import MultiCursor
from matplotlib.axes import Axes
import mplcursors

from typing import Any, Callable
from abc import ABC, abstractmethod

class BaseStrategy(ABC):

    PERIODS = [5, 10, 20, 30, 60, 120, 250]

    COLORS = ['#7dc3ea', '#ffa600', '#f46a64', '#97c786', '#fcaaa6']

    PLOT_SETTINGS_KEY_CNT = 'plot_cnt'
    PLOT_SETTINGS_KEY_POSITION = 'position'
    PLOT_SETTINGS_KEY_AX_TITLE = 'ax_tile'
    PLOT_SETTINGS_KEY_AX_XLABAL = 'ax_xlabel'
    PLOT_SETTINGS_KEY_AX_YLABAL = 'ax_ylabel'
    PLOT_SETTINGS_KEY_COLS = 'cols'
    PLOT_SETTINGS_KEY_COL_NAME = 'col_name'
    PLOT_SETTINGS_KEY_COL_FUNC = 'col_func'
    PLOT_SETTINGS_KEY_COL_COLOR = 'col_color'
    PLOT_SETTINGS_KEY_COL_TIP = 'col_tip'

    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def get_plot_settings(self) -> dict[str, Any]:
        pass
        
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series|pd.DataFrame]:
        pass

    def entry_exit_plot(self, df: pd.DataFrame, xlabel: str, ylabel: str, title: str):
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
        plt.rcParams['axes.unicode_minus'] = False    # 解决负号 '-' 显示为方块的问题

        entries, exits, indicator_datas = self.generate_signals(df=df)
        
        settings = self.get_plot_settings()
        plot_cnt = settings[self.PLOT_SETTINGS_KEY_CNT]
        if plot_cnt == 2:
            # 创建画布
            fig = plt.figure(figsize=(16, 10))
            # 创建子图
            # 使用 GridSpec 定义网格：2行1列，高度比例为 [2, 1]
            gs = fig.add_gridspec(nrows=2, ncols=1, height_ratios=[2, 1])
            # 上面的图（占2/3）
            ax1 = fig.add_subplot(gs[0]) 
            self._plot_price(df=df, entries=entries, exits=exits, ax=ax1, xlabel=xlabel, ylabel=ylabel, title=title)
            # 下面的图（占1/3）
            ax2 = fig.add_subplot(gs[1])  
            self._plot_indictaor(indicator_datas=indicator_datas, settings=settings, ax=ax2)
            MultiCursor(fig.canvas, (ax1, ax2), color='r', lw=1)
        else:
            fig, ax = plt.subplots()
            self._plot_price(df=df, entries=entries, exits=exits, ax=ax, xlabel=xlabel, ylabel=ylabel, title=title)
            self._plot_indictaor(indicator_datas=indicator_datas, settings=settings, ax=ax)


        plt.subplots_adjust(
            left=0.03,    # 左边距（默认 0.125）
            right=0.99,   # 右边距（默认 0.9）
            bottom=0.05,  # 下边距（默认 0.11）
            top=0.97,     # 上边距（默认 0.88）
            hspace=0.13,  # 子图垂直间距
            wspace=0.035   # 子图水平间距
        )
        plt.tight_layout()
        plt.show()

    def _plot_price(self, df: pd.DataFrame, entries: pd.Series, exits: pd.Series, ax: Axes, xlabel: str, ylabel: str, title: str):
        
        close = df['close']
        
        entries = entries[entries == True]
        exits = exits[exits == True]
        entries_y = close.loc[entries.index]
        exits_y = close.loc[exits.index]

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.YearLocator())  # 每年一个主刻度
        ax.xaxis.set_minor_locator(mdates.MonthLocator())  # 每月一个副刻度

        ax.plot(close.index, close, linewidth=2, label='收盘价', color='#7dc3ea')
        sc_entry = ax.scatter(entries.index, entries_y, c='#97c786', s=50, label='策略进入点')
        sc_exit = ax.scatter(exits.index, exits_y, c='#f46a64', s=50, label='策略退出点')
        mplcursors.cursor(sc_entry)
        mplcursors.cursor(sc_exit)
        ax.set(xlabel=xlabel, ylabel=ylabel, title=title)
        ax.legend()
        ax.grid()
    
    def _plot_indictaor(self, indicator_datas: pd.Series|pd.DataFrame, settings: dict[str, Any], ax: Axes):
        
        cols = settings[self.PLOT_SETTINGS_KEY_COLS]
        for col in cols:
            name: str = col[self.PLOT_SETTINGS_KEY_COL_NAME]
            func: Callable = col[self.PLOT_SETTINGS_KEY_COL_FUNC]
            color: str = col[self.PLOT_SETTINGS_KEY_COL_COLOR]
            tip: int = col[self.PLOT_SETTINGS_KEY_COL_TIP]
            indicator = func(indicator_datas.index, indicator_datas if len(cols) == 1 else indicator_datas[name], label=name, color=color)
            if tip == 1:
                mplcursors.cursor(indicator, hover=True)
    
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.YearLocator())  # 每年一个主刻度
        ax.xaxis.set_minor_locator(mdates.MonthLocator())  # 每月一个副刻度
        if settings[self.PLOT_SETTINGS_KEY_CNT] != 1:
            ax.set(xlabel=settings[self.PLOT_SETTINGS_KEY_AX_XLABAL], ylabel=settings[self.PLOT_SETTINGS_KEY_AX_YLABAL])
        ax.legend()
        ax.grid()
