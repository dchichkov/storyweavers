#!/usr/bin/env python3
"""
storyworlds/worlds/brussel_suspense_bedtime_story.py
=====================================================

A standalone story world sketch for a bedtime suspense tale: a child hears a
creepy little sound at bedtime, worries about a missing tiny thing, and learns
that a safe check-and-help routine can turn suspense into rest.

The seed word "brussel" appears as part of the child's tiny plush friend, a
brussel sprout toy that matters at bedtime.

The world is small on purpose:
- one child
- one bedtime worry
- one helper
- one hiding place
- one safe method

It still models changing state with physical meters and emotional memes, uses a
Python reasonableness gate, includes an inline ASP twin, and produces three QA
sets from world state rather than from rendered English.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden_in: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    darkness: str
    soundscape: str
    affordance: str


@dataclass
class Worry:
    id: str
    label: str
    hidden_phrase: str
    clue: str
    risk_phrase: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    action: str
    result: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "bedroom": Setting(
        id="bedroom",
        place="the bedroom",
        darkness="soft and deep",
        soundscape="the hall hummed with house-night sounds",
        affordance="bedtime",
    ),
    "hallway": Setting(
        id="hallway",
        place="the hallway",
        darkness="long and narrow",
        soundscape="the floorboards gave tiny sleepy creaks",
        affordance="bedtime",
    ),
    "nursery": Setting(
        id="nursery",
        place="the nursery",
        darkness="gentle and blue",
        soundscape="the window tapped with a quiet night breeze",
        affordance="bedtime",
    ),
}

WORRIES = {
    "shadow": Worry(
        id="shadow",
        label="a shadow",
        hidden_phrase="under the bed",
        clue="a dark shape that looked bigger than it was",
        risk_phrase="the shadow might be a monster",
        zone="under_bed",
        tags={"shadow", "dark"},
    ),
    "missing_brussel": Worry(
        id="missing_brussel",
        label="the brussel plush",
        hidden_phrase="inside the toy basket",
        clue="one tiny green ear was sticking out",
        risk_phrase="the brussel plush was lost before bedtime",
        zone="basket",
        tags={"brussel", "toy"},
    ),
    "clatter": Worry(
        id="clatter",
        label="a clatter",
        hidden_phrase="behind the curtain",
        clue="something had tapped the wall once and then stopped",
        risk_phrase="something noisy might still be awake",
        zone="curtain",
        tags={"sound", "curtain"},
    ),
    "door_squeak": Worry(
        id="door_squeak",
        label="the closet door",
        hidden_phrase="in the closet",
        clue="the closet door had shifted just a little",
        risk_phrase="the closet might hide something scary",
        zone="closet",
        tags={"closet", "door"},
    ),
}

METHODS = {
    "peek_with_light": Method(
        id="peek_with_light",
        label="peek with the night-light",
        action="hold the night-light up and look carefully",
        result="the room looked smaller and safer",
        power=3,
        tags={"light", "careful"},
    ),
    "ask_parent": Method(
        id="ask_parent",
        label="ask a parent",
        action="call for a parent and wait close by",
        result="the worry stopped feeling so big",
        power=4,
        tags={"help", "parent"},
    ),
    "check_basket": Method(
        id="check_basket",
        label="check the toy basket",
        action="lift the blanket off the basket and look inside",
        result="the missing thing could be found right away",
        power=2,
        tags={"basket", "toy"},
    ),
    "open_door_slowly": Method(
        id="open_door_slowly",
        label="open the door slowly",
        action="turn the handle a little and peek through the crack",
        result="the dark place gave up its secret",
        power=3,
        tags={"door", "careful"},
    ),
}

COMFORTS = {
    "night_light": Comfort(
        id="night_light",
        label="night-light",
        phrase="a small night-light",
        glow="glowed like a tiny moon",
        tags={"light"},
    ),
    "story_book": Comfort(
        id="story_book",
        label="story book",
        phrase="a bedtime story book",
        glow="waited with its pages tucked flat",
        tags={"book"},
    ),
    "blanket": Comfort(
        id="blanket",
        label="blanket",
        phrase="a soft blanket",
        glow="made the bed look cozy and safe",
        tags={"blanket"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Ella", "Rose", "Ava"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Milo", "Theo", "Eli"]
HELPER_NAMES = ["Mom", "Dad"]
TRAITS = ["sleepy", "curious", "careful", "brave", "quiet"]


@dataclass
class StoryParams:
    setting: str = "bedroom"
    worry: str = "shadow"
    method: str = "peek_with_light"
    comfort: str = "night_light"
    name: str = "Mia"
    gender: str = "girl"
    helper: str = "Mom"
    trait: str = "curious"
    seed: Optional[int] = None


def _build_person_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting in SETTINGS:
        for worry_id, worry in WORRIES.items():
            for method_id, method in METHODS.items():
                for comfort_id, comfort in COMFORTS.items():
                    if "brussel" in worry.tags and "light" in comfort.tags:
                        combos.append((setting, worry_id, method_id, comfort_id))
                    elif "dark" in worry.tags and method_id in {"peek_with_light", "ask_parent", "open_door_slowly"}:
                        combos.append((setting, worry_id, method_id, comfort_id))
    # remove weak duplicate-ish cases by requiring each method to have a compatible worry
    out = []
    for combo in combos:
        setting, worry_id, method_id, comfort_id = combo
        worry = WORRIES[worry_id]
        method = METHODS[method_id]
        comfort = COMFORTS[comfort_id]
        if worry_id == "missing_brussel" and comfort_id == "night_light":
            out.append(combo)
        elif worry_id in {"shadow", "door_squeak", "clatter"} and method.power >= 2:
            out.append(combo)
    uniq = []
    seen = set()
    for c in out:
        if c not in seen:
            uniq.append(c)
            seen.add(c)
    return uniq


def _choose_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str, str]:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.worry is None or c[1] == args.worry)
              and (args.method is None or c[2] == args.method)
              and (args.comfort is None or c[3] == args.comfort)]
    if not combos:
        raise StoryError("(No valid bedtime-suspense combination matches the given options.)")
    return rng.choice(sorted(combos))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting, worry, method, comfort = _choose_combo(args, rng)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _build_person_name(rng, gender)
    helper = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        worry=worry,
        method=method,
        comfort=comfort,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def _make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    worry = WORRIES[params.worry]
    method = METHODS[params.method]
    comfort = COMFORTS[params.comfort]
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    helper_type = "mother" if params.helper == "Mom" else "father"
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=params.helper))
    worry_ent = world.add(Entity(id="worry", type="thing", label=worry.label, phrase=worry.hidden_phrase))
    comfort_ent = world.add(Entity(id="comfort", type="thing", label=comfort.label, phrase=comfort.phrase))
    method_ent = world.add(Entity(id="method", type="thing", label=method.label, phrase=method.action))
    child.owner = child.id
    comfort_ent.owner = child.id
    comfort_ent.caretaker = helper.id
    world.facts = {
        "child": child,
        "helper": helper,
        "worry_cfg": worry,
        "method_cfg": method,
        "comfort_cfg": comfort,
        "worry_ent": worry_ent,
        "comfort_ent": comfort_ent,
        "method_ent": method_ent,
        "solved": False,
        "found": False,
    }
    return world


def _predict(world: World, params: StoryParams) -> bool:
    sim = world.copy()
    worry = sim.facts["worry_cfg"]
    method = sim.facts["method_cfg"]
    sim.facts["solved"] = method.power >= (3 if worry.id == "shadow" else 2)
    return bool(sim.facts["solved"])


def _resolve_worry(world: World) -> None:
    worry: Worry = world.facts["worry_cfg"]
    if world.facts["solved"]:
        sig = ("solved", worry.id)
        if sig in world.fired:
            return
        world.fired.add(sig)
        world.get("worry_ent").meters["gone"] += 1
        world.get("child").memes["relief"] += 1
        world.get("child").memes["courage"] += 1
    else:
        sig = ("unsolved", worry.id)
        if sig in world.fired:
            return
        world.fired.add(sig)
        world.get("child").memes["worry"] += 1


def _tell(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    worry: Worry = world.facts["worry_cfg"]
    method: Method = world.facts["method_cfg"]
    comfort: Comfort = world.facts["comfort_cfg"]
    setting = world.setting

    child.memes["sleepy"] += 1
    child.memes["suspense"] += 1
    world.say(f"It was bedtime in {setting.place}, and {setting.soundscape}.")
    world.say(f"{child.label} had {comfort.phrase}, and {comfort.glow}.")
    if worry.id == "missing_brussel":
        world.say(f"But the brussel plush was not where it should be.")
    else:
        world.say(f"But {worry.label} was {worry.hidden_phrase}.")
    world.say(f"The clue was simple: {worry.clue}.")
    world.para()
    world.say(f"{child.label} felt very still and listened to the dark.")
    if worry.id == "missing_brussel":
        world.say(f"The little brussel toy mattered a lot, and that made the room feel extra quiet.")
    world.say(f"Then {child.label} chose to {method.action}.")
    world.say(f"{helper.label} stayed close and said to take one slow look at a time.")

    if world.facts["solved"]:
        world.para()
        if worry.id == "missing_brussel":
            world.say(f"Under the basket, the brussel plush was found at last, with one tiny green ear sticking out.")
        elif worry.zone == "under_bed":
            world.say(f"Under the bed, the dark shape was only a piled-up blanket, not a monster at all.")
        elif worry.zone == "closet":
            world.say(f"The closet was only a little messy, and the noise had been a loose shoe tapping the wall.")
        else:
            world.say(f"The room gave up its secret, and the worry turned small and plain.")
        world.say(f"{method.result.capitalize()}.")
        world.say(f"{child.label} smiled, hugged {world.get('comfort').label}, and the bed looked cozy again.")
    else:
        world.para()
        world.say(f"But the worry stayed big, so {helper.label} helped {child.label} back to bed.")
        world.say(f"Together they shut the dark place gently and kept the comfort close until sleep came.")
        world.say(f"The room was still quiet, but not quite safe enough to feel easy.")

    _resolve_worry(world)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.worry not in WORRIES:
        raise StoryError("Unknown worry.")
    if params.method not in METHODS:
        raise StoryError("Unknown method.")
    if params.comfort not in COMFORTS:
        raise StoryError("Unknown comfort.")
    world = _make_world(params)
    _predict(world, params)
    _tell(world)
    world.facts["params"] = params
    world.facts["ending"] = "solved" if world.facts["solved"] else "unsolved"
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]
    worry: Worry = world.facts["worry_cfg"]
    method: Method = world.facts["method_cfg"]
    comfort: Comfort = world.facts["comfort_cfg"]
    return [
        f"Write a bedtime story for a small child named {child.label} that includes the word 'brussel' and a tiny suspenseful worry.",
        f"Tell a gentle suspense story where {child.label} hears something strange and uses {method.label} to feel safe again.",
        f"Write a bedtime story with a soft scare, a careful helper, and {comfort.label} that ends with the worry becoming small.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    worry: Worry = world.facts["worry_cfg"]
    method: Method = world.facts["method_cfg"]
    comfort: Comfort = world.facts["comfort_cfg"]
    ending = world.facts["ending"]
    qs: list[QAItem] = [
        QAItem(
            question=f"What kind of bedtime feeling did {child.label} have at the start?",
            answer=f"{child.label} felt suspenseful and a little worried, because bedtime was quiet and {worry.clue}. That kind of quiet can make a small sound feel much bigger than it is.",
        ),
        QAItem(
            question=f"What did {child.label} do to check the worry?",
            answer=f"{child.label} chose to {method.action}. {helper.label} stayed close, so the check felt careful instead of scary.",
        ),
    ]
    if worry.id == "missing_brussel":
        qs.append(QAItem(
            question=f"What was special about the missing thing in the story?",
            answer="It was the brussel plush, a tiny green toy that mattered enough to make bedtime feel suspenseful. Finding it made the room feel safe again.",
        ))
    if ending == "solved":
        qs.append(QAItem(
            question=f"What changed at the end after the check?",
            answer=f"The worry stopped being huge, and the room felt cozy again. {child.label} could rest with {comfort.label}, because the hidden thing was found or explained.",
        ))
    else:
        qs.append(QAItem(
            question=f"Why did the story end with the worry still feeling big?",
            answer=f"The check did not solve it right away, so {helper.label} helped {child.label} back to bed. The room stayed quiet, but the worry needed a little more time to settle.",
        ))
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    worry: Worry = world.facts["worry_cfg"]
    method: Method = world.facts["method_cfg"]
    comfort: Comfort = world.facts["comfort_cfg"]
    out = [
        QAItem(
            question="What does a night-light do?",
            answer="A night-light gives a soft glow so a room is not totally dark. That makes bedtime feel less scary.",
        ),
        QAItem(
            question="Why can a careful check help at bedtime?",
            answer="A careful check helps because many scary-looking things are only ordinary things in the dark. Looking slowly can turn a big worry into a small one.",
        ),
    ]
    if "brussel" in worry.tags or comfort.id == "night_light":
        out.append(QAItem(
            question="What is the brussel word doing in this story?",
            answer="It names the tiny brussel plush, a little toy that matters to the child. Because it is small and special, its absence can feel like a big bedtime mystery.",
        ))
    if "light" in method.tags:
        out.append(QAItem(
            question="Why is light helpful when you are unsure about a dark corner?",
            answer="Light helps you see what is really there. Once you can see clearly, the suspense usually gets much smaller.",
        ))
    if comfort.id == "blanket":
        out.append(QAItem(
            question="What is a blanket for at bedtime?",
            answer="A blanket keeps you warm and cozy. Feeling cozy can help your body relax and get ready to sleep.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    lines.append(f"  ending: {world.facts.get('ending')}")
    return "\n".join(lines)


ASP_RULES = r"""
solvable(W, M, C) :- worry(W), method(M), comfort(C), compatible(W, M, C).

compatible(missing_brussel, peek_with_light, night_light).
compatible(missing_brussel, ask_parent, night_light).
compatible(shadow, peek_with_light, night_light).
compatible(shadow, ask_parent, story_book).
compatible(door_squeak, open_door_slowly, night_light).
compatible(clatter, ask_parent, blanket).

#show solvable/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for wid in WORRIES:
        lines.append(asp.fact("worry", wid))
    for mid in METHODS:
        lines.append(asp.fact("method", mid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/3."))
    return sorted(set(asp.atoms(model, "solvable")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    rc = 0
    if py == clingo:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python combos.")
        print(" only in ASP:", sorted(clingo - py))
        print(" only in Python:", sorted(py - clingo))
    try:
        sample = generate(
            StoryParams(
                setting="bedroom",
                worry="missing_brussel",
                method="peek_with_light",
                comfort="night_light",
                name="Mia",
                gender="girl",
                helper="Mom",
                trait="curious",
            )
        )
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime suspense storyworld with 'brussel'.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--worry", choices=WORRIES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    _predict(world, params)
    _tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="bedroom", worry="missing_brussel", method="check_basket", comfort="night_light", name="Mia", gender="girl", helper="Mom", trait="curious"),
    StoryParams(setting="hallway", worry="shadow", method="peek_with_light", comfort="story_book", name="Leo", gender="boy", helper="Dad", trait="careful"),
    StoryParams(setting="nursery", worry="door_squeak", method="open_door_slowly", comfort="blanket", name="Nora", gender="girl", helper="Mom", trait="brave"),
    StoryParams(setting="bedroom", worry="clatter", method="ask_parent", comfort="night_light", name="Finn", gender="boy", helper="Dad", trait="quiet"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combo = _choose_combo(args, rng)
    setting, worry, method, comfort = combo
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _build_person_name(rng, gender)
    helper = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        worry=worry,
        method=method,
        comfort=comfort,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def _choose_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str, str]:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.worry is None or c[1] == args.worry)
              and (args.method is None or c[2] == args.method)
              and (args.comfort is None or c[3] == args.comfort)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    return rng.choice(sorted(combos))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solvable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.worry} with {p.method} in {p.setting}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
