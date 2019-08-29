# -*- coding: utf-8 -*-

from myhdl import (
    block, always_comb, always, instances, instance,
    enum
)
from myhdl import ConcatSignal as concat
from pipeline.hdl import *



@block
def pa_composer(va, prev_va,
                utlb_va, utlb_pa, utlb_page_size,
                same_page, pa):

    @always_comb
    def composer():

        # 4K
        if page_size == 0:
            pass
        # 16K
        elif page_size == 1:
            pass
        # 64K
        elif page_size ==



@block
def cross_page_check(va, utlb_va, utlb_page_size,
                     cross_page,
                     ):

    same_4k   = UBool(0)
    same_16k  = UBool(0)
    same_64k  = UBool(0)
    same_2m   = UBool(0)
    same_32m  = UBool(0)
    same_512m = UBool(0)
    same_1g   = UBool(0)
    page_4k   = UBool(0)
    page_16k  = UBool(0)
    page_64k  = UBool(0)
    page_2m   = UBool(0)
    page_32m  = UBool(0)
    page_512m = UBool(0)
    page_1g   = UBool(0)

    @always_comb
    def page_check():
        same_4k.next   = True if va[48:12] == utlb_va[48:12] else False
        same_16k.next  = True if va[48:14] == utlb_va[48:12] else False
        same_64k.next  = True if va[48:16] == utlb_va[48:12] else False
        same_2m.next   = True if va[48:21] == utlb_va[48:12] else False
        same_32m.next  = True if va[48:25] == utlb_va[48:12] else False
        same_512m.next = True if va[48:29] == utlb_va[48:12] else False
        same_1g.next   = True if va[48:30] == utlb_va[48:12] else False

        page_4k.next   = True if utlb_page_size == 0 else False
        page_16k.next  = True if utlb_page_size == 1 else False
        page_64k.next  = True if utlb_page_size == 2 else False
        page_2m.next   = True if utlb_page_size == 3 else False
        page_32m.next  = True if utlb_page_size == 4 else False
        page_512m.next = True if utlb_page_size == 5 else False
        page_1g.next   = True if utlb_page_size == 6 else False

        cross_page.next = (page_4k   and same_4k) or \
                          (page_16k  and same_16k) or \
                          (page_64k  and same_64k) or \
                          (page_2m   and same_2m) or \
                          (page_32m  and same_32m) or \
                          (page_512m and same_512m) or \
                          (page_1g   and same_1g)

    return instances()



TLB_STATE = enum('IDLE', 'TLB', 'WAIT', 'SYNC')


@block
def tlb_ctrl(
    clk, rst_n, enable, flush,

    # upstream input
    ivld, istart, idrop, iurgent, imode,
    ioffset, iva,


    # from prefetch response
    prf_vld, prf_fault, prf_match, prf_pa, prf_page_size,

    # from pipelien & data path
    cross_page,

    # ooo flush
    ooo_flush,

    # internal uuTLB
    invalid,                            # invalidate the only uuTLB entry
    replace,                            # replace the only uuTLB entry

    # pipeline output

    # backpressure
    stall,

    # monitor
    st, nxt
):


    # =============================================
    # pipeline sigs and payload
    # =============================================
    tlb_start = UBool(0)
    tlb_drop = UBool(0)
    
    va = UInt(len(iva), 0)                          # current processing request's VA
    prev_va = UInt(len(iva), 0)                     # record of last incoming VA
    offset = UInt(len(ioffset), 0)
    pa = UInt(len(prf_pa), 0)


    # act as uuTLB entry
    page_size=UInt(3)


    st = UEnum(TLB_STATE)
    nxt = UEnum(TLB_STATE)


    prf_sync = UBool(0)


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
                pass

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

        @always_comb
        def _status():
            prf_sync.next = prf_vld and (prf_fault or not prf_match)




        @always_ff(clk.posedge, reset=rst_n)
        def va_controls():
            if flush:
                va.next = 0
                prev_va.next = 0
            elif tlb_start:
                va.next = iva
                prev_va.next = 0
            else:
                if tlb_drop:
                    if st == TLB_STATE.TLB or TLB_STATE.WAIT:
                        va.next = iva
                    elif st == TLB_STATE.SYNC:
                        va.next = iva
                        prev_va.next = va
                    else:
                        va.next = va
                        prev_va.next = prev_va
                else:
                    if st == TLB_STATE.WAIT and not prf_sync:   # drop and re-lookup
                        va.next = iva
                        prev_va.next = 0
                    elif st == TLB_STATE.SYNC and not stall:
                        if cross_page:
                            va.next = iva
                            prev_va.next = 0
                        else:
                            va.next = iva
                            prev_va.next = va
                    else:
                        va.next = va
                        prev_va.next = prev_va


        @always_ff(clk.posedge, reset=rst_n)
        def pa_control():
            if flush:
                pa.next = 0
            elif tlb_start:
                pa.next = 0
            else:
                if st == TLB_STATE.WAIT and prf_sync:
                    pa.next = prf_pa
                elif st == TLB_STATE.SYNC:
                    if tlb_drop:



            else:
                pa.next = pa





        @always_ff(clk.posedge, reset=rst_n)
        def va_vld_control():


        @always_comb
        def va_controls():
            pass






