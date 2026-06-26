#!/usr/bin/env python3
"""
A campground ghost story world with motel stay, dialogue, conflict, and sharing.

Seed tale:
A family stays at a little motel beside a campground. At night, a shy ghost keeps
knocking on the wall and humming a lonely tune. The children get scared at first,
but then they discover the ghost is cold and wants someone to share a lantern and
listen. The family talks kindly, makes room at the fire, and the ghost becomes a
soft, helpful friend.

This script turns that premise into a small simulation:
- typed entities with meters and memes
- a state-driven conflict that can be soothed by sharing
- child-facing prose with an eerie but gentle tone
- an inline ASP twin for the reasonableness gate
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
    traits: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"cold": 0.0, "glow": 0.0, "fear": 0.0, "coziness": 0.0, "shared": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "curiosity": 0.0, "kindness": 0.0, "conflict": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = []
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    hero: str
    sibling: str
    parent: str
    seed: Optional[int] = None


HERO_NAMES = ["Mina", "Owen", "Tara", "Jude", "Lila", "Noah", "Piper", "Eli"]
SIBLING_NAMES = ["Sage", "Ivy", "Ben", "Maya", "Finn", "June", "Theo", "Rae"]
PARENT_TYPES = ["mother", "father"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Campground motel ghost story world.")
    ap.add_argument("--place", choices=["campground"])
    ap.add_argument("--hero")
    ap.add_argument("--sibling")
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


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "campground"),
        asp.fact("place_has", "campground", "motel"),
        asp.fact("place_has", "campground", "firepit"),
        asp.fact("entity", "ghost"),
        asp.fact("entity", "lantern"),
        asp.fact("entity", "blanket"),
        asp.fact("entity", "family"),
        asp.fact("feature", "dialogue"),
        asp.fact("feature", "conflict"),
        asp.fact("feature", "sharing"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
feature_story(dialogue).
feature_story(conflict).
feature_story(sharing).
valid_story(campground,motel,ghost_story) :- setting(campground), place_has(campground,motel).
valid_story(campground,motel,ghost_story) :- entity(ghost), entity(lantern), entity(blanket).
has_dialogue :- feature(dialogue).
has_conflict :- feature(conflict).
has_sharing :- feature(sharing).
reasonably_complete :- has_dialogue, has_conflict, has_sharing.
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _predict_conflict(world: World) -> bool:
    sim = world.copy()
    _night_haunt(sim, narrate=False)
    return sim.get("hero").memes["fear"] >= THRESHOLD and sim.get("ghost").memes["lonely"] >= THRESHOLD


def _night_haunt(world: World, narrate: bool = True) -> None:
    ghost = world.get("ghost")
    hero = world.get("hero")
    if ("haunt",) in world.fired:
        return
    world.fired.add(("haunt",))
    ghost.meters["cold"] += 1
    hero.memes["fear"] += 1
    ghost.memes["lonely"] += 1
    if narrate:
        world.say("At night, something tapped the motel wall three times, soft as knuckles in the dark.")
        world.say("The lantern on the picnic table shivered, and everyone listened.")


def _dialogue(world: World) -> None:
    hero = world.get("hero")
    sibling = world.get("sibling")
    parent = world.get("parent")
    ghost = world.get("ghost")
    if hero.memes["fear"] >= THRESHOLD and ("dialogue",) not in world.fired:
        world.fired.add(("dialogue",))
        world.say(f'"Did you hear that?" {hero.id} whispered.')
        world.say(f'"Yes," said {sibling.id}, pressing close to {parent.pronoun("possessive")} side.')
        world.say(f'"I am cold," came a tiny voice from the dark. "I only wanted someone to talk to."')
        ghost.memes["curiosity"] += 1


def _sharing(world: World) -> None:
    ghost = world.get("ghost")
    parent = world.get("parent")
    if ghost.meters["cold"] >= THRESHOLD and ("share",) not in world.fired:
        world.fired.add(("share",))
        ghost.meters["shared"] += 1
        ghost.meters["cold"] = 0.0
        ghost.memes["kindness"] += 1
        parent.meters["coziness"] += 1
        world.say(f"{parent.id} set out a blanket and moved the lantern closer so the ghost could warm up.")
        world.say("Everyone made room by the fire, and the ghost sat where the orange light could reach.")
        world.say("The lonely knocking stopped, because now the dark had company.")


def _resolve(world: World) -> None:
    hero = world.get("hero")
    sibling = world.get("sibling")
    ghost = world.get("ghost")
    if ghost.memes["kindness"] >= THRESHOLD and ("resolve",) not in world.fired:
        world.fired.add(("resolve",))
        hero.memes["fear"] = 0.0
        hero.memes["relief"] += 1
        sibling.memes["curiosity"] += 1
        world.say(f"{hero.id} stopped trembling first.")
        world.say(f'{hero.id} asked, "Do you want to share our marshmallows?"')
        world.say('The ghost smiled in a pale, moonlit way. "Yes, please," it said.')
        world.say("By the last glow of the lantern, the campground felt warm instead of strange.")


def _run(world: World) -> None:
    _night_haunt(world)
    _dialogue(world)
    _sharing(world)
    _resolve(world)


def tell(params: StoryParams) -> World:
    world = World(setting=params.place)
    hero = world.add(Entity(id="hero", kind="character", type="child", label=params.hero))
    sibling = world.add(Entity(id="sibling", kind="character", type="child", label=params.sibling))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the ghost"))
    lantern = world.add(Entity(id="lantern", kind="thing", type="lantern", label="lantern", owner="family"))
    blanket = world.add(Entity(id="blanket", kind="thing", type="blanket", label="blanket", owner="family"))

    world.say(f"{params.hero} and {params.sibling} stayed at a little motel near the campground with {params.parent} watching over them.")
    world.say("The little room smelled like pine trees and old wood, and the window showed the black shapes of the campsite.")
    world.say("A lantern waited on the table, and a folded blanket sat beside it.")
    world.say("That was when the wall began to knock.")

    _run(world)

    world.facts.update(
        hero=hero,
        sibling=sibling,
        parent=parent,
        ghost=ghost,
        lantern=lantern,
        blanket=blanket,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        'Write a child-friendly ghost story set at a campground motel, with dialogue, conflict, and sharing.',
        f"Tell a gentle spooky story about {p.hero}, {p.sibling}, and {p.parent} hearing a lonely ghost near a motel.",
        "Write a short story where scared children discover that a ghost only wanted warmth, talk, and a place to share.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Where did {p.hero} and {p.sibling} stay in the story?",
            answer=f"They stayed at a little motel near the campground, with {p.parent} there too.",
        ),
        QAItem(
            question="What did the ghost want at first?",
            answer="The ghost wanted someone to talk to and a warm place to sit by the lantern.",
        ),
        QAItem(
            question="How did the family help the ghost?",
            answer="They talked kindly, brought the lantern closer, shared a blanket, and made room by the fire.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The ghost became less lonely, the children felt brave, and the campground felt warm instead of scary.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a motel?",
            answer="A motel is a place where travelers can sleep near a road or campsite for one night or more.",
        ),
        QAItem(
            question="Why can a lantern help at a campground?",
            answer="A lantern gives a soft light that helps people see in the dark and feel less afraid.",
        ),
        QAItem(
            question="Why does sharing help when someone is lonely?",
            answer="Sharing makes room for another person and shows them they are welcome, which can help loneliness feel smaller.",
        ),
        QAItem(
            question="What makes a ghost story spooky but gentle?",
            answer="A gentle ghost story can use whispers, dark woods, and strange sounds, but still end with kindness and safety.",
        ),
    ]


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"  {e.id}: type={e.type} meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
    out.append(f"  fired={sorted(world.fired)}")
    return "\n".join(out)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_reasonable() -> bool:
    return True


def asp_verify() -> int:
    py = {("campground", "motel", "ghost_story")}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} story pattern).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    sibling = args.sibling or rng.choice([n for n in SIBLING_NAMES if n != hero])
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(place="campground", hero=hero, sibling=sibling, parent=parent, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="campground", hero="Mina", sibling="Sage", parent="mother"),
    StoryParams(place="campground", hero="Owen", sibling="Maya", parent="father"),
    StoryParams(place="campground", hero="Tara", sibling="Ben", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
            header = f"### {p.hero} at the campground motel"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
