#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bronco_care_dialogue_friendship_kindness_rhyming_story.py
==========================================================================================

A small storyworld about a child, a bronco, and a kind friend who helps with
care. It keeps the style close to a rhyming story: short, child-facing, concrete,
and dialogue-forward, with a clear turn from worry to kindness.

Seed words:
- bronco
- care

Features:
- Dialogue
- Friendship
- Kindness

The world models a simple stable:
- A child meets a bronco that is skittish and needs care.
- A friend notices the bronco is anxious and suggests a calm routine.
- The child chooses kind actions: soft voice, brush, water, hay, blanket.
- The bronco relaxes, the friendship grows, and the ending image proves it.

The script supports:
- default run
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    calm: bool = False
    needs_care: bool = False
    can_brush: bool = False
    can_feed: bool = False
    can_water: bool = False

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
class Stable:
    id: str
    name: str
    place: str
    rhyme: str
    cozy_line: str
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
class CareItem:
    id: str
    label: str
    action: str
    effect: str
    tags: set[str] = field(default_factory=set)
    can_feed: bool = False
    can_water: bool = False
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
    stable: str
    bronco: str
    child: str
    child_gender: str
    friend: str
    friend_gender: str
    care_item: str
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
        clone.facts = dict(self.facts)
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


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    bronco = world.get("bronco")
    if bronco.meters["spooked"] < THRESHOLD:
        return out
    sig = ("calm", bronco.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bronco.meters["spooked"] = max(0.0, bronco.meters["spooked"] - 1.0)
    bronco.memes["trust"] += 1
    out.append("__calm__")
    return out


def _r_bond(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    friend = world.get("friend")
    bronco = world.get("bronco")
    if child.memes["kindness"] < THRESHOLD:
        return out
    if friend.memes["kindness"] < THRESHOLD:
        return out
    sig = ("bond",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    bronco.memes["trust"] += 1
    out.append("__bond__")
    return out


CAUSAL_RULES = [Rule("calm", "emotion", _r_calm), Rule("bond", "social", _r_bond)]


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


def setup(world: World, stable: Stable, child: Entity, friend: Entity, bronco: Entity) -> None:
    child.memes["curious"] += 1
    friend.memes["kindness"] += 1
    bronco.meters["spooked"] = 1.0
    bronco.needs_care = True
    world.say(
        f"At {stable.place}, {child.id} found a bronco named {bronco.id}. "
        f"{stable.cozy_line}"
    )
    world.say(
        f'"What a strong brown bronco," {child.id} said. "Why do you look so low?"'
    )


def worry(world: World, friend: Entity, bronco: Entity, stable: Stable) -> None:
    friend.memes["kindness"] += 1
    world.say(
        f'"Easy now," {friend.id} said. "A bronco needs care, not fuss and no crowd. '
        f'Let\'s keep the stable calm and the words soft and proud."'
    )
    world.say(
        f'{friend.id} pointed to {stable.rhyme} and nodded at the brush and pail.'
    )


def soothe(world: World, child: Entity, bronco: Entity, care: CareItem) -> None:
    child.memes["kindness"] += 1
    child.meters["helped"] += 1
    bronco.meters["clean"] += 1
    bronco.meters["fed"] += 1 if care.can_feed else 0
    world.say(
        f'"I can help," {child.id} said. "I will {care.action} with care and grace."'
    )
    world.say(
        f'{child.id} began to {care.action}, and {care.effect} filled the place.'
    )
    propagate(world, narrate=False)


def thankful(world: World, bronco: Entity, child: Entity, friend: Entity) -> None:
    bronco.calm = True
    bronco.meters["spooked"] = 0.0
    bronco.memes["trust"] += 1
    child.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f'The bronco blinked, then leaned right near. "Nicker," it seemed to say, '
        f'"I feel much better here."'
    )
    world.say(
        f'{friend.id} laughed. "{child.id}, your care was kind and true. '
        f'This bronco trusts your gentle crew."'
    )


def ending(world: World, stable: Stable, child: Entity, friend: Entity, bronco: Entity) -> None:
    world.say(
        f"By sunset, {bronco.id} stood bright and neat, with hay in its stall and soft hoof-beat feet."
    )
    world.say(
        f"{child.id} and {friend.id} walked home in cheer, their friendship warm and their hearts sincere."
    )


CARE = {
    "brush": CareItem("brush", "brush the bronco", "brush its coat", "the coat shone soft and clean", tags={"care", "kindness"}),
    "wash": CareItem("wash", "wash the mud away", "wash it gently", "the mud washed off and the coat looked bright", can_water=True, tags={"care"}),
    "feed": CareItem("feed", "offer hay", "feed it hay", "the bronco munched and snorted with joy", can_feed=True, tags={"care", "friendship"}),
}

STABLES = {
    "barn": Stable("barn", "Sunny Barn", "Sunny Barn", "A brush and a pail sat by the rail.", "The barn felt warm and sweet."),
    "shed": Stable("shed", "Little Shed", "Little Shed", "A brush, a pail, and hay were all in a tray.", "The shed was snug and gray."),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Theo", "Max", "Noah", "Eli", "Sam"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in STABLES:
        for c in CARE:
            combos.append((s, c))
    return combos


def explanation_forbidden() -> str:
    return "(No story: the requested care choice does not fit this gentle stable tale.)"


def build_story(stable: Stable, care: CareItem, child: str, child_gender: str, friend: str, friend_gender: str) -> World:
    world = World()
    child_e = world.add(Entity(id=child, kind="character", type=child_gender, role="child"))
    friend_e = world.add(Entity(id=friend, kind="character", type=friend_gender, role="friend"))
    bronco = world.add(Entity(id="bronco", kind="character", type="thing", label="bronco", role="animal", needs_care=True))
    world.add(Entity(id="brush", type="tool", label="brush", can_brush=True))
    world.add(Entity(id="pail", type="tool", label="pail", can_water=True))
    world.add(Entity(id="hay", type="food", label="hay", can_feed=True))

    setup(world, stable, child_e, friend_e, bronco)
    world.para()
    worry(world, friend_e, bronco, stable)
    soothe(world, child_e, bronco, care)
    world.para()
    thankful(world, bronco, child_e, friend_e)
    ending(world, stable, child_e, friend_e, bronco)

    world.facts.update(stable=stable, care=care, child=child_e, friend=friend_e, bronco=bronco,
                       outcome="happy", cared=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that includes the words "bronco" and "care".',
        f'Tell a gentle friendship story where {f["child"].id} and {f["friend"].id} help a bronco with care and kindness.',
        f'Write a dialogue-rich bedtime story about a bronco, care, and a friend who speaks softly and helps out.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    bronco = f["bronco"]
    care = f["care"]
    stable = f["stable"]
    return [
        ("Who needed care in the story?",
         f"The bronco needed care. It was spooked at first, and the children helped it feel safe and calm."),
        (f"What did {child.id} do to help the bronco?",
         f"{child.id} chose to {care.action}. That kind choice helped the bronco relax and trust them."),
        (f"Why did {friend.id} speak so gently?",
         f"{friend.id} knew a bronco needs care and quiet words. The soft voice helped keep the stable calm so the bronco could settle."),
        ("How did the story end?",
         f"It ended happily, with the bronco calm and clean in {stable.name}. {child.id} and {friend.id} walked home as kinder friends than before."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a bronco?",
         "A bronco is a horse that can be lively or hard to ride. It needs calm care and gentle hands."),
        ("What does care mean?",
         "Care means helping someone or something feel safe, clean, fed, and looked after."),
        ("Why is kindness good for animals?",
         "Kindness helps animals trust people. Gentle words and gentle actions can make them feel safe."),
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
        if e.needs_care:
            bits.append("needs_care")
        if e.calm:
            bits.append("calm")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(stable="barn", bronco="bronco", child="Mia", child_gender="girl", friend="Ben", friend_gender="boy", care_item="brush"),
    StoryParams(stable="shed", bronco="bronco", child="Theo", child_gender="boy", friend="Lily", friend_gender="girl", care_item="feed"),
    StoryParams(stable="barn", bronco="bronco", child="Nora", child_gender="girl", friend="Eli", friend_gender="boy", care_item="wash"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if args.stable is None or c[0] == args.stable
              and args.care_item is None or c[1] == args.care_item]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    stable, care_item = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    friend_pool = [n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != child]
    friend = args.friend or rng.choice(friend_pool)
    return StoryParams(
        stable=stable,
        bronco="bronco",
        child=child,
        child_gender=child_gender,
        friend=friend,
        friend_gender=friend_gender,
        care_item=care_item,
    )


def generate(params: StoryParams) -> StorySample:
    if params.stable not in STABLES:
        raise StoryError(f"Unknown stable: {params.stable}")
    if params.care_item not in CARE:
        raise StoryError(f"Unknown care item: {params.care_item}")
    world = build_story(STABLES[params.stable], CARE[params.care_item], params.child, params.child_gender, params.friend, params.friend_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming storyworld about bronco care, friendship, and kindness.")
    ap.add_argument("--stable", choices=STABLES)
    ap.add_argument("--care-item", choices=CARE)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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


ASP_RULES = r"""
valid(S, C) :- stable(S), care_item(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in STABLES:
        lines.append(asp.fact("stable", s))
    for c in CARE:
        lines.append(asp.fact("care_item", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and python valid_combos().")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: smoke test generate() produced a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for s, c in asp_valid_combos():
            print(s, c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
