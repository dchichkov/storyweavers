#!/usr/bin/env python3
"""
storyworlds/worlds/parody_dinky_booth_moral_value_reconciliation_detective.py
===============================================================================

A tiny detective-story world about a dinky booth, a parody clue, moral value,
and reconciliation.

Premise:
- A child detective notices a strange little booth.
- A playful parody message points to a missing item.
- The detective must choose between blaming someone and seeking the truth.
- The ending resolves in reconciliation, with the truth made clear and a broken
  friendship repaired.

This script models a small causal domain:
- physical meters: clue strength, suspicion, damage, repair
- emotional memes: worry, pride, shame, trust, reconciliation, moral_value

It supports the standard Storyweavers storyworld interface plus an inline ASP
reasonableness gate.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["clue", "suspicion", "damage", "repair"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "pride", "shame", "trust", "reconciliation", "moral_value"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Booth:
    label: str
    phrase: str
    clue: str
    size: str = "dinky"
    booth_kind: str = "booth"


@dataclass
class StoryParams:
    place: str
    booth: str
    clue_style: str
    detective_name: str
    detective_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "police_station": Setting(place="the police station", indoor=True, affords={"detect"}),
    "market": Setting(place="the market", indoor=False, affords={"detect"}),
    "museum": Setting(place="the museum lobby", indoor=True, affords={"detect"}),
}

BOOTS = {
    "dinky_booth": Booth(
        label="dinky booth",
        phrase="a dinky booth with a hand-painted sign",
        clue="a tiny painted clue",
        size="dinky",
        booth_kind="booth",
    ),
    "photo_booth": Booth(
        label="photo booth",
        phrase="a photo booth with a creaky curtain",
        clue="a ribbon of fake laughter",
        size="dinky",
        booth_kind="booth",
    ),
    "ticket_booth": Booth(
        label="ticket booth",
        phrase="a little ticket booth with a cracked glass window",
        clue="a stamped ticket stub",
        size="dinky",
        booth_kind="booth",
    ),
}

CLUE_STYLES = {
    "parody": "parody",
    "mock_notice": "parody",
    "funny_sign": "parody",
}

GIRL_NAMES = ["Mina", "Ivy", "Zara", "Nora", "Lila", "June"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Eli", "Noah", "Max"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def detect_reason(world: World, detective: Entity, booth: Booth, friend: Entity) -> bool:
    # The clue is real if the booth exists and the friend feels blamed.
    return booth.size == "dinky" and friend.memes["shame"] >= THRESHOLD


def maybe_mislead(world: World, detective: Entity, booth: Booth, friend: Entity) -> None:
    detective.meters["clue"] += 1
    detective.memes["worry"] += 1
    detective.memes["moral_value"] += 1
    if booth.clue == "a tiny painted clue":
        world.say(
            f"{detective.id} noticed the {booth.label}: {booth.phrase}. "
            f"On the sign, someone had painted a parody clue that looked funny, "
            f"but also strangely important."
        )
    elif booth.clue == "a ribbon of fake laughter":
        world.say(
            f"{detective.id} spotted the {booth.label} and heard a parody laugh "
            f"stuck behind the curtain, like a joke that wanted to hide something."
        )
    else:
        world.say(
            f"{detective.id} found the {booth.label} and a clue that seemed too small "
            f"to matter at first."
        )


def raise_suspicion(world: World, detective: Entity, friend: Entity) -> None:
    detective.meters["suspicion"] += 1
    friend.memes["shame"] += 1
    friend.memes["trust"] -= 0.5
    world.say(
        f"At first, {detective.id} thought {friend.id} had done something wrong. "
        f"That guess made {friend.id} look down at the floor."
    )


def investigate_truth(world: World, detective: Entity, booth: Booth, friend: Entity) -> None:
    detective.meters["clue"] += 1
    detective.memes["worry"] += 0.5
    detective.memes["trust"] += 0.5
    world.say(
        f"But {detective.id} looked again at the {booth.label} and compared the clue "
        f"to the scuff marks nearby. The pieces fit better than blame did."
    )


def repair_harm(world: World, detective: Entity, friend: Entity) -> None:
    detective.meters["repair"] += 1
    friend.memes["shame"] = max(0.0, friend.memes["shame"] - 1.0)
    friend.memes["trust"] += 1.0
    detective.memes["reconciliation"] += 1
    detective.memes["moral_value"] += 1
    world.say(
        f"{detective.id} apologized for jumping to a conclusion, and {friend.id} "
        f"admitted the clue was only a prank. The two of them smiled, because truth "
        f"felt better than winning an argument."
    )


def resolve(world: World, detective: Entity, friend: Entity, booth: Booth) -> None:
    detective.meters["clue"] += 1
    detective.memes["reconciliation"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"In the end, the mystery was small but important: the dinky booth had been "
        f"used for a silly parody, not a theft. {detective.id} and {friend.id} "
        f"walked away side by side, with the booth glowing like a tiny stage for the truth."
    )


def tell(setting: Setting, booth_def: Booth, clue_style: str,
         detective_name: str, detective_gender: str,
         friend_name: str, friend_gender: str) -> World:
    world = World(setting)
    booth = world.add(Entity(
        id="booth",
        kind="thing",
        type="booth",
        label=booth_def.label,
        phrase=booth_def.phrase,
    ))
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        label="detective",
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        label="friend",
    ))

    world.say(
        f"{detective.id} was a little detective who liked solving small mysteries."
    )
    world.say(
        f"{detective.id} and {friend.id} had come to {setting.place} when they found "
        f"{booth_def.phrase}."
    )
    world.para()
    maybe_mislead(world, detective, booth_def, friend)
    raise_suspicion(world, detective, friend)
    investigate_truth(world, detective, booth_def, friend)
    world.para()
    repair_harm(world, detective, friend)
    resolve(world, detective, friend, booth_def)

    world.facts = {
        "setting": setting,
        "booth": booth_def,
        "clue_style": clue_style,
        "detective": detective,
        "friend": friend,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = f["detective"]
    friend = f["friend"]
    booth = f["booth"]
    return [
        f'Write a short detective story for a child that includes the words "parody" and "dinky".',
        f"Tell a mystery about {det.id}, a little detective, a {booth.label}, and a misunderstanding that ends in reconciliation.",
        f"Write a gentle detective tale where {friend.id} is suspected at first, but the truth is found by looking at a dinky booth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    friend = f["friend"]
    booth = f["booth"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What kind of story is this one about {det.id} and the booth?",
            answer=f"It is a little detective story set at {setting.place}, where a small clue leads to a careful investigation.",
        ),
        QAItem(
            question=f"What did {det.id} notice near the {booth.label}?",
            answer=f"{det.id} noticed a parody clue near the {booth.label}, and the clue made the mystery feel funny and suspicious at the same time.",
        ),
        QAItem(
            question=f"Why did {friend.id} feel bad at first?",
            answer=f"{friend.id} felt bad because {det.id} first thought {friend.id} might have caused the problem, which made {friend.id} feel blamed.",
        ),
        QAItem(
            question=f"How did the story end for {det.id} and {friend.id}?",
            answer=f"They ended with reconciliation: {det.id} apologized, the truth came out, and the two friends walked away together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks carefully for clues to solve a problem or mystery.",
        ),
        QAItem(
            question="What does parody mean?",
            answer="Parody is a playful imitation of something else, often made to be funny.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a disagreement or hurt feelings.",
        ),
        QAItem(
            question="What does dinky mean?",
            answer="Dinky means very small, tiny, or little in a way that feels cute or weak.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A booth is relevant if it is dinky and has a parody clue.
relevant_booth(B) :- booth(B), size(B,dinky), clue_style(B,parody).

% A suspicion is reasonable when a friend is blamed before the clue is checked.
has_misunderstanding(D,F) :- detective(D), friend(F), blamed(D,F), relevant_booth(_).

% Reconciliation happens only if the detective learns the truth and apologizes.
can_reconcile(D,F) :- detective(D), friend(F), apology(D,F), truth_found(D,F).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for bid, b in BOOTS.items():
        lines.append(asp.fact("booth", bid))
        lines.append(asp.fact("size", bid, b.size))
        lines.append(asp.fact("clue_style", bid, "parody"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show relevant_booth/1."))
    atoms = sorted(set(asp.atoms(model, "relevant_booth")))
    python = sorted((bid,) for bid, b in BOOTS.items() if b.size == "dinky")
    if set(atoms) == set(python):
        print(f"OK: ASP parity matches Python for relevant booths ({len(atoms)}).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  ASP:", atoms)
    print("  PY :", python)
    return 1


# ---------------------------------------------------------------------------
# Generation / params
# ---------------------------------------------------------------------------

@dataclass
class StoryParamsRegistry:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: dinky booth, parody clue, reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--booth", choices=BOOTS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    booth = args.booth or rng.choice(list(BOOTS))
    detective_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    if args.name:
        detective_name = args.name
    else:
        detective_name = rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    if args.friend:
        friend_name = args.friend
    else:
        friend_name = rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != detective_name])
    return StoryParams(
        place=place,
        booth=booth,
        clue_style="parody",
        detective_name=detective_name,
        detective_gender=detective_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        BOOTS[params.booth],
        params.clue_style,
        params.detective_name,
        params.detective_gender,
        params.friend_name,
        params.friend_gender,
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
        print()
        print("--- world trace ---")
        for e in sample.world.entities.values():
            m = {k: v for k, v in e.meters.items() if v}
            e_ = {k: v for k, v in e.memes.items() if v}
            bits = []
            if m:
                bits.append(f"meters={m}")
            if e_:
                bits.append(f"memes={e_}")
            print(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show relevant_booth/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show relevant_booth/1."))
        print(sorted(set(asp.atoms(model, "relevant_booth"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("police_station", "dinky_booth", "parody", "Mina", "girl", "Owen", "boy"),
            StoryParams("museum", "photo_booth", "parody", "Theo", "boy", "Ivy", "girl"),
            StoryParams("market", "ticket_booth", "parody", "Lila", "girl", "Max", "boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(s, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
