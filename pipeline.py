# -*- coding: utf-8 -*-

from myhdl import (
    block, always_comb, always, instances, instance,
    enum
)
from myhdl import delay, StopSimulation, Simulation

from pipeline.hdl import *
from pipeline.lib.mem import ssrom

try:
    from pipeline.sim import recv as downstream
except:

    @block
    def downstream():

        def recv():
            pass

        return instances()


POT_STATE = enum('IDLE', 'RD', 'PEND')


@block
def ram_decoder(index, offset):
    pass



@block
def pot_fsm(clk, rst_n, enable,
            # upstream input, start is just a valid
            flush, start, index, offset, amount, base,
            # combinatorial SRAM input control
            cen, ren, addr,
            # pipe SRAM output mux control
            select,
            # pipe cmd
            ovld, ostart, odrop, oflush, ourgent,
            # pipe registers data
            base_va,
            # pipe ctrl
            cnt,
            # downstream feedback
            stop,
            # monitor
            st, nxt,
            # Must have
            STATE
            ):
    # =============================================
    # 
    # =============================================
    OFFSET_INDEX_MAX = 14
    OFFSET_ENTRY_MAX = 64

    # =============================================
    # Sigs and pipe registers
    # =============================================
    pot_start = UBool(0)

    ovld = UBool(0)                         # pipe command, ovld act as valid
    ostart = UBool(0)                       # pipe command, downstream restart
    odrop = UBool(0)                        # pipe command, downstream drop current
    oflush = UBool(0)                       # pipe command, downstream flush
    ourgent = UBool(0)                      # pipe QoS for downstream

    cnt = UInt(len(amount))                 # pipe register of amount counter
    idx = UInt(len(addr))                   # pipe register of index
    oft = UInt(len(offset))                 # pipe register of offset

    nxt_cnt = UInt(len(amount))
    nxt_idx = UInt(len(addr))
    nxt_oft = UInt(len(offset))
    nxt_idx = UInt(len(addr))
    nxt_cnt = UInt(len(amount))

    pipe_timer = UInt(11, 1024)

    # =============================================
    # pipeline control
    # =============================================

    # FSM start condition
    @always_comb
    def fsm_start():
        pot_start.next = start and amount != 0

    # pipe FSM
    @always_ff(clk.posedge, reset=rst_n)
    def state():
        if enable:
            st.next = nxt

    @always_comb
    def state_transition():
        nxt.next = POT_STATE.IDLE
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
                if stop:
                    if nxt_cnt == 0:
                        nxt.next = POT_STATE.IDLE
                    else:
                        nxt.next = POT_STATE.PEND
                else:
                    if nxt_cnt == 0:
                        nxt.next = POT_STATE.IDLE
                    else:
                        nxt.next = POT_STATE.RD

        elif st == POT_STATE.PEND:
            if flush:
                nxt.next = POT_STATE.IDLE
            elif pot_start:
                nxt.next = POT_STATE.RD
            elif stop:
                nxt.next = POT_STATE.PEND
            else:
                nxt.next = POT_STATE.RD
        else:
            nxt.next = POT_STATE.IDLE

    # =============================================
    # pipeline payload/register control
    # =============================================

    @always(clk.posedge, reset=rst_n)
    def pipe_registers():
        if enable:
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
            if not stop:
                nxt_cnt.next = cnt - 1 if cnt != 0 else 0
            else:
                nxt_cnt.next = cnt

        if flush:
            nxt_oft.next = 0
        elif pot_start:
            nxt_oft.next = offset
        else:
            if not stop:
                nxt_oft.next = 0 if oft == OFFSET_INDEX_MAX else oft + 1
            else:
                nxt_oft.next = idx

        if flush:
            nxt_idx.next = 0
        elif pot_start:
            nxt_idx.next = index
        else:
            if not stop:
                nxt_idx.next = OFFSET_ENTRY_MAX if idx == OFFSET_ENTRY_MAX else idx + 1
            else:
                nxt_idx.next = idx
                       
    @always(clk.posedge, reset=rst_n)
    def va_register():
        if flush:
            base_va.next = 0
        else:
            if pot_start:
                base_va.next = base
            else:
                base_va.next = base_va

    # =============================================
    # pipeline command controls
    # =============================================
    @always(clk.posedge, reset=rst_n)
    def pipe_cmd_control():
        pass

    # =============================================
    # SRAM controls
    # =============================================
    @always_comb
    def ram_control():
        pass

    # =============================================
    # pipeline monitor
    # =============================================
    



if __name__ == "__main__":

    @block
    def pot_top():

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
        OFFSET_TABLE1 = [i+1 for i in range(2**len(index))]
        ram1 = ssrom(clk=clk, ren=ren, addr=addr,
                     dout=offset, CONTENT=OFFSET_TABLE)
        ram2 = ssrom(clk=clk, ren=ren, addr=addr,
                     dout=offset, CONTENT=OFFSET_TABLE)
        ram3 = ssrom(clk=clk, ren=ren, addr=addr,
                     dout=offset, CONTENT=OFFSET_TABLE)
        ram4 = ssrom(clk=clk, ren=ren, addr=addr,
                     dout=offset, CONTENT=OFFSET_TABLE)

        pot = pot_fsm(clk=clk, rst_n=rst_n,
                      # upstream input
                      enable=enable, base=base, index=index, start=start, amount=amount,
                      # output sram
                      addr=addr, ren=ren,
                      # stage out
                      ostart=chk_tlb, base_va=base_va, cnt=trans_cnt, ovld=vld,
                      # downstream feedback
                      stop=stop,
                      # for monitor
                      st=mst, nxt=mnxt,
                      STATE=POT_STATE
                      )

        recv = downstream(clk=clk, rst_n=rst_n, enable=enable,
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


    tb = pot_top()
    tb.config_sim(trace=True)
    tb.run_sim()


