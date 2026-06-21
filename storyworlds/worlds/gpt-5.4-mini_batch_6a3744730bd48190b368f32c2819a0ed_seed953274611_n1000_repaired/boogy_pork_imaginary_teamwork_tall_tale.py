#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/boogy_pork_imaginary_teamwork_tall_tale.py
===========================================================================

A small tall-tale storyworld about a barnyard boogy, a missing pork pie,
and an imaginary helper who makes the rescue possible through teamwork.

The world is built to satisfy the Storyweavers contract:
- typed entities with meters and memes
- a state-driven story engine
- grounded QA from world state
- Python and ASP parity checks
- standalone stdlib script shape
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
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
    sky: str
    feature: str
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
class Item:
    id: str
    label: str
    phrase: str
    place: str
    weight: int
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
class Helper:
    id: str
    label: str
    phrase: str
    power: int
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
class Trouble:
    id: str
    label: str
    phrase: str
    spread: int
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
class StoryParams:
    setting: str
    helper: str
    trouble: str
    item: str
    hero: str
    sidekick: str
    hero_gender: str
    sidekick_gender: str
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


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    trouble = world.get("trouble")
    if trouble.meters["loose"] < THRESHOLD:
        return out
    sig = ("spread",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("barn").meters["chaos"] += trouble.spread
    world.get("hero").memes["surprise"] += 1
    world.get("sidekick").memes["surprise"] += 1
    out.append("__spread__")
    return out


def _r_teamwork(world: World) -> list[str]:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    if hero.memes["resolve"] < THRESHOLD or sidekick.memes["resolve"] < THRESHOLD:
        return []
    sig = ("teamwork",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("barn").meters["help"] += 1
    return ["__teamwork__"]


CAUSAL_RULES = [Rule("spread", _r_spread), Rule("teamwork", _r_teamwork)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTINGS = {
    "barn": Setting(id="barn", place="the big red barn", sky="wide sky", feature="hay loft", tags={"barn"}),
    "prairie": Setting(id="prairie", place="the windy prairie", sky="wide sky", feature="open grass", tags={"prairie"}),
}

HELPERS = {
    "imaginary": Helper(id="imaginary", label="imaginary helper", phrase="an imaginary helper with a shining hat", power=3, tags={"imaginary"}),
    "neighbors": Helper(id="neighbors", label="neighbors", phrase="a chain of neighbors and hands", power=4, tags={"teamwork"}),
}

TROUBLES = {
    "boogy": Trouble(id="boogy", label="boogy", phrase="a boogy in the loft", spread=2, tags={"boogy"}),
    "stampede": Trouble(id="stampede", label="stampede", phrase="a runaway puff of pigs", spread=3, tags={"pork"}),
}

ITEMS = {
    "pork": Item(id="pork", label="pork pie", phrase="a warm pork pie", place="the kitchen shelf", weight=2, tags={"pork"}),
    "kettle": Item(id="kettle", label="kettle", phrase="a kettle of tea", place="the stove", weight=1, tags={"tea"}),
}

HERO_NAMES = ["Hank", "Mabel", "June", "Ezra", "Rosie", "Buck"]
SIDEKICK_NAMES = ["Cora", "Tate", "Ivy", "Otis", "Dora", "Will"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for hid in HELPERS:
            for tid in TROUBLES:
                for iid in ITEMS:
                    combos.append((sid, hid, tid, iid))
    return combos


def reason_gate(params: StoryParams) -> None:
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    if params.trouble not in TROUBLES:
        raise StoryError(f"Unknown trouble: {params.trouble}")
    if params.item not in ITEMS:
        raise StoryError(f"Unknown item: {params.item}")


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    helper = HELPERS[params.helper]
    trouble = TROUBLES[params.trouble]
    item = ITEMS[params.item]

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero, role="hero"))
    sidekick = world.add(Entity(id="sidekick", kind="character", type=params.sidekick_gender, label=params.sidekick, role="sidekick"))
    world.add(Entity(id="barn", kind="place", type="place", label=setting.place, tags=set(setting.tags)))
    world.add(Entity(id="trouble", kind="thing", type="thing", label=trouble.label, tags=set(trouble.tags)))
    world.add(Entity(id="item", kind="thing", type="thing", label=item.label, tags=set(item.tags)))

    hero.memes["wonder"] = 1
    sidekick.memes["wonder"] = 1
    world.facts.update(setting=setting, helper=helper, trouble=trouble, item=item, hero=hero, sidekick=sidekick)

    world.say(
        f"In {setting.place}, under the {setting.sky}, {hero.label_word} and {sidekick.label_word} were busy with a tall tale of teamwork."
    )
    world.say(
        f"They were trying to keep {item.phrase} safe while a {trouble.label} wobbled out of the {setting.feature} like a runaway storm."
    )

    world.para()
    hero.memes["resolve"] += 1
    sidekick.memes["resolve"] += 1
    world.say(
        f'"That boogy has us on our toes," said {hero.label_word}, "but I can call for help, and we can work together."'
    )
    world.say(
        f'{sidekick.label_word} nodded. "I can fetch {helper.phrase} if you steady the door."'
    )

    trouble.meters["loose"] += 1
    propagate(world, narrate=False)

    world.para()
    if helper.id == "imaginary":
        world.say(
            f'Nobody else could be seen, but {helper.phrase} seemed to answer at once, as plain as a bell in the wind.'
        )
        world.say(
            f'With that imaginary helper in the middle and the two friends pulling together, the boogy was steered back to the loft.'
        )
        world.get("barn").meters["help"] += helper.power
        world.get("barn").meters["chaos"] = max(0.0, world.get("barn").meters["chaos"] - helper.power)
    else:
        world.say(
            f'{helper.phrase} came with a hurry, and all three worked together until the trouble lost its bite.'
        )
        world.get("barn").meters["help"] += helper.power
        world.get("barn").meters["chaos"] = max(0.0, world.get("barn").meters["chaos"] - helper.power)

    world.para()
    world.say(
        f'By sunset the {trouble.label} was tucked away, the {item.label} was still warm, and the barn stood calm again.'
    )
    world.say(
        f'That was the kind of teamwork tall tales are built on: two brave young hands, and a helper imagined right on time.'
    )

    world.facts["outcome"] = "calm"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a child that includes the words "boogy", "pork", and "imaginary".',
        f"Tell a teamwork story where {f['hero'].label_word} and {f['sidekick'].label_word} use an imaginary helper to handle a boogy near pork.",
        f"Write a funny barn story with a big feeling, a shared plan, and a safe ending that mentions pork pie and an imaginary helper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    helper = f["helper"]
    trouble = f["trouble"]
    item = f["item"]
    return [
        QAItem(
            question="What were the children trying to protect?",
            answer=f"They were trying to protect {item.phrase}. It stayed safe because they worked together instead of panicking."
        ),
        QAItem(
            question="How did the imaginary helper matter?",
            answer=f"The imaginary helper gave them courage and a plan. Even though nobody could see that helper, the idea helped {hero.label_word} and {sidekick.label_word} act together."
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The boogy was put back where it belonged, the pork pie was still warm, and the barn was calm again. The trouble shrank because teamwork took over."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together. When everyone does a small part, a big problem can feel much smaller."
        ),
        QAItem(
            question="What is imaginary?",
            answer="Imaginary means made up in your mind. An imaginary helper is not something you can touch, but the idea can still encourage you."
        ),
        QAItem(
            question="What is pork?",
            answer="Pork is meat that comes from a pig. People may cook it into meals like pies or roasts."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,H,T,I) :- setting(S), helper(H), trouble(T), item(I).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for t in TROUBLES:
        lines.append(asp.fact("trouble", t))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    try:
        py = set(valid_combos())
        asp_set = set(asp_valid_combos())
        if py != asp_set:
            print("MISMATCH in valid combos")
            print("python only:", sorted(py - asp_set))
            print("asp only:", sorted(asp_set - py))
            return 1
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, helper=None, trouble=None, item=None,
            hero=None, sidekick=None, hero_gender=None, sidekick_gender=None,
            seed=None
        ), random.Random(7)))
        if not sample.story.strip():
            print("Smoke test failed: empty story")
            return 1
        print(f"OK: ASP parity and smoke test passed ({len(py)} combos).")
        return 0
    except Exception:
        traceback.print_exc()
        return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale teamwork storyworld with boogy, pork, and imaginary.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--hero-gender", dest="hero_gender", choices=["boy", "girl"])
    ap.add_argument("--sidekick-gender", dest="sidekick_gender", choices=["boy", "girl"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    helper = args.helper or rng.choice(list(HELPERS))
    trouble = args.trouble or rng.choice(list(TROUBLES))
    item = args.item or rng.choice(list(ITEMS))
    reason_gate(StoryParams(setting=setting, helper=helper, trouble=trouble, item=item, hero="", sidekick="", hero_gender="boy", sidekick_gender="girl"))
    hero_gender = args.hero_gender or rng.choice(["boy", "girl"])
    sidekick_gender = args.sidekick_gender or ("girl" if hero_gender == "boy" else "boy")
    hero = args.hero or rng.choice(["Hank", "Mabel", "June", "Ezra", "Rosie", "Buck"])
    sidekick = args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    return StoryParams(setting=setting, helper=helper, trouble=trouble, item=item, hero=hero, sidekick=sidekick, hero_gender=hero_gender, sidekick_gender=sidekick_gender)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.helper not in HELPERS or params.trouble not in TROUBLES or params.item not in ITEMS:
        raise StoryError("Invalid parameters for this storyworld.")
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
    StoryParams(setting="barn", helper="imaginary", trouble="boogy", item="pork", hero="Hank", sidekick="Cora", hero_gender="boy", sidekick_gender="girl"),
    StoryParams(setting="prairie", helper="neighbors", trouble="stampede", item="pork", hero="Mabel", sidekick="Otis", hero_gender="girl", sidekick_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show valid/4."))
        for tup in sorted(set(asp.atoms(model, "valid"))):
            print(tup)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
