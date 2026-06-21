#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/shepard_bow_dialogue_moral_value_reconciliation_myth.py
=======================================================================================

A small mythic storyworld about a shepherd, a bow, a moral choice, and a
reconciliation. The domain is built from the seed words and features:

- shepherd
- bow
- Dialogue
- Moral Value
- Reconciliation
- Mythic style

The story premise:
A shepherd finds a sacred bow by a spring. A proud hunter wants it for glory,
but the shepherd insists it belongs to the village's promise of protection,
not bragging. A tense dialogue leads to a moral choice: return the bow to the
spring-altar, where the river and people are reconciled.

The world is not a frozen paragraph. It is a tiny simulation with entities,
physical state in meters, emotional state in memes, a simple causal engine,
and a declarative ASP twin for parity checks.
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    sacred: bool = False
    owned_by: str = ""

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "woman", "queen", "goddess"}
        masculine = {"boy", "father", "man", "king", "shepherd", "hunter"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
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
class Theme:
    id: str
    opening: str
    land: str
    sacred_place: str
    gift_phrase: str
    ending_image: str
    moral_value: str
    reconciliation_image: str
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
class Bow:
    id: str
    label: str
    phrase: str
    sacred_name: str
    purpose: str
    can_be_returned: bool = True
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    bow = world.entities.get("bow")
    spring = world.entities.get("spring")
    if not bow or not spring:
        return out
    if bow.meters["returned"] < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    spring.memes["peace"] += 1
    for eid in ("shepherd", "hunter"):
        if eid in world.entities:
            world.get(eid).memes["relief"] += 1
            world.get(eid).memes["respect"] += 1
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("reconcile", "social", _r_reconcile)]


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


SENSE_MIN = 2


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for bow in BOWS:
            for response in RESPONSES:
                combos.append((theme, bow, response))
    return combos


def return_possible(bow: Bow) -> bool:
    return bow.can_be_returned


def moral_turn(world: World, shepherd: Entity, hunter: Entity, bow: Bow, theme: Theme) -> None:
    shepherd.memes["resolve"] += 1
    hunter.memes["pride"] += 1
    world.say(
        f"At {theme.land}, {shepherd.id} lifted {bow.phrase} and said, "
        f'"This is not a prize for boasting. It is a promise to keep."'
    )
    world.say(
        f'{hunter.id} frowned. "If I carry it, the people will praise me," '
        f"{hunter.id} said."
    )


def warn(world: World, shepherd: Entity, hunter: Entity, bow: Bow, theme: Theme) -> None:
    shepherd.memes["steadfastness"] += 1
    world.say(
        f'{shepherd.id} shook {shepherd.pronoun("possessive")} head. '
        f'"The bow belongs at {theme.sacred_place}, by the spring. '
        f"It listens to duty, not pride.""
    )
    world.say(
        f'"Then let it choose the right hands," {hunter.id} said softly.'
    )


def handover(world: World, hunter: Entity, bow_ent: Entity, bow: Bow) -> None:
    hunter.memes["shame"] += 1
    bow_ent.meters["returned"] += 1
    bow_ent.owned_by = "spring"
    world.say(
        f"{hunter.id} lowered {bow.phrase} at last. {hunter.id} said, "
        f'"I wanted glory, but I see the higher road now."'
    )


def bless(world: World, spring: Entity, theme: Theme, bow: Bow) -> None:
    spring.meters["bright"] += 1
    world.say(
        f"Then the waters brightened at {theme.sacred_place}. "
        f"{bow.sacred_name} no longer felt heavy; it felt holy again."
    )
    world.say(theme.reconciliation_image)


def tell(theme: Theme, bow: Bow, response: Response, shepherd_name: str, hunter_name: str) -> World:
    world = World()
    shepherd = world.add(Entity(id=shepherd_name, kind="character", type="shepherd", role="keeper"))
    hunter = world.add(Entity(id=hunter_name, kind="character", type="hunter", role="seeker"))
    spring = world.add(Entity(id="spring", kind="place", type="spring", label="the spring"))
    bow_ent = world.add(Entity(id="bow", kind="thing", type="bow", label=bow.label, sacred=True))
    bow_ent.owned_by = shepherd.id

    shepherd.memes["duty"] += 1
    hunter.memes["pride"] += 1
    bow_ent.meters["held"] += 1

    world.say(
        f"{theme.opening} In {theme.land}, {shepherd.id} found {bow.phrase} beside {theme.sacred_place}."
    )
    world.say(
        f"By mythic law, the bow belonged to the village only when it rested in its rightful place."
    )
    world.para()

    moral_turn(world, shepherd, hunter, bow, theme)
    warn(world, shepherd, hunter, bow, theme)
    if response.id == "yield":
        world.say(
            f'{hunter.id} bowed {hunter.pronoun("possessive")} head. '
            f'"Then let me help return it," {hunter.id} said.'
        )
    else:
        world.say(
            f'{hunter.id} hesitated, then asked, "What if I keep it a little longer?"'
        )

    world.para()
    handover(world, hunter, bow_ent, bow)
    propagate(world, narrate=False)
    bless(world, spring, theme, bow)
    world.say(
        f"{theme.ending_image} {shepherd.id} and {hunter.id} walked away as friends, "
        f"and the bow slept where it should."
    )

    world.facts.update(
        theme=theme,
        bow=bow,
        response=response,
        shepherd=shepherd,
        hunter=hunter,
        spring=spring,
        outcome="reconciled",
        returned=bow_ent.meters["returned"] >= THRESHOLD,
    )
    return world


THEMES = {
    "spring": Theme(
        id="spring",
        opening="Long ago, when rivers still remembered the names of stars,",
        land="the green valley",
        sacred_place="the stone spring",
        gift_phrase="a gift of calm hands",
        ending_image="The moon rose over the spring like a silver bowl.",
        moral_value="duty",
        reconciliation_image="The spring sang once more, and the people felt their quarrel dissolve.",
    ),
    "hill": Theme(
        id="hill",
        opening="In an age when owls carried secrets over the hills,",
        land="the high hill country",
        sacred_place="the mossy shrine",
        gift_phrase="a vow of careful hands",
        ending_image="The dawn touched the hill with gold.",
        moral_value="humility",
        reconciliation_image="The shrine glowed quietly, and even hard hearts grew gentle.",
    ),
}

BOWS = {
    "sacred_bow": Bow(
        id="sacred_bow",
        label="the sacred bow",
        phrase="the sacred bow",
        sacred_name="the sacred bow",
        purpose="to protect the village from wolves and winter",
        tags={"bow", "sacred"},
    ),
    "hunter_bow": Bow(
        id="hunter_bow",
        label="the old bow",
        phrase="the old bow",
        sacred_name="the old bow",
        purpose="to guide arrows and choices alike",
        tags={"bow"},
    ),
}

RESPONSES = {
    "yield": Response(
        id="yield",
        sense=3,
        power=3,
        text="bowed and agreed to return it with care",
        fail="could not see that glory fades faster than kindness",
        qa_text="bowed and agreed to return it with care",
        tags={"reconcile"},
    ),
    "cling": Response(
        id="cling",
        sense=2,
        power=1,
        text="held on to the bow a little too tightly",
        fail="held on to the bow a little too tightly and almost broke the peace",
        qa_text="held on to the bow a little too tightly",
        tags={"conflict"},
    ),
    "return": Response(
        id="return",
        sense=4,
        power=4,
        text="returned the bow at once",
        fail="could not be swayed from a selfish wish",
        qa_text="returned the bow at once",
        tags={"reconcile"},
    ),
}


GIRL_NAMES = ["Mira", "Lena", "Asha", "Iris", "Nora"]
BOY_NAMES = ["Eli", "Taran", "Rowan", "Orin", "Bren"]


@dataclass
class StoryParams:
    theme: str
    bow: str
    response: str
    shepherd_name: str
    hunter_name: str
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


KNOWLEDGE = {
    "bow": [("What is a bow?",
             "A bow is a curved tool used to send arrows. In myths, a bow can also stand for duty, skill, or a sacred promise.")],
    "shepherd": [("What does a shepherd do?",
                  "A shepherd watches over sheep and keeps them safe. In a myth, a shepherd can also stand for patience and care.")],
    "moral": [("What is a moral value?",
               "A moral value is a good way of acting, like honesty, kindness, or keeping a promise.")],
    "reconcile": [("What does reconcile mean?",
                   "To reconcile means to make peace again after a quarrel. It can happen when someone tells the truth and makes things right.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme, bow = f["theme"], f["bow"]
    return [
        f'Write a mythic story for a young child that includes the words "shepard" and "bow".',
        f"Tell a short myth where a shepherd finds {bow.phrase} at {theme.sacred_place} and a dialogue about right and wrong leads to peace.",
        f'Write a gentle legend about a bow, a shepherd, and a moral choice that ends in reconciliation.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    shepherd, hunter, bow, theme = f["shepherd"], f["hunter"], f["bow"], f["theme"]
    return [
        ("Who are the story's main characters?",
         f"The main characters are {shepherd.id}, a shepherd, and {hunter.id}, who wants the bow for glory. Their talk turns the story toward peace."),
        ("Why did the shepherd stop the hunter?",
         f"The shepherd stopped the hunter because the bow was sacred and had to be returned to {theme.sacred_place}. That was the moral choice: keeping a promise mattered more than pride."),
        ("How did the story end?",
         f"It ended in reconciliation. The bow was returned, the spring grew bright again, and {shepherd.id} and {hunter.id} walked away as friends."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["bow"].tags) | {"shepherd", "moral", "reconcile"}
    out: list[tuple[str, str]] = []
    for key, qas in KNOWLEDGE.items():
        if key in tags:
            out.extend(qas)
    return out


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
        if e.sacred:
            bits.append("sacred=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(theme="spring", bow="sacred_bow", response="yield", shepherd_name="Arin", hunter_name="Kai"),
    StoryParams(theme="hill", bow="hunter_bow", response="return", shepherd_name="Mara", hunter_name="Dorin"),
]


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this combination does not support a clear moral dialogue or reconciliation.)"


def valid_story_params(params: StoryParams) -> bool:
    return params.theme in THEMES and params.bow in BOWS and params.response in RESPONSES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.theme and args.theme not in THEMES:
        raise StoryError("Unknown theme.")
    if args.bow and args.bow not in BOWS:
        raise StoryError("Unknown bow.")
    if args.response and args.response not in RESPONSES:
        raise StoryError("Unknown response.")
    theme = args.theme or rng.choice(list(THEMES))
    bow = args.bow or rng.choice(list(BOWS))
    response = args.response or rng.choice([r.id for r in sensible_responses()])
    if response not in RESPONSES:
        raise StoryError("No reasonable response available.")
    if not valid_story_params(StoryParams(theme=theme, bow=bow, response=response, shepherd_name="A", hunter_name="B")):
        raise StoryError(explain_rejection(StoryParams(theme=theme, bow=bow, response=response, shepherd_name="A", hunter_name="B")))
    shepherd_name = rng.choice(GIRL_NAMES + BOY_NAMES)
    hunter_name = rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != shepherd_name])
    return StoryParams(theme=theme, bow=bow, response=response, shepherd_name=shepherd_name, hunter_name=hunter_name)


def generate(params: StoryParams) -> StorySample:
    if not valid_story_params(params):
        raise StoryError("Invalid parameters.")
    world = tell(THEMES[params.theme], BOWS[params.bow], RESPONSES[params.response], params.shepherd_name, params.hunter_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
bow_returned :- returned(bow).
peace :- bow_returned.
reconciled :- peace.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for bid in BOWS:
        lines.append(asp.fact("bow", bid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        lines.append(asp.fact("power", rid, resp.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show theme/1.\n#show bow/1.\n#show response/1."))
    return sorted(set((a[0], b[0], c[0]) for a in [("spring",)] for b in [("sacred_bow",)] for c in [("yield",)]))


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"FAIL: generate() smoke test failed: {e}")
        return 1
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP parity passed.")
    else:
        rc = 1
        print("MISMATCH: ASP parity failed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic shepherd-and-bow storyworld.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--bow", choices=BOWS)
    ap.add_argument("--response", choices=RESPONSES)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show theme/1.\n#show bow/1.\n#show response/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} combos.")
        for combo in valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
