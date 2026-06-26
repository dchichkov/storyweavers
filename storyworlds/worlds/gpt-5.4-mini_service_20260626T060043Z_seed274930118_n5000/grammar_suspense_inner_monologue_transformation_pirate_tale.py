#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/grammar_suspense_inner_monologue_transformation_pirate_tale.py
=========================================================================================================

A standalone pirate-tale storyworld about a small crew, a grammar clue, a
rising suspense beat, an inner monologue turn, and a transformation from
nervous deckhand to brave helper-captain.

Seed tale premise:
---
A young cabin kid finds a torn treasure map with a sentence that only makes
sense if the comma is in the right place. The ship is caught in fog, the crew
argues over the clue, and the kid quietly thinks through the grammar. When the
kid realizes the map says to turn after the reef, not before it, the crew
changes course, the storm clears, and the kid feels transformed into a real
pirate helper.

This script builds that premise as a small simulated world with meters and
memes, plus a Python reasonableness gate and an inline ASP twin.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
        if self.type in {"girl", "boy", "child", "deckhand", "kid"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"captain", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the misty sea"
    weather: str = "foggy"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    text: str
    verb: str
    turn: str
    warning: str
    keyword: str = "grammar"
    risky: bool = True


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    help_text: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        return c


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_fog(world: World) -> list[str]:
    out = []
    if world.setting.weather != "foggy":
        return out
    for e in world.entities.values():
        if e.kind == "character" and e.memes.get("doubt", 0) >= THRESHOLD:
            sig = ("fog", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["suspense"] = e.memes.get("suspense", 0) + 1
            out.append("The fog seemed to press closer, as if it wanted to hear the secret too.")
    return out


def _r_transformation(world: World) -> list[str]:
    out = []
    hero = world.facts.get("hero")
    if not hero:
        return out
    ent = world.get(hero.id)
    if ent.memes.get("courage", 0) >= THRESHOLD and ent.meters.get("understood", 0) >= THRESHOLD:
        sig = ("transform", ent.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        ent.memes["pride"] = ent.memes.get("pride", 0) + 1
        out.append(f"{ent.id} stood a little taller, feeling like a true pirate helper at last.")
    return out


CAUSAL_RULES = [Rule("fog", _r_fog), Rule("transformation", _r_transformation)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_understanding(world: World, hero: Entity, clue: Clue) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["doubt"] = sim.get(hero.id).memes.get("doubt", 0) + 1
    read_clue(sim, sim.get(hero.id), clue, narrate=False)
    return sim.get(hero.id).meters.get("understood", 0) >= THRESHOLD


def read_clue(world: World, hero: Entity, clue: Clue, narrate: bool = True) -> None:
    hero.meters["heard"] = hero.meters.get("heard", 0) + 1
    hero.meters["understood"] = hero.meters.get("understood", 0) + 1
    world.say(f"{hero.id} studied the torn map and noticed the little {clue.keyword} clue hiding in the sentence." if narrate else "")
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, captain: Entity, clue: Clue, prize: Prize) -> None:
    world.say(f"{hero.id} was a young deckhand aboard the {world.setting.place}, and {hero.pronoun('possessive')} {captain.label} watched the sails.")
    world.say(f"The crew had found a torn map with a line that read, '{clue.text}'.")
    world.say(f"{hero.id} loved the way {clue.keyword} could change a story, but {hero.pronoun('possessive')} {prize.label} was only a crumpled scrap in {hero.pronoun('possessive')} hands.")
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1


def suspense(world: World, hero: Entity, captain: Entity, clue: Clue, prize: Prize) -> None:
    world.para()
    world.say(f"Then the fog rolled in thick as wool, and the ship creaked toward the reef.")
    world.say(f"The captain frowned. 'If that comma is wrong, we'll turn too soon and smash the hull,' {captain.pronoun('subject')} said.")
    hero.memes["doubt"] = hero.memes.get("doubt", 0) + 1
    world.say(f"{hero.id}'s stomach fluttered. {hero.pronoun('subject').capitalize()} wondered if the clue was too small to matter.")
    world.say(f"Maybe everyone was looking at the sentence the wrong way, {hero.pronoun('subject')} thought.")
    if clue.warning:
        world.say(f"The warning felt sharp: {clue.warning}")


def inner_monologue(world: World, hero: Entity, clue: Clue, prize: Prize) -> bool:
    world.para()
    world.say(f"{hero.id} stared at the map and thought, 'A comma can change where the ship goes. If the words say to turn after the reef, then the reef comes first.'")
    world.say(f"'{clue.text}' could mean something safer, {hero.pronoun('subject')} realized.")
    understood = bool(re.search(r"after the reef", clue.text))
    if understood:
        hero.meters["grammar"] = hero.meters.get("grammar", 0) + 1
        hero.meters["understood"] = hero.meters.get("understood", 0) + 1
        hero.memes["courage"] = hero.memes.get("courage", 0) + 1
        world.say(f"{hero.id} took a brave breath, because the grammar made the route clear.")
    return understood


def transformation(world: World, hero: Entity, captain: Entity, clue: Clue, prize: Prize) -> None:
    world.para()
    world.say(f"{hero.id} spoke up at last. 'We should turn after the reef,' {hero.pronoun('subject')} said, pointing with a shaking finger that soon grew steady.")
    world.say(f"The captain checked the torn line again and nodded hard. 'By the black gulls, you're right.'")
    world.say(f"The helm swung the other way, the ship slipped past the reef, and the fog thinned like a curtain lifting.")
    world.say(f"{hero.id} felt changed, as if the little grammar clue had turned {hero.pronoun('possessive')} brave heart into a lantern.")
    world.say(f"Before long, the crew laughed, the sea opened wide, and {hero.id} was no longer just a deckhand with a scrap of paper; {hero.pronoun('subject').capitalize()} was the one who saved the course.")


SETTINGS = {
    "misty_sea": Setting(place="the Misty Sea", weather="foggy", affords={"read", "navigate"}),
    "harbor": Setting(place="the Harbor", weather="windy", affords={"read", "navigate"}),
}

CLUES = {
    "comma_turn": Clue(
        text="Turn after the reef, not before it.",
        verb="read the map",
        turn="turn after the reef",
        warning="One wrong pause could send the ship onto the rocks.",
        keyword="grammar",
    ),
    "rescue_sentence": Clue(
        text="Sail past the reef, then follow the gulls.",
        verb="read the map",
        turn="follow the gulls",
        warning="The crew must understand the sentence before the wind changes.",
        keyword="grammar",
    ),
}

PRIZES = {
    "map": Prize(label="map", phrase="a torn treasure map", region="hands"),
    "compass": Prize(label="compass", phrase="a brass compass", region="hands"),
}

GEAR = {
    "spyglass": Gear(id="spyglass", label="a spyglass", help_text="It helped the deckhand read the tiny marks on the map."),
    "lantern": Gear(id="lantern", label="a lantern", help_text="It lit the scrap so the comma could be seen."),
}

GIRL_NAMES = ["Mira", "Nell", "Ava", "Rose", "Tessa"]
BOY_NAMES = ["Finn", "Jory", "Pip", "Rowan", "Tobin"]
TRAITS = ["brave", "curious", "quiet", "shy", "bright"]


@dataclass
class StoryParams:
    setting: str
    clue: str
    prize: str
    name: str
    gender: str
    captain: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with grammar, suspense, inner monologue, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["captain"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    captain = args.captain or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, clue=clue, prize=prize, name=name, gender=gender, captain=captain, trait=trait)


def valid_combo(params: StoryParams) -> bool:
    return params.clue in CLUES and params.prize in PRIZES and params.setting in SETTINGS


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type="child", label="deckhand"))
    captain = world.add(Entity(id="Captain", kind="character", type="captain", label="captain"))
    prize = world.add(Entity(id="Prize", type="thing", label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=hero.id, caretaker=captain.id))
    clue = CLUES[params.clue]

    world.facts.update(hero=hero, captain=captain, prize=prize, clue=clue, params=params)

    setup(world, hero, captain, clue, prize)
    suspense(world, hero, captain, clue, prize)
    if not predict_understanding(world, hero, clue):
        raise StoryError("The clue never becomes clear enough to drive a believable transformation.")
    inner_monologue(world, hero, clue, prize)
    transformation(world, hero, captain, clue, prize)
    hero.memes["transformed"] = hero.memes.get("transformed", 0) + 1
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    return [
        f'Write a pirate tale for a young child that includes the word "grammar" and a hidden clue about a comma.',
        f"Tell a suspenseful story where {hero.id} listens to {clue.text.lower()} and finds the right place to turn the ship.",
        f"Write a short story with inner monologue in which a small pirate thinks through grammar and becomes brave.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, clue, prize = f["hero"], f["captain"], f["clue"], f["prize"]
    return [
        QAItem(
            question=f"What did {hero.id} notice on the torn {prize.label}?",
            answer=f"{hero.id} noticed a grammar clue on the torn {prize.label}: '{clue.text}'",
        ),
        QAItem(
            question=f"Why was the ship in danger before {hero.id} spoke up?",
            answer=f"The ship was in danger because the fog was thick and the crew might turn the wrong way at the reef.",
        ),
        QAItem(
            question=f"What changed after {hero.id} thought through the sentence?",
            answer=f"{hero.id} realized the ship should turn after the reef, told the captain, and the crew changed course safely.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt transformed and brave, like a real pirate helper.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is grammar?",
            answer="Grammar is the way words are put together so sentences make sense.",
        ),
        QAItem(
            question="What does a comma do?",
            answer="A comma is a small mark in writing that can show a pause or separate parts of a sentence.",
        ),
        QAItem(
            question="Why can fog be scary on a ship?",
            answer="Fog can hide rocks, reefs, and other ships, so sailors must move carefully.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H).
clue(C) :- clue_name(C).
prize(P) :- prize_name(P).

needs_grammar(H, C) :- hero(H), clue(C).
storm_risk(H) :- hero(H), foggy_sea.
understands(H, C) :- needs_grammar(H, C), comma_clue(C).

transformed(H) :- understands(H, C), brave(H).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("foggy_sea")]
    for name in GIRL_NAMES + BOY_NAMES:
        lines.append(asp.fact("character", name))
    for c in CLUES:
        lines.append(asp.fact("clue_name", c))
    for p in PRIZES:
        lines.append(asp.fact("prize_name", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show transformed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="misty_sea", clue="comma_turn", prize="map", name="Pip", gender="boy", captain="captain", trait="curious"),
            StoryParams(setting="harbor", clue="rescue_sentence", prize="map", name="Mira", gender="girl", captain="captain", trait="bright"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            i += 1
            if not valid_combo(p):
                continue
            sample = generate(p)
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
