#!/usr/bin/env python3
"""
storyworlds/worlds/commentary_mud_initiative_conflict_twist_sound_effects.py
=============================================================================

A standalone story world about a child who loves commentary, mud, initiative,
conflict, twist, and sound effects.

The premise is a comedy-friendly muddy outing:
- a child loves narrating everything like a tiny announcer,
- the child wants to jump into a muddy game right away,
- a parent worries about a clean shirt getting ruined,
- a sibling turns the situation into a funny twist,
- the family finds a safe, silly compromise that still feels exciting.

The world is small, typed, and state-driven:
- physical meters track mud and cleanliness,
- emotional memes track joy, conflict, initiative, and surprise,
- story beats are produced from the live model instead of a fixed template.
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

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meter(key) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.meme(key) + amount

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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoor: bool
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
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meter("mud") < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.add_meter("mud", 1.0)
            item.add_meter("dirty", 1.0)
            out.append(f"{actor.id}'s {item.label} got muddy.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.meme("initiative") < THRESHOLD or actor.meme("warned") < THRESHOLD:
            continue
        if actor.meme("conflict") >= THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.add_meme("conflict", 1.0)
        return [f"__conflict__"]
    return []


CAUSAL_RULES = [
    _r_soil,
    _r_conflict,
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


def predict_soil(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "soiled": prize.meter("dirty") >= THRESHOLD,
        "conflict": actor.meme("conflict") >= THRESHOLD or actor.meme("initiative") >= THRESHOLD,
    }


def activity_sound(activity: Activity) -> str:
    return {
        "mud_run": "squish-squash",
        "mud_puddle": "plop-plip",
    }.get(activity.id, "thump-bloop")


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little comedian who loved commentary and sound effects."
    )
    world.say(
        f"{hero.pronoun().capitalize()} could make a walk to the mailbox sound like a parade."
    )


def loves(world: World, hero: Entity, activity: Activity) -> None:
    hero.add_meme("joy", 1.0)
    hero.add_meme("initiative", 1.0)
    world.say(
        f"{hero.id} loved to narrate every move: \"{activity_sound(activity)}!\" "
        f"and then the whole yard felt like a silly sports show."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"That morning, {hero.id}'s {parent.label_word} bought {hero.pronoun('object')} "
        f"{prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.add_meme("love", 1.0)
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} "
        f"like the star of a tiny comedy show."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One rainy day, " if world.weather == "rainy" else "One day, "
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to {world.setting.place}."
    )
    world.say("The mud waited there with a glossy, squishy shine.")
    world.say(
        f"{hero.id} shouted, \"{activity_sound(activity)}!\" and pointed like an announcer."
    )


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.add_meme("initiative", 1.0)
    world.say(
        f"{hero.id} wanted to jump into the mud right away and do the commentary at the same time."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_soil(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    hero.add_meme("warned", 1.0)
    clause = f"You'll get your {prize.label} all muddy"
    clause += f", and then I'll have to wash {prize.it()}"
    world.say(
        f"\"{clause},\" {hero.pronoun('possessive')} {parent.label_word} said, trying not to laugh."
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.add_meme("initiative", 1.0)
    world.say(
        f"{hero.id} took a dramatic step forward anyway."
    )
    world.say(
        f"{hero.pronoun().capitalize()} made the loudest \"{activity_sound(activity)}!\" yet."
    )


def grab(world: World, parent: Entity, hero: Entity) -> None:
    hero.add_meme("conflict", 1.0)
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.pronoun('possessive')} {parent.label_word} grabbed {hero.pronoun('possessive')} hand and said, "
        f"\"Hold on, superstar. We need a safer gag.\""
    )


def twist(world: World, sibling: Entity, hero: Entity, activity: Activity) -> None:
    sibling.add_meme("twist", 1.0)
    world.say(
        f"Just then, {sibling.id} marched in wearing a huge grin and a bucket."
    )
    world.say(
        f"\"Not mud mud,\" {sibling.id} whispered. \"It's the comedy mud for the prank contest.\""
    )
    world.say(
        f"{hero.id} blinked. The big muddy pile was actually stage-safe brown pudding with a rubber chicken on top."
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    if predict_soil(world, hero, activity, prize.id)["soiled"] is False:
        return None
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
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label_word} smiled and said, "
        f"\"How about we {gear_def.prep} first?\""
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.add_meme("joy", 1.0)
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} laughed so hard that even the mud looked amused."
    )
    world.say(
        f"Soon they {gear_def.tail}, and {hero.id} could still do {hero.pronoun('possessive')} funny commentary."
    )
    world.say(
        f"{hero.id} hopped in place, the pudding splash went {activity_sound(activity)}, and "
        f"{prize.label} stayed clean while everybody giggled."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Mina",
    hero_type: str = "girl",
    hero_traits: Optional[list[str]] = None,
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={},
        memes={},
    ))
    hero.memes.update({"joy": 0.0, "initiative": 0.0})

    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        meters={},
        memes={},
    ))
    sibling = world.add(Entity(
        id="Pip",
        kind="character",
        type="boy",
        label="the sibling",
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

    intro(world, hero)
    loves(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab(world, parent, hero)

    world.para()
    twist(world, sibling, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        sibling=sibling,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear_def,
        conflict=hero.meme("conflict") >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "backyard": Setting(place="the backyard", indoor=False, affords={"mud_run"}),
}

ACTIVITIES = {
    "mud_run": Activity(
        id="mud_run",
        verb="run through the mud",
        gerund="running through mud",
        rush="dash into the mud",
        mess="mud",
        soil="all muddy",
        zone={"feet", "legs", "torso"},
        weather="rainy",
        keyword="mud",
        tags={"mud", "initiative", "conflict", "twist", "sound effects", "comedy"},
    ),
    "mud_puddle": Activity(
        id="mud_puddle",
        verb="jump in the mud puddle",
        gerund="jumping in the mud puddle",
        rush="leap into the puddle",
        mess="mud",
        soil="muddy and spotted",
        zone={"feet", "legs"},
        weather="rainy",
        keyword="mud",
        tags={"mud", "initiative", "sound effects", "comedy"},
    ),
}

PRIZES = {
    "shirt": Prize(
        label="shirt",
        phrase="a bright clean shirt",
        type="shirt",
        region="torso",
    ),
    "overalls": Prize(
        label="overalls",
        phrase="fresh blue overalls",
        type="overalls",
        region="torso",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="boots",
        label="mud boots",
        covers={"feet"},
        guards={"mud"},
        prep="put on the mud boots",
        tail="marched back with the mud boots on",
        plural=True,
    ),
    Gear(
        id="apron",
        label="a silly apron",
        covers={"torso"},
        guards={"mud"},
        prep="put on a silly apron",
        tail="came back wearing the silly apron",
    ),
    Gear(
        id="boots_and_apron",
        label="mud boots and a silly apron",
        covers={"feet", "torso"},
        guards={"mud"},
        prep="put on mud boots and a silly apron",
        tail="came back wearing mud boots and a silly apron",
        plural=True,
    ),
]

NAMES = ["Mina", "Luca", "Nora", "Theo", "Pia", "Finn"]
TRAITS = ["funny", "bossy", "brave", "bubbly", "curious", "cheeky"]


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
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "mud": [("What is mud?", "Mud is wet dirt that squishes and sticks to shoes and clothes.")],
    "initiative": [("What does initiative mean?",
                    "Initiative means starting something on your own and taking the first step.")],
    "conflict": [("What is conflict?", "Conflict is a problem or disagreement between characters.")],
    "twist": [("What is a twist in a story?",
               "A twist is an unexpected change that surprises the characters or the reader.")],
    "sound effects": [("What are sound effects?",
                       "Sound effects are made-up words like boom, squish, or swoosh that help a story feel lively.")],
    "comedy": [("What makes something comedy?",
                 "Comedy is meant to be funny and make people laugh.")],
}

KNOWLEDGE_ORDER = ["mud", "initiative", "conflict", "twist", "sound effects", "comedy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        'Write a short comedy story for a young child about commentary, mud, initiative, conflict, twist, and sound effects.',
        f"Tell a funny story where {hero.id} wants to {act.verb} while wearing {prize.phrase}, but {hero.pronoun('possessive')} {parent.label_word} worries.",
        f"Make a playful story in which a child shouts silly sound effects, meets a muddy problem, and finds a twist that helps everybody laugh.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, sibling, prize, act = f["hero"], f["parent"], f["sibling"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What did {hero.id} love to do in the story?",
            answer=f"{hero.id} loved commentary and sound effects, so every step sounded like a little show.",
        ),
        QAItem(
            question=f"Why did {hero.id}'s {parent.label_word} worry when {hero.id} wanted to {act.verb}?",
            answer=f"{hero.id}'s {parent.label_word} worried because {prize.label} could get muddy if {hero.id} jumped in without protection.",
        ),
        QAItem(
            question=f"What was the funny twist?",
            answer=f"The muddy-looking pile turned out to be a comedy prop, and {sibling.id} helped turn the problem into a joke.",
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"What caused the conflict in the middle of the story?",
            answer=f"The conflict happened when {hero.id} took initiative and tried to dash into the mud even after the warning.",
        ))
    if gear:
        qa.append(QAItem(
            question=f"How did the gear help {hero.id}?",
            answer=f"{gear.label} helped because it protected the important parts of {prize.label} from the mud, so {hero.id} could play and still look clean.",
        ))
    qa.append(QAItem(
        question=f"How did the story end?",
        answer=f"It ended with {hero.id} laughing, making silly commentary, and keeping {prize.label} clean while everyone enjoyed the muddy joke.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
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
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
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


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
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
    ap = argparse.ArgumentParser(
        description="Comedy story world: commentary, mud, initiative, conflict, twist, and sound effects."
    )
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
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError("No valid story fits those explicit choices.")
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
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait], params.parent)
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
    StoryParams(place="backyard", activity="mud_run", prize="shirt", name="Mina", gender="girl", parent="mother", trait="funny"),
    StoryParams(place="backyard", activity="mud_puddle", prize="overalls", name="Theo", gender="boy", parent="father", trait="cheeky"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
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
