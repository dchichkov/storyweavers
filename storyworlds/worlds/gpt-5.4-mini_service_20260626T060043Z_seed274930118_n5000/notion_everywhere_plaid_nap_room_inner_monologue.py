#!/usr/bin/env python3
"""
storyworlds/worlds/notion_everywhere_plaid_nap_room_inner_monologue.py
======================================================================

A small storyworld in a nap room, told in a tall-tale voice.

Seed tale:
---
In a nap room that was quieter than a moonbeam, a little child named Pip got
a wild notion. The room had a plaid blanket, a soft cot, and a row of paper
stars on the wall. Pip was supposed to lie still and rest, but the notion kept
wandering everywhere.

Pip's curiosity was bigger than a teacup and louder than a cricket. While the
other children drifted toward sleep, Pip kept peeking, asking, and thinking in
a secret inner monologue: What is under the cot? Why does the plaid blanket
look like a map? Could a notion fit inside a pillow?

At last, Pip followed the curiosity too far, woke up the room, and made a bad
ending out of what might have been a nap. The blanket slipped, the lamp tilted,
and the quiet vanished like mist. Pip learned that some notions are best left
for after rest.

World model:
---
- A child in a nap room has a thought-nugget called a notion.
- The notion grows when curiosity rises and the room stays quiet.
- Inner monologue can intensify curiosity when the child starts wondering.
- A plaid blanket may comfort or distract.
- Too much curiosity in a nap room can spoil the nap and produce a bad ending.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

NARRATIVE_STYLE = "tall_tale"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the nap room"
    quiet: bool = True


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    caretaker_type: str
    blanket: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.trace = list(self.trace)
        clone.facts = copy.deepcopy(self.facts)
        return clone


THRESHOLD = 1.0


def _is_child(ent: Entity) -> bool:
    return ent.kind == "character"


def _rule_notion_spreads(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("notion_spread",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["notion"] += 1
    out.append("The notion kept bobbing up in the child's head like a cork on a creek.")
    return out


def _rule_inner_monologue_fuels_curiosity(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes["inner_monologue"] < THRESHOLD:
        return out
    sig = ("monologue_curiosity",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    out.append("The child's private thinking made the wondering grow longer and louder.")
    return out


def _rule_curiosity_wakes_room(world: World) -> list[str]:
    out = []
    child = world.get("child")
    caret = world.get("caretaker")
    blanket = world.get("blanket")
    if child.memes["curiosity"] < 2 or child.meters["notion"] < THRESHOLD:
        return out
    sig = ("wake_room",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["bad_end"] = True
    blanket.meters["slip"] += 1
    caret.memes["alarm"] += 1
    out.append("That curiosity woke the room, and the quiet flew off like a startled bird.")
    return out


def _rule_bad_ending(world: World) -> list[str]:
    out = []
    if not world.facts.get("bad_end"):
        return out
    sig = ("bad_ending",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The plaid blanket slid crooked, the lamp tipped, and the nap ended in a bad ending.")
    return out


CAUSAL_RULES = [_rule_inner_monologue_fuels_curiosity, _rule_notion_spreads, _rule_curiosity_wakes_room, _rule_bad_ending]


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


def _do_monologue(world: World, child: Entity) -> None:
    child.memes["inner_monologue"] += 1
    world.say(
        f'In {world.setting.place}, {child.id} began a secret inner monologue: '
        f'"What is under the cot? Why does the plaid blanket look like a map?"'
    )
    propagate(world)


def _do_curious_peek(world: World, child: Entity, blanket: Entity) -> None:
    child.memes["curiosity"] += 1
    child.meters["notion"] += 1
    world.say(
        f"{child.id} leaned toward the cot and peeped under the plaid blanket, "
        f"as if curiosity were a lantern in a thunderstorm."
    )
    if blanket.phrase:
        world.say(f"The {blanket.label} seemed to stretch everywhere in the child's imagination.")
    propagate(world)


def tell(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    caretaker = world.add(Entity(id="caretaker", kind="character", type=params.caretaker_type, label="the caretaker"))
    blanket = world.add(Entity(id="blanket", type="blanket", label="plaid blanket", phrase="a plaid blanket", caretaker="caretaker"))
    world.facts.update(child=child, caretaker=caretaker, blanket=blanket, params=params)

    world.say(
        f"In the nap room, {child.id} was a small {child.type} with a big talent for noticing things."
    )
    world.say(
        f"There was a plaid blanket, a low cot, and a hush so deep it seemed to have roots."
    )
    world.say(
        f"{child.id} loved the plaid blanket because it looked as if it had been sewn from little roads."
    )

    world.para()
    _do_monologue(world, child)
    _do_curious_peek(world, child, blanket)
    world.say(
        f"{child.id} kept thinking the notion might be hiding somewhere everywhere at once."
    )

    world.para()
    if world.facts.get("bad_end"):
        world.say(
            f"The caretaker hurried over, gathered the tilted blanket, and sighed at the trouble."
        )
        world.say(
            f"{child.id} had wanted a nap-room mystery, but curiosity had carried the day into a bad ending."
        )
    else:
        world.say(f"The room stayed quiet, and the child nearly drifted off.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        'Write a tall-tale bedtime story in a nap room about a child, a plaid blanket, and a notion that seems to be everywhere.',
        f"Tell a story where {child.id} has an inner monologue in the nap room, grows curious, and ends with a bad ending.",
        "Write a child-facing story about curiosity and a plaid blanket, with a dreamlike, tall-tale feeling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    blanket = f["blanket"]
    caretaker = f["caretaker"]
    bad = world.facts.get("bad_end", False)
    return [
        QAItem(
            question=f"What kind of room was the story set in?",
            answer=f"It was set in the nap room, where the air was meant to stay hushed and sleepy.",
        ),
        QAItem(
            question=f"What did {child.id} keep thinking about?",
            answer=f"{child.id} kept thinking about the plaid blanket and the little notion that seemed to be everywhere.",
        ),
        QAItem(
            question=f"Why did the story end badly?",
            answer=(
                f"It ended badly because curiosity grew too large, the plaid blanket slipped, "
                f"and the caretaker had to rush over and stop the nap from falling apart."
            ) if bad else f"It did not truly end badly in this version, though the room stayed very close to waking."
        ),
        QAItem(
            question=f"Who noticed the trouble at the end?",
            answer=f"The caretaker noticed the trouble and hurried in when the quiet broke.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to peek, ask, and find out what is hidden.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet thinking a person does inside their own head.",
        ),
        QAItem(
            question="What is a plaid blanket?",
            answer="A plaid blanket is a blanket with a pattern of crossing stripes or squares, often in bright colors.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:9} ({e.type}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


NAMES = ["Pip", "Milo", "June", "Nell", "Wren", "Otto", "Bess", "Finn"]
CHILD_TYPES = ["girl", "boy"]
CARETAKER_TYPES = ["mother", "father", "nurse", "caretaker"]
BLANKETS = ["plaid blanket", "red plaid blanket", "blue plaid blanket"]


CURATED = [
    StoryParams(child_name="Pip", child_type="boy", caretaker_type="nurse", blanket="plaid blanket"),
    StoryParams(child_name="June", child_type="girl", caretaker_type="mother", blanket="red plaid blanket"),
    StoryParams(child_name="Wren", child_type="girl", caretaker_type="caretaker", blanket="blue plaid blanket"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall-tale storyworld in a nap room with curiosity, inner monologue, and a bad ending.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--caretaker-type", choices=CARETAKER_TYPES)
    ap.add_argument("--blanket", choices=BLANKETS)
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
    name = args.name or rng.choice(NAMES)
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    caretaker_type = args.caretaker_type or rng.choice(CARETAKER_TYPES)
    blanket = args.blanket or rng.choice(BLANKETS)
    return StoryParams(name, child_type, caretaker_type, blanket)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
% A notion grows when curiosity is already present.
notion_grows :- curiosity(X), X >= 1.

% Inner monologue can strengthen curiosity.
monologue_fuels_curiosity :- inner_monologue(X), X >= 1.

% Too much curiosity in the nap room causes a bad ending.
bad_ending :- curiosity(X), notion(Y), X >= 2, Y >= 1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "nap_room"),
        asp.fact("feature", "inner_monologue"),
        asp.fact("feature", "bad_ending"),
        asp.fact("feature", "curiosity"),
        asp.fact("style", "tall_tale"),
        asp.fact("word", "notion"),
        asp.fact("word", "everywhere"),
        asp.fact("word", "plaid"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show bad_ending/0."))
    if model:
        print("OK: ASP twin can derive a bad ending from the world facts.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected result.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
