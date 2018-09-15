# -*- coding: utf-8 -*-
"""
Shim layer atop myHDL
"""

from myhdl import *

# from myhdl import Signal, modbv, intbv, ResetSignal, always_seq


def UBool(val=0):
    """
    Boolean Signal
    :param val: initial value
    :return: Signal of boolean
    """
    assert val >= 0
    return Signal(bool(val))


def UEnum(enum):
    """
    Construct a Signal according to enumeration type
    :param enum: an object of myHDL's EnumType
    :return: Signal of Enum type
    """
    assert isinstance(enum, EnumType)

    # find first property of EnumItemType
    attrs = [getattr(enum, n) for n in dir(enum)]
    items = list(filter(lambda x: isinstance(x, EnumItemType), attrs))
    assert len(items) > 0

    return Signal(items[0])


def UInt(width, val=0, min=None, max=None):
    """
    Unsigned int signal
    :param width: bit-width
    :param val:  initial value
    :param min:  minimum value
    :param max:  maximu value
    :return: Signal of modbv
    """
    assert val >= 0 and width > 0
    return Signal(modbv(val=val, min=min, max=max)[width:])


def SInt(width, val=0, min=None, max=None, _nrbits=0):
    """
    Two's complement representation of signed int
    :param width: bit width
    :param val:  initial value
    :param min:  minimum value, could be less than zero
    :param max:  maximum value, be aware on the relationship with bit width
    :return: Signal of intbv
    """
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





# Semantic constructs
always_ff = always_seq
