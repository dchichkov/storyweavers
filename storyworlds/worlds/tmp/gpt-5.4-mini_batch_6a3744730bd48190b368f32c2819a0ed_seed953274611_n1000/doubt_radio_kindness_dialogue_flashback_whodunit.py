#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/doubt_radio_kindness_dialogue_flashback_whodunit.py
===================================================================================

A standalone storyworld for a small whodunit-style mystery about doubt, a radio,
kindness, dialogue, and a flashback that reveals what really happened.

Premise
-------
A child hears a strange crackle on the radio, suspects someone in the room, and
starts to doubt everyone. The mystery resolves when a kind choice and a short
flashback reveal that the radio was altered for a helpful reason, not a mean one.

This script follows the Storyweavers contract:
- typed world entities with meters and memes
- a simulated causal model
- explicit invalid options raising StoryError
- a Python reasonableness gate with an inline ASP twin
- grounded prompts, story QA, and world-knowledge QA
- CLI flags: -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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

DUBIOUS_THRESHOLD = 1.0
TRUST_THRESHOLD = 1.0
KINDNESS_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Location:
    id: str
    place: str
    mood: str
    quiet: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class RadioSetup:
    id: str
    label: str
    phrase: str
    glitch: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SuspectAction:
    id: str
    label: str
    sense: int
    cause: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    setup: str
    action: str
    helper: str
    narrator: str
    narrator_gender: str
    adult: str
    adult_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.location)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_doubt_spreads(world: World) -> list[str]:
    out = []
    radio = world.get("radio")
    if radio.meters["strange"] < DUBIOUS_THRESHOLD:
        return out
    for e in world.characters():
        sig = ("doubt", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["doubt"] += 1
        out.append(f"{e.id} could not stop wondering what had happened.")
    return out


def _r_kindness_cools(world: World) -> list[str]:
    out = []
    helper = world.get("helper")
    for e in world.characters():
        if e.id == helper.id:
            continue
        if helper.memes["kindness"] < KINDNESS_THRESHOLD:
            continue
        sig = ("kindness", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["trust"] += 1
        out.append(f"{helper.id} stayed calm and made the room feel safer.")
    return out


CAUSAL_RULES = [Rule("doubt_spreads", _r_doubt_spreads), Rule("kindness_cools", _r_kindness_cools)]


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


def reasonableness_gate(setup: RadioSetup, action: SuspectAction) -> bool:
    return setup.id in RADIO_SETUPS and action.id in ACTIONS


def mystery_risk(setup: RadioSetup, action: SuspectAction) -> bool:
    return setup.id == "old_radio" and action.sense >= 2


def sensible_actions() -> list[SuspectAction]:
    return [a for a in ACTIONS.values() if a.sense >= 2]


def predict_mystery(world: World) -> dict:
    sim = world.copy()
    _flashback(sim, narrate=False)
    return {
        "revealed": bool(sim.facts.get("reveal")),
        "trust": sim.get("narrator").memes["trust"],
    }


def _flashback(world: World, narrate: bool = True) -> None:
    narrator = world.get("narrator")
    helper = world.get("helper")
    narrator.memes["memory"] += 1
    world.facts["reveal"] = True
    if narrate:
        world.say(
            f"{narrator.id} remembered something from before: {helper.id} had "
            f"worked on the radio for a kind reason."
        )
        world.say(
            f"In that flashback, {helper.id} had tucked a note beside the set so "
            f"nobody would worry."
        )


def introduce(world: World, narrator: Entity, helper: Entity, setup: RadioSetup) -> None:
    narrator.memes["curiosity"] += 1
    world.say(
        f"At {world.location.place}, a little radio on the shelf gave off {setup.glitch}."
    )
    world.say(
        f"{narrator.id} frowned. '{setup.phrase} Did someone touch it?'"
    )


def observe_clue(world: World, narrator: Entity, setup: RadioSetup) -> None:
    world.say(
        f"On the back of the radio, {narrator.id} found {setup.clue}."
    )
    narrator.memes["doubt"] += 1
    world.say(
        f"That made {narrator.id} doubt the first idea that popped into {narrator.pronoun('possessive')} head."
    )


def question_people(world: World, narrator: Entity, helper: Entity, adult: Entity) -> None:
    world.say(
        f"'{helper.id}, did you move it?' {narrator.id} asked."
    )
    world.say(
        f"'{Nope}'".replace("Nope", "No, I only helped with the batteries, not the mystery"),)
    world.say(
        f"'{adult.id}, do you know?' {narrator.id} asked."
    )
    world.say(
        f"'{adult.id}' shook {adult.pronoun('possessive')} head and said, 'Let's look carefully first.'"
    )


def gentle_help(world: World, helper: Entity, narrator: Entity) -> None:
    helper.memes["kindness"] += 2
    world.say(
        f"{helper.id} did not laugh at the doubt. Instead, {helper.id} brought a small lamp and sat close."
    )
    world.say(
        f"'We can solve it together,' {helper.id} said softly."
    )
    narrator.memes["trust"] += 1


def flashback(world: World, narrator: Entity, helper: Entity) -> None:
    _flashback(world, narrate=True)
    world.say(
        f"Now {narrator.id} understood why the radio had been opened: {helper.id} had been trying to fix a crackly speaker so the announcements could be heard."
    )


def reveal(world: World, narrator: Entity, helper: Entity, adult: Entity, setup: RadioSetup) -> None:
    world.say(
        f"{narrator.id} looked at {helper.id} again and said, 'You were helping, weren't you?'"
    )
    world.say(
        f"{helper.id} nodded. '{setup.reveal}'"
    )
    world.say(
        f"{adult.id} smiled and said, 'Kindness can sound like a mystery when you do not know the whole story.'"
    )


def ending(world: World, narrator: Entity, helper: Entity, adult: Entity) -> None:
    narrator.memes["trust"] += 1
    world.say(
        f"After that, {narrator.id} felt less doubt and more trust."
    )
    world.say(
        f"The radio still sat on the shelf, but now it sounded warm and useful, and the room felt brighter because everyone had been kind."
    )


RADIO_SETUPS = {
    "old_radio": RadioSetup(
        id="old_radio",
        label="the old radio",
        phrase="The radio is crackling again.",
        glitch="a scratchy little crackle",
        clue="a folded note taped under the battery cover",
        tags={"radio", "mystery"},
    ),
    "kitchen_radio": RadioSetup(
        id="kitchen_radio",
        label="the kitchen radio",
        phrase="Who turned the dial?",
        glitch="a burst of static",
        clue="fresh fingerprints beside the knob",
        tags={"radio", "mystery"},
    ),
}

ACTIONS = {
    "battery_fix": SuspectAction(
        id="battery_fix",
        label="battery fix",
        sense=3,
        cause="the batteries were loose",
        reveal="I opened it to stop the crackle, and I left a note so nobody would worry",
        tags={"kindness", "radio"},
    ),
    "weather_note": SuspectAction(
        id="weather_note",
        label="weather note",
        sense=2,
        cause="the storm made the signal waver",
        reveal="I was checking the station because the storm made the signal weak",
        tags={"radio"},
    ),
    "mischief": SuspectAction(
        id="mischief",
        label="mischief",
        sense=0,
        cause="someone wanted to cause trouble",
        reveal="",
        tags={"doubt"},
    ),
}

LOCATIONS = {
    "library": Location(id="library", place="the little library", mood="quiet", quiet=True, tags={"quiet", "radio"}),
    "kitchen": Location(id="kitchen", place="the kitchen", mood="busy", quiet=False, tags={"radio", "home"}),
    "clubroom": Location(id="clubroom", place="the club room", mood="cozy", quiet=False, tags={"radio", "kindness"}),
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Lina", "Ada", "Tess"]
BOY_NAMES = ["Noel", "Owen", "Finn", "Ezra", "Milo", "Levi"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in LOCATIONS:
        for setup in RADIO_SETUPS:
            if mystery_risk(RADIO_SETUPS[setup], ACTIONS["battery_fix"]):
                out.append((place, setup))
    return out


def explain_rejection(setup: RadioSetup, action: SuspectAction) -> str:
    if action.sense < 2:
        return "(No story: that suspect action is too mean or too weak for a gentle whodunit."
    return "(No story: this setup does not produce a good radio mystery.)"


def explain_action_rejection(aid: str) -> str:
    action = ACTIONS[aid]
    allowed = " / ".join(sorted(a.id for a in sensible_actions()))
    return (
        f"(Refusing action '{aid}': it is not reasonable for a child-friendly mystery. "
        f"Try one of: {allowed}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld: doubt, radio, kindness, dialogue, flashback.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--setup", choices=RADIO_SETUPS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and ACTIONS[args.action].sense < 2:
        raise StoryError(explain_action_rejection(args.action))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.setup is None or c[1] == args.setup)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, setup = rng.choice(sorted(combos))
    action = args.action or rng.choice(sorted(a.id for a in sensible_actions()))
    narrator_gender = rng.choice(["girl", "boy"])
    narrator = rng.choice(GIRL_NAMES if narrator_gender == "girl" else BOY_NAMES)
    adult_gender = rng.choice(["mother", "father"])
    adult = "Mom" if adult_gender == "mother" else "Dad"
    helper = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != narrator])
    return StoryParams(
        place=place,
        setup=setup,
        action=action,
        helper=helper,
        narrator=narrator,
        narrator_gender=narrator_gender,
        adult=adult,
        adult_gender=adult_gender,
        seed=None,
    )


def tell(params: StoryParams) -> World:
    location = LOCATIONS[params.place]
    setup = RADIO_SETUPS[params.setup]
    action = ACTIONS[params.action]
    world = World(location)
    narrator = world.add(Entity(id="narrator", kind="character", type=params.narrator_gender, label=params.narrator, role="detective"))
    helper = world.add(Entity(id="helper", kind="character", type="girl", label=params.helper, role="kind helper"))
    adult = world.add(Entity(id="adult", kind="character", type=params.adult_gender, label=params.adult, role="adult"))
    radio = world.add(Entity(id="radio", kind="thing", type="radio", label=setup.label, tags={"radio"}))
    clue = world.add(Entity(id="clue", kind="thing", type="note", label=setup.clue))
    helper.memes["kindness"] = 2
    world.facts["action"] = action
    world.facts["setup"] = setup
    world.facts["radio"] = radio
    world.facts["narrator"] = narrator
    world.facts["helper"] = helper
    world.facts["adult"] = adult

    introduce(world, narrator, helper, setup)
    world.para()
    observe_clue(world, narrator, setup)
    question_people(world, narrator, helper, adult)
    gentle_help(world, helper, narrator)
    world.para()
    flashback(world, narrator, helper)
    reveal(world, narrator, helper, adult, setup)
    ending(world, narrator, helper, adult)
    radio.meters["strange"] = 0.0
    world.facts["reveal"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setup = f["setup"]
    return [
        f'Write a child-friendly whodunit story that includes the words "doubt" and "radio".',
        f"Tell a mystery where {f['narrator'].label} feels doubt about {setup.label}, but a kind helper and a flashback reveal the truth.",
        f"Write a short story with dialogue and a flashback in which the radio is not a bad sign after all.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    narrator = f["narrator"]
    helper = f["helper"]
    adult = f["adult"]
    setup = f["setup"]
    action = f["action"]
    return [
        ("What made the narrator feel doubt?",
         f"The radio made a scratchy sound, so {narrator.label} thought something strange had happened. The clue under the battery cover made the doubt stronger at first."),
        ("Who helped solve the mystery?",
         f"{helper.label} helped by staying calm, bringing a lamp, and talking kindly. That made it easier for {narrator.label} to look again instead of guessing too fast."),
        ("What did the flashback show?",
         f"It showed that {helper.label} had opened the radio for a helpful reason. {action.reveal or 'The real reason was kind, not mean.'}"),
        ("How did the story end?",
         f"The radio was still there, but the mystery was understood and the room felt safer. {narrator.label} ended with less doubt and more trust."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a radio?",
         "A radio is a machine that plays sound from far away stations. People can listen to music, news, or voices through it."),
        ("What does doubt mean?",
         "Doubt means you are not sure yet and you want to think carefully before deciding. It can help you ask good questions."),
        ("What is a flashback in a story?",
         "A flashback is a scene that shows something from earlier. Writers use it to explain a mystery or give more clues."),
        ("Why is kindness important in a mystery story?",
         "Kindness keeps people calm so they can think clearly. When people are kind, they can solve problems without making the situation worse."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible_action(A) :- action(A), sense(A,S), S >= 2.
valid(P, S) :- place(P), setup(S), sensible_action(battery_fix), risk(S).
risk(old_radio) :- setup(old_radio).
risk(kitchen_radio) :- setup(kitchen_radio).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in LOCATIONS:
        lines.append(asp.fact("place", p))
    for sid, s in RADIO_SETUPS.items():
        lines.append(asp.fact("setup", sid))
        if s.id == "old_radio":
            lines.append(asp.fact("risk", sid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_actions() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible_action/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible_action"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    if set(asp_sensible_actions()) != {a.id for a in sensible_actions()}:
        rc = 1
        print("MISMATCH in sensible actions")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, setup=None, action=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    else:
        print("OK: smoke test passed.")
    return rc


def valid_combos() -> list[tuple[str, str]]:
    return [(p, s) for p in LOCATIONS for s in RADIO_SETUPS if mystery_risk(RADIO_SETUPS[s], ACTIONS["battery_fix"])]


def sensible_actions() -> list[SuspectAction]:
    return [a for a in ACTIONS.values() if a.sense >= 2]


def generate(params: StoryParams) -> StorySample:
    if params.place not in LOCATIONS or params.setup not in RADIO_SETUPS or params.action not in ACTIONS:
        raise StoryError("(Invalid parameters.)")
    if ACTIONS[params.action].sense < 2:
        raise StoryError(explain_action_rejection(params.action))
    world = tell(params)
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


CURATED = [
    StoryParams(place="library", setup="old_radio", action="battery_fix", helper="Ivy", narrator="Mina", narrator_gender="girl", adult="Mom", adult_gender="mother"),
    StoryParams(place="kitchen", setup="kitchen_radio", action="weather_note", helper="Noel", narrator="Finn", narrator_gender="boy", adult="Dad", adult_gender="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2.\n#show sensible_action/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible actions:", ", ".join(asp_sensible_actions()))
        for p, s in asp_valid_combos():
            print(f"{p} {s}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
