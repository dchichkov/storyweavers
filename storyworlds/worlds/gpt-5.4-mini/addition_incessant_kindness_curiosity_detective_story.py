#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/addition_incessant_kindness_curiosity_detective_story.py
========================================================================================

A standalone storyworld for a tiny detective tale: a child detective notices an
incessant tapping sound, uses curiosity to follow clues, and answers it with
kindness after a small addition to the puzzle reveals the source.

The world is built as a compact causal simulation. Typed entities carry physical
meters and emotional memes; state changes drive the prose, the Q&A, and the
verification checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
    light: str
    rooms: set[str] = field(default_factory=set)

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
class Suspect:
    id: str
    label: str
    place: str
    clue: str
    sound: str
    innocent_reason: str
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
class Tool:
    id: str
    label: str
    use: str
    adds: str
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_restless(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["restless"] < THRESHOLD:
            continue
        sig = ("restless", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append("__restless__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    if world.get("helper").memes["kindness"] >= THRESHOLD and world.get("child").memes["fear"] >= THRESHOLD:
        sig = ("kindness",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("helper").memes["warmth"] += 1
            out.append("__kindness__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("restless", "emotional", _r_restless),
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


def predict_source(world: World, suspect_id: str) -> dict:
    sim = world.copy()
    _do_observe(sim, sim.get(suspect_id), narrate=False)
    return {
        "heard": sim.get(suspect_id).meters["heard"] >= THRESHOLD,
        "assistant_calm": sim.get("assistant").memes["calm"] >= THRESHOLD,
    }


def _do_observe(world: World, suspect: Entity, narrate: bool = True) -> None:
    suspect.meters["heard"] += 1
    suspect.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def _do_addition(world: World, tool: Tool, suspect: Entity) -> None:
    suspect.meters["heard"] += 1
    suspect.memes["curiosity"] += 1
    world.say(f"{tool.label.capitalize()} made an addition to the puzzle: one more clue.")
    propagate(world, narrate=True)


def setup(world: World, child: Entity, assistant: Entity) -> None:
    child.memes["curiosity"] = 1
    child.memes["kindness"] = 1
    assistant.memes["calm"] = 1
    world.say(
        f"At {world.setting.place}, {child.id} was a small detective with a bright notebook, "
        f"and {assistant.id} kept the desk tidy beside {world.setting.light}."
    )
    world.say(
        f"{child.id} liked solving little mysteries, and {assistant.id} liked helping in a quiet way."
    )


def hear_sound(world: World, child: Entity, suspect: Suspect) -> None:
    child.meters["restless"] += 1
    world.say(
        f"Then an incessant tapping started near {suspect.place}. Tap, tap, tap -- it would not stop."
    )
    world.say(f"{child.id} frowned. {child.pronoun().capitalize()} wanted to know what made the noise.")


def suspect_list(world: World, child: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} made a list of suspects: a loose window latch, a dripping pipe, and a lonely clock."
    )


def investigate(world: World, child: Entity, suspect: Suspect, tool: Tool) -> None:
    pred = predict_source(world, suspect.id)
    world.facts["predicted"] = pred
    world.say(
        f"{child.id} followed the tapping to {suspect.place}. {child.pronoun().capitalize()} listened close, "
        f"then used a little addition: {tool.adds}."
    )
    world.say(
        f"The new clue proved {suspect.label} was only a noisy helper, not a troublemaker."
    )


def reveal(world: World, child: Entity, assistant: Entity, suspect: Suspect) -> None:
    child.memes["relief"] += 1
    assistant.memes["warmth"] += 1
    world.say(
        f"Behind {suspect.label}, {child.id} found {suspect.clue}. That was the real source of the tapping."
    )
    world.say(
        f"{assistant.id} smiled and said {suspect.innocent_reason}."
    )


def kindness_fix(world: World, child: Entity, assistant: Entity, suspect: Suspect) -> None:
    child.memes["kindness"] += 1
    assistant.memes["kindness"] += 1
    world.say(
        f"{child.id} was kind about it. Instead of blaming anyone, {child.pronoun()} tucked the clue into place and smiled."
    )
    world.say(
        f"{assistant.id} added a soft felt pad, and the tapping turned into a gentle tick."
    )


def ending(world: World, child: Entity, assistant: Entity, suspect: Suspect) -> None:
    world.say(
        f"By bedtime, the room was quiet again. {child.id}'s notebook had one neat solution, "
        f"and the mystery ended with a calm lamp, a kinder heart, and no more incessant tapping."
    )


def tell(setting: Setting, suspect: Suspect, tool: Tool,
         child_name: str = "Mina", child_gender: str = "girl",
         assistant_name: str = "Aunt Bea", assistant_gender: str = "woman") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="detective"))
    assistant = world.add(Entity(id=assistant_name, kind="character", type=assistant_gender, role="helper"))
    noisy = world.add(Entity(id="noise", type="thing", label=suspect.label))
    world.add(Entity(id="tool", type="thing", label=tool.label))

    setup(world, child, assistant)
    world.para()
    hear_sound(world, child, suspect)
    suspect_list(world, child)
    investigate(world, child, suspect, tool)
    reveal(world, child, assistant, suspect)
    kindness_fix(world, child, assistant, suspect)
    ending(world, child, assistant, suspect)

    world.facts.update(
        child=child,
        assistant=assistant,
        suspect=suspect,
        tool=tool,
        setting=setting,
        outcome="solved",
        noisy=noisy,
    )
    return world


SETTINGS = {
    "library": Setting("library", "the old library", "a brass desk lamp", {"reading nook", "desk"}),
    "museum": Setting("museum", "the little museum", "a wall of sunny windows", {"hall", "archive"}),
    "attic": Setting("attic", "the attic room", "a round attic lamp", {"boxes", "window"}),
}

SUSPECTS = {
    "clock": Suspect(
        "clock",
        "clock",
        "the back shelf",
        "a tiny broken bead under the clock",
        "tap, tap, tap",
        "The clock was only rattling because one bead had slipped inside it.",
        tags={"clock", "noise"},
    ),
    "pipe": Suspect(
        "pipe",
        "pipe",
        "the wash sink",
        "a small pebble stuck by the pipe",
        "tap, tap, tap",
        "The pipe was fine; the pebble made the sound when the water started to trickle.",
        tags={"pipe", "noise"},
    ),
    "window": Suspect(
        "window",
        "window latch",
        "the window seat",
        "a loose paper tag rubbing the latch",
        "tap, tap, tap",
        "The latch was not broken; a paper tag was brushing it in the breeze.",
        tags={"window", "noise"},
    ),
}

TOOLS = {
    "list": Tool("list", "a clue list", "write down clues", "one more clue"),
    "mirror": Tool("mirror", "a tiny mirror", "peek around corners", "a better look"),
    "string": Tool("string", "a piece of string", "mark the trail", "a helpful addition"),
}

GIRL_NAMES = ["Mina", "Nora", "Lena", "Ivy", "June"]
BOY_NAMES = ["Owen", "Theo", "Leo", "Milo", "Finn"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    suspect: str
    tool: str
    child_name: str
    child_gender: str
    assistant_name: str
    assistant_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for suspect in SUSPECTS:
            for tool in TOOLS:
                combos.append((s, suspect, tool))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a child that includes the words "addition" and "incessant".',
        f"Tell a cozy mystery where {f['child'].id} hears incessant tapping at {f['setting'].place} and solves it with curiosity and kindness.",
        f"Write a short detective tale where one extra clue, an addition to the puzzle, helps reveal what is making the noise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    assistant = f["assistant"]
    suspect = f["suspect"]
    tool = f["tool"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer="It is a little detective story. A curious child follows a noisy clue, solves the mystery, and treats everyone kindly."
        ),
        QAItem(
            question="What problem did the child notice?",
            answer=f"{child.id} heard incessant tapping near {suspect.place}. The sound would not stop, so the child knew there was a mystery to solve."
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{child.id} used {tool.label} as an addition to the clues, then found the real cause behind {suspect.label}. That careful extra clue helped the child understand the noise without blaming anyone."
        ),
        QAItem(
            question="How did kindness matter in the ending?",
            answer=f"{child.id} stayed kind to {assistant.id} and to the noisy object, then helped fix the problem gently. That made the ending calm instead of mean."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curiosity do for a detective?",
            answer="Curiosity helps a detective keep looking, listen closely, and ask good questions until the clue makes sense."
        ),
        QAItem(
            question="Why can a noisy thing still be harmless?",
            answer="A noisy thing can be harmless if it is only loose, stuck, or rubbing against something. The sound can be annoying without meaning something bad is happening."
        ),
        QAItem(
            question="What is kindness in a mystery?",
            answer="Kindness means solving the problem without blaming, shouting, or hurting anyone. It helps everyone feel safe while the mystery is fixed."
        ),
        QAItem(
            question="What is an addition?",
            answer="An addition is something extra that gets added to a set or a puzzle. In a mystery, one extra clue can make the answer clear."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("library", "clock", "list", "Mina", "girl", "Aunt Bea", "woman"),
    StoryParams("museum", "window", "mirror", "Owen", "boy", "Uncle Ray", "man"),
    StoryParams("attic", "pipe", "string", "Lena", "girl", "Dad", "man"),
]


ASP_RULES = r"""
noisy(N) :- suspect(N).
curiosity(D) :- child(D).
addition_clue(T) :- tool(T).
solved(D,S) :- curiosity(D), noisy(S), addition_clue(T), tool(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show suspect/1."))
    return 0 if set(asp.atoms(model, "suspect")) == {(sid,) for sid in SUSPECTS} else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world about curiosity and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--assistant-name")
    ap.add_argument("--assistant-gender", choices=["woman", "man"])
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    tool = args.tool or rng.choice(sorted(TOOLS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    assistant_gender = args.assistant_gender or rng.choice(["woman", "man"])
    assistant_name = args.assistant_name or ("Aunt Bea" if assistant_gender == "woman" else "Uncle Ray")
    return StoryParams(setting, suspect, tool, child_name, child_gender, assistant_name, assistant_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        SUSPECTS[params.suspect],
        TOOLS[params.tool],
        params.child_name,
        params.child_gender,
        params.assistant_name,
        params.assistant_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show suspect/1."))
    return sorted(set(asp.atoms(model, "suspect")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show suspect/1."))
        return
    if args.verify:
        rc = asp_verify()
        if rc != 0:
            sys.exit(rc)
        try:
            sample = generate(CURATED[0])
            _ = sample.story
        except Exception as exc:  # pragma: no cover
            print(f"SMOKE TEST FAILED: {exc}")
            sys.exit(1)
        print("OK: ASP parity and story generation smoke test passed.")
        return
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible suspects:")
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
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
