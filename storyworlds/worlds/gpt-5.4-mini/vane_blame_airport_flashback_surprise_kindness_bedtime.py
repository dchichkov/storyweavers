#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/vane_blame_airport_flashback_surprise_kindness_bedtime.py
========================================================================================

A small standalone storyworld for an airport bedtime tale with a gentle
surprise, a flashback, and a kindness turn. The core seed image is a child at an
airport, a spinning vane, a moment of blame, and a soft ending where someone
helps instead of scolding.

The world model keeps the story grounded in state:
- a child gets tired and worried at the airport
- a loose information vane / spinner causes confusion
- blame threatens the mood
- a flashback explains why the child feels scared
- a surprise gift or plan changes the moment
- kindness resolves the tension and leads to sleepiness and calm

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and inline ASP twin
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
SLEEPY_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    spins: bool = False
    can_confuse: bool = False
    calm: bool = False

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
    id: str
    place: str
    mood: str
    waiting_spot: str


@dataclass
class Spinner:
    id: str
    label: str
    phrase: str
    sound: str
    flashback_trigger: bool = False
    spins: bool = True
    can_confuse: bool = True


@dataclass
class Event:
    id: str
    kind: str
    label: str
    effect: str
    fix: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_blame(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["worry"] >= THRESHOLD and child.memes["blamed"] >= THRESHOLD:
        sig = ("blame",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["sad"] += 1
        out.append("__blame__")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.meters["flashback"] >= THRESHOLD and ("flashback",) not in world.fired:
        world.fired.add(("flashback",))
        child.memes["worry"] += 1
        out.append("__flashback__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if not child or not helper:
        return out
    if helper.meters["kindness"] >= THRESHOLD and ("kindness",) not in world.fired:
        world.fired.add(("kindness",))
        child.memes["calm"] += 1
        child.memes["safe"] += 1
        out.append("__kindness__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("blame", "social", _r_blame),
    Rule("flashback", "memory", _r_flashback),
    Rule("kindness", "social", _r_kindness),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable_combo(setting: Setting, spinner: Spinner, event: Event) -> bool:
    return setting.id == "airport" and spinner.can_confuse and spinner.spins and event.kind in {"lost", "delay"}


def choose_sleep_spot(setting: Setting) -> str:
    return setting.waiting_spot


def _setup(world: World, child: Entity, helper: Entity, setting: Setting, spinner: Spinner) -> None:
    child.memes["tired"] += 1
    helper.memes["gentle"] += 1
    world.say(
        f"The airport was bright and busy, but {child.id} and {helper.id} had found "
        f"a quiet corner near {choose_sleep_spot(setting)}."
    )
    world.say(
        f"{child.id} listened to the soft rolling bags and watched the small {spinner.label} turn."
    )


def _tempt(world: World, child: Entity, spinner: Spinner, event: Event) -> None:
    child.memes["curious"] += 1
    world.say(
        f"{spinner.sound} went the little {spinner.label}. {child.id} leaned closer and wondered "
        f"why it kept pointing the same way."
    )
    world.say(
        f"That made {child.id} think of {event.effect}, and the thought felt bigger than the room."
    )


def _flashback(world: World, child: Entity, event: Event) -> None:
    child.meters["flashback"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a flashback slipped in: once before, {child.id} had {event.effect} in a crowded place, "
        f"and nobody had explained it kindly."
    )
    world.say(
        f"The memory made {child.id} hide close to {child.pronoun('possessive')} helper."
    )


def _blame(world: World, child: Entity, helper: Entity) -> None:
    child.memes["blamed"] += 1
    world.say(
        f"A sharp voice nearby tried to place blame, but {helper.id} put a warm hand on {child.id}'s shoulder."
    )
    world.say(
        f'"You did not do anything wrong," {helper.id} said softly. "Let us breathe together."'
    )


def _surprise(world: World, helper: Entity, child: Entity, event: Event) -> None:
    helper.meters["kindness"] += 1
    world.say(
        f"Then came a surprise: {helper.id} reached into a bag and found {event.fix}."
    )
    world.say(
        f"It was not loud or shiny, just exactly what {child.id} needed."
    )
    propagate(world, narrate=False)


def _kindness(world: World, helper: Entity, child: Entity, event: Event) -> None:
    child.memes["calm"] += 1
    child.memes["joy"] += 1
    child.memes["sleepy"] += 1
    world.say(
        f"{helper.id} wrapped {child.id} in a soft blanket and told a tiny story about a brave little vane that kept turning even when the wind was confused."
    )
    world.say(
        f"{child.id} smiled, because kindness felt better than blame."
    )


def _ending(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"At last, {child.id} rested against {helper.id} in the quiet chair by {setting.waiting_spot}, "
        f"and the airport lights looked like sleepy stars."
    )
    world.say(
        f"The little vane kept spinning gently, but now it only meant it was time to close {child.id}'s eyes."
    )


def tell(setting: Setting, spinner: Spinner, event: Event, child_name: str = "Mina",
         child_gender: str = "girl", helper_name: str = "Aunt June",
         helper_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    child.memes["worry"] = 0.0
    child.memes["joy"] = 1.0
    helper.meters["kindness"] = 0.0
    world.add(Entity(id="vane", type="thing", label="vane", spins=True, can_confuse=True))
    world.add(Entity(id="chair", type="thing", label=setting.waiting_spot))
    _setup(world, child, helper, setting, spinner)
    world.para()
    _tempt(world, child, spinner, event)
    _flashback(world, child, event)
    _blame(world, child, helper)
    world.para()
    _surprise(world, helper, child, event)
    _kindness(world, helper, child, event)
    world.para()
    _ending(world, child, helper, setting)
    world.facts.update(
        child=child, helper=helper, setting=setting, spinner=spinner, event=event,
        outcome="kind",
        flashback=True,
        surprise=True,
    )
    return world


SETTINGS = {
    "airport": Setting("airport", "the airport", "bright and busy", "window seat"),
}

SPINNERS = {
    "vane": Spinner("vane", "vane", "a tiny vane on a toy plane", "Whirr!", flashback_trigger=True),
    "sign": Spinner("sign", "spinner sign", "a round spinner sign near the gate", "Tick-tick!", flashback_trigger=False),
}

EVENTS = {
    "blame": Event("blame", "lost", "lost snack", "a snack went missing", "a banana and a sticker", tags={"blame"}),
    "delay": Event("delay", "delay", "waited too long", "the plane was delayed", "a warm cup of cocoa", tags={"delay"}),
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Lena", "Zoe", "Ella"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Finn", "Noah", "Max"]


@dataclass
class StoryParams:
    setting: str
    spinner: str
    event: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [("airport", sid, eid) for sid in SPINNERS for eid in EVENTS if reasonable_combo(SETTINGS["airport"], SPINNERS[sid], EVENTS[eid])]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Airport bedtime storyworld with vane, blame, flashback, surprise, kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spinner", choices=SPINNERS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man", "girl", "boy"])
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
    if args.spinner and args.event:
        if not reasonable_combo(SETTINGS["airport"], SPINNERS[args.spinner], EVENTS[args.event]):
            raise StoryError("(No story: this airport combo does not support the needed confusion-to-kindness turn.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.spinner is None or c[1] == args.spinner)
              and (args.event is None or c[2] == args.event)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, spinner, event = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or ("Aunt June" if helper_gender == "woman" else "Uncle Ben")
    return StoryParams(setting, spinner, event, child, child_gender, helper, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f'Write a bedtime-style story for a young child set at an airport, and include the words "vane" and "blame".',
        f"Tell a gentle airport story where {child.id} feels worried, remembers a flashback, and then is comforted with kindness.",
        f"Write a soft story with a surprise at the airport, a small mistake, and a calm ending where nobody is blamed harshly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, spinner, event = f["child"], f["helper"], f["spinner"], f["event"]
    return [
        QAItem(
            question=f"Why did {child.id} feel upset at the airport?",
            answer=f"{child.id} felt upset because the little {spinner.label} and the crowded airport made the old memory come back. The blame nearby made the feeling heavier, so {child.id} needed comfort."
        ),
        QAItem(
            question="What changed the mood in the middle of the story?",
            answer=f"A surprise changed the mood when {helper.id} found {event.fix} and offered it with kindness. That helped {child.id} stop worrying and feel safe again."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {child.id} resting calmly beside {helper.id} at {f['setting'].waiting_spot}. The spinning vane was no longer scary; it had become part of a sleepy, peaceful airport night."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a vane?", "A vane is a small piece that turns when air moves. It can help show direction or decorate something that spins."),
        QAItem("What does blame mean?", "Blame is when someone says another person did something wrong. Kind words are usually better when someone is already upset."),
        QAItem("What is a flashback?", "A flashback is when an old memory comes back very clearly. It can make a person feel as if something from before is happening again."),
        QAItem("What is kindness?", "Kindness is helping, speaking gently, and making someone feel safe. It can turn a hard moment into a softer one."),
        QAItem("What is a surprise?", "A surprise is something you do not expect. A good surprise can make a scary moment feel lighter."),
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.spins:
            bits.append("spins=True")
        if e.can_confuse:
            bits.append("can_confuse=True")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("airport", "vane", "blame", "Mina", "girl", "Aunt June", "woman"),
    StoryParams("airport", "sign", "delay", "Owen", "boy", "Uncle Ben", "man"),
]


def explain_rejection(spinner: Spinner, event: Event) -> str:
    return f"(No story: the airport tale needs a spinner that can stir a flashback and an event that leaves room for kindness; {spinner.label} with {event.label} does not fit.)"


ASP_RULES = r"""
uses_airport(S) :- setting(S), airport(S).
can_story(Spin, Ev) :- spinner(Spin), event(Ev), airport_ok(Spin), airport_event(Ev).
airport_ok(Spin) :- spinner(Spin), confuses(Spin).
airport_event(Ev) :- event(Ev), kind(Ev, lost).
story_kindness :- flashback, blame, surprise, kindness.
outcome(kind) :- story_kindness.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("airport", sid))
    for sid, s in SPINNERS.items():
        lines.append(asp.fact("spinner", sid))
        if s.can_confuse:
            lines.append(asp.fact("confuses", sid))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("kind", eid, e.kind))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show can_story/2."))
    return sorted(set(asp.atoms(model, "can_story")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set((s, sp, e) for s, sp, e in valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: normal generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SPINNERS[params.spinner], EVENTS[params.event],
                 params.child, params.child_gender, params.helper, params.helper_gender)
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
        print(asp_program("", "#show can_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for item in asp_valid_combos():
            print(" ", item)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
