#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/smartypants_mystery_to_solve_problem_solving_magic.py
=====================================================================================

A small storyworld for a ghost-story-flavored mystery about a smart child, a
puzzling missing thing, careful problem solving, and a little bit of magic.

The world is built around a child nicknamed "smartypants" who helps solve a
gentle mystery in an old house at night. The simulation tracks physical state
with meters and emotional state with memes, so the story is driven by what
happens in the world rather than by a frozen paragraph template.

The generated stories are child-facing, concrete, and complete:
- a spooky premise
- a problem that needs solving
- clues, magic, and a turn
- a closing image that proves what changed
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
class Place:
    id: str
    label: str
    darkness: str
    clue_spot: str
    sound: str
    spooky_image: str
    feels: str
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
class Mystery:
    id: str
    missing: str
    missing_phrase: str
    place_hint: str
    clue: str
    reveal: str
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
class MagicTool:
    id: str
    label: str
    phrase: str
    effect: str
    limit: str
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
class Solution:
    id: str
    sense: int
    power: int
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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    if world.get("house").meters["spooky"] >= THRESHOLD:
        sig = ("fear",)
        if sig not in world.fired:
            world.fired.add(sig)
            kid = world.get("kid")
            kid.memes["unease"] += 1
            out.append("")
    return out


def _r_light(world: World) -> list[str]:
    out: list[str] = []
    if world.get("lantern").meters["glow"] >= THRESHOLD:
        sig = ("light",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("darkness").meters["faded"] += 1
            out.append("")
    return out


CAUSAL_RULES = [Rule("fear", "emotional", _r_fear), Rule("light", "physical", _r_light)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)


def mystery_at_risk(mystery: Mystery, place: Place) -> bool:
    return place.id in mystery.tags or mystery.id in place.tags


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= 2]


def resolve_mystery(solution: Solution, mystery: Mystery, delay: int) -> bool:
    return solution.power >= (1 + delay)


def source_of_magic(tool: MagicTool) -> str:
    return tool.limit


def predict(world: World, tool_id: str) -> dict:
    sim = world.copy()
    _use_magic(sim, sim.get(tool_id), narrate=False)
    return {
        "glow": sim.get("lantern").meters["glow"],
        "found": sim.facts.get("found", False),
    }


def _use_magic(world: World, tool: Entity, narrate: bool = True) -> None:
    tool.meters["glow"] += 1
    world.get("lantern").meters["glow"] += 1
    propagate(world, narrate=narrate)


def opener(world: World, kid: Entity, adult: Entity, place: Place) -> None:
    kid.memes["curiosity"] += 1
    world.say(
        f"On a moon-cold night, {kid.id} and {adult.id} tiptoed into {place.label}. "
        f"{place.spooky_image}"
    )
    world.say(
        f'The house felt like a ghost story, and {kid.id} was nicknamed smartypants '
        f'because {kid.pronoun()} always noticed small things first.'
    )


def missing_problem(world: World, kid: Entity, mystery: Mystery, place: Place) -> None:
    world.say(
        f"Then they noticed a problem: {mystery.missing_phrase} had gone missing. "
        f"It should have been near {place.clue_spot}, but it was gone."
    )
    world.say(
        f'{kid.id} whispered, "That is a mystery to solve." The only sound was {place.sound}.'
    )


def study_clue(world: World, kid: Entity, mystery: Mystery, place: Place) -> None:
    kid.memes["focus"] += 1
    world.say(
        f"{kid.id} looked slowly around {place.label}, careful as could be. "
        f"At {place.clue_spot}, {mystery.clue}"
    )


def try_magic(world: World, kid: Entity, tool: MagicTool) -> None:
    kid.memes["hope"] += 1
    world.say(
        f'Then {kid.id} held up {tool.phrase} and said, "Maybe magic can help." '
        f"{tool.effect}"
    )
    _use_magic(world, world.get("lantern"))


def reason_it_out(world: World, kid: Entity, mystery: Mystery, solution: Solution) -> None:
    kid.memes["confidence"] += 1
    world.say(
        f"{kid.id} did not guess wildly. {kid.id} thought it through, checked the clue, "
        f"and used problem solving instead of fear."
    )
    world.say(
        f'At last, {kid.id} said, "{solution.qa_text}"'
    )


def reveal(world: World, adult: Entity, mystery: Mystery) -> None:
    world.say(
        f"Behind a curtain and a stack of books, they found {mystery.reveal}. "
        f"{adult.label_word.capitalize()} smiled, because the mystery had an ordinary answer after all."
    )


def ending(world: World, kid: Entity, adult: Entity, place: Place) -> None:
    kid.memes["relief"] += 1
    kid.memes["joy"] += 1
    world.say(
        f'By the time they left {place.label}, the lantern glowed warmly in {kid.id}\'s hands, '
        f'and the ghost-story house felt cozy instead of spooky.'
    )
    world.say(
        f"{kid.id} walked home feeling proud, like a real smartypants detective."
    )


def tell(place: Place, mystery: Mystery, magic: MagicTool, solution: Solution,
         kid_name: str = "Mina", kid_gender: str = "girl",
         adult_name: str = "Aunt June", adult_gender: str = "woman",
         delay: int = 0) -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_gender, traits=["smart"], attrs={"nickname": "smartypants"}))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender))
    house = world.add(Entity(id="house", type="house", label="the old house"))
    lantern = world.add(Entity(id="lantern", type="thing", label=magic.label))
    darkness = world.add(Entity(id="darkness", type="thing", label="the dark corners"))
    world.facts["nickname"] = "smartypants"

    house.meters["spooky"] = 1
    lantern.meters["glow"] = 0
    darkness.meters["faded"] = 0

    opener(world, kid, adult, place)
    world.para()
    missing_problem(world, kid, mystery, place)
    study_clue(world, kid, mystery, place)
    world.para()
    try_magic(world, kid, magic)
    if not mystery_at_risk(mystery, place):
        raise StoryError("This mystery/place pairing does not support a real clue to solve.")
    found = resolve_mystery(solution, mystery, delay)
    if found:
        reason_it_out(world, kid, mystery, solution)
        reveal(world, adult, mystery)
        world.facts["found"] = True
    else:
        world.say(
            f"The first idea was not enough, so {kid.id} paused, looked again, and tried a better clue."
        )
        world.say(
            f"That was smart problem solving: keep looking, keep thinking, and do not give up."
        )
        world.facts["found"] = False
    world.para()
    ending(world, kid, adult, place)
    world.facts.update(place=place, mystery=mystery, magic=magic, solution=solution,
                       kid=kid, adult=adult, delay=delay, house=house, lantern=lantern)
    return world


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic",
        darkness="dusty dark",
        clue_spot="an old trunk",
        sound="the tick-tick of rain on the roof",
        spooky_image="A beam of silver moonlight slipped through a cracked window and made the dust look like floating ghosts.",
        feels="creaky",
        tags={"attic", "mystery"},
    ),
    "hall": Place(
        id="hall",
        label="the long hall",
        darkness="shadowy dark",
        clue_spot="a narrow table",
        sound="the hush of sleeping rooms",
        spooky_image="The wallpaper leaned in crooked stripes, and every shadow seemed to have a secret.",
        feels="quiet",
        tags={"hall", "mystery"},
    ),
    "garden_shed": Place(
        id="garden_shed",
        label="the garden shed",
        darkness="bumpy dark",
        clue_spot="a shelf of jars",
        sound="a sleepy wind tapping the tin roof",
        spooky_image="Tools hung from the walls like silent little ghosts, each one shiny in the moonlight.",
        feels="rusty",
        tags={"shed", "mystery"},
    ),
}

MYSTERIES = {
    "missing_key": Mystery(
        id="missing_key",
        missing="key",
        missing_phrase="the silver key",
        place_hint="trunk",
        clue="a tiny silver shine peeped from under a rug.",
        reveal="the silver key tucked inside a teacup",
        tags={"attic", "hall", "mystery"},
    ),
    "missing_note": Mystery(
        id="missing_note",
        missing="note",
        missing_phrase="the note in the jar",
        place_hint="jar",
        clue="there was paper dust near the shelf, like someone had just moved a page.",
        reveal="the note folded inside a lantern shade",
        tags={"garden_shed", "hall", "mystery"},
    ),
    "missing_cat": Mystery(
        id="missing_cat",
        missing="cat",
        missing_phrase="the little cat",
        place_hint="chair",
        clue="two soft paw prints crossed the floor and stopped at the curtain.",
        reveal="the sleepy cat curled behind a blanket",
        tags={"attic", "garden_shed", "mystery"},
    ),
}

MAGIC_TOOLS = {
    "charm_lantern": MagicTool(
        id="charm_lantern",
        label="a charm lantern",
        phrase="a charm lantern",
        effect="Its little light flickered blue and made the shadows blink back.",
        limit="It only glows when someone is calm and looking carefully.",
        tags={"magic", "light"},
    ),
    "glow_pebble": MagicTool(
        id="glow_pebble",
        label="a glow pebble",
        phrase="a glow pebble",
        effect="The pebble warmed up and gave off a soft pearly shine.",
        limit="It works best when held by a patient hand.",
        tags={"magic", "light"},
    ),
}

SOLUTIONS = {
    "look_closer": Solution(
        id="look_closer",
        sense=3,
        power=3,
        text="looked closer and followed the clue until the answer came into view",
        fail="looked closer, but still missed the answer",
        qa_text="I think we should follow the clue and check the places where it makes sense to hide.",
        tags={"problem_solving", "clue"},
    ),
    "ask_gently": Solution(
        id="ask_gently",
        sense=2,
        power=2,
        text="asked the housekeeper gently, and the answer matched the clue",
        fail="asked gently, but the answer was not enough",
        qa_text="Let us ask kindly and listen to the clue together.",
        tags={"problem_solving", "asking"},
    ),
    "search_twice": Solution(
        id="search_twice",
        sense=3,
        power=4,
        text="searched twice, then found the hiding place the second time around",
        fail="searched twice, but the answer was still hidden",
        qa_text="We should search again, because mysteries sometimes need a second look.",
        tags={"problem_solving", "search"},
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Lily", "Ava", "Zoe"]
BOY_NAMES = ["Noah", "Theo", "Finn", "Ben", "Max"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    magic: str
    solution: str
    kid_name: str
    kid_gender: str
    adult_name: str
    adult_gender: str
    delay: int = 0
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for m in MYSTERIES:
            for s in SOLUTIONS:
                if mystery_at_risk(MYSTERIES[m], PLACES[p]):
                    combos.append((p, m, s))
    return combos


def explain_rejection(place: Place, mystery: Mystery) -> str:
    return (
        f"(No story: {mystery.missing_phrase} does not fit this place's clues well enough. "
        f"Pick a place whose hidden spots make the mystery believable.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost-story mystery about smart problem solving and magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--magic", choices=MAGIC_TOOLS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["woman", "man"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
    if args.place and args.mystery:
        if not mystery_at_risk(MYSTERIES[args.mystery], PLACES[args.place]):
            raise StoryError(explain_rejection(PLACES[args.place], MYSTERIES[args.mystery]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, solution = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    adult = args.adult or (f"Aunt {rng.choice(['June', 'Mabel', 'Dot'])}" if adult_gender == "woman" else f"Uncle {rng.choice(['Ray', 'Pete', 'Sam'])}")
    magic = args.magic or rng.choice(sorted(MAGIC_TOOLS))
    return StoryParams(
        place=place,
        mystery=mystery,
        magic=magic,
        solution=solution,
        kid_name=name,
        kid_gender=gender,
        adult_name=adult,
        adult_gender=adult_gender,
        delay=args.delay,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story mystery for a 3-to-5-year-old that includes the word "smartypants" and shows careful problem solving.',
        f"Tell a gentle spooky story where {f['kid'].id}, nicknamed smartypants, uses magic to help solve {f['mystery'].missing_phrase}.",
        f"Write a child-friendly mystery in an old house where a clue, a little magic light, and smart problem solving lead to an answer.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid, adult, mystery, place, magic = f["kid"], f["adult"], f["mystery"], f["place"], f["magic"]
    return [
        ("Who is the story about?",
         f"It is about {kid.id}, who is nicknamed smartypants, and {adult.id}. They go into {place.label} to solve a mystery."),
        ("What was missing?",
         f"{mystery.missing_phrase} was missing. That was the mystery they had to solve."),
        ("How did the child help solve the mystery?",
         f"{kid.id} looked carefully, used {magic.phrase}, and kept using problem solving until the clue made sense. That is how the answer was found."),
        ("How did the story end?",
         f"They found {mystery.reveal}, and the house felt cozy again. The spooky feeling changed into a warm, solved feeling."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a mystery?",
         "A mystery is something that is missing or confusing, so people have to look for clues and think carefully to solve it."),
        ("What does problem solving mean?",
         "Problem solving means noticing a problem, thinking about clues, and trying a sensible way to fix it."),
        ("What is magic in a story?",
         "Magic is a special story idea that can make strange lights, charms, or surprises happen. In a story, it can help show wonder."),
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
magic_help :- tool(lantern), glow(lantern), not solved.
solved :- clue_seen, smart_think.
smart_think :- kid(smartypants).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for tid in MAGIC_TOOLS:
        lines.append(asp.fact("tool", tid))
    for sid in SOLUTIONS:
        lines.append(asp.fact("solution", sid))
    lines.append(asp.fact("smart_kid", "smartypants"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show smart_think/0."))
    ok = bool(model)
    p = resolve_params(argparse.Namespace(place=None, mystery=None, magic=None, solution=None, name=None, gender=None, adult=None, adult_gender=None, delay=0), random.Random(1))
    try:
        sample = generate(p)
        print("OK: normal generate() succeeded.")
    except Exception as err:
        print(f"FAIL: generate() crashed: {err}")
        return 1
    if not ok:
        print("FAIL: ASP check did not derive the expected smart_think atom.")
        return 1
    print("OK: ASP twin is reachable and generate() smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.magic not in MAGIC_TOOLS or params.solution not in SOLUTIONS:
        raise StoryError("Invalid story parameters.")
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], MAGIC_TOOLS[params.magic], SOLUTIONS[params.solution],
                 kid_name=params.kid_name, kid_gender=params.kid_gender, adult_name=params.adult_name, adult_gender=params.adult_gender, delay=params.delay)
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


CURATED = [
    StoryParams(place="attic", mystery="missing_key", magic="charm_lantern", solution="look_closer", kid_name="Mina", kid_gender="girl", adult_name="Aunt June", adult_gender="woman", delay=0),
    StoryParams(place="hall", mystery="missing_note", magic="glow_pebble", solution="search_twice", kid_name="Theo", kid_gender="boy", adult_name="Uncle Ray", adult_gender="man", delay=0),
    StoryParams(place="garden_shed", mystery="missing_cat", magic="charm_lantern", solution="ask_gently", kid_name="Lily", kid_gender="girl", adult_name="Aunt Mabel", adult_gender="woman", delay=0),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show smart_think/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
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
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
