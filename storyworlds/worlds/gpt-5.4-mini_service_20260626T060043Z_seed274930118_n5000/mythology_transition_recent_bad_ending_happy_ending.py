#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mythology_transition_recent_bad_ending_happy_ending.py
===============================================================================================================================

A standalone story world for a small whodunit-flavored mythology transition tale.

Premise:
- A child detective helps during a recent transition between two rooms in a little
  museum-library of myths.
- A treasured myth book risks a bad ending if its last page gets dusty, bent, or torn.
- A careful clue trail leads to a happy ending: the missing page is found, protected,
  and the story is completed.

This script follows the Storyweavers contract:
- self-contained stdlib script
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager imports from storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- inline ASP_RULES twin with Python reasonableness gate
- world state drives prose and Q&A
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
        if not self.meters:
            self.meters = {"dusty": 0.0, "torn": 0.0, "missing": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "curiosity": 0.0, "relief": 0.0, "suspicion": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
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
        clone.facts = dict(self.facts)
        return clone


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("transition", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("spill", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dusty"] = item.meters.get("dusty", 0.0) + 1
            item.meters["torn"] = item.meters.get("torn", 0.0) + 1
            out.append(f"{actor.id}'s {item.label} got dusty and bent.")
    return out


def _r_missing(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("torn", 0.0) < THRESHOLD:
            continue
        if item.meters.get("missing", 0.0) >= THRESHOLD:
            continue
        sig = ("missing", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["missing"] = 1.0
        out.append(f"That made one page slip away from the pile.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("suspicion", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("safe_page", 0.0) < THRESHOLD:
            continue
        sig = ("relief", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["relief"] = actor.memes.get("relief", 0.0) + 1
        actor.memes["worry"] = 0.0
        out.append(f"{actor.id} breathed out, because the clue made sense at last.")
    return out


CAUSAL_RULES = [
    _r_spill,
    _r_missing,
    _r_relief,
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
        "soiled": bool(prize and prize.meters.get("missing", 0.0) >= THRESHOLD),
        "dusty": bool(prize and prize.meters.get("dusty", 0.0) >= THRESHOLD),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.meters["transition"] = actor.meters.get("transition", 0.0) + 1
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.memes.keys() if False), "")
    world.say(f"{hero.id} was a little detective who noticed crumbs, dust, and odd little clues.")


def setup(world: World, hero: Entity, archivist: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} loved old mythology stories, especially the ones about brave guides, "
        f"hidden doors, and endings that changed in the last line."
    )
    world.say(
        f"On a recent morning, {hero.id} and {archivist.label} were helping with a transition "
        f"from the old room to the new one at {world.setting.place}."
    )
    world.say(
        f"Among the boxes was a special {prize.label} with {prize.phrase}, meant for the next reading of a myth."
    )


def arrive(world: World, hero: Entity, archivist: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} looked at the doorway, the labels, and the boxes, because this was a mystery with a simple kind of trouble."
    )
    world.say(
        f"Something had gone wrong during the transition, and the first clue was that the {activity.keyword or activity.id} dust was everywhere."
    )


def wants(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"{hero.id} wanted to solve it before the myth story reached a bad ending, because the last page looked important."
    )
    world.say(
        f"{hero.id} followed the marks and tried to {activity.rush}, hoping the missing page had only slipped away."
    )


def warn(world: World, archivist: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_bad_ending"] = True
    world.say(
        f'"If we are not careful, that {prize.label} could end in a bad ending," {archivist.label} said softly.'
    )
    return True


def clue(world: World, hero: Entity) -> None:
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0.0) + 1
    world.say(
        f"{hero.id} noticed a tiny trail of paper bits near a crate, and that made the mystery feel less random."
    )


def fix(world: World, archivist: Entity, hero: Entity, prize: Entity, gear_def: Gear) -> None:
    world.say(
        f'{archivist.label} smiled. "How about we {gear_def.prep}?"'
    )
    world.say(
        f"{hero.id} helped wrap the {prize.label} in the {gear_def.label}, and the page stopped slipping."
    )
    hero.meters["safe_page"] = 1.0
    hero.memes["suspicion"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    prize.meters["missing"] = 0.0
    prize.meters["safe"] = 1.0
    world.say(
        f"Then the missing page was found tucked inside the book cart, where it had fallen during the recent transition."
    )
    world.say(
        f"They put it back, and the myth finally had a happy ending instead of a bad one."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina", hero_type: str = "girl",
         parent_type: str = "aunt", trait: str = "curious") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"worry": 0, "curiosity": 0, "relief": 0, "suspicion": 0}))
    archivist = world.add(Entity(id="Archivist", kind="character", type=parent_type, label="the archivist"))
    prize = world.add(Entity(
        id="myth_book",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=archivist.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    setup(world, hero, archivist, prize, activity)
    world.para()
    arrive(world, hero, archivist, activity)
    wants(world, hero, activity, prize)
    warn(world, archivist, hero, activity, prize)
    clue(world, hero)
    _do_activity(world, hero, activity, narrate=True)

    world.para()
    gear_def = select_gear(activity, prize)
    if gear_def is not None:
        fix(world, archivist, hero, prize, gear_def)

    world.facts.update(
        hero=hero,
        archivist=archivist,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "museum-library": Setting(place="the museum-library", indoor=True, affords={"transition"}),
    "archive-room": Setting(place="the archive room", indoor=True, affords={"transition"}),
    "reading-room": Setting(place="the reading room", indoor=True, affords={"transition"}),
}

ACTIVITIES = {
    "transition": Activity(
        id="transition",
        verb="help with the transition",
        gerund="helping with the transition",
        rush="follow the labels to the next room",
        mess="dusty",
        soil="lost",
        zone={"torso", "hands"},
        weather="",
        keyword="transition",
        tags={"mythology", "transition", "recent"},
    ),
}

PRIZES = {
    "myth_page": Prize(
        label="myth book",
        phrase="bright gold letters and one last page with a half-finished ending",
        type="book",
        region="torso",
        plural=False,
    ),
    "scroll": Prize(
        label="myth scroll",
        phrase="soft ribbon ties and a silver seal",
        type="scroll",
        region="torso",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="book_cart",
        label="book cart",
        covers={"torso"},
        guards={"dusty"},
        prep="wheel over the book cart and place the book on it first",
        tail="rolled the book cart slowly into the new room",
    ),
    Gear(
        id="archive_sleeve",
        label="archive sleeve",
        covers={"torso"},
        guards={"dusty"},
        prep="slip the page into an archive sleeve first",
        tail="slid the sleeve into the box",
    ),
]

HERO_NAMES = ["Mina", "Nia", "Iris", "June", "Tess", "Lena"]
TRAITS = ["curious", "careful", "brave"]


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
    "mythology": [
        ("What is mythology?", "Mythology is a collection of old stories that people told about gods, heroes, monsters, and the world."),
    ],
    "transition": [
        ("What is a transition?", "A transition is a change from one place, state, or situation to another."),
    ],
    "recent": [
        ("What does recent mean?", "Recent means something happened not long ago."),
    ],
    "book": [
        ("Why should a book be handled carefully?", "A book should be handled carefully so its pages do not get bent, torn, or lost."),
    ],
    "dusty": [
        ("What makes dust gather on books?", "Dust gathers when tiny bits from the air land on surfaces, especially if things are moved around."),
    ],
    "archive_sleeve": [
        ("What is an archive sleeve for?", "An archive sleeve protects a page or picture from dust and bending."),
    ],
    "book_cart": [
        ("Why use a book cart?", "A book cart helps move books safely from one room to another."),
    ],
    "lost": [
        ("What do you do if a page is lost?", "You look carefully for clues, check nearby boxes and corners, and put the page back where it belongs."),
    ],
}

KNOWLEDGE_ORDER = ["mythology", "transition", "recent", "book", "dusty", "archive_sleeve", "book_cart", "lost"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        'Write a short whodunit-style story for a child about mythology, a recent transition, and a missing page.',
        f"Tell a gentle mystery where {hero.id} helps during a transition and keeps the {prize.label} from a bad ending.",
        f"Write a simple story that includes the word '{act.keyword}' and ends with a happy ending after the missing page is found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, archivist, prize, act = f["hero"], f["archivist"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"What was {hero.id} helping with in the story?",
            answer=f"{hero.id} was helping with a recent transition from the old room to the new one.",
        ),
        QAItem(
            question=f"What was special about the {prize.label}?",
            answer=f"It had {prize.phrase}, so it mattered for the next mythology reading.",
        ),
        QAItem(
            question=f"Why did {hero.id} worry about a bad ending?",
            answer=f"{hero.id} worried the missing page would be lost or torn before the myth story could finish properly.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question="How did the story end?",
                answer="The missing page was found and protected, so the myth ended with a happy ending.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: the {prize.label} would not be at risk during this transition.)"
    return f"(No story: nothing in the gear catalog reasonably protects the {prize.label} from this transition.)"


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
    name = args.name or rng.choice(HERO_NAMES)
    gender = args.gender or "girl"
    parent = args.parent or "aunt"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


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
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


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
    ap = argparse.ArgumentParser(description="Whodunit-style mythology transition story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["aunt", "father", "mother", "uncle"])
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


CURATED = [
    StoryParams(place="museum-library", activity="transition", prize="myth_page", name="Mina", gender="girl", parent="aunt", trait="curious"),
    StoryParams(place="archive-room", activity="transition", prize="scroll", name="Iris", gender="girl", parent="mother", trait="careful"),
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
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
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
