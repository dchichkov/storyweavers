#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/force_gaze_chamomile_curiosity_repetition_transformation_slice.py
===============================================================================================

A small slice-of-life storyworld about a child, a tiny household ritual, and a
gentle transformation driven by curiosity and repetition.

Seed words: force, gaze, chamomile
Features: curiosity, repetition, transformation
Style: slice of life
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
class Ritual:
    id: str
    action: str
    repeated_action: str
    curiosity: str
    transform: str
    ingredient: str
    vessel: str
    warm_word: str
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
class Result:
    id: str
    phrase: str
    effect: str
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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    mug = world.entities.get("mug")
    if not child or not mug:
        return out
    if child.memes["curiosity"] >= THRESHOLD and child.meters["tries"] >= 2 and ("repeat", "child") not in world.fired:
        world.fired.add(("repeat", "child"))
        child.memes["familiar"] += 1
        mug.meters["steeped"] += 1
        out.append("Each time, the chamomile looked a little softer and a little calmer.")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    mug = world.entities.get("mug")
    child = world.entities.get("child")
    kettle = world.entities.get("kettle")
    if not mug or not child:
        return out
    if mug.meters["steeped"] >= 1 and ("transform", "mug") not in world.fired:
        world.fired.add(("transform", "mug"))
        mug.meters["warm"] += 1
        child.memes["calm"] += 1
        if kettle:
            kettle.meters["steam"] += 1
        out.append("At last, the tea changed color and gave off a gentle, sleepy smell.")
    return out


def _r_bond(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    grownup = world.entities.get("grownup")
    if not child or not grownup:
        return out
    if child.memes["calm"] >= THRESHOLD and ("bond", "child") not in world.fired:
        world.fired.add(("bond", "child"))
        grownup.memes["pride"] += 1
        child.memes["trust"] += 1
        out.append("The room felt smaller in the best way, like a shared secret made of steam.")
    return out


CAUSAL_RULES = [
    Rule("repetition", _r_repetition),
    Rule("transformation", _r_transformation),
    Rule("bond", _r_bond),
]


def reasonableness_gate(setting: Setting, ritual: Ritual, result: Result) -> bool:
    return ritual.ingredient == "chamomile" and "tea" in ritual.tags and "quiet" in setting.affordances and result.id == "sleepy"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for rid, ritual in RITUALS.items():
            for oid, result in RESULTS.items():
                if reasonableness_gate(setting, ritual, result):
                    combos.append((sid, rid, oid))
    return combos


def predict(world: World) -> dict:
    sim = world.copy()
    _steep(sim, narrate=False)
    return {
        "steeped": sim.get("mug").meters["steeped"] >= THRESHOLD,
        "calm": sim.get("child").memes["calm"] >= THRESHOLD,
    }


def _steep(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    mug = world.get("mug")
    kettle = world.get("kettle")
    child.meters["tries"] += 1
    child.memes["curiosity"] += 1
    mug.meters["steeped"] += 1
    if kettle:
        kettle.meters["boiled"] += 1
    world.say(
        f"{child.id} watched the chamomile leaves swirl in the mug and tried again, "
        f"carefully, with {child.pronoun('possessive')} elbows tucked in."
    )
    propagate(world, narrate=narrate)


def tell(setting: Setting, ritual: Ritual, result: Result,
         child_name: str = "Mina", child_gender: str = "girl",
         grownup_name: str = "Parent", grownup_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=["curious"]))
    grownup = world.add(Entity(id=grownup_name, kind="character", type=grownup_gender, role="grownup"))
    mug = world.add(Entity(id="mug", type="mug", label="mug"))
    kettle = world.add(Entity(id="kettle", type="kettle", label="kettle"))
    room = world.add(Entity(id="room", type="room", label=setting.place))

    child.memes["curiosity"] = 1.0
    grownup.memes["patience"] = 1.0

    world.say(
        f"In the quiet kitchen, {child.id} stood on tiptoe beside the kettle and the mug."
    )
    world.say(
        f"{child.id} liked the small evening rule: warm water, a spoon, and {ritual.ingredient} to taste."
    )
    world.say(
        f'{child.id} said, "{ritual.curiosity}" and looked at the mug as if it might answer back.'
    )

    world.para()
    world.say(
        f"{child.id} asked to help, so {grownup.id} let {child.pronoun('object')} {ritual.action}."
    )
    world.say(
        f"Then {child.id} {ritual.repeated_action}, because once was not enough for {child.pronoun('possessive')} gaze."
    )
    _steep(world)

    world.para()
    pred = predict(world)
    if pred["steeped"]:
        world.say(
            f"{grownup.id} smiled at the tiny force of repetition, the way a careful stir could change a whole mug."
        )
    world.say(
        f"When the steam rose, {child.id} stopped looking away and watched the color change."
    )
    world.say(
        f"The chamomile turned soft gold and {result.effect}."
    )
    propagate(world)

    world.para()
    child.memes["joy"] += 1
    child.memes["calm"] += 1
    grownup.memes["calm"] += 1
    world.say(
        f"{grownup.id} poured a little into a second cup and said {result.phrase}."
    )
    world.say(
        f"{child.id} held the warm mug with both hands, and the whole kitchen felt gentler than before."
    )

    world.facts.update(
        child=child,
        grownup=grownup,
        ritual=ritual,
        result=result,
        setting=setting,
        room=room,
        mug=mug,
        kettle=kettle,
    )
    return world


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="the kitchen", affordances={"quiet", "tea"}),
    "window": Setting(id="window", place="the window seat", affordances={"quiet"}),
    "table": Setting(id="table", place="the little table", affordances={"quiet", "tea"}),
}

RITUALS = {
    "tea": Ritual(
        id="tea",
        action="measure the water",
        repeated_action="counted the spoonfuls again",
        curiosity="What does chamomile smell like when it gets warm?",
        transform="gentle sleep",
        ingredient="chamomile",
        vessel="mug",
        warm_word="warm",
        tags={"tea", "quiet", "chamomile", "curiosity", "repetition"},
    ),
    "bath": Ritual(
        id="bath",
        action="stir the cup",
        repeated_action="stirred the cup one more time",
        curiosity="Could the little flowers make the water softer?",
        transform="stillness",
        ingredient="chamomile",
        vessel="mug",
        warm_word="warm",
        tags={"tea", "quiet", "chamomile", "curiosity", "repetition"},
    ),
}

RESULTS = {
    "sleepy": Result(
        id="sleepy",
        phrase="That was just right",
        effect="looked sleepy and calm",
        tags={"transformation"},
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "June"]
BOY_NAMES = ["Evan", "Owen", "Milo", "Theo", "Finn"]
TRAITS = ["curious", "patient", "gentle", "careful"]


@dataclass
class StoryParams:
    setting: str
    ritual: str
    result: str
    name: str
    gender: str
    grownup_gender: str
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


def valid_name_gender(result: Result, gender: str) -> bool:
    return True


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny slice-of-life storyworld about chamomile and change.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ritual", choices=RITUALS)
    ap.add_argument("--result", choices=RESULTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup-gender", choices=["woman", "man"])
    ap.add_argument("--name")
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
    if args.setting and args.ritual and args.result:
        if not reasonableness_gate(SETTINGS[args.setting], RITUALS[args.ritual], RESULTS[args.result]):
            raise StoryError("This combination does not fit the tiny chamomile kitchen story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.ritual is None or c[1] == args.ritual)
              and (args.result is None or c[2] == args.result)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, ritual, result = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grownup_gender = args.grownup_gender or rng.choice(["woman", "man"])
    return StoryParams(setting=setting, ritual=ritual, result=result, name=name, gender=gender, grownup_gender=grownup_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child that includes the words "force", "gaze", and "chamomile".',
        f"Tell a quiet kitchen story about {f['child'].id} noticing chamomile, asking curious questions, and changing the mood by repeating a tiny ritual.",
        "Write a gentle story where repetition turns an ordinary warm drink into a calm evening.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, grownup, ritual = f["child"], f["grownup"], f["ritual"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {grownup.id} in a quiet kitchen. The little moment begins with chamomile and grows into a calm evening."),
        ("Why did the child keep doing the same thing again?",
         f"{child.id} was curious and wanted to know what would happen next. Repetition mattered because the second try made the drink change more clearly."),
        ("How did the story change by the end?",
         f"The warm mug looked and felt different by the end, and everyone was calmer. The tiny force of repetition turned an ordinary cup into a gentle bedtime moment."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is chamomile?",
         "Chamomile is a small flowering herb that people often use to make a gentle tea. It has a soft smell and is often linked with calm evenings."),
        ("What does curiosity mean?",
         "Curiosity means wanting to know more and asking questions. A curious person looks closely because they want to understand."),
        ("What is repetition?",
         "Repetition means doing something again and again. Sometimes repetition helps you notice a change that one try alone would miss."),
        ("What is transformation?",
         "Transformation means something changes into a new form or feels different than before. Even a small change can make a big difference in a story."),
        ("What does force mean in a quiet story?",
         "Force can mean a steady push or pressure that helps something move or change. In a slice-of-life story, that can be the gentle push of habit and attention."),
        ("What is a gaze?",
         "A gaze is a steady look. When someone gazes at something, they watch it carefully and for a little while."),
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, r in RITUALS.items():
        lines.append(asp.fact("ritual", rid))
        if "chamomile" in r.tags:
            lines.append(asp.fact("uses", rid, "chamomile"))
    for oid in RESULTS:
        lines.append(asp.fact("result", oid))
    return "\n".join(lines)


ASP_RULES = r"""
good(S,R,O) :- setting(S), ritual(R), result(O), uses(R, chamomile).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good/3."))
    return sorted(set(asp.atoms(model, "good")))


def asp_verify() -> int:
    import io
    import contextlib
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        ok = False
    try:
        _ = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        sample = generate(StoryParams(setting="kitchen", ritual="tea", result="sleepy", name="Mina", gender="girl", grownup_gender="woman"))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        ok = False
    return 0 if ok else 1


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.ritual not in RITUALS or params.result not in RESULTS:
        raise StoryError("Invalid parameters.")
    if not reasonableness_gate(SETTINGS[params.setting], RITUALS[params.ritual], RESULTS[params.result]):
        raise StoryError("This storyworld only supports chamomile tea in a quiet setting.")
    world = tell(
        SETTINGS[params.setting],
        RITUALS[params.ritual],
        RESULTS[params.result],
        child_name=params.name,
        child_gender=params.gender,
        grownup_gender=params.grownup_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, r, o) for s in SETTINGS for r in RITUALS for o in RESULTS if reasonableness_gate(SETTINGS[s], RITUALS[r], RESULTS[o])]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [
            generate(StoryParams(setting="kitchen", ritual="tea", result="sleepy", name="Mina", gender="girl", grownup_gender="woman")),
        ]
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
