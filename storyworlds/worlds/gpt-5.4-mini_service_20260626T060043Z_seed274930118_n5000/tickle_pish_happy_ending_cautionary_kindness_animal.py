#!/usr/bin/env python3
"""
A small animal-story world about a playful tickle, a cautionary warning, and a kind ending.

Seed-tale premise:
A little animal friend wants to tickle another animal at playtime.
A grown-up warns that the wrong kind of tickle can lead to a pish-squirt or a worried fuss.
The child chooses kindness instead, and the story ends happily with everyone calm and smiling.

This world keeps the prose child-facing and state-driven:
- meters track physical conditions like slippery, startled, and pish
- memes track emotional conditions like joy, worry, trust, and kindness
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    sounds: str = ""
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk_meter: str
    caution: str
    consequence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    hero: str
    hero_type: str
    adult: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(place="the garden", indoors=False, sounds="soft birdsong", affords={"tickle"}),
    "barn": Setting(place="the barn", indoors=True, sounds="quiet straw-rustle", affords={"tickle"}),
    "yard": Setting(place="the yard", indoors=False, sounds="gentle breeze", affords={"tickle"}),
}

ACTIONS = {
    "tickle": Action(
        id="tickle",
        verb="tickle",
        gerund="tickling",
        rush="reach out to tickle",
        risk_meter="startled",
        caution="a too-hasty tickle can scare a small animal",
        consequence="pish",
        tags={"tickle", "kindness", "cautionary", "happy_ending"},
    ),
}

PRIZES = {
    "skunk": Prize(id="skunk", label="skunk", phrase="a little striped skunk", type="skunk"),
    "bunny": Prize(id="bunny", label="bunny", phrase="a soft gray bunny", type="bunny"),
    "duckling": Prize(id="duckling", label="duckling", phrase="a round yellow duckling", type="duckling"),
}

HEROES = {
    "kitten": ("kitten", "kitten"),
    "puppy": ("puppy", "puppy"),
    "lamb": ("lamb", "lamb"),
    "foxkit": ("fox kit", "foxkit"),
}

ADULTS = {
    "mother": "mother",
    "father": "father",
    "aunt": "aunt",
    "uncle": "uncle",
}

TRAITS = ["playful", "curious", "gentle", "cheerful", "sweet"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_startled(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    prize = world.get("prize")
    action = world.facts["action"]
    if hero.meters.get("tickle", 0) < THRESHOLD:
        return out
    if prize.type == "skunk":
        sig = ("startled", hero.id, prize.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        prize.meters["startled"] = prize.meters.get("startled", 0) + 1
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        out.append(f"The little skunk lifted its tail and looked ready to pish.")
    return out


def _r_pish(world: World) -> list[str]:
    out: list[str] = []
    prize = world.get("prize")
    if prize.meters.get("startled", 0) < THRESHOLD:
        return out
    sig = ("pish", prize.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.meters["pish"] = prize.meters.get("pish", 0) + 1
    out.append(f"pish! A tiny warning-squirt popped into the air.")
    return out


RULES = [Rule("startled", _r_startled), Rule("pish", _r_pish)]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                produced.extend(lines)
                changed = True
    for s in produced:
        world.say(s)
    return produced


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: tickle, caution, kindness, happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--adult", choices=ADULTS)
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("caution", aid, a.caution))
        lines.append(asp.fact("consequence", aid, a.consequence))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("animal", pid, p.type))
    for hid, (label, htype) in HEROES.items():
        lines.append(asp.fact("hero", hid))
        lines.append(asp.fact("hero_type", hid, htype))
    return "\n".join(lines)


ASP_RULES = r"""
can_story(S,A,P,H) :- affords(S,A), action(A), prize(P), hero(H), P = skunk.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_story/4."))
    return sorted(set(asp.atoms(model, "can_story")))


def reasonableness_gate(place: str, action: str, prize: str, hero: str) -> None:
    if action != "tickle" or prize != "skunk":
        raise StoryError("This world only tells the skunk tickle story, where caution and kindness matter.")
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    if hero not in HEROES:
        raise StoryError("Unknown hero.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    action = args.action or "tickle"
    prize = args.prize or "skunk"
    hero = args.hero or rng.choice(list(HEROES))
    adult = args.adult or rng.choice(list(ADULTS))
    reasonableness_gate(place, action, prize, hero)
    return StoryParams(place=place, action=action, prize=prize, hero=hero, hero_type=HEROES[hero][1], adult=adult)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero_name, hero_type = HEROES[params.hero]
    adult_type = ADULTS[params.adult]
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, meters={}, memes={"joy": 1}))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label=params.adult, memes={"trust": 1}))
    prize = world.add(Entity(id="prize", kind="character", type="skunk", label="skunk", phrase=PRIZES[params.prize].phrase, memes={"calm": 1}))
    world.facts.update(params=params, hero=hero, adult=adult, prize=prize, action=ACTIONS[params.action])
    world.say(f"At {world.setting.place}, the air felt full of {world.setting.sounds}.")
    world.say(f"A little {hero.label} was feeling {random.choice(TRAITS)} and wanted to {ACTIONS[params.action].verb} the skunk.")
    world.say(f"{adult.label.capitalize()} smiled and said, “Be careful. {ACTIONS[params.action].caution}.”")
    world.para()
    hero.meters["tickle"] = 1
    world.say(f"The little {hero.label} reached out anyway, but not too fast.")
    if params.prize == "skunk":
        world.say(f"The skunk twitched, then everyone paused before anything turned messy.")
    propagate(world)
    world.para()
    world.say(f"{hero.label.capitalize()} put the paw down and used a feather instead, which was much kinder.")
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    prize.memes["calm"] = prize.memes.get("calm", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["worry"] = 0
    world.say(f"The skunk stayed calm, no pish came out, and the three friends laughed together at the end.")
    return world


def prompts(world: World) -> list[str]:
    return [
        'Write a short animal story about a tickle, a warning, and a kind choice.',
        'Tell a gentle story where a young animal wants to tickle a skunk but learns to be careful.',
        'Write a happy-ending animal story that includes the words "tickle" and "pish".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    adult = f["adult"]
    return [
        QAItem(
            question=f"Who wanted to tickle the skunk at {world.setting.place}?",
            answer=f"The little {hero.label} wanted to tickle the skunk.",
        ),
        QAItem(
            question=f"Why did {adult.label} warn the little {hero.label}?",
            answer="Because a too-hasty tickle can scare a small animal and make the day turn into a pish of worry.",
        ),
        QAItem(
            question="What made the ending happy?",
            answer="The little animal chose kindness, used a feather instead of a rough tickle, and everyone stayed calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing actions that help others feel safe, calm, and cared for.",
        ),
        QAItem(
            question="What is a caution?",
            answer="A caution is a warning that helps someone avoid trouble or harm.",
        ),
        QAItem(
            question="What is a pish?",
            answer="In this story, pish is a tiny warning-squirt or soft spray that happens when a small animal gets startled.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
    StoryParams(place="garden", action="tickle", prize="skunk", hero="kitten", hero_type="kitten", adult="mother"),
    StoryParams(place="yard", action="tickle", prize="skunk", hero="puppy", hero_type="puppy", adult="father"),
]


def asp_verify() -> int:
    py = {("garden", "tickle", "skunk", "kitten"), ("yard", "tickle", "skunk", "puppy")}
    cl = set(asp_valid())
    if cl == py:
        print(f"OK: ASP matches Python ({len(cl)} story shapes).")
        return 0
    print("Mismatch between ASP and Python.")
    print("only in ASP:", sorted(cl - py))
    print("only in Python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show can_story/4."))
        for row in sorted(set(asp.atoms(model, "can_story"))):
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
