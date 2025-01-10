# -- coding: utf-8 --

import sys
import msvcrt

from ctypes import *

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


def print_devices_info(deviceList):
    for i in range(0, deviceList.nDeviceNum):
        mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
        if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE or mvcc_dev_info.nTLayerType == MV_GENTL_GIGE_DEVICE:
            print ("\ngige device: [%d]" % i)
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
            print ("\nu3v device: [%d]" % i)
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
            print ("\nCML device: [%d]" % i)
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
            print ("\nCXP device: [%d]" % i)
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
            print ("\nXoF device: [%d]" % i)
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


def print_interface_info(interfaceList):
    for i in range(0, interfaceList.nInterfaceNum):
        interfaceInfo = cast(interfaceList.pInterfaceInfos[i], POINTER(MV_INTERFACE_INFO)).contents
        print("interface: [%d]" % i)
        displayName = ""
        for per in interfaceInfo.chDisplayName:
            if per == 0:
                break
            displayName = displayName + chr(per)
        print("display name: %s" % displayName)

        serialNumber = ""
        for per in interfaceInfo.chSerialNumber:
            if per == 0:
                break
            serialNumber = serialNumber + chr(per)
        print("serial number: %s" % serialNumber)

        modelName = ""
        for per in interfaceInfo.chModelName:
            if per == 0:
                break
            modelName = modelName + chr(per)
        print("model name: %s" % modelName)

        interfaceId = ""
        for per in interfaceInfo.chInterfaceID:
            if per == 0:
                break
            interfaceId = interfaceId + chr(per)
        print("interface id: %s" % interfaceId)


if __name__ == "__main__":

    try:
        # ch:初始化SDK | en: initialize SDK
        MvCamera.MV_CC_Initialize()

        interfaceList = MV_INTERFACE_INFO_LIST()
        transportLayerType = MV_GIGE_INTERFACE | MV_CAMERALINK_INTERFACE | MV_CXP_INTERFACE | MV_XOF_INTERFACE

        # ch:枚举采集卡 | en:Enum interfaces
        ret = MvCamera.MV_CC_EnumInterfaces(transportLayerType, interfaceList)
        if ret != 0:
            print("enum interfaces fail! ret[0x%x]" % ret)
            sys.exit()

        if interfaceList.nInterfaceNum == 0:
            print("find no interface!")
            sys.exit()

        print("Find %d interfaces!" % interfaceList.nInterfaceNum)
        print_interface_info(interfaceList)

        nInterfaceIndex = input("please input the number of the interface to connect:")

        if int(nInterfaceIndex) >= interfaceList.nInterfaceNum:
            print("input error!")
            sys.exit()

        # ch:创建相机实例 | en:Create Camera Object
        cam_instance = MvCamera()
        interface_instance = MvCamera()

        # ch:选择采集卡并创建句柄 | en:Select interface and create handle
        curInterface = cast(interfaceList.pInterfaceInfos[int(nInterfaceIndex)], POINTER(MV_INTERFACE_INFO)).contents

        ret = interface_instance.MV_CC_CreateInterface(curInterface)
        if ret != 0:
            raise Exception("create interface handle fail! ret[0x%x]" % ret)

        # ch:打开设备 | en:Open device
        ret = interface_instance.MV_CC_OpenInterface()
        if ret != 0:
            raise Exception("open interface fail! ret[0x%x]" % ret)
        else:
            print("open interface success")

        # ch:枚举采集卡上相机 | en:Get Feature
        deviceList = MV_CC_DEVICE_INFO_LIST()
        ret = interface_instance.MV_CC_EnumDevicesByInterface(deviceList)
        if ret != 0:
            raise Exception("enum devices fail! ret[0x%x]" % ret)

        if deviceList.nDeviceNum == 0:
            raise Exception("find no device!")

        print_devices_info(deviceList)

        nCamIndex = input("please input the number of the device to connect:")

        if int(nCamIndex) >= deviceList.nDeviceNum:
            raise Exception("input error!")

        # ch:选择设备并创建句柄 | en:Select device and create handle
        stDeviceList = cast(deviceList.pDeviceInfo[int(nCamIndex)], POINTER(MV_CC_DEVICE_INFO)).contents

        ret = cam_instance.MV_CC_CreateHandle(stDeviceList)
        if ret != 0:
            raise Exception("create handle fail! ret[0x%x]" % ret)

        # ch:打开设备 | en:Open device
        ret = cam_instance.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            raise Exception("open device fail! ret[0x%x]" % ret)

        # ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
        if stDeviceList.nTLayerType == MV_GIGE_DEVICE or stDeviceList.nTLayerType == MV_GENTL_GIGE_DEVICE:
            nPacketSize = cam_instance.MV_CC_GetOptimalPacketSize()
            if int(nPacketSize) > 0:
                ret = cam_instance.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
                if ret != 0:
                    print("Warning: Set Packet Size fail! ret[0x%x]" % ret)
            else:
                print("Warning: Get Packet Size fail! ret[0x%x]" % nPacketSize)

        # ch:设置触发模式为off | en:Set trigger mode as off
        ret = cam_instance.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
        if ret != 0:
            raise Exception("set trigger mode fail! ret[0x%x]" % ret)

        # ch:注册抓图回调 | en:Register image callback
        ret = cam_instance.MV_CC_RegisterImageCallBackEx(CALL_BACK_FUN, None)
        if ret != 0:
            raise Exception("register image callback fail! ret[0x%x]" % ret)

        # ch:开始取流 | en:Start grab image
        ret = cam_instance.MV_CC_StartGrabbing()
        if ret != 0:
            raise Exception("start grabbing fail! ret[0x%x]" % ret)

        print("press a key to stop grabbing.")
        msvcrt.getch()

        # ch:停止取流 | en:Stop grab image
        ret = cam_instance.MV_CC_StopGrabbing()
        if ret != 0:
            raise Exception("stop grabbing fail! ret[0x%x]" % ret)

        # ch:关闭设备 | Close device
        ret = cam_instance.MV_CC_CloseDevice()
        if ret != 0:
            raise Exception("close deivce fail! ret[0x%x]" % ret)

        # ch:销毁句柄 | Destroy handle
        cam_instance.MV_CC_DestroyHandle()

        # ch:关闭采集卡 | en:Close interface
        interface_instance.MV_CC_CloseInterface()

        # ch:销毁采集卡句柄 | en:Destroy interface
        interface_instance.MV_CC_DestroyInterface()
    except Exception as e:
        print(e)
        cam_instance.MV_CC_CloseDevice()
        cam_instance.MV_CC_DestroyHandle()
        interface_instance.MV_CC_CloseInterface()
        interface_instance.MV_CC_DestroyInterface()

    finally:
        # ch:反初始化SDK | en: finalize SDK
        MvCamera.MV_CC_Finalize()

