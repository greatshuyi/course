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
    uutlb_vld = UBool(0)
    uutlb_page_size=UInt(3)
    uutlb_va = UInt(len(iva), 0)
    uutlb_pa = UInt(len(pa), 0)



    st = UEnum(TLB_STATE)
    nxt = UEnum(TLB_STATE)

    prf_sync = UBool(0)

    tlb_timer = UInt(9, max=511)
    tlb_timeout = UBool(0)


    # =============================================
    # pipeline control
    # =============================================

    @always_comb
    def glb_ctrl():
        tlb_start.next = istart or ooo_flush
        tlb_drop.next = ivld and idrop
        tlb_timeout.next = st == TLB_STATE.WAIT and tlb_timer == 511)
        prf_sync.next = prf_vld and (not prf_fault and prf_match)



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
            elif tlb_start or tlb_timeout or ooo_flush:
                nxt.next = TLB_STATE.TLB
            else:
                if prf_sync:
                    nxt.next = TLB_STATE.SYNC
                else:
                    nxt.next = TLB_STATE.WAIT

        elif st == TLB_STATE.SYNC:
            if flush:
                nxt.next = TLB_STATE.IDLE
            elif tlb_start:
                nxt.next = TLB_STATE.TLB
            else:
                nxt.next = TLB_STATE.TLB if cross_page else TLB_STATE.SYNC
                
        else:
            nxt.next = TLB_STATE.IDLE

    # timer
    @always_ff(clk.posedge, reset=rst_n)
    def monitor():
        if enable:
            if (st == TLB_STATE.TLB or st == TLB_STATE.WAIT) and nxt == TLB_STATE.WAIT:
                tlb_timer.next = 0 if tlb_timer == 511 else tlb_timer + 1
            else:
                tlb_timer.next = 0

    # =============================================
    # uuTLB controls
    # =============================================

    # Remember: incoming prefetch response always compared to va not prev_va!!!
    @always_ff(clk.posedge, reset=rst_n)
    def uutlb():

        # valid
        if flush or tlb_start or ooo_flush:
            uutlb_vld.next = False
        else:
            if st == TLB_STATE.WAIT and prf_sync:
                uutlb_vld.next = True
            elif st == TLB_STATE.SYNC and cross_page:
                uutlb_vld.next = False
            else:
                uutlb_vld.next = uutlb_vld

        # TODO: the critical step is how to handle va
        # va
        if tlb_start:
            uutlb_va.next = iva
        else:
            if st == TLB_STATE.TLB and tlb_drop:
                uutlb_va.next = iva
            elif st == TLB_STATE.WAIT and (tlb_drop or tlb_timeout):
                if tlb_drop:
                    uutlb_va.next = va

                uutlb_va.next = uutlb_va


        # page size and pa
        if st == TLB_STATE.TLB or TLB_STATE.WAIT:
            if prf_sync:
                uutlb_pa.next = prf_pa
                uutlb_page_size.next = prf_page_size
            else:
                uutlb_pa.next = uutlb_pa
                uutlb_page_size.next = uutlb_page_size


    # =============================================
    # data path controls
    # =============================================

    @always_ff(clk.posedge, reset=rst_n)
    def va_controls():
        if flush:
            va.next = 0
        elif tlb_start or (tlb_drop and st != TLB_STATE.IDLE):
            va.next = iva
        else:
            if st == TLB_STATE.WAIT and





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







    # =============================================
    # backpressure control
    # =============================================
    @always_ff(clk.posedge, reset=rst_n)
    def back_pressure():
        if flush:
            stall.next = False
        elif tlb_start:
            stall.next = True
        else:
            pass











            else:
                pa.next = pa





        @always_ff(clk.posedge, reset=rst_n)
        def va_vld_control():


        @always_comb
        def va_controls():
            pass






