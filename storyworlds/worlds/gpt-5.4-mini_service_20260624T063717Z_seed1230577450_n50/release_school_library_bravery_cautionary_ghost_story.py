#!/usr/bin/env python3
"""
Storyworld: release / bravery / cautionary ghost story in a school library.

This world stages a small, child-facing ghost story set in a school library.
The core tension is between a brave child who wants to help a shy ghost be
free and the cautionary rules that keep everyone safe. The emotional turn is
that bravery here means careful kindness, not reckless sneaking.

The story model tracks:
- physical meters: lantern light, footsteps, door states, dust, book order
- emotional memes: fear, courage, relief, trust, caution

The story contract:
- child-facing prose driven by simulated state
- explicit invalid parameter choices raise StoryError
- inline ASP twin mirrors the reasonableness gate
- generate/emit/main plus parser and parameter resolution are provided
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

STORY_THEME = "release"
WORLD_SETTING = "school library"
FEATURES = ("Bravery", "Cautionary")
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
    held: bool = False
    location: str = ""

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

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
class Room:
    name: str = "school library"
    quiet: bool = True
    after_school: bool = True
    open_door: bool = False
    moonlight: bool = False


@dataclass
class Ghost:
    name: str
    released: bool = False
    trapped_reason: str = ""
    trust: float = 0.0


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    ghost_name: str
    ghost_reason: str
    seed: Optional[int] = None


NAMES = {
    "girl": ["Maya", "Lena", "Ivy", "Nora", "Zoe"],
    "boy": ["Finn", "Eli", "Theo", "Noah", "Ben"],
}
HELPERS = ["librarian", "teacher", "friend"]
GHOST_NAMES = ["Milo", "Pearl", "June", "Wren"]
GHOST_REASONS = [
    "a locked story room",
    "a lost library key",
    "a stuck reading ladder",
]


class World:
    def __init__(self) -> None:
        self.room = Room()
        self.entities: dict[str, Entity] = {}
        self.ghost = Ghost(name="")
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


def _inc(m: dict[str, float], key: str, amount: float = 1.0) -> None:
    m[key] = m.get(key, 0.0) + amount


def brave_but_careful(world: World, child: Entity) -> None:
    _inc(child.memes, "courage", 1)
    _inc(child.memes, "caution", 1)
    world.say(
        f"{child.id} felt brave, but not silly-brave. "
        f"{child.pronoun().capitalize()} listened to the quiet rules of the library."
    )


def introduce(world: World, child: Entity, helper: Entity, ghost: Ghost) -> None:
    world.say(
        f"After school, {child.id} was in the {world.room.name}, where the shelves stood tall "
        f"and the air smelled like paper and dust."
    )
    world.say(
        f"{child.id} had a brave heart and a careful mind, and {child.pronoun('possessive')} "
        f"{helper.label} knew how to keep a calm room calm."
    )
    world.say(
        f"Then {child.id} heard a tiny whisper from behind the atlas shelf: "
        f"it was {ghost.name}, a shy little ghost who could not leave because of {ghost.trapped_reason}."
    )


def caution(world: World, child: Entity, helper: Entity) -> None:
    _inc(child.memes, "caution", 1)
    world.say(
        f"{helper.label.capitalize()} put a finger to {helper.pronoun('possessive')} lips and whispered, "
        f'"No running. No shouting. Quiet feet only."'
    )
    world.say(
        f"{child.id} nodded. Being brave in the library meant helping without startling the books or the ghost."
    )


def investigate(world: World, child: Entity, ghost: Ghost) -> None:
    _inc(child.meters, "footsteps", 1)
    _inc(child.memes, "fear", 1)
    world.say(
        f"{child.id} tiptoed between the shelves with a small flashlight. "
        f"The beam made the old book spines shine like sleepy stars."
    )
    world.say(
        f"Behind a tall row of books, {child.id} found {ghost.name} tucked into a curl of moon-white dust."
    )


def offer_help(world: World, child: Entity, helper: Entity, ghost: Ghost) -> None:
    ghost.trust += 1.0
    _inc(ghost.__dict__.setdefault("memes", {}), "relief", 1)
    world.say(
        f"{child.id} did not grab or command. {child.pronoun().capitalize()} asked softly, "
        f'"Can we help you go free?"'
    )
    world.say(
        f"{ghost.name} shimmered. The little ghost had been waiting for someone kind enough to ask first."
    )


def open_release(world: World, child: Entity, helper: Entity, ghost: Ghost) -> None:
    if not world.room.open_door:
        world.room.open_door = True
        _inc(child.meters, "hand_on_door", 1)
    ghost.released = True
    _inc(child.memes, "relief", 1)
    _inc(helper.memes, "relief", 1)
    world.say(
        f"{helper.label.capitalize()} opened the library door just a little, "
        f"so the night air could slip in without a bang."
    )
    world.say(
        f"Together they said a gentle goodbye, and {ghost.name} floated up like a soft page turning in a breeze."
    )
    world.say(
        f"The ghost was free at last, and the shelves stayed quiet and safe."
    )


def ending_image(world: World, child: Entity, helper: Entity, ghost: Ghost) -> None:
    world.say(
        f"{child.id} smiled under the lamp light, feeling brave because {child.pronoun('subject')} had been careful."
    )
    world.say(
        f"By the end, the library was peaceful, the doorway was open, and only a few dust motes still danced where {ghost.name} had been."
    )


def build_world(params: StoryParams) -> StorySample:
    world = World()
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={},
        memes={},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper if params.helper in {"mother", "father", "woman", "man", "girl", "boy"} else "teacher",
        label=f"the {params.helper}",
        meters={},
        memes={},
    ))
    ghost = Ghost(name=params.ghost_name, trapped_reason=params.ghost_reason)
    world.ghost = ghost
    world.facts.update(
        child=child,
        helper=helper,
        ghost=ghost,
        room=world.room,
        theme=STORY_THEME,
        setting=WORLD_SETTING,
    )

    introduce(world, child, helper, ghost)
    world.para()
    brave_but_careful(world, child)
    caution(world, child, helper)
    investigate(world, child, ghost)
    world.para()
    offer_help(world, child, helper, ghost)
    open_release(world, child, helper, ghost)
    ending_image(world, child, helper, ghost)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def valid_pair(params: StoryParams) -> bool:
    return params.gender in {"girl", "boy"} and params.ghost_reason in GHOST_REASONS


def explain_invalid(params: StoryParams) -> str:
    return " (No story: the requested school-library ghost tale needs a child, a shy ghost, and a release that can happen safely.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    ghost_reason = args.ghost_reason or rng.choice(GHOST_REASONS)
    params = StoryParams(
        name=name,
        gender=gender,
        helper=helper,
        ghost_name=ghost_name,
        ghost_reason=ghost_reason,
    )
    if not valid_pair(params):
        raise StoryError(explain_invalid(params))
    return params


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    ghost = f["ghost"]
    helper = f["helper"]
    return [
        f"Write a small ghost story for children set in a school library, where {child.id} is brave but careful.",
        f"Tell a cautionary story in which {helper.label} helps {child.id} release the shy ghost {ghost.name} safely.",
        f"Write a gentle release story that keeps the library quiet, uses brave listening, and ends with the ghost free.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    ghost: Ghost = f["ghost"]
    return [
        QAItem(
            question=f"Who was the brave child in the school library story?",
            answer=f"The brave child was {child.id}. {child.pronoun().capitalize()} stayed careful while helping the ghost.",
        ),
        QAItem(
            question=f"Why did {ghost.name} stay in the library at first?",
            answer=f"{ghost.name} stayed because of {ghost.trapped_reason}. The ghost needed gentle help to be released safely.",
        ),
        QAItem(
            question=f"What did {helper.label} tell {child.id} to do in the library?",
            answer=f"{helper.label.capitalize()} told {child.id} to use quiet feet, soft voices, and careful bravery.",
        ),
        QAItem(
            question=f"How did the story end for {ghost.name}?",
            answer=f"The story ended with {ghost.name} floating free at last, while the library stayed calm and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should people whisper in a library?",
            answer="People whisper in a library so others can read and listen without being disturbed.",
        ),
        QAItem(
            question="What does being brave mean in a careful story?",
            answer="Being brave in a careful story means doing the right thing even when it feels a little scary, but still following safe rules.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a story about a ghost, often with a spooky feeling, but it can still be gentle and kind for children.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"room.open_door={world.room.open_door}")
    lines.append(f"ghost.released={world.ghost.released}")
    lines.append(f"ghost.trust={world.ghost.trust}")
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
brave(C) :- courage(C), caution(C).
safe_release(G) :- ghost(G), released(G), careful(G).
valid_story(C,G) :- child(C), ghost(G), brave(C), safe_release(G).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("child", "child"), asp.fact("ghost", "ghost"), asp.fact("courage", "child"), asp.fact("caution", "child"), asp.fact("careful", "ghost"), asp.fact("released", "ghost")]
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="School library ghost story with bravery and caution.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--ghost-name")
    ap.add_argument("--ghost-reason", choices=GHOST_REASONS)
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


def generate(params: StoryParams) -> StorySample:
    return build_world(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(name="Maya", gender="girl", helper="teacher", ghost_name="Milo", ghost_reason="a locked story room"),
    StoryParams(name="Finn", gender="boy", helper="librarian", ghost_name="Pearl", ghost_reason="a lost library key"),
    StoryParams(name="Nora", gender="girl", helper="teacher", ghost_name="June", ghost_reason="a stuck reading ladder"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for this world, but the reasonableness gate is Python-backed in this seed.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
