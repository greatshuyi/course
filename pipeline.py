# -*- coding: utf-8 -*-

from myhdl import (
    block, always_comb, always, instances, instance,
    enum
)
from myhdl import delay, StopSimulation, Simulation

from pipeline.hdl import *


@block
def ssrom(clk, addr, dout, CONTENT):
    """ CONTENT == tuple of non-sparse values
    """

    @always(clk.posedge)
    def read():
        dout.next = CONTENT[int(addr)]

    return read


@block
def DelayLine(clk, rst_n, din, dout, WIDTH=1, TAPS=1):

    """
    Parameterized Synchronous Dealy Line
    :param clk:
    :param rst_n:
    :param din:
    :param dout:
    :param WIDTH:
    :param TAPS:
    :return:
    """

    taps = [UInt(WIDTH) for _ in range(TAPS)]

    @always_ff(clk.posedge, reset=rst_n)
    def delay_line():
        for i in range(TAPS):
            if i == 0:
                taps[i].next = din
            else:
                taps[i].next = taps[i-1]

    @always_comb
    def output():
        dout.next = taps[TAPS-1]

    return instances()


@block
def down_stream(clk, rst_n, enable,
                # upstream
                ivld, chk_tlb, din,
                # feedback
                stop,
                # stage out
                dout
                ):

    @always_ff(clk.posedge, reset=rst_n)
    def recv():
        if enable and ivld:
            dout.next = din
            if chk_tlb:
                stop.next = True if not stop else False
            else:
                if stop:
                    stop.next = False
                else:
                    stop.next = True if din % 2 != 0 and din > 3 else False

    return instances()


POT_STATE = enum('IDLE', 'RD', 'PEND')


@block
def upstream(clk, rst_n, enable,
             # upstream input
             start, index, amount, base,
             # output sram
             addr, ren,
             # stage out
             chk_tlb, base_va, trans_cnt, ovld,
             # downstream feedback
             stop,
             # monitor
             st, nxt,
             # Must have
             STATE
             ):

    # Sigs and Registers
    trans_cnt = UInt(len(amount))
    nxt_trans_cnt = UInt(len(amount))

    nxt_idx = UInt(len(addr))
    idx = UInt(len(addr))

    pot_start = UBool(0)

    # FSM start condition
    @always_comb
    def fsm_start():
        pot_start.next = start and amount != 0

        # STATE FSM
    @always_ff(clk.posedge, reset=rst_n)
    def state():
        if enable:
            st.next = nxt

    @always_comb
    def state_transition():
        nxt.next = POT_STATE.IDLE
        if st == POT_STATE.IDLE:
            if pot_start:
                nxt.next = POT_STATE.RD
            else:
                nxt.next = POT_STATE.IDLE

        elif st == POT_STATE.RD:
            if pot_start:
                nxt.next = POT_STATE.RD
            else:
                if stop:
                    if nxt_trans_cnt == 0:
                        nxt.next = POT_STATE.IDLE
                    else:
                        nxt.next = POT_STATE.PEND
                else:
                    if nxt_trans_cnt == 0:
                        nxt.next = POT_STATE.IDLE
                    else:
                        nxt.next = POT_STATE.RD

        elif st == POT_STATE.PEND:
            if pot_start:
                nxt.next = POT_STATE.RD
            elif stop:
                nxt.next = POT_STATE.PEND
            else:
                nxt.next = POT_STATE.RD
        else:
            nxt.next = POT_STATE.IDLE

    # pipe register control
    @always_ff(clk.posedge, reset=rst_n)
    def pipe_control():
        if enable:
            idx.next = nxt_idx
            chk_tlb.next = True if pot_start else False
            if pot_start:
                base_va.next = base
            # ovld.next = True if start or st != POT_STATE.IDLE else False
            ovld.next = True if nxt != POT_STATE.IDLE else False

    @always_ff(clk.posedge, reset=rst_n)
    def cnt_control():
        if enable:
            trans_cnt.next = nxt_trans_cnt

    @always_comb
    def cnt_ctrl():
        if pot_start:
            nxt_trans_cnt.next = amount
        else:
            if not stop:
                nxt_trans_cnt.next = trans_cnt - 1 if trans_cnt != 0 else 0
            else:
                nxt_trans_cnt.next = trans_cnt

    @always_comb
    def mop_ctrl():
        if pot_start:
            nxt_idx.next = index
        else:
            if not stop:
                nxt_idx.next = idx + 1
            else:
                nxt_idx.next = idx

        ren.next = True if nxt != POT_STATE.IDLE else False
        # if pot_start:
        #     ren.next = True
        # else:
        #     if st == POT_STATE.RD:
        #         ren.next = True
        #     else:
        #         ren.next = False

    @always_comb
    def addr_gen():
        addr.next = 0
        addr.next = nxt_idx

    return instances()


if __name__ == "__main__":

    @block
    def stall_top():

        clk = Clock(0)
        rst_n = AsyncReset(0)

        INDEX_WIDTH = 5

        # wires
        enable = UBool(1)
        base = UInt(5, 10)
        index = UInt(INDEX_WIDTH, 0)
        start = UBool(0)
        amount = UInt(4, 6)

        chk_tlb = UBool(0)
        offset = UInt(len(index)+1)
        base_va = UInt(len(base))

        trans_cnt = UInt(len(amount))
        addr = UInt(len(index))
        ren = UBool(0)

        vld = UBool(0)
        stop = UBool(0)
        offseto = UInt(len(offset))

        mst = UEnum(POT_STATE)
        mnxt = UEnum(POT_STATE)

        # Instance
        OFFSET_TABLE = [i+1 for i in range(2**len(index))]
        ram = ssrom(clk=clk, ren=ren, addr=addr,
                    dout=offset, CONTENT=OFFSET_TABLE)

        up = upstream(clk=clk, rst_n=rst_n,
                      # upstream input
                      enable=enable, base=base, index=index, start=start, amount=amount,
                      # output sram
                      addr=addr, ren=ren,
                      # stage out
                      chk_tlb=chk_tlb, base_va=base_va, trans_cnt=trans_cnt, ovld=vld,
                      # downstream feedback
                      stop=stop,
                      # for monitor
                      st=mst, nxt=mnxt,
                      STATE=POT_STATE
                      )

        downstream = down_stream(clk=clk, rst_n=rst_n, enable=enable,
                                 # upstream
                                 ivld=vld,
                                 chk_tlb=chk_tlb,
                                 din=offset,
                                 # feedback
                                 stop=stop,
                                 # stage out
                                 dout=offseto,
                                 )

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


    tb = stall_top()
    tb.config_sim(trace=True)
    tb.run_sim()



