# ===============================================================================
# Name      : code_reader.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2023-12-06 15:17
# Copyirght 2021 Hiroya Aoyama
# ===============================================================================
"""
必要なライブラリ(on raspberry pi)
sudo apt install libzbar0
sudo apt install libdmtx0 or libdmtx0b
pip install pyzbar==0.1.9
pip install pylibdtmx==0.1.10
"""
import cv2
import numpy as np
import traceback
import threading
import queue

from pydantic import BaseModel
from pyzbar.pyzbar import decode as zbar_decode
from pylibdmtx.pylibdmtx import decode as dmtx_decode
from typing import List, Union

try:
    from logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    from logging import getLogger
    logger = getLogger(__name__)


class CodeInfo(BaseModel):
    """読取結果の返り値フォーマット"""
    code_text: str = ''
    code_type: str = ''
    polygon: list = []


class CodeRect(BaseModel):
    """APIから返ってくるRect型の中身"""
    left: int = 0
    top: int = 0
    width: int = 0
    height: int = 0


class CodeReaderDaemon(threading.Thread):
    """APIのTimeoutが効かないので自作でTimeoutを実装"""

    def __init__(self, frame: np.ndarray, result_queue: queue.Queue,
                 *, code_type: str = 'QR'):
        super().__init__()
        self.daemon = True
        self.frame = frame
        self.result_queue = result_queue
        self.code_type = code_type

    def run(self) -> None:
        if self.code_type == 'QR':
            # NOTE: QRCode
            self.result_queue.put(zbar_decode(self.frame))
        else:
            # NOTE: DataMatrix
            self.result_queue.put(dmtx_decode(self.frame, max_count=1))


class CodeDecoder:
    """
    コード読取の基底クラス
    """

    def getErrorInfo(self) -> str:
        """エラートレース"""
        traceback_info = traceback.format_exc()
        return traceback_info

    def checkKernelSize(self, k_size: int) -> int:
        if k_size % 2 == 0:
            k_size -= 1
        if k_size < 3:
            return 3
        return k_size

    def checkImageChannel(self, image: np.ndarray) -> np.ndarray:
        """
        3チャンネルの画像をグレイスケールに変換
        APIに入れるときはグレイスケールのため、チェックを実施
        """
        if image.ndim == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    def emphasizeContrast(self, image: np.ndarray,
                          grid_size: int = 8, thresh: float = 2.0) -> np.ndarray:
        """ヒストグラム平坦化

        Args:
            g_scale (np.ndarray): _description_
            k_size (int, optional): _description_. Defaults to 8.
            thresh (float, optional): _description_. Defaults to 2.0.

        Returns:
            np.ndarray: _description_
        """
        image = self.checkImageChannel(image)
        clahe = cv2.createCLAHE(clipLimit=thresh, tileGridSize=(grid_size, grid_size))
        dst = clahe.apply(image)
        return dst

    def adaptiveThreshold(self, image: np.ndarray,
                          *, k_size: int = -1, c_val: int = 10) -> np.ndarray:
        """適応的二値化\n
        k_sizeでぼかした画像と元画像の差分をとり、c_valで二値化

        Args:
            g_scale (np.ndarray): _description_
            k_size (int, optional): _description_
            c_val (int, optional): _description_

        Returns:
            np.ndarray: _description_
        """
        h, w = image.shape[:2]
        if k_size < 0:
            # NOTE: 偶数であれば-1して奇数にする
            k_size = int(min([h, w]) / 7)

        k_size = self.checkKernelSize(k_size)

        image = self.checkImageChannel(image)
        dst = cv2.adaptiveThreshold(src=image,
                                    maxValue=255,
                                    adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    thresholdType=cv2.THRESH_BINARY,
                                    blockSize=k_size,
                                    C=c_val)
        return dst

    def decodeText(self, data: bytes) -> str:
        """
        テキストのデコード
        shift-jis(主に日本語)だとdecodeでエラーが出るので例外処理追加
        """
        try:
            text = data.decode('utf-8')
            return text
        except UnicodeDecodeError:
            text = data.decode('shift-jis')
            return text
        except Exception:
            print(self.getErrorInfo())
            return ''

    def decodeDataMatrix(self,
                         frame: np.ndarray,
                         timeout: float = 1.0,
                         use_daemon: bool = False) -> list:
        """Timeoutを実装したDatamatrixの読取"""

        if use_daemon:
            res_queue: queue.Queue = queue.Queue()
            CodeReaderDaemon(frame=frame,
                             result_queue=res_queue,
                             code_type='DM').start()
            try:
                return res_queue.get(block=True, timeout=timeout)
            except queue.Empty:
                logger.info(f'Timeout: {timeout:2f}[sec]')
                return []
        else:
            res = dmtx_decode(frame, max_count=1)
            return res

    def decodeQRCode(self, frame: np.ndarray,
                     timeout: float = 1.0) -> list:
        """QRの方はただのwrapper"""
        return zbar_decode(frame)

    def calculateDiagonalCorners(self, rect: CodeRect, size: tuple) -> list:
        """対角二点を計算"""
        height, _ = size
        pt1 = (int(rect.left), int(height - rect.top))
        pt2 = (int(rect.left + rect.width), int(height - rect.top - rect.height))
        return [
            (pt1[0], pt1[1]),
            (pt2[0], pt2[1]),
        ]

    def calculateSquareCorners(self, rect: CodeRect, size: tuple) -> list:
        """DataMatrixの方は角4点の座標が返ってこないので自力で計算"""
        height, _ = size
        pt1 = (int(rect.left), int(height - rect.top))
        pt2 = (int(rect.left + rect.width), int(height - rect.top - rect.height))

        center_x = (pt1[0] + pt2[0]) / 2
        center_y = (pt1[1] + pt2[1]) / 2
        dx, dy = (pt2[0] - pt1[0]), (pt2[1] - pt1[1])
        diagonal_length = np.sqrt(dx ** 2 + dy ** 2)
        radius = diagonal_length / 2
        unit_vector = (dx / diagonal_length, dy / diagonal_length)
        normal_vector = (int(-unit_vector[1] * radius), int(unit_vector[0] * radius))

        return [
            (pt1[0], pt1[1]),
            (int(center_x + normal_vector[0]), int(center_y + normal_vector[1])),
            (pt2[0], pt2[1]),
            (int(center_x - normal_vector[0]), int(center_y - normal_vector[1]))
        ]

    def drawPolygon(self, img: np.ndarray, polygon: Union[list, np.ndarray], *,
                    thickness: int = 2, color: tuple = (0, 255, 0)) -> np.ndarray:
        """ポリゴン描画"""
        polygon_ = [[round(pt[0]), round(pt[1])] for pt in polygon]
        img = cv2.polylines(img=img, pts=[np.array(polygon_)],
                            isClosed=True, color=color, thickness=thickness)
        return img

    def drawCodePosition(self, image: np.ndarray, c_info_l: List[CodeInfo]) -> np.ndarray:
        """コードの検出位置を描画"""
        dst = image.copy()
        for c_info in c_info_l:
            dst = self.drawPolygon(dst, polygon=c_info.polygon, thickness=3)
        return dst


class QRCodeReader(CodeDecoder):
    """
    QRコードの読み取りクラス
    """

    def __init__(self):
        super().__init__()

    def _read(self, frame: np.ndarray) -> List[CodeInfo]:
        """QRコードの読み取り"""
        image = frame.copy()
        # NOTE: 入力チェック
        image = self.checkImageChannel(image)
        # NOTE: 読取
        codes = self.decodeQRCode(image)
        if not codes:
            return []

        # NOTE: バーコードも読取対象に入っているのでフィルタ
        qrcodes = [code for code in codes if code.type == 'QRCODE']

        if not qrcodes:
            return []

        data: List[CodeInfo] = []

        for code_ in qrcodes:
            code_text = self.decodeText(code_.data)
            data.append(CodeInfo(code_text=code_text,
                                 code_type=code_.type,
                                 polygon=code_.polygon.copy()))
        return data

    def read(self, frame: np.ndarray) -> List[CodeInfo]:
        """
        QRの読み取り
        読取失敗したら色んな前処理をしてリトライする
        """
        image = frame.copy()
        res = self._read(image)
        if res:
            # NOTE: コードが見つかれば返す
            return res

        # NOTE: コントラスト強調でリトライ
        img_1 = self.emphasizeContrast(image)
        res = self._read(img_1)
        if res:
            # NOTE: コードが見つかれば返す
            return res

        # NOTE: 適応的二値化でリトライ
        img_1 = self.adaptiveThreshold(image)
        res = self._read(img_1)
        if res:
            # NOTE: コードが見つかれば返す
            return res
        return []


class DataMatrixReader(CodeDecoder):
    """
    データマトリクスの読み取りクラス
    """

    def __init__(self):
        super().__init__()

    def _read(self, frame: np.ndarray) -> List[CodeInfo]:
        """データマトリクスの読み取り"""
        image = frame.copy()
        # NOTE: 入力チェック
        image = self.checkImageChannel(image)
        # NOTE: 読取
        dmtxs = self.decodeDataMatrix(image, timeout=1.0)

        if not dmtxs:
            return []

        data: List[CodeInfo] = []

        for code_ in dmtxs:
            code_text = self.decodeText(code_.data)
            # code_polygon = self.calculateSquareCorners(rect=code_.rect,
            #                                            size=image.shape[:2])
            code_polygon = self.calculateDiagonalCorners(rect=code_.rect,
                                                         size=image.shape[:2])
            data.append(CodeInfo(code_text=code_text,
                                 code_type='DataMatrix',
                                 polygon=code_polygon.copy()))
        return data

    def read(self, frame: np.ndarray) -> List[CodeInfo]:
        """
        DataMatrixの読み取り
        読取失敗したら色んな前処理をしてリトライする
        """
        image = frame.copy()
        res = self._read(image)
        if res:
            # NOTE: コードが見つかれば返す
            return res

        # NOTE: コントラスト強調でリトライ
        img_1 = self.emphasizeContrast(image)
        res = self._read(img_1)
        if res:
            # NOTE: コードが見つかれば返す
            return res

        # NOTE: 適応的二値化でリトライ
        img_1 = self.adaptiveThreshold(image)
        res = self._read(img_1)
        if res:
            # NOTE: コードが見つかれば返す
            return res
        return []


if __name__ == '__main__':
    """
    テストコード
    """
    def imshow(src: np.ndarray) -> None:
        import matplotlib.pyplot as plt
        if src.ndim == 3:
            plt.imshow(cv2.cvtColor(src, cv2.COLOR_BGR2RGB))  # type: ignore
            plt.show()
        else:
            plt.imshow(cv2.cvtColor(src, cv2.COLOR_GRAY2RGB))  # type: ignore
            plt.show()

    def rotate_image(src: np.ndarray, angle: float) -> np.ndarray:
        h, w = src.shape[:2]
        if h == 0 or w == 0:
            logger.error('Image has zero Dimention')

        trans = cv2.getRotationMatrix2D(center=(int(w / 2), int(h / 2)),
                                        angle=angle, scale=1)

        img = cv2.warpAffine(src, trans, (w, h))

        return img

    # qr = QRCodeReader()
    dmtx = DataMatrixReader()
    image = cv2.imread(r'C:\Users\J100048001\Desktop\dmtx4.jpg')
    image = rotate_image(image, 10)
    image = dmtx.emphasizeContrast(image)
    imshow(image)
    # qr_res = qr.read(image)
    dm_res = dmtx.read(image)
    print(dm_res)

    # qr_img = qr.drawCodePosition(image, qr_res)
    dm_img = dmtx.drawCodePosition(image, dm_res)

    imshow(dm_img)
