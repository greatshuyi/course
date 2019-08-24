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
def pot_fsm(clk, rst_n,
            # upstream input
            enable, base, index, start, amount,
            # output sram
            addr,
            # stage out
            chk_tlb, base_va, trans_cnt,
            # downstream feedback
            stop,
            # monitor
            st, nxt,
            # Must have
            STATE
            ):

    # Sigs and Registers
    BASE_WIDTH = len(base)
    INDEX_WIDTH = len(index)

    # POT_STATE = enum('IDLE', 'RD', 'PEND')
    # st = Signal(POT_STATE.IDLE)
    # nxt = Signal(POT_STATE.IDLE)
    POT_STATE = STATE

    trans_cnt = UInt(len(amount))
    nxt_trans_cnt = UInt(len(amount))

    nxt_idx = UInt(len(addr))
    idx = UInt(len(addr))

    # STATE FSM
    @always_ff(clk.posedge, reset=rst_n)
    def state():
        if enable:
            st.next = nxt

    @always_comb
    def state_transition():
        if st == POT_STATE.IDLE:
            if start:
                nxt.next = POT_STATE.RD
            else:
                nxt.next = POT_STATE.IDLE

        elif st == POT_STATE.RD:
            if start:
                nxt.next = POT_STATE.RD
            elif stop:
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
            if start:
                nxt.next = POT_STATE.IDLE
            elif stop:
                nxt.next = POT_STATE.PEND
            else:
                nxt.next = POT_STATE.PEND
        else:
            nxt.next = POT_STATE.IDLE

    # pipe register control
    @always_ff(clk.posedge, reset=rst_n)
    def pipe_control():
        if enable:
            if start:
                chk_tlb.next = True
                base_va.next = base
                nxt_idx.next = idx

    @always_ff(clk.posedge, reset=rst_n)
    def cnt_control():
        if enable:
            trans_cnt.next = nxt_trans_cnt

    @always_comb
    def cnt_ctrl():
        if start:
            nxt_trans_cnt.next = amount
        else:
            nxt_trans_cnt.next = trans_cnt - 1 if trans_cnt != 0 else 0

    @always_comb
    def mop_ctrl():
        nxt_idx.next = index if start else idx + 1

    assign(addr, nxt_idx)

    return instances()


@block
def top_pot():

    clk = Clock(0)
    rst_n = AsyncReset(1)

    INDEX_WIDTH = 5

    #wires
    enable = UBool(1)
    base = UInt(5, 10)
    index = UInt(INDEX_WIDTH, 0)
    start = UBool(0)
    amount = UInt(4, 6)
    stop = UBool(0)

    chk_tlb = UBool(0)
    offset = UInt(len(index)+1)
    base_va = UInt(len(base))
    trans_cnt = UInt(len(amount))
    addr = UInt(len(index))

    POT_STATE = enum('IDLE', 'RD', 'PEND')
    mst = UEnum(POT_STATE)
    mnxt = UEnum(POT_STATE)

    # Instance
    OFFSET_TABLE = [i+1 for i in range(2**len(index))]
    ram = ssrom(clk=clk, addr=addr,
                dout=offset, CONTENT=OFFSET_TABLE)

    pot = pot_fsm(clk=clk, rst_n=rst_n,
                  # upstream input
                  enable=enable, base=base, index=index, start=start, amount=amount,
                  # output sram
                  addr=addr,
                  # stage out
                  chk_tlb=chk_tlb, base_va=base_va, trans_cnt=trans_cnt,
                  # downstream feedback
                  stop=stop,
                  # for monitor
                  st=mst, nxt=mnxt,
                  STATE=POT_STATE
                  )

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
        for i in range(3):
            yield clk.negedge
        yield clk.posedge
        for n in (16, 8, 8, 4):
            start.next = 1
            base.next = 2
            index.next = 1
            amount.next = 4
            yield clk.posedge
            start.next = 0
            for i in range(n-1):
                yield clk.posedge
        raise StopSimulation()

    return instances()


if __name__ == "__main__":
    tb = top_pot()
    tb.config_sim(trace=True)
    tb.run_sim()



