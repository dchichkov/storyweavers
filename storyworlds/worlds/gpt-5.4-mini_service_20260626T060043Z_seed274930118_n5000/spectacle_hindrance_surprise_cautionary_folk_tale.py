#!/usr/bin/env python3
"""
storyworlds/worlds/spectacle_hindrance_surprise_cautionary_folk_tale.py
=======================================================================

A small folk-tale story world about a planned spectacle, a stubborn hindrance,
and a surprising cautionary turn that ends in a safer, wiser celebration.

Premise:
- A child or young helper prepares for a village spectacle.
- Something important goes wrong: a lantern snuffs out, a bridge sways, a drum
  rips, or another physical hindrance blocks the show.
- A surprise helper, clever tool, or remembered warning turns the trouble into
  a safer path.
- The ending leaves a concrete image of the changed world: the show proceeds
  differently, or the crowd learns to avoid the danger next time.

This file is standalone and follows the Storyweavers storyworld contract.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "risk": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "surprise": 0.0, "hope": 0.0, "prudence": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "daughter"}
        male = {"boy", "man", "father", "son"}
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
    outdoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Spectacle:
    id: str
    name: str
    verb: str
    gerund: str
    setting_line: str
    ingredient: str
    danger: str
    hindrance: str
    surprise: str
    caution: str
    damage: str
    risk_zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    covers: set[str]
    fixes: set[str]
    prep: str
    tail: str
    plural: bool = False
    protective: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        return w


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "village_green": Place("the village green", outdoor=True, affords={"lanterns", "drum", "maypole"}),
    "river_path": Place("the river path", outdoor=True, affords={"lanterns", "drum"}),
    "barn_yard": Place("the barn yard", outdoor=True, affords={"drum", "maypole"}),
    "school_hall": Place("the school hall", outdoor=False, affords={"lanterns", "drum"}),
}

SPECTACLES = {
    "lanterns": Spectacle(
        id="lanterns",
        name="lantern show",
        verb="light the lantern show",
        gerund="lighting lanterns",
        setting_line="paper lanterns hung like little moons from the ropes.",
        ingredient="wax",
        danger="the flame could scorch the paper",
        hindrance="a sudden draft",
        surprise="a clay bowl of water",
        caution="keep water close when fire is near",
        damage="blackened",
        risk_zone={"hands", "torso"},
        keyword="spectacle",
        tags={"spectacle", "fire", "warning"},
    ),
    "drum": Spectacle(
        id="drum",
        name="drum dance",
        verb="start the drum dance",
        gerund="beating the drum",
        setting_line="the drumbeat bounced across the yard like a happy horse.",
        ingredient="hide",
        danger="the drum skin could split",
        hindrance="a frayed strap",
        surprise="a spare cord",
        caution="check old straps before a long show",
        damage="ripped",
        risk_zone={"hands"},
        keyword="spectacle",
        tags={"spectacle", "music", "warning"},
    ),
    "maypole": Spectacle(
        id="maypole",
        name="maypole dance",
        verb="raise the maypole dance",
        gerund="braiding ribbons",
        setting_line="bright ribbons waited in a basket beside the post.",
        ingredient="ribbons",
        danger="the pole could slip in soft ground",
        hindrance="muddy earth",
        surprise="flat stones",
        caution="set a tall pole on firm ground",
        damage="tilted",
        risk_zone={"feet"},
        keyword="spectacle",
        tags={"spectacle", "earth", "warning"},
    ),
}

AIDS = {
    "water_bowl": Aid(
        id="water_bowl",
        label="a clay bowl of water",
        phrase="a cool clay bowl of water",
        covers={"hands", "torso"},
        fixes={"fire"},
        prep="set a clay bowl of water beside the lanterns",
        tail="kept the water near the flames",
        protective=True,
    ),
    "spare_cord": Aid(
        id="spare_cord",
        label="a spare cord",
        phrase="a strong spare cord",
        covers={"hands"},
        fixes={"music"},
        prep="tie on a spare cord",
        tail="kept the drum tied tight",
    ),
    "flat_stones": Aid(
        id="flat_stones",
        label="flat stones",
        phrase="two flat stones",
        covers={"feet"},
        fixes={"earth"},
        prep="lay flat stones under the pole",
        tail="kept the pole standing firm",
        plural=True,
    ),
    "lantern_cover": Aid(
        id="lantern cover",
        label="a lantern cover",
        phrase="a stitched lantern cover",
        covers={"hands", "torso"},
        fixes={"fire"},
        prep="pull on a lantern cover",
        tail="held the paper safe from sparks",
    ),
}

CHARACTER_NAMES = {
    "girl": ["Mira", "Lena", "Sana", "Ivy", "Nora"],
    "boy": ["Jory", "Pavel", "Theo", "Tavi", "Eli"],
}
TRAITS = ["careful", "curious", "bold", "kind", "quiet", "cheerful"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    spectacle: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(S, A) :- spectacle(S), zone(S, R), aid_covers(A, R).
fixes(A, S) :- aid(A), spectacle(S), aid_fixes(A, K), danger_kind(S, K), at_risk(S, A).
valid(P, S, A) :- place(P), affords(P, S), fixes(A, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.outdoor:
            lines.append(asp.fact("outdoor", pid))
        for s in sorted(p.affords):
            lines.append(asp.fact("affords", pid, s))
    for sid, s in SPECTACLES.items():
        lines.append(asp.fact("spectacle", sid))
        lines.append(asp.fact("danger_kind", sid, {"fire": "fire", "music": "music", "earth": "earth"}[sid if sid in {"lanterns", "drum", "maypole"} else "fire"]))
        for r in sorted(s.risk_zone):
            lines.append(asp.fact("zone", sid, r))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for r in sorted(a.covers):
            lines.append(asp.fact("aid_covers", aid, r))
        for k in sorted(a.fixes):
            lines.append(asp.fact("aid_fixes", aid, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, p in PLACES.items():
        for sid in p.affords:
            spec = SPECTACLES[sid]
            for aid in AIDS.values():
                if any(region in spec.risk_zone for region in aid.covers) and any(
                    k in spec.tags for k in aid.fixes
                ):
                    out.append((pid, sid, aid.id))
    return sorted(set(out))


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
    print("MISMATCH between clingo and python gates.")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------
def choose_aid(spec: Spectacle) -> Optional[Aid]:
    for aid in AIDS.values():
        if any(region in spec.risk_zone for region in aid.covers) and any(k in spec.tags for k in aid.fixes):
            return aid
    return None


def predict_hindrance(world: World, actor: Entity, spec: Spectacle) -> dict:
    sim = world.copy()
    _do_spectacle(sim, sim.get(actor.id), spec, narrate=False)
    target = sim.facts["object"]
    return {"damaged": bool(target.meters["damage"] >= THRESHOLD)}


def _do_spectacle(world: World, actor: Entity, spec: Spectacle, narrate: bool = True) -> None:
    world.zone = set(spec.risk_zone)
    actor.memes["hope"] += 1
    if spec.id == "lanterns":
        actor.meters["risk"] += 1
    elif spec.id == "drum":
        actor.meters["risk"] += 0.5
    else:
        actor.meters["risk"] += 0.5
    if narrate:
        world.say(spec.setting_line)


def tell(place: Place, spec: Spectacle, hero_name: str, gender: str, parent: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, meters={"damage": 0.0, "risk": 0.0}, memes={"worry": 0.0, "surprise": 0.0, "hope": 0.0, "prudence": 0.0, "joy": 0.0}))
    elder = world.add(Entity(id="elder", kind="character", type=parent, label=f"the {parent}"))
    object_id = "object"
    object_ent = world.add(Entity(id=object_id, type="thing", label=spec.name, phrase=spec.name, caretaker=elder.id))
    world.facts["hero"] = hero
    world.facts["elder"] = elder
    world.facts["object"] = object_ent
    world.facts["spec"] = spec
    world.facts["place"] = place

    world.say(f"{hero.id} was a {trait} {gender} who loved the village spectacle.")
    world.say(f"The {parent} had promised a fine day for the {spec.name}, and {hero.id} helped with the work.")

    world.para()
    world.say(f"At {place.name}, {spec.setting_line}")
    world.say(f"But {spec.hindrance} came and made trouble. It was the kind of hindrance that could spoil the day.")
    hero.memes["worry"] += 1
    hero.memes["prudence"] += 1
    object_ent.meters["damage"] += 1

    world.para()
    aid = choose_aid(spec)
    if aid is None:
        raise StoryError("No sensible aid exists for this spectacle.")
    if spec.id == "lanterns":
        world.say(f"Then, as if by surprise, {hero.id} found {aid.label} beside the bench.")
        world.say(f"{hero.id} remembered the old caution: {spec.caution}.")
    elif spec.id == "drum":
        world.say(f"Then, by surprise, {hero.id} found {aid.label} tucked under the drum stool.")
        world.say(f"{hero.id} remembered the old caution: {spec.caution}.")
    else:
        world.say(f"Then, by surprise, {hero.id} spotted {aid.label} by the rope pile.")
        world.say(f"{hero.id} remembered the old caution: {spec.caution}.")

    if spec.id == "lanterns":
        hero.memes["surprise"] += 1
    if spec.id == "drum":
        hero.memes["surprise"] += 1
    if spec.id == "maypole":
        hero.memes["surprise"] += 1

    if spec.id == "lanterns":
        world.say(f"{hero.id} and {parent} used {aid.prep}, and the paper lanterns stayed safe.")
        object_ent.meters["damage"] = 0.0
    elif spec.id == "drum":
        world.say(f"{hero.id} and {parent} chose to {aid.prep}, and the drum kept its beat.")
        object_ent.meters["damage"] = 0.0
    else:
        world.say(f"{hero.id} and {parent} chose to {aid.prep}, and the pole stood straight.")
        object_ent.meters["damage"] = 0.0

    world.para()
    hero.memes["joy"] += 1
    world.say(f"In the end, the {spec.name} went on in a safer way.")
    world.say(f"{hero.id} smiled, and the crowd remembered that a small caution can save a whole spectacle.")
    world.facts.update(spec=spec, aid=aid)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    spec = world.facts["spec"]
    return [
        f'Write a folk tale for a child about a {spec.keyword} spectacle with a sudden hindrance and a surprising safe fix.',
        f'Tell a short story where a village show is almost ruined by {spec.hindrance}, but {spec.caution} helps save the day.',
        f'Write a gentle cautionary story in which a young helper remembers that {spec.caution.lower()}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    spec = world.facts["spec"]
    aid = world.facts["aid"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {place.name}?",
            answer=f"{hero.id} wanted to {spec.verb} with the village crowd.",
        ),
        QAItem(
            question=f"What hindrance caused trouble for the {spec.name}?",
            answer=f"The trouble came from {spec.hindrance}, which was the hindrance that could spoil the day.",
        ),
        QAItem(
            question=f"How did {hero.id} and {elder.label} fix the problem?",
            answer=f"They used {aid.label} and remembered that {spec.caution}. That kept the {spec.name} safe.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The {spec.name} still happened, but in a safer way, and the danger was no longer in charge.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "spectacle": [
        QAItem(
            question="What is a spectacle?",
            answer="A spectacle is a show that people gather to watch because it is lively, bright, or exciting.",
        )
    ],
    "warning": [
        QAItem(
            question="Why do people give warnings before a risky job?",
            answer="Warnings help people avoid harm by telling them what could go wrong before they begin.",
        )
    ],
    "fire": [
        QAItem(
            question="Why should water be kept near fire?",
            answer="Water can help stop a fire from spreading if sparks or flame get too close to something dry.",
        )
    ],
    "music": [
        QAItem(
            question="Why should an old drum strap be checked?",
            answer="An old strap can snap or slip, and then the drum may not stay steady while someone plays it.",
        )
    ],
    "earth": [
        QAItem(
            question="Why do flat stones help under a pole?",
            answer="Flat stones make the ground firmer so a pole is less likely to sink or tilt.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    spec = world.facts["spec"]
    out = list(WORLD_KNOWLEDGE["spectacle"])
    out.append(WORLD_KNOWLEDGE["warning"][0])
    if "fire" in spec.tags:
        out.append(WORLD_KNOWLEDGE["fire"][0])
    if "music" in spec.tags:
        out.append(WORLD_KNOWLEDGE["music"][0])
    if "earth" in spec.tags:
        out.append(WORLD_KNOWLEDGE["earth"][0])
    return out


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
    lines.append("== (3) World knowledge ==")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld of spectacle, hindrance, and caution.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--spectacle", choices=SPECTACLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.spectacle:
        combos = [c for c in combos if c[1] == args.spectacle]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, spectacle, _ = rng.choice(combos)
    spec = SPECTACLES[spectacle]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHARACTER_NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, spectacle=spectacle, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], SPECTACLES[params.spectacle], params.name, params.gender, params.parent, params.trait)
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
    StoryParams(place="village_green", spectacle="lanterns", name="Mira", gender="girl", parent="mother", trait="careful"),
    StoryParams(place="barn_yard", spectacle="drum", name="Theo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="river_path", spectacle="maypole", name="Lena", gender="girl", parent="mother", trait="bold"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
            header = f"### {p.name}: {p.spectacle} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
