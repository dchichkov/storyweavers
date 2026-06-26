#!/usr/bin/env python3
"""
storyworlds/worlds/huge_movement_silo_grocery_store_moral_value.py
===================================================================

A small folk-tale storyworld set in a grocery store, where a huge movement of
goods, a silo-like grain bin, friendship, conflict, and a moral choice shape a
complete little story.

The seed image is simple:
- a grocery store with a grain silo/bin for scooping dry food
- a huge movement of crates and carts through the aisles
- a friendship strained by conflict
- a moral value: sharing work, telling the truth, and helping a friend

The world simulates a few physical and emotional state changes so the prose is
driven by events rather than template swapping.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    moved_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the grocery store"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_bump(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character" or actor.meters.get("movement", 0) < THRESHOLD:
            continue
        carrier = world.facts.get("carrier")
        if not carrier:
            continue
        if actor.id == carrier.id:
            continue
        if actor.location != carrier.location:
            continue
        sig = ("bump", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["anger"] = actor.memes.get("anger", 0) + 1
        out.append(f"People began to grumble as the carts crowded the aisle.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    c1 = world.facts.get("friend_a")
    c2 = world.facts.get("friend_b")
    if not c1 or not c2:
        return out
    if c1.memes.get("anger", 0) < THRESHOLD:
        return out
    sig = ("conflict", c1.id, c2.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    c1.memes["conflict"] = c1.memes.get("conflict", 0) + 1
    c2.memes["conflict"] = c2.memes.get("conflict", 0) + 1
    out.append("__conflict__")
    return out


CAUSAL_RULES = [_r_bump, _r_conflict]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)


def show_qa_item(q: QAItem) -> str:
    return f"Q: {q.question}\nA: {q.answer}"


@dataclass
class StoryParams:
    name_a: str
    name_b: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "grocery": Setting(place="the grocery store", affords={"movement"}),
}

ACTIVITIES = {
    "movement": Activity(
        id="movement",
        verb="move the heavy carts",
        gerund="moving the heavy carts",
        rush="rush the carts through the aisle",
        mess="crowded",
        zone="aisle",
        keyword="movement",
        tags={"movement", "conflict"},
    ),
}

PRIZES = {
    "silo": Prize(
        label="silo bin",
        phrase="the tall grain silo bin",
        type="silo",
        location="back wall",
    ),
}

NAMES = ["Mina", "Jory", "Lena", "Tomas", "Nell", "Ravi", "Iris", "Bram"]
HELPERS = ["the clerk", "the baker", "the porter"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("grocery", "movement", "silo")]


def explain_rejection() -> str:
    return "(No story: this world only tells the grocery-store tale of movement around the silo bin.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale grocery store storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--helper", choices=HELPERS)
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
    if any([args.place, args.activity, args.prize]) and not (
        args.place in (None, "grocery")
        and args.activity in (None, "movement")
        and args.prize in (None, "silo")
    ):
        raise StoryError(explain_rejection())
    return StoryParams(
        name_a=args.name_a or rng.choice(NAMES),
        name_b=args.name_b or rng.choice([n for n in NAMES if n != (args.name_a or "")]),
        helper=args.helper or rng.choice(HELPERS),
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS["grocery"])
    a = world.add(Entity(id=params.name_a, kind="character", type="girl", location="aisle"))
    b = world.add(Entity(id=params.name_b, kind="character", type="boy", location="aisle"))
    helper = world.add(Entity(id="helper", kind="character", type="woman", label=params.helper, location="aisle"))
    silo = world.add(Entity(id="silo", type="silo", label="grain silo bin", phrase="a tall silo bin of oats", location="back wall"))
    cart = world.add(Entity(id="cart", type="cart", label="cart", location="aisle"))

    world.facts.update(friend_a=a, friend_b=b, helper=helper, silo=silo, cart=cart)

    world.say(f"Once, in {world.setting.place}, {a.id} and {b.id} were the best of friends.")
    world.say(f"They loved {ACTIVITIES['movement'].gerund}, because the day always felt lively when they worked together.")
    world.say(f"Near the back wall stood a tall grain silo bin, where the store kept oats and other dry goods.")

    world.para()
    a.meters["movement"] = 1
    b.meters["movement"] = 1
    cart.meters["movement"] = 1
    world.say(f"One day, a huge movement of carts and boxes began to roll through the store.")
    world.say(f"{a.id} and {b.id} tried to {ACTIVITIES['movement'].rush}, and the aisle grew narrow and noisy.")
    propagate(world, narrate=True)

    world.para()
    a.memes["want"] = 1
    b.memes["want"] = 1
    world.say(f"{a.id} wanted to be first beside the silo bin, but {b.id} wanted to help the helper instead.")
    world.say(f"At that, their voices rose, and their friendship cracked like a dropped biscuit.")
    a.memes["anger"] = 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"Then {params.helper} spoke kindly and pointed to the crowded aisle.")
    world.say(f'"A good hand can calm a big storm," said {params.helper}, "and friends grow stronger when they share the work."')
    a.memes["guilt"] = 1
    b.memes["guilt"] = 1
    a.memes["anger"] = 0
    b.memes["anger"] = 0
    a.memes["friendship"] = 1
    b.memes["friendship"] = 1
    world.say(f"{a.id} and {b.id} remembered the moral of the day: a kind act is worth more than pride.")
    world.say(f"They apologized, steadied the carts together, and made a lane to the silo bin for everyone.")
    world.say(f"By evening, the store was calm again, and the two friends walked home side by side.")

    world.facts.update(resolved=True, moral="kindness and sharing work mend conflict")
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short folk tale set in a grocery store about a huge movement of carts and a silo bin of grain.",
        "Tell a gentle story where two friends quarrel in a grocery store, then learn a moral lesson and make peace.",
        "Write a simple friendship story with conflict, a helper, and a wise choice near a silo in a grocery store.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["friend_a"]
    b = world.facts["friend_b"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"Who were the two friends in the grocery store tale?",
            answer=f"The two friends were {a.id} and {b.id}. They started the story happy, then argued, and later made peace.",
        ),
        QAItem(
            question=f"What caused the conflict in the store?",
            answer=f"The conflict began when a huge movement of carts and boxes crowded the aisle, and {a.id} and {b.id} both wanted to be first.",
        ),
        QAItem(
            question=f"Who helped the children remember the right thing to do?",
            answer=f"{helper.label} helped them by speaking kindly and reminding them that friends grow stronger when they share the work.",
        ),
        QAItem(
            question="What was the moral value of the story?",
            answer="The moral was that kindness, sharing work, and apologizing can mend friendship after conflict.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a grocery store?",
            answer="A grocery store is a shop where people buy food and other things they need for home.",
        ),
        QAItem(
            question="What is a silo used for?",
            answer="A silo or grain bin is used to store dry food like oats or grain so it stays ready to scoop or measure.",
        ),
        QAItem(
            question="Why can crowded aisles cause trouble?",
            answer="Crowded aisles can cause trouble because people and carts may bump into each other and make it hard to move safely.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(grocery).
activity(movement).
prize(silo).
affords(grocery,movement).

valid(grocery,movement,silo).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", "grocery"),
        asp.fact("activity", "movement"),
        asp.fact("prize", "silo"),
        asp.fact("affords", "grocery", "movement"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"[Prompt {i}] {p}")
        for q in sample.story_qa:
            print()
            print(show_qa_item(q))
        for q in sample.world_qa:
            print()
            print(show_qa_item(q))


CURATED = [
    StoryParams(name_a="Mina", name_b="Jory", helper="the clerk"),
    StoryParams(name_a="Lena", name_b="Tomas", helper="the porter"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
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
        while len(samples) < args.n and i < max(50, args.n * 20):
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
