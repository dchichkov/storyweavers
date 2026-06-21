#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fulfully_executive_lesson_learned_magic_bad_ending.py
======================================================================================

A small Storyweavers world in a whodunit style: an executive tries to solve a
mystery with a magic shortcut, someone disappears from sight, clues are traced,
and the ending turns bad before a lesson lands. The story includes the seed
words "fulfully" and "executive" as authored flavor words, and keeps the prose
child-facing, concrete, and state-driven.

The world is intentionally small:
- a sealed office after hours,
- one executive with a habit of saying "fulfully",
- one magic object that can hide, reveal, or mislead,
- one overlooked clue,
- one bad ending with a clear lesson learned.

It follows the Storyweavers contract:
- typed entities with meters and memes,
- world state drives prose,
- three Q&A sets from world state,
- a Python reasonableness gate plus inline ASP twin,
- CLI support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp.
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

MAGIC_MIN = 1.0
EVIDENCE_MIN = 1.0
DREAD_MIN = 1.0
LESSON_MIN = 1.0


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
        if self.type in {"woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father", "executive"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Clue:
    id: str
    label: str
    reveal: str
    hide_chance: float
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    effect: str
    cost: str
    safe_use: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Ending:
    id: str
    label: str
    severity: int
    text: str
    lesson: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        return clone
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_hide_clue(world: World) -> list[str]:
    out: list[str] = []
    for clue in [e for e in world.entities.values() if e.role == "clue"]:
        if clue.meters["seen"] >= MAGIC_MIN:
            continue
        sig = ("hide", clue.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        clue.meters["hidden"] += 1
        out.append("")
    return out


def _r_learn(world: World) -> list[str]:
    out: list[str] = []
    execu = world.entities.get("executive")
    clue = world.entities.get("note")
    if not execu or not clue:
        return out
    if execu.memes["doubt"] < DREAD_MIN:
        return out
    sig = ("learn",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    execu.memes["lesson"] += 1
    out.append("")
    return out


CAUSAL_RULES = [
    Rule("hide_clue", "mystery", _r_hide_clue),
    Rule("learn", "lesson", _r_learn),
]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                for s in sents:
                    if s:
                        world.say(s)


@dataclass
class StoryParams:
    office: str
    executive_name: str
    clue: str
    magic: str
    ending: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


OFFICES = {
    "boardroom": {
        "label": "the boardroom",
        "scene": "a silent boardroom with polished chairs and a clock that ticked too loud",
    },
    "hallway": {
        "label": "the hallway",
        "scene": "a quiet hallway with glass doors and a blue carpet",
    },
    "archive": {
        "label": "the archive room",
        "scene": "an archive room with boxes, folders, and one lamp left on",
    },
}

CLUES = {
    "note": Clue(
        id="note",
        label="a folded note",
        reveal="a folded note sat under the chair",
        hide_chance=0.4,
        tags={"paper", "mystery"},
    ),
    "ring": Clue(
        id="ring",
        label="a silver ring",
        reveal="a silver ring gleamed near the files",
        hide_chance=0.3,
        tags={"metal", "mystery"},
    ),
    "keycard": Clue(
        id="keycard",
        label="a missing keycard",
        reveal="a keycard lay behind the plant",
        hide_chance=0.5,
        tags={"plastic", "mystery"},
    ),
}

MAGICS = {
    "mirror": MagicTool(
        id="mirror",
        label="a magic mirror",
        phrase="a magic mirror",
        effect="could show the truth in a shimmer",
        cost="it also showed the wrong thing if spoken to too fast",
        safe_use="held it still and asked one careful question",
        tags={"magic", "reveal"},
    ),
    "lamp": MagicTool(
        id="lamp",
        label="a magic lamp",
        phrase="a magic lamp",
        effect="glowed over hidden clues",
        cost="its light dimmed whenever someone guessed instead of looked",
        safe_use="shone it slowly across the floor",
        tags={"magic", "reveal"},
    ),
    "coin": MagicTool(
        id="coin",
        label="a magic coin",
        phrase="a magic coin",
        effect="tipped toward where someone had been",
        cost="it spun wildly when used to hurry a search",
        safe_use="placed it flat and listened",
        tags={"magic", "hint"},
    ),
}

ENDINGS = {
    "bad": Ending(
        id="bad",
        label="a bad ending",
        severity=2,
        text="the wrong door opened and the room went dark",
        lesson="magic is not a shortcut for careful looking",
        tags={"bad", "lesson"},
    ),
    "worse": Ending(
        id="worse",
        label="a worse ending",
        severity=3,
        text="the clue was knocked under the cabinet and the mystery got bigger",
        lesson="rushing makes mysteries harder, not easier",
        tags={"bad", "lesson"},
    ),
}

NAMES = ["Mara", "Lena", "Nico", "Tess", "Owen", "June", "Iris", "Theo"]
CURATED = [
    StoryParams(office="boardroom", executive_name="Mara", clue="note", magic="mirror", ending="bad", seed=1),
    StoryParams(office="archive", executive_name="Nico", clue="keycard", magic="lamp", ending="worse", seed=2),
]

OFFICE_CHOICES = list(OFFICES)
NAME_CHOICES = list(NAMES)
CLUE_CHOICES = list(CLUES)
MAGIC_CHOICES = list(MAGICS)
ENDING_CHOICES = list(ENDINGS)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for office in OFFICES:
        for clue in CLUES:
            for magic in MAGICS:
                for ending in ENDINGS:
                    if clue in {"note", "keycard"} and magic in {"mirror", "lamp", "coin"}:
                        combos.append((office, clue, magic, ending))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.office not in OFFICES:
        raise StoryError("Unknown office.")
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if params.magic not in MAGICS:
        raise StoryError("Unknown magic.")
    if params.ending not in ENDINGS:
        raise StoryError("Unknown ending.")
    if params.ending == "worse" and params.magic == "coin":
        raise StoryError("The magic coin is too vague for the worse ending; pick a clearer magic object.")
    if params.clue == "ring" and params.office == "hallway":
        raise StoryError("The silver ring would not plausibly be found in that hallway scene.")


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World()
    office = OFFICES[params.office]
    execu = world.add(Entity(id="executive", kind="character", type="executive", label=params.executive_name, role="investigator"))
    clue = world.add(Entity(id="note", kind="thing", type="clue", label=CLUES[params.clue].label, role="clue", tags=set(CLUES[params.clue].tags)))
    magic = world.add(Entity(id="magic", kind="thing", type="magic", label=MAGICS[params.magic].label, role="tool", tags=set(MAGICS[params.magic].tags)))
    ending = ENDINGS[params.ending]
    execu.memes["curiosity"] = 1.0
    execu.memes["doubt"] = 1.0
    world.facts.update(office=office, clue=clue, magic=magic, ending=ending)
    world.say(f"After hours, {params.executive_name} walked into {office['label']}. {office['scene']}.")
    world.say(f"{params.executive_name} was the executive in charge, and {params.executive_name.lower()} said, \"I will solve this fulfully.\"")
    world.say(f"But something was wrong: {CLUES[params.clue].reveal}.")
    world.para()
    world.say(f"Then {params.executive_name} lifted {MAGICS[params.magic].phrase}. It {MAGICS[params.magic].effect}, but {MAGICS[params.magic].cost}.")
    execu.meters["magic"] += 1
    execu.memes["doubt"] += 1
    clue.meters["seen"] += 1
    if params.ending == "bad":
        execu.meters["dread"] += 1
    else:
        execu.meters["dread"] += 2
    propagate(world)
    world.para()
    if params.ending == "bad":
        world.say(f"{params.executive_name} followed the glow the wrong way, and {ending.text}.")
        world.say(f"Only then did {params.executive_name} learn the lesson: {ending.lesson}.")
    else:
        world.say(f"{params.executive_name} found the clue too late, and {ending.text}.")
        world.say(f"That was how {params.executive_name} learned that {ending.lesson}.")
    world.facts["outcome"] = params.ending
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    office = f["office"]["label"]
    clue = f["clue"].label
    magic = f["magic"].label
    ending = f["ending"].label
    return [
        f'Write a whodunit-style story for a young child set in {office}, with {magic} and {clue}, and include the word "fulfully".',
        f"Tell a short mystery where an executive tries to solve a problem with {magic}, but the ending goes bad and the lesson learned is that careful looking matters.",
        f'Write a child-friendly mystery story with a bad ending, a magic object, and the word "executive" somewhere in the story.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params_name = world.get("executive").label
    clue = f["clue"].label
    magic = f["magic"].label
    ending = f["ending"].lesson
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {params_name}, the executive who tried to solve the mystery. {params_name} was the person following the clues in the office.",
        ),
        QAItem(
            question=f"What did {params_name} try to use to solve the mystery?",
            answer=f"{params_name} tried to use {magic}. It seemed helpful at first, but it could not replace careful looking at the clues.",
        ),
        QAItem(
            question="Why did the ending go badly?",
            answer=f"The ending went badly because magic led {params_name} the wrong way instead of helping with the real clue. The story shows that {ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an executive?",
            answer="An executive is a grown-up who helps make big decisions and keeps a group working smoothly.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
        QAItem(
            question="Why can magic be tricky in a mystery?",
            answer="Magic can be tricky because it may point to the wrong thing if someone trusts it too much. Careful looking is still important.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "",
             "== (2) Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:7}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
occurs(magic).
lesson_learned :- executive(X), clue(C), magic(M), occurs(magic), seen(C), doubt(X).
bad_ending :- ending(bad).
valid(Office, Clue, Magic, Ending) :- office(Office), clue(Clue), magic(Magic), ending(Ending).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for o in OFFICES:
        lines.append(asp.fact("office", o))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
        lines.append(asp.fact("seen", c))
    for m in MAGICS:
        lines.append(asp.fact("magic", m))
    for e in ENDINGS:
        lines.append(asp.fact("ending", e))
    lines.append(asp.fact("executive", "x"))
    lines.append(asp.fact("doubt", "x"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set((o, c, m, e) for o, c, m, e in valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generate() succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with magic, a bad ending, and a lesson learned.")
    ap.add_argument("--office", choices=OFFICE_CHOICES)
    ap.add_argument("--name", choices=NAME_CHOICES)
    ap.add_argument("--clue", choices=CLUE_CHOICES)
    ap.add_argument("--magic", choices=MAGIC_CHOICES)
    ap.add_argument("--ending", choices=ENDING_CHOICES)
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
    office = args.office or rng.choice(OFFICE_CHOICES)
    clue = args.clue or rng.choice(CLUE_CHOICES)
    magic = args.magic or rng.choice(MAGIC_CHOICES)
    ending = args.ending or rng.choice(ENDING_CHOICES)
    params = StoryParams(
        office=office,
        executive_name=args.name or rng.choice(NAME_CHOICES),
        clue=clue,
        magic=magic,
        ending=ending,
        seed=None,
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    if params.office not in OFFICES or params.clue not in CLUES or params.magic not in MAGICS or params.ending not in ENDINGS:
        raise StoryError("Invalid parameters.")
    world = build_world(params)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
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
            p = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
