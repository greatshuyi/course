# -*- coding: utf-8 -*-

from myhdl import (
    block,  instances,
)
from myhdl import ConcatSignal as concat
from myhdl import delay, StopSimulation, Simulation
from pipeline.hdl import *

import random
from pipeline.lib.mem import ssrom

@block
def reciever(clk, rst_n, enable,
             # master side
             ivld, ordy,
             # slave side
             ovld, irdy,
             # data in/out
             din, dout,
             # REG_TYPE
             REG=None,
             ):

    rdy = UBool(0)
    timer = SInt(4, min=0)

    @always_ff(clk.posedge, reset=rst_n)
    def master():
        rdy.next = True if timer == 0 else False
        ordy.next = rdy and irdy
        timer.next = random.randint(1, 15) if timer == 0 else timer - 1

    @always_ff(clk.posedge, reset=rst_n)
    def recv():
        if ivld and rdy and irdy:
            dout.next = din

    @always_ff(clk.posedge, reset=rst_n)
    def slave():
        ovld.next = True

    return instances()





