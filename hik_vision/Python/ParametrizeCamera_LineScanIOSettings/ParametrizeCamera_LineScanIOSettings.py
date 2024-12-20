# -- coding: utf-8 --

import sys
import msvcrt

sys.path.append("../MvImport")
from MvCameraControl_class import *


winfun_ctype = WINFUNCTYPE

stFrameInfo = POINTER(MV_FRAME_OUT_INFO_EX)
pData = POINTER(c_ubyte)
FrameInfoCallBack = winfun_ctype(None, pData, stFrameInfo, c_void_p)

def image_callback(pData, pFrameInfo, pUser):
        stFrameInfo = cast(pFrameInfo, POINTER(MV_FRAME_OUT_INFO_EX)).contents
        if stFrameInfo:
            print("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (stFrameInfo.nWidth, stFrameInfo.nHeight, stFrameInfo.nFrameNum))

CALL_BACK_FUN = FrameInfoCallBack(image_callback)

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

        for i in range(0, deviceList.nDeviceNum):
            mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE or mvcc_dev_info.nTLayerType == MV_GENTL_GIGE_DEVICE:
                print("\ngige device: [%d]" % i)
                strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
                    if per == 0:
                        break
                    strModeName = strModeName + chr(per)
                print("device model name: %s" % strModeName)

                nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
                nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
                nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
                nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
                print("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
            elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                print("\nu3v device: [%d]" % i)
                strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                    if per == 0:
                        break
                    strModeName = strModeName + chr(per)
                print("device model name: %s" % strModeName)

                strSerialNumber = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                    if per == 0:
                        break
                    strSerialNumber = strSerialNumber + chr(per)
                print("user serial number: %s" % strSerialNumber)
            elif mvcc_dev_info.nTLayerType == MV_GENTL_CAMERALINK_DEVICE:
                print("\nCML device: [%d]" % i)
                strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stCMLInfo.chModelName:
                    if per == 0:
                        break
                    strModeName = strModeName + chr(per)
                print("device model name: %s" % strModeName)

                strSerialNumber = ""
                for per in mvcc_dev_info.SpecialInfo.stCMLInfo.chSerialNumber:
                    if per == 0:
                        break
                    strSerialNumber = strSerialNumber + chr(per)
                print("user serial number: %s" % strSerialNumber)
            elif mvcc_dev_info.nTLayerType == MV_GENTL_CXP_DEVICE:
                print("\nCXP device: [%d]" % i)
                strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stCXPInfo.chModelName:
                    if per == 0:
                        break
                    strModeName = strModeName + chr(per)
                print("device model name: %s" % strModeName)

                strSerialNumber = ""
                for per in mvcc_dev_info.SpecialInfo.stCXPInfo.chSerialNumber:
                    if per == 0:
                        break
                    strSerialNumber = strSerialNumber + chr(per)
                print("user serial number: %s" % strSerialNumber)
            elif mvcc_dev_info.nTLayerType == MV_GENTL_XOF_DEVICE:
                print("\nXoF device: [%d]" % i)
                strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stXoFInfo.chModelName:
                    if per == 0:
                        break
                    strModeName = strModeName + chr(per)
                print("device model name: %s" % strModeName)

                strSerialNumber = ""
                for per in mvcc_dev_info.SpecialInfo.stXoFInfo.chSerialNumber:
                    if per == 0:
                        break
                    strSerialNumber = strSerialNumber + chr(per)
                print("user serial number: %s" % strSerialNumber)

        nConnectionNum = input("please input the number of the device to connect:")

        if int(nConnectionNum) >= deviceList.nDeviceNum:
            print("input error!")
            sys.exit()

        nTriggerIndex = input("Please Input trigger selector index: 0-FrameBurstStart, 1-LineStart:")
        if int(nTriggerIndex) not in {0, 1}:
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

        # ch:线阵相机帧触发预设置 | en:Settings in FrameBurstStart mode
        if int(nTriggerIndex) == 0:
            # ch:设置触发选项为FrameBurstStart | en:Set trigger selector as FrameBurstStart
            ret = cam.MV_CC_SetEnumValue("TriggerSelector", 6)
            if ret != 0:
                raise Exception("set trigger selector fail! ret[0x%x]" % ret)

            # ch:设置触发模式为on | en:Set trigger mode as on
            ret = cam.MV_CC_SetEnumValue("TriggerMode", 1)
            if ret != 0:
                raise Exception("set trigger mode fail! ret[0x%x]" % ret)

            # ch:设置触发源为Line0 | en:Set trigger source as Line0
            ret = cam.MV_CC_SetEnumValue("TriggerSource", 0)
            if ret != 0:
                raise Exception("set trigger source fail! ret[0x%x]" % ret)
        # ch:线阵相机行触发预设置 | en:Settings in LineStart mode
        else:
            # ch:设置触发选项为LineStart | en:Set trigger selector as LineStart
            ret = cam.MV_CC_SetEnumValue("TriggerSelector", 9)
            if ret != 0:
                raise Exception("set trigger selector fail! ret[0x%x]" % ret)

            # ch:设置触发模式为on | en:Set trigger mode as on
            ret = cam.MV_CC_SetEnumValue("TriggerMode", 1)
            if ret != 0:
                raise Exception("set trigger mode fail! ret[0x%x]" % ret)

            # ch:设置触发源为EncoderModuleOut | en:Set trigger source as EncoderModuleOut
            ret = cam.MV_CC_SetEnumValue("TriggerSource", 6)
            if ret != 0:
                raise Exception("set trigger source fail! ret[0x%x]" % ret)

            # ch:设置编码器选项为Encoder0 | en:Set encoder selector as Encoder0
            ret = cam.MV_CC_SetEnumValue("EncoderSelector", 0)
            if ret != 0:
                raise Exception("set encoder selector fail! ret[0x%x]" % ret)

            # ch:设置编码器数据源A为Line1 | en:Set encoder source A as Line1
            ret = cam.MV_CC_SetEnumValue("EncoderSourceA", 1)
            if ret != 0:
                raise Exception("set encoder sourceA fail! ret[0x%x]" % ret)

            # ch:设置编码器数据源B为Line3 | en:Set encoder source B as Line3
            ret = cam.MV_CC_SetEnumValue("EncoderSourceB", 3)
            if ret != 0:
                raise Exception("set encoder sourceB fail! ret[0x%x]" % ret)

        # ch:注册抓图回调 | en:Register image callback
        ret = cam.MV_CC_RegisterImageCallBackEx(CALL_BACK_FUN, None)
        if ret != 0:
            raise Exception("register image callback fail! ret[0x%x]" % ret)

        # ch:开始取流 | en:Start grab image
        ret = cam.MV_CC_StartGrabbing()
        if ret != 0:
            raise Exception("start grabbing fail! ret[0x%x]" % ret)

        print("press a key to stop grabbing.")
        msvcrt.getch()

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
