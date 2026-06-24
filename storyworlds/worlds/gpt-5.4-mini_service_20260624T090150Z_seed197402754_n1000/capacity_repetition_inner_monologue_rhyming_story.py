#!/usr/bin/env python3
"""
A small story world about filling containers to capacity.

The seed tale here is simple: a child wants to carry too many things, learns
about capacity, and finds a better way with a bigger basket or by splitting the
load. The prose leans rhythmic and repetitive, with a little inner monologue to
keep the choice feeling alive and child-facing.
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
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    capacity: int
    singular_name: str = "thing"


@dataclass
class ItemGroup:
    id: str
    label: str
    phrase: str
    count: int
    volume_each: int


@dataclass
class Setting:
    place: str
    backdrop: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_log: list[str] = []

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", backdrop="The table was bright and the floor was neat."),
    "garden": Setting(place="the garden", backdrop="The path was sunny and the basket leaned by the gate."),
    "playroom": Setting(place="the playroom", backdrop="The rug was soft and the shelf stood tall and straight."),
}

VESSELS = {
    "small_box": Vessel(id="small_box", label="small box", phrase="a small red box", capacity=3, singular_name="toy"),
    "tiny_basket": Vessel(id="tiny_basket", label="tiny basket", phrase="a tiny woven basket", capacity=4, singular_name="pebble"),
    "big_bag": Vessel(id="big_bag", label="big bag", phrase="a big blue bag", capacity=8, singular_name="thing"),
    "wide_bucket": Vessel(id="wide_bucket", label="wide bucket", phrase="a wide silver bucket", capacity=10, singular_name="thing"),
}

ITEMS = {
    "apples": ItemGroup(id="apples", label="apples", phrase="shiny apples", count=5, volume_each=1),
    "blocks": ItemGroup(id="blocks", label="blocks", phrase="wooden blocks", count=6, volume_each=1),
    "shells": ItemGroup(id="shells", label="shells", phrase="little shells", count=7, volume_each=1),
    "cookies": ItemGroup(id="cookies", label="cookies", phrase="sweet cookies", count=4, volume_each=2),
}

HERO_NAMES = ["Mia", "Nina", "Toby", "Finn", "Luna", "Theo", "Ivy", "Noah"]
TRAITS = ["curious", "cheerful", "brave", "gentle", "busy", "dreamy"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    vessel: str
    item_group: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def total_volume(group: ItemGroup) -> int:
    return group.count * group.volume_each


def can_fit(vessel: Vessel, group: ItemGroup) -> bool:
    return total_volume(group) <= vessel.capacity


def reasonableness_gate(vessel: Vessel, group: ItemGroup) -> bool:
    return can_fit(vessel, group)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A rhyming story world about capacity, repetition, and a small inner monologue."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--item-group", choices=ITEMS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.vessel and args.item_group:
        v = VESSELS[args.vessel]
        g = ITEMS[args.item_group]
        if not reasonableness_gate(v, g):
            raise StoryError(
                f"(No story: {g.phrase} need total capacity {total_volume(g)}, but {v.label} holds only {v.capacity}.)"
            )

    combos = []
    for place in SETTINGS:
        for vessel_id, vessel in VESSELS.items():
            for group_id, group in ITEMS.items():
                if not reasonableness_gate(vessel, group):
                    continue
                if args.place and place != args.place:
                    continue
                if args.vessel and vessel_id != args.vessel:
                    continue
                if args.item_group and group_id != args.item_group:
                    continue
                combos.append((place, vessel_id, group_id))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, vessel_id, group_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, vessel=vessel_id, item_group=group_id, name=name, trait=trait)


def rhyming_opening(hero: Entity, group: ItemGroup, vessel: Vessel, setting: Setting) -> list[str]:
    lines = [
        f"{hero.id} was a {hero.meters.get('age_word', 'little')} {hero.meters.get('role_word', hero.kind)} who liked to carry and count.",
        f"{hero.id} liked to lift {group.phrase}, one by one, in a jolly little amount.",
        f"At {setting.place}, with {setting.backdrop.lower()} nearby, {hero.id} saw {vessel.phrase} and gave a small sigh.",
    ]
    return lines


def generate_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    vessel: Vessel = f["vessel"]
    group: ItemGroup = f["group"]

    world.say(f"{hero.id} wanted to fill {vessel.phrase} just so,")
    world.say(f"one, then two, then three, in a tidy little row.")
    world.say(f"{hero.id} counted softly, with a hop and a hum,")
    world.say(f"\"I can do it, I can do it, watch the little {group.label} come.\"")

    world.para()
    world.say(
        f"One went in, then two went in, then three went in fine;"
    )
    world.say(
        f"but {hero.id} frowned at the last few and drew a thin line."
    )
    world.say(
        f"\"Can they all fit? Can they all sit?\" {hero.id} wondered with care."
    )
    world.say(
        f"\"If I push them too much, will they tumble and tear?\""
    )

    if can_fit(vessel, group):
        world.para()
        world.say(f"{hero.id} breathed in and smiled a bright smile.")
        world.say(f"\"Yes, they fit, yes, they fit, just stay in a while.\"")
        world.say(
            f"So in went the last ones, neat as a song, and {vessel.label} stayed steady all day long."
        )
        world.say(
            f"{hero.id} clapped and laughed, then set the lid right down;"
        )
        world.say(
            f"not a crumb, not a bump, not a wobble, not a frown."
        )
        f["outcome"] = "fit"
    else:
        world.para()
        world.say(f"{hero.id} heard a tiny thought whispering inside:")
        world.say(
            f"\"Too full, too full; don't make a spill-ride.\""
        )
        world.say(
            f"Then {hero.id} tried to press them in, but the pile would not stay."
        )
        world.say(
            f"One slipped to the side, and the plan slid away."
        )
        world.say(
            f"So {hero.id} took a breath, then a second breath too,"
        )
        world.say(
            f"and said, \"I need a bigger vessel, or fewer things will do.\""
        )
        world.say(
            f"{hero.id} split the load with a careful new plan:"
        )
        world.say(
            f"some in {vessel.phrase}, and some in a second little span."
        )
        world.say(
            f"At last the room was calm, and the counting was sweet;"
        )
        world.say(
            f"the load fit with room to spare, and the day felt complete."
        )
        f["outcome"] = "split"

    if f["outcome"] == "fit":
        world.say(f"{hero.id} smiled at the sight, all snug and all neat,")
        world.say(f"for things that fit well make a good little beat.")
    else:
        world.say(f"{hero.id} smiled at the sight, with a plan that was wise,")
        world.say(f"for knowing a limit can make a big prize.")

    hero.memes["calm"] = 1.0
    hero.memes["pride"] = 1.0 if f["outcome"] == "fit" else 0.8


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", label=params.name))
    hero.meters["age_word"] = "little"
    hero.meters["role_word"] = "child"
    vessel = VESSELS[params.vessel]
    group = ITEMS[params.item_group]
    world.facts.update(hero=hero, vessel=vessel, group=group, params=params)

    world.say(f"{hero.id} was a {params.trait} child with a counting tune.")
    world.say(f"{hero.id} liked to handle things with rhythm and swoon.")
    world.say(f"{hero.id} saw {group.phrase} and a {vessel.phrase} nearby,")
    world.say(f"and wondered, \"Will they fit?\" with a spark in the eye.")

    world.para()
    generate_story(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.
fits(V,G) :- vessel(V,C), group(G,N,W), C >= N*W.
valid(P,V,G) :- place(P), vessel(V,_), group(G,_,_), fits(V,G).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for vid, v in VESSELS.items():
        lines.append(asp.fact("vessel", vid, v.capacity))
    for gid, g in ITEMS.items():
        lines.append(asp.fact("group", gid, g.count, g.volume_each))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, v, g) for p in SETTINGS for v, vessel in VESSELS.items() for g, group in ITEMS.items() if reasonableness_gate(vessel, group)}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    hero, vessel, group = f["hero"], f["vessel"], f["group"]
    return [
        f'Write a short rhyming story about a child named {hero.id} and the idea of capacity.',
        f"Tell a gentle story where {hero.id} wants to carry {group.phrase} in {vessel.phrase} but must think about space.",
        f"Write a child-friendly story that repeats a counting pattern and ends with a wise choice about {vessel.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, vessel, group = f["hero"], f["vessel"], f["group"]
    outcome = f["outcome"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do with {group.phrase} and {vessel.phrase}?",
            answer=f"{hero.id} wanted to fill {vessel.phrase} with {group.phrase} and carry them along.",
        ),
        QAItem(
            question=f"Why did {hero.id} pause and think about capacity?",
            answer=f"{hero.id} paused because the {group.label} needed more room than {vessel.label} could give, and the load had to fit safely.",
        ),
    ]
    if outcome == "fit":
        qa.append(QAItem(
            question=f"How did the story end for {hero.id} and the {vessel.label}?",
            answer=f"The last {group.label} fit neatly, and {hero.id} ended the day smiling because everything stayed snug and tidy.",
        ))
    else:
        qa.append(QAItem(
            question=f"What did {hero.id} do when the {vessel.label} was too small?",
            answer=f"{hero.id} split the load into two parts and chose a better plan so nothing spilled or got crowded.",
        ))
    return qa


WORLD_KNOWLEDGE = {
    "capacity": [
        QAItem(
            question="What does capacity mean?",
            answer="Capacity means how much something can hold, like water in a cup or toys in a box.",
        ),
    ],
    "counting": [
        QAItem(
            question="Why do children count things?",
            answer="Children count things to keep track of how many there are and to see if everything fits.",
        ),
    ],
    "container": [
        QAItem(
            question="What is a container?",
            answer="A container is something that holds other things, such as a basket, box, bag, or bucket.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE["capacity"] + WORLD_KNOWLEDGE["counting"] + WORLD_KNOWLEDGE["container"]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} meters={e.meters} memes={e.memes}")
    lines.append(f"facts: {world.facts.get('outcome', '')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
    StoryParams(place="kitchen", vessel="small_box", item_group="blocks", name="Mia", trait="curious"),
    StoryParams(place="garden", vessel="tiny_basket", item_group="apples", name="Theo", trait="cheerful"),
    StoryParams(place="playroom", vessel="big_bag", item_group="shells", name="Luna", trait="dreamy"),
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
        print(f"{len(triples)} valid combos:")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.item_group} in {p.vessel} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
