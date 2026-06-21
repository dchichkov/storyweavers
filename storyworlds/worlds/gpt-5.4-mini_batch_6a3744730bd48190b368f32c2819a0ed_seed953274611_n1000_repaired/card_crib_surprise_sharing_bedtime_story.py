#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/card_crib_surprise_sharing_bedtime_story.py
===========================================================================

A small bedtime-story world about a child, a card, a crib, a surprise, and a
gentle act of sharing. The premise is simple: a little child gets ready for bed,
finds a card tucked into the scene, notices a soft surprise, and learns that
sharing can make the night feel warmer.

The world is state-driven rather than frozen prose: typed entities carry
physical meters and emotional memes, a tiny causal engine advances the scene,
and a declarative ASP twin mirrors the Python reasonableness gate and ending
logic.

This script is self-contained except for the shared result containers
(`storyworlds/results.py`) and the optional ASP helper (`storyworlds/asp.py`),
which is imported lazily only when ASP features are used.
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
SENSE_MIN = 2


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
    plural: bool = False

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
    night_detail: str
    bed_detail: str
    allows: set[str] = field(default_factory=set)
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
class Surprise:
    id: str
    label: str
    phrase: str
    reveal: str
    warmth: str
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
class Sharing:
    id: str
    label: str
    offer: str
    response: str
    comfort: str
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
class Nightlight:
    id: str
    label: str
    phrase: str
    glow: str
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


def _r_bedtime(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["sleepy"] < THRESHOLD:
        return out
    sig = ("sleepy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] += 1
    out.append("__sleep__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    friend = world.get("friend")
    if child.memes["want_to_share"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["warmth"] += 1
    friend.memes["warmth"] += 1
    out.append("Sharing made the little room feel softer.")
    return out


CAUSAL_RULES = [Rule("bedtime", "calm", _r_bedtime), Rule("share", "social", _r_share)]


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


def reasonableness_gate(setting: Setting, surprise: Surprise, sharing: Sharing) -> bool:
    return "crib" in setting.allows and surprise.id in SURPRISES and sharing.id in SHARINGS


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for sur in SURPRISES:
            for sh in SHARINGS:
                if reasonableness_gate(SETTINGS[sid], SURPRISES[sur], SHARINGS[sh]):
                    combos.append((sid, sur, sh))
    return combos


def predict_reveal(world: World, surprise_id: str) -> dict:
    sim = world.copy()
    _do_reveal(sim, sim.get(surprise_id), narrate=False)
    return {
        "opened": sim.get(surprise_id).meters["opened"] >= THRESHOLD,
        "warmth": sim.get("child").memes["warmth"],
    }


def _do_reveal(world: World, surprise: Entity, narrate: bool = True) -> None:
    surprise.meters["opened"] += 1
    surprise.memes["wonder"] += 1
    propagate(world, narrate=narrate)


def begin(world: World, child: Entity, parent: Entity, setting: Setting) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"At bedtime, {child.id} settled into {setting.bed_detail} in {setting.place}. "
        f"{setting.night_detail}"
    )
    world.say(
        f"{child.id} held a small card while {parent.label_word} tucked the blanket in."
    )


def invite_surprise(world: World, child: Entity, surprise: Surprise) -> None:
    world.say(
        f"{child.id} found {surprise.phrase}, and {child.pronoun('possessive')} eyes went wide."
    )
    child.memes["wonder"] += 1


def share_prompt(world: World, child: Entity, friend: Entity, sharing: Sharing) -> None:
    child.memes["want_to_share"] += 1
    said = f'"{sharing.offer}"' if sharing.offer.endswith(("?", "!")) else f'"{sharing.offer},"'
    world.say(
        f'{said} {child.id} whispered, and then {child.id} smiled at {friend.id} '
        f'because {sharing.response}.'
    )


def reveal(world: World, child: Entity, surprise: Surprise, nightlight: Nightlight) -> None:
    _do_reveal(world, surprise)
    world.say(
        f"{surprise.reveal} {surprise.warmth} {nightlight.phrase.capitalize()} {nightlight.glow}, "
        f"making the crib corner look like a tiny safe harbor."
    )


def share_scene(world: World, child: Entity, friend: Entity, sharing: Sharing) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{child.id} passed the card to {friend.id}, and they looked at it together. "
        f"{sharing.comfort.capitalize()}."
    )


def ending(world: World, child: Entity, friend: Entity, parent: Entity, nightlight: Nightlight) -> None:
    child.memes["calm"] += 1
    friend.memes["calm"] += 1
    world.say(
        f"Then {parent.label_word} kissed {child.pronoun('possessive')} forehead and turned on {nightlight.phrase}, "
        f"which {nightlight.glow}."
    )
    world.say(
        f"{child.id} and {friend.id} curled up close, with the card between them, and the room felt quiet, "
        f"warm, and ready for sleep."
    )


def tell(setting: Setting, surprise: Surprise, sharing: Sharing, nightlight: Nightlight,
         child_name: str = "Mina", child_gender: str = "girl",
         friend_name: str = "Ollie", friend_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="card", type="card", label="card"))
    crib = world.add(Entity(id="crib", type="crib", label="crib"))
    world.facts["setting"] = setting.id
    world.facts["surprise"] = surprise.id
    world.facts["sharing"] = sharing.id
    world.facts["nightlight"] = nightlight.id
    world.facts["crib"] = crib.id

    begin(world, child, parent, setting)
    world.para()
    invite_surprise(world, child, surprise)
    share_prompt(world, child, friend, sharing)
    reveal(world, child, surprise, nightlight)
    world.para()
    share_scene(world, child, friend, sharing)
    ending(world, child, friend, parent, nightlight)

    world.facts.update(
        child=child, friend=friend, parent=parent,
        opened=world.get("surprise").meters["opened"] >= THRESHOLD if "surprise" in world.entities else False,
        shared=child.memes["want_to_share"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "nursery": Setting(id="nursery", place="the nursery", night_detail="The moonlight slipped through the curtains.", bed_detail="the little crib", allows={"crib"}),
    "small_room": Setting(id="small_room", place="the small room", night_detail="A hush filled the room like a soft blanket.", bed_detail="the cozy crib", allows={"crib"}),
}

SURPRISES = {
    "lullaby_card": Surprise(id="lullaby_card", label="card", phrase="a tiny card tucked into the blanket", reveal="The card was a note for bedtime.", warmth="It had a gentle lullaby written on it.", tags={"card", "surprise"}),
    "star_card": Surprise(id="star_card", label="card", phrase="a shiny card on the crib rail", reveal="The card held a little star drawing.", warmth="It seemed to glow with a bedtime wish.", tags={"card", "surprise"}),
}

SHARINGS = {
    "share_note": Sharing(id="share_note", label="sharing", offer="Would you like to share it with me?", response="the surprise felt better when two friends looked at it together", comfort="sharing made the card feel even sweeter", tags={"sharing"}),
    "share_blanket": Sharing(id="share_blanket", label="sharing", offer="Let's share the blanket and the card", response="they could both fit under the blanket", comfort="sharing the cozy space felt kind", tags={"sharing"}),
}

NIGHTLIGHTS = {
    "glow_lamp": Nightlight(id="glow_lamp", label="nightlight", phrase="the little nightlight", glow="glowed like a sleepy moon", tags={"light"}),
    "soft_lamp": Nightlight(id="soft_lamp", label="lamp", phrase="the soft lamp", glow="shined with a gentle gold", tags={"light"}),
}

GIRL_NAMES = ["Mina", "Luna", "Penny", "Iris", "Nora", "Sadie"]
BOY_NAMES = ["Ollie", "Theo", "Finn", "Milo", "Eli", "Robin"]


@dataclass
class StoryParams:
    setting: str
    surprise: str
    sharing: str
    nightlight: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    parent_type: str = "mother"
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


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the words "card" and "crib".',
        f"Tell a gentle bedtime story where {world.facts['child'].id} finds a card near the crib and learns about sharing.",
        "Write a calm surprise-and-sharing story that ends with everyone feeling sleepy and safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    friend = world.facts["friend"]
    parent = world.facts["parent"]
    setting = SETTINGS[world.facts["setting"]]
    surprise = SURPRISES[world.facts["surprise"]]
    sharing = SHARINGS[world.facts["sharing"]]
    nightlight = NIGHTLIGHTS[world.facts["nightlight"]]
    qa = [
        ("Who is the story about?", f"It is about {child.id}, {friend.id}, and {parent.label_word}. They are in {setting.place} at bedtime."),
        ("What did the child find?", f"{child.id} found a card tucked into the crib scene. The surprise made {child.id} stop and look closely."),
        ("What did sharing change?", f"Sharing made the surprise feel kinder and warmer. It let both children enjoy the card together instead of keeping it all to one side."),
    ]
    if world.facts.get("opened"):
        qa.append(("What happened when the card was opened?", f"The card was opened and the bedtime surprise was revealed. That made the room feel more tender and ready for sleep."))
    qa.append(("How did the story end?", f"It ended with {child.id} and {friend.id} close together, with the card between them and the light turned soft. The ending shows that the surprise was shared and everyone was calm."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a crib?", "A crib is a small bed for a baby or young child. It has high sides to help keep the child safe while sleeping."),
        ("What is a card?", "A card is a small flat piece of paper. People use cards to write notes, pictures, or messages."),
        ("What does sharing mean?", "Sharing means letting someone else enjoy something with you. It is a kind way to make play feel fair and friendly."),
        ("What is a bedtime story?", "A bedtime story is a calm story read before sleep. It helps children feel cozy and ready for rest."),
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
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="nursery", surprise="lullaby_card", sharing="share_note", nightlight="glow_lamp", child_name="Mina", child_gender="girl", friend_name="Ollie", friend_gender="boy", parent_type="mother"),
    StoryParams(setting="small_room", surprise="star_card", sharing="share_blanket", nightlight="soft_lamp", child_name="Theo", child_gender="boy", friend_name="Nora", friend_gender="girl", parent_type="father"),
]


def valid_choice(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.surprise in SURPRISES and params.sharing in SHARINGS and params.nightlight in NIGHTLIGHTS


def explain_rejection() -> str:
    return "(No story: the bedtime scene needs a crib, a card surprise, and a sharing moment that fit the quiet night.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("has_card", sid))
    for shid in SHARINGS:
        lines.append(asp.fact("sharing", shid))
    for nid in NIGHTLIGHTS:
        lines.append(asp.fact("nightlight", nid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, U, H) :- setting(S), surprise(U), sharing(H), has_card(U), sense_min(M), M <= 2.
shared_story(S, U, H) :- valid(S, U, H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combo gate")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, surprise=None, sharing=None, nightlight=None, child_name=None, child_gender=None, friend_name=None, friend_gender=None, parent_type=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with a card, a crib, surprise, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--sharing", choices=SHARINGS)
    ap.add_argument("--nightlight", choices=NIGHTLIGHTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", dest="parent_type", choices=["mother", "father"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    surprise = args.surprise or rng.choice(list(SURPRISES))
    sharing = args.sharing or rng.choice(list(SHARINGS))
    nightlight = args.nightlight or rng.choice(list(NIGHTLIGHTS))
    if setting not in SETTINGS or surprise not in SURPRISES or sharing not in SHARINGS or nightlight not in NIGHTLIGHTS:
        raise StoryError(explain_rejection())
    child_name = args.child_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != child_name])
    child_gender = args.child_gender or ("girl" if child_name in GIRL_NAMES else "boy")
    friend_gender = args.friend_gender or ("girl" if friend_name in GIRL_NAMES else "boy")
    return StoryParams(
        setting=setting,
        surprise=surprise,
        sharing=sharing,
        nightlight=nightlight,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent_type=args.parent_type or rng.choice(["mother", "father"]),
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_choice(params):
        raise StoryError(explain_rejection())
    world = tell(
        SETTINGS[params.setting],
        SURPRISES[params.surprise],
        SHARINGS[params.sharing],
        NIGHTLIGHTS[params.nightlight],
        child_name=params.child_name,
        child_gender=params.child_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent_type,
    )
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
        print(asp_program("#show valid/3.\n#show shared_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} bedtime-compatible combos:")
        for combo in combos:
            print(" ", combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
            header = f"### {p.child_name} at {p.setting} ({p.surprise}, {p.sharing})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
