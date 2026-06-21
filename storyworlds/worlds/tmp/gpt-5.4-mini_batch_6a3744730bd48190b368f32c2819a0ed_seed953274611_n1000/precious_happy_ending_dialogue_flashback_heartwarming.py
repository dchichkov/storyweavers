#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/precious_happy_ending_dialogue_flashback_heartwarming.py
========================================================================================

A small heartwarming storyworld about a precious object, a brief loss, a remembered
flashback, and a happy ending told through dialogue.

Premise
-------
A child treasures one special thing: a handmade keepsake, a tiny gift, or a beloved
object. It gets misplaced during an ordinary day. The child and a caring helper search,
remember an earlier moment of love, and find it again. The story ends with relief,
gratitude, and a warm image that proves what changed.

Features
--------
- heartwarming tone
- dialogue
- flashback
- happy ending

The world model keeps track of physical state in meters and feelings in memes, and the
story is rendered from that changing state.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    place: str
    precious: bool = True
    owner_hint: str = ""
    found_by_flashback: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    @property
    def the(self) -> str:
        return f"the {self.label}"


@dataclass
class PromptTheme:
    id: str
    ordinary_scene: str
    search_line: str
    remembered_line: str
    closing_image: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_item(self, i: Item) -> Item:
        self.items[i.id] = i
        return i

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.items = copy.deepcopy(self.items)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for item in world.items.values():
        if item.meters["found"] >= THRESHOLD and ("relief", item.id) not in world.fired:
            world.fired.add(("relief", item.id))
            for e in world.entities.values():
                e.memes["relief"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def valid_combos() -> list[tuple[str, str]]:
    return [(t.id, i.id) for t in THEMES.values() for i in ITEMS.values() if i.precious]


def reasonableness_gate(theme_id: str, item_id: str) -> None:
    if theme_id not in THEMES:
        raise StoryError(f"(No story: unknown theme '{theme_id}'.)")
    if item_id not in ITEMS:
        raise StoryError(f"(No story: unknown precious item '{item_id}'.)")


def _flashback(world: World, child: Entity, item: Item) -> None:
    child.memes["remembering"] += 1
    world.say(
        f"{child.id} paused. A flashback drifted in: {item.phrase} in {child.pronoun('possessive')} hands, "
        f"and a warm voice saying, \"Keep it close, because it is precious.\""
    )


def _search(world: World, child: Entity, helper: Entity, item: Item, theme: PromptTheme) -> None:
    child.memes["worry"] += 1
    helper.memes["care"] += 1
    world.say(
        f"\"Have you seen {item.the}?\" {child.id} asked. {helper.id} shook {helper.pronoun('possessive')} head. "
        f"\"Not yet,\" {helper.pronoun()} said gently. \"Let's look together.\""
    )
    world.say(
        f"They checked {theme.ordinary_scene}, then the quiet corners, and the worry in {child.id}'s chest grew small enough to listen."
    )


def _find(world: World, child: Entity, helper: Entity, item: Item) -> None:
    item.meters["found"] += 1
    item.found_by_flashback = True
    world.say(
        f"Then {child.id} remembered the last place {item.the} had been touched with care. "
        f'They whispered, "{item.owner_hint}..." and hurried there together.'
    )
    world.say(
        f"Under a soft cushion, {child.id} found {item.the}. \"There you are!\" {child.id} laughed. "
        f"\"I knew you were somewhere safe.\""
    )
    propagate(world, narrate=False)


def _ending(world: World, child: Entity, helper: Entity, item: Item, theme: PromptTheme) -> None:
    child.memes["joy"] += 2
    helper.memes["joy"] += 1
    world.say(
        f"\"I was so scared,\" {child.id} admitted. {helper.id} smiled. "
        f"\"You looked carefully, and you remembered what mattered. That's love doing the looking.\""
    )
    world.say(
        f"{item.id.capitalize()} was cleaned, tucked into a little pocket, and carried back into {theme.closing_image}."
    )
    world.say(
        f"This time, {item.the} was not lost at all. It was safe, close by, and more precious than ever."
    )


def tell(theme: PromptTheme, item: Item, child_name: str = "Mia", child_type: str = "girl",
         helper_name: str = "Mom", helper_type: str = "mother") -> World:
    world = World()
    child = world.add_entity(Entity(id=child_name, kind="character", type=child_type, role="child"))
    helper = world.add_entity(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    world.add_item(item)

    world.say(
        f"On an ordinary day, {child.id} and {helper.id} were sharing {theme.ordinary_scene}. "
        f"{child.id} loved one thing most of all: {item.phrase}."
    )
    world.say(
        f'\"{item.the} is precious,\" {child.id} said. {helper.id} smiled. \"Then we will take good care of it.\"'
    )
    world.para()
    _search(world, child, helper, item, theme)
    world.para()
    _flashback(world, child, item)
    _find(world, child, helper, item)
    world.para()
    _ending(world, child, helper, item, theme)

    world.facts.update(
        child=child,
        helper=helper,
        item=item,
        theme=theme,
        found=item.meters["found"] >= THRESHOLD,
    )
    return world


THEMES = {
    "bedtime": PromptTheme(
        id="bedtime",
        ordinary_scene="a bedtime tidy-up in the warm living room",
        search_line="They looked under blankets and behind pillows.",
        remembered_line="The memory helped the child breathe again.",
        closing_image="the bedtime shelf beside the night-light",
    ),
    "picnic": PromptTheme(
        id="picnic",
        ordinary_scene="a picnic on a sunny blanket in the park",
        search_line="They checked the basket, the grass, and the tree roots.",
        remembered_line="The memory pointed them back to the blanket.",
        closing_image="the picnic basket with crumbs and sunshine",
    ),
    "rainy_day": PromptTheme(
        id="rainy_day",
        ordinary_scene="a rainy afternoon at the kitchen table",
        search_line="They looked near the mug, the napkins, and the window seat.",
        remembered_line="The memory led them to the softest hiding place.",
        closing_image="the kitchen counter where the rain tapped softly",
    ),
}

ITEMS = {
    "star_pin": Item(
        id="star_pin",
        label="star pin",
        phrase="a tiny star-shaped pin",
        place="pocket",
        owner_hint="the pocket with the blue seam",
    ),
    "song_note": Item(
        id="song_note",
        label="paper note",
        phrase="a folded paper note with a song on it",
        place="book",
        owner_hint="the song tucked into the storybook",
    ),
    "button_bear": Item(
        id="button_bear",
        label="button bear",
        phrase="a little button bear from long ago",
        place="cushion",
        owner_hint="the cushion where the bear had rested before",
    ),
}

CURATED = [
    StoryParams := None
]

@dataclass
class StoryParams:
    theme: str
    item: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(theme="bedtime", item="star_pin", child_name="Mia", child_type="girl", helper_name="Mom", helper_type="mother"),
    StoryParams(theme="picnic", item="song_note", child_name="Noah", child_type="boy", helper_name="Dad", helper_type="father"),
    StoryParams(theme="rainy_day", item="button_bear", child_name="Ava", child_type="girl", helper_name="Mom", helper_type="mother"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the word "precious" and a gentle flashback.',
        f'Tell a dialogue-rich story where {f["child"].id} looks for {f["item"].phrase} and remembers why it is precious.',
        f'Write a happy ending story where a child loses something precious for a moment, remembers it, and finds it with help.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, item, theme = f["child"], f["helper"], f["item"], f["theme"]
    return [
        ("What was the child looking for?",
         f"{child.id} was looking for {item.the}. It mattered so much because {item.phrase} was precious to {child.id}."),
        ("What happened in the flashback?",
         f"{child.id} remembered having {item.phrase} in {child.pronoun('possessive')} hands and hearing that it should be kept close. That memory helped {child.pronoun('object')} think calmly and search in the right place."),
        ("How did the story end?",
         f"The story ended happily when {child.id} found {item.the} and carried it safely back into {theme.closing_image}. {helper.id} stayed beside {child.id}, and the ending felt warm and safe."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does precious mean?",
         "Precious means something is very special and loved a lot. People take careful care of precious things."),
        ("What is a flashback?",
         "A flashback is a memory scene from earlier. Stories use it to help readers understand why something matters now."),
        ("What is a dialogue?",
         "Dialogue is when characters speak to each other in the story. It helps the reader hear their feelings and choices."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    for i in world.items.values():
        bits = []
        if any(v for v in i.meters.values()):
            bits.append(f"meters={dict(i.meters)}")
        if i.found_by_flashback:
            bits.append("found_by_flashback=True")
        lines.append(f"  {i.id:8} (item   ) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(theme_id: str, item_id: str) -> str:
    if theme_id not in THEMES:
        return f"(No story: unknown theme '{theme_id}'.)"
    if item_id not in ITEMS:
        return f"(No story: unknown item '{item_id}'.)"
    return "(No story: that combination is not meaningful.)"


ASP_RULES = r"""
found(I) :- item(I), found_marker(I).
happy_end :- found(I).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("found_marker", iid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show found/1."))
    return sorted(set(asp.atoms(model, "found")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    rc = 0
    if set(asp_valid_combos()) != {(iid,) for iid in ITEMS}:
        rc = 1
        print("MISMATCH in ASP twin.")
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            sample = generate(resolve_params(argparse.Namespace(theme=None, item=None, child_name=None, child_type=None, helper_name=None, helper_type=None), random.Random(7)))
            emit(sample)
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming precious-object storyworld.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father"])
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
    theme = args.theme or rng.choice(list(THEMES))
    item = args.item or rng.choice(list(ITEMS))
    reasonableness_gate(theme, item)
    return StoryParams(
        theme=theme,
        item=item,
        child_name=args.child_name or rng.choice(["Mia", "Ava", "Noah", "Leo"]),
        child_type=args.child_type or rng.choice(["girl", "boy"]),
        helper_name=args.helper_name or rng.choice(["Mom", "Dad"]),
        helper_type=args.helper_type or rng.choice(["mother", "father"]),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES or params.item not in ITEMS:
        raise StoryError("Invalid params.")
    world = tell(
        THEMES[params.theme],
        ITEMS[params.item],
        child_name=params.child_name,
        child_type=params.child_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show found/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible items:", ", ".join(i[0] for i in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
