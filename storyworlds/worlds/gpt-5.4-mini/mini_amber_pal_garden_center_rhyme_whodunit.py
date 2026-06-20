#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mini_amber_pal_garden_center_rhyme_whodunit.py
===============================================================================

A small storyworld for a garden-center whodunit with rhyme.

Premise:
- Three child-sized friends, Mini, Amber, and Pal, visit a garden center.
- A tiny mystery appears: who moved the seed tray, and why is the rhyming sign
  all jumbled?
- The story uses a simulated world with meters (physical state) and memes
  (emotional state), not just a template swap.
- The ending proves the change: the missing item is found, the real culprit is
  identified, and the garden center feels orderly again.

The style aims at a child-facing whodunit: clues, suspicion, a calm reveal, and
a tidy ending image. Rhyme is baked into the prose with short paired lines.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/mini_amber_pal_garden_center_rhyme_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/mini_amber_pal_garden_center_rhyme_whodunit.py --qa
    python storyworlds/worlds/gpt-5.4-mini/mini_amber_pal_garden_center_rhyme_whodunit.py --verify
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
    kind: str = "thing"  # "character" | "thing"
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class GardenCenter:
    name: str
    rows: list[str]
    smells: list[str]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Clue:
    id: str
    label: str
    location: str
    tidy: bool = True
    moveable: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Suspect:
    id: str
    label: str
    habit: str
    likely: int
    actual: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, place: GardenCenter) -> None:
        self.place = place
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_spread_mess(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["mess"] < THRESHOLD:
            continue
        sig = ("mess", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("center").meters["disorder"] += 1
        out.append("__mess__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.get("Mini").memes["curious"] >= THRESHOLD and world.get("Amber").memes["uncertain"] >= THRESHOLD:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("Mini").memes["worry"] += 1
            world.get("Amber").memes["worry"] += 1
            out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("mess", _r_spread_mess), Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(x for x in lines if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def clue_at_risk(clue: Clue) -> bool:
    return clue.moveable and not clue.tidy


def suspect_who(motive: str, suspects: list[Suspect]) -> Suspect:
    for s in suspects:
        if s.habit == motive:
            return s
    return max(suspects, key=lambda s: s.likely)


def set_scene(world: World, mini: Entity, amber: Entity, pal: Entity, clue: Clue) -> None:
    mini.memes["curious"] += 1
    amber.memes["calm"] += 1
    pal.memes["careful"] += 1
    world.say(
        f"At the garden center, rows of basil, beans, and bright blooms stood in line. "
        f"Mini, Amber, and Pal walked slow, so no one would rile the soil."
    )
    world.say(
        f"Mini hummed, Amber smiled, and Pal kept pace through the sweet green smell. "
        f"Then a tiny sign went missing from the herb shelf, and the whole place lost its spell."
    )
    world.say(
        f"On the floor by the seed table sat a mini tray of amber pebbles, neat as a nap. "
        f"Pal tapped the shelf and said, \"Who moved the sign?\" - the first small clue in the map."
    )


def search(world: World, mini: Entity, amber: Entity, pal: Entity, clue: Clue) -> None:
    world.say(
        f"\"Who did it?\" Mini asked. \"Was it a prank, a flop, or a sneaky little hop?\" "
        f"Amber knelt and checked the labels; Pal looked high, then low, then top to top."
    )
    mini.memes["suspicion"] += 1
    amber.memes["suspicion"] += 1
    pal.memes["suspicion"] += 1
    world.say(
        f"The clue was simple: the sign was gone, but the watering can was still there in place. "
        f"That meant the thief had not come for plants, only for a rhyme and a face."
    )


def reveal(world: World, mini: Entity, amber: Entity, pal: Entity, suspect: Suspect, clue: Clue) -> None:
    world.say(
        f"Amber pointed at a trail of soil on the cart. \"A clue!\" she said with a grin. "
        f"\"The helper in the green apron borrowed the sign to fix the rhyme on the bin.\""
    )
    world.say(
        f"The real culprit was not a crook at all: it was the breeze, so light and sly. "
        f"It nudged the sign from a clip, and the clerk had carried it off to keep it high."
    )
    if suspect.actual:
        world.say(
            f"Mini blinked. \"So nobody meant to make a mess?\" Pal said, \"That seems true.\" "
            f"Amber nodded. \"The center just needed a better clip, and a calmer place for the sign to chew.\""
        )
    mini.memes["relief"] += 1
    amber.memes["relief"] += 1
    pal.memes["relief"] += 1
    world.get("center").meters["disorder"] = 0.0
    clue.tidy = True


def ending(world: World) -> None:
    world.say(
        f"Then the clerk pinned the rhyme sign back up, straight and bright in the sun. "
        f"\"Mini seed packets here,\" it read, and the little mystery was done."
    )
    world.say(
        f"Mini, Amber, and Pal laughed soft, and walked on by the thyme and mint. "
        f"The garden center looked neat again, with every label in the right tint."
    )


def tell(center: GardenCenter, clue: Clue, suspects: list[Suspect]) -> World:
    world = World(center)
    mini = world.add(Entity("Mini", kind="character", type="girl", role="sleuth"))
    amber = world.add(Entity("Amber", kind="character", type="girl", role="sleuth"))
    pal = world.add(Entity("Pal", kind="character", type="boy", role="helper"))
    world.add(Entity("center", type="place", label=center.name))
    world.add(Entity("sign", type="thing", label="rhyming sign"))
    world.add(Entity("tray", type="thing", label=clue.label))
    world.facts["clue"] = clue
    world.facts["suspects"] = suspects

    set_scene(world, mini, amber, pal, clue)
    world.para()
    search(world, mini, amber, pal, clue)
    world.para()
    suspect = suspect_who("careful", suspects)
    reveal(world, mini, amber, pal, suspect, clue)
    world.para()
    ending(world)

    world.facts.update(
        mini=mini,
        amber=amber,
        pal=pal,
        outcome="solved",
        clue_moved=clue.moveable,
        center=center,
    )
    return world


CENTER = GardenCenter(
    name="the garden center",
    rows=["basil", "beans", "bright blooms", "thyme", "mint"],
    smells=["soil", "rain", "fresh leaves"],
)

CLUES = {
    "amber_pebbles": Clue("amber_pebbles", "a mini tray of amber pebbles", "seed table", tidy=False, moveable=True),
    "lost_sign": Clue("lost_sign", "a rhyming sign", "herb shelf", tidy=False, moveable=True),
}

SUSPECTS = {
    "breeze": Suspect("breeze", "the breeze", "careful", 5, actual=True),
    "clerk": Suspect("clerk", "the clerk", "tidy", 7, actual=False),
    "cat": Suspect("cat", "the shop cat", "curious", 3, actual=False),
}


@dataclass
@dataclass
class StoryParams:
    clue: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Garden-center whodunit with rhyme.")
    ap.add_argument("--clue", choices=CLUES)
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
    clue = args.clue or rng.choice(sorted(CLUES))
    return StoryParams(clue=clue)


def generation_prompts(world: World) -> list[str]:
    clue = world.facts["clue"]
    return [
        f'Write a rhyme-filled whodunit set in a garden center that includes the words "mini", "amber", and "pal".',
        f"Tell a child-sized mystery story where Mini, Amber, and Pal notice {clue.label} has gone missing.",
        f'Write a gentle detective story in a garden center, with clues and a calm reveal, and keep the tone playful and rhyming.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    clue = world.facts["clue"]
    return [
        ("Who are the story's helpers?", "Mini, Amber, and Pal are the three friends who look for the clue together."),
        ("What went missing?", f"{clue.label.capitalize()} went missing from the garden center shelf, which made the friends start their little whodunit."),
        ("How did the mystery end?", "They found out it was not a bad trick at all, and the sign was put back neatly so the garden center looked calm again."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a garden center?", "A garden center is a place where people buy plants, seeds, pots, soil, and tools for gardens."),
        QAItem("Why do people label plants?", "People label plants so shoppers can tell which seeds or flowers they are picking up."),
        QAItem("What is a clue in a mystery?", "A clue is a small piece of information that helps you figure out what happened."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== Story Q&A ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World Q&A ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str]]:
    return [(cid,) for cid in CLUES]


ASP_RULES = r"""
valid(C) :- clue(C).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("clue", cid) for cid in CLUES)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [StoryParams("amber_pebbles"), StoryParams("lost_sign")]


def asp_verify() -> int:
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP parity.")
        return 1
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as exc:  # pragma: no cover - smoke check
        print(f"SMOKE FAIL: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(CENTER, CLUES[params.clue], list(SUSPECTS.values()))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
