#!/usr/bin/env python3
"""
kneel_suspense_flashback_comedy.py
==================================

A small storyworld about a child who kneels down to solve a tiny problem,
while a brief flashback adds suspense and the ending stays playful and funny.

Premise:
- A child wants to kneel and look under a piece of furniture to find a lost
  thing before a simple surprise is ruined.
- A remembered earlier mishap makes the search feel suspenseful.
- The child learns that a careful, low-to-the-ground method is the best fix.

The simulated state tracks:
- meters: search, dust, wobble, hidden, found, tidiness
- memes: curiosity, suspense, embarrassment, relief, laughter

The world is deliberately small: one setting, one hero, one helper, one lost
object, and one practical fix.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def mm(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    hiding_spot: str
    affords_kneel: bool = True


@dataclass
class LostThing:
    id: str
    label: str
    phrase: str
    hidden_place: str
    can_rattle: bool = False


@dataclass
class StoryParams:
    setting: str
    lost: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "hallway": Setting(place="the hallway", hiding_spot="under the bench"),
    "kitchen": Setting(place="the kitchen", hiding_spot="under the table"),
    "classroom": Setting(place="the classroom", hiding_spot="behind the cubbies"),
}

LOST_THINGS = {
    "marble": LostThing(
        id="marble",
        label="marble",
        phrase="a shiny blue marble",
        hidden_place="near the baseboard",
        can_rattle=True,
    ),
    "button": LostThing(
        id="button",
        label="button",
        phrase="a tiny red button",
        hidden_place="under the rug edge",
        can_rattle=False,
    ),
    "spoon": LostThing(
        id="spoon",
        label="spoon",
        phrase="a small silver spoon",
        hidden_place="behind the cereal box",
        can_rattle=True,
    ),
    "note": LostThing(
        id="note",
        label="note",
        phrase="a folded note",
        hidden_place="inside a shoe",
        can_rattle=False,
    ),
}

HELPER_LINES = {
    "cat": "The cat blinked as if this was the funniest rescue mission ever.",
    "dog": "The dog wagged its tail and looked ready to help, even if it only helped by sniffing.",
    "grandparent": "The grandparent smiled like they had seen this kind of silliness a hundred times before.",
}


@dataclass
class StoryEvent:
    name: str
    text: str


def _kneel(world: World, hero: Entity, lost: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.meters["search"] = hero.meters.get("search", 0.0) + 1
    world.say(
        f"{hero.id} decided to kneel down and look very carefully near the floor."
    )
    world.say(
        f"From down there, the world looked huge, and {hero.pronoun('possessive')} "
        f"{lost.label} had many places to hide."
    )


def _flashback(world: World, hero: Entity, lost: Entity) -> None:
    if "flashback" in world.fired:
        return
    world.fired.add("flashback")
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
    world.say(
        f"That reminded {hero.pronoun('object')} of the last time the {lost.label} rolled away."
    )
    world.say(
        f"Back then, it had zipped under the furniture so fast that {hero.id} had stared at the empty floor for a long minute."
    )


def _search(world: World, hero: Entity, lost: Entity) -> None:
    if "search" in world.fired:
        return
    world.fired.add("search")
    hero.meters["search"] = hero.meters.get("search", 0.0) + 1
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
    world.say(
        f"{hero.id} reached one hand under the {world.setting.hiding_spot.split()[-1]}, "
        f"slowly, slowly, as if the floor might be listening."
    )
    if lost.m.meters.get("hidden", 0.0) >= THRESHOLD:
        world.say(
            f"Then came a tiny sound: a little clink from somewhere dark and dusty."
        )


def _discover(world: World, hero: Entity, lost: Entity, helper: Entity) -> None:
    if "discover" in world.fired:
        return
    world.fired.add("discover")
    lost.meters["found"] = 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["laughter"] = hero.memes.get("laughter", 0.0) + 1
    world.say(
        f"At last, {hero.id} spotted {hero.pronoun('possessive')} {lost.phrase} shining in the dim space."
    )
    world.say(
        f"{helper.id} gave a cheerful little sound, as if to say, 'There you are!'"
    )


def _ending(world: World, hero: Entity, lost: Entity, helper: Entity) -> None:
    if "ending" in world.fired:
        return
    world.fired.add("ending")
    world.say(
        f"{hero.id} picked up the {lost.label}, stood back up, and laughed at how dramatic the whole search had felt."
    )
    world.say(
        f"In the end, kneeling had turned into the smartest move: the {lost.label} was safe, the floor was quiet, and {helper.id} was still smiling."
    )


def tell(setting: Setting, lost_cfg: LostThing, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"search": 0.0, "wobble": 0.0, "dust": 0.0},
        memes={"curiosity": 0.0, "suspense": 0.0, "relief": 0.0, "laughter": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label=helper_type,
        meters={},
        memes={},
    ))
    lost = world.add(Entity(
        id=lost_cfg.id,
        kind="thing",
        type=lost_cfg.id,
        label=lost_cfg.label,
        phrase=lost_cfg.phrase,
        owner=hero.id,
        meters={"hidden": 1.0},
    ))

    world.say(
        f"{hero.id} was a small {hero_type} who had lost {hero.pronoun('possessive')} {lost.label}."
    )
    world.say(
        f"It mattered because {hero.pronoun('possessive')} {lost.label} was supposed to be ready for a little surprise later."
    )

    world.para()
    world.say(f"The search began in {setting.place}, near {setting.hiding_spot}.")
    _kneel(world, hero, lost)
    _flashback(world, hero, lost)
    _search(world, hero, lost)

    world.para()
    world.say(f"{HELPER_LINES.get(helper_type, 'The helper waited patiently.')}")
    world.say(
        f"{hero.id} listened to the tiny clue and kept peeking under the edge of the furniture."
    )
    _discover(world, hero, lost, helper)

    world.para()
    _ending(world, hero, lost, helper)

    world.facts.update(hero=hero, helper=helper, lost=lost, setting=setting, lost_cfg=lost_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    lost = f["lost_cfg"]
    return [
        f'Write a short funny story for a young child where {hero.id} kneels to find {lost.phrase}.',
        f'Tell a suspenseful-but-silly story with a flashback, a kneeling search, and a happy ending.',
        f'Write a comedy story in which a child gets low to the ground to solve a tiny mystery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    lost_cfg: LostThing = f["lost_cfg"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"Who kneels down in {setting.place} to look for the missing {lost_cfg.label}?",
            answer=f"{hero.id} kneels down to search carefully near the floor, because {hero.pronoun('possessive')} {lost_cfg.label} is missing.",
        ),
        QAItem(
            question=f"What does the flashback remind {hero.id} about?",
            answer=f"It reminds {hero.id} that the {lost_cfg.label} once rolled away very fast and disappeared under the furniture.",
        ),
        QAItem(
            question=f"Who helps make the search feel less scary?",
            answer=f"The {helper.type} helps by being cheerful and patient while {hero.id} keeps looking.",
        ),
        QAItem(
            question=f"What happens at the end?",
            answer=f"{hero.id} finds the {lost_cfg.label}, feels relieved, and laughs because the whole search turned out to be a silly little adventure.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "kneel": [
        QAItem(
            question="What does it mean to kneel?",
            answer="To kneel means to bend your legs and rest on one or both knees so you can look closely at something lower down.",
        )
    ],
    "flashback": [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a quick look back at something that happened earlier, so the reader understands the story better.",
        )
    ],
    "suspense": [
        QAItem(
            question="What makes a story suspenseful?",
            answer="A story feels suspenseful when you wonder what will happen next and you are waiting to find out.",
        )
    ],
    "comedy": [
        QAItem(
            question="What makes a story funny?",
            answer="A funny story often has silly actions, playful surprises, or a small problem that turns out much less serious than it seemed.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [item for key in ("kneel", "flashback", "suspense", "comedy") for item in WORLD_KNOWLEDGE[key]]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(setting: str, lost: str) -> str:
    return f"(No story: the combination of {setting} and {lost} does not make a good kneeling search.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny comedy storyworld with kneel, suspense, and flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--lost", choices=LOST_THINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["cat", "dog", "grandparent"])
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
    lost = args.lost or rng.choice(list(LOST_THINGS))
    name = args.name or rng.choice(["Mia", "Leo", "Nina", "Ben", "Ava", "Owen"])
    gender = args.gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice(list(HELPER_LINES))
    if args.gender is None and name in {"Leo", "Ben", "Owen"}:
        gender = "boy"
    if args.gender is None and name in {"Mia", "Nina", "Ava"}:
        gender = "girl"
    return StoryParams(setting=setting, lost=lost, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], LOST_THINGS[params.lost], params.name, params.gender, params.helper)
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
setting(hallway). setting(kitchen). setting(classroom).

lost(marble). lost(button). lost(spoon). lost(note).

kneel_story(S,L) :- setting(S), lost(L).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for lid in LOST_THINGS:
        lines.append(asp.fact("lost", lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show kneel_story/2."))
    got = set(asp.atoms(model, "kneel_story"))
    want = {(s, l) for s in SETTINGS for l in LOST_THINGS}
    if got == want:
        print(f"OK: ASP matches Python registry pairs ({len(got)} combos).")
        return 0
    print("MISMATCH between ASP and Python registries.")
    print("only in ASP:", sorted(got - want))
    print("only in Python:", sorted(want - got))
    return 1


CURATED = [
    StoryParams(setting="hallway", lost="marble", name="Mia", gender="girl", helper="cat"),
    StoryParams(setting="kitchen", lost="spoon", name="Leo", gender="boy", helper="dog"),
    StoryParams(setting="classroom", lost="button", name="Ava", gender="girl", helper="grandparent"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show kneel_story/2."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show kneel_story/2."))
        print(sorted(set(asp.atoms(model, "kneel_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
