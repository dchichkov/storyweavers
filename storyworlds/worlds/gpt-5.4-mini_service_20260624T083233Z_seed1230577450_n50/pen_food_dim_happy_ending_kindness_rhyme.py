#!/usr/bin/env python3
"""
storyworlds/worlds/pen_food_dim_happy_ending_kindness_rhyme.py
===============================================================

A small comedy-leaning storyworld about a pen, a dim lunch, and a kind
rhyming fix that ends happily.

Seed-tale sketch:
---
A little child loved a shiny pen and wanted to use it at lunch to make silly
rhymes on place cards. The lunch table was dim, the ink was a little too eager,
and the child's shirt was new. A grown-up worried the shirt would get marked,
but the child kept trying to write a funny poem anyway. In the end, kindness
won: they found a proper apron, made a rhyme, and the lunch stayed cheerful.
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

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

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
    indoor: bool
    affords: set[str]


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
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"label"}),
    "cafeteria": Setting(place="the cafeteria", indoor=True, affords={"label"}),
    "picnic": Setting(place="the picnic table", indoor=False, affords={"label"}),
}

ACTIVITIES = {
    "label": Activity(
        id="label",
        verb="label the lunch boxes",
        gerund="labeling the lunch boxes",
        rush="scribble faster",
        mess="inky",
        soil="ink-splashed",
        zone={"torso", "hands"},
        weather="",
        keyword="pen",
        tags={"pen", "rhyme", "kindness"},
    )
}

PRIZES = {
    "shirt": Prize(
        label="shirt",
        phrase="a clean new shirt",
        type="shirt",
        region="torso",
    ),
    "apron": Prize(
        label="apron",
        phrase="a bright apron",
        type="apron",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="apron_gear",
        label="an apron",
        covers={"torso"},
        guards={"inky"},
        prep="put on an apron first",
        tail="slipped on the apron and got back to work",
    )
]

GIRL_NAMES = ["Mia", "Nora", "Lila", "Zoe", "Eva"]
BOY_NAMES = ["Noah", "Theo", "Max", "Eli", "Finn"]
TRAITS = ["cheerful", "curious", "silly", "kind", "bouncy"]


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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for pr_id, pr in PRIZES.items():
                if prize_at_risk(act, pr) and select_gear(act, pr):
                    out.append((place, act_id, pr_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: pen, food-dim, kindness, rhyme, and a happy ending.")
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


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not reach the {prize.label}, so there is no honest mess to avoid.)"
    return f"(No story: there is no reasonable gear that protects a {prize.label} from {activity.gerund}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    for item in world.entities.values():
        if item.worn_by == actor.id and item.region in world.zone and not item.protective and not world.covered(actor, item.region):
            item.meters[activity.mess] = item.meters.get(activity.mess, 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            if narrate:
                world.say(f"{actor.pronoun('possessive').capitalize()} {item.label} got inky.")
            if item.caretaker:
                carer = world.get(item.caretaker)
                carer.meters["workload"] = carer.meters.get("workload", 0.0) + 1


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, hero_traits: list[str], parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}, ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", meters={}, memes={}))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region))
    hero.traits = hero_traits  # type: ignore[attr-defined]
    prize.worn_by = hero.id

    world.say(f"{hero.id} was a {hero_traits[0]} little {hero_type} who loved a shiny pen and a funny rhyme.")
    world.say(f"At {setting.place}, {hero.id} wanted to {activity.verb}, because {activity.keyword} felt like magic in a joke.")
    world.say(f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} and hoped the lunch would stay neat.")
    world.para()
    world.say(f"One day, the table was a little too dim for tiny letters, and the pen seemed extra eager.")
    world.say(f"{hero.id} wanted to {activity.rush}, but {hero.pronoun('possessive')} {parent.label_word if hasattr(parent,'label_word') else 'parent'} worried the {prize.label} would get {activity.soil}.")
    if prize_at_risk(activity, prize):
        world.say(f'"You might get your {prize.label} {activity.soil}," {parent.pronoun("possessive") if hasattr(parent,"pronoun") else "their"} parent said. "Let\'s be kind to the shirt."')
    world.say(f"{hero.id} smiled and tried a silly little rhyme instead: " '"Pen in hand, we can be grand!"')
    world.para()
    gear = select_gear(activity, prize)
    if gear:
        gear_ent = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers)))
        gear_ent.worn_by = hero.id
        world.say(f"{hero.id}'s parent found {gear.label} and said, \"{gear.prep}, then you can keep your rhyme.\"")
        world.say(f"{hero.id} giggled, {gear.tail}, and the lunch stayed bright.")
        world.say(f"By the end, the shirt stayed clean, the rhyme was funny, and everyone felt kind.")
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short comedy story for a young child that includes the word "pen" and ends happily.',
        f"Tell a kind story where {hero.id} wants to {act.verb} at {world.setting.place} but worries about {prize.label}, then finds a rhyming fix.",
        f'Write a tiny story with a funny rhyme, a careful parent, and a child who uses a pen without ruining a {prize.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do with the pen?",
            answer=f"{hero.id} wanted to {act.verb}. It was a funny plan, but the grown-up had to think about the {prize.label}.",
        ),
        QAItem(
            question=f"Why was the parent worried about the {prize.label}?",
            answer=f"The parent was worried because the pen could make the {prize.label} {act.soil}. That would mean more cleanup later.",
        ),
        QAItem(
            question=f"What kind thing helped the story end well?",
            answer="Kindness helped. The child listened, tried a silly rhyme, and accepted a safer plan instead of making a mess.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"What helped {hero.id} keep going without ruining the {prize.label}?",
            answer=f"{gear.label} helped because it protected the shirt while {hero.id} kept using the pen and making rhymes.",
        ))
    qa.append(QAItem(
        question="What was funny about the ending?",
        answer=f"The ending was funny because {hero.id} turned a worried moment into a silly rhyme, and then everybody could laugh at lunch.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a pen?", answer="A pen is a tool people use to write or draw with ink."),
        QAItem(question="Why do people wear an apron?", answer="People wear an apron to keep clothes cleaner while they cook or make messy things."),
        QAItem(question="What is a rhyme?", answer="A rhyme is when words sound alike at the end, like cat and hat."),
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
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait, "stubborn"], params.parent)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
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


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py, cl = set(valid_combos()), set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="kitchen", activity="label", prize="shirt", name="Mia", gender="girl", parent="mother", trait="kind"),
    StoryParams(place="cafeteria", activity="label", prize="shirt", name="Noah", gender="boy", parent="father", trait="silly"),
    StoryParams(place="picnic", activity="label", prize="shirt", name="Lila", gender="girl", parent="mother", trait="cheerful"),
]


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
        print(asp_valid_combos())
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
