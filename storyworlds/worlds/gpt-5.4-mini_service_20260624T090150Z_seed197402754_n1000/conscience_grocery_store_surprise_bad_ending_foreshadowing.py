#!/usr/bin/env python3
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    name: str = ""
    label: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the grocery store"
    affords: set[str] = field(default_factory=lambda: {"aisle_case", "checkout", "quiet_watch"})


@dataclass
class Clue:
    kind: str
    phrase: str
    truth: str
    suspicious: bool = True


@dataclass
class Suspect:
    id: str
    label: str
    role: str
    has_item: bool = False
    nervous: bool = False


@dataclass
class StoryParams:
    clue: str
    suspect: str
    hero_name: str
    hero_type: str
    partner_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


CONSCIENCE = "conscience"

CLUES = {
    "missing_coupon": Clue("missing_coupon", "a torn coupon by the cereal shelf", "the cashier's drawer"),
    "spilled_milk": Clue("spilled_milk", "a white puddle near the milk", "a broken carton"),
    "mystery_note": Clue("mystery_note", "a folded note behind the apples", "a list from a helper"),
}

SUSPECTS = {
    "cashier": Suspect("cashier", "the cashier", "cashier"),
    "helper": Suspect("helper", "the stock helper", "helper"),
    "child": Suspect("child", "a small child", "child"),
}

GIRL_NAMES = ["Maya", "Nora", "Lena", "Ivy", "Ada", "Ruby"]
BOY_NAMES = ["Eli", "Noah", "Toby", "Miles", "Finn", "Owen"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective-style grocery store story with conscience, foreshadowing, a surprise, and a bad ending.")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--partner", choices=["mother", "father", "aunt", "uncle"])
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
    return [(c, s) for c in CLUES for s in SUSPECTS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.suspect:
        if args.clue == "spilled_milk" and args.suspect == "cashier":
            raise StoryError("The cashier cannot honestly be the spilled-milk culprit here; choose a different suspect.")
    combos = valid_combos()
    if args.clue:
        combos = [c for c in combos if c[0] == args.clue]
    if args.suspect:
        combos = [c for c in combos if c[1] == args.suspect]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    clue, suspect = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    partner = args.partner or rng.choice(["mother", "father", "aunt", "uncle"])
    hero_type = gender
    return StoryParams(clue=clue, suspect=suspect, hero_name=name, hero_type=hero_type, partner_type=partner)


def aspiration(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(f"{hero.name} liked the grocery store because every aisle hid a small mystery.")


def foreshadow(world: World, hero: Entity, clue: Clue) -> None:
    world.say(f"At the start, {hero.name} noticed {clue.phrase}, and {hero.pronoun('possessive')} conscience whispered to pay attention.")
    world.say("That tiny feeling was a clue that the day would not stay simple.")


def investigate(world: World, hero: Entity, suspect: Suspect, clue: Clue) -> None:
    hero.meters["attention"] = hero.meters.get("attention", 0) + 1
    world.say(f"{hero.name} followed the trail past the canned beans and watched {suspect.label} near the carts.")
    world.say(f"{hero.name}'s conscience said to look again before jumping to a conclusion.")


def surprise_turn(world: World, hero: Entity, suspect: Suspect, clue: Clue) -> None:
    suspect.nervous = True
    world.say(f"Then came the surprise: {suspect.label} was not stealing the thing at all.")
    world.say(f"The real problem was {clue.truth}, and {hero.name} had missed it at first.")


def bad_ending(world: World, hero: Entity, clue: Clue, partner: str) -> None:
    hero.memes["regret"] = hero.memes.get("regret", 0) + 1
    world.say(f"{hero.name} tried to fix everything too late, but the cart still bumped the stack of jars.")
    world.say(f"One glass jar cracked, the manager frowned, and even {partner} could only sigh at the mess.")
    world.say(f"In the end, the case was closed badly: the store had to clean up, and {hero.name} learned that rushing can make a small mystery worse.")


def tell_story(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, name=params.hero_name))
    partner = world.add(Entity(id="partner", kind="character", type=params.partner_type, name=params.partner_type))
    suspect = SUSPECTS[params.suspect]
    clue = CLUES[params.clue]

    world.facts.update(hero=hero, partner=partner, suspect=suspect, clue=clue)

    world.say(f"One afternoon, {hero.name} and {params.partner_type} went to the grocery store for dinner supplies.")
    aspiration(world, hero)
    world.say(f"{hero.name} wanted to play detective, because the {CONSCIENCE} in {hero.pronoun('possessive')} chest liked fair answers.")
    world.para()
    foreshadow(world, hero, clue)
    investigate(world, hero, suspect, clue)
    world.para()
    surprise_turn(world, hero, suspect, clue)
    bad_ending(world, hero, clue, params.partner_type)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    suspect: Suspect = f["suspect"]  # type: ignore[assignment]
    return [
        f"Write a detective story set in a grocery store where {hero.name} follows a clue and listens to {CONSCIENCE}.",
        f"Tell a child-sized mystery that starts with {clue.phrase} and ends with a surprise about {suspect.label}.",
        "Write a short, tense grocery-store story with foreshadowing and a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    partner: Entity = f["partner"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    suspect: Suspect = f["suspect"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did {hero.name} and {partner.name} go at the start?",
            answer=f"They went to the grocery store to buy dinner supplies and look for a clue.",
        ),
        QAItem(
            question=f"What clue helped {hero.name} start acting like a detective?",
            answer=f"The clue was {clue.phrase}. It made {hero.name} pay attention and listen to {CONSCIENCE}.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was that {suspect.label} was not causing the main trouble; the real problem was {clue.truth}.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=f"The ending was bad because {hero.name} rushed to fix things, a jar cracked, and the store had to clean up the mess.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a grocery store?",
            answer="A grocery store is a shop where people buy food and other everyday things for home.",
        ),
        QAItem(
            question="What is conscience?",
            answer="Conscience is the quiet feeling inside that helps a person know what is fair, kind, or safe to do.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a little hint early on that something important will happen later.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} name={e.name} meters={e.meters} memes={e.memes}")
    lines.append("events:")
    lines.extend(f"  {x}" for x in world.trace)
    return "\n".join(lines)


ASP_RULES = r"""
clue(missing_coupon).
clue(spilled_milk).
clue(mystery_note).

suspect(cashier).
suspect(helper).
suspect(child).

valid(C,S) :- clue(C), suspect(S), not bad_pair(C,S).
bad_pair(spilled_milk,cashier).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


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
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print("\n== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


CURATED = [
    StoryParams(clue="missing_coupon", suspect="helper", hero_name="Maya", hero_type="girl", partner_type="mother"),
    StoryParams(clue="spilled_milk", suspect="child", hero_name="Eli", hero_type="boy", partner_type="father"),
    StoryParams(clue="mystery_note", suspect="cashier", hero_name="Nora", hero_type="girl", partner_type="aunt"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.clue} / {p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
