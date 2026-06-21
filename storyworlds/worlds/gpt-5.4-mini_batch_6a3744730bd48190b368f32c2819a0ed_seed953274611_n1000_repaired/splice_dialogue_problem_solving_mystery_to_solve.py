#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/splice_dialogue_problem_solving_mystery_to_solve.py
====================================================================================

A tiny bedtime storyworld about a child solving a small mystery with dialogue,
careful thinking, and a useful splice.

Premise
-------
A child and a calm helper hear a strange bedtime riddle in the house:
the story banner, a paper lantern string, or a ribbon has split, and a
missing join must be mended before the night can feel peaceful again.

The world stays small on purpose. It uses:
- typed entities with physical meters and emotional memes,
- a forward-chained causal model,
- a reasonableness gate,
- an inline ASP twin,
- story-grounded and world-knowledge Q&A.

The seed word is "splice", and the bedtime tone keeps the language gentle,
concrete, and child-facing.
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    quiet_detail: str
    mystery_line: str
    mood: str
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
class MysteryObject:
    id: str
    label: str
    phrase: str
    hint: str
    problem: str
    solution: str
    makes_mystery: bool = False
    fixable: bool = True
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
class Fix:
    id: str
    label: str
    phrase: str
    method: str
    power: int
    sense: int
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
        return clone


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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["broken"] < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["worry"] += 1
        out.append("__mystery__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("fixed"):
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("relief", "social", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def reasonableness_gate(setting: Setting, obj: MysteryObject, fix: Fix) -> bool:
    return obj.fixable and obj.makes_mystery and fix.sense >= 2 and fix.power >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for oid, obj in OBJECTS.items():
            for fid, fix in FIXES.items():
                if reasonableness_gate(setting, obj, fix):
                    combos.append((sid, oid, fid))
    return combos


def choose_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options), gender


def tell(setting: Setting, obj: MysteryObject, fix: Fix, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str, seed_word: str = "splice") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper",
                              label="the helper", traits=["calm", "kind"]))
    mystery = world.add(Entity(id="mystery", kind="thing", type="thing", label=obj.label))
    tool = world.add(Entity(id="tool", kind="thing", type="thing", label=fix.label))
    child.memes["curiosity"] += 1
    helper.memes["calm"] += 1

    world.say(f"At bedtime, {child.id} and {helper.id} sat in {setting.place}. {setting.quiet_detail}")
    world.say(f'The room felt soft and sleepy, but one little thing was wrong: {setting.mystery_line}')

    world.para()
    world.say(f'"Why is it doing that?" {child.id} whispered.')
    world.say(f'"It looks like something needs a {seed_word}," {helper.id} said gently.')
    child.memes["curiosity"] += 1
    helper.memes["thinking"] += 1

    world.para()
    world.say(f'{child.id} peered closer. "{obj.hint}," {child.pronoun()} said.')
    world.say(f'"Good eye," {helper.id} replied. "{obj.problem}"')
    child.memes["confidence"] += 1
    mystery.meters["broken"] += 1

    propagate(world, narrate=False)

    world.para()
    world.say(f'"So what should we do?" {child.id} asked.')
    world.say(f'"We can {fix.method}," {helper.id} answered. "{obj.solution}"')
    world.say(f'Together they used the {fix.label} to {seed_word} the join.')
    mystery.meters["broken"] = 0.0
    world.facts["fixed"] = True
    propagate(world, narrate=False)

    world.para()
    world.say(f'The little join held tight again, and the room grew calm.')
    world.say(f'{child.id} smiled and hugged {helper.id}. "{obj.phrase} is all better," {child.pronoun()} said.')
    world.say(f'"Yes," {helper.id} said. "A small mystery can be solved when we look, ask, and try the kind fix."')

    world.facts.update(
        setting=setting,
        object=obj,
        fix=fix,
        child=child,
        helper=helper,
        seed_word=seed_word,
        outcome="fixed",
    )
    return world


SETTINGS = {
    "nursery": Setting(
        id="nursery",
        place="the nursery",
        quiet_detail="A moon lamp made a pale circle on the rug, and a teddy bear watched from the pillow.",
        mystery_line="one ribbon on the story banner had come loose and hung like a sleepy noodle.",
        mood="sleepy",
        tags={"bedtime", "banner"},
    ),
    "bedroom": Setting(
        id="bedroom",
        place="the bedroom",
        quiet_detail="A little star light glowed near the bed, and the blanket was tucked in a neat square.",
        mystery_line="the music box string had a tiny split, and it could not wind up right.",
        mood="calm",
        tags={"bedtime", "music_box"},
    ),
    "hall": Setting(
        id="hall",
        place="the hallway",
        quiet_detail="The hall light was dim, and the shadows stayed still on the wall.",
        mystery_line="a paper lantern string had a frayed place that made it wobble in the breeze.",
        mood="still",
        tags={"bedtime", "lantern"},
    ),
}

OBJECTS = {
    "ribbon": MysteryObject(
        id="ribbon",
        label="the ribbon",
        phrase="the ribbon",
        hint="It has one part that flops down and one part that stays stuck",
        problem="The ribbon needs a neat splice so it can hang straight again.",
        solution="Then the banner can stay up without slipping.",
        makes_mystery=True,
        fixable=True,
        tags={"ribbon", "splice"},
    ),
    "string": MysteryObject(
        id="string",
        label="the string",
        phrase="the string",
        hint="It has a tiny split right near the knot",
        problem="The string needs a careful splice so the music box can wind again.",
        solution="Then the tune can play softly before sleep.",
        makes_mystery=True,
        fixable=True,
        tags={"string", "splice", "music_box"},
    ),
    "lantern_cord": MysteryObject(
        id="lantern_cord",
        label="the lantern cord",
        phrase="the lantern cord",
        hint="One end is frayed, as if it got tired and split apart",
        problem="The cord needs a safe splice so the lantern can hang still.",
        solution="Then the little light can glow without wobbling.",
        makes_mystery=True,
        fixable=True,
        tags={"lantern", "splice"},
    ),
}

FIXES = {
    "tape": Fix(
        id="tape",
        label="the tape",
        phrase="some tape",
        method="make a neat splice with tape",
        power=2,
        sense=3,
        tags={"splice"},
    ),
    "knot": Fix(
        id="knot",
        label="the thread",
        phrase="some thread",
        method="tie a small knot and splice the ends together",
        power=2,
        sense=3,
        tags={"splice"},
    ),
    "clip": Fix(
        id="clip",
        label="the little clip",
        phrase="a little clip",
        method="clip the ends together for a careful splice",
        power=1,
        sense=2,
        tags={"splice"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Ella", "Ruby"]
BOY_NAMES = ["Theo", "Noah", "Finn", "Eli", "Milo", "Ben"]


@dataclass
class StoryParams:
    setting: str
    object: str
    fix: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime mystery storyworld about a small splice.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def explain_rejection(obj: MysteryObject, fix: Fix) -> str:
    return f"(No story: this mystery can't be solved reasonably with {fix.label} on {obj.label}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object is None or c[1] == args.object)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj, fix = rng.choice(sorted(combos))
    child_name = args.child_name
    child_gender = args.child_gender
    if child_name is None:
        child_name, child_gender = choose_name(rng)
    if child_gender is None:
        child_gender = rng.choice(["girl", "boy"])
    helper_name = args.helper_name or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != child_name])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        setting=setting,
        object=obj,
        fix=fix,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a child that includes the word "{f["seed_word"]}" and a small mystery to solve.',
        f"Tell a gentle story where {f['child'].id} asks what is wrong, and {f['helper'].id} helps solve it with a calm explanation.",
        f"Write a story with dialogue, a problem, and a careful fix that makes the sleepy room peaceful again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    obj = f["object"]
    fix = f["fix"]
    setting = f["setting"]
    return [
        QAItem(
            question="What was the mystery?",
            answer=f"It was a small problem with {obj.phrase} in {setting.place}. One part had split or come loose, so it needed a splice to feel right again.",
        ),
        QAItem(
            question="How did they solve it?",
            answer=f"{helper.id} suggested a calm fix, and together they used {fix.label} to make a neat splice. That careful work held the join together.",
        ),
        QAItem(
            question=f"Why did {child.id} feel better at the end?",
            answer=f"{child.id} felt better because the broken join was fixed and the room was quiet again. The mystery had an answer, so bedtime could be peaceful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does splice mean?",
            answer="To splice something means to join broken ends together neatly so it works again.",
        ),
        QAItem(
            question="Why do people ask questions when something seems odd?",
            answer="Questions help people notice clues and solve a problem step by step. That is how a mystery turns into an answer.",
        ),
        QAItem(
            question="What should you do before fixing something fragile?",
            answer="You should look closely, go slowly, and choose a gentle way to fix it. Careful hands help keep things safe.",
        ),
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


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.object not in OBJECTS:
        raise StoryError("Unknown object.")
    if params.fix not in FIXES:
        raise StoryError("Unknown fix.")
    setting = SETTINGS[params.setting]
    obj = OBJECTS[params.object]
    fix = FIXES[params.fix]
    if not reasonableness_gate(setting, obj, fix):
        raise StoryError(explain_rejection(obj, fix))
    world = tell(setting, obj, fix, params.child_name, params.child_gender, params.helper_name, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(setting="nursery", object="ribbon", fix="tape", child_name="Mia", child_gender="girl", helper_name="Luna", helper_gender="girl"),
    StoryParams(setting="bedroom", object="string", fix="knot", child_name="Theo", child_gender="boy", helper_name="Nora", helper_gender="girl"),
    StoryParams(setting="hall", object="lantern_cord", fix="clip", child_name="Eli", child_gender="boy", helper_name="Ivy", helper_gender="girl"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.makes_mystery:
            lines.append(asp.fact("mystery_object", oid))
        if obj.fixable:
            lines.append(asp.fact("fixable", oid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O,F) :- setting(S), mystery_object(O), fix(F), fixable(O), sense(F,N), sense_min(M), N >= M, power(F,P), P >= 1.
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
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, qa=True)
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, o, f in asp_valid_combos():
            print(f"  {s:10} {o:12} {f}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
