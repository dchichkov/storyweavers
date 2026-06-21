#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/microscopic_lesson_learned_twist_repetition_heartwarming.py
===========================================================================================

A tiny heartwarming storyworld about a child who tries to find a microscopic
thing, discovers a surprising twist, repeats the search with better care, and
learns a gentle lesson.

The world is deliberately small:
- one child
- one helper or grown-up
- one tiny object
- one tool for seeing tiny things
- one place that can hold the tiny object

The story engine is state-driven: feelings and physical conditions change over
time, and the ending proves what changed.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Place:
    id: str
    label: str
    tiny_hides: str
    surface: str
    can_shelter: bool = True
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
class TinyThing:
    id: str
    label: str
    phrase: str
    place_ok: set[str]
    visible_when: str
    important: str
    lost_text: str
    found_text: str
    tiny: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    sparkle: str
    tiny_view: bool = True
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
        self.scene: dict[str, str] = {}

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
        clone.scene = dict(self.scene)
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


def _r_notice(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    item = world.get("item")
    if child.memes["curiosity"] >= THRESHOLD and item.meters["hidden"] >= THRESHOLD:
        sig = ("notice",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["wonder"] += 1
            out.append("__notice__")
    return out


def _r_tiny_found(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    item = world.get("item")
    if child.meters["seen_with_magnifier"] >= THRESHOLD and item.meters["hidden"] < THRESHOLD:
        sig = ("found",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["found"] += 1
            out.append("__found__")
    return out


def _r_heart(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["worry"] >= THRESHOLD and helper.memes["kindness"] >= THRESHOLD:
        sig = ("heart",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["calm"] += 1
            helper.memes["pride"] += 1
            out.append("__heart__")
    return out


CAUSAL_RULES = [
    Rule("notice", "mind", _r_notice),
    Rule("tiny_found", "physical", _r_tiny_found),
    Rule("heart", "social", _r_heart),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def with_magnifier(world: World, child: Entity, tool: Tool) -> None:
    child.meters["seen_with_magnifier"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} held up {tool.phrase} and peered through it. "
        f"{tool.sparkle}"
    )


def search(world: World, child: Entity, item: TinyThing, place: Place, repeated: bool = False) -> None:
    child.memes["curiosity"] += 1
    if repeated:
        world.say(
            f"{child.id} searched {place.label} again, this time more slowly. "
            f"{item.lost_text}"
        )
    else:
        world.say(
            f"{child.id} searched {place.label} for {item.phrase}. "
            f"{item.lost_text}"
        )


def twist(world: World, helper: Entity, child: Entity, item: TinyThing) -> None:
    helper.memes["kindness"] += 1
    child.meters["found"] += 0
    world.say(
        f"Then came the twist: {helper.id} smiled and pointed to a tiny trail. "
        f"{item.important}"
    )


def reveal(world: World, child: Entity, item: TinyThing, place: Place) -> None:
    item.meters["hidden"] = 0
    child.meters["found"] += 1
    child.memes["joy"] += 1
    world.say(
        f"There, tucked in {place.tiny_hides}, was {item.phrase}. "
        f"{item.found_text}"
    )


def lesson(world: World, child: Entity, helper: Entity, item: TinyThing) -> None:
    child.memes["lesson"] += 1
    child.memes["love"] += 1
    helper.memes["love"] += 1
    world.say(
        f"{helper.id} laughed softly and said, "
        f'"Sometimes the smallest things are found when we slow down and look twice."'
    )
    world.say(
        f"{child.id} nodded, hugging {item.label}. "
        f"{item.label_word if hasattr(item, 'label_word') else ''}".strip()
    )
    world.say(
        f"And after that, {child.id} kept the tiny thing safe in a little box, "
        f"smiling at how a microscopic search could lead to such a warm surprise."
    )


def tell(place: Place, item: TinyThing, tool: Tool, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str, helper_role: str = "mom") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role=helper_role))
    child.memes["curiosity"] = 1
    child.memes["worry"] = 0
    helper.memes["kindness"] = 1
    item_ent = world.add(Entity(id="item", kind="thing", type="thing", label=item.label))
    world.scene = {"place": place.id, "item": item.id, "tool": tool.id}
    item_ent.meters["hidden"] = 1

    world.say(
        f"On a quiet afternoon, {child.id} and {helper.id} went to {place.label}. "
        f"{child.id} wanted to find {item.phrase}."
    )
    world.say(
        f"{child.id} loved the mysterious, microscopic feeling of looking for tiny things. "
        f"{place.surface.capitalize()} seemed full of little secrets."
    )

    world.para()
    search(world, child, item, place)
    with_magnifier(world, child, tool)
    propagate(world, narrate=False)

    world.para()
    twist(world, helper, child, item)
    world.say(
        f"{helper.id} showed {child.pronoun('object')} that the clue had been there the whole time, "
        f"just hidden in a place only a careful eye could notice."
    )
    search(world, child, item, place, repeated=True)
    reveal(world, child, item, place)
    lesson(world, child, helper, item)

    world.facts.update(
        child=child,
        helper=helper,
        item=item,
        place=place,
        tool=tool,
        repeated=True,
        found=True,
    )
    return world


PLACES = {
    "garden": Place(
        id="garden",
        label="the garden",
        tiny_hides="the seam between two stones",
        surface="the garden path glittered with dew",
        can_shelter=True,
    ),
    "kitchen": Place(
        id="kitchen",
        label="the kitchen table",
        tiny_hides="the edge of a sugar bowl",
        surface="the table was warm and bright",
        can_shelter=True,
    ),
    "porch": Place(
        id="porch",
        label="the porch",
        tiny_hides="the crack beside a flowerpot",
        surface="the porch boards were painted blue",
        can_shelter=True,
    ),
}

TINY_THINGS = {
    "button": TinyThing(
        id="button",
        label="a button",
        phrase="a tiny button",
        place_ok={"garden", "kitchen", "porch"},
        visible_when="the light was close",
        important="It matched the missing button on the coat.",
        lost_text="At first, the button seemed impossible to see.",
        found_text="It was so small that it looked like a shiny bead.",
    ),
    "bee_charm": TinyThing(
        id="bee_charm",
        label="a bee charm",
        phrase="a microscopic bee charm",
        place_ok={"garden", "porch"},
        visible_when="someone looked carefully",
        important="It had fallen from a bracelet and glinted like a star.",
        lost_text="At first, the charm was no bigger than a crumb.",
        found_text="It blinked gold in the light and looked very happy to be found.",
    ),
    "shell": TinyThing(
        id="shell",
        label="a shell",
        phrase="a microscopic shell",
        place_ok={"garden", "porch", "kitchen"},
        visible_when="the magnifier turned the light into a circle",
        important="It was a tiny treasure from a pocket full of sand.",
        lost_text="At first, the shell hid among the bright specks.",
        found_text="It shone softly, as if it had been waiting for a friend.",
    ),
}

TOOLS = {
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        phrase="a magnifying glass",
        helps="helps people see tiny things",
        sparkle="The glass made everything seem a little larger and much more interesting.",
        tiny_view=True,
    ),
    "lantern": Tool(
        id="lantern",
        label="little lamp",
        phrase="a little lamp",
        helps="lights up tiny spaces",
        sparkle="The lamp made a warm circle of light on the floor.",
        tiny_view=True,
    ),
}

CHILD_NAMES = ["Mia", "Lily", "Noah", "Ava", "Eli", "Zoe"]
HELPERS = ["Mom", "Dad", "Nia", "Leo", "Aunt May", "Uncle Ben"]


@dataclass
class StoryParams:
    place: str
    item: str
    tool: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    helper_role: str = "mom"
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for i, item in TINY_THINGS.items():
            if p in item.place_ok:
                for t in TOOLS:
                    combos.append((p, i, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny heartwarming microscopic storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=TINY_THINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy", "mother", "father", "woman", "man"])
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
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, tool = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice(HELPERS)
    return StoryParams(
        place=place,
        item=item,
        tool=tool,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_role=helper_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story that includes the word "microscopic" and a gentle surprise about {f["item_cfg"].phrase}.',
        f"Tell a child-friendly story where {f['child'].id} looks for {f['item_cfg'].phrase}, repeats the search more carefully, and learns a lesson.",
        f"Write a warm little story about a tiny search in {f['place'].label} with a twist and a kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    item: TinyThing = f["item_cfg"]
    place: Place = f["place"]
    qa = [
        QAItem(
            question=f"What was {child.id} trying to find?",
            answer=f"{child.id} was trying to find {item.phrase} in {place.label}. It seemed tiny, but it mattered a lot to the story."
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {helper.id} already knew where to look. {helper.id} noticed a tiny clue, so the search became a kind teamwork moment."
        ),
        QAItem(
            question="What did the child learn?",
            answer=f"{child.id} learned to slow down, look carefully, and try again. That second try is what led to the happy ending."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does microscopic mean?",
            answer="Microscopic means so tiny that you may need special help to see it clearly."
        ),
        QAItem(
            question="What does a magnifying glass do?",
            answer="A magnifying glass helps make small things easier to see. It can turn a tiny speck into something you can notice."
        ),
        QAItem(
            question="Why is it nice to look again when you miss something small?",
            answer="Looking again can help you notice details you skipped the first time. A careful second look can solve a tiny mystery."
        ),
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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, item in TINY_THINGS.items():
        lines.append(asp.fact("thing", iid))
        lines.append(asp.fact("tiny", iid))
        for p in sorted(item.place_ok):
            lines.append(asp.fact("ok_in", iid, p))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, I, T) :- place(P), thing(I), tool(T), ok_in(I, P).
"""

def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
        print("python only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams(
        place="garden",
        item="bee_charm",
        tool="magnifier",
        child_name="Mia",
        child_gender="girl",
        helper_name="Mom",
        helper_gender="mother",
        helper_role="mother",
    ),
    StoryParams(
        place="kitchen",
        item="button",
        tool="lantern",
        child_name="Noah",
        child_gender="boy",
        helper_name="Dad",
        helper_gender="father",
        helper_role="father",
    ),
    StoryParams(
        place="porch",
        item="shell",
        tool="magnifier",
        child_name="Ava",
        child_gender="girl",
        helper_name="Aunt May",
        helper_gender="woman",
        helper_role="woman",
    ),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.item not in TINY_THINGS:
        raise StoryError(f"Unknown item: {params.item}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")
    place = PLACES[params.place]
    item_cfg = TINY_THINGS[params.item]
    tool = TOOLS[params.tool]
    if params.place not in item_cfg.place_ok:
        raise StoryError("That tiny thing would not naturally be found in that place.")
    world = tell(
        place=place,
        item=item_cfg,
        tool=tool,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        helper_role=params.helper_role,
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, i, t in combos:
            print(f"  {p:8} {i:12} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
