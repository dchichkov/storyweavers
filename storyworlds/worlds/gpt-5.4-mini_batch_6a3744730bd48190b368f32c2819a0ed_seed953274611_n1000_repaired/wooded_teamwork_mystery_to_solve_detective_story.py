#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wooded_teamwork_mystery_to_solve_detective_story.py
===================================================================================

A small storyworld: a kid detective team in a wooded place solves a tiny mystery
by working together. The world is state-driven: clues appear, the team reasons,
they search, and the ending proves what changed.

The model keeps two axes:
- physical meters: dirt, found, hidden, damp, solved, etc.
- emotional memes: worry, confidence, teamwork, relief, curiosity, etc.

It supports a Python reasonableness gate and an inline ASP twin, plus QA sets
grounded in the simulated world.

Run:
    python storyworlds/worlds/gpt-5.4-mini/wooded_teamwork_mystery_to_solve_detective_story.py
    python storyworlds/worlds/gpt-5.4-mini/wooded_teamwork_mystery_to_solve_detective_story.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    affordances: set[str] = field(default_factory=set)
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


@dataclass
class Mystery:
    id: str
    missing: str
    hidden_in: str
    clue: str
    risk: str
    keyword: str
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
class Tool:
    id: str
    label: str
    use: str
    safe: bool = True
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
class StoryParams:
    setting: str
    mystery: str
    tool: str
    helper: str
    helper_gender: str
    detective: str
    detective_gender: str
    adult: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_damp(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["searching"] < THRESHOLD:
            continue
        sig = ("damp", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["focus"] += 1
        out.append("__")
    return out


def _r_solved(world: World) -> list[str]:
    out = []
    if world.facts.get("found_clue") and world.facts.get("tool_used") and not world.facts.get("solved"):
        world.facts["solved"] = True
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["relief"] += 1
        out.append("__")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    narr = []
    while changed:
        changed = False
        for rule in (_r_damp, _r_solved):
            s = rule(world)
            if s:
                changed = True
                narr.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for line in narr:
            world.say(line)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for t in TOOLS:
                if reasonableness(s, m, t):
                    combos.append((s, m, t))
    return combos


def reasonableness(setting_id: str, mystery_id: str, tool_id: str) -> bool:
    setting = SETTINGS[setting_id]
    mystery = MYSTERIES[mystery_id]
    tool = TOOLS[tool_id]
    return (
        setting.place == "wooded" and
        "woods" in setting.affordances and
        mystery.hidden_in == "wooded" and
        tool.safe
    )


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if params.helper_gender not in {"girl", "boy"} or params.detective_gender not in {"girl", "boy"}:
        raise StoryError("Invalid gender.")
    if not reasonableness(params.setting, params.mystery, params.tool):
        raise StoryError("That combination does not fit a wooded detective mystery.")
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]

    world = World(setting)
    det = world.add(Entity(id=params.detective, kind="character", type=params.detective_gender, role="detective"))
    helpy = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    adult = world.add(Entity(id=params.adult, kind="character", type="adult"))
    clue = world.add(Entity(id="clue", label=mystery.clue))
    hidden = world.add(Entity(id="hidden", label=mystery.missing))
    world.facts.update(detective=det, helper=helpy, adult=adult, mystery=mystery, tool=tool, clue=clue, hidden=hidden)
    return world


def tell(world: World) -> None:
    f = world.facts
    det: Entity = f["detective"]
    helpy: Entity = f["helper"]
    adult: Entity = f["adult"]
    mystery: Mystery = f["mystery"]
    tool: Tool = f["tool"]

    det.memes["curiosity"] += 1
    helpy.memes["teamwork"] += 1
    world.say(
        f"On a quiet wooded path, {det.id} and {helpy.id} noticed something odd near the trees. "
        f"{world.setting.detail} The little mystery was simple: {mystery.missing} had gone missing."
    )
    world.say(
        f'{det.id} squinted at the ground. "{mystery.clue}" {helpy.id} said, pointing beside the roots. '
        f"The clue looked fresh, and both children leaned closer."
    )

    world.para()
    det.meters["searching"] += 1
    helpy.meters["searching"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{det.id} took the lead, and {helpy.id} searched beside {mystery.hidden_in} with {tool.label}. "
        f"Together they followed the clue {mystery.keyword} by {mystery.keyword}."
    )

    found = True
    if found:
        mystery_found = world.get("hidden")
        mystery_found.meters["found"] += 1
        world.facts["found_clue"] = True
        world.say(
            f"Under a low branch, they found {mystery.missing}. It had been tucked away where the leaves were thick, "
            f"and the mystery made sense at last."
        )
        world.para()
        world.say(
            f"{adult.label_word.capitalize()} came over and smiled when the two children showed the clue and the found item. "
            f'"That was good teamwork," {adult.id} said. "One of you noticed, and the other one kept the search steady."'
        )
        world.facts["tool_used"] = True
        propagate(world, narrate=False)
        world.say(
            f"By the end, the wooded trail looked peaceful again, and {det.id} held {mystery.missing} with a bright grin. "
            f"{helpy.id} stood beside {det.id}, proud that together they had solved the little mystery."
        )


def prompts_from_world(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    det: Entity = f["detective"]
    helpy: Entity = f["helper"]
    return [
        f'Write a detective story for young children set in the wooded area, where {det.id} and {helpy.id} solve a mystery together.',
        f"Tell a teamwork story where a clue in the wooded place leads to {mystery.missing} being found.",
        f'Write a mystery-to-solve story that includes the word "wooded" and ends with the two children working as a team.',
    ]


def story_qa_from_world(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    det: Entity = f["detective"]
    helpy: Entity = f["helper"]
    adult: Entity = f["adult"]
    return [
        QAItem(
            question="What was the mystery?",
            answer=f"The mystery was to find {mystery.missing} in the wooded place. The clue led the children there, and they solved it together."
        ),
        QAItem(
            question=f"How did {det.id} and {helpy.id} solve the problem?",
            answer=f"They listened to the clue, searched side by side, and used teamwork to follow the trail. That steady searching helped them find {mystery.missing}."
        ),
        QAItem(
            question=f"What did {adult.id} say about their work?",
            answer=f"{adult.id} said it was good teamwork because one child noticed the clue and the other kept the search going. That is why the mystery could be solved."
        ),
    ]


def world_qa_from_world(world: World) -> list[QAItem]:
    return [
        QAItem("What does wooded mean?", "Wooded means full of trees or growing in a place with lots of trees."),
        QAItem("What does teamwork mean?", "Teamwork means people help each other and work together to finish something."),
        QAItem("What is a clue?", "A clue is a little piece of information that helps solve a mystery."),
    ]


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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


SETTINGS = {
    "wooded": Setting(id="wooded", place="wooded", detail="The wooded path was quiet, with mossy roots and a narrow trail.", affordances={"woods"}),
}

MYSTERIES = {
    "missing_key": Mystery(id="missing_key", missing="the small brass key", hidden_in="the mossy log", clue="A shiny mark caught the light near a root.", risk="lost", keyword="key", tags={"key", "search"}),
    "lost_hat": Mystery(id="lost_hat", missing="the red cap", hidden_in="the fallen branch", clue="A tiny red thread hung from the bark.", risk="lost", keyword="hat", tags={"hat", "search"}),
}

TOOLS = {
    "magnifier": Tool(id="magnifier", label="a magnifying glass", use="inspect clues", safe=True, tags={"detective"}),
    "notebook": Tool(id="notebook", label="a notebook", use="write down clues", safe=True, tags={"detective"}),
}

CURATED = [
    StoryParams(setting="wooded", mystery="missing_key", tool="magnifier", helper="Mina", helper_gender="girl", detective="Leo", detective_gender="boy", adult="Mara"),
    StoryParams(setting="wooded", mystery="lost_hat", tool="notebook", helper="Nia", helper_gender="girl", detective="Owen", detective_gender="boy", adult="Mr. Cole"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A wooded teamwork mystery detective storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if args.tool and args.tool not in TOOLS:
        raise StoryError("Unknown tool.")

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, tool = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(["Mina", "Nia", "June", "Pip"])
    detective = args.detective or rng.choice(["Leo", "Owen", "Ada", "Finn"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    adult = args.adult or rng.choice(["Mara", "Mr. Cole", "Aunt Joy"])
    return StoryParams(setting=setting, mystery=mystery, tool=tool, helper=helper, helper_gender=helper_gender, detective=detective, detective_gender=detective_gender, adult=adult)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.tool not in TOOLS:
        raise StoryError("Invalid params.")
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts_from_world(world),
        story_qa=story_qa_from_world(world),
        world_qa=world_qa_from_world(world),
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


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "wooded"), asp.fact("mystery", "missing_key"), asp.fact("mystery", "lost_hat")]
    lines.append(asp.fact("tool", "magnifier"))
    lines.append(asp.fact("tool", "notebook"))
    lines.append(asp.fact("safe", "magnifier"))
    lines.append(asp.fact("safe", "notebook"))
    lines.append(asp.fact("hidden_in_woods", "missing_key"))
    lines.append(asp.fact("hidden_in_woods", "lost_hat"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,M,T) :- setting(S), mystery(M), tool(T), hidden_in_woods(M), safe(T).
solves(M) :- valid(_,M,_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python gates.")
        rc = 1
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            sample = generate(CURATED[0])
            emit(sample, trace=False, qa=False)
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: ASP parity and story generation smoke test passed.")
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, m, t) for s in SETTINGS for m in MYSTERIES for t in TOOLS if reasonableness(s, m, t)]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show solves/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3.\n#show solves/1."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx + 1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
