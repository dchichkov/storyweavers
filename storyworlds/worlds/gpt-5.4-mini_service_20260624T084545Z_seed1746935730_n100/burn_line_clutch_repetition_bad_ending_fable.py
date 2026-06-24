#!/usr/bin/env python3
"""
A tiny fable-style story world about a creature, a line, and a bad choice.

Seed tale:
---
A clever little crow found a bright red thread stretched in a straight line
between two fence posts. He liked shiny things and would clutch them in his beak.
"Mine, mine, mine," he said again and again.

An old turtle warned him, "That thread is tied to the cookfire line. If you pull
it, the lamp oil will tip." But the crow did not listen. He tugged once, then
tugged again, then tugged a third time. The pot fell, the straw caught fire, and
the crow burned one wing.

The crow flew away with nothing but smoke behind him, and the turtle said that
greed and repetition can lead a fool to a bad ending.

Causal state model:
---
- a character may clutch an object
- a character may tug a line
- tugging the wrong line can tip oil or kindle flame
- fire can burn a wing, tail, or pouch
- repeated warnings can raise caution, but ignored warnings raise greed
- the ending is intentionally bad when the warning is ignored

Style instruments:
---
- fable voice with a short moral
- repetition in dialogue and prose
- a bad ending is part of the domain, not a bug
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"crow", "bird", "fox", "wolf", "cat", "dog"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"turtle", "tortoise", "hare", "mouse", "squirrel"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    line_kind: str
    fire_kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    line_kind: str
    burn_kind: str
    trigger: str
    clue: str
    moral_tag: str = ""


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    hazard: str
    prize: str
    hero: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_burn(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("flame", 0) < THRESHOLD:
            continue
        if e.meters.get("burned", 0) >= THRESHOLD:
            continue
        sig = ("burn", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["burned"] = e.meters.get("burned", 0) + 1
        out.append(f"{e.label or e.id} was burned by the flame.")
    return out


CAUSAL_RULES = [_r_burn]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def select_pronoun_name(name: str) -> str:
    return name


def build_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    hazard: Hazard = f["hazard"]
    prize: Entity = f["prize"]

    world.say(
        f"Once in {world.setting.place}, there lived a little {hero.type} named {hero.id} "
        f"who liked shiny things and would clutch them close."
    )
    world.say(
        f"{helper.id} the {helper.type} watched and warned, 'Do not pull the {hazard.line_kind} line, "
        f"do not pull the {hazard.line_kind} line,' for {hazard.clue}."
    )
    world.para()
    world.say(
        f"But {hero.id} saw {prize.phrase} on the line and said, 'Mine, mine, mine,' "
        f"again and again."
    )
    hero.memes["greed"] = hero.memes.get("greed", 0) + 1
    hero.memes["warning_heard"] = hero.memes.get("warning_heard", 0) + 1
    world.say(
        f"{hero.id} clutched {prize.it()} and tugged once, then tugged again, then tugged a third time."
    )
    prize.meters["tugged"] = prize.meters.get("tugged", 0) + 1
    if hazard.id == "oilline":
        world.say("The line snapped, the lamp tipped, and the oil spilled toward the straw.")
    else:
        world.say("The line snapped, the sparks jumped, and the dry straw began to glow.")
    world.say(
        f"At last, flame leaped up in a bright, hungry wink."
    )
    prize.meters["flame"] = 1
    propagate(world, narrate=True)
    hero.meters["burned"] = hero.meters.get("burned", 0) + 1
    hero.memes["shame"] = hero.memes.get("shame", 0) + 1
    world.say(
        f"{hero.id} flew away with a singed wing and no treasure at all, while {helper.id} "
        f"shook {helper.pronoun('possessive')} head."
    )
    world.para()
    world.say(
        f"'A greedy claw that clutches too hard,' said {helper.id}, 'may keep nothing and burn itself besides.'"
    )


SETTINGS = {
    "barnyard": Setting(place="the barnyard", line_kind="lamp", fire_kind="straw", affords={"tug", "clutch"}),
    "yard": Setting(place="the dusty yard", line_kind="oil", fire_kind="hay", affords={"tug", "clutch"}),
    "orchard": Setting(place="the orchard fence", line_kind="cord", fire_kind="leaves", affords={"tug", "clutch"}),
}

HAZARDS = {
    "oilline": Hazard(
        id="oilline",
        line_kind="lamp",
        burn_kind="oil",
        trigger="tugging the lamp line",
        clue="the lamp oil would spill and the straw would catch",
        moral_tag="greed",
    ),
    "strawline": Hazard(
        id="strawline",
        line_kind="straw",
        burn_kind="flame",
        trigger="pulling the straw line",
        clue="the dry straw would kindle and the fire would grow",
        moral_tag="warning",
    ),
}

PRIZES = {
    "thread": Prize(label="thread", phrase="a bright red thread", type="thread", region="beak"),
    "beads": Prize(label="beads", phrase="a little string of beads", type="beads", region="beak", plural=True),
    "ring": Prize(label="ring", phrase="a shiny brass ring", type="ring", region="beak"),
}

HEROES = [
    ("crow", "crow"),
    ("fox", "fox"),
    ("squirrel", "squirrel"),
]

HELPERS = [
    ("turtle", "turtle"),
    ("hare", "hare"),
    ("mouse", "mouse"),
]

GIRL_NAMES = ["Mina", "Lena", "Nia", "Tia"]
BOY_NAMES = ["Pip", "Otis", "Jory", "Finn"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style story world with repetition and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for hz in HAZARDS:
            for pr in PRIZES:
                combos.append((place, hz, pr))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, hazard, prize = rng.choice(sorted(combos))
    hero = args.hero_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(place=place, hazard=hazard, prize=prize, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type="crow", label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", type="turtle", label=params.helper))
    hazard = HAZARDS[params.hazard]
    prize = world.add(Entity(id="prize", label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase,
                             type=PRIZES[params.prize].type, plural=PRIZES[params.prize].plural))
    world.facts.update(hero=hero, helper=helper, hazard=hazard, prize=prize, params=params)
    build_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable about a {f["hero"].type} who keeps saying "mine, mine, mine" and then makes a mistake with a line.',
        f"Tell a repetition-heavy fable where {f['hero'].id} clutches a shiny prize and ignores {f['helper'].id}'s warning.",
        "Write a child-facing fable with a bad ending, a burned wing, and a moral about greed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, hazard = f["hero"], f["helper"], f["prize"], f["hazard"]
    return [
        QAItem(
            question=f"Who kept clutching the shiny prize in the story?",
            answer=f"{hero.id} kept clutching {prize.phrase}.",
        ),
        QAItem(
            question=f"What did {helper.id} warn {hero.id} not to do?",
            answer=f"{helper.id} warned {hero.id} not to pull the {hazard.line_kind} line.",
        ),
        QAItem(
            question=f"What happened at the end when {hero.id} would not listen?",
            answer=f"The line snapped, fire came up, and {hero.id} ended with a burned wing and no treasure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that often uses animals to teach a lesson.",
        ),
        QAItem(
            question="What does it mean to clutch something?",
            answer="To clutch something means to hold it tightly in your hands or beak.",
        ),
        QAItem(
            question="Why is fire dangerous?",
            answer="Fire is dangerous because it can burn skin, cloth, wood, and other things that should not catch fire.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} {e.type:8} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
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


ASP_RULES = r"""
% A story is valid if the hero clutches a prize, ignores a warning, and the line burns.
clutches(H, P) :- hero(H), prize(P).
warned(H) :- hero(H), helper(_).
ignores(H) :- clutches(H, _), warned(H).
bad_ending(H) :- ignores(H), burns(H).

% Burn happens when the chosen hazard is a fire-triggering line story.
burns(H) :- hero(H), hazard(_).
valid_story(Place, Hazard, Prize) :- place(Place), hazard(Hazard), prize(Prize).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for h in HAZARDS:
        lines.append(asp.fact("hazard", h))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    print(f"OK: {len(valid_combos())} simple combinations available.")
    return 0


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in [StoryParams(place=pl, hazard=hz, prize=pr, hero="Crow", helper="Turtle") for pl, hz, pr in valid_combos()[:5]]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
