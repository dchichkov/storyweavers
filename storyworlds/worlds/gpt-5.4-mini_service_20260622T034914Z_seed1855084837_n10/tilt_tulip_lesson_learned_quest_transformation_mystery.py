#!/usr/bin/env python3
"""
storyworlds/worlds/tilt_tulip_lesson_learned_quest_transformation_mystery.py
=============================================================================

A tiny storyworld built from a mystery-flavored seed: a curious child follows
a clue about a tilted object, a tulip, a quest, a lesson learned, and a small
transformation at the end.

The world keeps a compact simulation:
- typed entities with meters and memes
- a few forward rules for mystery, discovery, and transformation
- a reasonableness gate plus an inline ASP twin
- three Q&A sets grounded in simulated state, not rendered text

The result aims for a child-facing mystery tone: a clue, a search, a reveal,
and a changed ending image that proves something has transformed.
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
    phrase: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False
    vivid: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    label: str
    detail: str
    clues: list[str]
    places: set[str] = field(default_factory=set)
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
class Quest:
    id: str
    title: str
    verb: str
    search: str
    reveal: str
    clue_word: str
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
class Transformation:
    id: str
    title: str
    from_form: str
    to_form: str
    trigger: str
    effect: str
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
    setting: str
    quest: str
    transformation: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

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
            self.history.append(text)

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
        clone.history = list(self.history)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


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


def _r_discover(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue", "")
    if clue and clue not in world.fired:
        world.fired.add((clue, "discover"))
        world.get("child").memes["curiosity"] += 1
        out.append("__discover__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    if world.get("object").meters["tilted"] < THRESHOLD:
        return out
    sig = ("transform", world.get("object").id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("object").meters["opened"] += 1
    world.get("child").memes["wonder"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule("discover", _r_discover),
    Rule("transform", _r_transform),
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


def mystery_at_risk(setting: Setting, quest: Quest) -> bool:
    return quest.clue_word in setting.places


def transformation_possible(setting: Setting, quest: Quest, trans: Transformation) -> bool:
    return mystery_at_risk(setting, quest) and trans.from_form == "tilted closed thing" and trans.to_form == "open secret"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for qid, quest in QUESTS.items():
            for tid, trans in TRANSFORMS.items():
                if mystery_at_risk(setting, quest) and transformation_possible(setting, quest, trans):
                    combos.append((sid, qid, tid))
    return combos


def tell(setting: Setting, quest: Quest, trans: Transformation, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name))
    clue = world.add(Entity(id="clue", type="clue", label=quest.clue_word, phrase=f"a clue about {quest.clue_word}"))
    obj = world.add(Entity(id="object", type="thing", label="tilted lid", phrase="a tilted lid"))
    flower = world.add(Entity(id="flower", type="thing", label="tulip", phrase="a red tulip", vivid=True))
    world.facts.update(
        setting=setting,
        quest=quest,
        trans=trans,
        child=child,
        helper=helper,
        clue=clue,
        object=obj,
        flower=flower,
    )

    child.memes["curiosity"] += 1
    helper.memes["care"] += 1
    obj.meters["tilted"] += 1

    world.say(f"{child_name} noticed something odd in {setting.label}.")
    world.say(f"A small clue pointed toward {quest.clue_word}, and a red tulip nodded beside it.")
    world.say(f"{child_name} and {helper_name} began a quiet quest to follow the clue.")

    world.para()
    world.say(f"They searched near the path and around the flower bed, where the air smelled like rain.")
    world.say(f"{child_name} looked closer and saw that the tilted lid hid a tiny secret.")

    world.para()
    world.say(f"{child_name} tilted the lid a little more, and the hidden thing began to open.")
    obj.meters["tilted"] += 1
    propagate(world, narrate=False)
    if obj.meters["opened"] >= THRESHOLD:
        child.memes["joy"] += 1
        helper.memes["relief"] += 1
        flower.meters["bloomed"] += 1
        world.say(f"Inside was not trouble at all, but a dried seed packet tucked away for safekeeping.")
        world.say(f"The little packet helped a tulip patch grow brighter, as if the mystery had been waiting to become a garden.")
        world.say(f"{child_name} learned that some clues are not warnings; they are invitations to look carefully.")
        world.say(f"By the end, the tulip stood straighter, and the tiny hidden place had transformed into a new beginning.")
    else:
        world.say(f"The secret stayed closed, but the clue had still taught them to be patient and careful.")

    world.facts["resolved"] = obj.meters["opened"] >= THRESHOLD
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        label="the garden",
        detail="A red tulip grew near the path, and a little shed sat at the far end.",
        clues=["path", "shed", "flower bed"],
        places={"tulip", "path", "flower bed", "shed"},
    ),
    "backyard": Setting(
        id="backyard",
        label="the backyard",
        detail="A tulip patch leaned near a small bench, and the back gate creaked softly.",
        clues=["bench", "gate", "tulip patch"],
        places={"tulip", "bench", "gate", "tulip patch"},
    ),
    "courtyard": Setting(
        id="courtyard",
        label="the courtyard",
        detail="A potted tulip stood by a stone wall, and a narrow door hid in the shade.",
        clues=["stone wall", "door", "potted tulip"],
        places={"tulip", "stone wall", "door", "potted tulip"},
    ),
}

QUESTS = {
    "find_seed": Quest(
        id="find_seed",
        title="find the hidden seed",
        verb="search for the seed",
        search="searching for the seed",
        reveal="the seed packet",
        clue_word="tulip",
        tags={"tulip", "seed", "mystery"},
    ),
    "find_key": Quest(
        id="find_key",
        title="find the little key",
        verb="look for the key",
        search="looking for the key",
        reveal="a little key",
        clue_word="tulip",
        tags={"tulip", "key", "mystery"},
    ),
}

TRANSFORMS = {
    "seed_to_bloom": Transformation(
        id="seed_to_bloom",
        title="seed to bloom",
        from_form="tilted closed thing",
        to_form="open secret",
        trigger="the lid tilted open",
        effect="a hidden garden clue became a growing patch",
        tags={"transform", "tulip", "garden"},
    ),
    "locked_to_found": Transformation(
        id="locked_to_found",
        title="locked to found",
        from_form="tilted closed thing",
        to_form="open secret",
        trigger="the cover tipped just right",
        effect="a tucked-away clue became easy to see",
        tags={"transform", "mystery"},
    ),
}

GIRL_NAMES = ["Mia", "Lena", "Zoe", "Ivy", "Nora", "Ada", "Lila"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Leo", "Owen", "Max", "Theo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a small mystery story for a child that includes the words "{f["quest"].clue_word}" and "tilt".',
        f"Tell a quest story where {f['child'].label} follows a tulip clue in {f['setting'].label} and discovers a hidden change.",
        f"Write a gentle mystery with a lesson learned, a quest, and a transformation near a tulip.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    setting = f["setting"]
    quest = f["quest"]
    obj = f["object"]
    qas = [
        QAItem(
            question=f"Who went on the quest in {setting.label}?",
            answer=f"{child.label} went on the quest with {helper.label}. They followed a clue near the tulip and searched carefully together.",
        ),
        QAItem(
            question=f"What did {child.label} do to the tilted lid?",
            answer=f"{child.label} tilted the lid a little more so they could see what was hidden. That careful move helped the secret open instead of staying stuck.",
        ),
        QAItem(
            question=f"Why was the tulip important in the story?",
            answer=f"The tulip was part of the clue that led them to the hidden place. It made the mystery feel gentle and pointed them toward the answer.",
        ),
    ]
    if f.get("resolved"):
        qas.append(QAItem(
            question=f"What did {child.label} learn by the end?",
            answer=f"{child.label} learned that not every mystery is scary. Some clues are invitations to look closely, and careful searching can lead to a good surprise.",
        ))
        qas.append(QAItem(
            question=f"How did the hidden thing change?",
            answer=f"The hidden thing changed from a closed, tilted secret into something open and useful. That transformation helped the tulip patch look brighter at the end.",
        ))
        qas.append(QAItem(
            question=f"What proved the quest was finished?",
            answer=f"The little seed packet was found, and the tulip stood straighter afterward. That ending image showed the mystery had been solved and something had changed.",
        ))
    else:
        qas.append(QAItem(
            question=f"Did the quest find {quest.reveal}?",
            answer=f"Not yet. They found a clue and learned to be patient, but the secret stayed closed in that ending.",
        ))
    return qas


KNOWLEDGE = {
    "tulip": [
        (
            "What is a tulip?",
            "A tulip is a flower with smooth petals that often grows in gardens in bright colors.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a search for something important or interesting. It often means following clues step by step.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something that is not understood right away. People solve it by noticing clues and thinking carefully.",
        )
    ],
    "transform": [
        (
            "What does transformation mean?",
            "Transformation means something changes into a new form or state. It can be small, like a bud opening into a flower.",
        )
    ],
    "lesson": [
        (
            "What does it mean to learn a lesson?",
            "It means understanding something new that helps you do better next time. A good lesson can change how you act afterward.",
        )
    ],
}

KNOWLEDGE_ORDER = ["mystery", "quest", "tulip", "transform", "lesson"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags) | set(world.facts["trans"].tags)
    tags.add("lesson")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="garden", quest="find_seed", transformation="seed_to_bloom", child_name="Mia", child_gender="girl", helper_name="Leo", helper_gender="boy"),
    StoryParams(setting="backyard", quest="find_key", transformation="locked_to_found", child_name="Eli", child_gender="boy", helper_name="Nora", helper_gender="girl"),
    StoryParams(setting="courtyard", quest="find_seed", transformation="seed_to_bloom", child_name="Zoe", child_gender="girl", helper_name="Max", helper_gender="boy"),
]


def explain_rejection(setting: Setting, quest: Quest, trans: Transformation) -> str:
    return f"(No story: this combination does not give a believable clue path in {setting.label}. The tulip clue has to fit the setting, and the transformation must come from that search.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a tulip clue, a quest, a lesson learned, and a small transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--transformation", choices=TRANSFORMS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--parent", choices=["mother", "father"])  # accepted but unused; contract-friendly
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.transformation is None or c[2] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, trans = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if child_gender == "girl" else "girl"
    child_pool = GIRL_NAMES if child_gender == "girl" else BOY_NAMES
    helper_pool = BOY_NAMES if helper_gender == "boy" else GIRL_NAMES
    child_name = args.name or rng.choice(child_pool)
    helper_name = args.helper or rng.choice([n for n in helper_pool if n != child_name])
    return StoryParams(
        setting=setting,
        quest=quest,
        transformation=trans,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.quest not in QUESTS or params.transformation not in TRANSFORMS:
        raise StoryError("(Invalid params.)")
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    trans = TRANSFORMS[params.transformation]
    if not (mystery_at_risk(setting, quest) and transformation_possible(setting, quest, trans)):
        raise StoryError(explain_rejection(setting, quest, trans))
    world = tell(setting, quest, trans, params.child_name, params.child_gender, params.helper_name, params.helper_gender)
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in sorted(s.places):
            lines.append(asp.fact("places", sid, p))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("clue_word", qid, q.clue_word))
    for tid, t in TRANSFORMS.items():
        lines.append(asp.fact("transformation", tid))
        lines.append(asp.fact("from_form", tid, t.from_form))
        lines.append(asp.fact("to_form", tid, t.to_form))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,Q,T) :- setting(S), quest(Q), transformation(T), places(S,"tulip"), clue_word(Q,"tulip"), from_form(T,"tilted closed thing"), to_form(T,"open secret").
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate.")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))
    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, qa=True)
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, quest, transformation) combos:\n")
        for s, q, t in combos:
            print(f"  {s:10} {q:10} {t}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.quest} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
