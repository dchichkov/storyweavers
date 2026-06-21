#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cave_equity_repetition_misunderstanding_bad_ending_pirate.py
=============================================================================================

A small pirate-themed storyworld about a cave, a promise of equity, repeated
misunderstandings, and a bad ending when the wrong choice keeps happening.

The world simulates:
- a crew with typed entities
- physical meters and emotional memes
- repetition that makes trouble grow
- misunderstanding that twists intentions into conflict
- a bad ending where the cave claim is lost after the crew ignores the warning

The story stays child-facing, concrete, and state-driven.
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
METER_REPEAT = "repeat"
METER_DAMAGE = "damage"
METER_DUST = "dust"


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
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "captain"}
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


@dataclass
class Setting:
    id: str
    place: str
    dark_spot: str
    echo_word: str
    mood: str
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
class Goal:
    id: str
    phrase: str
    promise: str
    equity_word: str
    split_word: str
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Confusion:
    id: str
    misunderstanding: str
    repeated_line: str
    warning: str
    consequence: str
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
class Outcome:
    id: str
    intensity: int
    damage: int
    ending: str
    fail_text: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    crew = world.get("crew")
    cave = world.get("cave")
    if crew.meters[METER_REPEAT] < 2:
        return out
    sig = ("repeat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cave.meters[METER_DAMAGE] += 1
    crew.memes["frustration"] += 1
    out.append("The same mistake echoed again, and the cave floor broke a little more.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    if world.get("captain").memes["confused"] < THRESHOLD:
        return out
    sig = ("misunderstanding",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("crew").memes["tension"] += 1
    out.append("Nobody understood the plan the same way twice.")
    return out


CAUSAL_RULES = [
    Rule("repeat", _r_repeat),
    Rule("misunderstanding", _r_misunderstanding),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate cave equity storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--confusion", choices=CONFUSIONS)
    ap.add_argument("--outcome", choices=OUTCOMES)
    ap.add_argument("--name", choices=CREW_NAMES)
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for gid in GOALS:
            for cid in CONFUSIONS:
                for oid in OUTCOMES:
                    if setting.dark_spot and GOALS[gid].equity_word:
                        combos.append((sid, gid, cid, oid))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for cid in CONFUSIONS:
        lines.append(asp.fact("confusion", cid))
    for oid in OUTCOMES:
        lines.append(asp.fact("outcome", oid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,G,C,O) :- setting(S), goal(G), confusion(C), outcome(O).
repeated :- repeat_count(N), N >= 2.
misunderstood :- confused(C), confusion(C).
bad_end(O) :- outcome(O), damage(O,D), D >= 2.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


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
    return "\n".join(lines)


def explain_rejection(_: str = "") -> str:
    return "(No story: this setup does not support the cave-and-equity conflict.)"


def _pick_name(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["boy", "girl"])
    pool = BOY_NAMES if gender == "boy" else GIRL_NAMES
    return rng.choice(pool), gender


@dataclass
class StoryParams:
    setting: str
    goal: str
    confusion: str
    outcome: str
    name: str = ""
    seed: Optional[int] = None
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting or args.goal or args.confusion or args.outcome:
        combos = [
            c for c in combos
            if (args.setting is None or c[0] == args.setting)
            and (args.goal is None or c[1] == args.goal)
            and (args.confusion is None or c[2] == args.confusion)
            and (args.outcome is None or c[3] == args.outcome)
        ]
    if not combos:
        raise StoryError(explain_rejection())
    setting, goal, confusion, outcome = rng.choice(sorted(combos))
    name = args.name or rng.choice(CREW_NAMES)
    return StoryParams(
        setting=setting,
        goal=goal,
        confusion=confusion,
        outcome=outcome,
        name=name,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate story that uses the words "{f["setting_word"]}" and "{f["goal_word"]}" and has a repeated warning.',
        f"Tell a pirate tale where {f['captain'].id} keeps misunderstanding the same warning in the {f['setting_word']}, and the choice leads to a bad ending.",
        f'Write a short story with a cave, a promise of fairness, repeated mistakes, and a sad ending at sea or in a cave.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cap = f["captain"]
    crew = f["crew"]
    cave = f["cave"]
    qa = [
        ("What was the story about?",
         f"It was about {cap.id} and the crew in a cave, where they tried to make things fair and ended up in trouble."),
        ("Why did the warning keep coming back?",
         f"The warning kept coming back because the same plan was repeated again and again. Each time, the crew misunderstood it a little more."),
        ("What went wrong in the cave?",
         f"They thought they were being fair, but they were not listening to the real warning. That misunderstanding made the cave break and lose its safe shape."),
    ]
    if f["outcome"] == "bad":
        qa.append((
            "How did the story end?",
            f"It ended badly. The cave was damaged, the crew felt ashamed, and the chance to keep the place fair was lost."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a cave?",
         "A cave is a dark space in rock or earth where people can go inside, but it can be dangerous if the walls are weak."),
        ("What does equity mean?",
         "Equity means being fair in a way that gives people what they need, not just the same thing to everyone."),
        ("What is a misunderstanding?",
         "A misunderstanding happens when people do not take the same meaning from the same words, so they act on the wrong idea."),
    ]


SETTINGS = {
    "harbor": Setting("harbor", "the harbor", "the cave mouth", "echo", "salt and rope"),
    "island": Setting("island", "the island shore", "the cave tunnel", "echo", "wind and tide"),
    "reef": Setting("reef", "the reef path", "the cave hollow", "echo", "foam and stone"),
}

GOALS = {
    "equity": Goal("equity", "equity for the cave claim", "let every sailor have a fair turn", "equity", "share"),
    "share": Goal("share", "a fair share of the treasure", "split the gold right down the middle", "equity", "share"),
}

CONFUSIONS = {
    "repeat": Confusion("repeat", "the captain kept saying the same thing", "fair, fair, fair", "That is not what I meant!", "the crew kept guessing wrong"),
    "echo": Confusion("echo", "the cave echoed the words back badly", "fair, fare, fear", "We heard it wrong!", "the words came back twisted"),
}

OUTCOMES = {
    "bad": Outcome("bad", 2, 2, "bad ending", "failed to keep the cave safe"),
    "worse": Outcome("worse", 3, 3, "worse ending", "lost the cave to the damage"),
}

CREW_NAMES = ["Mara", "Finn", "Jory", "Lina", "Pip", "Nell"]
BOY_NAMES = ["Finn", "Jory", "Pip", "Theo"]
GIRL_NAMES = ["Mara", "Lina", "Nell", "Ada"]


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS or params.goal not in GOALS or params.confusion not in CONFUSIONS or params.outcome not in OUTCOMES:
        raise StoryError("invalid params")
    world = World()
    setting = SETTINGS[params.setting]
    goal = GOALS[params.goal]
    confusion = CONFUSIONS[params.confusion]
    outcome = OUTCOMES[params.outcome]

    captain = world.add(Entity(id=params.name or "Mara", kind="character", type="girl", role="captain"))
    crew = world.add(Entity(id="crew", kind="character", type="thing", role="crew"))
    cave = world.add(Entity(id="cave", kind="thing", type="thing", label="the cave"))
    captain.memes["confused"] = 0.0
    captain.meters[METER_REPEAT] = 0.0

    world.say(f"On the {setting.place}, {captain.id} led the crew to {setting.dark_spot}.")
    world.say(f'They whispered about {goal.phrase}, because "{goal.promise}" sounded kind.')
    world.say(f'But the cave kept answering back with its echo: "{confusion.repeated_line}."')

    world.para()
    captain.meters[METER_REPEAT] += 1
    crew.memes["confused"] += 1
    world.say(f"{captain.id} tried again. {confusion.warning}")
    world.say(f"{captain.id} repeated the plan anyway, and the crew nodded without understanding.")

    world.para()
    captain.meters[METER_REPEAT] += 1
    crew.memes["confused"] += 1
    propagate(world, narrate=False)
    world.say(f"{confusion.misunderstanding.capitalize()}, and the words came back wrong once more.")
    world.say(f"{captain.id} said the same promise again, but the others heard only a half-sense of it.")

    world.para()
    cave.meters[METER_DAMAGE] += outcome.damage
    cave.meters[METER_DUST] += 1
    crew.memes["regret"] += 1
    world.say(f"In the end, the {outcome.ending} arrived after too many repeats.")
    world.say(f"{outcome.fail_text.capitalize()}, and the cave mouth crumbled with a dusty groan.")
    world.say(f"The crew sailed away, and the dream of equity in that cave was lost.")

    world.facts.update(
        captain=captain,
        crew=crew,
        cave=cave,
        setting_word=setting.place,
        goal_word=goal.equity_word,
        outcome=outcome.id,
    )
    return world


def generate(params: StoryParams) -> StorySample:
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


CURATED = [
    StoryParams(setting="harbor", goal="equity", confusion="repeat", outcome="bad", name="Mara", seed=1),
    StoryParams(setting="island", goal="share", confusion="echo", outcome="worse", name="Finn", seed=2),
]


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH in valid combos")
        return 1
    # smoke test a normal generation
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as exc:  # pragma: no cover - defensive
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: ASP parity and story generation verified ({len(clingo_set)} combos).")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible stories")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
