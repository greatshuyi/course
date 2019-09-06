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
    clk,
    rst_n,
    enable,
    flush,
    # ooo flush
    i_ooo_flush,
    i_ooo_flush_tid,

    # pipeline input command
    istart,
    idrop,
    ibase,
    ioffset,
    ihint,
    idst,
    itype,
    ikeep,
    itid,
    # tlb prefetch request
    oprf_vld,
    oprf_pgt,
    oprf_va,
    oprf_pa,
    oprf_shared,
    oprf_spd,
    oprf_typ,
    oprf_hash_pc,
    oprf_page_size,
    oprf_dir,
    oprf_delta_hi,
    oprf_st,
    oprf_tid,
    oprf_prf,

    # tlb prefetch response
    iprf_vld,
    iprf_va,
    iprf_pa,
    iprf_page_size,
    iprf_shareable,
    iprf_flush,
    iprf_tid,
    iprf_pbha,
    iprf_drop,
    iprf_prf,

    # downstream NL channel
    oreq_vld,                       # OUT   1
    oreq_dst,                       # OUT	1
    oreq_keep,                      # OUT	1
    oreq_typ,                       # OUT	1
    oreq_prf,                       # OUT	1
    oreq_hash_pc,                   # OUT	1           PLE always send out True
    oreq_page_size,                 # OUT	[48:0]
    oreq_tid,                       # OUT	[1:0]
    oreq_va1312,                    # OUT	[4:0]
    oreq_shareable,                 # OUT	[1:0]
    oreq_pa,                        # OUT	[7:0]
    oreq_mair,                      # OUT   [4:0]
    oreq_rid,                       # OUT	[7:0]

    # pipeline backpressure
    istall, 
    ostall,

    # monitor
    st, 
    nxt
):
    # =============================================
    # pipeline sigs and payload
    # =============================================

    ooo_flush = UBool(0)

    tlb_start = UBool(0)
    tlb_drop = UBool(0)
    tlb_timer = UInt(9, max=511)
    tlb_timeout = UBool(0)
    prf_load = UBool(0)
    prf_va_match = UBool(0)
    prf_sync = UBool(0)
    cross_page = UBool(0)

    # address adder
    iva = UInt(len(ibase)+6)

    # staging buffer
    stage_va = UInt((len(ibase)+6))
    stage_hint = UBool(0)
    stage_dst = UBool(0)
    stage_type = UBool(0)
    stage_keep = UBool(0)
    stage_tid = UBool(0)

    # mux-ed output
    va = UInt(len(iva))
    hint = UBool(0)
    dst = UBool(0)
    type = UBool(0)
    keep = UBool(0)
    tid = UBool(0)

    # uuTLB entry
    uutlb_vld = UBool(0)
    uutlb_va = UInt(len(iva))
    uutlb_tid = UBool(0)

    uutlb_page_size = UInt(3)
    uutlb_sharable = UInt(2)
    uutlb_pa = UInt(len(iprf_pa))

    # tlb prefetch response pipe
    prf_vld = UBool()
    prf_va = UInt(len(iprf_va))
    prf_pa = UInt(len(iprf_pa))
    prf_page_size = UInt(len(iprf_page_size))
    prf_shareable = UBool(0)
    prf_flush = UBool(0)
    prf_tid = UBool(0)
    prf_pbha = UInt(len(iprf_pbha))
    prf_drop = UBool(0)
    prf_prf = UBool(0)

    st = UEnum(TLB_STATE)
    nxt = UEnum(TLB_STATE)

    # pipeline internal stall
    stop = UBool(0)             # FSM stop
    stall = UBool(0)            # internal stall
    ostall = UBool(0)           # output pipeline stall

    # =============================================
    # staging buffer
    # =============================================
    @always_ff(clk.posedge, reset=rst_n)
    def staging():
        if flush:
            stage_va.next = 0
            stage_hint.next = False
            stage_dst.next = False
            stage_type.next = False
            stage_keep.next = False
            stage_tid.next = False
        elif not stall and enable:
            stage_va.next = iva
            stage_hint.next = ihint
            stage_dst.next = idst
            stage_type.next = itype
            stage_keep.next = ikeep
            stage_tid.next = itid
        else:
            stage_va.next = iva
            stage_hint.next = ihint
            stage_dst.next = idst
            stage_type.next = itype
            stage_keep.next = ikeep
            stage_tid.next = itid

    @always_comb
    def mux():
        va.next = stage_va if psel else iva
        hint.next = stage_hint if psel else ihint
        dst.next = stage_dst if psel else idst
        type.next = stage_type if psel else itype
        keep.next = stage_keep if psel else ikeep
        tid.next = stage_tid if psel else itid

    # =============================================
    # pipeline control
    # =============================================

    @always_comb
    def glb_ctrl():
        ooo_flush.next = i_ooo_flush if uutlb_tid == i_ooo_flush_tid else False
        prf_va_match = True if prf_va == uutlb_va[:12] and prf_tid == uutlb_tid else False
        prf_sync.next = prf_vld and prf_va_match and not prf_drop and not prf_flush

        tlb_timeout.next = True if st == TLB_STATE.WAIT and tlb_timer == 511 else False
        cross_page.next = not (iva == uutlb_va) & uutlb_vld

    @always_ff(clk.posedge, reset=rst_n)
    def fsm_state():
        if enable:
            st.next = nxt
        else:
            st.next = st

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
            elif tlb_start or tlb_drop or ooo_flush:
                nxt.next = TLB_STATE.TLB
            else:
                nxt.next = TLB_STATE.WAIT

        elif st == TLB_STATE.WAIT:
            if flush:
                nxt.next = TLB_STATE.IDLE
            elif tlb_start or ooo_flush or tlb_drop or tlb_timeout:
                nxt.next = TLB_STATE.TLB
            else:
                if prf_sync:
                    nxt.next = TLB_STATE.SYNC
                else:
                    nxt.next = TLB_STATE.WAIT

        elif st == TLB_STATE.SYNC:
            if flush:
                nxt.next = TLB_STATE.IDLE
            elif tlb_start or ooo_flush:
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
        elif enable:
            if st == TLB_STATE.WAIT and prf_sync:
                uutlb_vld.next = True
            elif st == TLB_STATE.SYNC and cross_page:
                uutlb_vld.next = False
            else:
                uutlb_vld.next = uutlb_vld
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
            uutlb_sharable.next = prf_shareable

        else:  # hold
            uutlb_pa.next = uutlb_pa
            uutlb_page_size.next = uutlb_page_size
            uutlb_sharable.next = prf_shareable

    # =============================================
    # data path & controls
    # =============================================

    @always_ff(clk.posedge, reset=rst_n)
    def va_controls():
        if flush:
            pass



    @always_ff(clk.posedge, reset=rst_n)
    def pa_control():
        if flush:
            pass



    @always_ff(clk.posedge, reset=rst_n)
    def attr_control():
        pass


    @always_ff(clk.posedge, reset=rst_n)
    def handshake():
        # ovalid
        if flush or tlb_start:
            req_vld.next = False
        elif st == TLB_STATE.WAIT:
            req_vld.next = True if prf_sync else False
        elif st == TLB_STATE.SYNC:
            req_vld.next = False if cross_page or tlb_drop else True
        else:
            req_vld.next = req_vld


    # =============================================
    # TLB prefetch response
    # =============================================
    @always_ff(clk.posedge, reset=rst_n)
    def _tlb_resp():
        if enable:
            prf_vld.next = iprf_vld
            prf_va.next = iprf_va
            prf_pa.next = iprf_pa
            prf_page_size.next = iprf_page_size
            prf_shareable.next = iprf_shareable
            prf_flush.next = iprf_flush
            prf_tid.next = iprf_tid
            prf_pbha.next = iprf_pbha
            prf_drop.next = iprf_drop
            prf_prf.next = iprf_prf



    # =============================================
    # back pressure control
    # =============================================
    @always_comb
    def back_pressure():
        if st == TLB_STATE.IDLE:
            stall.next = False
        else:
            stall.next = not flush | stop | istall

        ostall.next = stall

    return instances()


def convert():

    pass
