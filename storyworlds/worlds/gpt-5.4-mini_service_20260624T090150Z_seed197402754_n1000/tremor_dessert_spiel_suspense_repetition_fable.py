#!/usr/bin/env python3
"""
A small storyworld: a fable-like tale about a tremor, a dessert, and a spiel.

The world is intentionally tiny and constraint-checked. A young creature wants a
dessert, a small tremor makes the treat wobble, and a wise elder gives a gentle
spiel about patience. The story turns on suspense and repetition, then resolves
through a careful, believable change in the world state.
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Dessert:
    id: str
    label: str
    phrase: str
    type: str
    fragile: bool = True


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.tremor_level: float = 0.0
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.tremor_level = self.tremor_level
        return clone


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    if world.tremor_level < THRESHOLD:
        return out
    for dessert in world.entities.values():
        if dessert.kind != "dessert":
            continue
        if dessert.meters.get("wobble", 0.0) >= THRESHOLD:
            continue
        sig = ("wobble", dessert.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        dessert.meters["wobble"] = dessert.meters.get("wobble", 0.0) + 1.0
        out.append(f"The {dessert.label} wobbled on its plate.")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for dessert in world.entities.values():
        if dessert.kind != "dessert":
            continue
        if dessert.meters.get("wobble", 0.0) < THRESHOLD:
            continue
        if dessert.meters.get("steady", 0.0) >= THRESHOLD:
            continue
        sig = ("spill", dessert.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        dessert.meters["mess"] = dessert.meters.get("mess", 0.0) + 1.0
        out.append(f"A little spill would follow if no one steadied it.")
    return out


CAUSAL_RULES = [
    _r_wobble,
    _r_spill,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_spill(world: World, hero: Entity, dessert_id: str) -> bool:
    sim = world.copy()
    sim.tremor_level = 1.0
    sim.get(dessert_id).meters["wobble"] = 0.0
    propagate(sim, narrate=False)
    dessert = sim.get(dessert_id)
    return dessert.meters.get("mess", 0.0) >= THRESHOLD


def setting_detail(setting: Setting) -> str:
    if setting.indoor:
        return f"{setting.place.capitalize()} was quiet, with a small table near the window."
    return f"{setting.place.capitalize()} sat in the warm afternoon like a safe little stage."


def select_gear() -> Gear:
    return Gear(
        id="steady_board",
        label="a steady board",
        prep="place the dessert on a steady board",
        tail="moved the dessert onto the steady board",
        protects={"wobble"},
    )


def tell(world: World, hero: Entity, elder: Entity, dessert: Entity) -> World:
    world.say(
        f"{hero.id} was a small, bright-eyed {hero.type} who loved sweet things and careful lessons."
    )
    world.say(
        f"{hero.id} loved the dessert, and the dessert loved to sit high and wait."
    )
    world.say(
        f"The elder had a gentle spiel: 'Slow paws, slow breaths, and a steady heart make a safer day.'"
    )
    world.para()
    world.say(setting_detail(world.setting))
    world.say(
        f"One day, a tremor came through {world.setting.place.lower()}. "
        f"It was only a little tremor, but it made the dessert tremble too."
    )
    world.tremor_level = 1.0
    dessert.meters["wobble"] = 1.0
    propagate(world, narrate=True)
    world.say(
        f"{hero.id} wanted the dessert right away, but the wobble kept going: wobble, wobble, wobble."
    )
    world.say(
        f"The elder repeated the spiel, not because the child could not hear it, but because the child needed to feel it."
    )
    world.para()
    if predict_spill(world, hero, dessert.id):
        gear = select_gear()
        world.say(
            f"Then the elder smiled and said, 'We can still have it, if we {gear.prep} first.'"
        )
        dessert.meters["steady"] = 1.0
        dessert.meters["mess"] = 0.0
        world.say(
            f"{hero.id} listened. The two of them {gear.tail}, and the wobble could not spoil the sweet treat."
        )
        world.say(
            f"At last, {hero.id} ate the dessert slowly, and the little tremor became only a memory."
        )
        world.facts.update(resolved=True, gear=gear)
    else:
        raise StoryError("No reasonable resolution: the dessert never truly risked spilling.")
    world.facts.update(hero=hero, elder=elder, dessert=dessert, setting=world.setting)
    return world


SETTINGS = {
    "cottage": Setting(place="the cottage", indoor=True, affords={"tremor"}),
    "garden": Setting(place="the garden", indoor=False, affords={"tremor"}),
}

DESSERTS = {
    "custard": Dessert(id="custard", label="custard cup", phrase="a sweet custard cup", type="custard"),
    "pie": Dessert(id="pie", label="berry pie", phrase="a warm berry pie", type="pie"),
}

NAMES = ["Milo", "Tessa", "Pip", "Luna", "Jun", "Nora"]
ELDERS = ["grandmother", "grandfather", "owl", "tortoise"]
TRAITS = ["curious", "gentle", "patient", "spry"]


@dataclass
class StoryParams:
    place: str
    dessert: str
    name: str
    elder: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(place, dessert) for place in SETTINGS for dessert in DESSERTS]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if s.indoor:
            lines.append(asp.fact("indoor", place))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", place, a))
    for did, d in DESSERTS.items():
        lines.append(asp.fact("dessert", did))
        lines.append(asp.fact("fragile", did))
    lines.append(asp.fact("tremor", "tremor"))
    return "\n".join(lines)


ASP_RULES = r"""
risk(Place, D) :- affords(Place, tremor), dessert(D), fragile(D).
fix(Place, D) :- risk(Place, D), place(P), board(P).
valid(Place, D) :- risk(Place, D), fix(Place, D).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about tremor, dessert, and a spiel.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--dessert", choices=DESSERTS)
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDERS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.dessert is None or c[1] == args.dessert)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, dessert = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        dessert=dessert,
        name=args.name or rng.choice(NAMES),
        elder=args.elder or rng.choice(ELDERS),
        trait=args.trait or rng.choice(TRAITS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, dessert = f["hero"], f["dessert"]
    return [
        f'Write a short fable for a young child about a {hero.pronoun("possessive")} dessert and a small tremor.',
        f"Tell a suspenseful little story where {hero.id} wants the {dessert.label} right away, but a wise {f['elder']} gives a spiel about patience.",
        "Write a story that uses repetition to show a wobbling dessert becoming safe again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, dessert = f["hero"], f["elder"], f["dessert"]
    return [
        QAItem(
            question=f"What did {hero.id} want when the tremor started?",
            answer=f"{hero.id} wanted the {dessert.label}, but it was wobbling and needed care first.",
        ),
        QAItem(
            question=f"Why did the {elder} give a spiel about patience?",
            answer=f"The {elder} gave a spiel because the tremor made the dessert wobble, and rushing could have made a spill.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{hero.id} listened, the dessert was steadied, and the sweet treat stayed safe at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a tremor?", answer="A tremor is a small shaking of the ground or a room."),
        QAItem(question="What is a dessert?", answer="A dessert is a sweet food eaten after a meal."),
        QAItem(question="What is a spiel?", answer="A spiel is a long little speech that explains something."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    lines.append(f"  tremor_level={world.tremor_level}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name[0] < "N" else "boy"))
    elder = world.add(Entity(id="Elder", kind="character", type=params.elder, label=params.elder))
    dessert = world.add(Entity(id=params.dessert, kind="dessert", type=DESSERTS[params.dessert].type,
                               label=DESSERTS[params.dessert].label, phrase=DESSERTS[params.dessert].phrase))
    hero.traits = [params.trait, "small"]
    tell(world, hero, elder, dessert)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for place, dessert in asp_valid_combos():
            print(f"  {place} {dessert}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for dessert in DESSERTS:
                params = StoryParams(place=place, dessert=dessert, name="Milo", elder="owl", trait="curious")
                params.seed = base_seed
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
