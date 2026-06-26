#!/usr/bin/env python3
"""
storyworlds/worlds/poppa_apple_skeletal_kindness_dialogue_suspense_detective.py
===============================================================================

A tiny detective-story world about Poppa, an apple, and a skeletal clue.

Premise seed:
- Poppa and a child are in a small neighborhood mystery.
- An apple goes missing.
- A skeletal-looking clue creates suspense.
- Kindness and dialogue reveal the answer instead of fear.

The world keeps one compact simulation with physical meters and emotional memes.
The story is generated from state changes, not from a frozen template.
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
        if self.type in {"girl", "daughter", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False


@dataclass
class Mystery:
    id: str
    label: str
    clue: str
    suspect: str
    reveal: str
    scene: str
    suspense_note: str
    kindness_note: str


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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True),
    "porch": Setting(place="the porch", indoor=False),
    "garden": Setting(place="the garden", indoor=False),
}

MYSTERIES = {
    "missing_apple": Mystery(
        id="missing_apple",
        label="missing apple",
        clue="a skeletal apple core with tiny bite marks",
        suspect="a hungry mouse",
        reveal="the mouse was only trying to make a nest warm and sweet",
        scene="the apple basket near the sink",
        suspense_note="The basket looked half-full, then half-empty, and nobody knew which shadow had moved first.",
        kindness_note="Poppa suggested leaving a small apple slice by the wall so the little mouse would not go hungry again.",
    ),
    "vanished_lunch": Mystery(
        id="vanished_lunch",
        label="vanished lunch apple",
        clue="a skeletal stem and a shiny crumb trail",
        suspect="a shy squirrel",
        reveal="the squirrel had taken the apple to share with its nest",
        scene="the porch step beside a striped lunch pail",
        suspense_note="The lunch pail sat open, and one careful bite had turned the whole morning quiet.",
        kindness_note="Poppa said they could leave a second apple under the bush, because sharing solved more than chasing did.",
    ),
    "orchard_clue": Mystery(
        id="orchard_clue",
        label="orchard apple mystery",
        clue="a skeletal branch that pointed like a finger",
        suspect="a helpful neighbor child",
        reveal="the child had moved the apple so a smaller kid could reach it",
        scene="the garden path under the old tree",
        suspense_note="A wind-stilled branch made the path feel like it was holding its breath.",
        kindness_note="Poppa praised the child for helping, then offered an extra apple to the smaller kid too.",
    ),
}

HERO_NAMES = ["Mia", "Noah", "Lena", "Eli", "Ruby", "Ari"]
MOODS = ["curious", "gentle", "brave", "thoughtful", "patient", "clever"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(kitchen). setting(porch). setting(garden).
indoor(kitchen).
outdoor(porch). outdoor(garden).

mystery(missing_apple). mystery(vanished_lunch). mystery(orchard_clue).

at_scene(missing_apple, kitchen).
at_scene(vanished_lunch, porch).
at_scene(orchard_clue, garden).

has_clue(missing_apple).
has_clue(vanished_lunch).
has_clue(orchard_clue).

kindness_solution(M) :- mystery(M).
suspenseful(M) :- has_clue(M).
dialogue_solution(M) :- kindness_solution(M), suspenseful(M).

valid_story(S, M) :- setting(S), mystery(M), at_scene(M, S), dialogue_solution(M).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        if SETTINGS[sid].indoor:
            lines.append(asp.fact("indoor", sid))
        else:
            lines.append(asp.fact("outdoor", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("has_clue", mid))
        lines.append(asp.fact("kindness_solution", mid))
        lines.append(asp.fact("suspenseful", mid))
    for mid, ms in MYSTERIES.items():
        lines.append(asp.fact("at_scene", mid, next(k for k, v in SETTINGS.items() if v.place == ms.scene_place if False)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    facts = []
    import asp
    for sid, s in SETTINGS.items():
        facts.append(asp.fact("setting", sid))
        if s.indoor:
            facts.append(asp.fact("indoor", sid))
        else:
            facts.append(asp.fact("outdoor", sid))
    for mid, m in MYSTERIES.items():
        facts.append(asp.fact("mystery", mid))
        facts.append(asp.fact("has_clue", mid))
        facts.append(asp.fact("kindness_solution", mid))
        facts.append(asp.fact("suspenseful", mid))
        facts.append(asp.fact("at_scene", mid, "kitchen" if mid == "missing_apple" else "porch" if mid == "vanished_lunch" else "garden"))
    return "\n".join(facts) + "\n" + ASP_RULES + "\n" + show + "\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    python_set = set((s, m) for s in SETTINGS for m in MYSTERIES)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story params and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    mood: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld about Poppa, an apple, and a skeletal clue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--mood", choices=MOODS)
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
    if args.place and args.mystery:
        if args.place not in SETTINGS or args.mystery not in MYSTERIES:
            raise StoryError("Unknown place or mystery.")
    choices = [(p, m) for p in SETTINGS for m in MYSTERIES]
    if args.place:
        choices = [c for c in choices if c[0] == args.place]
    if args.mystery:
        choices = [c for c in choices if c[1] == args.mystery]
    if not choices:
        raise StoryError("No valid story matches those options.")
    place, mystery = rng.choice(sorted(choices))
    name = args.name or rng.choice(HERO_NAMES)
    mood = args.mood or rng.choice(MOODS)
    return StoryParams(place=place, mystery=mystery, name=name, mood=mood)


def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    poppa = world.add(Entity(id="Poppa", kind="character", type="father", label="Poppa"))
    apple = world.add(Entity(id="apple", type="apple", label="apple", owner=poppa.id))
    clue = world.add(Entity(id="clue", type="clue", label="skeletal clue"))
    world.facts.update(hero=hero, poppa=poppa, apple=apple, clue=clue, mystery=MYSTERIES[params.mystery], params=params)
    return world


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    hero: Entity = world.facts["hero"]
    poppa: Entity = world.facts["poppa"]
    apple: Entity = world.facts["apple"]
    mystery: Mystery = world.facts["mystery"]

    # Act 1
    world.say(f"{hero.id} was a {params.mood} little detective who liked following small clues.")
    world.say(f"Poppa was gentle and steady, and he always listened before he guessed.")
    world.say(f"That morning, they found an apple waiting by {mystery.scene}.")

    world.para()

    # Act 2
    world.say(mystery.suspense_note)
    apple.meters["missing"] = 1
    hero.memes["curiosity"] = 1
    poppa.memes["calm"] = 1
    world.say(f"{hero.id} whispered, “Where did the apple go?”")
    world.say(f"Poppa said, “Let's look, and let's be kind about whoever needs it.”")
    world.say(f"Together they followed {mystery.clue}.")
    world.say(f"The clue felt a little spooky, but Poppa kept the room calm with a soft voice and a slow step.")

    world.para()

    # Act 3
    world.say(f"At last they found {mystery.suspect}.")
    world.say(f"{hero.id} said, “Were you the one who took it?”")
    world.say(f"{mystery.suspect.split()[0].capitalize()} answered, “Yes, but I was hungry and scared.”")
    world.say(f"Poppa nodded and said, “You should not sneak, but you can ask.”")
    world.say(mystery.kindness_note)
    apple.meters["found"] = 1
    apple.meters["shared"] = 1
    hero.memes["relief"] = 1
    poppa.memes["kindness"] = 1
    world.say(f"In the end, the apple was shared, the clue made sense, and the little mystery felt safe again.")

    world.facts.update(resolved=True, place=params.place)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    m = world.facts["mystery"]
    return [
        f'Write a short detective story for a child that includes "Poppa", an apple, and a skeletal clue.',
        f'Write a gentle suspense story set in {p.place} where {p.name} and Poppa solve a mystery about an apple.',
        f'Write a simple kindness-focused mystery story with dialogue, suspense, and an apple clue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    m: Mystery = world.facts["mystery"]
    return [
        QAItem(
            question=f"Who helped {p.name} solve the apple mystery?",
            answer=f"Poppa helped {p.name} solve it by staying calm, asking questions, and looking at the clue together.",
        ),
        QAItem(
            question="What was the spooky clue?",
            answer=f"The spooky clue was {m.clue}.",
        ),
        QAItem(
            question="Why was there suspense in the story?",
            answer=f"There was suspense because the apple was missing and nobody knew at first who moved it.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended kindly, with the apple shared and everyone feeling safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective story?",
            answer="A detective story is a story where someone looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means treating someone gently and helping instead of being mean or unfair.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="kitchen", mystery="missing_apple", name="Mia", mood="curious"),
    StoryParams(place="porch", mystery="vanished_lunch", name="Noah", mood="careful"),
    StoryParams(place="garden", mystery="orchard_clue", name="Lena", mood="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
