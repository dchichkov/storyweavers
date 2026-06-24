#!/usr/bin/env python3
"""
A heartwarming storyworld about a helper teaching a child how to make a rhyme
feel special.

Premise:
- A child wants to rhyme.
- A gentle helper teaches a simple trick.
- The child learns to special-ize the rhyme with a tiny detail.
- The story ends with a warm, proud result.

This world is intentionally small and classical: one setting, one child, one
helper, one poem-like rhyme craft, one meaningful turn, and one happy ending.
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
# Shared world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the sunny classroom"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Topic:
    id: str
    subject: str
    rhyme_word: str
    special_word: str
    helper_method: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    type: str
    trait: str
    special: str
    makes: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "classroom": Setting("the sunny classroom", True, {"teach", "rhyme"}),
    "library": Setting("the quiet library nook", True, {"teach", "rhyme"}),
    "kitchen": Setting("the cozy kitchen table", True, {"teach", "rhyme"}),
}

TOPICS = {
    "cat": Topic(
        id="cat",
        subject="cat",
        rhyme_word="hat",
        special_word="sparkle",
        helper_method="point to a tiny cat picture",
        keyword="cat",
        tags={"animal", "rhyme", "cute"},
    ),
    "tree": Topic(
        id="tree",
        subject="tree",
        rhyme_word="bee",
        special_word="leaf",
        helper_method="tap the branch in the drawing",
        keyword="tree",
        tags={"nature", "rhyme"},
    ),
    "star": Topic(
        id="star",
        subject="star",
        rhyme_word="glow",
        special_word="twinkle",
        helper_method="trace a star with a finger",
        keyword="star",
        tags={"sky", "rhyme", "kind"},
    ),
    "shoe": Topic(
        id="shoe",
        subject="shoe",
        rhyme_word="blue",
        special_word="lace",
        helper_method="point to a little shoe on the page",
        keyword="shoe",
        tags={"everyday", "rhyme"},
    ),
}

GIFTS = {
    "card": Gift(
        id="card",
        label="a handmade card",
        phrase="a little handmade card with room for a rhyme",
        type="card",
        trait="paper",
        special="decorate",
        makes="warm",
    ),
    "poem": Gift(
        id="poem",
        label="a poem strip",
        phrase="a narrow poem strip with space for one special line",
        type="paper",
        trait="paper",
        special="polish",
        makes="proud",
    ),
}

CHILD_NAMES = ["Mia", "Noah", "Lily", "Theo", "Ava", "Finn", "Nina", "Eli"]
HELPER_NAMES = ["Ms. Reed", "Mr. Pine", "Grandma June", "Aunt Bea"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
topic(T) :- topic_base(T).
can_teach(S, T) :- setting(S), topic(T), affords(S, teach), affords(S, rhyme).
special_story(S, T, G) :- can_teach(S, T), gift(G), uses_rhyme(T), makes_special(G).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TOPICS.items():
        lines.append(asp.fact("topic_base", tid))
        lines.append(asp.fact("uses_rhyme", tid))
        lines.append(asp.fact("rhyme_word", tid, t.rhyme_word))
        lines.append(asp.fact("special_word", tid, t.special_word))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("makes_special", gid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    topic: str
    gift: str
    child_name: str
    child_type: str
    helper_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative logic
# ---------------------------------------------------------------------------

def validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.topic not in TOPICS:
        raise StoryError("Unknown rhyme topic.")
    if params.gift not in GIFTS:
        raise StoryError("Unknown gift.")
    if params.child_type not in {"girl", "boy"}:
        raise StoryError("Child type must be girl or boy.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        traits=["little", "curious", "kind"],
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="woman" if "Ms." in params.helper_name or "Grandma" in params.helper_name or "Aunt" in params.helper_name else "man",
        traits=["gentle", "patient"],
    ))
    topic = TOPICS[params.topic]
    gift = world.add(Entity(
        id=params.gift,
        type=GIFTS[params.gift].type,
        label=GIFTS[params.gift].label,
        phrase=GIFTS[params.gift].phrase,
        owner=child.id,
    ))

    # Act 1: setup
    world.say(
        f"{child.id} was a little curious {child.type} who loved making rhymes."
    )
    world.say(
        f"In {world.setting.place}, {helper.id} showed {child.pronoun('object')} how a rhyme could be taught gently, one small step at a time."
    )
    world.say(
        f"{child.id} wanted to {topic.helper_method} and make a rhyme about a {topic.subject}."
    )

    # Act 2: tension and turn
    world.para()
    child.memes["desire"] = 1
    world.say(
        f'At first, {child.id} wrote, "I see a {topic.subject}, I see a {topic.rhyme_word}!"'
    )
    world.say(
        f"But the line felt plain, and {child.id} frowned a little."
    )
    world.say(
        f"{helper.id} smiled and said, 'Let us special-ize it with one tiny detail.'"
    )
    world.say(
        f"So {helper.id} helped {child.id} add the word '{topic.special_word}'."
    )

    # Act 3: resolution
    world.para()
    child.memes["joy"] = 1
    child.memes["pride"] = 1
    gift.worn_by = None
    world.say(
        f"Then {child.id} tucked the rhyme onto {gift.label} and made it shine."
    )
    world.say(
        f"The new line sounded sweet: 'I see a {topic.subject}, I see a {topic.rhyme_word}, and it sparkles with {topic.special_word}.'"
    )
    world.say(
        f"{child.id} beamed, and {helper.id} gave a proud nod. The rhyme was simple, special, and all {child.id}'s own."
    )

    world.facts.update(child=child, helper=helper, topic=topic, gift=gift, params=params)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    topic: Topic = f["topic"]
    return [
        f'Write a heartwarming story for a child about learning to rhyme with "{topic.subject}" and "{topic.rhyme_word}".',
        f"Tell a gentle tale where {p.child_name} is taught to special-ize a rhyme in {world.setting.place}.",
        f'Write a short story that includes the words "teach" and "special-ize" and ends with a proud rhyme.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    topic: Topic = f["topic"]
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    gift: Entity = f["gift"]
    return [
        QAItem(
            question=f"What did {p.child_name} want to do in {world.setting.place}?",
            answer=f"{p.child_name} wanted to make a rhyme about a {topic.subject} and learn how to special-ize it.",
        ),
        QAItem(
            question=f"Who taught {p.child_name} in the story?",
            answer=f"{helper.id} taught {child.id} patiently and helped {child.id} add one special detail to the rhyme.",
        ),
        QAItem(
            question=f"What did {p.child_name} put the rhyme on?",
            answer=f"{p.child_name} put the rhyme on {gift.label}, which made it feel warm and proud.",
        ),
        QAItem(
            question=f"How did the rhyme end up sounding?",
            answer=f"It ended up sounding simple, sweet, and special, with the words {topic.subject}, {topic.rhyme_word}, and {topic.special_word}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    topic: Topic = f["topic"]
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair of words or lines that sound alike at the end, like cat and hat.",
        ),
        QAItem(
            question="What does it mean to teach someone?",
            answer="To teach someone means to help them learn by showing, explaining, and practicing together.",
        ),
        QAItem(
            question="What does it mean to make something special?",
            answer="To make something special means to add a caring touch that helps it feel unique and loved.",
        ),
        QAItem(
            question=f"What word rhymes with {topic.subject} in this world?",
            answer=f"{topic.rhyme_word} rhymes with {topic.subject}.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for t in TOPICS:
            for g in GIFTS:
                out.append((s, t, g))
    return out


CURATED = [
    StoryParams("classroom", "cat", "card", "Mia", "girl", "Ms. Reed"),
    StoryParams("library", "tree", "poem", "Noah", "boy", "Grandma June"),
    StoryParams("kitchen", "star", "card", "Ava", "girl", "Aunt Bea"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.topic:
        combos = [c for c in combos if c[1] == args.topic]
    if args.gift:
        combos = [c for c in combos if c[2] == args.gift]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, topic, gift = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(setting, topic, gift, child_name, child_type, helper_name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show special_story/3."))
    return sorted(set(asp.atoms(model, "special_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - asp_set))
    print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming storyworld about teaching a child to special-ize a rhyme."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--topic", choices=TOPICS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show special_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show special_story/3."))
        triples = sorted(set(asp.atoms(model, "special_story")))
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(t)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.topic} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
