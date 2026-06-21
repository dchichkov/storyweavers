#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/recall_dance_studio_moral_value_heartwarming.py
===============================================================================

A small heartwarming storyworld set in a dance studio.

Premise:
- A child is preparing for a dance recital in a dance studio.
- A forgotten step or missed count creates a small worry.
- The child recalls a kind moral lesson: helping is more important than winning.
- With a gentle coach and a helpful friend, the group turns worry into teamwork.
- The ending proves the change through a warm, remembered moment.

This world includes the required word "recall", keeps the tone heartwarming, and
models state-driven changes in both meters and memes.
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
RECALL_MIN = 1.0


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
        female = {"girl", "mother", "woman", "coach"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"coach": "coach"}.get(self.type, self.type)
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
class StudioSetting:
    id: str
    place: str
    mirror: str
    floor: str
    music: str
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
class DanceRoutine:
    id: str
    name: str
    step: str
    counts: int
    risk: str
    lesson: str
    keyword: str = "recall"
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
class HelpAction:
    id: str
    skill: int
    warmth: int
    text: str
    fail: str
    qa_text: str
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
    routine: str
    helper: str
    child_name: str
    child_gender: str
    coach_gender: str
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


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    coach = world.entities.get("coach")
    if not child or not coach:
        return out
    if child.memes["worry"] < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    coach.memes["care"] += 1
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1)
    child.memes["trust"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("calm", "social", _r_calm)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for rid, routine in ROUTINES.items():
            for hid, helper in HELPS.items():
                if routine.keyword == "recall" and helper.skill >= 2:
                    combos.append((sid, rid, hid))
    return combos


def lesson_strength(routine: DanceRoutine) -> int:
    return routine.counts + 1


def helpful_enough(helper: HelpAction, routine: DanceRoutine) -> bool:
    return helper.skill >= lesson_strength(routine)


def predict(world: World, routine: DanceRoutine) -> dict:
    sim = world.copy()
    sim.get("child").memes["worry"] += 1
    propagate(sim, narrate=False)
    return {
        "worry": sim.get("child").memes["worry"],
        "trust": sim.get("child").memes["trust"],
    }


def introduce(world: World, child: Entity, coach: Entity, setting: StudioSetting, routine: DanceRoutine) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In the {setting.place}, {child.id} spun under the bright mirrors while "
        f"{coach.id} clapped softly to the music."
    )
    world.say(
        f"{child.id} loved practicing {routine.name}, and the whole room felt warm "
        f"with the steady beat."
    )


def miss_step(world: World, child: Entity, routine: DanceRoutine) -> None:
    child.memes["worry"] += 1
    child.meters["tired"] += 1
    world.say(
        f"At the tricky part, {child.id} missed a count and froze for a moment."
    )
    world.say(
        f"{child.id} wanted the turn to look perfect, but the mistake made the "
        f"studio suddenly feel very big."
    )


def recall_lesson(world: World, child: Entity, helper: Entity, routine: DanceRoutine) -> None:
    child.memes["recall"] += 1
    world.facts["recalled"] = True
    world.say(
        f"Then {child.id} stopped, took a breath, and tried to recall the kind "
        f"thing {helper.id} had said before."
    )
    world.say(
        f'"Helping is part of dancing," {child.id} remembered. '
        f'"We do better when we look after each other."'
    )


def offer_help(world: World, coach: Entity, helper: Entity, child: Entity, action: HelpAction) -> None:
    helper.memes["kindness"] += 1
    world.say(
        f"{coach.id} smiled and said {action.text}."
    )
    world.say(
        f"{helper.id} moved beside {child.id}, not in front of {child.id}, so the two "
        f"of them could practice together."
    )


def accept_help(world: World, child: Entity, helper: Entity, action: HelpAction) -> None:
    child.memes["trust"] += 1
    child.memes["joy"] += 1
    child.meters["steady"] += 1
    world.say(
        f"{child.id} nodded and let {helper.id} guide the first few steps."
    )
    world.say(
        f"With that gentle help, the dance became smooth again, and the music "
        f"felt friendly instead of scary."
    )


def ending(world: World, child: Entity, coach: Entity, helper: Entity, routine: DanceRoutine, action: HelpAction) -> None:
    world.say(
        f"By the end, {child.id} finished the routine with a bright smile, and "
        f"{coach.id} looked as proud as a sunbeam."
    )
    world.say(
        f"{child.id} {action.qa_text} {helper.id}, and the little team danced on, "
        f"warm, brave, and kind."
    )


def tell(setting: StudioSetting, routine: DanceRoutine, action: HelpAction,
         child_name: str, child_gender: str, coach_gender: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender,
                             label=child_name, role="dancer", traits=["young"]))
    coach = world.add(Entity(id="coach", kind="character", type=coach_gender,
                             label="the coach", role="coach"))
    helper = world.add(Entity(id="helper", kind="character", type="girl",
                              label="the helper", role="friend"))
    child.id = child_name
    child.label = child_name
    helper.id = HELPER_NAMES[0] if child_name != HELPER_NAMES[0] else HELPER_NAMES[1]
    helper.label = helper.id

    child.memes["trust"] = 0.0
    coach.memes["care"] = 1.0
    introduce(world, child, coach, setting, routine)
    world.para()
    miss_step(world, child, routine)
    recall_lesson(world, child, helper, routine)
    if helpful_enough(action, routine):
        offer_help(world, coach, helper, child, action)
        accept_help(world, child, helper, action)
    else:
        world.say("The help was too small to guide the dance, so they paused and tried again more slowly.")
        child.memes["worry"] += 1
    world.para()
    ending(world, child, coach, helper, routine, action)
    world.facts.update(setting=setting, routine=routine, action=action, child=child, coach=coach, helper=helper)
    return world


SETTINGS = {
    "dance_studio": StudioSetting(
        id="dance_studio",
        place="dance studio",
        mirror="tall mirrors",
        floor="springy floor",
        music="soft piano music",
        tags={"dance", "studio"},
    ),
}

ROUTINES = {
    "recital": DanceRoutine(
        id="recital",
        name="the recital dance",
        step="the spinning step",
        counts=4,
        risk="being left out",
        lesson="kindness matters more than being the best",
        tags={"recall", "moral"},
    ),
    "class_duet": DanceRoutine(
        id="class_duet",
        name="the duet",
        step="the tricky line step",
        counts=3,
        risk="losing the beat",
        lesson="sharing makes the music sweeter",
        tags={"recall", "moral"},
    ),
}

HELPS = {
    "counting": HelpAction(
        id="counting",
        skill=3,
        warmth=3,
        text="let's count it together from the start",
        fail="tried to hurry the count, but that would not have been enough",
        qa_text="kept dancing side by side with",
        tags={"help", "kind"},
    ),
    "gentle_hand": HelpAction(
        id="gentle_hand",
        skill=4,
        warmth=4,
        text="I can show you the step once, and then we can do it together",
        fail="gave a quick tip, but it still was not enough for the whole dance",
        qa_text="remembered to stay beside",
        tags={"help", "kind"},
    ),
}

HELPER_NAMES = ["Maya", "Noor", "Lina", "Sofia", "Ruby", "Ivy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming dance studio storyworld with recall and a moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--routine", choices=ROUTINES)
    ap.add_argument("--helper", choices=HELPS)
    ap.add_argument("--name", choices=HELPER_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--coach-gender", choices=["girl", "boy"])
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
              and (args.routine is None or c[1] == args.routine)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, routine, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    coach_gender = args.coach_gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(HELPER_NAMES)
    return StoryParams(setting=setting, routine=routine, helper=helper, child_name=child_name, child_gender=gender, coach_gender=coach_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    routine = f["routine"]
    return [
        f'Write a heartwarming story in a dance studio that includes the word "recall" and shows a moral value about helping.',
        f"Tell a gentle story where {f['child'].label} misses a step, recalls a kind lesson, and learns to work with a helper during {routine.name}.",
        f'Write a child-friendly story about a dance class where "recall" helps someone remember that kindness matters more than perfection.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    coach = f["coach"]
    routine = f["routine"]
    action = f["action"]
    return [
        ("Who is the story about?",
         f"It is about {child.label}, who was practicing {routine.name} in a dance studio with {coach.label} and {helper.label}."),
        ("What did {0} have to recall?".format(child.label),
         f"{child.label} had to recall the kind lesson that helping matters more than being perfect. That memory helped the dance turn from worry into teamwork."),
        ("How did the helper make the dance better?",
         f"{helper.label} stayed beside {child.label} and helped count the steps again. That made the tricky part feel safe and warm."),
        ("What moral value did the story teach?",
         f"It taught kindness and teamwork. The children learned that helping someone is more important than winning alone."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a dance studio?",
         "A dance studio is a room with space, mirrors, and music where people practice dances."),
        ("What does recall mean?",
         "Recall means to remember something from before. It helps you bring back a lesson, a song, or a step in your mind."),
        ("What is a moral value?",
         "A moral value is a good lesson about how to treat other people, like being kind, honest, or helpful."),
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


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.routine not in ROUTINES or params.helper not in HELPS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], ROUTINES[params.routine], HELPS[params.helper],
                 params.child_name, params.child_gender, params.coach_gender)
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


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", sid) for sid in SETTINGS]
    lines += [asp.fact("routine", rid) for rid in ROUTINES]
    lines += [asp.fact("helper", hid) for hid in HELPS]
    lines += [asp.fact("recall_word", "recall")]
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, R, H) :- setting(S), routine(R), helper(H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, routine=None, helper=None, name=None, gender=None, coach_gender=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams(setting="dance_studio", routine="recital", helper="counting", child_name="Mina", child_gender="girl", coach_gender="girl"),
    StoryParams(setting="dance_studio", routine="class_duet", helper="gentle_hand", child_name="Eli", child_gender="boy", coach_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories:")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
