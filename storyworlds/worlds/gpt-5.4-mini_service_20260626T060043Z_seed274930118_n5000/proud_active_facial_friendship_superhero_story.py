#!/usr/bin/env python3
"""
A Storyweavers world: a small superhero-friendship tale with proud, active,
facial-gesture details and a clear rescue-turn-resolution shape.

A seed-like premise:
- A young superhero feels proud and active, eager to race through the city.
- A close friend worries that the hero's special facial mask will get ruined.
- They argue briefly, then choose a safer plan that still lets them help.
- Friendship ends the story with a bright, shared heroic image.

This is a standalone world script with:
- parameter registries
- world simulation driven by meters + memes
- generated story prose
- grounded story/world Q&A
- inline ASP twin and verification
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
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in {"smudged", "wet", "dusty"}:
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got messy.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
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


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("grabbed_by", 0.0) < THRESHOLD or actor.memes.get("defiance", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0.0) + 1
        return ["__conflict__"]
    return []


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("shared_hope", 0.0) < THRESHOLD:
            continue
        sig = ("friendship", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
        out.append(f"{actor.id} felt braver with a friend nearby.")
    return out


CAUSAL_RULES = [
    _r_soil,
    _r_worry,
    _r_conflict,
    _r_friendship,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
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
    return {
        "soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["active"] = actor.memes.get("active", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} superhero who loved bright capes and big plans.")


def loves_friend(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    world.say(f"{hero.id} and {friend.id} were best friends, and they always teamed up on patrols.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["proud"] = hero.memes.get("proud", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} felt proud and active when {activity.gerund} "
        f"made the whole city seem ready for a rescue."
    )


def has_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} like a real hero gear piece.")


def arrive(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    world.say(f"One day, {hero.id} and {friend.id} hurried to {world.setting.place} to help after the alert sounded.")
    world.say(f"The street lights blinked, and the air felt busy and alive.")


def wants(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but {friend.id} held up a hand "
        f"and asked for a careful plan."
    )


def warn(world: World, friend: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"If you {activity.verb}, your {prize.label} will get {activity.soil}," '
        f"{friend.id} said. \"Let's keep the rescue smart.\""
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    world.say(f"{hero.id} frowned and tried to {activity.rush}, eager to prove {hero.pronoun('object')} could do it alone.")


def grab_conflict(world: World, friend: Entity, hero: Entity) -> None:
    hero.memes["grabbed_by"] = hero.memes.get("grabbed_by", 0.0) + 1
    propagate(world, narrate=False)
    world.say(
        f"But {friend.id} grabbed {hero.pronoun('possessive')} hand and said, "
        f"\"Friends save each other, not just the day.\""
    )


def compromise(world: World, friend: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=friend.id,
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
        f"{friend.id} smiled and pointed to {gear_def.label}. "
        f"\"Try this first, then you can still help.\""
    )
    return gear_def


def accept(world: World, friend: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id}'s face brightened into a proud smile, and {hero.id} nodded to {friend.id}. "
        f"Together they used {gear_def.label}, finished the rescue, and {hero.id} stayed ready for more active hero work."
    )
    world.say(
        f"By the end, {hero.id} was {activity.gerund}, {prize.label} stayed clean, "
        f"and the two friends flew home with matching grins."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Nova", hero_type: str = "girl",
         friend_name: str = "Pip", friend_type: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, label="the friend"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=friend.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    introduce(world, hero)
    loves_friend(world, hero, friend)
    loves_activity(world, hero, activity)
    has_prize(world, hero, prize)

    world.para()
    arrive(world, hero, friend, activity)
    wants(world, hero, friend, activity)
    warn(world, friend, hero, activity, prize)
    defies(world, hero, activity)
    grab_conflict(world, friend, hero)

    world.para()
    gear_def = compromise(world, friend, hero, activity, prize)
    if gear_def:
        accept(world, friend, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
        conflict=hero.memes.get("grabbed_by", 0.0) >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "city": Setting(place="the city square", affords={"dash", "rescue"}),
    "roof": Setting(place="the rooftop", affords={"dash", "rescue"}),
    "park": Setting(place="the park", affords={"dash", "rescue"}),
}

ACTIVITIES = {
    "dash": Activity(
        id="dash",
        verb="dash across the square",
        gerund="dashing across the square",
        rush="race into the square",
        mess="smudged",
        soil="smudged and dusty",
        zone={"face", "torso"},
        keyword="active",
        tags={"active", "city"},
    ),
    "rescue": Activity(
        id="rescue",
        verb="rescue the kite",
        gerund="rescuing the kite",
        rush="run toward the spinning kite",
        mess="wet",
        soil="wet and streaky",
        zone={"face"},
        keyword="friendship",
        tags={"friendship", "hero"},
    ),
}

PRIZES = {
    "mask": Prize(
        label="mask",
        phrase="a bright facial mask",
        type="mask",
        region="face",
    ),
    "visor": Prize(
        label="visor",
        phrase="a clear face visor",
        type="visor",
        region="face",
    ),
    "cape": Prize(
        label="cape",
        phrase="a red cape",
        type="cape",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="goggles",
        label="safety goggles",
        covers={"face"},
        guards={"smudged", "wet"},
        prep="put on safety goggles first",
        tail="put on the safety goggles",
    ),
    Gear(
        id="windmask",
        label="a windproof face shield",
        covers={"face"},
        guards={"smudged", "wet"},
        prep="use a windproof face shield first",
        tail="used the windproof face shield",
    ),
    Gear(
        id="raincloak",
        label="a rain cloak",
        covers={"face", "torso"},
        guards={"wet"},
        prep="pull on a rain cloak first",
        tail="pulled on the rain cloak",
    ),
]

HERO_NAMES = ["Nova", "Skye", "Mira", "Jett", "Rex", "Luna"]
FRIEND_NAMES = ["Pip", "Ivy", "Toby", "Zed", "Mina", "Bea"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "active": [("What does it mean to be active?",
                "Being active means moving around, playing, and using your body a lot.")],
    "friendship": [("What is friendship?",
                   "Friendship is when people care about each other, help each other, and like spending time together.")],
    "mask": [("What is a mask for?",
              "A mask can cover the face for fun, costume play, or to help a superhero look secret and strong.")],
    "visor": [("What does a visor do?",
               "A visor helps shield the eyes and face from wind, dust, or bright light.")],
    "cape": [("Why do superheroes wear capes?",
              "Superheroes wear capes because they look dramatic and can flap behind them while they hurry to help.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    act: Activity = f["activity"]
    prize: Prize = f["prize"]
    return [
        f'Write a short superhero story for a child that includes the word "{act.keyword}" and shows friendship.',
        f"Tell a proud, active hero story where {hero.id} and {friend.id} want to {act.verb}, but "
        f"the {prize.label} might get ruined, so they choose a safer plan.",
        f"Write a gentle superhero adventure about {hero.id}, {friend.id}, and a {prize.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    prize: Entity = f["prize"]
    act: Activity = f["activity"]
    gear = f.get("gear")
    qs = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a young superhero, and {friend.id}, {hero.id}'s close friend.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}, because {hero.id} felt proud and active and wanted to help right away.",
        ),
        QAItem(
            question=f"Why did {friend.id} worry about the {prize.label}?",
            answer=f"{friend.id} worried because if {hero.id} tried to {act.verb}, the {prize.label} would get {act.soil}.",
        ),
    ]
    if f.get("conflict"):
        qs.append(QAItem(
            question=f"What happened when {friend.id} tried to stop {hero.id}?",
            answer=f"{hero.id} tried to rush ahead, but {friend.id} held {hero.pronoun('possessive')} hand and reminded {hero.pronoun('object')} that friends solve problems together.",
        ))
    if f.get("resolved") and gear:
        qs.append(QAItem(
            question=f"How did the friends solve the problem?",
            answer=f"They used {gear.label} so {hero.id} could still {act.verb} without ruining the {prize.label}.",
        ))
        qs.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy, proud, and more connected to {friend.id} after they finished the heroic job together.",
        ))
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add("visor")
    out: list[QAItem] = []
    for key in ["active", "friendship", "mask", "visor", "cape"]:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="city", activity="dash", prize="mask", hero="Nova", hero_type="girl", friend="Pip", friend_type="boy"),
    StoryParams(place="roof", activity="rescue", prize="visor", hero="Skye", hero_type="girl", friend="Ivy", friend_type="girl"),
    StoryParams(place="park", activity="dash", prize="cape", hero="Jett", hero_type="boy", friend="Mina", friend_type="girl"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not reach the {prize.region}, so the {prize.label} would not honestly be at risk.)"
    return f"(No story: nothing in the gear catalog safely protects a {prize.label} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


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
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero friendship story world with proud, active, facial details.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    hero = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    hero_type = args.gender or rng.choice(["girl", "boy"])
    friend_type = args.friend_gender or rng.choice(["girl", "boy"])
    return StoryParams(place=place, activity=activity, prize=prize, hero=hero, hero_type=hero_type, friend=friend, friend_type=friend_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.hero, params.hero_type, params.friend, params.friend_type)
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
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible (place, activity, prize) combos:\n")
        for t in vals:
            print(" ", t)
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
            header = f"### {p.hero}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
