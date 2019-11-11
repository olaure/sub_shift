import datetime as dt
import logging
import re
from typing import Dict, List, Optional, Tuple

import click

LINE_TYPE_COUNTER = 0
LINE_TYPE_TIMER = 1
LINE_TYPE_SUB = 2

TIMER_RE = re.compile("(?P<sh>\d\d):(?P<sm>\d\d):(?P<ss>\d\d),(?P<sms>\d{3}) --> (?P<eh>\d\d):(?P<em>\d\d):(?P<es>\d\d),(?P<ems>\d{3})")

def read_file(filename: str) -> List[Dict]:
    subs = []
    with open(filename, "rb") as fle:
        lines = fle.readlines()

    sub_entry = {}
    line_type = LINE_TYPE_COUNTER

    for line in lines:
        if not line.strip():
            if sub_entry:
                subs.append(sub_entry)
            sub_entry = {}
            line_type = LINE_TYPE_COUNTER
            continue

        if line_type == LINE_TYPE_COUNTER:
            sub_entry["num"] = line
            line_type += 1

        elif line_type == LINE_TYPE_TIMER:
            match_entry = TIMER_RE.match(line.decode().strip())
            if not match_entry:
                logging.warning("failed to decode time line", line)
                sub_entry["timer"] = None
            else:
                sub_entry["timer"] = match_entry.groupdict()
            sub_entry["sub"] = []
            line_type += 1

        elif line_type == LINE_TYPE_SUB:
            sub_entry["sub"].append(line)

    if sub_entry:
        subs.append(sub_entry)

    return subs

def offset_delta(offset: float) -> dt.timedelta:
    """
    """
    # This is to avoid any rounding errors
    int_part, dec_part = str(offset).split('.')
    off_mil = int((dec_part + "000")[:3])
    is_neg = int_part[0] == '-'
    if is_neg:
        offset = int(int_part[1:])
    else:
        offset = int(int_part)

    off_hours = int(offset / 3600)
    offset -= 3600 * off_hours

    off_mins = int(offset / 60)
    offset -= 60.0 * float(off_mins)

    off_sec = int(offset)
    delta = dt.timedelta(hours=off_hours, minutes=off_mins, seconds=off_sec, milliseconds=off_mil)
    if is_neg:
        return -delta
    return delta

def shift_subs(subs: List[Dict], off_secs: float) -> List[Dict]:
    """
    """
    # This is to avoid any rounding errors
    offset = offset_delta(off_secs)

    for sub in subs:
        timer = sub["timer"]
        start_time = dt.datetime(2000, 1, 1,
                                 int(timer["sh"]),
                                 int(timer["sm"]),
                                 int(timer["ss"]),
                                 int(timer["sms"]) * 1000)
        end_time = dt.datetime(2000, 1, 1,
                                 int(timer["eh"]),
                                 int(timer["em"]),
                                 int(timer["es"]),
                                 int(timer["ems"]) * 1000)
        start_time += offset
        end_time += offset
        sub["timer"] = {
            "sh": "{:02}".format(start_time.hour),
            "eh": "{:02}".format(end_time.hour),

            "sm": "{:02}".format(start_time.minute),
            "em": "{:02}".format(end_time.minute),

            "ss": "{:02}".format(start_time.second),
            "es": "{:02}".format(end_time.second),

            "sms": "{:03}".format(start_time.microsecond // 1000),
            "ems": "{:03}".format(end_time.microsecond // 1000),
        }


def write_subs(subs: List[Dict], filename: str) -> None:
    lines = []
    for sub in subs:
        timer_format = "{sh}:{sm}:{ss},{sms} --> {eh}:{em}:{es},{ems}\r\n"
        lines.extend([
            sub["num"],
            timer_format.format(**sub["timer"]).encode(),
            *sub["sub"],
            b"\r\n"
        ])
    to_write = b"".join(lines)
    if filename:
        open(filename, "wb").write(to_write)
    else:
        print(to_write)

@click.command()
@click.argument('infile', required=1)
@click.option('--outfile', '-o', default=None, help='Output file. defaults to stdout.')
@click.option('--shift', '-s', default=0.0, help='shift in seconds (can be negative, truncated to miliseconds)')
def shift(infile: str = "", outfile: Optional[str] = None, shift: float = 0.0):
    try:
        subs = read_file(infile)
    except Exception as err:
        logging.error("Unable to read file %s: %s", infile, err)
        return

    try:
        shift_subs(subs, shift)
    except Exception as err:
        logging.error("Unable to shift subs: %s", err)
        return

    try:
        write_subs(subs, outfile)
    except Exception as err:
        logging.error("Unable to write subs: %s", err)
        return


if __name__ == '__main__':
    shift()
