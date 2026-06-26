#!/usr/bin/env python3
"""
A small whodunit-style story world about a needed bag, a cautious warning, and
a kind reveal.

The premise:
- Someone needs a specific bag for a small task or outing.
- The bag goes missing or is used without permission.
- A cautious character notices clues and warns others before the situation
  becomes worse.
- A kind character tells the truth, returns the bag, and helps repair trust.

The world model tracks:
- physical meters: possession, hiddenness, readiness, tidiness
- emotional memes: worry, kindness, suspicion, relief

This script generates child-facing stories with a mystery-like turn and a
gentle ending image.
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
# Core world entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden_in: str = ""
    carried_by: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt", "sister"}
        male = {"boy", "father", "dad", "man", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool = True
    clues: list[str] = field(default_factory=list)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    useful_for: str
    hidden_spot: str
    needed_for: str
    cautious_about: str


@dataclass
class StoryParams:
    place: str
    need_item: str
    bag_item: str
    hero_name: str
    hero_type: str
    cautious_name: str
    cautious_type: str
    kind_name: str
    kind_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "hall": Place(name="the hall", indoor=True, clues=["mud on the rug", "a soft thump", "an open closet"]),
    "kitchen": Place(name="the kitchen", indoor=True, clues=["a chair left out", "crumbs by the table", "a drawer not shut"]),
    "classroom": Place(name="the classroom", indoor=True, clues=["a shelf of hooks", "small shoes near the mat", "paper scraps"]),
    "garden_shed": Place(name="the garden shed", indoor=False, clues=["a dusty shelf", "a watering can", "a little path of footprints"]),
}

ITEMS = {
    "snack": Item(
        id="snack",
        label="snack bag",
        phrase="a small snack bag",
        useful_for="a walk",
        hidden_spot="behind the blue stool",
        needed_for="a walk",
        cautious_about="food getting forgotten",
    ),
    "library": Item(
        id="library",
        label="library bag",
        phrase="a plain library bag",
        useful_for="a trip to the library",
        hidden_spot="inside the coat closet",
        needed_for="a trip to the library",
        cautious_about="books getting bent",
    ),
    "toy": Item(
        id="toy",
        label="toy bag",
        phrase="a bright toy bag",
        useful_for="a playdate",
        hidden_spot="under the bench",
        needed_for="a playdate",
        cautious_about="small toys getting lost",
    ),
    "picnic": Item(
        id="picnic",
        label="picnic bag",
        phrase="a neat picnic bag",
        useful_for="a picnic",
        hidden_spot="behind the tall chair",
        needed_for="a picnic",
        cautious_about="sandwiches getting squashed",
    ),
}

HERO_NAMES = ["Mina", "Toby", "Lina", "Jasper", "Pia", "Noel", "Sage", "Ivy"]
CAUTIOUS_NAMES = ["June", "Mara", "Evan", "Nia", "Owen", "Milo", "Rosa", "Theo"]
KIND_NAMES = ["Ari", "Bea", "Cora", "Dylan", "Elsa", "Finn", "Luca", "Maya"]
KINDS = ["girl", "boy"]
TRAITS = ["careful", "gentle", "curious", "quiet", "steady", "brave"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters.get("need_missed", 0) < 1:
        return out
    sig = ("worry", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    out.append(f"{hero.id} felt worry rise like a tiny knot in a pocket.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    bag = world.get("bag")
    if bag.carried_by != "hero" or bag.hidden_in:
        return out
    sig = ("relief", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    out.append(f"The missing bag was safe again, and the room felt easier to breathe in.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    kind = world.get("kind")
    hero = world.get("hero")
    bag = world.get("bag")
    if bag.carried_by != "kind":
        return out
    sig = ("kindness", kind.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kind.memes["kindness"] = kind.memes.get("kindness", 0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    out.append(f"{kind.id} came forward kindly and handed the bag back.")
    return out


CAUSAL_RULES = [_r_worry, _r_kindness, _r_relief]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    world.say(s)


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
def describe_place(place: Place) -> str:
    return {
        "the hall": "The hall was quiet, with shoes lined up near the wall.",
        "the kitchen": "The kitchen smelled like toast, and every shelf looked busy.",
        "the classroom": "The classroom was neat, with hooks waiting by the wall.",
        "the garden shed": "The garden shed was dusty, with sunlight slipping through a crack.",
    }.get(place.name, f"{place.name.capitalize()} waited in its own still way.")


def introduce(world: World) -> None:
    hero = world.get("hero")
    cautious = world.get("cautious")
    kind = world.get("kind")
    bag = world.get("bag")
    world.say(
        f"{hero.id} was a {world.facts['hero_trait']} {hero.type} who needed {bag.phrase} for {world.facts['need_phrase']}."
    )
    world.say(
        f"{cautious.id} was the sort of {cautious.type} who noticed small things, and {kind.id} was kind enough to help when something went wrong."
    )
    world.say(describe_place(world.place))


def setup_mystery(world: World) -> None:
    hero = world.get("hero")
    bag = world.get("bag")
    hero.meters["need"] = 1
    bag.meters["present"] = 1
    bag.meters["hidden"] = 1
    bag.hidden_in = world.facts["hidden_spot"]
    world.say(
        f"One day, {hero.id} looked for {bag.label}, but it was not where it should have been."
    )
    world.say(
        f"That meant {hero.id} still needed it, and the empty spot felt strangely suspicious."
    )
    hero.meters["need_missed"] = 1


def caution(world: World) -> None:
    cautious = world.get("cautious")
    bag = world.get("bag")
    world.say(
        f"{cautious.id} frowned and said, 'We should be careful and follow the clues before we guess.'"
    )
    world.say(
        f"{cautious.id} noticed {world.place.clues[0]}, then pointed to {world.place.clues[1]}."
    )
    world.say(
        f"That cautious warning kept everyone from making a wild accusation."
    )
    world.facts["caution_used"] = True


def suspect_tension(world: World) -> None:
    hero = world.get("hero")
    world.say(
        f"{hero.id} felt a little suspicious, because the bag had vanished right before it was needed."
    )
    world.say(
        f"Still, {hero.id} listened, because the careful clue-finding looked kinder than blaming someone at once."
    )
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0) + 1


def reveal(world: World) -> None:
    kind = world.get("kind")
    bag = world.get("bag")
    hero = world.get("hero")
    world.say(
        f"At last, {kind.id} stepped forward with a blush and said the truth: the bag had been moved to {bag.hidden_in} by mistake."
    )
    bag.carried_by = kind.id
    bag.hidden_in = ""
    world.say(
        f"{kind.id} was sorry, but kind too, because {kind.id} had been saving the bag so it would not get dirty."
    )
    propagate(world)


def resolve(world: World) -> None:
    hero = world.get("hero")
    kind = world.get("kind")
    bag = world.get("bag")
    bag.carried_by = "hero"
    world.say(
        f"{kind.id} handed {bag.it()} back, and {hero.id} held the bag close like a found treasure."
    )
    world.say(
        f"{hero.id} thanked {kind.id} for telling the truth, and the careful warning turned into relief instead of trouble."
    )
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.meters["need_missed"] = 0
    bag.meters["present"] = 1
    bag.meters["hidden"] = 0
    bag.hidden_in = ""
    world.say(
        f"In the end, the needed bag was ready again, and the room felt calm and safe."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
need_missed(H) :- needs(H, B), missing(B).
cautionary(H) :- cautious(H).
kind_act(K) :- kind(K), returns(K, B).
resolved(H) :- need_missed(H), kind_act(_), returned(B), owns(H, B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("bag", iid))
        lines.append(asp.fact("needs_for", iid, item.needed_for))
        lines.append(asp.fact("hidden_spot", iid, item.hidden_spot))
    lines.append(asp.fact("cautious", "cautious"))
    lines.append(asp.fact("kind", "kind"))
    lines.append(asp.fact("hero", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show need_missed/1."))
    atoms = set(asp.atoms(model, "need_missed"))
    python_expected = {("hero",)}
    if atoms != python_expected:
        print("MISMATCH between ASP and Python gates")
        print("  asp:", sorted(atoms))
        print("  py :", sorted(python_expected))
        return 1
    print("OK: ASP and Python gates agree.")
    return 0


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def tell(place: Place, item: Item, hero_name: str, hero_type: str,
         cautious_name: str, cautious_type: str,
         kind_name: str, kind_type: str,
         trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    cautious = world.add(Entity(id="cautious", kind="character", type=cautious_type, label=cautious_name))
    kind = world.add(Entity(id="kind", kind="character", type=kind_type, label=kind_name))
    bag = world.add(Entity(id="bag", kind="thing", type="bag", label=item.label, phrase=item.phrase,
                           owner="hero", caretaker="hero"))

    world.facts = {
        "hero_name": hero_name,
        "hero_trait": trait,
        "need_phrase": item.needed_for,
        "hidden_spot": item.hidden_spot,
        "item_label": item.label,
        "place": place.name,
        "item": item.id,
    }

    introduce(world)
    world.para()
    setup_mystery(world)
    caution(world)
    suspect_tension(world)
    world.para()
    reveal(world)
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit-style story for a young child about a missing {f["item_label"]} and a gentle clue.',
        f"Tell a careful mystery where {f['hero_name']} needs {f['item_label']} for {f['need_phrase']}, but someone moved it and a kind truth fixes the problem.",
        f'Write a child-friendly story that includes the words "need" and "bag" and ends with a kind apology.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    cautious = world.get("cautious")
    kind = world.get("kind")
    bag = world.get("bag")
    item = world.facts["item_label"]
    need = world.facts["need_phrase"]
    return [
        QAItem(
            question=f"What did {hero.label} need?",
            answer=f"{hero.label} needed {bag.phrase} for {need}.",
        ),
        QAItem(
            question=f"Who told everyone to be careful and look at the clues first?",
            answer=f"{cautious.label} did. {cautious.label} was the cautious one who slowed everyone down so they would not make a bad guess.",
        ),
        QAItem(
            question=f"Who brought the {item} back at the end?",
            answer=f"{kind.label} brought it back, told the truth, and helped solve the little mystery kindly.",
        ),
        QAItem(
            question=f"Why did the bag cause worry?",
            answer=f"It caused worry because {hero.label} needed it, but it was hidden away when it should have been ready.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be cautious?",
            answer="Being cautious means taking care, slowing down, and checking things before you act.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping, speaking gently, and doing what is fair even when something goes wrong.",
        ),
        QAItem(
            question="Why do people use bags?",
            answer="People use bags to carry things together so the things are easy to find and bring along.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit-style cautionary kindness story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--need-item", choices=ITEMS)
    ap.add_argument("--bag-item", choices=ITEMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=KINDS)
    ap.add_argument("--cautious-name")
    ap.add_argument("--cautious-type", choices=KINDS)
    ap.add_argument("--kind-name")
    ap.add_argument("--kind-type", choices=KINDS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    need_item = args.need_item or rng.choice(list(ITEMS))
    bag_item = args.bag_item or need_item
    if need_item != bag_item:
        raise StoryError("This world keeps the needed object and the missing bag as the same item.")
    hero_type = args.hero_type or rng.choice(KINDS)
    cautious_type = args.cautious_type or rng.choice(KINDS)
    kind_type = args.kind_type or rng.choice(KINDS)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    cautious_name = args.cautious_name or rng.choice(CAUTIOUS_NAMES)
    kind_name = args.kind_name or rng.choice(KIND_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        need_item=need_item,
        bag_item=bag_item,
        hero_name=hero_name,
        hero_type=hero_type,
        cautious_name=cautious_name,
        cautious_type=cautious_type,
        kind_name=kind_name,
        kind_type=kind_type,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        ITEMS[params.need_item],
        params.hero_name,
        params.hero_type,
        params.cautious_name,
        params.cautious_type,
        params.kind_name,
        params.kind_type,
        trait="careful",
    )
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
    StoryParams(place="hall", need_item="snack", bag_item="snack", hero_name="Mina", hero_type="girl",
                cautious_name="June", cautious_type="girl", kind_name="Ari", kind_type="boy"),
    StoryParams(place="classroom", need_item="library", bag_item="library", hero_name="Toby", hero_type="boy",
                cautious_name="Evan", cautious_type="boy", kind_name="Bea", kind_type="girl"),
    StoryParams(place="kitchen", need_item="picnic", bag_item="picnic", hero_name="Lina", hero_type="girl",
                cautious_name="Rosa", cautious_type="girl", kind_name="Finn", kind_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show need_missed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show need_missed/1.\n#show cautionary/1.\n#show kind_act/1.\n"))
        print("ASP atoms:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.hero_name} at {p.place} ({p.need_item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
