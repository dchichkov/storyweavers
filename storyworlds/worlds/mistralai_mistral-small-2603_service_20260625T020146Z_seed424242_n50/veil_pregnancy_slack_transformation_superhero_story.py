#!/usr/bin/env python3
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
        female = {"hero", "mentor", "mom", "woman"}
        male = {"mentor", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

@dataclass
class Setting:
    place: str = "maternal center"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)

@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    twist: str = ""
    tags: set[str] = field(default_factory=set)

@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards_mess: Optional[str] = None
    plural: bool = False

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.pregnancy_stage: float = 0.0
        self.crisis: bool = False
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.pregnancy_stage = self.pregnancy_stage
        clone.crisis = self.crisis
        clone.paragraphs = [[]]
        return clone

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_power_strain(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.entities.values() if e.type == "hero"), None)
    if not hero or hero.meters.get("power", 0) < THRESHOLD:
        return out
    for item in world.entities.values():
        if item.worn_by == hero.id and not item.protective:
            sig = ("strain", item.id)
            if sig not in world.fired:
                world.fired.add(sig)
                item.meters["stress"] += 1
                out.append(
                    f"{hero.pronoun().capitalize()} felt a sharp pain in {hero.pronoun('possessive')} "
                    f"midsection as {hero.pronoun()} pushed {hero.it()} too hard."
                )
    if out and hero.memes.get("confidence", 0) > 0:
        hero.memes["confidence"] -= 1
    return out

def _r_balance_lesson(world: World) -> list[str]:
    hero = next((e for e in world.entities.values() if e.type == "hero"), None)
    mentor = next((e for e in world.entities.values() if e.type == "mentor"), None)
    if not hero or not mentor or hero.memes.get("anticipation", 0) < THRESHOLD:
        return []
    sig = ("balance", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["responsibility"] += 1
    return [
        f"{mentor.id} placed a gentle hand on {hero.pronoun('possessive')} shoulder. "
        f'"Every great power needs great rest," {mentor.pronoun()} whispered. '
        f"Rest is not slackness—it’s the true sacred veil of motherhood."'
    ]

CAUSAL_RULES: list[Rule] = [
    Rule(name="power_strain", tag="physical", apply=_r_power_strain),
    Rule(name="balance_lesson", tag="social", apply=_r_balance_lesson),
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

def predict_risk(world: World, actor: Entity, activity: Activity) -> float:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return sim.get(actor.id).meters.get("stress", 0) > THRESHOLD

def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.memes["anticipation"] += 0.3
    if "power" in world.facts:
        actor.memes["powerful"] += 0.7
    actor.meters["energy"] -= 0.4
    actor.memes["confidence"] += 0.2
    actor.meters["power_awakening"] += 0.15
    if world.pregnancy_stage > 0.7:
        actor.meters["power"] += 1
    propagate(world, narrate=narrate)

def discover_powers(world: World, hero: Entity) -> None:
    hero.memes["anticipation"] += 1
    world.facts["awakening_stage"] = world.pregnancy_stage
    world.say(
        f'One evening, as {hero.pronoun()} combed {hero.it()} long hair, '
        f'{hero.pronoun()} felt a strange warmth ripple under {hero.pronoun("possessive")} skin. '
        f"A shimmering veil of energy wavered before {hero.pronoun("object")}, "
        f"as if the child within had whispered: 'Awaken.'"
    )

def warn_off_balance(world: World, hero: Entity, mentor: Entity) -> None:
    world.say(
        f'"You’re flying between duties like a hummingbird with a broken wing," '
        f'{mentor.pronoun()} observed, eyes soft. "A hero does not neglect the '
        f'calm slack of pregnancy. There is power in rest, and rest is '
        f'this child’s first sanctuary."'
    )
    hero.memes["fear"] += 0.8

def train_control(world: World, hero: Entity, mentor: Entity, activity: Activity) -> None:
    hero.memes["responsibility"] += 1
    hero.memes["love"] += 0.6
    ment = f"{mentor.pronoun('possessive')} {mentor.label}"
    world.say(
        f'On {hero.pronoun("possessive")} next visit, {ment} guided '
        f"{hero.id} through gentle breathwork: inhale light, exhale "
        f"fear. The veil of power rippled—controlled, luminous, "
        f"no longer a reckless storm."
    )
    hero.meters["control"] = world.pregnancy_stage

def resolve_transformation(world: World, hero: Entity, child: Entity) -> None:
    world.crisis = False
    hero.memes["triumph"] += 1.2
    world.facts["transformation_depth"] = world.pregnancy_stage
    world.say(
        f'Sunlight caught {hero.id} as {hero.pronoun()} stood wrapped in '
        f'a light-veil of energy, {child.label} glowing within. '
        f"The transformation was complete: not a surrender to pain, "
        f"but a birth of purpose."
    )

SETTINGS = {
    "center": Setting(place="maternal center", indoor=True, affords={"rest", "train"}),
}

ACTIVITIES = {
    "power_dash": Activity(
        id="power_dash",
        verb="hurled {hero} forward at reckless speeds",
        gerund="hurling {hero} forward at reckless speeds",
        rush="bolt straight into action",
        twist="This {hero} forgot rest is the true veil of heroism",
        tags={"power", "transformation"},
    ),
    "luminous_rest": Activity(
        id="luminous_rest",
        verb="bathed {hero} in luminous calm",
        gerund="bathing {hero} in luminous calm",
        rush="embraced deep stillness",
        tags={"rest", "transformation"},
    ),
}

GEAR = [
    Gear(
        id="veil",
        label="sacred pregnancy veil",
        prep="adjust the sacred pregnancy veil",
        tail="donned the sacred pregnancy veil",
    ),
    Gear(
        id="shawl",
        label="calm shawl",
        prep="wrap the calm shawl around {hero}",
        tail="wrapped the calm shawl around {hero}",
    ),
]

def build_hero(is_girl: bool = True) -> Entity:
    name = random.choice(["Aria", "Nova"]) if is_girl else random.choice(
        ["Rook", "Kael"]
    )
    trait = random.choice(["fiery", "gentle"])
    return Entity(
        id=name,
        kind="character",
        type="hero",
        label=f"{trait} {is_girl and 'heroine' or 'hero'}",
        phrase=f"the {trait} {is_girl and 'heroine' or 'hero'} " "with the awakening power",
        traits=[trait, "pregnant"],
    )

def build_mentor(is_female: bool = True) -> Entity:
    name = random.choice(["Sister Lumen", "Mother Clara"]) if is_female else random.choice(
        ["Brother Sol", "Mentor Veyl"]
    )
    label = "the midwife-mentor"
    return Entity(
        id=name, kind="character", type="mentor", label=label, traits=["wise", "guiding"],
    )

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.pregnancy_stage: float = 0.0
        self.facts: dict = {}
        self.child_expected: bool = False

    def advance_week(self, weeks: float = 1.0) -> None:
        self.pregnancy_stage += weeks * 0.1
        if self.pregnancy_stage >= 0.99:
            self.pregnancy_stage = 1.0
            world.child_expected = True

@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    gender: str
    weeks: int
    seed: Optional[int] = None

def valid_combos(place: str, activity: str, gender: str) -> bool:
    return (
        place == "center"
        and activity in {"power_dash", "luminous_rest"}
        and gender in {"girl", "boy"}
    )

KNOWLEDGE = {
    "power": [
        ("What is a superhero pregnancy?",
         "A time when expectant heroes harness their latent abilities to protect the unborn, "
         "using embryonic light as armor and calm as weapon."),
        ("Why do pregnant heroes need a veil?",
         "The veil—often woven from energy or fabric—shields the child and channels "
         "power without strain. Too much force risks both mother and babe."),
    ],
    "rest": [
        ("Why is rest sacred in hero pregnancy?",
         "Rest is not slack. Every hero knows: the child’s sanctuary is a power "
         "source itself—luminous, untamed, and best honored through stillness."),
        ("What is ‘slack’ in superhero terms?",
         "Slack is the space where spontaneity meets deliberation: pause to steady "
         "powers before they surge beyond measure."),
    ],
}

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    prompts = [
        'Create a gentle heroic tale exploring a pregnant "super" who discovers '
        'energetic power, clashes with immaturity, then learns control via '
        'rest-"the sacred slack"-and glows with wisdom at term.',
        f'Write a 3-to-5-year-old version of a story about {f.get("name")}, '
        f'a pregnant {f.get("gender")} hero who overuses newfound energy, '
        "then rediscovers the calm within the sacred veil of motherhood.",
    ]
    a = ACTIVITIES.get(world.facts.get("activity"))
    if a:
        prompts[-1] += f" The climax involves {a.twist.replace('{hero}', f'{f.get(\"name\")}')}"
    return prompts

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    name = f.get("name")
    gender = f.get("gender")
    activity = f.get("activity")
    stage = f.get("awakening_stage", 0)
    hero = next((e for e in world.entities.values() if e.type == "hero"), None)
    if not hero:
        return []
    qa = [
        QAItem(
            question=f"Who is {name}?",
            answer=f"{name} is a {gender} pregnant hero "
                   f"with latent energy awakening at {stage:.1f} term.",
        ),
        QAItem(
            question=f"What nervous habit makes {name} push too hard despite pregnancy?",
            answer=f"{name} keeps trying to {ACTIVITIES[activity].gerund} "
                   "wanting to protect the baby by force.",
        ),
    ]
    if world.pregnancy_stage > 0.7:
        qa.append(QAItem(
            question=f"How did {name} learn to balance power and rest?",
            answer=f"A mentor taught {name} to use the veil of calm "
                   "as a shield and the slack of rest as the true sacred timing.",
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = world.facts.get("activity_tags", set())
    out = []
    for tag in ["power", "rest"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(tag, []))
    return out

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "center"))
    lines.append(asp.fact("indoor", "center"))
    lines.append(asp.fact("affords", "center", "power_dash"))
    lines.append(asp.fact("affords", "center", "luminous_rest"))
    lines.append(asp.fact("activity", "power_dash"))
    lines.append(asp.fact("activity", "luminous_rest"))
    lines.append(asp.fact("valid", "center", "power_dash", "hero"))
    lines.append(asp.fact("valid", "center", "luminous_rest", "hero"))
    return "\n".join(lines)

ASP_RULES = r"""
activity_valid(A) :- activity(A), affords(center, A).
hero_type(T) :- wears(G,T), gender(G,_).
story_ok :- activity_valid(A), gender(G,_), hero_type(hero).
:- not story_ok.
valid_center(A) :- activity_valid(A).
"""

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero pregnancy story world: Transformation via energy, "
                    "veil of care, and sacred slack."
    )
    ap.add_argument("--place", choices=["center"], default="center")
    ap.add_argument("--activity", choices=ACTIVITIES, default=random.choice(list(ACTIVITIES)))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"], default=random.choice(["girl", "boy"]))
    ap.add_argument("--weeks", type=float, default=30.0)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if not valid_combos(args.place, args.activity, args.gender):
        raise StoryError("Invalid hero pregnancy story setup detected.")
    name = args.name or random.choice(["Aria", "Nova", "Rook", "Kael"])
    weeks = max(12.0, min(42.0, args.weeks))
    return StoryParams(
        place=args.place,
        activity=args.activity,
        name=name,
        gender=args.gender,
        weeks=weeks,
        seed=args.seed,
    )

def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    world.advance_week(params.weeks * 0.1)
    is_girl = params.gender == "girl"
    hero = world.add(build_hero(is_girl))
    mentor = world.add(build_mentor(is_girl))
    child = world.add(Entity(
        id="child",
        kind="thing",
        type="babe",
        phrase="the glowing child within",
        traits=["precious", "sanctum"],
    ))
    hero.meters["power"] = 0.0
    hero.meter["stress"] = 0.0
    hero.memes["powerful"] = 0.0
    world.facts.update(
        name=params.name,
        gender=params.gender,
        weeks=params.weeks,
        activity=params.activity,
        activity_tags=ACTIVITIES[params.activity].tags,
    )
    world.para()
    discover_powers(world, hero)
    world.para()
    hero.advance_week(params.weeks)
    _do_activity(
        world, hero,
        ACTIVITIES[params.activity],
        narrate=True,
    )
    if world.get(hero.id).meters.get("stress", 0) > THRESHOLD:
        world.crisis = True
        world.say(
            f'Pain flared as {hero.pronoun()} realized too much action '
            f"endangers the child’s sacred veil."
        )
        world.para()
        warn_off_balance(world, hero, mentor)
        world.para()
        selected_gear = next((g for g in GEAR if g.guards_mess == "power"), None)
        if selected_gear:
            world.say(
                f'{hero.pronoun("possessive").capitalize()} {selected_gear.label} '
                f"shimmered into place as {hero.pronoun()} adjusted it. "
                "The child’s glow steadied—calm had returned."
            )
    world.para()
    train_control(world, hero, mentor, ACTIVITIES[params.activity])
    if world.pregnancy_stage > 0.9:
        world.para()
        resolve_transformation(world, hero, child)
    world.facts.update(
        crisis=world.crisis,
        final_stage=world.pregnancy_stage,
        power_level=world.get(hero.id).meters.get("power", 0),
    )
    return StorySample(
        params=params,
        prompts=generation_prompts(world),
        story=world.render(),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        import asp
        model = asp.one_model(asp_program(show="#show valid_center/1."))
        print("OK" if model else "FAIL")
        return
    if args.asp:
        print(asp_program(show="#show valid_center/1."))
        return
    if args.show_asp:
        print(asp_program(show="#show."))
        return
    samples = []
    rng = random.Random(args.seed)
    if args.all:
        for n in [20, 25, 30]:
            params = StoryParams(
                place="center",
                activity="power_dash",
                name=["Nova", "Kael"][n % 2],
                gender=["girl", "boy"][n % 2],
                weeks=n,
            )
            samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, rng)
            params.seed = args.seed + i if args.seed is not None else None
            samples.append(generate(params))
    if args.json:
        print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for s in samples:
        emit(s, trace=args.trace, qa=args.qa)

if __name__ == "__main__":
    main()
