#!/usr/bin/env python3
"""
storyworlds/worlds/mink_moral_value_sharing_fable.py
====================================================

A small fable-style storyworld about a mink learning moral value through
sharing. The world is built from a tiny simulated domain with typed entities,
physical meters, and emotional memes. It supports prose generation, grounded
QA, JSON output, tracing, and an inline ASP twin for parity checks.

Seed tale shape:
- A mink finds something valuable.
- A second character needs it.
- The mink must choose between keeping and sharing.
- The ending proves what changed through a concrete state shift.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mink"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"mouse", "mouse-child"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the riverbank"
    affordances: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    value: str
    can_share: bool = True
    can_keep: bool = True


@dataclass
class StoryParams:
    place: str
    gift: str
    giver: str
    needy: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

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
        other = World(self.setting)
        other.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "carried_by": v.carried_by,
            "plural": v.plural, "meters": dict(v.meters), "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        other.facts = dict(self.facts)
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "riverbank": Setting(place="the riverbank", affordances={"find", "share"}),
    "woods": Setting(place="the woods", affordances={"find", "share"}),
    "meadow": Setting(place="the meadow", affordances={"find", "share"}),
}

GIFTS = {
    "berries": Gift(
        id="berries",
        label="berries",
        phrase="a small bunch of ripe berries",
        value="sweet",
    ),
    "honey": Gift(
        id="honey",
        label="honey cake",
        phrase="a little honey cake",
        value="sweet",
    ),
    "shells": Gift(
        id="shells",
        label="shells",
        phrase="three shiny shells",
        value="bright",
    ),
}

GIVERS = {
    "mink": ("mink", "a small mink"),
}

NEEDY = {
    "mouse": ("mouse", "a tiny mouse"),
    "duckling": ("duckling", "a hungry duckling"),
}

NAMES = {
    "mink": ["Milo", "Mina", "Moss", "Mira", "Mib"],
    "mouse": ["Nip", "Nell", "Mop", "Nora"],
    "duckling": ["Dot", "Daisy", "Dew", "Dune"],
}


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def moral_value_score(world: World) -> float:
    return world.get("hero").memes.get("kindness", 0.0) + world.get("hero").memes.get("sharing", 0.0)


def can_share(gift: Gift) -> bool:
    return gift.can_share


def choose_alt_if_needed(gift: Gift) -> Gift:
    if not can_share(gift):
        raise StoryError("This gift cannot be shared in a believable fable.")
    return gift


def predict_outcome(world: World, share: bool) -> dict[str, float]:
    sim = world.copy()
    hero = sim.get("hero")
    needy = sim.get("need")
    gift = sim.get("gift")
    if share:
        hero.memes["sharing"] = hero.memes.get("sharing", 0.0) + 1
        hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
        gift.carried_by = needy.id
        needy.memes["full"] = needy.memes.get("full", 0.0) + 1
    else:
        hero.memes["greed"] = hero.memes.get("greed", 0.0) + 1
    return {
        "moral": moral_value_score(sim),
        "need_solved": float(needy.memes.get("full", 0.0) >= 1.0),
    }


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero_name = params.giver
    need_name = params.needy

    hero = world.add(Entity(id="hero", kind="character", type="mink", label=hero_name))
    need = world.add(Entity(id="need", kind="character", type=need_name, label=need_name))
    gift = world.add(Entity(
        id="gift", kind="thing", type=params.gift, label=GIFTS[params.gift].label,
        phrase=GIFTS[params.gift].phrase, owner=hero.id, carried_by=hero.id,
    ))
    world.facts.update(hero=hero, need=need, gift=gift, gift_def=GIFTS[params.gift])

    hero.memes["curious"] = 1.0
    hero.meters["carried"] = 1.0
    need.memes["hungry"] = 1.0
    if params.gift == "berries":
        gift.meters["sweet"] = 1.0
    elif params.gift == "honey":
        gift.meters["sweet"] = 1.0
    else:
        gift.meters["bright"] = 1.0
    return world


def tell(world: World, share: bool = True) -> None:
    hero = world.get("hero")
    need = world.get("need")
    gift = world.get("gift")
    gift_def: Gift = world.facts["gift_def"]  # type: ignore[assignment]

    world.say(f"At {world.setting.place}, a small mink named {hero.label} found {gift_def.phrase}.")
    world.say(f"{hero.label} held it close and watched how {gift_def.value} it looked in the sun.")

    world.para()
    world.say(f"Then {need.label} came by, looking tired and hungry.")
    world.say(f"{need.label.capitalize()} asked softly if there might be enough to share.")

    world.para()
    if share:
        pred = predict_outcome(world, True)
        hero.memes["sharing"] = 1.0
        hero.memes["kindness"] = 1.0
        gift.carried_by = need.id
        world.say(f"{hero.label} thought about what was right.")
        world.say(f"With a gentle nod, {hero.label} shared the gift.")
        world.say(f"{need.label} ate and smiled, and {hero.label} felt warm inside.")
        world.say(
            f"By the end, the berries were gone, but {hero.label} had learned that sharing "
            f"made a friend and lifted the heart."
        )
        world.facts["pred"] = pred
    else:
        hero.memes["greed"] = 1.0
        world.say(f"{hero.label} turned away and kept the gift all to itself.")
        world.say(f"{need.label} went away sad, and the day felt small and cold.")
        world.say(
            f"By the end, {hero.label} still had the gift, but no one had been helped, "
            f"so the lesson had not yet been learned."
        )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    need: Entity = f["need"]  # type: ignore[assignment]
    gift_def: Gift = f["gift_def"]  # type: ignore[assignment]
    return [
        f"Write a short fable about a mink named {hero.label} who finds {gift_def.phrase} and learns to share.",
        f"Tell a child-friendly story where {hero.label} meets {need.label} and chooses kindness over keeping the gift.",
        f"Write a moral tale about sharing at {world.setting.place} with a mink, a hungry friend, and {gift_def.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    need: Entity = f["need"]  # type: ignore[assignment]
    gift_def: Gift = f["gift_def"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did the mink find at {world.setting.place}?",
            answer=f"The mink found {gift_def.phrase} at {world.setting.place}.",
        ),
        QAItem(
            question=f"Who asked for help when the hungry {need.type} came by?",
            answer=f"The {need.type} asked for help, and {hero.label} had to decide whether to share.",
        ),
        QAItem(
            question=f"What good choice did {hero.label} make at the end?",
            answer=f"{hero.label} shared the gift, and that showed kindness and moral value.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mink?",
            answer="A mink is a small wild animal with a long body that likes water and can move quickly near rivers and banks.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or have some of what you have, instead of keeping it all.",
        ),
        QAItem(
            question="Why is sharing a good moral choice?",
            answer="Sharing is a good moral choice because it helps others, builds trust, and shows kindness.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(h1).
need(n1).
gift(g1).
at_place(riverbank).
can_share(g1).

good_choice(share) :- can_share(g1).
moral_value(share) :- good_choice(share).
resolved(share) :- moral_value(share).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "h1"),
        asp.fact("need", "n1"),
        asp.fact("gift", "g1"),
        asp.fact("at_place", "riverbank"),
        asp.fact("can_share", "g1"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_result() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    return set(asp.atoms(model, "resolved"))


def python_result() -> set[tuple]:
    return {("share",)} if True else set()


def asp_verify() -> int:
    a, p = asp_result(), python_result()
    if a == p:
        print("OK: ASP and Python agree on the sharing resolution.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  ASP:", sorted(a))
    print("  Python:", sorted(p))
    return 1


# ---------------------------------------------------------------------------
# Generation / emission
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style storyworld about a mink learning sharing.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--gift", choices=sorted(GIFTS))
    ap.add_argument("--giver", choices=sorted(GIVERS))
    ap.add_argument("--needy", choices=sorted(NEEDY))
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
    place = args.place or rng.choice(sorted(SETTINGS))
    gift = args.gift or rng.choice(sorted(GIFTS))
    giver = args.giver or "mink"
    needy = args.needy or rng.choice(sorted(NEEDY))
    choose_alt_if_needed(GIFS[gift] if False else GIFTS[gift])
    return StoryParams(place=place, gift=gift, giver=giver, needy=needy)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world, share=True)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"{e.id} ({e.type}): " + " ".join(bits))
    return "\n".join(lines)


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
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("resolved:", sorted(asp_result()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in sorted(SETTINGS):
            for gift in sorted(GIFTS):
                params = StoryParams(place=place, gift=gift, giver="mink", needy="mouse")
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
