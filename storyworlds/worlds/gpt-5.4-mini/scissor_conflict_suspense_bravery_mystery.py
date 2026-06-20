#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/scissor_conflict_suspense_bravery_mystery.py
=============================================================================

A standalone story world for a small mystery tale about a curious child,
a pair of scissors, a tense disagreement, a suspenseful clue hunt, and a brave
ending.

Core premise:
- A child finds a strange locked-up clue or tangled package.
- Someone wants to use scissors in a risky way.
- A cautious character objects, creating conflict and suspense.
- Bravery turns the scene toward a safe, sensible solution.
- The ending reveals what the mystery was and what changed.

The world is deliberately small and state-driven. It models:
- physical meters: stuck, torn, cut, opened, searched, discovered
- emotional memes: curiosity, worry, conflict, suspense, bravery, relief

It includes an inline ASP twin, a Python reasonableness gate, Q&A generation
from state, and a normal smoke-testable verification path.
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
SUSPENSE_THRESHOLD = 1.0
BRAVERY_THRESHOLD = 1.0


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
    dark_spot: str
    clue_spot: str
    ending_image: str

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
class MysteryObject:
    id: str
    label: str
    phrase: str
    risk: str
    clue: str
    hidden: str
    sharp: bool = False
    safe_use: bool = True

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
class SuspectMove:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["conflict"] >= THRESHOLD and ("conflict", e.id) not in world.fired:
            world.fired.add(("conflict", e.id))
            out.append("__conflict__")
    return out


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["suspense"] >= SUSPENSE_THRESHOLD and ("suspense", e.id) not in world.fired:
            world.fired.add(("suspense", e.id))
            out.append("__suspense__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["relief"] >= THRESHOLD and ("relief", e.id) not in world.fired:
            world.fired.add(("relief", e.id))
            out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("conflict", _r_conflict), Rule("suspense", _r_suspense), Rule("relief", _r_relief)]


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


def reasonable_use(obj: MysteryObject, move: SuspectMove) -> bool:
    return obj.sharp and obj.safe_use and move.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for oid, obj in OBJECTS.items():
            for mid, move in MOVES.items():
                if reasonable_use(obj, move):
                    combos.append((sid, oid, mid))
    return combos


def predict(world: World, obj_id: str, move_id: str) -> dict:
    sim = world.copy()
    _do_scare(sim, sim.get("child"), OBJECTS[obj_id], MOVES[move_id], narrate=False)
    return {
        "opened": sim.get("box").meters["opened"] >= THRESHOLD,
        "torn": sim.get("box").meters["torn"] >= THRESHOLD,
    }


def _do_scare(world: World, child: Entity, obj: MysteryObject, move: SuspectMove, narrate: bool = True) -> None:
    child.memes["suspense"] += 1
    child.meters["searched"] += 1
    world.get("box").meters["searched"] += 1


def open_with_scissors(world: World, child: Entity, obj: MysteryObject, move: SuspectMove) -> None:
    world.get("box").meters["opened"] += 1
    world.get("box").meters["cut"] += 1
    child.memes["bravery"] += 1
    world.say(
        f"{move.id.capitalize()} {move.text}."
    )


def tension(world: World, child: Entity, helper: Entity, obj: MysteryObject) -> None:
    child.memes["conflict"] += 1
    helper.memes["worry"] += 1
    world.say(
        f'{child.id} stared at the stuck box and whispered, "I think the answer is inside." '
        f'But {helper.id} bit {helper.pronoun("possessive")} lip. "Not with scissors right there," {helper.id} said.'
    )


def brave_choice(world: World, child: Entity, helper: Entity, obj: MysteryObject, move: SuspectMove) -> None:
    child.memes["bravery"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{child.id} took a breath, held the scissors still, and chose the careful way instead. '
        f"{helper.id} nodded, because that was the brave part."
    )


def reveal(world: World, setting: Setting, child: Entity, helper: Entity, obj: MysteryObject) -> None:
    world.get("box").meters["opened"] += 1
    world.get("box").meters["discovered"] += 1
    child.memes["relief"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"Inside was {obj.phrase}, and the mystery was solved: {obj.hidden}. "
        f"{setting.ending_image.capitalize()}."
    )
    world.say(
        f"{child.id} smiled at {helper.id}, and the two of them looked at the safe clue together."
    )


def tell(setting: Setting, obj: MysteryObject, move: SuspectMove,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_name: str = "Dad", helper_gender: str = "father") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    box = world.add(Entity(id="box", kind="thing", type="box", label="the box"))
    scissors = world.add(Entity(id="scissors", kind="thing", type="tool", label="the scissors"))

    child.memes["curiosity"] += 1
    child.memes["suspense"] += 1

    world.say(
        f"On a quiet evening, {child.id} found {setting.place} feeling extra still, "
        f"as if it were hiding a secret."
    )
    world.say(
        f"Near {setting.dark_spot}, {child.id} spotted {obj.phrase}. {obj.clue.capitalize()}."
    )

    world.para()
    tension(world, child, helper, obj)

    if move.sense < 2:
        raise StoryError("The scissors move is too unsafe to build a story around.")

    if obj.sharp:
        world.say(
            f"{child.id} kept looking at the jammed latch. {helper.id} watched closely, "
            f"ready for whatever happened next."
        )
    world.para()

    if obj.safe_use:
        if move.power >= 2:
            brave_choice(world, child, helper, obj, move)
            reveal(world, setting, child, helper, obj)
        else:
            child.memes["conflict"] += 1
            world.say(
                f"{child.id} almost tugged at the package with {scissors.label}, but stopped. "
                f"{helper.id} pointed to the tape and showed a safer way to loosen it."
            )
            reveal(world, setting, child, helper, obj)
    else:
        world.say(
            f"{child.id} realized the puzzle did not need a cut at all. "
            f"That was the brave choice: ask for help and keep the mystery safe."
        )
        reveal(world, setting, child, helper, obj)

    world.facts.update(
        child=child,
        helper=helper,
        box=box,
        scissors=scissors,
        setting=setting,
        obj=obj,
        move=move,
        outcome="solved",
    )
    return world


SETTINGS = {
    "attic": Setting("attic", "the dusty attic", "quiet beams", "the old trunk", "the corner window"),
    "library": Setting("library", "the little library room", "soft shelves", "the locked drawer", "the reading lamp"),
    "shed": Setting("shed", "the backyard shed", "creaky boards", "the hanging hook", "the narrow window"),
}

OBJECTS = {
    "ribbon_box": MysteryObject(
        "ribbon_box", "a ribbon box", "a ribbon box wrapped in tape",
        "the tape might tear if pulled too hard", "There was a tiny note tied to it",
        "the box held the answer to a birthday surprise", sharp=True, safe_use=True
    ),
    "mystery_package": MysteryObject(
        "mystery_package", "a parcel", "a small parcel tied with string",
        "the string could be loosened carefully", "A corner of the label peeked out",
        "it belonged to a neighbor who had left a surprise to return", sharp=True, safe_use=True
    ),
    "locked_tin": MysteryObject(
        "locked_tin", "a tin", "a little tin with a stubborn lid",
        "the lid was stuck, not sealed forever", "A hand-drawn star was on top",
        "it held old cookies for the next day", sharp=True, safe_use=True
    ),
}

MOVES = {
    "scissor_peek": SuspectMove(
        "scissor_peek", 3, 2,
        "used the scissors to snip the tape a little and peek inside",
        "tried to cut too fast and made a mess",
        "carefully snipped the tape and peeked inside",
    ),
    "scissor_open": SuspectMove(
        "scissor_open", 2, 3,
        "slid the scissors under the tape and opened the package slowly",
        "slid too hard and nicked the wrapping",
        "slowly opened the package with the scissors",
    ),
    "ask_first": SuspectMove(
        "ask_first", 3, 1,
        "asked for help and left the scissors on the table",
        "waited too long and the mystery stayed shut",
        "asked for help instead of cutting alone",
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Max", "Finn"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    object: str
    move: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld with scissors, conflict, suspense, and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if args.setting is None or c[0] == args.setting
              and args.object is None or c[1] == args.object
              and args.move is None or c[2] == args.move]
    if args.object and args.move and not reasonable_use(OBJECTS[args.object], MOVES[args.move]):
        raise StoryError("That scissors choice is too unsafe or dull for this mystery.")
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj_id, move_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    helper_name = args.helper_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(setting, obj_id, move_id, child_name, child_gender, helper_name, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        OBJECTS[params.object],
        MOVES[params.move],
        params.child_name,
        params.child_gender,
        params.helper_name,
        params.helper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    obj = f["obj"]
    return [
        f"Write a short mystery story for a 3-to-5-year-old where {child.id} finds {obj.label} and uses the word 'scissor'.",
        f"Tell a suspenseful but gentle mystery where {child.id} and {f['helper'].id} disagree about scissors, then solve the puzzle safely.",
        f"Write a child-friendly mystery story with conflict, suspense, and bravery that ends with the secret revealed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    obj = f["obj"]
    move = f["move"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}, who were looking at a strange clue together. The mystery centered on what was hidden inside the box."),
        ("Why was there conflict?",
         f"{child.id} wanted to use scissors to open the clue, but {helper.id} worried it might be done too fast. That disagreement made the moment tense."),
        ("How did bravery show up?",
         f"{child.id} took a breath and chose the careful way instead of rushing. That was brave because it meant doing the safe thing while the mystery still felt exciting."),
        ("What was the mystery in the end?",
         f"The mystery was solved when they opened {obj.phrase} and found out {obj.hidden}. The ending showed that the secret had been waiting there the whole time."),
    ]
    if move.id.startswith("scissor"):
        qa.append((
            "What did the scissors help with?",
            f"They helped {child.id} open the package carefully, not slash it open in a hurry. The scissors were part of the clue-solving, but the story stayed safe because the child used them gently."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = [
        ("What are scissors for?",
         "Scissors are tools used to cut paper, tape, string, and other things carefully. They are sharp, so children should use them with a grown-up nearby."),
        ("What is suspense in a story?",
         "Suspense is the worried, wondering feeling that makes you want to keep reading. It happens when you do not know what will happen next."),
        ("What does bravery mean?",
         "Bravery means doing the right thing even when you feel nervous or scared. A brave person does not need to feel fearless; they keep going carefully anyway."),
        ("What is a mystery story?",
         "A mystery story is a story where something is hidden or not explained at first. The characters look for clues until they discover the answer."),
    ]
    return out


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_response(move_id: str) -> str:
    move = MOVES[move_id]
    return f"(Refusing move '{move_id}': it scores too low for a safe mystery story.)"


ASP_RULES = r"""
reasonable(O,M) :- object(O), move(M), sharp(O), safe_use(O), sense(M,S), S >= 2.
story(S,O,M) :- setting(S), reasonable(O,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.sharp:
            lines.append(asp.fact("sharp", oid))
        if obj.safe_use:
            lines.append(asp.fact("safe_use", oid))
    for mid, move in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("sense", mid, move.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show story/3."))
    return sorted(set(asp.atoms(model, "story")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, object=None, move=None,
                                                            child_name=None, child_gender=None,
                                                            helper_name=None, helper_gender=None),
                                         random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generate() smoke test failed: {e}")
    return rc


def asp_show() -> str:
    return asp_program("", "#show story/3.")


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
    StoryParams("attic", "ribbon_box", "scissor_peek", "Mia", "girl", "Dad", "father"),
    StoryParams("library", "mystery_package", "scissor_open", "Noah", "boy", "Mom", "mother"),
    StoryParams("shed", "locked_tin", "ask_first", "Lily", "girl", "Dad", "father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        for s, o, m in asp_valid_combos():
            print(f"  {s:8} {o:16} {m}")
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
            header = f"### {p.child_name}: {p.setting} / {p.object} / {p.move}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def story_qa(world: World) -> list[tuple[str, str]]:
    return world_qa_placeholder(world)


def world_qa_placeholder(world: World) -> list[tuple[str, str]]:
    return world_knowledge_qa(world)


if __name__ == "__main__":
    main()
