#!/usr/bin/env python3
"""
A standalone story world for a small nursery-rhyme domain.

Premise:
A little child loves a sweet prize, but a stench rises from a nearby place.
The warning is real, the child ignores it, and the ending stays bad.

Style:
Short, child-facing, lightly rhymed prose.

This world is intentionally simple:
- typed entities with meters and memes
- a causal model that drives the ending
- a Python reasonableness gate
- an inline ASP twin for parity checks
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
        self.zone: set[str] = set()
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_stench_spoil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("stench", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.region not in world.zone:
                continue
            sig = ("spoil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["stale"] = item.meters.get("stale", 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"The {item.label} went stale and dirty.")
    return out


CAUSAL_RULES = [_r_stench_spoil]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def rhyme_line(*parts: str) -> str:
    return " ".join(p for p in parts if p)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Milo", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={},
        memes={},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        meters={},
        memes={},
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        meters={},
        memes={},
    ))

    trait = next((t for t in (hero_traits or []) if t != "little"), "little")
    world.say(f"Little {trait} {hero_name} had a bright small grin.")
    world.say(f"{hero_name} loved a {prize.phrase}, tucked neat and thin.")
    world.say(f"The day began soft as a lullaby tune, and {setting.place} hummed under the moon.")
    world.para()

    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"But near {setting.place}, there rose a stench so grim.")
    world.say(f"{hero_name} wanted to {activity.verb}, though the smell made the air feel dim.")
    world.say(f'"No, no," said {parent_type} {parent_type if parent_type != "mother" else ""}'.strip())
    world.say(f'"You\'ll spoil your {prize.label} if you go too near that bin."')
    world.para()

    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    world.say(f"But {hero_name} only giggled and tried to {activity.rush}, quick as a kite.")
    world.say(f"The stench blew up strong and nasty in the night.")
    hero.meters["stench"] = hero.meters.get("stench", 0.0) + 1
    world.zone = set(activity.zone)
    propagate(world, narrate=True)
    prize.meters["dirty"] = prize.meters.get("dirty", 0.0) + 1
    prize.meters["stale"] = prize.meters.get("stale", 0.0) + 1
    world.para()

    world.say(f"At last the sweet prize turned sour, and the bright day went blue.")
    world.say(f"{hero_name} stood with a wrinkled face, and there was nothing to do.")
    world.say(f"So the song ended badly; the stench stayed on, and the little one frowned.")
    world.say(f"The prize was ruined, and no happy fix came round.")

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        bad_ending=True,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"bin", "soup"}),
    "barn": Setting(place="the barn", affords={"hay", "bin"}),
    "cellar": Setting(place="the cellar", affords={"bin", "soup"}),
}

ACTIVITIES = {
    "bin": Activity(
        id="bin",
        verb="tip the bin",
        gerund="tipping the bin",
        rush="run to the bin",
        mess="stench",
        soil="stinky",
        zone={"torso"},
        keyword="stench",
        tags={"stench", "stink"},
    ),
    "soup": Activity(
        id="soup",
        verb="stir the soup",
        gerund="stirring the soup",
        rush="skip to the soup pot",
        mess="stench",
        soil="stale",
        zone={"hands", "torso"},
        keyword="stench",
        tags={"stench", "food"},
    ),
    "hay": Activity(
        id="hay",
        verb="poke the hay",
        gerund="poking the hay",
        rush="dash to the hay stack",
        mess="stench",
        soil="musty",
        zone={"torso"},
        keyword="stench",
        tags={"stench", "barn"},
    ),
}

PRIZES = {
    "cake": Prize(
        label="cake",
        phrase="a sweet little cake",
        type="cake",
        region="torso",
        genders={"girl", "boy"},
    ),
    "blanket": Prize(
        label="blanket",
        phrase="a soft white blanket",
        type="blanket",
        region="torso",
        genders={"girl", "boy"},
    ),
    "pie": Prize(
        label="pie",
        phrase="a tiny berry pie",
        type="pie",
        region="torso",
        genders={"girl", "boy"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Milo", "Theo", "Ben", "Finn", "Leo"]
TRAITS = ["little", "cheery", "spry", "busy", "bold"]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} would not reach a {prize.label}. "
        f"Choose a prize worn on the same part of the body as the stench.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s item here; try {ok}.)"


@dataclass
class QARegistry:
    pass


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short nursery rhyme about a child named {hero.id}, a stench, and a ruined {prize.label}.',
        f"Tell a simple story where {hero.id} wants to {act.verb} but {parent.label} warns about the stench.",
        f'Write a rhyming story for a little child that ends badly when "{f["activity"].keyword}" spoils a prize.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do near {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}, even though {parent.label} warned about the stench.",
        ),
        QAItem(
            question=f"What prize got ruined in the story?",
            answer=f"The {prize.label} got spoiled and ended up dirty and stale.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended badly. The stench stayed, the prize was ruined, and no happy fix came.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stench?",
            answer="A stench is a very strong, nasty smell that makes people wrinkle their noses.",
        ),
        QAItem(
            question="Why do people stay away from a stinky bin?",
            answer="They stay away because a stinky bin can smell awful and make the air unpleasant.",
        ),
        QAItem(
            question="What does it mean when something is stale?",
            answer="Stale means old and not fresh anymore, like food or air that has gone bad.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  zone={sorted(world.zone)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def valid_story_params() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
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
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P).
"""


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small nursery-rhyme story world with a stench and a bad ending.")
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
        act = ACTIVITIES[args.activity]
        pr = PRIZES[args.prize]
        if not prize_at_risk(act, pr):
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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait], params.parent)
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
    StoryParams(place="kitchen", activity="bin", prize="cake", name="Milo", gender="boy", parent="mother", trait="cheery"),
    StoryParams(place="barn", activity="hay", prize="blanket", name="Lily", gender="girl", parent="father", trait="spry"),
    StoryParams(place="cellar", activity="soup", prize="pie", name="Nora", gender="girl", parent="mother", trait="bold"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in triples:
            print(f"  {place:8} {act:8} {prize:8}")
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
