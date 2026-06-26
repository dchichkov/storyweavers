#!/usr/bin/env python3
"""
A standalone storyworld for a tiny space-adventure tale set in a bedroom.

Premise:
- A child loves a homemade space toy powered by a hydrogen balloon.
- The toy cannot safely launch inside the bedroom.
- A gentle dialogue leads to surrendering the unsafe plan and learning a lesson.

The simulated state tracks:
- physical meters: excitement, wobble, floating, clutter, repair
- emotional memes: curiosity, worry, bravery, surrender, relief, lesson_learned

The story is generated from world state, not from a fixed paragraph template.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Typed entities
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


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class Room:
    place: str = "the bedroom"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    attempt: str
    risk: str
    mess: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    label: str
    phrase: str
    type: str
    plural: bool = False
    fragile: bool = False
    risk_tags: set[str] = field(default_factory=set)


ROOMS = {
    "bedroom": Room(place="the bedroom", indoor=True, affords={"launch"}),
}

ACTIVITIES = {
    "launch": Activity(
        id="launch",
        verb="launch the hydrogen balloon rocket",
        gerund="launching the hydrogen balloon rocket",
        attempt="try to launch the hydrogen balloon rocket",
        risk="the balloon could pop and the room could get messy",
        mess="wobble",
        keyword="hydrogen",
        tags={"space", "hydrogen", "balloon"},
    ),
}

ITEMS = {
    "rocket": Item(
        label="rocket",
        phrase="a shiny cardboard rocket",
        type="rocket",
        fragile=True,
        risk_tags={"launch"},
    ),
    "helmet": Item(
        label="helmet",
        phrase="a tiny silver helmet",
        type="helmet",
    ),
}

GEAR = {
    "bedroom_table": Item(
        label="clear bedside space",
        phrase="a clear bedside space",
        type="space",
    ),
}


@dataclass
class StoryParams:
    room: str
    activity: str
    item: str
    name: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def is_risky(activity: Activity, room: Room, item: Item) -> bool:
    return room.indoor and activity.id in item.risk_tags


def do_attempt(world: World, hero: Entity, activity: Activity, item: Entity, narrate: bool = True) -> None:
    hero.meters["excitement"] = hero.meters.get("excitement", 0.0) + 1.0
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    hero.meters["wobble"] = hero.meters.get("wobble", 0.0) + 1.0
    world.facts["attempted"] = True
    world.facts["risky"] = True
    if narrate:
        world.say(f"{hero.id} reached for {item.label} and started to {activity.verb}.")
    if narrate:
        world.say("The little room felt like a launch pad, but the ceiling looked very close.")


def predict(world: World, hero: Entity, activity: Activity, item: Entity) -> dict:
    sim = world.copy()
    do_attempt(sim, sim.get(hero.id), activity, sim.get(item.id), narrate=False)
    return {
        "wobble": sim.get(hero.id).meters.get("wobble", 0.0),
        "risk": True,
    }


def warning(world: World, parent: Entity, hero: Entity, activity: Activity, item: Entity) -> None:
    pred = predict(world, hero, activity, item)
    if pred["risk"]:
        world.facts["warning"] = True
        world.say(
            f'"Careful," {parent.id} said. "That {item.label} is for pretend space, not a real bedroom launch."'
        )


def dialogue(world: World, parent: Entity, hero: Entity, activity: Activity, item: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    world.say(f'"But it is hydrogen," {hero.id} said. "Won\'t it lift off if I just try harder?"')
    world.say(f'"It might lift," {parent.id} answered, "but the bedroom is too small for a safe lesson."')
    world.say(f'"So what should I do?" {hero.id} asked, still holding the rocket.')


def surrender_plan(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["surrender"] = hero.memes.get("surrender", 0.0) + 1.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    world.facts["surrendered"] = True
    world.say(f'{hero.id} took a slow breath and let the idea go.')
    world.say(f'"Okay," {hero.id} said. "I surrender the launch for now."')


def lesson_learned(world: World, hero: Entity, parent: Entity, activity: Activity, item: Entity) -> None:
    hero.memes["lesson_learned"] = hero.memes.get("lesson_learned", 0.0) + 1.0
    world.facts["lesson_learned"] = True
    world.say(
        f"{parent.id} smiled and moved the rocket to a clear shelf. "
        f'"A smart space explorer checks the room first," {parent.id} said.'
    )
    world.say(
        f"{hero.id} nodded. The hydrogen balloon stayed safe, and the rocket became a bedroom display instead of a crash."
    )


# ---------------------------------------------------------------------------
# Narrative assembly
# ---------------------------------------------------------------------------
def tell(room: Room, activity: Activity, item_cfg: Item, hero_name: str, parent_type: str) -> World:
    world = World(room)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy" if hero_name in {"Max", "Leo", "Finn"} else "girl"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    item = world.add(Entity(id="rocket", type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase, owner=hero.id, caretaker=parent.id))

    hero.meters["excitement"] = 1.0
    hero.memes["curiosity"] = 1.0
    world.say(f"{hero.id} loved space adventures, even in {room.place}.")
    world.say(f"{hero.id} had a {item.phrase} and a little hydrogen balloon that looked ready for the stars.")

    world.para()
    warning(world, parent, hero, activity, item)
    do_attempt(world, hero, activity, item)
    dialogue(world, parent, hero, activity, item)

    world.para()
    surrender_plan(world, hero, parent, activity)
    lesson_learned(world, hero, parent, activity, item)

    world.facts.update(hero=hero, parent=parent, item=item, activity=activity, room=room)
    return world


# ---------------------------------------------------------------------------
# Registries and validity
# ---------------------------------------------------------------------------
HERO_NAMES = ["Mia", "Leo", "Nora", "Ava", "Finn", "Zoe"]
PARENT_TYPES = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for rname, room in ROOMS.items():
        for aid, act in ACTIVITIES.items():
            for iname, item in ITEMS.items():
                if is_risky(act, room, item):
                    combos.append((rname, aid, iname))
    return combos


def explain_rejection(activity: Activity, room: Room, item: Item) -> str:
    return (
        f"(No story: {activity.keyword} belongs in a larger safe space, and "
        f"{item.label} is only interesting here if the bedroom launch could go wrong.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
risky(Room, Act, Item) :- indoor(Room), affords(Room, Act), risk_tag(Item, Act).

valid(Room, Act, Item) :- risky(Room, Act, Item).

#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        if room.indoor:
            lines.append(asp.fact("indoor", rid))
        for act in sorted(room.affords):
            lines.append(asp.fact("affords", rid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risk_tag", aid, act.id))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in sorted(item.risk_tags):
            lines.append(asp.fact("risk_tag", iid, tag))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


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
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a gentle space adventure about {hero.id} in {world.room.place} using the word "hydrogen".',
        f"Tell a short story where a child and parent talk out loud about a bedroom rocket and the child learns a lesson.",
        f"Write a child-friendly dialogue story that ends with surrendering an unsafe launch and keeping the rocket safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, item, act = f["hero"], f["parent"], f["item"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {item.label} in the bedroom?",
            answer=f"{hero.id} wanted to {act.verb}, because {hero.pronoun('subject')} was imagining a space adventure."
        ),
        QAItem(
            question=f"Why did {parent.id} tell {hero.id} to slow down?",
            answer="The parent warned that the bedroom was too small for a safe launch, so the plan needed to change."
        ),
        QAItem(
            question=f"What did {hero.id} do after the talk?",
            answer=f"{hero.id} surrendered the launch plan, listened, and learned to keep the hydrogen rocket safe."
        ),
        QAItem(
            question=f"How did the story end?",
            answer="The rocket stayed safe on a shelf, and the child learned that a good space explorer checks the room first."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is hydrogen?",
            answer="Hydrogen is a very light gas. It can help balloons float, but it must be used carefully."
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is something a character understands after an experience, and it helps them make a better choice next time."
        ),
        QAItem(
            question="What is a dialogue?",
            answer="A dialogue is a conversation where characters speak to each other."
        ),
        QAItem(
            question="Why should a toy rocket stay away from a tiny room?",
            answer="A toy rocket needs space to move safely, and a tiny room can make the play risky or messy."
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure bedroom storyworld.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    if args.activity and args.item:
        act = ACTIVITIES[args.activity]
        item = ITEMS[args.item]
        if not is_risky(act, ROOMS[args.room or "bedroom"], item):
            raise StoryError(explain_rejection(act, ROOMS[args.room or "bedroom"], item))
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.activity is None or c[1] == args.activity)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, activity, item = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(room=room, activity=activity, item=item, name=name, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(ROOMS[params.room], ACTIVITIES[params.activity], ITEMS[params.item], params.name, params.parent)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(room="bedroom", activity="launch", item="rocket", name="Mia", parent="mother"),
    StoryParams(room="bedroom", activity="launch", item="helmet", name="Leo", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
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
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.activity} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
