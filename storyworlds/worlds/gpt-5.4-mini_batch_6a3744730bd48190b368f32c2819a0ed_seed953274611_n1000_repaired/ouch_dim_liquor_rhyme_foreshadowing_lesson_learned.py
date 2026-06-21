#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ouch_dim_liquor_rhyme_foreshadowing_lesson_learned.py
======================================================================================

A standalone storyworld about an animal finding a shiny bottle in a dim place,
hearing a foreshadowed warning, choosing a safe path, and learning a lesson.

The world keeps the prose small and state-driven:
- typed animals and objects
- physical meters and emotional memes
- a forward-chaining rule engine
- a reasonableness gate
- an inline ASP twin for parity checks

The story includes the seed words "ouch-dim" and "liquor" and is written in an
animal-story style with rhyme, foreshadowing, and a lesson learned.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
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
    safe: bool = False
    forbidden: bool = False
    dimming: bool = False
    gives_light: bool = False
    liquid: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "duck"}
        male = {"boy", "father", "dad", "man", "fox", "wolf", "bear", "lion"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
class Place:
    id: str
    label: str
    dimness: int
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
    safe_alternative: str = ""
    forbidden: bool = False
    liquid: bool = False
    gives_light: bool = False
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
class Reaction:
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    creature: str
    warning: str
    item: str
    response: str
    helper: str
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


PLACES = {
    "barn": Place("barn", "a barn", 3, tags={"dim", "barn"}),
    "shed": Place("shed", "a dim shed", 4, tags={"dim", "shed"}),
    "cave": Place("cave", "a little cave", 5, tags={"dim", "cave"}),
}

CREATURES = {
    "rabbit": {"type": "rabbit", "label": "rabbit", "name_pool": ["Rae", "Nib", "Pip"]},
    "fox": {"type": "fox", "label": "fox", "name_pool": ["Finn", "Puck", "Red"]},
    "bear": {"type": "bear", "label": "bear", "name_pool": ["Bruno", "Moss", "Hank"]},
}

WARNINGS = {
    "glow_sign": Item("glow_sign", "glow sign", "a glow sign that said ouch-dim", safe_alternative="lantern", gives_light=True, tags={"light"}),
    "liquor": Item("liquor", "liquor", "a bottle of liquor", forbidden=True, liquid=True, tags={"forbidden", "liquid"}),
}

SAFE_ITEMS = {
    "lantern": Item("lantern", "lantern", "a little lantern", gives_light=True, safe_alternative="lantern", tags={"light"}),
    "lamp": Item("lamp", "lamp", "a warm lamp", gives_light=True, safe_alternative="lamp", tags={"light"}),
}

RESPONSES = {
    "hide": Reaction("hide", 3, 2, "hid the bottle in straw and left it there", "tried to hide it, but the spill spread and the smell stayed", "hid the bottle safely", tags={"hide"}),
    "call": Reaction("call", 3, 4, "called a grown-up and kept everyone away", "called too late and could not stop the mess", "called a grown-up right away", tags={"call"}),
    "carry_out": Reaction("carry_out", 2, 3, "carried the bottle outside with a cloth wrapped around it", "carried it too clumsily and nearly dropped it", "carried the bottle outside carefully", tags={"carry"}),
}

NAME_POOL = ["Pip", "Rae", "Moss", "Finn", "Luna", "Toby", "Bram", "Nia"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for warning in WARNINGS:
            for item in WARNINGS:
                if warning == "glow_sign" and item == "liquor":
                    combos.append((place, warning, item))
    return combos


def _re_color(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def hazard_at_risk(place: Place, item: Item) -> bool:
    return place.dimness >= 3 and item.forbidden


def sensible_responses() -> list[Reaction]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def best_response() -> Reaction:
    return max(RESPONSES.values(), key=lambda r: r.power)


def can_contain(response: Reaction, place: Place) -> bool:
    return response.power >= place.dimness


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with rhyme, foreshadowing, and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--item", choices=WARNINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper")
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
    if args.item and args.item == "liquor" and args.warning and args.warning != "glow_sign":
        raise StoryError("The story needs a foreshadowing sign before the liquor appears.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.warning is None or c[1] == args.warning)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, warning, item = rng.choice(combos)
    creature = args.creature or rng.choice(list(CREATURES))
    response = args.response or rng.choice(list(RESPONSES))
    helper = args.helper or rng.choice(NAME_POOL)
    return StoryParams(place=place, creature=creature, warning=warning, item=item, response=response, helper=helper)


def tell(place: Place, creature_key: str, warning_key: str, item_key: str, response_key: str, helper: str) -> World:
    world = World()
    creature_cfg = CREATURES[creature_key]
    hero = world.add(Entity(id=helper, kind="character", type=creature_cfg["type"], label=creature_cfg["label"], role="hero"))
    friend = world.add(Entity(id=friendly_name(helper), kind="character", type="owl", label="owl", role="helper"))
    room = world.add(Entity(id="room", type="thing", label=place.label, dimming=True))
    warning = WARNINGS[warning_key]
    item = WARNINGS[item_key]
    safe = SAFE_ITEMS["lantern"]

    hero.memes["curiosity"] += 1
    friend.memes["care"] += 1

    world.say(
        f"In {place.label}, where the beams were low and the corners stayed a little hush, "
        f"{hero.id} found a clue that made the shadows grow."
    )
    world.say(
        f'There was a sign that whispered "ouch-dim", and beside it sat {item.phrase}. '
        f'The sign gave a foreshadowed hint: "When light looks slim, be slow and trim."'
    )
    world.para()
    world.say(
        f'{hero.id} leaned in and sniffed. "That bottle says liquor," {friend.id} warned. '
        f'"It is not for little paws, not for curious claws."'
    )
    hero.memes["temptation"] += 1
    response = RESPONSES[response_key]
    if can_contain(response, place):
        world.say(
            f'{hero.id} listened, and chose the safer scene. {friend.id} {response.text}.'
        )
        world.say(
            f"Then the two animals brought out {safe.phrase} so the dim place could gleam, "
            f"and the risky bottle was left alone like a bad dream."
        )
        hero.memes["lesson"] += 1
        friend.memes["relief"] += 1
        outcome = "contained"
    else:
        world.say(
            f'{hero.id} forgot the warning and reached too soon. {friend.id} {response.fail}.'
        )
        world.say(
            "The dim room smelled sharp and wrong, so the animals backed away and called for help."
        )
        hero.memes["lesson"] += 1
        outcome = "failed"
    world.facts.update(
        hero=hero,
        friend=friend,
        place=place,
        warning=warning,
        item=item,
        response=response,
        outcome=outcome,
        safe=safe,
    )
    return world


def friendly_name(helper: str) -> str:
    return "Owlie"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story that includes the words "ouch-dim" and "liquor" and ends with a lesson learned.',
        f"Tell a rhyming story where {f['hero'].id} is warned by an owl in a dim place and chooses the safe light instead of the liquor.",
        f"Write a foreshadowing animal story about a curious creature, a dim room, and a mistake that becomes a lesson.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, who meet in a dim place and face a risky bottle."),
        ("What warning did they see?",
         f"They saw a sign that said ouch-dim, which foreshadowed that the dark place was not safe for a curious animal."),
        ("What did the bottle contain?",
         f"The bottle was liquor. The owl warned that it was not for little paws, so the hero should stay away."),
    ]
    if f["outcome"] == "contained":
        qa.append((
            "What changed by the end?",
            f"{hero.id} listened and chose a safe light instead. The risky bottle was left alone, and the lesson learned made the ending feel bright."
        ))
    else:
        qa.append((
            "What happened when the warning was ignored?",
            f"{hero.id} reached too soon, and the grown-up help was needed. The dim place became a lesson about listening fast."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a lantern?",
         "A lantern is a light that can make a dim place brighter without a risky flame."),
        ("Why should animals stay away from liquor?",
         "Liquor is a grown-up drink, and children or animals should not touch it. It can be unsafe and is not a toy."),
        ("What does foreshadowing mean?",
         "Foreshadowing is a hint that tells you something important may happen soon."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mem = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={dict(m)}")
        if mem:
            bits.append(f"memes={dict(mem)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.dimming:
            bits.append("dimming=True")
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
valid(P,W,I) :- place(P), warning(W), item(I), W = glow_sign, I = liquor.
safe_choice(R) :- response(R), sense(R,S), S >= sense_min.
outcome(contained) :- safe_choice(R), response_power(R,P), place_dim(P1), P >= P1.
outcome(failed) :- not outcome(contained).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        lines.append(asp.fact("place_dim", p, PLACES[p].dimness))
    for w in WARNINGS:
        lines.append(asp.fact("warning", w))
    for i in WARNINGS:
        lines.append(asp.fact("item", i))
    for r in RESPONSES:
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, RESPONSES[r].sense))
        lines.append(asp.fact("response_power", r, RESPONSES[r].power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, creature=None, warning=None, item=None, response=None, helper=None), random.Random(0)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.creature not in CREATURES or params.warning not in WARNINGS or params.item not in WARNINGS or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    if params.warning != "glow_sign" or params.item != "liquor":
        raise StoryError("This world only supports the foreshadowing sign and the liquor bottle.")
    world = tell(PLACES[params.place], params.creature, params.warning, params.item, params.response, params.helper or "Pip")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        params_list = [
            StoryParams(place="barn", creature="rabbit", warning="glow_sign", item="liquor", response="call", helper="Pip"),
            StoryParams(place="shed", creature="fox", warning="glow_sign", item="liquor", response="carry_out", helper="Rae"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
