#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/only_tread_like_hotel_lobby_lesson_learned.py
===============================================================================

A tiny standalone story world for a comedy-leaning hotel-lobby lesson tale.

Seed idea:
- Setting: hotel lobby
- Feature: Lesson Learned
- Style: Comedy
- Seed words: only, tread, like

Premise rebuilt as a world model:
A child treats the hotel lobby like a stage, tiptoeing through the polished floor
and showing off silly fancy steps. The polished marble, brass poles, and luggage
cart make the scene funny, but the child gets a slapstick reminder that the lobby
is shared space: slow feet, indoor voices, and watching for other guests keeps
everyone safe and calm.

The script follows the shared Storyweavers contract:
- stdlib only
- self-contained world model with meters and memes
- StoryParams, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- Python reasonableness gate plus inline ASP twin
- QA derived from world state, not by parsing rendered English
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"risk": 0.0, "mess": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "embarrassment": 0.0, "lesson": 0.0, "calm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    floor: str
    props: list[str]
    tone: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Move:
    id: str
    label: str
    phrase: str
    style: str
    risk: int
    allowed: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    apply: Callable[["World"], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child or child.meters["risk"] < THRESHOLD:
        return out
    sig = ("slip", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["embarrassment"] += 1
    world.get("lobby").meters["risk"] += 1
    out.append("__slip__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    adult = world.entities.get("adult")
    if not child or not adult:
        return out
    if child.memes["lesson"] < THRESHOLD:
        return out
    sig = ("calm", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    adult.memes["calm"] += 1
    child.memes["joy"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("slip", _r_slip), Rule("calm", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable_combo(move: Move, setting: Setting) -> bool:
    return move.allowed and setting.place == "hotel lobby"


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, mid) for sid in SETTINGS for mid in MOVES if reasonable_combo(MOVES[mid], SETTINGS[sid])]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, mv in MOVES.items():
        lines.append(asp.fact("move", mid))
        if mv.allowed:
            lines.append(asp.fact("allowed", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M) :- setting(S), move(M), allowed(M).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
@dataclass
class StoryParams:
    setting: str
    move: str
    child: str
    child_gender: str
    adult: str
    adult_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SETTINGS = {
    "lobby": Setting(
        "lobby",
        "the hotel lobby",
        "the marble floor",
        ["a brass lamp", "a velvet rope", "a luggage cart", "a fishbowl"],
        "bright and echoey",
    )
}

MOVES = {
    "run": Move("run", "run", "ran like a wind-up toy", "noisy", 2, True, {"only", "tread", "like"}),
    "tiptoe": Move("tiptoe", "tiptoe", "tread like a mouse", "sneaky", 1, True, {"only", "tread", "like"}),
    "dance": Move("dance", "dance", "tread like a tiny show-off", "comic", 3, True, {"only", "tread", "like"}),
}

NAMES_GIRL = ["Mia", "Lily", "Zoe", "Ava", "Nora"]
NAMES_BOY = ["Ben", "Theo", "Leo", "Max", "Sam"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Hotel-lobby comedy storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def explain_rejection() -> str:
    return "(No story: this hotel-lobby move is too unreasonable for the lesson.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting != "lobby":
        raise StoryError(explain_rejection())
    combos = valid_combos()
    if args.move:
        combos = [c for c in combos if c[1] == args.move]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, move = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(setting, move, name, gender, adult, "mother" if adult == "mother" else "father")


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity("child", "character", params.child_gender, params.child, "child"))
    adult = world.add(Entity("adult", "character", params.adult_gender, params.adult, "adult"))
    lobby = world.add(Entity("lobby", "place", "lobby", "lobby"))
    move = MOVES[params.move]

    world.say(
        f"In the hotel lobby, {child.id} stared at the shiny floor and decided it was "
        f"the only place worth performing."
    )
    world.say(
        f"{child.id} wanted to {move.label} and {move.style} through the lobby, "
        f"like a tiny star with very serious shoes."
    )
    child.meters["risk"] += float(move.risk)

    world.para()
    world.say(
        f"{adult.id} noticed the fancy walk and gently said, "
        f"\"Slow tread, please. Hotels are for guests, not parades.\""
    )
    world.say(
        f"{child.id} tried to keep going, because the marble looked like a stage and "
        f"the lobby made every step sound like a drum."
    )

    if move.risk >= 3:
        child.meters["risk"] += 1
    propagate(world, narrate=False)

    world.para()
    if child.memes["embarrassment"] >= THRESHOLD:
        world.say(
            f"Then {child.id} gave a tiny cartoon slip, caught {child.pronoun('object')}self "
            f"on the velvet rope, and giggled instead of crying."
        )
        world.say(
            f"{adult.id} steadied {child.pronoun('object')} and pointed to the mat by the desk. "
            f"\"That is the proper runway,\" {adult.pronoun()} said."
        )
    else:
        world.say(
            f"{child.id} froze, took one careful step, and learned that the lobby was "
            f"not a playground after all."
        )

    child.memes["lesson"] += 1
    world.say(
        f"{child.id} nodded, switched to a careful walk, and stayed only on the mat. "
        f"The lobby looked calmer at once, as if the building had stopped holding its breath."
    )
    propagate(world)

    world.facts.update(child=child, adult=adult, lobby=lobby, move=move, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c, a, m = f["child"], f["adult"], f["move"]
    return [
        f'Write a comedy story for a young child set in a hotel lobby that includes the words "only", "tread", and "like".',
        f"Tell a funny lesson-learned story where {c.id} tries to {m.label} in a hotel lobby, then learns to move carefully after {a.id} speaks up.",
        f"Write a short humorous story about a child in a hotel lobby who wants to tread like a show-off, but ends by walking the proper way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, a, m = f["child"], f["adult"], f["move"]
    ans1 = (
        f"It is about {c.id} in a hotel lobby with {a.id}. {c.id} was trying to {m.label}, "
        f"and the shiny floor made the scene funny."
    )
    ans2 = (
        f"{c.id} learned to slow down and stay on the mat. That worked because the lobby is a shared place, "
        f"so careful feet keep everyone from slipping."
    )
    ans3 = (
        f"{a.id} warned that the hotel lobby is for guests, not parades, and that {c.id} should tread carefully. "
        f"The lesson was to move like a guest and not like a stage star."
    )
    return [
        QAItem("Who is the story about?", ans1),
        QAItem("What lesson did the child learn?", ans2),
        QAItem("What did the adult say about the lobby?", ans3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a hotel lobby?", "A hotel lobby is the shared front room of a hotel where guests check in, wait, and walk through."),
        QAItem("Why can a shiny floor be tricky?", "A shiny floor can be slippery, so careful walking helps people stay balanced."),
        QAItem("What should you do in a quiet indoor place?", "Use slow feet and indoor voices so everyone can relax and move safely."),
    ]


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
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:6} ({e.type}) meters={e.meters} memes={e.memes} role={e.role}")
    return "\n".join(lines)


CURATED = [
    StoryParams("lobby", "tiptoe", "Mia", "girl", "mother", "mother"),
    StoryParams("lobby", "dance", "Ben", "boy", "father", "father"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def asp_sensible() -> list[str]:
    return sorted(MOVES)


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH in ASP parity")
        print("python only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))
    else:
        print(f"OK: ASP parity matches ({len(py)} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible moves:", ", ".join(asp_sensible()))
        for s, m in asp_valid_combos():
            print(s, m)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
