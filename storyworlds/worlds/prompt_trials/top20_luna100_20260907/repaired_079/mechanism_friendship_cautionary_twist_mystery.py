#!/usr/bin/env python3
"""
A child-facing mystery about a tiny mechanism, a loyal friendship, and a
cautionary twist.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
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
    name: str = "Luna"
    friend_name: str = "Milo"
    place: str = "the old clock house"
    mechanism: str = "a brass key mechanism"


NAMES = ["Luna", "Milo", "Nia", "Theo", "Pia", "Arlo", "Sana", "Kit"]
PLACES = [
    "the old clock house",
    "the shuttered train shed",
    "the glasshouse behind the museum",
    "the little lighthouse workshop",
]
MECHANISMS = [
    "a brass key mechanism",
    "a wooden gear mechanism",
    "a silver bell mechanism",
    "a tiny spring mechanism",
]


@dataclass
class Friendship:
    trust: float = 0.0
    shared_choice: bool = False


@dataclass
class Cautionary:
    warning_seen: bool = False
    danger_avoided: bool = False


@dataclass
class Twist:
    secret_found: bool = False
    meaning_changed: bool = False


def _setup(world: World, params: StoryParams) -> None:
    luna = world.add(Entity(params.name, "character", "girl", params.name))
    friend = world.add(Entity(params.friend_name, "character", "boy", params.friend_name))
    mechanism = world.add(Entity("mechanism", "thing", "mechanism", params.mechanism))
    door = world.add(Entity("door", "thing", "door", "the locked door"))
    clue = world.add(Entity("clue", "thing", "clue", "the paper clue"))

    luna.meters["curiosity"] = 1.0
    friend.meters["care"] = 1.0
    mechanism.meters["tension"] = 1.0
    door.meters["locked"] = 1.0
    clue.memes["mystery"] = 1.0

    world.facts.update(
        luna=luna,
        friend=friend,
        mechanism=mechanism,
        door=door,
        clue=clue,
        params=params,
    )


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate(
        f"{params.name}|{params.friend_name}|{params.place}|{params.mechanism}"
    ))


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    friendship = Friendship()
    caution = Cautionary()
    twist = Twist()

    luna = world.facts["luna"]
    friend = world.facts["friend"]
    mechanism = world.facts["mechanism"]
    door = world.facts["door"]
    token = _token(params)

    world.say(
        f"{luna.label} and {friend.label} were best friends who loved solving small mysteries. "
        f"One rainy afternoon, they found {mechanism.label} beside a locked door in {params.place}."
    )
    world.say(
        f"The mechanism had three shining teeth and a red button, but no one knew what the button did."
    )

    world.para()
    world.say(
        f"{luna.label} reached toward it. The moment her finger touched the button, "
        "the mechanism clicked once and a strip of paper slid from the wall."
    )
    world.say(
        f'"It says, “Press twice for a surprise,”' {friend.label} read. '
        f'"That sounds exciting, but it might be a trick."'
    )
    world.say(
        f'"We can look for more clues before touching it again," {luna.label} replied. '
        "Their friendship made them willing to slow down instead of racing ahead."
    )
    friendship.trust = 1.0
    friendship.shared_choice = True

    world.para()
    world.say(
        f"Behind a loose floorboard, they found a second note. It warned, "
        "“A borrowed key opens the door, but it may also close the way home.”"
    )
    world.say(
        f"The friends almost ignored the warning because {mechanism.label} was ticking faster."
    )
    caution.warning_seen = True
    world.say(
        f'"The mystery is not asking us to be brave and reckless," {friend.label} said. '
        f'"It is asking us to understand the mechanism first."'
    )
    world.say(
        f"{luna.label} nodded and counted the teeth, the clicks, and the little arrows. "
        "The arrows pointed away from the locked door, toward a narrow box beneath the stairs."
    )

    world.para()
    world.say(
        f"Inside the box was a bright key. {luna.label} lifted it, but {friend.label} noticed "
        "a thin string tied to its handle."
    )
    world.say(
        "The string led back to the red button. The supposed surprise was a spring trap "
        "that would snap the door shut and drop the key into a dark drain."
    )
    twist.secret_found = True
    twist.meaning_changed = True
    world.say(
        f'"The first note was bait," {friend.label} whispered. '
        f'"The real clue was the warning."'
    )
    world.say(
        f'"And the key is not for the red button," {luna.label} said. '
        f'"It belongs in the small brass slot beside the arrows."'
    )
    caution.danger_avoided = True

    world.para()
    world.say(
        f"Together they placed the key in the brass slot and turned it slowly. "
        f"{mechanism.label} softened from a sharp rattle to a gentle hum."
    )
    world.say(
        "The locked door opened into a sunny courtyard where a lost kitten was waiting "
        "beside a basket of library books."
    )
    world.say(
        f"The friends carried the kitten and the books to the caretaker. "
        f'"We solved the mystery by checking the warning together," {luna.label} said.'
    )
    world.say(
        f'"And by trusting each other enough to stop," {friend.label} replied.'
    )
    world.say(
        "The red button never moved again. It sat quietly beneath its dusty sign, "
        "a small reminder that an exciting clue is not always a safe instruction."
    )
    world.say(
        f"That evening, {luna.label} and {friend.label} walked home through the rain, "
        "their friendship stronger because caution had helped them find the truth."
    )

    mechanism.meters["tension"] = 0.0
    door.meters["locked"] = 0.0
    world.facts.update(
        friendship=friendship,
        caution=caution,
        twist=twist,
        token=token,
    )
    world.fired.update({
        ("warning",),
        ("friendship",),
        ("twist",),
        ("mechanism_repaired",),
    })
    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a child-friendly mystery about {p.name} and {p.friend_name} finding {p.mechanism} in {p.place}.",
        "Show friendship changing a risky choice into a careful investigation.",
        "Include a cautionary warning and a twist revealing that the first clue was a trap.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            f"Where did {p.name} and {p.friend_name} find the mechanism?",
            f"They found {p.mechanism} beside a locked door in {p.place}.",
        ),
        QAItem(
            "Why did the friends wait before pressing the button twice?",
            "They wanted to look for more clues because the button might be a trick.",
        ),
        QAItem(
            "What warning did the second note give?",
            "It warned that a borrowed key could open the door but might also close the way home.",
        ),
        QAItem(
            "What was the mystery's twist?",
            "The first note was bait: pressing the red button would trigger a spring trap and lose the key.",
        ),
        QAItem(
            "How did the friends safely open the door?",
            "They studied the arrows and placed the key in the small brass slot instead of pressing the red button.",
        ),
        QAItem(
            "How did friendship help solve the mystery?",
            "The friends listened to each other and trusted one another enough to stop, check the warning, and act carefully.",
        ),
        QAItem(
            "What showed that the ending was happy?",
            "The door opened to a sunny courtyard, where the friends rescued a lost kitten and returned the library books.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a mechanism?",
            "A mechanism is a set of parts that work together to make something move, open, ring, or perform another job.",
        ),
        QAItem(
            "Why should people read a warning?",
            "A warning can reveal a danger and help people choose a safer action before trouble begins.",
        ),
        QAItem(
            "What makes a friendship helpful during a mystery?",
            "Friends can share observations, question risky ideas, and make a wiser plan together.",
        ),
    ]


ASP_RULES = r"""
friendship_helpful(S) :- trusts_each_other(S), shared_choice(S).
cautionary_warning(S) :- warning_seen(S), danger_avoided(S).
twist_revealed(S) :- secret_found(S), meaning_changed(S).
safe_solution(S) :- friendship_helpful(S), cautionary_warning(S), twist_revealed(S).
valid_story(S) :- safe_solution(S), mechanism_repaired(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("trusts_each_other", "story1"),
        asp.fact("shared_choice", "story1"),
        asp.fact("warning_seen", "story1"),
        asp.fact("danger_avoided", "story1"),
        asp.fact("secret_found", "story1"),
        asp.fact("meaning_changed", "story1"),
        asp.fact("mechanism_repaired", "story1"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    actual = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if actual == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(actual))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld about a mechanism, friendship, caution, and a twist.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend-name", choices=NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mechanism", choices=MECHANISMS)
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
    friends = [n for n in NAMES if n != name]
    friend = args.friend_name or rng.choice(friends)
    return StoryParams(
        seed=None,
        name=name,
        friend_name=friend,
        place=args.place or rng.choice(PLACES),
        mechanism=args.mechanism or rng.choice(MECHANISMS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id:12} ({entity.kind:9}) {' '.join(details)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
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


CURATED = [
    StoryParams(name="Luna", friend_name="Milo", place="the old clock house", mechanism="a brass key mechanism"),
    StoryParams(name="Nia", friend_name="Theo", place="the glasshouse behind the museum", mechanism="a wooden gear mechanism"),
    StoryParams(name="Pia", friend_name="Arlo", place="the little lighthouse workshop", mechanism="a silver bell mechanism"),
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
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
