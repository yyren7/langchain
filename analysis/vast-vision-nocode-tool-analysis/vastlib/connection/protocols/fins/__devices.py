
from pydantic import BaseModel
import psutil


class Device(BaseModel):
    symbol: str = "DM"
    name: str = "Data memory"
    notation: str = "10"
    binary: int = 0x82
    offset: int = 0
    unit: str = "word"


devices = [
    # CHANNEL(WORD) data type
    {
        "symbol": "CIO",
        "name": "Channel I/O",
        "binary": 0xB0
    },
    {
        "symbol": "WR",
        "name": "Internal auxiliary relay",
        "binary": 0xB1
    },
    {
        "symbol": "HR",
        "name": "Holding relay",
        "binary": 0xB2
    },
    {
        "symbol": "AR",
        "name": "Special auxiliary relay",
        "binary": 0xB3
    },
    {
        "symbol": "TIM",
        "name": "Special auxiliary relay",
        "binary": 0xB3
    },
    {
        "symbol": "CNT",
        "name": "Special auxiliary relay",
        "binary": 0xB3,
        "offset": 32768
    },
    {
        "symbol": "AR",
        "name": "Special auxiliary relay",
        "binary": 0xB3
    },
    {
        "symbol": "AR",
        "name": "Special auxiliary relay",
        "binary": 0xB3
    },


]

