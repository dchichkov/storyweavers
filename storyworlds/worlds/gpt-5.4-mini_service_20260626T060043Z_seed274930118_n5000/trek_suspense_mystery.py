#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/trek_suspense_mystery.py
======================================================================================================

A standalone story world for a small trek-suspense-mystery domain.

Premise:
- A child and a guide take a trek along a narrow forest path.
- A useful object goes missing or seems wrong.
- The child notices clues, the guide worries, and the pair solve the mystery by following the trail.
- The ending should prove the change: the missing thing is found, the trek continues, and the mood shifts from uneasy to relieved.

This file is self-contained and uses the shared result containers from storyworlds/results.py.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    trail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Trek:
    id: str
    verb: str
    gerund: str
    clue: str
    hazard: str
    tension: str
    location: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    kind: str
    risk: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    helper: str
    covers: set[str]
    guards: set[str]
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trail_clue: str = ""
        self.mystery_solved: bool = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.trail_clue = self.trail_clue
        clone.mystery_solved = self.mystery_solved
        return clone


SETTINGS = {
    "forest": Setting(place="the forest", trail="a narrow forest trail", affords={"ridge", "bridge", "cave"}),
    "hills": Setting(place="the hills", trail="a winding hill path", affords={"ridge", "cave"}),
    "lake": Setting(place="the lake shore", trail="a sandy path by the water", affords={"bridge", "shore"}),
}

TREKS = {
    "ridge": Trek(
        id="ridge",
        verb="trek to the ridge",
        gerund="trekking up the ridge",
        clue="a bent fern pointing uphill",
        hazard="mist",
        tension="the path seemed to vanish in the fog",
        location="the ridge",
        tags={"forest", "mist"},
    ),
    "bridge": Trek(
        id="bridge",
        verb="trek to the old bridge",
        gerund="crossing the old bridge",
        clue="mud on the stones by the creek",
        hazard="water",
        tension="the planks sounded hollow underfoot",
        location="the old bridge",
        tags={"water", "creek"},
    ),
    "cave": Trek(
        id="cave",
        verb="trek to the cave mouth",
        gerund="walking toward the cave mouth",
        clue="a cool draft drifting from the rocks",
        hazard="dark",
        tension="the cave entrance looked black as ink",
        location="the cave mouth",
        tags={"dark", "rocks"},
    ),
    "shore": Trek(
        id="shore",
        verb="trek to the shore",
        gerund="walking along the shore",
        clue="shells lined up like tiny white arrows",
        hazard="wind",
        tension="the wind kept whispering through the reeds",
        location="the shore",
        tags={"water", "wind"},
    ),
}

PRIZES = {
    "lantern": Prize(
        label="lantern",
        phrase="a little brass lantern",
        type="lantern",
        kind="lantern",
        risk="dark",
        region="hand",
    ),
    "map": Prize(
        label="map",
        phrase="a folded trail map",
        type="map",
        kind="map",
        risk="lost",
        region="hand",
    ),
    "compass": Prize(
        label="compass",
        phrase="a small compass in a leather case",
        type="compass",
        kind="compass",
        risk="lost",
        region="pocket",
    ),
    "snack": Prize(
        label="snack",
        phrase="a pouch of sweet berry crackers",
        type="snack",
        kind="snack",
        risk="hungry",
        region="pack",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="lamp_case",
        label="a padded case",
        helper="keep the lantern safe",
        covers={"hand"},
        guards={"dark"},
        tags={"lantern"},
    ),
    Gear(
        id="map_tube",
        label="a waterproof tube",
        helper="keep the map dry",
        covers={"hand"},
        guards={"lost"},
        tags={"map"},
    ),
    Gear(
        id="pocket_clip",
        label="a pocket clip",
        helper="keep the compass from slipping away",
        covers={"pocket"},
        guards={"lost"},
        tags={"compass"},
    ),
    Gear(
        id="snack_tin",
        label="a tin box",
        helper="keep the crackers from getting crushed",
        covers={"pack"},
        guards={"hungry"},
        tags={"snack"},
    ),
]

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ivy", "Rose", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Eli", "Theo", "Ben", "Max"]
GUIDE_NAMES = ["Grandma", "Uncle Rowan", "Aunt Mira", "Mr. Hale"]


@dataclass
class StoryParams:
    place: str
    trek: str
    prize: str
    name: str
    gender: str
    guide: str
    seed: Optional[int] = None


def prize_at_risk(trek: Trek, prize: Prize) -> bool:
    return trek.hazard == prize.risk or prize.kind in trek.tags


def select_gear(trek: Trek, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.kind in gear.tags and trek.hazard in gear.guards:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for trek_id in setting.affords:
            trek = TREKS[trek_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(trek, prize) and select_gear(trek, prize):
                    out.append((place, trek_id, prize_id))
    return out


def introduce(world: World, hero: Entity, guide: Entity, trek: Trek, prize: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved mysteries and quiet paths.")
    world.say(f"One day, {hero.id} and {guide.id} set out on {trek.gerund}, with {hero.pronoun('possessive')} {prize.label} packed close by.")


def build_mood(world: World, hero: Entity, trek: Trek) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
    world.say(f"The air felt still, and {trek.tension}.")
    world.say(f"{hero.id} noticed {trek.clue} and wondered what it meant.")


def prediction(world: World, hero: Entity, trek: Trek, prize: Entity) -> dict:
    sim = world.copy()
    sim.facts["spooky"] = True
    sim.get(hero.id).memes["suspense"] = sim.get(hero.id).memes.get("suspense", 0.0) + 1
    if prize.meters.get("safe", 0.0) < THRESHOLD:
        sim.facts["prize_missing"] = True
    return {
        "risk": prize_at_risk(trek, PRIZES[prize.type]),
        "missing": bool(sim.facts.get("prize_missing")),
    }


def suspect_loss(world: World, hero: Entity, guide: Entity, trek: Trek, prize: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(f"Then {hero.id} reached for {hero.pronoun('possessive')} {prize.label} and froze.")
    world.say(f"It was not where {hero.id} expected it to be.")
    world.say(f"{guide.id} looked around slowly, as if the trail itself might be hiding a clue.")


def find_clue(world: World, hero: Entity, guide: Entity, trek: Trek, prize: Entity) -> None:
    world.say(f"{hero.id} bent down and studied the ground.")
    world.say(f"Near the path, there was {trek.clue}.")
    world.say(f"That small clue matched the shape of the missing thing, so they followed it carefully.")


def resolve(world: World, hero: Entity, guide: Entity, trek: Trek, prize: Entity, gear: Optional[Gear]) -> None:
    prize.meters["safe"] = prize.meters.get("safe", 0.0) + 1
    hero.memes["suspense"] = 0.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.mystery_solved = True
    if gear is not None:
        world.say(f"At last, they found {hero.pronoun('possessive')} {prize.label} tucked safely beside the trail, and {gear.label} helped keep it in place after that.")
    else:
        world.say(f"At last, they found {hero.pronoun('possessive')} {prize.label} tucked safely beside the trail.")
    world.say(f"{hero.id} let out a small breath and smiled.")
    world.say(f"The trek went on, and {trek.location} no longer felt mysterious in a scary way; it felt friendly instead.")


def tell(setting: Setting, trek: Trek, prize_cfg: Prize, hero_name: str, hero_type: str, guide_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    guide = world.add(Entity(id=guide_name, kind="character", type="adult", label=guide_name))
    prize = world.add(Entity(
        id=prize_cfg.kind,
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=guide.id,
        plural=prize_cfg.plural,
    ))
    prize.meters["safe"] = 1.0

    introduce(world, hero, guide, trek, prize)
    world.para()
    build_mood(world, hero, trek)
    suspect_loss(world, hero, guide, trek, prize)
    find_clue(world, hero, guide, trek, prize)

    world.para()
    gear = select_gear(trek, prize_cfg)
    resolve(world, hero, guide, trek, prize, gear)

    world.facts.update(hero=hero, guide=guide, prize=prize, trek=trek, setting=setting, gear=gear)
    return world


KNOWLEDGE = {
    "lantern": [("What is a lantern?", "A lantern is a light that you can carry by hand so you can see in the dark.")],
    "map": [("What is a map?", "A map is a drawing that shows places and helps you find your way.")],
    "compass": [("What does a compass do?", "A compass helps you know which way is north so you can choose a direction.")],
    "snack": [("Why do hikers bring snacks?", "Hikers bring snacks so they have energy for a long walk.")],
    "trail": [("What is a trail?", "A trail is a path through nature that people can follow when they walk.")],
    "mist": [("What is mist?", "Mist is tiny drops of water in the air that make the world look hazy.")],
    "dark": [("Why can dark places feel spooky?", "Dark places can feel spooky because it is harder to see what is around you.")],
    "water": [("Why do people watch their step near water?", "People watch their step near water because the ground can be slippery.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    prize = f["prize"]
    trek = f["trek"]
    return [
        f'Write a short mystery story for a child about a trek on {world.setting.place} with the word "trek".',
        f"Tell a suspenseful story where {hero.id} and {guide.id} follow a clue on {trek.location} and worry about {hero.pronoun('possessive')} {prize.label}.",
        f"Write a gentle mystery where something small seems missing on a walk, then gets found before the trek ends.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    prize: Entity = f["prize"]
    trek: Trek = f["trek"]
    setting: Setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who went on the trek in the story?",
            answer=f"{hero.id} and {guide.id} went on {trek.gerund} together through {setting.place}.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice while walking?",
            answer=f"{hero.id} noticed {trek.clue}, which helped point the way forward.",
        ),
        QAItem(
            question=f"What seemed to be wrong with {hero.id}'s {prize.label}?",
            answer=f"{hero.id} thought {hero.pronoun('possessive')} {prize.label} was missing for a moment, which made the walk feel tense.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"They found {hero.pronoun('possessive')} {prize.label}, the mystery was solved, and the trek kept going in a calm way.",
        ),
    ]
    if f.get("gear") is not None:
        gear: Gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did {gear.label} help during the trek?",
                answer=f"{gear.label} helped keep the {prize.label} safe so the pair could finish the walk without losing it again.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out: list[QAItem] = []
    for tag in sorted({f["prize"].kind, f["trek"].hazard, "trail"}):
        if tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.plural:
            bits.append("plural=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  mystery_solved={world.mystery_solved}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="forest", trek="ridge", prize="lantern", name="Mia", gender="girl", guide="Grandma"),
    StoryParams(place="forest", trek="bridge", prize="map", name="Leo", gender="boy", guide="Uncle Rowan"),
    StoryParams(place="hills", trek="cave", prize="compass", name="Nora", gender="girl", guide="Aunt Mira"),
    StoryParams(place="lake", trek="shore", prize="snack", name="Finn", gender="boy", guide="Mr. Hale"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: trek, suspense, and a child-friendly mystery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trek", choices=TREKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=GUIDE_NAMES)
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
    if args.trek and args.prize:
        trek = TREKS[args.trek]
        prize = PRIZES[args.prize]
        if not prize_at_risk(trek, prize) or select_gear(trek, prize) is None:
            raise StoryError(f"(No story: {trek.gerund} does not make {prize.label} a reasonable mystery.)")

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.trek is None or c[1] == args.trek)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, trek_id, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(GUIDE_NAMES)
    return StoryParams(place=place, trek=trek_id, prize=prize_id, name=name, gender=gender, guide=guide)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TREKS[params.trek], PRIZES[params.prize], params.name, params.gender, params.guide)
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
prize_at_risk(T, P) :- hazard(T, H), risk(P, H).
protects(G, T, P) :- gear(G), prize_at_risk(T, P), guards(G, H), hazard(T, H), covers(G, R), region(P, R).
has_fix(T, P) :- protects(_, T, P).
valid(Place, Trek, Prize) :- affords(Place, Trek), prize_at_risk(Trek, Prize), has_fix(Trek, Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for t in sorted(setting.affords):
            lines.append(asp.fact("affords", place, t))
    for tid, trek in TREKS.items():
        lines.append(asp.fact("trek", tid))
        lines.append(asp.fact("hazard", tid, trek.hazard))
        for tag in sorted(trek.tags):
            lines.append(asp.fact("tag", tid, tag))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("risk", pid, prize.risk))
        lines.append(asp.fact("region", pid, prize.region))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for g in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, g))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_combos_asp())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: trek={p.trek} prize={p.prize} place={p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
