#!/usr/bin/env python3
"""
storyworlds/worlds/discriminate_bad_email_problem_solving_happy_ending.py
========================================================================

A tiny bedtime-story world about a child who learns to discriminate a bad
email from a good one, solves the problem with help, and ends happily.

Seed premise:
- A child sees a bad email and feels worried.
- A helper teaches a simple way to discriminate safe, useful messages from
  bad ones.
- The child solves the problem by checking details instead of panicking.
- The story ends with calm, safety, and a happy ending.

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- typed entities with meters and memes
- state-driven prose
- inline ASP twin and verification
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
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
# Domain model
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


@dataclass
class Setting:
    place: str = "the cozy kitchen table"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class EmailKind:
    id: str
    subject: str
    sender: str
    good: bool
    clue: str
    consequence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    purpose: str
    helps_with: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""


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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the cozy kitchen table", indoor=True, affords={"check_email"}),
    "bedroom": Setting(place="the little bedroom desk", indoor=True, affords={"check_email"}),
    "living_room": Setting(place="the living room couch", indoor=True, affords={"check_email"}),
}

EMAILS = {
    "bad_email": EmailKind(
        id="bad_email",
        subject="Free prize now!",
        sender="sparkly-gifts@example.net",
        good=False,
        clue="strange sender address and rushy words",
        consequence="could trick someone into clicking a bad link",
        tags={"bad", "email", "discriminate"},
    ),
    "good_email": EmailKind(
        id="good_email",
        subject="Your library book is ready",
        sender="library@example.org",
        good=True,
        clue="a familiar sender and a clear, calm message",
        consequence="gives a safe and useful update",
        tags={"good", "email", "discriminate"},
    ),
    "family_email": EmailKind(
        id="family_email",
        subject="Dinner will be a little late",
        sender="mom@example.org",
        good=True,
        clue="a known name and a simple note",
        consequence="helps the family plan dinner",
        tags={"good", "email"},
    ),
}

TOOLS = [
    Tool(
        id="check_sender",
        label="a magnifying glass for sender names",
        purpose="check the sender carefully",
        helps_with={"discriminate"},
        prep="look at the sender line first",
        tail="looked at the sender name and the subject line",
    ),
    Tool(
        id="ask_grownup",
        label="a grown-up helper",
        purpose="ask for help before clicking anything",
        helps_with={"bad", "email"},
        prep="ask a grown-up to read it together",
        tail="read the message together with a grown-up",
    ),
    Tool(
        id="slow_breath",
        label="a slow breath",
        purpose="settle worried feelings before choosing",
        helps_with={"bad"},
        prep="take one slow breath first",
        tail="took a slow breath and thought again",
    ),
]

NAMES = ["Mia", "Leo", "Nora", "Theo", "Lily", "Ben", "Ava", "Noah"]
PARENTS = ["mother", "father"]
TRAITS = ["curious", "gentle", "careful", "brave", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    email: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def is_reasonable(email: EmailKind, tool: Tool) -> bool:
    if email.good:
        return False
    return "discriminate" in tool.helps_with or "email" in tool.helps_with


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for email_id, email in EMAILS.items():
            if email.good:
                continue
            if any(is_reasonable(email, tool) for tool in TOOLS):
                combos.append((place, email_id))
    return combos


def explain_rejection(email: EmailKind) -> str:
    return (
        f"(No story: {email.subject!r} is not a bad email in this world, so it does not need a problem-solving story.)"
    )


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------

def choose_tool(email: EmailKind) -> Optional[Tool]:
    if email.good:
        return None
    for tool in TOOLS:
        if is_reasonable(email, tool):
            return tool
    return None


def tell(setting: Setting, email: EmailKind, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"worry": 0.0, "calm": 0.0, "joy": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}", memes={"calm": 0.0, "joy": 0.0}))
    message = world.add(Entity(
        id=email.id,
        kind="thing",
        type="email",
        label="email",
        phrase=email.subject,
        owner=hero.id,
        meters={"risk": 1.0 if not email.good else 0.0},
        memes={"bad": 1.0 if not email.good else 0.0},
    ))

    tool = choose_tool(email)

    # Setup
    world.say(
        f"{hero.id} was a {trait} little {hero_type} who liked quiet evenings at {setting.place}."
    )
    world.say(
        f"One night, {hero.id} opened a new email with the subject line {message.phrase!r}."
    )
    if not email.good:
        hero.memes["worry"] += 1
        world.say(
            f"It had a {email.clue}, and that made {hero.id} feel worried because {email.consequence}."
        )
    else:
        world.say(
            f"It looked calm and kind, with {email.clue}, so {hero.id} could read it safely."
        )

    # Problem
    if not email.good:
        world.para()
        world.say(
            f"{hero.id} wanted to click right away, but {hero.pronoun('possessive')} {parent_type} said, "
            f'"Let us discriminate carefully first."'
        )
        world.say(
            f"{hero.id} paused and asked for help instead of rushing."
        )

        if tool is not None:
            world.say(
                f"Together they used {tool.label}: they chose to {tool.prep}."
            )
            world.say(
                f"They saw the strange sender line, the pushy words, and the missing familiar details."
            )
            world.say(
                f"That showed the email was bad, so they closed it without clicking anything."
            )
            hero.memes["worry"] = 0.0
            hero.memes["calm"] += 1
            hero.memes["joy"] += 1
            parent.memes["calm"] += 1
            parent.memes["joy"] += 1
            message.meters["risk"] = 0.0
        else:
            raise StoryError("No safe tool exists to solve this email problem.")
    else:
        world.para()
        world.say(
            f"{hero.id} read it slowly, smiled, and put the good news on the table for {hero.pronoun('possessive')} {parent_type}."
        )
        hero.memes["joy"] += 1
        parent.memes["joy"] += 1

    # Ending
    world.para()
    if not email.good:
        world.say(
            f"After that, {hero.id} deleted the bad email, felt proud for being careful, and sat down for a warm bedtime snack."
        )
        world.say(
            f"{hero.id} and {hero.pronoun('possessive')} {parent_type} shared a happy smile, because the problem was solved and the night felt safe again."
        )
    else:
        world.say(
            f"Before bed, {hero.id} tucked the good email away and felt pleased that a careful check had kept everything peaceful."
        )
        world.say(
            f"The house stayed cozy, and {hero.id} fell asleep happy."
        )

    world.facts.update(
        hero=hero,
        parent=parent,
        email=message,
        email_kind=email,
        tool=tool,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    email = f["email_kind"]
    return [
        f'Write a bedtime story for a young child about how {hero.id} learns to discriminate a bad email from a safe one.',
        f'Write a gentle problem-solving story where a {hero.type} named {hero.id} gets a bad email and finds a calm way to handle it.',
        f'Write a happy-ending story that includes the words "discriminate", "bad", and "email".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    email = f["email_kind"]
    tool = f["tool"]
    setting = f["setting"]

    qas = [
        QAItem(
            question=f"What kind of message did {hero.id} find at {setting.place}?",
            answer=f"{hero.id} found a bad email with the subject line {email.subject!r}.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel worried about the email?",
            answer=f"{hero.id} felt worried because the email had {email.clue} and could have been unsafe.",
        ),
        QAItem(
            question=f"Who helped {hero.id} deal with the email problem?",
            answer=f"{hero.id}'s {parent.type} helped by reminding {hero.pronoun('object')} to discriminate carefully.",
        ),
    ]
    if tool is not None:
        qas.append(
            QAItem(
                question=f"What helped {hero.id} tell the bad email from a safe one?",
                answer=f"They used {tool.label} and {tool.tail}, which helped them notice the bad clues.",
            )
        )
    qas.append(
        QAItem(
            question=f"How did the story end after the bad email was handled?",
            answer=f"The story ended happily, with {hero.id} calm, proud, and safe again.",
        )
    )
    return qas


WORLD_KNOWLEDGE = {
    "discriminate": [
        QAItem(
            question="What does it mean to discriminate carefully when checking messages?",
            answer="It means to look for clues that show what is safe, what is bad, and what needs a grown-up to help.",
        )
    ],
    "bad": [
        QAItem(
            question="Why should a child be careful with bad messages?",
            answer="Bad messages can try to trick someone, so it is smart to pause and ask for help.",
        )
    ],
    "email": [
        QAItem(
            question="What is an email?",
            answer="An email is a message sent through the internet to a person or family.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["email_kind"].tags)
    out: list[QAItem] = []
    for tag in ["discriminate", "bad", "email"]:
        if tag in tags or tag in WORLD_KNOWLEDGE:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
bad_email(E) :- email(E), bad(E).
good_email(E) :- email(E), good(E).
can_discriminate(E) :- bad_email(E), tool(T), helps(T, discriminate).
safe_resolution(E) :- bad_email(E), can_discriminate(E).
valid_story(Place, Email) :- setting(Place), bad_email(Email), safe_resolution(Email).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for eid, e in EMAILS.items():
        lines.append(asp.fact("email", eid))
        if e.good:
            lines.append(asp.fact("good", eid))
        else:
            lines.append(asp.fact("bad", eid))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for h in sorted(t.helps_with):
            lines.append(asp.fact("helps", t.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    email: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world about discriminating a bad email and solving it safely."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--email", choices=EMAILS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
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
    if args.email:
        email = EMAILS[args.email]
        if email.good:
            raise StoryError(explain_rejection(email))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.email is None or c[1] == args.email)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, email_id = rng.choice(sorted(combos))
    email = EMAILS[email_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, email=email_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        EMAILS[params.email],
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
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
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="kitchen", email="bad_email", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="bedroom", email="bad_email", name="Leo", gender="boy", parent="father", trait="thoughtful"),
    StoryParams(place="living_room", email="bad_email", name="Nora", gender="girl", parent="mother", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, email) combos:\n")
        for place, email in combos:
            print(f"  {place:12} {email}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.email} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
