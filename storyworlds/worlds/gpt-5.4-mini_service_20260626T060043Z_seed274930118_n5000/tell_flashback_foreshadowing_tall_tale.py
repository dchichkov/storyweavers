#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tell_flashback_foreshadowing_tall_tale.py
================================================================================

A small story world in a tall-tale voice: someone tells a bigger-than-life story,
the past rushes in as a flashback, and a foreshadowing sign warns that the wind
is about to change.

The domain is deliberately tiny:
- a storyteller and a listener
- one brag-worthy object
- one risky activity
- one sensible, compatible fix

The premise is built around the seed word "tell" and the requested instruments:
Flashback and Foreshadowing.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for k in ("stress", "wind", "dust", "safety", "memory"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
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
    risk: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = ""
        self.zone: set[str] = set()

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
        clone.paragraphs = [[]]
        clone.weather = self.weather
        clone.zone = set(self.zone)
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    teller: str
    listener: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "hill": Setting(place="the windy hill", affords={"kite"}),
    "field": Setting(place="the open field", affords={"kite"}),
    "fair": Setting(place="the county fair", affords={"kite"}),
    "yard": Setting(place="the back yard", affords={"kite"}),
}

ACTIVITIES = {
    "kite": Activity(
        id="kite",
        verb="fly the kite",
        gerund="flying the kite",
        rush="run after the kite",
        risk="a hard yank from the wind",
        zone={"hands", "head"},
        keyword="kite",
        tags={"wind", "kite"},
    ),
}

PRIZES = {
    "hat": Prize(
        label="hat",
        phrase="a brand-new straw hat",
        type="hat",
        region="head",
    ),
    "scarf": Prize(
        label="scarf",
        phrase="a bright red scarf",
        type="scarf",
        region="neck",
    ),
}

GEAR = [
    Gear(
        id="stringgloves",
        label="a pair of string gloves",
        covers={"hands"},
        guards={"wind"},
        prep="tie on a pair of string gloves first",
        tail="tied on the string gloves and grinned at the gusts",
    ),
    Gear(
        id="brimstrap",
        label="a chin strap",
        covers={"head"},
        guards={"wind"},
        prep="buckle a chin strap under the hat",
        tail="buckled the chin strap and held the hat firm",
    ),
]

NAMES = ["Mina", "Josie", "Eli", "Ned", "Lottie", "Beau", "Willa", "Otis"]
TELLERS = ["grandma", "grandpa", "uncle", "aunt"]
TRAITS = ["bold", "cheerful", "lively", "roving", "braggy"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and "wind" in gear.guards:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters["wind"] += 1
    actor.memes["giddiness"] += 1
    for item in world.worn_items(actor):
        if item.protective:
            continue
        if item.region in world.zone and not world.covered(actor, item.region):
            item.meters["stress"] += 1
    if narrate:
        world.say(f"{actor.id} tried to {activity.verb}, and the whole sky seemed to lean closer.")


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"ruined": prize.meters["stress"] >= THRESHOLD}


def tell_flashback(world: World, teller: Entity, hero: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{teller.id} began to tell a tall tale so big that the porch boards seemed to listen."
    )
    world.say(
        f'"Once," {teller.pronoun("subject")} said, "I saw {hero.id} get ready to {activity.verb} with {hero.pronoun("possessive")} {prize.label} shining like a new coin."'
    )
    world.say(
        f"Then came the flashback: a year before, a wild gust had nearly whisked the {prize.label} clean away."
    )
    teller.memes["memory"] += 1


def foreshadow(world: World, activity: Activity) -> None:
    world.say(
        f"Over the hill, a dark cloud marched in slow as a wagon, which was foreshadowing enough for any sensible ear."
    )
    world.say(
        f"The breeze sharpened, and even the fence posts seemed to warn that {activity.risk} was close by."
    )


def warn(world: World, teller: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize.id)
    if not pred["ruined"]:
        return False
    world.say(
        f'"If you go now, that {prize.label} may meet {activity.risk}," {teller.id} said, "and I would hate to see it take wing."'
    )
    return True


def accept(world: World, teller: Entity, hero: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["trust"] += 1
    world.say(
        f"{hero.id} nodded, because the old story had turned into good advice."
    )
    world.say(
        f"They chose {gear.label} first, {gear.tail}, and at last {hero.id} was {activity.gerund} with {prize.label} safe and snug."
    )


def tell_story(world: World, teller: Entity, hero: Entity, prize: Entity, activity: Activity) -> None:
    tell_flashback(world, teller, hero, prize, activity)
    world.para()
    foreshadow(world, activity)
    warn(world, teller, hero, activity, prize)
    world.say(f"{hero.id} still wanted to {activity.verb}, as brave as a barn cat in a thunderstorm.")
    gear = select_gear(activity, prize)
    if gear is None:
        raise StoryError("No sensible fix exists for this setup.")
    item = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=teller.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    item.worn_by = hero.id
    world.say(
        f"{teller.id} smiled and said, 'We can tell the wind to wait a spell, then {gear.prep}.'"
    )
    accept(world, teller, hero, activity, prize, gear)
    world.para()
    world.say(
        f"By supper, the cloud had gone sailing off, the kite had danced, and the {prize.label} stayed as proud as a sheriff's badge."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "girl",
         teller_type: str = "grandma") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", "bold"],
    ))
    teller = world.add(Entity(
        id=teller_type,
        kind="character",
        type=teller_type,
        traits=["old", "tall-tale"],
    ))
    listener = world.add(Entity(
        id="listener",
        kind="character",
        type="child",
        traits=["wide-eyed"],
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=teller.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    prize.worn_by = hero.id
    teller.memes["pride"] += 1
    listener.memes["wonder"] += 1
    tell_story(world, teller, hero, prize, activity)
    world.facts.update(
        hero=hero,
        teller=teller,
        listener=listener,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=world.entities.get("stringgloves"),
        resolved=True,
        conflict=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    teller = f["teller"]
    prize = f["prize"]
    activity = f["activity"]
    place = f["setting"].place
    return [
        f'Write a short tall tale for a child that includes the word "tell" and takes place at {place}.',
        f"Tell a lively story where {teller.id} warns {hero.id} about {prize.label} before they {activity.verb}.",
        f"Write a story with a flashback and a foreshadowing sign, ending with {hero.id} safely {activity.gerund}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    teller = f["teller"]
    prize = f["prize"]
    activity = f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who told the tall tale in the story?",
            answer=f"{teller.id} told the tale, and {teller.pronoun('subject')} used the story to warn {hero.id} kindly.",
        ),
        QAItem(
            question=f"What happened in the flashback?",
            answer=f"The flashback showed a past day when a wild gust nearly carried off the {prize.label}. That old trouble helped explain the warning.",
        ),
        QAItem(
            question=f"What did the foreshadowing sign make the reader expect?",
            answer=f"The dark cloud and sharper breeze made it clear that the wind was getting ready to cause trouble.",
        ),
        QAItem(
            question=f"How did they keep the {prize.label} safe?",
            answer=f"They used {gear.label} first, so {hero.id} could {activity.verb} without losing the {prize.label} to the wind.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that steps back to an earlier time so we can understand what happened before.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints that something important or risky may happen soon.",
        ),
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a funny, bigger-than-life story that stretches the facts for style and excitement.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill", activity="kite", prize="hat", name="Mina", gender="girl", teller="grandma", listener="child", trait="bold"),
    StoryParams(place="field", activity="kite", prize="scarf", name="Eli", gender="boy", teller="grandpa", listener="child", trait="lively"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: the activity would not truly threaten the {prize.label}, so there is no honest conflict to tell.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s item here; try {ok}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
compatible(G,A,P) :- prize_at_risk(A,P), covers(G,R), worn_on(P,R), guards(G,wind).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), compatible(_,A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
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
    ap = argparse.ArgumentParser(description="Tall-tale story world with flashback and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--teller", choices=TELLERS)
    ap.add_argument("--listener")
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
    name = args.name or rng.choice(NAMES)
    teller = args.teller or rng.choice(TELLERS)
    listener = args.listener or "listener"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, teller=teller, listener=listener, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.teller)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
