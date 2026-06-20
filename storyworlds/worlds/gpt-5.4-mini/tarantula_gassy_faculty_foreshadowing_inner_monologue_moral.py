#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tarantula_gassy_faculty_foreshadowing_inner_monologue_moral.py
=============================================================================================

A tiny fairy-tale storyworld built from the seed words:

- tarantula
- gassy
- faculty

Narrative instruments:

- foreshadowing
- inner monologue
- moral value

The world simulates a child-sized castle school where a nervous student, a
harmless tarantula, and a very gassy banquet create a small misunderstanding.
A kind faculty member notices the warning signs early, the student listens to
their inner thoughts, and the ending turns into a gentle moral about speaking
up before a problem grows.

This script is standalone and uses only the Python stdlib plus the shared
storyworld result containers.
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
MOOD_CAUTIOUS = {"shy", "careful", "thoughtful", "gentle"}


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
        if self.type in {"girl", "princess", "queen", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def name_word(self) -> str:
        return self.label or self.id



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
    mood: str

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
class FacultyMember:
    id: str
    title: str
    gentleness: int
    wisdom: int

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
class Creature:
    id: str
    label: str
    harmless: bool = True
    skittish: bool = True

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
class Problem:
    id: str
    label: str
    smell: str
    warning: str
    intensity: int

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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
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


def _r_warning(world: World) -> list[str]:
    out: list[str] = []
    court = world.get("faculty")
    if court.meters["smell"] < THRESHOLD:
        return out
    sig = ("warning", court.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in ("child",):
        if kid in world.entities:
            world.get(kid).memes["worry"] += 1
    court.memes["alert"] += 1
    out.append("__foreshadow__")
    return out


CAUSAL_RULES = [Rule("warning", _r_warning)]


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


def predict_problem(world: World, problem_id: str) -> dict:
    sim = world.copy()
    _trigger_problem(sim, sim.get(problem_id), narrate=False)
    return {"smell": sim.get("faculty").meters["smell"], "worry": sim.get("child").memes["worry"]}


def _trigger_problem(world: World, problem: Entity, narrate: bool = True) -> None:
    problem.meters["smell"] += 1
    problem.meters["severity"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, child_name: str, child_type: str,
         faculty: FacultyMember, creature: Creature, problem: Problem,
         response: Response, seed: Optional[int] = None) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="student"))
    teacher = world.add(Entity(id="faculty", kind="character", type="teacher", label="the faculty", role="faculty"))
    beast = world.add(Entity(id=creature.id, kind="creature", type="spider", label=creature.label))
    problem_ent = world.add(Entity(id=problem.id, kind="thing", type="problem", label=problem.label))
    world.facts.update(
        setting=setting, child=child, faculty=teacher, creature=beast,
        problem=problem_ent, response=response, seed=seed, moral="kindness and honesty help"
    )

    child.memes["curiosity"] += 1
    child.memes["wonder"] += 1
    teacher.memes["wisdom"] += float(faculty.wisdom)

    world.say(
        f"Once in a castle school, {child.id} walked beneath the moonlit arches of {setting.place}. "
        f"{setting.detail}"
    )
    world.say(
        f"There, the {setting.mood} air carried a curious sign: {problem.warning}. "
        f"'{problem.smell.capitalize()},' thought {child.id}, and {child.pronoun('possessive')} heart began to tap a little faster."
    )

    world.para()
    child.memes["inner_voice"] += 1
    world.say(
        f"'{child.id}, stay calm,' {child.pronoun()} told {child.pronoun('possessive')}self in a small inner voice. "
        f"'A tarantula is not a monster, and a gassy room can make even brave knees wobble.'"
    )
    world.say(
        f"Just then, a tiny tarantula peeked from behind a blue banner. It was {creature.label}, and it only wanted to hide."
    )

    world.para()
    pred = predict_problem(world, "problem")
    world.facts["predicted_smell"] = pred["smell"]
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"{teacher.label.capitalize()} narrowed {teacher.pronoun('possessive')} eyes and noticed the warning signs first. "
        f"'{problem.warning}' {teacher.pronoun().capitalize()} said softly. 'Someone should open the windows before the smell grows.'"
    )
    world.say(
        f"{child.id} looked at the tarantula, then at the candles, and decided to speak up instead of guessing wrong."
    )

    world.para()
    _trigger_problem(world, problem_ent)
    world.say(
        f"The room grew {problem.smell}, and a puff of air slipped past the table. The faculty did not laugh; it listened."
    )
    if response.sense >= 2 and response.power >= problem.intensity:
        world.say(
            f"{teacher.label.capitalize()} {response.text.replace('{problem}', problem.label)}."
        )
        child.memes["relief"] += 1
        child.memes["bravery"] += 1
        world.say(
            f"The windows opened, the smell drifted out, and the tarantula tucked itself safely beside a book. "
            f"{child.id} smiled because the worry had been named before it could become a fuss."
        )
        world.say(
            f"Then {teacher.label.capitalize()} spoke the moral value aloud: 'When something feels strange, tell a grown-up kindly and quickly.'"
        )
        world.facts["outcome"] = "calm"
    else:
        world.say(
            f"{teacher.label.capitalize()} {response.fail.replace('{problem}', problem.label)}."
        )
        world.say(
            f"The smell still hung in the hall, and the child learned that ignoring a warning can make even a small problem feel huge."
        )
        world.facts["outcome"] = "messy"
    return world


SETTINGS = {
    "castle_school": Setting(
        "castle_school",
        "the castle school",
        "Golden candles flickered beside tall windows, and chalk dust shimmered on the stairs.",
        "moonlit",
    ),
    "library_tower": Setting(
        "library_tower",
        "the library tower",
        "Books slept on the shelves, and the spiral stair smelled faintly of old paper.",
        "quiet",
    ),
    "garden_hall": Setting(
        "garden_hall",
        "the garden hall",
        "Rose vines climbed the stone walls, and the supper tables were set beneath a painted ceiling.",
        "sweet",
    ),
}

CREATURES = {
    "tarantula": Creature("tarantula", "the tarantula", harmless=True, skittish=True),
    "tiny_spider": Creature("tiny_spider", "the tarantula", harmless=True, skittish=True),
}

PROBLEMS = {
    "gassy_banquet": Problem(
        "gassy_banquet",
        "a gassy banquet",
        "gassy",
        "A gassy breeze drifted from the banquet table",
        1,
    ),
    "gassy_cauldron": Problem(
        "gassy_cauldron",
        "a gassy stew",
        "gassy",
        "The cauldron burped a gassy warning",
        1,
    ),
    "gassy_goose": Problem(
        "gassy_goose",
        "a gassy goose",
        "gassy",
        "A gassy goose waddled through the hall",
        1,
    ),
}

RESPONSES = {
    "open_windows": Response(
        "open_windows",
        sense=3,
        power=3,
        text="opened the windows and waved a fan until the gassy smell floated away",
        fail="opened a window, but the smell stayed and stayed",
        qa_text="opened the windows and waved a fan until the gassy smell floated away",
    ),
    "move_banquet": Response(
        "move_banquet",
        sense=2,
        power=2,
        text="asked the servants to move the banquet outside, and the fresh air made room for everyone to breathe",
        fail="asked to move the feast, but it was too late for that to help",
        qa_text="asked the servants to move the banquet outside",
    ),
    "ignore_it": Response(
        "ignore_it",
        sense=1,
        power=1,
        text="pretended the gassy smell was not there",
        fail="pretended the problem was nothing at all",
        qa_text="pretended the gassy smell was not there",
    ),
}

CHILD_NAMES = ["Lina", "Mira", "Tomas", "Elin", "Nico", "Sara", "Pip"]
FACULTY_TITLES = ["the kindly dean", "the old professor", "the gentle tutor"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    creature: str
    problem: str
    response: str
    child: str
    child_type: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid in CREATURES:
            for pid in PROBLEMS:
                combos.append((sid, cid, pid))
    return combos


def explain_rejection() -> str:
    return "(No story: this world expects a tarantula, a gassy problem, and a faculty setting.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a tarantula, a gassy surprise, and the faculty.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"], dest="child_type")
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
    if args.problem and args.problem not in PROBLEMS:
        raise StoryError(explain_rejection())
    setting = args.setting or rng.choice(sorted(SETTINGS))
    creature = args.creature or "tarantula"
    problem = args.problem or rng.choice(sorted(PROBLEMS))
    response = args.response or rng.choice(["open_windows", "move_banquet"])
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILD_NAMES)
    return StoryParams(setting, creature, problem, response, child, child_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story that includes the words "{f["creature"].label}", "gassy", and "faculty".',
        f"Tell a gentle castle-school story where {f['child'].id} meets a tarantula and notices a gassy warning before asking the faculty for help.",
        "Write a fairy tale with foreshadowing, inner thoughts, and a moral about speaking up kindly when a small trouble appears.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    faculty = f["faculty"]
    problem = f["problem"]
    creature = f["creature"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, the tarantula, and the faculty at the castle school. The small cast keeps the fairy tale gentle and easy to follow."),
        ("What warning was foreshadowed early in the story?",
         f"The story hinted that a gassy smell was drifting through the hall. That mattered because the faculty could answer the problem before it grew into a bigger worry."),
        ("What did the child think in the inner monologue?",
         f"{child.id} thought to stay calm and not jump to the wrong conclusion. The inner voice helped {child.id} notice that the tarantula was harmless."),
    ]
    if f.get("outcome") == "calm":
        qa.append((
            "How did the faculty help?",
            f"{faculty.label.capitalize()} opened the windows and let the gassy smell drift away. That calm help matched the problem and kept the room peaceful."
        ))
        qa.append((
            "What moral value did the story teach?",
            f"It taught that kindness and honesty help when something feels strange. Speaking up early is braver than hiding from a small problem."
        ))
    else:
        qa.append((
            "What went wrong?",
            f"The faculty did not choose a strong enough answer, so the gassy smell stayed in the hall. The child learned that a small warning should be handled before it lingers."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a tarantula?",
         "A tarantula is a big spider. It may look scary, but many tarantulas are harmless."),
        ("What does gassy mean?",
         "Gassy means full of gas or a smell that can drift through a room. It is something you usually want to air out."),
        ("What is faculty?",
         "Faculty means the teachers and staff at a school or college. They help guide students and keep things orderly."),
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        params.child,
        params.child_type,
        FacultyMember("faculty", "the faculty", gentleness=3, wisdom=3),
        CREATURES[params.creature],
        PROBLEMS[params.problem],
        RESPONSES[params.response],
        seed=params.seed,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
gassy_problem(P) :- problem(P), smell(P, gassy).
calm_outcome(R) :- response(R), sense(R, S), S >= 2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CREATURES:
        lines.append(asp.fact("creature", cid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("smell", pid, "gassy"))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show gassy_problem/1."))
    return sorted(set(asp.atoms(model, "gassy_problem")))


def asp_sensible() -> list[str]:
    return [rid for rid, r in RESPONSES.items() if r.sense >= 2]


def asp_verify() -> int:
    rc = 0
    import_check = set(asp_valid_combos())
    python_check = {(pid,) for pid in PROBLEMS}
    if import_check != python_check:
        rc = 1
        print("MISMATCH in ASP combo gate")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: smoke test story is empty")
    print("OK: smoke test generated a story.")
    return rc


CURATED = [
    StoryParams("castle_school", "tarantula", "gassy_banquet", "open_windows", "Lina", "girl"),
    StoryParams("library_tower", "tarantula", "gassy_cauldron", "move_banquet", "Tomas", "boy"),
    StoryParams("garden_hall", "tarantula", "gassy_goose", "open_windows", "Mira", "girl"),
]


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
        print(asp_program(show="#show gassy_problem/1.\n#show calm_outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(rid for rid in asp_sensible()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
