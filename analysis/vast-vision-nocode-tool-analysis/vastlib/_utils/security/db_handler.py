# ===============================================================================
# Name      : eop_tray_pick.py
# Version   : 1.0.0
# Brief     : 4隅のマークがあるトレイからピックする
# Time-stamp: 2023-07-19 10:12
# Copyirght 2022 Hiroya Aoyama
# ===============================================================================

import sqlite3
from abc import ABCMeta, abstractmethod
from typing import Optional, List


class DBTable(metaclass=ABCMeta):
    def __init__(self, *, tablename: str = '', db_file: str = ''):
        self._tablename: str = tablename
        self._db_file: str = db_file

    def setTableName(self, tablename: str) -> None:
        self._tablename = tablename

    def setDBFilePath(self, db_file: str) -> None:
        self._db_file = db_file

    def connect(self) -> None:
        self.conn = sqlite3.connect(self._db_file)
        self.cursor = self.conn.cursor()

    @abstractmethod
    def createTable(self) -> None:
        pass

    @abstractmethod
    def insertRow(self, data: list) -> None:
        pass

    def updateData(self, update_dict: dict, condition_dict: dict) -> None:
        """データのアップデート

        Args:
            update_dict (dict): 変更するデータ
            condition_dict (dict): 基準とするデータ
        Examples:
            update_dict = {'judgement': 3, 'resolution': '800x600'}
            condition_dict = {'timestamp': '2023-07-13 10:00:00'}
            table.updateData(update_dict, condition_dict)
        """
        # NOTE: クエリ生成
        query = f'UPDATE {self._tablename} SET '
        set_clause = ', '.join([f'{key} = ?' for key in update_dict.keys()])
        query += set_clause + ' WHERE '
        where_clause = ' AND '.join([f'{key} = ?' for key in condition_dict.keys()])
        query += where_clause
        values = list(update_dict.values()) + list(condition_dict.values())

        # NOTE: クエリ実行
        self.cursor.execute(query, values)
        self.conn.commit()

    def deleteData(self, condition_dict: dict) -> None:
        """_summary_

        Args:
            condition_dict (dict): _description_
        Examples:
            condition_dict = {'judgement': 2}
            table.deleteData(condition_dict)
        """
        # NOTE: クエリ生成
        query = f'DELETE FROM {self._tablename} WHERE '
        where_clause = ' AND '.join([f'{key} = ?' for key in condition_dict.keys()])
        query += where_clause
        values = list(condition_dict.values())

        # NOTE: クエリ実行
        self.cursor.execute(query, values)
        self.conn.commit()

    def selectData(self, condition_dict: Optional[dict] = None):
        """_summary_

        Returns:
            _type_: _description_

        Examples:
            results = table.selectData()
            for row in results:
                print(row)
        """
        query = f'SELECT * FROM {self._tablename}'
        if condition_dict:
            where_clause = ' AND '.join([f'{key} = ?' for key in condition_dict.keys()])
            query += ' WHERE ' + where_clause
            values = list(condition_dict.values())
            self.cursor.execute(query, values)
        else:
            self.cursor.execute(query)

        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()
        self.conn.close()


if __name__ == '__main__':
    from pydantic import BaseModel

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

    class CustomDBTable(DBTable):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

        def createTable(self) -> None:
            # NOTE: InspectionResultsテーブルを作成
            sql_query = f'''
                CREATE TABLE IF NOT EXISTS {self._tablename} (
                    {Labels.timestamp} TEXT,
                    {Labels.judgement} INTEGER,
                    {Labels.resolution} TEXT,
                    {Labels.processing_time} REAL,
                    {Labels.x} REAL,
                    {Labels.y} REAL,
                    {Labels.z} REAL,
                    {Labels.r} REAL,
                    {Labels.num_pieces} INTEGER,
                    {Labels.error_message} TEXT
                )
            '''
            self.cursor.execute(sql_query)
            self.conn.commit()

        def insertRow(self, data: list) -> None:
            # NOTE: InspectionResultsテーブルを作成
            sql_query = f'''
                INSERT INTO {self._tablename} (
                    {Labels.timestamp},
                    {Labels.judgement},
                    {Labels.resolution},
                    {Labels.processing_time},
                    {Labels.x},
                    {Labels.y},
                    {Labels.z},
                    {Labels.r},
                    {Labels.num_pieces},
                    {Labels.error_message}
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            self.cursor.executemany(sql_query, data)
            self.conn.commit()

    # NOTE: テストコード

    db_file = 'inspection_results.sqlite'
    tablename = 'hoge1'
    table = CustomDBTable(db_file=db_file, tablename=tablename)

    table.connect()
    table.createTable()

    # NOTE: データを挿入
    data = [
        ('2023-07-13 10:00:00', 1, '640x480', 0.0, 1.0, 3.0, 0.0, 10.0, 0, ''),
        ('2023-07-13 10:00:01', 2, '', 1.5, 2.0, 4.0, 0.0, 20.0, 0, '')
    ]
    table.insertRow(data)

    # NOTE: データを更新
    update_dict = {'judgement': 3, 'resolution': '800x600'}
    condition_dict1 = {'timestamp': '2023-07-13 10:00:00'}
    table.updateData(update_dict, condition_dict1)

    # NOTE: データを削除
    condition_dict2 = {'judgement': 2}
    table.deleteData(condition_dict2)

    # データを選択
    results = table.selectData()
    for row in results:
        print(row)

    table.close()
