#!/usr/bin/env python3
"""
A small fairy-tale story world about a cautious wish, a dodo, and a magical
transformation.

Premise:
- A child courier wants to solicit help from a shy dodo at the moonlit glade.
- A spell makes the dodo scram unless the child speaks politely and keeps the
  tune in rhyme.
- A kindly transformation can turn fright into trust, but only if the warning
  is heeded.

The simulation tracks meters and memes:
- meters: distance, sparkle, weariness, steadiness
- memes: fear, trust, hope, relief, caution

The tale is built from state changes, not swapped nouns.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "child", "maiden"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "page"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    mood: str
    gleam: str
    can_host: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    guards: set[str]
    ritual: str
    finale: str


@dataclass
class StoryParams:
    place: str
    charm: str
    child_name: str
    child_type: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
# Content registries
# ---------------------------------------------------------------------------
PLACES = {
    "glade": Place(
        id="glade",
        label="the moonlit glade",
        mood="soft and silver",
        gleam="moonlight",
        can_host={"solicit", "rhyme", "cautionary", "transformation"},
    ),
    "brook": Place(
        id="brook",
        label="the whispering brook",
        mood="bright and quick",
        gleam="waterlight",
        can_host={"solicit", "rhyme", "cautionary"},
    ),
    "orchard": Place(
        id="orchard",
        label="the pear orchard",
        mood="green and sleepy",
        gleam="leaflight",
        can_host={"solicit", "rhyme", "transformation"},
    ),
}

CHARMS = {
    "rhyme": Charm(
        id="rhyme",
        label="a rhyme charm",
        phrase="a little rhyme that rang like a bell",
        guards={"fear"},
        ritual="speak in a kindly rhyme",
        finale="its last word softened into a hug",
    ),
    "cautionary": Charm(
        id="cautionary",
        label="a cautionary charm",
        phrase="a warning wrapped in a gold ribbon",
        guards={"scram"},
        ritual="listen to the warning before stepping closer",
        finale="the warning kept the trouble from waking",
    ),
    "transformation": Charm(
        id="transformation",
        label="a transformation charm",
        phrase="a spell that could turn shy fright into bright trust",
        guards={"fear", "scram"},
        ritual="offer a brave, gentle promise",
        finale="the spell changed the whole ending",
    ),
}

# A dodo belongs to a fairy-tale list of gentle creatures and can be frightened.
DODO_NAMES = ["Dodo", "Della", "Dot", "Dawn", "Dulcet"]
CHILD_NAMES = ["Lina", "Milo", "Tessa", "Pip", "Nora", "Eli"]
CHILD_TYPES = ["girl", "boy"]

# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
def _narrate_scram(world: World, child: Entity, dodo: Entity) -> None:
    sig = ("scram", child.id, dodo.id)
    if sig in world.fired:
        return
    if child.memes.get("caution", 0.0) >= 1.0 and child.memes.get("trust", 0.0) >= 1.0:
        return
    world.fired.add(sig)
    dodo.meters["distance"] = 1.0
    dodo.memes["fear"] = max(dodo.memes.get("fear", 0.0), 1.0)
    world.say(f"But the shy dodo gave one nervous blink and scrammed into the ferns.")


def _narrate_settle(world: World, child: Entity, dodo: Entity) -> None:
    sig = ("settle", child.id, dodo.id)
    if sig in world.fired:
        return
    if child.memes.get("caution", 0.0) < 1.0:
        return
    if child.memes.get("trust", 0.0) < 1.0:
        return
    world.fired.add(sig)
    dodo.meters["distance"] = 0.0
    dodo.memes["fear"] = 0.0
    dodo.memes["trust"] = 1.0
    world.say(f"The dodo paused, then came back with slow, feather-soft steps.")


def _narrate_transform(world: World, child: Entity, dodo: Entity, charm: Charm) -> None:
    sig = ("transform", child.id, dodo.id, charm.id)
    if sig in world.fired:
        return
    if charm.id != "transformation":
        return
    if child.memes.get("trust", 0.0) < 1.0 or child.memes.get("caution", 0.0) < 1.0:
        return
    world.fired.add(sig)
    dodo.type = "gentle dodo"
    dodo.label = "gentle dodo"
    dodo.meters["sparkle"] = 1.0
    dodo.memes["relief"] = 1.0
    world.say(f"The transformation charm glimmered, and the frightened dodo became a gentle friend.")


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell(place: Place, charm: Charm, child_name: str, child_type: str, helper_name: str) -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        meters={"distance": 0.0, "sparkle": 0.0, "weariness": 0.0, "steadiness": 0.0},
        memes={"fear": 0.0, "trust": 0.0, "hope": 0.0, "relief": 0.0, "caution": 0.0},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type="fairy",
        label="the meadow fairy",
        meters={"distance": 0.0, "sparkle": 1.0},
        memes={"wisdom": 1.0},
    ))
    dodo = world.add(Entity(
        id="dodo",
        kind="character",
        type="dodo",
        label="a shy dodo",
        meters={"distance": 0.0, "sparkle": 0.0},
        memes={"fear": 0.0, "trust": 0.0, "relief": 0.0},
    ))

    world.facts.update(child=child, helper=helper, dodo=dodo, charm=charm, place=place)

    # Act 1: setup
    world.say(
        f"Once upon a dusk, {child_name} went to {place.label}, where the air felt {place.mood} "
        f"and the {place.gleam} made the grass shine."
    )
    world.say(
        f"{child_name} came to solicit help from a dodo with a tiny ribbon of worry in {child.pronoun('possessive')} chest."
    )
    world.say(
        f"The meadow fairy carried {charm.phrase} and whispered that the charm asked for caution, not rush."
    )
    child.memes["hope"] += 1.0

    # Act 2: tension
    world.para()
    world.say(
        f"{child_name} tried to {charm.ritual}, but the first words came out too quick."
    )
    child.memes["caution"] += 0.0
    _narrate_scram(world, child, dodo)

    world.say(
        f"The fairy lifted one hand and reminded {child_name} that a kind wish works best when it is spoken slowly and in rhyme."
    )
    child.memes["caution"] += 1.0
    child.memes["trust"] += 1.0
    child.meters["steadiness"] += 1.0
    world.say(
        f"So {child_name} took a breath, slowed {child.pronoun('possessive')} feet, and spoke again in rhyme."
    )

    # Act 3: transformation
    world.para()
    world.say(
        f'"Please, dear dodo, hear my plea; come back and help beside the tree," {child_name} said in a little song.'
    )
    _narrate_settle(world, child, dodo)
    _narrate_transform(world, child, dodo, charm)
    child.memes["relief"] += 1.0
    child.meters["sparkle"] += 1.0

    world.say(
        f"At last the dodo bowed, no longer afraid, and the glade grew bright with trust."
    )
    world.say(
        f"{child_name} and the gentle dodo walked home together, while the warning had turned into a blessing."
    )
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Quality checks and narrative helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    charm = f["charm"]
    place = f["place"]
    return [
        f'Write a fairy-tale story about {child.id} at {place.label} where a dodo might scram unless a rhyme charm is used.',
        f"Tell a cautionary, magical story where {child.id} learns to be careful before asking a shy dodo for help.",
        f"Write a short fairy tale in which a transformation charm changes fear into trust at {place.label}.",
        f"Include the word '{charm.id}' and let the ending prove that a gentle warning mattered.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    dodo: Entity = f["dodo"]
    charm: Charm = f["charm"]
    place: Place = f["place"]

    return [
        QAItem(
            question=f"Who did {child.id} want to solicit help from at {place.label}?",
            answer=f"{child.id} wanted to solicit help from the shy dodo at {place.label}.",
        ),
        QAItem(
            question=f"What happened when {child.id} spoke too quickly at first?",
            answer="The dodo scrammed into the ferns because the wish sounded hurried and unsure.",
        ),
        QAItem(
            question=f"What did the fairy ask {child.id} to do before trying again?",
            answer=f"The fairy asked {child.id} to listen carefully, slow down, and speak in rhyme.",
        ),
        QAItem(
            question=f"How did the transformation charm change the ending?",
            answer="It turned the dodo's fear into trust, so the dodo came back as a gentle friend.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt relieved and hopeful, because the dodo stayed near instead of scramming away.",
        ),
        QAItem(
            question=f"Why was the story cautionary?",
            answer="It showed that a hurried wish can send a shy creature running, but a careful, kind approach can fix the trouble.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "dodo": [
        QAItem(
            question="What was a dodo?",
            answer="A dodo was a big, flightless bird. In fairy tales, it can be shy or silly, but it cannot fly away like a small bird.",
        )
    ],
    "rhyme": [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like 'light' and 'night'.",
        )
    ],
    "cautionary": [
        QAItem(
            question="What does cautionary mean in a story?",
            answer="Cautionary means the story gives a warning so the listener can learn to be careful.",
        )
    ],
    "transformation": [
        QAItem(
            question="What is a transformation in a fairy tale?",
            answer="A transformation is a magical change, like when fear becomes trust or a plain thing becomes something special.",
        )
    ],
    "solicit": [
        QAItem(
            question="What does it mean to solicit help?",
            answer="To solicit help means to ask for help politely.",
        )
    ],
    "scram": [
        QAItem(
            question="What does scram mean?",
            answer="Scram means to run away quickly, often because someone is startled or scared.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["charm"].id, "dodo", "rhyme", "cautionary", "transformation", "solicit", "scram"}
    out: list[QAItem] = []
    for key in ["solicit", "scram", "dodo", "rhyme", "cautionary", "transformation"]:
        if key in tags and key in WORLD_KNOWLEDGE:
            out.extend(WORLD_KNOWLEDGE[key])
    return out


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
        bits.append(f"type={e.type}")
        lines.append(f"  {e.id:10} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts:
% place(P). charm(C). can_host(P,C). child(X). dodo(D). seek_help(X,D).
% The declarative twin models a simple reasonableness gate.

scram(X,D) :- seek_help(X,D), hurried(X), shy(D), not cautious(X).
settle(X,D) :- seek_help(X,D), cautious(X), rhymed(X), shy(D).
transform(X,D) :- seek_help(X,D), cautious(X), rhymed(X), charm(transformation), shy(D).

ok_story(P,C) :- can_host(P,C), place(P), charm(C).
final(C) :- settle(X,D), transform(X,D), charm(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for c in sorted(place.can_host):
            lines.append(asp.fact("can_host", pid, c))
    for cid in CHARMS:
        lines.append(asp.fact("charm", cid))
    lines.append(asp.fact("shy", "dodo"))
    lines.append(asp.fact("seek_help", "child", "dodo"))
    lines.append(asp.fact("hurried", "child"))
    lines.append(asp.fact("cautious", "child"))
    lines.append(asp.fact("rhymed", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show ok_story/2."))
    return sorted(set(asp.atoms(model, "ok_story")))


def asp_verify() -> int:
    python_ok = {(p, c) for p in PLACES for c in CHARMS if p in PLACES and c in CHARMS and c in PLACES[p].can_host}
    asp_ok = set(asp_valid_combos())
    if asp_ok == python_ok:
        print(f"OK: clingo gate matches Python registry ({len(asp_ok)} combos).")
        return 0
    print("MISMATCH between clingo and Python registry:")
    if asp_ok - python_ok:
        print("  only in clingo:", sorted(asp_ok - python_ok))
    if python_ok - asp_ok:
        print("  only in python:", sorted(python_ok - asp_ok))
    return 1


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    charm: str
    child_name: str
    child_type: str
    helper_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world about solicit, dodo, scram, rhyme, cautionary, and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
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
    place = args.place or rng.choice(list(PLACES))
    charm = args.charm or rng.choice(list(CHARMS))
    if charm not in PLACES[place].can_host:
        raise StoryError(f"(No story: {CHARMS[charm].label} does not fit {PLACES[place].label}.)")
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    child_name = args.name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice(["Faye", "Mira", "Luma", "Puck"])
    return StoryParams(place=place, charm=charm, child_name=child_name, child_type=child_type, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        CHARMS[params.charm],
        params.child_name,
        params.child_type,
        params.helper_name,
    )
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="glade", charm="rhyme", child_name="Lina", child_type="girl", helper_name="Faye"),
    StoryParams(place="glade", charm="cautionary", child_name="Milo", child_type="boy", helper_name="Mira"),
    StoryParams(place="orchard", charm="transformation", child_name="Tessa", child_type="girl", helper_name="Luma"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show ok_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show ok_story/2."))
        print(sorted(set(asp.atoms(model, "ok_story"))))
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
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
            header = f"### {p.child_name}: {p.charm} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
