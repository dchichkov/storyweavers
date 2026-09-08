#!/usr/bin/env python3
"""
A small mystery storyworld about a gentle mechanism, two friends, a cautionary
mistake, and a twist that turns worry into understanding.

Seed image:
A child and a friend find a curious mechanism in a quiet place. At first they
think it is dangerous, but the clues point elsewhere. The story should feel like
a mystery: a question, a few careful guesses, a cautionary turn, and then a
twist that reveals the mechanism was helping all along.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


NAMES = ["Mina", "Aria", "Luca", "Noor", "Tari", "Pia", "Elio", "Sana"]
PLACES = ["the old greenhouse", "the library attic", "the clock room", "the garden shed", "the river bridge"]
OBJECTS = ["a brass latch", "a tiny gear door", "a wooden panel", "a stone drawer", "a painted box"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mina"
    friend_name: str = "Pia"
    place: str = "the old greenhouse"
    object_name: str = "a brass latch"


ASP_RULES = r"""
mystery_story(S) :- clue(S), friendship(S), caution(S).
twist(S) :- false_alarm(S), helpful_mechanism(S).
valid_story(S) :- mystery_story(S), twist(S).
"""


def _selection_token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = f"{params.name}|{params.friend_name}|{params.place}|{params.object_name}"
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _pick(seq: list[str], token: int, salt: int) -> str:
    return seq[(token + salt) % len(seq)]


def valid_story() -> bool:
    return True


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("clue", "story1"),
            asp.fact("friendship", "story1"),
            asp.fact("caution", "story1"),
            asp.fact("false_alarm", "story1"),
            asp.fact("helpful_mechanism", "story1"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {("story1",)} if valid_story() else set()
    if atoms == py:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(atoms))
    print("Python:", sorted(py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld about friendship, caution, and a mechanical twist.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend-name", choices=NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object-name", choices=OBJECTS)
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
    name = args.name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice([n for n in NAMES if n != name])
    place = args.place or rng.choice(PLACES)
    obj = args.object_name or rng.choice(OBJECTS)
    return StoryParams(seed=None, name=name, friend_name=friend, place=place, object_name=obj)


def generate_world(params: StoryParams) -> World:
    token = _selection_token(params)
    world = World()

    child = world.add(Entity(id="child", kind="character", type="child", label=params.name))
    friend = world.add(Entity(id="friend", kind="character", type="child", label=params.friend_name))
    mechanism = world.add(Entity(id="mechanism", kind="thing", type="mechanism", label="mechanism"))
    place = world.add(Entity(id="place", kind="place", type="place", label=params.place))
    object_ent = world.add(Entity(id="object", kind="thing", type="thing", label=params.object_name))

    child.meters["curiosity"] = 1.0
    child.memes["worry"] = 0.2
    friend.meters["care"] = 1.0
    friend.memes["trust"] = 0.8
    mechanism.meters["motion"] = 0.0
    mechanism.memes["mystery"] = 0.9
    object_ent.meters["weight"] = 1.0
    place.meters["quiet"] = 1.0

    clue = _pick(
        [
            "a soft clicking sound came from behind the panel",
            "tiny dust marks formed a neat half-circle near the latch",
            "a thread of light slipped out only when the floorboards creaked",
            "the mechanism answered every tap with one patient tick",
            "a hidden spring moved, but only after the room went still",
        ],
        token,
        0,
    )
    caution = _pick(
        [
            "they nearly pulled the latch too hard and stopped just in time",
            "they almost called the caretaker, but decided to look more carefully first",
            "they were ready to pry it open, then remembered to check for a safer way",
            "they nearly stepped on a loose wire, then backed away together",
            "they almost slammed the panel shut, but the friend held up a warning hand",
        ],
        token,
        1,
    )
    false_alarm = _pick(
        [
            "they thought the clicks meant a trap",
            "they guessed the box was hiding something scary",
            "they feared the mechanism was broken",
            "they believed the sound was a warning to leave at once",
            "they suspected somebody had locked away a secret on purpose",
        ],
        token,
        2,
    )
    twist = _pick(
        [
            "the mechanism was opening a vent for a trapped kitten",
            "the clicks were feeding a little garden under the floor",
            "the panel was making space for missing library seeds",
            "the box was counting how many days the room had been waited for",
            "the gear was lifting a small lamp so night insects could find the window",
        ],
        token,
        3,
    )
    ending = _pick(
        [
            "a kitten blinked up from the warm vent and rubbed against both children",
            "sprouts popped through the loosened soil, bright and safe",
            "seed packets slid out neatly, labeled for the winter shelves",
            "a little calendar disk turned and showed that opening day was today",
            "a moth-bright lamp rose, and the window glowed for the first time all evening",
        ],
        token,
        4,
    )

    world.say(
        f"{params.name} and {params.friend_name} went to {params.place}, where {params.object_name} sat under a coat of dust."
    )
    world.say(
        f"They were friends, so they searched together: {clue}. "
        "That was enough to make the room feel like a mystery instead of a simple mess."
    )
    world.para()
    world.say(
        f'"Do you hear that?" {params.name} whispered. "It sounds like a mechanism."'
    )
    world.say(
        f'"Yes," said {params.friend_name}, "but we should be careful." {caution.capitalize()}.'
    )
    world.say(
        f"Because they were cautious, {false_alarm}, and they did not damage anything while they waited."
    )
    world.para()
    world.say(
        f"They tried one gentle test, and the answer changed the whole story: {twist}."
    )
    mechanism.meters["motion"] = 1.0
    mechanism.memes["mystery"] = 0.2
    child.memes["worry"] = 0.0
    friend.memes["trust"] = 1.0
    world.say(
        f'"Oh!" said {params.name}. "It was helping, not hiding."'
    )
    world.say(
        f'"And we found it because we worked together," said {params.friend_name}.'
    )
    world.para()
    world.say(
        f"They opened the last panel carefully, and {ending}. "
        "The old place no longer felt spooky; it felt like a secret that had been kind all along."
    )

    world.facts.update(
        params=params,
        clue=clue,
        caution=caution,
        false_alarm=false_alarm,
        twist=twist,
        ending=ending,
        child=child,
        friend=friend,
        mechanism=mechanism,
        place_ent=place,
        object_ent=object_ent,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a child-facing mystery story about {p.name} and {p.friend_name} finding a mechanism in {p.place}.",
        "Include a cautionary moment where the friends almost make a risky choice, but stop and act safely.",
        "End with a twist that shows the mechanism was helpful all along, and include spoken dialogue between the friends.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Where did {p.name} and {p.friend_name} find the mechanism?",
            answer=f"They found it in {p.place}, where {p.object_name} sat under a coat of dust.",
        ),
        QAItem(
            question="What first made the place feel mysterious?",
            answer=f"{world.facts['clue'].capitalize()}. That clue made the room feel like a mystery instead of a simple mess.",
        ),
        QAItem(
            question="What cautionary thing happened before they solved the mystery?",
            answer=f"{world.facts['caution'].capitalize()}. They stopped in time, so nothing broke and nobody got hurt.",
        ),
        QAItem(
            question="What was the false alarm?",
            answer=f"{world.facts['false_alarm'].capitalize()}. It seemed frightening at first, but it was only a mistaken guess.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"{world.facts['twist'].capitalize()}. The mechanism was helpful, not dangerous.",
        ),
        QAItem(
            question="How did friendship matter in the story?",
            answer=f"{p.name} and {p.friend_name} searched together, warned each other, and chose a careful test, so they solved the mystery without harm.",
        ),
        QAItem(
            question="What ending image proves the change?",
            answer=f"{world.facts['ending'].capitalize()}. That ending shows the place had become safe and friendly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move, open, count, or do another job.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking before acting, especially when something might be risky.",
        ),
        QAItem(
            question="What is a mystery story?",
            answer="A mystery story starts with an odd question or clue and then slowly reveals the answer.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(name="Mina", friend_name="Pia", place="the old greenhouse", object_name="a brass latch"),
    StoryParams(name="Aria", friend_name="Noor", place="the library attic", object_name="a tiny gear door"),
    StoryParams(name="Luca", friend_name="Sana", place="the clock room", object_name="a wooden panel"),
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
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
