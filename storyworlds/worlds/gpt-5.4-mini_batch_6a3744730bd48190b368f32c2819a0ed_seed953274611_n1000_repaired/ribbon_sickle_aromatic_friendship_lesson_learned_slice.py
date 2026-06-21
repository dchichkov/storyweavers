#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ribbon_sickle_aromatic_friendship_lesson_learned_slice.py
==========================================================================================

A small slice-of-life storyworld about friendship, a shared garden chore, and a
lesson learned gently. The seed words are woven into a concrete world where a
child, a friend, and an aromatic herb patch are part of an ordinary afternoon.

The premise is simple: two friends try to tidy a garden bed, a sickle is
involved, a ribbon marks something special, and an aromatic plant invites a
mistake. The world model tracks what is seen, handled, nicked, tied, and learned.
The ending is always calm and child-facing: a mistake, a fix, and a clearer way
to treat tools and living things.
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
LESSON_THRESHOLD = 1.0
FRIENDSHIP_THRESHOLD = 1.0


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Place:
    id: str
    label: str
    aromatic: bool = False
    calm: bool = True
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
class Item:
    id: str
    label: str
    kind: str
    aromatic: bool = False
    ribboned: bool = False
    sharp: bool = False
    safe: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Action:
    id: str
    verb: str
    outcome: str
    lesson: str
    risk: int
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
        self.place: Optional[Place] = None
        self.items: dict[str, Item] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

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
        clone.items = copy.deepcopy(self.items)
        clone.place = copy.deepcopy(self.place)
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


def _r_aroma(world: World) -> list[str]:
    out: list[str] = []
    place = world.place
    if place and place.aromatic:
        sig = ("aroma", place.id)
        if sig not in world.fired:
            world.fired.add(sig)
            for e in list(world.entities.values()):
                e.memes["ease"] += 1
            out.append("__aroma__")
    return out


def _r_scrape(world: World) -> list[str]:
    out: list[str] = []
    tool = world.items.get("sickle")
    herb = world.items.get("herb")
    if not tool or not herb:
        return out
    if tool.meters["used"] < THRESHOLD or herb.meters["nicked"] >= THRESHOLD:
        return out
    sig = ("scrape", tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    herb.meters["nicked"] += 1
    herb.memes["surprise"] += 1
    out.append("__nick__")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    herb = world.items.get("herb")
    for e in list(world.entities.values()):
        if e.role != "friend" or herb is None:
            continue
        if herb.meters["nicked"] < THRESHOLD:
            continue
        sig = ("lesson", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["lesson"] += 1
        e.memes["care"] += 1
        out.append("__lesson__")
    return out


CAUSAL_RULES = [Rule("aroma", _r_aroma), Rule("scrape", _r_scrape), Rule("lesson", _r_lesson)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_reasonable(action: Action, ribbon: Item, sickle: Item, herb: Item) -> bool:
    return ribbon.ribboned and sickle.sharp and herb.aromatic and action.risk >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for act_id, act in ACTIONS.items():
            for item_id, item in ITEMS.items():
                if item.kind == "herb" and is_reasonable(act, ITEMS["ribbon"], ITEMS["sickle"], item):
                    combos.append((scene, act_id, item_id))
    return combos


def seed_story(world: World, child: Entity, friend: Entity, place: Place, ribbon: Item, sickle: Item, herb: Item, action: Action) -> None:
    child.memes["fondness"] += 1
    friend.memes["fondness"] += 1
    world.say(
        f"On a slow afternoon, {child.id} and {friend.id} met in {place.label}. "
        f"The air was gentle there, and the herb patch smelled {herb.label} and sweet."
    )
    world.say(
        f"{child.id} found a {ribbon.label} tied near the watering can, while {friend.id} held a small {sickle.label} for trimming."
    )
    world.say(
        f'"Let me help," {friend.id} said, and {child.id} nodded, because that was how their friendship usually worked.'
    )
    world.say(
        f"They meant to tidy the bed, but the narrow blade and the loose stems made the task feel more careful than it looked."
    )


def turn_story(world: World, child: Entity, friend: Entity, ribbon: Item, sickle: Item, herb: Item, action: Action) -> None:
    child.memes["worry"] += 1
    friend.memes["focus"] += 1
    world.para()
    world.say(
        f"{friend.id} reached in a little too quickly, and the {sickle.label} brushed the herb leaves instead of the stray weeds."
    )
    sickle.meters["used"] += 1
    propagate(world, narrate=False)
    world.say(
        f"One stem gave a tiny scratch, and the air turned even more {herb.label} as the leaves let out their smell."
    )
    world.say(
        f"{child.id} winced, then said softly, '{action.lesson}'."
    )


def resolution_story(world: World, child: Entity, friend: Entity, ribbon: Item, herb: Item) -> None:
    world.para()
    child.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    friend.memes["gratitude"] += 1
    world.say(
        f"{friend.id} set the {sickle.label} down right away and tucked the bent stem behind the ribbon so it would be easy to see."
    )
    ribbon.ribboned = True
    world.say(
        f"Together they tied the {ribbon.label} around the rescued plant and skipped the rest of the trimming."
    )
    world.say(
        f"After that, they watered the bed, admired the {herb.label} smell, and laughed at how a small mistake had taught them to slow down."
    )
    world.say(
        f"By evening, the ribbon still fluttered in the garden, and the friends had a new rule: look twice before using the sharp tool."
    )


SCENES = {
    "garden": Place(id="garden", label="the garden bed", aromatic=True, calm=True),
    "yard": Place(id="yard", label="the backyard corner", aromatic=False, calm=True),
    "porch": Place(id="porch", label="the porch planter", aromatic=True, calm=True),
}

ACTIONS = {
    "trim": Action(id="trim", verb="trim the herbs", outcome="a clipped stem", lesson="We should slow down and look first", risk=1, tags={"garden", "lesson"}),
    "tidy": Action(id="tidy", verb="tidy the bed", outcome="a neater patch", lesson="Sharp tools need careful hands", risk=1, tags={"friendship", "lesson"}),
}

ITEMS = {
    "ribbon": Item(id="ribbon", label="ribbon", kind="ribbon", ribboned=True, safe=True),
    "sickle": Item(id="sickle", label="sickle", kind="tool", sharp=True),
    "herb": Item(id="herb", label="aromatic", kind="plant", aromatic=True),
}

NAMES = ["Mina", "Jules", "Ada", "Nico", "Leah", "Owen", "Iris", "Ben"]


@dataclass
class StoryParams:
    scene: str
    action: str
    child: str
    friend: str
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


CURATED = [
    StoryParams(scene="garden", action="trim", child="Mina", friend="Jules"),
    StoryParams(scene="porch", action="tidy", child="Ada", friend="Nico"),
    StoryParams(scene="garden", action="tidy", child="Leah", friend="Owen"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about friendship and a lesson learned.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--child")
    ap.add_argument("--friend")
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations.")
    scene, action, _ = rng.choice([c for c in combos if (args.scene is None or c[0] == args.scene) and (args.action is None or c[1] == args.action)])
    child = args.child or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != child])
    return StoryParams(scene=scene, action=action, child=child, friend=friend)


def tell(params: StoryParams) -> World:
    if params.scene not in SCENES:
        raise StoryError("Unknown scene.")
    if params.action not in ACTIONS:
        raise StoryError("Unknown action.")
    world = World()
    place = copy.deepcopy(SCENES[params.scene])
    world.place = place
    child = world.add(Entity(id=params.child, kind="character", type="child", role="child"))
    friend = world.add(Entity(id=params.friend, kind="character", type="child", role="friend"))
    ribbon = world.add_item(copy.deepcopy(ITEMS["ribbon"]))
    sickle = world.add_item(copy.deepcopy(ITEMS["sickle"]))
    herb = world.add_item(copy.deepcopy(ITEMS["herb"]))
    action = ACTIONS[params.action]
    seed_story(world, child, friend, place, ribbon, sickle, herb, action)
    turn_story(world, child, friend, ribbon, sickle, herb, action)
    resolution_story(world, child, friend, ribbon, herb)
    world.facts.update(child=child, friend=friend, ribbon=ribbon, sickle=sickle, herb=herb, action=action, place=place)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story about friendship that uses the words "ribbon", "sickle", and "aromatic".',
        f"Tell a gentle garden story where {f['child'].id} and {f['friend'].id} work together, make one small mistake with a sickle, and learn a careful lesson.",
        f"Write a child-friendly story set in {f['place'].label} that ends with a new rule about using sharp tools near aromatic plants.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, friend, herb, sickle, action = f["child"], f["friend"], f["herb"], f["sickle"], f["action"]
    return [
        ("Who are the story about?", f"The story is about {child.id} and {friend.id}, two friends working together in the garden."),
        ("What did the herb smell like?", f"The herb smelled aromatic, so the garden air felt sweet and noticeable. That smell made the little mistake feel extra real."),
        ("What lesson did they learn?", f"They learned to slow down and look twice before using a sickle near living plants. The ribbon helped them remember what to protect."),
        (f"Why did {friend.id} stop and set down the {sickle.label}?", f"{friend.id} noticed the herb had been nicked and understood it was time to be more careful. {action.lesson}."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a ribbon?", "A ribbon is a narrow strip of cloth used to tie, decorate, or mark something special."),
        ("What is a sickle?", "A sickle is a small curved tool used for cutting plants. It should be handled carefully because the blade is sharp."),
        ("What does aromatic mean?", "Aromatic means it has a strong, pleasant smell that you can notice easily."),
        ("What does friendship mean?", "Friendship means caring about another person, helping them, and working together kindly."),
        ("What does it mean to learn a lesson?", "It means you understand something important from what happened, so you can do better next time."),
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
        lines.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    for item in world.items.values():
        meters = {k: v for k, v in item.meters.items() if v}
        memes = {k: v for k, v in item.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if item.ribboned:
            flags.append("ribboned")
        if item.sharp:
            flags.append("sharp")
        if item.aromatic:
            flags.append("aromatic")
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {item.id:10} (item) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
aromatic_place(P) :- place(P), aromatic(P).
small_mistake(S) :- action(S), risk(S, R), R >= 1.
lesson_learned(C, F) :- friend(C), friend(F), nicked(H), care(C), sharp_tool(H).
valid(Scene, Action, Herb) :- place(Scene), action(Action), herb(Herb), aromatic(Herb).
"""


def asp_facts() -> str:
    import asp
    parts = []
    for sid in SCENES:
        parts.append(asp.fact("place", sid))
        if SCENES[sid].aromatic:
            parts.append(asp.fact("aromatic", sid))
    for aid, a in ACTIONS.items():
        parts.append(asp.fact("action", aid))
        parts.append(asp.fact("risk", aid, a.risk))
    for iid, item in ITEMS.items():
        if item.kind == "herb":
            parts.append(asp.fact("herb", iid))
        if item.kind == "tool" and item.sharp:
            parts.append(asp.fact("sharp_tool", iid))
        if item.aromatic:
            parts.append(asp.fact("aromatic", iid))
    return "\n".join(parts)


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
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_qa(sample: StorySample) -> str:
    return format_qa(sample)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def explain_rejection() -> str:
    return "(No story: the chosen items don't make a sensible garden lesson.)"


def resolve_story(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def valid_scene_action(scene: str, action: str) -> bool:
    return scene in SCENES and action in ACTIONS


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{x}" for x in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
            header = f"### {p.child} & {p.friend}: {p.scene}, {p.action}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
