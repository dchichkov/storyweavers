#!/usr/bin/env python3
"""
storyworlds/worlds/campfire_caution.py
=====================================

Story world sketch for a campfire caution and safe alternative.

A child wants to act on a tempting object by the fire. The chosen response must be
compatible with both the object and the campsite setting.
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class CampSetting:
    key: str
    phrase: str
    allowed_responses: tuple[str, ...]
    warning: str


@dataclass(frozen=True)
class CampObject:
    key: str
    phrase: str
    danger: str
    risk_note: str
    compatible_responses: tuple[str, ...]


@dataclass(frozen=True)
class SafeResponse:
    key: str
    phrase: str
    cue: str
    action: str
    result: str
    lesson: str
    solves: tuple[str, ...]


@dataclass
class StoryParams:
    setting: str
    object: str
    response: str
    hero: str
    gender: str
    parent: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    traits: list[str] = field(default_factory=list)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "mother", "aunt", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in {"boy", "father", "uncle", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    params: StoryParams
    setting: CampSetting
    item: CampObject
    response: SafeResponse
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        for name, ent in self.entities.items():
            traits = ", ".join(ent.traits) if ent.traits else "none"
            rows.append(f"  {name:<10} ({ent.kind:<11}) traits=[{traits}] memes={dict(ent.memes)}")
        rows.append(f"  setting: {self.setting.key} ({self.setting.phrase})")
        rows.append(f"  object: {self.item.key} danger={self.item.danger}")
        rows.append(f"  response: {self.response.key} ({self.response.cue})")
        rows.append(f"  fired rules: {self.fired}")
        return "\n".join(rows)


SETTINGS = {
    "pine_glade": CampSetting(
        key="pine_glade",
        phrase="the pine glade campsite",
        allowed_responses=("long_rod", "mitts", "ask_adult"),
        warning="dry leaves crackled and sparks kept floating",
    ),
    "beach_lagoon": CampSetting(
        key="beach_lagoon",
        phrase="a beach lagoon campsite",
        allowed_responses=("long_rod", "ask_adult"),
        warning="the breeze pulled embers toward the open sand",
    ),
    "windy_ridge": CampSetting(
        key="windy_ridge",
        phrase="a windy ridge campsite",
        allowed_responses=("mitts", "ask_adult"),
        warning="gusts made small objects slide fast toward the flames",
    ),
}

OBJECTS = {
    "marshmallow": CampObject(
        key="marshmallow",
        phrase="a fresh marshmallow",
        danger="burn",
        risk_note="it can caramelize and burn quickly in heat",
        compatible_responses=("long_rod", "ask_adult"),
    ),
    "camp_pot": CampObject(
        key="camp_pot",
        phrase="an old camp pot",
        danger="steam",
        risk_note="steam can scald hands near the rim",
        compatible_responses=("mitts", "ask_adult"),
    ),
    "camp_stick": CampObject(
        key="camp_stick",
        phrase="a dry branch by the stones",
        danger="spark",
        risk_note="it can ignite and send sparks in the wind",
        compatible_responses=("long_rod", "ask_adult"),
    ),
    "metal_canister": CampObject(
        key="metal_canister",
        phrase="a metal canister",
        danger="steam",
        risk_note="its side can be dangerously hot for bare hands",
        compatible_responses=("mitts", "ask_adult"),
    ),
}

RESPONSES = {
    "long_rod": SafeResponse(
        key="long_rod",
        phrase="a long metal rod",
        cue="use distance to keep hands safe",
        action='{parent} passed {hero} {response_phrase} and said, "Keep your hands back."',
        result="{hero} nudged {item} from the bright edge to a safe place beside the fire.",
        lesson="Distance can make a dangerous action safe.",
        solves=("burn", "spark"),
    ),
    "mitts": SafeResponse(
        key="mitts",
        phrase="a pair of thick mitts",
        cue="use insulation when handling hot metal",
        action='{parent} put on {response_phrase} and showed {hero} the safer grip.',
        result="{hero} held {item} carefully and moved it without touching the hot metal.",
        lesson="Protection works when the helper stays close and deliberate.",
        solves=("steam", "burn"),
    ),
    "ask_adult": SafeResponse(
        key="ask_adult",
        phrase="a call for help",
        cue="let an adult do the risky step",
        action='{hero} asked {parent} for help before moving toward the fire.',
        result='{parent} handled {item} first and then showed a safe way for {hero} to watch.',
        lesson="Some tasks become safer when adults step in early.",
        solves=("burn", "steam", "spark"),
    ),
}

HEROS = {
    "girl": ("Mira", "Nora", "Lena", "Sage"),
    "boy": ("Noah", "Eli", "Ravi", "Theo"),
}

PARENTS = ("mother", "father", "uncle", "aunt", "grandmother", "grandfather")


def _pick_hero(gender: str, rng: random.Random) -> str:
    return rng.choice(HEROS[gender])


def _params_from_combo(args: argparse.Namespace, combo: tuple[str, str, str], index: int = 0) -> StoryParams:
    rng = random.Random(args.seed + index)
    gender = args.gender or rng.choice(sorted(HEROS))
    hero = args.hero or _pick_hero(gender, rng)
    parent = args.parent or rng.choice(PARENTS)
    setting, obj_key, response_key = combo
    return StoryParams(
        setting=setting,
        object=obj_key,
        response=response_key,
        hero=hero,
        gender=gender,
        parent=parent,
        seed=args.seed + index,
    )


def valid_combo(setting_key: str, object_key: str, response_key: str) -> bool:
    if setting_key not in SETTINGS or object_key not in OBJECTS or response_key not in RESPONSES:
        return False
    setting = SETTINGS[setting_key]
    item = OBJECTS[object_key]
    return response_key in setting.allowed_responses and response_key in item.compatible_responses


def invalid_reason(setting_key: str, object_key: str, response_key: str) -> str:
    if setting_key not in SETTINGS:
        return f"No story: unknown setting {setting_key!r}."
    if object_key not in OBJECTS:
        return f"No story: unknown object {object_key!r}."
    if response_key not in RESPONSES:
        return f"No story: unknown response {response_key!r}."
    setting = SETTINGS[setting_key]
    item = OBJECTS[object_key]
    if response_key not in setting.allowed_responses:
        return (
            f"No story: {setting.phrase} does not support response {response_key!r}. "
            f"Try one of: {', '.join(setting.allowed_responses)}."
        )
    if response_key not in item.compatible_responses:
        return (
            f"No story: {item.phrase} is not safely handled by {response_key!r}. "
            f"It is compatible with: {', '.join(item.compatible_responses)}."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_key in sorted(SETTINGS):
        for object_key in sorted(OBJECTS):
            for response_key in sorted(RESPONSES):
                if valid_combo(setting_key, object_key, response_key):
                    combos.append((setting_key, object_key, response_key))
    return combos


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    item = OBJECTS[params.object]
    response = RESPONSES[params.response]
    world = World(params=params, setting=setting, item=item, response=response)

    hero = world.add(Entity(params.hero, kind=params.gender, traits=["curious"]))
    adult_kind = params.parent.lower()
    world.add(Entity(params.parent.title(), kind=adult_kind, traits=["careful"]))

    world.facts["setting"] = setting.key
    world.facts["object"] = item.key
    world.facts["response"] = response.key
    world.facts["danger"] = item.danger
    world.facts["resolved"] = "1"
    world.facts["seed"] = str(params.seed)
    hero.memes["caution"] = 1.0
    world.facts["hero"] = hero.id
    world.facts["parent"] = params.parent.title()
    return world


def _render_story(world: World) -> str:
    setting = world.setting
    item = world.item
    response = world.response
    params = world.params
    hero = world.entities[params.hero]
    parent = world.entities[params.parent.title()]
    parent_ref = "his" if parent.kind in {"father", "uncle", "grandfather"} else "her"

    opening = (
        f"One evening at {setting.phrase}, {hero.id} watched the campfire glow and spotted {item.phrase}. "
        f"{setting.warning.capitalize()}."
    )
    temptation = (
        f"{hero.id} wanted to act quickly and reached for the object before thinking."
    )
    warning = (
        f'{parent.id} noticed and said, "Hold on. {item.phrase.capitalize()} near the fire can be '
        f'dangerous, because {item.risk_note}. We need a safe move."'
    )

    action = response.action.format(
        parent=parent.id,
        hero=hero.id,
        hero_pronoun=hero.pronoun("subject"),
        response_phrase=response.phrase,
        item=item.phrase,
    )
    outcome = response.result.format(
        parent=parent.id,
        hero=hero.id,
        parent_possessive=parent_ref,
        response_phrase=response.phrase,
        item=item.phrase,
    )
    lesson = (
        f'The lesson was clear: "{response.lesson}" '
        f"{hero.id} understood that caution is not the end of adventure; it is how adventures stay safe."
    )

    return "\n\n".join([opening, temptation, warning, action, outcome, lesson])


def _prompts(world: World) -> list[str]:
    return [
        'Write a cautionary campfire story using the words "campfire", "caution", and "help".',
        f"Tell a story where {world.params.hero} uses the safe option at the camp.",
        "Make sure the story shows why the method is safer than acting rashly.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    hero = world.params.hero
    item = world.item
    response = world.response
    setting = world.setting
    return [
        QAItem(
            "Who is in this story?",
            f"{hero} is the child near the campfire, and {world.params.parent} is the adult who helps control the risk. The setting is {setting.phrase}, where the fire changes what actions are safe.",
        ),
        QAItem(
            "Why was acting quickly not enough?",
            f"{hero} was about to handle {item.phrase}, which can be unsafe because {item.risk_note}. Moving fast would make the danger harder to see before hands or clothing got too close.",
        ),
        QAItem(
            "How did the safer response work?",
            f"{hero} used {response.phrase}. That response fits the hazard because it follows the cue to {response.cue} instead of relying on bravery alone.",
        ),
        QAItem(
            "What changed by the end?",
            f"{hero} moved {item.phrase} safely and kept the campfire moment calm. The important change is that the child chose a method that solved {item.danger} rather than touching the risk directly.",
        ),
        QAItem(
            "What practical lesson does this teach?",
            f"{response.lesson} In this world, a safe campfire choice is specific to the object and the campsite, not a generic rule to grab things carefully.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    base = [
        QAItem(
            "Why is there a safe-response constraint?",
            "Each campsite offers different tools and hazards, so only some responses are valid for each object. The constraint keeps the story from claiming that any tool can solve any fire danger.",
        ),
        QAItem(
            "Why does asking an adult always work?",
            f"{RESPONSES['ask_adult'].phrase.capitalize()} keeps the risky hand-action under adult supervision and avoids heat exposure. It is the broad fallback because an adult can choose whether to use distance, insulation, or no touch at all.",
        ),
    ]
    if world.item.danger == "steam":
        base.append(QAItem("How do mitts help with steam hazards?", "They insulate the hands and reduce direct heat transfer from hot metal or steam. The story still keeps the helper nearby, because protection works best when the motion is slow and deliberate."))
    if world.item.danger == "spark":
        base.append(QAItem("Why is distance good for spark risks?", "Distance reduces accidental contact and limits how far burns and embers can travel onto skin. That is why rod-like or adult-guided responses fit spark cases better than bare hands."))
    return base


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.setting, params.object, params.response):
        raise StoryError(invalid_reason(params.setting, params.object, params.response))
    world = build_world(params)
    return StorySample(
        params=params,
        story=_render_story(world),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = """
combo(S,O,R) :-
    setting(S),
    object(O),
    response(R),
    allows(S,R),
    compatible(O,R).

ok :- chosen(S,O,R), combo(S,O,R).

#show combo/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for setting in SETTINGS:
        rows.append(fact("setting", setting))
        for response in SETTINGS[setting].allowed_responses:
            rows.append(fact("allows", setting, response))
    for item in OBJECTS:
        rows.append(fact("object", item))
        for response in OBJECTS[item].compatible_responses:
            rows.append(fact("compatible", item, response))
    for response in RESPONSES:
        rows.append(fact("response", response))
    if params is not None:
        rows.append(fact("chosen", params.setting, params.object, params.response))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from storyworlds.asp import atoms, solve

    symbols = solve(asp_program(), models=0)
    combos: set[tuple[str, str, str]] = set()
    for model in symbols:
        combos.update(atoms(model, "combo"))
    return combos


def asp_verify(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params)), "ok"))


def verify() -> str:
    py = set(valid_combos())
    asp = asp_valid_combos()
    if py != asp:
        only_py = sorted(py - asp)
        only_asp = sorted(asp - py)
        raise StoryError(f"ASP/Python mismatch. only_python={only_py} only_asp={only_asp}")
    return f"OK: clingo gate matches valid_combos() ({len(py)} combos)."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate campfire caution world samples.")
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--object", choices=sorted(OBJECTS))
    parser.add_argument("--response", choices=sorted(RESPONSES))
    parser.add_argument("--hero", default=None)
    parser.add_argument("--gender", choices=sorted(HEROS), default=None)
    parser.add_argument("--parent", choices=PARENTS)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, index: int = 0) -> StoryParams:
    rng = random.Random(args.seed + index)
    choices = valid_combos()
    if args.setting or args.object or args.response:
        filtered = [
            (setting, obj, response)
            for (setting, obj, response) in choices
            if (args.setting is None or setting == args.setting)
            and (args.object is None or obj == args.object)
            and (args.response is None or response == args.response)
        ]
        if not filtered:
            raise StoryError(invalid_reason(args.setting or "<setting>", args.object or "<object>", args.response or "<response>"))
        combo = rng.choice(filtered)
    else:
        combo = rng.choice(choices)
    return _params_from_combo(args, combo, index)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Story prompts ==")
    for i, prompt in enumerate(sample.prompts, 1):
        print(f"{i}. {prompt}")
    print("\n== (2) Story Q&A ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World Q&A ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(sample: StorySample, args: argparse.Namespace, label: str | None = None) -> None:
    if args.json:
        print(sample.to_json())
        return
    if label:
        print(label)
    print(sample.story)
    if args.trace and sample.world is not None:
        print(sample.world.trace())
    if args.qa:
        _print_qa(sample)


def _emit_asp_listing() -> None:
    for setting, obj, response in sorted(asp_valid_combos()):
        print(f"{setting}\t{obj}\t{response}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            _emit_asp_listing()
            return 0
        if args.all:
            combos = valid_combos()
            for i, combo in enumerate(combos, 1):
                sample = generate(_params_from_combo(args, combo, i))
                emit(sample, args, f"### {combo[0]} / {combo[1]} / {combo[2]}")
                if i != len(combos) and not args.json:
                    print("\n" + "=" * 72 + "\n")
            return 0
        for i in range(max(1, args.n)):
            sample = generate(resolve_params(args, i))
            emit(sample, args, f"### variant {i + 1}" if args.n > 1 and not args.json else None)
            if i != max(1, args.n) - 1 and not args.json:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
