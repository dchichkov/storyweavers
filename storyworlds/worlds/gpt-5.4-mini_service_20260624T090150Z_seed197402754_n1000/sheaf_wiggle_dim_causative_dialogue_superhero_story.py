#!/usr/bin/env python3
"""
Superhero Story world: a small, causative rescue tale with dialogue.

Seed words used in-world: sheaf, wiggle-dim, causative.
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


@dataclass
class Hero:
    name: str
    alias: str
    powers: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class Sidekick:
    name: str
    phrase: str


@dataclass
class Villain:
    name: str
    plan: str


@dataclass
class ObjectThing:
    label: str
    phrase: str
    owner: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Scene:
    place: str
    danger: str
    cure: str
    clue: str
    gadget: str


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.hero: Optional[Hero] = None
        self.sidekick: Optional[Sidekick] = None
        self.villain: Optional[Villain] = None
        self.object: Optional[ObjectThing] = None
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        if self.hero:
            lines.append(f"hero={self.hero.name} alias={self.hero.alias} meters={self.hero.meters} memes={self.hero.memes}")
        if self.sidekick:
            lines.append(f"sidekick={self.sidekick.name}")
        if self.villain:
            lines.append(f"villain={self.villain.name} plan={self.villain.plan}")
        if self.object:
            lines.append(f"object={self.object.label} meters={self.object.meters}")
        lines.append(f"scene={self.scene}")
        return "\n".join(lines)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_alias: str
    sidekick_name: str
    villain_name: str
    object_label: str
    seed: Optional[int] = None


PLACES = {
    "skybridge": Scene(
        place="Skybridge Station",
        danger="a jam of stuck doors",
        cure="a careful unlock",
        clue="a squeaky panel",
        gadget="wiggle-dim wrench",
    ),
    "harbor": Scene(
        place="Harbor Tower",
        danger="a drifting fog screen",
        cure="a bright signal",
        clue="a flashing dial",
        gadget="wiggle-dim beacon",
    ),
    "museum": Scene(
        place="Metro Museum",
        danger="a locked glass hall",
        cure="a quiet opening",
        clue="a thin seam",
        gadget="wiggle-dim key",
    ),
}

HEROES = [
    ("Mia", "Captain Bright"),
    ("Noah", "Thunder Kid"),
    ("Ava", "Star Shield"),
    ("Leo", "Bolt Spark"),
]

SIDEKICKS = [
    "Pip",
    "June",
    "Zig",
    "Tess",
]

VILLAINS = [
    "Doctor Drift",
    "Count Cobble",
    "The Grey Moth",
    "Captain Hollow",
]

OBJECTS = [
    ("sheaf of blueprints", "a sheaf of blueprints"),
    ("sheaf of rescue notes", "a sheaf of rescue notes"),
    ("sheaf of clue cards", "a sheaf of clue cards"),
]


ASP_RULES = r"""
hero(H) :- hero_name(H).
place(P) :- place_name(P).
danger(D) :- danger_name(D).
gadget(G) :- gadget_name(G).
object(O) :- object_name(O).

causative(H, D) :- hero(H), danger(D).
resolves(H, D) :- causative(H, D), gadget(G), clue(C).
valid_story(P, H, D) :- place(P), hero(H), danger(D), causative(H, D).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for key in PLACES:
        lines.append(asp.fact("place_name", key))
        lines.append(asp.fact("danger_name", PLACES[key].danger))
        lines.append(asp.fact("gadget_name", PLACES[key].gadget))
    for name, _alias in HEROES:
        lines.append(asp.fact("hero_name", name))
    for name in SIDEKICKS:
        lines.append(asp.fact("sidekick_name", name))
    for name in VILLAINS:
        lines.append(asp.fact("villain_name", name))
    for label, _phrase in OBJECTS:
        lines.append(asp.fact("object_name", label))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for hero, _ in HEROES:
            for danger in {PLACES[place].danger}:
                combos.append((place, hero, danger))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with dialogue and a causative rescue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--villain")
    ap.add_argument("--object")
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
    place = args.place or rng.choice(list(PLACES))
    scene = PLACES[place]
    hero_name, hero_alias = rng.choice(HEROES)
    if args.hero:
        match = next((h for h in HEROES if h[0] == args.hero), None)
        if not match:
            raise StoryError("Unknown hero.")
        hero_name, hero_alias = match
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    villain = args.villain or rng.choice(VILLAINS)
    obj_label, obj_phrase = rng.choice(OBJECTS)
    if args.object:
        match = next((o for o in OBJECTS if o[0] == args.object), None)
        if not match:
            raise StoryError("Unknown object.")
        obj_label, obj_phrase = match
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_alias=hero_alias,
        sidekick_name=sidekick,
        villain_name=villain,
        object_label=obj_label,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    scene = PLACES[params.place]
    world = World(scene)
    hero = Hero(name=params.hero_name, alias=params.hero_alias, powers=["fly fast", "hear tiny clues"])
    sidekick = Sidekick(name=params.sidekick_name, phrase="a quick-nervous helper")
    villain = Villain(name=params.villain_name, plan=f"hide the {scene.place.lower()} gate behind {scene.danger}")
    obj = ObjectThing(label=params.object_label, phrase=params.object_label, owner=hero.name)

    world.hero = hero
    world.sidekick = sidekick
    world.villain = villain
    world.object = obj

    hero.meters["alert"] = 1
    hero.memes["duty"] = 2
    obj.meters["held"] = 1
    world.facts.update(place=params.place, hero=hero.name, villain=villain.name, object=obj.label, danger=scene.danger)

    world.say(f"At {scene.place}, {hero.name} was known as {hero.alias}, and {hero.pronoun().capitalize()} kept a sheaf of {obj.label} tucked under {hero.possessive()} arm.")
    world.say(f'{sidekick.name} looked up and whispered, "{hero.alias}, something feels causative today."')
    world.say(f'{hero.name} nodded. "If there is a problem, there will be a cause, and we will find it," {hero.pronoun()} said.')

    world.para()
    world.say(f"Then {villain.name} swept in with a grin. \"I have hidden the gate with {scene.danger},\" {villain.name} said.")
    world.say(f'{sidekick.name} pointed at {scene.clue}. "Look! A clue!"')
    world.say(f'{hero.name} held up the {scene.gadget} and said, "{scene.place} needs a little wiggle-dim work."')

    world.para()
    world.say(f"{hero.name} stepped closer, listened to the clicks, and gave the {scene.gadget} one careful wiggle.")
    world.say(f'"Is it opening?" asked {sidekick.name}.')
    world.say(f'"Yes," said {hero.name}. "The causative problem made the jam, and the wiggle-dim fix is untying it."')
    world.say(f"The lock sighed, the {scene.danger} lifted, and the path to the gate opened wide.")
    world.say(f'{villain.name} blinked. "No fair," {villain.name} muttered.')
    world.say(f'{hero.name} smiled. "It is fair," {hero.pronoun()} said. "We followed the cause and changed the result."')

    world.para()
    world.say(f"At last, {hero.name} and {sidekick.name} stood beside the open gate while the sheaf of {obj.label} fluttered safely in the breeze.")
    world.say(f'The city glowed below them, and {hero.alias} looked ready for the next call for help.')

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly superhero story that includes the words "sheaf", "wiggle-dim", and "causative".',
        f'Write a short superhero rescue story set at {f["place"]} where {f["hero"]} solves a causative problem.',
        f'Write a story with dialogue in which a hero uses a wiggle-dim gadget to fix a danger and protect a sheaf of papers.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    villain = f["villain"]
    place = f["place"]
    danger = f["danger"]
    obj = f["object"]
    scene = world.scene
    return [
        QAItem(
            question=f"Who was the superhero in the story at {place}?",
            answer=f"The superhero was {hero}. {hero} was the one who noticed the problem and used the wiggle-dim gadget to fix it.",
        ),
        QAItem(
            question=f"What problem did {villain} make at {place}?",
            answer=f"{villain} hid the gate with {danger}, which made the place hard to cross until the hero found the cause and changed it.",
        ),
        QAItem(
            question=f"What did the hero keep safe in a sheaf?",
            answer=f"The hero kept a sheaf of {obj} safe while the rescue was happening.",
        ),
        QAItem(
            question=f"How did the hero solve the causative problem?",
            answer=f"{hero} used the {scene.gadget} and gave it a careful wiggle, which loosened the jam and opened the way forward.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does causative mean?",
            answer="Causative means something that causes another thing to happen. If you change the cause, you can change the result.",
        ),
        QAItem(
            question="What is a sheaf?",
            answer="A sheaf is a bundle of papers or thin things held together in a neat stack.",
        ),
        QAItem(
            question="What does wiggle-dim suggest?",
            answer="Wiggle-dim suggests a small gadget or tool that works by wiggling, twisting, or gently moving a part into place.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does causative mean?",
            answer="Causative means something that causes another thing to happen. If you change the cause, you can change the result.",
        ),
        QAItem(
            question="What is a sheaf?",
            answer="A sheaf is a bundle of papers or thin things held together in a neat stack.",
        ),
        QAItem(
            question="What does wiggle-dim suggest?",
            answer="Wiggle-dim suggests a small gadget or tool that works by wiggling, twisting, or gently moving a part into place.",
        ),
    ]


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
    return world.trace()


CURATED = [
    StoryParams(place="skybridge", hero_name="Mia", hero_alias="Captain Bright", sidekick_name="Pip", villain_name="Doctor Drift", object_label="sheaf of blueprints"),
    StoryParams(place="harbor", hero_name="Noah", hero_alias="Thunder Kid", sidekick_name="June", villain_name="Count Cobble", object_label="sheaf of rescue notes"),
    StoryParams(place="museum", hero_name="Ava", hero_alias="Star Shield", sidekick_name="Zig", villain_name="The Grey Moth", object_label="sheaf of clue cards"),
]


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
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for item in combos:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
