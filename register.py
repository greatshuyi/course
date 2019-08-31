# -*- coding: utf-8 -*-

from myhdl import (
    block, always_comb, always, instances, instance,
    enum
)
from myhdl import ConcatSignal as concat
from pipeline.hdl import *


@block
def DFFE(clk, en, d, q, WIDTH, NAME):
    """Synchronous enable"""

    @always(clk.posedge)
    def _DFFE():
        if en:
            q.next = d
        else:
            q.next = q
    return _DFFE


DFFE.verilog_code = \
"""
lib_DFFE #($WIDTH) $NAME (
    .clk($clk),
    .en($en),
    .d($d),
    .q($q)

"""


@block
def DFFCE(clk, clear, en, d, q):
    """Synchronous clear and(then) enable"""

    @always(clk.posedge)
    def _DFFCE():
        if clear:
            q.next = 0
        elif en:
            q.next = d
        else:
            q.next = q

    return _DFFCE


DFFCE.verilog_code = \
"""
lib_DFFCE #(WIDTH) 
"""


@block
def DFFRCE(clk, rst_n, clear, en, d, q):
    """Asynchronous reset, synchronous clear and(then) enable"""

    @always_ff(clk.posedge, reset=rst_n)
    def _DFFRCE():
        if clear:
            q.next = 0
        elif en:
            q.next = d
        else:
            q.next = q

    return _DFFRCE


DFFRCE.verilog_code = \
"""
lib_DFFRCE #(WIDTH) 
"""


@block
def DFFRCU(clk, rst_n, clear, d, q):
    """Asynchronous reset, synchronous clear and(then) enable"""

    @always_ff(clk.posedge, reset=rst_n)
    def _DFFRCU():
        if clear:
            q.next = 0
        else:
            q.next = d

    return _DFFRCU


DFFRCU.verilog_code = \
"""
lib_DFFRCU #(WIDTH) 
"""

@block
def DFFRE(clk, rst_n, en, d, q):
    """Asynchronous reset, synchronous clear and(then) enable"""

    @always_ff(clk.posedge, reset=rst_n)
    def _DFFRE():
        if en:
            q.next = d
        else:
            q.next = q

    return _DFFRE


DFFRE.verilog_code = \
"""
lib_DFFRE #($WIDTH)   
"""


