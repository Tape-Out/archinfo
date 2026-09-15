# archinfo

Chip identity registers.

![maturity](https://img.shields.io/badge/maturity-simulated-yellow) ![license](https://img.shields.io/badge/license-MulanPSL--2.0-blue)

Part of the [Tape-Out](https://github.com/Tape-Out) IP library: Bluespec IP over the
bus-neutral contracts in [`hwcore`](https://github.com/Tape-Out/hwcore), assembled by
[`xirang`](https://github.com/Tape-Out/xirang). Maturity runs `planned` -> `simulated` ->
`fpga-proven` -> `asic-ready` -> `silicon-proven`.

## Status

Simulated. Five read-only registers give software the identity and build-time configuration of the chip. The values are parameters set in the SoC manifest, so they synthesise to constants.

`vendor` holds the JEDEC JEP106 manufacturer ID in the `mvendorid` layout of the RISC-V privileged specification, section 3.1.2: the number of 0x7f continuation codes in bits 31:7 and the last byte without its parity bit in bits 6:0. `soc` holds the same ID in the SMCCC SOC_ID layout that Linux decodes in `drivers/firmware/smccc/soc_id.c`: continuation codes in bits 30:24, the identification code in bits 22:16 and the SoC part number in bits 15:0. Both fields at zero mean a non-commercial implementation.

The encodings live in `Jep106.bs`, written in Bluespec Haskell: one pure function per layout, and a constructor that rejects an out-of-range ID at compile time, so a bad manifest value fails the build instead of reading back a wrong vendor. `Archinfo.bsv` feeds the values to the generated register block.

The testbench computes the expected values from the raw JEDEC byte sequence, continuation codes followed by a last byte with odd parity. Before it generates anything, it checks that decoding against the privileged specification's example, where twelve continuation codes and 0x8a encode as 0x60a. It then reads all five registers at every point of the parameter matrix.

Area is 12 to 26 um2 across the parameter range. The registers are constants, so synthesis keeps only the address decode and the read multiplexer.

## Parameters

| Parameter | Range | Meaning |
| :--: | :--: | :-- |
| `bank` | 0 to 127 | JEP106 continuation codes |
| `maker` | 0 to 126 | last byte of the JEP106 ID, without parity |
| `part` | 0 to 65535 | SoC part number |
| `rev` | 0 to 15 | revision |
| `harts` | 1 to 8 | number of harts |
| `ramBytes` | 0 to 4294967295 | on-chip RAM in bytes |

## Registers

| Offset | Register | Contents |
| :--: | :-- | :-- |
| 0x00 | `vendor` | JEDEC ID in the `mvendorid` layout |
| 0x04 | `soc` | JEDEC ID and part number in the SMCCC SOC_ID layout |
| 0x08 | `revision` | `rev` |
| 0x0C | `harts` | `harts` |
| 0x10 | `ram` | `ramBytes` |

The IDCODE layout of the RISC-V debug specification is not provided yet; it goes into `Jep106.bs` when `rvdbg` needs it.

## License

Mulan PSL v2.
