# -*- coding: utf-8 -*-

from myhdl import (
    block, always_comb, always, instances, instance,
    enum
)
from myhdl import ConcatSignal as concat
from pipeline.hdl import *
from myhdl import delay, StopSimulation


from pipeline.lib.mem import ssrom


from pipeline.sim.reciever import reciever as downstream





@block
def ram_decoder(cen, ren, index, offset,
                bank_cen, bank_ren, bank_addr, bank_select
                ):

    addr = concat(index, offset)

    @always_comb
    def decoder():
        bank_cen.next = cen
        bank_ren.next = ren
        bank_addr.next = addr
        bank_select.next = 1


ram_decoder.verilog_code = \
"""
ram_decoder ram_decoder (
    .cen(cen),
    .ren(ren),
    .index(bank_idx),
    .offset(bank_oft),
    .bank_cen(bank_cen),
    .bank_ren(bank_ren),
    .bank_index(bank_index),
    .bank_select(bank_select)
    );
"""

POT_STATE = enum('IDLE', 'RD', 'PEND')


@block
def pot_fsm(clk, rst_n, enable,
            # upstream input
            flush, start, index, offset, amount, base, mode,
            # combinatorial SRAM input/output control
            bank_cen, bank_ren, bank_addr, bank_mask, bank_select,
            # pipe cmd
            ovld, ostart, odrop, ourgent, omode,
            # pipe registers data
            obase,
            # pipe ctrl
            cnt,
            # reciever feedback
            stall,
            # monitor
            st, nxt,
            # for simulation only
            rcen, rren, raddr
            ):

    # =============================================
    # Constant & Parameter
    # =============================================
    MAX_OFFSET = 14
    MAX_INDEX = 64
    MAX_TIMER = 4

    # =============================================
    # Sigs and pipe registers
    # =============================================

    ovld = UBool(0)                         # pipe command, ovld act as valid
    ostart = UBool(0)                       # pipe command, reciever restart
    odrop = UBool(0)                        # pipe command, reciever drop current
    ourgent = UBool(0)                      # pipe QoS for reciever

    ocomplete = UBool(0)                    # to main control and upstream

    omode = UInt(2, 0)

    cnt = UInt(len(amount))                 # pipe register of amount counter
    idx = UInt(len(index))                  # pipe register of index
    oft = UInt(len(offset))                 # pipe register of offset

    nxt_cnt = UInt(len(amount))
    nxt_idx = UInt(len(index))
    nxt_oft = UInt(len(offset))
    nxt_idx = UInt(len(index))
    nxt_cnt = UInt(len(amount))

    timer = UInt(11, 1024)                  # pending time out timer

    pot_start = UBool(0)
    pot_complete = UBool(0)                 # complete all transfer or reach POT last column
    pot_timeout = UBool(0)
    pot_enable = UBool(0)

    # internal RAM control
    cen = UBool(0)
    ren = UBool(0)
    bank_idx = UInt(len(idx))
    bank_oft = UInt(len(oft))

    # =============================================
    # pipeline control
    # =============================================

    # FSM start condition
    @always_comb
    def fsm_start():
        pot_start.next = start and amount != 0
        pot_complete.next = nxt_cnt == 0 or (idx == MAX_INDEX) and (oft == MAX_OFFSET)
        pot_enable.next = enable and not stall
        pot_timeout.next = True if timer == MAX_TIMER else False

    # pipe FSM
    @always_ff(clk.posedge, reset=rst_n)
    def fsm_state():
        if enable:
            st.next = nxt

    @always_comb
    def fsm_transition():

        if st == POT_STATE.IDLE:
            if flush:
                nxt.next = POT_STATE.IDLE
            elif pot_start:
                nxt.next = POT_STATE.RD
            else:
                nxt.next = POT_STATE.IDLE

        elif st == POT_STATE.RD:
            if flush:
                nxt.next = POT_STATE.IDLE
            elif pot_start:
                nxt.next = POT_STATE.RD
            else:
                if stall:
                    nxt.next = POT_STATE.PEND
                else:
                    if pot_complete:
                        nxt.next = POT_STATE.IDLE
                    else:
                        nxt.next = POT_STATE.RD

        elif st == POT_STATE.PEND:
            if flush:
                nxt.next = POT_STATE.IDLE
            elif pot_start:
                nxt.next = POT_STATE.RD
            else:
                if not stall:
                    nxt.next = POT_STATE.PEND
                else:
                    if pot_timeout:
                        nxt.next = POT_STATE.RD
                    else:
                        nxt.next = POT_STATE.PEND
        else:
            nxt.next = POT_STATE.IDLE

    # =============================================
    # pipeline payload/register control
    # =============================================

    @always_ff(clk.posedge, reset=rst_n)
    def pipe_registers():
        if pot_enable:
            idx.next = nxt_idx
            oft.next = nxt_oft
            cnt.next = nxt_cnt

    @always_comb
    def pipe_control():
        if flush:
            nxt_cnt.next = 0
        elif pot_start:
            nxt_cnt.next = amount
        else:
            if not stall:
                nxt_cnt.next = cnt - 1 if cnt != 0 else 0
            else:
                nxt_cnt.next = cnt

        if flush:
            nxt_oft.next = 0
        elif pot_start:
            nxt_oft.next = offset
        else:
            if not stall:
                nxt_oft.next = 0 if oft == MAX_OFFSET else oft + 1
            else:
                nxt_oft.next = idx

        if flush:
            nxt_idx.next = 0
        elif pot_start:
            nxt_idx.next = index
        else:
            if not stall:
                if idx == MAX_INDEX:
                    nxt_idx.next = MAX_INDEX
                else:
                    nxt_idx.next = idx + 1 if oft == MAX_OFFSET else idx
            else:
                nxt_idx.next = idx
                       
    @always_ff(clk.posedge, reset=rst_n)
    def base_control():
        if flush:
            obase.next = 0
        else:
            if pot_start:
                obase.next = base
            else:
                obase.next = obase

    @always_ff(clk.posedge, reset=rst_n)
    def mode_control():
        if flush:
            omode.next = 0
        else:
            if pot_start:
                omode.next = mode
            else:
                omode.next = omode

    # =============================================
    # pipeline command controls
    # =============================================

    # handshake valid
    @always_ff(clk.posedge, reset=rst_n)
    def valid():
        if flush:
            ovld.next = False
        else:
            if st == POT_STATE.IDLE and pot_start or st != POT_STATE.IDLE:
                ovld.next = True
            else:
                ovld.next = False

    @always_ff(clk.posedge, reset=rst_n)
    def start_control():
        if flush:
            ostart.next = False
        elif pot_start:
            ostart.next = True
        else:
            if stall:
                ostart.next = ostart
            else:
                ostart.next = False if ostart else ostart

    @always_ff(clk.posedge, reset=rst_n)
    def drop_control():
        if flush:
            odrop.next = False
        elif start:
            ostart.next = False
        else:
            if stall:
                odrop.next = odrop
            else:
                odrop.next = True if st == POT_STATE.PEND and pot_timeout else False

    @always_ff(clk.posedge, reset=rst_n)
    def urgent_control():
        if flush:
            ourgent.next = False
        elif pot_start:
            ourgent.next = False
        else:
            if st == POT_STATE.IDLE and pot_start:
                ourgent.next = True
            else:
                ourgent.next = ourgent

    @always_ff(clk.posedge, reset=rst_n)
    def complete_control():
        if flush:
            ocomplete.next = False
        elif pot_start:
            ocomplete.next = False
        else:
            if st == POT_STATE.RD and pot_complete:
                ocomplete.next = True
            else:
                ocomplete.next = False

    # =============================================
    # SRAM controls
    # =============================================

    decoder = ram_decoder(cen=cen, ren=ren, index=bank_idx, offset=bank_oft,
                          bank_cen=bank_cen, bank_ren=bank_ren,
                          bank_addr=bank_addr, bank_mask=bank_mask,
                          bank_sel=bank_select)

    @always_comb
    def ram_control():
        if flush:
            cen.next = False
            ren.next = False
        else:
            if pot_start and st == POT_STATE.IDLE or st != POT_STATE.IDLE:
                cen.next = True
                ren.next = True
            else:
                cen.next = False
                ren.next = False

        bank_idx.next = nxt_idx
        bank_oft.next = nxt_oft

    # =============================================
    # pipeline monitor
    # =============================================
    @always_ff(clk.posedge, reset=rst_n)
    def pipe_counter():
        if flush:
            timer.next = 0
        elif pot_start:
            timer.next = 0
        else:
            if st == POT_STATE.RD and stall:
                timer.next = timer + 1
            elif st == POT_STATE.PEND:
                if not stall:
                    timer.next = 0
                else:
                    if pot_timeout:
                        timer.next = 0
                    else:
                        timer.next = timer + 1
            else:
                timer.next = timer

    if __debug__:
        @always_comb
        def ram_sim():
            rcen.next = cen
            rren.next = ren
            raddr.next = concat(bank_idx, bank_oft)


    return instances()


if __name__ == "__main__":

    @block
    def pot_top():

        clk = Clock(0)
        rst_n = AsyncReset(0)

        INDEX_WIDTH = 6
        BANK_NUM = 4
        BANK_WIDTH = 72
        BANK_DEPTH = 2**INDEX_WIDTH
        BANK_MASK = int(BANK_WIDTH/8)
        BANK_MUX = 6

        # wires
        flush = UBool(0)
        start = UBool(0)
        enable = UBool(1)

        base = UInt(5, 10)
        index = UInt(INDEX_WIDTH, 0)
        pipe_offset = UInt(4, 0)
        amount = UInt(4, 6)
        mode = UInt(2, 3)

        bank_cen = UInt(BANK_NUM, 0)
        bank_ren = UInt(BANK_NUM, 0)
        bank_addr = UInt(INDEX_WIDTH, 0)
        bank_mask = UInt(BANK_MASK, 0)
        bank_select = UInt(BANK_MUX, 0)

        pipe_vld = UBool(0)
        pipe_ostart= UBool(0)
        pipe_drop= UBool(0)
        pipe_urgent= UBool(0)
        pipe_mode= UBool(0)
        pipe_base= UBool(0)
        pot_cnt= UInt(INDEX_WIDTH)
        pipe_stall= UBool(0)

        rren = UBool(0)
        raddr = UInt(INDEX_WIDTH)

        mst = UEnum(POT_STATE)
        mnxt = UEnum(POT_STATE)

        # Instance
        OFFSET_TABLE = [i + 1 for i in range(2 ** len(index))]

        ram = ssrom(clk=clk, ren=rren, addr=raddr,
                    dout=pipe_offset, CONTENT=OFFSET_TABLE)

        pot = pot_fsm(clk=clk, rst_n=rst_n, enable=enable,
                      # upstream input
                      flush=flush, start=start, index=index,
                      offset=pipe_offset, amount=amount, base=base, mode=mode,
                      # combinatorial SRAM input/output control
                      bank_cen=bank_cen, bank_ren=bank_ren, bank_addr=bank_addr,
                      bank_mask=bank_mask, bank_select=bank_select,
                      # pipe cmd
                      ovld=pipe_vld, ostart=pipe_ostart,
                      odrop=pipe_drop, ourgent=pipe_urgent, omode=pipe_mode,
                      # pipe registers data
                      obase=pipe_base,
                      # pipe ctrl
                      cnt=pot_cnt,
                      # reciever feedback
                      stall=pipe_stall,
                      # monitor
                      st=mst, nxt=mnxt
                      )

        din = concat(pipe_ostart, pipe_drop, pipe_urgent, pipe_mode,
                     pipe_base, pipe_offset)
        dout = UBool(len(din))

        irdy = UBool(1)
        ovld = UBool(0)

        recv = downstream(clk=clk, rst_n=rst_n, enable=enable,
                          # master side
                          ivld=pipe_vld, ordy=pipe_stall,
                          # slave side
                          ovld=ovld, irdy=irdy,
                          # data in/out
                          din=din, dout=dout,
                          # REG_TYPE
                          REG=None)

        cycle_list = [30 for _ in range(4)]

        @always(delay(10))
        def clkgen():
            clk.next = not clk

        @instance
        def rstgen():
            for i in range(3):
                yield clk.negedge
            rst_n.next = True

        @instance
        def stimulus():
            for i in range(6):
                yield clk.negedge
            yield clk.posedge
            for n in cycle_list:
                start.next = 1
                base.next = 2
                index.next = 1
                amount.next = 8
                yield clk.posedge
                start.next = 0
                if n != 1:
                    for i in range(n):
                        yield clk.posedge
            raise StopSimulation()

        return instances()


    tb = pot_top()
    tb.config_sim(trace=True)
    tb.run_sim()


