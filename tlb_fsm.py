# -*- coding: utf-8 -*-

from myhdl import (
    block, always_comb, always, instances, instance,
    enum
)
from myhdl import ConcatSignal as concat
from pipeline.hdl import *


@block
def pa_composer(va, prev_va,
                utlb_va, utlb_pa, uutlb_page_size,
                same_page, pa):
    @always_comb
    def composer():

        # 4K
        if uutlb_page_size == 0:
            pass
        # 16K
        elif uutlb_page_size == 1:
            pass
        # 64K
        elif uutlb_page_size == 2:
            pass

        else:
            pass


@block
def cross_page_check(va, utlb_va, utlb_page_size,
                     cross_page,
                     ):
    same_4k = UBool(0)
    same_16k = UBool(0)
    same_64k = UBool(0)
    same_2m = UBool(0)
    same_32m = UBool(0)
    same_512m = UBool(0)
    same_1g = UBool(0)
    same_16g = UBool(0)
    page_4k = UBool(0)
    page_16k = UBool(0)
    page_64k = UBool(0)
    page_2m = UBool(0)
    page_32m = UBool(0)
    page_512m = UBool(0)
    page_1g = UBool(0)
    page_16g = UBool(0)

    @always_comb
    def page_check():
        same_4k.next = True if va[48:12] == utlb_va[48:12] else False
        same_16k.next = True if va[48:14] == utlb_va[48:12] else False
        same_64k.next = True if va[48:16] == utlb_va[48:12] else False
        same_2m.next = True if va[48:21] == utlb_va[48:12] else False
        same_32m.next = True if va[48:25] == utlb_va[48:12] else False
        same_512m.next = True if va[48:29] == utlb_va[48:12] else False
        same_1g.next = True if va[48:30] == utlb_va[48:12] else False
        same_16g.next = True if va[48:34] == utlb_va[48:34] else False

        page_4k.next = True if utlb_page_size == 0 else False
        page_16k.next = True if utlb_page_size == 1 else False
        page_64k.next = True if utlb_page_size == 2 else False
        page_2m.next = True if utlb_page_size == 3 else False
        page_32m.next = True if utlb_page_size == 4 else False
        page_512m.next = True if utlb_page_size == 5 else False
        page_1g.next = True if utlb_page_size == 6 else False
        page_16g.next = True if utlb_page_size == 7 else False

        cross_page.next = (page_4k and same_4k) or \
                          (page_16k and same_16k) or \
                          (page_64k and same_64k) or \
                          (page_2m and same_2m) or \
                          (page_32m and same_32m) or \
                          (page_512m and same_512m) or \
                          (page_1g and same_1g) or \
                          (page_16g and same_1g)

    return page_check()


TLB_STATE = enum('IDLE', 'TLB', 'WAIT', 'SYNC')


@block
def tlb_ctrl(
    clk, rst_n, enable, flush,

    # pipeline input
    # command
    ivld, istart, idrop,
    iurgent, imode, ibase, ioffset,

    # ooo flush
    ooo_flush,

    # from pipelien & data path

    # from prefetch response
    prf_vld, prf_fault, prf_match, prf_pa, prf_page_size,



    # downstream pipeline interface
    istall, ovalid,

    # backpressure to previous pipe
    ostall,

    # monitor
    st, nxt
):
    # =============================================
    # pipeline sigs and payload
    # =============================================

    # staging buffer
    stage_start = UBool(0)
    stage_drop = UBool(0)
    stage_base = UInt(len(ibase))
    stage_offset = UInt(len(ioffset))

    # mux-ed output
    tlb_start = UBool(0)
    tlb_drop = UBool(0)
    base = UInt(len(ibase))
    offset = UInt(len(ioffset))

    # clear sig from FSM to stage cmd
    clr_start = UBool(0)
    clr_drop = UBool(0)

    # act as uuTLB entry
    uutlb_vld = UBool(0)
    uutlb_page_size = UInt(3)
    uutlb_va = UInt(len(iva), 0)
    uutlb_pa = UInt(len(pa), 0)

    st = UEnum(TLB_STATE)
    nxt = UEnum(TLB_STATE)

    tlb_timer = UInt(9, max=511)
    tlb_timeout = UBool(0)
    prf_sync = UBool(0)

    # data path & pipeline
    iva = UInt(len(ibase)+len(ioffset))
    cross_page = UBool(0)

    # pipeline internal stall
    stop = UBool(0)

    va = UInt(len(iva), 0)  # current processing request's VA
    pa = UInt(len(prf_pa), 0)

    # =============================================
    # pipeline control
    # =============================================

    @always_comb
    def glb_ctrl():
        tlb_start.next = stage_start if stop else istart
        tlb_drop.next = stage_drop if stop else idrop
        base.next = stage_base if stop else ibase
        offset.next = stage_offset if stop else ioffset
        # tlb_start.next = istart or ooo_flush
        # tlb_drop.next = ivld and idrop
        tlb_timeout.next = True if st == TLB_STATE.WAIT and tlb_timer == 511 else False
        prf_sync.next = prf_vld and (not prf_fault and prf_match)
        cross_page.next = (iva == uutlb_va) and uutlb_vld

    @always_ff(clk.posedge, reset=rst_n)
    def staging():
        if flush:
            stage_start.next = False
            stage_drop.next = False
            stage_base.next = 0
            stage_offset.next = 0
        elif not stop and enable:
            stage_base.next = ibase
            stage_offset.next = ioffset

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
    # uuTLB & controls
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

        # TODO: the critical step is how to handle va, recheck
        if enable:

            if tlb_start:
                uutlb_va.next = iva
            elif enable:
                if (st == TLB_STATE.TLB or st == TLB_STATE.WAIT) and tlb_drop:
                    uutlb_va.next = iva
                elif st == TLB_STATE.WAIT and (tlb_drop or tlb_timeout):
                    uutlb_va.next = iva
                elif st == TLB_STATE.SYNC and cross_page:
                    uutlb_va.next = iva
                else:
                    uutlb_va.next = uutlb_va
        else:
            uutlb_va.next = uutlb_va

        # page size/pa/...
        if enable and st == TLB_STATE.WAIT and prf_sync:
            uutlb_pa.next = prf_pa
            uutlb_page_size.next = prf_page_size
        else:  # hold
            uutlb_pa.next = uutlb_pa
            uutlb_page_size.next = uutlb_page_size

    # =============================================
    # data path & controls
    # =============================================

    @always_ff(clk.posedge, reset=rst_n)
    def va_controls():



    @always_ff(clk.posedge, reset=rst_n)
    def pa_control():
        if flush:


    @always_ff(clk.posedge, reset=rst_n)
    def handshake():
        # ovalid
        if flush or tlb_start:
            ovalid.next = False
        elif st == TLB_STATE.WAIT:
            ovalid.next = True if prf_sync else False
        elif st == TLB_STATE.SYNC:
            ovalid.next = False if cross_page or tlb_drop else True
        else:
            ovalid.next = ovalid

    # =============================================
    # back pressure control
    # =============================================
    @always_comb
    def back_pressure():
        if st == TLB_STATE.IDLE:
            ostall.next = False
        else:
            ostall.next = not flush | stop | istall

    return instances()





 // TLB response
utlb_resp_fill_vld			IN	1
utlb_resp_fill_va			IN	[48:12]
utlb_resp_fill_pa			IN	[40:12]
utlb_resp_fill_page_size	IN	[2:0]
utlb_resp_fill_shared		IN	1
utlb_resp_flush				IN	1
utlb_resp_tid				IN	1
utlb_resp_pbha				IN	2
utlb_resp_drop				IN	1
utlb_resp_prf				IN	1


// TLB request
utlb_req_vld				OUT	1
utlb_req_pgt				OUT	1
utlb_req_va					OUT	[48:12]
utlb_req_pa					OUT	[40:2]
utlb_req_shared				OUT	1
utlb_req_spd				OUT	[1:0]
utlb_req_typ				OUT	[1:0]
utlb_req_hash_pc			OUT	[10:0]
utlb_req_page_size			OUT	[2:0]
utlb_req_dir				OUT	1
utlb_req_delta_hi			OUT	[15:12]
utlb_req_st					OUT	1
utlb_req_tid				OUT	1
utlb_req_prf				OUT	1


ple_req_vld_e4				OUT	1
ple_req_dst					OUT	1
ple_req_keep				OUT	1
ple_req_typ					OUT	1
ple_req_prf					OUT	1
ple_req_pa					OUT	[48:0]
ple_req_shareable			OUT	[1:0]
ple_reg_mair_e4				OUT	[4:0]
ple_req_va1312				OUT	[1:0]
ple_req_hash_tag			OUT	[7:0]
ple_req_rid					OUT	[7:0]
ple_req_accept				IN	1
		
ple_req_send_finish			IN	1
















