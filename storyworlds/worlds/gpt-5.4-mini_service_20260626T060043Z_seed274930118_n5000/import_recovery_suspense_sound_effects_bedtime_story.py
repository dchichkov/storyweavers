#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/import_recovery_suspense_sound_effects_bedtime_story.py
===============================================================================================================

A small bedtime-story world about a child, a missing beloved thing, suspenseful
searching, and a gentle recovery.

Seed words:
- import
- recovery

Narrative instruments:
- Suspense
- Sound Effects

Style:
- Bedtime Story
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["lost", "found", "cozy", "sleepy", "searched"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "courage", "relief", "love", "tenderness"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _trace_sound(world: World, text: str) -> None:
    world.say(text)


def _search(world: World, hero: Entity, prize: Entity, narrate: bool = True) -> None:
    hero.meters["searched"] += 1
    hero.memes["worry"] += 1
    prize.meters["lost"] += 1
    if narrate:
        _trace_sound(world, "The room answered with a tiny creak, and the dark stayed still.")


def _recover(world: World, hero: Entity, prize: Entity, gear: Gear, narrate: bool = True) -> None:
    sig = ("recovery", prize.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    prize.meters["lost"] = 0
    prize.meters["found"] += 1
    hero.memes["relief"] += 1
    hero.memes["courage"] += 1
    if narrate:
        _trace_sound(world, 'There came a soft "tap-tap" from under the bed, then a happy little "oh!"')


def predict_recovery(world: World, hero: Entity, prize: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["searched"] += 1
    sim.get(prize.id).meters["lost"] += 1
    return True


SETTINGS = {
    "bedroom": Setting(place="the bedroom", affords={"search"}),
    "nursery": Setting(place="the nursery", affords={"search"}),
}

ACTIVITIES = {
    "search": Activity(
        id="search",
        verb="look under the bed",
        gerund="looking under the bed",
        rush="peek under the bed",
        keyword="recovery",
        tags={"search", "dark", "sound"},
    ),
}

PRIZES = {
    "bunny": Prize(label="bunny", phrase="a soft striped bunny", type="bunny"),
    "blanket": Prize(label="blanket", phrase="a tiny blue blanket", type="blanket"),
    "bear": Prize(label="bear", phrase="a round sleepy bear", type="bear"),
}

GEAR = [
    Gear(
        id="flashlight",
        label="a small flashlight",
        prep="turn on a small flashlight",
        tail='the flashlight made a bright path, and the search was not scary anymore',
        guards={"dark"},
    ),
    Gear(
        id="nightlight",
        label="a nightlight",
        prep="switch on the nightlight",
        tail='the nightlight glowed like a tiny moon, so the shadows felt friendly',
        guards={"dark"},
    ),
]

NAMES_GIRL = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
NAMES_BOY = ["Leo", "Finn", "Theo", "Max", "Ben"]
TRAITS = ["sleepy", "gentle", "curious", "brave", "tiny"]


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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, "search") for place in SETTINGS for _ in PRIZES]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return activity.id == "search"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    return GEAR[0] if prize_at_risk(activity, prize) else None


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id))

    hero.memes["love"] += 1
    hero.memes["tenderness"] += 1
    prize.meters["lost"] = 1
    world.say(f"{hero.id} was a {trait} little {hero.type} who loved {prize.phrase}.")
    world.say(f"At bedtime, {hero.id}'s {parent_type} tucked {hero.id} in and whispered, 'Good night.'")
    world.say(f"But then {hero.id} noticed {hero.pronoun('possessive')} {prize.label} was missing.")
    world.para()
    world.say(f"In the dim {setting.place}, {hero.id} wanted to {activity.verb}.")
    world.say(f'{hero.id} took a breath and started {activity.gerund}.')
    _search(world, hero, prize)
    world.say(f"The floor said {f'\"{activity.rush}\"'} as {hero.id} slid a hand farther under the bed.")
    gear = select_gear(activity, prize)
    if gear:
        world.para()
        world.say(f"Then {hero.id}'s {parent_type} smiled, reached for {gear.label}, and said, '{gear.prep}.'")
        _recover(world, hero, prize, gear, narrate=True)
        world.say(f"They kept going until a little {prize.label} nose peeked out from the dark.")
        world.say(f"{gear.tail.capitalize()}.")
        hero.memes["relief"] += 1
        hero.meters["cozy"] += 1
        prize.meters["found"] += 1
        world.para()
        world.say(f"{hero.id} hugged {hero.pronoun('possessive')} {prize.label} tight.")
        world.say(f"The room felt warm again, and the blanket of night felt safe.")
        world.say(f'Soon {hero.id} was yawning, and the only sound left was a soft "shhh" from the dark.')
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a bedtime story for a small child about "recovery" and a missing {prize.label}.',
        f"Tell a gentle suspense story where {hero.id} hears tiny sound effects in {f['setting'].place} and {parent.label} helps recover the {prize.label}.",
        f'Write a child-friendly story that includes the word "import" once and ends with a cozy recovery after a dark bedtime search.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What was missing at bedtime for {hero.id}?",
            answer=f"{hero.id} noticed that {hero.pronoun('possessive')} {prize.label} was missing, so the room suddenly felt a little suspenseful.",
        ),
        QAItem(
            question=f"What did {hero.id} and {parent.label} do to recover it?",
            answer=f"They looked under the bed together, used a small light, and followed the little sound until the {prize.label} was found again.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when the {prize.label} came back?",
            answer=f"{hero.id} felt relief and courage, then hugged {hero.pronoun('possessive')} {prize.label} close and got ready for sleep.",
        ),
        QAItem(
            question=f"What sound effects helped the search feel suspenseful?",
            answer='The story used little sounds like a creak, a tap-tap, and a soft shhh to make the dark bedroom feel exciting but gentle.',
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashlight for?",
            answer="A flashlight makes a beam of light so people can see in the dark.",
        ),
        QAItem(
            question="What does recovery mean in a story like this?",
            answer="Recovery means finding something again after it was lost or missing.",
        ),
        QAItem(
            question="Why can dark rooms feel a little scary at bedtime?",
            answer="Dark rooms hide corners and shapes, so a child may feel unsure until a parent helps make them feel safe.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), A = search.
has_fix(A,P) :- prize_at_risk(A,P), gear(G), guards(G,dark).
valid(Place,A,P) :- setting(Place), affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for g in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, g))
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
    ap = argparse.ArgumentParser(description="A bedtime story world about suspense, sound effects, and recovery.")
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
              and (args.activity is None or c[1] == args.activity)]
    if not combos:
        raise StoryError("(No valid bedtime story matches the given options.)")
    place, activity = rng.choice(sorted(combos))
    prize = args.prize or rng.choice(sorted(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


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


CURATED = [
    StoryParams(place="bedroom", activity="search", prize="bunny", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="nursery", activity="search", prize="blanket", name="Leo", gender="boy", parent="father", trait="sleepy"),
    StoryParams(place="bedroom", activity="search", prize="bear", name="Nora", gender="girl", parent="mother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
