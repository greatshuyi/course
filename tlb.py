# -*- coding: utf-8 -*-

from myhdl import (
    block, always_comb, always, instances, instance,
    enum
)
from myhdl import ConcatSignal as concat
from pipeline.hdl import *


TLB_STATE = enum('IDLE', 'TLB', 'WAIT', 'SYNC')


@block
def tlb_ctrl(
    clk, rst_n, enable, flush,

    # upstream input
    ivld, istart, idrop, iurgent, imode,

    # from prefetch response
    prf_vld, prf_fault, prf_match, prf_pa,

    # from pipelien & data path
    cross_page, iva, 

    # ooo flush
    ooo_flush,

    # internal uuTLB
    invalid,                            # invalidate the only uuTLB entry
    replace,                            # replace the only uuTLB entry

    # pipe registers data
    base_va,
    # pipe ctrl
    cnt,
    # backpressure
    stall,

    # monitor
    st, nxt
):


    # =============================================
    # 
    # =============================================
    tlb_start = UBool(0)
    tlb_drop = UBool(0)
    
    va = UInt(len(iva), 0)                          # current processing request's VA
    prev_va = UInt(len(iva), 0)                     # record of last incoming VA
    nxt_va = UInt(len(iva), 0)                      # record of last incoming VA

    st = UEnum(TLB_STATE)
    nxt = UEnum(TLB_STATE)

    # =============================================
    # pipeline control
    # =============================================

    @always_comb
    def glb_ctrl():
        tlb_start.next = istart or ooo_flush
        tlb_drop.next = ivld and idrop

    @always_ff(clk.posedge, reset=rst_n)
    def fsm_state():
        if enable:
            st.next = nxt

    @always_comb
    def fsm_transition():
        if st == TLB_STATE.IDLE:
            if flush:
                nxt.next = TLB_STATE.IDLE
            elif tlb_start:
                nxt.next = TLB_STATE.TLB
            else:
                nxt.next = TLB_STATE.IDLE

        elif st == TLB_STATE.TLB:
            if flush:
                nxt.next = TLB_STATE.IDLE
            elif tlb_start or tlb_drop:
                nxt.next = TLB_STATE.TLB
            else:
                nxt.next = TLB_STATE.WAIT

        elif st == TLB_STATE.WAIT:
            if flush:
                nxt.next = TLB_STATE.IDLE
            elif tlb_start or tlb_drop:
                nxt.next = TLB_STATE.TLB
            else:
                if not prf_vld:
                    nxt.next = TLB_STATE.WAIT
                else:
                    if prf_fault or not prf_match:
                        nxt.next = TLB_STATE.TLB
                    else:
                        nxt.next = TLB_STATE.SYNC

        elif st == TLB_STATE.SYNC:
            if tlb_start:
                nxt.next = TLB_STATE.TLB
            elif tlb_drop:
                nxt.next = TLB_STATE.TLB if cross_page else TLB_STATE.SYNC
            else:
                nxt.next = TLB_STATE.SYNC
                
        else:
            nxt.next = TLB_STATE.IDLE

        # FSM output backpressure
        @always_ff(clk.posedge, reset=rst_n)
        def back_pressure():
            if flush:
                stall.next = False
            elif tlb_start:
                stall.next = True
            else:




        # =============================================
        # uuTLB controls
        # =============================================

        # Remember: incoming prefetch response always compared to va not prev_va!!!
        @always_comb
        def uutlb():
            if flush:
                replace.next = False
            elif tlb_start:
                replace.next = False




        # =============================================
        # pipeline payload controls
        # =============================================
        @always_ff(clk.posedge, reset=rst_n)
        def pipe_ctrls():
            pass


        @always_comb
        def va_controls():
            pass






