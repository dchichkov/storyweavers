#!/usr/bin/env python3
"""
A small pirate storyworld with foreshadowing: an athletic young pirate wants to
practice hard, but the captain notices a clue that something valuable may get
ruined unless they choose a safer way.

Seed words included: athletic, hickory, carpet.
Style target: Pirate Tale.
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

    def __post_init__(self):
        if not self.meters:
            self.meters = {"mud": 0.0, "wet": 0.0, "dust": 0.0, "dirty": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "pride": 0.0, "foreshadow": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_soil(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for mess in ("mud", "wet", "dust"):
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                    continue
                sig = ("soil", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                out.append(f"{actor.id}'s {item.label} got {mess} and dirty.")
    return out


def _r_worry(world: World) -> list[str]:
    out = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


CAUSAL_RULES = [_r_soil, _r_worry]


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


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.place == "the ship":
        return "The deck creaked, and a hickory rail shone in the salt light."
    if setting.place == "the harbor":
        return "The harbor smelled of salt and rope, and gulls circled overhead."
    return f"{setting.place.capitalize()} waited in the sea breeze."


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was an athletic little pirate who liked to move fast on deck.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, "
        f"and {activity.keyword} made {hero.pronoun('possessive')} feet feel quick as gull wings."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One calm morning, {parent.label} brought {hero.id} {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} every chance {hero.pronoun()} got.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def foreshadow(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    pred = predict_mess(world, hero, activity, prize.id)
    if pred["soiled"]:
        parent.memes["foreshadow"] = parent.memes.get("foreshadow", 0.0) + 1
        world.say(
            f"{parent.label} noticed a wet patch and a smear of sand near the {prize.label}. "
            f'"That is a clue," {parent.label} said. "If you charge ahead, {prize.label} may get ruined."'
        )


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 0.5
    world.say(f"{hero.id} still wanted to {activity.verb} right away.")


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 0.2
    world.say(f"{hero.id} took a breath, then tried to {activity.rush}.")


def offer(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    if not predict_mess(world, hero, activity, prize.id)["soiled"]:
        return None
    gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, protective=True, covers=set(gear_def.covers), plural=gear_def.plural))
    gear.worn_by = hero.id
    world.say(
        f'{parent.label} smiled and said, "How about we {gear_def.prep} first?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["worry"] = 0
    world.say(
        f"{hero.id} grinned, nodded, and followed the plan. "
        f"Then {hero.pronoun()} was {activity.gerund}, {prize.label} stayed clean, and the crew cheered under the salt wind."
    )


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


SETTINGS = {
    "ship": Setting(place="the ship", indoor=False, affords={"drill", "sprint", "rope"}),
    "harbor": Setting(place="the harbor", indoor=False, affords={"sprint", "rope"}),
    "dock": Setting(place="the dock", indoor=False, affords={"drill", "sprint"}),
}

ACTIVITIES = {
    "drill": Activity(
        id="drill",
        verb="practice deck drills",
        gerund="practicing deck drills",
        rush="dash across the deck",
        mess="mud",
        soil="muddy",
        zone={"feet", "legs"},
        weather="windy",
        keyword="drills",
        tags={"athletic", "mud"},
    ),
    "sprint": Activity(
        id="sprint",
        verb="sprint on the deck",
        gerund="sprinting on the deck",
        rush="charge down the deck",
        mess="wet",
        soil="wet",
        zone={"feet", "legs", "torso"},
        weather="windy",
        keyword="sprint",
        tags={"athletic", "wet"},
    ),
    "rope": Activity(
        id="rope",
        verb="climb the rope",
        gerund="climbing ropes",
        rush="race up the rope",
        mess="dust",
        soil="dusty",
        zone={"feet", "hands", "legs"},
        weather="windy",
        keyword="rope",
        tags={"athletic", "dust"},
    ),
}

PRIZES = {
    "carpet": Prize(
        label="carpet",
        phrase="a hickory carpet for the captain's cabin",
        type="carpet",
        region="floor",
        genders={"girl", "boy"},
    ),
    "coat": Prize(
        label="coat",
        phrase="a bright captain's coat",
        type="coat",
        region="torso",
    ),
    "boots": Prize(
        label="boots",
        phrase="new boots with brass buckles",
        type="boots",
        region="feet",
        plural=True,
    ),
}

GEAR = [
    Gear(id="dryboots", label="dry deck boots", covers={"feet"}, guards={"mud", "wet"}, prep="put on dry deck boots", tail="put on the dry deck boots", plural=True),
    Gear(id="rugcover", label="a hickory mat", covers={"floor"}, guards={"mud", "wet", "dust"}, prep="lay down a hickory mat", tail="laid down the hickory mat"),
    Gear(id="cloak", label="a short rain cloak", covers={"torso"}, guards={"wet"}, prep="wear a short rain cloak", tail="wore the short rain cloak"),
]

GIRL_NAMES = ["Mira", "Nina", "Lena", "Pia", "Ivy"]
BOY_NAMES = ["Jace", "Toby", "Finn", "Owen", "Rafe"]
TRAITS = ["bold", "cheerful", "quick", "brave", "spirited"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a pirate tale for a young child about an athletic {hero.type} named {hero.id} who wants to {act.verb}.',
        f"Tell a story where {parent.label} warns that {prize.phrase} could be ruined, and the warning turns out to be wise.",
        f'Write a short pirate story with the word "hickory" and a clever safer plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little athletic pirate, and {parent.label}, who looked out for {hero.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {act.verb} on the ship.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {prize.label}?",
            answer=f"{parent.label} worried because the activity could leave the {prize.label} {act.soil}, and the story showed that clue before the danger grew worse.",
        ),
    ]
    if f.get("gear"):
        gear = f["gear"]
        qa.append(QAItem(
            question="How did they solve the problem?",
            answer=f"They used {gear.label} first, so {hero.id} could keep going without ruining the {prize.label}.",
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and proud, because {hero.pronoun()} got to play and the {prize.label} stayed safe.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hickory tree known for?",
            answer="Hickory is a very hard kind of wood, so people use it when they want something strong and sturdy.",
        ),
        QAItem(
            question="What is a carpet for?",
            answer="A carpet is a soft floor covering that helps make a room warmer and nicer to walk on.",
        ),
        QAItem(
            question="What does foreshadowing mean in a story?",
            answer="Foreshadowing is when a story gives a small clue early on that hints at what may happen later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        s = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={m} memes={s}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ship", activity="drill", prize="carpet", name="Mira", gender="girl", parent="captain", trait="bold"),
    StoryParams(place="dock", activity="sprint", prize="boots", name="Rafe", gender="boy", parent="captain", trait="quick"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError("That pirate tale would not have a real problem-and-fix.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid pirate story matches those choices.")
    place, activity, prize = rng.choice(sorted(combos))
    p = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(p.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or "captain"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Captain", kind="character", type=parent_type, label="the captain"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)
    world.para()
    arrive(world, hero, parent, activity)
    foreshadow(world, parent, hero, activity, prize)
    wants(world, hero, activity)
    defies(world, hero, activity)
    world.para()
    gear_def = offer(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)
    world.facts = {"hero": hero, "parent": parent, "activity": activity, "prize": prize, "prize_cfg": prize_cfg, "gear": gear_def, "resolved": gear_def is not None}
    return world


def generate(params: StoryParams) -> StorySample:
    hero_type = params.gender
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, hero_type, params.parent)
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
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
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    print("only clingo:", sorted(clingo_set - python_set))
    print("only python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
            params = resolve_params(args, random.Random(seed))
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
