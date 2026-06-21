#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/creak_twist_moral_value_sharing_folk_tale.py
=============================================================================

A small folk-tale storyworld about a creaky cottage bench, a shared feast, and
a twist that teaches a moral value: when a little one shares, the whole village
finds a kinder ending.

The story engine models:
- typed entities with physical meters and emotional memes
- a tiny causal chain driven by world state, not frozen prose
- a reasonableness gate plus an inline ASP twin
- three QA sets grounded in the generated world

The seed prompt is "creak" with features Twist, Moral Value, Sharing, in a
folk-tale style.
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
MORAL_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "grandmother"}
        male = {"boy", "father", "man", "king", "grandfather"}
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


@dataclass
class Setting:
    id: str
    place: str
    time: str
    mood: str
    affords: set[str] = field(default_factory=set)
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
class Treasure:
    id: str
    label: str
    phrase: str
    owner: str
    kind: str = "food"
    shareable: bool = True
    tasty: bool = True
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
class Twist:
    id: str
    reveal: str
    surprise: str
    turns: str
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
class Moral:
    id: str
    saying: str
    lesson: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c.facts = dict(self.facts)
        return c


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


def _r_hunger(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["hunger"] < THRESHOLD:
            continue
        sig = ("hunger", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["want"] += 1
        out.append("")
    return out


def _r_sharing_spreads(world: World) -> list[str]:
    out: list[str] = []
    giver = world.entities.get("child")
    if not giver or giver.memes["shared"] < THRESHOLD:
        return out
    sig = ("shared", giver.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for name in ("mothers_joy", "neighbors_joy"):
        if name in world.entities:
            world.get(name).memes["joy"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("hunger", "physical", _r_hunger),
    Rule("sharing", "social", _r_sharing_spreads),
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
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(share: Treasure, twist: Twist, setting: Setting) -> bool:
    return share.shareable and "bench" in setting.affords and "moral" in twist.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, twist in TWISTS.items():
            for pid, treasure in TREASURES.items():
                if reasonableness_gate(treasure, twist, setting):
                    combos.append((sid, tid, pid))
    return combos


def best_treasure() -> Treasure:
    return max(TREASURES.values(), key=lambda t: int(t.shareable))


def predict_twist(world: World, treasure_id: str) -> dict:
    sim = world.copy()
    _take(sim, sim.get("child"), sim.get(treasure_id), narrate=False)
    return {"shared": sim.get("child").memes["shared"] >= THRESHOLD}


def _take(world: World, child: Entity, treasure: Entity, narrate: bool = True) -> None:
    child.meters["fullness"] += 1
    treasure.meters["used"] += 1
    if narrate:
        world.say("")


def _build_setup(world: World, child: Entity, elder: Entity, setting: Setting) -> None:
    child.memes["hope"] += 1
    elder.memes["care"] += 1
    world.say(
        f"In a little village by the woods, {child.id} and {elder.id} lived near "
        f"{setting.place}. {setting.mood.capitalize()} sat over the roofs, and the old "
        f"wooden bench gave a soft creak whenever anyone sat upon it."
    )


def desire(world: World, child: Entity, treasure: Treasure) -> None:
    child.memes["want"] += 1
    world.say(
        f"One evening, {child.id} found {treasure.phrase} waiting on the bench. "
        f"The sight made {child.pronoun()} smile and stand very still."
    )


def warn(world: World, elder: Entity, child: Entity, treasure: Treasure) -> None:
    pred = predict_twist(world, "treasure")
    if pred["shared"]:
        world.facts["predicted_sharing"] = True
    world.say(
        f'"Wait," said {elder.id}. "That {treasure.label_word} is for everyone in the "
        f"house, and the villagers will come hungry after the market."'
    )


def twist_reveal(world: World, twist: Twist, treasure: Treasure) -> None:
    world.say(
        f"Then came the twist: {twist.reveal}. {twist.surprise} "
        f"The little surprise {twist.turns}, and the bench gave another creak as the lid "
        f"lifted."
    )


def share_act(world: World, child: Entity, elder: Entity, treasure: Treasure, moral: Moral) -> None:
    child.memes["shared"] += 1
    child.memes["kindness"] += 1
    elder.memes["relief"] += 1
    world.say(
        f"{child.id} did not hide the {treasure.label}. Instead, {child.pronoun()} "
        f"carried it to {elder.id} and said, 'Let us share.' "
        f"{moral.saying}"
    )


def ending(world: World, child: Entity, elder: Entity, treasure: Treasure) -> None:
    child.memes["joy"] += 1
    elder.memes["joy"] += 1
    world.say(
        f"Together they cut the {treasure.label} into little pieces and passed them around. "
        f"By the time the stars came out, the bench was empty, the bowl was full, and "
        f"the whole cottage smelled warm and sweet."
    )
    world.say(
        f"{child.id} learned that a gift grows larger when it is shared, and {elder.id} "
        f"smiled at the bright, gentle ending."
    )


def tell(setting: Setting, treasure: Treasure, twist: Twist, moral: Moral,
         child_name: str = "Milo", child_gender: str = "boy",
         elder_name: str = "Gran", elder_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child", traits=["small"], attrs={"relation": "grandchild"}))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender,
                             role="elder", traits=["wise"], attrs={"relation": "grandchild"}))
    bench = world.add(Entity(id="bench", type="bench", label="old bench"))
    treasure_ent = world.add(Entity(id="treasure", type="treasure", label=treasure.label))
    world.facts["setting"] = setting
    world.facts["treasure"] = treasure
    world.facts["twist"] = twist
    world.facts["moral"] = moral

    _build_setup(world, child, elder, setting)
    world.para()
    desire(world, child, treasure)
    warn(world, elder, child, treasure)
    world.para()
    twist_reveal(world, twist, treasure)
    share_act(world, child, elder, treasure, moral)
    world.para()
    ending(world, child, elder, treasure)

    world.facts.update(child=child, elder=elder, bench=bench, treasure_ent=treasure_ent)
    return world


SETTINGS = {
    "cottage": Setting(id="cottage", place="the mossy cottage", time="evening", mood="twilight",
                       affords={"bench"}),
    "village": Setting(id="village", place="the village green", time="evening", mood="golden",
                       affords={"bench"}),
    "orchard": Setting(id="orchard", place="the apple orchard", time="evening", mood="soft",
                       affords={"bench"}),
}

TREASURES = {
    "honeycake": Treasure(id="honeycake", label="honey cake", phrase="a little honey cake", owner="elder",
                          tags={"sweet", "sharing"}),
    "bread": Treasure(id="bread", label="bread loaf", phrase="a crusty loaf of bread", owner="elder",
                      tags={"sharing"}),
    "berries": Treasure(id="berries", label="berry tart", phrase="a berry tart", owner="elder",
                        tags={"sweet", "sharing"}),
}

TWISTS = {
    "mouse": Twist(id="mouse", reveal="A tiny mouse was already nibbling the crust", surprise="But the cake was not lost.",
                   turns="belonged to the mouse as much as to the child", tags={"twist", "moral"}),
    "beggar": Twist(id="beggar", reveal="a tired traveler had stopped at the gate", surprise="He had not come to steal.",
                     turns="asked only for a kind share", tags={"twist", "moral"}),
    "crow": Twist(id="crow", reveal="a black crow had pecked the corner clean", surprise="The rest still smelled sweet.",
                  turns="was enough for more than one hungry mouth", tags={"twist", "moral"}),
}

MORALS = {
    "share": Moral(id="share", saying="And so the child learned: a generous hand keeps a treasure warm.", lesson="sharing brings joy",
                   tags={"moral", "sharing"}),
    "more": Moral(id="more", saying="For when one gives a little, there is often enough for all.", lesson="a gift can grow",
                  tags={"moral", "sharing"}),
}

GIRL_NAMES = ["Mira", "Lena", "Tess", "Nora", "Ari"]
BOY_NAMES = ["Milo", "Ben", "Otis", "Pip", "Jory"]


@dataclass
class StoryParams:
    setting: str
    treasure: str
    twist: str
    moral: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about a creaky bench, a sharing twist, and a moral.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["boy", "girl"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-gender", choices=["man", "woman"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.twist is None or c[1] == args.twist)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, twist, treasure = rng.choice(sorted(combos))
    moral = args.moral or rng.choice(sorted(MORALS))
    child_gender = args.child_gender or rng.choice(["boy", "girl"])
    elder_gender = args.elder_gender or "woman"
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_name = args.elder_name or "Gran"
    return StoryParams(setting=setting, treasure=treasure, twist=twist, moral=moral,
                       child_name=child_name, child_gender=child_gender,
                       elder_name=elder_name, elder_gender=elder_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a 3-to-5-year-old that includes the word "creak" and a surprise ending about sharing.',
        f"Tell a short village story where {f['child'].id} finds {f['treasure'].phrase}, hears a creak, and learns to share.",
        f"Write a gentle moral story with a twist: the child thinks the treat is theirs alone, but sharing changes the ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, elder, treasure, twist, moral = f["child"], f["elder"], f["treasure"], f["twist"], f["moral"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {elder.id}, a child and an elder living near the bench in the village. The story follows how they handle the treat and the surprise together."
        ),
        QAItem(
            question="What made the story turn?",
            answer=f"The turn came when {twist.reveal.lower()}. That twist changed the treat from something to hide into something to share."
        ),
        QAItem(
            question="What moral does the story teach?",
            answer=f"It teaches that {moral.lesson}. The ending proves it because {child.id} shares the food and everyone feels glad."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a creak sound like?",
            answer="A creak is a small, squeaky sound, like old wood making a little complaint when someone sits down or opens it."
        ),
        QAItem(
            question="Why is sharing a good thing?",
            answer="Sharing is kind because it lets more than one person enjoy something. It can turn a small treat into a happy moment for everyone."
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old-style story from the people, often with simple characters, a surprise, and a lesson to learn."
        ),
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, P) :- setting(S), twist(T), treasure(P), shareable(P), bench_setting(S), moral_twist(T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "bench" in s.affords:
            lines.append(asp.fact("bench_setting", sid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if t.shareable:
            lines.append(asp.fact("shareable", tid))
    for tid, t in TWISTS.items():
        lines.append(asp.fact("twist", tid))
        if "moral" in t.tags:
            lines.append(asp.fact("moral_twist", tid))
    for mid in MORALS:
        lines.append(asp.fact("moral", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: generate() smoke test produced a story.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams(setting="cottage", treasure="honeycake", twist="mouse", moral="share",
                child_name="Milo", child_gender="boy", elder_name="Gran", elder_gender="woman"),
    StoryParams(setting="village", treasure="bread", twist="beggar", moral="more",
                child_name="Mira", child_gender="girl", elder_name="Grandpa", elder_gender="man"),
    StoryParams(setting="orchard", treasure="berries", twist="crow", moral="share",
                child_name="Tess", child_gender="girl", elder_name="Grandma", elder_gender="woman"),
]


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    treasure = TREASURES.get(params.treasure)
    twist = TWISTS.get(params.twist)
    moral = MORALS.get(params.moral)
    if not (setting and treasure and twist and moral):
        raise StoryError("(Invalid params for this world.)")
    world = tell(setting, treasure, twist, moral, params.child_name, params.child_gender,
                 params.elder_name, params.elder_gender)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
