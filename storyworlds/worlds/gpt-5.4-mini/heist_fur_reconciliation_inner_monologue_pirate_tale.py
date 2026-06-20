#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/heist_fur_reconciliation_inner_monologue_pirate_tale.py
======================================================================================

A small standalone storyworld for a pirate-tale-style reconciliation story.

Premise:
- A child pirate plans a tiny heist to "borrow" a fur coat that makes the cabin
  feel cozy and grand.
- The heist goes wrong because someone is worried, hurt, or embarrassed.
- The main turn happens through an inner monologue that reveals the real feeling.
- The ending is reconciliation: an apology, a returned or shared item, and a
  warm pirate-style closing image.

This world keeps the story grounded in state:
- physical meters track missing / hidden / worn / returned / cozy
- emotional memes track want / fear / guilt / hurt / forgiveness / warmth

It also includes:
- StoryParams
- build_parser, resolve_params, generate, emit, main
- valid_combos and an inline ASP twin
- --verify with a smoke test
- --qa, --json, --trace, --all, --seed, --asp, --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    scene: str
    ship: str
    dark_spot: str
    ending_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    wear: str
    cozy: str = "cozy"
    soft: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Crew:
    id: str
    child: str
    sibling: str
    parent: str
    child_gender: str
    sibling_gender: str
    parent_gender: str
    child_age: int
    sibling_age: int
    relation: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    place: str
    prize: str
    crew: str
    name1: str
    name2: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for e in list(world.entities.values()):
            if e.meters["missing"] >= THRESHOLD and ("missing", e.id) not in world.fired:
                world.fired.add(("missing", e.id))
                if "holder" in world.entities:
                    world.get("holder").memes["worry"] += 1
                changed = True
            if e.meters["returned"] >= THRESHOLD and ("returned", e.id) not in world.fired:
                world.fired.add(("returned", e.id))
                if "holder" in world.entities:
                    world.get("holder").memes["relief"] += 1
                changed = True
            if e.meters["cozy"] >= THRESHOLD and ("cozy", e.id) not in world.fired:
                world.fired.add(("cozy", e.id))
                if "child" in world.entities:
                    world.get("child").memes["warmth"] += 1
                changed = True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for prize_id, prize in PRIZES.items():
            for crew_id, crew in CREWS.items():
                if prize.soft and place_id in {"cove", "deck", "harbor", "cabin"}:
                    combos.append((place_id, prize_id, crew_id))
    return combos


def inner_voice(world: World, child: Entity, sibling: Entity, prize: Entity) -> None:
    world.say(
        f"{child.id} watched the {prize.label} sway on the hook and thought, "
        f"maybe a tiny heist would be clever. "
        f"{child.pronoun().capitalize()} told {child.pronoun('object')} self that a pirate could borrow one little thing."
    )
    child.memes["want"] += 1
    child.memes["bravado"] += 1


def take(world: World, child: Entity, sibling: Entity, prize: Entity) -> None:
    prize.meters["missing"] += 1
    child.meters["hidden"] += 1
    propagate(world)
    world.say(
        f"On the moonlit deck, {child.id} tiptoed through the captain's chest and "
        f"slipped the {prize.label} away."
    )


def confrontation(world: World, child: Entity, sibling: Entity, prize: Entity) -> None:
    sibling.memes["hurt"] += 1
    world.say(
        f"But {sibling.id} saw the empty hook and frowned. "
        f'"That was mine," {sibling.id} said, and the salt wind felt suddenly very cold.'
    )
    world.say(
        f"{child.id} froze. {child.pronoun('possessive').capitalize()} chest felt tight, and the heist no longer felt brave."
    )


def reconcile(world: World, child: Entity, sibling: Entity, prize: Entity, parent: Entity) -> None:
    child.memes["guilt"] += 1
    child.memes["fear"] += 1
    world.say(
        f"In {child.id}'s head, one thought kept circling like a gull: "
        f"I wanted the fur because it looked soft and grand, but I hurt {sibling.id}. "
        f"I can give it back. I can say sorry."
    )
    prize.meters["returned"] += 1
    child.meters["hidden"] = 0
    sibling.meters["worn"] += 1
    world.say(
        f"{child.id} held out the {prize.label}. \"I was wrong,\" "
        f"{child.id} said quietly. \"I should have asked.\""
    )
    sibling.memes["forgiveness"] += 1
    sibling.memes["warmth"] += 1
    world.say(
        f"{sibling.id} blinked, then nodded. \"You can ask next time,\" "
        f"{sibling.id} said. \"And you can share this one now.\""
    )
    world.say(
        f"{parent.label_word.capitalize()} came by with a grin, wrapped both children in a blanket of calm, and said the best pirate loot was a mended friendship."
    )
    child.meters["cozy"] += 1
    sibling.meters["cozy"] += 1
    parent.memes["pride"] += 1
    propagate(world)


def tell(place: Place, prize: Prize, crew: Crew, name1: str, name2: str) -> World:
    world = World()
    child = world.add(Entity(id=name1, kind="character", type=crew.child_gender, role="child"))
    sibling = world.add(Entity(id=name2, kind="character", type=crew.sibling_gender, role="sibling"))
    parent = world.add(Entity(id=crew.parent, kind="character", type=crew.parent_gender, role="parent", label="the parent"))
    hook = world.add(Entity(id="hook", label=prize.label, owner=sibling.id))
    world.facts.update(place=place, prize=prize, crew=crew, child=child, sibling=sibling, parent=parent, hook=hook)

    world.say(
        f"On {place.scene}, {child.id} and {sibling.id} turned the old cabin into a pirate ship. "
        f"{place.ship}"
    )
    world.say(
        f"{sibling.id} wore {sibling.pronoun('possessive')} {prize.phrase}, and it looked warm against the sea air."
    )
    world.para()
    inner_voice(world, child, sibling, hook)
    take(world, child, sibling, hook)
    world.para()
    confrontation(world, child, sibling, hook)
    world.para()
    reconcile(world, child, sibling, hook, parent)
    world.say(
        f"At the end, {place.ending_image}, and the two little pirates sailed on with softer hearts and a shared laugh."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    prize: Prize = f["prize"]
    crew: Crew = f["crew"]
    child: Entity = f["child"]
    sibling: Entity = f["sibling"]
    return [
        f'Write a pirate tale for a young child that includes the words "heist" and "{prize.label}" and ends in reconciliation.',
        f"Tell a short story about {child.id} and {sibling.id} on a pirate ship where one child makes a tiny heist, feels guilty, and gives back the fur.",
        f"Write a warm pirate story set on {place.scene} with an inner monologue that shows why a child apologizes and fixes a mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    sibling: Entity = f["sibling"]
    prize: Prize = f["prize"]
    parent: Entity = f["parent"]
    return [
        QAItem(
            question="What did the child want to do?",
            answer=f"{child.id} wanted to make a tiny heist and borrow the {prize.label} because it looked soft and grand. But that choice hurt {sibling.id}, so the story turned toward apology and repair.",
        ),
        QAItem(
            question="What did the child think about after the mistake?",
            answer=f"{child.id} thought about how the fur had not been theirs to take. In the inner monologue, {child.id} realized that giving it back and saying sorry would be braver than pretending nothing happened.",
        ),
        QAItem(
            question="How did the siblings fix things?",
            answer=f"{child.id} returned the {prize.label} and said sorry, and {sibling.id} forgave them. {parent.label_word.capitalize()} helped them settle down, and the fight ended with shared warmth instead of anger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a heist?",
            answer="A heist is a sneaky taking of something, often planned in secret. In a kid story it should be small, harmless, and followed by a mistake being fixed.",
        ),
        QAItem(
            question="What does fur feel like?",
            answer="Fur is usually soft and warm to the touch. That is why a child might stare at it and imagine cozy pirate treasure.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace after a hurt. People apologize, forgive each other, and the relationship feels warm again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


PLACES = {
    "cabin": Place("cabin", "a creaky pirate cabin", "The lanterns glowed low and the maps fluttered on the walls.", "the fur coat hanging by the berth", "the lantern shone on two children who were smiling again"),
    "deck": Place("deck", "the moonlit deck", "The ropes hummed, the mast creaked, and the moon made silver paths on the boards.", "the fur hood resting on a peg", "the deck felt bright with a gentler kind of treasure"),
    "harbor": Place("harbor", "a sleepy harbor dock", "The water lapped softly, and the little ship rocked like a cradle.", "the fur wrap folded on a crate", "the harbor looked warm as the family waved together"),
    "cove": Place("cove", "a hidden cove", "The waves whispered at the rocks, and the cave mouth looked like a secret entrance.", "the fur cape draped over a chest", "the cove was calm, with friendship shining brighter than loot"),
}

PRIZES = {
    "fur": Prize("fur", "fur coat", "a soft fur coat", "coat"),
    "fur_wrap": Prize("fur_wrap", "fur wrap", "a soft fur wrap", "wrap"),
    "fur_cape": Prize("fur_cape", "fur cape", "a fluffy fur cape", "cape"),
}

CREWS = {
    "siblings": Crew("siblings", "boy", "girl", "mother", "boy", "girl", "mother", 6, 8, "siblings"),
    "mates": Crew("mates", "girl", "boy", "father", "girl", "boy", "father", 7, 7, "friends"),
}


def explain_rejection() -> str:
    return "(No story: this tiny pirate tale needs a soft fur item and a place where it can be worn or borrowed.)"


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("soft", pid))
    for cid in CREWS:
        lines.append(asp.fact("crew", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, R, C) :- place(P), prize(R), crew(C), soft(R).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python combos.")
        print("only python:", sorted(py - clingo))
        print("only asp:", sorted(clingo - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale reconciliation storyworld with a heist and inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--crew", choices=CREWS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.prize is None or c[1] == args.prize)
              and (args.crew is None or c[2] == args.crew)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, prize, crew = rng.choice(sorted(combos))
    n1 = args.name1 or rng.choice(["Mara", "Pip", "Tess", "Nico", "Jules"])
    n2 = args.name2 or rng.choice([n for n in ["Mara", "Pip", "Tess", "Nico", "Jules", "Robin"] if n != n1])
    return StoryParams(place=place, prize=prize, crew=crew, name1=n1, name2=n2)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PRIZES[params.prize], CREWS[params.crew], params.name1, params.name2)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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
    StoryParams("cabin", "fur", "siblings", "Mara", "Pip"),
    StoryParams("deck", "fur_wrap", "mates", "Tess", "Nico"),
    StoryParams("cove", "fur_cape", "siblings", "Jules", "Robin"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            i += 1
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
