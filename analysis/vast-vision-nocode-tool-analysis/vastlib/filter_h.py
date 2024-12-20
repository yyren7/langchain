# ===============================================================================
# Name      : filter_h.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2023-07-31 11:05
# Copyirght 2021 Hiroya Aoyama
# ===============================================================================
import numpy as np
import cv2
from typing import Tuple

# NOTE: フィルタリスト
# 先鋭化フィルタ
# 平滑化フィルタ
# ノイズ除去フィルタ
# リアルタイム差分フィルタ
# モルフォロジー処理
# ヒストグラム平坦化
# ラプラシアンフィルタ
# ソーベルフィルタ
# MeanShiftフィルタ
# マスクを考慮した大津の二値化


def load_image(path) -> np.ndarray:
    img = cv2.imread(path)
    return img


def sharpening_fileter(image: np.ndarray, k: int = 1) -> np.ndarray:
    """先鋭化フィルタ

    Args:
        image (np.ndarray): 入力画像
        k (int, optional): ゲイン

    Returns:
        np.ndarray: _description_
    """
    proc_image = image.copy()
    kernel = np.array([
        [-k / 9, -k / 9, -k / 9],
        [-k / 9, 1 + 8 * k / 9, -k / 9],
        [-k / 9, -k / 9, -k / 9]
    ], dtype=np.float32)

    proc_image = cv2.filter2D(proc_image, -1, kernel).astype(np.uint8)
    return proc_image


def noise_smoothing_filter(image: np.ndarray, ksize: int = 5) -> np.ndarray:
    """平滑化フィルタ

    Args:
        image (np.ndarray): 入力画像
        ksize (int, optional): カーネルサイズ

    Returns:
        np.ndarray: _description_
    """
    proc_image = image.copy()
    proc_image = cv2.blur(src=proc_image, ksize=(ksize, ksize))
    proc_image = cv2.medianBlur(src=proc_image, ksize=ksize)

    return proc_image


def noise_removal_filter(image: np.ndarray,
                         h: int = 10,
                         template_patch_size: int = 7,
                         window_size: int = 21) -> np.ndarray:
    """ノイズ除去フィルタ

    Args:
        image (np.ndarray): 入力画像(グレースケール)
        h (int, optional): ノイズ除去の強弱
        template_patch_size (int, optional): テンプレート窓の大きさ(奇数)
        window_size (int, optional): 探索窓の大きさ(奇数)

    Returns:
        np.ndarray: _description_
    """
    proc_image = image.copy()
    image = cv2.fastNlMeansDenoising(
        src=image,
        dst=None,
        h=h,  # noise strength
        templateWindowSize=template_patch_size,
        searchWindowSize=window_size
    )

    return proc_image


def realtime_difference_filter(image: np.ndarray,
                               itr: int = 1,
                               ksize: int = 3,
                               noise: str = 'black',
                               threshold: int = 100) -> np.ndarray:
    """リアルタイム差分フィルタ

    Args:
        image (np.ndarray): 入力画像
        itr (int, optional): モルフォロジー処理の試行回数
        ksize (int, optional): カーネルサイズ
        noise (str, optional): ノイズの色. Defaults to 'black'.
        threshold (int, optional): 差分閾値. Defaults to 100.

    Returns:
        np.ndarray: _description_
    """
    proc_image = image.copy()

    if noise == 'black':
        op1 = cv2.MORPH_OPEN
        op2 = cv2.MORPH_CLOSE
    else:  # white
        op1 = cv2.MORPH_CLOSE
        op2 = cv2.MORPH_OPEN

    kernel = np.ones((ksize, ksize), np.uint8)

    proc_image = cv2.morphologyEx(src=proc_image,
                                  op=op1,
                                  kernel=kernel,
                                  iterations=itr)
    proc_image = cv2.morphologyEx(src=proc_image,
                                  op=op2,
                                  kernel=kernel,
                                  iterations=itr)
    # NOTE: 差分フィルタ
    diff_image = image.astype(np.float32) - proc_image.astype(np.float32)
    diff_map_image = np.where((np.abs(diff_image) > threshold), 255, 0)
    return diff_map_image.astype(np.uint8)


def contrast_enhancement_filter(image: np.ndarray, grid_size: int,
                                clip_limit: float) -> np.ndarray:
    """ヒストグラム平坦化

    Args:
        image (np.ndarray): 入力画像(グレイスケール)

    Returns:
        np.ndarray: _description_
    """
    proc_image = image.copy()
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(grid_size, grid_size))
    proc_image = clahe.apply(proc_image)
    return proc_image


def laplacian_filter(image: np.ndarray) -> np.ndarray:
    """ラプラシアンフィルタ

    Args:
        image (np.ndarray): 入力画像(グレイスケール)

    Returns:
        np.ndarray: _description_
    """
    proc_image = image.copy()

    kernel = np.array([
        [1, 1, 1],
        [1, -8, 1],
        [1, 1, 1]
    ], dtype=np.float32)

    proc_image = cv2.filter2D(proc_image, -1, kernel).astype(np.uint8)
    return proc_image


def sobel_filter(image: np.ndarray, axis:str="x") -> Tuple[np.ndarray, np.ndarray]:
    """ソーベルフィルタ

    Args:
        image (np.ndarray): 入力画像(グレイスケール)

    Returns:
        np.ndarray: _description_
    """

    proc_image = image.copy()

    if axis == "x":
        kernel_x = np.array([
            [-1, 0, 1],
            [-2, 0, 2],
            [-1, 0, 1]
        ], dtype=np.float32)

        sobel = cv2.filter2D(proc_image, -1, kernel_x)

    else:
        kernel_y = np.array([
            [-1, -2, -1],
            [0, 0, 0],
            [1, 2, 1]
        ], dtype=np.float32)

        sobel = cv2.filter2D(proc_image, -1, kernel_y)

    return sobel


def mean_shift_filter(image: np.ndarray, sp: float, sr: float) -> np.ndarray:
    """Mean-Shift法による画像セグメンテーション(減色処理)

    Args:
        image (np.ndarray): 入力画像
        sp (float): 空間窓の半径
        sr (float): 色空間窓の半径

    Returns:
        np.ndarray: 出力画像
    """

    proc_image = image.copy()
    shifted = cv2.pyrMeanShiftFiltering(src=proc_image, sp=sp, sr=sr)
    return shifted


def distance_transform(binary_image: np.ndarray, mask_size: int = 5) -> np.ndarray:
    """距離変換

    Args:
        binary_image (np.ndarray): 入力画像(二値化)
        mask_size (int, optional): マスクサイズ. Defaults to 5.

    Returns:
        np.ndarray: _description_
    """
    dist_transform = cv2.distanceTransform(src=binary_image,
                                           distanceType=cv2.DIST_L2,
                                           maskSize=mask_size)
    return dist_transform


def watershed(image: np.ndarray, markers: np.ndarray) -> np.ndarray:
    """領域分割

    Args:
        image (np.ndarray): 入力画像
        markers (np.ndarray): マーカー画像

    Returns:
        np.ndarray: _description_
    """
    img = image.copy()
    mker = cv2.watershed(img, markers)
    # NOTE: 背景塗りつぶし
    img[mker == -1] = [255, 0, 0]
    return img


def search_threshold(img_gray: np.ndarray,
                     mask: np.ndarray,
                     min_th: int = 0,
                     max_th: int = 256,
                     high_contrast_ratio: float = 1.0,
                     low_limit_th: int = 125) -> int:
    """ Search threshold by Otsu method with mask.
    This function is referenced this site.
    https://www.programmersought.com/article/32286738061/

    Parameters
    -------------------
    img_gray : np.ndarray
    mask : np.ndarray
        Mask image contains only 0 and 255
    min_th : int = 0
    max_th : int = 256
    high_contrast_ratio : float = 1.0
        If this value < 1.0, percentage of cumsum histgram will be checked.
    lowest_th : int = 125

    Returns
    -------------------
    int
        Detected thresholed
    """

    px_counts = np.count_nonzero(mask)

    hist = cv2.calcHist(images=[img_gray], channels=[0], mask=mask,
                        histSize=[256], ranges=[0, 256])

    # NOTE: ヒストグラムの累積和を先に求めることで、ループ中の合計計算を省く
    cum_hist = np.cumsum(hist)

    # NOTE: カウントがなかったbinは0、それ以外の画素値だけが残る
    pixel_sum_hist = [hist[i] * i for i in range(256)]
    cum_pixel_sum_hist = np.cumsum(pixel_sum_hist)

    # NOTE: ループ回数削減のため最も明るい画素チェック
    # NOTE: max値より0.3%おちる値を閾値探索上限にすることで、
    # 黒一色の画像をはじく準備をする
    cum_hist_ratio = cum_pixel_sum_hist / np.max(cum_pixel_sum_hist)
    eval_cum_hist = np.where(cum_hist_ratio <= high_contrast_ratio)
    max_th = eval_cum_hist[0][-1]

    if max_th < low_limit_th:  # NOTE: 暗い色一色なので人間の直感と反する閾値が検出されかねない
        suitable_th = low_limit_th
        return suitable_th

    max_g = 0
    suitable_th = min_th

    # NOTE: If you can determine the approximate range of the threshold,
    # you can set it here to reduce the number of threshold traversals
    th_list = [i for i in range(min_th, max_th) if int(hist[i][0]) != 0]
    for th in th_list:

        # NOTE: 累積和を使ってthを境にしたクラスそれぞれ画素値合計を計算
        fore_pix = cum_hist[-1] - cum_hist[th]
        back_pix = cum_hist[th]
        if 0 == fore_pix:
            break
        if 0 == back_pix:
            continue

        # NOTE: 藤城にはこの計算式導出過程が理解できなかった
        w0 = float(fore_pix) / px_counts
        u0 = float(cum_pixel_sum_hist[-1]
                   - cum_pixel_sum_hist[th]) / fore_pix
        w1 = float(back_pix) / px_counts
        u1 = float(cum_pixel_sum_hist[th]) / back_pix

        # NOTE: intra-class variance
        g = w0 * w1 * (u0 - u1) * (u0 - u1)
        if g > max_g:
            max_g = g
            suitable_th = th

    return suitable_th


if __name__ == '__main__':
    # import matplotlib.pyplot as plt
    #
    # def imshow(src):
    #     plt.imshow(cv2.cvtColor(src, cv2.COLOR_BGR2RGB))  # type: ignore
    #     plt.show()
    #
    # # myfilter = FilterClass()
    # img = load_image("test.jpg")
    # img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # imshow(img)
    # # dst = myfilter.realtime_difference_filter(img)
    # # dst = myfilter.sharpening_fileter(img)
    # # dst = myfilter.contrast_enhancement_filter(img)
    # # laplacian = cv2.Laplacian(img.astype(np.float32), cv2.CV_64F)
    # # dst1, dst2 = myfilter.sobel(img)
    # # dst = dst1 + dst2
    # dst = noise_removal_filter(img)
    # imshow(dst.astype(np.uint8))

    img = np.load("../sample.npy")
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hoge = contrast_enhancement_filter(img, 8, 40.0)