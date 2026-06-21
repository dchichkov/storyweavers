#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/haven_star_cake_transformation_lesson_learned_pirate.py
========================================================================================

A standalone storyworld for a small pirate-tale domain built from the seed words
"haven", "star", and "cake", with two core features: Transformation and Lesson
Learned.

The story engine models a tiny crew on a sheltered harbor island. A child pirate
wants something shiny or special, gets tempted to do the wrong thing, learns a
lesson from a calm helper, and changes into a kinder helper by the end.

The world is intentionally small and classical:
- a haven where the crew can shelter
- a star-shaped cake that matters to everyone
- one tempting action that risks ruining the cake or hurting trust
- a turning point where a helper explains the consequence
- a transformation ending that proves the child changed

Run it:
    python storyworlds/worlds/gpt-5.4-mini/haven_star_cake_transformation_lesson_learned_pirate.py
    python storyworlds/worlds/gpt-5.4-mini/haven_star_cake_transformation_lesson_learned_pirate.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/haven_star_cake_transformation_lesson_learned_pirate.py --verify
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
LESSON_GAIN = 1.0
TRANSFORM_GAIN = 1.0


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
    edible: bool = False
    fragile: bool = False
    magical: bool = False
    safe_place: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
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
    mood: str
    detail: str
    sky: str
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
class Temptation:
    id: str
    label: str
    action: str
    risk: str
    consequence: str
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
class Helper:
    id: str
    label: str
    method: str
    lesson: str
    gift: str
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
class Outcome:
    id: str
    transform: str
    lesson_line: str
    ending_image: str
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


def _r_smear(world: World) -> list[str]:
    out = []
    cake = world.entities.get("cake")
    child = world.entities.get("child")
    if not cake or not child:
        return out
    if child.meters["greedy"] < THRESHOLD or cake.meters["covered"] >= THRESHOLD:
        return out
    sig = ("smear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cake.meters["smeared"] += 1
    cake.meters["ruined"] += 1
    child.memes["shame"] += 1
    out.append("__smear__")
    return out


def _r_stain_trust(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    friend = world.entities.get("friend")
    if not child or not friend:
        return out
    if child.meters["greedy"] < THRESHOLD:
        return out
    sig = ("trust",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["hurt"] += 1
    return ["__trust__"]
    return out


CAUSAL_RULES = [Rule("smear", _r_smear), Rule("trust", _r_stain_trust)]


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


def predictable_loss(world: World) -> bool:
    sim = world.copy()
    sim.get("child").meters["greedy"] += 1
    propagate(sim, narrate=False)
    return sim.get("cake").meters["ruined"] >= THRESHOLD


def tell(scene: Scene, temptation: Temptation, helper: Helper, outcome: Outcome,
         child_name: str = "Pip", child_type: str = "boy",
         friend_name: str = "Mara", friend_type: str = "girl",
         captain_name: str = "Captain Bell", captain_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name,
                             role="instigator", traits=["bold"], attrs={"name": child_name}))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name,
                              role="cautioner", traits=["kind"], attrs={"name": friend_name}))
    captain = world.add(Entity(id="captain", kind="character", type=captain_type, label=captain_name,
                               role="helper"))
    haven = world.add(Entity(id="haven", kind="thing", type="place", label="the haven",
                             safe_place=True, magical=True))
    cake = world.add(Entity(id="cake", kind="thing", type="cake", label="the star cake",
                            edible=True, fragile=True))
    chest = world.add(Entity(id="chest", kind="thing", type="thing", label="the picnic chest"))
    cake.meters["whole"] = 1.0
    child.memes["joy"] = 1.0
    friend.memes["care"] = 1.0

    world.say(
        f"At {scene.place}, the little crew had found a safe {scene.mood} haven. "
        f"{scene.detail}"
    )
    world.say(
        f"On the table sat {cake.label}, bright as a star under {scene.sky}. "
        f"It was the best cake the pirates had ever seen."
    )
    world.say(
        f"{child.label} leaned closer and said, \"{temptation.action}!\" "
        f"{friend.label} frowned and warned that it could {temptation.risk}."
    )

    world.para()
    child.meters["greedy"] += 1
    child.memes["want"] += 1
    if not predictable_loss(world):
        world.say(f"But the idea did not feel right for a cake like this, so {child.label} paused.")
    else:
        world.say(f"{child.label} reached for the cake anyway, and {temptation.consequence}.")
        propagate(world, narrate=False)
        cake.meters["covered"] += 0.0

    world.say(
        f"{friend.label} pointed at the cake and said, \"A haven is for keeping things safe, "
        f"not for taking without asking.\""
    )
    child.memes["listen"] += 1
    child.memes["greedy"] = 0.0
    child.memes["kind"] += 1
    child.meters["bright"] += TRANSFORM_GAIN
    world.say(
        f"{captain.label} came over with a calm smile. {captain.pronoun().capitalize()} did not scold. "
        f"Instead, {captain.pronoun()} cut the cake into honest pieces and handed one to each pirate."
    )

    world.para()
    world.say(
        f"{child.label} felt heat in {child.pronoun('possessive')} cheeks, then a new sort of pride. "
        f"{outcome.transform}"
    )
    world.say(
        f"{helper.method}. {helper.lesson} {helper.gift}."
    )
    world.say(
        f"In the end, {outcome.ending_image}."
    )

    child.memes["lesson"] += LESSON_GAIN
    child.memes["transformed"] += 1
    friend.memes["relief"] += 1
    cake.meters["served"] = 1.0
    cake.meters["ruined"] = 0.0
    cake.meters["whole"] = 1.0

    world.facts.update(
        scene=scene, temptation=temptation, helper=helper, outcome=outcome,
        child=child, friend=friend, captain=captain, haven=haven, cake=cake, chest=chest,
        transformed=child.memes["transformed"] >= THRESHOLD,
        lesson_learned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


SCENES = {
    "harbor": Scene(
        id="harbor",
        place="the harbor",
        mood="harbor",
        detail="Their ship bobbed beside the pier, and the gulls sounded like tiny spies.",
        sky="a clear moonlit sky",
        tags={"haven", "pirate", "star", "cake"},
    ),
    "island": Scene(
        id="island",
        place="the island cove",
        mood="island",
        detail="A ring of palms made a quiet shelter where the wind could not bite.",
        sky="a bright evening sky",
        tags={"haven", "pirate", "star", "cake"},
    ),
}

TEMPTATIONS = {
    "eat_first": Temptation(
        id="eat_first",
        label="eat_first",
        action="Let's take the biggest bite first",
        risk="crush the star decoration",
        consequence="the frosting slid off in a white splash",
        tags={"cake", "star"},
    ),
    "hide_slice": Temptation(
        id="hide_slice",
        label="hide_slice",
        action="I'll hide a slice in my pocket",
        risk="smear the cake and make everyone sad",
        consequence="the sugary crumbs stuck to every seam",
        tags={"cake", "lesson"},
    ),
}

HELPERS = {
    "share": Helper(
        id="share",
        label="share",
        method="The captain showed how to share the cake fairly, one neat slice at a time",
        lesson="The lesson was simple: a treasure tastes better when everyone gets some",
        gift="Soon the whole crew was smiling",
        tags={"lesson", "cake"},
    ),
    "apology": Helper(
        id="apology",
        label="apology",
        method="The child apologized and helped smooth the frosting back into a star",
        lesson="The lesson was simple: saying sorry and fixing a mess can be brave",
        gift="Then the room felt lighter",
        tags={"lesson", "star"},
    ),
}

OUTCOMES = {
    "transformed": Outcome(
        id="transformed",
        transform="That was the moment the pirate changed from grabby to generous",
        lesson_line="The child learned that a real pirate keeps promises and shares the best prize",
        ending_image="the star cake sat whole at the center of the haven while little hands passed slices around",
        tags={"transformation", "lesson"},
    ),
    "gentle": Outcome(
        id="gentle",
        transform="That was the moment the pirate became calmer and kinder",
        lesson_line="The child learned that listening early keeps a story sweet",
        ending_image="the star cake shone on the table while the crew laughed in the warm haven",
        tags={"transformation", "lesson"},
    ),
}

NAMES_BOY = ["Pip", "Jory", "Finn", "Milo", "Tate"]
NAMES_GIRL = ["Mara", "Luna", "Nell", "Sia", "Rina"]
PARENT_NAMES = ["Captain Bell", "Aunt Tessa", "Old Mara"]


@dataclass
class StoryParams:
    scene: str
    temptation: str
    helper: str
    outcome: str
    child_name: str
    child_type: str
    friend_name: str
    friend_type: str
    captain_name: str
    captain_type: str
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
    return [(s, t, h) for s in SCENES for t in TEMPTATIONS for h in HELPERS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale world with haven, star, cake, transformation, and lesson learned.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--outcome", choices=OUTCOMES)
    ap.add_argument("--child-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--captain-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.temptation is None or c[1] == args.temptation)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, temptation, helper = rng.choice(sorted(combos))
    outcome = args.outcome or rng.choice(sorted(OUTCOMES))
    gender = rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    friend_name = args.friend_name or rng.choice([n for n in (NAMES_GIRL + NAMES_BOY) if n != child_name])
    captain_name = args.captain_name or rng.choice(PARENT_NAMES)
    return StoryParams(
        scene=scene,
        temptation=temptation,
        helper=helper,
        outcome=outcome,
        child_name=child_name,
        child_type=gender,
        friend_name=friend_name,
        friend_type="girl" if gender == "boy" else "boy",
        captain_name=captain_name,
        captain_type="mother",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate story for a young child that uses the words "haven", "star", and "cake".',
        f"Tell a story where {f['child'].label} is tempted by the star cake in a safe haven, then learns a lesson.",
        f"Write a short pirate tale about a child who changes after hearing why the cake should be shared.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    captain = f["captain"]
    cake = f["cake"]
    helper = f["helper"]
    outcome = f["outcome"]
    items = [
        QAItem(
            question="What words from the seed appear in the story?",
            answer="The story includes haven, star, and cake, and it turns them into a pirate scene where those things matter to the ending."
        ),
        QAItem(
            question=f"What was {child.label} tempted to do?",
            answer=f"{child.label} was tempted to take the cake in a selfish way instead of waiting and sharing. That choice would have ruined the star cake and hurt the crew's trust."
        ),
        QAItem(
            question=f"How did the helper change the situation?",
            answer=f"{captain.label} stayed calm, explained the lesson, and helped turn the moment into sharing instead of a mess. That made it easier for {child.label} to change."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The child became kinder and more careful. The star cake stayed a happy treasure in the haven, and the crew could eat it together."
        ),
    ]
    if f["transformed"]:
        items.append(
            QAItem(
                question=f"Why is this a transformation story?",
                answer=f"Because {child.label} starts out grabby and ends up generous. The final scene shows the pirate acting in a new way."
            )
        )
    if f["lesson_learned"]:
        items.append(
            QAItem(
                question="What lesson did the child learn?",
                answer=f"The child learned that a real treasure should be shared and that fixing a mistake is braver than making one. The story ends with that lesson shown in action."
            )
        )
    return items


KNOWLEDGE = {
    "haven": [("What is a haven?",
              "A haven is a safe place where people can rest, hide from trouble, or feel calm.")],
    "star": [("What is a star shape?",
             "A star shape has points that go out from the middle, like a bright star in the sky.")],
    "cake": [("Why do people share cake?",
             "People share cake because it is a treat, and sharing helps everyone enjoy the celebration.")],
    "pirate": [("What is a pirate tale?",
               "A pirate tale is a story about sea adventurers, treasure, and bold choices on ships or islands.")],
    "transformation": [("What is a transformation in a story?",
                      "A transformation is when a character changes in an important way by the end of the story.")],
    "lesson": [("What does it mean to learn a lesson?",
                "Learning a lesson means understanding something important that helps you act better next time.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"haven", "star", "cake", "pirate", "transformation", "lesson"}
    out = []
    for key in ["haven", "star", "cake", "pirate", "transformation", "lesson"]:
        if key in tags:
            for q, a in KNOWLEDGE[key]:
                out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("\n== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}\nA: {item.answer}")
    parts.append("\n== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(parts)


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.temptation not in TEMPTATIONS or params.helper not in HELPERS or params.outcome not in OUTCOMES:
        raise StoryError("Invalid StoryParams values.")
    world = tell(
        SCENES[params.scene],
        TEMPTATIONS[params.temptation],
        HELPERS[params.helper],
        OUTCOMES[params.outcome],
        child_name=params.child_name,
        child_type=params.child_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        captain_name=params.captain_name,
        captain_type=params.captain_type,
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
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Scene, Temptation, Helper) :- scene(Scene), temptation(Temptation), helper(Helper).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for s in SCENES:
        lines.append(asp.fact("scene", s))
    for t in TEMPTATIONS:
        lines.append(asp.fact("temptation", t))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generation smoke test crashed: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams(
        scene="harbor",
        temptation="eat_first",
        helper="share",
        outcome="transformed",
        child_name="Pip",
        child_type="boy",
        friend_name="Mara",
        friend_type="girl",
        captain_name="Captain Bell",
        captain_type="mother",
    ),
    StoryParams(
        scene="island",
        temptation="hide_slice",
        helper="apology",
        outcome="gentle",
        child_name="Luna",
        child_type="girl",
        friend_name="Finn",
        friend_type="boy",
        captain_name="Aunt Tessa",
        captain_type="mother",
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.child_name} in {p.scene} ({p.temptation}, {p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
