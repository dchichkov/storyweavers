#!/usr/bin/env python3
"""
storyworlds/worlds/double_dude_twist_comedy.py
==============================================

A small comedy storyworld about a dude, a double order, and a twist that turns
the mistake into a funny ending.

Initial story:
---
A little dude named Milo wanted a double cookie for snack time. His sister
Tess said the picnic basket already had one cookie each, and that the last one
was for their neighbor. Milo tried to stack the cookies anyway, but the top
one slid off and landed on a banana peel.

That was the twist: the "double" cookie was not for one hungry dude after all.
It was for both kids to share with the neighbor, who turned out to be already
bringing a whole plate of snacks.

Milo laughed, Tess laughed, and the three of them made a silly cookie tower
with fruit instead. The picnic ended with crumbly smiles and no one feeling
cheated.

Causal state updates:
---
    order/plan attempt           -> actor.hunger += 1 ; actor.expectation += 1
    snack stack slips            -> snack.mess += 1 ; actor.embarrassment += 1
    shared surprise              -> actor.joy += 1 ; helper.joy += 1 ; twist += 1
    generous fix accepted        -> all joy += 1 ; actor.hunger -= 1 ; basket.nibbles += 1

Scripted social/emotional beats:
---
    setup                        -> wonder/joy rises
    mistaken doubling            -> tension/embarrassment rises
    twist reveal                 -> surprise and laughter
    shared fix                   -> joy and relief rise; awkwardness drops
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
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "sister", "woman"}
        male = {"boy", "father", "brother", "man", "dude"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)
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
class Snack:
    id: str
    label: str
    phrase: str
    mess: str
    kind: str
    quantity: int = 1
    shareable: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Twist:
    id: str
    reveal: str
    effect: str
    cue: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.twist_seen = False

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.twist_seen = self.twist_seen
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    for snack in list(world.entities.values()):
        if snack.kind != "thing":
            continue
        if snack.meters["stacked"] < THRESHOLD:
            continue
        sig = ("slip", snack.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        snack.meters["messy"] += 1
        world.get("hero").memes["embarrassment"] += 1
        out.append("__slip__")
    return out


def _r_twist(world: World) -> list[str]:
    if world.twist_seen:
        return []
    if world.get("hero").memes["embarrassment"] < THRESHOLD:
        return []
    sig = ("twist",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.twist_seen = True
    world.get("hero").memes["surprise"] += 1
    world.get("friend").memes["joy"] += 1
    return ["__twist__"]


CAUSAL_RULES = [Rule("slip", _r_slip), Rule("twist", _r_twist)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for snack_id, snack in SNACKS.items():
            if snack.shareable and snack.quantity >= 2 and setting_id in {"park", "kitchen", "yard"}:
                combos.append((setting_id, snack_id, "share"))
    return combos


@dataclass
class StoryParams:
    setting: str = "park"
    snack: str = "cookies"
    twist: str = "mixup"
    hero_name: str = "Milo"
    hero_type: str = "dude"
    friend_name: str = "Tess"
    friend_type: str = "girl"
    helper_name: str = "Nico"
    helper_type: str = "dude"
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


SETTINGS = {
    "park": Setting("the park", {"share"}),
    "kitchen": Setting("the kitchen", {"share"}),
    "yard": Setting("the yard", {"share"}),
}

SNACKS = {
    "cookies": Snack("cookies", "cookies", "a double cookie", "crumbly", "cookie", quantity=2),
    "grapes": Snack("grapes", "grapes", "a double handful of grapes", "squishy", "fruit", quantity=2),
    "popsicles": Snack("popsicles", "popsicles", "two popsicles", "sticky", "treat", quantity=2),
}

TWISTS = {
    "mixup": Twist("mixup", "the double snack was meant to be shared", "sharing", "double"),
    "neighbor": Twist("neighbor", "the neighbor arrived with more snacks", "laughter", "neighbor"),
}


def tell(setting: Setting, snack: Snack, twist: Twist, hero_name: str, hero_type: str,
         friend_name: str, friend_type: str, helper_name: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    basket = world.add(Entity(id="basket", type="thing", label="the picnic basket"))
    snack_ent = world.add(Entity(id="snack", type="thing", label=snack.label))

    world.facts.update(hero=hero, friend=friend, helper=helper, basket=basket,
                       snack=snack, twist=twist, setting=setting)

    hero.memes["hunger"] = 1
    hero.memes["hope"] = 1
    friend.memes["joy"] = 1
    helper.memes["joy"] = 1

    world.say(f"At {setting.place}, {hero_name} was a little {hero_type} with a big appetite.")
    world.say(
        f"{hero.pronoun().capitalize()} wanted {snack.phrase} and asked for a double bite, "
        f"because a {hero_type} can be very serious about snack time."
    )

    world.para()
    world.say(
        f"But {friend_name} pointed at the picnic basket and grinned. "
        f'"Hold on, dude," {friend_name} said. "The basket already has enough for sharing."'
    )
    hero.memes["expectation"] += 1
    snack_ent.meters["stacked"] += 1
    propagate(world, narrate=False)
    if hero.memes["embarrassment"] >= THRESHOLD:
        world.say(
            f"{hero_name} tried to stack the snacks into a double tower anyway, "
            f"but one slid off with a tiny plop."
        )
        world.say(
            f"That was the twist: the double snack was never supposed to be one giant pile for one hungry dude."
        )

    world.para()
    world.say(
        f"{helper_name} laughed first, then everyone else did too. "
        f"{helper_name} brought out a bowl of extra fruit, and the three of them built a silly snack tower together."
    )
    hero.memes["joy"] += 2
    friend.memes["joy"] += 1
    helper.memes["joy"] += 1
    hero.memes["embarrassment"] = max(0.0, hero.memes["embarrassment"] - 1)
    snack_ent.meters["shared"] += 1
    basket.meters["nibbles"] += 1
    world.say(
        f"By the end, {hero_name} was smiling so hard that even the crumbs looked funny, "
        f"and the picnic basket had become a place for sharing instead of a place for worry."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cheerful story for a young child about a dude named {f["hero"].id} '
        f'who wants {f["snack"].phrase} and learns to share after a funny twist.',
        f"Tell a comedy story where the word \"double\" matters, a dude gets the wrong idea about snack time, "
        f"and everyone ends up laughing together.",
        f'Write a short funny story set at {f["setting"].place} that includes the words "double" and "dude".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    snack: Snack = f["snack"]
    twist: Twist = f["twist"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"What did {hero.id} want at {setting.place}?",
            answer=f"{hero.id} wanted {snack.phrase}. He thought a double helping would make snack time extra fun.",
        ),
        QAItem(
            question=f"Why did the story turn funny for {hero.id}?",
            answer=f"The twist was that the double snack was meant for sharing, not for one person alone. Once {friend.id} pointed that out, the mistake became a joke instead of a problem.",
        ),
        QAItem(
            question=f"How did the snack time end?",
            answer=f"It ended with everyone sharing and laughing together. The snack tower became silly, and no one stayed upset.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does double mean?",
            answer="Double means two of something instead of just one. It can also mean extra or twice as much.",
        ),
        QAItem(
            question="Why do people share snacks?",
            answer="People share snacks so everyone gets a taste and no one feels left out. Sharing can make a small snack feel happier.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what you expected. It often makes the story more funny or exciting.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="park", snack="cookies", twist="mixup", hero_name="Milo", hero_type="dude",
                friend_name="Tess", friend_type="girl", helper_name="Nico", helper_type="dude"),
    StoryParams(setting="kitchen", snack="grapes", twist="neighbor", hero_name="Ben", hero_type="dude",
                friend_name="Ada", friend_type="girl", helper_name="Ollie", helper_type="dude"),
]


def explain_rejection() -> str:
    return "(No story: this world needs a shareable double snack in a place where sharing makes sense.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a dude, a double snack, and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--helper-name")
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
              and (args.snack is None or c[1] == args.snack)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, snack, twist = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        snack=snack,
        twist=args.twist or rng.choice(sorted(TWISTS)),
        hero_name=args.hero_name or rng.choice(["Milo", "Ben", "Jude", "Omar", "Theo"]),
        hero_type="dude",
        friend_name=args.friend_name or rng.choice(["Tess", "Ada", "Nia", "Lina", "June"]),
        friend_type="girl",
        helper_name=args.helper_name or rng.choice(["Nico", "Kai", "Rex", "Eli", "Bo"]),
        helper_type="dude",
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.snack not in SNACKS or params.twist not in TWISTS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], SNACKS[params.snack], TWISTS[params.twist],
                 params.hero_name, params.hero_type, params.friend_name, params.friend_type,
                 params.helper_name, params.helper_type)
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
        for group, items in [("prompts", sample.prompts), ("story_qa", sample.story_qa), ("world_qa", sample.world_qa)]:
            if group == "prompts":
                print("== prompts ==")
                for i, p in enumerate(items, 1):
                    print(f"{i}. {p}")
            else:
                print(f"== {group} ==")
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")


ASP_RULES = r"""
valid(SN, SK) :- setting(SN), snack(SK), shareable(SK), quantity(SK, Q), Q >= 2.
twist_ok(T) :- twist(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("afford", sid, a))
    for skid, sk in SNACKS.items():
        lines.append(asp.fact("snack", skid))
        lines.append(asp.fact("quantity", skid, sk.quantity))
        if sk.shareable:
            lines.append(asp.fact("shareable", skid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(a, b) for a, b, _ in valid_combos()}
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP.")
        print("only python:", sorted(py - cl))
        print("only clingo:", sorted(cl - py))
        return 1
    # smoke test ordinary generation
    sample = generate(CURATED[0])
    assert sample.story and sample.world is not None
    print("OK: ASP matches Python; generation smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for a, b in asp_valid_combos():
            print(a, b)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        i = 0
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
