#!/usr/bin/env python3
"""
storyworlds/worlds/berry_drip_flashback_curiosity_detective_story.py
====================================================================

A small detective-story world about a curious child detective, a berry drip,
and a flashback that reveals the real clue.

Premise:
- A child notices a berry drip in an unexpected place.
- Curiosity pushes them to investigate like a little detective.
- A flashback reveals where the berry stain came from.
- The ending resolves the mystery with a concrete, state-driven reveal.

The world is intentionally tiny and constraint-checked:
- Only a handful of entities exist.
- The mystery is only generated when the clue chain is reasonable.
- The resolution is driven by simulated state, not a static template swap.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    carried_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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


@dataclass
class Setting:
    place: str
    indoor: bool = False
    supports_flashback: bool = True


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    location: str
    implies: str


@dataclass
class StoryParams:
    place: str
    detective_name: str
    detective_type: str
    parent_type: str
    berry_item: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _flashback_clue(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    berry = world.get("berry_item")
    if detective.memes.get("flashback", 0) < THRESHOLD:
        return out
    if detective.memes.get("curiosity", 0) < THRESHOLD:
        return out
    sig = ("flashback",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    berry.hidden = False
    clue = world.facts.get("flashback_clue")
    if clue:
        out.append(
            f"Then the detective remembered a tiny flashback: {clue}. "
            f"The memory fit the drip like a key in a lock."
        )
    return out


def _reveal_truth(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    berry = world.get("berry_item")
    kitchen = world.get("kitchen")
    if not berry.hidden:
        sig = ("reveal",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        detective.memes["confidence"] = detective.memes.get("confidence", 0) + 1
        out.append(
            f"The clue led the detective back to {kitchen.label}, where the berry "
            f"stain had really started."
        )
        out.append(
            f"In the end, the mystery was simple: {berry.phrase} had dripped from "
            f"{world.facts['source_phrase']}, and the trail had only looked spooky at first."
        )
    return out


CAUSAL_RULES = [_flashback_clue, _reveal_truth]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def simulate_investigation(world: World) -> None:
    detective = world.get("detective")
    berry = world.get("berry_item")
    source = world.get("source")
    detective.memes["curiosity"] += 1
    world.say(
        f"{detective.id} was a little detective who noticed every odd thing in {world.setting.place}."
    )
    world.say(
        f"One afternoon, {detective.pronoun().capitalize()} spotted a berry drip on the floor."
    )
    world.say(
        f"{detective.pronoun().capitalize()} leaned closer, because curiosity made the stain feel like a clue."
    )
    detective.memes["flashback"] += 1
    world.say(
        f"That made {detective.pronoun('object')} pause and think back to an earlier moment."
    )
    propagate(world, narrate=True)
    world.para()
    if source.location == "basket":
        world.say(
            f"At last, {detective.id} checked the basket and found the berries had tipped there first."
        )
    else:
        world.say(
            f"At last, {detective.id} checked the counter and found the berries had been left near the edge."
        )
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"{detective.id} smiled, because the drip was not a scary mess after all; it was just a clue that told the truth."
    )


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, supports_flashback=True),
    "porch": Setting(place="the porch", indoor=False, supports_flashback=True),
    "hallway": Setting(place="the hallway", indoor=True, supports_flashback=True),
}

DETECTIVE_NAMES = ["Maya", "Noah", "Lena", "Theo", "Iris", "Ben"]
BERRY_ITEMS = {
    "jam": Clue(id="jam", label="jam jar", phrase="the jam jar", location="counter", implies="a berry drip from the jam jar"),
    "basket": Clue(id="basket", label="berry basket", phrase="the berry basket", location="basket", implies="a berry drip from the berry basket"),
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for item in BERRY_ITEMS:
            combos.append((place, item))
    return combos


def explain_rejection(place: str, berry_item: str) -> str:
    return f"(No story: the requested place and berry source do not make a clean detective clue.)"


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=params.detective_type,
        label=params.detective_name,
        meters={"distance": 0.0},
        memes={"curiosity": 1.0, "flashback": 0.0, "confidence": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent_type,
        label="the parent",
        meters={"distance": 0.0},
        memes={"worry": 0.0},
    ))
    berry = world.add(Entity(
        id="berry_item",
        kind="thing",
        type="berries",
        label="berry drizzle",
        phrase="the berry drizzle",
        owner=detective.id,
        caretaker=parent.id,
        location="floor",
        meters={"drip": 1.0},
        memes={"mystery": 1.0},
    ))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type="container",
        label=BERRY_ITEMS[params.berry_item].label,
        phrase=BERRY_ITEMS[params.berry_item].phrase,
        location=BERRY_ITEMS[params.berry_item].location,
    ))
    kitchen = world.add(Entity(
        id="kitchen",
        kind="thing",
        type="room",
        label="the kitchen",
        location=params.place,
    ))

    world.facts.update(
        detective=detective,
        parent=parent,
        berry_item=berry,
        source=source,
        kitchen=kitchen,
        flashback_clue=f"the berries had slid from {source.phrase} onto the floor",
        source_phrase=source.phrase,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a child that includes the words "berry" and "drip".',
        f"Tell a gentle mystery about {f['detective'].label} the detective, who follows a berry drip and has a flashback.",
        f"Write a simple story where curiosity leads to a clue, and the berry drip is explained at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.get("detective")
    b = world.get("berry_item")
    src = world.get("source")
    return [
        QAItem(
            question=f"Who noticed the berry drip first?",
            answer=f"{d.label} noticed the berry drip first because {d.pronoun('subject')} was curious and looked closely.",
        ),
        QAItem(
            question=f"What did the detective remember in the flashback?",
            answer=f"The detective remembered that {src.phrase} had tipped and made the drip.",
        ),
        QAItem(
            question=f"What was the berry drip really from?",
            answer=f"It was really from {src.phrase}, not from a mystery thief.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened earlier, so a character can remember an important clue.",
        ),
        QAItem(
            question="Why is curiosity useful in a mystery?",
            answer="Curiosity helps a detective keep looking, ask questions, and notice small clues that explain what happened.",
        ),
        QAItem(
            question="What does a drip mean?",
            answer="A drip is a small drop of liquid falling or hanging from something.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id}: ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.berry_item and args.berry_item not in BERRY_ITEMS:
        raise StoryError("Unknown berry source.")

    place = args.place or rng.choice(list(SETTINGS))
    berry_item = args.berry_item or rng.choice(list(BERRY_ITEMS))
    name = args.name or rng.choice(DETECTIVE_NAMES)
    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    parent_type = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        detective_name=name,
        detective_type=detective_type,
        parent_type=parent_type,
        berry_item=berry_item,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate_investigation(world)
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


ASP_RULES = r"""
% A berry drip is visible when curiosity and a flashback both happen.
visible_drip(D) :- detective(D), curious(D), flashback(D).

% The story is valid if the setting supports a clue, the detective gets curious,
% and the berry source makes sense for a drip.
valid_story(P, B) :- setting(P), source(B), clue_chain(P, B).
clue_chain(P, B) :- setting(P), source(B), berry_source(B), place_supports_flashback(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        if setting.supports_flashback:
            lines.append(asp.fact("place_supports_flashback", pid))
    for bid in BERRY_ITEMS:
        lines.append(asp.fact("source", bid))
        lines.append(asp.fact("berry_source", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world about berry drips and flashbacks.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--berry-item", choices=list(BERRY_ITEMS))
    ap.add_argument("--name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place, berry_item in valid_combos():
            params = StoryParams(
                place=place,
                detective_name=DETECTIVE_NAMES[0],
                detective_type="girl",
                parent_type="mother",
                berry_item=berry_item,
                seed=base_seed,
            )
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
