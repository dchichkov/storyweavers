#!/usr/bin/env python3
"""
A small story world for a funny, rhyming valentine scene in an arena.

The seed image:
A child enters an arena with a valentine meant for someone special.
Something silly goes wrong, the child gets embarrassed, and then a funny
rhyming fix helps the moment end happily.

The world is modeled with physical meters and emotional memes:
- the arena can be crowded, echoey, or slippery
- a valentine card can be crumpled or still neat
- the child can feel excited, shy, amused, or proud

The story is generated from simulated state, not from a frozen paragraph.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    gender: str
    recipient: str
    arena: str = "the arena"
    seed: Optional[int] = None


@dataclass
class World:
    arena: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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
        w = World(self.arena)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: callable


def _r_echo(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes.get("shout", 0) >= THRESHOLD and ("echo",) not in world.fired:
        world.fired.add(("echo",))
        child.memes["embarrass"] = child.memes.get("embarrass", 0) + 1
        out.append("The words came back in a bouncing echo, which made the child blush.")
    return out


def _r_crumple(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    card = world.entities.get("valentine")
    if not child or not card:
        return out
    if child.meters.get("stumble", 0) >= THRESHOLD and card.meters.get("neat", 0) >= THRESHOLD:
        sig = ("crumple",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        card.meters["neat"] = 0
        card.meters["crumpled"] = 1
        child.memes["worry"] = child.memes.get("worry", 0) + 1
        out.append("The valentine bent in a funny little fold.")
    return out


def _r_laugh(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    if child and child.memes.get("embarrass", 0) >= THRESHOLD and ("laugh",) not in world.fired:
        world.fired.add(("laugh",))
        child.memes["humor"] = child.memes.get("humor", 0) + 1
        child.memes["joy"] = child.memes.get("joy", 0) + 1
        out.append("Then the child giggled at the silly echo, and the giggle made the worry shrink.")
    return out


RULES = [
    Rule("echo", _r_echo),
    Rule("crumple", _r_crumple),
    Rule("laugh", _r_laugh),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyming_line(a: str, b: str) -> str:
    return f"{a}, {b}; {a} and {b}."


def setup_world(params: StoryParams) -> World:
    world = World(params.arena)
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    recipient = world.add(Entity(id="recipient", kind="character", type="friend", label=params.recipient))
    valentine = world.add(Entity(
        id="valentine",
        kind="thing",
        type="card",
        label="valentine",
        phrase="a bright handmade valentine",
        owner="child",
        carried_by="child",
        meters={"neat": 1},
    ))
    world.facts.update(child=child, recipient=recipient, valentine=valentine)
    return world


def tell(world: World) -> None:
    child = world.get("child")
    recipient = world.get("recipient")
    card = world.get("valentine")

    world.say(
        f"{child.label} had a valentine, a tiny heart-card bright and fine, "
        f"and hurried to {world.arena} to share it on time."
    )
    world.say(
        f"The place was wide and echo-y, a funny public stage, "
        f"where every happy whisper bounced around the cage."
    )

    world.para()
    child.memes["excited"] = 1
    world.say(
        f"{child.label} wanted to give the valentine to {recipient.label} with a grin, "
        f"but the big arena made the little heart feel thin."
    )

    child.meters["stumble"] = 1
    child.memes["shout"] = 1
    world.say(
        f"While walking up the steps, {child.label} tripped on a broom, "
        f"and the card flipped like a fish in a room."
    )
    propagate(world, narrate=True)

    world.para()
    if card.meters.get("crumpled", 0) >= THRESHOLD:
        world.say(
            f"{child.label} picked up the card and gave a little shrug, "
            f"then laughed at the fold with a hopeful hug."
        )
    else:
        world.say(
            f"{child.label} kept the card held high, steady and neat, "
            f"and heard the arena drum a cheerful beat."
        )

    child.memes["brave"] = 1
    world.say(
        f"Then {child.label} said a rhyme so bright it made the moment glow: "
        f"'{rhyming_line("I came with a card", "to make your day shine")}'"
    )
    recipient.memes["delight"] = 1
    recipient.memes["love"] = 1
    world.say(
        f"{recipient.label} smiled at the joke and took the valentine with care, "
        f"and the funny little rhyme hung sweetly in the air."
    )

    world.para()
    world.say(
        f"So the child left the arena with a lighter, happier pace, "
        f"and a crumpled valentine that still felt full of grace."
    )

    world.facts.update(
        child=child,
        recipient=recipient,
        valentine=card,
        resolved=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    recipient = f["recipient"]
    return [
        f"Write a short rhyming story about {child.label} bringing a valentine into an arena.",
        f"Tell a funny story where {child.label} tries to give {recipient.label} a valentine and something silly happens in the arena.",
        "Write a child-friendly rhyming tale with a valentine, an arena, and a cheerful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    recipient = f["recipient"]
    card = f["valentine"]
    return [
        QAItem(
            question=f"Who brought the valentine into the arena?",
            answer=f"{child.label} brought the valentine into the arena.",
        ),
        QAItem(
            question=f"What made the scene funny in the arena?",
            answer="The arena echoed the child's words, and the child laughed at the silly sound.",
        ),
        QAItem(
            question=f"What happened to the valentine after the stumble?",
            answer="It got a little crumpled, but it was still sweet and good to give.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{recipient.label} smiled, took the valentine, and the child left feeling happy and brave.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a valentine?",
            answer="A valentine is a kind note or card that shares caring feelings, often with hearts or kind words.",
        ),
        QAItem(
            question="What is an arena?",
            answer="An arena is a big open place where people can gather, watch, or play games.",
        ),
        QAItem(
            question="Why can echoes sound funny?",
            answer="Echoes sound funny because the same sound comes back a moment later from a wall or large space.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for (n,) in world.fired)}")
    return "\n".join(lines)


# ---------------- ASP twin ----------------

ASP_RULES = r"""
child(X) :- child_name(X).
recipient(X) :- recipient_name(X).
thing(valentine).
place(arena).

funny_scene :- echo_event, laugh_event.
crumpled(valentine) :- stumble_event.

valid_story :- child_name(_), recipient_name(_), place(arena), thing(valentine).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("child_name", "child"),
        asp.fact("recipient_name", "recipient"),
        asp.fact("place", "arena"),
        asp.fact("thing", "valentine"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    asp_ok = any(sym.name == "valid_story" for sym in model)
    py_ok = True
    if asp_ok == py_ok:
        print("OK: ASP and Python reasonableness gates agree.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    return 1


# ---------------- Registry ----------------

NAMES_GIRL = ["Mina", "Lila", "Nora", "Tia", "Ava"]
NAMES_BOY = ["Eli", "Milo", "Theo", "Finn", "Noah"]
RECIPIENTS = ["Sam", "Jules", "Riley", "Casey", "Pip"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A funny rhyming valentine story in an arena.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--recipient")
    ap.add_argument("--arena", default="the arena")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    recipient = args.recipient or rng.choice([r for r in RECIPIENTS if r != name])
    arena = args.arena
    return StoryParams(name=name, gender=gender, recipient=recipient, arena=arena)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(name="Mina", gender="girl", recipient="Sam", arena="the arena"),
    StoryParams(name="Eli", gender="boy", recipient="Jules", arena="the arena"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/0."))
        print("ASP model:", model)
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
            header = f"### {p.name} at {p.arena}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
