#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/peeve_cigar_valley_conflict_rhyme_dialogue_space.py
============================================================================================================

A small Space Adventure storyworld about a stubborn crew, a dusty valley, a
tiny peeve, and a cigar-shaped signal flare.

Premise:
- A young space traveler and a companion land in a quiet valley on an airless
  moon.
- The traveler has a peeve about leaving before the beacon is fixed.
- A smoking cigar-shaped flare can attract help, but it also risks confusing
  the valley's ancient sensors.

Tension:
- One crew member wants to rush home.
- The other insists on solving the beacon problem first.
- They argue in a short dialogue, with a rhyme used as the turning point.

Resolution:
- They stop, listen, and choose a careful plan.
- The cigar-shaped flare is used only as a signal after the beacon is repaired.
- The valley lights up, the conflict fades, and the crew leaves together.

The world model tracks physical state in meters and emotional state in memes,
and the prose is generated from that evolving state rather than a fixed template.
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
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "pilot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the valley"
    sky: str = "violet"
    afford: set[str] = field(default_factory=set)


@dataclass
class ObjectDef:
    id: str
    label: str
    phrase: str
    risk: str
    signal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    object: str
    name: str
    partner: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


OBJECTS = {
    "cigar": ObjectDef(
        id="cigar",
        label="cigar",
        phrase="a bright cigar-shaped flare",
        risk="smoky",
        signal="glowing",
        tags={"smoke", "signal"},
    ),
    "beacon": ObjectDef(
        id="beacon",
        label="beacon",
        phrase="a broken beacon lens",
        risk="dim",
        signal="bright",
        tags={"light", "signal"},
    ),
    "scanner": ObjectDef(
        id="scanner",
        label="scanner",
        phrase="a valley scanner",
        risk="fuzzy",
        signal="steady",
        tags={"signal"},
    ),
}

SETTINGS = {
    "valley": Setting(place="the valley", sky="violet", afford={"cigar", "beacon", "scanner"}),
    "dust_valley": Setting(place="the dust valley", sky="amber", afford={"cigar", "beacon"}),
}

PEEVE_RHYME = [
    "A quick fix can stick, but a careful fix can sing.",
    "A flare can share a path, but not if it hides the ring.",
]


TRAITS = ["curious", "brave", "restless", "careful", "bright", "stubborn"]
NAMES = ["Nova", "Mira", "Tess", "Juno", "Pip", "Rin", "Kai", "Luna"]
PARTNERS = ["pilot", "captain"]
GENDERS = ["girl", "boy"]


def rhyme_line() -> str:
    return random.choice(PEEVE_RHYME)


def setup_story(world: World, hero: Entity, partner: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next(t for t in hero.memes.get('traits', ['curious']) if t)} traveler "
        f"who loved quiet moons."
    )


def predict_help(world: World, item: Entity) -> bool:
    return item.meters.get("fixed", 0.0) >= THRESHOLD


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Nova", "Mira", "Tess", "Juno", "Pip", "Rin", "Luna"} else "boy",
        meters={"tired": 0.0},
        memes={"peeve": 1.0, "conflict": 0.0, "hope": 0.0, "traits": [params.trait]},
    ))
    partner = world.add(Entity(
        id="Partner",
        kind="character",
        type=params.partner,
        label=f"the {params.partner}",
        meters={"tired": 0.0},
        memes={"patience": 1.0, "conflict": 0.0},
    ))
    item_def = OBJECTS[params.object]
    item = world.add(Entity(
        id=item_def.id,
        kind="thing",
        type=item_def.id,
        label=item_def.label,
        phrase=item_def.phrase,
        owner=hero.id,
        caretaker=partner.id,
        meters={"fixed": 0.0, "smoke": 0.0, "signal": 0.0},
        memes={"mystery": 1.0},
    ))

    # Act 1
    world.say(
        f"On a violet afternoon, {hero.id} and {partner.label} landed in {setting.place}."
    )
    world.say(
        f"They found {item.phrase} beside a half-buried console, and {hero.id} felt a small peeve rise."
    )
    world.say(
        f'{hero.id} said, "We should fix it now."'
    )

    # Act 2
    world.para()
    world.say(
        f'{partner.label.capitalize()} said, "We can patch it later and head home."'
    )
    hero.memes["peeve"] += 1
    hero.memes["conflict"] += 1
    partner.memes["conflict"] += 1
    world.say(
        f'{hero.id} frowned. "If we leave it dim, no one will hear us from the valley."'
    )
    world.say(
        f'{partner.label.capitalize()} pointed at the sky. "That cigar-shaped flare could help, but only after the lens is clean."'
    )

    # Rhyme turn
    world.say(f'{hero.id} breathed out and said, "{rhyme_line()}"')
    world.say(
        f"That line slowed them down. They looked at the broken lens again and stopped arguing."
    )

    # Repair
    item.meters["fixed"] += 1.0
    item.meters["signal"] += 1.0
    hero.memes["conflict"] = 0.0
    partner.memes["conflict"] = 0.0
    hero.memes["hope"] += 1
    world.say(
        f"Together they cleaned the beacon, and its little light woke up like a star."
    )

    # Act 3
    world.para()
    item.meters["smoke"] += 1.0
    world.say(
        f'Only then did {partner.label} light the cigar-shaped flare, and the valley answered with a bright echo.'
    )
    world.say(
        f'{hero.id} smiled. "Now the signal can travel far."'
    )
    world.say(
        f"They packed their tools, left the valley glowing behind them, and flew home side by side."
    )

    world.facts.update(
        hero=hero,
        partner=partner,
        item=item,
        setting=setting,
        object_def=item_def,
        place=params.place,
        trait=params.trait,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short Space Adventure story for a young child about {hero.id}, a peeve, and a valley.',
        f"Tell a gentle dialogue story where {hero.id} and {f['partner'].label} argue, then use a rhyme to calm down.",
        f'Write a story that includes a cigar-shaped flare and ends with a bright signal in the valley.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    item = f["item"]
    return [
        QAItem(
            question=f"What made {hero.id} feel upset in the valley?",
            answer=f"{hero.id} had a peeve about leaving the broken beacon alone, because the valley would stay quiet and dark.",
        ),
        QAItem(
            question=f"What did {partner.label} want to do before fixing the beacon?",
            answer=f"{partner.label} wanted to head home first, but {hero.id} wanted to fix the beacon before leaving.",
        ),
        QAItem(
            question="How did they stop arguing?",
            answer=f"{hero.id} said a rhyme, and that helped both of them slow down and listen before they chose the careful plan.",
        ),
        QAItem(
            question=f"What happened after they fixed the beacon?",
            answer=f"The beacon lit up, and then they used the cigar-shaped flare as a signal so the valley could answer back.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a valley?",
            answer="A valley is a low area between hills or mountains. People can travel through it, and it can feel quiet and wide.",
        ),
        QAItem(
            question="What does a signal flare do?",
            answer="A signal flare makes a bright light or smoke so other people can notice where you are and come help.",
        ),
        QAItem(
            question="Why can smoke be useful in space travel stories?",
            answer="Smoke can make a signal easy to see from far away, especially when a crew needs help or wants to be found.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== story questions =="]
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={ {k:v for k,v in e.meters.items() if v} } memes={ {k:v for k,v in e.memes.items() if v and k != 'traits'} }"
        )
    return "\n".join(lines)


ASP_RULES = r"""
hero_conflict(H) :- peeve(H), wants_fix(H), not fixed_first.
rhyme_settles(H) :- rhyme(H), conflict(H).
signal_ready(I) :- fixed(I), flare(I).
valid_story(P, O) :- place(P), object(O), afford(P, O).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        for a in sorted(SETTINGS[pid].afford):
            lines.append(asp.fact("afford", pid, a))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld with peeve, cigar, and valley.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--partner", choices=PARTNERS)
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


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for obj in setting.afford:
            out.append((place, obj))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos if args.place is None or c[0] == args.place]
    combos = [c for c in combos if args.object is None or c[1] == args.object]
    if not combos:
        raise StoryError("No valid story combination matches those options.")
    place, obj = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    partner = args.partner or rng.choice(PARTNERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, object=obj, name=name, partner=partner, trait=trait)


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


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/2.")
    model = asp.one_model(program)
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    py = sorted(valid_combos())
    asp_pairs = [(a, b) for (a, b) in atoms]
    if sorted(asp_pairs) == py:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP:", asp_pairs)
    print("PY :", py)
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = []
        for i, (place, obj) in enumerate(valid_combos()):
            params = StoryParams(place=place, object=obj, name=NAMES[i % len(NAMES)], partner=PARTNERS[i % len(PARTNERS)], trait=TRAITS[i % len(TRAITS)], seed=base_seed + i)
            samples.append(generate(params))
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
