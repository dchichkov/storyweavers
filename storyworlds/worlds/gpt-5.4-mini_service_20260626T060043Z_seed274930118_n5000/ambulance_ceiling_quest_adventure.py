#!/usr/bin/env python3
"""
storyworlds/worlds/ambulance_ceiling_quest_adventure.py
======================================================

A small Adventure-style storyworld about a brave quest, a low ceiling,
and an ambulance that must find a clever way through.

Premise:
- A child or young adventurer wants to complete a quest with an ambulance.
- The ambulance is taller than the ceiling in one place.
- A warning, a near-miss, and a careful change of plan create the turn.
- The ending proves the quest succeeded in a safer, smarter way.

This file is self-contained except for the shared result containers in
storyworlds/results.py and the optional ASP helper in storyworlds/asp.py.
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
    plural: bool = False
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
    indoor: bool = False
    route: str = ""
    ceiling_clearance: float = 0.0
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    goal: str
    keyword: str
    tags: set[str] = field(default_factory=set)
    requires: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    height: float
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    reduces_height_to: float


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def _r_scratch(world: World) -> list[str]:
    out: list[str] = []
    ambulance = next((e for e in world.entities.values() if e.type == "ambulance"), None)
    ceiling = world.entities.get("ceiling")
    if not ambulance or not ceiling:
        return out
    if ambulance.meters.get("height", 0.0) <= ceiling.meters.get("clearance", 0.0):
        return out
    if ("scratch", ambulance.id) in world.fired:
        return out
    world.fired.add(("scratch", ambulance.id))
    ambulance.memes["worry"] = ambulance.memes.get("worry", 0.0) + 1
    out.append("The ambulance's roof nearly brushed the ceiling.")
    return out


def _r_stop(world: World) -> list[str]:
    out: list[str] = []
    ambulance = next((e for e in world.entities.values() if e.type == "ambulance"), None)
    ceiling = world.entities.get("ceiling")
    if not ambulance or not ceiling:
        return out
    if ambulance.meters.get("height", 0.0) <= ceiling.meters.get("clearance", 0.0):
        return out
    if ambulance.memes.get("stuck", 0.0) >= THRESHOLD:
        return out
    ambulance.memes["stuck"] = 1.0
    out.append("The ambulance had to stop before the low ceiling.")
    return out


RULES = [_r_scratch, _r_stop]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def can_fit(world: World, ambulance: Entity) -> bool:
    ceiling = world.entities["ceiling"]
    return ambulance.meters["height"] <= ceiling.meters["clearance"]


def choose_gear(quest: Quest, prize: Prize) -> Optional[Gear]:
    if "fold_mast" in quest.requires and prize.height > 0:
        return GEAR["folding_mast"]
    return None


def tell(setting: Setting, quest: Quest, prize_cfg: Prize,
         hero_name: str = "Maya", hero_type: str = "girl",
         parent_type: str = "father") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, label=hero_name,
        meters={"courage": 1.0}, memes={"wonder": 1.0}
    ))
    parent = world.add(Entity(id="Guide", kind="character", type=parent_type, label="the guide"))

    ambulance = world.add(Entity(
        id="ambulance",
        kind="thing",
        type="ambulance",
        label="ambulance",
        phrase="a shiny little ambulance with a bright light on top",
        owner=hero.id,
        meters={"height": 3.0, "speed": 1.0},
        memes={"pride": 1.0},
    ))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        meters={"height": prize_cfg.height},
        plural=prize_cfg.plural,
    ))
    ceiling = world.add(Entity(
        id="ceiling",
        kind="thing",
        type="ceiling",
        label="ceiling",
        phrase="the low ceiling over the passage",
        meters={"clearance": setting.ceiling_clearance},
    ))

    world.say(
        f"{hero.id} was a brave little {hero.type} who loved adventures and secret quests."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had an ambulance and a mission to reach {quest.goal}."
    )
    world.say(
        f"The prize was {prize.phrase}, and it made the journey feel important."
    )

    world.para()
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label} set out along "
        f"{setting.route} at {setting.place}."
    )
    world.say(
        f"{quest.verb.capitalize()} was the plan, and the little ambulance rolled ahead with a hopeful buzz."
    )

    if not can_fit(world, ambulance):
        world.say(
            f"Then they saw the ceiling. It was too low for the ambulance's tall roof."
        )
        propagate(world, narrate=True)
        world.say(
            f"{hero.id} wanted to rush forward anyway, but {hero.pronoun('possessive')} {parent.label} held up a hand."
        )
        hero.memes["want"] = hero.memes.get("want", 0.0) + 1
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
        world.say(
            f'"Let\'s not scrape the roof," {hero.pronoun("possessive")} {parent.label} said. '
            f'"A quest can be clever, not just fast."'
        )
        gear = choose_gear(quest, prize)
        if gear is None:
            raise StoryError("No safe gear exists for this quest and ceiling height.")
        ambulance.meters["height"] = gear.reduces_height_to
        world.say(
            f"They used {gear.label}, and the ambulance became low enough to pass."
        )
        world.say(
            f"{hero.id} grinned, because the quest could continue without bumping the ceiling."
        )
        world.para()
        world.say(
            f"They went on {quest.rush}, and at last {quest.goal} was reached."
        )
        world.say(
            f"The ambulance rolled through safely, {quest.gerund}, while the ceiling stayed untouched above."
        )
        world.say(
            f"{gear.tail.capitalize()}, and the brave little team finished the day with the prize still safe."
        )
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        hero.memes["victory"] = hero.memes.get("victory", 0.0) + 1
    else:
        world.say(
            f"The ceiling was high enough after all, so the ambulance drove right through."
        )
        world.para()
        world.say(
            f"They kept {quest.gerund} and reached {quest.goal} with the prize still safe."
        )
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1

    world.facts.update(
        hero=hero,
        parent=parent,
        ambulance=ambulance,
        prize=prize,
        ceiling=ceiling,
        quest=quest,
        setting=setting,
        gear=world.facts.get("gear"),
        resolved=ambulance.meters["height"] <= ceiling.meters["clearance"],
    )
    return world


SETTINGS = {
    "garage": Setting(
        place="the garage",
        indoor=True,
        route="the painted lane",
        ceiling_clearance=2.2,
        affords={"garage_quest", "repair_quest"},
    ),
    "tunnel": Setting(
        place="the tunnel",
        indoor=True,
        route="the narrow tunnel path",
        ceiling_clearance=1.8,
        affords={"tunnel_quest"},
    ),
    "museum": Setting(
        place="the old museum hall",
        indoor=True,
        route="the marble corridor",
        ceiling_clearance=2.6,
        affords={"museum_quest"},
    ),
    "station": Setting(
        place="the rescue station",
        indoor=True,
        route="the blue corridor",
        ceiling_clearance=2.0,
        affords={"station_quest"},
    ),
}

QUESTS = {
    "garage_quest": Quest(
        id="garage_quest",
        verb="begin the rescue quest",
        gerund="beginning the rescue quest",
        rush="head down the painted lane",
        goal="the yellow gate",
        keyword="quest",
        tags={"quest", "rescue"},
        requires={"fold_mast"},
    ),
    "tunnel_quest": Quest(
        id="tunnel_quest",
        verb="follow the rescue quest",
        gerund="following the rescue quest",
        rush="dash through the tunnel",
        goal="the lantern door",
        keyword="quest",
        tags={"quest", "tunnel"},
        requires={"fold_mast"},
    ),
    "museum_quest": Quest(
        id="museum_quest",
        verb="take the treasure quest",
        gerund="taking the treasure quest",
        rush="glide along the marble corridor",
        goal="the glass arch",
        keyword="quest",
        tags={"quest", "treasure"},
        requires={"fold_mast"},
    ),
    "station_quest": Quest(
        id="station_quest",
        verb="start the station quest",
        gerund="starting the station quest",
        rush="roll to the far blue door",
        goal="the star map room",
        keyword="quest",
        tags={"quest", "map"},
        requires={"fold_mast"},
    ),
}

PRIZES = {
    "badge": Prize("badge", "a bright rescue badge", "badge", 0.2),
    "map": Prize("map", "a folded star map", "map", 0.1),
    "lantern": Prize("lantern", "a small lantern", "lantern", 0.6),
    "key": Prize("key", "a tiny gold key", "key", 0.1),
}

GEAR = {
    "folding_mast": Gear(
        id="folding_mast",
        label="the folding light mast",
        prep="they folded down the light mast first",
        tail="they folded the light mast again before the next stretch",
        reduces_height_to=1.5,
    )
}

GIRL_NAMES = ["Maya", "Luna", "Nina", "Ivy", "Zara", "Tia"]
BOY_NAMES = ["Leo", "Finn", "Owen", "Jude", "Max", "Theo"]
TRAITS = ["brave", "curious", "cheerful", "bold", "gentle"]


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            for pid in PRIZES:
                out.append((place, qid, pid))
    return out


def explain_rejection(setting: Setting, quest: Quest) -> str:
    return (
        f"(No story: {setting.place} does not support {quest.id}, "
        f"or the ceiling trouble would not create a useful quest.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure-style quest storyworld: an ambulance, a ceiling, and a clever route."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, q, prize = f["hero"], f["quest"], f["prize"]
    return [
        f'Write a short Adventure-style story for a child about a quest, an ambulance, and a low ceiling.',
        f"Tell a brave quest story where {hero.id} must guide an ambulance toward {q.goal} while keeping {prize.phrase} safe.",
        f'Write a child-friendly adventure that includes the word "quest" and solves the ceiling problem with a smart choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, ambulance, prize, ceiling, quest = (
        f["hero"], f["parent"], f["ambulance"], f["prize"], f["ceiling"], f["quest"]
    )
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to do on the quest?",
            answer=f"{hero.id} was trying to {quest.verb} and reach {quest.goal} with the ambulance and the prize.",
        ),
        QAItem(
            question=f"Why did the ambulance have trouble near the ceiling?",
            answer=f"The ambulance had trouble because it was taller than the ceiling's clearance, so it could not pass safely at first.",
        ),
        QAItem(
            question=f"What did the guide say when the route got too tight?",
            answer=f"The guide said not to scrape the roof and reminded {hero.id} that a quest can be clever, not just fast.",
        ),
    ]
    if ambulance.meters["height"] > ceiling.meters["clearance"]:
        qa.append(QAItem(
            question=f"How did {hero.id} get the ambulance through the low ceiling?",
            answer="They folded down the light mast so the ambulance became low enough to pass without bumping the ceiling.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is an ambulance for?",
            answer="An ambulance is a rescue vehicle that helps carry sick or hurt people to safety and care.",
        ),
        QAItem(
            question="What is a ceiling?",
            answer="A ceiling is the top inside surface of a room or passage.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or mission to find, save, or bring back something important.",
        ),
    ]
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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.
valid(P, Q, Pr) :- place(P), quest(Q), prize(Pr), affords(P, Q).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("place", p))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", p, q))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for pr in PRIZES:
        lines.append(asp.fact("prize", pr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], PRIZES[params.prize], params.name, params.gender, params.parent)
    if world.entities["ambulance"].meters["height"] > world.entities["ceiling"].meters["clearance"]:
        world.facts["gear"] = GEAR["folding_mast"]
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, quest, prize) combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("garage", "garage_quest", "badge", "Maya", "girl", "father", "brave"),
            StoryParams("tunnel", "tunnel_quest", "map", "Leo", "boy", "mother", "curious"),
            StoryParams("museum", "museum_quest", "lantern", "Ivy", "girl", "father", "bold"),
            StoryParams("station", "station_quest", "key", "Finn", "boy", "mother", "gentle"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.quest} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
