# -*- coding: utf-8 -*-

from myhdl import (
    block, always_comb, always, instances, instance,
    enum
)
from myhdl import ConcatSignal as concat
from pipeline.hdl import *



POT_STATE = enum('IDLE', 'RD', 'PEND')


POT_STATE = enum('IDLE', 'RD', 'PEND')

@block
def pot_ctrl(clk, rst_n, enable,
             flush,
             istart,
             iindex,
             icolumn,
             iamount,
             ibase,
             imode,
             iprf_mode,
             itid,
             ram_ren,
             ram_index,
             ram_offset,
             ostart,
             odrop,
             omode,
             obase,
             otid,
             cnt,
             istall,
             oack,
             st,
             nxt,
             rcen,
             rren,
             raddr
             ):
    # =============================================
    # Constant & Parameter
    # =============================================
    MAX_OFFSET = 14
    MAX_INDEX = 64
    OFFSET_LIMIT = MAX_OFFSET-1
    INDEX_LIMIT = MAX_INDEX-1

    MAX_TIMER = 1024

    # =============================================
    # Sigs and pipe registers
    # =============================================

    # cnt = UInt(len(iamount))  # pipe register of amount counter
    idx = UInt(len(iindex))  # pipe register of index
    oft = UInt(len(icolumn))  # pipe register of offset

    nxt_cnt = UInt(len(iamount))
    nxt_idx = UInt(len(iindex))
    nxt_oft = UInt(len(icolumn))
    nxt_idx = UInt(len(iindex))
    nxt_cnt = UInt(len(iamount))

    timer = UInt(11)  # pending time out timer

    pot_start = UBool(0)
    pot_complete = UBool(0)  # complete all transfer or reach POT last column
    pot_timeout = UBool(0)

    # =============================================
    # pipeline control
    # =============================================

    # FSM start condition
    @always_comb
    def fsm_start():
        pot_start.next = istart and iamount != 0
        pot_complete.next = nxt_cnt == 0 or (idx == INDEX_LIMIT) and (oft == OFFSET_LIMIT)
        pot_timeout.next = True if timer == MAX_TIMER else False

    # pipe FSM
    @always_ff(clk.posedge, reset=rst_n)
    def fsm_state():
        if enable:
            st.next = nxt
        else:
            st.next = st

    @always_comb
    def fsm_transition():

        if st == POT_STATE.IDLE:
            if flush:
                nxt.next = POT_STATE.IDLE
            else:
                nxt.next = POT_STATE.RD if pot_start else POT_STATE.IDLE

        elif st == POT_STATE.RD:
            if flush:
                nxt.next = POT_STATE.IDLE
            elif pot_start:
                nxt.next = POT_STATE.RD
            else:
                if istall:
                    nxt.next = POT_STATE.PEND
                else:
                    nxt.next = POT_STATE.IDLE if pot_complete else POT_STATE.RD

        elif st == POT_STATE.PEND:
            if flush:
                nxt.next = POT_STATE.IDLE
            else:
                nxt.next = POT_STATE.RD if pot_start or pot_timeout or not istall else POT_STATE.PEND

        else:
            nxt.next = POT_STATE.IDLE

    # =============================================
    # pipeline monitor
    # =============================================
    @always_ff(clk.posedge, reset=rst_n)
    def pipe_counter():
        if flush or pot_start:
            timer.next = 0
        else:
            if (st == POT_STATE.RD or st == POT_STATE.PEND) and istall:
                timer.next = 0 if timer == MAX_TIMER else timer + 1
            else:
                timer.next = 0

    # =============================================
    # pipeline payload/register control
    # =============================================

    @always_ff(clk.posedge, reset=rst_n)
    def pipe_registers():
        if enable:
            idx.next = nxt_idx
            oft.next = nxt_oft
            cnt.next = nxt_cnt
        else:
            idx.next = idx
            oft.next = oft
            cnt.next = cnt

    @always_comb
    def _cnt_ctrl():
        if flush:
            nxt_cnt.next = 0
        else:
            if pot_start:
                nxt_cnt.next = iamount
            elif not istall:
                nxt_cnt.next = cnt - 1 if cnt != 0 else 0
            else:
                nxt_cnt.next = cnt

    @always_comb
    def _oft_ctrl():
        if flush:
            nxt_oft.next = 0
        else:
            if pot_start:
                nxt_oft.next = icolumn
            elif not istall and idx != INDEX_LIMIT:
                nxt_oft.next = 0 if oft == OFFSET_LIMIT else oft + 1
            else:
                nxt_oft.next = idx

    @always_comb
    def _idx_ctrl():
        if flush:
            nxt_idx.next = 0
        else:
            if pot_start:
                nxt_idx.next = iindex
            elif not istall and idx != INDEX_LIMIT and oft != OFFSET_LIMIT:
                    nxt_idx.next = idx + 1
            else:
                nxt_idx.next = idx

    @always_ff(clk.posedge, reset=rst_n)
    def start_ctrl():
        if flush or not enable:
            ostart.next = False
        else:
            ostart.next = istart

    @always_ff(clk.posedge, reset=rst_n)
    def drop_ctrl():
        if flush:
            odrop.next = False
        else:
            odrop.next = True if (st == POT_STATE.PEND and pot_timeout and enable) else False

    @always_ff(clk.posedge, reset=rst_n)
    def base_control():
        if flush:
            obase.next = 0
        else:
            obase.next = ibase if pot_start and enable else obase

    @always_ff(clk.posedge, reset=rst_n)
    def mode_control():
        if flush:
            omode.next = 0
        else:
            omode.next = imode if pot_start and enable else omode

    @always_ff(clk.posedge, reset=rst_n)
    def tid_ctrl():
        if flush:
            otid.next = False
        else:
            otid.next = itid if pot_start and enable else otid

    # =============================================
    # command acknowledge
    # =============================================

    @always_ff(clk.posedge, reset=rst_n)
    def oack_ctrl():
        if flush or pot_start:
            oack.next = False
        else:
            oack.next = True if not enable or (not oack and st == POT_STATE.RD and pot_complete) else False

    # =============================================
    # SRAM controls
    # =============================================

    @always_comb
    def ram_control():
        ram_ren.next = True if not flush and (pot_start and st == POT_STATE.IDLE or st == POT_STATE.RD) else False
        ram_index.next = iindex if pot_start else idx
        ram_offset.next = icolumn if pot_start else oft

    if __debug__:
        raddr_cat = concat(ram_index, ram_offset)

        @always_comb
        def ram_sim():
            rcen.next = ram_ren
            rren.next = ram_ren
            # raddr.next = concat(ram_index, ram_offset)
            raddr.next = raddr_cat

    return instances()


def convert():
    clk = UBool(0)
    rst_n = AsyncReset(0)

    BASE_VA_WIDTH = 43      # [48:6]
    INDEX_WIDTH = 6         # [60:55]
    COLUMN_WIDTH = 4        # [54:51]
    AMOUNT_WIDTH = 7        # [50:44]

    # wires
    enable = UBool(0)
    flush = UBool(0)

    istart = UBool(0)
    ibase = UInt(BASE_VA_WIDTH)
    iindex = UInt(INDEX_WIDTH)
    icolumn = UInt(COLUMN_WIDTH)
    iamount = UInt(AMOUNT_WIDTH)
    imode = UInt(2)

    iprf_mode = UInt(2)
    itid = UBool(0)
    ram_ren = UBool(0)
    ram_index = UInt(INDEX_WIDTH)
    ram_offset = UInt(COLUMN_WIDTH)
    ostart = UBool(0)
    odrop = UBool(0)
    omode = UInt(2)
    obase = UInt(BASE_VA_WIDTH)
    otid = UBool(0)
    cnt = UInt(AMOUNT_WIDTH)
    istall = UBool(0)
    oack = UBool(0)
    st = UEnum(POT_STATE)
    nxt = UEnum(POT_STATE)
    rcen = UBool(0)
    rren = UBool(0)
    raddr = UInt(INDEX_WIDTH+COLUMN_WIDTH)

    # Instance
    # OFFSET_TABLE = [i + 1 for i in range(2 ** (INDEX_WIDTH+COLUMN_WIDTH))]

    # ram = ssrom(clk=clk, ren=rren, addr=raddr,
    #             dout=pipe_offset, CONTENT=OFFSET_TABLE)

    pot = pot_ctrl(clk=clk, rst_n=rst_n, enable=enable,
                   flush=flush,
                   istart=istart,
                   iindex=iindex,
                   icolumn=icolumn,
                   iamount=iamount,
                   ibase=ibase,
                   imode=imode,
                   iprf_mode=iprf_mode,
                   itid=itid,
                   ram_ren=ram_ren,
                   ram_index=ram_index,
                   ram_offset=ram_offset,
                   ostart=ostart,
                   odrop=odrop,
                   omode=omode,
                   obase=obase,
                   otid=otid,
                   cnt=cnt,
                   istall=istall,
                   oack=oack,
                   st=st,
                   nxt=nxt,
                   rcen=rcen,
                   rren=rren,
                   raddr=raddr
                   )

    pot.convert(hdl='Verilog')


convert()


