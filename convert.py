def _writeModuleHeader(f, intf, doc):
    reg_buffer = StringIO()
    wire_buffer = StringIO()
    input_buffer = StringIO()
    output_buffer = StringIO()
    inout_buffer = StringIO()

    print("module %s (" % intf.name, file=f)
    b = StringIO()
    for portname in intf.argnames:
        print("    %s," % portname, file=b)
    print(b.getvalue()[:-2], file=f)
    b.close()
    print(");", file=f)
    print(doc, file=f)
    print(file=f)
    for portname in intf.argnames:
        s = intf.argdict[portname]
        if s._name is None:
            raise ToVerilogError(_error.ShadowingSignal, portname)
        if s._inList:
            raise ToVerilogError(_error.PortInList, portname)
        # make sure signal name is equal to its port name
        s._name = portname
        r = _getRangeString(s)
        p = _getSignString(s)
        if s._driven:
            if s._read:
                if not isinstance(s, _TristateSignal):
                    warnings.warn("%s: %s" % (_error.OutputPortRead, portname),
                                  category=ToVerilogWarning
                                  )
            if isinstance(s, _TristateSignal):
                # print("inout %s%s%s;" % (p, r, portname), file=f)
                print("inout %s%s%s;" % (p, r, portname), file=inout_buffer)
            else:
                # print("output %s%s%s;" % (p, r, portname), file=f)
                print("output %s%s%s;" % (p, r, portname), file=output_buffer)
            if s._driven == 'reg':
                #print("reg %s%s%s;" % (p, r, portname), file=f)
                print("reg %s%s%s;" % (p, r, portname), file=wire_buffer)
            else:
                #print("wire %s%s%s;" % (p, r, portname), file=f)
                print("wire %s%s%s;" % (p, r, portname), file=reg_buffer)
        else:
            if not s._read:
                warnings.warn("%s: %s" % (_error.UnusedPort, portname),
                              category=ToVerilogWarning
                              )
            # print("input %s%s%s;" % (p, r, portname), file=f)
            print("input %s%s%s;" % (p, r, portname), file=input_buffer)

    print("// Ports declaration", file=f)
    print(input_buffer.getvalue(), file=f)
    print(output_buffer.getvalue(), file=f)
    print(reg_buffer.getvalue(), file=f)
    print(wire_buffer.getvalue(), file=f)
    print(file=f)
    input_buffer.close()
    output_buffer.close()
    inout_buffer.close()
    reg_buffer.close()
    wire_buffer.close()
    
def _writeSigDecls(f, intf, siglist, memlist):
    constwires = []
    wire_buffer = StringIO()
    reg_buffer = StringIO()

    print("// Signal Declaration", file=f)
    for s in siglist:
        if not s._used:
            continue
        if s._name in intf.argnames:
            continue
        r = _getRangeString(s)
        p = _getSignString(s)
        if s._driven:
            if not s._read and not isinstance(s, _TristateDriver):
                warnings.warn("%s: %s" % (_error.UnreadSignal, s._name),
                              category=ToVerilogWarning
                              )
            k = 'wire'
            if s._driven == 'reg':
                k = 'reg'
            # the following line implements initial value assignments
            # don't initial value "wire", inital assignment to a wire
            # equates to a continuous assignment [reference]
            if not toVerilog.initial_values or k == 'wire':
                #print("%s %s%s%s;" % (k, p, r, s._name), file=f)
                if k == 'wire':
                    print("%s %s%s%s;" % (k, p, r, s._name), file=wire_buffer)
                else:
                    print("%s %s%s%s;" % (k, p, r, s._name), file=reg_buffer)
            else:
                if isinstance(s._init, myhdl._enum.EnumItemType):
                    # print("%s %s%s%s = %s;" %
                    #       (k, p, r, s._name, s._init._toVerilog()), file=f)
                    if k == 'wire':
                        print("%s %s%s%s = %s;" %
                              (k, p, r, s._name, s._init._toVerilog()), file=wire_buffer)
                    else:
                        print("%s %s%s%s = %s;" %
                              (k, p, r, s._name, s._init._toVerilog()), file=reg_buffer)
                else:
                    # print("%s %s%s%s = %s;" %
                    #       (k, p, r, s._name, _intRepr(s._init)), file=f)
                    if k == 'wire':
                        print("%s %s%s%s = %s;" %
                              (k, p, r, s._name, _intRepr(s._init)), file=wire_buffer)
                    else:
                        print("%s %s%s%s = %s;" %
                              (k, p, r, s._name, _intRepr(s._init)), file=reg_buffer)
        elif s._read:
            # the original exception
            # raise ToVerilogError(_error.UndrivenSignal, s._name)
            # changed to a warning and a continuous assignment to a wire
            warnings.warn("%s: %s" % (_error.UndrivenSignal, s._name),
                          category=ToVerilogWarning
                          )
            constwires.append(s)
            # print("wire %s%s;" % (r, s._name), file=f)
            print("wire %s%s;" % (r, s._name), file=wire_buffer)

    # added by shuyi
    print(wire_buffer.getvalue(), file=f)
    print(reg_buffer.getvalue(), file=f)
    print(file=f)
    wire_buffer.close()
    reg_buffer.close()

    for m in memlist:
        if not m._used:
            continue
        # infer attributes for the case of named signals in a list
        for i, s in enumerate(m.mem):
            if not m._driven and s._driven:
                m._driven = s._driven
            if not m._read and s._read:
                m._read = s._read
        if not m._driven and not m._read:
            continue
        r = _getRangeString(m.elObj)
        p = _getSignString(m.elObj)
        k = 'wire'
        initial_assignments = None
        if m._driven:
            k = m._driven

            if toVerilog.initial_values and not k == 'wire':
                if all([each._init == m.mem[0]._init for each in m.mem]):

                    initialize_block_name = ('INITIALIZE_' + m.name).upper()
                    _initial_assignments = (
                        '''
                        initial begin: %s
                            integer i;
                            for(i=0; i<%d; i=i+1) begin
                                %s[i] = %s;
                            end
                        end
                        ''' % (initialize_block_name, len(m.mem), m.name,
                               _intRepr(m.mem[0]._init)))

                    initial_assignments = (
                        textwrap.dedent(_initial_assignments))

                else:
                    val_assignments = '\n'.join(
                        ['    %s[%d] <= %s;' %
                         (m.name, n, _intRepr(each._init))
                         for n, each in enumerate(m.mem)])
                    initial_assignments = (
                        'initial begin\n' + val_assignments + '\nend')

        print("%s %s%s%s [0:%s-1];" % (k, p, r, m.name, m.depth),
              file=f)

        if initial_assignments is not None:
            print(initial_assignments, file=f)

    print(file=f)
    print("/***************************************************", file=f)
    print(" * Found no driven Signals listed below", file=f)
    for s in constwires:
        if s._type in (bool, intbv):
            c = int(s.val)
        else:
            raise ToVerilogError("Unexpected type for constant signal", s._name)
        c_len = s._nrbits
        c_str = "%s" % c
        print("assign %s = %s'd%s;" % (s._name, c_len, c_str), file=f)
    print("***************************************************/", file=f)
    # print(file=f)
    # shadow signal assignments
    for s in siglist:
        if hasattr(s, 'toVerilog') and s._driven:
            print(s.toVerilog(), file=f)
    print(file=f)
