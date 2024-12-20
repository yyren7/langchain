# ===============================================================================
# Name      : code_reader.py
# Version   : 1.0.0
# Brief     :
# Copyirght 2021 Hiroya Aoyama
# ===============================================================================

"""

    必要なライブラリ(on raspberry pi)
    sudo apt install libzbar0
    sudo apt install libdmtx0 or libdmtx0b
    pip install pyzbar == 0.1.8
    pip install pylibdtmx == 0.1.9

    # NOTE: 使い方
    image = capture()
    # NOTE: QRCode
    success, data, code_img = CodeReader.read_qrcode()
    # NOTE: DataMatrix
    success, data, code_img = CodeReader.read_datamatrix()
    
    print(data)
"""

import cv2
import numpy as np
# import qrcode
from pyzbar.pyzbar import decode as zbar_decode
# from pyzbar.pyzbar import ZBarSymbol
from pylibdmtx.pylibdmtx import encode as dmtx_encode
from pylibdmtx.pylibdmtx import decode as dmtx_decode
from PIL import Image
# import time
import threading
import queue
import math
# BARCODE_TYPE = ['EAN13','UPCA','UPCE','EAN8','CODE128','CODE39']
try:
    from logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    from logging import getLogger
    logger = getLogger(__name__)


def imshow(src):
    cv2.imshow("barcode", src)
    cv2.waitKey(0)


class CR_Daemon(threading.Thread):
    def __init__(self, frame=None, result_queue=None):
        super().__init__()
        self.daemon = True
        self.frame = frame
        self.result_queue = result_queue

    def run(self):
        # maxcount 1
        self.result_queue.put(dmtx_decode(self.frame, max_count=1))


def decode_datamatrix(frame, timeout=5):
    res_queue: queue.Queue = queue.Queue()
    CR_Daemon(frame=frame, result_queue=res_queue).start()
    try:
        return res_queue.get(block=True, timeout=timeout)
    except queue.Empty:
        logger.info(f'Timeout: {timeout:2f}[sec]')
        return None


def rot(centerPoint, angle, X_Mat):
    [xc, yc] = centerPoint
    dr = angle * math.pi / 180

    # 回転行列
    R_Mat = np.array([[math.cos(dr), -math.sin(dr), xc - xc * math.cos(dr) + yc * math.sin(dr)],
                      [math.sin(dr), math.cos(dr), yc - xc * math.sin(dr) - yc * math.cos(dr)]])
    # [0, 0, 1]])
    Y_Mat = np.dot(R_Mat, X_Mat)

    return Y_Mat


def calc_polygon(rect, img_size):
    (width, height) = img_size
    asp = [1, 1]
    # 対角線
    diagonal_square = rect.height**2 + rect.width**2
    # 一辺
    short_length = int(math.sqrt(diagonal_square / (1.0 + (asp[1] / asp[0])**2)))
    long_length = int(short_length * (asp[1] / asp[0]))
    angle = math.atan(rect.height / rect.width) * 180 / math.pi
    angle_bias = math.atan((asp[0] / asp[1])) * 180 / math.pi
    angle = int(angle - angle_bias)
    (xmin, ymin, xmax, ymax) = (
        int(rect.left),
        int(height - rect.top - rect.height),
        int(rect.left + rect.width),
        int(height - rect.top)
    )
    [xc, yc] = [int((xmin + xmax) / 2), int((ymin + ymax) / 2)]
    xmin, ymin, xmax, ymax = int(xc - long_length / 2), \
        int(yc - short_length / 2), \
        int(xc + long_length / 2), \
        int(yc + short_length / 2)
    xmat = np.array([[xmin, ymin, 1], [xmin, ymax, 1], [xmax, ymax, 1], [xmax, ymin, 1]]).T
    ymat = rot([xc, yc], -angle, xmat)
    pts = ymat.T.astype(np.int32)
    return pts


def text_decoder(data: bytes):
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        text = data.decode('shift-jis')
    except Exception as e:
        logger.error(str(e))
        text = 'Decode Error'
    return text


def contrast_enhancement_filter(image: np.ndarray):
    proc_image = image.copy()
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    proc_image = clahe.apply(proc_image)
    return proc_image


def check_roi(img: np.ndarray, r_data: list) -> bool:
    height, width = img.shape[:2]
    if r_data[0] < 0 or r_data[2] > height:
        return False
    elif r_data[1] < 0 or r_data[3] > width:
        return False
    else:
        return True


def crop_roi(img: np.ndarray, r_data: list) -> np.ndarray:
    roi = img[r_data[0]:r_data[2], r_data[1]:r_data[3]]
    return roi


def insert_roi(img: np.ndarray, roi: np.ndarray, r_data: list) -> np.ndarray:
    img[r_data[0]:r_data[2], r_data[1]:r_data[3]] = roi
    dst = cv2.rectangle(img, pt1=(r_data[1], r_data[0]),
                        pt2=(r_data[3], r_data[2]),
                        color=(200, 200, 50),
                        thickness=3)
    logger.info(dst.shape)
    return dst


class ThreadWithResult(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, *, daemon=None):
        def function():
            self.success, self.data, self.dst = target(*args, **kwargs)
        super().__init__(group=group, target=function, name=name, daemon=daemon)


class CodeReader:

    def read_code(self, img: np.ndarray):
        thread_bar = ThreadWithResult(target=CodeReader.read_barcode, args=(img,))
        thread_qr = ThreadWithResult(target=CodeReader.read_qrcode, args=(img,))
        thread_mtx = ThreadWithResult(target=CodeReader.read_datamatrix, args=(img,))
        thread_bar.start()
        thread_qr.start()
        thread_mtx.start()
        thread_bar.join()
        thread_qr.join()
        thread_mtx.join()

        if thread_bar.success:
            return thread_bar.success, thread_bar.data, thread_bar.dst
        elif thread_qr.success:
            return thread_qr.success, thread_qr.data, thread_qr.dst
        elif thread_mtx.success:
            return thread_mtx.success, thread_mtx.data, thread_mtx.dst
        else:
            return False, [{'TEXT': ''}], None

    @staticmethod
    def read_barcode(img: np.ndarray, roi_data: list = None):
        origi_img = img.copy()
        code_img = img.copy()

        if roi_data is not None:
            s = check_roi(code_img, roi_data)
            if not s:
                return False, [{'TEXT': 'ROI is out of range'}], code_img
            code_img = crop_roi(code_img, roi_data)

        if code_img.ndim == 3:
            code_img = cv2.cvtColor(code_img, cv2.COLOR_BGR2GRAY)
        else:
            origi_img = cv2.cvtColor(origi_img, cv2.COLOR_GRAY2BGR)

        codes = zbar_decode(code_img)
        if not(codes):
            codes = zbar_decode(contrast_enhancement_filter(code_img))

        code_img = cv2.cvtColor(code_img, cv2.COLOR_GRAY2BGR)

        if codes:
            barcodes = [code for code in codes if code.type != 'QRCODE']
            if len(barcodes) != 0:
                data = []
                for barcode in barcodes:
                    code_text = text_decoder(barcode.data)
                    code_type = barcode.type
                    code_polygon = barcode.polygon
                    code_img = cv2.polylines(code_img, [np.array(code_polygon)], isClosed=True, color=(0, 255, 0), thickness=5)
                    data.append({
                        'TEXT': code_text,
                        'TYPE': code_type,
                        'POLYGON': code_polygon
                    })
                if roi_data is not None:
                    code_img = insert_roi(origi_img, code_img, roi_data)
                return True, data, code_img

            else:
                if roi_data is not None:
                    code_img = insert_roi(origi_img, code_img, roi_data)
                return False, [{'TEXT': ''}], None
        else:
            if roi_data is not None:
                code_img = insert_roi(origi_img, code_img, roi_data)
            return False, [{'TEXT': ''}], None

    @staticmethod
    def read_qrcode(img: np.ndarray, roi_data: list = None):
        # from pyzbar.pyzbar import Decoded
        # qrcode: Decoded
        origi_img = img.copy()
        code_img = img.copy()

        if roi_data is not None:
            s = check_roi(code_img, roi_data)
            if not s:
                return False, [{'TEXT': 'ROI is out of range'}], code_img
            code_img = crop_roi(code_img, roi_data)

        if code_img.ndim == 3:
            code_img = cv2.cvtColor(code_img, cv2.COLOR_BGR2GRAY)
        else:
            origi_img = cv2.cvtColor(origi_img, cv2.COLOR_GRAY2BGR)

        codes = zbar_decode(code_img)
        if not(codes):
            codes = zbar_decode(contrast_enhancement_filter(code_img))

        code_img = cv2.cvtColor(code_img, cv2.COLOR_GRAY2BGR)

        if codes:
            qrcodes = [code for code in codes if code.type == 'QRCODE']
            if len(qrcodes) != 0:
                data = []
                for qrcode in qrcodes:
                    code_text = text_decoder(qrcode.data)
                    code_type = qrcode.type
                    code_polygon = qrcode.polygon
                    code_img = cv2.polylines(code_img, [np.array(code_polygon)], isClosed=True, color=(0, 255, 0), thickness=5)
                    data.append({
                        'TEXT': code_text,
                        'TYPE': code_type,
                        'POLYGON': code_polygon
                    })

                if roi_data is not None:
                    code_img = insert_roi(origi_img, code_img, roi_data)
                return True, data, code_img

            else:
                if roi_data is not None:
                    code_img = insert_roi(origi_img, code_img, roi_data)
                return False, [{'TEXT': ''}], code_img
        else:
            if roi_data is not None:
                code_img = insert_roi(origi_img, code_img, roi_data)
            return False, [{'TEXT': ''}], code_img

    @staticmethod
    def read_datamatrix(img: np.ndarray, roi_data: list = None):
        # from pylibdmtx.pylibdmtx import Decoded
        # code: Decoded
        origi_img = img.copy()
        code_img = img.copy()

        if roi_data is not None:
            s = check_roi(code_img, roi_data)
            if not s:
                return False, [{'TEXT': 'ROI is out of range'}], code_img
            code_img = crop_roi(code_img, roi_data)

        if code_img.ndim == 3:
            code_img = cv2.cvtColor(code_img, cv2.COLOR_BGR2GRAY)
        else:
            origi_img = cv2.cvtColor(origi_img, cv2.COLOR_GRAY2BGR)

        codes = decode_datamatrix(code_img, timeout=0.2)
        if not(codes):
            codes = decode_datamatrix(contrast_enhancement_filter(code_img), timeout=0.2)

        code_img = cv2.cvtColor(code_img, cv2.COLOR_GRAY2BGR)

        if codes:
            h, w = code_img.shape[:2]
            data = []
            # logger.info(codes)
            for code in codes:
                # logger.info(code)
                code_text = text_decoder(code.data)
                code_type = "DATAMATRIX"
                code_polygon = calc_polygon(rect=code.rect, img_size=(w, h))
                code_img = cv2.polylines(code_img, [np.array(code_polygon)], isClosed=True, color=(0, 255, 0), thickness=5)
                data.append({
                    'TEXT': code_text,
                    'TYPE': code_type,
                    'POLYGON': code_polygon
                })
            if roi_data is not None:
                code_img = insert_roi(origi_img, code_img, roi_data)
            return True, data, code_img
        else:
            if roi_data is not None:
                code_img = insert_roi(origi_img, code_img, roi_data)
            return False, [{'TEXT': ''}], code_img


class CodeCreator:
    @staticmethod
    def bit2cv(src):
        new_image = np.array(src, dtype=np.uint8)
        new_image = np.where(new_image == 1, 255, 0)
        return new_image.astype(np.uint8)

    @staticmethod
    def pil2cv(src):
        new_image = np.array(src, dtype=np.uint8)
        if new_image.ndim == 2:
            pass
        elif new_image.shape[2] == 3:
            new_image = new_image[:, :, ::-1]
        elif new_image.shape[2] == 4:
            new_image = new_image[:, :, [2, 1, 0, 3]]
        return new_image

    @staticmethod
    def create_qrcode(code_txt):
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=5,  # default: 10 # セルの大きさ
            border=0,  # default: 4 # 外枠の幅
        )
        qr.add_data(code_txt)
        qr.make(fit=True)
        img = qr.make_image()
        # img.save('qrcode.jpg')
        return CodeCreator.bit2cv(img)

    @staticmethod
    def create_datamatrix(code_txt, code_size='32x32'):
        encoded = dmtx_encode(code_txt.encode('utf-8'), size=code_size)
        code_img = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
        return CodeCreator.pil2cv(code_img)
