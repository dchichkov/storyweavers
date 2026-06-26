#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/aggression_rehearsal_twist_foreshadowing_inner_monologue_mystery.py
================================================================================

A standalone story world for a small mystery domain: a rehearsal that seems
aggressive at first, then turns out to be part of a staged clue.

Premise:
- A child is in a school auditorium after hours.
- A rehearsal scene sounds harsh and suspicious.
- The child follows foreshadowing clues and inner monologue.
- Twist: the "aggression" was acting, and the real mystery is about a missing prop clue.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- standalone stdlib script
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- lazy ASP import inside helpers
- Python reasonableness gate plus inline ASP twin
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "risk": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "fear": 0.0, "certainty": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


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
    sound: str
    clue: str
    twist: str
    zone: set[str]
    keyword: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    fragile: bool = True


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()
        self.suspicion: float = 0.0

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.suspicion = self.suspicion
        c.paragraphs = [[]]
        return c


def covered(actor: Entity, item: Entity) -> bool:
    return False


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("aggression", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.kind == "thing" and item.worn_by == actor.id:
                continue
        for item in world.entities.values():
            if item.kind != "thing" or item.owner != actor.id:
                continue
            if item.protective:
                continue
            sig = ("damage", actor.id, item.id)
            if sig in world.fired:
                continue
            if item.region not in world.zone:
                continue
            world.fired.add(sig)
            item.meters["damage"] += 1
            out.append(f"Something delicate onstage got bumped.")
    return out


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    if world.suspicion >= THRESHOLD:
        sig = ("suspicion")
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__suspicious__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_damage, _r_suspicion):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend([s for s in sents if s != "__suspicious__"])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_damage(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    sim.zone = set(activity.zone)
    sim.get(actor.id).meters["aggression"] += 1
    prize = sim.get(prize_id)
    return {"damaged": prize.meters["damage"] >= THRESHOLD}


def reasonableness_gate(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone and activity.id == "rehearsal"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.keyword in gear.guards and prize.region in gear.covers:
            return gear
    return None


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        region=prize_cfg.region,
    ))

    world.say(f"{hero.id} was a {trait} little {hero.type} who loved noticing quiet details.")
    world.say(f"{hero.pronoun('subject').capitalize()} had a habit of listening twice before speaking.")
    world.say(f"At the school auditorium, the air smelled like dust, chalk, and old curtains.")
    world.say(f"{hero.id} was helping with a {activity.gerund} for the evening show.")

    world.para()
    world.say(f"{hero.id} noticed a sharp {activity.sound} from backstage.")
    world.say(f"In {hero.pronoun('possessive')} head, {hero.id} thought, 'That sounds mean. Maybe someone is angry.'")
    world.say(f"Then {hero.id} saw {activity.clue}, and the worry grew bigger.")
    world.say(f"{hero.id} stared at the {prize.label} and wondered why it had been left so close to the stage edge.")

    world.para()
    world.zone = set(activity.zone)
    hero.meters["aggression"] += 1
    hero.memes["curiosity"] += 1
    world.suspicion += 1
    if predict_damage(world, hero, activity, prize.id)["damaged"]:
        world.say(f'{hero.id} whispered, "If the scene gets rough, the {prize.label} could get hurt."')
    world.say(f"{hero.id}'s {parent.label_word if hasattr(parent, 'label_word') else 'parent'} stepped closer and said the line again.")
    world.say(f'It still sounded fierce, which made {hero.id} think, "That cannot be the whole story."')
    propagate(world, narrate=False)
    world.say(f"Then the lights flickered once, like a tiny wink from the room.")

    world.para()
    gear_def = select_gear(activity, prize)
    if gear_def:
        gear = world.add(Entity(
            id=gear_def.id,
            type="gear",
            label=gear_def.label,
            protective=True,
            covers=set(gear_def.covers),
            owner=hero.id,
        ))
        gear.worn_by = hero.id
        world.say(f"{hero.id}'s {parent.type if parent_type else 'parent'} smiled and offered {gear_def.prep}.")
        world.say(f"{hero.id} put it on, and the sharp sounds suddenly made more sense.")
    world.say(f"The twist came when the backstage door opened and the missing page fluttered out of a prop box.")
    world.say(f"The 'angry' voice was only a rehearsal voice, made to practice a villain's line.")
    world.say(f"The real mystery was the page, and it had slipped inside the box when the cast rushed their cues.")
    world.say(f"{hero.id} found it, and {hero.id} felt the fear turn into relief.")
    world.say(f"By the end, the auditorium felt calm again, and the rehearsal sounded brave instead of scary.")

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        gear=gear_def,
        setting=setting,
        trait=trait,
    )
    return world


SETTINGS = {
    "auditorium": Setting(place="the school auditorium", indoor=True, affords={"rehearsal"}),
    "backstage": Setting(place="backstage", indoor=True, affords={"rehearsal"}),
    "library": Setting(place="the library stage corner", indoor=True, affords={"rehearsal"}),
}

ACTIVITIES = {
    "rehearsal": Activity(
        id="rehearsal",
        verb="rehearse the scene",
        gerund="rehearsing the scene",
        sound="bang",
        clue="a torn program page hidden under a chair",
        twist="the noisy scene was only practice",
        zone={"torso", "hands"},
        keyword="rehearsal",
    ),
}

PRIZES = {
    "script": Prize(label="script", phrase="a folded script page", type="paper", region="hands"),
    "prop": Prize(label="prop mask", phrase="a shiny prop mask", type="mask", region="face"),
    "lantern": Prize(label="lantern", phrase="a glass lantern prop", type="lantern", region="hands"),
}

GEAR = [
    Gear(id="pouch", label="a padded pouch", covers={"hands"}, guards={"rehearsal"}, prep="put the page in a padded pouch", tail="kept the page safe"),
    Gear(id="case", label="a soft prop case", covers={"hands", "torso"}, guards={"rehearsal"}, prep="carry the prop in a soft case", tail="moved the prop without a bump"),
]

TRAITS = ["careful", "curious", "quiet", "sharp-eyed", "nervous"]

GIRL_NAMES = ["Mina", "Ivy", "Lena", "Tess", "Nora", "June"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Ben", "Milo", "Owen"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for act_id in s.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if reasonableness_gate(act, prize) and select_gear(act, prize):
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-sized mystery story about {f["hero"].id} and a rehearsal in {f["setting"].place}.',
        f'Tell a story where a noisy {f["activity"].keyword} sounds aggressive, but the twist is innocent.',
        f'Write a mystery with foreshadowing, inner monologue, and a twist involving a missing {f["prize"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    act = f["activity"]
    return [
        QAItem(
            question=f"What was {hero.id} helping with at {world.setting.place}?",
            answer=f"{hero.id} was helping with {act.gerund}, which sounded mysterious at first.",
        ),
        QAItem(
            question=f"Why did {hero.id} think someone might be angry?",
            answer=f"{hero.id} heard the sharp {act.sound} and thought the scene sounded mean, so {hero.id} worried it might be real aggression.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the harsh-sounding moment was only a rehearsal, and the real mystery was a missing {prize.label} page that had slipped into a prop box.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} found the missing page, and the rehearsal turned calm and safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rehearsal?",
            answer="A rehearsal is a practice run for a play, concert, or show before the real performance.",
        ),
        QAItem(
            question="What is a foreshadowing clue?",
            answer="A foreshadowing clue is a small detail that hints at something important that will matter later in the story.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the voice of a character's thoughts inside their head.",
        ),
        QAItem(
            question="What is a twist in a mystery?",
            answer="A twist is a surprising change that makes the answer different from what the reader first expected.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="auditorium", activity="rehearsal", prize="script", name="Mina", gender="girl", parent="mother", trait="sharp-eyed"),
    StoryParams(place="backstage", activity="rehearsal", prize="lantern", name="Eli", gender="boy", parent="father", trait="curious"),
    StoryParams(place="library", activity="rehearsal", prize="prop", name="Tess", gender="girl", parent="mother", trait="quiet"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: the {activity.id} setup does not plausibly put a {prize.label} in danger.)"


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: {PRIZES[prize_id].label} story here is not restricted by gender, so this check should not trigger.)"


ASP_RULES = r"""
% A prize is at risk when the rehearsal reaches the prize's region.
at_risk(A, P) :- rehearsal(A), reaches(A, R), worn_on(P, R).

% Gear is a compatible fix when it covers the prize's region and is meant for rehearsal props.
fix(G, A, P) :- gear(G), at_risk(A, P), covers(G, R), worn_on(P, R), guards(G, rehearsal).

valid(Place, A, P) :- affords(Place, A), at_risk(A, P), fix(_, A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("rehearsal", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("reaches", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world: aggression, rehearsal, foreshadowing, and a twist.")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for t in triples:
            print("  ", t)
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
