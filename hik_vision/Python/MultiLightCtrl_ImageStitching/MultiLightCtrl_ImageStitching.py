# -- coding: utf-8 --

import sys
from ctypes import *

sys.path.append("../MvImport")
from MvCameraControl_class import *

exposure_num = 2  # 分时频闪的灯数, 默认曝光个数为2

HB_format_list = [
    PixelType_Gvsp_HB_Mono8,
    PixelType_Gvsp_HB_Mono10,
    PixelType_Gvsp_HB_Mono10_Packed,
    PixelType_Gvsp_HB_Mono12,
    PixelType_Gvsp_HB_Mono12_Packed,
    PixelType_Gvsp_HB_Mono16,
    PixelType_Gvsp_HB_BayerGR8,
    PixelType_Gvsp_HB_BayerRG8,
    PixelType_Gvsp_HB_BayerGB8,
    PixelType_Gvsp_HB_BayerBG8,
    PixelType_Gvsp_HB_BayerRBGG8,
    PixelType_Gvsp_HB_BayerGR10,
    PixelType_Gvsp_HB_BayerRG10,
    PixelType_Gvsp_HB_BayerGB10,
    PixelType_Gvsp_HB_BayerBG10,
    PixelType_Gvsp_HB_BayerGR12,
    PixelType_Gvsp_HB_BayerRG12,
    PixelType_Gvsp_HB_BayerGB12,
    PixelType_Gvsp_HB_BayerBG12,
    PixelType_Gvsp_HB_BayerGR10_Packed,
    PixelType_Gvsp_HB_BayerRG10_Packed,
    PixelType_Gvsp_HB_BayerGB10_Packed,
    PixelType_Gvsp_HB_BayerBG10_Packed,
    PixelType_Gvsp_HB_BayerGR12_Packed,
    PixelType_Gvsp_HB_BayerRG12_Packed,
    PixelType_Gvsp_HB_BayerGB12_Packed,
    PixelType_Gvsp_HB_BayerBG12_Packed,
    PixelType_Gvsp_HB_YUV422_Packed,
    PixelType_Gvsp_HB_YUV422_YUYV_Packed,
    PixelType_Gvsp_HB_RGB8_Packed,
    PixelType_Gvsp_HB_BGR8_Packed,
    PixelType_Gvsp_HB_RGBA8_Packed,
    PixelType_Gvsp_HB_BGRA8_Packed,
    PixelType_Gvsp_HB_RGB16_Packed,
    PixelType_Gvsp_HB_BGR16_Packed,
    PixelType_Gvsp_HB_RGBA16_Packed,
    PixelType_Gvsp_HB_BGRA16_Packed]


def print_devices_info(deviceList):
    for index in range(0, deviceList.nDeviceNum):
        mvcc_dev_info = cast(deviceList.pDeviceInfo[index], POINTER(MV_CC_DEVICE_INFO)).contents
        if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE or mvcc_dev_info.nTLayerType == MV_GENTL_GIGE_DEVICE:
            print ("\ngige device: [%d]" % index)
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
                if per == 0:
                    break
                strModeName = strModeName + chr(per)
            print ("device model name: %s" % strModeName)

            nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
            nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
            nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
            nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
            print ("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
        elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
            print ("\nu3v device: [%d]" % index)
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                if per == 0:
                    break
                strModeName = strModeName + chr(per)
            print ("device model name: %s" % strModeName)

            strSerialNumber = ""
            for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                if per == 0:
                    break
                strSerialNumber = strSerialNumber + chr(per)
            print ("user serial number: %s" % strSerialNumber)
        elif mvcc_dev_info.nTLayerType == MV_GENTL_CAMERALINK_DEVICE:
            print ("\nCML device: [%d]" % index)
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stCMLInfo.chModelName:
                if per == 0:
                    break
                strModeName = strModeName + chr(per)
            print ("device model name: %s" % strModeName)

            strSerialNumber = ""
            for per in mvcc_dev_info.SpecialInfo.stCMLInfo.chSerialNumber:
                if per == 0:
                    break
                strSerialNumber = strSerialNumber + chr(per)
            print ("user serial number: %s" % strSerialNumber)
        elif mvcc_dev_info.nTLayerType == MV_GENTL_CXP_DEVICE:
            print ("\nCXP device: [%d]" % index)
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stCXPInfo.chModelName:
                if per == 0:
                    break
                strModeName = strModeName + chr(per)
            print ("device model name: %s" % strModeName)

            strSerialNumber = ""
            for per in mvcc_dev_info.SpecialInfo.stCXPInfo.chSerialNumber:
                if per == 0:
                    break
                strSerialNumber = strSerialNumber + chr(per)
            print ("user serial number: %s" % strSerialNumber)
        elif mvcc_dev_info.nTLayerType == MV_GENTL_XOF_DEVICE:
            print ("\nXoF device: [%d]" % index)
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stXoFInfo.chModelName:
                if per == 0:
                    break
                strModeName = strModeName + chr(per)
            print ("device model name: %s" % strModeName)

            strSerialNumber = ""
            for per in mvcc_dev_info.SpecialInfo.stXoFInfo.chSerialNumber:
                if per == 0:
                    break
                strSerialNumber = strSerialNumber + chr(per)
            print ("user serial number: %s" % strSerialNumber)

if __name__ == "__main__":

    try:
        # ch:初始化SDK | en: initialize SDK
        MvCamera.MV_CC_Initialize()

        deviceList = MV_CC_DEVICE_INFO_LIST()
        tlayerType = (MV_GIGE_DEVICE | MV_USB_DEVICE | MV_GENTL_CAMERALINK_DEVICE
                      | MV_GENTL_CXP_DEVICE | MV_GENTL_XOF_DEVICE)

        # ch:枚举设备 | en:Enum device
        ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
        if ret != 0:
            print("enum devices fail! ret[0x%x]" % ret)
            sys.exit()

        if deviceList.nDeviceNum == 0:
            print("find no device!")
            sys.exit()

        print("Find %d devices!" % deviceList.nDeviceNum)

        print_devices_info(deviceList)

        nConnectionNum = input("please input the number of the device to connect:")

        if int(nConnectionNum) >= deviceList.nDeviceNum:
            print("input error!")
            sys.exit()

        # ch:创建相机实例 | en:Create Camera Object
        cam = MvCamera()

        # ch:选择设备并创建句柄 | en:Select device and create handle
        stDeviceList = cast(deviceList.pDeviceInfo[int(nConnectionNum)], POINTER(MV_CC_DEVICE_INFO)).contents

        ret = cam.MV_CC_CreateHandle(stDeviceList)
        if ret != 0:
            raise Exception("create handle fail! ret[0x%x]" % ret)

        # ch:打开设备 | en:Open device
        ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            raise Exception("open device fail! ret[0x%x]" % ret)

        # ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
        if stDeviceList.nTLayerType == MV_GIGE_DEVICE or stDeviceList.nTLayerType == MV_GENTL_GIGE_DEVICE:
            nPacketSize = cam.MV_CC_GetOptimalPacketSize()
            if int(nPacketSize) > 0:
                ret = cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
                if ret != 0:
                    print("Warning: Set Packet Size fail! ret[0x%x]" % ret)
            else:
                print("Warning: Get Packet Size fail! ret[0x%x]" % nPacketSize)

        # ch:设置曝光组数为2 | en:Set light number to 2
        ret = cam.MV_CC_SetEnumValue("MultiLightControl", exposure_num)
        if ret != 0:
            pass

        # ch:设置触发模式为off | en:Set trigger mode as off
        ret = cam.MV_CC_SetEnumValue("TriggerMode", 0)
        if ret != 0:
            raise Exception("set trigger mode fail! ret[0x%x]" % ret)

        # ch:开始取流 | en:Start grab image
        ret = cam.MV_CC_StartGrabbing()
        if ret != 0:
            raise Exception("start grabbing fail! ret[0x%x]" % ret)

        # ch:获取的帧信息 | en: frame from device
        stOutFrame = MV_FRAME_OUT()
        memset(byref(stOutFrame), 0, sizeof(stOutFrame))

        # ch:解码参数 | en: decode parameters
        stDecodeParam = MV_CC_HB_DECODE_PARAM()
        memset(byref(stDecodeParam), 0, sizeof(stDecodeParam))

        # ch:重构参数 | en: reconstruct image parameters
        stReconstructParam = MV_RECONSTRUCT_IMAGE_PARAM()
        memset(byref(stReconstructParam), 0, sizeof(stReconstructParam))

        # ch:重构后的图像列表 | en: image data list,after reconstruction
        dst_buffer_list = []

        ret = cam.MV_CC_GetImageBuffer(stOutFrame, 20000)
        if ret == 0:
            print("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (
                stOutFrame.stFrameInfo.nWidth, stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nFrameNum))

            # ch:如果图像是HB格式，需要先解码 | en:If the image is HB format, should to be decoded first
            if stOutFrame.stFrameInfo.enPixelType in HB_format_list:
                # 获取数据包大小
                stParam = MVCC_INTVALUE()
                memset(byref(stParam), 0, sizeof(stParam))
                ret = cam.MV_CC_GetIntValue("PayloadSize", stParam)
                if 0 != ret:
                    raise Exception("Get PayloadSize fail! ret[0x%x]" % ret)
                nPayloadSize = stParam.nCurValue
                stDecodeParam.pSrcBuf = stOutFrame.pBufAddr
                stDecodeParam.nSrcLen = stOutFrame.stFrameInfo.nFrameLen
                stDecodeParam.pDstBuf = (c_ubyte * nPayloadSize)()
                stDecodeParam.nDstBufSize = nPayloadSize
                ret = cam.MV_CC_HBDecode(stDecodeParam)
                if ret != 0:
                    cam.MV_CC_FreeImageBuffer(stOutFrame)
                    raise Exception("HB Decode fail! ret[0x%x]" % ret)
                else:
                    stReconstructParam.nWidth = stDecodeParam.nWidth
                    stReconstructParam.nHeight = stDecodeParam.nHeight
                    stReconstructParam.enPixelType = stDecodeParam.enDstPixelType
                    stReconstructParam.pSrcData = stDecodeParam.pDstBuf
                    stReconstructParam.nSrcDataLen = stDecodeParam.nDstBufLen
            else:
                stReconstructParam.nWidth = stOutFrame.stFrameInfo.nWidth
                stReconstructParam.nHeight = stOutFrame.stFrameInfo.nHeight
                stReconstructParam.enPixelType = stOutFrame.stFrameInfo.enPixelType
                stReconstructParam.pSrcData = stOutFrame.pBufAddr
                stReconstructParam.nSrcDataLen = stOutFrame.stFrameInfo.nFrameLen

            stReconstructParam.nExposureNum = exposure_num
            stReconstructParam.enReconstructMethod = MV_SPLIT_BY_LINE

            dst_buffer_len = int(stReconstructParam.nSrcDataLen/exposure_num)
            for i in range(exposure_num):
                dst_buffer = (c_ubyte * dst_buffer_len)()
                dst_buffer_list.append(dst_buffer)
                stReconstructParam.stDstBufList[i].pBuf = dst_buffer_list[i]
                stReconstructParam.stDstBufList[i].nBufSize = dst_buffer_len

            # ch:图像重构 | en:Image Reconstruct
            ret = cam.MV_CC_ReconstructImage(stReconstructParam)
            if ret != 0:
                cam.MV_CC_FreeImageBuffer(stOutFrame)
                raise Exception("MV_CC_ReconstructImage fail! ret[0x%x]" % ret)
            else:
                print("Reconstruct image success")

            # ch: 保持图像到文件 | en: Save image to file
            file_name = "Image_w%d_h%d_fn%d.bmp" % (stReconstructParam.nWidth, stReconstructParam.nHeight,
                                                    stOutFrame.stFrameInfo.nFrameNum)
            c_file_path = file_name.encode('ascii')
            stSaveParam = MV_SAVE_IMAGE_TO_FILE_PARAM_EX()
            stSaveParam.enPixelType = stReconstructParam.enPixelType  # ch:相机对应的像素格式 | en:Camera pixel type
            stSaveParam.nWidth = stReconstructParam.nWidth  # ch:相机对应的宽 | en:Width
            stSaveParam.nHeight = stReconstructParam.nHeight  # ch:相机对应的高 | en:Height
            stSaveParam.nDataLen = stReconstructParam.nSrcDataLen
            stSaveParam.pData = (c_ubyte * stReconstructParam.nSrcDataLen)(*dst_buffer_list[0],*dst_buffer_list[1])
            stSaveParam.enImageType = MV_Image_Bmp  # ch:需要保存的图像类型 | en:Image format to save
            stSaveParam.pcImagePath = create_string_buffer(c_file_path)
            stSaveParam.iMethodValue = 1
            ret = cam.MV_CC_SaveImageToFileEx(stSaveParam)
            if ret != 0:
                print("Save stitched image fail! ret[0x%x]" % ret)
            else:
                print("Save stitched image success")
            cam.MV_CC_FreeImageBuffer(stOutFrame)
        else:
            raise Exception("no data[0x%x]" % ret)

        # ch:停止取流 | en:Stop grab image
        ret = cam.MV_CC_StopGrabbing()
        if ret != 0:
            raise Exception("stop grabbing fail! ret[0x%x]" % ret)

        # ch:关闭设备 | Close device
        ret = cam.MV_CC_CloseDevice()
        if ret != 0:
            raise Exception("close device fail! ret[0x%x]" % ret)

        # ch:销毁句柄 | Destroy handle0
        cam.MV_CC_DestroyHandle()

    except Exception as e:
        print(e)
        cam.MV_CC_CloseDevice()
        cam.MV_CC_DestroyHandle()
    finally:
        # ch:反初始化SDK | en: finalize SDK
        MvCamera.MV_CC_Finalize()
