#!/usr/bin/env python3
"""
storyworlds/worlds/bath_dim_misunderstanding_surprise_sound_effects_comedy.py
=============================================================================

A tiny comedy storyworld about a dim bath, a misunderstanding, a surprise,
and lots of sound effects.

Seed premise:
- A child is in a dim bathroom bath.
- The child uses silly sound effects while playing.
- A parent mishears the sounds and worries.
- A surprise reveal turns the worry into laughter.

The world is intentionally small and constraint-checked: the parent only warns
when the simulated state makes the misunderstanding plausible, and the ending
must resolve into a child-friendly joke.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    dim: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    sound: str
    misunderstanding: str
    surprise: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    kind: str
    makes_sound: bool = False
    surprise_reveal: bool = False
    caretaker_side_effect: str = ""


@dataclass
class StoryParams:
    place: str
    activity: str
    object: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_misunderstand(world: World) -> list[str]:
    out = []
    child = world.facts["child"]
    parent = world.facts["parent"]
    act = world.facts["activity"]
    obj = world.facts["object"]
    if child.memes.get("soundy", 0.0) < THRESHOLD:
        return out
    if world.facts.get("understood"):
        return out
    sig = ("misunderstand", child.id, obj.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parent.memes["worry"] = parent.memes.get("worry", 0.0) + 1.0
    out.append(
        f"{parent.pronoun().capitalize()} heard the silly {act.sound} and thought "
        f"something odd was happening in the bath."
    )
    return out


def _r_splash_surprise(world: World) -> list[str]:
    out = []
    child = world.facts["child"]
    obj = world.facts["object"]
    if child.meters.get("splash", 0.0) < THRESHOLD:
        return out
    sig = ("surprise", child.id, obj.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["delight"] = child.memes.get("delight", 0.0) + 1.0
    out.append(f"Then there was a surprise: {obj.phrase} bobbed up like it had been waiting to join the joke.")
    return out


def _r_laugh(world: World) -> list[str]:
    out = []
    child = world.facts["child"]
    parent = world.facts["parent"]
    if parent.memes.get("worry", 0.0) < THRESHOLD:
        return out
    if child.memes.get("delight", 0.0) < THRESHOLD:
        return out
    sig = ("laugh", child.id, parent.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parent.memes["worry"] = 0.0
    parent.memes["amused"] = parent.memes.get("amused", 0.0) + 1.0
    out.append("The worry popped like a bubble, and the grown-up could not help laughing too.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_misunderstand, _r_splash_surprise, _r_laugh):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def create_story_world(setting: Setting, activity: Activity, obj_cfg: ObjectThing,
                       hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"splash": 0.0},
        memes={"curiosity": 1.0, "soundy": 0.0, "delight": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the grown-up",
        meters={},
        memes={"worry": 0.0, "amused": 0.0},
    ))
    obj = world.add(Entity(
        id=obj_cfg.id,
        kind="thing",
        type=obj_cfg.kind,
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        owner=child.id,
        caretaker=parent.id,
    ))

    world.facts.update(child=child, parent=parent, activity=activity, object=obj, trait=trait)

    world.say(f"{child.id} was a little {trait} {child.type} who loved bath time.")
    world.say(f"The bathroom was dim, and the water made soft little ripples in the tub.")
    world.say(f"{child.id} kept {activity.gerund}, because the bath felt like the perfect place for a joke.")
    world.para()

    child.meters["splash"] += 1.0
    child.memes["soundy"] += 1.0
    world.say(f'{child.id} went "splash-swish!" and then "{activity.sound}!" to make the bubbles giggle.')
    world.say(f'The {obj.label} answered with a tiny "{activity.sound}!" too, which made the whole bath feel extra silly.')
    propagate(world, narrate=True)

    world.para()
    world.say(f"{parent.id} peeked in, expecting a problem, but found a very funny scene instead.")
    if not world.facts.get("resolved"):
        world.say(f"{child.id} held up the {obj.label} and grinned.")
        world.say(f'"{activity.surprise}!" {child.id} said, and the joke finally made sense.')
        world.facts["resolved"] = True
    if parent.memes.get("amused", 0.0) >= THRESHOLD:
        world.say(f"{parent.id} laughed so hard that even the towel seemed to smile.")
        world.say(f"In the end, {child.id} kept playing, the bath stayed cozy, and the dim room was full of happy splashy sound effects.")

    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["object"] = obj
    world.facts["activity"] = activity
    return world


SETTINGS = {
    "bathroom": Setting(place="the bathroom", dim=True),
    "tiny_bathroom": Setting(place="the tiny bathroom", dim=True),
}

ACTIVITIES = {
    "sound_effects": Activity(
        id="sound_effects",
        verb="make sound effects",
        gerund="making sound effects",
        sound="splish-sploosh",
        misunderstanding="thought there was a big problem",
        surprise="It was only a toy boat popping up",
        risk="the grown-up would worry",
        keyword="bath-dim",
        tags={"bath-dim", "sound effects", "comedy"},
    ),
    "duck_orchestra": Activity(
        id="duck_orchestra",
        verb="lead a duck orchestra",
        gerund="leading a duck orchestra",
        sound="quack-quack",
        misunderstanding="thought the tub was full of tiny ducks",
        surprise="the duck was just squeaking for attention",
        risk="the bath would turn into a noisy mystery",
        keyword="bath-dim",
        tags={"bath-dim", "misunderstanding", "surprise", "sound effects"},
    ),
}

OBJECTS = {
    "toy_boat": ObjectThing(
        id="toy_boat",
        label="toy boat",
        phrase="a tiny toy boat",
        kind="toy",
        makes_sound=False,
        surprise_reveal=True,
    ),
    "squeaky_duck": ObjectThing(
        id="squeaky_duck",
        label="squeaky duck",
        phrase="a bright squeaky duck",
        kind="toy",
        makes_sound=True,
        surprise_reveal=True,
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Zoe", "Ben", "Ava", "Finn", "Lily"]
TRAITS = ["cheerful", "curious", "silly", "spirited", "playful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for act in ACTIVITIES:
            for obj in OBJECTS:
                combos.append((place, act, obj))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    activity = f["activity"]
    obj = f["object"]
    return [
        f'Write a short comedy story for a small child about "{activity.keyword}" in a dim bath.',
        f"Tell a funny story where {child.id} makes {activity.sound} sounds, {obj.label} surprises the grown-up, and everyone laughs.",
        f"Write a gentle bath-time tale with a misunderstanding, a surprise, and silly sound effects.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    activity = f["activity"]
    obj = f["object"]
    return [
        QAItem(
            question=f"What was {child.id} doing in the dim bath?",
            answer=f"{child.id} was {activity.gerund} and making the bath into a silly little comedy show.",
        ),
        QAItem(
            question=f"Why did {parent.label} first worry in the story?",
            answer=f"{parent.label.capitalize()} heard {activity.sound} sounds and misunderstood them, so it seemed like something strange might be happening.",
        ),
        QAItem(
            question=f"What surprise made the story funny?",
            answer=f"The surprise was {obj.phrase} bobbing up and joining the joke, which turned the worry into laughter.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{parent.id} laughed, {child.id} kept playing, and the dim bathroom stayed full of cheerful splashy sound effects.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks one thing is true, but the real situation is different.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that suddenly appears or happens.",
        ),
        QAItem(
            question="Why are sound effects fun in stories?",
            answer="Sound effects are fun because they help a story feel lively and silly, especially in comedy.",
        ),
    ]


ASP_RULES = r"""
% A bath-time misunderstanding is plausible when a child makes sound effects in
% a dim bath and the parent hears those sounds.
misunderstanding(A) :- activity(A), dim_bath, sound_effects(A).
surprise(A) :- activity(A), reveal_object(A).
funny_end(A) :- misunderstanding(A), surprise(A).

#show misunderstanding/1.
#show surprise/1.
#show funny_end/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.dim:
            lines.append(asp.fact("dim_bath"))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        if "sound effects" in a.tags:
            lines.append(asp.fact("sound_effects", aid))
    for oid, o in OBJECTS.items():
        if o.surprise_reveal:
            lines.append(asp.fact("reveal_object", "sound_effects"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show funny_end/1."))
    atoms = asp.atoms(model, "funny_end")
    if atoms:
        print("OK: ASP found a funny bath ending.")
        return 0
    print("MISMATCH: ASP did not find the expected ending.")
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="bathroom", activity="sound_effects", object="toy_boat", name="Mia", gender="girl", parent="mother", trait="cheerful"),
    StoryParams(place="tiny_bathroom", activity="duck_orchestra", object="squeaky_duck", name="Leo", gender="boy", parent="father", trait="silly"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny comedy world about a dim bath, misunderstanding, surprise, and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--object", choices=OBJECTS)
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
    choices = valid_combos()
    if not choices:
        raise StoryError("No valid bath story combinations exist.")
    place = args.place or rng.choice(sorted(SETTINGS))
    activity = args.activity or rng.choice(sorted(ACTIVITIES))
    obj = args.object or rng.choice(sorted(OBJECTS))
    if (place, activity, obj) not in choices:
        raise StoryError("That bath combination is not supported by this world.")
    if args.gender:
        gender = args.gender
    else:
        gender = rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, object=obj, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = create_story_world(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        OBJECTS[params.object],
        params.name,
        params.gender,
        params.parent,
        params.trait,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show funny_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show funny_end/1."))
        print("ASP atoms:", asp.atoms(model, "funny_end"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.name}: {p.activity} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
