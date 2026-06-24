#!/usr/bin/env python3
"""
A compact storyworld: a tiny comedy about an artist, a repeating crash, a
surprise, and a lesson learned.

The world is intentionally small and classical:
- one child-like protagonist
- one fragile goal
- repeated attempts that keep crashing
- a surprise reveal
- a clear lesson learned at the end
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wore: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    crash_word: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectPrize:
    label: str
    phrase: str
    type: str
    fragile: bool = True


@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


SETTINGS = {
    "studio": Setting("the studio", {"paint", "tower"}),
    "kitchen": Setting("the kitchen", {"cookies", "tower"}),
    "garage": Setting("the garage", {"tower", "cart"}),
}

ACTIVITIES = {
    "tower": Activity(
        id="tower",
        verb="build a taller tower",
        gerund="building towers",
        rush="run back for one more block",
        mess="cluttered",
        crash_word="crash",
        keyword="tower",
        tags={"crash", "lesson", "repeat", "surprise", "comedy"},
    ),
    "paint": Activity(
        id="paint",
        verb="paint a big poster",
        gerund="painting pictures",
        rush="grab another brush",
        mess="spotted",
        crash_word="splat",
        keyword="paint",
        tags={"surprise", "comedy"},
    ),
    "cookies": Activity(
        id="cookies",
        verb="stack cookie boxes",
        gerund="stacking boxes",
        rush="add one more box",
        mess="crumbly",
        crash_word="crash",
        keyword="cookies",
        tags={"crash", "repeat", "comedy"},
    ),
    "cart": Activity(
        id="cart",
        verb="push the squeaky cart",
        gerund="pushing the cart",
        rush="give it one more push",
        mess="wobbly",
        crash_word="bang",
        keyword="cart",
        tags={"crash", "surprise", "comedy"},
    ),
}

PRIZES = {
    "blocks": ObjectPrize("blocks", "a neat stack of blocks", "blocks", True),
    "posters": ObjectPrize("posters", "a roll of bright posters", "posters", True),
    "cookies": ObjectPrize("cookies", "a tray of cookies", "cookies", True),
    "cups": ObjectPrize("cups", "a tower of cups", "cups", True),
}

GIRL_NAMES = ["Mia", "Luna", "Ada", "Nia", "Tess", "Maya"]
BOY_NAMES = ["Leo", "Noah", "Owen", "Finn", "Max", "Eli"]
TRAITS = ["curious", "cheerful", "bouncy", "silly"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_crash(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    prize = world.get("prize")
    if hero.meters.get("clumsy", 0) < THRESHOLD:
        return out
    sig = ("crash", prize.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.meters["broken"] = prize.meters.get("broken", 0) + 1
    hero.memes["embarrassed"] = hero.memes.get("embarrassed", 0) + 1
    out.append(f"Their {prize.label} went crash.")
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes.get("trying_again", 0) < THRESHOLD:
        return out
    sig = ("repeat")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["determined"] = hero.memes.get("determined", 0) + 1
    out.append("They tried again, because a funny problem is still a problem.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters.get("broken", 0) < THRESHOLD:
        return out
    sig = ("lesson")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["lesson_learned"] = 1
    out.append("They learned to make a smaller plan first.")
    return out


CAUSAL_RULES = [
    Rule("crash", _r_crash),
    Rule("repeat", _r_repetition),
    Rule("lesson", _r_lesson),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


def tell(setting: Setting, activity: Activity, prize_cfg: ObjectPrize,
         name: str, gender: str, parent: str) -> World:
    world = World(setting)
    hero = world.add(Entity("hero", kind="character", type=gender, label=name))
    adult = world.add(Entity("adult", kind="character", type=parent, label=parent))
    prize = world.add(Entity("prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))
    world.facts.update(hero=hero, adult=adult, prize=prize, activity=activity, setting=setting)

    world.say(f"{hero.label} was a little artist who loved {activity.gerund}.")
    world.say(f"One day, {hero.label} wanted to {activity.verb}, and {adult.label} brought {prize.phrase}.")
    world.para()
    world.say(f"At {setting.place}, {hero.label} tried to {activity.verb}.")
    hero.meters["clumsy"] = 1
    hero.memes["trying_again"] = 1
    world.say(f"Then came the first {activity.crash_word}.")
    propagate(world, narrate=True)
    world.para()
    world.say(f"{hero.label} tried again.")
    hero.meters["clumsy"] = 1
    hero.memes["trying_again"] = 1
    world.say(f"Then came another {activity.crash_word}.")
    propagate(world, narrate=True)
    world.para()
    world.say(f"At last, {adult.label} pointed to the tiny mistake and smiled.")
    world.say(f'"Maybe a smaller start would work," said {adult.label}.')
    hero.meters["broken"] = max(hero.meters.get("broken", 0), 1)
    propagate(world, narrate=True)
    world.say(
        f"{hero.label} made a smaller plan, and this time the room stayed tidy. "
        f"{hero.label} laughed at the silly lesson learned."
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f"Write a funny story about {hero.label}, an artist who keeps having a {act.crash_word}.",
        f"Tell a comedy story where someone tries to {act.verb} but learns a lesson after the mess.",
        f"Write a short repeated-try story with a surprise ending and a clear lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    adult = f["adult"]
    prize = f["prize"]
    act = f["activity"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, a little artist who kept trying to {act.verb}.",
        ),
        QAItem(
            question=f"What kept happening when {hero.label} tried to {act.verb}?",
            answer=f"Things kept going {act.crash_word}, so the attempt had to be tried more than once.",
        ),
        QAItem(
            question=f"What did {adult.label} help {hero.label} learn?",
            answer=f"{adult.label} helped {hero.label} learn to start smaller, so the final plan worked better.",
        ),
        QAItem(
            question=f"What surprise happened at the end?",
            answer=f"The surprise was that the real fix was simple: a smaller plan kept {prize.label} safe and the room tidy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crash?",
            answer="A crash is a loud, sudden bump or break, like when something falls down with a bang.",
        ),
        QAItem(
            question="Why do people try again after a mistake?",
            answer="People try again because practice can help them do better the next time.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a useful idea someone remembers after something goes wrong.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: {e.label or e.type} meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("studio", "tower", "blocks", "Mia", "girl", "mother"),
    StoryParams("kitchen", "cookies", "cups", "Leo", "boy", "father"),
    StoryParams("garage", "cart", "posters", "Ada", "girl", "father"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: crash, repetition, surprise, and lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    activity = args.activity or rng.choice(sorted(SETTINGS[setting].affords))
    if activity not in SETTINGS[setting].affords:
        raise StoryError("That activity does not fit the setting.")
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, activity=activity, prize=prize, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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


ASP_RULES = r"""
setting(studio). setting(kitchen). setting(garage).
affords(studio,tower). affords(studio,paint). affords(studio,cookies).
affords(kitchen,tower). affords(kitchen,cookies).
affords(garage,tower). affords(garage,cart).

valid(S,A,P) :- affords(S,A), prize(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
        for a in sorted(SETTINGS[s].affords):
            lines.append(asp.fact("affords", s, a))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    python_set = {(s, a, p) for s in SETTINGS for a in SETTINGS[s].affords for p in PRIZES}
    try:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        clingo_set = set(asp.atoms(model, "valid"))
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    if clingo_set == python_set:
        print(f"OK: ASP matches Python ({len(clingo_set)} combos).")
        return 0
    print("Mismatch.")
    print("only in asp:", sorted(clingo_set - python_set))
    print("only in py:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

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

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
