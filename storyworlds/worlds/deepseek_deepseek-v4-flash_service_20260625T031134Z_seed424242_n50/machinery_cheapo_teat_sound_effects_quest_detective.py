#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/machinery_cheapo_teat_sound_effects_quest_detective.py
==============================================================================================================================================

A standalone *story world* sketch for "The Machinery at the Teat" tale and close,
*constraint-checked* variations of it.

Initial story (used to build a world model):
---
Detective Grizzle lived in a small town with old machinery. Every night, a 
mysterious sound came from the old teacup factory. The cheapo watch on the 
detective's wrist ticked loudly. Grizzle followed the whirring noise through 
creaking doors. The sound led to a dusty room with a giant teat machine. 
The machine sputtered, then stopped. Grizzle found a loose bolt. With a twist, 
the noise vanished. The mystery was solved.

Causal state updates:
---
    follow sound               -> detective.location.clue++
                                  detective.curiosity++
    examine machinery           -> machinery.understood++
    find fault                 -> machinery.fixed = true
    resolve case               -> detective.satisfaction++ ; detective.case_active = false
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

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    loudness: float = 0.0
    place: str = ""
    hidden: bool = False
    broken: bool = True
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        male = {"detective", "boy", "man", "dad"}
        female = {"girl", "woman", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"detective": "detective", "machine": "machine"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the old factory"
    affords: set[str] = field(default_factory=set)


@dataclass
class SoundEffect:
    id: str
    verb: str
    noun: str
    onomatopoeia: str
    source: str
    tone: str = "mysterious"


@dataclass
class Clue:
    label: str
    phrase: str
    type: str
    hidden: bool = True
    solves: Optional[str] = None


@dataclass
class Gear:
    label: str
    phrase: str
    property: str


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.sound_trace: list[str] = []

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
        clone.paragraphs = [[]]
        clone.sound_trace = list(self.sound_trace)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_follow_sound(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["heard_sound"] >= THRESHOLD and not actor.memes["followed"]:
            sig = ("follow", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["followed"] = 1.0
            actor.meters["clue"] += 1
            out.append(
                f"{actor.pronoun('possessive').capitalize()} ears perked up. "
                f"The sound led {actor.pronoun('object')} through the shadows."
            )
    return out


def _r_examine_machinery(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for machine in [e for e in world.entities.values() if e.type == "machinery"]:
            if actor.memes["followed"] >= THRESHOLD and not machine.memes["examined"]:
                sig = ("examine", machine.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                machine.memes["examined"] = 1.0
                machine.meters["understood"] += 1
                out.append(
                    f"{actor.pronoun().capitalize()} studied the {machine.label} "
                    f"with careful eyes."
                )
    return out


def _r_find_fault(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for machine in [e for e in world.entities.values() if e.type == "machinery"]:
            if machine.memes["examined"] >= THRESHOLD and machine.broken:
                sig = ("fix", machine.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                machine.broken = False
                actor.memes["satisfaction"] += 1
                actor.memes["case_active"] = 0.0
                out.append(
                    f"{actor.pronoun().capitalize()} found the loose bolt "
                    f"and twisted it tight. The machine sighed and was still."
                )
    return out


CAUSAL_RULES = [
    Rule("follow_sound", "investigation", _r_follow_sound),
    Rule("examine_machinery", "investigation", _r_examine_machinery),
    Rule("find_fault", "resolution", _r_find_fault),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def detect_intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.type} who noticed every little thing. "
        f"The {', '.join(hero.traits)} sleuth lived for puzzles."
    )


def cheapo_watch(world: World, hero: Entity, gear: Gear) -> None:
    hero.memes["equipped"] += 1
    world.say(
        f"A {gear.label} ticked loudly on {hero.pronoun('possessive')} wrist. "
        f"It was a {gear.property} thing, but it worked."
    )
    e = world.add(Entity(
        id="cheapo_watch", kind="thing", type="gear", label=gear.label,
        phrase=gear.phrase, owner=hero.id, loudness=0.5,
    ))


def sound_intro(world: World, sound: SoundEffect) -> None:
    world.say(
        f"'{sound.onomatopoeia}' -- the {sound.noun} echoed through "
        f"{world.setting.place}. It was a {sound.tone} {sound.verb}."
    )
    world.sound_trace.append(sound.onomatopoeia)


def follow_quest(world: World, hero: Entity, sound: SoundEffect) -> None:
    hero.memes["heard_sound"] += 1
    propagate(world)
    world.say(
        f"{hero.id} followed the {sound.noun} through creaking doors. "
        f"The {sound.onomatopoeia} grew louder."
    )


def machinery_found(world: World, hero: Entity, machine: Entity) -> None:
    world.say(
        f"In a dusty room, {hero.pronoun()} found a giant {machine.label}. "
        f"It sputtered and groaned."
    )


def clue_discovery(world: World, hero: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} spotted {clue.phrase} hidden in the "
        f"shadows. '{clue.label}!' {hero.pronoun()} whispered."
    )


def resolve_case(world: World, hero: Entity, machine: Entity) -> None:
    hero.memes["satisfaction"] -= 0.5
    propagate(world)
    world.say(
        f"With a final twist, the {machine.label} fell silent. "
        f"The mystery was solved. {hero.id} smiled."
    )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "factory": Setting(place="the old factory", affords={"whir", "clank"}),
    "warehouse": Setting(place="the empty warehouse", affords={"buzz", "hiss"}),
    "workshop": Setting(place="the dusty workshop", affords={"creak", "rattle"}),
}

SOUNDS = {
    "whir": SoundEffect(id="whir", verb="whirring", noun="sound of spinning gears",
                        onomatopoeia="WHIRRR", source="machinery"),
    "clank": SoundEffect(id="clank", verb="clanking", noun="noise of metal on metal",
                          onomatopoeia="CLANK", source="pipes"),
    "buzz": SoundEffect(id="buzz", verb="buzzing", noun="electrical hum",
                        onomatopoeia="BUZZZZ", source="wires"),
    "hiss": SoundEffect(id="hiss", verb="hissing", noun="steam escaping",
                         onomatopoeia="HISSS", source="pipes"),
    "creak": SoundEffect(id="creak", verb="creaking", noun="old wood bending",
                          onomatopoeia="CREEEAK", source="floor"),
    "rattle": SoundEffect(id="rattle", verb="rattling", noun="loose parts shaking",
                           onomatopoeia="RATTLERATTLE", source="machinery"),
}

MACHINERY = {
    "teat_machine": Entity(id="teat_machine", kind="thing", type="machinery",
                            label="teat machine",
                            phrase="a huge teat machine with many tubes",
                            broken=True, place="dusty room"),
    "gear_box": Entity(id="gear_box", kind="thing", type="machinery",
                        label="gear box",
                        phrase="a box of tangled gears",
                        broken=True, place="corner"),
    "steam_engine": Entity(id="steam_engine", kind="thing", type="machinery",
                            label="steam engine",
                            phrase="an old steam engine",
                            broken=True, place="boiler room"),
}

CLUES = {
    "loose_bolt": Clue(label="loose bolt", phrase="a shiny, loose bolt",
                        type="mechanical", hidden=True, solves="teat_machine"),
    "frayed_wire": Clue(label="frayed wire", phrase="a frayed, sparking wire",
                         type="electrical", hidden=True, solves="gear_box"),
    "cracked_pipe": Clue(label="cracked pipe", phrase="a cracked, dripping pipe",
                          type="plumbing", hidden=True, solves="steam_engine"),
}

GEAR_ITEMS = [
    Gear(label="cheapo watch", phrase="a cheapo watch that ticked loudly",
         property="cheap"),
    Gear(label="magnifying glass", phrase="a small magnifying glass",
         property="scratched"),
    Gear(label="notebook", phrase="a worn leather notebook",
         property="bent"),
]

DETECTIVE_NAMES = ["Grizzle", "Bones", "Whisker", "Muzzle", "Snout"]
TRAITS = ["sharp-eyed", "thoughtful", "persistent", "curious", "methodical"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(setting, sound, machine)"""
    combos = []
    for place, setting in SETTINGS.items():
        for sid, sound in SOUNDS.items():
            for mid in MACHINERY:
                if sound.source in {"machinery", "pipes", "floor"}:
                    combos.append((place, sid, mid))
    return combos


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    sound: str
    machine: str
    clue: str
    name: str
    gear: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "machinery": [("What is machinery?", "Machinery is a machine or group of machines that do work, like gears and engines.")],
    "teat": [("What is a teat?", "A teat is a part of a machine that pours or drips liquid, like a faucet.")],
    "cheapo": [("What does cheapo mean?", "Cheapo means something that is cheap or not well made, but still works.")],
    "sound": [("How do we describe sounds in stories?", "Sounds like WHIRRR or CLANK help readers imagine what is happening.")],
    "quest": [("What is a quest?", "A quest is a search for something, like a clue or an answer to a mystery.")],
    "detective": [("What does a detective do?", "A detective looks for clues and solves mysteries.")],
}
KNOWLEDGE_ORDER = ["machinery", "teat", "cheapo", "sound", "quest", "detective"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f.get("hero")
    sound = f.get("sound")
    return [
        "Write a detective story for young children that includes a mysterious sound.",
        "Tell a story about a detective who finds a clue and solves a machinery puzzle.",
        "Write a short tale with the words 'machinery', 'cheapo', and 'teat'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f.get("hero")
    sound = f.get("sound")
    machine = f.get("machine")
    clue = f.get("clue")
    qa = []
    if hero and sound:
        qa.append(QAItem(
            question=f"What sound did {hero.id} follow?",
            answer=f"{hero.id} followed the {sound.noun} that went '{sound.onomatopoeia}'."
        ))
    if machine:
        qa.append(QAItem(
            question=f"What did {hero.id} find in {world.setting.place}?",
            answer=f"{hero.pronoun('possessive').capitalize()} found a {machine.label} that was broken and making noise."
        ))
    if clue:
        qa.append(QAItem(
            question=f"What clue helped {hero.id} solve the case?",
            answer=f"{hero.pronoun('possessive').capitalize()} found {clue.phrase} and fixed the machine."
        ))
    return qa if qa else [QAItem("What is this story about?",
                                  "It is about a detective who solves a machinery mystery.")]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in {"machinery", "teat", "cheapo", "sound", "quest", "detective"}:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out


# ---------------------------------------------------------------------------
# Clingo ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting_with_sound(P, S) :- affords(P, S), sound_source(S, mach).
compatible(P, S, M) :- setting_with_sound(P, S), machine(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("sound_source", sid, s.source))
    for mid in MACHINERY:
        lines.append(asp.fact("machine", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH")
    return 1


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: machinery detective quest with sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--machine", choices=MACHINERY)
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
    combos = [(p, s, m) for p, s, m in valid_combos()
              if (args.place is None or p == args.place)
              and (args.sound is None or s == args.sound)
              and (args.machine is None or m == args.machine)]
    if not combos:
        raise StoryError("No valid combination.")
    p, s, m = rng.choice(sorted(combos))
    name = args.name or rng.choice(DETECTIVE_NAMES)
    clue = rng.choice(list(CLUES.keys()))
    gear = rng.choice(GEAR_ITEMS).label
    trait = rng.choice(TRAITS)
    return StoryParams(place=p, sound=s, machine=m, clue=clue, name=name, gear=gear, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    sound = SOUNDS[params.sound]
    machine = MACHINERY[params.machine]
    clue = CLUES[params.clue]

    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type="detective",
                            traits=["detective", params.trait]))
    mach = world.add(Entity(id=params.machine, kind="thing", type="machinery",
                             label=machine.label, phrase=machine.phrase,
                             broken=True, place=machine.place))

    detect_intro(world, hero)
    cheapo_watch(world, hero, Gear(label=params.gear, phrase=params.gear, property="cheap"))

    world.para()
    sound_intro(world, sound)
    follow_quest(world, hero, sound)

    world.para()
    machinery_found(world, hero, mach)
    clue_discovery(world, hero, clue)

    world.para()
    resolve_case(world, hero, mach)

    world.facts.update(hero=hero, sound=sound, machine=mach, clue=clue)

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
        lines = ["--- world model state ---"]
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            if e.broken:
                bits.append("broken")
            lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
        print("\n".join(lines))
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World-knowledge questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(f"  {combo}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples = []
    if args.all:
        combos = valid_combos()
        for p, s, m in combos:
            params = StoryParams(place=p, sound=s, machine=m,
                                 clue=random.choice(list(CLUES.keys())),
                                 name=random.choice(DETECTIVE_NAMES),
                                 gear=random.choice(GEAR_ITEMS).label,
                                 trait=random.choice(TRAITS))
            samples.append(generate(params))
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
            header = f"### {p.name}: {p.sound} at {p.place} (machine: {p.machine})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
