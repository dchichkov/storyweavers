#!/usr/bin/env python3
"""
storyworlds/worlds/structure_curiosity_flashback_tall_tale.py
============================================================

A tall-tale storyworld about a curious child, a sturdy structure, and a flashback
to how it was built.

The world model tracks:
- physical meters: wobble, repair, weather, height, strength
- emotional memes: curiosity, pride, worry, relief, wonder

The premise stays small and classical: a child notices a famous structure, asks
how it stayed up so long, remembers an older tale about its first building, and
helps fix the one weak spot before the wind can brag louder than the people.

The story is intentionally close to Tall Tale style:
- a large, memorable structure
- a curious child
- a flashback to the old building story
- a practical fix that proves the structure changed
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["wobble", "repair", "strength", "height", "weather"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "pride", "worry", "relief", "wonder", "memory"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    sky: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Structure:
    id: str
    label: str
    phrase: str
    kind: str
    setting: str
    weak_spot: str
    fix: str
    fix_tool: str
    flashback_line: str
    tall_tale_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    structure: str
    name: str
    gender: str
    elder: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.lines: list[str] = []
        self.para_open = True

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if not line:
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.facts = dict(self.facts)
        return c


SETTINGS = {
    "creek": Setting(place="the creek bridge", sky="windy", affords={"bridge"}),
    "hill": Setting(place="the hilltop tower", sky="blowy", affords={"tower"}),
    "field": Setting(place="the old barn", sky="stormy", affords={"barn"}),
    "forest": Setting(place="the treehouse", sky="swaying", affords={"treehouse"}),
}

STRUCTURES = {
    "bridge": Structure(
        id="bridge",
        label="bridge",
        phrase="a long bridge over the creek",
        kind="bridge",
        setting="creek",
        weak_spot="the middle plank",
        fix="a new plank and two iron braces",
        fix_tool="a hammer and rope",
        flashback_line="Long ago, the elder had sworn the bridge would outlast a hundred frogs and a thousand summer storms.",
        tall_tale_line="The bridge stood so proud it seemed to tip its hat to the clouds.",
        tags={"wood", "water", "wind"},
    ),
    "tower": Structure(
        id="tower",
        label="tower",
        phrase="a tall lookout tower on the hill",
        kind="tower",
        setting="hill",
        weak_spot="the top beam",
        fix="a thick beam and fresh nails",
        fix_tool="a ladder and a wrench",
        flashback_line="Long ago, the elder had climbed the first beam while the moon watched like a silver lantern.",
        tall_tale_line="The tower rose so high it could almost gossip with the stars.",
        tags={"wood", "sky", "wind"},
    ),
    "barn": Structure(
        id="barn",
        label="barn",
        phrase="a red barn in the field",
        kind="barn",
        setting="field",
        weak_spot="the swinging door hinge",
        fix="a new hinge and a sturdy latch",
        fix_tool="a screwdriver and a crate",
        flashback_line="Long ago, the elder had hammered the barn together before breakfast and before the rooster finished boasting.",
        tall_tale_line="The barn was so broad it looked like it could hide a thundercloud in its pocket.",
        tags={"wood", "animals", "wind"},
    ),
    "treehouse": Structure(
        id="treehouse",
        label="treehouse",
        phrase="a little treehouse in the forest",
        kind="treehouse",
        setting="forest",
        weak_spot="the ladder rung",
        fix="a new rung and a tight knot",
        fix_tool="a saw and a spool of twine",
        flashback_line="Long ago, the elder had tied the first rope while the pine trees leaned in to watch.",
        tall_tale_line="The treehouse sat so high that squirrels treated it like a neighbors' porch.",
        tags={"wood", "trees", "wind"},
    ),
}

GENDERS = {"girl", "boy"}
NAMES = {
    "girl": ["Maya", "June", "Lily", "Hazel", "Nora", "Ruby"],
    "boy": ["Owen", "Ben", "Theo", "Milo", "Eli", "Jasper"],
}
ELDERS = ["grandmother", "grandfather"]
TRAITS = ["curious", "bright-eyed", "plucky", "lively", "wondering"]

KNOWLEDGE = {
    "bridge": [
        QAItem(
            question="What is a bridge for?",
            answer="A bridge helps people cross over water, roads, or other places that are hard to cross on foot."
        )
    ],
    "tower": [
        QAItem(
            question="What is a tower?",
            answer="A tower is a tall structure built to stand high above the ground."
        )
    ],
    "barn": [
        QAItem(
            question="What is a barn for?",
            answer="A barn is a big building where farmers can keep hay, tools, or animals safe from the weather."
        )
    ],
    "treehouse": [
        QAItem(
            question="What is a treehouse?",
            answer="A treehouse is a small house or platform built among tree branches for play or lookout."
        )
    ],
    "wind": [
        QAItem(
            question="Why can wind make a structure wobble?",
            answer="Wind can push on a structure, so a loose part may shake or sway if it is not fastened well."
        )
    ],
    "wood": [
        QAItem(
            question="Why is wood useful for building?",
            answer="Wood is useful because it can be cut, nailed, and shaped into many strong building pieces."
        )
    ],
    "repair": [
        QAItem(
            question="Why do people repair old things?",
            answer="People repair old things so they stay safe, work better, and last longer."
        )
    ],
}


def valid_combos() -> list[tuple[str, str]]:
    return sorted((place, sid) for sid, s in STRUCTURES.items() for place in SETTINGS if s.setting == place)


def explain_rejection(place: str, structure: str) -> str:
    s = STRUCTURES[structure]
    return f"(No story: {s.label} belongs at {s.setting}, not at {place}.)"


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    structure = STRUCTURES[params.structure]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    elder = world.add(Entity(id="Elder", kind="character", type=params.elder, label=f"the {params.elder}", meters={}, memes={}))
    obj = world.add(Entity(
        id=structure.id,
        type=structure.kind,
        label=structure.label,
        phrase=structure.phrase,
        owner=elder.id,
        caretaker=elder.id,
    ))

    hero.memes["curiosity"] += 1
    hero.memes["wonder"] += 1
    elder.memes["pride"] += 1
    obj.meters["strength"] = 3.0
    obj.meters["wobble"] = 0.0

    world.say(f"{hero.id} was a {random.choice(TRAITS)} child who loved asking how big things stayed up.")
    world.say(f"One day, {hero.id} saw {obj.phrase} and blinked at it like it had grown there by magic.")
    world.say(f"The {obj.label} was so tall and brave it seemed to wear the sky like a hat.")

    world.para()
    world.say(f"{hero.id} asked, \"How did {obj.label} get so sturdy?\"")
    world.say(f"The {params.elder} smiled, because that was a question with a long tail on it.")
    world.say(structure.flashback_line)
    world.say(f"In the flashback, the {params.elder} had the {structure.fix_tool} in one hand and a dream as big as a barn door in the other.")
    hero.memes["memory"] += 1

    world.para()
    world.say(f"Then the wind came whistling over {params.place} and found {structure.weak_spot}.")
    obj.meters["wobble"] += 1.0
    hero.memes["worry"] += 1
    world.say(f"{structure.weak_spot.capitalize()} began to quiver, and {hero.id}'s eyes grew wide with concern.")
    world.say(f"{structure.tall_tale_line}")

    world.para()
    world.say(f"{hero.id} did not run home; {hero.pronoun()} fetched {structure.fix_tool} and helped the {params.elder} mend the weak spot.")
    obj.meters["repair"] += 1.0
    obj.meters["wobble"] = 0.0
    obj.meters["strength"] += 1.0
    hero.memes["curiosity"] += 1
    hero.memes["relief"] += 1
    elder.memes["relief"] += 1
    world.say(f"They fastened {structure.fix} until the whole structure stood square and proud again.")
    world.say(f"By sunset, the {obj.label} was not just old; it was old and mended and ready for another hundred stories.")
    world.say(f"{hero.id} looked up and grinned, because the flashback had turned into a fresh tomorrow.")

    world.facts.update(
        hero=hero,
        elder=elder,
        structure=obj,
        structure_cfg=structure,
        place=params.place,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    h = f["hero"]
    s = f["structure_cfg"]
    return [
        f'Write a tall tale for a child named {h.id} about a {s.label} and the word "structure".',
        f"Tell a curious story with a flashback in which {h.id} learns how {s.label} stayed sturdy.",
        f"Write a short, child-friendly story where a big structure wobbles, gets repaired, and ends stronger than before.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h = f["hero"]
    elder = f["elder"]
    s = f["structure_cfg"]
    obj = f["structure"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {h.id}, a curious child who wanted to know how the {s.label} stayed strong."
        ),
        QAItem(
            question=f"What did {h.id} see at {f['place']}?",
            answer=f"{h.id} saw {s.phrase}, which was a famous structure in the story."
        ),
        QAItem(
            question=f"What was the flashback about?",
            answer=f"The flashback was about how the {elder.type} first built the {s.label}, piece by piece, long ago."
        ),
        QAItem(
            question=f"What problem did the structure have?",
            answer=f"The {s.label} began to wobble at {s.weak_spot} when the wind pushed on it."
        ),
        QAItem(
            question=f"How was the structure fixed?",
            answer=f"They used {s.fix_tool} and put in {s.fix} so the structure could stand steady again."
        ),
        QAItem(
            question=f"How did {h.id} feel at the end?",
            answer=f"{h.id} felt relieved and full of wonder, because the structure was sturdy again and the old story had become a new memory."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["structure_cfg"].tags)
    tags.add("repair")
    tags.add(world.facts["structure_cfg"].kind)
    out: list[QAItem] = []
    for key in ["bridge", "tower", "barn", "treehouse", "wind", "wood", "repair"]:
        if key in tags or key == world.facts["structure_cfg"].kind:
            out.extend(KNOWLEDGE[key])
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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="creek", structure="bridge", name="Maya", gender="girl", elder="grandfather"),
    StoryParams(place="hill", structure="tower", name="Owen", gender="boy", elder="grandmother"),
    StoryParams(place="field", structure="barn", name="Lily", gender="girl", elder="grandfather"),
    StoryParams(place="forest", structure="treehouse", name="Theo", gender="boy", elder="grandmother"),
]


ASP_RULES = r"""
place(P) :- setting(P).
structure(S) :- structure_kind(S).
compatible(P,S) :- place(P), structure(S), built_in(S,P).
valid_story(P,S) :- compatible(P,S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for sid, s in STRUCTURES.items():
        lines.append(asp.fact("structure_kind", sid))
        lines.append(asp.fact("built_in", sid, s.setting))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld with curiosity and flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--structure", choices=STRUCTURES)
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDERS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.structure:
        if STRUCTURES[args.structure].setting != args.place:
            raise StoryError(explain_rejection(args.place, args.structure))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.structure is None or c[1] == args.structure)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, structure = rng.choice(combos)
    gender = args.gender or rng.choice(sorted(GENDERS))
    name = args.name or rng.choice(NAMES[gender])
    elder = args.elder or rng.choice(ELDERS)
    return StoryParams(place=place, structure=structure, name=name, gender=gender, elder=elder)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        for place, structure in combos:
            print(f"{place}\t{structure}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.structure} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
