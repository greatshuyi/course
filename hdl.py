# -*- coding: utf-8 -*-
"""
Shim layer atop myHDL
"""

from myhdl import *

# from myhdl import Signal, modbv, intbv, ResetSignal, always_seq


def UBool(val=0):
    assert val >= 0
    return Signal(bool(val))


def UInt(width, val=0, min=None, max=None, _nrbits=0):
    assert val >= 0 and width > 0
    return Signal(modbv(val=val, min=min, max=max)[width:])


def SInt(width, val=0, min=None, max=None, _nrbits=0):
    assert val >= 0 and width > 0
    return Signal(intbv(val=val, min=min, max=max)[width:])


def SyncReset(val, active=0):
    """
    Construct a synchronous reset signal, defaults to low active
    :param val: initial value
    :param active: active level, high/low
    :return: myHDL's ResetSignal
    """
    return ResetSignal(val=val, active=active, isasync=False)


def AsyncReset(val, active=0):
    """
    Construct a asynchronous reset signal, defaults to low active
    :param val: initial value
    :param active: active level, high/low
    :return: myHDL's ResetSignal
    """
    return ResetSignal(val=val, active=active, isasync=True)


DummyEnumType = enum("dummy", "foobar")

Enum = enum()


def Enum(enum):
    """
    Construct a Signal according to enumeration type
    :param enum:
    :return:
    """
    assert isinstance(enum, type(DummyEnumType))

    for p in dir(enum):
        print(type(p))

    return Signal(enum)

# Semantic constructs

always_ff = always_seq
