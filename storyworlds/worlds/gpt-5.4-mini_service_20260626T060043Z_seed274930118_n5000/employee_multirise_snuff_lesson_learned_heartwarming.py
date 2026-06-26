#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/employee_multirise_snuff_lesson_learned_heartwarming.py
=================================================================================================

A small, self-contained storyworld about an employee at MultiRise who learns a
gentle lesson the hard way, then makes things right.

Seed-inspired premise:
- employee
- multirise
- snuff
- lesson learned
- heartwarming tone

The world is built as a tiny simulation: an employee, a mentor, a shared place,
a risky action, and a kind compromise that changes the state of the world.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    traits: list[str] = field(default_factory=list)
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
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soot(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("soot", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soot", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["soot"] = item.meters.get("soot", 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label_word} picked up a little soot.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] = carer.meters.get("workload", 0.0) + 1
        out.append(f"That would mean more work for {carer.label_word}.")
    return out


def _r_empathy(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("regret", 0.0) < THRESHOLD:
            continue
        sig = ("empathy", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["kindness"] = actor.memes.get("kindness", 0.0) + 1
        out.append(f"{actor.id} paused and listened more carefully.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("soot", "physical", _r_soot),
    Rule("workload", "physical", _r_workload),
    Rule("empathy", "social", _r_empathy),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def activity_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD),
        "workload": sum(e.meters.get("workload", 0.0) for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("That activity does not fit this setting.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["nervous"] = actor.memes.get("nervous", 0.0) + 1
    propagate(world, narrate=narrate)


def setting_detail(setting: Setting) -> str:
    return f"The {setting.place.removeprefix('the ')} glowed softly after hours."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "kind")
    world.say(f"{hero.id} was a little {trait} {hero.type} who worked at MultiRise.")


def loves(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(f"{hero.id} loved {activity.gerund}, because it made busy days feel calm and useful.")


def workday(world: World, hero: Entity, mentor: Entity, activity: Activity, prize: Entity) -> None:
    world.say(f"One evening at MultiRise, {hero.id} and {mentor.label_word} stayed behind in the lobby.")
    world.say(setting_detail(world.setting))
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} eyes kept landing on {hero.pronoun('possessive')} {prize.label}.")
    world.say(f"{mentor.label_word} gently warned, \"If you {activity.verb}, your {prize.label} could get {activity.soil}.\"")


def regret(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["regret"] = hero.memes.get("regret", 0.0) + 1
    world.say(f"{hero.id} frowned, because the warning was true and a little hard to hear.")
    world.say(f"{hero.id} tried to {activity.rush}, but stopped to think first.")


def compromise(world: World, mentor: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=mentor.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f"{mentor.label_word} smiled and said, \"How about we {gear_def.prep} first?\"")
    return gear_def


def accept(world: World, mentor: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.memes["regret"] = 0.0
    world.say(f"{hero.id} nodded, because the better idea made sense right away.")
    world.say(f"{hero.id} put on {gear_def.label} and then {activity.verb}, while {prize.label} stayed clean.")
    world.say(f"At the end, {hero.id} laughed softly, and {mentor.label_word} looked proud and warm.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str,
         hero_traits: Optional[list[str]] = None, mentor_type: str = "manager") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["careful", "kind"]),
    ))
    mentor = world.add(Entity(id="Mentor", kind="character", type=mentor_type, label="the manager"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=mentor.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves(world, hero, activity)
    world.say(f"{hero.id} wore {prize.phrase} to work because it made the day feel special.")
    world.para()
    workday(world, hero, mentor, activity, prize)
    regret(world, hero, activity)
    gear_def = compromise(world, mentor, hero, activity, prize)
    world.para()
    if gear_def:
        accept(world, mentor, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, mentor=mentor, prize=prize, activity=activity, setting=setting, gear=gear_def)
    return world


SETTINGS = {
    "multirise": Setting(place="the MultiRise lobby", indoor=True, affords={"snuff", "tidy"}),
}

ACTIVITIES = {
    "snuff": Activity(
        id="snuff",
        verb="snuff the candles",
        gerund="snuffing candles",
        rush="hurry to snuff the candles",
        mess="soot",
        soil="smudged with soot",
        zone={"torso"},
        keyword="snuff",
        tags={"snuff", "candle", "soot"},
    ),
    "tidy": Activity(
        id="tidy",
        verb="tidy the lobby",
        gerund="tidying the lobby",
        rush="hurry to tidy the lobby",
        mess="dust",
        soil="dusty",
        zone={"torso"},
        keyword="tidy",
        tags={"tidy", "clean"},
    ),
}

PRIZES = {
    "apron": Prize(
        label="apron",
        phrase="a clean white apron",
        type="apron",
        region="torso",
    ),
    "badge": Prize(
        label="badge",
        phrase="a shiny welcome badge",
        type="badge",
        region="torso",
    ),
    "scarf": Prize(
        label="scarf",
        phrase="a soft blue scarf",
        type="scarf",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="smock",
        label="an old smock",
        covers={"torso"},
        guards={"soot", "dust"},
        prep="put on an old smock",
        tail="put on the old smock",
    ),
    Gear(
        id="cover",
        label="a cloth cover",
        covers={"torso"},
        guards={"soot"},
        prep="lay a cloth cover over the table",
        tail="lay the cloth cover over the table",
    ),
]

NAMES = ["Ari", "Mina", "Noah", "Lina", "Tess", "Jules", "Pia", "Ben"]
TRAITS = ["thoughtful", "gentle", "careful", "cheerful", "patient", "quiet"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if activity_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    mentor: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "snuff": [("What does it mean to snuff a candle?", "To snuff a candle means to put out the flame safely, often with a snuffer or by covering it the right way.")],
    "candle": [("What is a candle?", "A candle is a stick of wax with a wick that can burn and give off light.")],
    "soot": [("What is soot?", "Soot is a black powder made when something burns. It can leave a smudgy mark.")],
    "smock": [("What is a smock for?", "A smock helps keep clothes clean when you are doing something messy.")],
    "clean": [("Why do people like clean clothes?", "Clean clothes feel fresh, look nice, and are easier to wear again.")],
    "kind": [("What does it mean to be kind?", "Being kind means thinking about how other people feel and choosing actions that help them.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mentor, act, prize = f["hero"], f["mentor"], f["activity"], f["prize"]
    return [
        f"Write a heartwarming story about an employee at MultiRise who wants to {act.verb} while wearing {prize.phrase}.",
        f"Tell a small lesson-learned story where {hero.id} and {mentor.label_word} choose a safer way to {act.verb}.",
        f"Write a gentle workplace story that includes the word \"{act.keyword}\" and ends with everyone feeling proud.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mentor, prize, act = f["hero"], f["mentor"], f["prize"], f["activity"]
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {trait} {hero.type} who works at MultiRise with {mentor.label_word}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the lobby?",
            answer=f"{hero.id} wanted to {act.verb}, but first had to think about the safety of {hero.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question=f"Why did the manager speak up?",
            answer=f"The manager spoke up because {hero.id}'s {prize.label} could get {act.soil} if {hero.id} rushed ahead without care.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, {hero.id} used {f['gear'].label if f.get('gear') else 'a better plan'} and learned that asking first can save work and feelings.",
        ),
    ]
    if f.get("gear"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did {gear.label} help?",
                answer=f"{gear.label.capitalize()} helped by covering the {', '.join(sorted(gear.covers))} so {act.mess} could not reach the {prize.label}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
    out: list[QAItem] = []
    for tag in ["snuff", "candle", "soot", "smock", "clean", "kind"]:
        if tag in tags or tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(tag, []))
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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
    ap = argparse.ArgumentParser(description="Heartwarming lesson-learned storyworld set at MultiRise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["manager"])
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
        if not (activity_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError("That activity and prize do not make a believable lesson-learned story here.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(NAMES)
    mentor = args.mentor or "manager"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, mentor=mentor, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait, "stubborn"],
        params.mentor,
    )
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
    StoryParams(place="multirise", activity="snuff", prize="apron", name="Ari", gender="boy", mentor="manager", trait="thoughtful"),
    StoryParams(place="multirise", activity="snuff", prize="scarf", name="Mina", gender="girl", mentor="manager", trait="gentle"),
    StoryParams(place="multirise", activity="tidy", prize="badge", name="Tess", gender="girl", mentor="manager", trait="patient"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not activity_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not put {prize.label} at risk here.)"
    return f"(No story: nothing in the gear list protects {prize.label} from {activity.gerund}.)"


def asp_valid_story_rows() -> list[tuple]:
    return asp_valid_stories()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_story_rows()
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
