#!/usr/bin/env python3
"""
storyworlds/worlds/soybean_moral_value_nursery_rhyme.py
========================================================

A small storyworld for a nursery-rhyme style soybean tale with a moral value
turn: the little soybean learns kindness, sharing, and patience while growing.

The world is intentionally simple and classical:
- a tiny soybean seed has physical state (meters) and emotional state (memes)
- it lives in one setting, with a small handful of characters and objects
- a tension arises when the soybean wants something scarce
- the ending proves a change in the world state and in the soybean's feelings

This script follows the storyworld contract:
- stdlib only for the prose engine
- eager imports from storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"child", "girl", "boy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"mother", "father", "adult"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the sunny garden"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mood:
    id: str
    name: str
    cue: str
    lesson: str
    want: str
    action: str
    trouble: str
    remedy: str
    ending: str


@dataclass
class StoryParams:
    mood: str
    name: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


MOODS = {
    "sharing": Mood(
        id="sharing",
        name="sharing",
        cue="share the water",
        lesson="kindness grows kinder when it is shared",
        want="keep the watering can all for itself",
        action="share the water with the thirsty sprouts",
        trouble="the little sprouts would stay dry",
        remedy="give each sprout a small sip",
        ending="every sprout had a shiny drop on its leaf",
    ),
    "patience": Mood(
        id="patience",
        name="patience",
        cue="wait for the sun",
        lesson="good things grow best when we wait a little",
        want="rush the sprout and pop right up",
        action="wait a little while the warm sun worked",
        trouble="the soil would still be too sleepy",
        remedy="rest in the dark soil and wait",
        ending="the shoot peeked out when the morning was ready",
    ),
    "gentleness": Mood(
        id="gentleness",
        name="gentleness",
        cue="be gentle with the bean",
        lesson="gentle hands help fragile things grow",
        want="wiggle hard and bump the soil",
        action="move softly so the shell could open slow and safe",
        trouble="the tiny shell might crack too soon",
        remedy="breathe slow and loosen softly",
        ending="the husk opened like a little smile",
    ),
}

SETTINGS = {
    "garden": Setting(place="the sunny garden", affords={"sharing", "patience", "gentleness"}),
    "window": Setting(place="the kitchen window", affords={"sharing", "patience", "gentleness"}),
    "patch": Setting(place="the bean patch", affords={"sharing", "patience", "gentleness"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Theo", "Ben", "Max"]
ADULTS = ["mother", "father"]

KNOWLEDGE = {
    "soybean": [
        (
            "What is a soybean?",
            "A soybean is a small bean that can grow into a plant and become food when people cook it in many kinds of dishes.",
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting someone else use or have some of what you have so everyone can enjoy a little of it.",
        )
    ],
    "patience": [
        (
            "What is patience?",
            "Patience means waiting calmly for something to happen instead of hurrying it along.",
        )
    ],
    "gentleness": [
        (
            "What does gentle mean?",
            "Gentle means soft and careful, so you do not hurt something delicate.",
        )
    ],
}


def valid_moods() -> list[str]:
    return list(MOODS.keys())


def reasonableness_gate(mood: Mood) -> bool:
    return mood.id in MOODS and bool(mood.lesson)


def select_mood(rng: random.Random, explicit: Optional[str] = None) -> Mood:
    if explicit:
        if explicit not in MOODS:
            raise StoryError(f"(No story: unknown moral value '{explicit}'.)")
        mood = MOODS[explicit]
        if not reasonableness_gate(mood):
            raise StoryError("(No story: that moral value does not form a complete story.)")
        return mood
    return MOODS[rng.choice(sorted(MOODS))]


def _tone_opening(hero: Entity, setting: Setting, mood: Mood) -> str:
    return (
        f"Little {hero.label}, a soybean so small, lived in {setting.place}. "
        f"It liked to {mood.cue}, and it hummed a tiny tune."
    )


def _tone_middle(hero: Entity, parent: Entity, mood: Mood) -> str:
    return (
        f"But one bright day, {hero.label} wanted to {mood.want}. "
        f"That was a problem, because {mood.trouble}."
    )


def _tone_turn(parent: Entity, hero: Entity, mood: Mood) -> str:
    return (
        f"So {parent.label} smiled and said, "
        f"\"Little soybean, {mood.action}. {mood.remedy}.\""
    )


def _tone_ending(hero: Entity, parent: Entity, mood: Mood) -> str:
    return (
        f"{hero.label} listened, and its heart grew calm and bright. "
        f"{mood.ending}, and {mood.lesson}. "
        f"{parent.label} clapped softly, and the garden looked sweet and light."
    )


def build_world(params: StoryParams) -> World:
    mood = MOODS[params.mood]
    world = World(SETTINGS["garden"])
    hero = world.add(Entity(
        id="soybean",
        kind="character",
        type="soybean",
        label=params.name,
        phrase="a tiny soybean",
        owner="soil",
        meters={"growth": 0.0, "thirst": 1.0, "sun": 0.5},
        memes={"hope": 0.5, "impatience": 0.0, "kindness": 0.0, "calm": 0.2},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        phrase=f"the {params.parent}",
        meters={"work": 0.0},
        memes={"care": 1.0},
    ))
    water = world.add(Entity(
        id="water",
        kind="thing",
        type="water",
        label="the little watering can",
        phrase="a small watering can",
        meters={"water": 2.0},
    ))
    sprouts = world.add(Entity(
        id="sprouts",
        kind="character",
        type="sprout",
        label="the thirsty sprouts",
        phrase="the thirsty sprouts",
        plural=True,
        meters={"thirst": 1.0},
        memes={"hope": 0.4},
    ))

    world.facts.update(hero=hero, parent=parent, water=water, sprouts=sprouts, mood=mood)
    return world


def narrate_story(world: World) -> None:
    hero = world.get("soybean")
    parent = world.get("parent")
    water = world.get("water")
    sprouts = world.get("sprouts")
    mood: Mood = world.facts["mood"]

    world.say(_tone_opening(hero, world.setting, mood))
    world.say(f"Every morning, {hero.label} watched {water.label} shine beside the bed of soil.")
    world.para()

    hero.memes["impatience"] += 1.0
    hero.meters["thirst"] += 0.5
    world.say(_tone_middle(hero, parent, mood))
    world.say(f"It clutched its tiny shell and wished for the whole can at once.")

    if mood.id == "sharing":
        world.say(f"Yet {sprouts.label} were nearby, and their leaves looked droopy and small.")
        parent.memes["care"] += 0.2
        hero.memes["kindness"] += 0.5
        hero.meters["growth"] += 0.2
    elif mood.id == "patience":
        world.say(f"The soil was warm, but the little shoot was not ready to pop up yet.")
        hero.memes["hope"] += 0.3
    else:
        world.say(f"The shell felt brittle, and a hard wiggle would have been too rough.")
        hero.memes["calm"] += 0.4

    world.para()
    hero.memes["calm"] += 0.8
    hero.memes["impatience"] = 0.0
    hero.meters["thirst"] = 0.0
    water.meters["water"] -= 1.0
    sprouts.meters["thirst"] = 0.0
    world.say(_tone_turn(parent, hero, mood))

    if mood.id == "sharing":
        world.say("The little soybean tipped the can, and each sprout got a tiny sip.")
        world.say("No drop was too big, and no leaf was left out.")
        hero.meters["growth"] += 0.6
        sprouts.memes["hope"] += 0.6
    elif mood.id == "patience":
        world.say("The soybean tucked itself in the warm soil and counted soft cloud shapes.")
        world.say("Soon the morning came, and the green shoot pushed up by itself.")
        hero.meters["growth"] += 0.7
        hero.memes["hope"] += 0.4
    else:
        world.say("The soybean breathed slow and let the husk open little by little.")
        world.say("Its shell loosened gently, and the new sprout stayed safe.")
        hero.meters["growth"] += 0.5
        hero.memes["kindness"] += 0.4

    world.para()
    world.say(_tone_ending(hero, parent, mood))
    hero.meters["growth"] += 1.0
    hero.memes["kindness"] += 0.5
    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    mood: Mood = world.facts["mood"]
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    return [
        f'Write a short nursery rhyme story about a soybean that learns to {mood.cue}.',
        f"Tell a gentle story where {hero.label} the soybean wants to {mood.want}, but {parent.label} guides it toward a kinder choice.",
        f'Write a simple rhyme-like story using the word "soybean" and ending with a moral about how {mood.lesson}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    mood: Mood = world.facts["mood"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.label}, a tiny soybean, and {parent.label}, who helps it learn a good lesson.",
        ),
        QAItem(
            question=f"What did the soybean want to do at first?",
            answer=f"It wanted to {mood.want}.",
        ),
        QAItem(
            question=f"What did the parent teach the soybean?",
            answer=f"The parent taught the soybean that {mood.lesson}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {mood.ending.lower()}, and the soybean felt calm and proud.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    mood: Mood = world.facts["mood"]
    return [QAItem(question=q, answer=a) for q, a in KNOWLEDGE["soybean"] + KNOWLEDGE[mood.id]]


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
        bits = []
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
mood(sharing).
mood(patience).
mood(gentleness).

complete(M) :- mood(M).
valid_story(M) :- complete(M).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("mood", m) for m in MOODS)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_moods() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(name for (name,) in asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_moods())
    python_set = set(valid_moods())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_moods() ({len(clingo_set)} moods).")
        return 0
    print("MISMATCH between clingo and valid_moods():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Soybean moral-value nursery rhyme storyworld.")
    ap.add_argument("--mood", choices=sorted(MOODS))
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=ADULTS)
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
    mood = select_mood(rng, args.mood)
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    parent = args.parent or rng.choice(ADULTS)
    return StoryParams(mood=mood.id, name=name, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate_story(world)
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


CURATED = [
    StoryParams(mood="sharing", name="Mia", parent="mother"),
    StoryParams(mood="patience", name="Leo", parent="father"),
    StoryParams(mood="gentleness", name="Nora", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(", ".join(sorted(name for (name,) in asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: moral={p.mood}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
