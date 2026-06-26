#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gasket_gruyere_zoo_misunderstanding_moral_value_fairy.py
==============================================================================================================

A small fairy-tale storyworld set in a zoo, built around a misunderstanding
and a moral-value turn. The seed words are "gasket" and "gruyere".

Premise:
- A young caretaker visits the zoo with a precious wedge of gruyere.
- A leaking fountain needs a gasket, and the leak makes the path wet and
  troublesome.
- A gentle misunderstanding arises when an animal thinks the cheese is meant
  for the fountain repair.

Turn:
- The keeper explains the difference between the gasket and the gruyere.
- The characters learn to ask before taking, and to use the right thing for
  the right job.

Resolution:
- The fountain is fixed with the gasket.
- The gruyere is shared at a picnic only after asking kindly.
- The ending image proves the change: dry stones, happy faces, and a wiser
  zoo.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "keeper"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the zoo"
    name: str = "the zoo"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if actor.meters.get("wet", 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.region not in world.zone:
                    continue
                sig = ("soak", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["wet"] = item.meters.get("wet", 0.0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                changed = True
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got wet.")
        for item in world.entities.values():
            if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
                continue
            sig = ("work", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            carer = world.get(item.caretaker)
            carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
            changed = True
            out.append(f"That would mean more work for {carer.label}.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_leak(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**vars(v)) for k, v in world.entities.items()}
    sim.fired = set(world.fired)
    sim.zone = set(activity.zone)
    sim_actor = sim.get(actor.id)
    sim_actor.meters["wet"] = sim_actor.meters.get("wet", 0.0) + 1
    propagate(sim, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("wet", 0.0) >= THRESHOLD)}


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Caretaker", kind="character", type=parent_type, label="the keeper"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id,
                             caretaker=parent.id, region=prize_cfg.region,
                             plural=prize_cfg.plural))
    gasket = world.add(Entity(id="Gasket", type="thing", label="gasket", phrase="a small rubber gasket"))
    cheese = world.add(Entity(id="Cheese", type="thing", label="gruyere", phrase="a wedge of gruyere"))

    world.facts.update(hero=hero, parent=parent, prize=prize, gasket=gasket, cheese=cheese,
                       activity=activity, setting=setting, trait=trait)

    world.say(f"Once upon a time, {hero.id} was a little {trait} {hero.type} who loved the zoo.")
    world.say(f"{hero.id} carried {hero.pronoun('possessive')} {cheese.label} in a basket and admired the bright cages and tall trees.")
    world.say(f"Near the turtle pond, a drip-drip sound came from the fountain, and the keeper frowned at the broken seal.")
    world.para()

    world.say(f"{hero.id} wanted to {activity.verb}, but the wet stones made the path slippery.")
    world.say(f'The keeper said, "We need the {gasket.label} to stop the leak, not the {cheese.label}."')
    world.say(f"Just then, a curious animal peeked out and misunderstood the shiny smell of the {cheese.label}.")
    world.say(f"It thought the cheese was the special fix and nosed closer, which made {hero.id} gasp.")
    world.para()

    world.say(f'The keeper smiled and said, "Ask first, and use the right thing for the right job."')
    world.say(f"{hero.id} nodded, handed over the {gasket.label}, and saved the {cheese.label} for the picnic.")
    world.say(f"The fountain became still and dry, and the zoo path looked safe again.")
    world.say(f"At last, {hero.id} shared the {cheese.label} kindly with the keeper after asking, and everyone laughed softly beside the quiet pond.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f'Write a fairy tale set in a zoo where a child named {hero.id} brings a gasket and a wedge of gruyere.',
        f"Tell a gentle story about {hero.id} at the zoo, where a misunderstanding about {f['cheese'].label} leads to a moral lesson.",
        f"Write a child-friendly fairy tale where the right fix is a {f['gasket'].label}, not {f['cheese'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who was the fairy tale about?",
            answer=f"It was about {hero.id}, a little {trait} {hero.type}, and the keeper at the zoo.",
        ),
        QAItem(
            question=f"What was wrong at the zoo?",
            answer=f"The fountain was leaking, so the stones were wet and slippery near the turtle pond.",
        ),
        QAItem(
            question=f"What did the keeper say was needed to stop the leak?",
            answer=f"The keeper said they needed the gasket to stop the leak, not the gruyere.",
        ),
        QAItem(
            question=f"What misunderstanding happened in the middle of the story?",
            answer=f"A curious animal misunderstood the smell and thought the gruyere was the special fix.",
        ),
        QAItem(
            question=f"What moral did the story teach?",
            answer=f"It taught that it is wise to ask first and use the right thing for the right job.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The gasket fixed the fountain, the path dried, and the gruyere was saved for a kind picnic.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gasket?",
            answer="A gasket is a ring or seal that helps stop leaks where two parts meet tightly.",
        ),
        QAItem(
            question="What is gruyere?",
            answer="Gruyere is a kind of cheese with a rich, nutty taste.",
        ),
        QAItem(
            question="Why should someone ask before taking something?",
            answer="Asking first shows respect and helps make sure the thing belongs to the right person or is safe to use.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world Q&A ==")
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "zoo": Setting(place="the zoo", name="the zoo", affords={"fix", "picnic"}),
}

ACTIVITIES = {
    "fix": Activity(
        id="fix",
        verb="mend the fountain",
        gerund="mending the fountain",
        rush="run to the broken seal",
        mess="wet",
        soil="wet and slippery",
        zone={"feet"},
        keyword="gasket",
        tags={"gasket", "misunderstanding", "moral"},
    ),
}

PRIZES = {
    "gruyere": Prize(
        label="gruyere",
        phrase="a wedge of gruyere",
        type="cheese",
        region="feet",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="gasket",
        label="gasket",
        covers={"feet"},
        guards={"wet"},
        prep="use the gasket on the fountain",
        tail="set the gasket in place and stopped the leak",
    ),
]

GIRL_NAMES = ["Mina", "Lena", "Ari", "Nora"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Jon"]
TRAITS = ["kind", "curious", "brave", "gentle"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale zoo storyworld with a misunderstanding and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "keeper"])
    ap.add_argument("--name")
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
    place = args.place or "zoo"
    activity = args.activity or "fix"
    prize = args.prize or "gruyere"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["keeper", "mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.parent, params.trait)
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


ASP_RULES = r"""
place(zoo).
activity(fix).
prize(gruyere).
gasket(gasket).

needs_fix(fix).
has_moral(moral).
has_misunderstanding(misunderstanding).

valid_story(Place, Act, Prize) :- place(Place), activity(Act), prize(Prize).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("place", "zoo"), asp.fact("activity", "fix"), asp.fact("prize", "gruyere"), asp.fact("gasket", "gasket")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    py = [("zoo", "fix", "gruyere")]
    if atoms == py:
        print("OK: ASP matches Python story gate (1 combo).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  ASP:", atoms)
    print("  PY :", py)
    return 1


CURATED = [
    StoryParams(place="zoo", activity="fix", prize="gruyere", name="Mina", gender="girl", parent="keeper", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
