#!/usr/bin/env python3
"""
festival_search.py
==================

Seed:

    Words: map, whistle, lantern
    Features: Problem Solving, Mystery, Teamwork
    Style: Mystery

A child loses a treasured object during a festival, and a remembered sound or
clue guides a careful search through a district with a tool that must match the
kind of place the object went missing.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

STORYWORLDS = Path(__file__).resolve().parents[1]
if str(STORYWORLDS) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS))

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class District:
    key: str
    phrase: str
    supported_spots: tuple[str, ...]
    atmosphere: str


@dataclass(frozen=True)
class LostObject:
    key: str
    phrase: str
    material: str
    water_safe: bool
    loved_for: str


@dataclass(frozen=True)
class SearchSpot:
    key: str
    phrase: str
    need: str
    clue: str
    flashback: str
    hazard: str = "dry"


@dataclass(frozen=True)
class SearchMethod:
    key: str
    phrase: str
    action: str
    solves: tuple[str, ...]
    unsafe: bool = False


@dataclass
class StoryParams:
    district: str
    lost_object: str
    spot: str
    method: str
    hero: str
    gender: str
    helper: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    tags: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = round(self.meters.get(key, 0.0) + amount, 2)

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = round(self.memes.get(key, 0.0) + amount, 2)


@dataclass
class World:
    params: StoryParams
    district: District
    lost_object: LostObject
    spot: SearchSpot
    method: SearchMethod
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    fired: list[str] = field(default_factory=list)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        for name, ent in self.entities.items():
            tags = ", ".join(f"{k}={v}" for k, v in sorted(ent.tags.items()))
            meters = f" meters={ent.meters}" if ent.meters else ""
            memes = f" memes={ent.memes}" if ent.memes else ""
            suffix = f" {tags}" if tags else ""
            rows.append(f"  {name:<9} ({ent.kind:<11}){suffix}{meters}{memes}")
        fact_text = ", ".join(f"{k}={v}" for k, v in sorted(self.facts.items()))
        rows.append(f"  facts: {fact_text}")
        rows.append(f"  fired rules: {self.fired}")
        return "\n".join(rows)


DISTRICTS: dict[str, District] = {
    "fairground": District(
        "fairground",
        "the summer fairground",
        ("under_bench", "ticket_box", "crowd_queue"),
        "bright lights, candy stalls, and many voices",
    ),
    "orchard": District(
        "orchard",
        "the orchard lane",
        ("orchard_tree", "hay_silo", "flower_wall"),
        "crisp soil, tall branches, and late-evening wind",
    ),
    "river_dock": District(
        "river_dock",
        "the river dock",
        ("dock_rope", "river_boat", "dock_cradle"),
        "hazy water smell and rope-thud sounds",
    ),
    "station": District(
        "station",
        "the station platform",
        ("clock_door", "locker_box", "tower_steps"),
        "distant whistles and hard tile underfoot",
    ),
}

LOST_OBJECTS: dict[str, LostObject] = {
    "paper_note": LostObject("paper_note", "paper note", "paper", False, "the midnight treasure clue"),
    "tin_whistle": LostObject("tin_whistle", "tiny tin whistle", "tin", True, "the lantern parade"),
    "felt_map": LostObject("felt_map", "felt map", "felt", False, "the hidden orchard route"),
    "glass_lantern": LostObject("glass_lantern", "small glass lantern", "glass", False, "the moonlight ceremony"),
}

SPOTS: dict[str, SearchSpot] = {
    "under_bench": SearchSpot(
        "under_bench",
        "under a painted bench",
        "reach",
        "a tiny clink that seemed to roll out and vanish",
        "the child had dropped a coin there during the final laugh",
        "crowd",
    ),
    "ticket_box": SearchSpot(
        "ticket_box",
        "inside an old ticket box",
        "key",
        "a small metal click, then silence",
        "the key had slipped before the last drumbeat",
        "locked",
    ),
    "crowd_queue": SearchSpot(
        "crowd_queue",
        "in a crowded queue",
        "ask",
        "the soft voice saying, \"ask the old man in blue\"",
        "a shout was interrupted by a whistle, and nobody noticed the object fall",
        "busy",
    ),
    "dock_rope": SearchSpot(
        "dock_rope",
        "near the dock rope",
        "net",
        "a wet thud and a rope-creak",
        "the rope had snapped loose and tugged backward in a gust",
        "water",
    ),
    "river_boat": SearchSpot(
        "river_boat",
        "under the riverboat seat",
        "reach",
        "a hollow knock from inside the dark seat",
        "the child swayed and slid a little at the last turn",
        "water",
    ),
    "dock_cradle": SearchSpot(
        "dock_cradle",
        "inside the dock cradle",
        "ask",
        "a dockworker said, \"Look by the blue crate mark\"",
        "the worker had seen the bundle drop near the crate",
        "water",
    ),
    "orchard_tree": SearchSpot(
        "orchard_tree",
        "up in the orchard tree hollow",
        "height",
        "a soft rustle from above",
        "the branch shook when the whistle blew from below",
        "height",
    ),
    "flower_wall": SearchSpot(
        "flower_wall",
        "behind a flower wall",
        "dark",
        "a faint warm glow peeking from the leaves",
        "the child followed the glow because a lantern had flickered there",
        "dark",
    ),
    "hay_silo": SearchSpot(
        "hay_silo",
        "inside the hay silo",
        "reach",
        "a thump on soft hay",
        "the child stumbled while stepping around stacked bales",
        "dry",
    ),
    "clock_door": SearchSpot(
        "clock_door",
        "behind the station clock door",
        "key",
        "a click like a key turning for one moment",
        "the door opened when the right key was turned",
        "locked",
    ),
    "locker_box": SearchSpot(
        "locker_box",
        "inside a station locker",
        "key",
        "a key ring rattled at the bottom shelf",
        "a locker had swallowed the object after the stampede",
        "locked",
    ),
    "tower_steps": SearchSpot(
        "tower_steps",
        "inside the tower steps",
        "dark",
        "a warm breath of air from above the stairs",
        "the object slipped behind the wall while looking for the top bell",
        "dark",
    ),
}

METHODS: dict[str, SearchMethod] = {
    "careful_reach": SearchMethod(
        "careful_reach",
        "a careful reach",
        "slid a hand slowly inside the opening",
        ("reach",),
    ),
    "ask_helper": SearchMethod(
        "ask_helper",
        "help from a kind helper",
        "asked a person they trusted to check nearby places",
        ("ask",),
    ),
    "net_scoop": SearchMethod(
        "net_scoop",
        "a long-handled scoop net",
        "scooped with a net without leaning too far",
        ("net",),
    ),
    "borrowed_key": SearchMethod(
        "borrowed_key",
        "a borrowed key",
        "asked for the right key and opened the right box",
        ("key",),
    ),
    "steady_ladder": SearchMethod(
        "steady_ladder",
        "a steady ladder held by an adult",
        "climbed with support and reached up slowly",
        ("height",),
    ),
    "small_lantern": SearchMethod(
        "small_lantern",
        "a small lantern",
        "lit a lantern and searched the shadowy corners",
        ("dark",),
    ),
    "daring_dash": SearchMethod(
        "daring_dash",
        "a daring dash through the scene",
        "ran while reaching and looking at every face",
        ("ask", "reach", "key", "dark", "height", "net"),
        unsafe=True,
    ),
}

HERO_NAMES = {
    "girl": ("Mara", "Lena", "Ivy", "Rosa", "Noor"),
    "boy": ("Ike", "Max", "Leo", "Theo", "Noah"),
}

HELPERS = ("grandmother", "uncle", "park_guard", "mother", "bus_driver")


def pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def valid_combo(district: str, lost_object: str, spot: str, method: str) -> bool:
    if district not in DISTRICTS or lost_object not in LOST_OBJECTS or spot not in SPOTS or method not in METHODS:
        return False
    d = DISTRICTS[district]
    lo = LOST_OBJECTS[lost_object]
    s = SPOTS[spot]
    m = METHODS[method]
    if m.unsafe:
        return False
    if spot not in d.supported_spots:
        return False
    if s.need not in m.solves:
        return False
    if s.hazard == "water" and not lo.water_safe:
        return False
    return True


def explain_rejection(district: str, lost_object: str, spot: str, method: str) -> str:
    if district not in DISTRICTS:
        return f"No story: unknown district {district!r}."
    if lost_object not in LOST_OBJECTS:
        return f"No story: unknown lost object {lost_object!r}."
    if spot not in SPOTS:
        return f"No story: unknown search spot {spot!r}."
    if method not in METHODS:
        return f"No story: unknown method {method!r}."
    if METHODS[method].unsafe:
        return "No story: a dash is unsafe here; search needs calm and method."
    if spot not in DISTRICTS[district].supported_spots:
        return f"No story: {SPOTS[spot].phrase} does not exist in {DISTRICTS[district].phrase}."
    if SPOTS[spot].need not in METHODS[method].solves:
        return f"No story: {METHODS[method].phrase} does not match a {SPOTS[spot].need} search for {SPOTS[spot].phrase}."
    if SPOTS[spot].hazard == "water" and not LOST_OBJECTS[lost_object].water_safe:
        return f"No story: a {LOST_OBJECTS[lost_object].material} object would be ruined in water."
    return "No story: this setup is not reasonable."


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for district in DISTRICTS:
        for lost_object in LOST_OBJECTS:
            for spot in SPOTS:
                for method in METHODS:
                    if valid_combo(district, lost_object, spot, method):
                        out.append((district, lost_object, spot, method))
    return out


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.district, params.lost_object, params.spot, params.method):
        raise StoryError(explain_rejection(params.district, params.lost_object, params.spot, params.method))
    return World(
        params=params,
        district=DISTRICTS[params.district],
        lost_object=LOST_OBJECTS[params.lost_object],
        spot=SPOTS[params.spot],
        method=METHODS[params.method],
        entities={},
    )


def _rule_missing(world: World) -> None:
    hero = world.entities["Hero"]
    lost = world.entities["Object"]
    hero.add_meme("worry", 1.2)
    hero.add_meme("focus", 0.8)
    lost.tags["status"] = "missing"
    world.facts["problem"] = f"lost {world.lost_object.phrase} at {world.district.phrase}"
    world.facts["clue"] = world.spot.clue
    world.facts["flashback"] = world.spot.flashback
    world.fired.append("missing_object")


def _rule_search(world: World) -> None:
    hero = world.entities["Hero"]
    world.entities["District"].add_meter("traffic", 0.7)
    world.facts["atmosphere"] = world.district.atmosphere
    hero.add_meme("curiosity", 0.9)
    world.facts["need"] = world.spot.need
    world.fired.append("spot_investigation")


def _rule_safe_found(world: World) -> None:
    hero = world.entities["Hero"]
    obj = world.entities["Object"]
    helper = world.entities["Helper"]
    hero.add_meme("confidence", 1.0)
    hero.add_meme("relief", 1.2)
    obj.tags["status"] = "found"
    obj.tags["found_at"] = world.spot.key
    helper.add_meme("helpfulness", 0.8)
    world.facts["method"] = world.method.phrase
    world.facts["found_by"] = world.params.helper
    world.fired.append("safe_found")


def _rule_hazard(world: World) -> None:
    if world.spot.hazard == "locked":
        world.facts["hazard_warning"] = "a locked part needed patience and permission"
    elif world.spot.hazard == "height":
        world.facts["hazard_warning"] = "height can be dangerous without support"
    elif world.spot.hazard == "water":
        world.facts["hazard_warning"] = "water can pull a loose object out of reach"
    elif world.spot.hazard == "dark":
        world.facts["hazard_warning"] = "dark corners hide where small things can land"
    else:
        world.facts["hazard_warning"] = "crowds and movement can hide a small object"


def apply_rules(world: World) -> None:
    world.entities["Hero"] = Entity(world.params.hero, "child", {"mood": "worried"})
    world.entities["Object"] = Entity("festival item", "artifact", {"material": world.lost_object.material})
    world.entities["Spot"] = Entity(world.spot.key, "place", {"clue": world.spot.clue})
    world.entities["District"] = Entity(world.district.key, "place", {"atmosphere": world.district.atmosphere})
    world.entities["Helper"] = Entity(world.params.helper, "person", {"role": "support"})
    _rule_missing(world)
    _rule_search(world)
    _rule_safe_found(world)
    _rule_hazard(world)


def predict_risk(world: World) -> str:
    if world.spot.hazard == "water":
        return "Water can make reaching and lifting dangerous"
    if world.spot.hazard == "locked":
        return "Locked spots need the right access and calm"
    if world.spot.hazard == "height":
        return "A child could fall without support"
    if world.spot.hazard == "dark":
        return "Dark places can hide the object and make movement uncertain"
    return "Crowds can make a child bump into moving objects"


def need_word(need: str) -> str:
    return {"ask": "helper", "height": "high-place", "dark": "dark-place"}.get(need, need)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    apply_rules(world)
    helper = params.helper.replace("_", " ").title()
    _, possessive, _ = pronouns(params.gender)

    story = [
        f"{params.hero} walked through {world.district.phrase} during the festival, holding {possessive} {world.lost_object.phrase}.",
        f"When the music shifted and the whistles blew, the {world.lost_object.phrase} was gone. {params.hero} heard only {world.spot.clue} in memory, and {params.hero.split()[0] if ' ' in params.hero else params.hero} stood very still.",
    ]

    helping = pronouns(params.gender)[2]
    story.append(
        f'{params.hero} breathed deeply and said, "{helper}, we will find it before the evening ends." '
        f"{helper} nodded and said the clue could be read backward: {world.spot.flashback}."
    )

    story.append(
        f"They chose the right method: {world.method.phrase}. {params.hero} {world.method.action}. "
        f"{predict_risk(world)}. At last, {params.hero.split()[0] if ' ' in params.hero else params.hero}'s {world.lost_object.phrase} was waiting {world.spot.phrase}."
    )

    end = (
        f"{params.hero} held {possessive} {world.lost_object.phrase} against {possessive} heart and laughed when the festival lights came back into focus. "
        f"The mystery taught {helping} to pause, ask for help, and match the right method to the right place."
    )
    story.append(end)
    world.story = "\n\n".join(story)
    sample = StorySample(
        params=params,
        story=world.story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a mystery story using the words "map", "whistle", and "lantern".',
        f"Create a festival problem-solving story where {world.params.hero} loses {world.lost_object.phrase}.",
        f"Explain how {world.params.hero} found the item with {world.method.phrase} in {world.district.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero_obj = world.params.hero
    return [
        QAItem("What was lost?", f"The story says {hero_obj} lost {world.lost_object.phrase}. That object matters because the whole search begins when the festival noise hides where it went."),
        QAItem("Where did the clue point?", f"The clue was {world.spot.clue}. That pointed to the area described as {world.spot.phrase}."),
        QAItem("Why was a careful method needed?", f"Because the place needed a {need_word(world.spot.need)} approach and had a {world.spot.hazard} hazard. Running a rushed method could make the search dangerous."),
        QAItem("How was the object found?", f"They used {world.method.phrase}, because it matched the {need_word(world.spot.need)} search in the area described as {world.spot.phrase}. The recovery follows the clue trail instead of arriving by chance."),
        QAItem("What lesson did the festival mystery teach?", "It showed that listening to clues, using the right tool, and asking for help can solve a problem safely and calmly. The ending proves the lesson because the lost object comes back without anyone rushing into the hazard."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    risk = predict_risk(world)
    qas = [
        QAItem("Why can crowded places make searches harder?", "Crowds make it easy to lose sight of small details. Calm, slower steps keep the search safer and clearer."),
        QAItem("Why is asking a helper useful?", "Helpers can remember details and physically assist in places children should not reach alone."),
        QAItem("Why does this story stress matching method to place?", f"Different places need different actions. Here, the place required a {need_word(world.spot.need)} approach, and {world.method.phrase} was chosen."),
    ]
    if world.spot.hazard == "water":
        qas.append(QAItem("Why are water spots treated carefully?", "Water moves objects and footing fast, so safe retrieval is important to avoid loss or harm."))
    if world.lost_object.material in ("paper", "felt", "glass"):
        qas.append(QAItem("What could happen to fragile materials near water?", f"A {world.lost_object.material} item can weaken, lose shape, or break if it gets soaked."))
    if world.spot.need == "key":
        qas.append(QAItem("What does the key clue imply?", "Some places are closed or locked, so safe opening matters more than forcing."))
    if world.spot.need == "height":
        qas.append(QAItem("Why is adult support needed for height checks?", "Height can cause falls. Support keeps children steady."))
    if world.spot.need == "dark":
        qas.append(QAItem("Why does a lantern help in dark areas?", "A lantern gives focused light so the searcher can see where small things hid."))
    return qas


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate festival-search storyworld samples.")
    parser.add_argument("--district", choices=sorted(DISTRICTS))
    parser.add_argument("--lost-object", dest="lost_object", choices=sorted(LOST_OBJECTS))
    parser.add_argument("--spot", choices=sorted(SPOTS))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HERO_NAMES))
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def _matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str]]:
    combos = []
    for combo in valid_combos():
        district, lost_object, spot, method = combo
        if args.district and args.district != district:
            continue
        if args.lost_object and args.lost_object != lost_object:
            continue
        if args.spot and args.spot != spot:
            continue
        if args.method and args.method != method:
            continue
        combos.append(combo)
    return combos


def _make_params(args: argparse.Namespace, rng: random.Random, combo: tuple[str, str, str, str], seed: int | None) -> StoryParams:
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or rng.choice(HERO_NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    district, lost_object, spot, method = combo
    return StoryParams(district, lost_object, spot, method, hero, gender, helper, seed)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = _matching_combos(args)
    if not combos:
        raise StoryError(explain_rejection(args.district or "fairground", args.lost_object or "paper_note", args.spot or "under_bench", args.method or "careful_reach"))
    seed = getattr(rng, "story_seed", None)
    return _make_params(args, rng, rng.choice(combos), seed)


def format_qa(sample: StorySample) -> str:
    lines = ["", "== (1) Generation prompts -- asks that would produce this story =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story details ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child-level checks ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print(format_qa(sample))


def _json_dump(samples: list[StorySample]) -> None:
    if len(samples) == 1:
        print(samples[0].to_json())
    else:
        print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))


ASP_RULES = r"""
water_bad(A,S) :- lost_object(A), hazard(S,water), not water_safe(A).

combo(D,A,S,M) :-
    district(D),
    lost_object(A),
    spot(S),
    method(M),
    district_spot(D,S),
    need(S,N),
    solves(M,N),
    not unsafe(M),
    not water_bad(A,S).

ok :- chosen(D,A,S,M), combo(D,A,S,M).

#show combo/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    import asp

    rows: list[str] = []
    for key, district in DISTRICTS.items():
        rows.append(asp.fact("district", key))
        for spot in district.supported_spots:
            rows.append(asp.fact("district_spot", key, spot))
    for key, obj in LOST_OBJECTS.items():
        rows.append(asp.fact("lost_object", key))
        if obj.water_safe:
            rows.append(asp.fact("water_safe", key))
    for key, spot in SPOTS.items():
        rows.append(asp.fact("spot", key))
        rows.append(asp.fact("need", key, spot.need))
        rows.append(asp.fact("hazard", key, spot.hazard))
    for key, method in METHODS.items():
        rows.append(asp.fact("method", key))
        for need in method.solves:
            rows.append(asp.fact("solves", key, need))
        if method.unsafe:
            rows.append(asp.fact("unsafe", key))
    if params is not None:
        rows.append(asp.fact("chosen", params.district, params.lost_object, params.spot, params.method))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str]]:
    import asp

    combos: set[tuple[str, str, str, str]] = set()
    for model in asp.solve(asp_program(), models=0):
        combos.update(asp.atoms(model, "combo"))
    return combos


def asp_verify(params: StoryParams) -> bool:
    import asp

    return bool(asp.atoms(asp.one_model(asp_program(params)), "ok"))


def verify() -> str:
    py = set(valid_combos())
    logic = asp_valid_combos()
    if py != logic:
        raise StoryError(f"ASP/Python mismatch. only_python={sorted(py - logic)} only_asp={sorted(logic - py)}")
    for district, lost_object, spot, method in sorted(py):
        params = StoryParams(district, lost_object, spot, method, "Mara", "girl", "mother", 0)
        if not asp_verify(params):
            raise StoryError(f"ASP rejected Python-valid combo: {(district, lost_object, spot, method)}")
    return f"OK: clingo gate matches valid_combos() ({len(py)} combos)."


def _samples_for_all(args: argparse.Namespace) -> list[StorySample]:
    samples = []
    combos = valid_combos()
    for i, combo in enumerate(combos):
        seed = (args.seed if args.seed is not None else 9000) + i
        rng = random.Random(seed)
        rng.story_seed = seed
        sample = generate(_make_params(args, rng, combo, seed))
        samples.append(sample)
    return samples


def _samples_for_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples = []
    seen: set[str] = set()
    i = 0
    target = max(1, args.n)
    while len(samples) < target and i < target * 25:
        story_seed = base_seed + i
        rng = random.Random(story_seed)
        rng.story_seed = story_seed
        sample = generate(resolve_params(args, rng))
        if sample.story not in seen:
            seen.add(sample.story)
            samples.append(sample)
        i += 1
    return samples


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
            for combo in sorted(asp_valid_combos()):
                print("\t".join(combo))
            return 0

        samples = _samples_for_all(args) if args.all else _samples_for_n(args)
        if args.json:
            _json_dump(samples)
            return 0
        for i, sample in enumerate(samples):
            header = ""
            if args.all:
                header = f"### {sample.params.hero}: {sample.params.lost_object} in {sample.params.district} via {sample.params.spot}"
            elif len(samples) > 1:
                header = f"### variant {i + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if i != len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
