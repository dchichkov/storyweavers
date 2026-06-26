#!/usr/bin/env python3
"""
A fairy-tale storyworld about a stubborn goose, a small dab of paint, and a
charging argument that ends in a gentle, magical repair.

Seed words:
- dab
- gander
- charge

Features:
- Repetition
- Dialogue
- Conflict

Style:
- Fairy tale
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = False
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
    plural: bool = False


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


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


SETTINGS = {
    "meadow": Place("the meadow", affords={"dab", "gander"}),
    "pond": Place("the pond", affords={"gander"}),
    "garden": Place("the garden", affords={"dab", "gander"}),
    "courtyard": Place("the courtyard", affords={"dab"}),
}

ACTIVITIES = {
    "dab": Activity(
        id="dab",
        verb="dab the spell on the stone",
        gerund="dabbing the spell on the stone",
        rush="rush to dab the spell",
        mess="inked",
        soil="ink-stained",
        zone={"hands"},
        keyword="dab",
        tags={"dab", "ink"},
    ),
    "gander": Activity(
        id="gander",
        verb="gather the gander feathers",
        gerund="gathering the gander feathers",
        rush="charge toward the gander",
        mess="muddy",
        soil="mud-spattered",
        zone={"feet", "legs"},
        keyword="gander",
        tags={"gander", "feather"},
    ),
    "charge": Activity(
        id="charge",
        verb="charge the tiny lantern with moonlight",
        gerund="charging the tiny lantern with moonlight",
        rush="charge at the dark corner",
        mess="sparked",
        soil="spark-scorched",
        zone={"hands", "torso"},
        keyword="charge",
        tags={"charge", "light"},
    ),
}

PRIZES = {
    "cloak": Prize("cloak", "a bright little cloak", "cloak", "torso"),
    "boots": Prize("boots", "soft traveler boots", "boots", "feet", plural=True),
    "gloves": Prize("gloves", "silver gloves", "gloves", "hands", plural=True),
}

GEAR = [
    Gear("apron", "a blue apron", {"torso", "hands"}, {"inked"}, "put on a blue apron", "put on the blue apron"),
    Gear("galoshes", "muddy galoshes", {"feet", "legs"}, {"muddy"}, "pull on muddy galoshes", "pull on the muddy galoshes", True),
    Gear("mittens", "mooncloth mittens", {"hands"}, {"sparked", "inked"}, "wear mooncloth mittens", "wear the mooncloth mittens", True),
]

NAMES = ["Mira", "Tansy", "Elsie", "Rowan", "Pip", "Lina", "Bram", "Oona"]
TRAITS = ["brave", "curious", "stubborn", "gentle", "merry"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in SETTINGS.items():
        for act_id in place.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone and any(prize.region in g.covers and act.mess in g.guards for g in GEAR):
                    out.append((place_id, act_id, prize_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld about dab, gander, and charge.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (pr.region in act.zone and any(pr.region in g.covers and act.mess in g.guards for g in GEAR)):
            raise StoryError("(No valid story: that activity cannot reasonably affect that prize.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender not in PRIZES[prize].genders:
        raise StoryError("(No story: that prize does not fit the chosen gender in this world.)")
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def reasonableness_gate(params: StoryParams) -> bool:
    act = ACTIVITIES[params.activity]
    pr = PRIZES[params.prize]
    return pr.region in act.zone and any(pr.region in g.covers and act.mess in g.guards for g in GEAR)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), protects(_,A,P).
#show valid/3.
"""


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: ASP matches Python ({len(p)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(p - a))
    print("only asp:", sorted(a - p))
    return 1


def _consume_conflict(world: World, actor: Entity, act: Activity, prize: Entity) -> None:
    actor.memes["conflict"] = max(actor.memes.get("conflict", 0.0), 1.0)
    world.say(f"{actor.id} frowned. {actor.pronoun().capitalize()} wanted to {act.verb}, but the {prize.label} might be ruined.")


def _repetition(world: World, actor: Entity, act: Activity) -> None:
    world.say(f"Again and again, {actor.id} tried to {act.verb}. Again and again, the worry returned.")


def _dialogue(world: World, hero: Entity, parent: Entity, act: Activity, prize: Entity) -> None:
    world.say(f'"Let me do it," said {hero.id}.')
    world.say(f'"Not yet," said {parent.label}. "Your {prize.label} could get {ACTIVITIES[act.id].soil}."')


def _resolve(world: World, hero: Entity, parent: Entity, act: Activity, prize: Entity, gear: Gear) -> None:
    world.say(f'{parent.label.capitalize()} smiled. "Then let us {gear.prep} first."')
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["conflict"] = 0.0
    world.say(f"They {gear.tail}, and at last {hero.id} could {act.gerund} while the {prize.label} stayed clean.")


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(params.name, kind="character", type=params.gender, traits=[params.trait, "small"]))
    parent = world.add(Entity("Parent", kind="character", type=params.parent, label="the parent"))
    prize = world.add(Entity(
        "Prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase, owner=hero.id, caretaker=parent.id,
        plural=PRIZES[params.prize].plural, worn_by=hero.id
    ))
    act = ACTIVITIES[params.activity]
    place = SETTINGS[params.place]

    world.say(f"Once in {place.name}, there lived a {params.trait} {params.gender} named {hero.id}.")
    world.say(f"{hero.id} loved to {act.gerund}.")
    world.say(f"{hero.id} also cherished {prize.phrase}.")

    world.para()
    world.say(f"One twilight, {hero.id} and {parent.label} went to {place.name}.")
    world.say(f"{hero.id} wished to {act.verb}, and {hero.id} wished it twice, for fairy tales like their wishes repeated.")
    _repetition(world, hero, act)
    _consume_conflict(world, hero, act, prize)
    _dialogue(world, hero, parent, act, prize)

    gear = next(g for g in GEAR if prize.region in g.covers and act.mess in g.guards)
    world.para()
    _resolve(world, hero, parent, act, prize, gear)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=act, gear=gear, place=place)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act, gear = f["hero"], f["parent"], f["prize"], f["activity"], f["gear"]
    return [
        QAItem(
            question=f"Who wanted to {act.verb} in the fairy tale?",
            answer=f"{hero.id} wanted to {act.verb}, but the worry was that {prize.phrase} might get messy."
        ),
        QAItem(
            question=f"Why did {parent.label} worry?",
            answer=f"{parent.label.capitalize()} worried because if {hero.id} kept going, the {prize.label} could get {act.soil}."
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They used {gear.label} first, so {hero.id} could {act.gerund} without ruining the {prize.label}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(question="What is a gander?", answer="A gander is a male goose."),
        QAItem(question="What does dab mean?", answer="To dab means to touch something lightly with a small bit of paint, cloth, or liquid."),
        QAItem(question="What does charge mean?", answer="To charge can mean to fill something with power or to rush forward quickly."),
    ]
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale about a child named {f["hero"].id} who wants to {f["activity"].verb} while a gander watches.',
        f'Tell a short story with repetition and dialogue where the word "{f["activity"].keyword}" matters.',
        f'Write a gentle conflict story that ends with {f["hero"].id} using {f["gear"].label} before charging ahead.',
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("meadow", "dab", "cloak", "Mira", "girl", "mother", "brave"),
    StoryParams("garden", "gander", "boots", "Bram", "boy", "father", "curious"),
    StoryParams("courtyard", "charge", "gloves", "Oona", "girl", "mother", "merry"),
]


def generate(params: StoryParams) -> StorySample:
    if not reasonableness_gate(params):
        raise StoryError("(No valid story from these parameters.)")
    world = World(SETTINGS[params.place])
    world = tell(world, params)
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


def asp_show() -> str:
    return asp_program("#show valid/3.")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        for t in triples:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
