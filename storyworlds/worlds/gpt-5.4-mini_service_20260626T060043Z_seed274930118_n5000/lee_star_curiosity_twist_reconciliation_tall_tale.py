#!/usr/bin/env python3
"""
storyworlds/worlds/lee_star_curiosity_twist_reconciliation_tall_tale.py
======================================================================

A small tall-tale storyworld about Lee, a star, curiosity, a twist, and a
reconciliation.

Seed tale premise:
- Lee is a bright-eyed, curious child.
- On a wide night, Lee spots a star and wants to get closer.
- The first plan goes wrong in a tall-tale way: the "star" is not what it
  seemed, and the climb turns into a twist.
- With a grandparent's help, Lee and the adult settle the matter, make amends,
  and end the night together under the real star.

The world is intentionally small:
- one child hero
- one elder helper
- one prized object worn or carried by the hero
- one curious action that can threaten that prize
- one compatible protective fix
- a twist that turns the first guess inside out
- a reconciliation beat that resolves the tension
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
    carried_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["dusty", "scratched", "safe", "workload"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "twist", "relief", "reconciliation", "joy", "love"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "granny"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
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
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    soil: str
    zone: set[str]
    weather: str
    keyword: str = ""
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

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for act in ["dusty", "scratched"]:
            if actor.meters[act] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", item.id, act)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[act] += 1
                out.append(f"{actor.id}'s {item.label_word} got dusty in the wind.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["dusty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("workload", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.meters["workload"] += 1
        out.append(f"That would mean more work for {caretaker.label_word}.")
    return out


CAUSAL_RULES = [
    ("soil", _r_soil),
    ("workload", _r_workload),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
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


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.risk in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters["dusty"] >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.risk] += 1
    actor.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place} was still and bright, with a long window looking out."
    if activity.weather == "night":
        return f"The night wind hummed over {setting.place}, and the stars looked close enough to shout at."
    return f"{setting.place.capitalize()} sat open and wide, like a page waiting for a tall tale."


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little curious {hero.type} with eyes that followed every sparkle in the sky."
    )


def loves_star(world: World, hero: Entity, star: Entity) -> None:
    hero.memes["love"] += 1
    world.say(
        f"{hero.id} loved the {star.label}, because it seemed to wink as if it knew a secret."
    )


def buys(world: World, elder: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"Before the sun went down, {hero.id}'s {elder.label_word} brought home {hero.pronoun('object')} {prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} proudly, as if it had been stitched by a lucky moonbeam."
    )


def arrive(world: World, hero: Entity, elder: Entity, activity: Activity) -> None:
    world.say(
        f"One night, {hero.id} and {hero.pronoun('possessive')} {elder.label_word} went to {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, because {activity.keyword or 'the star'} looked too grand to leave alone."
    )


def warn(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"If you {activity.verb}, your {prize.label} will get {activity.soil}," '
        f"{hero.pronoun('possessive')} {elder.label_word} said. "
        f'"Let us think on it before the night grows wild."'
    )
    hero.memes["worry"] += 1
    return True


def twist(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["twist"] += 1
    world.say(
        f"{hero.id} tried to {activity.rush}, but the shining thing turned out to be no star at all."
    )
    world.say(
        f"It was a tin star pinned to an old weather vane, and the wind had nabbed it clean away."
    )


def compromise(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=elder.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {elder.label_word} smiled and said, "
        f'"How about we {gear_def.prep} and {activity.verb} together?"'
    )
    return gear_def


def reconcile(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["reconciliation"] += 1
    hero.memes["worry"] = 0
    world.say(
        f"{hero.id} nodded, hugged {hero.pronoun('possessive')} {elder.label_word}, and said, "
        f'"I was only chasing the secret."'
    )
    world.say(
        f"They {gear_def.tail}. After that, {hero.id} could {activity.gerund}, "
        f"{prize.label} stayed clean, and the real star shone overhead like a lantern for the whole town."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Lee",
    hero_type: str = "boy",
    elder_type: str = "grandfather",
) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="grandpa",
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=elder.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    star = world.add(Entity(
        id="star",
        kind="thing",
        type="star",
        label="star",
        phrase="a bright star",
    ))

    introduce(world, hero)
    loves_star(world, hero, star)
    buys(world, elder, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, elder, activity)
    wants(world, hero, activity)
    warn(world, elder, hero, activity, prize)
    twist(world, hero, activity)

    world.para()
    gear_def = compromise(world, elder, hero, activity, prize)
    if gear_def:
        reconcile(world, elder, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, elder=elder, prize=prize, star=star, activity=activity, setting=setting, gear=gear_def)
    return world


SETTINGS = {
    "hill": Setting(place="the hill", indoor=False, affords={"reach"}),
    "barn": Setting(place="the barnyard", indoor=False, affords={"reach"}),
    "porch": Setting(place="the porch", indoor=False, affords={"reach"}),
}

ACTIVITIES = {
    "reach": Activity(
        id="reach",
        verb="reach for the star",
        gerund="reaching for the star",
        rush="climb higher toward the star",
        risk="dusty",
        soil="dusty",
        zone={"torso"},
        weather="night",
        keyword="star",
        tags={"star", "night"},
    ),
}

PRIZES = {
    "hat": Prize(
        label="hat",
        phrase="a bright blue hat",
        type="hat",
        region="torso",
    ),
    "coat": Prize(
        label="coat",
        phrase="a long Sunday coat",
        type="coat",
        region="torso",
    ),
    "scarf": Prize(
        label="scarf",
        phrase="a woolly scarf",
        type="scarf",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="a canvas apron",
        covers={"torso"},
        guards={"dusty"},
        prep="put on a canvas apron first",
        tail="walked back with the apron on",
    ),
    Gear(
        id="shawl",
        label="a thick shawl",
        covers={"torso"},
        guards={"dusty"},
        prep="wrap a thick shawl around your shoulders",
        tail="came back wrapped up against the dust",
    ),
]

NAMES = ["Lee", "June", "Bess", "Ollie", "Milo"]
TALL_TALE_TRAITS = ["curious", "bold", "bright-eyed", "restless", "wonder-struck"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str = "Lee"
    gender: str = "boy"
    elder: str = "grandfather"
    trait: str = "curious"
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, elder, act, prize = f["hero"], f["elder"], f["activity"], f["prize"]
    return [
        f'Write a tall-tale story for a child about {hero.id}, a star, and a curious night at {f["setting"].place}.',
        f"Tell a short story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {elder.label_word} worries about {hero.pronoun('possessive')} {prize.label}, then they make up.",
        f'Write a story that includes the words "curiosity", "twist", and "reconciliation" and ends with the real star overhead.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, act, prize = f["hero"], f["elder"], f["activity"], f["prize"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who is this story mostly about?",
            answer=f"It is mostly about {hero.id}, a {hero.memes and 'curious'} {hero.type} who keeps looking toward the star.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {f['setting'].place}?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {elder.label_word} worry about the {prize.label}?",
            answer=f"{elder.label_word} worried because if {hero.id} tried to {act.verb}, the {prize.label} would get {act.soil}.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The shining star was not a sky-star at all. It was a tin star stuck on an old weather vane, caught by the wind.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"{gear.label.capitalize()} covered the part of {hero.id}'s clothes that could get dusty, so the two of them could try the plan safely.",
        ))
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"{hero.id} and {elder.label_word} reconciled, and the real star shone over them while {hero.id}'s {prize.label} stayed clean.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a star?",
            answer="A star is a bright ball of hot light far away in the sky, and on clear nights it can look like a tiny lamp.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to look closer, ask questions, and find out what something really is.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people calm down, talk kindly, and become friendly again after a disagreement.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what the characters thought was true.",
        ),
    ]


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill", activity="reach", prize="hat", name="Lee", gender="boy", elder="grandfather", trait="curious"),
    StoryParams(place="barn", activity="reach", prize="coat", name="Lee", gender="boy", elder="grandfather", trait="bright-eyed"),
    StoryParams(place="porch", activity="reach", prize="scarf", name="Lee", gender="boy", elder="grandfather", trait="restless"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), risk_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
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
        lines.append(asp.fact("risk_of", aid, a.risk))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
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
    ap = argparse.ArgumentParser(description="Tall-tale story world: Lee, a star, curiosity, a twist, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["grandfather", "grandmother"])
    ap.add_argument("--trait", choices=TALL_TALE_TRAITS)
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
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        gender=args.gender or "boy",
        elder=args.elder or "grandfather",
        trait=args.trait or rng.choice(TALL_TALE_TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.elder)
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
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in combos:
            print(f"  {place:8} {act:8} {prize:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
