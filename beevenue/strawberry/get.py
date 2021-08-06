import random
from typing import Dict, Generator, List, Tuple, Union

from flask import current_app
from sentry_sdk import start_span

from beevenue.flask import g, request
from beevenue.document_types import TinyMediumDocument
from beevenue.strawberry.viewmodels import (
    ViolationViewModel,
    ViolationsViewModel,
    fix_view_model,
)

from .json import decode_rules_json
from .rule import Rule


def get_rules() -> List[Rule]:
    with start_span(op="http", description="Loading current rules"):
        rules_file_path = current_app.config["BEEVENUE_RULES_FILE"]
        with open(rules_file_path, "r") as rules_file:
            rules_file_json = rules_file.read()

        rules_file_json = rules_file_json or "[]"

        return decode_rules_json(rules_file_json)


def get_violations(medium_id: int) -> ViolationsViewModel:
    medium = g.fast.get_tiny(medium_id)

    violations = []

    for rule in get_rules():
        for violation in rule.violations_for(medium):
            fixes = [fix_view_model(f) for f in violation.get_fixes()]
            violations.append(
                ViolationViewModel(text=rule.pprint(), fixes=fixes)
            )

    return ViolationsViewModel(violations)


GeneratorResult = Tuple[TinyMediumDocument, bool]
MediaGenerator = Generator[GeneratorResult, None, None]


def _nsfw_generator() -> MediaGenerator:
    all_media = g.fast.get_all_tiny()
    random.shuffle(all_media)
    for medium in all_media:
        yield medium, True


def _sfw_generator() -> MediaGenerator:
    all_media = g.fast.get_all_tiny()
    sorted_ratings = ["s", "q", "e", "u"]

    media_by_rating: Dict[str, List[TinyMediumDocument]] = {
        r: list() for r in sorted_ratings
    }

    for medium in all_media:
        media_by_rating[medium.rating].append(medium)

    for rating in sorted_ratings:
        is_visible = rating == "s"
        current_media = media_by_rating[rating]
        random.shuffle(current_media)
        for medium in current_media:
            yield medium, is_visible


def _generate_random_media() -> MediaGenerator:
    if request.beevenue_context.is_sfw:
        return _sfw_generator()

    return _nsfw_generator()


RandomViolation = Tuple[int, None]
Notification = Tuple[None, str]
NoViolationsLeft = Tuple[None, None]
RandomRuleViolation = Union[RandomViolation, Notification, NoViolationsLeft]


def random_rule_violation() -> RandomRuleViolation:
    rules = get_rules()
    random.shuffle(rules)

    for medium, is_visible in _generate_random_media():
        for rule in rules:
            if rule.is_violated_by(medium):
                if is_visible:
                    return medium.medium_id, None
                return None, "There are no more SFW rule violations."

    return None, None
