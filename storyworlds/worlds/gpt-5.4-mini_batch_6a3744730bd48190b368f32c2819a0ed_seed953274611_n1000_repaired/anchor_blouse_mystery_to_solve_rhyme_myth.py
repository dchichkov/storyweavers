#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/anchor_blouse_mystery_to_solve_rhyme_myth.py
=============================================================================

A standalone storyworld about a small mythic mystery: a village keeps losing a
ceremonial anchor, a child notices clues around a blouse, and the truth is solved
with a rhyming, child-facing reveal.

The domain is intentionally tiny and state-driven:
- typed entities carry physical meters and emotional memes,
- a forward rule engine makes clues matter,
- the story contains a mystery to solve and ends with a proof image of what
  changed,
- the prose leans mythic, but stays concrete and gentle.

Run it
------
    python anchor_blouse_mystery_to_solve_rhyme_myth.py
    python anchor_blouse_mystery_to_solve_rhyme_myth.py --qa
    python anchor_blouse_mystery_to_solve_rhyme_myth.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    name: str
    mystery: str
    rhyme_cue: str
    anchor_spot: str
    hidden_spot: str
    rescue_image: str
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
class ObjectThing:
    id: str
    label: str
    phrase: str
    tag: str
    clue_word: str
    can_hide: bool = False
    can_tug: bool = False
    can_show: bool = False
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
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


def _r_find_clue(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.role != "clue" or ent.meters["noticed"] < THRESHOLD:
            continue
        sig = ("noticed", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("child").memes["curiosity"] += 1
        out.append(f"{world.get('child').id} felt the clue tug at {ent.label}.")
    return out


def _r_solve(world: World) -> list[str]:
    out = []
    if world.get("child").memes["curiosity"] < THRESHOLD:
        return out
    if world.get("breeze").meters["pull"] < THRESHOLD:
        return out
    sig = ("solve",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("anchor").meters["found"] = 1
    world.get("blouse").meters["revealed"] = 1
    world.get("mystery").meters["solved"] = 1
    out.append("__solve__")
    return out


CAUSAL_RULES = [Rule("find_clue", _r_find_clue), Rule("solve", _r_solve)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b}"


def no_story_reason() -> str:
    return "(No story: this world needs both the anchor mystery and the blouse clue.)"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for mystery_id, mystery in MYSTERIES.items():
            for blouse_id, blouse in BLOUSES.items():
                if mystery.anchor and blouse.can_show:
                    combos.append((place_id, mystery_id, blouse_id))
    return combos


@dataclass
class StoryParams:
    place: str
    mystery: str
    blouse: str
    child_name: str
    child_gender: str
    keeper_name: str
    keeper_gender: str
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
    "harbor": Place(
        id="harbor",
        name="the harbor",
        mystery="the old anchor had vanished from the shrine",
        rhyme_cue="salt and light",
        anchor_spot="the stone shrine by the water",
        hidden_spot="a reed basket beneath the pier",
        rescue_image="the anchor resting once more beside the tide",
    ),
    "grove": Place(
        id="grove",
        name="the moonlit grove",
        mystery="the anchor had gone missing from the moonwell",
        rhyme_cue="leaf and stone",
        anchor_spot="the moonwell ring",
        hidden_spot="a hollow log under fern roots",
        rescue_image="the anchor shining by the silver pool",
    ),
    "hill": Place(
        id="hill",
        name="the windy hill",
        mystery="the anchor had slipped away from the watch-stone",
        rhyme_cue="wind and song",
        anchor_spot="the watch-stone at the ridge",
        hidden_spot="a cloak chest in the shepherd hut",
        rescue_image="the anchor standing proud in the dawn",
    ),
}

MYSTERIES = {
    "missing_anchor": ObjectThing(
        id="missing_anchor",
        label="anchor",
        phrase="an ancient anchor",
        tag="anchor",
        clue_word="rhyme",
        can_hide=True,
        can_tug=True,
        can_show=True,
    ),
}

BLOUSES = {
    "blue_blouse": ObjectThing(
        id="blue_blouse",
        label="blouse",
        phrase="a blue blouse",
        tag="blouse",
        clue_word="thread",
        can_hide=True,
        can_tug=False,
        can_show=True,
    ),
    "white_blouse": ObjectThing(
        id="white_blouse",
        label="blouse",
        phrase="a white blouse",
        tag="blouse",
        clue_word="stitch",
        can_hide=True,
        can_tug=False,
        can_show=True,
    ),
}

CHILD_NAMES = ["Lina", "Mira", "Sana", "Kora", "Iris", "Nila"]
KEEPER_NAMES = ["Aunt Rowa", "Uncle Tane", "Grandma Iva", "Keeper Sol"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic mystery storyworld with rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--blouse", choices=BLOUSES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.blouse is None or c[2] == args.blouse)]
    if not combos:
        raise StoryError(no_story_reason())
    place, mystery, blouse = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    child_name = rng.choice(CHILD_NAMES)
    keeper_gender = rng.choice(["woman", "man"])
    keeper_name = rng.choice(KEEPER_NAMES)
    return StoryParams(
        place=place,
        mystery=mystery,
        blouse=blouse,
        child_name=child_name,
        child_gender=child_gender,
        keeper_name=keeper_name,
        keeper_gender=keeper_gender,
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.blouse not in BLOUSES:
        raise StoryError("Invalid story parameters.")
    world = World(PLACES[params.place])
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="solver"))
    keeper = world.add(Entity(id=params.keeper_name, kind="character", type=params.keeper_gender, role="keeper"))
    anchor = world.add(Entity(id="anchor", kind="thing", type="relic", label="anchor", role="relic"))
    blouse = world.add(Entity(id="blouse", kind="thing", type="garment", label="blouse", role="clue"))
    breeze = world.add(Entity(id="breeze", kind="thing", type="wind", label="breeze", role="cause"))
    mystery = world.add(Entity(id="mystery", kind="thing", type="mystery", label="mystery", role="mystery"))
    blouse.meters["noticed"] = 1
    breeze.meters["pull"] = 1
    child.memes["sadness"] += 1
    child.memes["wonder"] += 1

    world.say(
        f"In {world.place.name}, {world.place.mystery}. "
        f"{child.id} saw {world.place.anchor_spot} and asked, "
        f'"Why does the night keep its secret?"'
    )
    world.say(
        f"Near the water, {child.id} found {BLOUSES[params.blouse].phrase} snagged on a peg, "
        f"soft as cloud-rhyme."
    )
    world.para()
    world.say(
        f'{keeper.id} knelt by the shrine. "Listen, little seeker: when cloth is '
        f'left by the stones, it may sing of the one who moved them."'
    )
    child.memes["curiosity"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"{child.id} followed the blouse-thread to {world.place.hidden_spot}. "
        f"There, behind reed and root, the missing anchor waited."
    )
    world.say(
        f'"The anchor was not stolen by a shadow," {child.id} said. '
        f'"It was hidden, and the blouse was the clue."'
    )
    world.para()
    anchor.meters["found"] = 1
    blouse.meters["revealed"] = 1
    mystery.meters["solved"] = 1
    child.memes["joy"] += 1
    keeper.memes["relief"] += 1
    world.say(
        f'Together they carried the anchor back to {world.place.anchor_spot}. '
        f"The cloth fluttered, the rope sang, and the old mystery ended in a clear note."
    )
    world.say(
        f"At dusk, {world.place.rescue_image}. {child.id} and {keeper.id} smiled "
        f"like two lanterns after rain."
    )
    world.facts.update(
        place=params.place,
        mystery=params.mystery,
        blouse=params.blouse,
        child=child,
        keeper=keeper,
        anchor=anchor,
        blouse_ent=blouse,
        breeze=breeze,
        outcome="solved",
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a myth-like mystery for a young child in which an anchor goes missing and a blouse helps solve the riddle.",
        f"Tell a gentle rhyme story set at {world.place.name} where a child follows a blouse clue to find the anchor.",
        "Make the ending peaceful, with the missing thing returned and the mystery explained in a simple rhyme.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    keeper = f["keeper"]
    place = world.place
    return [
        ("What was the mystery?",
         f"The mystery was that the anchor had gone missing from {place.anchor_spot}. "
         f"The story begins with that loss and keeps asking where it went."),
        ("What clue helped solve it?",
         f"The blouse was the clue. It had been left near the water, and that small cloth trail led them to the hidden place."),
        ("How did they solve the mystery?",
         f"{child.id} followed the blouse-thread to {place.hidden_spot}, where the anchor was waiting. "
         f"Then {child.id} and {keeper.id} carried it back together."),
        ("How did the story end?",
         f"It ended with the anchor back at {place.anchor_spot}, calm and safe. "
         f"The place looked whole again, so the mystery was solved."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an anchor?",
         "An anchor is a heavy object that helps a boat or a special place stay steady. "
         "In a story, it can also be an important old thing to protect."),
        ("What is a blouse?",
         "A blouse is a kind of shirt, usually soft and light. "
         "It can flutter in the wind and leave a clear clue behind."),
        ("What does it mean to solve a mystery?",
         "It means finding the answer to a puzzling question. "
         "You look for clues until the hidden truth becomes clear."),
        ("What is a rhyme?",
         "A rhyme is when words sound alike at the end, like light and night. "
         "Rhymes can make a story feel musical and memorable."),
    ]


def valid_story_reason() -> str:
    return "(No story: this world always needs a clue that can reveal the anchor.)"


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
        lines.append(asp.fact("anchor", m))
    for b in BLOUSES:
        lines.append(asp.fact("blouse", b))
        lines.append(asp.fact("can_show", b))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, M, B) :- place(P), mystery(M), blouse(B), anchor(M), can_show(B).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("Mismatch between ASP and Python valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: smoke test generate() produced a story.")
    except Exception as exc:
        rc = 1
        print(f"Smoke test failed: {exc}")
    return rc


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for row in valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(
            place=p, mystery=m, blouse=b,
            child_name="Lina", child_gender="girl",
            keeper_name="Keeper Sol", keeper_gender="woman",
        )) for p, m, b in valid_combos()]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
