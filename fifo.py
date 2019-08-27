# -*- coding: utf-8 -*-


from myhdl import (
    block, always_comb, always, instances, instance,
    enum
)

from pipelines.hdl import *

from pipelines.lib.mem import regfile

@block
def fifo_reg(clk, rst_n, clr,
             # write side
             wen, din, full, afull,
             # read side
             ren, dout, empty, aempty,
             # full deallocate policy

             dealloc,  # 0-deallocate young, 1-deallocate old
             # req/ack protocal
             req, ack,
             # status
             cnt,
             # parameters
             FIFOWIDTH=None, FIFODEPTH = None,
             WATERLINE=None, REQACK=False
             ):

    if __debug__:
        WIDTH = FIFOWIDTH if FIFOWIDTH is not None else len(din)
        DEPTH = FIFODEPTH
        assert FIFODEPTH is not None
        assert FIFODEPTH >= 1
        assert len(din) == len(dout)
        assert WIDTH > 0

    PTRW = int(WIDTH).bit_length()

    cnt_en = UBool(0)
    cnt = UInt(PTRW-1, 0)
    nxt_cnt = UInt(PTRW - 1, 0)

    wptr = UInt(PTRW, 0)
    rptr = UInt(PTRW, 0)

    nxt_wptr = UInt(PTRW, 0)
    nxt_rptr = UInt(PTRW, 0)

    waddr = UInt(PTRW-1, 0)
    raddr = UInt(PTRW-1, 0)

    # =========================================
    # Memory instance
    # =========================================
    mem = regfile(clk=clk, rst_n=rst_n,
                  wen=wen, waddr=waddr, din=din,
                  ren=ren, raddr=raddr, dout=dout,
                  WIDTH=FIFOWIDTH, DEPTH=FIFODEPTH)

    # =========================================
    # Write/Read Controls
    # =========================================
    @always_comb
    def mem_control():
        waddr.next = wptr[PTRW-1:]
        raddr.next = rptr[PTRW-1:]
        cnt_en.next = (not full and wen) or (not empty and ren)

    @always_ff(clk.posedge, reset=rst_n)
    def cnt_register():
        if clr:
            cnt.next = 0
        elif cnt_en:
            cnt.next = nxt_cnt
        else:
            cnt.next = cnt

    @always_comb
    def cnt_control():
        if clr:
            cnt.next = 0
        # The reason why we dont us
        elif cnt_en:
            # region: can be implemented by case...endcase in verilog
            if wen and not ren:
                cnt.next = DEPTH if cnt == DEPTH else cnt + 1
            elif not wen and ren:
                cnt.next = 0 if cnt == 0 else cnt - 1
            else:
                cnt.next = cnt
            # endregion
        else:
            cnt.next = cnt

    @always_ff(clk.posedge, reset=rst_n)
    def ptr_register():
        if clr:
            wptr.next = 0
            rptr.next = 0
        elif wen or ren:
            wptr.next = nxt_wptr
            rptr.next = nxt_rptr
        else:
            wptr.next = wptr
            rptr.next = rptr

    @always_comb
    def ptr_control():
        pass

    # =========================================
    # Status Interface
    # =========================================
    if REQACK:
    else:

        @always_comb
        def event_control():




    return instances()
