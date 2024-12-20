# ===============================================================================
# Name      : eop_tray_pick.py
# Version   : 1.0.0
# Brief     : 4隅のマークがあるトレイからピックする
# Time-stamp: 2023-07-19 18:22
# Copyirght 2022 Hiroya Aoyama
# ===============================================================================
import csv
# import datetime
# import numpy as np
import polars as pl
import plotly.graph_objects as go
from pydantic import BaseModel
from typing import List


FIELDNAMES: List[str] = ['timestamp', 'judgement', 'resolution', 'processing_time', 'x', 'y', 'z', 'r', 'num_pieces', 'error_message']


class LabelList(BaseModel):
    """データフレームにアクセスする時に使うラベルリスト"""
    timestamp: str = FIELDNAMES[0]
    judgement: str = FIELDNAMES[1]
    resolution: str = FIELDNAMES[2]
    processing_time: str = FIELDNAMES[3]
    x: str = FIELDNAMES[4]
    y: str = FIELDNAMES[5]
    z: str = FIELDNAMES[6]
    r: str = FIELDNAMES[7]
    num_pieces: str = FIELDNAMES[8]
    error_message: str = FIELDNAMES[9]


Labels = LabelList()


class PositionData(BaseModel):
    """ワークの位置情報"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    r: float = 0.0


class InspectionResults(BaseModel):
    """検査結果の情報"""
    timestamp: str = '2000-01-01 12:00:00'  # NOTE: 検査時刻 YYYY-MM-DD HH:mm:SS
    judgement: int = 1  # NOTE: 処理結果 OK:1, NG:2, ERR:3
    resolution: str = '640x480'  # NOTE: 解像度
    processing_time: float = 0.0  # NOTE: 処理時間
    position: PositionData = PositionData()  # NOTE: ワークの位置
    num_pieces: int = 0  # NOTE: ワークの数
    error_message: str = ''  # NOTE: エラーメッセージ


class InspectionResultsCSVHandler:
    """Inspection ResultsをCSVファイルに書き込むクラス"""

    @staticmethod
    def create_new_csv(filename: str) -> None:
        """Inspection ResultsをCSVファイルに書き込む"""
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writeheader()

    @staticmethod
    def add_data_to_csv(result: InspectionResults, filename: str) -> None:
        """Inspection ResultsをCSVファイルに書き込む"""
        with open(filename, 'a', newline='') as csvfile:
            writer = csv.DictWriter(f=csvfile, fieldnames=FIELDNAMES)
            writer.writerow({
                Labels.timestamp: result.timestamp,
                Labels.judgement: result.judgement,
                Labels.resolution: result.resolution,
                Labels.processing_time: result.processing_time,
                Labels.x: result.position.x,
                Labels.y: result.position.y,
                Labels.z: result.position.z,
                Labels.r: result.position.r,
                Labels.num_pieces: result.num_pieces,
                Labels.error_message: result.error_message
            })


class InspectionResultsVisualizer:
    """可視化関数"""
    @staticmethod
    def read_data_from_csv(filename: str) -> pl.DataFrame:
        """CSVファイルからInspection Resultsを読み取る"""
        return pl.read_csv(filename)

    @staticmethod
    def visualize_judgement(results: pl.DataFrame) -> str:
        """処理結果を棒グラフで可視化する"""
        counts = results[Labels.judgement].value_counts()
        mapper = {1: 'OK', 2: 'NG', 3: 'ERR'}
        # NOTE: 1, 2, 3の順番にソート
        counts = counts.sort(Labels.judgement)
        mapper = {1: 'OK', 2: 'NG', 3: 'ERR'}
        counts = counts.with_columns(pl.col(Labels.judgement).apply(lambda x: mapper.get(x, 'Unknown'),
                                                                    return_dtype=str))
        fig = go.Figure(data=[go.Bar(x=counts[Labels.judgement],
                                     y=counts['counts'],
                                     marker=dict(color=['green', 'red', 'yellow']))
                              ],
                        )
        fig.update_layout(title='Inspection Results - Judgement', xaxis_title='Judgement', yaxis_title='Count')
        return fig.to_html(full_html=False)

    @staticmethod
    def visualize_time_series(results: pl.DataFrame) -> str:
        """時系列で検査結果を可視化する"""
        timestamps = results[Labels.timestamp].str.strptime(pl.Datetime, '%Y-%m-%d %H:%M:%S')
        fig = go.Figure(data=[go.Scatter(x=timestamps, y=results[Labels.judgement], mode='markers')])
        fig.update_layout(title='Inspection Results - Time Series', xaxis_title='Timestamp', yaxis_title='Judgement')
        return fig.to_html(full_html=False)

    @staticmethod
    def visualize_processing_time(results: pl.DataFrame) -> str:
        """処理時間をグラフで可視化する"""
        timestamps = results[Labels.timestamp].str.strptime(pl.Datetime, '%Y-%m-%d %H:%M:%S')
        fig = go.Figure(data=[go.Scatter(x=timestamps, y=results[Labels.processing_time], mode='lines')])
        fig.update_layout(title='Inspection Results - Processing Time', xaxis_title='Time', yaxis_title='Processing Time')
        return fig.to_html(full_html=False)

    @staticmethod
    def visualize_xy_position(results: pl.DataFrame) -> str:
        """X-Y位置をプロットする"""
        fig = go.Figure(data=[go.Scatter(x=results[Labels.x], y=results[Labels.y],
                                         mode='markers', text=results[Labels.timestamp], hovertemplate='%{text}')])
        fig.update_layout(title='Inspection Results - X-Y Position', xaxis_title='X', yaxis_title='Y')
        return fig.to_html(full_html=False)

    @staticmethod
    def visualize_polar_position(results: pl.DataFrame) -> str:
        """Rを円に配置してプロットする"""
        fig = go.Figure(data=[go.Scatterpolar(r=[i for i in range(len(results[Labels.r]))], theta=results[Labels.r],
                                              mode='markers', text=results[Labels.timestamp], hovertemplate='%{text}')])
        fig.update_layout(title='Inspection Results - Polar Position', polar=dict(radialaxis=dict(visible=True)))
        return fig.to_html(full_html=False)


if __name__ == '__main__':
    import sys
    from PySide2 import QtWidgets, QtWebEngineWidgets, QtCore
    import tempfile

    def switch_graph(web_view: QtWebEngineWidgets.QWebEngineView,
                     combo_box: QtWidgets.QComboBox,
                     html_list: List[str]):

        index = combo_box.currentIndex()
        if index < 0:
            return

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_file:
            temp_file.write(html_list[index].encode())
            temp_file_path = temp_file.name

        web_view.load(QtCore.QUrl.fromLocalFile(temp_file_path))

    # NOTE: テストデータ
    data = pl.DataFrame({
        Labels.timestamp: ['2023-07-13 10:00:00',
                           '2023-07-13 10:00:01',
                           '2023-07-13 10:00:02',
                           '2023-07-13 10:00:03',
                           '2023-07-13 10:00:04',
                           '2023-07-13 10:00:05',
                           '2023-07-13 10:00:06',
                           '2023-07-13 10:00:07',
                           '2023-07-13 10:00:08',
                           '2023-07-13 10:00:09'],
        Labels.judgement: [1, 2, 2, 1, 1, 1, 1, 1, 1, 3],
        Labels.resolution: ['', '', '', '', '', '', '', '', '', ''],
        Labels.processing_time: [10, 20, 10, 10, 10, 20, 10, 20, 40, 10],
        Labels.x: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        Labels.y: [10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
        Labels.z: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        Labels.r: [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        Labels.num_pieces: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        Labels.error_message: ['', '', '', '', '', '', '', '', '', ''],
    })

    # NOTE: HTML群
    html_str1 = InspectionResultsVisualizer.visualize_judgement(data)
    html_str2 = InspectionResultsVisualizer.visualize_time_series(data)
    html_str3 = InspectionResultsVisualizer.visualize_xy_position(data)
    html_str4 = InspectionResultsVisualizer.visualize_polar_position(data)
    html_str5 = InspectionResultsVisualizer.visualize_processing_time(data)

    # NOTE: アプリケーションの起動
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()

    # NOTE: コンボボックスを作成
    combo_box = QtWidgets.QComboBox()
    combo_box.addItems(['a', 'b', 'c', 'd', 'e'])

    # NOTE: WebEngineViewを作成
    web_view = QtWebEngineWidgets.QWebEngineView()

    # NOTE: レイアウトに追加
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(combo_box)
    layout.addWidget(web_view)

    # NOTE: 最初はhtml 1を表示しておく
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_file:
        temp_file.write(html_str1.encode())
        temp_file_path = temp_file.name

    web_view.load(QtCore.QUrl.fromLocalFile(temp_file_path))

    # NOTE: コンボボックスの変更イベントでグラフを切り替え
    combo_box.currentIndexChanged.connect(lambda: switch_graph(web_view=web_view,
                                                               combo_box=combo_box,
                                                               html_list=[html_str1,
                                                                          html_str2,
                                                                          html_str3,
                                                                          html_str4,
                                                                          html_str5]))

    # NOTE: QtWidgetにLayoutを追加して表示
    window.setCentralWidget(QtWidgets.QWidget())
    window.centralWidget().setLayout(layout)
    window.show()

    # NOTE: アプリケーションの実行
    sys.exit(app.exec_())
