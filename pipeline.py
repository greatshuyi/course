# -*- coding: utf-8 -*-

from myhdl import *
from myhdl_lib.pipeline_control import pipeline_control


def ssrom(clk, addr, dout, CONTENT):
    """ CONTENT == tuple of non-sparse values
    """

    @always(clk.posedge)
    def read():
        dout.next = CONTENT[int(addr)]

    return read


def pa_gen(rst, clk, rx_rdy, rx_vld, rx_dat, tx_rdy, tx_vld, tx_base, tx_index):
    """
    Implementation: 3 - stage pipeline
        stage 0: registers input data
        stage 1: read out offset
        stage 2: multiplies by 2
    Each stage is implemented as a separate process controlled
    by a central pipeline control unit via an enable signal
    The pipeline control unit manages the handshake and synchronizes
    the operation of the stages
    """


    NUM_STAGES = 3

    stage_en = Signal(intbv(0)[NUM_STAGES:])

    stop_rx = Signal(intbv(0)[NUM_STAGES:])

    ##################pipe ctrl##################
    pipe_ctrl = pipeline_control(
        rst=rst,
        clk=clk,
        rx_vld=rx_vld,
        rx_rdy=rx_rdy,
        tx_vld=tx_vld,
        tx_rdy=tx_rdy,
        stage_enable=stage_en,
        stop_rx=stop_rx)


    ###################Stage 1##################

    BASE_WIDTH = len(tx_base)
    base = Signal(intbv(0)[BASE_WIDTH:])
    INDEX_WIDTH = len(tx_index)
    index = Signal(intbv(0)[INDEX_WIDTH:])

    start = Signal(bool)

    @always_seq(clk.posedge, reset=rst)
    def stage_0():
        """Register input data"""
        if stage_en[0]:
            base.next = tx_base
            index.next = tx_index
            start.next = start

    ###################Stage 2##################

    OFFSET_TABLE = (i+1 for i in range(2**INDEX_WIDTH))
    offset = Signal(intbv(0))
    table = ssrom(clk=clk, addr=index, dout=offset, CONTENT=OFFSET_TABLE)

    POT_STATE = enum('IDLE', 'RD', 'PEND')


    @always_comb
    def stage_1():
        """Read out offset
        """
