#!/usr/bin/env python3
"""
A small Storyweavers world: a ghost story about a brochure, a lesson learned,
a transformation, and a moral value.

The core premise is simple:
- a child brings home a mysterious brochure
- the brochure seems spooky and unsettling
- the child learns a lesson about honesty and asking for help
- the scary feeling transforms into understanding and care
- the ending proves the moral value changed how the child acts
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
class Person:
    id: str
    type: str = "child"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if case == "subject":
            return "she" if self.type == "girl" else "he" if self.type == "boy" else "they"
        if case == "object":
            return "her" if self.type == "girl" else "him" if self.type == "boy" else "them"
        return "her" if self.type == "girl" else "his" if self.type == "boy" else "their"


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    owner: str = ""
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    gender: str
    setting: str
    brochure_topic: str
    seed: Optional[int] = None


SETTINGS = {
    "hallway": "the hallway",
    "front porch": "the front porch",
    "library corner": "the library corner",
    "bus stop": "the bus stop",
}

BROCHURE_TOPICS = {
    "summer camp": {
        "front": "a bright brochure for summer camp",
        "pages": "summer camp",
        "shadow": "the ink-smudged camper on the back",
        "lesson": "it is better to ask a grown-up what a strange paper means than to guess alone",
        "moral": "honesty and asking for help make fear smaller",
    },
    "animal shelter": {
        "front": "a colorful brochure for the animal shelter",
        "pages": "the animal shelter",
        "shadow": "the little paw print on the last page",
        "lesson": "kindness grows when someone learns what a place really needs",
        "moral": "care and honesty turn worry into help",
    },
    "museum day": {
        "front": "a folded brochure for museum day",
        "pages": "museum day",
        "shadow": "the pale statue drawing on the back",
        "lesson": "a spooky-looking thing can become safe once it is understood",
        "moral": "understanding is stronger than guessing",
    },
}

NAMES = {
    "girl": ["Mia", "Lina", "Nora", "Ava", "Zoe"],
    "boy": ["Leo", "Finn", "Eli", "Noah", "Ben"],
}

TRAITS = ["curious", "quiet", "brave", "gentle", "thoughtful"]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.people: dict[str, Person] = {}
        self.things: dict[str, Thing] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add_person(self, person: Person) -> Person:
        self.people[person.id] = person
        return person

    def add_thing(self, thing: Thing) -> Thing:
        self.things[thing.id] = thing
        return thing

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.params)
        w.people = copy.deepcopy(self.people)
        w.things = copy.deepcopy(self.things)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _ghostly_fright(world: World, child: Person, brochure: Thing) -> None:
    child.memes["fear"] = child.memes.get("fear", 0) + 1
    brochure.meters["mystery"] = brochure.meters.get("mystery", 0) + 1
    world.say(
        f"{child.id} found {brochure.phrase} tucked in a quiet place, and the room "
        f"seemed colder at once."
    )
    world.say(
        f"The last page showed {BROCHURE_TOPICS[world.params.brochure_topic]['shadow']}, "
        f"and that made {child.id} hold the paper with careful fingers."
    )


def _lesson_and_turn(world: World, child: Person, brochure: Thing) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(
        f"{child.id} almost guessed a spooky story about the brochure, but then "
        f"{child.pronoun()} remembered that guessing can make shadows bigger."
    )
    world.say(
        f"So {child.id} asked a grown-up to read it aloud, and the words turned out to "
        f"be about {BROCHURE_TOPICS[world.params.brochure_topic]['pages']}."
    )


def _transformation(world: World, child: Person, brochure: Thing) -> None:
    child.memes["fear"] = 0
    child.memes["calm"] = child.memes.get("calm", 0) + 1
    child.memes["understanding"] = child.memes.get("understanding", 0) + 1
    brochure.meters["mystery"] = 0
    brochure.meters["meaning"] = brochure.meters.get("meaning", 0) + 1
    world.say(
        f"After that, the brochure did not seem haunted anymore; it seemed helpful."
    )
    world.say(
        f"{child.id} noticed that the strange picture was only a sign, and the sign had "
        f"a simple message once someone explained it."
    )


def _moral_value(world: World, child: Person, brochure: Thing) -> None:
    child.memes["honesty"] = child.memes.get("honesty", 0) + 1
    child.memes["helpfulness"] = child.memes.get("helpfulness", 0) + 1
    world.say(
        f"{child.id} folded the brochure neatly and promised to ask questions first next time."
    )
    world.say(
        f"That night, the paper stayed by the lamp, and it looked less like a ghost story "
        f"and more like a lesson learned."
    )


def tell(params: StoryParams) -> World:
    world = World(params)
    child = world.add_person(Person(
        id=params.name,
        type=params.gender,
        label=params.name,
        traits=[random.choice(TRAITS)],
    ))
    brochure = world.add_thing(Thing(
        id="brochure",
        label="brochure",
        phrase=BROCHURE_TOPICS[params.brochure_topic]["front"],
        owner=child.id,
        location=params.setting,
    ))

    world.say(
        f"One evening at {SETTINGS[params.setting]}, {child.id} noticed {brochure.phrase}."
    )
    world.say(
        f"{child.id} was a {child.traits[0]} {params.gender} who liked to know what every little thing meant."
    )

    world.para()
    _ghostly_fright(world, child, brochure)
    world.say(
        f"The paper fluttered in a draft, and {child.id} decided it might be a ghostly clue."
    )

    world.para()
    _lesson_and_turn(world, child, brochure)
    _transformation(world, child, brochure)
    _moral_value(world, child, brochure)

    world.facts.update(
        child=child,
        brochure=brochure,
        setting=params.setting,
        topic=params.brochure_topic,
        moral=BROCHURE_TOPICS[params.brochure_topic]["moral"],
        lesson=BROCHURE_TOPICS[params.brochure_topic]["lesson"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child: Person = world.facts["child"]  # type: ignore[assignment]
    topic = world.facts["topic"]
    setting = world.facts["setting"]
    return [
        f"Write a gentle ghost story for children about a {topic} brochure found at {setting}.",
        f"Tell a short story where {child.id} thinks a brochure is spooky, then learns the truth and feels better.",
        f"Write a story with a lesson learned, a transformation, and a moral value centered on a brochure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Person = world.facts["child"]  # type: ignore[assignment]
    brochure: Thing = world.facts["brochure"]  # type: ignore[assignment]
    topic = world.facts["topic"]
    setting = world.facts["setting"]
    lesson = world.facts["lesson"]
    moral = world.facts["moral"]
    return [
        QAItem(
            question=f"What did {child.id} find at {setting}?",
            answer=f"{child.id} found {brochure.phrase}, and at first it felt spooky.",
        ),
        QAItem(
            question=f"What lesson did the story teach about the {topic} brochure?",
            answer=lesson,
        ),
        QAItem(
            question=f"What changed after {child.id} asked for help?",
            answer=f"The brochure stopped seeming haunted, and {child.id} became calm and understanding.",
        ),
        QAItem(
            question="What moral value did the story end with?",
            answer=moral,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a brochure?",
            answer="A brochure is a folded paper with words and pictures that gives information about something.",
        ),
        QAItem(
            question="What do people do when something seems spooky but might be safe?",
            answer="They can ask a grown-up, look closely, and learn what it really means.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


@dataclass
class StoryState:
    child_brochure_seen: bool = False
    fear: bool = False
    transformed: bool = False
    learned: bool = False


def explain_state(world: World) -> str:
    child: Person = world.facts["child"]  # type: ignore[assignment]
    brochure: Thing = world.facts["brochure"]  # type: ignore[assignment]
    lines = ["--- world model state ---"]
    lines.append(f"child: {child.id} memes={dict(child.memes)}")
    lines.append(f"brochure: {brochure.label} meters={dict(brochure.meters)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for topic in BROCHURE_TOPICS:
        lines.append(asp.fact("topic", topic))
    lines.append(asp.fact("feature", "lesson_learned"))
    lines.append(asp.fact("feature", "transformation"))
    lines.append(asp.fact("feature", "moral_value"))
    lines.append(asp.fact("style", "ghost_story"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, T) :- setting(S), topic(T).
feature_present(lesson_learned).
feature_present(transformation).
feature_present(moral_value).
style_ok :- style(ghost_story).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, t) for s in SETTINGS for t in BROCHURE_TOPICS}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world about a brochure.")
    ap.add_argument("--name", choices=sorted({n for vals in NAMES.values() for n in vals}))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--topic", choices=BROCHURE_TOPICS)
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
    topic = args.topic or rng.choice(list(BROCHURE_TOPICS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    return StoryParams(name=name, gender=gender, setting=setting, brochure_topic=topic)


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
        print(explain_state(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, topic) combos:\n")
        for s, t in combos:
            print(f"  {s:14} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            for topic in BROCHURE_TOPICS:
                p = StoryParams(
                    name=random.choice(NAMES["girl"] + NAMES["boy"]),
                    gender=random.choice(["girl", "boy"]),
                    setting=setting,
                    brochure_topic=topic,
                    seed=base_seed,
                )
                samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
