#!/usr/bin/env python3
"""
A standalone story world for a juvenile pirate tale about bravery.

Seed tale:
---
A small pirate child wanted to prove they were brave. On a windy day, the child
and a kindly captain sailed to a rocky cove to look for a lost silver compass.
The child was scared by the dark cave and the loud waves, but the captain said
bravery did not mean never being afraid; it meant doing the helpful thing anyway.
The child took a deep breath, went into the cave with a lantern, and found the
compass. At the end, the child felt proud, the captain smiled, and the crew set
sail home with the compass shining in the lantern light.
---

This script models that premise as a small simulation:
- a juvenile pirate with meters and memes
- a risky cove visit
- a fear turn
- a bravery choice that resolves the search
- grounded story QA and world QA
- an inline ASP twin plus a Python reasonableness gate
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["fear", "bravery", "joy", "pride", "worry", "trust", "relief", "tiredness", "salt", "wind"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captainess"}
        male = {"boy", "father", "man", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the rocky cove"
    weather: str = "windy"
    affords: set[str] = field(default_factory=set)


@dataclass
class Objective:
    id: str
    noun: str
    phrase: str
    risky_place: str
    obstacle: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    covers: set[str]
    helps_against: set[str]
    phrase: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _r_fear(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes["fear"] < THRESHOLD:
            continue
        sig = ("fear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append(f"{e.id} felt their heart thump a little faster.")
    return out


def _r_bravery(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes["bravery"] < THRESHOLD:
            continue
        sig = ("brave", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] += 1
        e.memes["pride"] += 1
        out.append(f"{e.id} stood up straighter and kept going.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_fear, _r_bravery):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_story(params: "StoryParams") -> bool:
    if params.objective not in OBJECTIVES:
        return False
    if params.aid not in AIDS:
        return False
    obj = OBJECTIVES[params.objective]
    aid = AIDS[params.aid]
    return params.objective in VALID_OBJECTIVES and obj.obstacle in aid.helps_against and obj.risky_place == SETTINGS[params.setting].place


def explain_rejection(params: "StoryParams") -> str:
    obj = OBJECTIVES.get(params.objective)
    aid = AIDS.get(params.aid)
    if obj and aid:
        return f"(No story: {aid.label} does not help with {obj.obstacle}, so the brave turn would feel fake.)"
    return "(No story: the requested choices do not fit this pirate tale.)"


def predict_success(world: World, hero: Entity, objective: Objective, aid: Aid) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["fear"] += 1
    sim.get(hero.id).memes["bravery"] += 1
    return objective.obstacle in aid.helps_against


def introduce(world: World, hero: Entity, captain: Entity) -> None:
    world.say(
        f"{hero.id} was a juvenile pirate with a brave little grin and shaky knees when the waves got loud."
    )
    world.say(f"{hero.id} sailed with {captain.label_word}, who spoke softly and watched the sea carefully.")


def want(objective: Objective, hero: Entity, captain: Entity, world: World) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(
        f"{hero.id} wanted to find the {objective.noun}, because no one wanted the crew to lose such a useful thing."
    )


def arrive(world: World, setting: Setting, objective: Objective, hero: Entity, captain: Entity) -> None:
    world.say(
        f"One {setting.weather} day, {hero.id} and {captain.label_word} reached {setting.place}, where the rocks leaned close and the cave mouth looked dark."
    )
    world.say(
        f"The {objective.noun} was said to be somewhere inside, past the cold splash of the sea."
    )


def fear_turn(world: World, hero: Entity, objective: Objective) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} saw the black cave and gulped. The waves crashed, and {hero.pronoun('subject')} almost stepped back."
    )
    world.say(
        f'"I am scared," {hero.id} admitted, "but I still want to help."'
    )


def captain_teach(world: World, captain: Entity, hero: Entity, objective: Objective) -> None:
    captain.memes["trust"] += 1
    world.say(
        f'"Bravery does not mean never being afraid," {captain.label_word} said. "It means choosing the helpful thing anyway."'
    )


def take_aid(world: World, hero: Entity, aid: Aid) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} took the {aid.label} and a deep breath."
    )


def search_and_find(world: World, hero: Entity, objective: Objective, aid: Aid) -> None:
    if not predict_success(world, hero, objective, aid):
        raise StoryError(explain_rejection(world.facts["params"]))
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    hero.meters["tiredness"] += 1
    world.say(
        f"{hero.id} went into the cave with the {aid.label}, and the light chased the shadows away."
    )
    world.say(
        f"Under a wet stone, {hero.id} spotted the {objective.noun}. {objective.phrase.capitalize()}."
    )
    world.say(
        f"{hero.id} lifted it up and beamed, because the scary place had become a place of success."
    )


def return_home(world: World, hero: Entity, captain: Entity, objective: Objective, aid: Aid) -> None:
    hero.memes["relief"] += 1
    captain.memes["joy"] += 1
    world.say(
        f"Back on the ship, the crew cheered as the {objective.noun} shone in the {aid.label}'s glow."
    )
    world.say(
        f"{hero.id} felt proud all the way home, and the sea no longer felt so big."
    )


def tell(setting: Setting, objective: Objective, aid: Aid, hero_name: str, hero_type: str, captain_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    captain = world.add(Entity(id="Captain", kind="character", type=captain_type, label="the captain"))
    world.facts["params"] = StoryParams(setting=setting.id, objective=objective.id, aid=aid.id, name=hero_name, gender=hero_type, captain=captain_type)

    introduce(world, hero, captain)
    world.para()
    want(objective, hero, captain, world)
    arrive(world, setting, objective, hero, captain)
    fear_turn(world, hero, objective)
    captain_teach(world, captain, hero, objective)
    take_aid(world, hero, aid)
    search_and_find(world, hero, objective, aid)
    return_home(world, hero, captain, objective, aid)

    # unreachable
    return world


@dataclass
class SettingSpec:
    id: str
    place: str
    weather: str
    affords: set[str] = field(default_factory=set)


SETTINGS = {
    "cove": SettingSpec(id="cove", place="the rocky cove", weather="windy", affords={"compass", "map"}),
    "island": SettingSpec(id="island", place="the little island shore", weather="stormy", affords={"lantern", "compass"}),
    "harbor": SettingSpec(id="harbor", place="the moonlit harbor", weather="breezy", affords={"map", "flag"}),
}

OBJECTIVES = {
    "compass": Objective(
        id="compass",
        noun="silver compass",
        phrase="Its needle still pointed straight, even in the dark",
        risky_place="the rocky cove",
        obstacle="darkness",
        keyword="compass",
        tags={"sea", "treasure", "guide"},
    ),
    "map": Objective(
        id="map",
        noun="torn map",
        phrase="The torn edges fluttered like little sails",
        risky_place="the rocky cove",
        obstacle="wind",
        keyword="map",
        tags={"sea", "treasure", "guide"},
    ),
    "lantern": Objective(
        id="lantern",
        noun="little brass lantern",
        phrase="Its warm light made a brave path on the stones",
        risky_place="the little island shore",
        obstacle="darkness",
        keyword="lantern",
        tags={"light", "sea"},
    ),
    "flag": Objective(
        id="flag",
        noun="red signal flag",
        phrase="The bright cloth flashed like a tiny sunset",
        risky_place="the moonlit harbor",
        obstacle="distance",
        keyword="flag",
        tags={"sea", "signal"},
    ),
}

AIDS = {
    "lantern": Aid(id="lantern", label="lantern", covers={"darkness"}, helps_against={"darkness"}, phrase="a warm little light"),
    "rope": Aid(id="rope", label="rope", covers={"cliff"}, helps_against={"cliff"}, phrase="a strong rope for climbing"),
    "coat": Aid(id="coat", label="rain coat", covers={"wind"}, helps_against={"wind"}, phrase="a coat that blocked the sea wind"),
}

VALID_OBJECTIVES = {"compass", "map", "lantern", "flag"}
GIRL_NAMES = ["Mira", "Nina", "Tess", "Luna", "Ivy"]
BOY_NAMES = ["Owen", "Finn", "Jace", "Theo", "Kai"]


@dataclass
class StoryParams:
    setting: str
    objective: str
    aid: str
    name: str
    gender: str
    captain: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for oid, obj in OBJECTIVES.items():
            if obj.risky_place != s.place:
                continue
            for aid in AIDS.values():
                if obj.obstacle in aid.helps_against:
                    combos.append((sid, oid, aid.id))
    return combos


ASP_RULES = r"""
risky(O,S) :- objective(O), setting(S), place_of(S,P), risky_place(O,P).
can_help(A,O) :- aid(A), objective(O), obstacle(O,X), helps_against(A,X).
valid(S,O,A) :- risky(O,S), can_help(A,O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS.values():
        lines.append(asp.fact("setting", s.id))
        lines.append(asp.fact("place_of", s.id, s.place))
        if s.weather:
            lines.append(asp.fact("weather", s.id, s.weather))
    for o in OBJECTIVES.values():
        lines.append(asp.fact("objective", o.id))
        lines.append(asp.fact("risky_place", o.id, o.risky_place))
        lines.append(asp.fact("obstacle", o.id, o.obstacle))
    for a in AIDS.values():
        lines.append(asp.fact("aid", a.id))
        for x in sorted(a.helps_against):
            lines.append(asp.fact("helps_against", a.id, x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Juvenile pirate tale about bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--objective", choices=OBJECTIVES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--captain", choices=["captain"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.objective is None or c[1] == args.objective)
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError("(No valid pirate tale matches the given options.)")
    setting, objective, aid = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    captain = "captain"
    return StoryParams(setting=setting, objective=objective, aid=aid, name=name, gender=gender, captain=captain)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    obj = OBJECTIVES[p.objective]
    return [
        "Write a short juvenile pirate tale about bravery, a dark place, and a found treasure.",
        f"Tell a child-friendly pirate story where {p.name} is scared but brave enough to use a {AIDS[p.aid].label}.",
        f"Write a short story about a pirate child at {SETTINGS[p.setting].place} who finds a {obj.noun} by being brave.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    obj = OBJECTIVES[p.objective]
    aid = AIDS[p.aid]
    return [
        QAItem(
            question=f"Why was {p.name} brave in the story?",
            answer=f"{p.name} was brave because even though the cave was scary, {p.name} still went in to help the crew find the {obj.noun}.",
        ),
        QAItem(
            question=f"What did {p.name} use to see inside the dark place?",
            answer=f"{p.name} used a {aid.label} so the light could chase the shadows away.",
        ),
        QAItem(
            question=f"Where did {p.name} and the captain go?",
            answer=f"They went to {SETTINGS[p.setting].place} to search for the {obj.noun}.",
        ),
        QAItem(
            question=f"What changed at the end for {p.name}?",
            answer=f"By the end, {p.name} felt proud and less scared, because the brave choice worked and the {obj.noun} was found.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    obj = OBJECTIVES[p.objective]
    aid = AIDS[p.aid]
    return [
        QAItem(question="What is bravery?", answer="Bravery means doing the helpful thing even when you feel scared."),
        QAItem(question="What is a lantern for?", answer="A lantern gives off light so people can see in dark places."),
        QAItem(question="What is a compass for?", answer="A compass helps you know which way to go."),
        QAItem(question="What is a pirate ship?", answer="A pirate ship is a boat used by pirates to sail the sea."),
        QAItem(question=f"Why is {aid.label} useful here?", answer=f"It is useful because it helps with the obstacle in the story, so {p.name} can keep going."),
        QAItem(question=f"Why was the {obj.noun} important?", answer=f"It mattered because the crew wanted to find it and bring it home safely."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    objective = OBJECTIVES[params.objective]
    aid = AIDS[params.aid]
    world = tell(setting, objective, aid, params.name, params.gender, params.captain)
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="cove", objective="compass", aid="lantern", name="Mira", gender="girl", captain="captain"),
            StoryParams(setting="cove", objective="map", aid="coat", name="Owen", gender="boy", captain="captain"),
            StoryParams(setting="island", objective="lantern", aid="lantern", name="Luna", gender="girl", captain="captain"),
            StoryParams(setting="harbor", objective="flag", aid="coat", name="Finn", gender="boy", captain="captain"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
