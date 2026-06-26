#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T185554Z_seed424242_n50/knock_earthling_lingo_music_room_mystery_to.py
==============================================================================================================================

A comedy mystery story world: two children (one earthling, one alien) meet in a music room
through a repeating knock pattern and a secret lingo.  The mystery is solved by listening,
the repetition is the knock sequence, and the moral is patience and openness.
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

# Metaphorical mess kinds that represent the "danger" of forcing the box open.
MESS_KINDS = {"forced", "damaged"}

# Body regions used for the gear-coverage constraint (we treat the box lock as a region).
REGIONS = {"lock", "lid"}


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
        female = {"girl", "teacher", "woman"}
        male = {"boy", "man"}
        neutral = {"zorgian", "alien"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label if self.label else self.type


@dataclass
class Setting:
    place: str = "the music room"
    indoor: bool = True
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
    weather: str = ""
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_break(world: World) -> list[str]:
    """If the box is forced (actor has forced meters) and no gear protects the lock, the box gets damaged."""
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["forced"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.type == "box":
                if world.covered(actor, "lock"):
                    continue
                sig = ("break", item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["damaged"] += 1
                out.append(f"The {item.label} gave a sad creak.")
    return out


def _r_scare(world: World) -> list[str]:
    """If the alien is discovered too abruptly, the kids get scared."""
    alien = world.entities.get("Krix")
    if alien and alien.memes["shy"] >= THRESHOLD:
        if not world.facts.get("gentle_intro"):
            sig = ("scare", "kids")
            if sig not in world.fired:
                world.fired.add(sig)
                for actor in world.characters():
                    if actor.type in ("boy", "girl"):
                        actor.memes["fear"] += 1
                out = ["__scare__"]
                return out
    return []


CAUSAL_RULES = [
    Rule(name="break", tag="physical", apply=_r_break),
    Rule(name="scare", tag="social", apply=_r_scare),
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
                produced.extend(s for s in sents if s != "__scare__")
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


def predict_break(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "broken": bool(prize and prize.meters["damaged"] >= THRESHOLD),
    }


# --- Verbs ---
def setting_detail(setting: Setting, activity: Activity) -> str:
    return f"The {setting.place.replace('the ','')} smelled of wood and varnish, and a large piano stood in the corner."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved the {world.setting.place}.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund} and listening to the gentle sounds.")


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One day, {hero.pronoun('possessive')} {parent.label_word} brought a {prize.phrase} into the room.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id  # not really worn, but used for ownership tracking
    world.say(f"{hero.id} loved {prize.it} at once. {hero.pronoun('possessive').capitalize()} eyes sparkled.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} were alone in the room.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} but {hero.pronoun('possessive')} {parent.label_word} said, 'Wait.'")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_break(world, hero, activity, prize.id)
    if not pred["broken"]:
        return False
    world.facts["predicted_damage"] = "damaged"
    world.say(f'"If you force it, you might break {prize.it}," {hero.pronoun("possessive")} {parent.label_word} said.')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning but {hero.pronoun('possessive')} curiosity was stronger.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(f"but {hero.pronoun('possessive')} {parent.label_word} gently took {hero.pronoun('possessive')} hand.")


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(f'{hero.id} pouted. "But I want to know what is inside!" {hero.pronoun()} said.')


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_break(world, hero, activity, prize.id)["broken"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f'{hero.pronoun("possessive").capitalize()} {parent.label_word} smiled. '
              f'"How about we {gear_def.prep}?"')
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id}'s face lit up. 'Yes, let's do it!'")
    world.say(f"They {gear_def.tail}. A soft knock answered, and the {prize.label} opened gently.")
    # Introduce the alien
    alien = world.add(Entity(
        id="Krix", kind="character", type="zorgian", label="a tiny alien",
        phrase="a tiny purple alien with big eyes",
        traits=["shy", "friendly"]
    ))
    world.facts["gentle_intro"] = True
    world.say(f"Inside sat {alien.phrase}. 'Hello, earthling!' it said in a tiny voice.")
    world.say(f"{hero.id} laughed. 'You speak my lingo!' And from that day, they were friends.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mia", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "teacher") -> World:
    world = World(setting)
    world.weather = ""

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "brave"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the teacher"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None)
    return world


# --- Registries ---
SETTINGS = {
    "music_room": Setting(place="the music room", indoor=True, affords={"open_mystery_box"}),
}

ACTIVITIES = {
    "open_mystery_box": Activity(
        id="open_mystery_box",
        verb="open the mysterious box",
        gerund="listening to the mysterious box",
        rush="force the lid open",
        mess="forced",
        soil="damaged",
        zone={"lock"},
        weather="",
        keyword="knock",
        tags={"knock", "mystery"},
    ),
}

GEAR = [
    Gear(
        id="knock_code",
        label="a secret knock pattern",
        covers={"lock"},
        guards={"forced"},
        prep="use the secret knock pattern (knock-knock-knock, pause, knock) first",
        tail="tapped the secret knock pattern on the lid",
        plural=False,
    ),
]

PRIZES = {
    "music_box": Prize(
        label="music box",
        phrase="a beautiful old music box",
        type="box",
        region="lock",
        genders={"girl", "boy"},
    ),
}

GIRL_NAMES = ["Mia", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Sam", "Max"]
TRAITS = ["curious", "playful", "brave", "silly"]


def valid_combos() -> list[tuple[str, str]]:
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


# --- Q&A ---
KNOWLEDGE = {
    "knock": [("What is a knock?",
               "A knock is a sound you make by tapping your hand on a door or a box. "
               "People knock to say 'hello' or to ask if anyone is inside.")],
    "mystery": [("What is a mystery?",
                 "A mystery is something you do not understand yet. You solve it by looking, listening, and thinking.")],
    "music_room": [("What is a music room?",
                    "A music room is a room with instruments like a piano, drums, and xylophones, where you can make sounds and songs.")],
}
KNOWLEDGE_ORDER = ["knock", "mystery", "music_room"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short story for a young child about a mystery in a music room that involves a "knock" sound.',
        f"Tell a funny story where a {hero.type} named {hero.id} tries to solve a mystery with a secret lingo.",
        f'Write a simple story about a music box that knocks and the secret pattern that opens it.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the main {hero.type} in the story?",
            answer=f"The main {hero.type} is {hero.id}, a little {f['prize_cfg'].phrase} fan.",
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"Why did {hero.pronoun('possessive')} {parent.label_word} not want {hero.id} to force the box?",
            answer=f"The {parent.label_word} was worried the box would break if forced. Instead, they used a secret knock pattern.",
        ))
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did the knock pattern help solve the mystery?",
            answer=f"They tapped {gear.label} on the lid, and the box opened gently, revealing a tiny alien who said 'Hello, earthling!'",
        ))
        qa.append(QAItem(
            question=f"What happened after {hero.id} used the knock pattern?",
            answer=f"The box opened, and a friendly alien named Krix appeared. {hero.id} and Krix became friends.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="music_room", activity="open_mystery_box", prize="music_box",
                name="Mia", gender="girl", parent="teacher", trait="curious"),
    StoryParams(place="music_room", activity="open_mystery_box", prize="music_box",
                name="Leo", gender="boy", parent="teacher", trait="brave"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} is not a risk for {prize.label}. Try a prize with region {activity.zone}.)"


# --- ASP twin ---
ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
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
    ap = argparse.ArgumentParser(description="Comedy mystery: knock, earthling, lingo in a music room.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["teacher"])
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
    parent = "teacher"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id,
                       name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "stubborn"], params.parent)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
```
