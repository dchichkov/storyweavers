#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/radio_rhyme_adventure.py
=========================================================

A standalone tiny storyworld for an adventure tale with rhyme, centered on a
radio that helps a child explorer cross a small but tricky journey.

The premise:
- A curious child sets out on a little adventure.
- They carry a radio for tunes and clues.
- The radio can help only if it is turned on and tuned well.
- A shortcut can lead to trouble, while a careful route and a friendly helper
  lead to a bright ending.

This script follows the storyworld contract:
- stdlib only
- shared result containers from storyworlds/results.py
- typed entities with physical meters and emotional memes
- reasonableness gate plus inline ASP twin
- --verify smoke checks ordinary generation and parity
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
class Theme:
    id: str
    scene: str
    props: str
    title: str
    goal: str
    route_dark: str
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
class Radio:
    id: str
    label: str
    phrase: str
    sound: str
    clue: str
    rhyme_tag: str = "rhyme"
    plays_music: bool = True
    gives_clue: bool = True

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
class Place:
    id: str
    label: str
    scene_line: str
    safe_path: bool
    danger: str
    tags: set[str] = field(default_factory=set)

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
    risk: int
    text: str
    fail_text: str
    fix_text: str
    tags: set[str] = field(default_factory=set)

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
        clone = World()
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


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters["rain"] >= THRESHOLD and "radio" in world.entities:
        radio = world.get("radio")
        sig = ("wet",)
        if sig not in world.fired:
            world.fired.add(sig)
            radio.meters["quiet"] += 1
            hero.memes["worry"] += 1
            out.append("__wet__")
    return out


def _r_lost(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.memes["lost"] >= THRESHOLD:
        sig = ("lost",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] += 1
            out.append("The path felt wider than before.")
    return out


CAUSAL_RULES = [Rule("wet", "physical", _r_wet), Rule("lost", "social", _r_lost)]


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


def rhyme(line1: str, line2: str) -> str:
    return f"{line1}\n{line2}"


def radio_ok(radio: Radio) -> bool:
    return radio.plays_music and radio.gives_clue


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tid, theme in THEMES.items():
        for pid, place in PLACES.items():
            for pbid, problem in PROBLEMS.items():
                if theme.id == "adventure" and place.safe_path and problem.risk >= 1:
                    combos.append((tid, pid, pbid))
    return combos


@dataclass
@dataclass
class StoryParams:
    theme: str
    place: str
    problem: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
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


def setup(world: World, theme: Theme, place: Place, problem: Problem,
          hero: Entity, helper: Entity, parent: Entity, radio: Radio) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On a bright morning, {hero.id} set out on {theme.scene}. "
        f"{theme.props}"
    )
    world.say(
        f"{hero.id} carried {radio.phrase}, because a tune can travel like a kite, "
        f"and a clue can keep a brave child in sight."
    )
    world.say(
        f"{helper.id} walked along too, while {parent.label_word} waved from the gate, "
        f"and the road ahead looked small but full of fate."
    )
    world.say(
        f"At {place.label}, {problem.text}."
    )


def tempt(world: World, hero: Entity, problem: Problem, radio: Radio) -> None:
    hero.memes["bold"] += 1
    world.say(
        f'"I can take the sharp shortcut," {hero.id} said with a grin. '
        f'"The radio will sing, and I will win."'
    )
    world.say(
        f"But {problem.label} lurked nearby, all twist and bend, "
        f"and {hero.id} needed a careful friend."
    )


def warn(world: World, helper: Entity, hero: Entity, problem: Problem, radio: Radio) -> None:
    helper.memes["warning"] += 1
    world.say(
        f'"Wait," said {helper.id}. "That way looks fine, but {problem.label} can trip '
        f'your shoes in a crooked line.'
    )
    world.say(
        f'If the radio goes quiet and the way turns rough, we should slow down now, '
        f"not hurry enough."
    )


def choose_safe(world: World, hero: Entity, helper: Entity, radio: Radio,
                place: Place, problem: Problem) -> None:
    hero.memes["trust"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{hero.id} listened, and the shortcut lost its spark. "
        f"They followed the marked trail instead, bright and not dark."
    )
    world.say(
        f"{radio.sound} the radio played, {radio.clue}, and the path felt near. "
        f"Each step was steady, and each sign was clear."
    )
    world.say(
        f"They reached {place.label} without a tumble or tear, "
        f"and {problem.label} stayed behind them, far and clear."
    )


def stumble(world: World, hero: Entity, helper: Entity, problem: Problem, radio: Radio) -> None:
    hero.meters["trouble"] += 1
    hero.memes["fear"] += 1
    if "radio" in world.entities:
        world.get("radio").meters["static"] += 1
    world.say(
        f"{hero.id} hurried too fast, and {problem.label} made a spin. "
        f"Their foot slipped sideways, and they nearly tumbled in."
    )
    world.say(
        f"The radio crackled with static, thin and sour, "
        f"and the brave little trek lost a minute of power."
    )


def rescue(world: World, helper: Entity, parent: Entity, radio: Radio) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"Then {helper.id} held out a hand, and {parent.label_word} came near. "
        f"Together they steadied the walk with cheer."
    )
    world.say(
        f"{parent.label_word.capitalize()} fixed the radio dial with a gentle twist, "
        f"until the song returned and the static was dismissed."
    )


def ending(world: World, hero: Entity, helper: Entity, theme: Theme, radio: Radio,
           safe: bool) -> None:
    if safe:
        world.say(
            f"By sunset, {hero.id} and {helper.id} stood tall in a golden glow, "
            f"with {radio.label} singing low."
        )
        world.say(theme.ending_image)
    else:
        world.say(
            f"By sunset, {hero.id} was tired but glad to be home, "
            f"with {helper.id} beside them and the radio able to roam."
        )
        world.say(
            "The adventure had stumbled, but the friends were okay, "
            "and the lesson was bright: choose the steady way."
        )


def tell(theme: Theme, place: Place, problem: Problem, radio: Radio,
         hero_name: str = "Maya", hero_gender: str = "girl",
         helper_name: str = "Jun", helper_gender: str = "boy",
         parent_type: str = "mother", safe: bool = True) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    radio_ent = world.add(Entity(id="radio", kind="thing", type="radio", label="radio"))
    radio_ent.meters["battery"] = 1.0
    setup(world, theme, place, problem, hero, helper, parent, radio)
    world.para()
    tempt(world, hero, problem, radio)
    warn(world, helper, hero, problem, radio)
    world.para()
    if safe:
        choose_safe(world, hero, helper, radio, place, problem)
    else:
        stumble(world, hero, helper, problem, radio)
        rescue(world, helper, parent, radio)
    world.para()
    ending(world, hero, helper, theme, radio, safe=safe)
    world.facts.update(theme=theme, place=place, problem=problem, radio=radio, hero=hero,
                       helper=helper, parent=parent, safe=safe)
    return world


THEMES = {
    "adventure": Theme(
        "adventure",
        "a little trail by the hills",
        "A map was tucked in a pocket, a bottle held water, and a shiny compass pointed toward the hill path.",
        "Adventure",
        "the hidden bridge",
        "a shadowy bend in the trail",
        "At the end, the trail opened wide, and the friends reached the hilltop with the radio still singing.",
    ),
    "jungle": Theme(
        "jungle",
        "a leafy jungle path",
        "A backpack held bananas, a rope hung by the side, and bright leaves brushed their sleeves.",
        "Jungle Adventure",
        "the stone steps",
        "a muddy turn under hanging vines",
        "At the end, the vines opened to a sunny clearing, and the radio clicked happily in the green light.",
    ),
    "island": Theme(
        "island",
        "a sandy island trail",
        "A shell sat in the pocket, a little flag fluttered, and the sea breeze smelled like salt and spray.",
        "Island Adventure",
        "the lookout tower",
        "a narrow path over the dunes",
        "At the end, the friends reached the shore with the radio humming and the waves clapping below.",
    ),
}

PLACES = {
    "trail": Place("trail", "the trail", "the trail was narrow and a little twisty", True, "a fallen branch"),
    "bridge": Place("bridge", "the bridge", "the bridge crossed over a dry creek bed", True, "a loose plank"),
    "cave": Place("cave", "the cave mouth", "the cave mouth was dim, but the path markers shone", True, "a slippery rock"),
}

PROBLEMS = {
    "breeze": Problem("breeze", "the wind", 1, "the wind kept tugging at the paper map", "the wind blew the map away", "they tucked the map away"),
    "stones": Problem("stones", "the stones", 2, "the stones made the path bumpy and slow", "the stones sent a shoe skidding", "they stepped carefully between them"),
    "fog": Problem("fog", "the fog", 3, "the fog made the path look pale and puzzly", "the fog hid the next sign", "they listened to the radio and stayed close"),
}

RADIOS = {
    "classic": Radio("classic", "radio", "a small radio", "La-la", "the tune rhymed: bright night, right light"),
    "handheld": Radio("handheld", "radio", "a little hand radio", "Bum-bum", "the tune rhymed: slow and low, steady go"),
}

GIRL_NAMES = ["Maya", "Luna", "Ivy", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Jun", "Kai", "Theo", "Ben", "Leo", "Sam"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an adventure story for a young child that includes a radio and a rhyme.",
        f"Tell a small journey story where {f['hero'].id} carries {f['radio'].phrase} and learns to take the safe path.",
        f"Write a rhyming adventure with {f['helper'].id}, a radio, and a tricky path that becomes safe by the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, radio, place, problem = f["hero"], f["helper"], f["radio"], f["place"], f["problem"]
    qa = [
        ("What was the story about?",
         f"It was about {hero.id} going on a little adventure with {helper.id} and carrying {radio.phrase}. The journey was small, but it still had a tricky choice."),
        ("What problem made the adventure tricky?",
         f"{problem.text}. That made the path feel less easy, so the friends had to choose carefully."),
        ("What did {0} do when the path looked hard?".format(hero.id),
         f"{hero.id} listened to {helper.id} and chose the safer trail. That let the adventure continue without a fall."),
    ]
    if f["safe"]:
        qa.append((
            "How did the story end?",
            f"It ended safely, with {hero.id} and {helper.id} reaching {place.label} while the radio still sang. The ending shows they chose the steady route."
        ))
    else:
        qa.append((
            "What happened after the stumble?",
            f"{hero.id} nearly fell, but {helper.id} and {hero.pronoun('possessive')} parent helped steady the trip. After that, the radio worked again and they kept going."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"radio", "rhyme", "adventure"}
    return [
        ("What is a radio?",
         "A radio is a machine that can play music or voices through a speaker. People turn it on and tune it to hear stations."),
        ("Why is rhyme fun in a story?",
         "Rhyme makes words sound playful together. It can help a story feel bouncy, musical, and easy to remember."),
        ("Why does an adventure story feel exciting?",
         "An adventure story feels exciting because someone goes on a journey, meets a challenge, and has to make brave choices."),
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("adventure", "trail", "stones", "Maya", "girl", "Jun", "boy", "mother"),
    StoryParams("jungle", "bridge", "fog", "Ivy", "girl", "Kai", "boy", "father"),
    StoryParams("island", "cave", "breeze", "Leo", "boy", "Luna", "girl", "mother"),
]


def explain_rejection() -> str:
    return "(No story: this combination is not a small, safe adventure path.)"


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.safe_path:
            lines.append(asp.fact("safe_path", pid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for rid in RADIOS:
        lines.append(asp.fact("radio", rid))
        lines.append(asp.fact("gives_clue", rid))
        lines.append(asp.fact("plays_music", rid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, P, R) :- theme(T), place(P), problem(R), safe_path(P).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            theme=None, place=None, problem=None, seed=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Radio rhyme adventure storyworld.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid combinations.)")
    filtered = [
        c for c in combos
        if (args.theme is None or c[0] == args.theme)
        and (args.place is None or c[1] == args.place)
        and (args.problem is None or c[2] == args.problem)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    theme, place, problem = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = "boy" if gender == "girl" else "girl"
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(theme, place, problem, name, gender, helper, helper_gender, parent)


def generate(params: StoryParams) -> StorySample:
    theme = THEMES[params.theme]
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    radio = RADIOS["classic"]
    world = tell(theme, place, problem, radio, params.hero, params.hero_gender,
                 params.helper, params.helper_gender, params.parent, safe=True)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
