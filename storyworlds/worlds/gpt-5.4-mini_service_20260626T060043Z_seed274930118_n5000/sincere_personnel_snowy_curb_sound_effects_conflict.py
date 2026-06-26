#!/usr/bin/env python3
"""
A small storyworld: a sincere space crew at a snowy curb, with sound effects
and a mild conflict that resolves through careful teamwork.

The seed premise:
- A little space mission stops beside a snowy curb.
- The crew hears strange sound effects from a crate or machine.
- Sincere personnel must decide whether to rush forward or handle it safely.
- The tension resolves when they coordinate and the sound turns friendly.

This world is intentionally tiny and deterministic under seeded choice, but it
supports a few plausible variations with the same premise.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pilot", "scientist", "engineer", "kid", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"commander", "boy", "man", "astronaut"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the snowy curb"
    afford_sound_effects: bool = True
    afford_conflict: bool = True


@dataclass
class Event:
    name: str
    apply: callable


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.sound: str = ""
        self.trace_log: list[str] = []

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.sound = self.sound
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

GENDERS = {"girl", "boy"}
NAMES = {
    "girl": ["Mina", "Tess", "Nova", "Lia", "Pip"],
    "boy": ["Orin", "Finn", "Jace", "Eli", "Timo"],
}
TRAITS = ["sincere", "brave", "careful", "gentle", "curious"]

CREW_ROLES = {
    "captain": "captain",
    "pilot": "pilot",
    "engineer": "engineer",
    "medic": "medic",
}

SOUND_EFFECTS = {
    "beep": "beep-beep",
    "whoosh": "whoosh",
    "clank": "clank",
    "crunch": "crunch",
    "whirr": "whirr",
}

OBJECTS = {
    "crate": {"label": "silver crate", "phrase": "a silver crate with a blinking latch"},
    "scanner": {"label": "hand scanner", "phrase": "a hand scanner with a tiny light"},
    "sled": {"label": "cargo sled", "phrase": "a cargo sled with bright rails"},
}

SETTING = Setting(place="the snowy curb", afford_sound_effects=True, afford_conflict=True)


# ---------------------------------------------------------------------------
# World events
# ---------------------------------------------------------------------------

def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    emitted: list[str] = []
    while changed:
        changed = False
        for fn in (rule_sound_grows, rule_conflict_flares, rule_resolution_warms):
            out = fn(world)
            if out:
                changed = True
                emitted.extend(out)
    if narrate:
        for s in emitted:
            world.say(s)


def rule_sound_grows(world: World) -> list[str]:
    out = []
    crew = world.facts.get("crew")
    obj = world.facts.get("object")
    if not crew or not obj:
        return out
    if crew.meters.get("alert", 0) < THRESHOLD:
        return out
    sig = ("sound", obj.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    obj.meters["noise"] = obj.meters.get("noise", 0) + 1
    out.append(f"{world.sound.capitalize()}! The little device answered with a bright {world.sound}.")
    return out


def rule_conflict_flares(world: World) -> list[str]:
    crew = world.facts.get("crew")
    object_ = world.facts.get("object")
    if not crew or not object_:
        return []
    if crew.memes.get("worry", 0) < THRESHOLD:
        return []
    sig = ("conflict", crew.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crew.memes["conflict"] = crew.memes.get("conflict", 0) + 1
    return [f"{crew.id} frowned, because the sound felt strange and the curb looked slippery."]


def rule_resolution_warms(world: World) -> list[str]:
    crew = world.facts.get("crew")
    helper = world.facts.get("helper")
    obj = world.facts.get("object")
    if not crew or not helper or not obj:
        return []
    if helper.memes.get("sincere", 0) < THRESHOLD:
        return []
    if crew.memes.get("conflict", 0) < THRESHOLD:
        return []
    sig = ("resolve", crew.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crew.memes["conflict"] = 0
    crew.memes["trust"] = crew.memes.get("trust", 0) + 1
    obj.meters["safe"] = obj.meters.get("safe", 0) + 1
    return [f"Together, they listened closely, and the noisy thing turned into a friendly sound."]


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def valid_combo(role: str, obj_id: str, sound_key: str) -> bool:
    return role in CREW_ROLES and obj_id in OBJECTS and sound_key in SOUND_EFFECTS


def explain_rejection(role: str, obj_id: str, sound_key: str) -> str:
    if role not in CREW_ROLES:
        return "(No story: that crew role does not fit this tiny space mission.)"
    if obj_id not in OBJECTS:
        return "(No story: that object is not part of the shipyard cargo.)"
    if sound_key not in SOUND_EFFECTS:
        return "(No story: that sound effect is not in the sound board.)"
    return "(No story: that combination does not make a clear conflict-and-fix story.)"


# ---------------------------------------------------------------------------
# Narrative functions
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} {hero.type} on a little space crew, and {helper.id} was the most {helper.traits[0]} of the personnel."
    )
    world.say(
        f"They were parked beside {world.setting.place}, where the snow made everything look quiet and blue."
    )


def setup(world: World, hero: Entity, helper: Entity, obj: Entity, sound_key: str) -> None:
    world.say(
        f"Near the curb sat {obj.phrase}, and every so often it made a {SOUND_EFFECTS[sound_key]} sound."
    )
    world.say(
        f"{hero.id} liked the mission, but the sound made {hero.pronoun('possessive')} stomach feel wobbly."
    )
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    helper.memes["sincere"] = helper.memes.get("sincere", 0) + 1
    world.sound = SOUND_EFFECTS[sound_key]
    world.facts.update(crew=hero, helper=helper, object=obj, sound_key=sound_key)
    propogate = propagate
    propogate(world, narrate=True)


def conflict_scene(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    world.para()
    world.say(
        f"{hero.id} wanted to grab {obj.it()} right away, but {helper.id} held up a hand."
    )
    world.say(
        f'"Wait," {helper.id} said. "Snow by a curb can hide ice. Let me check first."'
    )
    hero.memes["impulse"] = hero.memes.get("impulse", 0) + 1
    propagate(world, narrate=True)


def resolution_scene(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    world.para()
    world.say(
        f"{helper.id} pointed the scanner at the crate, then nodded with a sincere smile."
    )
    world.say(
        f'"It is only a loose latch," {helper.id} said. "We can open it together, slowly."'
    )
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    propagate(world, narrate=True)
    world.say(
        f"{hero.id} breathed out, {obj.id} stopped rattling, and the snowy curb felt safe again."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    role: str
    gender: str
    name: str
    helper_name: str
    helper_role: str
    object_id: str
    sound_key: str
    seed: Optional[int] = None


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.role,
            traits=["sincere", "careful"],
        )
    )
    helper = world.add(
        Entity(
            id=params.helper_name,
            kind="character",
            type=params.helper_role,
            traits=["sincere", "steady"],
        )
    )
    obj_info = OBJECTS[params.object_id]
    obj = world.add(
        Entity(
            id=params.object_id,
            kind="thing",
            type=params.object_id,
            label=obj_info["label"],
            phrase=obj_info["phrase"],
        )
    )
    introduce(world, hero, helper)
    setup(world, hero, helper, obj, params.sound_key)
    conflict_scene(world, hero, helper, obj)
    resolution_scene(world, hero, helper, obj)

    world.facts.update(
        hero=hero,
        helper=helper,
        obj=obj,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obj = f["obj"]
    sound_key = f["params"].sound_key
    return [
        f'Write a short space-adventure story for a young child about a {hero.traits[0]} {hero.type} named {hero.id} who hears {SOUND_EFFECTS[sound_key]} by a {world.setting.place}.',
        f"Tell a gentle story where {hero.id} and {helper.id} are crew members, a {obj.label} is making a strange sound, and they solve the problem together.",
        f'Write a simple story set at {world.setting.place} that includes the sound word "{SOUND_EFFECTS[sound_key]}" and ends with the crew feeling safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obj = f["obj"]
    params = f["params"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {hero.traits[0]} {hero.type}, and {helper.id}, a {helper.traits[0]} member of the personnel.",
        ),
        QAItem(
            question=f"What was making the strange sound near the curb?",
            answer=f"{obj.phrase} was making the sound {SOUND_EFFECTS[params.sound_key]}.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel worried at first?",
            answer=f"{hero.id} felt worried because the sound was strange and the snowy curb could be slippery.",
        ),
        QAItem(
            question=f"How did the crew solve the problem?",
            answer=f"{helper.id} checked the {obj.label} carefully, and then {hero.id} and {helper.id} opened it together without rushing.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the end, the conflict was gone, the sound felt friendly, and the snowy curb felt safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a curb?",
            answer="A curb is the raised edge at the side of a road or sidewalk.",
        ),
        QAItem(
            question="Why can snow make a curb slippery?",
            answer="Snow can turn to ice or packed slush, which makes the ground slick and harder to walk on.",
        ),
        QAItem(
            question="What does a beep sound like?",
            answer='A beep is a short, sharp sound, like "beep" from a small machine or scanner.',
        ),
        QAItem(
            question="What does it mean to be sincere?",
            answer="Being sincere means being honest, open, and really meaning what you say.",
        ),
        QAItem(
            question="Who are personnel?",
            answer="Personnel are the people who work together as a team, like the crew on a mission.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(
            f"{e.id}: type={e.type}, meters={dict(e.meters)}, memes={dict(e.memes)}"
        )
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
role(captain;pilot;engineer;medic).
sound(beep;whoosh;clank;crunch;whirr).
object(crate;scanner;sled).

conflict(Role,Obj,Sound) :- role(Role), object(Obj), sound(Sound).
friendly_fix(Role,Obj,Sound) :- conflict(Role,Obj,Sound).

#show conflict/3.
#show friendly_fix/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for r in CREW_ROLES:
        lines.append(asp.fact("role", r))
    for s in SOUND_EFFECTS:
        lines.append(asp.fact("sound", s))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show conflict/3."))
    return sorted(set(asp.atoms(model, "conflict")))


def asp_verify() -> int:
    py = {(r, o, s) for r in CREW_ROLES for o in OBJECTS for s in SOUND_EFFECTS if valid_combo(r, o, s)}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP parity verified for {len(py)} combos.")
        return 0
    print("MISMATCH between Python and ASP:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params / parser / generator
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure storyworld at a snowy curb.")
    ap.add_argument("--role", choices=sorted(CREW_ROLES))
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-role", choices=sorted(CREW_ROLES))
    ap.add_argument("--object", dest="object_id", choices=sorted(OBJECTS))
    ap.add_argument("--sound", dest="sound_key", choices=sorted(SOUND_EFFECTS))
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
    role = args.role or rng.choice(list(CREW_ROLES))
    gender = args.gender or rng.choice(list(GENDERS))
    if args.role and args.role not in CREW_ROLES:
        raise StoryError("That crew role is not part of this storyworld.")
    if args.gender and args.gender not in GENDERS:
        raise StoryError("That gender is not part of this storyworld.")

    obj_id = args.object_id or rng.choice(list(OBJECTS))
    sound_key = args.sound_key or rng.choice(list(SOUND_EFFECTS))
    if not valid_combo(role, obj_id, sound_key):
        raise StoryError(explain_rejection(role, obj_id, sound_key))

    name = args.name or rng.choice(NAMES[gender])
    helper_name = args.helper_name or rng.choice([n for n in NAMES[gender] if n != name] or NAMES[gender])
    helper_role = args.helper_role or rng.choice([r for r in CREW_ROLES if r != role])

    return StoryParams(
        role=role,
        gender=gender,
        name=name,
        helper_name=helper_name,
        helper_role=helper_role,
        object_id=obj_id,
        sound_key=sound_key,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(role="captain", gender="girl", name="Nova", helper_name="Mina", helper_role="engineer", object_id="crate", sound_key="beep"),
    StoryParams(role="pilot", gender="boy", name="Eli", helper_name="Orin", helper_role="medic", object_id="scanner", sound_key="whirr"),
    StoryParams(role="engineer", gender="girl", name="Tess", helper_name="Lia", helper_role="captain", object_id="sled", sound_key="crunch"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show conflict/3.\n#show friendly_fix/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show conflict/3.\n#show friendly_fix/3."))
        print(f"{len(asp.atoms(model, 'conflict'))} conflict combinations available.")
        for t in asp.atoms(model, "conflict"):
            print(" ", t)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} / {p.object_id} / {p.sound_key}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
