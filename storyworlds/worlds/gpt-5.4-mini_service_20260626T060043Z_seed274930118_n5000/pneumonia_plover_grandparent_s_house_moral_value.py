#!/usr/bin/env python3
"""
A standalone story world about an animal child visiting a grandparent's house,
where a small mystery, a moral choice, and a foreshadowed illness turn into a
gentle rescue story.

Seed image:
- A young plover arrives at a grandparent's house.
- The grandparent seems tired and coughs.
- The plover notices clues, solves the mystery of pneumonia, and learns that
  caring means speaking up and helping before things get worse.

This world is constraint-checked and emits both prose and Q&A.
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
# Registries
# ---------------------------------------------------------------------------

CHARACTER_KINDS = ("plover", "duckling", "kitten", "fox kit", "bunny")
GRANDPARENT_KINDS = ("grandmother", "grandfather", "grandparent")
MOOD_TRAITS = ("brave", "curious", "kind", "careful", "small", "quick")

CLUES = {
    "cough": "a dry cough that kept coming back",
    "fever": "a hot forehead and tired eyes",
    "breathing": "short, careful breaths",
    "blanket": "a blanket pulled tight even near the fireplace",
    "tea": "a cup of warm tea sitting untouched",
    "window": "a cold draft slipping in from a cracked window",
}

MORAL_VALUES = {
    "ask_for_help": "It is wise to ask for help when something seems wrong.",
    "notice_clues": "Careful noticing can help solve a mystery before it grows bigger.",
    "care_for_elders": "Kind children help their elders get what they need.",
    "tell_the_truth": "Telling the truth can keep someone safe.",
}

WORLD_KNOWLEDGE = {
    "pneumonia": [
        (
            "What is pneumonia?",
            "Pneumonia is an illness that makes the lungs sore and makes breathing hard.",
        ),
        (
            "Why do people with pneumonia rest?",
            "People with pneumonia rest so their bodies can get stronger while they heal.",
        ),
    ],
    "plover": [
        (
            "What is a plover?",
            "A plover is a small bird with quick feet that lives near water and open ground.",
        ),
        (
            "What can a plover do well?",
            "A plover can dart, watch carefully, and notice tiny changes around it.",
        ),
    ],
    "grandparent": [
        (
            "Who is a grandparent?",
            "A grandparent is the parent of your mother or father, and often has warm stories to share.",
        ),
    ],
    "house": [
        (
            "What is a house?",
            "A house is a place where people live and keep things like beds, cups, and blankets.",
        ),
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something puzzling that you try to figure out by looking for clues.",
        ),
    ],
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

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

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "subject": "it",
            "object": "it",
            "possessive": "its",
        }
        if self.type in {"plover", "bird", "duckling", "kitten", "bunny"}:
            return mapping[case]
        return mapping[case]

    def they(self) -> str:
        return "they"


@dataclass
class StoryParams:
    place: str = "grandparent's house"
    child_kind: str = "plover"
    grandparent_kind: str = "grandparent"
    trait: str = "curious"
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = _copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Reasonable story constraints
# ---------------------------------------------------------------------------

def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "grandparent's house":
        raise StoryError("This world is set only in a grandparent's house.")
    if params.child_kind != "plover":
        raise StoryError("This storyworld is anchored on a plover child.")
    if params.grandparent_kind not in GRANDPARENT_KINDS:
        raise StoryError("Invalid grandparent role.")
    if params.trait not in MOOD_TRAITS:
        raise StoryError("Invalid trait selection.")


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% The child notices clues that can point to a hidden illness.
mystery_clue(cough).
mystery_clue(fever).
mystery_clue(breathing).
mystery_clue(blanket).

% Pneumonia is the illness in this world.
illness(pneumonia).

% A clue set is enough to suspect pneumonia.
suspect_pneumonia :- mystery_clue(cough), mystery_clue(fever), mystery_clue(breathing).

% The moral turn happens when the child asks for help and tells the truth.
moral_good :- asked_for_help, told_truth.

% The story resolves when help arrives and the grandparent rests.
resolved :- suspect_pneumonia, moral_good, got_help.
#show suspect_pneumonia/0.
#show moral_good/0.
#show resolved/0.
"""

def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("illness", "pneumonia"),
        asp.fact("place", "grandparent_s_house"),
        asp.fact("child", "plover"),
        asp.fact("grandparent", "grandparent"),
    ]
    for clue in ("cough", "fever", "breathing", "blanket"):
        lines.append(asp.fact("mystery_clue", clue))
    lines.append(asp.fact("asked_for_help"))
    lines.append(asp.fact("told_truth"))
    lines.append(asp.fact("got_help"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    atoms = {str(sym) for sym in model}
    want = {"suspect_pneumonia", "moral_good", "resolved"}
    if want.issubset(atoms):
        print("OK: ASP twin reaches the expected story resolution.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected atoms.")
    print("MODEL:", sorted(atoms))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(place=params.place)

    child_name = "Pip"
    gp_name = "Grandparent"

    child = world.add(Entity(id=child_name, kind="character", type=params.child_kind, label="little plover"))
    gp = world.add(Entity(id=gp_name, kind="character", type=params.grandparent_kind, label="grandparent"))

    world.add(Entity(id="blanket", type="thing", label="blanket", phrase="a soft blanket", owner=gp.id))
    world.add(Entity(id="tea", type="thing", label="tea", phrase="a cup of tea", owner=gp.id))
    world.add(Entity(id="window", type="thing", label="window", phrase="a cracked window", owner=gp.id))

    child.meters["alert"] = 0.0
    child.meters["courage"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["care"] = 0.0

    gp.meters["tired"] = 1.0
    gp.meters["sick"] = 1.0
    gp.memes["trust"] = 0.0

    world.facts.update(
        child=child,
        gp=gp,
        clue_order=["cough", "fever", "breathing", "blanket"],
        illness="pneumonia",
        moral="ask_for_help",
        resolved=False,
    )
    return world


def tell_story(world: World) -> None:
    child = world.get("Pip")
    gp = world.get("Grandparent")

    world.say(
        f"Little Pip was a curious plover who visited {gp.label} at the grandparent's house."
    )
    world.say(
        "The rooms were warm and tidy, with tea on the table and soft light on the walls."
    )
    world.say(
        "But Pip noticed something odd: a dry cough, a hot forehead, and breaths that came too short."
    )
    world.say(
        "Near the chair, a blanket was pulled tight, and the untouched tea looked like a tiny clue."
    )

    world.para()
    child.meters["alert"] += 1.0
    child.memes["worry"] += 1.0
    world.say(
        "Pip's feathers stood a little straighter. This was not a normal sleepy afternoon."
    )
    world.say(
        "The little plover remembered that a mystery could hide inside small signs."
    )
    world.say(
        "Instead of guessing, Pip decided to ask for help and tell the truth."
    )

    world.para()
    child.meters["courage"] += 1.0
    child.memes["care"] += 1.0
    gp.memes["trust"] += 1.0
    world.say(
        'Pip said, "Grandparent, something seems wrong. Your cough, your breathing, and your hot forehead all fit together."'
    )
    world.say(
        "The grandparent listened carefully, and Pip called for a grown-up who could help."
    )
    world.say(
        "Soon the mystery became clear: it was pneumonia, and rest and care were needed right away."
    )

    world.para()
    gp.meters["rest"] = 1.0
    world.facts["resolved"] = True
    world.say(
        "The house grew calmer after that. The blanket stayed over the grandparent's shoulders, the tea got warm again, and help arrived in time."
    )
    world.say(
        "Pip felt proud not because the mystery was scary, but because speaking up had helped solve it."
    )
    world.say(
        "At the end, the little plover sat by the window, watching the afternoon light, while the grandparent rested safely."
    )


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        "Write an animal story set in a grandparent's house where a plover notices clues to an illness and learns a moral lesson.",
        "Tell a gentle mystery story for children about a plover, pneumonia, and asking for help at a grandparent's house.",
        "Write a short moral-value story with foreshadowing, where careful noticing solves a small household mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who is the story about?",
            answer="The story is about Pip, a little plover who visits a grandparent's house.",
        ),
        QAItem(
            question="What mystery did Pip solve?",
            answer="Pip solved the mystery of why the grandparent seemed unwell: it was pneumonia.",
        ),
        QAItem(
            question="What clues made Pip worry?",
            answer="Pip noticed a dry cough, a hot forehead, short breaths, and an untouched cup of tea.",
        ),
        QAItem(
            question="What moral did Pip learn?",
            answer="Pip learned that it is wise to ask for help and tell the truth when something seems wrong.",
        ),
        QAItem(
            question="How did the story foreshadow the problem?",
            answer="The story foreshadowed the problem by showing small signs like coughing, tired eyes, and careful breathing before the illness was named.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ("plover", "pneumonia", "grandparent", "house", "mystery"):
        out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id}: {ent.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: plover, pneumonia, and a mystery at a grandparent's house.")
    ap.add_argument("--place", default="grandparent's house")
    ap.add_argument("--child-kind", choices=CHARACTER_KINDS, default="plover")
    ap.add_argument("--grandparent-kind", choices=GRANDPARENT_KINDS, default="grandparent")
    ap.add_argument("--trait", choices=MOOD_TRAITS)
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
    params = StoryParams(
        place=args.place or "grandparent's house",
        child_kind=args.child_kind or "plover",
        grandparent_kind=args.grandparent_kind or "grandparent",
        trait=args.trait or rng.choice(MOOD_TRAITS),
        seed=args.seed,
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
    StoryParams(trait="curious"),
    StoryParams(trait="brave"),
    StoryParams(trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("ASP atoms:")
        for sym in model:
            print(str(sym))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
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
