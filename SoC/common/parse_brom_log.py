#!/usr/bin/env python3

import fileinput
import re
import struct


DL_REGEX = r"\[DL\] (?P<x>[0-9A-F]{8}) (?P<y>[0-9A-F]{8}) (?P<a>[0-9A-F]{2})(?P<b>[0-9A-F]{2})(?P<c>[0-9A-F]{2})"
MSG_REGEX = r"(?P<type>[0-9A-Z]{2}): (?P<x>[0-9A-F]{4}) (?P<y>[0-9A-F]{4})( \[(?P<z>[0-9A-F]{4})\])?"


def get_orig(match):
    span = match.span()
    orig = match.string[span[0]:span[1]]
    return orig

def parse_dl(groups):
    usbdl_timeout_ms = int(groups['x'], 16)
    usbdl_mode = int(groups['y'], 16)
    flag = usbdl_mode >> 16
    timeout_s = (usbdl_mode >> 2) & 0x3fff
    enable = usbdl_mode & 1
    a = int(groups['a'], 16)
    b = int(groups['b'], 16)
    c = int(groups['c'], 16)

    print(" - {}: USB DL timeout: {} ms".format(groups['x'], usbdl_timeout_ms))
    print(" - {}: USB DL mode".format(groups['y']))
    print("   - Flag: {}".format("Present" if flag == 0x444C else "Absent"))
    print("   - Timeout: {} s".format(timeout_s))
    print("   - Enabled: {}".format(True if enable else False))
    print(" - {}".format(groups['a']))
    print(" - {}".format(groups['b']))
    print(" - {}".format(groups['c']))

def parse_bp(groups):
    flags_hi = int(groups['x'], 16)
    flags_lo = int(groups['y'], 16)
    offset = int(groups['z'], 16)
    flags = (flags_hi << 16) | flags_lo

    flag_bits = {
        0x00000001: "Preloader found on boot medium.",
        0x00000002: "USB synced for DL mode.",
        0x00000008: "JTAG is disabled.",
        0x00000010: "USB failed to sync for DL mode.",
        0x00000020: "UART synced for DL mode.",
        0x00000040: "UART failed to sync for DL mode.",
        0x00000080: "Preloader offset is non-zero.",
        0x00000200: "SEJ + 0xc0 (SEJ_CON1) bits [11:8] are not clear.",
        0x04000000: "Preloader on boot medium is 64-bit.",
        0x08000000: "USB DL HS (High Speed?) enabled.",
        0x10000000: "gfh_brom_cfg.gfh_brom_cfg_v3.reserved3 bit 0 and gfh_brom_cfg.gfh_brom_cfg_v3.flags.reserved1 are set: or M_SW_RES bit 6 is set.",
        0x20000000: "M_SW_RES bit 5 set.",
        0x40000000: "M_SW_RES bit 4 set.",
        0x80000000: "M_SW_RES bit 3 set.",
    }

    print(" - {} {}: Flags".format(groups['x'], groups['y']))
    for bit in range(32):
        mask = 1 << bit
        if flags & mask:
            description = flag_bits.get(mask, "Unknown.")
            print("   - {}".format(description))
    print(" - {}: Preloader offset: {} bytes".format(groups['z'], offset * 2048))

def parse_t0(groups):
    time_hi = int(groups['x'], 16)
    time_lo = int(groups['y'], 16)
    jtag_delay = int(groups['z'], 16)
    boot_time = (time_hi << 16) | time_lo

    print(" - {} {}: BROM execution time: {} ms".format(groups['x'], groups['y'], boot_time))
    print(" - {}: JTAG delay % 65536: {} ms".format(groups['z'], jtag_delay))

def parse_msg(groups):
    msg_type = groups['type']

    msg_handler = {
        'BP': parse_bp,
        'T0': parse_t0,
    }.get(msg_type, lambda x: None)

    msg_handler(groups)

def main():
    matchers = (
        (re.compile(DL_REGEX), parse_dl),
        (re.compile(MSG_REGEX), parse_msg),
    )
    for line in fileinput.input():
        for regex, handler in matchers:
            match = regex.search(line)
            if match:
                print(get_orig(match))
                groups = match.groupdict()
                handler(groups)
                break


if __name__ == "__main__":
    main()