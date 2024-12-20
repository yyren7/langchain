# ===============================================================================
# Name      : path_manager.py
# Version   : 1.0.0
# Brief     :
# Time-stamp: 2023-12-08 09:35
# Copyirght 2021 Hiroya Aoyama
# ===============================================================================
import os

# NOTE: IMAGE
ORIG_IMG = 'orig.bmp'
TEMPL_IMG = 'templ.jpg'
MASK_IMG = 'mask.png'
# NOTE: JSON
CAMERA_CFG = 'camera.json'
PARAM_CFG = 'param.json'
CALIB_CFG = 'calib_param.json'
OPTION_CFG = 'option.json'
PLC_CFG = 'plc.json'
REC_CFG = 'last_used.json'
PLC_ADDRESS_SHEET = 'vision_setting.xlsx'


class ConfigPath:
    """
    -data
        |-part1
            |-model
                |-modelA
                    |-orig.bmp
                    |-templ.jpg
                    |-mask.png
                    |-param.json
                |-modelB
                    |...
            |-last_used.json
        |-part2
            |-model
                |-...
            |-last_used.json
        |-common
            |-camera.json
            |-plc.json
            |-option.json
    -log
        |-img
            |-yyyy
                |-yyyy-mm
                    |-yyyy-mm-dd
                        |-yyyy-mm-dd-hh-MM-ss.jpg
        |-csv
            |-yyyy
                |-yyyy-mm
                    |-yyyy-mm-dd.csv

    """

    def __init__(self, header: str, modelname: str) -> None:
        self._header = header  # NOTE: 部品の名前フォルダ(/data/xxx/)
        self._model_header = os.path.join(header, 'model')
        # self._common_header = os.path.join(header, 'common')
        self._common_header = os.path.abspath(os.path.join(header, '../', 'common'))
        self._modelname = modelname
        # NOTE: IMAGE PATH
        self._orig_img = os.path.join(self._model_header, modelname, ORIG_IMG)
        self._templ_img = os.path.join(self._model_header, modelname, TEMPL_IMG)
        self._mask_img = os.path.join(self._model_header, modelname, MASK_IMG)
        # NOTE: JSON PATH
        self._param_cfg = os.path.join(self._model_header, modelname, PARAM_CFG)
        self._calib_cfg = os.path.join(self._model_header, modelname, CALIB_CFG)
        self._camera_cfg = os.path.join(self._common_header, CAMERA_CFG)
        self._option_cfg = os.path.join(self._common_header, OPTION_CFG)
        self._plc_cfg = os.path.join(self._common_header, PLC_CFG)
        self._last_used_cfg = os.path.join(header, REC_CFG)
        # NOTE: LOG IMG DIR
        self._log_img_dir = os.path.abspath(os.path.join(header, '../', '../', 'log', 'img'))
        self._log_csv_dir = os.path.abspath(os.path.join(header, '../', '../', 'log', 'csv'))
        # NOTE: EXCEL SHEET
        self._plc_address_sheet = os.path.abspath(os.path.join(header, '../', PLC_ADDRESS_SHEET))
        self.orig_plc_address_sheet = os.path.join('./', PLC_ADDRESS_SHEET)
        # NOTE: EXPORT FILE
        self.zip_program = os.path.abspath(os.path.join(header, '../', '../', 'program.zip'))
        self.zip_config = os.path.abspath(os.path.join(header, '../', '../', 'config.zip'))
        self.config_folder = os.path.abspath(os.path.join(header, '../', '../', 'data'))

    def update(self, modelname: str) -> None:
        self._modelname = modelname
        # NOTE: IMAGE PATH
        self._orig_img = os.path.join(self._model_header, modelname, ORIG_IMG)
        self._templ_img = os.path.join(self._model_header, modelname, TEMPL_IMG)
        self._mask_img = os.path.join(self._model_header, modelname, MASK_IMG)
        # NOTE: JSON PATH
        self._param_cfg = os.path.join(self._model_header, modelname, PARAM_CFG)
        self._calib_cfg = os.path.join(self._model_header, modelname, CALIB_CFG)
        self._camera_cfg = os.path.join(self._common_header, CAMERA_CFG)
        self._option_cfg = os.path.join(self._common_header, OPTION_CFG)
        self._plc_cfg = os.path.join(self._common_header, PLC_CFG)
        self._last_used_cfg = os.path.join(self._header, REC_CFG)
        # NOTE: EXCEL SHEET
        self._plc_address_sheet = os.path.abspath(os.path.join(self._header, '../', PLC_ADDRESS_SHEET))
        self.orig_plc_address_sheet = os.path.join('./', PLC_ADDRESS_SHEET)

    def set_header(self, header: str) -> None:
        """モデルに依存しないパスはここで更新"""
        self._header = header
        self._model_header = os.path.join(header, 'model')
        # self._common_header = os.path.join(header, 'common')
        self._common_header = os.path.abspath(os.path.join(header, '../', 'common'))
        self._log_img_dir = os.path.abspath(os.path.join(header, '../', '../', 'log', 'img'))
        self._log_csv_dir = os.path.abspath(os.path.join(header, '../', '../', 'log', 'csv'))
        # NOTE: EXPORT FILE
        self.zip_program = os.path.abspath(os.path.join(header, '../', '../', 'program.zip'))
        self.zip_config = os.path.abspath(os.path.join(header, '../', '../', 'config.zip'))
        self.config_folder = os.path.abspath(os.path.join(header, '../', '../', 'data'))
        self.update(self._modelname)

    @property
    def modelname(self) -> str:
        return self._modelname

    @property
    def orig_img(self) -> str:
        return self._orig_img

    @property
    def templ_img(self) -> str:
        return self._templ_img

    @property
    def mask_img(self) -> str:
        return self._mask_img

    @property
    def param_cfg(self) -> str:
        return self._param_cfg

    @property
    def calib_cfg(self) -> str:
        return self._calib_cfg

    @property
    def camera_cfg(self) -> str:
        return self._camera_cfg

    @property
    def option_cfg(self) -> str:
        return self._option_cfg

    @property
    def plc_cfg(self) -> str:
        return self._plc_cfg

    @property
    def last_used_cfg(self) -> str:
        return self._last_used_cfg

    @property
    def log_img_dir(self) -> str:
        return self._log_img_dir

    @property
    def log_csv_dir(self) -> str:
        return self._log_csv_dir

    @property
    def plc_address_sheet(self) -> str:
        return self._plc_address_sheet


class PathManager(ConfigPath):
    __version__ = '1.0.0'

    def __init__(self, header: str, modelname: str) -> None:
        super().__init__(header=header, modelname=modelname)

    def update(self, modelname: str) -> None:
        return super().update(modelname)

    def set_header(self, header: str) -> None:
        return super().set_header(header)


if __name__ == '__main__':
    pass
