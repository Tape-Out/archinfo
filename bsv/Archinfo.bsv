package Archinfo;

// 芯片身份与配置：全是只读寄存器，数值在装配时由清单给定，综合出来是常数。
// 厂商号怎么编进寄存器在 Jep106（BH）里。

import RegIf::*;
import ArchinfoRegs::*;
import Jep106::*;

typedef struct {
  Bit#(0) none;
} ArchinfoCfg;

// 参数全在类型里：息壤把清单的 int 参数按声明顺序当类型参数传进来
interface ArchinfoIfc#(numeric type aw, numeric type dw,
                       numeric type bank, numeric type maker, numeric type part,
                       numeric type rev, numeric type harts, numeric type ramBytes);
  interface RegIf#(aw, dw) regs;
endinterface

module mkArchinfo#(ArchinfoCfg cfg)(ArchinfoIfc#(aw, dw, bank, maker, part, rev, harts, ramBytes))
    provisos (Mul#(TDiv#(dw, 8), 8, dw), Add#(_a, 8, aw), Add#(_b, 32, dw));

  ArchinfoRegsIfc#(aw, dw) r <- mkArchinfoRegs;

  Jep106 id = jep106(valueOf(bank), valueOf(maker));

  rule show;
    r.vendor_in(mvendorid(id));
    r.soc_in(socId(id, fromInteger(valueOf(part))));
    r.revision_in(fromInteger(valueOf(rev)));
    r.harts_in(fromInteger(valueOf(harts)));
    r.ram_in(fromInteger(valueOf(ramBytes)));
  endrule

  interface regs = r.regs;
endmodule

endpackage
