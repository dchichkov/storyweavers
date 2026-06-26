#!/usr/bin/env python3
"""
trust_locker_veil_sound_effects_problem_solving.py
==================================================

A small adventure storyworld about trust, a locker, a veil, and the sound
effects that lead a child to solve a problem.

Premise:
- A child is planning a little adventure.
- A locker holds a hidden thing that matters.
- A veil changes how the child sees the moment.
- Sound effects mark the turning points.
- The child must decide who to trust and how to solve the problem.

This world is intentionally compact: it generates a small, complete story with
a beginning, a tension, a turn, and a resolution.
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
# Registries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Setting:
    place: str
    mood: str
    affordance: str


@dataclass(frozen=True)
class CharacterSpec:
    name: str
    role: str
    trait: str


@dataclass(frozen=True)
class ObjectSpec:
    label: str
    phrase: str
    kind: str


@dataclass(frozen=True)
class SoundSpec:
    cue: str
    effect: str
    moment: str


SETTINGS = {
    "old_station": Setting(place="an old train station", mood="windy", affordance="echoes"),
    "forest_gate": Setting(place="a piney forest gate", mood="bright", affordance="rustles"),
    "harbor_shed": Setting(place="a small harbor shed", mood="salt-bright", affordance="clanks"),
}

CHARACTERS = {
    "mira": CharacterSpec(name="Mira", role="girl", trait="curious"),
    "jace": CharacterSpec(name="Jace", role="boy", trait="careful"),
    "noor": CharacterSpec(name="Noor", role="girl", trait="brave"),
    "tobin": CharacterSpec(name="Tobin", role="boy", trait="steady"),
}

OBJECTS = {
    "locker_key": ObjectSpec(label="locker key", phrase="a brass locker key", kind="key"),
    "map_roll": ObjectSpec(label="map roll", phrase="a rolled map wrapped in twine", kind="map"),
    "signal_lamp": ObjectSpec(label="signal lamp", phrase="a little signal lamp", kind="lamp"),
}

VEILS = {
    "mist_veil": ObjectSpec(label="mist veil", phrase="a thin mist veil", kind="veil"),
    "cloth_veil": ObjectSpec(label="cloth veil", phrase="a pale cloth veil", kind="veil"),
}

SOUNDS = {
    "clink": SoundSpec(cue="Clink!", effect="the locker door tapped the key", moment="the first hint"),
    "whirr": SoundSpec(cue="Whirr!", effect="the latch shifted with a soft spin", moment="the lock began to give"),
    "click": SoundSpec(cue="Click!", effect="the door sprang open", moment="the answer arrived"),
    "tap": SoundSpec(cue="Tap-tap!", effect="small steps sounded in the hall", moment="the helper came near"),
}

TROUBLE = {
    "stuck_lock": "the locker would not open",
    "missing_key": "the key was missing",
    "faded_map": "the map was too hard to read",
}


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0, "pressure": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"trust": 0.0, "worry": 0.0, "joy": 0.0})


@dataclass
class StoryParams:
    setting: str
    hero: str
    friend: str
    object: str
    veil: str
    trouble: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.flags: dict[str, object] = {}

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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.flags = _copy.deepcopy(self.flags)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A valid story needs a setting, a hero, a friend, an object, and a veil.
valid_story(S, H, F, O, V) :- setting(S), hero(H), friend(F), object(O), veil(V).

% Trust matters if the friend helps and the hero accepts the help.
trust_help(H, F) :- help(F), trusts(H, F).

% A problem is solvable when the locker opens or the map becomes readable.
solved(T) :- locker_open(T).
solved(T) :- map_readable(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CHARACTERS:
        lines.append(asp.fact("hero", cid))
        lines.append(asp.fact("friend", cid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for vid in VEILS:
        lines.append(asp.fact("veil", vid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    atoms = set(asp.atoms(model, "valid_story"))
    expected = set()
    for s in SETTINGS:
        for h in CHARACTERS:
            for f in CHARACTERS:
                if f != h:
                    for o in OBJECTS:
                        for v in VEILS:
                            expected.add((s, h, f, o, v))
    if atoms == expected:
        print(f"OK: clingo gate matches registry combinations ({len(atoms)} combos).")
        return 0
    print("MISMATCH between clingo and registry combinations:")
    if atoms - expected:
        print("  only in clingo:", sorted(atoms - expected))
    if expected - atoms:
        print("  only in python:", sorted(expected - atoms))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def choose_reasonable_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    settings = list(SETTINGS.keys())
    heroes = list(CHARACTERS.keys())
    objects = list(OBJECTS.keys())
    veils = list(VEILS.keys())
    troubles = list(TROUBLE.keys())

    if args.hero and args.friend and args.hero == args.friend:
        raise StoryError("The hero and the friend must be different people.")

    picks = []
    for s in settings:
        if args.setting and s != args.setting:
            continue
        for h in heroes:
            if args.hero and h != args.hero:
                continue
            for f in heroes:
                if h == f:
                    continue
                if args.friend and f != args.friend:
                    continue
                for o in objects:
                    if args.object and o != args.object:
                        continue
                    for v in veils:
                        if args.veil and v != args.veil:
                            continue
                        for t in troubles:
                            picks.append((s, h, f, o, v, t))
    if not picks:
        raise StoryError("No valid combination matches the given options.")
    s, h, f, o, v, t = rng.choice(sorted(picks))
    return StoryParams(setting=s, hero=h, friend=f, object=o, veil=v, trouble=t)


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero_spec = CHARACTERS[params.hero]
    friend_spec = CHARACTERS[params.friend]
    obj_spec = OBJECTS[params.object]
    veil_spec = VEILS[params.veil]

    hero = world.add(Entity(id=hero_spec.name, kind="character", label=hero_spec.role))
    friend = world.add(Entity(id=friend_spec.name, kind="character", label=friend_spec.role))
    locker = world.add(Entity(id="locker", kind="thing", label="locker"))
    object_ent = world.add(Entity(id=obj_spec.kind, kind="thing", label=obj_spec.label))
    veil_ent = world.add(Entity(id=veil_spec.kind, kind="thing", label=veil_spec.label))

    world.flags.update(
        hero=hero,
        friend=friend,
        locker=locker,
        object=object_ent,
        veil=veil_ent,
        trouble=params.trouble,
        setting=world.setting,
        hero_spec=hero_spec,
        friend_spec=friend_spec,
        object_spec=obj_spec,
        veil_spec=veil_spec,
    )
    return world


def sound_line(sound: SoundSpec, tail: str) -> str:
    return f"{sound.cue} {sound.effect} {tail}"


def generate_story(world: World) -> None:
    f = world.flags
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    obj: Entity = f["object"]
    veil: Entity = f["veil"]

    hero_spec: CharacterSpec = f["hero_spec"]
    friend_spec: CharacterSpec = f["friend_spec"]
    obj_spec: ObjectSpec = f["object_spec"]
    veil_spec: ObjectSpec = f["veil_spec"]

    hero.memes["trust"] += 1
    hero.memes["worry"] += 1

    world.say(
        f"{hero_spec.name} was a {hero_spec.trait} {hero_spec.role} who loved little adventures at {world.setting.place}."
    )
    world.say(
        f"One day, {hero_spec.name} and {friend_spec.name} found {obj_spec.phrase} beside a locked locker."
    )
    world.say(
        f"Near the door, they also noticed {veil_spec.phrase}, and it fluttered like a secret flag."
    )

    world.para()
    world.say(
        f"{world.setting.place.capitalize()} felt full of {world.setting.affordance}, but the locker stayed stubborn and quiet."
    )
    if f["trouble"] == "stuck_lock":
        world.say(
            f"{hero_spec.name} tried the handle. Nothing moved."
        )
        world.say(
            sound_line(SOUNDS["clink"], "the key brushed the metal and made a tiny, sharp song.")
        )
        world.say(
            f"{hero_spec.name} frowned and looked at {friend_spec.name}. The problem was clear: the locker would not open."
        )
    elif f["trouble"] == "missing_key":
        world.say(
            f"{hero_spec.name} patted every pocket, but the key was gone."
        )
        world.say(
            sound_line(SOUNDS["tap"], "their boots echoed down the hall as they searched.")
        )
        world.say(
            f"{friend_spec.name} pointed at the locker and said the answer might still be nearby."
        )
    else:
        world.say(
            f"{hero_spec.name} held up the map, but the lines were faded under the soft veil of dust and light."
        )
        world.say(
            sound_line(SOUNDS["whirr"], "the air moved across the paper, but the path still looked blurred.")
        )
        world.say(
            f"{friend_spec.name} squinted and said they needed a better way to read it."
        )

    world.para()
    friend.memes["trust"] += 1
    hero.memes["trust"] += 1
    world.say(
        f"Then {friend_spec.name} said, \"Trust me. If we use the veil, we can solve this.\""
    )
    world.say(
        f"{hero_spec.name} listened, because the adventure felt safer when the two of them thought together."
    )

    if params.veil == "mist_veil":
        world.say(
            f"They held the mist veil against the doorway, and the drifting air showed a pattern in the dust."
        )
    else:
        world.say(
            f"They held the cloth veil over the lamp, and the softer light made the latch easy to see."
        )

    world.say(
        sound_line(SOUNDS["click"], f"{world.setting.affordance.capitalize()} answered at once.")
    )
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1

    if params.trouble == "stuck_lock":
        world.flags["locker_open"] = True
        world.say(
            f"The locker door opened, and inside was the {obj_spec.label} they needed for the trail ahead."
        )
    elif params.trouble == "missing_key":
        world.flags["locker_open"] = True
        world.say(
            f"They found the key tucked in the hem of the veil, then opened the locker with a proud little grin."
        )
    else:
        world.flags["map_readable"] = True
        world.say(
            f"With the veil set just right, the map became clear, and the path to the next gate shone out."
        )

    world.say(
        f"{hero_spec.name} smiled at {friend_spec.name} and said their trust had turned the trouble into a win."
    )
    world.say(
        f"Together they stepped forward, ready for the next part of the adventure."
    )


def world_from_params(params: StoryParams) -> World:
    world = setup_world(params)
    generate_story(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.flags
    hero_spec: CharacterSpec = f["hero_spec"]
    friend_spec: CharacterSpec = f["friend_spec"]
    obj_spec: ObjectSpec = f["object_spec"]
    veil_spec: ObjectSpec = f["veil_spec"]
    return [
        f'Write a short adventure story for a young child that includes "{hero_spec.name}", "{friend_spec.name}", and a locker.',
        f'Write a problem-solving story where trust helps {hero_spec.name} and {friend_spec.name} open a locker and use a veil.',
        f'Create a child-friendly adventure with sound effects like "Clink!" and "Click!" and a happy solution.',
        f'Write a story about {hero_spec.name} finding {obj_spec.phrase} near {veil_spec.phrase} and solving a problem by working together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.flags
    hero_spec: CharacterSpec = f["hero_spec"]
    friend_spec: CharacterSpec = f["friend_spec"]
    obj_spec: ObjectSpec = f["object_spec"]
    veil_spec: ObjectSpec = f["veil_spec"]

    qas = [
        QAItem(
            question=f"Who were the main characters in the story?",
            answer=f"The main characters were {hero_spec.name} and {friend_spec.name}, two children on a little adventure.",
        ),
        QAItem(
            question=f"What problem did {hero_spec.name} face at the locker?",
            answer=f"{hero_spec.name} faced {TROUBLE[f['trouble']]}, so the locker did not give up its secret right away.",
        ),
        QAItem(
            question=f"How did the veil help solve the problem?",
            answer=f"The {veil_spec.label} helped by changing what the children could see, so they could find the right answer and open the locker or read the map more clearly.",
        ),
        QAItem(
            question=f"What did the sound effects show in the story?",
            answer="The sound effects showed important moments, like the locker being tested, the latch moving, and the answer finally clicking into place.",
        ),
        QAItem(
            question=f"What was inside the locker or hidden by the problem?",
            answer=f"The story centered on {obj_spec.phrase}, which the children wanted to use for the next part of their adventure.",
        ),
        QAItem(
            question=f"Why did {hero_spec.name} trust {friend_spec.name}?",
            answer=f"{hero_spec.name} trusted {friend_spec.name} because the adventure felt better when they listened to each other and solved the problem together.",
        ),
    ]
    return qas


WORLD_KNOWLEDGE = {
    "trust": [
        QAItem(
            question="What is trust?",
            answer="Trust means believing someone will try to help, tell the truth, or keep you safe.",
        )
    ],
    "locker": [
        QAItem(
            question="What is a locker?",
            answer="A locker is a small box-like door or cabinet that can be locked to keep things safe.",
        )
    ],
    "veil": [
        QAItem(
            question="What is a veil?",
            answer="A veil is a thin covering that can soften what you see, like a light curtain over something.",
        )
    ],
    "sound": [
        QAItem(
            question="Why do stories use sound effects?",
            answer="Stories use sound effects to help readers hear important moments in their imagination and feel the action.",
        )
    ],
    "problem_solving": [
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means thinking, trying ideas, and finding a way to fix a difficult situation.",
        )
    ],
    "adventure": [
        QAItem(
            question="What makes a story feel like an adventure?",
            answer="An adventure story usually has a journey, a problem to solve, and a brave choice that leads forward.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"trust", "locker", "veil", "sound", "problem_solving", "adventure"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(WORLD_KNOWLEDGE.get(tag, []))
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


# ---------------------------------------------------------------------------
# CLI and output
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id:10} ({ent.kind:9}) {ent.label:12} {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with trust, locker, veil, sound effects, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--hero", choices=CHARACTERS.keys())
    ap.add_argument("--friend", choices=CHARACTERS.keys())
    ap.add_argument("--object", choices=OBJECTS.keys())
    ap.add_argument("--veil", choices=VEILS.keys())
    ap.add_argument("--trouble", choices=TROUBLE.keys())
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return choose_reasonable_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = world_from_params(params)
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
    StoryParams(setting="old_station", hero="mira", friend="jace", object="locker_key", veil="mist_veil", trouble="stuck_lock"),
    StoryParams(setting="forest_gate", hero="noor", friend="tobin", object="map_roll", veil="cloth_veil", trouble="faded_map"),
    StoryParams(setting="harbor_shed", hero="jace", friend="mira", object="signal_lamp", veil="mist_veil", trouble="missing_key"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/5."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible stories:")
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
            header = f"### {p.hero} and {p.friend} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
