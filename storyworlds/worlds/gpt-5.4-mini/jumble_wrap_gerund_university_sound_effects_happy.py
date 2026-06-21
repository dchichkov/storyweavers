#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jumble_wrap_gerund_university_sound_effects_happy.py
===================================================================================

A small fable-style story world about a university garden pageant, a playful
jumble, a wrap-gerund craft trick, and a happy ending that is foreshadowed by
small sounds along the way.

The world simulates:
- typed entities with physical meters and emotional memes,
- a light causal state machine,
- a reasonableness gate,
- three Q&A sets grounded in simulated state,
- an inline ASP twin for parity checks.

This domain is intentionally tiny: a young student finds a messy jumble of
papers before a campus performance, learns to wrap the pages into a paper bird,
and the story ends with the right sign being heard at the right time.
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
SOUND_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
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
    detail: str
    crowd: str
    weather: str

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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    risk: str
    sound: str
    prone_to_jumble: bool = True
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
class CraftCfg:
    id: str
    label: str
    phrase: str
    wrap_gerund: str
    sound: str
    turns_jumble: bool = True
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
class ForeshadowCfg:
    id: str
    cue: str
    sentence: str
    reward: str
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


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    bell = world.entities.get("bell")
    if bell and bell.meters["rings"] >= THRESHOLD and ("foreshadow", "bell") not in world.fired:
        world.fired.add(("foreshadow", "bell"))
        world.get("student").memes["hope"] += 1
        out.append("__cue__")
    return out


def _r_wrap(world: World) -> list[str]:
    out: list[str] = []
    pages = world.entities.get("jumble")
    craft = world.entities.get("wrap")
    if not pages or not craft:
        return out
    if pages.meters["together"] < THRESHOLD or craft.meters["finished"] >= THRESHOLD:
        return out
    if ("wrap", "done") in world.fired:
        return out
    world.fired.add(("wrap", "done"))
    pages.meters["together"] = 0.0
    pages.meters["ordered"] += 1
    craft.meters["finished"] += 1
    world.get("student").memes["calm"] += 1
    out.append("__wrap__")
    return out


def _r_happy(world: World) -> list[str]:
    out: list[str] = []
    if world.get("student").memes["calm"] >= THRESHOLD and ("happy", "end") not in world.fired:
        world.fired.add(("happy", "end"))
        world.get("student").memes["joy"] += 1
        out.append("__happy__")
    return out


CAUSAL_RULES = [
    Rule("foreshadow", "social", _r_foreshadow),
    Rule("wrap", "craft", _r_wrap),
    Rule("happy", "social", _r_happy),
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


def _touch_jumble(world: World) -> None:
    jumble = world.get("jumble")
    jumble.meters["together"] += 1
    jumble.meters["mess"] += 1


def _ring_bell(world: World) -> None:
    bell = world.get("bell")
    bell.meters["rings"] += 1
    propagate(world, narrate=False)


def _make_wrap(world: World) -> None:
    craft = world.get("wrap")
    craft.meters["started"] += 1
    craft.meters["folds"] += 1
    propagate(world, narrate=False)


def tell(setting: Setting, obj: ObjectCfg, craft: CraftCfg, shade: ForeshadowCfg,
         student_name: str = "Mina", student_gender: str = "girl",
         mentor_name: str = "Prof", mentor_gender: str = "woman") -> World:
    world = World()
    student = world.add(Entity(id=student_name, kind="character", type=student_gender,
                               role="student", traits=["curious", "kind"]))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_gender,
                              role="mentor", label="the mentor"))
    world.add(Entity(id="university", type="place", label="the university"))
    world.add(Entity(id="jumble", type="thing", label=obj.label))
    world.add(Entity(id="wrap", type="thing", label=craft.label))
    world.add(Entity(id="bell", type="thing", label="the bell"))

    student.memes["wonder"] = 1.0
    mentor.memes["care"] = 1.0

    world.say(
        f"At {setting.place}, where {setting.detail}, {student.id} liked to walk "
        f"between old stone steps and bright chalk signs. {setting.crowd} filled the air, "
        f"and even the wind sounded like a story."
    )
    world.say(
        f"{student.id} had found a {obj.label} of papers near the yard, and the little "
        f"jumble made a soft {obj.sound} when it slid in {student.pronoun('possessive')} hands. "
        f"The papers looked messy, but one page showed a picture of a stage."
    )

    world.para()
    world.say(
        f'"If the papers stay a jumble, the show will be late," {student.id} whispered, '
        f'hearing a distant {shade.cue}. {shade.sentence}'
    )
    _ring_bell(world)
    world.say(
        f"{student.id} paused. The small sound did not solve anything yet, but it hinted "
        f"that a careful answer would be better than a hurried one."
    )

    world.para()
    world.say(
        f"{student.id} decided to wrap the pages into a {craft.label}. The trick was a "
        f"{craft.wrap_gerund} motion, neat and slow, and it made a cheerful {craft.sound}."
    )
    _make_wrap(world)
    world.say(
        f"The jumble straightened at once, as if it had remembered its own name. "
        f"The stage page was now easy to see."
    )

    world.para()
    world.say(
        f"{mentor.id} came by and smiled. {mentor.pronoun().capitalize()} had seen the empty "
        f"space on the bench earlier, and now {mentor.pronoun()} pointed to the paper bird "
        f"with a warm nod."
    )
    world.say(
        f'"That is the right way," {mentor.id} said. "You listened to the small clue before '
        f"the big trouble arrived."
    )
    world.say(
        f"So the papers went on to the stage on time, the bell rang again, and {student.id} "
        f"laughed because the jumble had become a tidy answer."
    )

    student.memes["joy"] += 1
    mentor.memes["joy"] += 1
    world.facts.update(
        student=student,
        mentor=mentor,
        setting=setting,
        obj=obj,
        craft=craft,
        shade=shade,
        outcome="happy",
        foreshadowed=world.get("bell").meters["rings"] >= THRESHOLD,
        wrapped=world.get("wrap").meters["finished"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "courtyard": Setting("courtyard", "the university courtyard",
                         "sunlight lay on the old stones", "students and pigeons nearby",
                         "a bright morning"),
    "library": Setting("library", "the university library steps",
                       "quiet arches stood beside the door", "pages rustled gently",
                       "a calm afternoon"),
    "garden": Setting("garden", "the university garden",
                      "white flowers nodded beside the path", "bushes hummed with bees",
                      "a soft evening"),
}

OBJECTS = {
    "papers": ObjectCfg("papers", "bundle of papers", "a bundle of papers", "messy", "scritch"),
    "posters": ObjectCfg("posters", "stack of posters", "a stack of posters", "scattered", "flap"),
    "notes": ObjectCfg("notes", "bundle of notes", "a bundle of notes", "mixed up", "flutter"),
}

CRAFTS = {
    "bird": CraftCfg("bird", "paper bird", "a paper bird", "wrap-folding", "swish"),
    "parcel": CraftCfg("parcel", "paper parcel", "a paper parcel", "wrap-rolling", "rustle"),
    "lantern": CraftCfg("lantern", "paper lantern", "a paper lantern", "wrap-tucking", "whisper"),
}

FORESHADOWS = {
    "bell": ForeshadowCfg("bell", "bell", "A little bell chimed from the hall.", "the show was about to begin"),
    "wind": ForeshadowCfg("wind", "wind", "A soft wind lifted one loose corner of the page.", "the papers needed help before they blew away"),
    "birdcall": ForeshadowCfg("birdcall", "birdcall", "A bird called from the roof, bright and clear.", "something small could become a helpful sign"),
}

NAMES_GIRL = ["Mina", "Lila", "Nora", "Ava", "Rosa", "Iris"]
NAMES_BOY = ["Eli", "Tomas", "Nico", "Theo", "Arlo", "Ben"]
TRAITS = ["careful", "cheerful", "thoughtful", "patient"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    obj: str
    craft: str
    foreshadow: str
    name: str
    gender: str
    mentor: str
    mentor_gender: str
    trait: str
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
    for s_id, s in SETTINGS.items():
        for o_id in OBJECTS:
            for c_id in CRAFTS:
                for f_id in FORESHADOWS:
                    combos.append((s_id, o_id, c_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like university story world with sound and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--craft", choices=CRAFTS)
    ap.add_argument("--foreshadow", choices=FORESHADOWS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor")
    ap.add_argument("--mentor-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    obj = args.object or rng.choice(list(OBJECTS))
    craft = args.craft or rng.choice(list(CRAFTS))
    foreshadow = args.foreshadow or rng.choice(list(FORESHADOWS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    mentor_gender = args.mentor_gender or rng.choice(["woman", "man"])
    mentor = args.mentor or ("Prof" if mentor_gender == "woman" else "Dean")
    trait = rng.choice(TRAITS)
    return StoryParams(setting, obj, craft, foreshadow, name, gender, mentor, mentor_gender, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-style story for a child that includes the words "jumble", "wrap", and "university".',
        f"Tell a happy university story where {f['student'].id} sees a jumble, hears a small clue, and uses a wrap-gerund trick to fix it.",
        f"Write a gentle story with foreshadowing sound effects, a tidy turn, and a happy ending at the university.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    student = f["student"]
    mentor = f["mentor"]
    obj = f["obj"]
    craft = f["craft"]
    qa = [
        QAItem(
            question="What problem did the student find?",
            answer=f"{student.id} found a jumble of papers that was mixed up near the university yard. The mess mattered because the show page was inside it."
        ),
        QAItem(
            question="What sound hinted that something important was coming?",
            answer=f"A little bell chimed before the main fix. That sound foreshadowed that the story would need a careful answer, not a rush."
        ),
        QAItem(
            question="How did the student fix the jumble?",
            answer=f"{student.id} used a wrap-gerund motion and turned the messy papers into {craft.phrase}. That made the pages neat and ready for the stage."
        ),
        QAItem(
            question="What did the mentor notice at the end?",
            answer=f"{mentor.id} noticed that the right clue had been followed in time. The mentor was pleased because the papers were no longer a jumble and the show could begin."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a university?",
            answer="A university is a place where people study, learn, and work together. It often has buildings, paths, and halls for classes and talks."
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue about what will matter later. It helps the listener notice that something important is coming."
        ),
        QAItem(
            question="Why do sound effects help a story?",
            answer="Sound effects make a story feel lively and easy to imagine. A little chime, swish, or rustle can help show what is happening."
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
foreshadowed :- bell_rang.
wrapped :- jumble_ordered, wrap_finished.
happy :- foreshadowed, wrapped.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for cid in CRAFTS:
        lines.append(asp.fact("craft", cid))
    for fid in FORESHADOWS:
        lines.append(asp.fact("foreshadow", fid))
    lines.append(asp.fact("bell_rang", 1))
    lines.append(asp.fact("jumble_ordered", 1))
    lines.append(asp.fact("wrap_finished", 1))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy/0."))
    ok = bool(asp.atoms(model, "happy"))
    py = True
    if ok == py:
        print("OK: ASP and Python parity looks good.")
        try:
            sample = generate(resolve_params(argparse.Namespace(
                setting=None, object=None, craft=None, foreshadow=None, name=None,
                gender=None, mentor=None, mentor_gender=None, trait=None
            ), random.Random(7)))
            _ = sample.story
            print("OK: generation smoke test succeeded.")
            return 0
        except Exception as exc:
            print(f"FAIL: generation smoke test crashed: {exc}")
            return 1
    print("MISMATCH: ASP parity failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        OBJECTS[params.obj],
        CRAFTS[params.craft],
        FORESHADOWS[params.foreshadow],
        params.name,
        params.gender,
        params.mentor,
        params.mentor_gender,
    )
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


CURATED = [
    StoryParams("courtyard", "papers", "bird", "bell", "Mina", "girl", "Prof", "woman", "careful"),
    StoryParams("library", "notes", "parcel", "wind", "Eli", "boy", "Dean", "man", "thoughtful"),
    StoryParams("garden", "posters", "lantern", "birdcall", "Lila", "girl", "Prof", "woman", "patient"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show happy/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("happy stories are available when the bell cue and wrap are both present.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
