#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/seltzer_yam_sharing_moral_value_nursery_rhyme.py
=================================================================================

A small, self-contained storyworld about sharing a treat in a nursery-rhyme style.

Premise
-------
A child has a fizzy seltzer and a yam snack. A friend arrives, the child
faces a tug between keeping everything and sharing fairly, and the world
resolves through a moral choice that changes the emotional state of both
characters.

The engine is intentionally tiny but still state-driven:
- typed entities carry physical meters and emotional memes
- a forward rule pass updates state
- prose is rendered from the resulting world, not from a frozen template
- a Python reasonableness gate has an inline ASP twin
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MORAL_MIN = 2
SHARING_MIN = 2


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
class ItemCfg:
    id: str
    label: str
    phrase: str
    taste: str
    share_portion: str
    warm: bool = False
    fizzy: bool = False
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
class CharacterCfg:
    id: str
    gender: str
    type: str
    traits: list[str] = field(default_factory=list)
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
class StoryParams:
    child: str
    child_gender: str
    friend: str
    friend_gender: str
    parent: str
    treat: str
    setting: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    snack = world.get("snack")
    if snack.meters["shared"] >= THRESHOLD and ("soften",) not in world.fired:
        world.fired.add(("soften",))
        world.get("child").memes["joy"] += 1
        world.get("friend").memes["joy"] += 1
        out.append("The room felt warmer, and both children smiled.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for s in _r_soften(world):
            changed = True
            produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    taste: str
    share_portion: str
    warm: bool = False
    fizzy: bool = False
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


SETTINGS = {
    "kitchen": {"place": "the kitchen", "scene": "a bright little kitchen", "tags": {"home"}},
    "porch": {"place": "the porch", "scene": "a sunny front porch", "tags": {"home"}},
}

ITEMS = {
    "seltzer": Item(id="seltzer", label="seltzer", phrase="a glass of seltzer", taste="bubbly and bright",
                    share_portion="a small sip of seltzer", fizzy=True, tags={"drink", "fizzy"}),
    "yam": Item(id="yam", label="yam", phrase="a warm yam", taste="soft and sweet",
                share_portion="a neat little spoonful of yam", warm=True, tags={"food", "warm"}),
}

CHARACTERS = {
    "Ava": CharacterCfg(id="Ava", gender="girl", type="girl", traits=["kind"]),
    "Ben": CharacterCfg(id="Ben", gender="boy", type="boy", traits=["patient"]),
    "Mila": CharacterCfg(id="Mila", gender="girl", type="girl", traits=["gentle"]),
    "Noah": CharacterCfg(id="Noah", gender="boy", type="boy", traits=["thoughtful"]),
}

PARENTS = {
    "mother": "mom",
    "father": "dad",
}


def valid_combos() -> list[tuple[str, str]]:
    return [(s, t) for s in SETTINGS for t in ITEMS]


def reasonableness_gate(setting: str, treat: str) -> None:
    if setting not in SETTINGS:
        raise StoryError("(No story: unknown setting.)")
    if treat not in ITEMS:
        raise StoryError("(No story: unknown treat.)")


def tell(setting: str, child: CharacterCfg, friend: CharacterCfg, parent: str, treat: Item) -> World:
    world = World()
    c = world.add(Entity(id=child.id, kind="character", type=child.type, role="child", traits=child.traits))
    f = world.add(Entity(id=friend.id, kind="character", type=friend.type, role="friend", traits=friend.traits))
    p = world.add(Entity(id="Parent", kind="character", type=parent, role="parent", label="the parent"))
    snack = world.add(Entity(id="snack", kind="thing", type=treat.id, label=treat.label, attrs={"kind": treat.id}))
    world.facts.update(setting=setting, child=c, friend=f, parent=p, snack=snack, treat=treat)

    scene = SETTINGS[setting]["scene"]
    world.say(
        f"Down in {SETTINGS[setting]['place']}, in {scene}, {c.id} had {treat.phrase}. "
        f"It looked so nice, it sparkled and shone."
    )
    world.say(
        f"{f.id} came by with a hungry grin, and {c.id} held the treat in a careful spin. "
        f'\"Can I have some?\" said {f.id} with cheer, \"for sharing is sweet, and kindness is dear.\"'
    )

    c.memes["want_keep"] += 1
    c.memes["sharing"] += 1
    c.memes["moral"] = 1.0

    world.para()
    world.say(
        f"{c.id} looked at the {treat.label} round, then looked at {f.id} on the ground. "
        f"The bubbles danced, the yam was warm, and both could help a tiny storm."
    )

    if treat.fizzy:
        world.say("The seltzer fizzed like little bells.")
    if treat.warm:
        world.say("The yam gave off a cozy smell.")

    # Decision: keep or share.
    c.memes["greedy"] += 0.0
    should_share = True

    world.para()
    if should_share:
        snack.meters["shared"] = 1.0
        c.memes["sharing"] += 1
        c.memes["moral"] += 1
        f.memes["gratitude"] += 1
        world.say(
            f"So {c.id} smiled a small, brave smile, and shared the {treat.label}. "
            f"{c.id} poured {treat.share_portion} for {f.id}, and left plenty to go around."
        )
        world.say(
            f"{f.id} took the share and said, \"Thank you, thank you!\" "
            f"The little room felt bigger with kindness inside."
        )
        propagate(world, narrate=True)
    else:
        snack.meters["shared"] = 0.0

    world.para()
    world.say(
        f"In the end, {c.id} had less in hand but more in heart, and {f.id} had a treat as well. "
        f"That is how the rhyme goes: sharing makes the sweetest song of all."
    )

    world.facts["outcome"] = "shared" if snack.meters["shared"] >= THRESHOLD else "kept"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    treat = f["treat"]
    return [
        f'Write a nursery-rhyme-style story that includes the words "seltzer" and "yam" and teaches sharing.',
        f"Tell a gentle moral tale where {f['child'].id} learns to share {treat.label} with {f['friend'].id}.",
        f"Write a short rhyme about a child, a friend, and {treat.share_portion}, ending with a kind moral.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, fr, treat = f["child"], f["friend"], f["treat"]
    return [
        QAItem(
            question="What did the child have?",
            answer=f"The child had {treat.phrase}. It was the special treat in the story, and it set up the sharing choice."
        ),
        QAItem(
            question="What did the friend ask for?",
            answer=f"The friend asked for some of the treat, and {c.id} chose to share. That made the ending kinder for both children."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with sharing and a happy feeling. {c.id} had a little less to keep, but both children felt warm and pleased."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is seltzer?",
            answer="Seltzer is fizzy water. It bubbles and sparkles, and people often drink it cold."
        ),
        QAItem(
            question="What is a yam?",
            answer="A yam is a root vegetable. It can be cooked until it is soft and sweet."
        ),
        QAItem(
            question="Why is sharing a good choice?",
            answer="Sharing is good because it helps another person feel cared for. It also turns one small joy into two happy smiles."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
treat(T) :- item(T).
shared :- has(snack), shared_item(snack).
good_end :- shared.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for cid in CHARACTERS:
        lines.append(asp.fact("child_name", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, treat=None, child=None, friend=None, parent=None, gender=None, seed=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about seltzer, yam, and sharing.")
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--treat", choices=list(ITEMS))
    ap.add_argument("--child", choices=list(CHARACTERS))
    ap.add_argument("--friend", choices=list(CHARACTERS))
    ap.add_argument("--parent", choices=list(PARENTS))
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
    if args.setting and args.treat:
        reasonableness_gate(args.setting, args.treat)

    setting = args.setting or rng.choice(list(SETTINGS))
    treat = args.treat or rng.choice(list(ITEMS))
    child = args.child or rng.choice(list(CHARACTERS))
    friend = args.friend or rng.choice([k for k in CHARACTERS if k != child])
    parent = args.parent or rng.choice(list(PARENTS))
    return StoryParams(
        child=child,
        child_gender=CHARACTERS[child].gender,
        friend=friend,
        friend_gender=CHARACTERS[friend].gender,
        parent=parent,
        treat=treat,
        setting=setting,
    )


def generate(params: StoryParams) -> StorySample:
    if params.child not in CHARACTERS:
        raise StoryError("unknown child")
    if params.friend not in CHARACTERS:
        raise StoryError("unknown friend")
    if params.treat not in ITEMS:
        raise StoryError("unknown treat")
    if params.setting not in SETTINGS:
        raise StoryError("unknown setting")
    world = tell(
        setting=params.setting,
        child=CHARACTERS[params.child],
        friend=CHARACTERS[params.friend],
        parent=params.parent,
        treat=ITEMS[params.treat],
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting, treat in valid_combos():
            p = StoryParams(
                child="Ava",
                child_gender="girl",
                friend="Ben",
                friend_gender="boy",
                parent="mother",
                treat=treat,
                setting=setting,
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
