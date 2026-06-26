#!/usr/bin/env python3
"""
storyworlds/worlds/burden_inspection_swimming_pool_cautionary_fairy_tale.py
===========================================================================

A standalone story world for a cautionary fairy tale set at a swimming pool.

Premise:
- A small child dearly wants to swim at a bright pool.
- The child is carrying a burden, and a careful inspection can reveal whether
  that burden is safe near the water.
- A fairy-tale guardian warns the child, and the story turns on choosing the
  lighter, safer option.

This world is deliberately small and constraint-driven:
- physical meters track things like wetness, heaviness, and readiness
- emotional memes track worry, courage, and relief
- the prose is driven by the simulated state, not a frozen template swap

Seed words used by the domain: burden, inspection
Setting: swimming pool
Style: fairy tale
Tone: cautionary
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    protective: bool = False
    floats: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "heavy": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "courage": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "fairy"}
        male = {"boy", "father", "dad", "man", "goblin"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the swimming pool"
    affords: set[str] = field(default_factory=lambda: {"swim", "splash", "dive", "inspect"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    risk: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Burden:
    id: str
    label: str
    phrase: str
    heaviness: float
    can_float: bool = False
    targets: set[str] = field(default_factory=set)
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    protects_from: set[str] = field(default_factory=set)
    reduces_heavy: float = 0.0
    floaty: bool = False


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
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.carried_by == actor.id and not item.protective:
                sig = ("wet_item", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["wet"] += 1
                out.append(f"{item.label.capitalize()} splashed and grew damp.")
    return out


def _r_burden_sinks(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        burden = world.facts.get("burden_entity")
        if burden and burden.carried_by == actor.id:
            item = burden
            if item.protective:
                continue
            sig = ("sink", actor.id, item.id)
            if sig in world.fired:
                continue
            if item.meters["heavy"] < THRESHOLD and item.meters["safe"] < THRESHOLD:
                continue
            world.fired.add(sig)
            actor.memes["worry"] += 1
            out.append("__sinking__")
    return out


RULES = [Rule("wet", _r_wet), Rule("sink", _r_burden_sinks)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__sinking__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def inspect_burden(world: World, inspector: Entity, burden: Entity) -> bool:
    burden.meters["heavy"] = burden.meters.get("heavy", 0.0)
    burden.memes["inspected"] = 1.0
    if burden.heaviness >= 2.0:
        inspector.memes["worry"] += 1
        world.say(
            f"{inspector.pronoun().capitalize()} looked at the {burden.label} during the inspection "
            f"and saw that it was far too heavy for a swim."
        )
        return False
    burden.meters["safe"] = 1.0
    world.say(
        f"{inspector.pronoun().capitalize()} gave the {burden.label} a careful inspection and found "
        f"that it could stay by the pool."
    )
    return True


def _carry(world: World, actor: Entity, burden: Entity) -> None:
    burden.carried_by = actor.id
    burden.meters["heavy"] = burden.heaviness
    actor.meters["heavy"] += burden.heaviness
    actor.memes["joy"] += 1


def _enter_pool(world: World, actor: Entity, activity: Activity) -> None:
    actor.meters["wet"] += 1
    actor.memes["courage"] += 1
    propagate(world, narrate=True)


def _offer_gear(world: World, guardian: Entity, child: Entity, activity: Activity, burden: Entity) -> Optional[Gear]:
    if burden.heaviness < 2.0:
        return None
    gear = GEAR["basket"]
    g = world.add(Entity(
        id=gear.id,
        type="thing",
        label=gear.label,
        protective=True,
        floats=gear.floaty,
        meters={"wet": 0.0, "heavy": 0.0, "safe": 1.0},
    ))
    world.say(
        f"{guardian.pronoun().capitalize()} held up {gear.label} and said, "
        f"\"If we put the {burden.label} there, you may still {activity.verb}.\""
    )
    return g


def tell(setting: Setting, activity: Activity, burden_cfg: Burden,
         hero_name: str = "Mira", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", "bright-eyed"],
        meters={"wet": 0.0, "heavy": 0.0, "safe": 0.0},
        memes={"joy": 1.0, "worry": 0.0, "courage": 0.0, "relief": 0.0},
    ))
    guardian = world.add(Entity(id="Guardian", kind="character", type=parent_type, label="the guardian"))
    burden = world.add(Entity(
        id=burden_cfg.id,
        type="thing",
        label=burden_cfg.label,
        phrase=burden_cfg.phrase,
        owner=hero.id,
        caretaker=guardian.id,
        meters={"wet": 0.0, "heavy": burden_cfg.heaviness, "safe": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "courage": 0.0, "relief": 0.0},
    ))
    world.facts["burden_entity"] = burden
    hero.facts = {}

    world.say(f"{hero.id} was a little {hero_type} who loved the bright swimming pool.")
    world.say(
        f"{hero.pronoun().capitalize()} also had a {burden.label}, a {burden.phrase}, and it felt like a real burden."
    )
    world.say(
        f"One sunny morning, the guardian came for an inspection by the pool and looked at the water, the tiles, and the {burden.label}."
    )

    world.para()
    _carry(world, hero, burden)
    world.say(
        f"{hero.id} wanted to {activity.verb}, even though {hero.pronoun('possessive')} arms were full."
    )
    safe = inspect_burden(world, guardian, burden)
    if not safe:
        world.say(
            f"\"No, little one,\" said the guardian. \"A {burden.label} that heavy can pull you down in the water.\""
        )
        hero.memes["worry"] += 1
        hero.memes["courage"] += 1

    world.para()
    world.say(
        f"{hero.id} tried to {activity.rush}, but the burden made the first step slow and wobbly."
    )
    if burden.heaviness >= 2.0:
        world.say(
            f"Then the burden slipped toward the water, and {hero.id} felt a sharp little fright."
        )
        hero.memes["worry"] += 1

    gear = None
    if burden.heaviness >= 2.0:
        gear = _offer_gear(world, guardian, hero, activity, burden)
        if gear is not None:
            burden.carried_by = None
            burden.meters["heavy"] = 0.0
            burden.meters["safe"] = 1.0
            hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
            hero.memes["relief"] += 1
            world.say(
                f"{hero.id} left the burden in {gear.label} beside the pool."
            )

    world.para()
    _enter_pool(world, hero, activity)
    if gear is not None:
        world.say(
            f"{hero.id} could finally {activity.gerund} while the burden stayed safe and dry."
        )
    else:
        world.say(
            f"{hero.id} swam only after setting the burden aside, and the water felt light again."
        )
    hero.memes["relief"] += 1
    world.say(
        f"By the end, the pool still shone, the burden was no trouble at all, and the guardian smiled at the wise choice."
    )

    world.facts.update(
        hero=hero,
        guardian=guardian,
        burden=burden,
        activity=activity,
        gear=gear,
        resolved=True,
        inspected=True,
    )
    return world


SETTINGS = {
    "pool": Setting(place="the swimming pool"),
}

ACTIVITIES = {
    "swim": Activity(
        id="swim",
        verb="swim",
        gerund="swimming",
        rush="dash toward the deep end",
        mess="wet",
        soil="soaked",
        risk="a burden in the water can drag a child down",
        keyword="swim",
        tags={"water", "safety"},
    ),
    "splash": Activity(
        id="splash",
        verb="splash",
        gerund="splashing",
        rush="run straight into the shallow water",
        mess="wet",
        soil="drenched",
        risk="a burden makes slipping easier",
        keyword="splash",
        tags={"water", "safety"},
    ),
    "dive": Activity(
        id="dive",
        verb="dive",
        gerund="diving",
        rush="leap from the pool edge",
        mess="wet",
        soil="sopping",
        risk="a burden makes a leap unsafe",
        keyword="dive",
        tags={"water", "safety"},
    ),
}

BURDENS = {
    "bucket": Burden(
        id="bucket",
        label="bucket",
        phrase="a little pail of pebbles",
        heaviness=2.5,
        can_float=False,
        targets={"swim", "dive"},
    ),
    "book": Burden(
        id="book",
        label="book",
        phrase="a storybook with gold corners",
        heaviness=1.5,
        can_float=False,
        targets={"swim", "splash"},
    ),
    "crown": Burden(
        id="crown",
        label="crown",
        phrase="a tiny crown of polished brass",
        heaviness=2.0,
        can_float=False,
        targets={"swim", "dive"},
    ),
}

@dataclass
class GearSpec:
    id: str
    label: str
    floaty: bool = False

GEAR = {
    "basket": GearSpec(id="basket", label="a wicker basket", floaty=True),
}

GIRL_NAMES = ["Mira", "Lina", "Iris", "Elsa", "Nora"]
BOY_NAMES = ["Owen", "Toby", "Finn", "Theo", "Robin"]


@dataclass
class StoryParams:
    place: str
    activity: str
    burden: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for act_id, act in ACTIVITIES.items():
            for burden_id, burden in BURDENS.items():
                if act_id in burden.targets and burden.heaviness >= 1.5:
                    combos.append((place, act_id, burden_id))
    return combos


def prize_at_risk(activity: Activity, burden: Burden) -> bool:
    return activity.id in burden.targets


def select_gear(activity: Activity, burden: Burden) -> Optional[GearSpec]:
    if burden.heaviness >= 2.0:
        return GEAR["basket"]
    return None


def explain_rejection(activity: Activity, burden: Burden) -> str:
    if not prize_at_risk(activity, burden):
        return "(No story: that burden would not create a meaningful pool caution.)"
    return "(No story: the burden is too light to require a fairy-tale inspection and cautionary turn.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.burden:
        act = ACTIVITIES[args.activity]
        bur = BURDENS[args.burden]
        if not (prize_at_risk(act, bur) and select_gear(act, bur)):
            raise StoryError(explain_rejection(act, bur))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.burden is None or c[2] == args.burden)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, burden = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, burden=burden, name=name, gender=gender, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, guardian, burden, activity = f["hero"], f["guardian"], f["burden"], f["activity"]
    return [
        f'Write a fairy-tale cautionary story set at {world.setting.place} about a child named {hero.id} and a burden.',
        f"Tell a short story where {hero.id} wants to {activity.verb} but {guardian.label} insists on an inspection first.",
        f'Write a child-friendly cautionary tale that uses the words "burden" and "inspection" and ends safely at the pool.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guardian, burden, activity = f["hero"], f["guardian"], f["burden"], f["activity"]
    qa = [
        QAItem(
            question=f"Who was the story about at {world.setting.place}?",
            answer=f"It was about {hero.id}, a little {hero.type}, and the burden {hero.pronoun('possessive')} guardian noticed during the inspection.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do by the swimming pool?",
            answer=f"{hero.id} wanted to {activity.verb}, even though carrying the {burden.label} made the choice risky.",
        ),
        QAItem(
            question="Why did the guardian warn the child?",
            answer=f"The guardian warned {hero.id} because the burden was heavy, and a heavy burden near water can make swimming unsafe.",
        ),
        QAItem(
            question="What changed by the end of the tale?",
            answer=f"By the end, the burden stayed safely by the pool, and {hero.id} could enjoy the water without danger.",
        ),
    ]
    if f.get("gear") is not None:
        qa.append(
            QAItem(
                question="How did the wicker basket help?",
                answer=f"The wicker basket gave the burden a safe place to rest, so {hero.id} could {activity.verb} without carrying it into the pool.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    burden = world.facts["burden"]
    act = world.facts["activity"]
    out = [
        QAItem(
            question="What is a burden?",
            answer="A burden is something heavy or troublesome that someone must carry or manage.",
        ),
        QAItem(
            question="What is an inspection?",
            answer="An inspection is a careful look to check whether something is safe, clean, or ready.",
        ),
        QAItem(
            question="Why should heavy things stay away from the edge of a swimming pool?",
            answer="Heavy things can slip, splash, or pull someone off balance near water, so it is safer to set them aside first.",
        ),
    ]
    if burden.heaviness >= 2.0:
        out.append(
            QAItem(
                question="Why can a wicker basket be useful?",
                answer="A wicker basket can hold things neatly and give them a stable place to rest.",
            )
        )
    if act.id in {"swim", "splash", "dive"}:
        out.append(
            QAItem(
                question="What is a swimming pool?",
                answer="A swimming pool is a place filled with water where people can swim, splash, and play carefully.",
            )
        )
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append("protective=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="pool", activity="swim", burden="bucket", name="Mira", gender="girl", parent="mother"),
    StoryParams(place="pool", activity="splash", burden="book", name="Owen", gender="boy", parent="father"),
    StoryParams(place="pool", activity="dive", burden="crown", name="Lina", gender="girl", parent="mother"),
]


ASP_RULES = r"""
prize_at_risk(A, B) :- activity(A), burden(B), targets(B, A).
need_gear(A, B) :- prize_at_risk(A, B), heavy(B).
valid_story(P, A, B) :- setting(P), prize_at_risk(A, B), need_gear(A, B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    for bid, bur in BURDENS.items():
        lines.append(asp.fact("burden", bid))
        if bur.heaviness >= 2.0:
            lines.append(asp.fact("heavy", bid))
        for t in sorted(bur.targets):
            lines.append(asp.fact("targets", bid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    ap = argparse.ArgumentParser(description="A cautionary fairy tale set at a swimming pool.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--burden", choices=BURDENS)
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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], BURDENS[params.burden], params.name, params.gender, params.parent)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.activity} with {p.burden} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
