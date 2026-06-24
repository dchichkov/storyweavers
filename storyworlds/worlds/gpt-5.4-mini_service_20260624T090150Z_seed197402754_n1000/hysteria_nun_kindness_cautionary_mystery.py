#!/usr/bin/env python3
"""
A small mystery-story world: a child, a nun, a misunderstood clue, and a calm,
kind resolution.

The domain is intentionally tiny and constraint-driven: a cautious search can
prevent a scare, while kindness can turn hysteria into trust.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "nun"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old cloister"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    risk: str
    reveals: str
    location: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    clue: str
    hero_name: str
    hero_type: str
    nun_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery world: kindness, caution, and a small scare.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--nun-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    "cloister": Setting(place="the old cloister", indoors=True, affords={"lantern", "echo"}),
    "garden": Setting(place="the quiet garden", indoors=False, affords={"lantern", "note"}),
}

CLUES = {
    "hysteria": Clue(
        id="hysteria",
        label="hysteria",
        phrase="a fluttery note about a missing bell",
        risk="a panic",
        reveals="the missing bell was only behind a curtain",
        location="the chapel",
        tags={"hysteria", "mystery", "cautionary"},
    ),
    "nun": Clue(
        id="nun",
        label="nun",
        phrase="the nun's candle and key ring",
        risk="a mix-up",
        reveals="the key ring had fallen under a prayer bench",
        location="the hall",
        tags={"nun", "kindness", "mystery"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Tess", "Nora", "Ivy", "Clara"]
BOY_NAMES = ["Eli", "Theo", "Noah", "Ben", "Owen", "Finn"]
NUN_NAMES = ["Sister Agnes", "Sister Ruth", "Sister Clare", "Sister Miriam"]


ASP_RULES = r"""
at_risk(C) :- clue(C), reveals(C, _).
calm_plan(C) :- at_risk(C), kindness(C), caution(C).
valid_story(P, C) :- place(P), clue(C), calm_plan(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c in CLUES.values():
        lines.append(asp.fact("clue", c.id))
        lines.append(asp.fact("reveals", c.id, c.reveals))
        if "kindness" in c.tags:
            lines.append(asp.fact("kindness", c.id))
        if "cautionary" in c.tags:
            lines.append(asp.fact("caution", c.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in SETTINGS for c in CLUES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.clue and args.clue not in CLUES:
        raise StoryError("Unknown clue.")
    place = args.place or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    nun_name = args.nun_name or rng.choice(NUN_NAMES)
    return StoryParams(place=place, clue=clue, hero_name=name, hero_type=gender, nun_name=nun_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CLUES[params.clue], params.hero_name, params.hero_type, params.nun_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle mystery for a young child that includes the word "{f["clue"].label}".',
        f"Tell a story where {f['hero'].id} and {f['nun'].id} use kindness and caution to calm a scare.",
        f"Write a short story about a nun, a child, and a clue in {world.setting.place}.",
    ]


def _set(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + value


def tell(setting: Setting, clue_cfg: Clue, hero_name: str, hero_type: str, nun_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    nun = world.add(Entity(id=nun_name, kind="character", type="nun", label=nun_name))
    clue = world.add(Entity(id="clue", type="thing", label=clue_cfg.label, phrase=clue_cfg.phrase))
    world.facts.update(hero=hero, nun=nun, clue=clue_cfg)

    world.say(
        f"In {setting.place}, {hero.id} noticed {clue_cfg.phrase}. "
        f"{nun.id} was nearby, and {nun.pronoun('subject').capitalize()} had a calm way of looking at small troubles."
    )

    world.para()
    _set(hero, "worry", 1)
    _set(nun, "kindness", 1)
    world.say(
        f"Then the room filled with hysteria when someone whispered that {clue_cfg.label} meant something bad. "
        f"{hero.id} felt the worry jump in {hero.pronoun('possessive')} chest, but {nun.id} lifted a hand and said, "
        f'"Let us be careful and look first."'
    )

    world.para()
    _set(hero, "caution", 1)
    _set(nun, "caution", 1)
    world.say(
        f"{hero.id} and {nun.id} followed the clue slowly, step by step. "
        f"They looked behind the curtain, under the bench, and beside the chapel door."
    )

    world.para()
    _set(hero, "joy", 1)
    _set(nun, "joy", 1)
    world.say(
        f"At last, they found that {clue_cfg.reveals}. "
        f"The scare melted away, because kindness had helped the search and caution had kept everyone safe."
    )

    world.para()
    world.say(
        f"{hero.id} smiled, and {nun.id} smiled back. "
        f"The old {clue_cfg.label} was no longer a mystery at all; it was only a reminder that quiet questions can stop a big fright."
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    nun = f["nun"]
    clue = f["clue"]
    return [
        QAItem(
            question=f"Who helped {hero.id} when the hysteria started?",
            answer=f"{nun.id} helped {hero.id} by staying calm and using kindness instead of joining the panic.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice in {world.setting.place}?",
            answer=f"{hero.id} noticed {clue.phrase}, which started the little mystery.",
        ),
        QAItem(
            question=f"What happened after they looked carefully?",
            answer=f"They found that {clue.reveals}, so the scary rumor turned out to be harmless.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nun?",
            answer="A nun is a woman who lives in a religious community and often spends time praying, teaching, and helping others.",
        ),
        QAItem(
            question="What does kindness do in a tense moment?",
            answer="Kindness can make people feel safer, softer, and more ready to listen when they are scared.",
        ),
        QAItem(
            question="Why should people be cautious when something looks strange?",
            answer="Caution helps people check carefully before they jump to a scary conclusion.",
        ),
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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="cloister", clue="hysteria", hero_name="Mina", hero_type="girl", nun_name="Sister Agnes"),
    StoryParams(place="garden", clue="nun", hero_name="Theo", hero_type="boy", nun_name="Sister Ruth"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:\n")
        for p, c in combos:
            print(f"  {p:10} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
