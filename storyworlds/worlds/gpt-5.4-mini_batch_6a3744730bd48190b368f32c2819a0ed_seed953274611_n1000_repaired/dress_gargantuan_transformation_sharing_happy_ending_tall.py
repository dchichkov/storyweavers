#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dress_gargantuan_transformation_sharing_happy_ending_tall.py
============================================================================================

A tiny storyworld in a tall-tale register: a child finds a dress that becomes
gargantuan, the room turns into a sharing puzzle, and the ending lands safely
and happily when everyone cooperates.

The world is small on purpose:
- one child
- one magical dress
- one transformation
- one sharing decision
- one happy ending

It still models state, not frozen prose. The dress grows, the child reacts, a
helper arrives, and the final image proves what changed.
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Dress:
    id: str
    label: str
    phrase: str
    color: str
    sparkle: str
    transform_word: str
    original_fit: str
    grown_fit: str
    shareable_with: str
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
    type: str
    label: str
    voice: str
    tool: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_gargantuan(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    dress = world.entities.get("dress")
    if not child or not dress:
        return out
    if dress.meters["size"] < THRESHOLD:
        return out
    sig = ("gargantuan",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["wonder"] += 1
    child.memes["worry"] += 1
    out.append("__gargantuan__")
    return out


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


CAUSAL_RULES = [Rule("gargantuan", _r_gargantuan)]


@dataclass
class StoryParams:
    name: str = "Mabel"
    gender: str = "girl"
    helper: str = "grandma"
    helper_gender: str = "woman"
    dress: str = "blue"
    share_item: str = "cake"
    growth: int = 3
    seed: Optional[int] = None
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


NAMES = {
    "girl": ["Mabel", "June", "Luna", "Pearl", "Sadie", "Ivy", "Nora"],
    "boy": ["Hank", "Otis", "Bram", "Jasper", "Toby", "Rufus", "Milo"],
}
HELPERS = {
    "woman": ["grandma", "aunt", "neighbor", "mother"],
    "man": ["grandpa", "uncle", "neighbor", "father"],
}
DRESSES = {
    "blue": Dress(
        id="blue",
        label="dress",
        phrase="a bright blue dress",
        color="blue",
        sparkle="shone like river water in moonlight",
        transform_word="grew",
        original_fit="fit just right",
        grown_fit="could fill a barn doorway",
        shareable_with="everyone",
        tags={"dress", "transformation", "sharing"},
    ),
    "red": Dress(
        id="red",
        label="dress",
        phrase="a red dress with silver buttons",
        color="red",
        sparkle="glimmered like a cartwheel of stars",
        transform_word="swelled",
        original_fit="fit like a wish",
        grown_fit="could shade a wagon team",
        shareable_with="everyone",
        tags={"dress", "transformation", "sharing"},
    ),
}
SHARING_ITEMS = {
    "cake": "cake",
    "pancakes": "pancakes",
    "apples": "apples",
}


def valid_combos() -> list[tuple[str, str]]:
    return [(d, s) for d in DRESSES for s in SHARING_ITEMS]


def explain_rejection(dress: str, share_item: str) -> str:
    if dress not in DRESSES or share_item not in SHARING_ITEMS:
        return "(No story: the requested choices are not part of this little world.)"
    return "(No story: this tale only needs a dress and a sharing object, but the requested pair is incompatible.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: dress, gargantuan, sharing, happy ending.")
    ap.add_argument("--name", choices=sum(NAMES.values(), []))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["grandma", "aunt", "neighbor", "mother", "grandpa", "uncle", "father"])
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("--dress", choices=DRESSES)
    ap.add_argument("--share-item", choices=SHARING_ITEMS)
    ap.add_argument("--growth", type=int, choices=[1, 2, 3, 4, 5], help="how much the dress grows")
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
    if args.dress and args.dress not in DRESSES:
        raise StoryError(explain_rejection(args.dress, args.share_item or "cake"))
    if args.share_item and args.share_item not in SHARING_ITEMS:
        raise StoryError(explain_rejection(args.dress or "blue", args.share_item))

    combos = [c for c in valid_combos()
              if (args.dress is None or c[0] == args.dress)
              and (args.share_item is None or c[1] == args.share_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    dress, share_item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    helper = args.helper or rng.choice(HELPERS[helper_gender])
    growth = args.growth if args.growth is not None else rng.randint(2, 5)
    return StoryParams(name=name, gender=gender, helper=helper, helper_gender=helper_gender,
                       dress=dress, share_item=share_item, growth=growth)


def _introduce(world: World, child: Entity, dress: Dress) -> None:
    child.memes["joy"] += 1
    world.say(f"Once, in a little town with a big sky, {child.id} found {dress.phrase}.")
    world.say(f"It {dress.sparkle}, and at first it {dress.original_fit}.")


def _transform(world: World, child: Entity, dress_ent: Entity, dress: Dress, growth: int) -> None:
    dress_ent.meters["size"] += growth
    dress_ent.meters["weight"] += 1
    child.memes["surprise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then, at a wink and a whistle, the {dress.label} {dress.transform_word} and grew "
        f"so big it seemed {dress.grown_fit}."
    )
    world.say(f"{child.id} blinked up at the gargantuan {dress.label} and laughed, half amazed and half alarmed.")


def _ask_share(world: World, child: Entity, helper: Entity, dress: Dress, share_item: str) -> None:
    child.memes["need"] += 1
    world.say(
        f"{helper.id} came along with a basket of {share_item}, and {child.id} said, "
        f'"If the {dress.label} keeps growing, we may need to share more than a chair."'
    )
    world.say(
        f'{helper.id} grinned. "{child.id}, a tall tale only stays friendly when there is room for one more."'
    )


def _share(world: World, child: Entity, helper: Entity, dress: Dress, share_item: str) -> None:
    child.memes["share"] += 1
    helper.memes["share"] += 1
    world.say(
        f"So they spread out a blanket, passed around the {share_item}, and made a wide, happy circle."
    )
    world.say(
        f"{child.id} let {helper.pronoun('object')} hold one side of the {dress.label}, "
        f"and it stopped feeling scarce and started feeling splendid."
    )


def _ending(world: World, child: Entity, helper: Entity, dress: Dress) -> None:
    child.memes["happy"] += 1
    helper.memes["happy"] += 1
    world.say(
        f"By sunset, the {dress.label} still towered enormous and marvelous, but nobody minded now."
    )
    world.say(
        f"{child.id} and {helper.id} shared the last of the {world.facts['share_item']} and watched the sky turn gold."
    )
    world.say(
        f"The gargantuan {dress.label} hung nearby like a banner over a feast, and the whole town called it a happy ending."
    )


def tell(params: StoryParams) -> World:
    if params.gender not in NAMES:
        raise StoryError("invalid gender")
    if params.helper_gender not in HELPERS:
        raise StoryError("invalid helper gender")
    if params.dress not in DRESSES:
        raise StoryError("invalid dress")
    if params.share_item not in SHARING_ITEMS:
        raise StoryError("invalid share item")

    world = World()
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    dress = DRESSES[params.dress]
    dress_ent = world.add(Entity(id="dress", kind="thing", type="dress", label="dress", tags=set(dress.tags)))
    world.facts["share_item"] = params.share_item

    _introduce(world, child, dress)
    world.para()
    _transform(world, child, dress_ent, dress, params.growth)
    _ask_share(world, child, helper, dress, params.share_item)
    world.para()
    _share(world, child, helper, dress, params.share_item)
    world.para()
    _ending(world, child, helper, dress)

    world.facts.update(child=child, helper=helper, dress_cfg=dress, dress_ent=dress_ent, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a tall tale for young children that includes the words '{f['dress_cfg'].label}' and 'gargantuan'.",
        f"Tell a happy story where {f['child'].id} finds a dress that grows huge, and {f['helper'].id} helps with sharing.",
        f"Write a gentle transformation story with a very big dress, a sharing moment, and a cheerful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    dress = f["dress_cfg"]
    share_item = f["share_item"]
    return [
        QAItem(
            question=f"What happened to the dress?",
            answer=f"It transformed and grew gargantuan. It started out fitting {child.id}, then it became so large that everyone had to make room for it."
        ),
        QAItem(
            question=f"How did {child.id} and {helper.id} solve the problem?",
            answer=f"They shared the space and shared the {share_item}. That turned the big problem into a friendly, cooperative moment."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily. The gargantuan {dress.label} stayed marvelous, and everyone sat together as if the whole town were one big table."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dress?",
            answer="A dress is a piece of clothing a person can wear. It is usually meant to cover the body comfortably."
        ),
        QAItem(
            question="What does gargantuan mean?",
            answer="Gargantuan means extremely huge. It is a fancy word for something so big it feels larger than life."
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy something too. It is a kind way to make sure everyone has a turn."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(sig[0] for sig in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mabel", gender="girl", helper="grandma", helper_gender="woman",
                dress="blue", share_item="cake", growth=4),
    StoryParams(name="Hank", gender="boy", helper="uncle", helper_gender="man",
                dress="red", share_item="pancakes", growth=5),
    StoryParams(name="Ivy", gender="girl", helper="neighbor", helper_gender="woman",
                dress="blue", share_item="apples", growth=3),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for did, d in DRESSES.items():
        lines.append(asp.fact("dress_type", did))
        lines.append(asp.fact("grow_word", did, d.transform_word))
    for sid in SHARING_ITEMS:
        lines.append(asp.fact("share_item", sid))
    lines.append(asp.fact("threshold", 1))
    return "\n".join(lines)


ASP_RULES = r"""
gargantuan(D) :- dress_size(D, S), threshold(T), S >= T.
happy_ending :- gargantuan(dress), sharing, kindness.
sharing :- share_event.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2.\nvalid(D,S) :- dress_type(D), share_item(S)."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in combo model.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        _ = sample.to_json()
        print("OK: generate()/serialization smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def valid_combos() -> list[tuple[str, str]]:
    return [(d, s) for d in DRESSES for s in SHARING_ITEMS]


def generate(params: StoryParams) -> StorySample:
    if params.dress not in DRESSES:
        raise StoryError("invalid dress")
    if params.share_item not in SHARING_ITEMS:
        raise StoryError("invalid sharing item")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.dress is None or c[0] == args.dress)
              and (args.share_item is None or c[1] == args.share_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    dress, share_item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = NAMES[gender]
    name = args.name or rng.choice(name_pool)
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    helper = args.helper or rng.choice(HELPERS[helper_gender])
    growth = args.growth if args.growth is not None else rng.randint(2, 5)
    return StoryParams(name=name, gender=gender, helper=helper, helper_gender=helper_gender,
                       dress=dress, share_item=share_item, growth=growth)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for d, s in valid_combos():
            print(f"  {d:5} {s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
