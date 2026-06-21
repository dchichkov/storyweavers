#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jabber_consent_humor_dialogue_bravery_bedtime_story.py
=====================================================================================

A small bedtime-story storyworld about a child who wants to keep jabbering at
night, a caregiver who asks for consent, and a brave choice to settle down
together. The story stays gentle and concrete, with a little humor and dialogue,
and every sample is driven by world state rather than by swapping nouns in a
fixed paragraph.

Premise
-------
A child is excited and chatty at bedtime. The parent wants calm, asks consent
before a cozy game or story-sharing ritual, and the child must choose between
more jabbering and the brave act of settling in for sleep.

The world is built from a tiny simulation:
- typed entities with meters and memes
- a forward-chained causal model
- explicit reasonableness checks
- a Python gate and inline ASP twin
- three Q&A sets grounded in the generated world

Seed words: jabber, consent
Features: Humor, Dialogue, Bravery
Style: Bedtime Story
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
MAX_JABBER = 2.0


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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
class SoundToy:
    id: str
    label: str
    phrase: str
    humors: list[str]
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
class ConsentMove:
    id: str
    label: str
    request: str
    granted: str
    denied: str
    brave_text: str
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
    toy: str
    move: str
    child_name: str
    child_gender: str
    parent_gender: str
    sibling_name: str = ""
    sibling_gender: str = "boy"
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


def _r_jabber(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    parent = world.get("parent")
    toy = world.get("toy")
    if child.meters["jabber"] < THRESHOLD:
        return out
    sig = ("jabber", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["excited"] += 1
    parent.memes["sleepy"] += 1
    out.append(
        f"{child.id}'s words bubbled like warm tea, and the room got even more giggly."
    )
    if toy.label == "plush dragon":
        out.append("The plush dragon looked as if it might tell a joke, too.")
    return out


def _r_consent(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    parent = world.get("parent")
    if child.memes["asked"] < THRESHOLD or parent.meters["asked_for_consent"] < THRESHOLD:
        return out
    sig = ("consent", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["trust"] += 1
    parent.memes["pride"] += 1
    out.append("Because they asked first, the room stayed calm enough to listen.")
    return out


def _r_sleep(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["sleepy"] < THRESHOLD:
        return out
    sig = ("sleep", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] += 1
    out.append("The yawn arrived like a small moon and turned the pillow inviting.")
    return out


CAUSAL_RULES = [
    Rule("jabber", "social", _r_jabber),
    Rule("consent", "social", _r_consent),
    Rule("sleep", "physical", _r_sleep),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def valid_choice(setting: Setting, toy: SoundToy, move: ConsentMove) -> bool:
    return "night" in setting.tags and "gentle" in move.tags and toy.label


def safe_moves() -> list[ConsentMove]:
    return [m for m in MOVES.values() if "gentle" in m.tags]


def ask_for_consent(world: World, child: Entity, parent: Entity, move: ConsentMove) -> None:
    child.meters["jabber"] += 1
    parent.meters["asked_for_consent"] += 1
    world.say(
        f"{child.id} was so full of bedtime news that {child.pronoun()} could barely "
        f"keep the stories in a neat little line."
    )
    world.say(
        f'"Can I {move.request}?" {child.id} asked. "{parent.label_word.capitalize()}, '
        f'may I?"'
    )


def wait_and_listen(world: World, parent: Entity, child: Entity, move: ConsentMove) -> bool:
    if child.memes["excited"] >= 1 and parent.meters["asked_for_consent"] >= THRESHOLD:
        world.say(
            f'{parent.label_word.capitalize()} smiled. "{move.granted}"'
        )
        return True
    world.say(
        f'{parent.label_word.capitalize()} shook {parent.pronoun("possessive")} head. '
        f'"{move.denied}"'
    )
    return False


def act_bravely(world: World, child: Entity, parent: Entity, toy: Entity, move: ConsentMove) -> None:
    child.memes["bravery"] += 1
    child.meters["jabber"] = max(0.0, child.meters["jabber"] - 1)
    world.say(
        f'{child.id} took a brave breath, tucked {child.pronoun("possessive")} chin, '
        f'and chose the calmer game.'
    )
    world.say(
        f'"That was brave," {parent.id} said, "and very grown-up for bedtime."'
    )


def cuddle_and_settle(world: World, child: Entity, parent: Entity, toy: Entity, setting: Setting) -> None:
    child.meters["sleepy"] += 1
    child.memes["joy"] += 1
    world.say(
        f'Then they snuggled under the blanket in {setting.place}, and {toy.label} '
        f'lay beside the pillow like a tiny watchful guard.'
    )
    world.say(
        f"The last thing to wobble was a yawn, and even that fell asleep."
    )


def tell(setting: Setting, toy_def: SoundToy, move_def: ConsentMove,
         child_name: str = "Mia", child_gender: str = "girl",
         parent_gender: str = "mother", sibling_name: str = "",
         sibling_gender: str = "boy") -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name, kind="character", type=child_gender, role="child",
        traits=["chatty", "kind"], attrs={"sibling": sibling_name}
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_gender, role="parent",
        label=f"the {SettingParentNames[parent_gender]}"
    ))
    toy = world.add(Entity(id="toy", type="toy", label=toy_def.label))
    if sibling_name:
        world.add(Entity(id="sibling", kind="character", type=sibling_gender, role="sibling", label=sibling_name))

    child.meters["jabber"] = 1.0
    child.memes["excited"] = 1.0
    world.say(
        f"At bedtime, {child.id} and {parent.label_word} sat in {setting.cozy} of "
        f"{setting.place}."
    )
    world.say(
        f"{child.id} loved to {move_def.request} with {toy_def.phrase}, and "
        f"the whole room could hear {child.pronoun('possessive')} happy jabber."
    )
    world.para()
    ask_for_consent(world, child, parent, move_def)
    if wait_and_listen(world, parent, child, move_def):
        world.para()
        child.meters["sleepy"] += 1
        child.meters["jabber"] = 0.0
        propagate(world, narrate=True)
        act_bravely(world, child, parent, toy, move_def)
        cuddle_and_settle(world, child, parent, toy, setting)
    else:
        world.para()
        parent.memes["steadfast"] += 1
        world.say(
            f"{child.id} made one tiny grumbly face, then listened."
        )
        child.meters["sleepy"] += 1
        cuddle_and_settle(world, child, parent, toy, setting)

    world.facts.update(
        child=child,
        parent=parent,
        toy=toy,
        toy_def=toy_def,
        move=move_def,
        setting=setting,
        consented=True,
        brave=child.memes["bravery"] >= THRESHOLD,
    )
    return world


SettingParentNames = {"mother": "mom", "father": "dad"}

SETTINGS = {
    "nursery": Setting(id="nursery", place="the nursery", quiet="soft", cozy="nest-like", tags={"night"}),
    "moonroom": Setting(id="moonroom", place="the moonlit room", quiet="soft", cozy="cloudy", tags={"night"}),
    "tent": Setting(id="tent", place="the little tent", quiet="hushed", cozy="sleepy", tags={"night"}),
}

TOYS = {
    "bunny": SoundToy(id="bunny", label="plush bunny", phrase="a plush bunny", humors=["ears", "puff"], tags={"toy"}),
    "dragon": SoundToy(id="dragon", label="plush dragon", phrase="a plush dragon", humors=["snore", "blink"], tags={"toy"}),
    "rocket": SoundToy(id="rocket", label="sleepy rocket", phrase="a sleepy rocket", humors=["zoom", "yawn"], tags={"toy"}),
}

MOVES = {
    "story": ConsentMove(
        id="story",
        label="story",
        request="tell one more story",
        granted="Of course. One small story, then sleep.",
        denied="Not tonight, sweetie. It's time for resting.",
        brave_text="chose to stop talking and listen",
        tags={"gentle", "dialogue"},
    ),
    "song": ConsentMove(
        id="song",
        label="song",
        request="sing one tiny song",
        granted="Yes. One hush-hush song, then the stars can finish it.",
        denied="Not this one. The pillow is asking for quiet.",
        brave_text="picked a quieter song and used a softer voice",
        tags={"gentle", "dialogue"},
    ),
    "joke": ConsentMove(
        id="joke",
        label="joke",
        request="tell a silly joke",
        granted="Yes, but only one. The blanket already looks giggly.",
        denied="No more jokes right now. The moon is trying to nap.",
        brave_text="saved the joke for morning and grinned anyway",
        tags={"gentle", "dialogue", "humor"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid in TOYS:
            for mid in MOVES:
                if valid_choice(SETTINGS[sid], TOYS[tid], MOVES[mid]):
                    combos.append((sid, tid, mid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story that includes the words "jabber" and "consent" and features a child named {f["child"].id}.',
        f"Tell a gentle, funny bedtime story where {f['child'].id} wants to keep jabbering, asks for consent, and ends by settling down safely.",
        f'Write a short dialogue story for a sleepy child about asking consent before one more bedtime {f["move"].label}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, toy, move = f["child"], f["parent"], f["toy"], f["move"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.label_word}, who were getting ready for bed together. The child was chatty, and the grown-up stayed calm."),
        ("What did the child want to do?",
         f"{child.id} wanted to {move.request} and keep jabbering a little longer. That was the childly part of bedtime, even though sleep was waiting."),
        ("What did the child ask for?",
         f"{child.id} asked for consent before {move.request}. The question was polite, and it gave {parent.label_word} room to answer clearly."),
    ]
    qa.append((
        "Why was the child brave?",
        f"{child.id} was brave because {child.pronoun()} chose to listen and settle down instead of arguing for more chatter. That kind of bravery is quiet, but it helps bedtime go smoothly."
    ))
    if f.get("consented"):
        qa.append((
            "What changed after the child asked?",
            f"The room stayed calm enough to hear the answer, and the child could wait. Asking first made the moment gentler, so the family could choose a cozy plan together."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with {child.id} tucked in beside {toy.label}, calm and sleepy. The jabbering stopped, and the blanket took over the talking."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does consent mean?",
         "Consent means asking first and getting a clear yes before you do something that affects someone else. It helps people feel safe and respected."),
        ("What is jabbering?",
         "Jabbering is talking very fast and a lot, especially when someone is excited or nervous. At bedtime, a little jabber can be funny, but too much can keep sleep away."),
        ("Why is bravery useful at bedtime?",
         "Bravery helps a child choose a calm next step, even when the louder choice looks tempting. Sometimes bravery means listening, slowing down, and getting ready to rest."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, toy: SoundToy, move: ConsentMove) -> str:
    return f"(No story: the chosen bedtime nook, toy, and move do not fit the calm, consent-based setup.)"


CURATED = [
    StoryParams(setting="nursery", toy="bunny", move="story", child_name="Mia", child_gender="girl", parent_gender="mother", sibling_name="Ben", sibling_gender="boy"),
    StoryParams(setting="moonroom", toy="dragon", move="joke", child_name="Noah", child_gender="boy", parent_gender="father", sibling_name=""),
    StoryParams(setting="tent", toy="rocket", move="song", child_name="Luna", child_gender="girl", parent_gender="mother", sibling_name="Pip", sibling_gender="girl"),
]


def outcome_of(params: StoryParams) -> str:
    return "calm"


ASP_RULES = r"""
valid(S, T, M) :- setting(S), toy(T), move(M), night(S), gentle(M).
brave(C) :- child(C), asked_consent(C), consented(C).
calm_end :- brave(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "night" in s.tags:
            lines.append(asp.fact("night", sid))
    for tid, t in TOYS.items():
        lines.append(asp.fact("toy", tid))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        if "gentle" in m.tags:
            lines.append(asp.fact("gentle", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    try:
        clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
        if clingo_set != python_set:
            print("MISMATCH in valid combos")
            print("only in clingo:", sorted(clingo_set - python_set))
            print("only in python:", sorted(python_set - clingo_set))
            return 1
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: ASP parity and story generation smoke test passed.")
        return 0
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        traceback.print_exc()
        return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about jabber, consent, humor, dialogue, and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-gender", choices=["mother", "father"])
    ap.add_argument("--sibling-name")
    ap.add_argument("--sibling-gender", choices=["girl", "boy"])
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
              and (args.toy is None or c[1] == args.toy)
              and (args.move is None or c[2] == args.move)]
    if not combos:
        raise StoryError("(No valid bedtime story matches the given options.)")
    setting, toy, move = rng.choice(sorted(combos))
    setting_def = SETTINGS[setting]
    toy_def = TOYS[toy]
    move_def = MOVES[move]
    return StoryParams(
        setting=setting,
        toy=toy,
        move=move,
        child_name=args.child_name or rng.choice(["Mia", "Luna", "Noah", "Eli", "Ada"]),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        parent_gender=args.parent_gender or rng.choice(["mother", "father"]),
        sibling_name=args.sibling_name or "",
        sibling_gender=args.sibling_gender or "boy",
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        toy_def = TOYS[params.toy]
        move_def = MOVES[params.move]
    except KeyError as exc:
        raise StoryError(f"Invalid story parameter: {exc}") from exc
    if not valid_choice(setting, toy_def, move_def):
        raise StoryError(explain_rejection(setting, toy_def, move_def))
    world = tell(setting, toy_def, move_def, params.child_name, params.child_gender, params.parent_gender, params.sibling_name, params.sibling_gender)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, t, m in combos:
            print(f"  {s:8} {t:8} {m}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
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
