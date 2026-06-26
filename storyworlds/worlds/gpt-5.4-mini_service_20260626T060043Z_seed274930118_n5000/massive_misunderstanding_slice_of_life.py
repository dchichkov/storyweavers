#!/usr/bin/env python3
"""
storyworlds/worlds/massive_misunderstanding_slice_of_life.py
============================================================

A small slice-of-life storyworld about a massive misunderstanding:
a child makes a big, ordinary home project, a grown-up misreads the scene,
and everyone finds the gentle truth in the end.

The world is intentionally narrow: a few settings, a few home activities,
and a few reasonable fixes. The simulated state drives the prose.
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
    kind: str = "thing"  # "character" | "thing"
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
            self.meters = {"messy": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "misunderstanding": 0.0, "warmth": 0.0, "relief": 0.0}

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

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    clue: str
    keyword: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"poster", "bake"}),
    "living_room": Setting(place="the living room", indoor=True, affords={"poster", "blocks"}),
    "porch": Setting(place="the porch", indoor=False, affords={"garden"}),
    "study": Setting(place="the study", indoor=True, affords={"poster", "notes"}),
}

ACTIVITIES = {
    "poster": Activity(
        id="poster",
        verb="make a poster",
        gerund="making a poster",
        mess="painty",
        clue="paint and tape",
        keyword="poster",
        zone={"torso", "hands"},
        tags={"paint", "home"},
    ),
    "bake": Activity(
        id="bake",
        verb="bake muffins",
        gerund="baking muffins",
        mess="floury",
        clue="flour and spoons",
        keyword="muffins",
        zone={"torso", "hands"},
        tags={"kitchen", "home"},
    ),
    "blocks": Activity(
        id="blocks",
        verb="build a tower",
        gerund="building a tower",
        mess="scattered",
        clue="blocks and cushions",
        keyword="tower",
        zone={"floor"},
        tags={"play", "home"},
    ),
    "notes": Activity(
        id="notes",
        verb="write a note",
        gerund="writing a note",
        mess="inky",
        clue="paper and pencils",
        keyword="note",
        zone={"hands"},
        tags={"paper", "home"},
    ),
    "garden": Activity(
        id="garden",
        verb="plant seeds",
        gerund="planting seeds",
        mess="muddy",
        clue="soil and tiny pots",
        keyword="seeds",
        zone={"hands", "knees"},
        tags={"garden", "home"},
    ),
}

PRIZES = {
    "shirt": Prize("shirt", "a clean blue shirt", "shirt", "torso"),
    "apron": Prize("apron", "a soft white apron", "apron", "torso"),
    "pants": Prize("pants", "new gray pants", "pants", "legs"),
    "rug": Prize("rug", "the little rug", "rug", "floor"),
}

GEAR = [
    Gear("smock", "a paint smock", {"torso"}, {"painty", "floury", "inky"}, "put on a paint smock first", "went to get the paint smock"),
    Gear("tablecloth", "a tablecloth", {"floor"}, {"painty", "floury"}, "cover the table with a tablecloth", "spread the tablecloth on the table"),
    Gear("mat", "a floor mat", {"floor"}, {"scattered"}, "set down a floor mat", "brought out the floor mat"),
    Gear("gardengloves", "garden gloves", {"hands"}, {"muddy"}, "wear garden gloves", "put on the garden gloves"),
]

GIRL_NAMES = ["Mia", "Nora", "Lina", "Sofia", "Ivy", "June"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Max", "Theo", "Finn"]
TRAITS = ["quiet", "curious", "playful", "careful", "brave", "patient"]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.mess in gear.guards:
            return gear
    return None


def reasonableness_gate(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone and select_gear(activity, prize) is not None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} would not reasonably threaten {prize.label} "
        f"well enough for a misunderstanding-and-fix story, or there is no gentle fix "
        f"in the home toolset.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: this version does not fit a {gender} hero with {PRIZES[prize_id].label}.)"


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.label_word} who noticed every tiny thing in the house.")


def love_home(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund} on quiet afternoons, because {activity.clue} always made the room feel lively."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One slow afternoon,"
    world.say(f"{day} {hero.id} and {hero.pronoun('possessive')} {parent.label_word} were in {world.setting.place}.")
    world.say(f"The house was calm, with room for a small project and a big idea.")


def want(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["warmth"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} because {hero.pronoun('possessive')} {prize.label} needed something lovely to do."
    )


def predict_mess(world: World, hero: Entity, activity: Activity, prize: Entity) -> bool:
    sim = Entity("tmp", kind="character", type=hero.type)
    sim.meters = dict(hero.meters)
    sim.memes = dict(hero.memes)
    sim.meters[activity.mess] = sim.meters.get(activity.mess, 0.0) + 1.0
    return prize.region in activity.zone


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    if not predict_mess(world, hero, activity, prize):
        return False
    world.facts["misread"] = True
    world.say(
        f'"{That := "That" if True else "That"} looks like a massive mess," {parent.pronoun("possessive")} {parent.label_word} said, peeking at the paint and tape. "Is the {prize.label} all right?"'
    )
    parent.memes["misunderstanding"] += 1
    parent.memes["worry"] += 1
    return True


def clarify(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["misunderstanding"] += 1
    world.say(
        f"{hero.id} blinked and shook {hero.pronoun('possessive')} head. "
        f'"No, {hero.pronoun("possessive")} {activity.verb} was for a surprise," {hero.pronoun()} said softly.'
    )


def offer_fix(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    if not reasonableness_gate(activity, prize):
        return None
    item = world.add(Entity(
        id=gear.id,
        kind="thing",
        type=gear.label,
        label=gear.label,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
        owner=hero.id,
        caretaker=parent.id,
        worn_by=hero.id,
    ))
    world.say(
        f'{parent.pronoun("possessive").capitalize()} {parent.label_word} softened right away. '
        f'"How about we {gear.prep} and keep going?"'
    )
    return gear


def resolve(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.memes["warmth"] += 1
    parent.memes["worry"] = 0.0
    parent.memes["misunderstanding"] = 0.0
    world.say(
        f'{hero.id} smiled and leaned against {hero.pronoun("possessive")} {parent.label_word}. '
        f'"I thought you were upset," {hero.pronoun()} admitted.'
    )
    world.say(
        f'"I just could not see the surprise yet," {parent.pronoun()} said. '
        f'Then they {gear.tail}, and soon {hero.id} was {activity.gerund} while {prize.label} stayed tidy.'
    )
    world.say(
        f'By the end, the house had a {activity.keyword} that looked {activity.clue}, and the earlier mix-up felt small and warm.'
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, region=prize_cfg.region))

    introduce(world, hero)
    love_home(world, hero, activity)
    world.say(f"That afternoon, {hero.id} had {prize_cfg.phrase} nearby.")
    arrive(world, hero, parent, activity)
    want(world, hero, activity, prize)
    warn(world, parent, hero, activity, prize)
    clarify(world, hero, activity)
    world.para()
    gear = offer_fix(world, parent, hero, activity, prize)
    if gear:
        resolve(world, parent, hero, activity, prize, gear)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear, trait=trait)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act = f["hero"], f["parent"], f["activity"]
    return [
        f'Write a short slice-of-life story for a child that includes the word "massive" and a misunderstanding about {act.keyword}.',
        f"Tell a gentle home story where {hero.id} wants to {act.verb} and {parent.label_word} first thinks it is a problem.",
        f"Write a calm story about a small project, a big misunderstanding, and a warm ending in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do in {world.setting.place}?",
            answer=f"{hero.id} was trying to {act.verb}. {hero.pronoun().capitalize()} wanted the day to feel special and calm.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} think there was a problem at first?",
            answer=f"{parent.pronoun().capitalize()} saw {act.clue} and thought it looked like a massive mess before hearing the real plan.",
        ),
        QAItem(
            question=f"What helped the family finish the project without ruining the {prize.label}?",
            answer=f"They used {f['gear'].label if f.get('gear') else 'a careful plan'}, so {hero.id} could keep going and the {prize.label} stayed tidy.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} {act.gerund} and everyone understanding that the big, busy-looking project was actually a sweet surprise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone sees or hears something and gets the meaning wrong at first.",
        ),
        QAItem(
            question="What does massive mean?",
            answer="Massive means very big or very large.",
        ),
        QAItem(
            question="Why do people use paint smocks?",
            answer="People use paint smocks to keep paint off their clothes while they make art.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="poster", prize="shirt", name="Mia", gender="girl", parent="mother", trait="playful"),
    StoryParams(place="living_room", activity="blocks", prize="rug", name="Owen", gender="boy", parent="father", trait="careful"),
    StoryParams(place="study", activity="notes", prize="apron", name="Nora", gender="girl", parent="mother", trait="patient"),
    StoryParams(place="kitchen", activity="bake", prize="shirt", name="Finn", gender="boy", parent="mother", trait="curious"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), prize_region(P,R).
fix(G,A,P) :- gear(G), prize_at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), prize_region(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), fix(_,A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about a massive misunderstanding.")
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
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not reasonableness_gate(act, prize):
            raise StoryError(explain_rejection(act, prize))
    if args.gender and args.prize and args.gender not in {"girl", "boy"}:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, "girl" if params.gender == "girl" else "boy", params.parent, params.trait)
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
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
