#!/usr/bin/env python3
"""
storyworlds/worlds/botanic_revolt_squish_riverbank_friendship_mystery_to.py
=============================================================================

A small slice-of-life storyworld set on a riverbank.

Seed premise:
- Two friends spend a quiet afternoon by the river.
- A botanic project gets disrupted by squishy mud and a tiny mystery.
- The children investigate, discover a harmless cause, and learn a gentle lesson
  about plants, patience, and sharing space.

The world is intentionally tiny and constraint-checked: only reasonable
problem/solution pairings are allowed, and the story is driven by world state
rather than a frozen template.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
MESS_KINDS = {"squish", "mud"}
REGIONS = {"feet", "legs", "hands", "torso"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    place: str = "the riverbank"
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
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectThing:
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_squish_dirty(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["squish"] < THRESHOLD and actor.meters["mud"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("dirty", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["squish"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got muddy.")
    return out


def _r_mystery(world: World) -> list[str]:
    if world.facts.get("mystery_solved"):
        return []
    if world.facts.get("clue_seen") and world.facts.get("friend_helped"):
        if ("mystery",) in world.fired:
            return []
        world.fired.add(("mystery",))
        world.facts["mystery_solved"] = True
        return ["__mystery_solved__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule("dirty", "physical", _r_squish_dirty),
    Rule("mystery", "social", _r_mystery),
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
                produced.extend(s for s in sents if s != "__mystery_solved__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: ObjectThing) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: ObjectThing) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
    }


def activity_line(activity: Activity) -> str:
    return {
        "botanic": "the little pots and seed trays looked eager for a gentle hand",
        "squish": "the mud at the riverbank made every step feel like a soft stamp",
        "revolt": "the crowded flowerbed looked as if it wanted more room to breathe",
    }.get(activity.id, "the afternoon felt calm and bright")


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved quiet afternoons by the riverbank.")


def friendship_setup(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"{hero.id} and {friend.id} were best friends, and they liked to spend time "
        f"together doing small, useful things."
    )
    world.say(f"They had come for a {activity.keyword} day, and {activity_line(activity)}.")


def seed_mystery(world: World, hero: Entity, clue: Entity) -> None:
    world.say(
        f"Then {hero.id} noticed something odd: a tiny {clue.label} was gone from the "
        f"botanic tray."
    )
    world.say(
        f"That made the whole patch feel like a mystery to solve."
    )


def worry_and_wonder(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} worried that the little garden work would be ruined if the {activity.mess} "
        f"spread to {prize.label}."
    )
    world.say(
        f"{friend.id} did not laugh; {friend.pronoun()} looked carefully at the path and said, "
        f'"Let’s check the clues."'
    )


def clue_found(world: World, hero: Entity, friend: Entity, clue: Entity, cause: Entity) -> None:
    world.facts["clue_seen"] = True
    world.say(
        f"They followed a soft trail of squish near the river stones and found {cause.phrase}."
    )
    world.say(
        f"It was only {cause.phrase}, not a thief at all, and the missing {clue.label} had simply "
        f"rolled under a leaf."
    )
    world.facts["friend_helped"] = True


def resolve(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["lesson"] += 1
    friend.memes["joy"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f"{hero.id} and {friend.id} brushed off their hands, put the tray back in place, and "
        f"kept working with a little more care."
    )
    world.say(
        f"By the end, the botanic table was neat again, the mystery was solved, and "
        f"{prize.label} stayed clean."
    )
    world.say(
        f"They learned that friends can fix a worry faster when they stay calm and look closely."
    )


SETTING = Setting(place="the riverbank", affords={"botanic", "squish", "revolt"})

ACTIVITIES = {
    "botanic": Activity(
        id="botanic",
        verb="tend the plants",
        gerund="watering little sprouts",
        rush="hurry to the seed trays",
        mess="mud",
        soil="muddy",
        zone={"hands", "feet"},
        keyword="botanic",
        tags={"botanic", "plants"},
    ),
    "squish": Activity(
        id="squish",
        verb="step through the mud",
        gerund="squishing through the mud",
        rush="run over the muddy path",
        mess="squish",
        soil="squishy and messy",
        zone={"feet", "legs"},
        keyword="squish",
        tags={"mud", "squish"},
    ),
    "revolt": Activity(
        id="revolt",
        verb="make room for the plants",
        gerund="moving pots apart",
        rush="move the trays aside",
        mess="mud",
        soil="muddy",
        zone={"hands", "torso"},
        keyword="revolt",
        tags={"plants", "revolt"},
    ),
}

PRIZES = {
    "apron": ObjectThing(
        label="apron",
        phrase="a clean apron with blue pockets",
        type="apron",
        region="torso",
    ),
    "boots": ObjectThing(
        label="boots",
        phrase="little yellow boots",
        type="boots",
        region="feet",
        plural=True,
    ),
    "skirt": ObjectThing(
        label="skirt",
        phrase="a neat green skirt",
        type="skirt",
        region="legs",
        genders={"girl"},
    ),
}

CLUES = {
    "seed": Entity(id="seed", type="thing", label="seed", phrase="a tiny sunflower seed"),
    "leaf": Entity(id="leaf", type="thing", label="leaf", phrase="a curled leaf"),
}

CAUSES = {
    "snail": Entity(id="snail", type="thing", label="snail", phrase="a small snail with a shiny trail"),
}

GEAR = [
    Gear(
        id="rubber_boots",
        label="rubber boots",
        covers={"feet"},
        guards={"squish"},
        prep="put on rubber boots first",
        tail="slipped on the rubber boots",
        plural=True,
    ),
    Gear(
        id="garden_apron",
        label="a garden apron",
        covers={"torso"},
        guards={"mud", "squish"},
        prep="wear a garden apron",
        tail="buttoned up the garden apron",
    ),
]

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Sage", "Pia"]
BOY_NAMES = ["Otis", "Jude", "Ben", "Noah", "Arlo", "Theo"]
TRAITS = ["curious", "gentle", "cheerful", "patient", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    friend: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in {"riverbank": SETTING}.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, act, prize = f["hero"], f["friend"], f["activity"], f["prize"]
    return [
        f'Write a short slice-of-life story for a child about botanic work, a small mystery, and friendship at the riverbank.',
        f"Tell a gentle story where {hero.id} and {friend.id} work at the riverbank, notice a squishy clue, and learn a lesson.",
        f'Write a simple story using the words "botanic", "revolt", and "squish" that ends with a solved mystery and a calm lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, act = f["hero"], f["friend"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The story was about {hero.id} and {friend.id}, two friends at the riverbank.",
        ),
        QAItem(
            question=f"What kind of work were they doing by the river?",
            answer=f"They were doing botanic work, helping little plants and seed trays stay neat and healthy.",
        ),
        QAItem(
            question=f"What made the children think there was a mystery to solve?",
            answer=f"They noticed that a tiny seed was missing from the botanic tray, so they started looking carefully.",
        ),
    ]
    if f.get("mystery_solved"):
        qa.append(
            QAItem(
                question=f"How did they solve the mystery?",
                answer="They followed the soft squish on the path, found a harmless snail trail, and saw that the seed had only rolled under a leaf.",
            )
        )
    if f.get("gear"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did {gear.label} help with the muddy path?",
                answer=f"{gear.label.capitalize()} helped because it kept the wet squish away from the part of the body that needed protecting.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a riverbank?",
            answer="A riverbank is the land right next to a river.",
        ),
        QAItem(
            question="What does botanic mean?",
            answer="Botanic means connected to plants and the study of plants.",
        ),
        QAItem(
            question="Why can mud make shoes messy?",
            answer="Mud is wet dirt, so it sticks to shoes and clothing and leaves them dirty.",
        ),
        QAItem(
            question="Why do friends work well together?",
            answer="Friends can share ideas, help each other, and make hard jobs feel easier.",
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def tell(setting: Setting, activity: Activity, prize_cfg: ObjectThing, hero_name: str, hero_type: str,
         hero_traits: Optional[list[str]] = None, friend_name: str = "Mara") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["curious"])))
    friend_type = "girl" if hero_type == "boy" else "boy"
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, traits=["little", "kind"]))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=hero.id, caretaker=friend.id, region=prize_cfg.region, plural=prize_cfg.plural))
    clue = world.add(copy.deepcopy(CLUES["seed"]))
    cause = world.add(copy.deepcopy(CAUSES["snail"]))

    introduce(world, hero)
    friendship_setup(world, hero, friend, activity)
    world.say(f"They had a botanic kit, a notebook, and a shared wish to keep the riverbank tidy.")
    world.say(f"{hero.id} wore {prize.phrase} because it was their turn to carry the clean things.")

    world.para()
    world.say(f"At the riverbank, {activity_line(activity)}.")
    seed_mystery(world, hero, clue)
    worry_and_wonder(world, hero, friend, activity, prize)
    clue_found(world, hero, friend, clue, cause)

    gear_def = select_gear(activity, prize)
    if gear_def:
        world.say(f"They decided to use {gear_def.label} so the muddy work would stay easy.")
        world.say(
            f'"{gear_def.prep}," {friend.id} said, and {hero.id} nodded.'
        )
        world.say(
            f"That choice kept the {prize.label} clean while they finished the botanic work."
        )

    world.para()
    if gear_def:
        resolve(world, hero, friend, activity, prize, gear_def)
    else:
        world.say(f"Even without special gear, they slowed down, stayed careful, and finished together.")

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
        mystery_solved=True,
    )
    return world


CURATED = [
    StoryParams(
        place="riverbank",
        activity="botanic",
        prize="apron",
        name="Mina",
        gender="girl",
        friend="Jude",
        trait="curious",
    ),
    StoryParams(
        place="riverbank",
        activity="squish",
        prize="boots",
        name="Otis",
        gender="boy",
        friend="Lena",
        trait="thoughtful",
    ),
    StoryParams(
        place="riverbank",
        activity="revolt",
        prize="skirt",
        name="Ivy",
        gender="girl",
        friend="Ben",
        trait="patient",
    ),
]


KNOWLEDGE_ORDER = ["botanic", "squish", "plants", "mud", "revolt"]


ASP_RULES = r"""
% A prize is at risk when the activity reaches the body region it sits on.
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

% Gear is a valid fix only if it guards the mess and covers the at-risk region.
protects(G, A, P) :- prize_at_risk(A, P), gear(G),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).

valid_story(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "riverbank"))
    for a in sorted(SETTING.affords):
        lines.append(asp.fact("affords", "riverbank", a))
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
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo_model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(clingo_model, "valid_story"))
    if py != clingo_set:
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - py:
            print("  only in clingo:", sorted(clingo_set - py))
        if py - clingo_set:
            print("  only in python:", sorted(py - clingo_set))
        return 1
    print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    sample = generate(resolve_params(argparse.Namespace(place=None, activity=None, prize=None, gender=None, name=None, parent=None, trait=None), random.Random(7)))
    if not sample.story.strip():
        print("ERROR: generated empty story")
        return 1
    print("OK: generated story is non-empty.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life riverbank storyworld with botanic work, a small mystery, and friendship.")
    ap.add_argument("--place", choices=["riverbank"])
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--parent", choices=["mother", "father"])
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


def explain_rejection(activity: Activity, prize: ObjectThing) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not reach the {prize.label}, so there is no honest little problem to solve.)"
    return f"(No story: there is no protective gear here that can keep {prize.label} clean during {activity.gerund}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait], params.friend)
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
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
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
