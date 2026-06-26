#!/usr/bin/env python3
"""
storyworlds/worlds/bait_tremble_list_reconciliation_myth.py
===========================================================

A small mythic storyworld about a child, a forbidden bait, a trembling fear,
and a reconciliation that restores the village's peace.

The world is intentionally tiny and classical:
- a child wants to use bait at the river,
- an elder worries because the village's sacred list forbids a certain taking,
- the child trembles, learns the reason, and makes amends,
- reconciliation ends the story with the list honored and the river calmed.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- eager import from storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "daughter", "sister"}
        male = {"boy", "man", "father", "son", "brother"}
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
    sacred: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Bait:
    id: str
    label: str
    phrase: str
    made_of: str
    river_word: str
    risk_word: str
    can_reconcile: bool = True


@dataclass
class ListItem:
    id: str
    label: str
    phrase: str
    forbidden_action: str
    reason: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        return World(
            place=copy.deepcopy(self.place),
            entities=copy.deepcopy(self.entities),
            facts=copy.deepcopy(self.facts),
            fired=set(self.fired),
            paragraphs=[[]],
        )

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    hero: str
    gender: str
    elder: str
    bait: str
    list_item: str
    seed: Optional[int] = None


PLACES = {
    "riverbank": Place(name="the riverbank", sacred=True, affords={"bait"}),
    "village": Place(name="the village square", sacred=False, affords=set()),
    "grove": Place(name="the old grove", sacred=True, affords={"bait"}),
}

BAITS = {
    "reed": Bait(
        id="reed",
        label="reed bait",
        phrase="a small bundle of sweet reed bait",
        made_of="reeds",
        river_word="river",
        risk_word="tremble",
    ),
    "honey": Bait(
        id="honey",
        label="honey bait",
        phrase="a sticky little cake of honey bait",
        made_of="honey",
        river_word="river",
        risk_word="tremble",
    ),
    "berry": Bait(
        id="berry",
        label="berry bait",
        phrase="a bright bowl of berry bait",
        made_of="berries",
        river_word="river",
        risk_word="tremble",
    ),
}

LISTS = {
    "taboo": ListItem(
        id="taboo",
        label="the sacred list",
        phrase="the sacred list of river rules",
        forbidden_action="take bait before the blessing",
        reason="it kept the river spirit from feeling tricked",
    ),
    "offering": ListItem(
        id="offering",
        label="the village list",
        phrase="the village list of offerings",
        forbidden_action="hide the offering from the elder",
        reason="each gift had to be spoken aloud",
    ),
    "promise": ListItem(
        id="promise",
        label="the old list",
        phrase="the old list of promises",
        forbidden_action="use bait without asking",
        reason="the promise was meant to keep peace",
    ),
}

GIRL_NAMES = ["Mira", "Nia", "Lina", "Sera", "Tala", "Iris", "Mina"]
BOY_NAMES = ["Orin", "Kai", "Pavel", "Ari", "Niko", "Daren", "Theo"]
ELDER_NAMES = ["Grandmother Asha", "Old Kora", "Elder Ilya", "Grandfather Sol"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: bait, tremble, list, reconciliation.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--bait", choices=BAITS.keys())
    ap.add_argument("--list-item", choices=LISTS.keys())
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


def reasonableness_gate(place: str, bait: str, list_item: str) -> bool:
    return place in {"riverbank", "grove"} and bait in BAITS and list_item in LISTS


def explain_rejection(place: str, bait: str, list_item: str) -> str:
    return (
        f"(No story: {bait} and {list_item} need a sacred place like the riverbank or grove, "
        f"because this myth depends on a real river-side tension and reconciliation.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES.keys()))
    bait = args.bait or rng.choice(list(BAITS.keys()))
    list_item = args.list_item or rng.choice(list(LISTS.keys()))
    if not reasonableness_gate(place, bait, list_item):
        raise StoryError(explain_rejection(place, bait, list_item))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(place=place, hero=hero, gender=gender, elder=elder, bait=bait, list_item=list_item)


def _do_tremble(world: World, hero: Entity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    hero.meters["tremble"] = hero.meters.get("tremble", 0) + 1


def _do_reconcile(world: World, hero: Entity, elder: Entity, list_item: ListItem, bait: Bait) -> None:
    hero.memes["peace"] = hero.memes.get("peace", 0) + 1
    hero.memes["fear"] = 0
    elder.memes["peace"] = elder.memes.get("peace", 0) + 1
    world.facts["reconciled"] = True
    world.facts["reconciliation"] = f"{hero.id} returned the bait and followed {list_item.label}."


def tell(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type=params.gender))
    elder = world.add(Entity(id="elder", kind="character", type="elder", label=params.elder))
    bait = BAITS[params.bait]
    list_item = LISTS[params.list_item]
    world.add(Entity(id="bait", type="bait", label=bait.label, phrase=bait.phrase, owner=hero.id))
    world.add(Entity(id="list", type="list", label=list_item.label, phrase=list_item.phrase, caretaker=elder.id))

    world.facts.update(hero=hero, elder=elder, bait=bait, list_item=list_item, place=world.place)

    world.say(f"Long ago, {hero.id} lived near {world.place.name}, where the water knew old songs.")
    world.say(f"{hero.id} loved the {bait.label}, because {bait.phrase} shone like a tiny treasure.")
    world.say(f"Beside the fire, {elder.label} guarded {list_item.phrase}, and everyone in the village knew its weight.")

    world.para()
    world.say(f"One dawn, {hero.id} reached for the bait and felt a sudden tremble in {hero.pronoun('possessive')} hands.")
    _do_tremble(world, hero)
    world.say(f"{hero.pronoun().capitalize()} wanted to {list_item.forbidden_action}, but {list_item.reason}.")
    world.say(f"When {hero.id} stepped toward the {world.place.name.split()[-1]}, {elder.label} raised a hand and spoke softly.")

    world.para()
    world.say(f'"The {list_item.label} says we must not {list_item.forbidden_action}," {elder.label} said.')
    world.say(f'"If we forget the list, the river will grow shy, and our gifts will turn into dust."')
    world.say(f"{hero.id} trembled harder, because {hero.pronoun('possessive')} wish had hurt the old promise.")

    world.para()
    world.say(f"Then {hero.id} bowed, carried the bait back, and placed it at {elder.label}'s feet.")
    _do_reconcile(world, hero, elder, list_item, bait)
    world.say(f'Together they spoke the {list_item.label} aloud, and the words felt like a warm blanket over the stones.')
    world.say(f"By sunset, {hero.id} and {elder.label} walked side by side, and the river sang without fear.")

    world.facts["place_name"] = world.place.name
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    bait = f["bait"]
    list_item = f["list_item"]
    return [
        f'Write a short myth for a child about {hero.id}, {bait.label}, and {list_item.label}.',
        f"Tell a gentle story where {hero.id} trembles, {elder.label} warns about the list, and they reconcile.",
        f'Write a mythic tale that includes a bait, a trembling choice, and a reconciliation at {world.place.name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    bait: Bait = f["bait"]
    list_item: ListItem = f["list_item"]
    place = f["place_name"]
    return [
        QAItem(
            question=f"Who was the story about near {place}?",
            answer=f"It was about {hero.id}, who lived near {place} and wanted the {bait.label}.",
        ),
        QAItem(
            question=f"Why did {hero.id} tremble when reaching for the bait?",
            answer=f"{hero.id} trembled because {list_item.label} said not to {list_item.forbidden_action}, and the choice felt heavy.",
        ),
        QAItem(
            question=f"What did {elder.label} remind {hero.id} about?",
            answer=f"{elder.label} reminded {hero.id} about {list_item.phrase}, because {list_item.reason}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with reconciliation: {hero.id} returned the bait, followed the list, and walked beside {elder.label} in peace.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bait?",
            answer="Bait is food or a tempting thing used to attract an animal, especially fish in a river or pond.",
        ),
        QAItem(
            question="What does it mean to tremble?",
            answer="To tremble means to shake a little, often because of fear, cold, or excitement.",
        ),
        QAItem(
            question="What is a list?",
            answer="A list is a set of words written in order, often to remember rules, names, or things to do.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop fighting, make peace, and feel friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
place_sacred(P) :- sacred_place(P).
story_ok(P,B,L) :- place_sacred(P), bait(B), list_item(L).

tremble(H) :- hero(H).
reconcile(H,E) :- hero(H), elder(E), list_item(_), bait(_).
#show story_ok/3.
#show tremble/1.
#show reconcile/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("sacred_place", pid) if p.sacred else asp.fact("place", pid))
    for bid in BAITS:
        lines.append(asp.fact("bait", bid))
    for lid in LISTS:
        lines.append(asp.fact("list_item", lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    asp_set = set(asp.atoms(model, "story_ok"))
    py_set = {
        (place, bait, lid)
        for place in PLACES
        for bait in BAITS
        for lid in LISTS
        if reasonableness_gate(place, bait, lid)
    }
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print(" only in clingo:", sorted(asp_set - py_set))
    print(" only in python:", sorted(py_set - asp_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


def resolve_story(params: StoryParams) -> StorySample:
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
    StoryParams(place="riverbank", hero="Mira", gender="girl", elder="Grandmother Asha", bait="reed", list_item="taboo"),
    StoryParams(place="grove", hero="Orin", gender="boy", elder="Old Kora", bait="honey", list_item="offering"),
    StoryParams(place="riverbank", hero="Tala", gender="girl", elder="Elder Ilya", bait="berry", list_item="promise"),
]


def generate(params: StoryParams) -> StorySample:
    return resolve_story(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_ok/3.\n#show tremble/1.\n#show reconcile/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, bait, lid in combos:
            print(f"  {place:10} {bait:8} {lid:10}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.hero}: {p.bait} at {p.place} (list: {p.list_item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
