#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/owe_congest_sharing_bedtime_story.py
====================================================================

A small bedtime-story world about sharing, a little owed turn, and a congested
nose that makes sleep harder until kindness and a warm bedtime routine fix it.

The domain is intentionally narrow:
- two children share a cozy bedtime object,
- one child owes the other a turn or apology,
- one child has a congested nose and needs a gentle comfort routine,
- the ending proves that sharing restored calm.

It follows the shared storyworld contract and supports:
default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
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
class BedtimeSetting:
    id: str
    place: str
    glow: str
    calm_detail: str
    shared_space: str

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
class BedtimeObject:
    id: str
    label: str
    phrase: str
    comfort: str
    shares_with: str
    soothing: bool = False
    plural: bool = False
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
class SharingNeed:
    id: str
    label: str
    phrase: str
    kind: str
    soothe_phrase: str
    sense: int
    power: int
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
    setting: BedtimeSetting
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["calm"] >= THRESHOLD and ent.meters["shared"] >= THRESHOLD:
            sig = ("settle", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["sleepy"] += 1
            out.append("__settle__")
    return out


CAUSAL_RULES = [Rule("settle", "social", _r_settle)]


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


def sharing_is_reasonable(share: BedtimeObject, need: SharingNeed) -> bool:
    return share.soothing and need.sense >= SENSE_MIN


def choose_shareable() -> list[tuple[str, str]]:
    out = []
    for sid, s in SHARING_OBJECTS.items():
        for nid, n in NEEDS.items():
            if sharing_is_reasonable(s, n):
                out.append((sid, nid))
    return out


def need_severity(need: SharingNeed, delay: int) -> int:
    return 1 + delay if need.kind == "congest" else delay


def can_settle(need: SharingNeed, delay: int) -> bool:
    return need.power >= need_severity(need, delay)


def predict(world: World, need_id: str, share_id: str) -> dict:
    sim = world.copy()
    _apply_need(sim, sim.get("sick"), NEEDS[need_id], narrate=False)
    _share(sim, sim.get("helper"), sim.get("sick"), SHARING_OBJECTS[share_id], NEEDS[need_id], narrate=False)
    return {
        "settled": sim.get("sick").meters["calm"] >= THRESHOLD,
        "shared": sim.get("helper").meters["shared"] >= THRESHOLD,
    }


def _apply_need(world: World, child: Entity, need: SharingNeed, narrate: bool = True) -> None:
    child.meters[need.kind] += 1
    child.memes["tired"] += 1
    propagate(world, narrate=narrate)


def _share(world: World, helper: Entity, child: Entity, item: BedtimeObject,
           need: SharingNeed, narrate: bool = True) -> None:
    helper.meters["shared"] += 1
    child.meters["calm"] += 1
    child.memes["grateful"] += 1
    helper.memes["kind"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, a: Entity, b: Entity, setting: BedtimeSetting) -> None:
    world.say(
        f"At bedtime, {a.id} and {b.id} were in {setting.place}. "
        f"{setting.glow} and {setting.calm_detail} made the room feel soft and safe."
    )
    world.say(
        f"They shared {setting.shared_space}, because sharing helped the little room feel cozy."
    )


def trouble(world: World, sick: Entity, need: SharingNeed, item: BedtimeObject) -> None:
    sick.meters[need.kind] += 1
    sick.memes["sad"] += 1
    world.say(
        f"But {sick.id} had a congested nose, and {sick.pronoun('possessive')} breathing felt stuffy."
    )
    world.say(
        f"{sick.id} looked at {item.phrase} and sniffled, wishing bedtime could feel easier."
    )


def owe_beats(world: World, helper: Entity, sick: Entity, item: BedtimeObject) -> None:
    helper.memes["guilt"] += 1
    helper.meters["owes"] += 1
    world.say(
        f"{helper.id} remembered {helper.pronoun('possessive')} promise. "
        f"{helper.id} owed {sick.id} a turn with {item.label} after borrowing it earlier."
    )


def warn(world: World, helper: Entity, sick: Entity, need: SharingNeed, item: BedtimeObject) -> None:
    pred = predict(world, need.id, item.id)
    world.facts["predicted_settled"] = pred["settled"]
    world.say(
        f"{helper.id} could tell {sick.id} needed help. "
        f"'{sick.id}, {item.label} will help us share the calm,' {helper.pronoun()} said softly."
    )


def choose_and_share(world: World, helper: Entity, sick: Entity, item: BedtimeObject,
                     need: SharingNeed, delay: int) -> None:
    helper.meters["shared"] += 1
    sick.meters["calm"] += 1
    if can_settle(need, delay):
        world.say(
            f"{helper.id} tucked {item.phrase} beside {sick.id} and shared it gently."
        )
        world.say(
            f"The soft help worked at once, and {sick.id}'s stuffy breathing slowed."
        )
    else:
        world.say(
            f"{helper.id} tried to share {item.label}, but the stuffy feeling was too strong at first."
        )


def bedtime_finish(world: World, helper: Entity, sick: Entity, setting: BedtimeSetting,
                   item: BedtimeObject) -> None:
    helper.meters["shared"] += 1
    sick.meters["calm"] += 1
    sick.memes["love"] += 1
    helper.memes["love"] += 1
    world.say(
        f"Then {helper.id} and {sick.id} curled up together under the blanket."
    )
    world.say(
        f"{item.phrase.capitalize()} glowed nearby, and the room stayed quiet enough for sleep."
    )
    world.say(
        f"{sick.id} breathed easier, and both children drifted off feeling safe, shared, and warm."
    )


def tell(setting: BedtimeSetting, item: BedtimeObject, need: SharingNeed,
         helper_name: str = "Mina", helper_gender: str = "girl",
         sick_name: str = "Noah", sick_gender: str = "boy",
         delay: int = 0) -> World:
    world = World(setting)
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender,
                              role="helper", traits=["gentle"]))
    sick = world.add(Entity(id=sick_name, kind="character", type=sick_gender,
                            role="sick", traits=["sleepy"]))
    parent = world.add(Entity(id="Parent", kind="character", type="mother", role="parent",
                              label="the parent"))

    world.add(Entity(id="item", type="thing", label=item.label))
    world.add(Entity(id="need", type="thing", label=need.label))

    world.facts["delay"] = delay
    world.facts["item"] = item
    world.facts["need"] = need
    world.facts["helper"] = helper
    world.facts["sick"] = sick
    world.facts["parent"] = parent

    opening(world, helper, sick, setting)
    world.para()
    trouble(world, sick, need, item)
    owe_beats(world, helper, sick, item)
    warn(world, helper, sick, need, item)
    choose_and_share(world, helper, sick, item, need, delay)
    world.para()
    bedtime_finish(world, helper, sick, setting, item)
    world.facts["outcome"] = "shared"
    return world


SETTINGS = {
    "moonroom": BedtimeSetting(
        "moonroom",
        "the moonlit bedroom",
        "A moonbeam made a silver stripe across the quilt.",
        "The pillow smelled like lavender.",
        "the big blanket",
    ),
    "nursery": BedtimeSetting(
        "nursery",
        "the nursery",
        "A tiny lamp glowed like a sleepy star.",
        "The teddy bear sat waiting on the shelf.",
        "the storybook",
    ),
    "cozy_corner": BedtimeSetting(
        "cozy_corner",
        "the cozy corner",
        "A night-light blinked once and then stayed calm.",
        "The curtains made little shadows on the wall.",
        "the night lamp",
    ),
}

SHARING_OBJECTS = {
    "blanket": BedtimeObject(
        "blanket", "blanket", "a warm blanket", "warmth", "share the blanket", soothing=True,
        tags={"blanket", "shared", "bedtime"},
    ),
    "lamp": BedtimeObject(
        "lamp", "lamp", "a little lamp", "light", "share the light", soothing=True,
        tags={"lamp", "light", "bedtime"},
    ),
    "book": BedtimeObject(
        "book", "storybook", "a soft storybook", "story", "share the storybook", soothing=True,
        tags={"book", "story", "bedtime"},
    ),
}

NEEDS = {
    "congest": SharingNeed(
        "congest", "congested nose", "a congested nose", "congest",
        "the warm blanket and steady breathing helped", 2, 2, tags={"congest", "nose"},
    ),
    "sharing": SharingNeed(
        "sharing", "sharing need", "a sharing need", "share",
        "sharing made the room feel kinder", 2, 2, tags={"sharing"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Ella", "Maya", "Nora"]
BOY_NAMES = ["Noah", "Theo", "Eli", "Finn", "Owen", "Ben"]
TRAITS = ["gentle", "kind", "quiet", "patient"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    sharing_object: str
    need: str
    helper: str
    helper_gender: str
    sick: str
    sick_gender: str
    delay: int = 0
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for oid in SHARING_OBJECTS:
            for nid in NEEDS:
                if sharing_is_reasonable(SHARING_OBJECTS[oid], NEEDS[nid]):
                    combos.append((sid, oid, nid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: sharing at bedtime with a congested nose and a gentle owed turn."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sharing-object", choices=SHARING_OBJECTS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
              and (args.sharing_object is None or c[1] == args.sharing_object)
              and (args.need is None or c[2] == args.need)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, sharing_object, need = rng.choice(sorted(combos))
    helper_gender = rng.choice(["girl", "boy"])
    helper = rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    sick_gender = "boy" if helper_gender == "girl" else "girl"
    sick = rng.choice(BOY_NAMES if sick_gender == "boy" else GIRL_NAMES)
    while sick == helper:
        sick = rng.choice(BOY_NAMES if sick_gender == "boy" else GIRL_NAMES)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, sharing_object, need, helper, helper_gender, sick, sick_gender, delay=delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a 3-to-5-year-old about sharing that includes the word "{f["need"].label}".',
        f"Tell a cozy story where {f['helper'].id} shares {f['item'].phrase} with {f['sick'].id}, whose nose is {f['need'].label}.",
        f'Write a gentle bedtime story in which two children make things calmer by sharing, and include the word "owe".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    helper, sick, item, need = f["helper"], f["sick"], f["item"], f["need"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {helper.id} and {sick.id}, two children at bedtime who are learning to share kindly.",
        ),
        QAItem(
            question=f"What did {helper.id} owe {sick.id}?",
            answer=f"{helper.id} owed {sick.id} a turn with {item.label}. That promise made the sharing feel fair and gentle.",
        ),
        QAItem(
            question=f"Why was {sick.id} uncomfortable?",
            answer=f"{sick.id} had {need.phrase}, so breathing felt stuffy. The warm bedtime sharing helped {sick.id} settle down.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with both children curled up calm and warm, and {sick.id} breathing easier beside the shared bedtime item.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["item"].tags) | set(f["need"].tags)
    out = []
    if "congest" in tags:
        out.append(QAItem(
            question="What does congested mean?",
            answer="Congested means stuffed up, like when a nose feels blocked and breathing is harder than usual.",
        ))
    if "bedtime" in tags:
        out.append(QAItem(
            question="Why can sharing help at bedtime?",
            answer="Sharing can make bedtime feel calmer because everyone gets a turn and nobody feels left out.",
        ))
    if "light" in tags:
        out.append(QAItem(
            question="What makes a bedtime lamp good for children?",
            answer="A bedtime lamp gives soft light without being bright or scary, so the room can feel safe and sleepy.",
        ))
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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


def explain_rejection(need: SharingNeed, item: BedtimeObject) -> str:
    return (
        f"(No story: {item.label} is not a sensible bedtime-shared fix for {need.label}. "
        f"Pick one of the compatible shared objects instead.)"
    )


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obj in SHARING_OBJECTS.items():
        lines.append(asp.fact("sharing_object", oid))
        if obj.soothing:
            lines.append(asp.fact("soothing", oid))
    for nid, need in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("sense", nid, need.sense))
        lines.append(asp.fact("power", nid, need.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
shareable(O, N) :- sharing_object(O), need(N), soothing(O), sense(N, S), sense_min(M), S >= M.
valid(S, O, N) :- setting(S), shareable(O, N).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_shareable() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show shareable/2."))
    return sorted(o for (o, _) in asp.atoms(model, "shareable"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    sample = generate(resolve_params(argparse.Namespace(setting=None, sharing_object=None, need=None, delay=None), random.Random(7)))
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: generated story was empty")
    else:
        print("OK: generation smoke test produced a story.")
    return rc


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    sick = world.add(Entity(id=params.sick, kind="character", type=params.sick_gender, role="sick"))
    parent = world.add(Entity(id="Parent", kind="character", type="mother", role="parent", label="the parent"))
    item = SHARING_OBJECTS[params.sharing_object]
    need = NEEDS[params.need]

    world.add(Entity(id="item", label=item.label))
    world.add(Entity(id="need", label=need.label))

    opening(world, helper, sick, world.setting)
    world.para()
    trouble(world, sick, need, item)
    owe_beats(world, helper, sick, item)
    warn(world, helper, sick, need, item)
    choose_and_share(world, helper, sick, item, need, params.delay)
    world.para()
    bedtime_finish(world, helper, sick, world.setting, item)

    world.facts.update(helper=helper, sick=sick, parent=parent, item=item, need=need, delay=params.delay)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show shareable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, o, n in combos:
            print(f"  {s:12} {o:8} {n}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("moonroom", "blanket", "congest", "Mina", "girl", "Noah", "boy", 0),
            StoryParams("nursery", "book", "sharing", "Luna", "girl", "Eli", "boy", 1),
            StoryParams("cozy_corner", "lamp", "congest", "Theo", "boy", "Maya", "girl", 0),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.helper} & {p.sick}: {p.sharing_object}, {p.need}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
