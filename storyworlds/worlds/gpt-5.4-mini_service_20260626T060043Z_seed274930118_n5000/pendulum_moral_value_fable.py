#!/usr/bin/env python3
"""
A tiny fable-like storyworld about a pendulum, a shared moral value, and the
way a small choice can change a whole town's heart.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class Choice:
    id: str
    action: str
    motion: str
    consequence: str
    moral_value: str
    mood_shift: str
    keyword: str = "pendulum"


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "heart"


@dataclass
class Helper:
    id: str
    label: str
    offer: str
    closing: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "village": Setting(place="the village square", detail="A little clock tower stood nearby, and its pendulum swayed in the breeze."),
    "garden": Setting(place="the quiet garden", detail="A stone path led past bright flowers and a small bell rope."),
    "school": Setting(place="the old schoolyard", detail="A tall hallway clock ticked above the doorway."),
}

CHOICES = {
    "honesty": Choice(
        id="honesty",
        action="tell the truth",
        motion="step forward and tell the truth",
        consequence="admits the mistake",
        moral_value="honesty",
        mood_shift="brave",
    ),
    "patience": Choice(
        id="patience",
        action="wait their turn",
        motion="stand still and wait kindly",
        consequence="shares the moment",
        moral_value="patience",
        mood_shift="calm",
    ),
    "kindness": Choice(
        id="kindness",
        action="help a friend",
        motion="reach out and help a friend",
        consequence="makes room for another",
        moral_value="kindness",
        mood_shift="warm",
    ),
}

PRIZES = {
    "bell": Prize(label="bell", phrase="a shiny brass bell", type="bell"),
    "seedbag": Prize(label="seedbag", phrase="a little bag of seeds", type="seedbag"),
    "apple": Prize(label="apple", phrase="a red apple for the teacher", type="apple"),
}

HELPERS = {
    "rabbit": Helper(id="rabbit", label="a rabbit helper", offer="offer a steadier way", closing="they all listened to the wise little rabbit"),
    "grandmother": Helper(id="grandmother", label="Grandmother", offer="suggest a gentler choice", closing="Grandmother smiled and spoke softly"),
    "clockmaker": Helper(id="clockmaker", label="the clockmaker", offer="show how to balance the gears", closing="the clockmaker pointed to the pendulum"),
}

NAMES = ["Milo", "Ada", "Nia", "Tomas", "Lena", "Omar", "Pip", "Rosa"]
TRAITS = ["small", "curious", "stubborn", "gentle", "bright", "thoughtful"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    choice: str
    prize: str
    name: str
    trait: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def hero_title(hero: Entity) -> str:
    return f"{next((t for t in hero.meters.keys() if False), '')}"


def choose_compatible(place: Optional[str], choice: Optional[str], prize: Optional[str]) -> list[tuple[str, str, str]]:
    combos = []
    for p in SETTINGS:
        for c in CHOICES:
            for r in PRIZES:
                if place and p != place:
                    continue
                if choice and c != choice:
                    continue
                if prize and r != prize:
                    continue
                combos.append((p, c, r))
    return combos


def predict(world: World, hero: Entity, choice: Choice, prize: Prize) -> dict[str, object]:
    sim = world.copy()
    sim.facts["tempted"] = True
    sim.facts["moral"] = choice.moral_value
    return {"moral_value": choice.moral_value, "risk": prize.label == "bell" and choice.id == "honesty"}


def reasonableness_gate(choice: Choice, prize: Prize) -> bool:
    # Fable logic: the value should matter to the prize/scene in some way.
    if choice.id == "honesty" and prize.label != "bell":
        return True
    if choice.id == "patience" and prize.label in {"seedbag", "apple"}:
        return True
    if choice.id == "kindness":
        return True
    return True


def story_intro(world: World, hero: Entity, choice: Choice) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes['trait']} child who lived near {world.setting.place}. "
        f"{hero.pronoun().capitalize()} loved the old pendulum clock because it swung back and forth like a patient little heart."
    )
    world.say(world.setting.detail)


def build_conflict(world: World, hero: Entity, choice: Choice, prize: Prize) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(
        f"One day, {hero.id} wanted to {choice.action}, but a harder choice came first. "
        f"The {prize.label} was there, and no one was watching."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} heart swung like the pendulum: one way toward taking the easy road, and the other toward {choice.moral_value}."
    )


def helper_offer(world: World, helper: Helper, hero: Entity, choice: Choice) -> None:
    world.say(
        f"Then {helper.label} arrived and seemed to {helper.offer}. "
        f'"The pendulum does not stay to one side," {helper.label} said. "A good heart can return too."'
    )


def resolve(world: World, hero: Entity, choice: Choice, prize: Prize, helper: Helper) -> None:
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    hero.memes["peace"] = hero.memes.get("peace", 0) + 1
    world.say(
        f"So {hero.id} chose to {choice.motion} instead. "
        f"{hero.id} {choice.consequence}, and {choice.moral_value} made the room feel lighter."
    )
    world.say(
        f"At the end, {helper.closing}, and the pendulum kept swinging while {hero.id}'s smile stayed steady. "
        f"The little town remembered that a kind choice can move a bigger world."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    choice = CHOICES[params.choice]
    prize = PRIZES[params.prize]
    helper = HELPERS[params.helper]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        memes={"trait": params.trait, "moral": 1.0},
    ))
    world.add(Entity(id="pendulum", kind="thing", type="pendulum", label="pendulum clock"))
    world.add(Entity(id="prize", kind="thing", type=prize.type, label=prize.label, phrase=prize.phrase))
    world.add(Entity(id="helper", kind="character", type="helper", label=helper.label))

    world.facts.update(
        hero=hero,
        choice=choice,
        prize=prize,
        helper=helper,
        setting=setting,
    )

    story_intro(world, hero, choice)
    world.para()
    build_conflict(world, hero, choice, prize)
    helper_offer(world, helper, hero, choice)
    world.para()
    resolve(world, hero, choice, prize, helper)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    choice: Choice = f["choice"]
    prize: Prize = f["prize"]
    return [
        f'Write a short fable for a child about a pendulum and the value of {choice.moral_value}.',
        f"Tell a gentle story where {hero.id} faces a choice about the {prize.label} and learns {choice.moral_value}.",
        f'Write a tiny moral tale that includes a pendulum clock, a small temptation, and a kind ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    choice: Choice = f["choice"]
    prize: Prize = f["prize"]
    helper: Helper = f["helper"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"What kind of story is this about {hero.id} at {setting.place}?",
            answer=f"It is a fable-like story about {hero.id}, the pendulum clock, and a choice about {choice.moral_value}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before making the better choice?",
            answer=f"{hero.id} wanted to {choice.action}, but then {hero.id} learned to think about {choice.moral_value} first.",
        ),
        QAItem(
            question=f"Who helped {hero.id} remember the right thing to do?",
            answer=f"{helper.label} helped by reminding {hero.id} that a good heart can return to the right side, like a pendulum.",
        ),
        QAItem(
            question=f"What stayed important at the end of the story?",
            answer=f"The pendulum kept swinging, and {hero.id} kept the lesson of {choice.moral_value} in mind.",
        ),
        QAItem(
            question=f"What was special about the {prize.label} in the story?",
            answer=f"The {prize.label} was part of the temptation, and choosing wisely mattered more than taking it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pendulum?",
            answer="A pendulum is a weight that swings back and forth, often inside a clock.",
        ),
        QAItem(
            question="What does honesty mean?",
            answer="Honesty means telling the truth, even when it feels hard.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means caring about others and helping them when you can.",
        ),
        QAItem(
            question="Why do stories use a moral value in a fable?",
            answer="Fables use a moral value to show a lesson about how to behave well.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------

ASP_RULES = r"""
moral_value(honesty).
moral_value(patience).
moral_value(kindness).

choice_ok(C) :- moral_value(C).

story_ok(P, C, R) :- setting(P), choice_ok(C), prize(R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for cid in CHOICES:
        lines.append(asp.fact("choice", cid))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    py = set((p, c, r) for p in SETTINGS for c in CHOICES for r in PRIZES)
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    return 1


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about a pendulum and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS := ["small", "curious", "stubborn", "gentle", "bright", "thoughtful"])
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(list(SETTINGS))
    choice = args.choice or rng.choice(list(CHOICES))
    prize = args.prize or rng.choice(list(PRIZES))
    helper = args.helper or rng.choice(list(HELPERS))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, choice=choice, prize=prize, name=name, trait=trait, helper=helper)


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
        print(asp_program("#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos")
        for combo in combos[:50]:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in SETTINGS:
            for c in CHOICES:
                for r in PRIZES:
                    params = StoryParams(place=p, choice=c, prize=r, name="Milo", trait="curious", helper="rabbit")
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
