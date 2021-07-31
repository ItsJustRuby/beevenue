from typing import List

from flask import current_app
from sentry_sdk import start_span

from .json import decode_rules_json
from .rule import Rule


def get_rules() -> List[Rule]:
    with start_span(op="http", description="Loading current rules"):
        rules_file_path = current_app.config["BEEVENUE_RULES_FILE"]
        with open(rules_file_path, "r") as rules_file:
            rules_file_json = rules_file.read()

        rules_file_json = rules_file_json or "[]"

        return decode_rules_json(rules_file_json)
