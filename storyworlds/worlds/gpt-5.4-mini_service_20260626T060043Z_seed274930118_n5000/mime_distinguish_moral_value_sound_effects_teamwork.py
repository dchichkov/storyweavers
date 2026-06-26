#!/usr/bin/env python3
"""
Standalone storyworld: a rhyming little tale about a mime who learns to
distinguish kind help from showy trouble, with teamwork and sound effects.

The premise is a small stage world: a mime troupe is rehearsing a parade.
The hero wants to make a splash, but a friend needs the troupe to work
together. The turn is that the hero learns to distinguish noisy attention from
real help, and the ending image proves the change through a shared performance.
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
# Small domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    role: str = ""
    label: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if case == "subject":
            return "they" if self.plural else "he"
        if case == "object":
            return "them" if self.plural else "him"
        return "their" if self.plural else "his"

    def possessive(self) -> str:
        return "their" if self.plural else "his"


@dataclass
class Stage:
    place: str = "the little stage"
    backstage: str = "the back curtain"
    affords: set[str] = field(default_factory=lambda: {"rehearsal", "pantomime"})


@dataclass
class Act:
    id: str
    verb: str
    showy_noise: str
    help_noise: str
    moral_choice: str
    rhyme_end: str
    keyword: str


@dataclass
class Prop:
    id: str
    label: str
    role: str
    protects: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    act: str
    prop: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state and narration
# ---------------------------------------------------------------------------
class World:
    def __init__(self, stage: Stage) -> None:
        self.stage = stage
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
STAGE = Stage()

ACTS = {
    "bells": Act(
        id="bells",
        verb="ring little bells",
        showy_noise="jingle-jangle",
        help_noise="tap-tap",
        moral_choice="choose to help instead of hog the spotlight",
        rhyme_end="bright and light",
        keyword="bells",
    ),
    "sticks": Act(
        id="sticks",
        verb="clack two sticks",
        showy_noise="clack-clack",
        help_noise="tick-tick",
        moral_choice="use small signals to guide the team",
        rhyme_end="quick and slick",
        keyword="sticks",
    ),
    "shoes": Act(
        id="shoes",
        verb="squeak silly shoes",
        showy_noise="squeak-squeak",
        help_noise="shush-shush",
        moral_choice="make room for everyone to move together",
        rhyme_end="neat and sweet",
        keyword="shoes",
    ),
}

PROPS = {
    "scarf": Prop(id="scarf", label="a red scarf", role="signal", protects={"hands"}),
    "hat": Prop(id="hat", label="a floppy hat", role="focus", protects={"head"}),
    "glove": Prop(id="glove", label="a white glove", role="signal", protects={"hands"}),
}

NAMES = ["Milo", "Pip", "Noa", "Luca", "Jori", "Tess", "Beni", "Mara"]
BUDDIES = ["Ari", "June", "Sora", "Rae"]
PLACES = ["the little stage", "the town square", "the school hall"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def act_needs_teamwork(act: Act) -> bool:
    return True


def prop_helps(act: Act, prop: Prop) -> bool:
    return prop.role in {"signal", "focus"} and len(prop.protects) > 0


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for aid, act in ACTS.items():
        for pid, prop in PROPS.items():
            if act_needs_teamwork(act) and prop_helps(act, prop):
                out.append((aid, pid))
    return out


def explain_rejection(act: Act, prop: Prop) -> str:
    return (
        f"(No story: {act.verb} needs a prop that can support teamwork, but "
        f"{prop.label} does not make a believable shared cue.)"
    )


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def rhyme_line(verb: str, end: str) -> str:
    return f"and every step felt snug and right, with a beat that ended {end}."


def tell(act: Act, prop: Prop, name: str, place: str, buddy: str) -> World:
    world = World(STAGE)
    mime = world.add(Entity(id=name, kind="character", role="mime", label="mime"))
    friend = world.add(Entity(id=buddy, kind="character", role="helper", label="friend"))
    prop_ent = world.add(Entity(id=prop.id, role=prop.role, label=prop.label))

    world.facts.update(mime=mime, friend=friend, prop=prop_ent, act=act, place=place)

    world.say(
        f"{mime.id} was a little mime who loved to {act.verb} at {place}, "
        f"and {mime.pronoun()} always hoped the day would feel {act.rhyme_end}."
    )
    world.say(
        f"{mime.id} could make a tiny {act.showy_noise}, but {friend.id} was the one "
        f"who knew how to keep the whole troupe in time."
    )

    world.para()
    world.say(
        f"One day, the troupe gathered near {place} for a parade rehearsal. "
        f"{friend.id} held up {prop.label}, because the little prop gave the group a clear cue."
    )
    world.say(
        f"{mime.id} wanted to be the star and went {act.showy_noise} too loudly, "
        f"so the others wobbled and missed the beat."
    )

    world.say(
        f"{friend.id} did not frown. Instead, {friend.id} whispered, "
        f"\"Can you distinguish a noisy trick from a helpful signal?\""
    )
    mime.memes["embarrassment"] = 1
    mime.memes["curiosity"] = 1

    world.para()
    world.say(
        f"{mime.id} paused and listened. The loud sound was only for show, "
        f"but the soft cue was for teamwork. {mime.id} could distinguish the two at last."
    )
    mime.memes["understanding"] = 1
    mime.memes["pride"] = 1
    friend.memes["trust"] = 1

    world.say(
        f"So {mime.id} put the shiny bit aside and copied {friend.id}'s gentle cue: "
        f"{act.help_noise}, {act.help_noise}, nice and slow."
    )
    world.say(
        f"Then the troupe moved together, {friend.id} leading and {mime.id} helping, "
        f"{rhyme_line(act.verb, act.rhyme_end)}"
    )
    world.say(
        f"By the end, {mime.id} had learned a moral value that mattered more than applause: "
        f"{act.moral_choice}."
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act: Act = f["act"]
    return [
        f'Write a rhyming story for a child about a mime who can distinguish "{act.showy_noise}" from "{act.help_noise}".',
        f"Tell a gentle teamwork story where {f['mime'].id} learns that {act.moral_choice}.",
        f'Write a small stage story with the word "mime" and the idea of distinguishing a useful signal from a flashy sound effect.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mime: Entity = f["mime"]
    friend: Entity = f["friend"]
    act: Act = f["act"]
    prop: Prop = f["prop"]
    place = f["place"]

    return [
        QAItem(
            question=f"What kind of character is {mime.id} in the story?",
            answer=f"{mime.id} is a little mime who likes to perform on the stage and work with a team.",
        ),
        QAItem(
            question=f"What did {mime.id} need to distinguish during rehearsal?",
            answer=(
                f"{mime.id} needed to distinguish a noisy showy sound, \"{act.showy_noise}\", "
                f"from the softer teamwork cue, \"{act.help_noise}\"."
            ),
        ),
        QAItem(
            question=f"How did {friend.id} help the troupe at {place}?",
            answer=(
                f"{friend.id} helped by holding up {prop.label} and giving a clear cue so everyone "
                f"could move together in time."
            ),
        ),
        QAItem(
            question=f"What moral value did {mime.id} learn by the end?",
            answer=(
                f"{mime.id} learned that real kindness is helping the group, not just making noise "
                f"for attention."
            ),
        ),
    ]


KNOWLEDGE = {
    "mime": [
        QAItem(
            question="What does a mime do?",
            answer="A mime tells a story with actions, facial expression, and body movement instead of talking much.",
        )
    ],
    "distinguish": [
        QAItem(
            question="What does it mean to distinguish two things?",
            answer="To distinguish two things means to tell them apart and notice how they are different.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help one another and work together to reach the same goal.",
        )
    ],
    "sound": [
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special noise that helps make a story, show, or game feel more alive.",
        )
    ],
    "moral": [
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good idea about how to treat others, like being kind, honest, or helpful.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    return [item for key in ["mime", "distinguish", "teamwork", "sound", "moral"] for item in KNOWLEDGE[key]]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable when the act can support teamwork and the prop is a
% believable cue for the mime troupe.
helpful_prop(P) :- prop(P), role(P, signal).
helpful_prop(P) :- prop(P), role(P, focus).

valid(A, P) :- act(A), prop(P), teamwork(A), helpful_prop(P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for aid, act in ACTS.items():
        lines.append(asp.fact("act", aid))
        lines.append(asp.fact("teamwork", aid))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("role", pid, prop.role))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------
def valid_story_params() -> list[tuple[str, str]]:
    return valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.act and args.prop and (args.act, args.prop) not in valid_combos():
        raise StoryError(explain_rejection(ACTS[args.act], PROPS[args.prop]))

    combos = [
        (a, p)
        for a, p in valid_combos()
        if (args.act is None or a == args.act) and (args.prop is None or p == args.prop)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    act, prop = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(act=act, prop=prop, name=name, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    act = ACTS[params.act]
    prop = PROPS[params.prop]
    place = STAGE.place
    rng = random.Random(params.seed or 0)
    buddy = rng.choice(BUDDIES)
    if params.name == buddy:
        buddy = next(x for x in BUDDIES if x != buddy)

    world = tell(act, prop, params.name, place, buddy)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"  {ent.id:10} ({ent.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world about a mime, distinguishing sound, and teamwork."
    )
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name", choices=NAMES)
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


CURATED = [
    StoryParams(act="bells", prop="scarf", name="Milo"),
    StoryParams(act="sticks", prop="glove", name="Pip"),
    StoryParams(act="shoes", prop="hat", name="Noa"),
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for a, p in combos:
            print(f"  {a} {p}")
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
