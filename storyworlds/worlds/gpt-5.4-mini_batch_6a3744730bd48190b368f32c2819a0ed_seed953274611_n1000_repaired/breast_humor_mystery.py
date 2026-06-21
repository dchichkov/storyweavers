#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/breast_humor_mystery.py
=======================================================

A small standalone story world for a humorous mystery about a child detective,
a puzzling clue, and a harmless final reveal.

Premise
-------
A child and a birdkeeper are trying to solve a tiny mystery: why a robin keeps
showing up with crumbs on its breast, and where a missing shiny button went.
The story stays close to mystery style, but the turns are gentle and funny.

This world models:
- typed entities with physical meters and emotional memes
- a forward-chained causal world state
- a reasonableness gate and inline ASP twin
- three Q&A sets grounded in the simulated world

The required seed word is included in the domain vocabulary via the bird's
breast clue.
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
    role: str = ""
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
class Setting:
    id: str
    place: str
    mood: str
    detail: str
    indoors: bool = False
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
class Suspect:
    id: str
    label: str
    clue: str
    habit: str
    funny: str
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
class ClueItem:
    id: str
    label: str
    phrase: str
    hidden_in: str
    reveals: str
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
class Resolution:
    id: str
    sense: int
    effect: str
    text: str
    reveal_text: str
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


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["mess"] < THRESHOLD:
            continue
        sig = ("mess", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "detective" in world.entities:
            world.get("detective").memes["curious"] += 1
        out.append("__clue__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("joke_found") and not world.facts.get("laughed"):
        world.facts["laughed"] = True
        if "detective" in world.entities:
            world.get("detective").memes["joy"] += 1
        out.append("The detective had to grin, because the answer was sillier than the clue.")
    return out


CAUSAL_RULES = [Rule("mess", "physical", _r_mess), Rule("laugh", "social", _r_laugh)]


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


def safe_combo(clue: ClueItem, suspect: Suspect) -> bool:
    return clue.reveals in suspect.tags


def sensible_resolutions() -> list[Resolution]:
    return [r for r in RESOLUTIONS.values() if r.sense >= SENSE_MIN]


def clue_strength(clue: ClueItem, delay: int) -> int:
    return 1 + delay


def is_enough(resolution: Resolution, clue: ClueItem, delay: int) -> bool:
    return resolution.effect == clue.reveals or resolution.sense >= clue_strength(clue, delay)


def predict(world: World, clue: ClueItem, suspect: Suspect) -> dict:
    sim = world.copy()
    sim.get("clue").meters["mess"] += 1
    propagate(sim, narrate=False)
    sim.facts["joke_found"] = safe_combo(clue, suspect)
    return {"messy": sim.get("clue").meters["mess"] >= THRESHOLD, "funny": sim.facts["joke_found"]}


def setup(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["curious"] += 1
    helper.memes["patient"] += 1
    world.say(
        f"On a bright afternoon, {child.id} and {helper.id} wandered through {setting.place}. "
        f"{setting.detail}"
    )
    world.say(
        f'{child.id} was trying to solve a tiny mystery, and {helper.id} promised to help.'
    )


def introduce_clue(world: World, child: Entity, clue: ClueItem) -> None:
    world.say(
        f"Then {child.id} noticed a clue: {clue.phrase}. It had been found {clue.hidden_in}, "
        f"and it pointed toward {clue.reveals}."
    )
    world.say(
        f"That was odd enough to make {child.id} scrunch {child.pronoun('possessive')} nose."
    )


def question(world: World, child: Entity, suspect: Suspect, clue: ClueItem) -> None:
    child.memes["suspicion"] += 1
    world.say(
        f'{child.id} pointed and whispered, "Could {suspect.label} be the one?" '
        f"{suspect.funny}."
    )
    world.say(
        f"The clue seemed to match {suspect.habit}, but not quite in a serious way."
    )


def warn(world: World, helper: Entity, child: Entity, suspect: Suspect, clue: ClueItem) -> None:
    pred = predict(world, clue, suspect)
    helper.memes["care"] += 1
    world.facts["predicted_funny"] = pred["funny"]
    world.say(
        f'{helper.id} said, "Let’s not blame anyone yet. A clue can point to the truth, '
        f'but it can also point to a joke."'
    )
    if pred["messy"]:
        world.say(
            f'{helper.id} added, "That crumb on the breast looks like a clue, but we should '
            f'look closer before we guess."'
        )


def investigate(world: World, child: Entity, suspect: Suspect, clue: ClueItem) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} peered at {suspect.label} and the little crumb on its breast. "
        f"The bird only puffed up like a tiny feathered puffball."
    )


def reveal(world: World, child: Entity, helper: Entity, clue: ClueItem, suspect: Suspect, resolution: Resolution) -> None:
    world.facts["joke_found"] = True
    propagate(world, narrate=False)
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"At last, {child.id} found the answer: {resolution.text}. "
        f"{resolution.reveal_text.format(clue=clue.label, suspect=suspect.label)}"
    )
    world.say(
        f"The whole mystery turned out to be funny, not frightening, and {suspect.label} gave one proud little hop."
    )


def ending(world: World, child: Entity, helper: Entity, setting: Setting, suspect: Suspect) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"By the time they left {setting.place}, {child.id} was laughing, and {suspect.label} "
        f"still had the tiny crumb on its breast like a badge."
    )
    world.say(
        f"Now the clue made sense, and the mystery felt solved."
    )


def tell(setting: Setting, suspect: Suspect, clue: ClueItem, resolution: Resolution,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Aunt June", helper_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    bird = world.add(Entity(id="bird", kind="character", type="bird", label=suspect.label))

    setup(world, child, helper, setting)
    world.para()
    introduce_clue(world, child, clue)
    question(world, child, bird, clue)
    warn(world, helper, child, suspect, clue)
    investigate(world, child, bird, clue)
    world.para()
    reveal(world, child, helper, clue, bird, resolution)
    ending(world, child, helper, setting, bird)

    world.facts.update(
        child=child,
        helper=helper,
        bird=bird,
        setting=setting,
        suspect=suspect,
        clue=clue,
        resolution=resolution,
        joke_found=True,
        solved=True,
    )
    return world


SETTINGS = {
    "garden": Setting(id="garden", place="the garden", mood="sunny", detail="The roses leaned toward a birdbath, and every leaf looked suspicious in the nicest way."),
    "yard": Setting(id="yard", place="the backyard", mood="breezy", detail="The fence creaked, the grass twinkled, and even the mailbox seemed to be hiding a secret."),
    "park": Setting(id="park", place="the park", mood="quiet", detail="A row of benches watched the path, and a squirrel sat very still like a tiny witness."),
}

SUSPECTS = {
    "robin": Suspect(id="robin", label="a robin", clue="crumbs", habit="picking up crumbs", funny="The robin looked innocent, with the most serious little eyes."),
    "duck": Suspect(id="duck", label="a duck", clue="splashes", habit="waddling through puddles", funny="The duck was too busy wobbling to look mysterious."),
    "cat": Suspect(id="cat", label="a cat", clue="whiskers", habit="sitting on warm things", funny="The cat blinked as if it had solved the case already."),
}

CLUES = {
    "crumb": ClueItem(id="crumb", label="crumb", phrase="a crumb on the bird's breast", hidden_in="on a stone by the path", reveals="crumbs", tags={"crumb", "breast"}),
    "feather": ClueItem(id="feather", label="feather", phrase="a bright feather stuck to a bench", hidden_in="under a leaf", reveals="whiskers", tags={"feather"}),
    "splash": ClueItem(id="splash", label="splash mark", phrase="a tiny splash mark near the puddle", hidden_in="beside the birdbath", reveals="splashes", tags={"splash"}),
}

RESOLUTIONS = {
    "crumbs": Resolution(id="crumbs", sense=3, effect="crumbs", text="the robin had merely been nibbling breakfast", reveal_text="It was only {suspect}, and the clue was just a breakfast crumb.", tags={"crumb"}),
    "joke": Resolution(id="joke", sense=4, effect="crumbs", text="the mystery was a funny one", reveal_text="The so-called clue matched {suspect}, but it was only a silly breakfast trail.", tags={"crumb"}),
    "warmth": Resolution(id="warmth", sense=2, effect="whiskers", text="the cat had been sitting in the sun", reveal_text="It turned out to be {suspect}, and the clue was just a warm place to sit.", tags={"cat"}),
}

SENSE_MIN = 2


@dataclass
class StoryParams:
    setting: str
    suspect: str
    clue: str
    resolution: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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
    for s in SETTINGS:
        for su, suspect in SUSPECTS.items():
            for c, clue in CLUES.items():
                if clue.reveals in suspect.tags:
                    combos.append((s, su, c))
    return combos


def explain_rejection(suspect: Suspect, clue: ClueItem) -> str:
    return f"(No story: {clue.label} does not match {suspect.label} in a believable way for this mystery.)"


def explain_resolution(rid: str) -> str:
    r = RESOLUTIONS[rid]
    better = " / ".join(sorted(x.id for x in sensible_resolutions()))
    return f"(Refusing resolution '{rid}': it is too weak for this mystery (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humorous mystery storyworld with a bird clue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
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
    if args.resolution and RESOLUTIONS[args.resolution].sense < SENSE_MIN:
        raise StoryError(explain_resolution(args.resolution))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.suspect is None or c[1] == args.suspect)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, suspect, clue = rng.choice(sorted(combos))
    resolution = args.resolution or rng.choice(sorted(r.id for r in sensible_resolutions()))
    child_name = "Mina" if rng.random() < 0.5 else "Noah"
    child_gender = "girl" if child_name == "Mina" else "boy"
    helper_name = "Aunt June"
    helper_gender = "woman"
    return StoryParams(setting=setting, suspect=suspect, clue=clue, resolution=resolution,
                       child_name=child_name, child_gender=child_gender,
                       helper_name=helper_name, helper_gender=helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a humorous mystery story for a young child set in {f["setting"].place} that includes the word "breast".',
        f"Tell a gentle detective story where {f['child'].id} follows a clue and discovers why {f['bird'].label} has crumbs on its breast.",
        f"Write a funny mystery with a small reveal at the end, using {f['suspect'].label} and a clue about a bird's breast.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, bird = f["child"], f["helper"], f["bird"]
    clue, setting, resolution = f["clue"], f["setting"], f["resolution"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}, who try to solve a tiny mystery in {setting.place}."),
        ("What clue did {0} notice?".format(child.id),
         f"{child.id} noticed {clue.phrase}. That clue made the bird look suspicious, even though it was only a small funny sign."),
        ("What did they learn at the end?",
         f"They learned that {resolution.text}. The answer was harmless, and that is why the story ends with laughter."),
    ]
    if f.get("joke_found"):
        qa.append((
            "Why was the clue funny?",
            f"It was funny because the crumb on {bird.label}'s breast looked dramatic, but it only meant breakfast. The mystery sounded bigger than it really was."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a clue?",
         "A clue is a small hint that can help solve a mystery. Clues can be things you see, hear, or find."),
        ("What is a mystery?",
         "A mystery is a puzzling question or problem where you have to look for hints to find the answer."),
        ("Why might a bird have crumbs on its breast?",
         "A bird can get crumbs on its breast if it has been pecking at food or brushing past something messy. That does not mean it did anything wrong."),
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="garden", suspect="robin", clue="crumb", resolution="crumbs",
                child_name="Mina", child_gender="girl", helper_name="Aunt June", helper_gender="woman"),
    StoryParams(setting="yard", suspect="duck", clue="splash", resolution="joke",
                child_name="Noah", child_gender="boy", helper_name="Aunt June", helper_gender="woman"),
    StoryParams(setting="park", suspect="cat", clue="feather", resolution="warmth",
                child_name="Mina", child_gender="girl", helper_name="Aunt June", helper_gender="woman"),
]


def tell_story(params: StoryParams) -> StorySample:
    return generate(params)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.suspect not in SUSPECTS or params.clue not in CLUES or params.resolution not in RESOLUTIONS:
        raise StoryError("(Invalid StoryParams: unknown setting, suspect, clue, or resolution.)")
    resolution = RESOLUTIONS[params.resolution]
    if resolution.sense < SENSE_MIN:
        raise StoryError(explain_resolution(params.resolution))
    setting = SETTINGS[params.setting]
    suspect = SUSPECTS[params.suspect]
    clue = CLUES[params.clue]
    if not safe_combo(clue, suspect):
        raise StoryError(explain_rejection(suspect, clue))
    world = tell(setting, suspect, clue, resolution, params.child_name, params.child_gender,
                 params.helper_name, params.helper_gender)
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
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        for t in sorted(s.tags):
            lines.append(asp.fact("suspect_tag", sid, t))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("reveals", cid, c.reveals))
    for rid, r in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
safe(C, S) :- clue(C), suspect(S), reveals(C, T), suspect_tag(S, T).
valid(Se, Su, Cl) :- setting(Se), suspect(Su), clue(Cl), safe(Cl, Su).
sensible(R) :- resolution(R), sense(R, N), sense_min(M), N >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos().")
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    if set(asp_sensible()) != {r.id for r in sensible_resolutions()}:
        rc = 1
        print("MISMATCH in sensible resolutions.")
    else:
        print(f"OK: sensible resolutions match ({sorted(asp_sensible())}).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous mystery storyworld with a bird clue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
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
    if args.resolution and RESOLUTIONS[args.resolution].sense < SENSE_MIN:
        raise StoryError(explain_resolution(args.resolution))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.suspect is None or c[1] == args.suspect)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, suspect, clue = rng.choice(sorted(combos))
    resolution = args.resolution or rng.choice(sorted(r.id for r in sensible_resolutions()))
    child_name = rng.choice(["Mina", "Noah", "Iris", "Theo"])
    child_gender = "girl" if child_name in {"Mina", "Iris"} else "boy"
    return StoryParams(
        setting=setting,
        suspect=suspect,
        clue=clue,
        resolution=resolution,
        child_name=child_name,
        child_gender=child_gender,
        helper_name="Aunt June",
        helper_gender="woman",
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible resolutions: {', '.join(asp_sensible())}\n")
        for se, su, cl in asp_valid_combos():
            print(f"  {se:8} {su:8} {cl}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
