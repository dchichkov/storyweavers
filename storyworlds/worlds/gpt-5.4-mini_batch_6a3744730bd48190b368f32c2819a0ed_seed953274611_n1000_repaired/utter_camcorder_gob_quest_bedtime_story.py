#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/utter_camcorder_gob_quest_bedtime_story.py
===========================================================================

A tiny bedtime-quest story world built from the seed words:

- utter
- camcorder
- gob

Premise
-------
A child prepares for bed, notices a small "gob" of lost moonlight in the room,
and goes on a gentle quest to return it to a sleepy night scene. A camcorder is
present as a story-making object: it records clues, helps the child notice what
changed, and becomes part of the ending image. The story is calm, concrete, and
state-driven, with a clear beginning, turn, and resolution.

The story should feel like a bedtime tale:
- soft, cozy setting
- a small quest
- a helpful tool
- a warm ending image

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/utter_camcorder_gob_quest_bedtime_story.py
    python storyworlds/worlds/gpt-5.4-mini/utter_camcorder_gob_quest_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/utter_camcorder_gob_quest_bedtime_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/utter_camcorder_gob_quest_bedtime_story.py --verify
    python storyworlds/worlds/gpt-5.4-mini/utter_camcorder_gob_quest_bedtime_story.py --show-asp
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    quiet: str
    cozy: str
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
class Quest:
    id: str
    title: str
    clue: str
    need: str
    return_line: str
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


@dataclass
class ObjectDef:
    id: str
    label: str
    role: str
    useful_for: set[str] = field(default_factory=set)
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
class StoryParams:
    place: str
    quest: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent_gender: str
    object_id: str
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


def _r_glow(world: World) -> list[str]:
    out: list[str] = []
    gob = world.get("gob")
    if gob.meters["lost"] < THRESHOLD:
        return out
    sig = ("glow", gob.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["darkness"] += 1
    world.get("child").memes["curiosity"] += 1
    out.append("__glow__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["rest"] < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").memes["cozy"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("glow", _r_glow), Rule("calm", _r_calm)]


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


def slip_away(world: World, gob: Entity) -> None:
    gob.meters["lost"] += 1
    propagate(world, narrate=False)


def predict_gob(world: World) -> dict:
    sim = world.copy()
    slip_away(sim, sim.get("gob"))
    return {
        "darkness": sim.get("room").meters["darkness"],
        "curiosity": sim.get("child").memes["curiosity"],
    }


def start_bedtime(world: World, child: Entity, parent: Entity, place: Place) -> None:
    child.memes["tired"] += 1
    world.say(
        f"At bedtime, {child.id} lay in {place.label}, where the shadows were soft "
        f"and the blankets felt like clouds."
    )
    world.say(
        f"{parent.id} tucked the quilt up high and whispered, "
        f"\"Time for one last quiet story, then sleep.\""
    )


def notice_gob(world: World, child: Entity, obj: Entity, quest: Quest, place: Place) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"But near the pillow, {child.id} spotted a tiny {quest.id}: a little {obj.label} "
        f"of moonlight that had rolled out of the night."
    )
    world.say(
        f"\"I think I can help,\" {child.id} said. The word was uttered very softly, "
        f"so softly it felt like a secret."
    )


def prepare_camcorder(world: World, child: Entity, camcorder: Entity) -> None:
    camcorder.meters["ready"] += 1
    world.say(
        f"{child.id} picked up the camcorder and pointed it gently at the room. "
        f"Its small light blinked awake, ready to remember the clues."
    )


def question_path(world: World, helper: Entity, place: Place, quest: Quest) -> None:
    helper.memes["helpful"] += 1
    world.say(
        f"{helper.id} walked with {world.get('child').id} through {place.cozy}. "
        f"Together they followed the quiet clue: {quest.clue}."
    )


def find_gob(world: World, child: Entity, gob: Entity, obj: Entity, quest: Quest) -> None:
    gob.meters["found"] += 1
    gob.meters["lost"] = 0.0
    child.memes["hope"] += 1
    world.say(
        f"Under the little chair they found the missing {obj.label}, glowing as if it "
        f"had been waiting for the quest to begin."
    )
    world.say(
        f"The camcorder turned toward it and hummed a tiny, happy hum, as if it knew "
        f"this was the important part to keep."
    )


def return_gob(world: World, parent: Entity, child: Entity, gob: Entity, quest: Quest) -> None:
    child.memes["rest"] += 1
    world.get("room").meters["darkness"] = max(0.0, world.get("room").meters["darkness"] - 1)
    world.say(
        f"{parent.id} smiled when {child.id} brought the {gob.label} back. "
        f"{quest.return_line}"
    )
    world.say(
        f"{child.id} set the little thing back beside the lamp, and the room looked "
        f"like it had found its own bedtime again."
    )


def ending(world: World, child: Entity, parent: Entity, camcorder: Entity, quest: Quest, place: Place) -> None:
    world.say(
        f"At last, {parent.id} kissed {child.id} goodnight. On the camcorder screen, "
        f"{quest.ending_image}"
    )
    world.say(
        f"{place.label} was still and warm, the gob was back where it belonged, and "
        f"{child.id} drifted off knowing the tiny quest was safely done."
    )


def tell(place: Place, quest: Quest, obj: ObjectDef, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str, parent_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_gender, role="parent"))
    room = world.add(Entity(id="room", type="room", label=place.label))
    gob = world.add(Entity(id="gob", type="thing", label=obj.label, tags=set(obj.tags)))
    camcorder = world.add(Entity(id="camcorder", type="thing", label="camcorder", tags={"camcorder"}))

    world.facts.update(place=place, quest=quest, obj=obj, child=child, helper=helper, parent=parent,
                       gob=gob, camcorder=camcorder)

    start_bedtime(world, child, parent, place)
    world.para()
    notice_gob(world, child, gob, quest, place)
    prepare_camcorder(world, child, camcorder)
    world.para()
    question_path(world, helper, place, quest)
    slip_away(world, gob)
    world.say("The room grew a little dimmer, and everyone went looking with careful feet.")
    find_gob(world, child, gob, gob, quest)
    return_gob(world, parent, child, gob, quest)
    world.para()
    ending(world, child, parent, camcorder, quest, place)
    return world


# fix flow: return_gob before ending
def tell(place: Place, quest: Quest, obj: ObjectDef, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str, parent_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_gender, role="parent"))
    world.add(Entity(id="room", type="room", label=place.label))
    gob = world.add(Entity(id="gob", type="thing", label=obj.label, tags=set(obj.tags)))
    camcorder = world.add(Entity(id="camcorder", type="thing", label="camcorder", tags={"camcorder"}))

    world.facts.update(place=place, quest=quest, obj=obj, child=child, helper=helper, parent=parent,
                       gob=gob, camcorder=camcorder)

    start_bedtime(world, child, parent, place)
    world.para()
    notice_gob(world, child, gob, quest, place)
    prepare_camcorder(world, child, camcorder)
    world.para()
    question_path(world, helper, place, quest)
    slip_away(world, gob)
    world.say("The room grew a little dimmer, and everyone went looking with careful feet.")
    find_gob(world, child, gob, gob, quest)
    return_gob(world, parent, child, gob, quest)
    world.para()
    ending(world, child, parent, camcorder, quest, place)
    return world


# correct implementation
def tell(place: Place, quest: Quest, obj: ObjectDef, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str, parent_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_gender, role="parent"))
    world.add(Entity(id="room", type="room", label=place.label))
    gob = world.add(Entity(id="gob", type="thing", label=obj.label, tags=set(obj.tags)))
    camcorder = world.add(Entity(id="camcorder", type="thing", label="camcorder", tags={"camcorder"}))

    world.facts.update(place=place, quest=quest, obj=obj, child=child, helper=helper, parent=parent,
                       gob=gob, camcorder=camcorder)

    start_bedtime(world, child, parent, place)
    world.para()
    notice_gob(world, child, gob, quest, place)
    prepare_camcorder(world, child, camcorder)
    world.para()
    question_path(world, helper, place, quest)
    slip_away(world, gob)
    world.say("The room grew a little dimmer, and everyone went looking with careful feet.")
    find_gob(world, child, gob, gob, quest)
    world.para()
    return_gob(world, parent, child, gob, quest)
    world.para()
    ending(world, child, parent, camcorder, quest, place)
    return world


PLACES = {
    "bedroom": Place(
        id="bedroom",
        label="the bedroom",
        quiet="the hush of pillows and moonlight",
        cozy="the blanket hill by the window",
        tags={"bedtime", "quiet"},
    ),
    "nursery": Place(
        id="nursery",
        label="the nursery",
        quiet="the hush of a sleeping house",
        cozy="the little rug beside the crib",
        tags={"bedtime", "quiet"},
    ),
    "attic": Place(
        id="attic",
        label="the attic",
        quiet="the whisper of old boxes",
        cozy="the round rug under the skylight",
        tags={"bedtime", "quiet", "quest"},
    ),
}

QUESTS = {
    "moon_gob": Quest(
        id="moon-gob",
        title="the moon gob quest",
        clue="a silver line on the floor led under the chair",
        need="find the missing moon gob",
        return_line="The moon gob shone brighter once it was home.",
        ending_image="the camcorder showed a bright little gob tucked safe by the lamp",
        tags={"quest", "camcorder", "gob", "utter"},
    ),
    "toy_gob": Quest(
        id="toy-gob",
        title="the toy gob quest",
        clue="a small shape peeked out from under the quilt",
        need="find the missing toy gob",
        return_line="The toy gob was back in its cozy spot.",
        ending_image="the camcorder showed the toy gob smiling beside the quilt",
        tags={"quest", "camcorder", "gob", "utter"},
    ),
}

OBJECTS = {
    "moon": ObjectDef(
        id="moon",
        label="moon gob",
        role="lost treasure",
        useful_for={"quest"},
        tags={"gob", "moon"},
    ),
    "toy": ObjectDef(
        id="toy",
        label="toy gob",
        role="lost treasure",
        useful_for={"quest"},
        tags={"gob", "toy"},
    ),
}

NAMES_GIRL = ["Mina", "Lina", "Nora", "Ivy", "Maya"]
NAMES_BOY = ["Eli", "Toby", "Owen", "Finn", "Leo"]
HELPER_GIRL = ["Ava", "June", "Mila"]
HELPER_BOY = ["Noah", "Theo", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for q in QUESTS:
            for o in OBJECTS:
                combos.append((p, q, o))
    return combos


def explain_rejection(place: str, quest: str, obj: str) -> str:
    return "(No story: the bedtime quest cannot be formed from these choices.)"


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,Q,O) :- place(P), quest(Q), object(O).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos disagree.")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, quest=None, name=None, gender=None, helper=None, helper_gender=None,
            parent=None, object=None, n=1, seed=None, all=False, trace=False, qa=False,
            json=False, asp=False, verify=False, show_asp=False
        ), random.Random(123)))
        assert sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime quest story world with a camcorder and a gob.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["Ava", "June", "Mila", "Noah", "Theo", "Ben"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.place and args.place not in PLACES:
        raise StoryError(explain_rejection(args.place, args.quest or "", args.object_id or ""))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.object_id is None or c[2] == args.object_id)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, obj = rng.choice(sorted(combos))
    q = QUESTS[quest]
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper_name = args.helper or rng.choice(HELPER_GIRL if helper_gender == "girl" else HELPER_BOY)
    parent_gender = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, quest=quest, child_name=child_name, child_gender=child_gender,
                       helper_name=helper_name, helper_gender=helper_gender, parent_gender=parent_gender,
                       object_id=obj)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    obj = OBJECTS[params.object_id]
    world = tell(place, quest, obj, params.child_name, params.child_gender,
                 params.helper_name, params.helper_gender, params.parent_gender)
    story_qa = [
        QAItem(
            question="What was the child trying to do?",
            answer=f"{params.child_name} was trying to help with {quest.need}. That tiny quest was the center of the bedtime story.",
        ),
        QAItem(
            question="Why did the camcorder matter?",
            answer="The camcorder helped remember the little clues and made the ending image feel important. It recorded the moment the gob was found and returned to its place.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="The gob was no longer lost, and the room felt calm again. The child could drift off to sleep knowing the quest was done.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a camcorder?",
            answer="A camcorder is a camera that records moving pictures and sound. People use it to save moments they want to remember.",
        ),
        QAItem(
            question="What does utter mean?",
            answer="Utter means to say something out loud. In a quiet story, it can mean a word was spoken softly.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important. It often means following clues until the thing is found.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=[
        f"Write a bedtime story that includes the words utter, camcorder, and gob.",
        f"Tell a gentle quest story set in {place.label} where a child and helper follow a clue and use a camcorder.",
        f"Write a soft, child-facing story about a tiny lost gob being returned safely at bedtime.",
    ], story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate_story(params: StoryParams) -> StorySample:
    return generate(params)


CURATED = [
    StoryParams(place="bedroom", quest="moon_gob", child_name="Mina", child_gender="girl",
                helper_name="Noah", helper_gender="boy", parent_gender="mother", object_id="moon"),
    StoryParams(place="nursery", quest="toy_gob", child_name="Eli", child_gender="boy",
                helper_name="Ava", helper_gender="girl", parent_gender="father", object_id="toy"),
    StoryParams(place="attic", quest="moon_gob", child_name="Nora", child_gender="girl",
                helper_name="Ben", helper_gender="boy", parent_gender="mother", object_id="moon"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid story combinations")
        for combo in asp_valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate_story(p) for p in CURATED]
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
            sample = generate_story(params)
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
