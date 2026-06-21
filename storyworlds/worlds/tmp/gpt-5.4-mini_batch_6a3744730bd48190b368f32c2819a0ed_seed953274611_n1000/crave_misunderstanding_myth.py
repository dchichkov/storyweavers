#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/crave_misunderstanding_myth.py
===============================================================

A small mythic storyworld about a child who *craves* a thing, a
misunderstanding that stings, and a wiser ending that clears the air.

The world is built for child-facing stories in a myth style:
- a humble hero
- a small sacred need
- a misunderstanding that causes tension
- a revealing turn
- a bright ending image that proves the change

It supports:
- default run
- -n / --all / --seed
- --trace / --qa / --json
- --asp / --verify / --show-asp
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    title: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"strain": 0.0, "glow": 0.0, "scar": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"longing": 0.0, "hurt": 0.0, "fear": 0.0, "peace": 0.0, "understanding": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "goddess"}
        male = {"boy", "father", "king", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    mood: str
    holds: str


@dataclass
class Craving:
    id: str
    crave_word: str
    object_word: str
    scent: str
    need: str
    sacred: bool = False


@dataclass
class Misunderstanding:
    id: str
    mistaken_reading: str
    rumor: str
    hurt_line: str
    truth_line: str


@dataclass
class Remedy:
    id: str
    method: str
    effect: str
    ending_image: str
    gentle: bool = True


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_strain(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["longing"] >= THRESHOLD and hero.meters["strain"] < THRESHOLD:
        hero.meters["strain"] += 1
        hero.memes["hurt"] += 1
        out.append("")
    return out


def _r_misread(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("misread") and "misread" not in world.fired:
        world.fired.add(("misread",))
        hero = world.get("hero")
        other = world.get("other")
        hero.memes["hurt"] += 1
        other.memes["fear"] += 1
    return out


CAUSAL_RULES = [Rule("strain", _r_strain), Rule("misread", _r_misread)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def ask_craving(world: World, hero: Entity, craving: Craving) -> None:
    hero.memes["longing"] += 1
    world.say(
        f"In the old days of the hills, {hero.id} gazed toward the {craving.object_word}. "
        f"At once {hero.pronoun()} began to {craving.crave_word} {craving.object_word}, "
        f"for its {craving.scent} called like a small bell in the dark."
    )


def open_myth(world: World, place: Place, hero: Entity, other: Entity, craving: Craving) -> None:
    world.say(
        f"Long ago, at {place.label}, where the air was {place.mood} and the stones kept old songs, "
        f"{hero.id} and {other.id} lived beside {place.holds}."
    )
    world.say(
        f"Each night, {hero.id} looked at the {craving.object_word} and felt a deep want in {hero.pronoun('possessive')} chest."
    )


def misunderstanding(world: World, hero: Entity, other: Entity, myth: Misunderstanding) -> None:
    world.facts["misread"] = True
    hero.meters["strain"] += 1
    other.memes["fear"] += 1
    world.say(
        f"But {other.id} saw {hero.id} reaching for it and spoke too quickly: "
        f'"{myth.mistaken_reading}."'
    )
    world.say(
        f"The words fell like cold rain. {myth.hurt_line}"
    )


def reveal(world: World, hero: Entity, other: Entity, craving: Craving, myth: Misunderstanding) -> None:
    hero.memes["understanding"] += 1
    other.memes["understanding"] += 1
    world.say(
        f"Then {hero.id} lifted {hero.pronoun('possessive')} hands and spoke the truth: "
        f'"{myth.truth_line} {craving.need}."'
    )
    world.say(
        f"So the two of them stood together, and the hard thing became simple."
    )


def resolve(world: World, hero: Entity, other: Entity, craving: Craving, remedy: Remedy) -> None:
    hero.memes["peace"] += 1
    other.memes["peace"] += 1
    hero.meters["strain"] = 0.0
    world.say(
        f"{remedy.method.capitalize()}, and the old worry loosened like rope in warm rain."
    )
    world.say(
        f"{remedy.effect} {remedy.ending_image}"
    )
    world.say(
        f"At last, {hero.id} could {craving.crave_word} {craving.object_word} without shame, "
        f"and the night shone soft and kind around them."
    )


def tell(place: Place, craving: Craving, myth: Misunderstanding, remedy: Remedy) -> World:
    world = World()
    hero = world.add(Entity(id="Mara", kind="character", type="girl", label="Mara", role="hero", traits=["gentle"]))
    other = world.add(Entity(id="Taro", kind="character", type="boy", label="Taro", role="witness", traits=["hasty"]))
    world.add(Entity(id="sun", kind="thing", type="thing", label="sun-gold", role="gift"))
    open_myth(world, place, hero, other, craving)
    world.para()
    ask_craving(world, hero, craving)
    misunderstanding(world, hero, other, myth)
    propagate(world)
    world.para()
    reveal(world, hero, other, craving, myth)
    resolve(world, hero, other, craving, remedy)
    world.facts.update(
        hero=hero, other=other, place=place, craving=craving, myth=myth, remedy=remedy,
        outcome="healed", misread=True, seed=0
    )
    return world


@dataclass
class StoryParams:
    place: str
    craving: str
    misunderstanding: str
    remedy: str
    seed: Optional[int] = None


PLACES = {
    "hill_shrine": Place(id="hill_shrine", label="the hill shrine", mood="blue and wind-bright", holds="a small stone altar"),
    "river_bank": Place(id="river_bank", label="the river bank", mood="silver and listening", holds="reed shadows"),
    "orchard": Place(id="orchard", label="the orchard", mood="warm and hushed", holds="old fruit trees"),
}

CRAVINGS = {
    "honey": Craving(id="honey", crave_word="crave", object_word="the honey jar", scent="sweetness", need="She wanted the honey to soothe a tired heart", sacred=True),
    "starlight": Craving(id="starlight", crave_word="crave", object_word="the star bowl", scent="moon-cold light", need="She wanted the bowl to guide a night walk", sacred=True),
    "bread": Craving(id="bread", crave_word="crave", object_word="the bread loaf", scent="warm crust", need="She wanted the bread to share with the hungry", sacred=True),
}

MISUNDERSTANDINGS = {
    "greedy": Misunderstanding(id="greedy", mistaken_reading="You are being greedy", rumor="greed", hurt_line="Mara bowed her head, and the bright want inside her turned heavy.", truth_line="I do not crave it for myself alone; I crave it because"),
    "theft": Misunderstanding(id="theft", mistaken_reading="You mean to steal it", rumor="steal", hurt_line="Taro stepped back, ashamed of his own fear.", truth_line="I meant only to ask for it with respect; I crave it because"),
}

REMEDIES = {
    "sharing": Remedy(id="sharing", method="Mara broke the bread and shared it", effect="The rumor vanished at once.", ending_image="the two children ate beneath the stars, and their shadows sat close like friends."),
    "truth_fire": Remedy(id="truth_fire", method="Taro listened and lit a small truth-fire in his heart", effect="The lie melted away.", ending_image="the shrine lantern glowed, and the wind seemed to nod."),
}

def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, c, m) for p in PLACES for c in CRAVINGS for m in MISUNDERSTANDINGS if CRAVINGS[c].sacred]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world about craving and misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--craving", choices=CRAVINGS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--remedy", choices=REMEDIES)
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid mythic combinations.")
    place = args.place or rng.choice(list(PLACES))
    craving = args.craving or rng.choice(list(CRAVINGS))
    misunderstanding = args.misunderstanding or rng.choice(list(MISUNDERSTANDINGS))
    remedy = args.remedy or rng.choice(list(REMEDIES))
    if (place, craving, misunderstanding) not in combos:
        raise StoryError("That mythic combination does not fit the story.")
    return StoryParams(place=place, craving=craving, misunderstanding=misunderstanding, remedy=remedy)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic story for a child where someone begins to crave {f["craving"].object_word} and a misunderstanding causes trouble.',
        f'Tell a gentle myth about {f["hero"].id} at {f["place"].label} that includes the word "crave".',
        f'Write a story where fear and misunderstanding are cleared by truth, and the ending feels ancient and kind.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question="What did Mara crave?", answer=f'Mara craved {f["craving"].object_word}. She wanted it for the reason named in the story, not because she was mean.'),
        QAItem(question="What went wrong?", answer=f'Taro misunderstood what Mara wanted and spoke too quickly. That made the air feel heavy until Mara told the truth.'),
        QAItem(question="How did the story end?", answer=f'It ended in peace and shared light. The misunderstanding was cleared, and the night felt safe again.'),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does crave mean?", answer="To crave something is to want it very much. In a story, that strong want can start the action."),
        QAItem(question="What is a misunderstanding?", answer="A misunderstanding happens when someone thinks the wrong thing is true. A kind explanation can clear it up."),
        QAItem(question="What style is this story in?", answer="It is told in a myth style, with old places, bright symbols, and a feeling that the world is larger than one day."),
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
    parts = ["--- world ---"]
    for e in world.entities.values():
        parts.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(parts)


ASP_RULES = r"""
valid(P,C,M) :- place(P), craving(C), misunderstanding(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CRAVINGS:
        lines.append(asp.fact("craving", c))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", m))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.craving not in CRAVINGS or params.misunderstanding not in MISUNDERSTANDINGS or params.remedy not in REMEDIES:
        raise StoryError("Invalid story params.")
    world = tell(PLACES[params.place], CRAVINGS[params.craving], MISUNDERSTANDINGS[params.misunderstanding], REMEDIES[params.remedy])
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="hill_shrine", craving="honey", misunderstanding="greedy", remedy="sharing", seed=1),
    StoryParams(place="river_bank", craving="starlight", misunderstanding="theft", remedy="truth_fire", seed=2),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not samples:
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
