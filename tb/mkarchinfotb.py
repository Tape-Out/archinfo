"""archinfo 的行为测试台：读五个只读寄存器，与这一点的参数算出的期望值比。

期望值不照被测件的写法算：从 JEDEC JEP106 的原始字节序列算起（`bank` 个续码 0x7f，接一个带奇校验位的
最后字节），查过每个字节的奇校验，再照 RISC-V 特权规范 3.1.2 拆出续码个数与去掉校验位的低 7 位，
拼出 `vendor`（mvendorid 编码）与 `soc`（Linux soc_id.c 解的 SMCCC SOC_ID 编码）。
这份拆法生成之前先对特权规范的例子自证：12 个续码接 0x8a 编成 0x60a，按 Linux 的格式打出 jep106:0c0a。
"""
import json
import pathlib
import sys

out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
out.mkdir(parents=True, exist_ok=True)
cfg = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
label = cfg.get("label", "")
knobs = cfg.get("knobs", {})
DEFAULTS = {"bank": 0, "maker": 0, "part": 0, "rev": 0, "harts": 1, "ramBytes": 65536}
k = {n: int(knobs.get(n, v)) for n, v in DEFAULTS.items()}


def with_parity(low):
    return low | (0x80 if bin(low).count("1") % 2 == 0 else 0)


def split(seq):
    for x in seq:
        if bin(x).count("1") % 2 != 1:
            raise SystemExit(f"字节 {x:#04x} 不是奇校验，不生成测试台")
    n = 0
    while n < len(seq) and seq[n] == 0x7F:
        n += 1
    if n == len(seq):
        raise SystemExit("最后一个字节也是续码 0x7f，不是厂商号，不生成测试台")
    if n != len(seq) - 1:
        raise SystemExit("续码之后多出字节，不生成测试台")
    return n, seq[n] & 0x7F


n, low = split([0x7F] * 12 + [0x8A])
if (n << 7 | low) != 0x60A or f"jep106:{n:02x}{low:02x}" != "jep106:0c0a":
    raise SystemExit("拆法对不上特权规范的例子，不生成测试台")

bank, code = split([0x7F] * k["bank"] + [with_parity(k["maker"])])
want = [
    ("vendor", 0x00, bank << 7 | code),
    ("soc", 0x04, bank << 24 | code << 16 | k["part"]),
    ("revision", 0x08, k["rev"]),
    ("harts", 0x0C, k["harts"]),
    ("ram", 0x10, k["ramBytes"]),
]

checks = "\n".join(f"""    action
      let x <- d.regs.access(RegReq {{ addr: 8'h{a:02X}, write: False, wdata: 0, wstrb: 4'hF }});
      if (x.rdata != 32'h{v:08X} || x.err) begin
        $display("FAIL {name} reads %08h (err %0d), want {v:08x}", x.rdata, x.err);
        bad <= True;
      end
    endaction""" for name, a, v in want)

verdict = ("vendor and soc read the JEP106 identity in the mvendorid and SMCCC SOC_ID layouts, "
           "and revision, harts and ram read the configured values")

TEMPLATE = r'''package Archinfo@L@Tb;

// 由 tb/mkarchinfotb.py 生成，勿手改。这一点：@KNOBS@

import StmtFSM::*;
import RegIf::*;
import Archinfo::*;

(* synthesize *)
module mkArchinfo@L@Tb(Empty);
  ArchinfoIfc#(8, 32, @TARGS@) d <- mkArchinfo(ArchinfoCfg { none: ? });
  Reg#(Bool) bad <- mkReg(False);

  Stmt test = seq
@CHECKS@
  endseq;

  FSM fsm <- mkFSM(test);
  Reg#(Bool) started <- mkReg(False);

  rule go (!started);
    started <= True;
    fsm.start;
  endrule

  rule fin (started && fsm.done);
    if (bad) $display("FAILED");
    else $display("PASS archinfo: @VERDICT@");
    $finish(bad ? 1 : 0);
  endrule
endmodule

endpackage
'''

txt = (TEMPLATE.replace("@L@", label)
       .replace("@KNOBS@", " ".join(f"{n}={v}" for n, v in k.items()))
       .replace("@TARGS@", ", ".join(str(k[n]) for n in DEFAULTS))
       .replace("@CHECKS@", checks)
       .replace("@VERDICT@", verdict))

(out / f"Archinfo{label}Tb.bsv").write_text(txt, encoding="utf-8")
print(f"  archinfo 行为测试台就位：{k}")
