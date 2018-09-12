# -*- coding: utf-8 -*-
"""
General register slice containing PASS_SLICE, FORWARD_SLICE, REVERSE_SLICE, FULL_SLICE
"""

from myhdl import enum, intbv, modbv
from myhdl import Signal, always_comb, always_ff, instances
from myhdl import block


def UBool(val=0):
    assert val >= 0
    return Signal(bool(val))


def UInt(width, val=0):
    assert val >= 0 and width > 0
    return Signal(modbv(val)[width:])


def SInt(width, val=0):
    assert val >= 0 and width > 0
    return Signal(intbv(val)[width:])


@block
def pass_slice(
    clk,
    rst_n,
    # source side
    svalid,
    sready,
    spayload,
    # output side
    dvalid,
    dready,
    dpayload,
    width=16
):

    @always_comb
    def _seq():
        dvalid.next = svalid
        sready.next = dready
        dpayload.next = spayload

    return instances()


@block
def forward_slice(
    clk,
    rst_n,
    # source side
    svalid,
    sready,
    spayload,
    # output side
    dvalid,
    dready,
    dpayload,
    width=16
):

    pen = Signal(bool(0))
    svalid_r = Signal(bool(0))

    @always_comb
    def _comb():
        sready.next = dready or not svalid_r
        dvalid.next = svalid_r
        pen.next = (svalid and not svalid_r) or (svalid and svalid_r and dready)

    @always_ff(clk.posedge, reset=rst_n)
    def _seq():
        if svalid or dready:
            svalid_r.next = svalid

        if pen:
            dpayload.next = spayload

    return instances()


@block
def reverse_slice(
    clk,
    rst_n,
    # source side
    svalid,
    sready,
    spayload,
    # output side
    dvalid,
    dready,
    dpayload,
    width=16
):

    # registered ready sig on source side
    sready_r = Signal(bool(0))
    # status flag check if we've already loaded data
    loaded = Signal(bool(0))
    # payload latch enable sig
    pen = Signal(bool(0))

    @always_comb
    def _comb():
        # source side
        sready.next = not loaded


    @always_ff(clk.posedge, reset=rst_n)
    def _loaded():
        if (svalid and not loaded) or dready:
            loaded.next = not loaded    # toggle loaded

    @always_ff(clk.posedge, reset=rst_n)
    def _seq():
        # latch payload
        if pen:
            dpayload.next = spayload

        # register ready on source side
        sready_r.next = dready or not

    return instances()


@block
def full_slice(
    clk,
    rst_n,
    # source side
    svalid,
    sready,
    spayload,
    # output side
    dvalid,
    dready,
    dpayload,
    width=16
):

    # uses a small fsm to control load sequence
    st = enum("IDLE", "ONE", "ALL")
    nxt = enum()
    
    iready = Signal(bool(0))
    bload = Signal(bool(0))
    ovalid = UBool(0)
    
    pena = Signal(bool(0))
    penb = Signal(bool(0))

    # two set registers used as ping-pong to enable back-to-back transfer
    prega = Signal(intbv(0)[width:])
    pregb = Signal(intbv(0)[width:])

    # select signal between prega & pregb
    sel = Signal(bool(0))


    # FSM
    @always_comb
    def _transition():
        if st == t_state.IDLE:

        elif st == t_state.ONE:

        elif st == t_state.ALL:

        else:
            nxt.next = st


    @always_ff
    def _state():
        st.next = nxt

    @always_comb
    def _comb():
        pass

    @always_ff(clk.posedge, reset=rst_n)
    def _enable():
        #all payload load enable sigs
        pena.next = not bload and svalid and iready
        penb.next = bload and svalid and iready

    @always_ff(clk.posedge, reset=rst_n)
    def _payloada():
        if pena:
            prega.next = spayload
            print("Loading payload into register A")

    @always_ff(clk.posedge, reset=rst_n)
    def _payloadb():
        if penb:
            pregb.next = spayload
            print("Loading payload into register B")

    @always_comb
    def _out():
        print("Selecting from register{}".format("B" if sel else "A"))
        dpayload.next = prega if not sel else pregb
        sready.next = iready
        dvalid.next = ovalid


    return instances()



if __name__ == "__main__":
    pass
