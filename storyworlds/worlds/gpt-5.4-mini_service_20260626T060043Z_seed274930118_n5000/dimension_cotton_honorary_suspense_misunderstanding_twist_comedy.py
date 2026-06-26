#!/usr/bin/env python3
"""
storyworlds/worlds/dimension_cotton_honorary_suspense_misunderstanding_twist_comedy.py
======================================================================================

A small comedic story world about a child, a cotton prize, and a tense little
misunderstanding around dimensions.

Seed tale premise:
- A child is proud of an honorary cotton costume piece.
- A grown-up worries it will not fit through a narrow opening or into a small
  display box.
- Everyone gets confused about what "dimension" means.
- The turn reveals the real problem and the fix is funny, gentle, and concrete.

This world keeps the story child-facing and state-driven:
- physical meters track fit, cleanliness, wrinkles, and damage;
- emotional memes track suspense, confusion, pride, and relief;
- the story resolves through a believable compromise rather than a frozen
  paraphrase.

Features included:
- Suspense
- Misunderstanding
- Twist
- Comedy
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    container: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["clean", "wrinkled", "stretched", "damaged", "fit", "narrowness", "dust"]:
            self.meters.setdefault(k, 0.0)
        for k in ["pride", "suspense", "confusion", "relief", "joy", "worry", "amusement"]:
            self.memes.setdefault(k, 0.0)

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
    narrowness: float
    dust: float


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


class World:
    def __init__(self, setting: Setting) -> None:
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
        clone.facts = dict(self.facts)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_narrow_damage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if not world.zone:
                continue
            if item.region not in world.zone:
                continue
            if world.setting.narrowness < THRESHOLD:
                continue
            sig = ("narrow", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wrinkled"] += 1
            item.meters["fit"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got wrinkled in the squeeze.")
    return out


def _r_dusty(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if world.setting.dust < THRESHOLD:
                continue
            if "torso" != item.region and "head" != item.region:
                continue
            sig = ("dust", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dust"] += 1
            item.meters["clean"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} picked up a little dust.")
    return out


def _r_confusion(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["confusion"] < THRESHOLD:
            continue
        sig = ("confusion", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["suspense"] += 1
        return [f"{actor.id} kept wondering what the strange word meant."]
    return []


CAUSAL_RULES = [
    Rule("narrow_damage", _r_narrow_damage),
    Rule("dusty", _r_dusty),
    Rule("confusion", _r_confusion),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting, act: Activity) -> str:
    if setting.narrowness >= THRESHOLD:
        return f"The doorway looked extra skinny, like it had swallowed its dinner too fast."
    if setting.dust >= THRESHOLD:
        return f"The room was sunny and dusty, and every shelf looked a little sneezy."
    return f"The room waited quietly for the next silly idea."


def select_gear(act: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if act.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, act: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), act, narrate=False)
    prize = sim.get(prize_id)
    return {
        "wrinkled": prize.meters["wrinkled"] >= THRESHOLD,
        "dusty": prize.meters["dust"] >= THRESHOLD,
    }


def do_activity(world: World, actor: Entity, act: Activity, narrate: bool = True) -> None:
    world.zone = set(act.zone)
    actor.memes["joy"] += 1
    actor.meters[act.mess] += 1
    propagate(world, narrate=narrate)


def tell(world_setting: Setting, act: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(world_setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    hero.memes["pride"] += 1
    hero.memes["suspense"] += 1

    world.say(f"{hero.id} was a {trait} {hero.type} who loved {act.gerund}.")
    world.say(f"{hero.id} also loved {prize.phrase}, especially because it looked so official and shiny.")
    world.say(f"That morning, {hero.id}'s {parent.label} said the prize was honorary, which made {hero.id} stand up straighter.")

    world.para()
    world.say(f"At {world_setting.place}, {setting_detail(world_setting, act)}")
    world.say(f"{hero.id} wanted to {act.verb}, but the word \"dimension\" kept making everyone pause.")
    world.say(f"{hero.id} thought a dimension was a magic doorway. {parent.label} thought it was a measurement. Neither was helping.")

    world.para()
    world.say(f"Then came the suspense: would {prize.label} get ruined if {hero.id} tried to go through the tight space?")
    pred = predict_mess(world, hero, act, prize.id)
    if pred["wrinkled"] or pred["dusty"]:
        world.say(f"{parent.label.capitalize()} frowned a little and warned, \"That could make the {prize.label} all silly and messy.\"")
    hero.memes["confusion"] += 1
    world.say(f"{hero.id} tried to {act.rush}, but stopped when {parent.label} held up a gentle hand.")
    world.say(f"\"Wait,\" {hero.id} said, \"you mean the size of the doorway, not a superhero universe?\"")
    world.say(f"\"Exactly,\" said {parent.label}. \"This dimension is just very, very short.\"")

    world.para()
    gear_def = select_gear(act, prize)
    if gear_def is None:
        raise StoryError("No reasonable fix exists for this combination.")
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    world.say(f"Twist time: the \"cotton\" thing was not a trap at all. It was a soft cover made to keep the {prize.label} neat.")
    world.say(f"{parent.label.capitalize()} smiled and said, \"How about we {gear_def.prep} first?\"")
    hero.memes["confusion"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["amusement"] += 1
    hero.memes["joy"] += 1
    world.say(f"{hero.id} laughed so hard that the whole problem felt smaller than a button.")
    world.say(f"They {gear_def.tail}, and soon {hero.id} was {act.gerund} without ruining the {prize.label}.")
    world.say(f"In the end, the honorary cotton prize stayed neat, the doorway stayed silly, and everybody learned the meaning of the word with a grin.")

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=act,
        gear=gear_def,
        setting=world_setting,
        trait=trait,
    )
    return world


SETTINGS = {
    "hallway": Setting(place="the hallway", narrowness=1.0, dust=0.0),
    "clubroom": Setting(place="the clubroom", narrowness=0.0, dust=1.0),
    "stage": Setting(place="the stage door", narrowness=1.0, dust=1.0),
}

ACTIVITIES = {
    "squeeze": Activity(
        id="squeeze",
        verb="squeeze through the tiny doorway",
        gerund="squeezing through tiny doorways",
        rush="dash through the doorway",
        mess="wrinkled",
        soil="all wrinkled",
        zone={"torso"},
        keyword="dimension",
        tags={"dimension", "suspense"},
    ),
    "display": Activity(
        id="display",
        verb="set the prize on the display shelf",
        gerund="arranging careful displays",
        rush="set the prize on the shelf",
        mess="dust",
        soil="a little dusty",
        zone={"torso"},
        keyword="cotton",
        tags={"cotton", "comedy"},
    ),
    "peek": Activity(
        id="peek",
        verb="peek inside the little box",
        gerund="peeking into tiny boxes",
        rush="lean into the box",
        mess="wrinkled",
        soil="scrunched up",
        zone={"head", "torso"},
        keyword="honorary",
        tags={"honorary", "misunderstanding"},
    ),
}

PRIZES = {
    "sash": Prize(
        label="cotton sash",
        phrase="an honorary cotton sash",
        type="sash",
        region="torso",
    ),
    "badge": Prize(
        label="cotton badge",
        phrase="an honorary cotton badge",
        type="badge",
        region="torso",
    ),
    "cap": Prize(
        label="cotton cap",
        phrase="an honorary cotton cap",
        type="cap",
        region="head",
    ),
}

GEAR = [
    Gear(
        id="flatbox",
        label="a flat cotton box",
        covers={"torso", "head"},
        guards={"wrinkled", "dust"},
        prep="put the prize into the flat cotton box",
        tail="slid the prize into the flat cotton box",
    ),
    Gear(
        id="apron",
        label="a cotton apron",
        covers={"torso"},
        guards={"dust"},
        prep="wear a cotton apron first",
        tail="wore the cotton apron and walked proudly",
    ),
    Gear(
        id="roll",
        label="a neat rolling wrap",
        covers={"torso", "head"},
        guards={"wrinkled"},
        prep="roll the prize gently in a neat wrap",
        tail="rolled the prize gently in the wrap",
    ),
]

GIRL_NAMES = ["Mia", "Luna", "Nora", "Pip", "Tia"]
BOY_NAMES = ["Ollie", "Finn", "Theo", "Max", "Ari"]
TRAITS = ["silly", "bright", "curious", "proud", "bouncy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in ACTIVITIES:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    if select_gear(act, prize):
                        combos.append((place, act_id, prize_id))
    return combos


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short comedy story for a child about "{act.keyword}", a cotton prize, and a funny misunderstanding about dimensions.',
        f"Tell a story where {hero.id} wants to {act.verb}, but {parent.label} worries about {prize.phrase}.",
        f"Write a gentle suspense story that ends with a twist about the word dimension and a neat cotton fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}, and the whole scene became funny because everyone argued about what dimension meant.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {prize.label}?",
            answer=f"{parent.label.capitalize()} worried the {prize.label} might get wrinkled or dusty if {hero.id} rushed through the narrow place.",
        ),
        QAItem(
            question=f"What was the misunderstanding in the story?",
            answer=f"The misunderstanding was that {hero.id} thought dimension meant a magic world, while {parent.label} meant the size of the doorway or box.",
        ),
        QAItem(
            question=f"What was the twist at the end?",
            answer=f"The twist was that the cotton item was a safe, neat cover and not a problem at all, so {hero.id} could keep the honorary prize clean.",
        ),
    ]
    if f.get("gear"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"It helped by protecting the {prize.label} while {hero.id} moved through the tight, dusty place.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    if "cotton" in tags:
        out.append(QAItem(
            question="What is cotton?",
            answer="Cotton is a soft plant fiber that people use to make clothes, cloth, and cozy covers.",
        ))
    if "dimension" in tags:
        out.append(QAItem(
            question="What is a dimension?",
            answer="A dimension is a way to describe size, like how long, wide, or tall something is.",
        ))
    if "honorary" in tags:
        out.append(QAItem(
            question="What does honorary mean?",
            answer="Honorary means given as a special honor, even if it is mostly for fun or celebration.",
        ))
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.protective:
            parts.append(f"covers={sorted(e.covers)}")
        if e.region:
            parts.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hallway", activity="squeeze", prize="sash", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="clubroom", activity="display", prize="badge", name="Ollie", gender="boy", parent="father", trait="bouncy"),
    StoryParams(place="stage", activity="peek", prize="cap", name="Nora", gender="girl", parent="mother", trait="silly"),
]


def explain_rejection(act: Activity, prize: Prize) -> str:
    return f"(No story: this activity does not reasonably threaten the {prize.label}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: {PRIZES[prize_id].label} is not a typical {gender}'s item here.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
has_fix(A,P) :- gear(G), prize_at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- setting(Place), affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.narrowness >= THRESHOLD:
            lines.append(asp.fact("narrow", sid))
        if s.dust >= THRESHOLD:
            lines.append(asp.fact("dusty", sid))
        for a in ACTIVITIES:
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for guard in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, guard))
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
    ap = argparse.ArgumentParser(description="A comedic story world about cotton, dimensions, and a funny misunderstanding.")
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
        if pr.region not in act.zone:
            raise StoryError(explain_rejection(act, pr))
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
