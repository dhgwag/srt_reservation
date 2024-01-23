""" Quickstart script for InstaPy usage """

# imports
from train_reservation.srt import SRT
from train_reservation.ktx import KTX
from config import *
import asyncio

if __name__ == "__main__":
    if train == 'srt':
        srt = SRT()
        asyncio.run(srt.run())
    else:
        ktx = KTX()
        asyncio.run(ktx.run())
