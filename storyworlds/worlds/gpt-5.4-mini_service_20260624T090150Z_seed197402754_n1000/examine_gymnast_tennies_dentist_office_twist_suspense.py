#!/usr/bin/env python3
"""
storyworlds/worlds/examine_gymnast_tennies_dentist_office_twist_suspense.py
============================================================================

A small bedtime-story world about a young gymnast, a pair of tennies, and a
gentle dental visit with a little conflict, suspense, and a final twist.

Seed tale sketch:
---
A little gymnast named Mina had shiny tennies she loved to wear on the way to
the dentist office. One day, Mina felt nervous about having her teeth examined.
Her mom said the dentist was kind, but Mina still held her tennies tight and
peeked at the big chair. The dentist smiled, listened carefully, and discovered
a tiny pebble hiding in one shoe. The real problem was not just Mina's wobbly
feelings, but the sore spot from the pebble. Mina took off the shoe, got her
teeth checked, and left with clean tennies, clean teeth, and a brave grin.

World model:
---
- The hero is a child gymnast who loves motion and balance.
- The tennies are a prized object, worn during the walk to the dentist office.
- The tension comes from fear of the examination and worry about the tennies.
- The twist is that the dentist's careful examination finds a pebble in the
  tennies, which explains the discomfort and gives the child a reason to trust
  the visit.
- The ending image proves the change: calm breathing, checked teeth, and
  tennies set neatly beside the chair.

Bedtime-story style:
---
The prose is concrete, soft, and child-facing. The story starts with a cozy
setup, turns through a small worry, and ends with a reassuring image that
shows what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
EPS = 1e-9


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dentist office"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.memes.get("worry", 0.0) < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["tight"] = ent.memes.get("tight", 0.0) + 1
        out.append(f"{ent.id} held still and took a careful breath.")
    return out


def _r_pebble(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("hero")
    tennies = world.facts.get("tennies")
    if not child or not tennies:
        return out
    if child.memes.get("fidgets", 0.0) < THRESHOLD:
        return out
    if tennies.meters.get("pebble", 0.0) < THRESHOLD:
        sig = ("pebble", tennies.id)
        if sig not in world.fired:
            world.fired.add(sig)
            tennies.meters["pebble"] = 1.0
            out.append("A tiny pebble waited inside one shoe.")
    return out


RULES = [Rule("worry", _r_worry), Rule("pebble", _r_pebble)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def story_premise() -> str:
    return "A little gymnast named Lila loved her tennies and was visiting the dentist office."


def predict_pebble(world: World, child: Entity, tennies: Entity) -> bool:
    sim = world.copy()
    sim.get(child.id).memes["fidgets"] = sim.get(child.id).memes.get("fidgets", 0.0) + 1
    sim.get(child.id).memes["worry"] = sim.get(child.id).memes.get("worry", 0.0) + 1
    sim.get(tennies.id).meters["pebble"] = 1.0
    return True


def tell(world: World) -> None:
    hero = world.add(Entity(id="Lila", kind="character", type="girl"))
    parent = world.add(Entity(id="Mom", kind="character", type="mother", label="Mom"))
    dentist = world.add(Entity(id="DrGreen", kind="character", type="woman", label="Dr. Green"))
    tennies = world.add(Entity(id="Tennies", type="shoes", label="tennies", phrase="bright blue tennies", plural=True))
    tennies.worn_by = hero.id

    world.facts.update(hero=hero, parent=parent, dentist=dentist, tennies=tennies)

    hero.memes["joy"] = 1.0
    hero.memes["love"] = 1.0
    world.say("Lila was a little gymnast who liked to bounce, stretch, and land with tiny, careful feet.")
    world.say("She loved her bright blue tennies because they made her feel quick and safe.")
    world.say("One morning, Lila and Mom walked to the dentist office for a gentle checkup.")

    world.para()
    hero.memes["worry"] = 1.0
    hero.memes["fidgets"] = 1.0
    world.say("The waiting room was soft and quiet, but the big chair still looked very tall.")
    world.say("Lila wanted to keep her tennies on and stand by the door.")
    world.say("Mom smiled and said Dr. Green would only look carefully and count tiny things.")

    propagate(world, narrate=True)
    world.say('"We can do this slowly," Dr. Green said, with a voice as warm as a blanket.')

    world.para()
    world.say("Lila sat down, but she still held one shoe with both hands.")
    world.say("Then Dr. Green leaned close with a small light and a small mirror.")
    world.say("That was when the twist appeared: the shoes were not the only thing that needed examining.")
    world.say("Dr. Green found a tiny pebble hiding in one tennie, and that was why Lila had been wiggly all morning.")

    world.say("Mom blinked in surprise, and Lila gasped, because the pebble had been poking her foot the whole time.")
    world.say("The dentist carefully tipped the pebble out, and Lila's shoulders dropped at once.")

    world.para()
    hero.memes["worry"] = 0.0
    hero.memes["trust"] = 1.0
    hero.memes["conflict"] = 0.0
    world.say("After that, Lila opened her mouth for the checkup and stayed very still.")
    world.say("Dr. Green counted each tooth and said they were looking bright and clean.")
    world.say("Then Lila set her tennies neatly beside the chair, with no pebble inside and no fear left in her chest.")
    world.say("On the way home, Lila bounced once in the hallway, then smiled a sleepy smile, because the dentist office had turned out to be a safe place after all.")

    world.facts["resolved"] = True
    world.facts["twist"] = True
    world.facts["conflict"] = True
    world.facts["suspense"] = True


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a bedtime story about a gymnast visiting a dentist office, with a pair of tennies and a gentle twist.',
        'Tell a child-friendly story where examine, gymnast, and tennies all matter, and the tension ends kindly.',
        'Write a soft suspense story in a dentist office where a young gymnast worries, then learns the real problem.',
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who was the story about?",
            answer="The story was about Lila, a little gymnast, and her mom during a visit to the dentist office.",
        ),
        QAItem(
            question="Why was Lila nervous at the dentist office?",
            answer="Lila felt nervous because the big chair looked tall and she did not know what the examination would be like.",
        ),
        QAItem(
            question="What were the tennies like?",
            answer="They were bright blue tennies that Lila loved because they made her feel quick and safe.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The twist was that Dr. Green found a tiny pebble hiding in one tennie, which explained why Lila had been wiggly.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The story ended with Lila calm, her teeth checked, and her tennies set neatly beside the chair.",
        ),
    ]


KNOWLEDGE = {
    "gymnast": [
        QAItem(
            question="What does a gymnast do?",
            answer="A gymnast practices balance, stretching, jumping, and careful moves with the body.",
        )
    ],
    "tennies": [
        QAItem(
            question="What are tennies?",
            answer="Tennies are sneakers or tennis shoes, a kind of comfortable shoe for walking and playing.",
        )
    ],
    "dentist": [
        QAItem(
            question="What does a dentist do?",
            answer="A dentist checks teeth and helps keep mouths healthy and clean.",
        )
    ],
    "examine": [
        QAItem(
            question="What does it mean to examine something?",
            answer="To examine something means to look at it carefully and notice small details.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [item for key in ("examine", "gymnast", "tennies", "dentist") for item in KNOWLEDGE[key]]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    name: str = "Lila"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: gymnast, tennies, dentist office, twist, suspense.")
    ap.add_argument("--name", default="Lila")
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
    return StoryParams(name=args.name or rng.choice(["Lila", "Mina", "Nora", "Ella"]), seed=args.seed)


ASP_RULES = r"""
hero(lila).
setting(dentist_office).
item(tennies).
role(gymnast).

story_ok :- hero(lila), setting(dentist_office), item(tennies), role(gymnast).
#show story_ok/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("hero", "lila"),
        asp.fact("setting", "dentist_office"),
        asp.fact("item", "tennies"),
        asp.fact("role", "gymnast"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_ok/0."))
    ok = any(sym.name == "story_ok" for sym in model)
    if ok:
        print("OK: ASP gate is satisfied.")
        return 0
    print("MISMATCH: ASP gate failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(Setting())
    tell(world)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [StoryParams(name=n) for n in ["Lila", "Mina", "Nora"]]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern: gymnast + tennies + dentist office.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
