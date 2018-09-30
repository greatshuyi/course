# -*- coding: utf-8 -*-
"""
General register slice containing PASS_SLICE, FORWARD_SLICE, REVERSE_SLICE, FULL_SLICE
See https://www.southampton.ac.uk/~bim/notes/cad/reference/ZyboWorkshop/2015_2_zybo_labsolution/lab2/lab2.srcs/sources_1/ipshared/xilinx.com/axi_register_slice_v2_1/03a8e0ba/hdl/verilog/axi_register_slice_v2_1_axic_register_slice.v
as reference.
"""

from synth.hdl import *


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
    """Forward register slice inserting registers on forward path(valid) while maintaining
    one cycle latency and back-to-back transfer capability. combinatorial path from source
    valid to sink valid"""

    #
    ren = Signal(bool(0))

    # as forward slice, register incoming valid on source side
    valid_en = UBool(0)
    svalid_ff = Signal(bool(0))

    @always_comb
    def _dvalid():
        dvalid.next = svalid_ff

    @always_comb
    def _sready():
        """Assert sready only when:
        1. downstream can comsume data (by driving dready high),
        2. we have space in internal buffer
        """
        sready.next = dready or not svalid_ff

    @always_comb
    def _ren():
        """when to latch source payload into internal buffer:
        1. svalid is asserted and internal buffer does not have a valid transfer of previous cycle
        2. svalid is asserted and do has a previous transfer inside and also downstream consume a
        transfer
        """
        ren.next = (svalid and not svalid_ff) or (svalid and svalid_ff and dready)

    @always_comb
    def _valid_en():
        """
        Latch valid(also indicating internal buffer holds a valid transfer) when either :
        1. svalid is asserted: always set valid if source is attempting to transfer
        2. dready is asserted: downstream can receive data
        """
        valid_en.next = svalid or (not svalid and dready)

    @always_ff(clk.posedge, reset=rst_n)
    def _valid_ff():
        """Indicating if we have a valid transfer inside by inserting register on valid path"""
        if valid_en:
            svalid_ff.next = svalid

    @always_ff(clk.posedge, reset=rst_n)
    def _payload():
        """latch payload"""
        if ren:
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
    """
    Reverse register slice inserting registers on reverse path( form downstream ready to upstream
    ready), while maintaining one cycle latency and back-to-back transfer capability. To support this
    function it uses a combinatorial path from svalid to dvalid, and mux output between source side
    data and internal buffer.

    1. latch payload only when svalid asserted and both internal buffer empty and dready asserted
    2. assert dvalid when svalid is set or internal buffer loaded
    3. assert sready only when internal buffer is empty(actually break ready path by inserting
    registers)

    :param clk:
    :param rst_n:
    :param svalid:
    :param sready:
    :param spayload:
    :param dvalid:
    :param dready:
    :param dpayload:
    :param width:
    :return:
    """

    # status flag check if we've already loaded data
    loaded = UBool(0)

    # payload latch enable sig
    ren = UBool(0)
    buffer = UInt(width, 0)

    @always_comb
    def _comb():

        # if svalid and both internal internal buffer is empty and destiny side is not ready
        ren.next = svalid and not (loaded or dready)

        # assert dvalid only when svalid and internal buffer has been loaded with data
        dvalid.next = svalid or loaded

        # assert sready only when internal buffer is empty
        sready.next = not loaded

        # mux between internal buffer and source side
        dpayload = buffer if loaded else spayload

    @always_ff(clk.posedge, reset=rst_n)
    def _loaded():
        """Use a internal sig to indicating if internal buffer has been loaed"""
        if svalid and not loaded and not dready:
            loaded.next = not loaded    # toggle loaded

    @always_ff(clk.posedge, reset=rst_n)
    def _seq():
        if ren:
            buffer.next = spayload

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
    """
    Fully registered slice by inserting register both in forward path(valid) and
    reverse path(ready). To ensure a minimum latency of 1 and back-to-back transfer,
    this implementation uses a two-depth fifo(implemented as ping-pong storage) to
    compress bubble cycle.
    :param clk:
    :param rst_n:
    :param svalid:
    :param sready:
    :param spayload:
    :param dvalid:
    :param dready:
    :param dpayload:
    :param width:
    :return:
    """

    # uses a small fsm to control load sequence
    state_t = enum("IDLE", "ONE", "ALL")
    st = UEnum(state_t)
    nxt = UEnum(state_t)

    # two set registers used as ping-pong to enable back-to-back transfer
    rena = UBool(0)
    renb = UBool(0)
    rega = UInt(width, val=0)
    regb = UInt(width, val=0)

    #
    valid_a = UBool(False)
    valid_b = UBool(False)

    # select between two internal register sets
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
        rena.next = not bload and svalid and iready
        renb.next = bload and svalid and iready

    @always_ff(clk.posedge, reset=rst_n)
    def _payloada():
        """Loads source payload into internal register A"""
        if rena:
            rega.next = spayload
            print("Loading payload into register A")

    @always_ff(clk.posedge, reset=rst_n)
    def _payloadb():
        """Loads source payload into internal register B"""
        if renb:
            regb.next = spayload
            print("Loading payload into register B")

    @always_comb
    def _payload_out():
        print("Selecting from register {}".format("B" if sel else "A"))
        dpayload.next = rega if not sel else regb

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

    slice = forward_slice(clk, rst_n, svalid, sready, spayload,
                              dvalid, dready, dpayload, width)

    slice.convert(hdl="Verilog")


