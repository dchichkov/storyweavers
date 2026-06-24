#!/usr/bin/env python3
"""
Standalone storyworld: rehearsal, slink, plumb, magic, flashback, pirate tale.

A small pirate crew is preparing for a harbor performance. A nervous deckhand
wants to slink away from rehearsal, but a magical clue and a flashback about a
lost chart help the crew plumb the right course and finish with a bold pirate
image.

The world is intentionally tiny and constraint-checked:
- the rehearsal happens only in a setting that can host it,
- the magical helper must actually fix the problem,
- the flashback is a stateful memory beat, not a frozen paragraph swap,
- invalid explicit choices raise StoryError.

The script supports the standard storyworld CLI:
default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify,
and --show-asp.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

STORY_TOPICS = {"rehearsal", "slink", "plumb", "magic", "flashback", "pirate"}


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father", "captain", "sailor", "deckhand", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the harbor stage"
    affords: set[str] = field(default_factory=lambda: {"rehearsal"})


@dataclass
class CrewRole:
    id: str
    title: str
    temperament: str
    can_plumb: bool = False
    can_magic: bool = False


@dataclass
class Prophecy:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    reveals: str = ""
    magical: bool = False


@dataclass
class StoryParams:
    place: str
    role: str
    prophecy: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


CREW = {
    "deckhand": CrewRole("deckhand", "deckhand", "nervous", can_plumb=True),
    "captain": CrewRole("captain", "captain", "bold", can_magic=True),
    "firstmate": CrewRole("firstmate", "first mate", "steady", can_plumb=True, can_magic=True),
}

PROPS = {
    "chart": Prophecy("chart", "golden chart", "a golden chart with a hidden route", helps={"plumb"}, reveals="the bend in the bay", magical=True),
    "lantern": Prophecy("lantern", "moon lantern", "a moon lantern that glowed even in fog", helps={"magic"}, reveals="the safe pier", magical=True),
    "rope": Prophecy("rope", "braided rope", "a braided rope for tying the stage", helps=set(), reveals="", magical=False),
}

SETTINGS = {
    "harbor": Setting("the harbor stage", {"rehearsal"}),
    "dock": Setting("the dockside yard", {"rehearsal"}),
}

NAMES = ["Mira", "Bram", "Jory", "Nell", "Pip", "Tessa", "Rook", "Finn"]
TRAITS = ["nervous", "brave", "curious", "quick", "sleepy"]


def _plumb_choice(role: CrewRole, prop: Prophecy) -> bool:
    return role.can_plumb and "plumb" in prop.helps


def _magic_choice(role: CrewRole, prop: Prophecy) -> bool:
    return role.can_magic and prop.magical


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for role_id, role in CREW.items():
            for prop_id, prop in PROPS.items():
                if place in SETTINGS and (role.can_plumb or role.can_magic) and (prop.magical or prop.helps):
                    if (_plumb_choice(role, prop) or _magic_choice(role, prop)):
                        out.append((place, role_id, prop_id))
    return out


ASP_RULES = r"""
valid(P,R,O) :- setting(P), role(R), prop(O), plumb_fix(R,O).
valid(P,R,O) :- setting(P), role(R), prop(O), magic_fix(R,O).
plumb_fix(R,O) :- can_plumb(R), helps(O, plumb).
magic_fix(R,O) :- can_magic(R), magical(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
        for a in SETTINGS[pid].affords:
            lines.append(asp.fact("affords", pid, a))
    for rid, r in CREW.items():
        lines.append(asp.fact("role", rid))
        if r.can_plumb:
            lines.append(asp.fact("can_plumb", rid))
        if r.can_magic:
            lines.append(asp.fact("can_magic", rid))
    for oid, o in PROPS.items():
        lines.append(asp.fact("prop", oid))
        if o.magical:
            lines.append(asp.fact("magical", oid))
        for h in o.helps:
            lines.append(asp.fact("helps", oid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with rehearsal, magic, and flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--role", choices=CREW)
    ap.add_argument("--prophecy", choices=PROPS)
    ap.add_argument("--name")
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
              if (args.place is None or c[0] == args.place)
              and (args.role is None or c[1] == args.role)
              and (args.prophecy is None or c[2] == args.prophecy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, role, prop = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, role=role, prophecy=prop, name=name)


def _setup(world: World, hero: Entity, role: CrewRole, prop: Prophecy) -> None:
    world.say(f"{hero.id} was a {role.temperament} little pirate who loved the harbor lights.")
    world.say(f"One afternoon, the crew prepared for a rehearsal at {world.setting.place}.")
    world.say(f"They had {prop.phrase}, and the chart felt important to everyone on deck.")


def _flashback(world: World, hero: Entity, prop: Prophecy) -> None:
    hero.memes["memory"] = hero.memes.get("memory", 0) + 1
    world.say(f"Then came a flashback: {hero.id} remembered the old storm that had split the bay fog.")
    world.say(f"In that memory, the {prop.label} had glimmered and shown {prop.reveals}.")


def _slink(world: World, hero: Entity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    world.say(f"{hero.id} tried to slink toward the shadow of a crate instead of joining the rehearsal.")


def _plumb_and_fix(world: World, hero: Entity, role: CrewRole, prop: Prophecy) -> bool:
    if role.can_plumb and prop.helps and "plumb" in prop.helps:
        hero.meters["confidence"] = hero.meters.get("confidence", 0) + 1
        world.say(f"The first mate told {hero.id} to plumb the chart's bend and trust the hidden route.")
        return True
    if role.can_magic and prop.magical:
        hero.meters["confidence"] = hero.meters.get("confidence", 0) + 1
        world.say(f"The captain used a bit of magic, and the moon lantern lit the stage like a guiding star.")
        return True
    return False


def tell_story(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    role = CREW[params.role]
    prop = PROPS[params.prophecy]
    hero = world.add(Entity(id=params.name, kind="character", type=role.id))
    prop_ent = world.add(Entity(id="prop", type=prop.id, label=prop.label, phrase=prop.phrase, owner=hero.id))
    hero.meters["confidence"] = 0
    world.facts.update(hero=hero, role=role, prop=prop, place=params.place, prop_ent=prop_ent)
    _setup(world, hero, role, prop)
    world.para()
    _slink(world, hero)
    _flashback(world, hero, prop)
    fixed = _plumb_and_fix(world, hero, role, prop)
    world.para()
    if fixed:
        world.say(f"{hero.id} stepped out from hiding and joined the rehearsal with a grin.")
        world.say(f"By sunset, the pirates beat their drums in time, and the {prop.label} shone over the water.")
    else:
        world.say(f"The rehearsal stayed wobbly, because there was no real plumb or magic to set it right.")
    world.facts["resolved"] = fixed
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, role, prop = f["hero"], f["role"], f["prop"]
    return [
        f'Write a short pirate tale for a young child about a rehearsal, a slinking deckhand, and a magical fix.',
        f"Tell a story where {hero.id} the {role.title} tries to slink away, then learns to plumb the problem with {prop.label}.",
        f'Write a gentle pirate story that includes a flashback, the word "plumb", and a cheerful ending at {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, role, prop = f["hero"], f["role"], f["prop"]
    return [
        QAItem(
            question=f"Who tried to slink away from the rehearsal?",
            answer=f"{hero.id} did. {hero.id} was the {role.title} and first looked nervous, then found courage again.",
        ),
        QAItem(
            question=f"What made the flashback important in the story?",
            answer=f"The flashback reminded {hero.id} of an old storm and showed why {prop.label} mattered for the harbor rehearsal.",
        ),
        QAItem(
            question=f"How did the crew fix the trouble at {world.setting.place}?",
            answer=(
                f"They used {('plumb' if role.can_plumb else 'magic')} to solve it, so {hero.id} could join the rehearsal "
                f"and the pirates finished together."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to rehearse?",
            answer="To rehearse means to practice before a show or performance so everyone can do it well.",
        ),
        QAItem(
            question="What does it mean to slink?",
            answer="To slink means to move quietly and sneakily, often because someone feels shy or afraid.",
        ),
        QAItem(
            question="What does it mean to plumb a problem?",
            answer="To plumb a problem means to look deeply into it and figure out what is really going on.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when the story remembers something that happened before.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("\n== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}\nA: {item.answer}")
    parts.append("\n== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(place="harbor", role="firstmate", prophecy="chart", name="Nell"),
    StoryParams(place="dock", role="captain", prophecy="lantern", name="Rook"),
    StoryParams(place="harbor", role="deckhand", prophecy="chart", name="Pip"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
