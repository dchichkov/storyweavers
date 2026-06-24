#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T073613Z_seed779406221_n50/gristle_whir_real_ist_dialogue_ghost_story.py
===============================================================================================================

A standalone tiny storyworld with a Ghost-Story mood, built from the seed words
"gristle", "whir", and "real-ist". The setting is a small old house where a
child listens for a ghost, a skeptical "real-ist" voice pushes the inquiry
forward, and dialogue carries the turn from spookiness to explanation.

Premise:
- A child hears a ghostly sound in an old room.
- The room contains a bowl of broth with a bit of gristle, and a small fan that
  makes a steady whir.
- The child is a real-ist: they want proof, not just a chill.

Tension:
- The house grows quiet, the sound seems ghostly, and fear rises.
- The child's parent or companion wants to hush the worry, but the child keeps
  asking questions.

Turn:
- The whir points to the fan, not a spirit.
- The gristle in the bowl is the only thing truly surprising to the child.

Resolution:
- The child proves the noise is real, but not a ghost.
- The ending image shows the fan, the broth, and the child feeling braver.

The world uses physical meters and emotional memes, a small causal rule engine,
grounded Q&A, a reasonableness gate, and an inline ASP twin for parity checks.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    loud: bool = False
    whirs: bool = False
    edible: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    old: bool = True
    rooms: set[str] = field(default_factory=set)


@dataclass
class Sound:
    id: str
    label: str
    clue: str
    source: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    sound: str
    food: str
    child: str
    child_gender: str
    companion: str
    companion_gender: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def people(self) -> list[Entity]:
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
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_nervous(world: World) -> list[str]:
    out = []
    for p in world.people():
        if p.memes["fear"] < THRESHOLD:
            continue
        sig = ("nervous", p.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        p.memes["alert"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("nervous", _r_nervous)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            for s in rule.apply(world):
                if s:
                    changed = True
                    produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sound_at_risk(sound: Sound, setting: Setting) -> bool:
    return sound.id in {"whir", "ghost_rattle"} and setting.old


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for snd in SOUNDS:
            for food in FOODS:
                if sound_at_risk(SOUNDS[snd], SETTINGS[s]):
                    combos.append((s, snd, food))
    return combos


def explain_rejection(sound: Sound, setting: Setting) -> str:
    return f"(No story: {sound.label} doesn't fit this small ghost-story setting.)"


def whisper_line(child: Entity, text: str) -> str:
    return f'"{text}," {child.id} whispered.'


def tell(setting: Setting, sound: Sound, food_label: str, child_name: str, child_gender: str,
         companion_name: str, companion_gender: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child",
                             traits=["little", trait, "real-ist"]))
    comp = world.add(Entity(id=companion_name, kind="character", type=companion_gender,
                            role="companion", traits=["gentle"]))
    fan = world.add(Entity(id="fan", type="fan", label="old fan", whirs=True))
    bowl = world.add(Entity(id="bowl", type="food", label=food_label, edible=True))
    bowl.meters["full"] = 1
    child.memes["curiosity"] += 1
    comp.memes["calm"] += 1

    world.say(f"{child.id} stood in the old {setting.place} and listened.")
    world.say(f"The air was quiet except for a thin {sound.label} from the corner.")
    world.say(whisper_line(child, f"Did you hear that?"))
    world.say(f'{comp.id} nodded. "{sound.clue}," {comp.id} said.')

    world.para()
    child.memes["fear"] += 1
    child.memes["realist"] += 1
    world.say(f"{child.id} was a real-ist, so {child.pronoun()} did not want a pretend answer.")
    world.say(f'{child.id} crept closer and said, "If it is a ghost, I want to see where it starts."')
    if food_label == "broth with gristle":
        world.say(f"On the table sat a warm bowl of {food_label}; the gristle made a tiny pale curl.")
    else:
        world.say(f"On the table sat {food_label}, waiting beside the lamp.")
    world.say(f"The sound kept going: {sound.label}, {sound.label}, {sound.label}.")
    propagate(world, narrate=False)

    world.para()
    world.say(f'{child.id} pointed. "That whir is the fan, not a ghost."')
    world.say(f'{comp.id} blinked, then laughed softly. "{sound.clue} was real after all."')
    child.memes["fear"] = 0
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    world.say(f"{child.id} grinned, because being a real-ist meant liking true things, even spooky ones.")
    world.say(f"The old fan kept its steady whir, and the {food_label} stayed right where it was.")

    world.facts.update(child=child, companion=comp, setting=setting, sound=sound, food=food_label)
    return world


SETTINGS = {
    "kitchen": Setting(place="kitchen", rooms={"table", "corner"}),
    "attic": Setting(place="attic", rooms={"beam", "box"}),
    "hall": Setting(place="hallway", rooms={"door", "rug"}),
}

SOUNDS = {
    "whir": Sound(id="whir", label="whir", clue="Something is turning", source="fan", tags={"whir", "fan"}),
    "ghost_rattle": Sound(id="ghost_rattle", label="rattle", clue="Something is rattling", source="loose window", tags={"ghost", "window"}),
}

FOODS = {
    "broth": "broth with gristle",
    "pie": "apple pie",
    "toast": "buttered toast",
}

KID_NAMES = ["Nina", "Milo", "June", "Owen", "Ada", "Theo", "Mina", "Eli"]
GENDERS = {"girl": "girl", "boy": "boy"}
TRAITS = ["careful", "curious", "brave", "plain-spoken"]


@dataclass
class StoryParamsResolved:
    setting: str
    sound: str
    food: str
    child: str
    child_gender: str
    companion: str
    companion_gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost-story for a small child where {f["child"].id} hears a {f["sound"].label} in the {f["setting"].place}.',
        f'Tell a dialogue-heavy story where a real-ist child proves a spooky noise is just a fan and not a ghost.',
        f'Write a short child-facing story that includes "{f["sound"].label}" and "{f["food"]}" and ends with a calm explanation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    comp = f["companion"]
    sound = f["sound"]
    setting = f["setting"]
    food = f["food"]
    return [
        QAItem(
            question=f"What did {child.id} hear in the {setting.place}?",
            answer=f"{child.id} heard a {sound.label} in the {setting.place}, and it sounded spooky at first. Then they found out it came from the fan.",
        ),
        QAItem(
            question=f"Why did {child.id} say they were a real-ist?",
            answer=f"{child.id} wanted a true answer, not just a pretend one. Being a real-ist meant looking closely and finding the real source of the sound.",
        ),
        QAItem(
            question=f"What was on the table while the sound kept going?",
            answer=f"There was a bowl of {food} on the table. The little bit of gristle helped make the scene feel real and ordinary, even in a spooky room.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = []
    if "gristle" in f["food"]:
        out.append(QAItem(
            question="What is gristle?",
            answer="Gristle is a tough, chewy little bit in meat or broth. Some people eat around it because it does not feel soft.",
        ))
    out.append(QAItem(
        question="What does a fan do?",
        answer="A fan moves air around and can make a steady whir. It can sound spooky in a quiet room, but it is just a machine.",
    ))
    out.append(QAItem(
        question="What does real mean when someone says they are a real-ist?",
        answer="A real-ist is someone who wants to know what is actually there. They look for the real reason instead of guessing wildly.",
    ))
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
        if e.whirs:
            bits.append("whirs=True")
        if e.edible:
            bits.append("edible=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for snd in SOUNDS.values():
        lines.append(asp.fact("sound", snd.id))
        if sound_at_risk(snd, SETTINGS["kitchen"]):
            lines.append(asp.fact("spooky", snd.id))
    for k, v in FOODS.items():
        lines.append(asp.fact("food", k))
        if "gristle" in v:
            lines.append(asp.fact("has_gristle", k))
    return "\n".join(lines)


ASP_RULES = r"""
spooky_story(S, N, F) :- setting(S), sound(N), food(F), spooky(N).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show spooky_story/3."))
    return sorted(set(asp.atoms(model, "spooky_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print(" only in clingo:", sorted(a - p))
    print(" only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: a real-ist child hears a spooky whir and finds the real cause.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, n, f) for s in SETTINGS for n in SOUNDS for f in FOODS if sound_at_risk(SOUNDS[n], SETTINGS[s])]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.sound is None or c[1] == args.sound)
              and (args.food is None or c[2] == args.food)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, sound, food = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or ("boy" if child_gender == "girl" else "girl")
    child_pool = KID_NAMES[:]
    companion_pool = [n for n in KID_NAMES if n != child_pool[0]]
    child = args.child or rng.choice(child_pool)
    companion = args.companion or rng.choice([n for n in companion_pool if n != child])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, sound, food, child, child_gender, companion, companion_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SOUNDS[params.sound], FOODS[params.food],
                 params.child, params.child_gender, params.companion, params.companion_gender, params.trait)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_program("#show spooky_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} spooky combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(s, n, f, "Nina", "girl", "Milo", "boy", "curious")) for s, n, f in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


CURATED = [
    ("kitchen", "whir", "broth"),
    ("attic", "ghost_rattle", "pie"),
    ("hall", "whir", "toast"),
]


if __name__ == "__main__":
    main()
