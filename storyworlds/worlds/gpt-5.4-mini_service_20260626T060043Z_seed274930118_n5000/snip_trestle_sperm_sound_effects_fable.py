#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/snip_trestle_sperm_sound_effects_fable.py
===============================================================================================================

A tiny fable-style story world about snipping on a trestle, sound effects, and
a whale below the boards.

Premise:
- A small animal works on an old trestle by the water.
- It wants to snip something useful, but the snip sound travels far.
- A sleeping sperm whale below the trestle hears every sharp sound.

Turn:
- A loud snip wakes the whale and causes trouble.

Resolution:
- The animal learns to wrap the tool, making a soft snip instead.
- The whale stays calm, and the work finishes well.

The story is built from world state, not a frozen paragraph.  The same core
simulation also powers QA, trace, and the inline ASP twin.
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

SOUND_KINDS = {"snip", "clang", "tap", "rustle"}
MOOD_KINDS = {"calm", "proud", "grumpy", "sleepy"}

GENTLE_NAMES = ["Mina", "Pip", "Tala", "Bram", "Nori", "Lumi", "Otto", "Suri"]
ANIMAL_TYPES = ["mouse", "fox", "otter", "bird", "beaver", "cat"]
ACTOR_ROLES = ["worker", "helper", "watcher"]


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    below: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


# ---------------------------------------------------------------------------
# Settings / items
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    outdoors: bool = True
    water_below: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    result_sound: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    type: str = "thing"
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    quiets: set[str]
    plural: bool = False


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.echo = 0.0

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.echo = self.echo
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def _r_sound_echo(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("sound", 0.0) < THRESHOLD:
            continue
        sig = ("echo", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.echo += 1
        out.append("The sound bounced under the trestle and rang over the water.")
    return out


def _r_wake_whale(world: World) -> list[str]:
    out: list[str] = []
    whale = world.entities.get("whale")
    if not whale:
        return out
    if world.echo < THRESHOLD:
        return out
    if whale.memes.get("sleepy", 0.0) < THRESHOLD:
        return out
    sig = ("wake", "whale")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    whale.memes["sleepy"] = 0.0
    whale.memes["grumpy"] = whale.memes.get("grumpy", 0.0) + 1.0
    out.append("Below the boards, the sperm whale stirred and frowned at the noise.")
    return out


CAUSAL_RULES = [
    _r_sound_echo,
    _r_wake_whale,
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


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def should_risk_whale(activity: Activity, prize: Prize) -> bool:
    return prize.region == "below_water"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if activity.id in g.quiets and prize.region == "below_water":
            return g
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.verb} only matters here if the sound can reach the whale "
        f"below the trestle, and nothing in the gear list changes that.)"
    )


# ---------------------------------------------------------------------------
# Scripted actions
# ---------------------------------------------------------------------------
def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.facts["activity_id"] = activity.id
    actor.meters["sound"] = actor.meters.get("sound", 0.0) + 1.0
    actor.memes["determined"] = actor.memes.get("determined", 0.0) + 1.0
    world.say(f"{actor.id} went on the trestle and tried to {activity.verb}.")
    world.say(f"{activity.sound}! {activity.sound}! The boards answered with a sharp little echo.")
    propagate(world, narrate=narrate)


def warn(world: World, guide: Entity, actor: Entity, activity: Activity, prize: Entity) -> None:
    whale = world.get("whale")
    if whale.memes.get("sleepy", 0.0) < THRESHOLD:
        return
    world.say(
        f'"Careful," said {guide.id}. "If you keep making that {activity.result_sound}, '
        f"the sperm whale will wake.""
    )


def compromise(world: World, guide: Entity, actor: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(
        Entity(
            id=gear_def.id,
            type="gear",
            label=gear_def.label,
            protective=True,
            owner=actor.id,
        )
    )
    gear.worn_by = actor.id
    actor.memes["calm"] = actor.memes.get("calm", 0.0) + 1.0
    world.say(
        f'{guide.id} smiled. "{gear_def.prep} and then try again. That way the work can stay kind."'
    )
    return gear_def


def accept(world: World, guide: Entity, actor: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    whale = world.get("whale")
    whale.memes["grumpy"] = 0.0
    whale.memes["calm"] = whale.memes.get("calm", 0.0) + 1.0
    actor.memes["proud"] = actor.memes.get("proud", 0.0) + 1.0
    world.say(
        f'{actor.id} listened, took the {gear_def.label}, and made a softer try: {gear_def.tail}.'
    )
    world.say(
        f'At last came a quiet {activity.sound.lower()} instead of a sharp one, and the whale stayed asleep.'
    )
    world.say(
        f"So the trestle held the work, the water held the silence, and {actor.id} learned that a soft way can be the strongest way."
    )


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "trestle": Setting(place="the trestle", outdoors=True, water_below=True, affords={"snip"}),
    "harbor": Setting(place="the harbor trestle", outdoors=True, water_below=True, affords={"snip"}),
}

ACTIVITIES = {
    "snip": Activity(
        id="snip",
        verb="snip the rope",
        gerund="snipping the rope",
        rush="snip faster",
        sound="Snip",
        result_sound="snip",
        keyword="snip",
        tags={"sound", "rope", "trestle"},
    )
}

PRIZES = {
    "rope": Prize(
        label="rope",
        phrase="a long rope tied to the rail",
        region="below_water",
    )
}

GEAR = [
    Gear(
        id="wrap",
        label="a soft cloth wrap",
        prep="wrap the scissors in a soft cloth",
        tail="the cloth kept the blades from singing out",
        quiets={"snip"},
    ),
    Gear(
        id="muffler",
        label="a felt blade muffler",
        prep="fit a felt muffler over the blade",
        tail="the felt turned the sharp snip into a hush",
        quiets={"snip"},
    ),
]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    role: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story build
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, role: str) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type="mouse" if role == "worker" else "fox",
            label=role,
            memes={"calm": 0.0, "proud": 0.0, "determined": 0.0},
            meters={"sound": 0.0},
        )
    )
    guide = world.add(
        Entity(
            id="Guide",
            kind="character",
            type="bird",
            label="the old bird",
            memes={"calm": 1.0},
        )
    )
    whale = world.add(
        Entity(
            id="whale",
            kind="character",
            type="sperm whale",
            label="the sperm whale",
            below=setting.place,
            memes={"sleepy": 1.0, "grumpy": 0.0, "calm": 0.0},
        )
    )
    prize = world.add(
        Entity(
            id="rope",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            caretaker=guide.id,
        )
    )

    # Act 1
    world.say(f"On an old trestle above the water, {hero.id} was a {role} who loved useful work.")
    world.say(f"{hero.id} liked the clean little task of {activity.gerund}.")
    world.say(f"Down below, the sperm whale slept under the boards and let the tide rock its dreams.")

    # Act 2
    world.para()
    world.say(f"But every {activity.keyword} made a sound: {activity.sound.lower()}!")
    warn(world, guide, hero, activity, prize)
    _do_activity(world, hero, activity, narrate=True)

    # Act 3
    world.para()
    gear_def = compromise(world, guide, hero, activity, prize)
    if gear_def is not None:
        accept(world, guide, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        guide=guide,
        whale=whale,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
        resolved=gear_def is not None,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        'Write a short fable for a child about a trestle, a snip, and a sleeping whale.',
        f'Write a gentle story where {hero.id} wants to {act.verb} on a trestle but must learn to make the sound softer.',
        'Tell a simple story with sound effects that ends with a quiet, kind solution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    whale = f["whale"]
    act = f["activity"]
    gear = f["gear"]

    qa = [
        QAItem(
            question=f"What did {hero.id} want to do on the trestle?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did the old bird warn {hero.id}?",
            answer=(
                f"The old bird warned {hero.id} because the {act.sound.lower()} was too loud, "
                f"and the sperm whale below the trestle could wake up and get grumpy."
            ),
        ),
        QAItem(
            question="What sound was heard when the work got noisy?",
            answer=f"The story kept saying {act.sound.lower()} and letting the sound echo under the trestle.",
        ),
    ]
    if gear is not None:
        qa.append(
            QAItem(
                question=f"How did the soft cloth help {hero.id}?",
                answer=(
                    f"The soft cloth made the {act.result_sound} quieter, so {hero.id} could keep working "
                    f"without waking the sperm whale."
                ),
            )
        )
        qa.append(
            QAItem(
                question=f"How did the whale feel at the end?",
                answer=(
                    f"The whale stopped being grumpy and stayed calm and sleepy because the noise turned soft."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a trestle?",
            answer="A trestle is a bridge or framework made of many supports, often with open spaces underneath.",
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a word like snip or bang that lets you hear the action in your mind.",
        ),
        QAItem(
            question="What does a soft cloth wrap do?",
            answer="A soft cloth wrap helps cover something hard so it makes less noise and feels gentler.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        if e.below:
            bits.append(f"below={e.below}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  echo={world.echo}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), below_water(P), makes_noise(A).
quiet_fix(A,P) :- gear(G), prize_at_risk(A,P), quiets(G,A).
valid_story(Place,A,P) :- setting(Place), affords(Place,A), prize_at_risk(A,P), quiet_fix(A,P).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("makes_noise", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.region == "below_water":
            lines.append(asp.fact("below_water", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for a in sorted(g.quiets):
            lines.append(asp.fact("quiets", g.id, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id, prize in PRIZES.items():
                if should_risk_whale(ACTIVITIES[act_id], prize) and select_gear(ACTIVITIES[act_id], prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a trestle, a snip, and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ACTOR_ROLES)
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
        act = ACTIVITIES[args.activity]
        pr = PRIZES[args.prize]
        if not (should_risk_whale(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(GENTLE_NAMES)
    role = args.role or rng.choice(ACTOR_ROLES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.role)
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
    StoryParams(place="trestle", activity="snip", prize="rope", name="Pip", role="worker"),
    StoryParams(place="harbor", activity="snip", prize="rope", name="Mina", role="helper"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
