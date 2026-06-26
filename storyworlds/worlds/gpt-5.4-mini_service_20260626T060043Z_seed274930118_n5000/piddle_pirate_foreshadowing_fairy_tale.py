#!/usr/bin/env python3
"""
A fairy-tale story world about a careful child, a cheeky pirate, and
foreshadowed piddles that turn into a small nighttime problem and a kindly fix.
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


@dataclass
class Thing:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "princess", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "prince", "father", "man", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the harbor"
    kind: str = "outdoor"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    foreshadow: str
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
        self.entities: dict[str, Thing] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Thing) -> Thing:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Thing:
        return self.entities[eid]

    def characters(self) -> list[Thing]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Thing) -> list[Thing]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Thing, region: str) -> bool:
        for item in self.worn_items(actor):
            if item.id in GEAR_BY_ID and region in GEAR_BY_ID[item.id].covers:
                return True
        return False

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


THRESHOLD = 1.0


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if actor.meters.get("piddle", 0.0) >= THRESHOLD:
                for item in world.worn_items(actor):
                    if item.id in GEAR_BY_ID:
                        gear = GEAR_BY_ID[item.id]
                        if item.plural:
                            continue
                        if any(r in world.zone for r in gear.covers):
                            continue
                    if item.region not in world.zone:
                        continue
                    sig = ("mess", actor.id, item.id)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.meters["piddle"] = item.meters.get("piddle", 0.0) + 1
                    item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                    produced.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got damp and dirty.")
                    changed = True
            if actor.memes.get("fright", 0.0) >= THRESHOLD and actor.memes.get("hope", 0.0) >= THRESHOLD:
                sig = ("calm", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    actor.memes["calm"] = actor.memes.get("calm", 0.0) + 1
                    produced.append(f"The worry softened a little in {actor.id}'s heart.")
                    changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about a pirate, piddles, and foreshadowing.")
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


def _valid_combo(place: str, activity: str, prize: str) -> bool:
    act = ACTIVITIES[activity]
    pr = PRIZES[prize]
    return pr.region in act.zone and select_gear(act, pr) is not None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for activity in s.affords:
            for prize in PRIZES:
                if _valid_combo(place, activity, prize):
                    out.append((place, activity, prize))
    return out


def select_gear(activity: Action, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def explain_rejection(activity: Action, prize: Prize) -> str:
    return f"(No story: {activity.gerund} does not plausibly trouble {prize.label}, so there is no honest foreshadowing and no real fix.)"


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s prize in this little world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    if args.activity and args.prize:
        if not _valid_combo(args.place or "harbor", args.activity, args.prize):
            raise StoryError(explain_rejection(ACTIVITIES[args.activity], PRIZES[args.prize]))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    pr = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(pr.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


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


def tell(setting: Setting, activity: Action, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Thing(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Thing(id="parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Thing(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                            owner=hero.id, caretaker=parent.id, worn_by=hero.id, plural=prize_cfg.plural))
    hero.memes["love"] = 1
    hero.memes["curious"] = 1

    world.say(f"Once in {setting.place}, there lived a little {trait} {hero.type} named {hero.id}.")
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, and {activity.foreshadow}.")
    world.say(f"One day, {parent.label_word(parent)} bought {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} wore {prize.it()} proudly, as if it had been stitched from moonlight.")

    world.para()
    world.say(f"At dusk, {hero.id} and {hero.pronoun('possessive')} {parent_type} went to {setting.place}.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {parent.label_word(parent)} looked at the {prize.label} and frowned.")
    world.say(f'"If you {activity.verb}, you may get {activity.soil}," {parent.label_word(parent)} said.')

    world.para()
    hero.memes["fright"] = 1
    world.say(f"{hero.id} heard the warning and tried to {activity.rush}.")
    world.say(f"Then the smallest thing came true: the {activity.keyword} sign in the path was not just a sign at all.")
    world.zone = set(activity.zone)
    hero.meters["piddle"] = 1
    propagate(world, narrate=True)

    world.para()
    gear = select_gear(activity, prize)
    if gear is None:
        raise StoryError("No reasonable gear exists for this story.")
    gear_ent = world.add(Thing(id=gear.id, type="gear", label=gear.label, worn_by=hero.id, plural=gear.plural))
    world.say(f"{parent.label_word(parent).capitalize()} smiled and said, 'Let us put on {gear.prep}.'")
    world.say(f"{hero.id} agreed, and soon they {gear.tail}.")
    hero.memes["hope"] = 1
    hero.memes["fright"] = 0
    hero.memes["calm"] = 1
    world.zone = set()
    world.say(f"After that, {hero.id} could {activity.verb} without ruining the {prize.label}, and the little night felt safe again.")

    world.facts = {
        "hero": hero,
        "parent": parent,
        "prize": prize,
        "activity": activity,
        "setting": setting,
        "gear": gear_ent,
        "trait": trait,
    }
    return world


def parent_label(parent: Thing) -> str:
    return {"mother": "mom", "father": "dad"}.get(parent.type, parent.label or parent.type)


Thing.label_word = parent_label  # type: ignore[attr-defined]


SETTINGS = {
    "harbor": Setting(place="the harbor", affords={"piddle"}),
    "dock": Setting(place="the old dock", affords={"piddle"}),
    "cottage": Setting(place="the cottage lane", affords={"piddle"}),
}

ACTIVITIES = {
    "piddle": Action(
        id="piddle",
        verb="splash in the shallows",
        gerund="splashing in the shallows",
        rush="run to the water's edge",
        mess="piddle",
        soil="wet and muddy",
        zone={"feet", "hem"},
        keyword="piddle",
        foreshadow="the gulls cried as if a wet surprise were waiting",
        tags={"piddle", "water"},
    ),
    "pirate": Action(
        id="pirate",
        verb="pretend to be a pirate",
        gerund="playing pirate",
        rush="dash to the little boat",
        mess="piddle",
        soil="wet and splashy",
        zone={"feet", "hem"},
        keyword="pirate",
        foreshadow="his toy compass kept spinning toward trouble",
        tags={"pirate", "boat"},
    ),
}

PRIZES = {
    "cloak": Prize(label="cloak", phrase="a bright velvet cloak", type="cloak", region="torso"),
    "boots": Prize(label="boots", phrase="little golden boots", type="boots", region="feet", plural=True),
    "skirt": Prize(label="skirt", phrase="a soft blue skirt", type="skirt", region="hem"),
}

GEAR = [
    Gear(id="oilskin", label="an oilskin coat", covers={"torso"}, guards={"piddle"}, prep="put on an oilskin coat first", tail="went back to the harbor in the oilskin coat"),
    Gear(id="rubberboots", label="rubber boots", covers={"feet"}, guards={"piddle"}, prep="pull on rubber boots", tail="walked again in rubber boots", plural=True),
    Gear(id="apron", label="a stout apron", covers={"hem", "torso"}, guards={"piddle"}, prep="tie on a stout apron", tail="returned with the stout apron"),
]
GEAR_BY_ID = {g.id: g for g in GEAR}

GIRL_NAMES = ["Mira", "Ella", "Luna", "Rose", "Nell"]
BOY_NAMES = ["Finn", "Theo", "Bram", "Otto", "Pip"]
TRAITS = ["brave", "curious", "gentle", "cheerful", "stubborn"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a fairy tale about {hero.id}, a {hero.pronoun("subject")} little {hero.type}, and a pirate theme using the word "{act.keyword}".',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {parent_label(parent)} worries about {prize.phrase}.",
        f'Write a child-sized fairy tale with foreshadowing, a piddle, and a happy ending at {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type}, and {parent_label(parent)}, who cared about the {prize.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {act.verb}, but the story foreshadowed that the water would make trouble for the {prize.label}.",
        ),
        QAItem(
            question=f"What helped {hero.id} stay dry enough to keep the {prize.label} nice?",
            answer=f"{gear.label} helped, because it matched the wet trouble and covered the part that could get spoiled.",
        ),
        QAItem(
            question=f"Why did {parent_label(parent)} warn {hero.id}?",
            answer=f"{parent_label(parent)} warned {hero.id} because {act.foreshadow.lower()} and the {prize.label} might get {act.soil}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a pirate?", answer="A pirate is a storybook sailor who sails the sea and often looks for treasure."),
        QAItem(question="What is foreshadowing?", answer="Foreshadowing is a clue that hints something important may happen later."),
        QAItem(question="What is a piddle?", answer="A piddle is a little puddle of water or a small wet splash on the ground."),
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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    out.append(f"  fired={sorted(world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
% An activity is valid when the prize is worn on a region the activity splashes.
valid(Place, Act, Prize) :- affords(Place, Act), splashes(Act, Region), worn_on(Prize, Region), has_gear(Act, Prize).
has_gear(Act, Prize) :- gear(G), mess_of(Act, M), guards(G, M), covers(G, R), worn_on(Prize, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for prid, prize in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("worn_on", prid, prize.region))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
        for r in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
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


CURATED = [
    StoryParams(place="harbor", activity="piddle", prize="boots", name="Mira", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="dock", activity="pirate", prize="cloak", name="Finn", gender="boy", parent="father", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
