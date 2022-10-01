import os
import argparse
import re
import json

datetime_pattern = "^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) ([0-1][0-10]|2[0-3]):([0-5][0-9]):([0-5][0-9])(,|\.)\d{3}"

def line_startswith_dt(line_to_check):
    if re.search(datetime_pattern, line_to_check) is None:
        return False
    else:
        return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--in_logs",
        type=str,
        help="path to directory containing logs to repair"
    )
    ap.add_argument(
        "--out_logs",
        type=str,
        help="path to folder where repaired logs would be placed"
    )
    args = ap.parse_args()
    logs_to_repair = args.in_logs
    logs_repaired = args.out_logs
    if logs_to_repair is None or logs_repaired is None:
        print("Usage: python logs-history-repair.py --in_logs DIR_NAME --out_logs DIR_NAME")
        exit(1)
    for infn in os.listdir(logs_to_repair):
        with open(
            os.path.join(logs_to_repair, infn),
            'r'
        ) as inf:
            lines_tr = inf.readlines()
        repaired_lines = []
        merging_json = False
        json_lines = []
        json_text = ""
        message_before_json = ''
        end_of_lines = False
        for idx, ltrn in enumerate(lines_tr):
            ltr = ltrn.strip("\n")
            if merging_json:
                json_lines.append(ltr)
            if line_startswith_dt(ltr) and ltr.endswith("{"):
                merging_json = True
                json_lines.append("{")
                message_before_json = ltr[:-2]
            else:
                if not merging_json:
                    repaired_lines.append(ltr)
            end_of_json = False
            try:
                next_line = lines_tr[idx+1]
            except IndexError:
                end_of_json = True
                end_of_lines = True
            if ltr == "}" and line_startswith_dt(next_line):
                end_of_json = True
            if end_of_json:
                merging_json = False
                if not end_of_lines:
                    json_raw_text = "".join(json_lines)
                    json_data = json.loads(json_raw_text)
                    json_text = json.dumps(
                        json_data,
                        separators=(",", ": ")
                        )
                repaired_lines.append(
                    f"{message_before_json} {json_text}"
                    )
                json_lines = []
                json_text = ""
                message_before_json = ""
        outfn = f"repaired-{infn}"
        with open(
            os.path.join(logs_repaired, outfn),
            mode="w"
        ) as outf:
            outf.write("\n".join(repaired_lines))



