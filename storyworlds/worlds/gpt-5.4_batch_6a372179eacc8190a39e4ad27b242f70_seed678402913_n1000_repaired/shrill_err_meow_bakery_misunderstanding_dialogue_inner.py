#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shrill_err_meow_bakery_misunderstanding_dialogue_inner.py

A standalone storyworld about a child in a bakery who hears a shrill sound,
misunderstands it as a cat's cry, and goes on a small indoor adventure to help.
The world model tracks noise, worry, clues, and repair. The turn comes from a
misunderstanding; the resolution comes from dialogue, careful checking, and a
kind explanation.

Run it
------
python storyworlds/worlds/gpt-5.4/shrill_err_meow_bakery_misunderstanding_dialogue_inner.py
python storyworlds/worlds/gpt-5.4/shrill_err_meow_bakery_misunderstanding_dialogue_inner.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/shrill_err_meow_bakery_misunderstanding_dialogue_inner.py --all --qa
python storyworlds/worlds/gpt-5.4/shrill_err_meow_bakery_misunderstanding_dialogue_inner.py --trace
python storyworlds/worlds/gpt-5.4/shrill_err_meow_bakery_misunderstanding_dialogue_inner.py --json
python storyworlds/worlds/gpt-5.4/shrill_err_meow_bakery_misunderstanding_dialogue_inner.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "baker_woman"}
        male = {"boy", "father", "man", "baker_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "baker_woman": "baker",
            "baker_man": "baker",
        }.get(self.type, self.type)


@dataclass
class SoundCue:
    id: str
    label: str
    source: str
    shrill_text: str
    mistaken_as: str
    clue_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    obstacle: str
    clue_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperAction:
    id: str
    sense: int
    text: str
    success_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["heard_shrill"] >= THRESHOLD and hero.memes["worry"] < THRESHOLD:
        sig = ("worry", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_search(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["worry"] >= THRESHOLD and hero.memes["brave"] >= THRESHOLD:
        sig = ("search", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["searching"] += 1
            out.append("__search__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["truth_known"] >= THRESHOLD:
        sig = ("relief", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["relief"] += 1
            hero.memes["worry"] = 0.0
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="worry", tag="emotion", apply=_r_worry),
    Rule(name="search", tag="action", apply=_r_search),
    Rule(name="relief", tag="emotion", apply=_r_relief),
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
    return produced


def valid_combo(sound: SoundCue, place: HidingPlace, action: HelperAction) -> bool:
    return sound.source in place.tags and action.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sound_id, sound in SOUNDS.items():
        for place_id, place in PLACES.items():
            for action_id, action in ACTIONS.items():
                if valid_combo(sound, place, action):
                    combos.append((sound_id, place_id, action_id))
    return combos


def sensible_actions() -> list[str]:
    return sorted(aid for aid, action in ACTIONS.items() if action.sense >= SENSE_MIN)


def predict_misunderstanding(sound: SoundCue, place: HidingPlace) -> dict:
    hears_cat = sound.mistaken_as == "cat" and sound.source in place.tags
    return {
        "hears_cat": hears_cat,
        "worry": 1 if hears_cat else 0,
    }


def introduce(world: World, hero: Entity, baker: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} stepped into the bakery with {hero.pronoun('possessive')} "
        f"{baker.label_word}, and the room felt like the start of a tiny adventure. "
        f"Warm bread breathed from the shelves, and {item.phrase} waited behind the glass."
    )


def goal(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} had come for {item.label}, and {hero.pronoun('possessive')} eyes "
        f"followed the shining rows as if treasure might be hiding among them."
    )


def hear_sound(world: World, hero: Entity, sound: SoundCue) -> None:
    hero.meters["heard_shrill"] += 1
    world.facts["heard_word"] = "shrill"
    propagate(world, narrate=False)
    world.say(
        f"Then a {sound.shrill_text} sliced through the bakery. "
        f'"{sound.label}!" {hero.id} whispered. In the next breath {hero.pronoun()} thought, '
        f'"Did something just go meow?"'
    )


def inner_monologue(world: World, hero: Entity, place: HidingPlace) -> None:
    hero.memes["brave"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.pronoun().capitalize()} pressed one hand to {hero.pronoun("possessive")} chest. '
        f'"Err... if a little cat is stuck {place.phrase}, I should help," '
        f'{hero.pronoun()} thought.'
    )


def ask(world: World, hero: Entity, baker: Entity) -> None:
    hero.memes["trust"] += 1
    world.say(
        f'"Did you hear that meow?" {hero.id} asked. "{hero.pronoun("subject").capitalize()} sounds scared." '
        f'The {baker.label_word} looked up at once.'
    )


def search(world: World, hero: Entity, place: HidingPlace) -> None:
    hero.meters["searched"] += 1
    world.say(
        f"{hero.id} hurried toward {place.phrase}, feeling brave and shaky at the same time. "
        f"{place.obstacle.capitalize()} made the corner feel secret, like the mouth of a cave."
    )


def find_clue(world: World, hero: Entity, sound: SoundCue, place: HidingPlace) -> None:
    hero.meters["clue_seen"] += 1
    world.say(
        f"But when {hero.pronoun()} peered in, {place.clue_text} "
        f"Then {sound.clue_text}"
    )


def explain_truth(world: World, baker: Entity, hero: Entity, sound: SoundCue) -> None:
    hero.meters["truth_known"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"There is no cat," the {baker.label_word} said gently. "That sound came from '
        f'{sound.source}. It can be sharp and shrill when steam slips out."'
    )
    world.say(
        f'{hero.id} blinked. "{hero.pronoun("subject").capitalize()} thought it said meow."'
    )


def repair(world: World, baker: Entity, action: HelperAction) -> None:
    world.get("machine").meters["fixed"] += 1
    world.say(
        f"The {baker.label_word} {action.text}. {action.success_text}"
    )


def resolve(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f'{hero.id} let out a tiny laugh. The bakery did not hide a lost cat after all; '
        f'it hid a simple mistake and the answer to it. Soon {hero.pronoun()} was holding '
        f'{item.phrase}, and the sweet smell felt friendly instead of mysterious.'
    )


def ending_image(world: World, hero: Entity, baker: Entity, item: Entity) -> None:
    world.say(
        f'As they stepped back toward the counter, {hero.id} listened again. '
        f'This time the bakery hummed softly, the tray of {item.label} gleamed, '
        f'and {hero.pronoun()} felt proud for asking instead of guessing.'
    )


def tell(
    sound: SoundCue,
    place: HidingPlace,
    action: HelperAction,
    hero_name: str,
    hero_type: str,
    baker_type: str,
    treat: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[trait],
    ))
    baker = world.add(Entity(
        id="baker",
        kind="character",
        type=baker_type,
        label="the baker",
        phrase="the baker",
        role="baker",
    ))
    item = world.add(Entity(
        id="treat",
        type="treat",
        label=TREATS[treat],
        phrase=f"a {TREATS[treat]}",
    ))
    machine = world.add(Entity(
        id="machine",
        type="machine",
        label=sound.source,
        phrase=f"the {sound.source}",
        tags={sound.source},
    ))
    corner = world.add(Entity(
        id="place",
        type="place",
        label=place.label,
        phrase=place.phrase,
        tags=set(place.tags),
    ))
    hero.id = hero_name

    introduce(world, hero, baker, item)
    goal(world, hero, item)

    world.para()
    hear_sound(world, hero, sound)
    inner_monologue(world, hero, place)
    ask(world, hero, baker)

    world.para()
    search(world, hero, place)
    find_clue(world, hero, sound, place)
    explain_truth(world, baker, hero, sound)
    repair(world, baker, action)

    world.para()
    resolve(world, hero, item)
    ending_image(world, hero, baker, item)

    world.facts.update(
        hero=hero,
        baker=baker,
        item=item,
        machine=machine,
        place_cfg=place,
        sound_cfg=sound,
        action_cfg=action,
        misunderstanding=True,
        truth_known=hero.meters["truth_known"] >= THRESHOLD,
        repaired=machine.meters["fixed"] >= THRESHOLD,
    )
    return world


SOUNDS = {
    "kettle": SoundCue(
        id="kettle",
        label="the kettle",
        source="kettle",
        shrill_text="shrill whistle",
        mistaken_as="cat",
        clue_text="a silver kettle by the cocoa stove gave another thin cry.",
        tags={"kettle", "counter_nook"},
    ),
    "mixer": SoundCue(
        id="mixer",
        label="the mixer",
        source="mixer",
        shrill_text="shrill squeak",
        mistaken_as="cat",
        clue_text="the old mixer on the side table squealed once as its belt slipped.",
        tags={"mixer", "flour_shelf"},
    ),
    "oven_vent": SoundCue(
        id="oven_vent",
        label="the oven vent",
        source="oven vent",
        shrill_text="shrill hiss",
        mistaken_as="cat",
        clue_text="a breath of steam sang through the oven vent near the warm wall.",
        tags={"oven vent", "warming_rack"},
    ),
}

PLACES = {
    "counter_nook": HidingPlace(
        id="counter_nook",
        label="counter nook",
        phrase="behind the counter nook",
        obstacle="a hanging apron and a stack of cake boxes",
        clue_text="there were no whiskers, only warm shadows under the shelves. ",
        tags={"kettle", "counter_nook"},
    ),
    "flour_shelf": HidingPlace(
        id="flour_shelf",
        label="flour shelf",
        phrase="beside the tall flour shelf",
        obstacle="big paper sacks and scoops",
        clue_text="nothing furry blinked back; only flour dust floated in one bright strip of light. ",
        tags={"mixer", "flour_shelf"},
    ),
    "warming_rack": HidingPlace(
        id="warming_rack",
        label="warming rack",
        phrase="near the warming rack",
        obstacle="racks of buns and a curtain of sweet steam",
        clue_text="there was no tiny tail at all, only trays and shining pans. ",
        tags={"oven vent", "warming_rack"},
    ),
}

ACTIONS = {
    "lift_lid": HelperAction(
        id="lift_lid",
        sense=3,
        text="lifted the kettle lid with a cloth and turned the flame down",
        success_text="At once the sharp cry faded into a soft little sigh.",
        tags={"kettle", "steam"},
    ),
    "switch_off": HelperAction(
        id="switch_off",
        sense=3,
        text="switched the mixer off and settled its loose guard back into place",
        success_text="The squeak stopped, and the room sounded safe again.",
        tags={"mixer", "machine"},
    ),
    "open_vent": HelperAction(
        id="open_vent",
        sense=2,
        text="opened the vent wider so the steam could escape the right way",
        success_text="The hiss smoothed out and no longer sounded like a frightened cry.",
        tags={"oven vent", "steam"},
    ),
    "tap_machine": HelperAction(
        id="tap_machine",
        sense=1,
        text="gave the machine a random tap",
        success_text="It quieted for a blink, but that was more luck than good sense.",
        tags={"weak"},
    ),
}

TREATS = {
    "bun": "honey bun",
    "roll": "cinnamon roll",
    "cookie": "jam cookie",
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Theo"]
TRAITS = ["curious", "brave", "hopeful", "careful"]
HERO_TYPES = ["girl", "boy"]
BAKER_TYPES = ["baker_woman", "baker_man"]


@dataclass
class StoryParams:
    sound: str
    place: str
    action: str
    treat: str
    hero_name: str
    hero_type: str
    baker_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "kettle": [
        (
            "Why can a kettle make a loud sound?",
            "A kettle can whistle when hot steam pushes through a small opening. That sharp sound can seem very loud indoors.",
        )
    ],
    "mixer": [
        (
            "What is a mixer in a bakery?",
            "A mixer is a machine that stirs dough or batter. When part of it rubs the wrong way, it can squeak or squeal.",
        )
    ],
    "oven vent": [
        (
            "What does an oven vent do?",
            "An oven vent lets hot air and steam out. If steam squeezes through a narrow place, it can hiss sharply.",
        )
    ],
    "steam": [
        (
            "What is steam?",
            "Steam is water that has gotten hot and turned into a misty gas. It can hiss or whistle when it moves through a small gap.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something means one thing, but it really means another. Asking a question can help clear it up.",
        )
    ],
    "bakery": [
        (
            "What is a bakery?",
            "A bakery is a place where people bake bread, buns, cakes, and other treats. It often smells warm and sweet because ovens are working there.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bakery", "misunderstanding", "kettle", "mixer", "oven vent", "steam"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sound = f["sound_cfg"]
    place = f["place_cfg"]
    item = f["item"]
    return [
        'Write an adventure-style story for a 3-to-5-year-old set in a bakery that includes the words "shrill", "err", and "meow".',
        f"Tell a small misunderstanding story where {hero.id} hears a shrill sound near {place.label}, thinks a cat went meow, and learns the truth by asking the baker.",
        f"Write a child-facing bakery adventure with dialogue and inner monologue, ending with {hero.id} feeling proud and safe while holding {item.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    baker = f["baker"]
    sound = f["sound_cfg"]
    place = f["place_cfg"]
    item = f["item"]
    action = f["action_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child in a bakery, and the baker who helped explain a confusing sound.",
        ),
        (
            "What made the adventure begin?",
            f"A shrill sound suddenly cut through the bakery. {hero.id} misunderstood it and thought it might be a cat saying meow.",
        ),
        (
            f"Why did {hero.id} hurry to {place.label}?",
            f"{hero.id} thought a little cat might be stuck there and feel scared. That mistaken idea made the ordinary bakery corner feel like part of an adventure.",
        ),
        (
            "What does the word 'err' do in the story?",
            f"It shows {hero.id} hesitating and thinking out loud. The small 'Err...' moment makes the inner worry feel real before the truth is known.",
        ),
        (
            "What was the sound really coming from?",
            f"It was really coming from the {sound.source}, not from a cat. The baker explained that steam or a machine part could make a sharp sound like that.",
        ),
        (
            "How did the baker fix the problem?",
            f"The baker {action.text}. {action.success_text} That change proved the strange noise had an ordinary cause.",
        ),
        (
            f"How did {hero.id} feel at the end?",
            f"{hero.id} felt relieved and proud. Asking a question turned a scary misunderstanding into a calm answer and a happy bakery moment.",
        ),
        (
            "How did the story end?",
            f"It ended with the bakery sounding soft again while {hero.id} held {item.phrase}. The ending image shows that the mystery is over and the place feels friendly now.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sound = f["sound_cfg"]
    tags = {"bakery", "misunderstanding", sound.source}
    if "steam" in f["action_cfg"].tags:
        tags.add("steam")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        sound="kettle",
        place="counter_nook",
        action="lift_lid",
        treat="bun",
        hero_name="Lily",
        hero_type="girl",
        baker_type="baker_woman",
        trait="curious",
    ),
    StoryParams(
        sound="mixer",
        place="flour_shelf",
        action="switch_off",
        treat="roll",
        hero_name="Ben",
        hero_type="boy",
        baker_type="baker_man",
        trait="brave",
    ),
    StoryParams(
        sound="oven_vent",
        place="warming_rack",
        action="open_vent",
        treat="cookie",
        hero_name="Nora",
        hero_type="girl",
        baker_type="baker_woman",
        trait="careful",
    ),
]


def explain_rejection(sound: SoundCue, place: HidingPlace, action: HelperAction) -> str:
    if action.sense < SENSE_MIN:
        return (
            f"(No story: action '{action.id}' is too weak or random for a careful bakery fix. "
            f"Try one of: {', '.join(sensible_actions())}.)"
        )
    if sound.source not in place.tags:
        return (
            f"(No story: {place.label} is not a plausible place for a sound from the {sound.source}. "
            f"The child needs a believable clue trail for the misunderstanding.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
sound_place_ok(S, P) :- sound_source(S, Src), place_has(P, Src).
sensible_action(A) :- action(A), sense(A, V), sense_min(M), V >= M.
valid(S, P, A) :- sound(S), place(P), action(A), sound_place_ok(S, P), sensible_action(A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("sound_source", sid, sound.source))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for tag in sorted(place.tags):
            if tag in {"kettle", "mixer", "oven vent"}:
                lines.append(asp.fact("place_has", pid, tag))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, action.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_action/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible_action"))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    py_sens = set(sensible_actions())
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible actions match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible actions: clingo={sorted(asp_sens)} python={sorted(py_sens)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "meow" not in sample.story or "shrill" not in sample.story or "Err" not in sample.story:
            raise StoryError("smoke test story missing required narrative elements")
        print("OK: smoke test generate() succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a bakery misunderstanding solved by dialogue and careful checking."
    )
    ap.add_argument("--sound", choices=sorted(SOUNDS))
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--action", choices=sorted(ACTIONS))
    ap.add_argument("--treat", choices=sorted(TREATS))
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--baker-type", choices=BAKER_TYPES)
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
    if args.sound and args.place and args.action:
        sound = SOUNDS[args.sound]
        place = PLACES[args.place]
        action = ACTIONS[args.action]
        if not valid_combo(sound, place, action):
            raise StoryError(explain_rejection(sound, place, action))
    if args.action and ACTIONS[args.action].sense < SENSE_MIN:
        raise StoryError(explain_rejection(SOUNDS[args.sound] if args.sound else next(iter(SOUNDS.values())),
                                          PLACES[args.place] if args.place else next(iter(PLACES.values())),
                                          ACTIONS[args.action]))

    combos = [
        combo for combo in valid_combos()
        if (args.sound is None or combo[0] == args.sound)
        and (args.place is None or combo[1] == args.place)
        and (args.action is None or combo[2] == args.action)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    sound_id, place_id, action_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    baker_type = args.baker_type or rng.choice(BAKER_TYPES)
    treat = args.treat or rng.choice(sorted(TREATS))
    trait = rng.choice(TRAITS)
    if args.name:
        hero_name = args.name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    return StoryParams(
        sound=sound_id,
        place=place_id,
        action=action_id,
        treat=treat,
        hero_name=hero_name,
        hero_type=hero_type,
        baker_type=baker_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.sound not in SOUNDS:
        raise StoryError(f"Unknown sound: {params.sound}")
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.action not in ACTIONS:
        raise StoryError(f"Unknown action: {params.action}")
    if params.treat not in TREATS:
        raise StoryError(f"Unknown treat: {params.treat}")
    sound = SOUNDS[params.sound]
    place = PLACES[params.place]
    action = ACTIONS[params.action]
    if not valid_combo(sound, place, action):
        raise StoryError(explain_rejection(sound, place, action))

    world = tell(
        sound=sound,
        place=place,
        action=action,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        baker_type=params.baker_type,
        treat=params.treat,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible_action/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible actions: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (sound, place, action) combos:\n")
        for sound, place, action in combos:
            print(f"  {sound:10} {place:14} {action}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.hero_name}: {p.sound} at {p.place} ({p.action})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
