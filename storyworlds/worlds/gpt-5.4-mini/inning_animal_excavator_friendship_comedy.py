#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/inning_animal_excavator_friendship_comedy.py
=============================================================================

A small, self-contained storyworld for a comedy about friendship, an inning at
a neighborhood game, an animal helper, and an excavator that causes trouble
before helping in a sensible way.

The domain is intentionally tiny:
- Two friends try to finish an inning at a playful game.
- An animal wanders into the field and creates a comic problem.
- An excavator is used in an absurd but ultimately helpful way.
- The story turns on cooperation, not damage: the friends solve the mess
  together and end with a happy image proving what changed.

The story quality goal is a child-facing, state-driven comedy with a clear
beginning, middle turn, and ending.
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
    phrase: str
    field: str
    noise: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class AnimalKind:
    id: str
    label: str
    phrase: str
    behavior: str
    comic_sound: str
    can_help: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class ExcavatorKind:
    id: str
    label: str
    phrase: str
    scoop: str
    fix: str
    boom: str
    can_help: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Game:
    id: str
    activity: str
    inning_line: str
    score_line: str
    ending_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["mess"] < THRESHOLD:
            continue
        sig = ("spook", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in list(world.entities.values()):
            if kid.role == "friend":
                kid.memes["flustered"] += 1
        out.append("__spook__")
    return out


def _r_lift_teamwork(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("excavator")
    if not helper or helper.meters["used"] < THRESHOLD:
        return out
    if helper.meters["cleared"] >= THRESHOLD:
        sig = ("lift_teamwork",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        for kid in list(world.entities.values()):
            if kid.role == "friend":
                kid.memes["joy"] += 1
        out.append("__cheer__")
    return out


CAUSAL_RULES = [Rule("spook", "social", _r_spook), Rule("lift_teamwork", "social", _r_lift_teamwork)]


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


def hazard_due_to_animal(animal: AnimalKind, setting: Setting) -> bool:
    return animal.can_help and setting.id in {"field", "diamond", "park"}


def sensible_excavator(excavator: ExcavatorKind) -> bool:
    return excavator.can_help


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid, animal in ANIMALS.items():
            for xid, exc in EXCAVATORS.items():
                if hazard_due_to_animal(animal, setting) and sensible_excavator(exc):
                    combos.append((sid, aid, xid))
    return combos


def choose_relevant_parking(setting: Setting) -> str:
    return "the edge of the field" if setting.id == "field" else "the side of the lot"


def predict_problem(world: World, animal: AnimalKind) -> dict:
    sim = world.copy()
    sim.get("animal").meters["mess"] += 1
    propagate(sim, narrate=False)
    return {"messy": sim.get("animal").meters["mess"] >= THRESHOLD}


def _do_animal(world: World, animal: AnimalKind) -> None:
    a = world.get("animal")
    a.meters["mess"] += 1
    a.memes["surprise"] += 1
    propagate(world, narrate=False)


def setup(world: World, friend1: Entity, friend2: Entity, game: Game) -> None:
    friend1.memes["joy"] += 1
    friend2.memes["joy"] += 1
    world.say(
        f"On a sunny afternoon, {friend1.id} and {friend2.id} met at {world.setting.place}. "
        f"{game.inning_line} {game.score_line}"
    )
    world.say(
        f"They were playing a silly little game, and the crowd kept pretending it was a very important inning."
    )


def animal_arrives(world: World, animal: AnimalKind) -> None:
    world.say(
        f"Then {animal.phrase} trotted onto the field with a look that said it owned the place."
    )
    world.say(f"It made a cheerful {animal.comic_sound} and sat right where the game was about to happen.")


def ask_for_help(world: World, friend1: Entity, friend2: Entity, animal: AnimalKind, excavator: ExcavatorKind) -> None:
    friend2.memes["worry"] += 1
    world.say(
        f"{friend2.id} blinked. '{friend1.id}, we cannot play an inning with {animal.label} in the middle of it,' "
        f"{friend2.pronoun()} said."
    )
    world.say(
        f"{friend1.id} squinted at the problem and pointed at {excavator.label}. "
        f"'Maybe the big machine can help move the problem gently,' {friend1.pronoun()} said."
    )


def use_excavator(world: World, excavator: ExcavatorKind, setting: Setting) -> None:
    ex = world.get("excavator")
    ex.meters["used"] += 1
    ex.meters["cleared"] += 1
    world.say(
        f"An {excavator.phrase} rolled in, {excavator.boom} and {excavator.scoop} the way a toy truck might dream of doing."
    )
    world.say(
        f"The driver used it to {excavator.fix}, and the animal waddled to {choose_relevant_parking(setting)}."
    )


def rescue_friendship(world: World, friend1: Entity, friend2: Entity, animal: AnimalKind, game: Game) -> None:
    friend1.memes["relief"] += 1
    friend2.memes["relief"] += 1
    world.say(
        f"Once the field was clear, {friend1.id} and {friend2.id} laughed so hard they almost forgot the score."
    )
    world.say(
        f"{animal.label} snorted happily, as if the whole thing had been planned for a parade."
    )
    world.say(
        f"Then the game finally went on, and this time the inning felt easy, friendly, and very, very funny."
    )
    world.say(f"The ending image was simple: {game.ending_image}")


def tell(setting: Setting, game: Game, animal: AnimalKind, excavator: ExcavatorKind,
         friend1_name: str = "Mina", friend1_gender: str = "girl",
         friend2_name: str = "Leo", friend2_gender: str = "boy") -> World:
    world = World(setting)
    f1 = world.add(Entity(id=friend1_name, kind="character", type=friend1_gender, role="friend"))
    f2 = world.add(Entity(id=friend2_name, kind="character", type=friend2_gender, role="friend"))
    world.add(Entity(id="animal", kind="character", type="animal", label=animal.label, role="animal"))
    world.add(Entity(id="excavator", kind="thing", type="machine", label=excavator.label, role="tool"))
    setup(world, f1, f2, game)
    world.para()
    animal_arrives(world, animal)
    ask_for_help(world, f1, f2, animal, excavator)
    world.para()
    use_excavator(world, excavator, setting)
    rescue_friendship(world, f1, f2, animal, game)
    world.facts.update(
        friend1=f1, friend2=f2, setting=setting, game=game, animal=animal,
        excavator=excavator, outcome="fixed",
    )
    return world


SETTINGS = {
    "field": Setting("field", "the baseball field", "a green baseball field", "the grass", "the crowd"),
    "park": Setting("park", "the park ball diamond", "a little park diamond", "the dirt", "the benches"),
}

ANIMALS = {
    "duck": AnimalKind("duck", "duck", "a duck", "waddled", "quack-quack"),
    "goat": AnimalKind("goat", "goat", "a goat", "nibbled", "baa-honk"),
    "cat": AnimalKind("cat", "cat", "a very smug cat", "strolled", "mrrp"),
}

EXCAVATORS = {
    "yellow": ExcavatorKind("yellow", "yellow excavator", "a yellow excavator", "scooped up", "move the duckyard mess", "whirr-clank"),
    "blue": ExcavatorKind("blue", "blue excavator", "a blue excavator", "lifted", "shuffle the silly pile aside", "chugga-chug"),
}

GAMES = {
    "inning": Game(
        "inning",
        "they were trying to finish one more inning",
        "It was the third inning, and nobody agreed on the score",
        "The scoreboard looked confused, but the friends kept grinning",
        "two friends standing beside a neat, empty field with the animal now safe at the side",
    ),
    "friendly": Game(
        "friendly",
        "they were playing a friendly inning for fun",
        "It was the first inning, and the game was more laughter than competition",
        "The team was mostly snacks and cheering",
        "the friends waving at the animal while the excavator waited like a patient giant",
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Pia", "Tess"]
BOY_NAMES = ["Leo", "Owen", "Milo", "Noah", "Ezra"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    game: str
    animal: str
    excavator: str
    friend1: str
    friend1_gender: str
    friend2: str
    friend2_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a funny friendship story about {f['friend1'].id} and {f['friend2'].id} at {f['setting'].place}, using the words inning, animal, and excavator.",
        f"Tell a comedy story where an animal interrupts an inning and an excavator helps two friends solve it together.",
        f"Write a child-friendly story about friendship, a silly machine, and a helpful cleanup at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="Who are the story's main friends?",
            answer=f"The story is about {f['friend1'].id} and {f['friend2'].id}. They stay together, laugh together, and fix the problem together."
        ),
        QAItem(
            question="What interrupted the inning?",
            answer=f"{f['animal'].label.capitalize()} wandered onto the field and made the inning look extra silly. That is what caused the friends to stop and solve the problem first."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They used the {f['excavator'].label} to move the animal gently to the side. After that, the friends could keep playing and the inning could continue."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What is an inning?",
            answer="An inning is one part of a baseball game. After an inning ends, the teams switch and keep playing."
        ),
        QAItem(
            question="What is an excavator?",
            answer="An excavator is a big machine with a long arm and a bucket. It can scoop and move dirt or other heavy things."
        ),
        QAItem(
            question="Why do friends help each other?",
            answer="Friends help each other because friendship means sharing, solving problems, and being kind when something goes wrong."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world only tells a funny, friendly story where an animal causes a small problem and an excavator helps solve it.)"


ASP_RULES = r"""
valid(S,A,E) :- setting(S), animal(A), excavator(E).
problem(A) :- animal(A).
helpful(E) :- excavator(E).
outcome(fixed) :- problem(_), helpful(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for eid in EXCAVATORS:
        lines.append(asp.fact("excavator", eid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import sys as _sys
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, game=None, animal=None, excavator=None,
            friend1=None, friend1_gender=None, friend2=None, friend2_gender=None,
            n=1, seed=None, all=False, trace=False, qa=False, json=False,
            asp=False, verify=False, show_asp=False
        ), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    if rc == 0:
        print("OK: ASP parity and story smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about friendship, inning, animal, and excavator.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--game", choices=GAMES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--excavator", choices=EXCAVATORS)
    ap.add_argument("--friend1")
    ap.add_argument("--friend1-gender", dest="friend1_gender", choices=["girl", "boy"])
    ap.add_argument("--friend2")
    ap.add_argument("--friend2-gender", dest="friend2_gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    game = args.game or rng.choice(list(GAMES))
    animal = args.animal or rng.choice(list(ANIMALS))
    excavator = args.excavator or rng.choice(list(EXCAVATORS))
    friend1_gender = args.friend1_gender or rng.choice(["girl", "boy"])
    friend2_gender = args.friend2_gender or ("boy" if friend1_gender == "girl" else "girl")
    friend1 = args.friend1 or rng.choice(GIRL_NAMES if friend1_gender == "girl" else BOY_NAMES)
    friend2_pool = [n for n in (GIRL_NAMES if friend2_gender == "girl" else BOY_NAMES) if n != friend1]
    friend2 = args.friend2 or rng.choice(friend2_pool)
    return StoryParams(setting, game, animal, excavator, friend1, friend1_gender, friend2, friend2_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        GAMES[params.game],
        ANIMALS[params.animal],
        EXCAVATORS[params.excavator],
        params.friend1,
        params.friend1_gender,
        params.friend2,
        params.friend2_gender,
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("field", "inning", "duck", "yellow", "Mina", "girl", "Leo", "boy"),
            StoryParams("park", "friendly", "goat", "blue", "Nora", "girl", "Owen", "boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        if len(samples) > 1:
            p = sample.params
            print(f"### variant {i + 1}: {p.friend1} & {p.friend2} with {p.animal} and {p.excavator}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
