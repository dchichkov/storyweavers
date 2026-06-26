#!/usr/bin/env python3
"""
A standalone Storyweavers world: a storied tall tale with a flashback, a learned
lesson, and a repeating refrain.

This world tells a small, child-facing story about a big-voiced kid whose tall
tales make a problem, then remembers an earlier lesson, then repeats the right
choice until the mess is fixed.
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
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def get(self, key: str) -> float:
        return float(self.meters.get(key, 0.0))

    def feel(self, key: str) -> float:
        return float(self.memes.get(key, 0.0))


@dataclass
class Setting:
    place: str
    landmark: str
    weather: str
    audience: str


@dataclass
class StoryParams:
    name: str
    setting: str
    boast: str
    object: str
    lesson: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    flashback_seen: bool = False
    repeated_phrase: str = ""

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "prairie": Setting(
        place="the wide prairie",
        landmark="a wagon wheel bigger than a milk pail",
        weather="windy",
        audience="crows on the fence",
    ),
    "riverbank": Setting(
        place="the muddy riverbank",
        landmark="a crooked bridge",
        weather="bright",
        audience="fish and frogs",
    ),
    "orchard": Setting(
        place="the apple orchard",
        landmark="a ladder leaning on an old tree",
        weather="golden",
        audience="a sleepy dog and two sparrows",
    ),
}

BOASTS = {
    "horse": "I can out-run a galloping horse",
    "tree": "I can toss a tree branch higher than a kite",
    "wind": "I can whistle louder than the wind",
}

OBJECTS = {
    "hat": "a floppy hat",
    "kettle": "a dented kettle",
    "boots": "a pair of dusty boots",
}

LESSONS = {
    "truth": "A story stays sturdy when it keeps close to the truth",
    "humble": "A big brag can get a little body into a bigger pickle",
    "ask": "If a job is too tall, it is wise to ask for help",
}

NAMES = ["Hank", "Mabel", "Jesse", "Clara", "Otis", "Ruby", "Eli", "Nell"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting=setting)

    child = world.add(Entity(id=params.name, kind="character", label=params.name))
    helper = world.add(Entity(id="Grandpa", kind="character", label="Grandpa"))
    object_ = world.add(Entity(id=params.object, kind="thing", label=OBJECTS[params.object]))

    child.memes["pride"] = 1.0
    child.memes["joy"] = 1.0
    child.memes["trouble"] = 0.0
    child.meters["distance"] = 0.0
    object_.meters["tipped"] = 0.0

    world.facts.update(
        child=child,
        helper=helper,
        object=object_,
        lesson=LESSONS[params.lesson],
        boast=BOASTS[params.boast],
        setting=setting,
        params=params,
    )
    return world


def tell_story(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    object_: Entity = f["object"]
    setting: Setting = f["setting"]
    boast: str = f["boast"]
    lesson: str = f["lesson"]

    world.say(
        f"On {setting.place}, {child.id} was a small spark of a kid with a big voice and a bigger grin."
    )
    world.say(
        f"{child.id} kept saying, \"{boast}!\" so many times that even {setting.audience} seemed to turn and listen."
    )
    world.say(
        f"Near the {setting.landmark}, {child.id} found {object_.label} and tried to show off by swinging it like a prize ribbon."
    )

    # Cause trouble: the object tips and starts a mess.
    child.meters["distance"] += 1.0
    child.memes["pride"] += 1.0
    object_.meters["tipped"] += 1.0
    world.say(
        f"But the {object_.label} wobbled, then toppled, and the whole thing went clatter-clatter-clang."
    )
    world.say(
        f"That made {child.id} blush so hard it looked like sunset had climbed into {child.id}'s cheeks."
    )

    # Flashback.
    world.para()
    world.flashback_seen = True
    world.say(
        f"Then {child.id} remembered a lesson from yesterday, when {helper.id} had said, \"Big words are fine, but honest hands do better work.\""
    )
    world.say(
        f"{child.id} had nodded then, though the lesson had drifted away like a leaf in a creek."
    )

    # Repetition turns the story.
    world.para()
    world.repeated_phrase = "slow and steady, slow and steady"
    child.memes["humility"] = 1.0
    child.memes["resolve"] = 1.0
    world.say(
        f"So {child.id} took a breath and said, \"{world.repeated_phrase}.\""
    )
    world.say(
        f"Again {child.id} said it, \"{world.repeated_phrase},\" and this time the words sounded like boots on a boardwalk."
    )
    world.say(
        f"With the same steady motion each time, {child.id} set the {object_.label} right side up, brushed off the dust, and fixed the whole mishap."
    )

    # Resolution.
    world.say(
        f"{helper.id} smiled from the fence line and said the lesson out loud once more: \"Tell the truth, do the work, and the day can still turn bright.\""
    )
    world.say(
        f"{child.id} laughed, tucked the brag away for later, and walked home with a cleaner heart than before."
    )

    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    return [
        f'Write a tall-tale style story for a child named {params.name} who keeps repeating the line "{BOASTS[params.boast]}."',
        f"Tell a story with a flashback, a lesson learned, and repetition, set on {world.setting.place}.",
        f"Write a storied, child-friendly tale where {params.name} learns to be humble after a boast goes wrong.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    setting: Setting = f["setting"]
    object_: Entity = f["object"]

    return [
        QAItem(
            question=f"Where did {params.name}'s tall tale take place?",
            answer=f"It took place on {setting.place}, near {setting.landmark}.",
        ),
        QAItem(
            question=f"What did {params.name} keep repeating at the start of the story?",
            answer=f"{params.name} kept repeating, \"{BOASTS[params.boast]}!\"",
        ),
        QAItem(
            question=f"Who reminded {params.name} about the lesson in the flashback?",
            answer=f"{helper.id} reminded {params.name} that honest hands do better work.",
        ),
        QAItem(
            question=f"What did {params.name} do to fix the trouble?",
            answer=f"{params.name} used slow, steady motions to set {object_.label} right side up and clean up the mess.",
        ),
        QAItem(
            question=f"What lesson did {params.name} learn?",
            answer=f"{LESSONS[params.lesson]}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tall tale?",
            answer=(
                "A tall tale is a story that makes things sound bigger, wilder, or funnier than ordinary life, "
                "but it still usually has a lesson or a point."
            ),
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer=(
                "A flashback is when a story pauses to remember something that happened earlier, "
                "so the reader can understand why a character feels or acts a certain way."
            ),
        ),
        QAItem(
            question="Why do stories repeat words sometimes?",
            answer=(
                "Repetition can make a line stick in the mind, sound musical, or show that a character is trying hard to stay calm."
            ),
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(prairie). setting(riverbank). setting(orchard).
boast(horse). boast(tree). boast(wind).
object(hat). object(kettle). object(boots).
lesson(truth). lesson(humble). lesson(ask).

valid_story(S,B,O,L) :- setting(S), boast(B), object(O), lesson(L).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for b in BOASTS:
        lines.append(asp.fact("boast", b))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for l in LESSONS:
        lines.append(asp.fact("lesson", l))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = {(s, b, o, l) for s in SETTINGS for b in BOASTS for o in OBJECTS for l in LESSONS}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python registry cross-product ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python.")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A storied tall tale world with flashback, lesson learned, and repetition."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--boast", choices=BOASTS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    boast = args.boast or rng.choice(list(BOASTS))
    obj = args.object_ or rng.choice(list(OBJECTS))
    lesson = args.lesson or rng.choice(list(LESSONS))
    name = args.name or rng.choice(NAMES)
    return StoryParams(name=name, setting=setting, boast=boast, object=obj, lesson=lesson)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"setting: {world.setting.place}")
    lines.append(f"flashback_seen: {world.flashback_seen}")
    lines.append(f"repeated_phrase: {world.repeated_phrase}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s, b, o, l in stories:
            print(f"  {s:9} {b:6} {o:6} {l:6}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for setting in SETTINGS:
            for boast in BOASTS:
                for obj in OBJECTS:
                    for lesson in LESSONS:
                        params = StoryParams(
                            name=random.choice(NAMES),
                            setting=setting,
                            boast=boast,
                            object=obj,
                            lesson=lesson,
                            seed=base_seed,
                        )
                        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
