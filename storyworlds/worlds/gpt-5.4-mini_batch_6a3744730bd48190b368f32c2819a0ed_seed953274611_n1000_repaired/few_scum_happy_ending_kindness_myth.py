#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/few_scum_happy_ending_kindness_myth.py
=======================================================================

A small myth-like storyworld about a poor village, a river with scum, and a
kindness that turns a hard day into a happy ending.

The world models a few villagers, a river, a ferry, and a sacred lantern.
The premise is simple: the river is fouled by scum, the ferry cannot cross,
and someone must choose between pride and kindness. The turn comes when a
helper cleans the water and shares the work, and the ending image proves the
change by showing the river bright again and the village safely across.

Seed words required by the prompt are woven into the prose: "few" and "scum".
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
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "priestess"}
        male = {"boy", "man", "father", "priest"}
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
    river_name: str
    village_name: str
    affliction: str
    blessing: str
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
class Trouble:
    id: str
    label: str
    cause: str
    stain_word: str
    removes_light: bool = False
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
class Helper:
    id: str
    label: str
    act: str
    gift: str
    warmth: str
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
class Remedy:
    id: str
    label: str
    power: int
    text: str
    fail: str
    qa_text: str
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_scum_spread(world: World) -> list[str]:
    out: list[str] = []
    river = world.get("river")
    if river.meters["scum"] < THRESHOLD:
        return out
    sig = ("scum_spread",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("ferry").meters["blocked"] += 1
    world.get("villagers").memes["worry"] += 1
    out.append("The river thickened, and the ferry could not cross.")
    return out


def _r_blessing(world: World) -> list[str]:
    out: list[str] = []
    river = world.get("river")
    if river.meters["cleared"] < THRESHOLD:
        return out
    sig = ("blessed",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    river.meters["shine"] += 1
    world.get("villagers").memes["hope"] += 1
    out.append("The water opened like glass, and the lantern-light returned.")
    return out


RULES = [Rule("scum_spread", _r_scum_spread), Rule("blessing", _r_blessing)]


def valid_combos() -> list[tuple[str, str]]:
    return [("harbor", "scum")]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", "harbor"),
        asp.fact("trouble", "scum"),
        asp.fact("remedy", "cleansing"),
        asp.fact("kindness", "shared_work"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
valid(harbor, scum) :- setting(harbor), trouble(scum).
"""
    
@dataclass
class StoryParams:
    setting: str
    trouble: str
    remedy: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
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
    "harbor": Setting(
        id="harbor",
        place="the salt harbor",
        river_name="the silver river",
        village_name="the little shore village",
        affliction="scum",
        blessing="safe crossing",
    )
}

TROUBLES = {
    "scum": Trouble(
        id="scum",
        label="scum",
        cause="still water and a bad tide",
        stain_word="scummed",
        removes_light=True,
    )
}

HELPERS = {
    "kindness": Helper(
        id="kindness",
        label="kindness",
        act="shared the labor of cleaning",
        gift="a bucket and a brush",
        warmth="warm as bread",
    )
}

REMEDIES = {
    "cleansing": Remedy(
        id="cleansing",
        label="cleansing the river",
        power=1,
        text="cleaned the scum from the river with a bucket, a brush, and patient hands",
        fail="tried to clean the river, but the scum stayed thick",
        qa_text="cleaned the river with a bucket, a brush, and patient hands",
    )
}

NAMES_GIRL = ["Mira", "Nia", "Tala", "Rhea", "Sora"]
NAMES_BOY = ["Ivo", "Nilo", "Pax", "Daren", "Kian"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A myth-like storyworld of scum, kindness, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    setting = args.setting or "harbor"
    trouble = args.trouble or "scum"
    remedy = args.remedy or "cleansing"
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(NAMES_GIRL if hero_gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice([n for n in (NAMES_GIRL if helper_gender == "girl" else NAMES_BOY) if n != hero])
    if setting not in SETTINGS or trouble not in TROUBLES or remedy not in REMEDIES:
        raise StoryError("(Invalid story choices.)")
    return StoryParams(setting=setting, trouble=trouble, remedy=remedy, hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender)


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS or params.trouble not in TROUBLES or params.remedy not in REMEDIES:
        raise StoryError("(Invalid params.)")
    world = World()
    setting = SETTINGS[params.setting]
    trouble = TROUBLES[params.trouble]
    remedy = REMEDIES[params.remedy]
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero", label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper", label=params.helper))
    river = world.add(Entity(id="river", type="river", label=setting.river_name))
    ferry = world.add(Entity(id="ferry", type="thing", label="the ferry"))
    villagers = world.add(Entity(id="villagers", type="group", label="the few villagers"))
    lantern = world.add(Entity(id="lantern", type="thing", label="the sacred lantern"))
    hero.memes["duty"] += 1
    helper.memes["kindness"] += 1
    world.say(f"At {setting.place}, the few villagers watched {setting.river_name}, where scum drifted like gray ashes.")
    world.say(f"{hero.id} bore the sacred lantern, but its light could not cross the water while the ferry was blocked.")
    world.para()
    world.say(f"{helper.id} saw the trouble and answered with kindness.")
    river.meters["scum"] += 1
    propagate(world, narrate=False)
    world.say(f"Together, {hero.id} and {helper.id} did not turn away from the scum; they faced it and cleansed it.")
    river.meters["cleared"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(f"By dawn, {remedy.text}, and the ferry moved again.")
    world.say(f"The few villagers crossed singing, and the lantern shone on clean water instead of scum.")
    world.facts.update(setting=setting, trouble=trouble, remedy=remedy, hero=hero, helper=helper, river=river, ferry=ferry, villagers=villagers)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short myth for a child that includes the words "few" and "scum" and ends happily.',
        f"Tell a myth-like story where {world.facts['hero'].id} and {world.facts['helper'].id} use kindness to clear scum from a river.",
        "Write a simple, hopeful village tale where a blocked crossing opens again after patient help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question="What was wrong with the river?",
            answer="It was covered with scum, so the water looked dirty and the ferry could not cross.",
        ),
        QAItem(
            question="How did the helper solve the problem?",
            answer=f"{helper.id} chose kindness and worked with {hero.id} to clean the scum from the river. Because they stayed patient and shared the labor, the water became clear enough for the ferry to move again.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily. The few villagers crossed on the ferry, and the lantern shone on clean water instead of scum.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is scum?",
            answer="Scum is a dirty layer that floats on water or gathers at the top. It can make clean-looking water seem ugly or unsafe.",
        ),
        QAItem(
            question="What does kindness mean in a story?",
            answer="Kindness means helping without being cruel. In myths, kindness often changes a hard situation into a good one.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        parts.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    parts.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(parts)


CURATED = [
    StoryParams(setting="harbor", trouble="scum", remedy="cleansing", hero="Mira", hero_gender="girl", helper="Ivo", helper_gender="boy"),
    StoryParams(setting="harbor", trouble="scum", remedy="cleansing", hero="Nia", hero_gender="girl", helper="Pax", helper_gender="boy"),
]


def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.trouble in TROUBLES and params.remedy in REMEDIES


def explain_rejection() -> str:
    return "(No story: this world only tells a harbor myth about scum and kindness.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo gates differ.")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, trouble=None, remedy=None, hero=None, hero_gender=None, helper=None, helper_gender=None), random.Random(777)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
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
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
