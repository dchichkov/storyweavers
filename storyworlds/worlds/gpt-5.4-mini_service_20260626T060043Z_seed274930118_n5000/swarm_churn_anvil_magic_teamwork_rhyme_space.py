#!/usr/bin/env python3
"""
A standalone storyworld for a small Space Adventure domain:
a crew meets a strange swarm, survives the churn of a ship system,
and uses Magic, Teamwork, and Rhyme to save an anvil from disaster.

The world is a tiny, causal simulation with typed entities, meters and memes,
plus an inline ASP twin for a reasonableness gate and registry parity.
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


# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Typed entities
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pilot", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "engineer"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class Setting:
    place: str
    beyond: str
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
        return [e for e in self.entities.values() if e.owner == actor.id and e.region]

    def covered(self, actor: Entity, region: str) -> bool:
        for item in self.worn_items(actor):
            if item.id in self.entities and item.label in {"helmet", "suit"} and region in {"torso", "head"}:
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
            "owner": v.owner, "caretaker": v.caretaker, "region": v.region, "plural": v.plural,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

SETTINGS = {
    "orbit": Setting(place="the bright orbit station", beyond="the blue planet below", affords={"swarm", "churn", "anvil"}),
    "dock": Setting(place="the star dock", beyond="the dark lane of comets", affords={"swarm", "churn"}),
    "moonbase": Setting(place="the moonbase hangar", beyond="the cratered moonscape", affords={"anvil", "churn"}),
}

ACTIVITIES = {
    "swarm": Activity(
        id="swarm",
        verb="follow the swarm",
        gerund="following the swarm",
        rush="dash toward the blinking swarm",
        mess="buzzed",
        soil="buzzed up",
        zone={"head", "torso"},
        keyword="swarm",
        tags={"swarm", "space"},
    ),
    "churn": Activity(
        id="churn",
        verb="calm the churn",
        gerund="calming the churn",
        rush="run to the churned panel",
        mess="shaken",
        soil="shaken and rattling",
        zone={"torso"},
        keyword="churn",
        tags={"churn", "space"},
    ),
    "anvil": Activity(
        id="anvil",
        verb="lift the anvil",
        gerund="lifting the anvil",
        rush="rush to the heavy anvil",
        mess="bumped",
        soil="bumped and dented",
        zone={"hands", "torso"},
        keyword="anvil",
        tags={"anvil", "metal"},
    ),
}

PRIZES = {
    "helmet": Prize(label="helmet", phrase="a silver helmet with a moon visor", type="helmet", region="head"),
    "cloak": Prize(label="cloak", phrase="a starry cloak", type="cloak", region="torso"),
    "boots": Prize(label="boots", phrase="bright rocket boots", type="boots", region="feet", plural=True),
    "gloves": Prize(label="gloves", phrase="soft pilot gloves", type="gloves", region="hands", plural=True),
}

GEAR = [
    Gear(id="bubble", label="a bubble shield", covers={"head", "torso"}, guards={"buzzed", "shaken"}, prep="raise a bubble shield", tail="raised the bubble shield"),
    Gear(id="magnet", label="magnet gloves", covers={"hands"}, guards={"bumped"}, prep="put on magnet gloves", tail="slipped on the magnet gloves", plural=True),
    Gear(id="cloakwrap", label="a cloak wrap", covers={"torso"}, guards={"shaken", "buzzed"}, prep="wrap up in a cloak wrap", tail="wrapped up in the cloak wrap"),
]

GIRL_NAMES = ["Nova", "Luna", "Mira", "Zia", "Aria", "Ivy", "Rin", "Tala"]
BOY_NAMES = ["Jet", "Orin", "Kai", "Leo", "Finn", "Pax", "Nico", "Soren"]
TRAITS = ["brave", "curious", "cheerful", "clever", "spunky", "gentle"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for act in ACTIVITIES.values():
            if actor.meters.get(act.mess, 0) < THRESHOLD:
                continue
            for prize in world.entities.values():
                if prize.owner != actor.id:
                    continue
                if prize.region not in act.zone:
                    continue
                sig = ("damage", actor.id, prize.id, act.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                prize.meters[act.mess] = prize.meters.get(act.mess, 0) + 1
                prize.meters["dirty"] = prize.meters.get("dirty", 0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {prize.label} got {act.soil}.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0) + 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


CAUSAL_RULES = [
    _r_damage,
    _r_worry,
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters.get("dirty", 0) >= THRESHOLD),
        "worry": sum(e.memes.get("worry", 0) for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------

def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"{world.setting.place} cannot support {activity.id}.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved the hush of stars and the hum of engines.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}; it felt like a game made of light.")
    hero.memes["love_play"] = hero.memes.get("love_play", 0) + 1


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} {parent.label} held up a calm hand.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_worry"] = pred["worry"]
    world.say(f'"You\'ll get your {prize.label} {activity.soil}," {parent.label} said. "Let\'s choose a safer way."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0) + 1
    world.say(f"{hero.id} heard the warning, but the pull of the {activity.keyword} was still strong.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["grabbed_by"] = hero.memes.get("grabbed_by", 0) + 1
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    world.say(f"but {hero.pronoun('possessive')} {parent.label} gently grabbed {hero.pronoun('possessive')} hand.")


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        kind="thing",
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        plural=gear_def.plural,
    ))
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        del world.entities[gear.id]
        return None
    world.say(f'{hero.pronoun("possessive").capitalize()} {parent.label} smiled and said, "How about we {gear_def.prep} and {activity.verb} together?"')
    gear.owner = hero.id
    return gear


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    hero.memes["conflict"] = 0.0
    world.say(f'{hero.id} grinned and hugged {hero.pronoun("possessive")} {parent.label}. "Yes, let\'s do it!" {hero.pronoun()} said.')
    world.say(f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, {prize.label} safe and bright, while the stars blinked like tiny cheers.")


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------

def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Nova", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="Captain", kind="character", type=parent_type, label="the captain"))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_activity(world, hero, activity)
    world.say(f"That same day, {parent.label} gave {hero.id} {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} loved {prize.it()} and wore {prize.it()} like a treasure from a comet cave.")

    world.para()
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}, far above {world.setting.beyond}.")
    wants(world, hero, parent, activity)
    warned = warn(world, parent, hero, activity, prize)
    if warned:
        defies(world, hero, activity)
        grab_hand(world, parent, hero)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def is not None:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
        conflict=hero.memes.get("conflict", 0) >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

KNOWLEDGE = {
    "swarm": [("What is a swarm?", "A swarm is a lot of small creatures or machines moving together in one busy group.")],
    "churn": [("What does churn mean?", "Churn means to move around and mix in a restless, busy way.")],
    "anvil": [("What is an anvil?", "An anvil is a very heavy block of metal that people use for hammering and shaping things.")],
    "magic": [("What is magic in a story?", "Magic is a special kind of wonder that can make surprising things happen.")],
    "teamwork": [("What is teamwork?", "Teamwork means people help each other and work together to reach the same goal.")],
    "rhyme": [("What is a rhyme?", "A rhyme is when words sound alike at the end, like cat and hat.")],
    "space": [("Why do space stories feel exciting?", "Space stories feel exciting because they can include rockets, stars, planets, and faraway places.")],
}

KNOWLEDGE_ORDER = ["space", "swarm", "churn", "anvil", "magic", "teamwork", "rhyme"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short Space Adventure story for a child about "{act.keyword}", "{prize.label}", and a gentle rescue.',
        f"Tell a story where {hero.id} and {parent.label} use magic, teamwork, and rhyme to handle the {act.keyword} and protect the {prize.label}.",
        f"Write a bright space tale with a swarm, a churn, and an anvil, ending in a happy plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.type}, and {parent.label}, who help each other in space.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the warning?",
            answer=f"{hero.id} wanted to {act.verb}, because the idea of the {act.keyword} felt exciting and magical.",
        ),
        QAItem(
            question=f"What prize did the captain give {hero.id}?",
            answer=f"The captain gave {hero.id} {prize.phrase}. It was the special prize they wanted to keep safe.",
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"Why did the captain worry about the {prize.label}?",
            answer=f"The captain worried because if {hero.id} went to {act.verb}, the {prize.label} would get {act.soil}. That would make more work, so the captain stopped {hero.id} in time.",
        ))
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did they solve the problem?",
            answer=f"They used {gear.label} and worked together. That teamwork let {hero.id} {act.verb} without ruining the {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"What changed at the end?",
            answer=f"At the end, {hero.id} was happy, the {prize.label} stayed safe, and the crew could smile at the stars.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.update({"magic", "teamwork", "rhyme"})
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- prize_at_risk(A, P), gear(G), guards(G, M), mess_of(A, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
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
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
        if prize.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(prize.genders):
            lines.append(asp.fact("wears", g, pid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, c))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Params / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld: swarm, churn, anvil, magic, teamwork, rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
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
    return f"(No story: {activity.gerund} does not reasonably threaten {prize.label} without a compatible fix.)"


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
    gender = args.gender or rng.choice(sorted(PRIZES[prize_id].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        parent="captain",
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait],
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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
    StoryParams(place="orbit", activity="swarm", prize="helmet", name="Nova", gender="girl", parent="captain", trait="brave"),
    StoryParams(place="orbit", activity="churn", prize="cloak", name="Kai", gender="boy", parent="captain", trait="curious"),
    StoryParams(place="moonbase", activity="anvil", prize="gloves", name="Mira", gender="girl", parent="captain", trait="cheerful"),
]


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
        print(f"{len(combos)} compatible combos:\n")
        for place, act, prize in combos:
            print(f"  {place:8} {act:8} {prize:8}")
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
