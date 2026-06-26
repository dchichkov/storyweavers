#!/usr/bin/env python3
"""
storyworlds/worlds/reed_confess_invent_twist_misunderstanding_heartwarming.py
==============================================================================

A small heartwarming storyworld about reeds, invention, and a misunderstanding
that turns into a gentle confession.

Seed premise:
- A child loves the riverside reeds and wants to invent something clever.
- A misunderstanding makes an adult think the child ruined the reeds on purpose.
- The child confesses, and the twist is that the "broken" reeds became a new
  little instrument or craft that brings them closer together.

This world uses a tiny stateful simulation:
- physical meters track gathered reeds, tools, and whether a handmade invention
  exists
- emotional memes track curiosity, worry, misunderstanding, confession, and
  relief

The prose is driven by world state, not swapped nouns.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    near_water: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    twist: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    plural: bool = False
    hands: int = 1
    fragile: bool = False
    fits_in: str = "pocket"


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

PLACES = {
    "riverbank": Place(id="riverbank", label="the riverbank", near_water=True, affords={"reed", "invent"}),
    "pond": Place(id="pond", label="the pond", near_water=True, affords={"reed", "invent"}),
    "garden": Place(id="garden", label="the garden", near_water=False, affords={"invent"}),
}

ACTIONS = {
    "reed": Activity(
        id="reed",
        verb="pick some reeds",
        gerund="picking reeds",
        rush="run to the edge of the water",
        risk="someone might think the reeds were ruined",
        twist="the reeds were perfect for a tiny invention",
        tags={"reed", "water"},
    ),
    "invent": Activity(
        id="invent",
        verb="invent a little reed flute",
        gerund="inventing a little reed flute",
        rush="hurry to the workbench",
        risk="the work might look like trouble at first",
        twist="the work was actually a gift",
        tags={"invent", "reed"},
    ),
}

ITEMS = {
    "knife": Item(
        id="knife",
        label="a little pocket knife",
        phrase="a little pocket knife with a dull shine",
        type="knife",
        hands=1,
        fragile=False,
        fits_in="pocket",
    ),
    "ribbon": Item(
        id="ribbon",
        label="a blue ribbon",
        phrase="a blue ribbon for tying things neatly",
        type="ribbon",
        plural=False,
        hands=0,
        fragile=False,
        fits_in="pocket",
    ),
    "lantern": Item(
        id="lantern",
        label="a tiny lantern",
        phrase="a tiny lantern with a warm yellow glow",
        type="lantern",
        hands=1,
        fragile=True,
        fits_in="table",
    ),
}

NAMES = ["Mina", "Eli", "Nora", "Theo", "Lina", "Owen", "Ruby", "Jasper"]
PARENTS = [("mother", "Mom"), ("father", "Dad"), ("grandmother", "Grandma"), ("grandfather", "Grandpa")]
TRAITS = ["curious", "gentle", "patient", "thoughtful", "shy", "brave"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    item: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for aid, act in ACTIONS.items():
            if aid == "reed" and not place.near_water:
                continue
            for iid in ITEMS:
                if aid == "invent" and iid == "knife":
                    combos.append((pid, aid, iid))
                elif aid == "reed" and iid in {"knife", "ribbon"}:
                    combos.append((pid, aid, iid))
    return combos


def explain_rejection(place: Place, act: Activity, item: Item) -> str:
    if act.id == "reed" and not place.near_water:
        return "(No story: reeds grow near water, so this activity needs a place by the water.)"
    return "(No story: that combination does not support a believable misunderstanding and heartwarming fix.)"


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------

def _do_pick_reeds(world: World, child: Entity, item: Entity) -> None:
    child.meters["gathered"] = child.meters.get("gathered", 0) + 1
    child.meters["wet_hands"] = child.meters.get("wet_hands", 0) + 1
    item.meters["reeds"] = item.meters.get("reeds", 0) + 1
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    world.say(
        f"{child.id} bent by the water and picked the tall reeds with care. "
        f"Their fingers felt cool and green from the river air."
    )
    world.say(
        f"{child.pronoun().capitalize()} kept a small bundle tucked against {child.pronoun('possessive')} side, "
        f"already thinking about what {child.pronoun()} could make."
    )


def _do_invent(world: World, child: Entity, parent: Entity, item: Entity) -> None:
    child.meters["invention"] = child.meters.get("invention", 0) + 1
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    item.meters["cut_reeds"] = item.meters.get("cut_reeds", 0) + 1
    world.say(
        f"At home, {child.id} tied the reeds with {ITEMS['ribbon'].label} and slowly made a tiny flute."
    )
    world.say(
        f"It was not fancy, but the neat little tube could sing a soft whistle when blown just right."
    )


def _misunderstanding(world: World, child: Entity, parent: Entity, item: Entity) -> None:
    parent.memes["worry"] = parent.memes.get("worry", 0) + 1
    child.memes["misunderstanding"] = child.memes.get("misunderstanding", 0) + 1
    world.say(
        f"When {parent.id} saw the scattered reed pieces, {parent.pronoun()} looked startled."
    )
    world.say(
        f'"Oh, no," {parent.id} said softly. "Did you break the reeds just for fun?"'
    )


def _confess(world: World, child: Entity, parent: Entity, item: Entity) -> None:
    child.memes["confession"] = child.memes.get("confession", 0) + 1
    parent.memes["worry"] = max(0, parent.memes.get("worry", 0) - 1)
    parent.memes["understanding"] = parent.memes.get("understanding", 0) + 1
    world.say(
        f"{child.id} looked down at {child.pronoun('possessive')} hands and confessed the truth."
    )
    world.say(
        f'"I was not trying to be careless," {child.id} said. "I wanted to invent something kind and small."'
    )


def _heartwarming_twist(world: World, child: Entity, parent: Entity, item: Entity) -> None:
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    parent.memes["pride"] = parent.memes.get("pride", 0) + 1
    world.say(
        f"Then came the twist: the little flute made a bright, whispery note, and {parent.id} smiled."
    )
    world.say(
        f'"Why, you did invent something," {parent.id} said. "You turned a handful of reeds into music."'
    )
    world.say(
        f"They sat together by the warm light, listening to the soft reed song, "
        f"and the riverbank felt kinder than before."
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(place: Place, activity: Activity, item_cfg: Item, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    parent_label = dict(PARENTS)[parent_type] if parent_type in dict(PARENTS) else parent_type
    parent = world.add(Entity(id=parent_label, kind="character", type=parent_type, label=parent_label))
    item = world.add(Entity(id=item_cfg.id, type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase))

    world.say(
        f"{child.id} was a {trait} child who loved the riverbank and the tall, green reeds."
    )
    world.say(
        f"{child.pronoun().capitalize()} liked to invent little things from ordinary pieces of the world."
    )

    world.para()
    if activity.id == "reed":
        world.say(
            f"One day at {place.label}, {child.id} went looking for reeds while {parent.id} waited nearby."
        )
        _do_pick_reeds(world, child, item)
    else:
        world.say(
            f"One day, {child.id} stayed close to the worktable and tried to invent something with the reeds already gathered."
        )
        _do_invent(world, child, parent, item)

    world.para()
    if activity.id == "reed":
        _do_invent(world, child, parent, item)
    else:
        world.say(
            f"{parent.id} came closer and noticed the reed scraps and the careful tying."
        )
    _misunderstanding(world, child, parent, item)
    _confess(world, child, parent, item)
    _heartwarming_twist(world, child, parent, item)

    world.facts = {
        "child": child,
        "parent": parent,
        "item": item,
        "place": place,
        "activity": activity,
        "trait": trait,
        "parent_type": parent_type,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    act = f["activity"]
    place = f["place"]
    return [
        f'Write a heartwarming story for a child named {child.id} who loves to {act.verb} at {place.label}.',
        f"Tell a gentle story where a misunderstanding about reeds turns into a confession and a happy surprise.",
        f"Write a short story that includes the words reed, confess, and invent, and ends with a warm family moment.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    item = f["item"]
    act = f["activity"]
    place = f["place"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who was the child in the story?",
            answer=f"The child was {child.id}, a {trait} little {child.type}.",
        ),
        QAItem(
            question=f"What did {child.id} want to do with the reeds?",
            answer=f"{child.id} wanted to {act.verb}, because {child.pronoun()} liked inventing small things.",
        ),
        QAItem(
            question=f"Why did {parent.id} get worried?",
            answer=f"{parent.id} got worried because the scattered reed pieces looked like trouble at first.",
        ),
        QAItem(
            question=f"What did {child.id} confess?",
            answer=f"{child.id} confessed that the reeds were not ruined on purpose; they were part of a little invention.",
        ),
        QAItem(
            question=f"What was the twist at the end?",
            answer=f"The twist was that the reed pieces became a tiny flute, so the supposed mistake turned into music.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened at {place.label}, near the water and the reeds.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What are reeds?",
        answer="Reeds are tall, thin plants that grow in wet places near water.",
    ),
    QAItem(
        question="What does it mean to confess?",
        answer="To confess means to tell the truth about something, especially when you feel nervous or sorry.",
    ),
    QAItem(
        question="What does invent mean?",
        answer="To invent means to make up a new idea or create something new from what you have.",
    ),
    QAItem(
        question="Why can music feel comforting?",
        answer="Music can feel comforting because gentle sounds can help people relax and feel close to each other.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:9}) meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the place supports the chosen activity.
valid(P, A, I) :- place(P), activity(A), item(I), affords(P, A).

% Reed gathering only makes sense near water.
valid(P, reed, I) :- place(P), near_water(P), item(I), I = knife; I = ribbon.

% Inventing is also valid with either a knife or ribbon, because both can help
% make or tie a little reed craft.
valid(P, invent, I) :- place(P), activity(invent), item(I), I = knife; I = ribbon.

#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.near_water:
            lines.append(asp.fact("near_water", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("activity", aid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - ap:
        print("  only in python:", sorted(py - ap))
    if ap - py:
        print("  only in clingo:", sorted(ap - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming reed / confess / invent story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy", "mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--parent", choices=[p for p, _ in PARENTS])
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
    if args.place and args.activity and args.item:
        place = PLACES[args.place]
        act = ACTIONS[args.activity]
        item = ITEMS[args.item]
        if (args.place, args.activity, args.item) not in valid_combos():
            raise StoryError(explain_rejection(place, act, item))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, item = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice([p for p, _ in PARENTS])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, item=item, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ACTIONS[params.activity], ITEMS[params.item], params.name, params.gender, params.parent, params.trait)
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


CURATED = [
    StoryParams(place="riverbank", activity="reed", item="ribbon", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="pond", activity="reed", item="knife", name="Eli", gender="boy", parent="grandfather", trait="thoughtful"),
    StoryParams(place="garden", activity="invent", item="knife", name="Nora", gender="girl", parent="grandmother", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, item) combos:\n")
        for t in triples:
            print(" ", t)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
