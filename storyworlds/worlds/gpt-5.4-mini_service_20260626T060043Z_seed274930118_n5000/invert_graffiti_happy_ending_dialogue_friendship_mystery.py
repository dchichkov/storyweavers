#!/usr/bin/env python3
"""
A small mystery story world about graffiti, an inverted clue, friendship, and a
happy ending.

The seed premise:
- A child finds graffiti near a quiet place.
- The child and a friend investigate like little detectives.
- A clue only makes sense when viewed inverted.
- The ending is warm: the supposed problem becomes a shared mural and a new
  friendship.

This file is self-contained and follows the Storyweavers world contract.
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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    surface: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for k in ["paint", "cleanliness", "confidence", "joy", "trust", "curiosity", "worry", "friendship"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    surface: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.scene: str = "setup"

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _apply_graffiti(world: World) -> list[str]:
    out = []
    if world.scene != "conflict":
        return out
    artist = world.facts["artist"]
    clue = world.facts["clue"]
    prize = world.facts["prize"]
    if artist.meters["paint"] < THRESHOLD:
        return out
    sig = ("graffiti", prize.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.meters["paint"] += 1
    prize.meters["cleanliness"] -= 1
    out.append(f"The {prize.label} got splashed with paint.")
    if clue == "invert":
        world.facts["invert_reveals"] = True
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    more = True
    while more:
        more = False
        for fn in [_apply_graffiti]:
            sents = fn(world)
            if sents:
                more = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about graffiti and an inverted clue.")
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.surface == "wall" and activity.id == "graffiti"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if activity.mess in g.guards and prize.surface in g.covers:
            return g
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = ACTIVITIES[aid]
            for pid, pr in PRIZES.items():
                if prize_at_risk(act, pr) and select_gear(act, pr):
                    out.append((place, aid, pid))
    return out


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    clue: str
    seed: Optional[int] = None


SETTINGS = {
    "alley": Setting(place="the alley", indoor=False, affords={"graffiti"}),
    "schoolyard": Setting(place="the schoolyard", indoor=False, affords={"graffiti"}),
    "courtyard": Setting(place="the courtyard", indoor=False, affords={"graffiti"}),
}

ACTIVITIES = {
    "graffiti": Activity(
        id="graffiti",
        verb="make graffiti",
        gerund="making graffiti",
        rush="run toward the wall with the spray can",
        mess="paint",
        soil="painted",
        keyword="graffiti",
        tags={"graffiti", "paint", "mystery"},
    )
}

PRIZES = {
    "wall": Prize(label="wall", phrase="a clean white wall", type="wall", surface="wall"),
    "sign": Prize(label="sign", phrase="a tidy wooden sign", type="sign", surface="wall"),
    "mural": Prize(label="mural board", phrase="a blank mural board", type="mural board", surface="wall"),
}

GEAR = [
    Gear(
        id="dropcloth",
        label="a drop cloth",
        covers={"wall"},
        guards={"paint"},
        prep="lay down a drop cloth first",
        tail="laid down a drop cloth",
    ),
    Gear(
        id="tape",
        label="painter's tape",
        covers={"wall"},
        guards={"paint"},
        prep="tape the edges first",
        tail="taped the edges",
    ),
]

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe"]
BOY_NAMES = ["Finn", "Leo", "Ben", "Theo", "Max"]
TRAITS = ["curious", "gentle", "brave", "thoughtful", "careful"]

CURATED = [
    StoryParams(place="alley", activity="graffiti", prize="wall", name="Mia", gender="girl", parent="mother", clue="invert"),
    StoryParams(place="schoolyard", activity="graffiti", prize="sign", name="Theo", gender="boy", parent="father", clue="invert"),
    StoryParams(place="courtyard", activity="graffiti", prize="mural", name="Nora", gender="girl", parent="mother", clue="invert"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} only matters here when it could paint a {prize.label}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: a {PRIZES[prize_id].label} does not fit that gender choice here.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), graffiti(A), wall_prize(P).
has_fix(A,P) :- prize_at_risk(A,P), fix(G,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.surface == "wall":
            lines.append(asp.fact("wall_prize", pid))
    for g in GEAR:
        lines.append(asp.fact("fix", g.id, "graffiti", "wall"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    clue = "invert"
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, clue=clue)


def _story_begin(world: World, hero: Entity, friend: Entity, parent: Entity, prize: Entity) -> None:
    world.say(f"{hero.id} was a {hero.traits[0]} little {hero.type} who loved mysteries.")
    world.say(f"{hero.id} and {friend.id} were best friends, and they liked solving puzzles together.")
    world.say(f"One day, they found {prize.phrase} near {world.setting.place}.")
    world.say(f"It had fresh graffiti on it, and nobody knew who had done it.")


def _story_middle(world: World, hero: Entity, friend: Entity, parent: Entity, prize: Entity) -> None:
    world.para()
    world.scene = "conflict"
    world.say(f'"This looks strange," {hero.id} said. "{friend.id}, do you think it was meant to be mean?"')
    world.say(f'"Maybe not," {friend.id} said. "Look at the letters upside down."')
    world.say(f"{hero.id} tilted the picture and then turned it invert. Suddenly, the clue made sense.")
    world.say(f'"It says, "Meet me by the wall,"' if world.facts["clue"] == "invert" else f'"It says something else," {friend.id} whispered.')
    world.say(f"{parent.id} frowned at first. " + f'"We should be careful with {prize.label}," {parent.id} said.')
    world.say(f"{hero.id} and {friend.id} agreed to investigate kindly instead of jumping to the wrong idea.")


def _story_end(world: World, hero: Entity, friend: Entity, parent: Entity, prize: Entity) -> None:
    world.para()
    world.scene = "resolution"
    world.say(f"They found the artist hiding behind the corner: it was another friend, {world.facts['artist_name']}, who had made a surprise mural plan.")
    world.say(f'"We wanted to help," {world.facts["artist_name"]} said. "I did not mean to spoil anything."')
    world.say(f'"Then let us do it together," {hero.id} said. "{friend.id}, will you help us?"')
    world.say(f'"Of course!" {friend.id} said, and all the kids smiled.')
    world.say(f"They laid down a drop cloth, painted a bright new design, and kept {prize.label} clean while the wall became beautiful.")
    world.say(f"In the end, the mystery had a happy ending: the graffiti was not a problem anymore, but a shared mural and a new friendship.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, clue: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["curious", "gentle"]))
    friend = world.add(Entity(id="Friend", kind="character", type="boy" if hero_type == "girl" else "girl", traits=["kind", "helpful"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, surface=prize_cfg.surface))
    artist = world.add(Entity(id="Artist", kind="character", type="boy", traits=["creative"]))
    world.facts.update(hero=hero, friend=friend, parent=parent, prize=prize, artist=artist, clue=clue, artist_name="Noah")
    _story_begin(world, hero, friend, parent, prize)
    _story_middle(world, hero, friend, parent, prize)
    _story_end(world, hero, friend, parent, prize)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short mystery story for a young child about {hero.id}, a friendly clue, and the word "graffiti".',
        f"Tell a gentle detective story where {hero.id} and a friend solve a graffiti mystery with an inverted clue.",
        f"Write a happy-ending story with dialogue, friendship, and a surprise mural near {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, parent, prize = f["hero"], f["friend"], f["parent"], f["prize"]
    return [
        QAItem(
            question=f"What kind of story is this about {hero.id} and {friend.id}?",
            answer=f"It is a mystery story about {hero.id} and {friend.id} solving a graffiti clue together.",
        ),
        QAItem(
            question=f"What did {friend.id} tell {hero.id} to do with the clue?",
            answer="The friend told the hero to look at the letters upside down, so the clue had to be inverted to make sense.",
        ),
        QAItem(
            question=f"How did the story end near {world.setting.place}?",
            answer=f"It ended happily with a shared mural, a clean {prize.label}, and a new friendship.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is graffiti?",
            answer="Graffiti is writing or art made on walls or other surfaces, often with paint or spray.",
        ),
        QAItem(
            question="What does invert mean?",
            answer="Invert means to turn something upside down or switch its position so it faces the opposite way.",
        ),
        QAItem(
            question="Why can a mystery story have a happy ending?",
            answer="A mystery can end happily when the friends figure out the truth and fix the problem kindly.",
        ),
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v not in (0, 0.0)}
        memes = {k: v for k, v in e.memes.items() if v not in (0, 0.0)}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.surface:
            bits.append(f"surface={e.surface}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.clue)
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_asp_view() -> str:
    return asp_program("#show valid/3.")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(build_asp_view())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
