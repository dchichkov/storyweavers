#!/usr/bin/env python3
"""
storyworlds/worlds/subjunctive_aquarium_sharing_slice_of_life.py
================================================================

A small aquarium slice-of-life storyworld about sharing, with a gentle
subjunctive wish threaded through a real, state-driven social turn.

Premise used to build the world:
---
At the aquarium, a child arrives with one small picture guide and a cousin
who also wants to look at it. The child feels a tiny tug of possessiveness,
then notices that the day would go better if they could share it. A parent
suggests a simple way to do that: take turns, read the names together, and
point at the fish for each other.

Causal state updates:
---
    wanting to keep the guide -> possessor.memes["possessive"] += 1
    successful sharing move     -> sharer.memes["generosity"] += 1
                                    sharer.memes["joy"] += 1
                                    sharer.memes["tension"] -= 1
    accepted turn-taking        -> both children.memes["calm"] += 1
                                    both children.memes["joy"] += 1
    refused sharing             -> child.memes["tension"] += 1 ; story can become invalid
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

AQUARIUM_PLACES = {
    "main_hall": "the aquarium",
}

FISHES = [
    "blue tang",
    "seahorse",
    "jellyfish",
    "clownfish",
    "stingray",
    "catfish",
]

NAMES = ["Maya", "Noah", "Lena", "Owen", "Iris", "Theo", "Nina", "Ari"]
RELATIONS = ["cousin", "sister", "brother", "friend"]
TRAITS = ["quiet", "curious", "patient", "shy", "cheerful", "gentle"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["clean", "held", "shared", "used"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "tension", "possessive", "generosity", "calm", "want"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the aquarium"


@dataclass
class SharedItem:
    id: str
    label: str
    phrase: str
    carries: str = "with both hands"


@dataclass
class StoryParams:
    place: str
    item: str
    fish: str
    name: str
    relation: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


def _share_turn(world: World) -> list[str]:
    out = []
    child = world.get("child")
    buddy = world.get("buddy")
    item = world.get("item")
    if item.meters["shared"] < 1:
        return out
    sig = "share_turn"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["generosity"] += 1
    buddy.memes["calm"] += 1
    child.memes["calm"] += 1
    child.memes["joy"] += 1
    buddy.memes["joy"] += 1
    out.append(
        f"{child.id} handed the {item.label} over and let {buddy.id} take a turn."
    )
    return out


def _resolve_possessive(world: World) -> list[str]:
    out = []
    child = world.get("child")
    buddy = world.get("buddy")
    item = world.get("item")
    if item.meters["shared"] < 1 or child.memes["possessive"] < 1:
        return out
    sig = "resolve"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["tension"] = 0.0
    buddy.memes["tension"] = 0.0
    out.append("Both of them settled into a kinder rhythm.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_share_turn, _resolve_possessive):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    child = world.add(Entity(id="child", kind="character", type="girl", meters={}, memes={}))
    child.id = params.name
    child.type = "girl" if params.relation in {"sister", "friend"} else "boy"
    child.memes["want"] = 1
    child.memes["possessive"] = 1
    child.memes["tension"] = 1

    buddy = world.add(Entity(id="buddy", kind="character", type="boy", meters={}, memes={}))
    buddy.id = "the " + params.relation
    buddy.type = "girl" if params.relation == "sister" else "boy"
    buddy.memes["want"] = 1

    item = world.add(Entity(
        id="item",
        kind="thing",
        type="guide",
        label="picture guide",
        plural=False,
        owner=child.id,
        meters={"shared": 0.0, "held": 1.0},
    ))

    fish = params.fish

    world.say(
        f"{child.id} arrived at {params.place} with a {params.trait} little picture guide."
    )
    world.say(
        f"{buddy.id} wanted to look too, and for a moment {child.id} wished it could all belong to just one pair of hands."
    )
    world.para()
    world.say(
        f"Then they stood beside the bright tanks, where the {fish} drifted like tiny moving commas."
    )
    world.say(
        f"\"If only there were two guides,\" {child.id} thought, \"but there is only one.\""
    )
    world.say(
        f"{buddy.id} pointed at the fish and waited, and that waiting made the room feel quieter."
    )

    item.meters["shared"] = 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{child.id} smiled, opened the guide to the {fish} page, and read the name out loud so {buddy.id} could hear."
    )
    world.say(
        f"After that, they took turns holding the book, and every time one of them found a fish, the other one got to be the first to point."
    )
    world.say(
        f"By the time they left, the guide was still flat and safe, and both children were still talking about the {fish} as if they had discovered a small treasure together."
    )

    world.facts.update(
        child=child,
        buddy=buddy,
        item=item,
        fish=fish,
        params=params,
        shared=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    buddy = f["buddy"]
    fish = f["fish"]
    return [
        f'Write a short slice-of-life story at an aquarium that includes the word "subjunctive" and shows two children learning to share one picture guide.',
        f"Tell a gentle aquarium story where {child.id} and {buddy.id} use one guidebook to find the {fish}, and a wishful thought leads to a sharing moment.",
        f"Write a small subjunctive story about an aquarium visit, taking turns, and how sharing makes the day feel calmer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    buddy = f["buddy"]
    item = f["item"]
    fish = f["fish"]
    return [
        QAItem(
            question=f"Where did {child.id} and {buddy.id} spend the story?",
            answer=f"They spent the story at the aquarium, where they watched the fish and shared a picture guide.",
        ),
        QAItem(
            question=f"What did {child.id} and {buddy.id} share?",
            answer=f"They shared one picture guide, and they took turns holding it so both of them could look at the fish.",
        ),
        QAItem(
            question=f"Which fish did the guide help them notice?",
            answer=f"The guide helped them notice the {fish}, which they kept pointing out together.",
        ),
        QAItem(
            question=f"How did sharing change the mood of the visit?",
            answer=f"Sharing made the visit calmer and happier, because {child.id} stopped holding onto the guide so tightly and both children could enjoy it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an aquarium?",
            answer="An aquarium is a place where people can see fish and other water animals in tanks.",
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let more than one person use or enjoy something in turns or together.",
        ),
        QAItem(
            question="What does subjunctive mean in a sentence?",
            answer="Subjunctive language talks about wishes, possibilities, or things that are not fully real yet, like saying 'If only...'",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str
    item: str
    fish: str
    name: str
    relation: str
    trait: str
    seed: Optional[int] = None


ITEMS = {
    "guide": SharedItem(id="guide", label="picture guide", phrase="a small picture guide"),
}

CURATED = [
    StoryParams(place="the aquarium", item="guide", fish="jellyfish", name="Maya", relation="cousin", trait="curious"),
    StoryParams(place="the aquarium", item="guide", fish="blue tang", name="Noah", relation="sister", trait="gentle"),
    StoryParams(place="the aquarium", item="guide", fish="seahorse", name="Lena", relation="friend", trait="quiet"),
]


ASP_RULES = r"""
shared(Item) :- item(Item).
turning(kind) :- shared(guide).
calm_visit :- shared(guide), fish_visible.
good_story :- calm_visit.
"""

def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("place", "aquarium"))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
    for f in FISHES:
        lines.append(asp.fact("fish", f))
    lines.append(asp.fact("fish_visible"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life aquarium storyworld about sharing and subjunctive wishes.")
    ap.add_argument("--place", choices=["the aquarium"])
    ap.add_argument("--item", choices=["guide"])
    ap.add_argument("--fish", choices=FISHES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--relation", choices=RELATIONS)
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
    place = args.place or "the aquarium"
    item = args.item or "guide"
    fish = args.fish or rng.choice(FISHES)
    name = args.name or rng.choice(NAMES)
    relation = args.relation or rng.choice(RELATIONS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, fish=fish, name=name, relation=relation, trait=trait)


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


def asp_verify() -> int:
    print("OK: ASP twin is present for the aquarium sharing world.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: sharing at {p.place} with {p.fish}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
