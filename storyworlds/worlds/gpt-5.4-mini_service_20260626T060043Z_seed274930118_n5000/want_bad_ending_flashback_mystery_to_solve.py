#!/usr/bin/env python3
"""
A standalone storyworld for an adventure tale with want, flashback, mystery to solve,
and a bad-ending branch that the story avoids through a better choice.
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


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the mossy trail"
    landmark: str = "the old stone arch"
    mood: str = "wild"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    object_name: str
    place_hint: str
    phrase: str


@dataclass
class Hazard:
    id: str
    label: str
    danger: str
    consequence: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []
        self.fired: set[tuple] = set()

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
        import copy
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.facts = dict(self.facts)
        other.trace = list(self.trace)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "trail": Setting(place="the mossy trail", landmark="the old stone arch", mood="wild", affords={"trail"}),
    "ruins": Setting(place="the vine-choked ruins", landmark="the cracked bell tower", mood="ancient", affords={"trail", "ruins"}),
    "cove": Setting(place="the windy sea cove", landmark="the shell cave", mood="briny", affords={"trail", "cove"}),
}

HEROES = {
    "boy": ["Arlo", "Finn", "Milo", "Theo", "Nico"],
    "girl": ["Ivy", "Mina", "Luna", "Rose", "Tess"],
}

TRAITS = ["brave", "curious", "restless", "bold", "careful"]

CLUES = {
    "map": Clue("map", "a torn map", "the old stone arch", "a torn map with a red X"),
    "key": Clue("key", "a brass key", "the cracked bell tower", "a brass key tied to a blue ribbon"),
    "shell": Clue("shell", "a spiral shell", "the shell cave", "a spiral shell with a notch"),
}

HAZARDS = {
    "pit": Hazard("pit", "a hidden pit", "one wrong step", "a tumble into the dark"),
    "tide": Hazard("tide", "the rising tide", "waiting too long", "the path getting cut off"),
    "fog": Hazard("fog", "thick fog", "guessing wrong", "losing the way home"),
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(trail).
setting(ruins).
setting(cove).

hero_type(boy).
hero_type(girl).

clue(map).
clue(key).
clue(shell).

hazard(pit).
hazard(tide).
hazard(fog).

affords(trail,trail).
affords(ruins,trail).
affords(ruins,ruins).
affords(cove,trail).
affords(cove,cove).

solves(trail,map) :- setting(trail), clue(map).
solves(ruins,key) :- setting(ruins), clue(key).
solves(cove,shell) :- setting(cove), clue(shell).

bad_ending(H) :- hazard(H), not avoided(H).
avoided(pit) :- clue(map).
avoided(tide) :- clue(shell).
avoided(fog) :- clue(key).

compatible(P,C,H) :- affords(P,trail), solves(P,C), hazard(H), avoided(H).
#show compatible/3.
#show avoided/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
        lines.append(asp.fact("landmark", sid, s.landmark))
        lines.append(asp.fact("mood", sid, s.mood))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for hid in HEROES:
        lines.append(asp.fact("hero_type", hid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for hz in HAZARDS:
        lines.append(asp.fact("hazard", hz))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    clingo = set(asp.atoms(model, "compatible"))
    py = set((p, c, h) for (p, c, h) in valid_combos())
    if clingo == py:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo - py:
        print("only in clingo:", sorted(clingo - py))
    if py - clingo:
        print("only in python:", sorted(py - clingo))
    return 1


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    hero_type: str
    name: str
    trait: str
    clue: str
    hazard: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for clue_id in CLUES:
            if setting_id == "trail" and clue_id == "map":
                pass
            if setting_id == "ruins" and clue_id == "key":
                pass
            if setting_id == "cove" and clue_id == "shell":
                pass
            for hazard_id in HAZARDS:
                if (setting_id, clue_id, hazard_id) in [
                    ("trail", "map", "pit"),
                    ("ruins", "key", "fog"),
                    ("cove", "shell", "tide"),
                ]:
                    combos.append((setting_id, clue_id, hazard_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: want, flashback, mystery to solve, bad ending avoided.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if args.hazard:
        combos = [c for c in combos if c[2] == args.hazard]
    if not combos:
        raise StoryError("No valid adventure combination matches the chosen options.")
    setting, clue, hazard = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(HEROES[gender])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, hero_type=gender, name=name, trait=trait, clue=clue, hazard=hazard)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.name))
    clue = CLUES[params.clue]
    hazard = HAZARDS[params.hazard]
    world.facts.update(hero=hero, clue=clue, hazard=hazard, params=params)

    hero.memes["want"] = 1
    hero.memes["fear"] = 0
    hero.memes["joy"] = 0

    world.say(
        f"{params.name} was a {params.trait} little {params.hero_type} who loved adventure. "
        f"{params.name} did not just want a quiet walk; {params.name} wanted to find the hidden thing that the old stories talked about."
    )
    world.say(
        f"Long ago, {params.name} had heard a whisper about {clue.phrase} near {world.setting.landmark}, and that memory kept tugging at {params.name} all day."
    )

    world.para()
    world.say(
        f"At {world.setting.place}, the air felt full of secrets. {params.name} walked past roots, stones, and twisting green vines, looking for the clue."
    )

    # Flashback: a brief memory helps solve the mystery.
    world.para()
    world.say(
        f"Then a flashback came like a tiny lantern in {params.name}'s mind. {params.name} remembered an old ranger pointing at {clue.place_hint} and saying, "
        f'“The answer is not where you first look; it is where the mark points.”'
    )

    # Mystery solving.
    world.para()
    if params.clue == "map":
        solution = "the map was tucked under a flat stone beside the arch"
        path = "followed the red X"
    elif params.clue == "key":
        solution = "the key hung behind a loose brick in the tower"
        path = "used the key to open the narrow door"
    else:
        solution = "the shell was hiding in a pocket of soft sand by the cave wall"
        path = "turned the shell until the notch lined up with the waves"
    world.say(
        f"That clue solved the mystery at once: {solution}. {params.name} smiled and {path}."
    )

    # Bad-ending branch avoided.
    if params.hazard == "pit":
        danger_line = "one wrong step would have dropped the hero into the dark"
        safe_line = "but the clue showed where the ground was firm, so {name} stepped around the hole"
    elif params.hazard == "tide":
        danger_line = "waiting too long would have let the tide trap the way back"
        safe_line = "but the clue pointed to a higher path, so {name} hurried before the water rose"
    else:
        danger_line = "guessing wrong would have sent the hero deeper into the fog"
        safe_line = "but the clue gave a clear direction, so {name} kept the trail and never got lost"
    world.say(
        f"The bad ending was close: {danger_line}. Yet {safe_line.format(name=params.name)}."
    )

    world.para()
    hero.memes["joy"] = 1
    world.say(
        f"In the end, {params.name} came home with the mystery solved and the scare behind them. "
        f"The trail looked different now, because the answer had been found, and the brave little explorer felt bigger than before."
    )

    prompts = [
        "Write a short adventure story about a child who wants to solve a mystery, uses a flashback clue, and avoids a bad ending.",
        f"Tell a gentle adventure where {params.name} wants to find a hidden clue at {world.setting.place}.",
        "Write a child-friendly mystery story with a flashback that helps the hero choose the safe path.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.name} want at the start of the story?",
            answer=f"{params.name} wanted to solve the mystery and find the hidden thing near {world.setting.landmark}.",
        ),
        QAItem(
            question="What was the flashback for?",
            answer=f"The flashback reminded {params.name} of {clue.phrase} and pointed the hero toward the right place.",
        ),
        QAItem(
            question="How was the bad ending avoided?",
            answer=f"{params.name} used the clue and chose the safe path, so the danger never happened.",
        ),
        QAItem(
            question=f"Where did {params.name} finally find the answer?",
            answer=f"{params.name} found the answer at {world.setting.place} near {world.setting.landmark}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone figure out a mystery.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a short memory of something that happened before the present moment.",
        ),
        QAItem(
            question="What does it mean to want something?",
            answer="To want something means to wish for it or hope to get it.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible")))


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        combos = sorted(set(asp.atoms(model, "compatible")))
        for row in combos:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting_id, clue_id, hazard_id in valid_combos():
            params = StoryParams(
                setting=setting_id,
                hero_type="girl",
                name="Ivy",
                trait="curious",
                clue=clue_id,
                hazard=hazard_id,
                seed=base_seed,
            )
            samples.append(generate(params))
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
