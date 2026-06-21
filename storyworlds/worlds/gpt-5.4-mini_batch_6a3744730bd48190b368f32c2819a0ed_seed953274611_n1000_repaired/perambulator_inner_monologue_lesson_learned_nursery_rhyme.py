#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/perambulator_inner_monologue_lesson_learned_nursery_rhyme.py
===========================================================================================

A tiny standalone storyworld: a child takes a perambulator on a rhyming outing,
gets a small scare when a wheel sticks, thinks through what to do, asks for help,
and learns a gentle lesson. The prose is nursery-rhyme-ish, but the events are
state-driven rather than a frozen template.

The world includes:
- a perambulator
- inner monologue beats
- a lesson learned beat
- child-facing, complete stories with a clear turn and ending image

Run it:
    python storyworlds/worlds/gpt-5.4-mini/perambulator_inner_monologue_lesson_learned_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4-mini/perambulator_inner_monologue_lesson_learned_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/perambulator_inner_monologue_lesson_learned_nursery_rhyme.py --verify
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
    rhyme_line: str
    weather: str = ""
    indoors: bool = False
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
class Traveler:
    id: str
    label: str
    can_roll: bool = True
    causes_stick: bool = False
    smooth: bool = False
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
class Fix:
    id: str
    label: str
    sense: int
    power: int
    action: str
    fail: str
    result: str
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
    traveler: str
    fix: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


def _r_worry(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters["stuck"] >= THRESHOLD and ("worry",) not in world.fired:
        world.fired.add(("worry",))
        child.memes["worry"] += 1
        out.append("__inner__")
    return out


def _r_help(world: World) -> list[str]:
    out = []
    child = world.get("child")
    parent = world.get("parent")
    if child.meters["stuck"] >= THRESHOLD and parent.meters["helping"] >= THRESHOLD:
        sig = ("help",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["stuck"] = 0.0
            child.memes["relief"] += 1
            parent.memes["care"] += 1
            out.append("__helped__")
    return out


RULES = [Rule("worry", _r_worry), Rule("help", _r_help)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def traveltime(setting: Setting) -> str:
    return setting.rhyme_line


def predict_stick(world: World, traveler: Traveler) -> bool:
    sim = world.copy()
    sim.get("pram").meters["stuck"] += 1 if traveler.causes_stick else 0
    propagate(sim, narrate=False)
    return sim.get("pram").meters["stuck"] >= THRESHOLD


def trip(world: World, child: Entity, pram: Entity, setting: Setting, traveler: Traveler) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Down the lane in {setting.place}, {child.id} went with a happy spring, "
        f"pushing the {traveler.label} that hummed like a songbird's wing."
    )
    world.say(traveltime(setting))
    world.say(
        f"{child.id} felt clever and proud, as bright as morning dew, "
        f"for the {traveler.label} rolled nicely, tidy, shiny, and new."
    )


def snag(world: World, child: Entity, pram: Entity, traveler: Traveler) -> None:
    pram.meters["stuck"] += 1
    child.memes["surprise"] += 1
    world.say(
        f"Then oh! the {traveler.label} gave a stop, one wheel in the crack, "
        f"and the little roll went bumpy-bump, then would not come back."
    )


def inner_voice(world: World, child: Entity, pram: Entity, traveler: Traveler) -> None:
    child.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} thought, 'If I tug and yank, the wheel may squeal and groan. "
        f"I must not make a muddle all alone.'"
    )
    world.say(
        f"'I should ask for help,' {child.id} thought, 'for two hands are kinder than one.'"
    )


def call_help(world: World, parent: Entity, child: Entity) -> None:
    parent.meters["helping"] += 1
    world.say(
        f'Then {child.id} called, "Please help me, {parent.id}! The {label_pram} is stuck!"'
    )


def free_pram(world: World, parent: Entity, child: Entity, pram: Entity, fix: Fix) -> None:
    parent.memes["care"] += 1
    child.meters["stuck"] = 0.0
    world.say(
        f"{parent.id} came with a calm little grin and {fix.action}."
    )
    world.say(
        f"The {fix.label} {fix.result}, and the {label_pram} rolled on so light."
    )


def lesson(world: World, child: Entity, parent: Entity, pram: Entity) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} nodded and learned the tune: if something sticks or sways, "
        f"stop, think, and ask a grown-up in the proper ways."
    )
    world.say(
        f"So off they went again, the {label_pram} straight and right, "
        f"with {child.id} singing softly in the bright, kind light."
    )


def label_pram() -> str:
    return "perambulator"


SETTINGS = {
    "garden_path": Setting(
        id="garden_path",
        place="the garden path",
        rhyme_line="The daisies dipped and the robins trilled, while the sun on the stones was spilled.",
        weather="bright",
    ),
    "brick_walk": Setting(
        id="brick_walk",
        place="the brick walk",
        rhyme_line="The little bricks went clickety-click, like a drumbeat fast and quick.",
        weather="clear",
    ),
    "porch_lane": Setting(
        id="porch_lane",
        place="the porch lane",
        rhyme_line="The porch bells chimed and the breezes blew, as the day in silver sparkles grew.",
        weather="mild",
    ),
}

TRAVELERS = {
    "pram": Traveler(
        id="pram",
        label="perambulator",
        can_roll=True,
        causes_stick=True,
        smooth=False,
        tags={"perambulator"},
    ),
    "perambulator": Traveler(
        id="perambulator",
        label="perambulator",
        can_roll=True,
        causes_stick=True,
        smooth=False,
        tags={"perambulator"},
    ),
}

FIXES = {
    "lift_and_turn": Fix(
        id="lift_and_turn",
        label="gentle lift-and-turn",
        sense=3,
        power=3,
        action="lifted the front a little and turned the wheel free",
        fail="lifted and turned, but the crack held fast",
        result="gave a merry little jerk and spun again",
        tags={"help", "wheel"},
    ),
    "pull_back": Fix(
        id="pull_back",
        label="slow pull-back",
        sense=2,
        power=2,
        action="pulled the perambulator back a tiny bit and rocked it loose",
        fail="pulled back, but the wheel was wedged too tight",
        result="woke from its wedged-up nap and rolled on",
        tags={"help", "wheel"},
    ),
    "oil_and_shift": Fix(
        id="oil_and_shift",
        label="drop of oil",
        sense=3,
        power=3,
        action="put a drop of oil on the axle and shifted the wheel just so",
        fail="tried a drop of oil, but the path was still too rough",
        result="slipped forward with a soft, happy swish",
        tags={"help", "wheel"},
    ),
}

NAMES_GIRL = ["Mina", "Lily", "Nora", "Poppy", "Ella", "Wren"]
NAMES_BOY = ["Theo", "Finn", "Ollie", "Robin", "Jasper", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TRAVELERS:
            for f in FIXES:
                combos.append((s, t, f))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny nursery-rhyme storyworld about a perambulator, an inner monologue, and a lesson learned."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--traveler", choices=TRAVELERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.traveler is None or c[1] == args.traveler)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, traveler, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, traveler=traveler, fix=fix,
                       child_name=name, child_gender=gender,
                       parent_name=parent, parent_gender="woman" if parent == "mother" else "man")


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    parent = world.add(Entity(id=params.parent_name, kind="character", type=params.parent_gender, role="parent", label="the parent"))
    setting = SETTINGS[params.setting]
    traveler = TRAVELERS[params.traveler]
    fix = FIXES[params.fix]
    pram = world.add(Entity(id="pram", type="thing", label=traveler.label, role="object"))
    world.facts.update(child=child, parent=parent, setting=setting, traveler=traveler, fix=fix, pram=pram)

    trip(world, child, pram, setting, traveler)
    world.para()
    snag(world, child, pram, traveler)
    inner_voice(world, child, pram, traveler)
    call_help(world, parent, child)
    world.para()
    free_pram(world, parent, child, pram, fix)
    lesson(world, child, parent, pram)
    world.facts["outcome"] = "learned"
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    return [
        "Write a nursery-rhyme-style story that includes the word 'perambulator' and shows a child thinking to themself before asking for help.",
        f"Tell a gentle rhyme about {f['child'].id}, a perambulator, and a small problem on {f['setting'].place} that gets solved kindly.",
        "Write a short child-facing story with an inner monologue beat and a lesson learned beat, ending in a safe, rolling scene.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, setting, fix = f["child"], f["parent"], f["setting"], f["fix"]
    return [
        ("What was the child pushing?", "The child was pushing a perambulator. It was the little wheeled carriage in the story."),
        ("What happened when the wheel stuck?", "The perambulator stopped moving for a moment. The child noticed the problem and thought carefully before acting."),
        ("What did the child learn?", "The child learned to stop, think, and ask a grown-up for help when something gets stuck. That made the ending safe and happy."),
        (f"Who helped {child.id}?", f"{parent.id} helped {child.id} with a calm fix, and the perambulator rolled again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a perambulator?", "A perambulator is a baby carriage or pram that rolls on wheels."),
        ("Why should you ask for help when a wheel is stuck?", "A grown-up can help in a safe way. That keeps the child from pulling too hard or making the problem worse."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T,F) :- setting(S), traveler(T), fix(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TRAVELERS:
        lines.append(asp.fact("traveler", t))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python disagree.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, traveler=None, fix=None, name=None, gender=None, parent=None), random.Random(7)))
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


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
    StoryParams(setting="garden_path", traveler="pram", fix="lift_and_turn", child_name="Mina", child_gender="girl", parent_name="Mum", parent_gender="woman"),
    StoryParams(setting="brick_walk", traveler="perambulator", fix="pull_back", child_name="Theo", child_gender="boy", parent_name="Dad", parent_gender="man"),
    StoryParams(setting="porch_lane", traveler="pram", fix="oil_and_shift", child_name="Nora", child_gender="girl", parent_name="Mother", parent_gender="woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{t}" for t in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
