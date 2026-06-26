#!/usr/bin/env python3
"""
Storyworld: fillet quest kindness fable

A small fable-world about a hungry little seeker, a precious fillet, and a
choice between cleverness and kindness. The world simulates a quest with a
physical prize and a moral turn: sharing, helping, or protecting someone else
from hunger.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carries: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "queen"}
        male = {"boy", "man", "father", "brother", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    mood: str = ""


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    keyword: str = "fillet"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    ownerable: bool = True


@dataclass
class Kindness:
    id: str
    offer: str
    result: str
    helps: str
    tags: set[str] = field(default_factory=set)


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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _act_quest(world: World, hero: Entity, quest: Quest) -> None:
    hero.meters["travel"] = hero.meters.get("travel", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(f"{hero.id} set out on a small quest to {quest.verb}.")


def _act_see_risk(world: World, hero: Entity, prize: Entity, quest: Quest) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"Then {hero.id} saw that the {prize.label} might be lost if nobody was careful; "
        f"the path ahead looked like {quest.risk}."
    )


def _act_kindness(world: World, helper: Entity, hero: Entity, kindness: Kindness, prize: Entity) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
    world.say(kindness.offer)
    world.say(kindness.result)
    prize.meters["safe"] = prize.meters.get("safe", 0.0) + 1


def _act_resolution(world: World, hero: Entity, prize: Entity, kindness: Kindness) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["greed"] = 0.0
    world.say(
        f"In the end, {hero.id} learned that a brave heart can be gentle too: "
        f"{kindness.helps}, and the {prize.label} stayed safe."
    )


def tell(
    setting: Setting,
    quest: Quest,
    prize: Prize,
    kindness: Kindness,
    hero_name: str,
    hero_type: str,
    helper_name: str,
    helper_type: str,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["small", "curious"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, traits=["kind", "patient"]))
    item = world.add(Entity(id="fillet", type=prize.type, label=prize.label, phrase=prize.phrase, owner=hero.id))

    world.say(
        f"Once there was a little {hero_type} named {hero.id}, who lived near {setting.place} "
        f"and dreamed of a {prize.label}."
    )
    world.say(f"{hero.id} loved a good {quest.keyword} and hoped to {quest.verb}.")
    world.para()
    _act_quest(world, hero, quest)
    _act_see_risk(world, hero, item, quest)
    world.say(
        f"{helper.id} noticed the trouble and chose kindness over hurry."
    )
    _act_kindness(world, helper, hero, kindness, item)
    world.para()
    _act_resolution(world, hero, item, kindness)
    world.say(
        f"That night, {hero.id} went home full of gratitude, and the {prize.label} was still there "
        f"to share."
    )

    world.facts.update(hero=hero, helper=helper, prize=item, quest=quest, kindness=kindness, setting=setting)
    return world


SETTINGS = {
    "riverbank": Setting(place="the riverbank", affords={"quest"}, mood="flowing"),
    "market": Setting(place="the market square", affords={"quest"}, mood="busy"),
    "cottage": Setting(place="the cottage door", affords={"quest"}, mood="quiet"),
}

QUESTS = {
    "fillet": Quest(
        id="fillet",
        verb="find the missing fillet",
        gerund="looking for the fillet",
        rush="dash down the path",
        risk="rocks, splashes, and a hungry delay",
        keyword="fillet",
        tags={"fillet", "quest"},
    ),
    "return": Quest(
        id="return",
        verb="return the fillet to the basket",
        gerund="carrying the fillet home",
        rush="hurry back",
        risk="a slippery stone and a long, wet step",
        keyword="fillet",
        tags={"fillet", "return"},
    ),
}

PRIZES = {
    "fillet": Prize(
        label="fillet",
        phrase="a fresh little fish fillet",
        type="food",
        ownerable=True,
    )
}

KINDNESSES = {
    "share": Kindness(
        id="share",
        offer="So the helper split the fillet in two, giving the smaller piece to the hungry one.",
        result="At once, the air felt warmer, because nobody had to stay hungry and worried.",
        helps="sharing made the quest kinder than winning alone",
        tags={"kindness", "share"},
    ),
    "carry": Kindness(
        id="carry",
        offer="So the helper lifted the fillet into a clean basket and walked beside the seeker.",
        result="That kept the treasure steady and made the road feel less hard.",
        helps="walking together kept the fillet safe",
        tags={"kindness", "carry"},
    ),
}

HERO_NAMES = ["Mina", "Toby", "Pip", "Lena", "Sera", "Niko"]
HELPER_NAMES = ["Grandma", "Old Reed", "Moss", "Aunt Joy", "Bram"]
TRAITS = ["gentle", "bold", "patient", "bright", "careful"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    prize: str
    kindness: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for q in QUESTS:
            for p in PRIZES:
                for k in KINDNESSES:
                    combos.append((s, q, p, k))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like quest world about a fillet and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["mouse", "fox", "boy", "girl", "rabbit"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["owl", "hare", "woman", "man", "turtle"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if args.kindness:
        combos = [c for c in combos if c[3] == args.kindness]
    if not combos:
        raise StoryError("No valid story matches the given options.")

    setting, quest, prize, kindness = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["mouse", "fox", "rabbit", "boy", "girl"])
    helper_type = args.helper_type or rng.choice(["owl", "hare", "woman", "man", "turtle"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        quest=quest,
        prize=prize,
        kindness=kindness,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        trait=trait,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short fable about {f['hero'].id}, a {f['hero'].type}, who searches for a fillet and learns kindness.",
        f"Tell a tiny quest story where a {f['hero'].type} named {f['hero'].id} wants to {f['quest'].verb}.",
        f"Create a child-friendly fable that includes a fillet, a helper, and a gentle act of kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, quest, kindness = f["hero"], f["helper"], f["prize"], f["quest"], f["kindness"]
    return [
        QAItem(
            question=f"Who went on the quest for the fillet?",
            answer=f"{hero.id}, a little {hero.type}, went on the quest for the {prize.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {quest.verb}.",
        ),
        QAItem(
            question=f"How did {helper.id} help?",
            answer=kindness.offer + " " + kindness.result,
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The {prize.label} stayed safe, and {hero.id} learned that kindness matters more than rushing alone.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fillet?",
            answer="A fillet is a boneless piece of fish or meat, usually cut into a neat strip.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, share, or care about someone else's feelings or needs.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to खोज? No—A quest is a search or mission to find or do something important.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- place(S).
quest(Q) :- quest_id(Q).
prize(P) :- prize_id(P).
kindness(K) :- kindness_id(K).

story_combo(S,Q,P,K) :- setting(S), quest(Q), prize(P), kindness(K).
#show story_combo/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("place", s))
    for q in QUESTS:
        lines.append(asp.fact("quest_id", q))
    for p in PRIZES:
        lines.append(asp.fact("prize_id", p))
    for k in KINDNESSES:
        lines.append(asp.fact("kindness_id", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_combo/4."))
    return sorted(set(asp.atoms(model, "story_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - asp_set))
    print("only asp:", sorted(asp_set - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    prize = PRIZES[params.prize]
    kindness = KINDNESSES[params.kindness]
    world = tell(setting, quest, prize, kindness, params.hero_name, params.hero_type, params.helper_name, params.helper_type)
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


CURATED = [
    StoryParams("riverbank", "fillet", "fillet", "share", "Mina", "mouse", "Grandma", "woman", "gentle"),
    StoryParams("market", "return", "fillet", "carry", "Pip", "rabbit", "Old Reed", "turtle", "careful"),
    StoryParams("cottage", "fillet", "fillet", "share", "Lena", "girl", "Aunt Joy", "woman", "bright"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_combo/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} combos")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.quest} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
