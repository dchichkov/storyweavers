#!/usr/bin/env python3
"""
A small ghost-story world set in a theater, with a weeny haunting, rhymes,
and a transformation that turns fear into a performance.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the theater"
    affords: set[str] = field(default_factory=set)


@dataclass
class Act:
    id: str
    verb: str
    gerund: str
    trigger: str
    rhyme_line: str
    change: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    label: str
    phrase: str
    type: str
    fragile: bool = True
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Charm:
    id: str
    label: str
    prep: str
    tail: str
    turns: set[str]
    guards: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _add_meter(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = _meter(e, key) + amount


def _add_mem(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = _mem(e, key) + amount


def _do_act(world: World, hero: Entity, act: Act) -> None:
    if act.id not in world.setting.affords:
        raise StoryError(f"The theater cannot host {act.id}.")
    _add_meter(hero, act.change)
    _add_mem(hero, "wonder")
    if _meter(hero, "fear") >= THRESHOLD:
        _add_mem(hero, "shiver")
    world.say(f"{hero.id} {act.gerund}, and the air answered with a soft, strange hush.")


def _ghost_appears(world: World, ghost: Entity, act: Act) -> None:
    _add_mem(ghost, "lonely")
    _add_mem(ghost, "curious")
    world.say(
        f"From the dark curtain, a weeny ghost drifted out and hummed a rhyme: "
        f"“{act.rhyme_line}”"
    )


def _haunt(world: World, ghost: Entity, prop: Entity) -> None:
    _add_mem(prop, "spooky")
    _add_meter(prop, "tilt")
    world.say(f"The little ghost brushed past the {prop.label}, and it gave a tiny wobble.")


def _transform(world: World, hero: Entity, ghost: Entity, prop: Entity, charm: Charm) -> None:
    _add_mem(hero, "brave")
    _add_mem(hero, "joy")
    _add_mem(ghost, "belonging")
    prop.label = f"{prop.label} of lights"
    prop.phrase = f"a {prop.phrase} glowing with stage lights"
    world.say(
        f"{hero.id} answered the rhyme, and the ghost grew warmer, brighter, and less alone."
    )
    world.say(
        f"Then the theater changed: the old prop turned into {prop.phrase}, "
        f"and the spooky silence became applause."
    )
    world.say(
        f"{hero.id} and the weeny ghost used {charm.label} to finish the show, "
        f"and the haunted theater felt kind at last."
    )


def can_fix(act: Act, item: Item) -> bool:
    return act.change in {"spooky", "cold"} and item.fragile


def select_charm(act: Act, item: Item) -> Optional[Charm]:
    for c in CHARMS:
        if act.change in c.turns and "haunted" in c.guards:
            return c
    return None


@dataclass
class StoryParams:
    theater: str
    act: str
    prize: str
    name: str
    gender: str
    ghost_name: str
    seed: Optional[int] = None


THEATERS = {
    "main": Setting(place="the theater", affords={"rhyme", "transformation"}),
    "little": Setting(place="the little theater", affords={"rhyme", "transformation"}),
}

ACTS = {
    "rhyme": Act(
        id="rhyme",
        verb="listen to the rhyme",
        gerund="listened to the rhyme",
        trigger="heard the rhyme",
        rhyme_line="Step softly, keep the lights low, let the brave little heart grow",
        change="spooky",
        mood="uneasy",
        tags={"ghost", "theater", "rhyme"},
    ),
    "transformation": Act(
        id="transformation",
        verb="watch the transformation",
        gerund="watched the transformation",
        trigger="saw the change",
        rhyme_line="When a tune is true and kind, even shadows can unwind",
        change="bright",
        mood="wondering",
        tags={"ghost", "theater", "transform"},
    ),
}

ITEMS = {
    "mask": Item(label="mask", phrase="a paper mask", type="mask"),
    "cape": Item(label="cape", phrase="a velvet cape", type="cape"),
    "crown": Item(label="crown", phrase="a tiny crown", type="crown"),
}

CHARMS = [
    Charm(
        id="lantern",
        label="a lantern",
        prep="hold up a lantern",
        tail="held the lantern high",
        turns={"spooky", "cold"},
        guards={"haunted"},
    ),
    Charm(
        id="song",
        label="a warm song",
        prep="sing a warm song",
        tail="sang a warm song",
        turns={"spooky", "bright"},
        guards={"haunted"},
    ),
]

GIRL_NAMES = ["Mina", "Luna", "Nora", "Ivy", "Rose"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Max", "Jude"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for t in THEATERS:
        for a in ACTS:
            for p in ITEMS:
                if can_fix(ACTS[a], ITEMS[p]):
                    out.append((t, a, p))
    return out


def build_story(world: World, hero: Entity, ghost: Entity, act: Act, item: Entity, charm: Charm) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved the old {world.setting.place}."
    )
    world.say(
        f"Every night, {hero.pronoun('subject')} watched the stage curtains sway like sleepy clouds."
    )
    world.say(
        f"{hero.id} wore {hero.pronoun('possessive')} {item.label} for the show, because it made {hero.pronoun('object')} feel special."
    )
    world.say(
        f"One quiet evening, {hero.id} and {hero.pronoun('possessive')} grown-up stepped into {world.setting.place}."
    )
    _ghost_appears(world, ghost, act)
    world.say(
        f"{hero.id} wanted to {act.verb}, but the little ghost was already there, making the shadows dance."
    )
    _add_mem(hero, "fear")
    world.say(
        f"When {ghost.id} floated closer, {hero.id} held still and listened."
    )
    _haunt(world, ghost, item)
    world.say(
        f"Then {hero.id} remembered the rhyme and answered it in a clear voice."
    )
    _transform(world, hero, ghost, item, charm)


def tell(params: StoryParams) -> World:
    world = World(THEATERS[params.theater])
    act = ACTS[params.act]
    item_cfg = ITEMS[params.prize]
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    ghost = world.add(Entity(id=params.ghost_name, kind="character", type="ghost", meters={}, memes={}))
    item = world.add(Entity(id="prize", type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase, owner=hero.id))
    charm = select_charm(act, item_cfg)
    if charm is None:
        raise StoryError("No calm charm fits this haunted theater story.")
    build_story(world, hero, ghost, act, item, charm)
    world.facts.update(hero=hero, ghost=ghost, act=act, item=item, charm=charm, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["act"]
    item = f["item"]
    return [
        f'Write a gentle ghost story set in a theater with a weeny ghost and the word "{act.id}".',
        f"Tell a child-sized story where {hero.id} listens for a rhyme in the theater and changes from fear to wonder.",
        f"Write a story about a little stage costume, a shy ghost, and a transformation that ends in a happy performance.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ghost = f["ghost"]
    act = f["act"]
    item = f["item"]
    qas = [
        QAItem(
            question=f"Where does {hero.id}'s ghost story take place?",
            answer=f"It takes place in {world.setting.place}, where the curtains and stage make a spooky little home for the story.",
        ),
        QAItem(
            question=f"What kind of ghost did {hero.id} meet?",
            answer=f"{hero.id} met a weeny ghost named {ghost.id}, and the ghost floated out of the dark and spoke in a rhyme.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the ghost appeared?",
            answer=f"{hero.id} wanted to {act.verb}, but first there was a shivery moment in the theater.",
        ),
        QAItem(
            question=f"What happened to the {item.label} during the story?",
            answer=f"The {item.label} was nudged by the little haunting and then became part of the bright show at the end.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with a transformation: the spooky feeling turned warm, the ghost felt less lonely, and the theater felt kind.",
        ),
    ]
    return qas


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a theater?",
            answer="A theater is a place where people act, watch a show, and listen to stories and songs together.",
        ),
        QAItem(
            question="What does a rhyme do in a story?",
            answer="A rhyme uses words that sound alike at the ends, and it can make a story feel musical and magical.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or feeling into another, like spooky becoming bright and friendly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for p in sample.prompts:
        parts.append(p)
    parts.append("")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id} ({e.type}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
good_combo(T,A,P) :- theater(T), act(A), item(P), can_fix(A,P).
#show good_combo/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for t in THEATERS:
        lines.append(asp.fact("theater", t))
    for a in ACTS:
        lines.append(asp.fact("act", a))
        lines.append(asp.fact("can_fix", a, "mask"))
        lines.append(asp.fact("can_fix", a, "cape"))
        lines.append(asp.fact("can_fix", a, "crown"))
    for p in ITEMS:
        lines.append(asp.fact("item", p))
    return "\n".join(lines)


def asp_program(show: str = "#show good_combo/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "good_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - ac:
        print("only python:", sorted(py - ac))
    if ac - py:
        print("only asp:", sorted(ac - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story theater world with rhyme and transformation.")
    ap.add_argument("--theater", choices=THEATERS)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--prize", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--ghost-name")
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
    if args.theater is not None:
        combos = [c for c in combos if c[0] == args.theater]
    if args.act is not None:
        combos = [c for c in combos if c[1] == args.act]
    if args.prize is not None:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("No valid theater story matches those choices.")

    theater, act, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    ghost_name = args.ghost_name or rng.choice(["Moth", "Pip", "Whisp", "Mink"])
    return StoryParams(theater=theater, act=act, prize=prize, name=name, gender=gender, ghost_name=ghost_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(theater="main", act="rhyme", prize="mask", name="Mina", gender="girl", ghost_name="Moth"),
            StoryParams(theater="little", act="transformation", prize="cape", name="Theo", gender="boy", ghost_name="Pip"),
            StoryParams(theater="main", act="rhyme", prize="crown", name="Luna", gender="girl", ghost_name="Whisp"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
