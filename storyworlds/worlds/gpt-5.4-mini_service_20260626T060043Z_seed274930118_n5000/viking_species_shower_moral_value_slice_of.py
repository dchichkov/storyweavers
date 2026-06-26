#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/viking_species_shower_moral_value_slice_of.py
===============================================================================================================

A standalone story world for a small slice-of-life tale about a viking
community, different species sharing a shower house, and a moral value
about fairness and care.

Seed image:
- A child in a seaside viking village comes in from muddy work.
- The shower house is busy because several species need different warmth,
  water pressure, and soap.
- The child wants to hurry, but the adult asks them to notice others.
- The story turns when they help make the shower kind for everyone.

This world models:
- Physical state in meters: warmth, wetness, mud, clean, steam, patience
- Emotional state in memes: joy, worry, pride, patience, care, fairness

The key narrative instrument is Moral Value:
- A moral value is the reason a choice is good for the whole little community.
- The story should show that value through action, not lecture.

The style is intended to be Slice of Life:
- small domestic stakes
- concrete shared spaces
- gentle social turn
- ending image that proves what changed
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
    species: str = "human"
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.species in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.species in {"boy", "man", "father", "viking"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def them(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class SpeciesProfile:
    id: str
    name: str
    needs_warmth: bool = True
    likes_shallow_water: bool = False
    prefers_soft_soap: bool = False


@dataclass
class BathItem:
    id: str
    label: str
    kind: str
    helps: set[str] = field(default_factory=set)
    warmth_bonus: float = 0.0
    steam_bonus: float = 0.0
    soap_bonus: float = 0.0


@dataclass
class StoryParams:
    place: str
    species: str
    item: str
    name: str
    role: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _inc(ent: Entity, key: str, amt: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _incm(ent: Entity, key: str, amt: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for child in world.characters():
        if child.meters.get("mud", 0.0) >= THRESHOLD and not child.memes.get("in_shower", 0.0):
            sig = ("mud_notice", child.id)
            if sig not in world.fired:
                world.fired.add(sig)
                out.append(f"{child.id} noticed the mud on {child.pronoun('possessive')} sleeves.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_clean(world: World, actor: Entity, item: BathItem) -> dict:
    sim = world.copy()
    _use_item(sim, sim.get(actor.id), item, narrate=False)
    me = sim.get(actor.id)
    return {
        "clean": me.meters.get("clean", 0.0) >= THRESHOLD,
        "warm": me.meters.get("warmth", 0.0) >= THRESHOLD,
        "shared": me.memes.get("fairness", 0.0) >= THRESHOLD,
    }


def _use_item(world: World, actor: Entity, item: BathItem, narrate: bool = True) -> None:
    _inc(actor, "clean", 1.0)
    _inc(actor, "wet", -1.0)
    _inc(actor, "warmth", item.warmth_bonus)
    _inc(actor, "steam", item.steam_bonus)
    _inc(actor, "soap", item.soap_bonus)
    _incm(actor, "care", 1.0)
    if narrate:
        world.say(f"{actor.id} used the {item.label} and felt better right away.")


def _wait_turn(world: World, actor: Entity) -> None:
    _incm(actor, "patience", 1.0)
    _incm(actor, "fairness", 1.0)
    world.say(f"{actor.id} waited for {actor.pronoun('possessive')} turn, listening to the water hum.")


def _adjust_shower(world: World, parent: Entity, child: Entity, species: SpeciesProfile) -> None:
    sig = ("adjust", child.id, species.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    if species.needs_warmth:
        _inc(child, "warmth", 1.0)
    if species.prefers_soft_soap:
        _inc(child, "soap", 1.0)
    _incm(parent, "care", 1.0)
    _incm(child, "joy", 1.0)
    world.say(
        f"{parent.id} turned the shower a little kinder for {species.name}, "
        f"so the water felt right on {child.pronoun('possessive')} skin."
    )


def _moral_turn(world: World, parent: Entity, child: Entity, other: Entity) -> None:
    _incm(child, "fairness", 1.0)
    _incm(child, "pride", 1.0)
    _incm(parent, "pride", 1.0)
    world.say(
        f"{child.id} saw {other.id} waiting too, and understood that a good shower "
        f"was not just for one pair of feet."
    )
    world.say(
        f"{child.id} helped make room, and {parent.id} smiled because kindness "
        f"had become part of the morning."
    )


def _set_up(world: World, child: Entity, parent: Entity, item: BathItem, other: Entity, species: SpeciesProfile) -> None:
    _inc(child, "mud", 1.0)
    _inc(child, "wet", 1.0)
    _incm(child, "worry", 1.0)
    world.say(
        f"After the harbor work, {child.id} came home muddy and cool, with salt "
        f"in {child.pronoun('possessive')} hair."
    )
    world.say(
        f"In the shower house, {other.id} was already waiting, and {species.name} "
        f"needed the water to feel a little different."
    )
    world.say(f"{child.id} wanted the {item.label} first because {child.pronoun('subject')} was tired and sticky.")


def _conflict(world: World, parent: Entity, child: Entity, item: BathItem) -> None:
    _incm(child, "impatience", 1.0)
    _incm(parent, "concern", 1.0)
    world.say(
        f"{parent.id} raised a hand and said the shower should be shared, "
        f"because {item.label} would help more than just {child.id}."
    )
    world.say(
        f"{child.id} frowned, but the warm room was small and the bench held only a few towels."
    )


def _resolution(world: World, parent: Entity, child: Entity, other: Entity, species: SpeciesProfile, item: BathItem) -> None:
    _adjust_shower(world, parent, child, species)
    _wait_turn(world, other)
    _use_item(world, child, item)
    _moral_turn(world, parent, child, other)
    _inc(child, "steam", 1.0)
    _inc(other, "warmth", 1.0)
    _inc(other, "clean", 1.0)
    world.say(
        f"By the end, the shower mist curled above the tiles, {child.id}'s hair "
        f"lay neat again, and {other.id} stepped in when the room was ready."
    )
    world.say(
        f"The morning felt simple and good: one shower, two turns, and a village "
        f"that knew how to be fair."
    )


def tell(place: Place, species: SpeciesProfile, item: BathItem, name: str, role: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=role, species=species.id))
    parent = world.add(Entity(id="Aunt", kind="character", type="adult", species="human"))
    other = world.add(Entity(id="Milo", kind="character", type="child", species="seal"))
    bath = world.add(Entity(id="Shower", kind="thing", type="fixture", label="shower"))
    towel = world.add(Entity(id="Towel", kind="thing", type="cloth", label="dry towel"))

    _set_up(world, child, parent, item, other, species)
    world.para()
    _conflict(world, parent, child, item)
    world.say(f"The {bath.label} dripped softly while {parent.id} kept the line calm.")
    world.para()
    _resolution(world, parent, child, other, species, item)

    world.facts.update(
        child=child,
        parent=parent,
        other=other,
        species=species,
        item=item,
        bath=bath,
        towel=towel,
        place=place,
        resolved=True,
    )
    return world


PLACES = {
    "harbor": Place(id="harbor", label="the harbor bathhouse", indoors=True, affords={"shower"}),
    "longhall": Place(id="longhall", label="the longhall washroom", indoors=True, affords={"shower"}),
    "cabin": Place(id="cabin", label="the little cabin washroom", indoors=True, affords={"shower"}),
}

SPECIES = {
    "human": SpeciesProfile(id="human", name="human", needs_warmth=True),
    "seal": SpeciesProfile(id="seal", name="seal", needs_warmth=True, likes_shallow_water=True),
    "fox": SpeciesProfile(id="fox", name="fox", needs_warmth=True, prefers_soft_soap=True),
    "goat": SpeciesProfile(id="goat", name="goat", needs_warmth=False),
}

ITEMS = {
    "warm_bucket": BathItem(id="warm_bucket", label="warm bucket", kind="bucket", helps={"warmth"}, warmth_bonus=1.0),
    "soft_soap": BathItem(id="soft_soap", label="soft soap", kind="soap", helps={"soap"}, soap_bonus=1.0),
    "steam_cloth": BathItem(id="steam_cloth", label="steam cloth", kind="cloth", helps={"steam"}, steam_bonus=1.0),
}

NAMES = {
    "viking": ["Astrid", "Signe", "Kari", "Eira", "Runa"],
    "human": ["Mika", "Tove", "Linn", "Jori"],
    "seal": ["Pip", "Nell", "Moss"],
    "fox": ["Pella", "Vik", "Rune"],
    "goat": ["Bran", "Hild", "Tikka"],
}

TRAITS = ["careful", "bright", "quiet", "bold", "kind"]


def compatible() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for sid, species in SPECIES.items():
            for iid, item in ITEMS.items():
                if place.indoors and "shower" in place.affords:
                    if species.needs_warmth and item.warmth_bonus > 0:
                        out.append((pid, sid, iid))
                    elif species.prefers_soft_soap and item.soap_bonus > 0:
                        out.append((pid, sid, iid))
                    elif item.kind == "cloth":
                        out.append((pid, sid, iid))
    return out


@dataclass
class StoryParams:
    place: str
    species: str
    item: str
    name: str
    role: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life viking shower storyworld with species and moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--species", choices=SPECIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["child", "teen", "viking"])
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
    combos = compatible()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.species:
        combos = [c for c in combos if c[1] == args.species]
    if args.item:
        combos = [c for c in combos if c[2] == args.item]
    if not combos:
        raise StoryError("No reasonable shower story matches those choices.")
    place, species, item = rng.choice(sorted(combos))
    s = SPECIES[species]
    role = args.role or "viking"
    name = args.name or rng.choice(NAMES.get(species, NAMES["viking"]))
    return StoryParams(place=place, species=species, item=item, name=name, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], SPECIES[params.species], ITEMS[params.item], params.name, params.role)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle slice-of-life story about a viking child named {f["child"].id} sharing a shower house.',
        f"Tell a short story where a {f['species'].name} child learns to wait for others in the shower.",
        f"Write a story with the words viking, species, shower, and a moral value about fairness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, other, species, item, place = f["child"], f["parent"], f["other"], f["species"], f["item"], f["place"]
    return [
        QAItem(
            question=f"Why did {child.id} need the shower after coming home?",
            answer=f"{child.id} came home muddy and cool from harbor work, so the shower helped {child.pronoun('object')} get clean and warm again.",
        ),
        QAItem(
            question=f"What worried {parent.id} in the shower house?",
            answer=f"{parent.id} wanted the shower to be shared fairly, because {other.id} was waiting too and {species.name} needed the water to feel right.",
        ),
        QAItem(
            question=f"How did {child.id} show the moral value in the end?",
            answer=f"{child.id} waited, helped make the shower kinder for {species.name}, and then used the {item.label} without crowding {other.id}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The shower went from busy and cramped to calm and shared, and everyone had their turn in a kinder way at {place.label}.",
        ),
    ]


KNOWLEDGE = {
    "viking": [
        ("What is a viking?",
         "A viking was a seafaring person from old Scandinavia who traveled by boat, traded, explored, and lived near the sea.")
    ],
    "species": [
        ("What does species mean?",
         "A species is a group of living things that are alike and can be described as one kind of animal or one kind of plant.")
    ],
    "shower": [
        ("What is a shower?",
         "A shower is a place where water falls down from above so people can wash themselves clean.")
    ],
    "fairness": [
        ("What is fairness?",
         "Fairness means giving people a proper turn and treating their needs with equal care.")
    ],
    "care": [
        ("What does it mean to care for someone?",
         "To care for someone means to notice what they need and help in a kind, thoughtful way.")
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question=q, answer=a)
        for key in ["viking", "species", "shower", "fairness", "care"]
        for q, a in KNOWLEDGE[key]
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if abs(v) > 0.0}
        memes = {k: round(v, 2) for k, v in e.memes.items() if abs(v) > 0.0}
        lines.append(f"{e.id}: {e.type} {e.species} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(Child, Item) :- child(Child), item(Item), needs(Item, Need), has(Child, Need).
good_choice(Child, Item) :- at_risk(Child, Item), helps(Item, Need), needs(Item, Need).
shared_good(Child, Other) :- waiting(Other), shares(Child), fairness(Child).

valid_story(Place, Species, Item) :- place(Place), species(Species), item(Item),
                                     compatible(Place, Species, Item).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, s in SPECIES.items():
        lines.append(asp.fact("species", sid))
        if s.needs_warmth:
            lines.append(asp.fact("needs", sid, "warmth"))
        if s.likes_shallow_water:
            lines.append(asp.fact("likes", sid, "shallow_water"))
        if s.prefers_soft_soap:
            lines.append(asp.fact("prefers", sid, "soft_soap"))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.warmth_bonus > 0:
            lines.append(asp.fact("helps", iid, "warmth"))
        if item.steam_bonus > 0:
            lines.append(asp.fact("helps", iid, "steam"))
        if item.soap_bonus > 0:
            lines.append(asp.fact("helps", iid, "soap"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(compatible())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combinations).")
        return 0
    print("Mismatch between ASP and Python.")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def explain_rejection() -> str:
    return "This shower story needs a combination that can honestly support warmth, care, and sharing."


def valid_combos() -> list[tuple[str, str, str]]:
    return compatible()


def select_item(species: SpeciesProfile, rng: random.Random) -> BathItem:
    options = [i for i in ITEMS.values() if i.kind == "cloth" or (species.prefers_soft_soap and i.soap_bonus > 0) or (species.needs_warmth and i.warmth_bonus > 0)]
    return rng.choice(options)


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
    StoryParams(place="harbor", species="seal", item="warm_bucket", name="Signe", role="viking"),
    StoryParams(place="longhall", species="fox", item="soft_soap", name="Astrid", role="viking"),
    StoryParams(place="cabin", species="human", item="steam_cloth", name="Kari", role="viking"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} compatible story tuples:")
        for row in vals:
            print(" ", row)
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
            header = f"### {p.name}: {p.species} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
