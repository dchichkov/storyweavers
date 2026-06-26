#!/usr/bin/env python3
"""
A small ghost-story world built around a foreshadowed fudgecicle mishap.

Seed premise:
- A child wants a moonlit view from a spooky place.
- A fudgecicle can drip and endanger something fragile.
- Tiny warnings, flickers, and creaks foreshadow the problem before the turn.
- The ending resolves the danger with a careful, child-friendly fix.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    view: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting):
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

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "attic": Setting(place="the attic window", view="moonlit rooftops", indoors=True, affords={"view"}),
    "porch": Setting(place="the front porch", view="sleepy street", indoors=False, affords={"view"}),
    "garden": Setting(place="the night garden", view="silver moonflowers", indoors=False, affords={"view"}),
}

FORESHADOWS = [
    "The candle flame gave a tiny wobble.",
    "A cold draft slipped under the door and tugged at the curtains.",
    "Somewhere below, an old floorboard gave a soft creak.",
]

ACTIVITIES = {
    "view": Thing(
        id="view",
        label="a moonlit view",
        phrase="a spooky moonlit view",
        type="view",
        region="hands",
        mess="dripped",
        soil="sticky",
        zone={"hands", "torso"},
        keyword="view",
        tags={"view", "night", "ghost"},
    ),
    "ghostwalk": Thing(
        id="ghostwalk",
        label="a ghost walk",
        phrase="a quiet ghost walk",
        type="walk",
        region="feet",
        mess="cold",
        soil="chilly",
        zone={"feet", "hands"},
        keyword="ghost",
        tags={"ghost", "night"},
    ),
}

PRIZES = {
    "fudgecicle": Thing(
        id="fudgecicle",
        label="fudgecicle",
        phrase="a chocolate fudgecicle",
        type="snack",
        region="hands",
        mess="sticky",
        soil="melted and sticky",
        zone={"hands", "torso"},
        keyword="fudgecicle",
        tags={"fudgecicle", "sticky", "cold"},
    ),
}

GEAR = [
    Gear(
        id="plate",
        label="a little tin plate",
        covers={"hands"},
        guards={"sticky"},
        prep="put the fudgecicle on a little tin plate",
        tail="set the plate on the sill",
    ),
    Gear(
        id="napkin",
        label="a folded napkin",
        covers={"hands"},
        guards={"sticky"},
        prep="wrap a folded napkin around the stick",
        tail="kept the treat wrapped as they looked out",
    ),
]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    sidekick: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "June"]
BOY_NAMES = ["Owen", "Eli", "Jude", "Finn", "Theo"]
TRAITS = ["curious", "brave", "quiet", "careful", "sensitive"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with foreshadowing and a fudgecicle.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick", choices=["ghost", "grandma ghost"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                out.append((place, act, prize))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    sidekick = args.sidekick or rng.choice(["ghost", "grandma ghost"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, sidekick=sidekick, trait=trait)


def _do_view(world: World, actor: Entity, act: Thing, narrate: bool = True) -> None:
    world.zone = set(act.zone)
    actor.memes["wonder"] = actor.memes.get("wonder", 0) + 1
    if narrate:
        world.say(f"{actor.id} leaned in to {act.keyword} at the window.")


def predict_mess(world: World, actor: Entity, prize_id: str) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters["sticky"] = 1.0
    sim.zone = {"hands", "torso"}
    prize = sim.get(prize_id)
    prize.meters["sticky"] = 1.0
    return prize.meters["sticky"] >= THRESHOLD


def foreshadow(world: World) -> None:
    for line in FORESHADOWS:
        world.say(line)


def offer_fix(world: World, hero: Entity, prize: Entity) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and prize.meters.get("sticky", 0) < THRESHOLD:
            continue
        if "sticky" in gear.guards:
            ent = world.add(Entity(id=gear.id, type="thing", label=gear.label, protective=True, covers=set(gear.covers)))
            ent.worn_by = hero.id
            world.say(f"{hero.id}'s sidekick pointed to {gear.label} and whispered a simple idea.")
            world.say(f'They could {gear.prep}, and then {gear.tail}.')
            return gear
    return None


def tell(setting: Setting, act: Thing, prize_cfg: Thing, hero_name: str, sidekick: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl" if hero_name in GIRL_NAMES else "boy", traits=["little", trait]))
    ghost = world.add(Entity(id=sidekick, kind="character", type="ghost"))
    prize = world.add(Entity(id=prize_cfg.id, type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, region=prize_cfg.region))
    lamp = world.add(Entity(id="lamp", type="thing", label="an old lamp", protective=False))
    lamp.meters["flicker"] = 0.0

    world.say(f"{hero.id} found {hero.pronoun('possessive')} way to {setting.place} with a small {ghost.id} floating near the window.")
    world.say(f"{hero.id} wanted to {act.keyword} because the {setting.view} looked like a picture made of silver.")
    world.say(f"{hero.id} was carrying {hero.pronoun('possessive')} {prize.label}, and the sweet cold smell made the room feel cozy.")
    world.para()

    foreshadow(world)
    world.say(f"The last clue was the {prize.label}; it could melt and endanger the lamp if no one watched it closely.")
    world.say(f"{ghost.id} looked at the treat, then at the lamp, as if it already knew trouble was coming.")
    world.para()

    _do_view(world, hero, act)
    hero.meters["sticky"] = 1.0
    prize.meters["sticky"] = 1.0
    lamp.meters["flicker"] = 1.0
    world.say(f"Just then, a warm drip slid down the stick, and the lamp gave a nervous flicker.")
    world.say(f"{hero.id} gasped, because the fudgecicle might smear the sill and make a mess near the flame.")
    world.say(f"{ghost.id} raised one pale finger and pointed to a safe fix before the drip could spread.")

    world.para()
    gear = offer_fix(world, hero, prize)
    if gear:
        hero.meters["sticky"] = 0.0
        prize.meters["sticky"] = 0.0
        lamp.meters["flicker"] = 0.0
        hero.memes["relief"] = hero.memes.get("relief", 0) + 1
        world.say(f"So {hero.id} did it carefully, and the fudgecicle rested safely on the sill.")
        world.say(f"After that, they could look out at the {setting.view} without worrying about the lamp.")
        world.say(f"The room felt quiet and brave, and the ghost smiled like a friend in the dark.")

    world.facts.update(hero=hero, ghost=ghost, prize=prize, setting=setting, activity=act, gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short ghost story for young children that includes the word "fudgecicle" and the word "view".',
        f"Tell a spooky-but-gentle story where {hero.id} wants to {f['activity'].keyword} and a ghost helps keep a fudgecicle from causing trouble.",
        f"Write a foreshadowed story with a moonlit view, a cold treat, and a careful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ghost, prize, setting, act = f["hero"], f["ghost"], f["prize"], f["setting"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {setting.place}?",
            answer=f"{hero.id} wanted to {act.keyword} so {hero.pronoun('possessive')} could look at the {setting.view}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} watch the fudgecicle?",
            answer=f"The little ghost named {ghost.id} helped keep an eye on the fudgecicle and showed a safer way.",
        ),
        QAItem(
            question=f"Why was the fudgecicle a problem?",
            answer="It was cold and sweet, so it could melt, drip, and endanger the lamp if nobody handled it carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives small clues before something important happens, like a creak or a flicker that hints at trouble ahead.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale about a spooky person or place, but it can still be gentle, curious, and safe for children.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
activity(view).
prize(fudgecicle).
setting(attic).
foreshadow(creak).
foreshadow(flicker).

valid_story(P,A,R) :- setting(P), activity(A), prize(R).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", k) for k in SETTINGS]
    lines += [asp.fact("activity", k) for k in ACTIVITIES]
    lines += [asp.fact("prize", k) for k in PRIZES]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if asp_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


CURATED = [
    StoryParams(place="attic", activity="view", prize="fudgecicle", name="Mina", sidekick="ghost", trait="curious"),
    StoryParams(place="porch", activity="view", prize="fudgecicle", name="Owen", sidekick="ghost", trait="careful"),
    StoryParams(place="garden", activity="view", prize="fudgecicle", name="Ivy", sidekick="grandma ghost", trait="quiet"),
]


def explain_rejection() -> str:
    return "(No story: this world only tells gentle ghost stories about a view and a fudgecicle.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.sidekick, params.trait)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
