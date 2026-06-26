#!/usr/bin/env python3
"""
storyworlds/worlds/copulate_cautionary_fable.py
================================================

A small cautionary fable world about two animals who want to copulate in the
wrong place, learn a concrete risk, and choose a safer way to begin a family.

The world is intentionally modest: a few animal kinds, a few places, one danger
per setting, and one sensible elder who can warn the pair.  The story should read
like a fable: brief, concrete, slightly moral, and ending with a clear change in
state.
"""

from __future__ import annotations

import argparse
import copy
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
    place: str = ""
    mates_with: Optional[str] = None
    wary: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "deer", "hare"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    danger: str
    afford: set[str] = field(default_factory=set)
    shelter: str = ""


@dataclass
class Pair:
    id: str
    animal: str
    verb: str
    coupling_phrase: str
    risk: str
    danger_kind: str
    danger_meter: str
    shelter_fix: str
    shelter_entity: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ElderAdvice:
    id: str
    label: str
    warning: str
    fix: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary fable story world about a risky copulating pair.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--pair", choices=PAIRS.keys())
    ap.add_argument("--elder", choices=ELDERS.keys())
    ap.add_argument("--name1")
    ap.add_argument("--name2")
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


SETTINGS = {
    "reedbed": Setting(place="the reedbed", danger="a muddy sinkhole", afford={"copulate"}, shelter="the hollow bank"),
    "orchard": Setting(place="the orchard", danger="a prowling fox", afford={"copulate"}, shelter="the thorn hedge"),
    "meadow": Setting(place="the meadow", danger="a sudden storm", afford={"copulate"}, shelter="the stone burrow"),
}

PAIRS = {
    "hares": Pair(
        id="hares",
        animal="hare",
        verb="copulate",
        coupling_phrase="stay together to copulate",
        risk="a sinkhole",
        danger_kind="mud",
        danger_meter="mire",
        shelter_fix="the dry burrow",
        shelter_entity="burrow",
        tags={"hare", "mud"},
    ),
    "foxes": Pair(
        id="foxes",
        animal="fox",
        verb="copulate",
        coupling_phrase="copulate",
        risk="a prowling fox",
        danger_kind="fox",
        danger_meter="fear",
        shelter_fix="the thorn hedge",
        shelter_entity="hedge",
        tags={"fox", "predator"},
    ),
    "deer": Pair(
        id="deer",
        animal="deer",
        verb="copulate",
        coupling_phrase="pair up and copulate",
        risk="a storm",
        danger_kind="storm",
        danger_meter="cold",
        shelter_fix="the stone burrow",
        shelter_entity="burrow",
        tags={"deer", "weather"},
    ),
}

ELDERS = {
    "mother_hare": ElderAdvice(
        id="mother_hare",
        label="old hare",
        warning="The ground there is soft, and soft ground can swallow a careless hop.",
        fix="They could use the dry burrow first.",
        tail="Then the night would be quiet and safe.",
    ),
    "old_fox": ElderAdvice(
        id="old_fox",
        label="old fox",
        warning="A bright meadow is easy to see, and easy to see means easy to catch.",
        fix="They could slip into the thorn hedge instead.",
        tail="Then no hungry eye would find them.",
    ),
    "old_deer": ElderAdvice(
        id="old_deer",
        label="old deer",
        warning="Clouds can turn kind paths into cold, loud trouble very quickly.",
        fix="They could wait in the stone burrow.",
        tail="Then the storm could pass above them.",
    ),
}

NAMES = {
    "hare": ["Pip", "Luna", "Moss", "Tansy", "Bran", "Wren"],
    "fox": ["Sable", "Rust", "Nim", "Ember", "Pike", "Fenn"],
    "deer": ["Mira", "Ash", "Glen", "Orr", "Fern", "Rowan"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for p in PAIRS:
            for e in ELDERS:
                out.append((s, p, e))
    return out


@dataclass
class StoryParams:
    setting: str
    pair: str
    elder: str
    name1: str
    name2: str
    seed: Optional[int] = None


def choose_names(pair: Pair, rng: random.Random) -> tuple[str, str]:
    pool = NAMES[pair.animal]
    a, b = rng.sample(pool, 2)
    return a, b


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.pair and args.pair not in PAIRS:
        raise StoryError("Unknown pair.")
    if args.elder and args.elder not in ELDERS:
        raise StoryError("Unknown elder.")

    settings = [args.setting] if args.setting else list(SETTINGS)
    pairs = [args.pair] if args.pair else list(PAIRS)
    elders = [args.elder] if args.elder else list(ELDERS)

    combos = [(s, p, e) for s in settings for p in pairs for e in elders]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    setting, pair, elder = rng.choice(sorted(combos))
    p = PAIRS[pair]
    n1, n2 = choose_names(p, rng)
    if args.name1:
        n1 = args.name1
    if args.name2:
        n2 = args.name2
    return StoryParams(setting=setting, pair=pair, elder=elder, name1=n1, name2=n2)


def _do_copulation(world: World, a: Entity, b: Entity, pair: Pair, narrate: bool = True) -> None:
    a.mates_with = b.id
    b.mates_with = a.id
    a.memes["desire"] = a.memes.get("desire", 0.0) + 1
    b.memes["desire"] = b.memes.get("desire", 0.0) + 1
    if narrate:
        world.say(f"{a.id} and {b.id} wanted to {pair.verb} right away.")


def predict_risk(world: World, pair: Pair, a: Entity, b: Entity) -> bool:
    sim = world.copy()
    _do_copulation(sim, sim.get(a.id), sim.get(b.id), pair, narrate=False)
    danger = sim.setting.danger
    if pair.danger_kind == "mud":
        return danger == "a muddy sinkhole"
    if pair.danger_kind == "fox":
        return danger == "a prowling fox"
    return danger == "a sudden storm"


def tell(setting: Setting, pair: Pair, elder: ElderAdvice, name1: str, name2: str) -> World:
    world = World(setting)
    a = world.add(Entity(id=name1, kind="character", type=pair.animal, label=pair.animal, place=setting.place))
    b = world.add(Entity(id=name2, kind="character", type=pair.animal, label=pair.animal, place=setting.place))
    old = world.add(Entity(id="elder", kind="character", type=pair.animal, label=elder.label, wary=True, place=setting.place))

    world.say(f"In {setting.place}, there lived two small {pair.animal}s named {a.id} and {b.id}.")
    world.say(f"They liked each other and wanted to {pair.verb} when the moon was high.")
    world.say(f"But {setting.place} had its own danger: {setting.danger}.")
    world.para()

    world.say(f"One evening, {a.id} and {b.id} crept toward the open ground.")
    if predict_risk(world, pair, a, b):
        world.say(f"Then the old {pair.animal} called, \"{elder.warning}\"")
        world.say(f"\"{elder.fix}\"")
        world.say(f"{a.id} and {b.id} stopped to listen.")
        world.say(f"They chose {setting.shelter} instead of the open place.")
        world.say(f"There, they could {pair.coupling_phrase} without fear.")
        world.para()
        world.say(f"At last, they settled together in {setting.shelter}, and the night stayed gentle.")
        world.say(f"The fable's lesson was plain: desire is not wisdom, and a safer place can save the day.")
    else:
        world.say(f"They did not see the danger at first, but the old {pair.animal} warned them anyway.")
        world.say(f"Because of that warning, they moved to {setting.shelter} before anything went wrong.")
        world.say(f"There they could {pair.coupling_phrase}, and the danger was left outside.")
    world.facts.update(
        a=a,
        b=b,
        elder=old,
        pair=pair,
        setting=setting,
        advice=elder,
        safe_place=setting.shelter,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short cautionary fable about two {f['pair'].animal}s who want to copulate in {f['setting'].place} but learn to choose a safer place.",
        f"Tell a gentle animal fable with a warning, a safer shelter, and a lesson about not rushing to copulate when danger is near.",
        f"Write a child-friendly cautionary story about {f['a'].id} and {f['b'].id}, an elder warning, and a better place to begin a family.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    pair: Pair = f["pair"]
    setting: Setting = f["setting"]
    elder: ElderAdvice = f["advice"]
    a: Entity = f["a"]
    b: Entity = f["b"]
    return [
        QAItem(
            question=f"Who are the two {pair.animal}s in the fable?",
            answer=f"They are {a.id} and {b.id}, two small {pair.animal}s who wanted to copulate.",
        ),
        QAItem(
            question=f"What danger made {setting.place} a poor place for them to stay?",
            answer=f"{setting.place} was risky because of {setting.danger}. That is why the elder warned them to move.",
        ),
        QAItem(
            question=f"What did the old {pair.animal} tell them to do instead?",
            answer=f"{elder.fix} The safer shelter let them avoid the danger and keep their night calm.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They chose {setting.shelter} and stayed there together. The ending shows they learned to be careful before they copulated.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    pair: Pair = f["pair"]
    return [
        QAItem(
            question=f"What is an elder in a fable?",
            answer="An elder is an older character who gives advice from experience and tries to keep others safe.",
        ),
        QAItem(
            question=f"Why is it wiser to choose a sheltered place when danger is near?",
            answer="A sheltered place can keep an animal away from predators, weather, or bad footing, so the pair has a better chance to stay safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.place:
            bits.append(f"place={e.place}")
        if e.mates_with:
            bits.append(f"mates_with={e.mates_with}")
        if e.wary:
            bits.append("wary=True")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place_setting(reedbed, muddy_sinkhole).
place_setting(orchard, fox).
place_setting(meadow, storm).

pair(hare, copulate).
pair(fox, copulate).
pair(deer, copulate).

safer_place(reedbed, burrow).
safer_place(orchard, hedge).
safer_place(meadow, burrow).

valid(Setting, Pair, Elder) :- place_setting(Setting, _), pair(Pair, copulate), elder(Elder).

elder(mother_hare).
elder(old_fox).
elder(old_deer).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, setting in SETTINGS.items():
        lines.append(asp.fact("place_setting", key, setting.danger.replace(" ", "_")))
        lines.append(asp.fact("shelter", key, setting.shelter.replace("the ", "").replace(" ", "_")))
    for key, pair in PAIRS.items():
        lines.append(asp.fact("pair", pair.animal, pair.verb))
        lines.append(asp.fact("pair_tag", key))
    for key in ELDERS:
        lines.append(asp.fact("elder", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.pair is None or c[1] == args.pair)
        and (args.elder is None or c[2] == args.elder)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, pair, elder = rng.choice(sorted(combos))
    p = PAIRS[pair]
    n1, n2 = choose_names(p, rng)
    if args.name1:
        n1 = args.name1
    if args.name2:
        n2 = args.name2
    return StoryParams(setting=setting, pair=pair, elder=elder, name1=n1, name2=n2)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PAIRS[params.pair], ELDERS[params.elder], params.name1, params.name2)
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
    StoryParams(setting="reedbed", pair="hares", elder="mother_hare", name1="Pip", name2="Luna"),
    StoryParams(setting="orchard", pair="foxes", elder="old_fox", name1="Sable", name2="Ember"),
    StoryParams(setting="meadow", pair="deer", elder="old_deer", name1="Mira", name2="Rowan"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name1} and {p.name2}: {p.pair} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
