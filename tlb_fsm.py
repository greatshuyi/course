from myhdl import (
    block, always_comb, always, instances, instance,
    enum
)
from myhdl import ConcatSignal as concat
from pipeline.hdl import *


@block
def va_adder(base, offset, va):

    ZEROS = 0b000000
    # va_tmp = UInt(len(va))

    @always_comb
    def _adder():
        va.next = concat(base, ZEROS) + offset

    return instances()


va_adder.verilog_code = \
"""
assign $va = {$base, {6{1'b0}}} + $offset;
"""


@block
def pa_composer(uutlb_va, va,
                uutlb_pa, prf_pa,
                page_size,
                pa_sel,
                pa):
    @always_comb
    def composer():

        # 4K
        if page_size == 0:
            pa.next = concat(0b00000000, uutlb_pa, va[6:]) if \
                pa_sel else concat(0b00000000, prf_pa, uutlb_va[6:])
        # 16K
        elif page_size == 1:
            pa.next = concat(0b00000000, uutlb_pa, va[8:]) if \
                pa_sel else concat(0b00000000, prf_pa, uutlb_va[8:])
        # 64K
        elif page_size == 2:
            pa.next = concat(0b00000000, uutlb_pa, va[10:]) if \
                pa_sel else concat(0b00000000, prf_pa, uutlb_va[10:])
        # 2M
        elif page_size == 2:
            pa.next = concat(0b00000000, uutlb_pa, va[15:]) if \
                pa_sel else concat(0b00000000, prf_pa, uutlb_va[15:])
        # 32M
        elif page_size == 2:
            pa.next = concat(0b00000000, uutlb_pa, va[19:]) if \
                pa_sel else concat(0b00000000, prf_pa, uutlb_va[19:])
        # 512M
        elif page_size == 2:
            pa.next = concat(0b00000000, uutlb_pa, va[23:]) if \
                pa_sel else concat(0b00000000, prf_pa, uutlb_va[23:])
        # 1G
        elif page_size == 2:
            pa.next = concat(0b00000000, uutlb_pa, va[24:]) if \
                pa_sel else concat(0b00000000, prf_pa, uutlb_va[24:])
        # 16G
        else:
            pa.next = concat(0b00000000, uutlb_pa, va[28:]) if \
                pa_sel else concat(0b00000000, prf_pa, uutlb_va[28:])

    return composer


pa_composer.verilog_code = \
"""
wire [40:6] fpa_lo = $page_size == 0 ? {$prf_pa[28: 0], $uutlb_va[5 :0]} :
                     $page_size == 1 ? {$prf_pa[28: 2], $uutlb_va[7 :0]} :
                     $page_size == 2 ? {$prf_pa[28: 4], $uutlb_va[9 :0]} :
                     $page_size == 3 ? {$prf_pa[28: 9], $uutlb_va[14:0]} :
                     $page_size == 4 ? {$prf_pa[28:13], $uutlb_va[18:0]} :
                     $page_size == 5 ? {$prf_pa[28:17], $uutlb_va[22:0]} :
                     $page_size == 6 ? {$prf_pa[28:18], $uutlb_va[23:0]} :
                     $page_size == 7 ? {$prf_pa[28:22], $uutlb_va[27:0]} : 35'b0;
                     
wire [40:6] spa_lo = $page_size == 0 ? {$uutlb_pa[28: 0], $va[5 :0]} :
                     $page_size == 1 ? {$uutlb_pa[28: 2], $va[7 :0]} :
                     $page_size == 2 ? {$uutlb_pa[28: 4], $va[9 :0]} :
                     $page_size == 3 ? {$uutlb_pa[28: 9], $va[14:0]} :
                     $page_size == 4 ? {$uutlb_pa[28:13], $va[18:0]} :
                     $page_size == 5 ? {$uutlb_pa[28:17], $va[22:0]} :
                     $page_size == 6 ? {$uutlb_pa[28:18], $va[23:0]} :
                     $page_size == 7 ? {$uutlb_pa[28:22], $va[27:0]} : 35'b0;
 
assign $pa = $pa_sel ? {{8{1'b0}}, spa_lo} : {{8{1'b0}}, fpa_lo};
"""


@block
def cross_page_check(va, tid,
                     uutlb_va, uutlb_page_size, uutlb_tid,
                     cross_page
                     ):
    same_4k = UBool(0)
    same_16k = UBool(0)
    same_64k = UBool(0)
    same_2m = UBool(0)
    same_32m = UBool(0)
    same_512m = UBool(0)
    same_1g = UBool(0)
    same_16g = UBool(0)
    # page_4k = UBool(0)
    # page_16k = UBool(0)
    # page_64k = UBool(0)
    # page_2m = UBool(0)
    # page_32m = UBool(0)
    # page_512m = UBool(0)
    # page_1g = UBool(0)
    # page_16g = UBool(0)
    same_page = UBool(0)

    @always_comb
    def same_page():
        same_4k.next   = True if va[: 6] == uutlb_va[: 6] else False
        same_16k.next  = True if va[: 8] == uutlb_va[: 8] else False
        same_64k.next  = True if va[:10] == uutlb_va[:10] else False
        same_2m.next   = True if va[:15] == uutlb_va[:15] else False
        same_32m.next  = True if va[:19] == uutlb_va[:19] else False
        same_512m.next = True if va[:23] == uutlb_va[:23] else False
        same_1g.next   = True if va[:29] == uutlb_va[:29] else False
        same_16g.next  = True if va[:28] == uutlb_va[:28] else False

    @always_comb
    def same_page_size():
        if uutlb_page_size == 0:
            same_page.next = same_4k
        elif uutlb_page_size == 1:
            same_page.next = same_16k
        elif uutlb_page_size == 2:
            same_page.next = same_64k
        elif uutlb_page_size == 3:
            same_page.next = same_2m
        elif uutlb_page_size == 4:
            same_page.next = same_32m
        elif uutlb_page_size == 5:
            same_page.next = same_512m
        elif uutlb_page_size == 6:
            same_page.next = same_1g
        elif uutlb_page_size == 7:
            same_page.next = same_16g
        else:
            same_page.next = False

    @always_comb
    def cross_page():
        cross_page.next = not same_page or (uutlb_tid != tid)

    return instances()


cross_page_check.verilog_code = \
"""
// wire page_4k   = ($uutlb_page_size == 0) ? 1'b1 : 1'b0;
// wire page_16k  = ($uutlb_page_size == 1) ? 1'b1 : 1'b0;
// wire page_64k  = ($uutlb_page_size == 2) ? 1'b1 : 1'b0;
// wire page_2m   = ($uutlb_page_size == 3) ? 1'b1 : 1'b0;
// wire page_32m  = ($uutlb_page_size == 4) ? 1'b1 : 1'b0;
// wire page_512m = ($uutlb_page_size == 5) ? 1'b1 : 1'b0;
// wire page_1g   = ($uutlb_page_size == 6) ? 1'b1 : 1'b0;
// wire page_16g  = ($uutlb_page_size == 7) ? 1'b1 : 1'b0;
wire same_4k   = ($va[42: 6] == $uutlb_va[42: 6]) ? 1'b1 : 1'b0;
wire same_16k  = ($va[42: 8] == $uutlb_va[42: 8]) ? 1'b1 : 1'b0;
wire same_64k  = ($va[42:10] == $uutlb_va[42:10]) ? 1'b1 : 1'b0;
wire same_2m   = ($va[42:15] == $uutlb_va[42:15]) ? 1'b1 : 1'b0;
wire same_32m  = ($va[42:19] == $uutlb_va[42:19]) ? 1'b1 : 1'b0;
wire same_512m = ($va[42:23] == $uutlb_va[42:23]) ? 1'b1 : 1'b0;
wire same_1g   = ($va[42:29] == $uutlb_va[42:29]) ? 1'b1 : 1'b0;
wire same_16g  = ($va[42:28] == $uutlb_va[42:28]) ? 1'b1 : 1'b0;

wire same_page = ($uutlb_page_size == 0) ? same_4k   :
                 ($uutlb_page_size == 1) ? same_16k  :
                 ($uutlb_page_size == 2) ? same_64k  :
                 ($uutlb_page_size == 3) ? same_2m   :
                 ($uutlb_page_size == 4) ? same_32m  :
                 ($uutlb_page_size == 5) ? same_512m :
                 ($uutlb_page_size == 6) ? same_1g   :
                 ($uutlb_page_size == 7) ? same_16g  : 1'b0 ;

assign $cross_page = (tid ^ $uutlb_tid) | ~same_page;

"""


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
    oreq_pa,                        # OUT	[40:6]
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
    tlb_timer = UInt(10, max=511)
    tlb_timeout = UBool(0)
    prf_load = UBool(0)
    prf_va_match = UBool(0)
    prf_sync = UBool(0)
    cross_page = UBool(0)

    # address adder
    iva = UInt((len(ibase)+6))

    # staging buffer
    stage_va = UInt(len(iva))
    stage_hint = UBool(0)
    stage_dst = UBool(0)
    stage_type = UBool(0)
    stage_keep = UBool(0)
    stage_tid = UBool(0)
    
    stage_load = UBool(0)

    # mux-ed output
    va = UInt(len(ibase))
    hint = UBool(0)
    dst = UBool(0)
    typ = UBool(0)
    keep = UBool(0)
    tid = UBool(0)

    # generated prefetch request
    pa = UInt(len(oreq_pa))
    hash_pc = UInt(len(oreq_hash_pc))
    page_size = UInt(len(oreq_page_size))
    v1312 = UInt(len(oreq_va1312))
    shareable = UInt(len(oreq_shareable))
    mair = UInt(len(oreq_mair))
    rid = UInt(len(oreq_rid))

    # selection between different PA source
    pa_sel = UBool(0)

    # uuTLB entry
    uutlb_vld = UBool(0)
    uutlb_va = UInt((len(ibase)))
    uutlb_tid = UBool(0)

    uutlb_page_size = UInt(3)
    uutlb_shareable = UBool(0)
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

    # st = UEnum(TLB_STATE)
    # nxt = UEnum(TLB_STATE)

    # pipeline internal stall
    stop = UBool(0)             # FSM stop
    stall = UBool(0)            # internal stall

    # =============================================
    # va generation
    # =============================================

    adder = va_adder(base=ibase, offset=ioffset, va=iva)

    # =============================================
    # staging buffer
    # =============================================
    @always_comb
    def staging_en():
        stage_load.next = tlb_start or st == TLB_STATE.IDLE or ((st == TLB_STATE.TLB or st == TLB_STATE.WAIT) and tlb_drop) or (st == TLB_STATE.SYNC and enable and not stall)

    @always_ff(clk.posedge, reset=rst_n)
    def staging():
        if flush:
            stage_va.next = 0
            stage_hint.next = False
            stage_dst.next = False
            stage_type.next = False
            stage_keep.next = False
            stage_tid.next = False
        # elif not stall and enable:
        elif stage_load:
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
        va.next = stage_va[:6] if stall else iva[:6]
        hint.next = stage_hint if stall else ihint
        dst.next = stage_dst if stall else idst
        typ.next = stage_type if stall else itype
        keep.next = stage_keep if stall else ikeep
        tid.next = stage_tid if stall else itid

    # =============================================
    # pipeline control
    # =============================================

    @always_comb
    def glb_ctrl():
        tlb_start.next = istart and enable
        tlb_drop.next = idrop and enable
        ooo_flush.next = i_ooo_flush & enable if uutlb_tid == i_ooo_flush_tid else False
        tlb_timeout.next = True if st == TLB_STATE.WAIT and tlb_timer == 511 and enable else False

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

    @always_comb
    def _stop():
        stop.next = True if st == TLB_STATE.TLB or st == TLB_STATE.WAIT else False

    # timer
    @always_ff(clk.posedge, reset=rst_n)
    def monitor():
        if enable:
            if (st == TLB_STATE.TLB or st == TLB_STATE.WAIT) and nxt == TLB_STATE.WAIT:
                tlb_timer.next = 0 if tlb_timer == 511 else tlb_timer + 1
            else:
                tlb_timer.next = 0
        else:
            tlb_timer.next = tlb_timer

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

    @always_comb
    def _tlb_match():
        prf_va_match.next = (prf_va == uutlb_va[:6]) and (prf_tid == uutlb_tid)

    @always_comb
    def _tlb_cam():
        prf_sync.next = prf_vld and (prf_va_match and not prf_drop and not prf_flush)\
                        and (not tlb_timeout and not tlb_start and not tlb_drop and not ooo_flush)

    # =============================================
    # TLB prefetch request
    # =============================================
    @always_comb
    def _oprf_load():
        prf_load.next = tlb_start or \
                        (st == TLB_STATE.TLB and tlb_drop) or \
                        (st == TLB_STATE.WAIT and (tlb_drop or ooo_flush)) or \
                        (st == TLB_STATE.SYNC and (cross_page or ooo_flush))
        
    @always_ff(clk.posedge, reset=rst_n)
    def _oprf_attr():
        if flush:
            oprf_vld.next = False
        else:
            if tlb_start:
                oprf_vld.next = True
            elif st == TLB_STATE.TLB and tlb_drop:
                oprf_vld.next = True
            elif st == TLB_STATE.WAIT and (tlb_timeout or tlb_drop or ooo_flush):
                oprf_vld.next = True
            elif st == TLB_STATE.SYNC and (cross_page or ooo_flush):
                oprf_vld.next = True
            else:
                oprf_vld.next = False

    @always_ff(clk.posedge, reset=rst_n)
    def _oprf_pld_sel():
        """VA, TID, HASH_PC always load from stage output or hold"""
        # if tlb_start:
        #     oprf_va.next = va[:12]
        # elif st == TLB_STATE.WAIT and tlb_drop:
        #     oprf_va.next = va[:12]
        # elif st == TLB_STATE.WAIT and not tlb_drop and (tlb_timeout or ooo_flush):
        #     oprf_va.next = oprf_va
        # elif st == TLB_STATE.SYNC and (cross_page or ooo_flush):
        #     oprf_va.next = va[:12]
        # else:
        #     oprf_va.next = oprf_va
        if prf_load:
            oprf_va.next = va[:6]
            oprf_tid.next = tid
            oprf_hash_pc.next = va[11:]
        else:
            oprf_va.next = oprf_va
            oprf_tid.next = oprf_tid
            oprf_hash_pc.next = oprf_hash_pc

    @always_ff(clk.posedge, reset=rst_n)
    def _oprf_pld():
        oprf_pgt.next = False
        oprf_pa.next = 0
        oprf_shared.next = True
        oprf_spd.next = 0
        oprf_typ.next = 1
        oprf_page_size.next = 0
        oprf_dir.next = 0
        oprf_delta_hi.next = 0
        oprf_st.next = False
        oprf_prf.next = True

    # =============================================
    # uuTLB & controls
    # =============================================

    # Remember: incoming prefetch response always compared to va not prev_va!!!
    @always_ff(clk.posedge, reset=rst_n)
    def _uutlb_vld():
        # valid
        if flush or tlb_start or ooo_flush or (st == TLB_STATE.SYNC and cross_page):
            uutlb_vld.next = False
        elif enable:
                uutlb_vld.next = True if st == TLB_STATE.WAIT and prf_sync else False
        else:
            uutlb_vld.next = uutlb_vld

    @always_ff(clk.posedge, reset=rst_n)
    def _uutlb_va_tid():
        if prf_load:
            uutlb_va.next = iva[:6]
            uutlb_tid.next = tid
        else:
            uutlb_va.next = uutlb_va
            uutlb_tid.next = tid

    @always_ff(clk.posedge, reset=rst_n)
    def _uutlb_pld():
        # page size/pa/...
        if enable and st == TLB_STATE.WAIT and prf_sync:
            uutlb_pa.next = prf_pa
            uutlb_page_size.next = prf_page_size
            uutlb_shareable.next = prf_shareable

        else:  # hold
            uutlb_pa.next = uutlb_pa
            uutlb_page_size.next = uutlb_page_size
            uutlb_shareable.next = uutlb_shareable

    # =============================================
    # data path & controls
    # =============================================
    # BZERO = 0b0
    # shareable_t1 = concat(BZERO, uutlb_shareable)
    # shareable_t2 = concat(BZERO, prf_shareable)
    shareable_t1 = UInt(2)
    shareable_t2 = UInt(2)

    @always_comb
    def _shareable():
        shareable_t1.next = 1 if uutlb_shareable else 0
        shareable_t2.next = 1 if prf_shareable else 0

    @always_comb
    def _oreq_pld_1():
        pa_sel.next = True if st == TLB_STATE.SYNC else False
        page_size.next = uutlb_page_size if st == TLB_STATE.SYNC else prf_page_size
        # shareable.next = concat(0b0, uutlb_shareable) if st == TLB_STATE.SYNC else concat(0b0, prf_shareable)
        shareable.next = shareable_t1 if st == TLB_STATE.SYNC else shareable_t2
        v1312.next = uutlb_va[8:6] if st == TLB_STATE.SYNC else va[8:6]
        hash_pc.next = uutlb_va[13:6] if st == TLB_STATE.SYNC else va[13:6]
        mair.next = uutlb_va[14:9] if st == TLB_STATE.SYNC else va[14:9]
        rid.next = uutlb_va[14:6] if st == TLB_STATE.SYNC else va[8:6]

    page_check = cross_page_check(va=va, tid=tid,
                                  uutlb_va=uutlb_va, uutlb_page_size=uutlb_page_size,
                                  uutlb_tid=uutlb_tid,
                                  cross_page=cross_page,
                                  )
    
    composer = pa_composer(uutlb_va=uutlb_va, va=va,
                           uutlb_pa=uutlb_pa, prf_pa=prf_pa, 
                           page_size=page_size, pa_sel=pa_sel,
                           pa=pa)

    @always_ff(clk.posedge, reset=rst_n)
    def _oreq_pld():
        if (st == TLB_STATE.WAIT and prf_sync) or (st == TLB_STATE.SYNC and not istall):
            oreq_dst.next = dst
            oreq_keep.next = keep
            oreq_typ.next = typ
            oreq_prf.next = True
            oreq_hash_pc.next = hash_pc
            oreq_page_size.next = page_size
            oreq_tid.next = tid
            oreq_va1312.next = v1312
            oreq_shareable.next = shareable
            oreq_pa.next = pa
            oreq_mair.next = mair
            oreq_rid.next = rid
        else:
            oreq_dst.next = oreq_dst
            oreq_keep.next = oreq_keep
            oreq_typ.next = oreq_typ
            oreq_prf.next = oreq_prf
            oreq_hash_pc.next = oreq_hash_pc
            oreq_page_size.next = oreq_page_size
            oreq_tid.next = oreq_tid
            oreq_va1312.next = oreq_va1312
            oreq_shareable.next = oreq_shareable
            oreq_pa.next = oreq_pa
            oreq_mair.next = oreq_mair
            oreq_rid.next = oreq_rid

    @always_ff(clk.posedge, reset=rst_n)
    def _oreq_vld():
        if flush or tlb_start:
            oreq_vld.next = False
        else:
            if st == TLB_STATE.WAIT and prf_sync:
                oreq_vld.next = True
            elif st == TLB_STATE.SYNC:
                oreq_vld.next = False if cross_page or ooo_flush else True
            else:
                oreq_vld.next = False

    # =============================================
    # back pressure control
    # =============================================
    @always_comb
    def back_pressure():
        if st == TLB_STATE.IDLE:
            stall.next = False
        else:
            stall.next = not flush | stop | istall

    @always_comb
    def _ostall():
        ostall.next = stall

    return instances()


def convert():

    BASE_VA_WIDTH = 43 # [48:6]
    OFFSET_WIDTH = 11

    OPRF_VA_WIDTH = 37 # [48:12]
    OPRF_PA_WIDTH = 39 # [40: 2]
    OPRF_HASH_PC_WIDTH = 11 # [10: 0]
    OPRF_DELTA_HI_WIDTH = 4 # [15:12]

    IPRF_VA_WIDTH = 37 # [48:12]
    IPRF_PA_WIDTH = 29 # [40:12]

    OREQ_HASH_PC_WIDTH = 7 # [6:0]
    OREQ_PA_WIDTH = 43 # [48:6]

    clk = UBool(0)
    rst_n = AsyncReset(0)
    enable = UBool(0)
    flush = UBool(0)

    # ooo flush
    i_ooo_flush = UBool(0)
    i_ooo_flush_tid = UBool(0)

    # pipeline input command
    istart = UBool(0)
    idrop = UBool(0)
    ibase = UInt(BASE_VA_WIDTH)
    ioffset = UInt(OFFSET_WIDTH)
    ihint = UBool(0)
    idst = UBool(0)
    itype = UBool(0)
    ikeep = UBool(0)
    itid = UBool(0)

    # tlb prefetch request
    oprf_vld = UBool(0)
    oprf_pgt = UBool(0)
    oprf_va = UInt(OPRF_VA_WIDTH)
    oprf_pa = UInt(OPRF_PA_WIDTH)
    oprf_shared = UBool(0)
    oprf_spd = UInt(2)
    oprf_typ = UInt(2)
    oprf_hash_pc = UInt(OPRF_HASH_PC_WIDTH)
    oprf_page_size = UInt(3)
    oprf_dir = UBool(0)
    oprf_delta_hi = UInt(OPRF_DELTA_HI_WIDTH)
    oprf_st = UBool(0)
    oprf_tid = UBool(0)
    oprf_prf = UBool(0)

    # tlb prefetch response
    iprf_vld = UBool(0)
    iprf_va = UInt(IPRF_VA_WIDTH)
    iprf_pa = UBool(IPRF_PA_WIDTH)
    iprf_page_size = UInt(3)
    iprf_shareable = UBool(0)
    iprf_flush = UBool(0)
    iprf_tid = UBool(0)
    iprf_pbha = UInt(2)
    iprf_drop = UBool(0)
    iprf_prf = UBool(0)

    # downstream NL channel
    oreq_vld = UBool(0)  # OUT   1
    oreq_dst = UBool(0)  # OUT	1
    oreq_keep = UBool(0)  # OUT	1
    oreq_typ = UBool(0)  # OUT	1
    oreq_prf = UBool(0)  # OUT	1
    oreq_hash_pc = UInt(OREQ_HASH_PC_WIDTH)   # OUT	1           PLE always send out True
    oreq_page_size = UInt(2)  # OUT	[48:0]
    oreq_tid = UBool(0)  # OUT	[1:0]
    oreq_va1312 = UInt(2)  # OUT	[4:0]
    oreq_shareable = UInt(2)  # OUT	[1:0]
    oreq_pa = UInt(OREQ_PA_WIDTH)  # OUT	[40:6]
    oreq_mair = UInt(5)  # OUT   [4:0]
    oreq_rid = UInt(8)  # OUT	[7:0]

    # pipeline backpressure
    istall = UBool(0)
    ostall = UBool(0)

    # monitor
    st = UEnum(TLB_STATE)
    nxt = UEnum(TLB_STATE)

    tlb = tlb_ctrl(
        clk=clk,
        rst_n=rst_n,
        enable=enable,
        flush=flush,

        # ooo flush
        i_ooo_flush=i_ooo_flush,
        i_ooo_flush_tid=i_ooo_flush_tid,

        # pipeline input command
        istart=istart,
        idrop=idrop,
        ibase=ibase,
        ioffset=ioffset,
        ihint=ihint,
        idst=idst,
        itype=itype,
        ikeep=ikeep,
        itid=itid,
        # tlb prefetch request
        oprf_vld=oprf_vld,
        oprf_pgt=oprf_pgt,
        oprf_va=oprf_va,
        oprf_pa=oprf_pa,
        oprf_shared=oprf_shared,
        oprf_spd=oprf_spd,
        oprf_typ=oprf_typ,
        oprf_hash_pc=oprf_hash_pc,
        oprf_page_size=oprf_page_size,
        oprf_dir=oprf_dir,
        oprf_delta_hi=oprf_delta_hi,
        oprf_st=oprf_st,
        oprf_tid=oprf_tid,
        oprf_prf=oprf_prf,

        # tlb prefetch response
        iprf_vld=iprf_vld,
        iprf_va=iprf_va,
        iprf_pa=iprf_pa,
        iprf_page_size=iprf_page_size,
        iprf_shareable=iprf_shareable,
        iprf_flush=iprf_flush,
        iprf_tid=iprf_tid,
        iprf_pbha=iprf_pbha,
        iprf_drop=iprf_drop,
        iprf_prf=iprf_prf,

        # downstream NL channel
        oreq_vld=oreq_vld,                       # OUT   1
        oreq_dst=oreq_dst,                       # OUT	1
        oreq_keep=oreq_keep,                      # OUT	1
        oreq_typ=oreq_typ,                       # OUT	1
        oreq_prf=oreq_prf,                       # OUT	1
        oreq_hash_pc=oreq_hash_pc,                   # OUT	1           PLE always send out True
        oreq_page_size=oreq_page_size,                 # OUT	[48:0]
        oreq_tid=oreq_tid,                       # OUT	[1:0]
        oreq_va1312=oreq_va1312,                    # OUT	[4:0]
        oreq_shareable=oreq_shareable,                 # OUT	[1:0]
        oreq_pa=oreq_pa,                        # OUT	[40:6]
        oreq_mair=oreq_mair,                      # OUT   [4:0]
        oreq_rid=oreq_rid,

        # pipeline backpressure
        istall=istall,
        ostall=ostall,

        # monitor
        st=st,
        nxt=nxt

    )

    tlb.convert(hdl='Verilog')


convert()
