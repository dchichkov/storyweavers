#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/goldfish_lesson_learned_surprise_slice_of_life.py
==================================================================================

A small slice-of-life story world about a child, a goldfish, a surprise, and a
lesson learned.

The domain is intentionally tiny: a child cares for a pet goldfish at home,
something surprising happens around the fish tank or bowl, an adult helps, and
the child learns a gentle everyday lesson. The stories are state-driven rather
than template-swapped; simulated meters and memes decide which beats appear.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/goldfish_lesson_learned_surprise_slice_of_life.py
    python storyworlds/worlds/gpt-5.4-mini/goldfish_lesson_learned_surprise_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4-mini/goldfish_lesson_learned_surprise_slice_of_life.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/goldfish_lesson_learned_surprise_slice_of_life.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/goldfish_lesson_learned_surprise_slice_of_life.py --verify
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
    scene: str
    place_sentence: str
    cozy_detail: str
    surprise_detail: str
    evening: bool = False

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
class Pet:
    id: str
    label: str
    phrase: str
    bowl_word: str
    splash_word: str
    surprise_action: str
    behavior: str
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
class Lesson:
    id: str
    sense: int
    text: str
    fix_text: str
    lesson_text: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    fish = world.get("goldfish")
    if fish.meters["stirred"] >= THRESHOLD and ("worry", "goldfish") not in world.fired:
        world.fired.add(("worry", "goldfish"))
        world.get("child").memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_splash(world: World) -> list[str]:
    out: list[str] = []
    fish = world.get("goldfish")
    if fish.meters["splashed"] >= THRESHOLD and ("splash", "goldfish") not in world.fired:
        world.fired.add(("splash", "goldfish"))
        world.get("child").memes["surprise"] += 1
        out.append("__surprise__")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["helped"] >= THRESHOLD and ("lesson", "child") not in world.fired:
        world.fired.add(("lesson", "child"))
        child.memes["lesson"] += 1
        out.append("__lesson__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("splash", "physical", _r_splash),
    Rule("lesson", "social", _r_lesson),
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


def predict(world: World, event: str) -> dict:
    sim = world.copy()
    if event == "spill":
        sim.get("goldfish").meters["splashed"] += 1
    elif event == "feed":
        sim.get("goldfish").meters["stirred"] += 1
    propagate(sim, narrate=False)
    return {
        "surprised": sim.get("child").memes["surprise"] >= THRESHOLD,
        "worried": sim.get("child").memes["worry"] >= THRESHOLD,
    }


def do_setup(world: World, child: Entity, parent: Entity, setting: Setting, fish: Pet) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} sat with {parent.label_word} in {setting.scene}. "
        f"{setting.place_sentence} {setting.cozy_detail}"
    )
    world.say(
        f"{child.id} loved watching the {fish.label} drift through the water, slow and bright."
    )


def do_surprise(world: World, child: Entity, parent: Entity, fish: Pet, setting: Setting) -> None:
    child.meters["stirred"] += 1
    world.say(
        f"Then came a surprise: {setting.surprise_detail} {fish.surprise_action}."
    )
    world.say(
        f"The {fish.label} made a quick little swirl, and {child.id} blinked in delight."
    )
    propagate(world, narrate=True)


def warn(world: World, parent: Entity, child: Entity, fish: Pet, lesson: Lesson) -> None:
    pred = predict(world, "spill")
    if pred["worried"]:
        world.facts["predicted_worry"] = True
        world.say(
            f'"Careful," {parent.label_word} said softly. "If the water splashes, the '
            f'{fish.label} can get stressed. {lesson.text}"'
        )


def act_mistake(world: World, child: Entity, fish: Pet) -> None:
    child.memes["impulse"] += 1
    world.say(
        f"{child.id} almost leaned too close, because the surprise made {child.pronoun('possessive')} hands fidgety."
    )
    world.say(
        f"But {child.id} stopped in time and moved back from the bowl."
    )


def fix(world: World, child: Entity, parent: Entity, fish: Pet, lesson: Lesson) -> None:
    child.meters["helped"] += 1
    world.say(
        f"{parent.label_word.capitalize()} brought a small towel and showed {child.pronoun('object')} how to dry the little spill first."
    )
    world.say(
        f"Together they gave the {fish.label} a calm, clean bowl again."
    )
    propagate(world, narrate=True)
    world.say(f"That was the lesson learned: {lesson.lesson_text}")


def ending(world: World, child: Entity, fish: Pet, setting: Setting) -> None:
    child.memes["joy"] += 1
    world.say(
        f"By the end, the room felt peaceful again, and the {fish.label} was swimming in smooth little circles."
    )
    world.say(
        f"{child.id} smiled at the bright orange fins and remembered to move gently around the bowl."
    )


def tell(setting: Setting, fish: Pet, lesson: Lesson, child_name: str = "Mia",
         child_gender: str = "girl", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    goldfish = world.add(Entity(id="goldfish", kind="character", type="fish", label=fish.label))
    world.facts["setting"] = setting
    world.facts["fish"] = fish
    world.facts["lesson"] = lesson

    do_setup(world, child, parent, setting, fish)
    world.para()
    do_surprise(world, child, parent, fish, setting)
    warn(world, parent, child, fish, lesson)
    act_mistake(world, child, fish)
    world.para()
    fix(world, child, parent, fish, lesson)
    ending(world, child, fish, setting)

    world.facts.update(child=child, parent=parent, goldfish=goldfish, outcome="lesson")
    return world


SETTINGS = {
    "kitchen": Setting(
        "kitchen",
        "the kitchen table",
        "The fish bowl sat near a sunny window, and a little plant leaned beside it.",
        "A bowl of crackers sat on the counter, and the afternoon was very still.",
        "A tiny splash came from the bowl,",
    ),
    "living_room": Setting(
        "living_room",
        "the living room",
        "The tank stood on a low shelf, and a blue blanket was folded on the couch.",
        "A small lamp made the glass shine, and the whole room felt calm.",
        "The fish tank made a soft clink,",
    ),
    "bedroom": Setting(
        "bedroom",
        "the bedroom",
        "A little desk lamp glowed beside the fish bowl, and stuffed animals watched from the bed.",
        "The room smelled like clean sheets and bedtime soap.",
        "A playful ripple moved through the water,",
        evening=True,
    ),
}

FISHES = {
    "goldfish": Pet("goldfish", "goldfish", "a goldfish", "bowl", "splash", "flipped its tail", "likes calm water", {"goldfish", "pet"}),
    "goldfish_red": Pet("goldfish_red", "goldfish", "a goldfish", "bowl", "ripple", "did a tiny loop", "likes small meals", {"goldfish", "pet"}),
    "goldfish_orange": Pet("goldfish_orange", "goldfish", "a goldfish", "tank", "bubbly tap", "wobbled happily", "likes clean water", {"goldfish", "pet"}),
}

LESSONS = {
    "gentle": Lesson(
        "gentle", 2,
        "It was better to move gently around the fish bowl.",
        "They wiped the water away before it could spread.",
        "When something small can get frightened, the kindest thing is to be gentle.",
        {"gentle", "care"},
    ),
    "feeding": Lesson(
        "feeding", 2,
        "It was better to give only a tiny pinch of food.",
        "They saved the extra food for later.",
        "A little food is enough, because too much can make a pet's water messy.",
        {"feeding", "care"},
    ),
    "cleaning": Lesson(
        "cleaning", 2,
        "It was better to clean up spills right away.",
        "They dried the counter with a towel.",
        "Tiny spills are easier to handle when you clean them early.",
        {"cleaning", "care"},
    ),
}

CHILD_NAMES = ["Mia", "Lily", "Noah", "Ben", "Ava", "Ella", "Theo", "Zoe"]
PARENTS = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for fid in FISHES:
            for lid in LESSONS:
                combos.append((sid, fid, lid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    fish: str
    lesson: str
    child_name: str
    child_gender: str
    parent_type: str
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


KNOWLEDGE = {
    "goldfish": [("What is a goldfish?", "A goldfish is a small pet fish that lives in water. It can be orange, and it needs gentle care.")],
    "bowl": [("What is a fish bowl?", "A fish bowl is a round glass container that holds water for a small fish.")],
    "tank": [("What is a fish tank?", "A fish tank is a bigger glass home for fish. It gives them more room to swim.")],
    "gentle": [("Why should you be gentle with a pet fish?", "Fish can get stressed by loud noise or rough movement, so gentle care helps them stay calm.")],
    "feeding": [("How much should you feed a goldfish?", "Just a little food is enough. Too much food can make the water messy.")],
    "cleaning": [("Why clean up a spill quickly?", "Cleaning up a spill early keeps the table neat and makes the room safer and calmer.")],
}

KNOWLEDGE_ORDER = ["goldfish", "bowl", "tank", "gentle", "feeding", "cleaning"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the word "goldfish" and ends with a gentle lesson learned.',
        f"Tell a quiet home story where {f['child'].id} spends time with {f['fish'].label} and learns to be more careful after a surprise.",
        f"Write a simple everyday story about a child, a goldfish, and a small surprise at home.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    fish = f["fish"]
    setting = f["setting"]
    lesson = f["lesson"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, {child.pronoun('possessive')} {parent.label_word}, and a {fish.label}."),
        ("Where did the story happen?",
         f"It happened in {setting.scene}, with a fish bowl or tank in the room."),
        ("What surprised {0}?".format(child.id),
         f"The {fish.label} made a sudden little move, and the water gave a tiny surprise ripple."),
        ("What did the child learn?",
         f"{lesson.lesson_text} The surprise helped {child.id} remember to move gently and keep the area calm."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["fish"].tags) | set(world.facts["lesson"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "goldfish", "gentle", "Mia", "girl", "mother"),
    StoryParams("living_room", "goldfish_red", "feeding", "Noah", "boy", "father"),
    StoryParams("bedroom", "goldfish_orange", "cleaning", "Ava", "girl", "mother"),
]


def outcome_of(params: StoryParams) -> str:
    return "lesson"


def explain_rejection() -> str:
    return "(No story: this world is built to be a gentle slice-of-life around a goldfish, so the requested options do not fit.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.evening:
            lines.append(asp.fact("evening", sid))
    for fid in FISHES:
        lines.append(asp.fact("fish", fid))
    for lid, l in LESSONS.items():
        lines.append(asp.fact("lesson", lid))
        lines.append(asp.fact("sense", lid, l.sense))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S, F, L) :- setting(S), fish(F), lesson(L).
gentle_lesson(L) :- lesson(L), sense(L, S), S >= 2.
outcome(lesson) :- compatible(_, _, _), gentle_lesson(_).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python combo gates differ.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small goldfish slice-of-life story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--fish", choices=FISHES)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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
              and (args.fish is None or c[1] == args.fish)
              and (args.lesson is None or c[2] == args.lesson)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, fish, lesson = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILD_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(setting, fish, lesson, name, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], FISHES[params.fish], LESSONS[params.lesson],
                 params.child_name, params.child_gender, params.parent_type)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show compatible/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for s, f, l in combos:
            print(f"  {s:12} {f:16} {l}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.fish} / {p.lesson} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
