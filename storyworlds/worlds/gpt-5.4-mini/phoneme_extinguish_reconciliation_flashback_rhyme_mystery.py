#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/phoneme_extinguish_reconciliation_flashback_rhyme_mystery.py
============================================================================================

A standalone story world sketch for a small mystery about a child, a strange
sound clue, a harmless mistake, and a gentle reconciliation. The world keeps the
focus on two seed words -- phoneme and extinguish -- while adding a child-facing
mystery tone, a brief flashback, and a rhyming ending that helps seal the case.

The domain:
- A child hears a strange phoneme clue in a quiet place.
- Something small gets messy or smoky, but not dangerous.
- A helper calms things down and helps extinguish the worry.
- A flashback explains why the clue matters.
- The two characters reconcile and the story ends with a rhyme.

This file is self-contained and uses only the standard library plus the shared
storyworlds/results.py containers.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    mood: str
    hiding_spot: str
    echo_spot: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Clue:
    id: str
    word: str
    phrase: str
    meaning: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Mishap:
    id: str
    trigger: str
    effect: str
    can_extinguish: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

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
            self.history.append(text)

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
        c.facts = copy.deepcopy(self.facts)
        c.history = list(self.history)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_smoke(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["smoke"] < THRESHOLD:
            continue
        sig = ("smoke", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["mystery"] += 1
        for ch in list(world.entities.values()):
            if ch.kind == "character":
                ch.memes["unease"] += 1
        out.append("__smoke__")
    return out


RULES = [Rule("smoke", _r_smoke)]


def propagate(world: World, narrate: bool = True) -> None:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)


def valid_clues() -> list[str]:
    return [c.id for c in CLUES.values()]


def reasonable_combo(setting: Setting, clue: Clue, mishap: Mishap, fix: Fix) -> bool:
    return clue.id in setting.hiding_spot or clue.id in setting.echo_spot or True


def sense_gate(fix: Fix) -> bool:
    return fix.sense >= SENSE_MIN


def severity(delay: int) -> int:
    return 1 + delay


def contained(fix: Fix, delay: int) -> bool:
    return fix.power >= severity(delay)


def tell_flashback(world: World, child: Entity, helper: Entity, clue: Clue) -> None:
    child.memes["memory"] += 1
    world.say(
        f"Later, {child.id} remembered a flashback: on the first day of school, "
        f"{helper.id} had taught {child.pronoun('object')} how to listen for the "
        f"small parts of a word. That was why the strange phoneme felt important."
    )
    world.say(
        f"The memory fitted the clue like a key."
    )


def open_scene(world: World, child: Entity, helper: Entity, setting: Setting, clue: Clue) -> None:
    world.say(
        f"On a quiet evening, {child.id} and {helper.id} walked through {setting.place}. "
        f"The place looked calm, but {setting.mood} hid in the corners."
    )
    world.say(
        f"{child.id} noticed a scrap of paper tucked near {setting.hiding_spot}, "
        f"and on it was the word {clue.word}."
    )
    world.say(
        f'"That must mean something," {child.id} whispered. '
        f'"A {clue.word} is a small sound piece, and clues like that do not appear by accident."'
    )


def raise_mystery(world: World, child: Entity, helper: Entity, clue: Clue) -> None:
    child.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"{helper.id} leaned closer. " + f'"The word {clue.word} points to a hidden meaning," '
        f"{helper.pronoun()} said. " + f'"Let\'s follow it."'
    )
    world.say(
        f"They searched near {world.setting.echo_spot}, where even tiny sounds seemed to stay behind."
    )


def mishap_event(world: World, child: Entity, mishap: Mishap, delay: int) -> None:
    room = world.get("room")
    room.meters["smoke"] += 1 + delay
    room.meters["mystery"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a little puff of smoke rose from a bent candle stub. It was not a big fire, "
        f"but it was enough to make everyone step back."
    )
    world.say(
        f"The smoky puff looked puzzling, and the clue seemed even stranger."
    )


def warn(world: World, helper: Entity, child: Entity) -> None:
    world.say(
        f'{helper.id} touched {helper.pronoun("possessive")} shoulder and said, '
        f'"We do not need to fear the whole mystery. We just need to extinguish the smoke, '
        f"then look at the clue again."
    )


def reconcile(world: World, child: Entity, helper: Entity, fix: Fix, clue: Clue) -> None:
    child.memes["fear"] = 0.0
    helper.memes["fear"] = 0.0
    child.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.say(
        f'At first {child.id} felt cross, because the smoky puff had spoiled the search. '
        f'But {helper.id} smiled and showed {child.id} a better way.'
    )
    world.say(
        f'"Sorry for snapping," {child.id} said. '
        f'"Sorry for rushing," {helper.id} answered. '
        f'They forgave each other at once, and their worry grew smaller.'
    )


def resolve(world: World, child: Entity, helper: Entity, fix: Fix, clue: Clue, delay: int) -> None:
    if contained(fix, delay):
        world.say(
            f"{helper.id} used {fix.text} and the smoke faded at once."
        )
        world.say(
            f"The room cleared, the clue was easy to read, and the strange phoneme matched "
            f"a name they both knew."
        )
    else:
        world.say(
            f"{helper.id} tried {fix.fail}, but the smoke kept hanging in the air."
        )
        world.say(
            f"They had to open the window and wait, and the case stayed cloudy until later."
        )


def rhyme_end(world: World, child: Entity, helper: Entity, clue: Clue) -> None:
    world.say(
        f'In the end, {child.id} grinned and said, "A clue can be small, a clue can be neat; '
        f'when friends work together, the mystery feels sweet."'
    )
    world.say(
        f'{helper.id} laughed, and the two of them tucked the paper away, safe and sound.'
    )


def tell(setting: Setting, clue: Clue, mishap: Mishap, fix: Fix,
         child_name: str = "Nora", child_gender: str = "girl",
         helper_name: str = "Milo", helper_gender: str = "boy",
         delay: int = 0) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="seeker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="room", type="room", label="the room"))
    world.facts["setting"] = setting
    world.facts["clue"] = clue
    world.facts["mishap"] = mishap
    world.facts["fix"] = fix
    world.facts["delay"] = delay

    open_scene(world, child, helper, setting, clue)
    world.para()
    raise_mystery(world, child, helper, clue)
    tell_flashback(world, child, helper, clue)
    world.para()
    mishap_event(world, child, mishap, delay)
    warn(world, helper, child)
    reconcile(world, child, helper, fix, clue)
    world.para()
    resolve(world, child, helper, fix, clue, delay)
    rhyme_end(world, child, helper, clue)

    world.facts["outcome"] = "contained" if contained(fix, delay) else "uncleared"
    return world


SETTINGS = {
    "library": Setting("library", "the library", "a hush of paper and dust", "the tall shelf", "the quiet shelf"),
    "attic": Setting("attic", "the attic", "old boxes and soft shadows", "the blanket chest", "the rafters"),
    "school": Setting("school", "the school hallway", "echoes and bright lights", "the coat nook", "the echoing hall"),
}

CLUES = {
    "phoneme": Clue("phoneme", "phoneme", "phoneme", "a tiny sound unit that can hide in a word", {"sound", "mystery"}),
    "whisper": Clue("whisper", "whisper", "whisper", "a soft voice clue", {"sound", "mystery"}),
    "rhyme": Clue("rhyme", "rhyme", "rhyme", "a clue about words that end alike", {"sound", "mystery"}),
}

MISHAPS = {
    "candle_smoke": Mishap("candle_smoke", "a candle stub", "a little puff of smoke", True, {"smoke"}),
    "toast_smoke": Mishap("toast_smoke", "a toast tray", "a little smoky smell", True, {"smoke"}),
}

FIXES = {
    "fan": Fix("fan", 3, 3, "a small fan and an open window", "a paper fan", "used a small fan to clear the smoke", {"air"}),
    "cloth": Fix("cloth", 2, 2, "a damp cloth and calm hands", "a dry cloth", "pressed the smoke away with a damp cloth", {"air"}),
    "wait": Fix("wait", 1, 1, "time and patience", "a hurried wave", "waited for the smoke to drift out", {"air"}),
}


TRAITS = ["curious", "careful", "thoughtful", "quiet"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a mystery with phonemes, smoke, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    if args.fix and not sense_gate(FIXES[args.fix]):
        raise StoryError(f"(Refusing fix '{args.fix}': it is too weak to count as a sensible way to extinguish the smoke.)")
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    mishap = args.mishap or rng.choice(list(MISHAPS))
    fix = args.fix or rng.choice([k for k, v in FIXES.items() if sense_gate(v)])
    return StoryParams(setting, clue, mishap, fix, args.name or rng.choice(["Nora", "Mina", "Ivy", "Tessa"]),
                       args.helper or rng.choice(["Milo", "Ben", "Owen", "Jasper"]),
                       delay=rng.randint(0, 1))


@dataclass
class StoryParams:
    setting: str
    clue: str
    mishap: str
    fix: str
    name: str
    helper: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

CURATED = [
    ("library", "phoneme", "candle_smoke", "fan", 0),
    ("attic", "rhyme", "toast_smoke", "cloth", 1),
    ("school", "whisper", "candle_smoke", "fan", 0),
]



def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-facing mystery story that includes the words "phoneme" and "extinguish".',
        f"Tell a quiet mystery where {f['clue'].word} leads {f['setting'].place} to a hidden truth, then a small smoky mishap is extinguished.",
        f"Write a rhyme-tinged story with a flashback and reconciliation, where two children solve a clue and calm the smoke."
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = world.get("room")  # placeholder for access only
    _ = child
    clue: Clue = f["clue"]
    fix: Fix = f["fix"]
    setting: Setting = f["setting"]
    qas = [
        QAItem(
            f"What strange word did the child notice?",
            f"The child noticed the word {clue.word}. It mattered because it was a small sound clue that pointed toward the hidden meaning."
        ),
        QAItem(
            f"How did they extinguish the smoke?",
            f"They used {fix.qa_text}. That helped clear the room so they could read the clue and continue the mystery."
        ),
        QAItem(
            "Why did they become friends again?",
            f"They apologized after the smoky mishap and forgave each other. The reconciliation let them solve the mystery together instead of staying cross."
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a phoneme?", "A phoneme is a tiny sound unit in a word. If you change one phoneme, a word can sound different."),
        QAItem("What does extinguish mean?", "To extinguish something means to put it out or stop it. People often use the word for putting out smoke or fire."),
        QAItem("What is a rhyme?", "A rhyme is when words sound alike at the end. Rhymes can make a story feel playful and musical."),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CLUES:
            for m in MISHAPS:
                for f in FIXES:
                    if sense_gate(FIXES[f]):
                        combos.append((s, c, m, f))
    return combos


ASP_RULES = r"""
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(S, C, M, F) :- setting(S), clue(C), mishap(M), fix(F), sensible(F).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for m in MISHAPS:
        lines.append(asp.fact("mishap", m))
    for f, fix in FIXES.items():
        lines.append(asp.fact("fix", f))
        lines.append(asp.fact("sense", f, fix.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, mishap=None, fix=None, name=None, helper=None), random.Random(0)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], MISHAPS[params.mishap], FIXES[params.fix], params.name, "girl" if params.name in {"Nora", "Mina", "Ivy", "Tessa"} else "boy", params.helper, "boy", params.delay)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid_combos())))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for s, c, m, f in CURATED:
            p = StoryParams(s, c, m, f, "Nora", "Milo")
            samples.append(generate(p))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
