#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/saloon_idea_distinction_magic_rhyming_story.py
===============================================================================

A small standalone story world for a rhyming, magic-flavored saloon tale.

Seed words:
- saloon
- idea
- distinction

The world keeps a tiny simulation: a child has an idea for a magic show in a
saloon, misunderstands the distinction between real magic and stage magic, and a
careful helper turns the moment into a safe, sparkling rhyme.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MAGIC_MIN = 1.0


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


@dataclass
class Setting:
    id: str
    label: str
    mood: str
    props: list[str] = field(default_factory=list)
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
class MagicItem:
    id: str
    label: str
    glow: str
    safe: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
    setting: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    idea: str
    magic_item: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_glow(world: World) -> list[str]:
    out = []
    helper = world.get("helper")
    item = world.get("magic_item")
    if helper.memes["calm"] < THRESHOLD or item.meters["glow"] < MAGIC_MIN:
        return out
    sig = ("glow",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("saloon").meters["sparkle"] += 1
    out.append("__glow__")
    return out


def _r_distinction(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["confusion"] < THRESHOLD:
        return []
    sig = ("distinction",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["understanding"] += 1
    return ["__understanding__"]


CAUSAL_RULES = [Rule("glow", _r_glow), Rule("distinction", _r_distinction)]


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


def predict_magic(world: World) -> dict:
    sim = world.copy()
    sim.get("magic_item").meters["glow"] += 1
    propagate(sim, narrate=False)
    return {
        "sparkle": sim.get("saloon").meters["sparkle"],
        "understanding": sim.get("child").memes["understanding"],
    }


def tell(setting: Setting, child_name: str, child_gender: str, helper_name: str,
         helper_gender: str, idea: str, magic_item: MagicItem) -> World:
    w = World()
    child = w.add(Entity(id="child", kind="character", type=child_gender, label=child_name,
                         role="dreamer", traits=["bright"], attrs={"name": child_name}))
    helper = w.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name,
                          role="guide", traits=["careful"], attrs={"name": helper_name}))
    saloon = w.add(Entity(id="saloon", kind="place", type="saloon", label=setting.label,
                          traits=["dusty", "warm"], attrs={"mood": setting.mood}))
    item = w.add(Entity(id="magic_item", kind="thing", type="magic_item",
                        label=magic_item.label, traits=["magic"], attrs={"glow": magic_item.glow}))
    item.meters["glow"] = 1.0

    child.memes["wonder"] += 1
    child.memes["confusion"] += 1
    helper.memes["calm"] += 1

    w.say(
        f"In a saloon so cozy and bright, {child_name} had an idea that felt just right. "
        f"{child_name} wanted a show that would twirl and swoon, "
        f"with a little bit of magic beneath the moon."
    )
    w.say(
        f'"{idea.capitalize()}," {child_name} said with a grin and a glance, '
        f'"I can make the old saloon all dance!"'
    )

    w.para()
    w.say(
        f"But there was a distinction to learn that day: real magic and stage magic are not the same way. "
        f"Real magic can scare; stage magic can gleam, like a ribbon of light in a bedtime dream."
    )
    w.say(
        f'{helper_name} smiled soft and said, "Let\'s keep it clean; '
        f"we can make a trick that's safe and keen."
    )
    w.say(
        f"We can wave the {magic_item.label_word}, and we can rhyme, "
        f"and make the saloon sparkle one beat at a time."'
    )

    w.para()
    pred = predict_magic(w)
    child.memes["confusion"] += 1
    child.memes["curiosity"] += 1
    w.say(
        f'{child_name} nodded and tried the new plan in tune: '
        f'{child_name} tapped the {magic_item.label_word}, and up came a boon.'
    )
    item.meters["glow"] += 1
    propagate(w, narrate=False)
    w.say(
        f"The lantern-like glow made the saloon shine; "
        f"the chairs looked merry, the floor looked fine."
    )
    w.say(
        f'Then {child_name} saw the distinction clear: '
        f"safe stage magic can bring delight and cheer."
    )
    w.say(
        f'{child_name} laughed, "{child_name} can rhyme, {child_name} can play, '
        f"and keep the true magic in a safe little way!"
    )
    w.say(
        f"With {helper_name} beside {child_name}, the saloon glowed gold, "
        f"and the whole small crowd felt brave and bold."
    )

    w.facts.update(
        setting=setting,
        child=child,
        helper=helper,
        saloon=saloon,
        magic_item=item,
        idea=idea,
        predicted=pred,
        ending="sparkling",
    )
    return w


SETTINGS = {
    "saloon": Setting(id="saloon", label="the saloon", mood="warm", props=["lantern", "hat", "piano"]),
    "back_room": Setting(id="back_room", label="the back room", mood="quiet", props=["mirror", "card"]),
}

MAGIC_ITEMS = {
    "wand": MagicItem(id="wand", label="a silver wand", glow="softly"),
    "ribbon": MagicItem(id="ribbon", label="a bright ribbon", glow="like starlight"),
    "lantern": MagicItem(id="lantern", label="a tiny lantern", glow="warmly"),
}

CHILD_NAMES = ["Milo", "Nina", "Pip", "Lena", "Jasper", "Tia"]
HELPER_NAMES = ["Ada", "Bram", "Cora", "Duke", "Elsa", "Finn"]
IDEAS = [
    "I have an idea",
    "What if we make a magic trick",
    "I know a bright little idea",
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, i, m) for s in SETTINGS for i in IDEAS for m in MAGIC_ITEMS]


def explain_rejection() -> str:
    return "(No story: this tiny world needs a magic item, a setting, and an idea.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming saloon magic story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--idea", choices=IDEAS)
    ap.add_argument("--magic-item", choices=MAGIC_ITEMS, dest="magic_item")
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"], dest="child_gender")
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"], dest="helper_gender")
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
        raise StoryError(explain_rejection())
    setting = args.setting or rng.choice(list(SETTINGS))
    idea = args.idea or rng.choice(IDEAS)
    magic_item = args.magic_item or rng.choice(list(MAGIC_ITEMS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != child])
    return StoryParams(setting=setting, child=child, child_gender=child_gender,
                       helper=helper, helper_gender=helper_gender, idea=idea,
                       magic_item=magic_item)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.magic_item not in MAGIC_ITEMS or params.idea not in IDEAS:
        raise StoryError("Invalid parameters for this saloon story.")
    world = tell(SETTINGS[params.setting], params.child, params.child_gender,
                 params.helper, params.helper_gender, params.idea,
                 MAGIC_ITEMS[params.magic_item])
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story set in a {f["setting"].label} that includes the words "saloon", "idea", and "distinction".',
        f"Tell a child-friendly magic story where {f['child'].label} learns the distinction between real magic and stage magic.",
        f"Write a small rhyming saloon tale where a bright idea becomes a safe magic trick.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item = f["magic_item"]
    qs = [
        ("What is the story about?",
         f"It is about {child.label} in {f['setting'].label} with {helper.label}. {child.label} has an idea, and the tale grows into a safe magic moment."),
        ("What distinction does the story teach?",
         "It teaches the distinction between real magic and stage magic. Real magic is the scary kind the story steps away from, while stage magic is a safe trick that sparkles for fun."),
        (f"What did {child.label} do with the magic item?",
         f"{child.label} tapped {item.label}, and the saloon began to glow. That glow made the trick look magical without turning the moment unsafe."),
    ]
    if f["ending"] == "sparkling":
        qs.append((
            "How did the story end?",
            f"It ended with the saloon shining warmly and everyone smiling. {child.label} understood the distinction and kept the magic gentle and bright."
        ))
    return qs


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a saloon?",
         "A saloon is a room for people to gather, talk, and sometimes enjoy music or a show."),
        ("What is an idea?",
         "An idea is a thought or plan in your mind. It can be the start of making something new."),
        ("What does distinction mean?",
         "A distinction is a difference between two things. It helps you tell one kind of thing from another."),
        ("What is stage magic?",
         "Stage magic is a trick or performance that looks magical but is done safely for an audience."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="saloon", child="Milo", child_gender="boy", helper="Ada", helper_gender="girl", idea="I have an idea", magic_item="wand"),
    StoryParams(setting="saloon", child="Nina", child_gender="girl", helper="Finn", helper_gender="boy", idea="What if we make a magic trick", magic_item="lantern"),
    StoryParams(setting="back_room", child="Pip", child_gender="boy", helper="Cora", helper_gender="girl", idea="I know a bright little idea", magic_item="ribbon"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for i in IDEAS:
        lines.append(asp.fact("idea", i))
    for m in MAGIC_ITEMS:
        lines.append(asp.fact("magic_item", m))
    lines.append(asp.fact("safe", "stage_magic"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, I, M) :- setting(S), idea(I), magic_item(M).
sparkles(M) :- magic_item(M), safe(stage_magic).
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"FAILED: normal generation smoke test crashed: {exc}")
        return 1
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos disagree.")
        rc = 1
    else:
        print(f"OK: ASP and Python agree on {len(valid_combos())} combos.")
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


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a saloon?", "A saloon is a gathering place with a warm, lively feeling."),
        ("What does distinction mean?", "A distinction is a difference you can notice between two things."),
        ("What is an idea?", "An idea is a thought that can grow into a plan."),
        ("What is stage magic?", "Stage magic is safe pretend magic that looks wonderful to the audience."),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show sparkles/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

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
