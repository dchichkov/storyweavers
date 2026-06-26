#!/usr/bin/env python3
"""
Standalone storyworld for a rhyming tale in a storm drain:
a little honcho faces a misunderstanding, then reconciliation,
with a surprise that changes the day.

The world is small and state-driven:
- a child leader ("honcho") gathers friends near a storm drain
- a warning is misunderstood as blame or refusal
- tension rises, then a surprise appears
- the misunderstanding is repaired through apology and sharing

This script follows the Storyweavers world contract.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the storm drain"
    affords: set[str] = field(default_factory=lambda: {"echo", "pebble", "play"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    misunderstanding: str
    turn: str
    rhyme_a: str
    rhyme_b: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    reveal: str
    tag: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    surprise: str
    seed: Optional[int] = None


HERO_NAMES = ["Nina", "Milo", "June", "Theo", "Luna", "Pip", "Sage", "Arlo"]
PARENT_TYPES = ["mother", "father"]
GENDERS = ["girl", "boy"]

ACTIVITY = Activity(
    id="echo",
    verb="call to the drain",
    gerund="calling to the drain",
    rush="lean down near the grate",
    sound="plinky, clinky echoes",
    misunderstanding="the honcho thought the warning was a scold",
    turn="the honcho learned the warning was only meant to help",
    rhyme_a="glow",
    rhyme_b="show",
    tags={"echo", "storm drain", "misunderstanding", "reconciliation", "surprise"},
)

SURPRISES = {
    "duckling": Surprise(
        id="duckling",
        label="a duckling",
        phrase="a tiny duckling in a blue rain cap",
        reveal="Out popped a tiny duckling in a blue rain cap, peeping from a dry pocket below.",
        tag="surprise",
    ),
    "key": Surprise(
        id="key",
        label="a key",
        phrase="a shiny key on a string",
        reveal="Out flashed a shiny key on a string, twinkling in the water's glow.",
        tag="surprise",
    ),
    "fish": Surprise(
        id="fish",
        label="a fish",
        phrase="a silver fish",
        reveal="Out zipped a silver fish, quick as a wink, through the drain's little hole.",
        tag="surprise",
    ),
}


ASP_RULES = r"""
setting(storm_drain).
activity(echo).
tag(echo, misunderstanding).
tag(echo, reconciliation).
tag(echo, surprise).

misunderstanding(A) :- activity(A), tag(A, misunderstanding).
reconciliation(A) :- activity(A), tag(A, reconciliation).
surprise(A) :- activity(A), tag(A, surprise).
story_ready(S) :- setting(S), misunderstanding(echo), reconciliation(echo), surprise(echo).
#show story_ready/1.
#show misunderstanding/1.
#show reconciliation/1.
#show surprise/1.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "storm_drain"), asp.fact("activity", "echo")]
    for tag in sorted(ACTIVITY.tags):
        lines.append(asp.fact("tag", "echo", tag))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise_item", sid))
        lines.append(asp.fact("reveal", sid, s.reveal))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ready/1."))
    atoms = set(asp.atoms(model, "story_ready"))
    ok = atoms == {("storm_drain",)}
    if ok:
        print("OK: ASP twin confirms the story shape.")
        return 0
    print("Mismatch in ASP twin.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storm-drain storyworld with misunderstanding and reconciliation.")
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
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
    surprise = args.surprise or rng.choice(sorted(SURPRISES))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(name=name, gender=gender, parent=parent, surprise=surprise)


def build_world(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    buddy = world.add(Entity(id="Buddy", kind="character", type="kid", label="a muddy buddy"))
    surprise = SURPRISES[params.surprise]
    prize = world.add(Entity(id="Prize", type=surprise.id, label=surprise.label, phrase=surprise.phrase, location="drain"))

    hero.memes["curious"] = 1
    hero.memes["lead"] = 1
    buddy.memes["hope"] = 1

    world.say(
        f"In the storm drain by the curb, {hero.id} was the honcho of the hop, "
        f"with {buddy.label} ready to skip and plop."
    )
    world.say(
        f"{hero.id} loved to {ACTIVITY.gerund}; the drip-drip sound gave a bumpy, bouncy glow."
    )
    world.say(
        f"Each echo came back with a tick-tock rhyme, like little wet bells in a rainy-time chime."
    )

    world.para()
    world.say(
        f"Then {hero.id} leaned in to {ACTIVITY.verb}, but {parent.label} said, "
        f"\"Not there, dear heart; the grate is a tricky part.\""
    )
    hero.memes["want"] = 1
    parent.memes["worry"] = 1
    world.say(
        f"But {hero.id} heard a stern little sting and thought, "
        f"\"{ACTIVITY.misunderstanding}.\" So {hero.id} frowned and felt far from spring."
    )
    hero.memes["hurt"] = 1

    world.para()
    world.say(
        f"Just then, the water gave a wobble and a twirl, and {surprise.reveal}"
    )
    world.say(
        f"The surprise made everyone blink and grin; it turned the tough mood soft from within."
    )
    hero.memes["surprise"] = 1
    buddy.memes["surprise"] = 1

    world.say(
        f"{parent.label.capitalize()} pointed and said, \"See? I was warning you kindly, to keep little feet from slipping blindly.\""
    )
    hero.memes["understand"] = 1
    world.say(
        f"{hero.id} looked up slow, then smiled in place: \"Oh! You meant safety, not bossy face.\""
    )
    hero.memes["apology"] = 1

    world.para()
    world.say(
        f"{hero.id} said, \"I'm sorry for my grumpy frown; let's share this surprise and pass it around.\""
    )
    parent.memes["relief"] = 1
    hero.memes["love"] = 1
    hero.memes["peace"] = 1
    world.say(
        f"So they all peered in, with the storm drain aglow, and the honcho learned kindness can soften the flow."
    )
    world.say(
        f"At day's sweet end, with raindrops in air, the misunderstanding was mended with gentle care."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        buddy=buddy,
        surprise=surprise,
        prize=prize,
        activity=ACTIVITY,
        setting=world.setting,
    )
    return world


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    surprise = f["surprise"]
    return [
        'Write a short rhyming story for a child about a honcho in a storm drain who has a misunderstanding and then a reconciliation.',
        f"Tell a rhyming tale where {hero.id} is the honcho, a warning is misunderstood, and a surprise from the drain helps everyone make up.",
        f"Write a gentle rhyme about the storm drain, {surprise.label}, and how a worried parent and a young leader become friends again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    surprise = f["surprise"]
    return [
        QAItem(
            question=f"Who was the honcho in the storm drain story?",
            answer=f"{hero.id} was the honcho, the little leader who wanted to call to the drain and listen for echoes.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {hero.id} near the grate?",
            answer=f"{parent.label.capitalize()} warned {hero.id} because the storm drain was a tricky place, and little feet could slip too close to the edge.",
        ),
        QAItem(
            question=f"What misunderstanding happened when {hero.id} heard the warning?",
            answer=f"{hero.id} thought the warning was a scold, not a caring safety message, so {hero.id} felt hurt for a moment.",
        ),
        QAItem(
            question=f"What surprise appeared in the drain?",
            answer=f"{surprise.reveal}",
        ),
        QAItem(
            question=f"How did the story end after the surprise?",
            answer=f"{hero.id} apologized, understood the warning, and everyone shared the surprise with a peaceful smile at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a storm drain for?",
            answer="A storm drain helps carry rainwater away from streets so puddles do not pile up too high.",
        ),
        QAItem(
            question="What does a surprise do in a story?",
            answer="A surprise is something unexpected that can change how the characters feel or what they do next.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks words or actions mean one thing, but they really mean something else.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who were upset make peace again and feel friendly once more.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Nina", gender="girl", parent="mother", surprise="duckling"),
    StoryParams(name="Milo", gender="boy", parent="father", surprise="key"),
    StoryParams(name="Luna", gender="girl", parent="mother", surprise="fish"),
]


def asp_valid() -> bool:
    import asp
    model = asp.one_model(asp_program("#show story_ready/1."))
    return set(asp.atoms(model, "story_ready")) == {("storm_drain",)}


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
        print(asp_program("#show story_ready/1."))
        return
    if args.verify:
        if asp_valid():
            print("OK: ASP parity verified.")
            return
        raise SystemExit(1)
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ready/1."))
        print(sorted(asp.atoms(model, "story_ready")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
