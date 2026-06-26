#!/usr/bin/env python3
"""
A small ghost-story world about a child, a pot, a spooky misunderstanding,
and the brave choice that clears it up.

Seed tale:
---
In the middle of a long month, a child heard strange bumps from an old pot
in the attic. The child thought a ghost was trapped inside. After a shaky
night, they looked closely, found the pot only held a loose tin spoon and a
windy draft, and felt brave enough to laugh at the mistake.
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
    hidden_in: Optional[str] = None
    openable: bool = False
    opened: bool = False
    contents: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the old house"
    rooms: list[str] = field(default_factory=lambda: ["hall", "attic", "kitchen"])


@dataclass
class StoryParams:
    month: str
    pot: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


@dataclass
class MonthPot:
    name: str
    month_index: int
    spooky: bool
    noisy: bool
    lid: str
    color: str
    place: str
    tags: set[str] = field(default_factory=set)


MONTHS = [
    MonthPot("January", 1, True, True, "tin lid", "silver", "the attic", {"month", "ghost"}),
    MonthPot("February", 2, True, False, "rusty lid", "gray", "the pantry", {"month", "ghost"}),
    MonthPot("March", 3, False, True, "wooden lid", "brown", "the hallway", {"month"}),
    MonthPot("April", 4, True, True, "cracked lid", "black", "the attic", {"month", "ghost"}),
]

POTS = {
    "teapot": MonthPot("teapot", 0, True, True, "tin lid", "dull brass", "the attic", {"pot", "ghost"}),
    "flowerpot": MonthPot("flowerpot", 0, False, True, "clay rim", "red clay", "the window", {"pot"}),
    "cookingpot": MonthPot("cooking pot", 0, True, True, "metal lid", "dark metal", "the kitchen", {"pot", "ghost"}),
}

GHOST_HINTS = {
    "ghost": "a ghost might be hiding nearby",
    "breeze": "a breeze might be making the noise",
    "shadow": "a shadow might be playing tricks",
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Lila", "Hazel", "June"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Milo", "Finn", "Arlo"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def monologue(world: World, hero: Entity, text: str) -> None:
    hero.memes["thinking"] = hero.memes.get("thinking", 0.0) + 1
    world.say(f"{hero.pronoun('subject').capitalize()} thought, \"{text}\"")


def bravery(world: World, hero: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    world.say(f"{hero.pronoun('subject').capitalize()} took a brave breath and stepped closer.")


def misunderstanding(world: World, hero: Entity, pot: Entity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(
        f"The sound from the {pot.label} made {hero.id} sure something spooky was inside."
    )


def open_pot(world: World, hero: Entity, pot: Entity) -> None:
    if not pot.openable:
        raise StoryError("This pot cannot be opened in a believable way.")
    pot.opened = True
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    if "ghost" in pot.contents:
        world.say(f"{hero.id} opened the {pot.label}, but only saw an empty, harmless space.")
    else:
        world.say(f"{hero.id} opened the {pot.label} and found the noise had a simple cause.")


def reveal(world: World, hero: Entity, pot: Entity) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(
        f"Inside the {pot.label} was a loose spoon and a draft from a cracked window, "
        f"not a ghost at all."
    )
    world.say(f"{hero.id} laughed softly because the scary month had only been playing a trick.")


def tell(setting: Setting, month: MonthPot, pot_cfg: MonthPot,
         hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    pot = world.add(Entity(
        id="pot",
        type="pot",
        label=pot_cfg.name,
        phrase=pot_cfg.name,
        owner=parent.id,
        openable=True,
        contents=["spoon", "draft"] if pot_cfg.spooky else ["soil"],
    ))

    world.say(
        f"In {month.name}, {hero.id} lived in {setting.place} and kept listening to little house sounds."
    )
    world.say(
        f"There was an old {pot.label} tucked away where the shadows were deepest."
    )
    monologue(world, hero, "What if a ghost is trapped in that pot?")
    misunderstanding(world, hero, pot)

    world.para()
    world.say(
        f"That night, the bumps came again, and {hero.id}'s heart beat fast."
    )
    bravery(world, hero)
    open_pot(world, hero, pot)
    reveal(world, hero, pot)

    world.para()
    world.say(
        f"By the end of {month.name}, {hero.id} could walk past the old {pot.label} without fear."
    )
    world.say(
        f"The pot stayed only a pot, and {hero.id} stayed brave enough to look twice before worrying."
    )

    world.facts.update(month=month, pot=pot_cfg, hero=hero, parent=parent, pot_entity=pot)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    month = f["month"]
    pot = f["pot"]
    return [
        f'Write a ghost-story for a young child set in {month.name} with an old {pot.name} and a gentle surprise.',
        f"Tell a spooky-but-kind story about {hero.id} and a {pot.name} that seems haunted but turns out not to be.",
        f'Write a short story that includes the words "month" and "pot" and ends with bravery replacing fear.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    month = f["month"]
    pot = f["pot"]
    return [
        QAItem(
            question=f"What made {hero.id} think the {pot.name} was spooky?",
            answer=f"{hero.id} heard strange bumps from the {pot.name}, so {hero.pronoun('subject')} thought a ghost might be inside.",
        ),
        QAItem(
            question=f"What did {hero.id} do before opening the {pot.name}?",
            answer=f"{hero.id} took a brave breath, stepped closer, and opened the {pot.name} instead of running away.",
        ),
        QAItem(
            question=f"What was the real reason for the noise in {month.name}?",
            answer="The noise came from a loose spoon and a draft from a cracked window, not from a ghost.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a month?",
            answer="A month is one part of the year. People use months to keep track of time as the days go by.",
        ),
        QAItem(
            question="What is a pot?",
            answer="A pot is a container people use for cooking, holding plants, or storing small things.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel scared.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but the real reason is different.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in your head that says what you are thinking.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.openable:
            bits.append(f"openable={e.openable}")
        if e.opened:
            bits.append("opened=True")
        if e.contents:
            bits.append(f"contents={e.contents}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Facts:
% month/1, pot/1, spooky_pot/1, noisy_pot/1

spooky_story(M, P) :- month(M), pot(P), spooky_pot(P), noisy_pot(P).
has_misunderstanding(M, P) :- spooky_story(M, P).
brave_turn(M, P) :- has_misunderstanding(M, P).
resolved(M, P) :- brave_turn(M, P).
#show spooky_story/2.
#show has_misunderstanding/2.
#show brave_turn/2.
#show resolved/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for m in MONTHS:
        lines.append(asp.fact("month", m.name.lower()))
    for p in POTS.values():
        lines.append(asp.fact("pot", p.name.replace(" ", "_").lower()))
        if p.spooky:
            lines.append(asp.fact("spooky_pot", p.name.replace(" ", "_").lower()))
        if p.noisy:
            lines.append(asp.fact("noisy_pot", p.name.replace(" ", "_").lower()))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/2."))
    atoms = sorted(set(asp.atoms(model, "resolved")))
    expected = [(m.name.lower(), p.name.replace(" ", "_").lower()) for m in MONTHS for p in POTS.values() if m.spooky and p.spooky]
    if atoms == expected:
        print(f"OK: ASP parity matches Python ({len(atoms)} cases).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  asp:", atoms)
    print("  py :", expected)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: month, pot, inner monologue, bravery, misunderstanding.")
    ap.add_argument("--month", choices=[m.name.lower() for m in MONTHS])
    ap.add_argument("--pot", choices=list(POTS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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


def valid_combos() -> list[tuple[str, str]]:
    return [(m.name.lower(), p) for m in MONTHS for p, cfg in POTS.items() if cfg.spooky and cfg.noisy and m.spooky]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.month:
        combos = [c for c in combos if c[0] == args.month]
    if args.pot:
        combos = [c for c in combos if c[1] == args.pot]
    if not combos:
        raise StoryError("No valid month/pot combination matches the given options.")
    month, pot = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(month=month, pot=pot, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    month = next(m for m in MONTHS if m.name.lower() == params.month)
    pot_cfg = POTS[params.pot]
    world = tell(Setting(), month, pot_cfg, params.name, params.gender, params.parent)
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
    StoryParams(month="january", pot="teapot", name="Mina", gender="girl", parent="mother"),
    StoryParams(month="april", pot="cookingpot", name="Owen", gender="boy", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/2."))
        for atom in sorted(set(asp.atoms(model, "resolved"))):
            print(atom)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
