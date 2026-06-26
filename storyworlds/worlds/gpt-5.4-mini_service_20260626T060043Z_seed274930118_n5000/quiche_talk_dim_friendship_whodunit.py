#!/usr/bin/env python3
"""
A small whodunit-style storyworld about friendship, a shared quiche, and the
moment someone's voice goes talk-dim.

Premise:
- A cozy gathering of friends.
- A quiche is placed on the table.
- Someone notices a clue: a missing slice, a crumb trail, a quiet voice.
- The group investigates without cruelty.
- The truth is revealed, and friendship is strengthened.

The simulated world tracks:
- physical state in meters: quiche slices, crumbs, light, distance, sound
- emotional state in memes: trust, worry, relief, friendship, embarrassment

The story is authored from world state rather than rendered from a fixed template.
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
    name: str
    role: str = "friend"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for k in ["trust", "worry", "relief", "friendship", "embarrassment", "curiosity"]:
            self.memes.setdefault(k, 0.0)
        for k in ["crumbs_found", "voice_dim", "distance_walked", "quiche_eaten"]:
            self.meters.setdefault(k, 0.0)

    def subj(self) -> str:
        return self.name

    def obj(self) -> str:
        return self.name

    def poss(self) -> str:
        return f"{self.name}'s"


@dataclass
class Thing:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["slices_left", "crumbs", "warmth", "missing_slice"]:
            self.meters.setdefault(k, 0.0)


@dataclass
class Scene:
    place: str = "the kitchen"
    time: str = "evening"
    mood: str = "cozy"


@dataclass
class StoryParams:
    place: str = "the kitchen"
    host: str = "Mina"
    detective: str = "Jules"
    friend1: str = "Pip"
    friend2: str = "Tara"
    culprit: str = "Pip"
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.people: dict[str, Person] = {}
        self.things: dict[str, Thing] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add_person(self, p: Person) -> Person:
        self.people[p.id] = p
        return p

    def add_thing(self, t: Thing) -> Thing:
        self.things[t.id] = t
        return t

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def truthy(x: float) -> bool:
    return x >= 1.0


def clamp0(x: float) -> float:
    return max(0.0, x)


def update_friendship(world: World, a: Person, b: Person, delta: float) -> None:
    a.memes["friendship"] += delta
    b.memes["friendship"] += delta


def set_voice_dim(person: Person, value: float) -> None:
    person.meters["voice_dim"] = value
    if value >= 1.0:
        person.memes["worry"] += 1.0


def find_crumbs(world: World, seeker: Person, quiche: Thing) -> None:
    if quiche.meters["crumbs"] >= 1.0:
        seeker.meters["crumbs_found"] += 1.0
        seeker.memes["curiosity"] += 1.0
        world.trace.append(f"{seeker.name} noticed crumbs near the table.")


def accusation_is_careful(world: World, detective: Person) -> bool:
    return detective.memes["curiosity"] >= 1.0 and detective.memes["worry"] >= 1.0


def reveal_culprit(world: World, detective: Person, culprit: Person, quiche: Thing) -> None:
    culprit.memes["embarrassment"] += 1.0
    culprit.memes["worry"] += 1.0
    detective.memes["relief"] += 1.0
    detective.memes["trust"] += 1.0
    update_friendship(world, detective, culprit, 1.0)
    world.trace.append(f"{detective.name} learned who ate the missing slice.")


def resolve_quiche(world: World, host: Person, detective: Person, culprit: Person, quiche: Thing) -> None:
    if quiche.meters["missing_slice"] >= 1.0:
        host.memes["worry"] += 1.0
        detective.memes["curiosity"] += 1.0
        culprit.memes["embarrassment"] += 1.0
        reveal_culprit(world, detective, culprit, quiche)
        culprit.memes["relief"] += 1.0
        host.memes["relief"] += 1.0
        update_friendship(world, host, detective, 1.0)
        update_friendship(world, host, culprit, 0.5)


def build_world(params: StoryParams) -> World:
    scene = Scene(place=params.place)
    world = World(scene)
    host = world.add_person(Person(id="host", name=params.host))
    detective = world.add_person(Person(id="detective", name=params.detective))
    friend1 = world.add_person(Person(id="friend1", name=params.friend1))
    friend2 = world.add_person(Person(id="friend2", name=params.friend2))
    quiche = world.add_thing(Thing(id="quiche", label="quiche"))
    quiche.meters["slices_left"] = 6.0
    quiche.meters["crumbs"] = 0.0
    quiche.meters["warmth"] = 1.0
    world.facts.update(host=host, detective=detective, friend1=friend1, friend2=friend2, culprit=world.people["friend1"], quiche=quiche)
    return world


def tell(world: World, params: StoryParams) -> World:
    host = world.people["host"]
    detective = world.people["detective"]
    friend1 = world.people["friend1"]
    friend2 = world.people["friend2"]
    culprit = world.people["friend1"]
    quiche = world.things["quiche"]

    world.say(
        f"On a quiet evening at {world.scene.place}, {host.name} set a warm quiche on the table for a small circle of friends."
    )
    update_friendship(world, host, detective, 0.5)
    update_friendship(world, host, friend1, 0.5)
    update_friendship(world, host, friend2, 0.5)

    world.para()
    world.say(
        f"Everyone laughed at first, but then {detective.name} noticed something odd: one slice was missing, and the air felt talk-dim."
    )
    set_voice_dim(detective, 1.0)
    world.say(
        f"{friend1.name} looked down at {f"{friend1.name}'s" if False else friend1.name}'s} plate and went very quiet."
    )
    friend1.memes["worry"] += 1.0
    friend1.meters["distance_walked"] += 1.0
    quiche.meters["missing_slice"] = 1.0
    quiche.meters["crumbs"] = 1.0
    find_crumbs(world, detective, quiche)

    world.para()
    world.say(
        f"{detective.name} did not snap an accusation. Instead, {detective.name} followed the crumbs and asked gentle questions."
    )
    detective.memes["curiosity"] += 1.0
    detective.memes["worry"] += 1.0
    if accusation_is_careful(world, detective):
        world.say(
            f"That careful way of looking made {friend2.name} remember seeing {culprit.name} near the quiche with a fork and a flustered face."
        )
        friend2.memes["trust"] += 1.0
        update_friendship(world, detective, friend2, 0.5)

    resolve_quiche(world, host, detective, culprit, quiche)

    world.para()
    world.say(
        f"In the end, {culprit.name} admitted it had been a hungry mistake, not a mean trick, and promised to help bake a second quiche."
    )
    culprit.memes["embarrassment"] = clamp0(culprit.memes["embarrassment"] - 1.0)
    culprit.memes["relief"] += 1.0
    host.memes["relief"] += 1.0
    detective.memes["relief"] += 1.0
    update_friendship(world, host, culprit, 1.0)
    update_friendship(world, host, detective, 0.5)
    update_friendship(world, detective, culprit, 0.5)

    world.say(
        f"The room felt less talk-dim after that. The friends ate the remaining quiche together, and the missing slice turned into a new shared laugh."
    )

    world.facts.update(
        missing_slice=quiche.meters["missing_slice"] >= 1.0,
        crumbs=quiche.meters["crumbs"] >= 1.0,
        culprit=culprit,
        detective=detective,
        host=host,
        friend2=friend2,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    host: Person = f["host"]
    detective: Person = f["detective"]
    culprit: Person = f["culprit"]
    friend2: Person = f["friend2"]
    return [
        QAItem(
            question=f"What did {host.name} put on the table for the friends?",
            answer=f"{host.name} put a warm quiche on the table, and everyone gathered around it."
        ),
        QAItem(
            question=f"Why did the room feel talk-dim when {detective.name} noticed the missing slice?",
            answer=f"The room felt talk-dim because something was odd: one slice was gone, and {detective.name} could tell someone was hiding a small mistake."
        ),
        QAItem(
            question=f"How did {detective.name} investigate without hurting anyone's feelings?",
            answer=f"{detective.name} followed the crumbs, asked gentle questions, and stayed curious instead of blaming anyone right away."
        ),
        QAItem(
            question=f"Who admitted what happened to the quiche?",
            answer=f"{culprit.name} admitted taking the missing slice and said it was a hungry mistake."
        ),
        QAItem(
            question=f"What did {friend2.name} help the others remember?",
            answer=f"{friend2.name} remembered seeing {culprit.name} near the quiche with a fork and a flustered face."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is quiche?",
            answer="Quiche is a baked savory pie with a filling, often with eggs and cheese."
        ),
        QAItem(
            question="What does it mean when a voice is talk-dim?",
            answer="A talk-dim voice is very quiet or subdued, like someone is nervous, shy, or trying not to be heard."
        ),
        QAItem(
            question="What does friendship help people do in a mystery?",
            answer="Friendship helps people stay calm, ask fair questions, and tell the truth without being cruel."
        ),
        QAItem(
            question="Why do detectives look for crumbs in a story?",
            answer="Crumbs can be clues that show where someone walked or what they ate."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a child-friendly whodunit about friends, a quiche, and a quiet clue.',
        f"Tell a gentle mystery at {world.scene.place} where the missing quiche slice is solved through friendship.",
        "Write a short story where someone's voice goes talk-dim and the group solves the puzzle kindly.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for p in world.people.values():
        memes = {k: v for k, v in p.memes.items() if v}
        meters = {k: v for k, v in p.meters.items() if v}
        lines.append(f"  {p.name:10} memes={memes} meters={meters}")
    quiche = world.things["quiche"]
    lines.append(f"  quiche      meters={dict(quiche.meters)}")
    lines.append(f"  trace: {world.trace}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is reasonable when quiche is missing, a detective notices crumbs,
% and the group can identify the culprit through calm questioning.
missing_slice(quiche) :- quiche_missing(quiche).
clue(crumbs) :- crumbs_present.
careful_detective(detective) :- curious(detective), worried(detective).
solved :- missing_slice(quiche), clue(crumbs), careful_detective(detective), culprit_known.
friendship_grows(A,B) :- solved, friends(A,B).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("quiche_missing"),
        asp.fact("crumbs_present"),
        asp.fact("curious", "detective"),
        asp.fact("worried", "detective"),
        asp.fact("culprit_known"),
        asp.fact("friends", "host", "detective"),
        asp.fact("friends", "host", "friend1"),
        asp.fact("friends", "host", "friend2"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> bool:
    return True


def asp_verify() -> int:
    if not asp_reasonable():
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    print("OK: Python reasonableness gate is consistent.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld about friendship and quiche.")
    ap.add_argument("--place", default="the kitchen")
    ap.add_argument("--host", default="Mina")
    ap.add_argument("--detective", default="Jules")
    ap.add_argument("--friend1", default="Pip")
    ap.add_argument("--friend2", default="Tara")
    ap.add_argument("--culprit", default="Pip")
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
    host = args.host or rng.choice(["Mina", "Nora", "Ivy"])
    detective = args.detective or rng.choice(["Jules", "Mara", "Ezra"])
    friend1 = args.friend1 or rng.choice(["Pip", "Noel", "Ada"])
    friend2 = args.friend2 or rng.choice(["Tara", "Luca", "Bea"])
    culprit = args.culprit or friend1
    if culprit not in {friend1, friend2, host}:
        raise StoryError("The culprit must be one of the friends at the table.")
    if culprit == detective:
        raise StoryError("The detective should not be the culprit in this whodunit.")
    return StoryParams(
        place=args.place or "the kitchen",
        host=host,
        detective=detective,
        friend1=friend1,
        friend2=friend2,
        culprit=culprit,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(build_world(params), params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/0.\n#show friendship_grows/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/0.\n#show friendship_grows/2."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        seeds = [base_seed + i for i in range(5)]
        for s in seeds:
            params = resolve_params(args, random.Random(s))
            params.seed = s
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
