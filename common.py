# -*- coding: utf-8 -*-
"""
Some small common block
"""

import math

from synth.hdl import *


@block
def edge_detect(
    clk,
    rst_n,
    din,
    valid,
    mode=0
):
    """
    Detect posedge or negedge on input signal, default to posedge(mode=0)
    :param clk:
    :param rst_n:
    :param din:
    :param valid:
    :return:
    """

    din_r = UBool(0)

    @always_ff(clk.posedge, reset=rst_n)
    def _latch():
        din_r.next = din

    # TODO: conditional parameter on generate
    @always_comb
    def _valid():
        if mode == 0:
            valid.next = not din and din_r
        else:
            valid.next = din and not din_r

    return instances()


@block
def bin2ohot(din, dout):
    """Binary to one-hot conversion"""
    IN_W = len(din)
    OUT_W = 2**IN_W

    @always_comb
    def _conv():
        for i in range(OUT_W):
            if din == i:
                dout[i] = 1
            else:
                dout[i] = 0

    return instances()


@block
def ohot2bin(din, dout):
    IN_W = len(din)
    OUT_W = int(math.ceil(math.log2(IN_W)))

    dtmp = UInt(OUT_W, 0)
    idtmp = UInt(OUT_W, 0)

    @always_comb
    def _conv():
        for i in range(IN_W):
            idtmp = i
            if din[i] == 1:
                dtmp = dtmp or idtmp

        dout.next = dtmp


@block
def bin2gray(din, dout): pass


@block
def gray2bin(din, dout): pass


if __name__ == "__main__":

    clk = UBool(0)
    rst_n = AsyncReset(0, 0)
    din = UBool(0)
    valid = UBool(0)
    edge = edge_detect(clk, rst_n, din, valid)
    edge.convert(hdl="Verilog")

    # quite impressive, take a close look at here
    din = SInt(8)
    dout = SInt(3)
    b2o = bin2ohot(din, dout)
    b2o.convert(hdl="Verilog")
