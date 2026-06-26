#!/usr/bin/env python3
"""
A standalone storyworld for a small Rhyming Story domain about a saddle,
a snoop, and an ignite moment.

The premise:
- A child loves a pony and its special saddle.
- The child snoops where they should not, hoping to get ready for a ride.
- A tiny danger appears around fire/light, and an adult warns them.
- Dialogue turns the moment from sneaky to safe.
- The ending proves what changed: the saddle is ready, the barn stays safe,
  and the child learns to ask instead of snooping.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Place:
    name: str
    indoors: bool = False
    allows: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "barn": Place(name="the barn", indoors=True, allows={"saddle", "snoop", "ignite"}),
    "stable": Place(name="the stable", indoors=True, allows={"saddle", "snoop", "ignite"}),
    "yard": Place(name="the yard", indoors=False, allows={"saddle", "snoop", "ignite"}),
}

ITEMS = {
    "saddle": Item(
        id="saddle",
        label="saddle",
        phrase="a small brown saddle with a shiny buckle",
        region="back",
        genders={"girl", "boy"},
    ),
    "lantern": Item(
        id="lantern",
        label="lantern",
        phrase="a bright little lantern",
        region="hand",
        genders={"girl", "boy"},
    ),
    "matchbox": Item(
        id="matchbox",
        label="matchbox",
        phrase="a tiny matchbox",
        region="pocket",
        genders={"girl", "boy"},
    ),
}

NAMES = {
    "girl": ["Maya", "Lina", "Pia", "Nora", "Ruby"],
    "boy": ["Owen", "Finn", "Max", "Theo", "Eli"],
}
TRAITS = ["curious", "brave", "playful", "bright", "bouncy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is reasonable when the place allows all the pieces involved.
valid_story(Place, Item, Gender) :- place(Place), item(Item), wears(Gender, Item), allows(Place, Item).

% Snoop is only interesting when a child sneaks into a place with a saddle.
interesting_story(Place, Item, Gender) :- valid_story(Place, Item, Gender), item(Item), item_kind(Item, saddle).

% Ignite is safe only if the story includes a lantern and not the matchbox as the risky focus.
safe_ignite(Item) :- item_kind(Item, lantern).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(place.allows):
            lines.append(asp.fact("allows", pid, a))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_kind", iid, item.id))
        lines.append(asp.fact("worn_on", iid, item.region))
        for g in sorted(item.genders):
            lines.append(asp.fact("wears", g, iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            if place_id in {"barn", "stable", "yard"} and item_id in {"saddle", "lantern", "matchbox"}:
                combos.append((place_id, item_id, "any"))
    return combos


def explain_rejection(place: str, item: str) -> str:
    return (
        f"(No story: {ITEMS[item].label} and {PLACES[place].name} do not make a strong enough "
        f"saddle-snoop-ignite scene for this world.)"
    )


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

def rhyming_opening(name: str, trait: str, place: str) -> str:
    return f"{name} was a {trait} child by the {place}, with a hop in the step and a grin in the face."


def gentle_rhyme(text: str) -> str:
    return text


def predict_risk(world: World, item_id: str) -> bool:
    # If the story centers on the lantern or matchbox in a lit place, there is risk.
    return item_id in {"lantern", "matchbox"} and world.place.name in {"the barn", "the stable", "the yard"}


def tell_story(world: World, hero: Entity, parent: Entity, item: Entity, item_cfg: Item) -> None:
    world.say(rhyming_opening(hero.id, next(t for t in hero.memes.get("traits", []) if t != "little"), world.place.name))
    world.say(f"{hero.pronoun().capitalize()} loved the pony and loved the {item_cfg.label}; it gleamed like honey.")

    world.para()
    world.say(f"One day, {hero.id} went snoop-snoop-snooping where the tack boxes tucked.")
    world.say(f'"What are you doing?" asked {parent.pronoun().capitalize()}.')
    world.say(f'"I want to get the {item_cfg.label}!" said {hero.id}.')
    world.say(f'"First ask," said {parent.pronoun().capitalize()}, "for snooping makes trouble with luck."')

    world.para()
    if item_cfg.id == "saddle":
        world.say(f"{hero.id} had found the saddle, but a lantern sat near a shelf of dry hay.")
        world.say(f'"Please do not ignite anything near the hay," said {parent.pronoun().capitalize()}.')
        world.say(f'"I will not," said {hero.id}, "I only want the ride, not a fiery night."')
        world.say(f"{hero.id} blew out the matchbox thought and carried the saddle with care.")
        world.say(f'"Now that you asked, we can saddle the pony," said {parent.pronoun().capitalize()}, "and the barn can stay fair."')
        world.say(f"{hero.id} buckled the saddle, soft and sound, and the pony stood still on the straw-covered ground.")
    else:
        world.say(f"{hero.id} found the {item_cfg.label}, but the bright little light could not be lit alone.")
        world.say(f'"Do not ignite it by yourself," said {parent.pronoun().capitalize()}, "wait for me, then we will make the glow our own."')
        world.say(f'{hero.id} nodded and asked, not snooped, and the tiny light shone warm and bright.')
        world.say(f"Together they watched the gentle glow, and the barn felt cozy through the night.")

    world.para()
    world.say(f"In the end, {hero.id} learned a kinder way: ask first, then play.")
    world.say(f"The saddle was ready, the worry was small, and the barn stayed safe and snug for all.")

    world.facts.update(hero=hero, parent=parent, item=item, item_cfg=item_cfg)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    item_cfg = f["item_cfg"]
    return [
        f'Write a rhyming story for young children about a child who tries to snoop around a {world.place.name} for a {item_cfg.label}.',
        f"Tell a dialogue-heavy story where {hero.id} wants the {item_cfg.label}, but {parent.pronoun('subject').capitalize()} warns about ignite danger.",
        f'Write a gentle rhyming tale that uses the words "saddle", "snoop", and "ignite".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    item_cfg = f["item_cfg"]
    return [
        QAItem(
            question=f"What did {hero.id} want at {world.place.name}?",
            answer=f"{hero.id} wanted the {item_cfg.label} so {hero.id} could get ready for a pony ride.",
        ),
        QAItem(
            question=f"Why did {parent.id} warn {hero.id} about ignite danger?",
            answer=f"{parent.id} worried that a flame or a spark could be unsafe near dry hay and barn things.",
        ),
        QAItem(
            question=f"What changed after {hero.id} stopped snooping?",
            answer=f"{hero.id} asked first, got help, and the {item_cfg.label} was used safely instead of causing trouble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a saddle for?",
            answer="A saddle helps a person sit on a horse or pony more comfortably and stay steady while riding.",
        ),
        QAItem(
            question="What does snoop mean?",
            answer="To snoop means to look around secretly when you should be asking first.",
        ),
        QAItem(
            question="What does ignite mean?",
            answer="To ignite means to start burning or make a flame begin.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.item and args.item not in ITEMS:
        raise StoryError("Unknown item.")
    place = args.place or rng.choice(list(PLACES))
    item = args.item or rng.choice(list(ITEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender not in ITEMS[item].genders:
        raise StoryError(f"(No story: a {ITEMS[item].label} doesn't fit that gender choice here.)")
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, item=item, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    item_cfg = ITEMS[params.item]
    world = World(place)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        memes={"traits": ["little", params.trait]},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=params.parent,
    ))
    item = world.add(Entity(
        id=item_cfg.id,
        type=item_cfg.id,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))

    world.say(f"{hero.id} was a {params.trait} child by the {place.name}, with a hop in the step and a grin in the face.")
    world.say(f"{hero.id} loved the pony and loved the {item_cfg.label}; it gleamed like honey.")
    world.para()
    world.say(f"One day, {hero.id} went snoop-snoop-snooping where the tack boxes tucked.")
    world.say(f'"What are you doing?" asked {parent.pronoun().capitalize()}.')
    world.say(f'"I want the {item_cfg.label}!" said {hero.id}.')
    world.say(f'"First ask," said {parent.pronoun().capitalize()}, "for snooping makes trouble with luck."')

    world.para()
    if item_cfg.id == "saddle":
        world.say(f"{hero.id} had found the saddle, but a lantern sat near a shelf of dry hay.")
        world.say(f'"Please do not ignite anything near the hay," said {parent.pronoun().capitalize()}.')
        world.say(f'"I will not," said {hero.id}, "I only want the ride, not a fiery night."')
        world.say(f"{hero.id} carried the saddle with care, and the pony waited calm in the air.")
        world.say(f'"Now that you asked, we can saddle the pony," said {parent.pronoun().capitalize()}, "and the barn can stay fair."')
        world.say(f"{hero.id} buckled the saddle, soft and sound, and the pony stood still on the straw-covered ground.")
    else:
        world.say(f"{hero.id} found the {item_cfg.label}, but the little light should not be lit alone.")
        world.say(f'"Do not ignite it by yourself," said {parent.pronoun().capitalize()}, "wait for me, then we will make the glow our own."')
        world.say(f"{hero.id} nodded and asked, not snooped, and the tiny light shone warm and bright.")
        world.say(f"Together they watched the gentle glow, and the barn felt cozy through the night.")

    world.para()
    world.say(f"In the end, {hero.id} learned a kinder way: ask first, then play.")
    world.say(f"The saddle was ready, the worry was small, and the barn stayed safe and snug for all.")

    world.facts.update(hero=hero, parent=parent, item=item, item_cfg=item_cfg)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld about saddle, snoop, and ignite.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    StoryParams(place="barn", item="saddle", name="Maya", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="stable", item="lantern", name="Owen", gender="boy", parent="father", trait="playful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
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
            except StoryError as e:
                print(e)
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
