#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/stop_gerund_sibling_rhyme_lesson_learned_humor.py
===================================================================================

A standalone storyworld about a small superhero mishap: a younger sibling
won't stop *gerund*, the older sibling tries to help with a rhyming warning,
humor nudges the scene, and a lesson lands without the story turning mean.

The world is intentionally tiny. It models:
- a hero with a power meter and a mood meter,
- a sibling relationship,
- a playful "stop-gerund" warning beat,
- a small hazard or comic disruption,
- a helpful fix,
- and a final lesson learned image.

The prose is state-driven: the ending changes because the world state changes.
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
LESSON_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
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
class Scene:
    id: str
    place: str
    setup: str
    hero_power: str
    sibling_title: str
    hazard: str
    hazard_label: str
    comic_twist: str
    fix: str
    ending_image: str
    rhyme_line: str
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
class Trouble:
    id: str
    label: str
    verb: str
    gerund: str
    effect: str
    risk: str
    funny: str
    makes_problem: bool = True
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
class Solution:
    id: str
    label: str
    action: str
    outcome: str
    lesson: str
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


def _r_problem(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    sibling = world.get("sibling")
    trouble = world.get("trouble")
    if hero.meters["mischief"] < THRESHOLD:
        return out
    sig = ("problem",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["stuck"] += 1
    sibling.memes["worry"] += 1
    out.append(
        f"{trouble.label_word if False else ''}".strip()
    )
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["lesson"] < LESSON_THRESHOLD:
        return out
    sig = ("lesson",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("sibling").memes["pride"] += 1
    out.append("__lesson__")
    return out


CAUSAL_RULES = [
    Rule("problem", "physical", _r_problem),
    Rule("lesson", "social", _r_lesson),
]


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


def stop_gerund_allowed(trouble: Trouble) -> bool:
    return trouble.makes_problem


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for tid, t in TROUBLES.items():
            for sid, s in SOLUTIONS.items():
                if stop_gerund_allowed(t):
                    combos.append((scene, tid, sid))
    return combos


def scene_story(world: World, scene: Scene, trouble: Trouble, solution: Solution) -> None:
    hero = world.get("hero")
    sibling = world.get("sibling")
    parent = world.get("parent")

    hero.memes["joy"] += 1
    sibling.memes["joy"] += 1

    world.say(
        f"In {scene.place}, {hero.id} and {sibling.id} were playing superhero."
        f" {scene.setup}"
    )
    world.say(
        f"{hero.id} loved {trouble.gerund}, and {sibling.id} tried to say "
        f'"Stop-{trouble.gerund}!" with a grin.'
    )
    world.say(
        f'"If you keep {trouble.gerund}, the day may go astray," '
        f"{sibling.id} warned. "{scene.rhyme_line}"'
    )
    world.say(
        f"But {hero.id} kept going, and then {trouble.effect}. {trouble.funny}"
    )
    hero.meters["mischief"] += 1
    hero.memes["embarrassed"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"{parent.label_word.capitalize()} hurried over with a calm hero smile. "
        f"{solution.action}, and soon {solution.outcome}."
    )
    hero.memes["lesson"] += 1
    hero.memes["relief"] += 1
    sibling.memes["relief"] += 1
    world.say(
        f"{solution.lesson} {scene.comic_twist} {scene.ending_image}"
    )


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    out: list[tuple[str, str]] = []
    tags = set(f["trouble"].tags) | set(f["solution"].tags)
    if "comic" in tags:
        out.append(("Why can jokes help in a story?",
                    "Jokes can help because they make people relax enough to listen. "
                    "That can turn a tense moment into a smarter choice."))
    out.append(("What does a lesson learned mean?",
                "It means the character understands what went wrong and changes what they do next. "
                "That change is what makes the ending feel complete."))
    out.append(("What does a sibling mean?",
                "A sibling is a brother or sister. Siblings often tease, help, and learn from each other."))
    return out


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    trouble = f["trouble"]
    solution = f["solution"]
    scene = f["scene"]
    return [
        (f"Who is the story about?",
         f"It is about {hero.id} and {sibling.id}, two siblings playing superhero in {scene.place}. "
         f"Their little adventure starts with fun and turns into a lesson."),
        (f"What was {hero.id} doing that {sibling.id} wanted to stop?",
         f"{hero.id} was {trouble.gerund}. {sibling.id} tried to stop it because it was turning the game into a problem. "
         f"That is the exact moment the warning mattered."),
        (f"How did the problem get solved?",
         f"{world.get('parent').label_word.capitalize()} used {solution.label} to fix it, and then the game could calm down. "
         f"The help worked because it matched the trouble instead of making it worse."),
        ("How did the story end?",
         f"It ended with the siblings safe, smiling, and a little wiser. "
         f"{scene.ending_image} proves the lesson changed what they did next."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes the words "stop-gerund" and "sibling".',
        f"Tell a funny sibling superhero story where {f['hero'].id} keeps {f['trouble'].gerund} until a calm grown-up helps.",
        f"Write a rhyming lesson-learned story with humor, a sibling warning, and a bright ending image.",
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    scene: str
    trouble: str
    solution: str
    hero: str
    sibling: str
    parent: str
    hero_gender: str
    sibling_gender: str
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


SCENES = {
    "rooftop": Scene(
        id="rooftop",
        place="the rooftop garden",
        setup="A cape was a towel, a cardboard tube was a blaster, and a tin pan was a shield.",
        hero_power="zoom",
        sibling_title="sidekick",
        hazard="windy banner",
        hazard_label="banner",
        comic_twist="A pigeon in a tiny mood watched from the railing.",
        fix="a grown-up tugged the banner down",
        ending_image="The cape fluttered safely while the pigeon bowed like a judge.",
        rhyme_line="If the banner starts to blow, the safe choice is stop-and-go.",
    ),
    "alley": Scene(
        id="alley",
        place="the sunny alley",
        setup="A broom was a staff, a basket was a secret crate, and a lid became a helmet.",
        hero_power="spark",
        sibling_title="partner",
        hazard="rolling scooter",
        hazard_label="scooter",
        comic_twist="A cat blinked like it had better manners than everybody else.",
        fix="they parked the scooter by the wall",
        ending_image="The helmet sat straight while the cat flicked its tail like a little flag.",
        rhyme_line="If the wheels are zooming free, stop the rolling, friend, and see.",
    ),
    "park": Scene(
        id="park",
        place="the city park",
        setup="A bench was a command post, a scarf was a cape, and a stick was a very serious wand.",
        hero_power="blink",
        sibling_title="helper",
        hazard="goose parade",
        hazard_label="goose",
        comic_twist="One goose looked offended by the whole operation.",
        fix="they tossed breadcrumbs far away",
        ending_image="The command post stayed tidy while the geese marched off like tiny generals.",
        rhyme_line="If the geese begin to roam, stop the crumbs and bring them home.",
    ),
}

TROUBLES = {
    "swinging": Trouble(
        id="swinging",
        label="swing",
        verb="swing",
        gerund="swinging",
        effect="the rope began to twang like a loud spaghetti noodle",
        risk="someone might get bumped",
        funny="The swing complained with a squeak that sounded almost like a joke.",
        tags={"comic", "lesson"},
    ),
    "zooming": Trouble(
        id="zooming",
        label="zoom",
        verb="zoom",
        gerund="zooming",
        effect="the toy cart shot across the floor like a startled beetle",
        risk="the game turned too wild",
        funny="It zoomed so fast it seemed to be late for its own nap.",
        tags={"comic", "lesson"},
    ),
    "climbing": Trouble(
        id="climbing",
        label="climb",
        verb="climb",
        gerund="climbing",
        effect="the stacked boxes wobbled and made a wobble-wobble sound",
        risk="the stack could topple",
        funny="The boxes looked nervous, as if they wanted a seatbelt.",
        tags={"comic", "lesson"},
    ),
}

SOLUTIONS = {
    "steady_hands": Solution(
        id="steady_hands",
        label="steady hands",
        action="the grown-up held the stack steady and guided the hero down",
        outcome="the boxes stopped wobbling",
        lesson="The hero learned that speed is not always the same as bravery.",
        tags={"lesson"},
    ),
    "clear_space": Solution(
        id="clear_space",
        label="clear space",
        action="the grown-up cleared the floor and made room",
        outcome="the cart rolled without trouble",
        lesson="The hero learned that a hero can pause, look, and choose the safer path.",
        tags={"lesson"},
    ),
    "call_help": Solution(
        id="call_help",
        label="calling for help",
        action="the sibling called for help with the proudest tiny voice",
        outcome="the trouble turned into a tidy plan",
        lesson="The hero learned that asking for help can be the strongest move of all.",
        tags={"lesson", "comic"},
    ),
}

GIRL_NAMES = ["Mia", "Zoe", "Ava", "Lily", "Nora", "Ella"]
BOY_NAMES = ["Max", "Leo", "Theo", "Sam", "Finn", "Ben"]


def valid_story(scene: Scene, trouble: Trouble, solution: Solution) -> bool:
    return trouble.makes_problem and "lesson" in solution.tags


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scenes = [k for k in SCENES if args.scene is None or args.scene == k]
    troubles = [k for k in TROUBLES if args.trouble is None or args.trouble == k]
    solutions = [k for k in SOLUTIONS if args.solution is None or args.solution == k]
    combos = [(s, t, so) for s in scenes for t in troubles for so in solutions
              if valid_story(SCENES[s], TROUBLES[t], SOLUTIONS[so])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, trouble, solution = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    sibling_gender = args.sibling_gender or ("boy" if hero_gender == "girl" else "girl")
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    sibling = args.sibling or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    parent = args.parent or ("mom" if parent_gender == "mother" else "dad")
    return StoryParams(
        scene=scene,
        trouble=trouble,
        solution=solution,
        hero=hero,
        sibling=sibling,
        parent=parent,
        hero_gender=hero_gender,
        sibling_gender=sibling_gender,
        parent_gender=parent_gender,
    )


def tell(params: StoryParams) -> World:
    if params.scene not in SCENES or params.trouble not in TROUBLES or params.solution not in SOLUTIONS:
        raise StoryError("Invalid story parameters.")
    scene = SCENES[params.scene]
    trouble = TROUBLES[params.trouble]
    solution = SOLUTIONS[params.solution]
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero", age=7))
    sibling = world.add(Entity(id=params.sibling, kind="character", type=params.sibling_gender, role="sibling", age=9))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent_gender, role="parent", age=34, label="the grown-up"))
    trouble_ent = world.add(Entity(id="trouble", type="thing", label=trouble.label))
    solution_ent = world.add(Entity(id="solution", type="thing", label=solution.label))
    hero.attrs["scene"] = scene.id
    sibling.attrs["scene"] = scene.id
    world.facts.update(hero=hero, sibling=sibling, parent=parent, trouble=trouble, solution=solution, scene=scene)

    hero.memes["confidence"] += 1
    sibling.memes["care"] += 1
    world.say(f"{hero.id} and {sibling.id} were sidekicks in {scene.place}. {scene.setup}")
    world.say(f"{hero.id} kept {trouble.gerund}, even after {sibling.id} tried to stop-{trouble.gerund}.")
    world.say(f'{sibling.id} said, "{scene.rhyme_line}"')
    hero.meters["mischief"] += 1
    hero.memes["giggle"] += 1
    world.say(f"{trouble.funny} {scene.hazard_label.capitalize()} trouble started to grow.")
    world.para()
    world.say(f"The grown-up arrived and {solution.action}.")
    hero.memes["lesson"] += 1
    hero.memes["relief"] += 1
    sibling.memes["relief"] += 1
    world.say(f"{solution.lesson} {scene.comic_twist} {scene.ending_image}")
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        if t.makes_problem:
            lines.append(asp.fact("problematic", tid))
    for sid, s in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        if "lesson" in s.tags:
            lines.append(asp.fact("lesson_solution", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T,SOL) :- scene(S), trouble(T), solution(SOL), problematic(T), lesson_solution(SOL).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and python gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), _random.Random(777)))
        _ = sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero sibling rhyme lesson storyworld.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--sibling")
    ap.add_argument("--parent")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sibling-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for row in combos:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(scene="rooftop", trouble="swinging", solution="call_help", hero="Mia", sibling="Max", parent="Dad", hero_gender="girl", sibling_gender="boy", parent_gender="father"),
            StoryParams(scene="alley", trouble="zooming", solution="clear_space", hero="Leo", sibling="Nora", parent="Mom", hero_gender="boy", sibling_gender="girl", parent_gender="mother"),
            StoryParams(scene="park", trouble="climbing", solution="steady_hands", hero="Ava", sibling="Ben", parent="Dad", hero_gender="girl", sibling_gender="boy", parent_gender="father"),
        ]
        samples = [generate(p) for p in curated]
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
