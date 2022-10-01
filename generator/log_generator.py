import os
import sys
import argparse
import logging
from logging.handlers import RotatingFileHandler
import random
import json
import time


KEY = "Key"
LEVEL = "Level"
VALUE = "Value"

msgs_to_generate = 500

# Choosin maximum size of generated object 
max_obj_size = 3

# Choosing maximum depth of generated JSON
max_depth = 3

json_prefixes = [
    "Example log with JSON",
    "Log with example JSON",
    "JSON data in logs"
]

simple_messages = [
    "Some example log entry",
    "Log entry for test purpose",
    "Something important happened",
    "This is information that has to be saved"
]

def generate_json():
    # All JSONs roots in messages are dictionary
    data = {}

def make_key(l, i):
    return f"{LEVEL}-{max_depth-l+1}-{KEY}-{i+1}"

def make_value(l, i):
    return f"{LEVEL}-{max_depth-l+1}-{VALUE}-{i+1}"

def generate_json_level(level):
    # Level 0 need to generate values
    if level == max_depth:
        data = {}
    else:
        data = random.choice(
            [
                {},
                []
             ]
            )
    size = random.randint(0, max_obj_size)
    for idx in range(size):
        key = make_key(level, idx)
        value = make_value(level, idx)
        if level > 0:
            value = random.choice(
                [
                    generate_json_level(level - 1),
                    make_value(level, idx)
                ]
            )
        else:
            value = make_value(level, idx)
        if isinstance(data, list):
            data.append(value)
        else:
            data[key] = value
    return data


if __name__ == "__main__":
    if len(sys.argv) != 11:
        print("""
Expecting arguments:
--out_filename
--mode fg/sim
--logs_to_repair DIR_NAME
--logs_for_tests DIR_NAME
--sleep_time_base SECONDS
        """)
        exit(1)
    ap = argparse.ArgumentParser(
        description="Generator of test legs"
        )
    ap.add_argument(
        "--out_filename",
        type=str,
        help="Output filenemame"
    )
    ap.add_argument(
        "--sleep_time_base",
        type=float,
        help="Sleep time cycle base seconds as float number"
    )
    ap.add_argument(
        "--mode",
        type=str,
        help="Execution mode: fg-fast_generation, sim-simulate"
    )
    ap.add_argument(
        "--logs_to_repair",
        type=str,
        help="path to folder where broken logs would be created"
    )
    ap.add_argument(
        "--logs_for_tests",
        type=str,
        help="path to folder where proper logs necessary for testing would be created"
    )
    args = ap.parse_args()
    output_filename = args.out_filename
    logs_to_repair = args.logs_to_repair
    logs_for_tests = args.logs_for_tests
    sleep_time_base = args.sleep_time_base
    if not args.mode in ["fg", "sim"]:
        print("No proper work mode given. Please define -mode 'fg' or 'sim'. Exiting!")
        exit(1)
    logger_tr = logging.getLogger("logs_to_repair")
    logger_ft = logging.getLogger("logs_for_tests")
    logger_tr.setLevel(logging.INFO)
    logger_ft.setLevel(logging.INFO)
    file_formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    file_handler_tr = RotatingFileHandler(
        filename=os.path.join(logs_to_repair, output_filename),
        maxBytes=10000,
        backupCount=10
        )
    file_handler_ft = RotatingFileHandler(
        filename=os.path.join(logs_for_tests, output_filename),
        maxBytes=10000,
        backupCount=10
        )
    file_handler_tr.setFormatter(file_formatter)
    file_handler_ft.setFormatter(file_formatter)
    logger_tr.addHandler(file_handler_tr)
    logger_ft.addHandler(file_handler_ft)
    entry_index = 0
    print("_________________________")
    if args.mode == "sim":
        print("Starting log simulation")
    else:
        print("Starting log generation")
    while True:
        if args.mode == "sim":
            sleep_time = sleep_time_base + random.uniform(0, 1.25)
        else:
            if entry_index > msgs_to_generate:
                print(f"Finished. {msgs_to_generate} messages generated.")
                exit(0)
            sleep_time = 0
        time.sleep(sleep_time)
        entry_index += 1
        if random.randint(1, 5) < 3:
            prefix = random.choice(json_prefixes)
            jdata = generate_json_level(max_depth)
            msg_tr = " " + json.dumps(
                    jdata,
                    indent=4
                )
            msg_ft = " " + json.dumps(
                    jdata,
                )
        else:
            prefix = ""
            msg = random.choice(simple_messages)
            msg_tr = msg
            msg_ft = msg
        logger_tr.info(f"index={entry_index} {prefix}{msg_tr}")
        logger_ft.info(f"index={entry_index} {prefix}{msg_ft}")
    
