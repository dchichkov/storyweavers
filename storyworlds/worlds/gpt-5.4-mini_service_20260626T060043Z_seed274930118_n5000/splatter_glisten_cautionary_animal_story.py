#!/usr/bin/env python3
"""
A standalone story world for a small Animal-Story-style cautionary tale.

Seed image:
- A young animal loves the glisten of a bright place.
- A careful parent warns that a wild splatter could ruin a prized item.
- The child resists at first, then accepts a safer way and still gets to play.

This world keeps the domain small and constraint-checked:
- The story must be physically plausible in the simulated setting.
- The warning must be honest: the prize is actually at risk.
- The compromise must genuinely prevent the mess.

Words to surface in the domain:
- splatter
- glisten
- cautionary
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
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("wet", "muddy", "splattered", "dirty", "workload"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "love", "desire", "worry", "defiance", "conflict", "pride"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


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
    zone: set[str]
    weather: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.fired: set[tuple] = set()
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "creek": Setting(place="the creek bank", affords={"creek"}),
    "berry_patch": Setting(place="the berry patch", affords={"berries"}),
    "lantern_lawn": Setting(place="the lantern lawn", affords={"glisten"}),
}

ACTIVITIES = {
    "creek": Activity(
        id="creek",
        verb="splash in the creek",
        gerund="splashing in the creek",
        rush="run to the water",
        mess="splattered",
        soil="splattered and wet",
        zone={"feet", "torso"},
        weather="sunny",
        keyword="splatter",
        tags={"water", "splatter"},
    ),
    "berries": Activity(
        id="berries",
        verb="pick the berries",
        gerund="picking berries",
        rush="dash into the bushes",
        mess="splattered",
        soil="stained red",
        zone={"hands", "torso"},
        weather="sunny",
        keyword="splatter",
        tags={"fruit", "splatter"},
    ),
    "glisten": Activity(
        id="glisten",
        verb="chase the glistening bubbles",
        gerund="chasing glistening bubbles",
        rush="run after the shining bubbles",
        mess="wet",
        soil="wet and muddy",
        zone={"feet", "torso"},
        weather="sunny",
        keyword="glisten",
        tags={"shine", "wet", "glisten"},
    ),
}

PRIZES = {
    "scarf": Prize(label="scarf", phrase="a soft white scarf", type="scarf", region="torso"),
    "boots": Prize(label="boots", phrase="clean yellow boots", type="boots", region="feet", plural=True),
    "apron": Prize(label="apron", phrase="a little blue apron", type="apron", region="torso"),
}

GEAR = [
    Gear(
        id="raincoat",
        label="a raincoat",
        covers={"torso"},
        guards={"wet", "splattered"},
        prep="put on a raincoat first",
        tail="walked back to the shed for the raincoat",
    ),
    Gear(
        id="boots",
        label="rain boots",
        covers={"feet"},
        guards={"wet", "splattered"},
        prep="put on rain boots first",
        tail="went to fetch the rain boots",
        plural=True,
    ),
    Gear(
        id="apron",
        label="an apron",
        covers={"torso"},
        guards={"splattered"},
        prep="tie on an apron first",
        tail="went to fetch the apron",
    ),
]

GIRL_NAMES = ["Mina", "Luna", "Pip", "Tia", "Nora"]
BOY_NAMES = ["Rufus", "Milo", "Bram", "Ollie", "Toby"]
TRAITS = ["curious", "cheerful", "spirited", "stubborn", "playful"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.mess in gear.guards:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["dirty"] >= THRESHOLD, "workload": 1 if prize.meters["dirty"] >= THRESHOLD else 0}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    for item in world.worn_items(actor):
        if item.protective:
            continue
        if item.region in world.zone and not world.covered(actor, item.region):
            item.meters["dirty"] += 1
            item.meters[activity.mess] += 1
            if narrate:
                world.say(f"{actor.pronoun('possessive').capitalize()} {item.label} got {activity.soil}.")


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who noticed every shining thing.")


def loves(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}; the water and light made everything glisten.")


def gift(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"{hero.id}'s {parent.type} brought home {hero.pronoun('object')} {prize.phrase}.")


def wears(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    hero.memes["pride"] += 1
    world.say(f"{hero.id} wore {prize.it()} all day and liked how clean and bright it looked.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One sunny day, {hero.id} and {hero.pronoun('possessive')} {parent.type} went to {world.setting.place}.")
    world.say(f"The water and stones there could glisten like tiny jewels.")


def want(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb}, even before thinking about the mess.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(f'"You will get your {prize.label} {activity.soil}," {hero.pronoun("possessive")} {parent.type} said.')
    world.say(f'"That would mean more cleaning later."')
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} still rushed toward the fun and tried to {activity.rush}.")


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        pass
    g = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers), plural=gear.plural))
    g.worn_by = hero.id
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.type} smiled and said, 'How about we {gear.prep}?'")
    return gear


def accept(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["defiance"] = 0
    world.say(f"{hero.id} nodded, and soon they {gear.tail}.")
    world.say(f"After that, {hero.id} was {activity.gerund} while {prize.id} stayed clean and bright.")
    world.say(f"{hero.id} laughed as the creek and the day both glistened softly around {hero.pronoun('object')}.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))

    introduce(world, hero)
    loves(world, hero, activity)
    gift(world, parent, hero, prize)
    wears(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    want(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defy(world, hero, activity)
    world.para()
    gear = compromise(world, parent, hero, activity, prize)
    if gear:
        accept(world, hero, parent, activity, prize, gear)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear, trait=trait)
    return world


def build_story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, activity = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Why did {hero.id} get warned before {hero.pronoun('subject')} could {activity.verb}?",
            answer=f"{parent.type.capitalize()} warned {hero.id} because the {prize.label} would get {activity.soil} if {hero.id} splashed too close to the water.",
        ),
        QAItem(
            question=f"What did the parent offer so {hero.id} could still {activity.verb} safely?",
            answer=f"They offered a matching piece of gear that covered the right part of the body, so {hero.id} could play without ruining the {prize.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} {activity.gerund} safely while the {prize.label} stayed clean, so the day still glistened happily.",
        ),
    ]
    if f.get("gear"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did {gear.label} help in the story?",
                answer=f"{gear.label} covered the part that would have been splattered, so the mess did not reach the {prize.label}.",
            )
        )
    return qa


def build_world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does glisten mean?", answer="Glisten means to shine with a soft light, like water or a stone in the sun."),
        QAItem(question="What is a splatter?", answer="A splatter is a messy spray or splash that lands in little drops."),
        QAItem(question="Why do careful animals use gear in messy weather?", answer="They use gear to keep clean clothes, fur, or belongings from getting wet or stained."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, activity, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a short cautionary animal story about {hero.id} and the word "{activity.keyword}".',
        f"Tell a gentle story where a young {hero.type} wants to {activity.verb} but worries about a {prize.label}.",
        f'Create a child-friendly story with the words "splatter" and "glisten" and a safe ending.',
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = ["--- world trace ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        e_m = {k: v for k, v in e.memes.items() if v}
        info = []
        if m:
            info.append(f"meters={m}")
        if e_m:
            info.append(f"memes={e_m}")
        if e.protective:
            info.append(f"covers={sorted(e.covers)}")
        if e.region:
            info.append(f"region={e.region}")
        bits.append(f"  {e.id}: {e.type} {' '.join(info)}")
    bits.append(f"  fired={sorted(world.fired)}")
    return "\n".join(bits)


ASP_RULES = r"""
at_risk(A,P) :- splashes(A,R), worn_on(P,R).
fix(G,A,P) :- gear(G), at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), at_risk(A,P), fix(_,A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def verify() -> int:
    py = set(valid_combos())
    asp_set = set(valid_asp())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch:")
    print("python-only:", sorted(py - asp_set))
    print("asp-only:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small cautionary animal story world with splatter and glisten.")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    g = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if g == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=g, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=build_story_qa(world),
        world_qa=build_world_qa(world),
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
    StoryParams(place="creek", activity="creek", prize="scarf", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="berry_patch", activity="berries", prize="apron", name="Rufus", gender="boy", parent="father", trait="playful"),
    StoryParams(place="lantern_lawn", activity="glisten", prize="boots", name="Pip", gender="girl", parent="mother", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(pairs)} compatible stories:\n")
        for place, act, prize, gender in pairs:
            print(f"  {place:12} {act:10} {prize:8} {gender}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
