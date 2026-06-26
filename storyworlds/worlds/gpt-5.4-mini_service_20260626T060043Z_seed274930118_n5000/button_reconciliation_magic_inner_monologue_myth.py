#!/usr/bin/env python3
"""
storyworlds/worlds/button_reconciliation_magic_inner_monologue_myth.py
======================================================================

A small mythic story world about a magical button, a hard-feeling quarrel,
an inner murmur of doubt, and a reconciliation that changes the ending image.

Seed tale used to build the simulation:
---
Long ago, a child found a bright button in an old shrine. The button could
wake a sleeping lantern only if two people who had argued chose to mend their
hurt and press it together. At first the child wanted the magic for themself.
But the inner voice said the button would not listen to a selfish hand. So the
child went to the person they had quarreled with, spoke plainly, and made peace.
Then the button shone, the lantern woke, and the path home lit up like a small
star.
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
    owner: Optional[str] = None
    wears: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "sister", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "brother", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    image: str
    mood: str


@dataclass
class Relic:
    label: str
    phrase: str
    kind: str
    magic: str
    requires_reconciliation: bool = True


@dataclass
class StoryParams:
    setting: str
    relic: str = "button"
    name: str = "Mira"
    role: str = "girl"
    counterpart: str = "the elder"
    seed: Optional[int] = None


SETTINGS = {
    "shrine": Setting(place="the old shrine", image="a lantern asleep under carved stone", mood="hushed"),
    "grove": Setting(place="the moonlit grove", image="a path of roots and silver leaves", mood="soft"),
    "harbor": Setting(place="the harbor temple", image="waves tapping the pilings like fingers", mood="salt-bright"),
}

RELICS = {
    "button": Relic(
        label="button",
        phrase="a bright brass button with a star scratched on it",
        kind="button",
        magic="wake the sleeping lantern",
    ),
}

NAMES = ["Mira", "Tavi", "Ari", "Nola", "Sera", "Ivo", "Leif", "Kira"]
ROLE_OPTIONS = ["girl", "boy"]
COUNTERPARTS = ["the elder", "the lantern keeper", "the river aunt", "the shrine warden"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


def _inner_voice(world: World, hero: Entity, relic: Entity) -> None:
    if hero.memes.get("greed", 0.0) >= THRESHOLD and hero.memes.get("reconciliation", 0.0) < THRESHOLD:
        hero.memes["doubt"] = hero.memes.get("doubt", 0.0) + 1
        world.say(
            f"Inside {hero.pronoun('object')}, a small voice whispered that {relic.label} magic "
            f"would not answer a selfish hand."
        )


def _magic_checks(world: World, hero: Entity, relic: Entity, counterpart: Entity) -> bool:
    return hero.memes.get("reconciliation", 0.0) >= THRESHOLD and counterpart.memes.get("forgiveness", 0.0) >= THRESHOLD


def _wake_lantern(world: World, hero: Entity, relic: Entity) -> None:
    sig = ("wake", relic.id)
    if sig in world.fired:
        return
    if hero.meters.get("magic", 0.0) >= THRESHOLD and hero.memes.get("reconciliation", 0.0) >= THRESHOLD:
        world.fired.add(sig)
        relic.meters["glow"] = relic.meters.get("glow", 0.0) + 1
        world.facts["lantern_woke"] = True
        world.say("The button answered with a warm flash, and the sleeping lantern woke at once.")


def propagate(world: World) -> None:
    for e in world.entities.values():
        if e.type == "button":
            hero = world.get(world.facts["hero"])
            counterpart = world.get(world.facts["counterpart"])
            if _magic_checks(world, hero, e, counterpart):
                _wake_lantern(world, hero, e)


def tell(setting: Setting, relic_cfg: Relic, hero_name: str, role: str, counterpart_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=role, meters={"magic": 0.0}, memes={}))
    counterpart = world.add(Entity(id=counterpart_name, kind="character", type="priest", meters={}, memes={}))
    relic = world.add(Entity(id="relic", type=relic_cfg.kind, label=relic_cfg.label, phrase=relic_cfg.phrase, owner=hero.id))

    world.facts.update(hero=hero.id, counterpart=counterpart.id, relic=relic.id)

    world.say(f"Long ago, {hero.id} came to {setting.place}, where {setting.image}.")
    world.say(
        f"There {hero.pronoun('subject')} found {relic.phrase}. "
        f"It was said to {relic_cfg.magic}, but only after a quarrel was mended."
    )
    world.say(
        f"{hero.id} had argued with {counterpart_name} the day before, and the memory still felt sharp."
    )

    world.para()
    hero.memes["greed"] = 1.0
    world.say(
        f"{hero.id} wanted the magic all at once and held the button tight, as if wanting alone could make it obey."
    )
    _inner_voice(world, hero, relic)
    if hero.memes.get("doubt", 0.0) >= THRESHOLD:
        world.say(
            f"{hero.id} lowered {hero.pronoun('possessive')} hand and listened to that quiet warning."
        )

    world.para()
    hero.memes["reconciliation"] = 1.0
    counterpart.memes["forgiveness"] = 1.0
    hero.meters["magic"] = 1.0
    world.say(
        f"Then {hero.id} walked back to {counterpart_name}, bowed {hero.pronoun('possessive')} head, and spoke plainly: "
        f'"I was wrong. Will you forgive me?"'
    )
    world.say(
        f"{counterpart_name} looked at {hero.id} for a long moment, then nodded. "
        f'"I forgive you," {counterpart_name} said, and the air seemed to loosen.'
    )

    propagate(world)
    if not world.facts.get("lantern_woke"):
        world.say("The button stayed dark until the peace was real.")
    else:
        world.say(
            f"After that, {hero.id} and {counterpart_name} pressed the button together, and the path home shone."
        )

    world.facts.update(hero=hero, counterpart=counterpart, relic=relic)
    return world


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic story world: a magical button, an inner monologue, and a reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS, default="button")
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLE_OPTIONS)
    ap.add_argument("--counterpart")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    relic = args.relic or "button"
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLE_OPTIONS)
    counterpart = args.counterpart or rng.choice(COUNTERPARTS)
    return StoryParams(setting=setting, relic=relic, name=name, role=role, counterpart=counterpart)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], RELICS[params.relic], params.name, params.role, params.counterpart)
    hero = world.facts["hero"]
    counterpart = world.facts["counterpart"]
    relic = world.facts["relic"]
    story = world.render()
    prompts = [
        f"Write a short myth for children about a {params.relic} that only works after reconciliation.",
        f"Tell a gentle legendary story where {hero.id} must choose between keeping magic and making peace.",
        f"Write a simple myth with an inner monologue, a magical {params.relic}, and a healed quarrel.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {hero.id} hesitate before using the {relic.label}?",
            answer=(
                f"{hero.id} wanted the magic for {hero.pronoun('object')}, but a quiet inner voice warned "
                f"that the {relic.label} would not wake the lantern for a selfish hand."
            ),
        ),
        QAItem(
            question=f"What changed so the {relic.label} could work?",
            answer=(
                f"{hero.id} apologized to {counterpart.id}, and {counterpart.id} forgave {hero.pronoun('object')}. "
                f"Once their quarrel was mended, the magic answered."
            ),
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=(
                f"The {relic.label} flashed warm light, the lantern woke, and the path home shone after the peace was made."
            ),
        ),
    ]
    world_qa = [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who were upset mend their hurt and make peace again.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice of a character's own thoughts inside their head.",
        ),
        QAItem(
            question="What does magic mean in a myth?",
            answer="In a myth, magic is a special power that can do surprising things, often with rules or meaning.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H).
counterpart(C) :- character(C), not hero(C).
button(B) :- relic(B).
has_doubt(H) :- meme(H,reconciliation,1), meme(H,greed,1), character(H).
reconciled(H,C) :- meme(H,reconciliation,1), meme(C,forgiveness,1), character(H), character(C).
lantern_wakes(B) :- button(B), reconciled(H,C), magic(H,1).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("relic_kind", rid, r.kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    asp_settings = set(asp.atoms(model, "setting"))
    py_settings = set((k,) for k in SETTINGS)
    if asp_settings == py_settings:
        print(f"OK: ASP and Python agree on settings ({len(py_settings)}).")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP:", sorted(asp_settings))
    print("PY :", sorted(py_settings))
    return 1


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
    StoryParams(setting="shrine", name="Mira", role="girl", counterpart="the elder"),
    StoryParams(setting="grove", name="Tavi", role="boy", counterpart="the lantern keeper"),
    StoryParams(setting="harbor", name="Kira", role="girl", counterpart="the river aunt"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show setting/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
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
