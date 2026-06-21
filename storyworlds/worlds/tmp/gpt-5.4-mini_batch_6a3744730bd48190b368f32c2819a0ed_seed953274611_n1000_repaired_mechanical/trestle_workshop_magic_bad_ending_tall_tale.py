#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/trestle_workshop_magic_bad_ending_tall_tale.py
===============================================================================

A standalone story world for a tall-tale workshop tale about a trestle, a bit of
magic, and a bad ending when the boastful plan goes wrong.

The premise is small and classical:
- A workshop holds a tall trestle.
- A child or helper discovers a magic shortcut for raising a thing.
- A warning is ignored.
- The magic works too well or too wildly.
- The ending proves the mistake by leaving the workshop broken, lopsided, or
  filled with soot and regret.

The world is simulation-driven: characters and objects have physical meters and
emotional memes, and the story is rendered from the resulting state rather than
from a frozen text template.
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
MAGIC_MIN = 1
BAD_END_MIN = 1


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
        feminine = {"girl", "mother", "woman", "aunt"}
        masculine = {"boy", "father", "man", "uncle"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
    weather: str = ""
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
class Project:
    id: str
    name: str
    thing: str
    verb: str
    purpose: str
    size: str
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
class Magic:
    id: str
    name: str
    effect: str
    risk: str
    cue: str
    power: int
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
class Hazard:
    id: str
    name: str
    label: str
    spread: int
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
        clone.facts = dict(self.facts)
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


def _r_scorch(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["burning"] < THRESHOLD:
            continue
        sig = ("scorch", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "workshop" in world.entities:
            world.get("workshop").meters["wrecked"] += 1
        for who in list(world.entities.values()):
            if who.kind == "character":
                who.memes["fear"] += 1
        out.append("__scorch__")
    return out


CAUSAL_RULES: list[Rule] = [Rule("scorch", "physical", _r_scorch)]


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


def magic_possible(magic: Magic, project: Project) -> bool:
    return magic.power >= MAGIC_MIN and project.size in {"small", "tall", "wide"}


def bad_ending_possible(project: Project, hazard: Hazard, delay: int) -> bool:
    return hazard.spread + delay > 0


def ending_of(magic: Magic, project: Project, hazard: Hazard, delay: int) -> str:
    if not magic_possible(magic, project):
        return "invalid"
    return "bad" if bad_ending_possible(project, hazard, delay) else "safe"


def predict(world: World, project: Project, magic: Magic, hazard: Hazard) -> dict:
    sim = world.copy()
    _do_magic(sim, sim.get("helper"), project, magic, hazard, narrate=False)
    return {
        "burning": sim.get(project.thing).meters["burning"] >= THRESHOLD,
        "wrecked": sim.get("workshop").meters["wrecked"],
    }


def _do_magic(world: World, actor: Entity, project: Project, magic: Magic, hazard: Hazard, narrate: bool = True) -> None:
    thing = world.get(project.thing)
    thing.meters["lifted"] += 1
    thing.memes["hope"] += 1
    if project.name == "trestle":
        thing.meters["tipped"] += 1
    if hazard.spread:
        thing.meters["burning"] += 1
        propagate(world, narrate=narrate)


def tell(setting: Setting, project: Project, magic: Magic, hazard: Hazard,
         helper_name: str = "Mina", helper_type: str = "girl",
         warn_name: str = "Old Gus", warn_type: str = "man",
         delay: int = 1) -> World:
    world = World()
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type,
                              role="helper", traits=["bold"]))
    warn = world.add(Entity(id=warn_name, kind="character", type=warn_type,
                            role="warner", traits=["careful"]))
    workshop = world.add(Entity(id="workshop", type="room", label="the workshop"))
    thing = world.add(Entity(id=project.thing, type="project", label=project.name))
    sparks = world.add(Entity(id=hazard.id, type="hazard", label=hazard.label))
    world.add(Entity(id="magic", type="magic", label=magic.name))

    helper.memes["wonder"] = 1
    warn.memes["caution"] = 2
    world.facts["setting"] = setting
    world.facts["project"] = project
    world.facts["magic"] = magic
    world.facts["hazard"] = hazard
    world.facts["delay"] = delay

    world.say(
        f"In a noisy workshop as wide as a wagon shed, {helper.id} spotted a "
        f"{project.name} waiting by the trestle, and {setting.place} rang with "
        f"hammer taps and dust motes."
    )
    world.say(
        f"{helper.id} wanted to {project.verb} it at once. {project.purpose} "
        f"seemed like a fine idea, and the tall trestle stood there like a "
        f"patient giant."
    )
    world.para()
    world.say(
        f"Then {helper.id} found {magic.name}. {magic.cue} promised to {magic.effect}, "
        f"but it carried {magic.risk}."
    )
    world.say(
        f'"That sort of magic is a wild mule," {warn.id} said. '
        f'"It belongs nowhere near a workshop trestle."'
    )

    pred = predict(world, project, magic, hazard)
    world.facts["predicted_burning"] = pred["burning"]
    world.facts["predicted_wreck"] = pred["wrecked"]

    world.para()
    helper.memes["defiance"] += 1
    world.say(
        f'{helper.id} only grinned. "If it can lift a fence post, it can lift a '
        f"trestle!" {helper.pronoun()} cried, and {helper.pronoun()} worked the spell."
    )
    _do_magic(world, helper, project, magic, hazard, narrate=True)

    world.para()
    thing.meters["charred"] += 1
    workshop.meters["wrecked"] += 1
    helper.memes["regret"] += 2
    warn.memes["sadness"] += 1
    world.say(
        f"The magic leaped higher than a fiddler's hat. The {project.name} "
        f"tilted, the trestle skated sideways, and a puff of sparks kissed the "
        f"rafters. By the time the smoke rolled out, the workshop looked like a "
        f"storm had played a tune on it."
    )
    world.say(
        f"At last the {project.name} lay bent and blackened, and the trestle "
        f"stood crooked as a drunk chimney."
    )
    world.say(
        f"{warn.id} shook {warn.pronoun('possessive')} head. "
        f'"A workshop is for steady hands, not swaggering spells," {warn.id} said, '
        f'and {helper.id} had nothing bright to answer back.'
    )

    outcome = ending_of(magic, project, hazard, delay)
    world.facts["outcome"] = outcome
    world.facts["helper"] = helper
    world.facts["warner"] = warn
    world.facts["workshop"] = workshop
    world.facts["thing"] = thing
    return world


SETTINGS = {
    "workshop": Setting(
        id="workshop",
        place="the workshop",
        weather="dusty",
        tags={"workshop"},
    )
}

PROJECTS = {
    "trestle": Project(
        id="trestle",
        name="trestle",
        thing="trestle",
        verb="raise the trestle with a snap of magic",
        purpose="The plan was to lift it straight and fast",
        size="tall",
        tags={"trestle", "wood", "tall_tale"},
    ),
    "beam": Project(
        id="beam",
        name="beam",
        thing="beam",
        verb="raise the beam with a snap of magic",
        purpose="The plan was to lift it straight and fast",
        size="wide",
        tags={"beam", "wood", "tall_tale"},
    ),
}

MAGICS = {
    "glove": Magic(
        id="glove",
        name="a glittering glove spell",
        effect="raise anything it touched",
        risk="a habit of shaking loose at the worst possible time",
        cue="The glove sparkled like a pocket-sized lightning storm",
        power=2,
        tags={"magic", "glove"},
    ),
    "bell": Magic(
        id="bell",
        name="a brass bell charm",
        effect="make the whole beam hop and bob",
        risk="a taste for runaway echoes",
        cue="The bell chimed soft as a whisper before it rang like noon",
        power=1,
        tags={"magic", "bell"},
    ),
}

HAZARDS = {
    "sparks": Hazard(
        id="sparks",
        name="sparks",
        label="hot sparks",
        spread=1,
        tags={"sparks", "fire", "bad_ending"},
    ),
    "ember": Hazard(
        id="ember",
        name="ember",
        label="a red ember",
        spread=2,
        tags={"ember", "fire", "bad_ending"},
    ),
}

HELPER_NAMES = ["Mina", "Jeb", "Tilly", "Otis", "Pearl", "Rufus"]
WARNER_NAMES = ["Old Gus", "Aunt Cora", "Mr. Wren", "Nell", "Hank"]
GENDERS = {"girl": "girl", "boy": "boy", "woman": "woman", "man": "man"}


@dataclass
class StoryParams:
    setting: str
    project: str
    magic: str
    hazard: str
    helper_name: str = "Mina"
    helper_type: str = "girl"
    warner_name: str = "Old Gus"
    warner_type: str = "man"
    delay: int = 1
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, p in PROJECTS.items():
            for mid, m in MAGICS.items():
                for hid, h in HAZARDS.items():
                    if magic_possible(m, p) and bad_ending_possible(p, h, 1):
                        combos.append((sid, pid, mid, hid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale workshop storyworld with trestle, magic, and a bad ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--delay", type=int, default=None)
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
    if args.project and args.magic:
        if not magic_possible(MAGICS[args.magic], PROJECTS[args.project]):
            raise StoryError("(No story: that magic cannot reasonably do the lifting.)")
    if args.project and args.hazard:
        if not bad_ending_possible(PROJECTS[args.project], HAZARDS[args.hazard], args.delay or 1):
            raise StoryError("(No story: that hazard would not produce a bad ending.)")
    combos = [c for c in valid_combos()
              if args.setting in (None, c[0])
              and args.project in (None, c[1])
              and args.magic in (None, c[2])
              and args.hazard in (None, c[3])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, project, magic, hazard = rng.choice(sorted(combos))
    helper_name = rng.choice(HELPER_NAMES)
    warner_name = rng.choice([n for n in WARNER_NAMES if n != helper_name])
    helper_type = rng.choice(["girl", "boy"])
    warner_type = rng.choice(["woman", "man"])
    delay = args.delay if args.delay is not None else rng.randint(1, 2)
    return StoryParams(
        setting=setting,
        project=project,
        magic=magic,
        hazard=hazard,
        helper_name=helper_name,
        helper_type=helper_type,
        warner_name=warner_name,
        warner_type=warner_type,
        delay=delay,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: Project = f["project"]
    m: Magic = f["magic"]
    return [
        f'Write a tall-tale story set in a workshop that includes the word "{p.name}" and a little magic.',
        f"Tell a story where somebody tries to use {m.name} to {p.verb}, but the plan goes wrong in a workshop.",
        f"Write a bad-ending workshop tale about a trestle, a risky spell, and a lesson learned too late.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    helper: Entity = f["helper"]
    warner: Entity = f["warner"]
    project: Project = f["project"]
    magic: Magic = f["magic"]
    workshop: Entity = f["workshop"]
    thing: Entity = f["thing"]
    qa = [
        QAItem(
            question="What was the story about?",
            answer=(
                f"It was about {helper.id} in the workshop trying to use {magic.name} "
                f"to lift the {project.name}. The tall trestle made the plan feel grand, "
                f"but it also made the trouble bigger."
            ),
        ),
        QAItem(
            question=f"Why did {warner.id} warn {helper.id}?",
            answer=(
                f"{warner.id} warned {helper.id} because {magic.name} had {magic.risk}, "
                f"and that kind of wild help was not safe in a workshop. "
                f"The warning fit the danger because the trestle and sparks were both easy to upset."
            ),
        ),
        QAItem(
            question="How did the workshop change by the end?",
            answer=(
                f"It ended up wrecked and smoky. The {thing.label_word} was bent and blackened, "
                f"and the workshop itself was left looking crooked and tired."
            ),
        ),
    ]
    if f.get("predicted_burning"):
        qa.append(
            QAItem(
                question="What did the world model predict before the spell was cast?",
                answer=(
                    f"It predicted that the magic would set the {project.name} burning and wreck the workshop. "
                    f"That is why the warning mattered, even though {helper.id} ignored it."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    project: Project = f["project"]
    magic: Magic = f["magic"]
    hazard: Hazard = f["hazard"]
    items = [
        QAItem(
            question="What is a trestle?",
            answer="A trestle is a sturdy support frame. People use one to hold up something long or heavy while they work.",
        ),
        QAItem(
            question="What is magic in a tall tale?",
            answer="Magic is the make-believe force that can do impossible things in a story. It is useful in tall tales because it makes ordinary work swing bigger than life.",
        ),
        QAItem(
            question="Why are sparks dangerous in a workshop?",
            answer="Sparks are dangerous because they are tiny hot bits that can jump onto wood or dust. In a workshop, that can start a fire fast.",
        ),
        QAItem(
            question="Why should people be careful around a trestle?",
            answer="A trestle can tip or wobble if something heavy is lifted the wrong way. Being careful keeps the work and the people safe.",
        ),
    ]
    if project.name == "trestle":
        items.append(QAItem(
            question="Why does the word trestle fit this story?",
            answer="Because the trestle is the big wooden support at the center of the trouble. It is the thing the magic was supposed to raise, and the bad ending proves how badly that went.",
        ))
    if magic.name:
        items.append(QAItem(
            question="What makes a spell risky?",
            answer="A spell is risky when it does not stop where you want it to stop. Then the help turns into a mess, which is exactly what happened here.",
        ))
    return items


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.project not in PROJECTS:
        raise StoryError("Unknown project.")
    if params.magic not in MAGICS:
        raise StoryError("Unknown magic.")
    if params.hazard not in HAZARDS:
        raise StoryError("Unknown hazard.")
    if params.delay < 0:
        raise StoryError("Delay cannot be negative.")

    setting = SETTINGS[params.setting]
    project = PROJECTS[params.project]
    magic = MAGICS[params.magic]
    hazard = HAZARDS[params.hazard]
    if not magic_possible(magic, project):
        raise StoryError("(No story: the chosen magic is not a fit for the project.)")

    world = tell(setting, project, magic, hazard, params.helper_name, params.helper_type,
                 params.warner_name, params.warner_type, params.delay)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(S,P,M,H) :- setting(S), project(P), magic(M), hazard(H),
                  power(M, Pow), min_power(Min), Pow >= Min,
                  project_size(P, Sz), size_ok(Sz),
                  spread(H, Sp), delay(D), Sp + D > 0.
ending(bad) :- valid(_,_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("project_size", pid, p.size))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("power", mid, m.power))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("spread", hid, h.spread))
    lines.append(asp.fact("min_power", MAGIC_MIN))
    lines.append(asp.fact("size_ok", "small"))
    lines.append(asp.fact("size_ok", "tall"))
    lines.append(asp.fact("size_ok", "wide"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo gate:")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))

    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def explain_rejection() -> str:
    return "(No story: this combination would not make a plausible bad-ending workshop tale.)"


CURATED = [
    StoryParams(
        setting="workshop",
        project="trestle",
        magic="glove",
        hazard="sparks",
        helper_name="Mina",
        helper_type="girl",
        warner_name="Old Gus",
        warner_type="man",
        delay=1,
    ),
    StoryParams(
        setting="workshop",
        project="beam",
        magic="bell",
        hazard="ember",
        helper_name="Jeb",
        helper_type="boy",
        warner_name="Aunt Cora",
        warner_type="woman",
        delay=2,
    ),
]


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible workshop combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.helper_name}: {p.project} with {p.magic} in the workshop"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
