# -*- coding: utf-8 -*-
"""
General register slice containing PASS_SLICE, FORWARD_SLICE, REVERSE_SLICE, FULL_SLICE
"""

# from .hdl import enum, intbv, modbv
# from .hdl import Signal, always_comb, always_ff, instances
# from .hdl import block
#
# from .hdl import UBool, UInt, SInt

from hdl import *


@block
def pass_slice(
    # source side
    svalid,
    sready,
    spayload,
    # sink side
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
    # sink side
    dvalid,
    dready,
    dpayload,
    width=16
):

    pen = Signal(bool(0))

    # as forward slice, register incoming valid on source side
    svalid_ff = Signal(bool(0))

    @always_comb
    def _comb():
        sready.next = dready or not svalid_ff
        dvalid.next = svalid_ff
        pen.next = (svalid and not svalid_ff) or (svalid and svalid_ff and dready)

    @always_ff(clk.posedge, reset=rst_n)
    def _seq():
        if svalid or dready:
            svalid_ff.next = svalid

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
        sready_r.next = dready or not loaded

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
    state_t = enum("IDLE", "ONE", "ALL")

    st = Signal(state_t.IDLE)
    nxt = Signal(state_t.IDLE)

    iready = UBool(0)
    bload = UBool(0)
    ovalid = UBool(0)

    pena = UBool(0)
    penb = UBool(0)

    # two set registers used as ping-pong to enable back-to-back transfer
    prega = UInt(width, val=0)
    pregb = UInt(width, val=0)

    # select signal between prega & pregb
    sel = UBool(0)

    # FSM
    @always_comb
    def _transition():
        if st == state_t.IDLE:
            nxt.next = state_t.ONE
        elif st == state_t.ONE:
            nxt.next = state_t.ALL
        elif st == state_t.ALL:
            nxt.next = state_t.IDLE
        else:
            nxt.next = st

    @always_ff(clk.posedge, reset=rst_n)
    def _state():
        st.next = nxt

    @always_ff(clk.posedge, reset=rst_n)
    def _enable():
        # all payload load enable sigs
        pena.next = not bload and svalid and iready
        penb.next = bload and svalid and iready

    @always_ff(clk.posedge, reset=rst_n)
    def _payloada():
        if pena:
            prega.next = spayload
            # print("Loading payload into register A")

    @always_ff(clk.posedge, reset=rst_n)
    def _payloadb():
        if penb:
            pregb.next = spayload
            # print("Loading payload into register B")

    @always_comb
    def _out():
        # print("Selecting from register{}".format("B" if sel else "A"))
        dpayload.next = prega if not sel else pregb
        sready.next = iready
        dvalid.next = ovalid

    return instances()


if __name__ == "__main__":

    width = 16

    clk = UBool(0)
    rst_n = AsyncReset(1, 0)
    svalid = UBool(0)
    sready = UBool(0)
    spayload = UInt(width)
    dvalid = UBool(0)
    dready = UBool(0)
    dpayload = UInt(width)

    fwd_slice = full_slice(clk, rst_n, svalid, sready, spayload,
                              dvalid, dready, dpayload, width)

    fwd_slice.convert(hdl="Verilog")



