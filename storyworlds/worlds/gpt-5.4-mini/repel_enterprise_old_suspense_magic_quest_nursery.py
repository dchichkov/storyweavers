#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/repel_enterprise_old_suspense_magic_quest_nursery.py
=====================================================================================

A small standalone storyworld for a nursery-rhyme style tale about a child,
an old place, a suspenseful magical quest, and a wise, gentle way to repel a
tricky disturbance.

The world is built around a child-led "enterprise" to recover a lost trinket
from an old place while a magical nuisance tries to block the way. A calm helper
uses a safe charm to repel the nuisance, the quest continues, and the ending
proves what changed.

The story aims to keep a nursery-rhyme cadence:
- short concrete sentences
- repeated sounds and simple rhythm
- clear beginning, middle turn, and ending image

Seed words required by the prompt:
- repel
- enterprise
- old

Features required by the prompt:
- Suspense
- Magic
- Quest
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
CAUTIOUS_MIN = 2.0
MAGIC_SAFE_MIN = 2


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    label: str
    hush: str
    oldness: str
    eerie: str = ""

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
class Charm:
    id: str
    label: str
    phrase: str
    sound: str
    power: int
    sense: int
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
class Trouble:
    id: str
    label: str
    phrase: str
    threat: str
    spread: int
    can_be_repelted: bool = True
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
class QuestItem:
    id: str
    label: str
    phrase: str
    glow: str
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


def _r_unease(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["shadow"] < THRESHOLD:
            continue
        sig = ("unease", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in list(world.entities.values()):
            if kid.role == "quester":
                kid.memes["unease"] += 1
        out.append("__unease__")
    return out


def _r_repel(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["warded"] < THRESHOLD:
            continue
        sig = ("repel", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "gloom" in world.entities:
            world.get("gloom").meters["shadow"] = max(0.0, world.get("gloom").meters["shadow"] - 1.0)
        for kid in list(world.entities.values()):
            if kid.role == "quester":
                kid.memes["hope"] += 1
        out.append("__repel__")
    return out


RULES = [Rule("unease", "mood", _r_unease), Rule("repel", "magic", _r_repel)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                produced.extend(s for s in sent if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reason_gate(trouble: Trouble, charm: Charm) -> bool:
    return trouble.can_be_repelted and charm.sense >= MAGIC_SAFE_MIN


def respond_power_ok(charm: Charm, trouble: Trouble, delay: int) -> bool:
    return charm.power >= trouble.spread + delay


def predict(world: World, trouble_id: str, charm_id: str) -> dict:
    sim = world.copy()
    sim.get("gloom").meters["shadow"] += 1
    sim.get(charm_id).meters["warded"] += 1
    propagate(sim, narrate=False)
    return {"shadow": sim.get("gloom").meters["shadow"], "hope": sim.get("child").memes["hope"]}


def build_charms() -> dict[str, Charm]:
    return {
        "bell": Charm("bell", "a silver bell", "a bell that sings", "ding-ding", 2, 2, {"magic", "repel"}),
        "rhyme": Charm("rhyme", "a bright rhyme", "a rhyme to send it home", "la-la", 3, 3, {"magic", "repel"}),
        "spark": Charm("spark", "a little spark", "a spark of light", "twinkle", 1, 1, {"magic"}),
    }


def build_troubles() -> dict[str, Trouble]:
    return {
        "gloom": Trouble("gloom", "the gloom", "a ribbon of gloom", "it makes the path feel dim", 2, True, {"suspense", "magic"}),
        "mist": Trouble("mist", "the mist", "a hush of mist", "it hides the way", 1, True, {"suspense"}),
    }


def build_places() -> dict[str, Place]:
    return {
        "old_gate": Place("old_gate", "the old gate", "hush-hush", "old and mossy", "very still"),
        "old_tree": Place("old_tree", "the old tree", "rustle-rustle", "old and hollow", "watchful"),
    }


def build_quests() -> dict[str, QuestItem]:
    return {
        "star_key": QuestItem("star_key", "the star key", "a tiny star key", "a warm gold glow", {"quest", "magic"}),
        "moon_seed": QuestItem("moon_seed", "the moon seed", "a moon seed", "a pale pearl glow", {"quest", "magic"}),
    }


@dataclass
@dataclass
class StoryParams:
    place: str
    trouble: str
    charm: str
    quest_item: str
    name: str
    gender: str
    helper: str
    helper_gender: str
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
    places = build_places()
    troubles = build_troubles()
    charms = build_charms()
    return [(p, t, c) for p in places for t in troubles for c in charms if reason_gate(troubles[t], charms[c])]


class StoryErrorReason(Exception):
    pass


def tell(params: StoryParams) -> World:
    places = build_places()
    troubles = build_troubles()
    charms = build_charms()
    quests = build_quests()

    if params.place not in places or params.trouble not in troubles or params.charm not in charms or params.quest_item not in quests:
        raise StoryError("Unknown story parameter.")
    trouble = troubles[params.trouble]
    charm = charms[params.charm]
    if not reason_gate(trouble, charm):
        raise StoryError(f"(No story: {charm.label} is not a sensible enough charm to repel {trouble.label}.)")

    world = World()
    child = world.add(Entity("child", kind="character", type=params.gender, role="quester", label=params.name, traits=["small", "brave"]))
    helper = world.add(Entity("helper", kind="character", type=params.helper_gender, role="helper", label=params.helper, traits=["calm", "old"]))
    old_place = world.add(Entity("place", type="place", label=places[params.place].label))
    gloom = world.add(Entity("gloom", type="trouble", label=trouble.label))
    charm_ent = world.add(Entity("charm", type="charm", label=charm.label))
    quest = world.add(Entity("quest", type="quest", label=quests[params.quest_item].label))

    child.memes["hope"] = 1.0
    helper.memes["calm"] = 1.0
    world.say(f"Down by {old_place.label}, where the moss kept still, lived a small and merry child.")
    world.say(f"{params.name} had a little enterprise, a quest so light: to find {quests[params.quest_item].phrase} before the moon was bright.")
    world.say(f"But a hush came creeping, a ribbon of gloom, and the path grew dim as a cupboard room.")
    world.para()
    world.say(f'{params.name} peered ahead and whispered, "Oh dear, oh me, the dark looks wide, and who will guide me?"')
    child.memes["curiosity"] += 1
    child.meters["shadow"] += 1
    gloom.meters["shadow"] += 1
    child.meters["questing"] += 1

    predicted = predict(world, gloom.id, charm.id)
    world.facts["predicted"] = predicted

    helper.memes["calm"] += 1
    world.say(f"{params.helper} came with a twinkle and a steady tread. {params.helper} said, \"We'll keep you safe,\" and shook the old tree's head.")
    if charm.sense >= MAGIC_SAFE_MIN:
        world.say(f'"{charm.sound}," went {params.helper}, and the little charm was held up high.')
        world.say(f"It shone and hummed and began to repel the gloom, like dawn in a pie.")
        charm_ent.meters["warded"] += 1
        child.meters["shadow"] = max(0.0, child.meters["shadow"] - 1.0)
        propagate(world, narrate=False)
        if respond_power_ok(charm, trouble, params.delay):
            world.say(f"The gloom slid back, the path grew clear, and the child could march on without fear.")
            world.para()
            quest.meters["found"] += 1
            child.memes["joy"] += 1
            child.memes["hope"] += 1
            world.say(f"{params.name} found {quests[params.quest_item].phrase} beneath a leaf, a tiny thing with a moonlit belief.")
            world.say(f"Then home they went with the old bells ringing, and the night felt gentle, bright, and singing.")
            outcome = "won"
        else:
            world.say(f"The charm was brave, but the gloom was deep; it only stirred the dark from sleep.")
            world.say(f"The helper pulled the child away, and the quest ended safe, though not today.")
            outcome = "stalled"
    else:
        world.say(f"The charm was weak, the gloom stayed near, and the child felt shivery, oh dear.")
        outcome = "blocked"

    world.facts.update(
        child=child, helper=helper, place=old_place, trouble=trouble, charm=charm,
        quest=quest, outcome=outcome, params=params, quest_item=quests[params.quest_item],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story using the words "repel", "enterprise", and "old".',
        f"Tell a suspenseful magic quest for little listeners where {f['child'].label} and {f['helper'].label} visit {f['place'].label} and a charm helps repel trouble.",
        f"Write a gentle rhyming adventure with an old place, a brave child, and a magical thing that gets repelled.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    child = f["child"]
    helper = f["helper"]
    quest_item = f["quest_item"]
    trouble = f["trouble"]
    charm = f["charm"]
    qa = [
        QAItem(
            question="Who went on the quest?",
            answer=f"{params.name} went on the quest with {params.helper}. They were searching around the old place for {quest_item.phrase}.",
        ),
        QAItem(
            question="Why did the child need help?",
            answer=f"The path grew dim because {trouble.label} crept in and made everything feel suspenseful. {params.helper} helped because the child was still small and the old place felt tricky.",
        ),
    ]
    if f["outcome"] == "won":
        qa.append(
            QAItem(
                question="How was the trouble repelled?",
                answer=f"{params.helper} held up {charm.label} and used its bright magic to repel the gloom. That pushed the dark back and let the quest continue safely.",
            )
        )
        qa.append(
            QAItem(
                question="What changed by the end?",
                answer=f"The old path was no longer scary, and {params.name} could carry home {quest_item.phrase}. The ending shows that the charm made the dark step aside.",
            )
        )
    elif f["outcome"] == "stalled":
        qa.append(
            QAItem(
                question="Did the charm fully solve the problem?",
                answer=f"No, not fully. It made the trouble weaken, but it was too deep to finish the job, so the helper led the child away safely.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="What happened when the charm was too weak?",
                answer=f"The weak charm did not repel the gloom, so the child stayed blocked from the path. The helper kept everyone safe, but the quest could not move forward that night.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["trouble"].tags) | set(world.facts["charm"].tags) | set(world.facts["quest_item"].tags)
    bank = {
        "magic": [
            QAItem("What is magic in a story?", "Magic is pretend power in a story. It can make unusual things happen, like a charm shining or a spell chasing away gloom."),
        ],
        "suspense": [
            QAItem("What is suspense?", "Suspense is the feeling of wondering what will happen next. It can make a story feel quiet, tense, and exciting."),
        ],
        "quest": [
            QAItem("What is a quest?", "A quest is a search for something important. The hero keeps going until the goal is found or the way is no longer safe."),
        ],
        "repel": [
            QAItem("What does repel mean?", "To repel something is to push it back or keep it away. In a story, a charm can repel a bad shadow or a sneaky fog."),
        ],
        "old": [
            QAItem("What does old mean?", "Old means something has been around for a long time. An old place may be worn, dusty, or mossy, but it can still hide wonders."),
        ],
    }
    out: list[QAItem] = []
    for tag in ["repel", "old", "suspense", "magic", "quest"]:
        if tag in tags or tag in bank:
            out.extend(bank[tag])
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
repel_ok(T, C) :- trouble(T), charm(C), can_repel(T), sense(C, S), sense_min(M), S >= M.
safe_win :- repel_ok(T, C), power(C, P), spread(T, S), delay(D), P >= S + D.
show_repel(T, C) :- repel_ok(T, C).
show_result(win) :- safe_win.
show_result(stall) :- repel_ok(T, C), not safe_win.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in build_places():
        lines.append(asp.fact("place", pid))
    for tid, t in build_troubles().items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("spread", tid, t.spread))
        if t.can_be_repelted:
            lines.append(asp.fact("can_repel", tid))
    for cid, c in build_charms().items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("sense", cid, c.sense))
        lines.append(asp.fact("power", cid, c.power))
    lines.append(asp.fact("sense_min", MAGIC_SAFE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show repel_ok/2."))
    return sorted(set(asp.atoms(model, "repel_ok")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    try:
        import asp
        cl = set(asp_valid_combos())
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, trouble=None, charm=None, quest_item=None, name=None, gender=None, helper=None, helper_gender=None, delay=None), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"Smoke test failed: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: an old quest, a little enterprise, and a charm that can repel trouble.")
    ap.add_argument("--place", choices=build_places().keys())
    ap.add_argument("--trouble", choices=build_troubles().keys())
    ap.add_argument("--charm", choices=build_charms().keys())
    ap.add_argument("--quest-item", choices=build_quests().keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.charm and args.trouble:
        if not reason_gate(build_troubles()[args.trouble], build_charms()[args.charm]):
            raise StoryError(f"(No story: {build_charms()[args.charm].label} cannot sensibly repel {build_troubles()[args.trouble].label}.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.charm is None or c[2] == args.charm)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trouble, charm = rng.choice(sorted(combos))
    quest_item = args.quest_item or rng.choice(list(build_quests().keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(["Mina", "Lily", "Tom", "Rory", "Nina", "Pip"])
    helper = args.helper or rng.choice(["Gran", "Aunt May", "Old Ben", "Mister Blue", "Nanny Rose"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(place, trouble, charm, quest_item, name, gender, helper, helper_gender, delay)


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


CURATED = [
    StoryParams("old_gate", "gloom", "rhyme", "star_key", "Mina", "girl", "Gran", "girl", 0),
    StoryParams("old_tree", "mist", "bell", "moon_seed", "Pip", "boy", "Old Ben", "boy", 1),
    StoryParams("old_gate", "gloom", "bell", "star_key", "Lily", "girl", "Aunt May", "girl", 0),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show repel_ok/2.\n#show show_result/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible charm/trouble pairs:")
        for item in combos:
            print(item)
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
            header = f"### {p.name}: {p.place} / {p.trouble} / {p.charm}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
