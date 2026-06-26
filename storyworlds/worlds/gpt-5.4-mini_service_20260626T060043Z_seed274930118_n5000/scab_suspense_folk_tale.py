#!/usr/bin/env python3
"""
A standalone storyworld for a small folk-tale style suspense domain about a scab.

The seed image:
- A child gets a scab.
- The child is tempted to pick it.
- A careful elder keeps watch, makes a simple promise, and the scab heals.

The simulated world keeps both physical state (the scab, ointment, bandage, dirt)
and emotional state (worry, patience, relief). The suspense comes from whether
the child can leave the scab alone long enough for it to mend.
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
# Domain model
# ---------------------------------------------------------------------------

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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "sister"}
        male = {"boy", "father", "man", "grandfather", "brother"}
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
    indoors: bool = False
    quiet: bool = True
    has_stream: bool = False
    has_herbs: bool = False


@dataclass
class HealingItem:
    id: str
    label: str
    phrase: str
    kind: str
    helps_with: set[str] = field(default_factory=set)
    fits: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.daylight: str = "dawn"

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "village_lane": Place("the village lane", indoors=False, quiet=True, has_stream=False, has_herbs=False),
    "herb_garden": Place("the herb garden", indoors=False, quiet=True, has_stream=False, has_herbs=True),
    "brook_side": Place("the brook side", indoors=False, quiet=True, has_stream=True, has_herbs=True),
    "hearth_room": Place("the hearth room", indoors=True, quiet=True, has_stream=False, has_herbs=True),
}

HERO_NAMES = ["Mara", "Nell", "Tavi", "Lina", "Bram", "Anya", "Pip", "Reed", "Sora", "Niko"]
ELDER_NAMES = ["Grandmother", "Old Rowan", "Aunt Wren", "Grandfather", "Elder Mallow"]

TALES = {
    "scab": {
        "wound": "a small scrape on {body_part}",
        "dread": "the scab could split open if it was picked",
        "risk": "the scrape might bleed again",
        "ending": "the scab went from red and hard to dry and quiet",
        "body_part": "knee",
    },
    "elbow_scab": {
        "wound": "a scratch on {body_part}",
        "dread": "the scab might come loose if it was scratched",
        "risk": "the skin could start to sting again",
        "ending": "the scab stayed on until it turned small and brown",
        "body_part": "elbow",
    },
}

HEALING_ITEMS = {
    "bandage": HealingItem(
        id="bandage",
        label="bandage",
        phrase="a clean cloth bandage",
        kind="cover",
        helps_with={"scab"},
        fits={"knee", "elbow"},
    ),
    "salve": HealingItem(
        id="salve",
        label="salve",
        phrase="a little jar of green salve",
        kind="soothe",
        helps_with={"scab", "elbow_scab"},
        fits={"knee", "elbow"},
    ),
    "spare_kerchief": HealingItem(
        id="kerchief",
        label="kerchief",
        phrase="a soft kerchief",
        kind="cover",
        helps_with={"scab", "elbow_scab"},
        fits={"knee", "elbow"},
    ),
}

TRAITS = ["curious", "brave", "restless", "gentle", "stubborn", "sensible"]


# ---------------------------------------------------------------------------
# State and causal rules
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    tale: str
    name: str
    elder: str
    trait: str
    seed: Optional[int] = None


def wound_at_risk(tale: str) -> bool:
    return tale in TALES


def best_healing_item(tale: str, body_part: str) -> Optional[HealingItem]:
    for item in HEALING_ITEMS.values():
        if tale in item.helps_with and body_part in item.fits:
            return item
    return None


def place_has_cover(place: Place) -> bool:
    return place.indoors or place.has_herbs or place.has_stream


def tale_body_part(tale: str) -> str:
    return TALES[tale]["body_part"]


def tale_wound_text(tale: str) -> str:
    return TALES[tale]["wound"]


def tale_dread(tale: str) -> str:
    return TALES[tale]["dread"]


def tale_risk(tale: str) -> str:
    return TALES[tale]["risk"]


def tale_ending(tale: str) -> str:
    return TALES[tale]["ending"]


def propagate(world: World) -> None:
    child = next(e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"})
    wound = world.get("wound")
    item = world.entities.get("healing")
    if wound.meters.get("picked", 0.0) >= THRESHOLD and "bleed" not in world.fired:
        world.fired.add(("bleed",))
        wound.meters["bleed"] = 1.0
        child.memes["worry"] += 1.0
        world.say(f"The little scrape began to sting, and {child.id} felt a hush of fear.")
    if item and wound.meters.get("care", 0.0) >= THRESHOLD and ("seal", item.id) not in world.fired:
        world.fired.add(("seal", item.id))
        wound.meters["covered"] = 1.0
        wound.memes["safe"] = 1.0
        child.memes["relief"] += 1.0
        world.say(f"The careful covering kept the scrape from catching on rough things.")
    if wound.meters.get("covered", 0.0) >= THRESHOLD and "heal" not in world.fired:
        world.fired.add(("heal",))
        wound.meters["healing"] = 1.0
        child.memes["patience"] += 1.0
        world.say(f"By sunset, the sore place had begun to mend.")


# ---------------------------------------------------------------------------
# Narrative beats
# ---------------------------------------------------------------------------

def introduce(world: World, child: Entity, elder: Entity, tale: str) -> None:
    body_part = tale_body_part(tale)
    world.say(
        f"Once, in {world.place.name}, there lived a {child.pronoun('subject')} child named {child.id} "
        f"who was {child.props.get('trait', 'quiet')} and remembered every small trouble."
    )
    world.say(
        f"One day {child.id} came home with {tale_wound_text(tale).format(body_part=body_part)}."
    )
    world.say(
        f"{elder.id} washed the place with warm water and said the old warning: "
        f'"Do not pick at a scab, for {tale_dread(tale)}."'
    )


def suspense(world: World, child: Entity, tale: str) -> None:
    child.memes["temptation"] += 1.0
    world.say(
        f"That evening the scab itched like a tiny thorn, and {child.id} kept looking at it."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} wanted to scratch it just once, but {tale_risk(tale)}."
    )
    world.say(
        f"The room grew very still, as if even the lamp flame was waiting to see what {child.id} would do."
    )


def offer_help(world: World, elder: Entity, tale: str, place: Place) -> Optional[HealingItem]:
    body_part = tale_body_part(tale)
    item = best_healing_item(tale, body_part)
    if item is None:
        return None
    ent = world.add(Entity(
        id="healing",
        type=item.kind,
        label=item.label,
        phrase=item.phrase,
        owner=elder.id,
        caretaker=elder.id,
    ))
    ent.props["kind"] = item.kind
    world.say(
        f"{elder.id} brought out {item.phrase} and wrapped it around the sore place."
    )
    if place.indoors:
        world.say("Inside the hearth room, the cover stayed clean and snug.")
    elif place.has_herbs:
        world.say("The herbs smelled sharp and kind, like the garden knew how to mend things.")
    else:
        world.say("The wind stayed away, so the cover did its quiet work.")
    return item


def resolve(world: World, child: Entity, elder: Entity, tale: str) -> None:
    wound = world.get("wound")
    child.memes["patience"] += 1.0
    wound.meters["care"] = 1.0
    propagate(world)
    world.say(
        f"{child.id} put both hands in {child.pronoun('possessive')} lap and waited."
    )
    world.say(
        f"{elder.id} sat beside {child.id} and told a soft story about a fox who once trusted time."
    )
    world.say(
        f"By morning, {tale_ending(tale)}, and the child could laugh without fear."
    )


def tell(place: Place, tale: str, hero_name: str, elder_name: str, trait: str) -> World:
    world = World(place)
    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type="girl" if hero_name in {"Mara", "Nell", "Lina", "Anya", "Sora"} else "boy",
        props={"trait": trait},
        meters={"health": 1.0},
        memes={"worry": 0.0, "relief": 0.0, "patience": 0.0, "temptation": 0.0},
    ))
    elder = world.add(Entity(
        id=elder_name,
        kind="character",
        type="grandmother" if "Grandmother" in elder_name or elder_name == "Aunt Wren" else "grandfather",
        props={"role": "elder"},
        memes={"care": 1.0},
    ))
    wound = world.add(Entity(
        id="wound",
        kind="thing",
        type=tale,
        label="scab",
        phrase="a scab",
        owner=child.id,
        caretaker=elder.id,
        meters={"picked": 0.0, "covered": 0.0, "healing": 0.0},
        memes={"safe": 0.0},
    ))

    world.say(
        f"{child.id} was a {trait} little one who loved to roam near {place.name}."
    )
    world.say(
        f"{elder.id} was the one who knew which leaves soothed a scrape and which touches made it worse."
    )
    world.para()
    introduce(world, child, elder, tale)
    world.para()
    suspense(world, child, tale)
    offer_help(world, elder, tale, place)
    resolve(world, child, elder, tale)

    world.facts.update(
        child=child,
        elder=elder,
        wound=wound,
        tale=tale,
        place=place,
        item=world.entities.get("healing"),
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    tale: str = f["tale"]
    return [
        f'Write a short folk tale for a young child about a scab and the worry of not picking it.',
        f"Tell a suspenseful bedtime story where {child.id} has a scab and {elder.id} helps {child.id} leave it alone.",
        f'Write a gentle story that includes the word "scab" and ends with the sore place healing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    tale: str = f["tale"]
    item: Optional[Entity] = f["item"]
    place: Place = f["place"]
    body_part = tale_body_part(tale)
    qa = [
        QAItem(
            question=f"What small hurt did {child.id} have in the story?",
            answer=f"{child.id} had a scab on {body_part}, and {elder.id} washed it carefully.",
        ),
        QAItem(
            question=f"Why was {child.id} tempted to touch the scab?",
            answer=f"The scab itched, and {child.id} wanted to scratch it even though that could make the hurt worse.",
        ),
        QAItem(
            question=f"Who helped {child.id} take care of the scab?",
            answer=f"{elder.id} helped by cleaning it, warning {child.id}, and covering it with a careful dressing.",
        ),
    ]
    if item is not None:
        qa.append(
            QAItem(
                question=f"What did {elder.id} bring to protect the scab?",
                answer=f"{elder.id} brought {item.phrase} so the scab could stay covered and heal quietly.",
            )
        )
    qa.append(
        QAItem(
            question=f"How did the story end for {child.id}'s scab?",
            answer=f"It healed slowly until it turned dry and small, and {child.id} no longer had to fear touching it.",
        )
    )
    return qa


WORLD_KNOWLEDGE = {
    "scab": (
        "What is a scab?",
        "A scab is a dry crust that forms over a small cut or scrape while the skin heals.",
    ),
    "bandage": (
        "What is a bandage for?",
        "A bandage helps keep a scrape clean and covered so it can heal.",
    ),
    "salve": (
        "What does salve do?",
        "Salve is a soothing ointment that can help a sore place feel better and stay soft.",
    ),
    "hearth": (
        "Why do people tell stories by the hearth?",
        "People gather by the hearth because it is warm and safe, which makes it a good place for stories.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    for key in ["scab", "bandage", "salve", "hearth"]:
        q, a = WORLD_KNOWLEDGE[key]
        out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for p in sample.prompts:
        parts.append(f"- {p}")
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)} props={dict(e.props)}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts:
% place(P). indoors(P). has_herbs(P). has_stream(P).
% tale(T). body_part(T,B). item(I). helps_with(I,T). fits(I,B).

at_risk(T) :- tale(T), body_part(T,B), wound_on(B).
needs_cover(T) :- at_risk(T), helps_with(I,T), fits(I,B), wound_on(B).

safe_choice(T) :- tale(T), at_risk(T), needs_cover(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        if place.has_herbs:
            lines.append(asp.fact("has_herbs", pid))
        if place.has_stream:
            lines.append(asp.fact("has_stream", pid))
    for tid, data in TALES.items():
        lines.append(asp.fact("tale", tid))
        lines.append(asp.fact("body_part", tid, data["body_part"]))
    for iid, item in HEALING_ITEMS.items():
        lines.append(asp.fact("item", iid))
        for t in sorted(item.helps_with):
            lines.append(asp.fact("helps_with", iid, t))
        for b in sorted(item.fits):
            lines.append(asp.fact("fits", iid, b))
    lines.append(asp.fact("wound_on", "knee"))
    lines.append(asp.fact("wound_on", "elbow"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_tales() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_choice/1."))
    return sorted(set(asp.atoms(model, "safe_choice")))


def asp_verify() -> int:
    python_set = {t for t in TALES if best_healing_item(t, tale_body_part(t)) is not None}
    asp_set = {x[0] for x in asp_valid_tales()}
    if python_set == asp_set:
        print(f"OK: ASP parity matches Python ({len(python_set)} tale(s)).")
        return 0
    print("MISMATCH between ASP and Python")
    print("python:", sorted(python_set))
    print("asp:", sorted(asp_set))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="herb_garden", tale="scab", name="Mara", elder="Grandmother", trait="curious"),
    StoryParams(place="hearth_room", tale="elbow_scab", name="Bram", elder="Old Rowan", trait="restless"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a scab, suspense, and a folk-tale cure.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tale", choices=TALES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--elder", choices=ELDER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    tale = args.tale or rng.choice(list(TALES))
    name = args.name or rng.choice(HERO_NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, tale=tale, name=name, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.tale, params.name, params.elder, params.trait)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_choice/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show safe_choice/1."))
        print(asp.atoms(model, "safe_choice"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
