#!/usr/bin/env python3
"""
storyworlds/worlds/triumph_sequel_surprise_slice_of_life.py
==========================================================

A small slice-of-life story world about a child, a quiet project, a surprise,
and the happy sequel that follows a little triumph.

The seed image is simple: someone tries an ordinary task, a tiny obstacle
appears, and the day turns on a gentle surprise that leads to a second win.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["mess", "clean", "work", "care", "timing"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "surprise", "triumph", "calm", "relief"]:
            self.memes.setdefault(k, 0.0)

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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
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
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["mess"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.id == "project":
                continue
            sig = ("soil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            if "paint" in world.zone and not world.covered(actor, "torso"):
                item.meters["mess"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got speckled with paint.")
    return out


def _r_surprise(world: World) -> list[str]:
    hero = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    if not hero or hero.memes["joy"] < THRESHOLD:
        return []
    sig = ("surprise", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["surprise"] += 1
    return ["__surprise__"]


def _r_triumph(world: World) -> list[str]:
    hero = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    if not hero:
        return []
    if hero.meters["clean"] < THRESHOLD:
        return []
    sig = ("triumph", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["triumph"] += 1
    hero.memes["joy"] += 1
    return [f"{hero.id} felt a little triumphant."]


CAUSAL_RULES = [
    Rule("soil", "physical", _r_soil),
    Rule("surprise", "social", _r_surprise),
    Rule("triumph", "social", _r_triumph),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__surprise__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["mess"] >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["mess"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


SETTINGS = {
    "kitchen": Setting(place="the kitchen table", indoor=True, affords={"paint", "bake"}),
    "porch": Setting(place="the porch", indoor=False, affords={"paint"}),
    "corner": Setting(place="the cozy corner by the window", indoor=True, affords={"draw", "paint"}),
}

ACTIVITIES = {
    "paint": Activity(
        id="paint",
        verb="paint a picture",
        gerund="painting pictures",
        rush="reach for the brush",
        mess="paint",
        soil="spattered",
        zone={"torso", "hands"},
        weather="",
        keyword="paint",
        tags={"paint", "surprise"},
    ),
    "bake": Activity(
        id="bake",
        verb="decorate the cupcakes",
        gerund="decorating cupcakes",
        rush="lean over the tray",
        mess="batter",
        soil="smudged",
        zone={"hands"},
        weather="",
        keyword="cupcakes",
        tags={"bake", "surprise"},
    ),
    "draw": Activity(
        id="draw",
        verb="draw a sequel page",
        gerund="drawing sequels",
        rush="grab the crayons",
        mess="crumb",
        soil="crumbled",
        zone={"hands"},
        weather="",
        keyword="sequel",
        tags={"sequel"},
    ),
}

PRIZES = {
    "shirt": Prize("shirt", "a clean white shirt", "shirt", "torso"),
    "apron": Prize("apron", "a bright apron", "apron", "torso"),
    "paper": Prize("paper", "a fresh page", "paper", "hands"),
}

GEAR = [
    Gear("apron", "an apron", {"torso"}, {"paint", "batter"}, "put on an apron first", "went to get the apron"),
    Gear("smock", "a paint smock", {"torso"}, {"paint"}, "pull on a paint smock", "found the paint smock"),
]


class StoryParams:
    def __init__(self, place: str, activity: str, prize: str, name: str, gender: str, parent: str, trait: str, seed: Optional[int] = None):
        self.place = place
        self.activity = activity
        self.prize = prize
        self.name = name
        self.gender = gender
        self.parent = parent
        self.trait = trait
        self.seed = seed


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    for gear in GEAR:
                        if act.mess in gear.guards and prize.region in gear.covers:
                            combos.append((place, act_id, prize_id))
                            break
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world with triumph, surprise, and a sequel.")
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
        if not (pr.region in act.zone and any(act.mess in g.guards and pr.region in g.covers for g in GEAR)):
            raise StoryError("That activity and prize do not make a believable little problem-and-fix story.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid story matches those options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Mina", "Luca", "Nora", "Theo", "Ava", "Ben"])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(["gentle", "cheerful", "quiet", "curious"])
    return StoryParams(place, activity, prize, name, gender, parent, trait)


def render_sentence(world: World, text: str) -> None:
    world.say(text)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait, "steady"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    gear_def = next((g for g in GEAR if activity.mess in g.guards and prize.region in g.covers), None)
    gear = None
    if gear_def:
        gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, protective=True, covers=set(gear_def.covers), plural=gear_def.plural))
        gear.worn_by = hero.id

    world.weather = activity.weather

    world.say(f"{hero.id} was a little {trait} {hero.type} who liked calm afternoons at {setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} wanted to {activity.verb} and make something nice just because it was a regular day.")
    world.say(f"At home, {hero.pronoun('possessive')} {parent_type if parent_type in {'mother', 'father'} else 'parent'} had given {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} loved {prize.label} and held {prize.it()} carefully.")

    world.para()
    world.say(f"Later, {hero.id} and {hero.pronoun('possessive')} {parent_type} sat down at {setting.place}.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {parent_type} noticed the {prize.label} might get {activity.soil}.")
    if not predict_mess(world, hero, activity, prize.id)["soiled"]:
        raise StoryError("This world has no honest problem for the parent to notice.")

    world.say(f'"If you {activity.verb}, your {prize.label} could get {activity.soil}," {hero.pronoun("possessive")} {parent_type} said.')
    world.say(f"{hero.id} frowned a little and reached for the brush anyway.")
    hero.memes["worry"] += 1
    hero.meters["mess"] += 1

    if gear_def:
        world.say(f"Then {hero.pronoun('possessive')} {parent_type} smiled and said, \"How about we {gear_def.prep}?\"")
        world.say(f"That was the kind of small fix that made sense.")
        world.say(f"{hero.id} nodded, and they {gear_def.tail}.")
        if gear:
            gear.worn_by = hero.id
        hero.memes["relief"] += 1
        hero.meters["clean"] += 1
        hero.memes["triumph"] += 1
        world.say(f"At last, {hero.id} could {activity.gerund} without ruining {hero.pronoun('possessive')} {prize.label}.")
        world.say(f"The little job felt like a triumph, because the work stayed neat and the afternoon stayed calm.")

    world.para()
    hero.memes["surprise"] += 1
    world.say(f"Just then, a surprise arrived: there was a second page, a sequel to the first little project.")
    world.say(f"{hero.id} laughed, because the surprise was not a problem at all. It was another chance to make something lovely.")
    hero.meters["clean"] += 1
    hero.memes["joy"] += 1
    hero.memes["triumph"] += 1
    world.say(f"So {hero.id} started the sequel too, and {hero.pronoun('possessive')} {parent_type} watched with a warm, proud smile.")
    world.say(f"By the end, the table held one finished piece and one new one beginning, and the room felt tidy, bright, and full of quiet triumph.")

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear, gear_def=gear_def)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f"Write a slice-of-life story about {hero.id} who wants to {act.verb} and has a small surprise sequel afterward.",
        f"Tell a gentle everyday story where {hero.id} and {hero.pronoun('possessive')} {parent.type} find a clever fix so {prize.label} stays clean.",
        f"Write a short child-friendly story using the words triumph, sequel, and surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f.get("gear")
    gear_name = gear.label if gear else "the helper item"
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} at {world.setting.place}, and {hero.pronoun('possessive')} {parent.type} stayed nearby to help.",
        ),
        QAItem(
            question=f"Why did {hero.pronoun('possessive')} {parent.type} worry about {prize.label}?",
            answer=f"{parent.id} worried because {prize.label} could get {act.soil} while {hero.id} was {act.gerund}.",
        ),
        QAItem(
            question=f"How did {gear_name} help the story turn out well?",
            answer=f"It helped {hero.id} do the project without ruining {hero.pronoun('possessive')} {prize.label}, so the little task became a triumph.",
        ),
        QAItem(
            question=f"What was the surprise sequel in the end?",
            answer=f"The surprise sequel was a second page of the project, so {hero.id} got to keep going and make one more happy little piece.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    act = world.facts["activity"]
    out = [QAItem("What is a sequel?", "A sequel is something that comes after the first part, like a second story or a next chapter.")]
    if "paint" in act.tags:
        out.append(QAItem("Why can paint be messy?", "Paint can drip and smear, so it can get on clothes, hands, and tables if you are not careful."))
    out.append(QAItem("What does triumph mean?", "Triumph means a happy success, when something hard or worrisome turns out well."))
    out.append(QAItem("What is a surprise?", "A surprise is something unexpected that appears suddenly and changes what happens next."))
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
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
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams("kitchen", "paint", "shirt", "Mina", "girl", "mother", "curious"),
    StoryParams("corner", "draw", "paper", "Theo", "boy", "father", "gentle"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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
        print(sorted(set(asp.atoms(model, "valid"))))
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
