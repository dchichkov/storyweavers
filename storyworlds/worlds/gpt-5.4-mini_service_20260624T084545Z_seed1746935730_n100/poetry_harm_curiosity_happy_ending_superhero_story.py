#!/usr/bin/env python3
"""
storyworlds/worlds/poetry_harm_curiosity_happy_ending_superhero_story.py
=========================================================================

A small superhero storyworld built from the seed idea:
curiosity leads a child hero toward poetry, but a harmful trap is avoided,
and the story ends happily.

The domain stays small and classical:
- one curious hero
- one protector/mentor
- one harm source
- one poetry object or message
- one concrete rescue/fix
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    mentor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "aunt"}
        male = {"boy", "man", "father", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str
    indoors: bool = False
    danger: str = ""
    noise: str = ""
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Plot:
    id: str
    want: str
    delight: str
    risk: str
    harm: str
    rescue: str
    ending: str
    clue: str
    tag: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Shield:
    id: str
    label: str
    phrase: str
    blocks: set[str]
    reply: str
    tail: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def one_para(world: World, text: str) -> None:
    world.say(text)


def danger_happens(world: World, hero: Entity, plot: Plot) -> bool:
    return hero.memes.get("curiosity", 0.0) >= THRESHOLD and not hero.meters.get("safe", 0.0)


def predict_harm(world: World, hero: Entity, plot: Plot) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["safe"] = 0.0
    sim.get(hero.id).memes["curiosity"] += 1.0
    return {"hurt": danger_happens(sim, sim.get(hero.id), plot)}


def apply_plot(world: World, hero: Entity, mentor: Entity, plot: Plot, shield: Optional[Shield]) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["hope"] += 1
    one_para(world, f"{hero.id} was a young superhero who loved {plot.want}.")
    one_para(world, f"One day, {plot.delight} near {world.setting.place} made {hero.id} look up in wonder.")
    world.para()
    one_para(world, f"{hero.id} wanted to {plot.want}, because {plot.delight} felt like a secret song.")
    if predict_harm(world, hero, plot)["hurt"]:
        hero.memes["worry"] += 1
        one_para(world, f"But {world.setting.danger} could cause {plot.harm}, and {mentor.label} noticed it first.")
        one_para(world, f'"{plot.clue}," {mentor.id} said, and {hero.id} listened carefully.')
        if shield:
            hero.meters["safe"] = 1.0
            hero.memes["trust"] += 1
            world.para()
            one_para(world, f'{mentor.id} gave {hero.id} {shield.phrase}. {shield.reply.capitalize()}, {hero.id} said.')
            one_para(world, f"Then {hero.id} could {plot.want} without any {plot.harm}, and {plot.ending}.")
            one_para(world, f"At the end, {plot.tail if hasattr(plot, 'tail') else ''}".strip())
            hero.memes["joy"] += 1
        else:
            pass
    else:
        hero.meters["safe"] = 1.0
        one_para(world, f"There was no real harm, so {hero.id} could follow the clue and keep the day bright.")
        one_para(world, f"That made the story end with {plot.ending}.")


SETTINGS = {
    "rooftop": Setting(place="the rooftop garden", indoors=False, danger="a loose storm wire", noise="wind"),
    "library": Setting(place="the quiet library", indoors=True, danger="a falling stack of books", noise="silence"),
    "alley": Setting(place="the brick alley", indoors=False, danger="a hidden puddle of slick oil", noise="echoes"),
    "stage": Setting(place="the little city stage", indoors=False, danger="a cracked speaker wire", noise="music"),
}

PLOTS = {
    "poem": Plot(
        id="poem",
        want="read a poem aloud",
        delight="the rhymes sounded brave and bright",
        risk="a harmful shock",
        harm="a painful jolt",
        rescue="hold the wire away with a glove",
        ending="the crowd cheered under a clear sky",
        clue="Use a glove and trust your eyes",
        tag="poetry",
    ),
    "rhyme": Plot(
        id="rhyme",
        want="deliver a rhyme to the crowd",
        delight="the words bounced like tiny stars",
        risk="a slippery fall",
        harm="a bruising tumble",
        rescue="step only on the painted stones",
        ending="the children clapped with big smiles",
        clue="Look before you leap",
        tag="poetry",
    ),
    "verse": Plot(
        id="verse",
        want="carry a verse to the mayor",
        delight="the lines felt like a secret cape",
        risk="a strong gust of harm",
        harm="a torn paper spill",
        rescue="slide the verse into a lantern sleeve",
        ending="the mayor smiled and waved from the steps",
        clue="Keep the verse tucked safe",
        tag="poetry",
    ),
}

SHIELDS = {
    "glove": Shield(
        id="glove",
        label="a blue glove",
        phrase="a blue glove that could hold the wire away",
        blocks={"shock"},
        reply="It will keep you safe",
        tail="the glove blocked the danger and the poem reached every ear",
    ),
    "stone": Shield(
        id="stone",
        label="the painted stones",
        phrase="the painted stones across the path",
        blocks={"fall"},
        reply="It will keep your feet steady",
        tail="the stones led the way and the rhyme stayed safe",
    ),
    "lantern": Shield(
        id="lantern",
        label="a lantern sleeve",
        phrase="a lantern sleeve for the paper",
        blocks={"gust"},
        reply="It will keep the verse tucked in",
        tail="the lantern sleeve kept the page safe and the verse stayed neat",
    ),
}

HERO_NAMES = ["Nova", "Milo", "Zara", "Iris", "Jude", "Piper"]
MENTOR_NAMES = ["Captain Bright", "Aunt Comet", "Professor Glow", "Guardian Gale"]


@dataclass
class StoryParams:
    setting: str
    plot: str
    hero: str
    mentor: str
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def asp_facts() -> str:
    import asp

    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
    for pid, p in PLOTS.items():
        lines.append(asp.fact("plot", pid))
        lines.append(asp.fact("risk", pid, p.risk))
        lines.append(asp.fact("harm", pid, p.harm))
        lines.append(asp.fact("tag", pid, p.tag))
    for gid, g in SHIELDS.items():
        lines.append(asp.fact("shield", gid))
        for b in sorted(g.blocks):
            lines.append(asp.fact("blocks", gid, b))
    return "\n".join(lines)


ASP_RULES = r"""
safe_plot(P) :- plot(P), risk(P, R), shield(G), blocks(G, R).
valid_story(S, P) :- setting(S), plot(P), safe_plot(P).
#show valid_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid in SETTINGS:
        for pid, p in PLOTS.items():
            if any(p.risk.endswith(x) for x in ("shock", "fall", "gust")):
                if p.id in SHIELDS:
                    pass
            if p.id == "poem" and "glove" in SHIELDS:
                out.append((sid, pid))
            elif p.id == "rhyme" and "stone" in SHIELDS:
                out.append((sid, pid))
            elif p.id == "verse" and "lantern" in SHIELDS:
                out.append((sid, pid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld with poetry, harm, curiosity, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plot", choices=PLOTS)
    ap.add_argument("--hero")
    ap.add_argument("--mentor")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "plot", None):
        combos = [c for c in combos if c[1] == getattr(args, "plot", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, plot = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    mentor = getattr(args, "mentor", None) or rng.choice(MENTOR_NAMES)
    return StoryParams(setting=setting, plot=plot, hero=hero, mentor=mentor)


def tell(params: StoryParams) -> tuple[World, Entity, Entity, Plot, Optional[Shield]]:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id=params.hero, kind="character", type="girl" if params.hero in {"Nova", "Zara", "Iris", "Piper"} else "boy"))
    mentor = world.add(Entity(id=params.mentor, kind="character", type="woman", label=params.mentor))
    plot = _safe_lookup(PLOTS, params.plot)

    shield = None
    if plot.id == "poem":
        shield = SHIELDS["glove"]
    elif plot.id == "rhyme":
        shield = SHIELDS["stone"]
    elif plot.id == "verse":
        shield = SHIELDS["lantern"]

    world.facts.update(hero=hero, mentor=mentor, plot=plot, shield=shield)
    apply_plot(world, hero, mentor, plot, shield)
    return world, hero, mentor, plot, shield


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    mentor = world.facts["mentor"]
    plot = world.facts["plot"]
    return [
        QAItem(
            question=f"Why did {hero.id} want to {plot.want}?",
            answer=f"{hero.id} wanted to {plot.want} because {plot.delight}. That made curiosity pull {hero.pronoun('subject')} forward.",
        ),
        QAItem(
            question=f"What harmful thing was the mentor trying to avoid?",
            answer=f"{mentor.label} was trying to avoid {plot.harm}, because the danger could turn the brave poetry moment into trouble.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: {plot.ending}. The hero stayed safe, and the poem or verse still reached the people.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    plot = world.facts["plot"]
    return [
        QAItem(
            question="What is poetry?",
            answer="Poetry is writing that uses rhythm, sound, and careful words to create a feeling or picture in your mind.",
        ),
        QAItem(
            question="Why can harm be dangerous?",
            answer="Harm is dangerous because it can hurt a person, break something important, or ruin a safe plan.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to look, ask, and learn more about what they do not know yet.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    plot = world.facts["plot"]
    hero = world.facts["hero"]
    mentor = world.facts["mentor"]
    return [
        f"Write a superhero story where {hero.id} is curious about poetry and avoids {plot.harm}.",
        f"Tell a child-friendly story with {hero.id}, {mentor.label}, and a happy ending after a close call.",
        f"Create a short action story about {plot.want} without letting harm win.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world, hero, mentor, plot, shield = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/2."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python combos.")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(setting="rooftop", plot="poem", hero="Nova", mentor="Captain Bright"),
    StoryParams(setting="library", plot="verse", hero="Iris", mentor="Professor Glow"),
    StoryParams(setting="stage", plot="rhyme", hero="Zara", mentor="Aunt Comet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for sid, pid in combos:
            print(f"  {sid:10} {pid}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero}: {p.plot} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
