# UPDATE_MISSING_FRAGMENTS Command

This document explains how to construct the UPDATE_MISSING_FRAGMENTS command payload so the satellite knows which fragments you already have.

## Command Arguments

- `tid` (1 byte): Transaction ID.
- `seq_offset` (2 bytes): Starting fragment index for this bitmap window.
- `MSB` (2 bytes): Most‑significant 16 bits of the bitmap.
- `LSB` (2 bytes): Least‑significant 16 bits of the bitmap.

## Bitmap Semantics

- The bitmap represents a window of up to 32 fragments starting at `seq_offset`.
- **Bit value meaning:**
  - `1` = fragment already received → remove from missing list.
  - `0` = fragment missing → add/keep in missing list.
- **Bit order:** MSB‑first within the window.
  - The **MSB of the 32‑bit bitmap corresponds to `seq_offset`**.
  - Next bit corresponds to `seq_offset + 1`, and so on.

## Window Length and Tail Window

If the transaction length isn’t a multiple of 32, the last window is shorter. Only bits for fragment indices in the range:

```
[seq_offset, number_of_packets)
```

are applied. Extra bits in the 32‑bit bitmap are ignored.

## Building MSB/LSB

You build a 32‑bit bitmap for the window and split it into:

- `MSB = (bitmap >> 16) & 0xFFFF`
- `LSB = bitmap & 0xFFFF`

## Example (Conceptual)

Assume a window starting at `seq_offset = 64` with 8 fragments in scope:

- If you already have fragments 64, 66, 67, and 71, then bits for those indices are 1.
- With MSB‑first order, the leftmost bit corresponds to 64, the next to 65, etc.

The encoded bitmap is then split into `MSB` and `LSB` and sent with `tid` and `seq_offset`.

## Example (Fragments 1, 10, 12 Received)

Assume:

- `seq_offset = 0`
- You already have fragments **1**, **10**, and **12**

With MSB‑first ordering (bit 31 → fragment 0, bit 30 → fragment 1, …):

- Fragment 1 → bit position 30
- Fragment 10 → bit position 21
- Fragment 12 → bit position 19

Bitmap value:

- `bitmap = (1 << 30) | (1 << 21) | (1 << 19) = 0x40280000`

Split into two 16‑bit values:

- `MSB = 0x4028` (decimal 16424)
- `LSB = 0x0000` (decimal 0)

So the command arguments should include:

- `seq_offset = 0`
- `MSB = 0x4028`
- `LSB = 0x0000`

## Related Code

- Bitmap generation and handling are implemented in `Transaction.generate_missing_bitmaps()` and `Transaction.update_missing_fragments_bitmap()`.
