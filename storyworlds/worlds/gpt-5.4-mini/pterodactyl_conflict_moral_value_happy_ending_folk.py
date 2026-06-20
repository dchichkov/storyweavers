#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pterodactyl_conflict_moral_value_happy_ending_folk.py
======================================================================================

A standalone storyworld for a small folk-tale domain: a child, a conflict about
whether to keep a found treasure, a pterodactyl in the scene, a moral choice,
and a happy ending.

This world is deliberately tiny and classical:
- a child finds something that isn't theirs
- a friend or elder warns them
- a pterodactyl becomes involved as a vivid, gentle witness/helper
- the child makes the moral choice to return the item
- the ending is warm and complete

The narration is state-driven: physical meters and emotional memes accumulate,
events change the world, and the final image proves what changed.
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
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    name: str
    place_line: str
    mood_line: str


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    moral: str
    found_line: str
    return_line: str


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    sound: str
    helps: bool = True


@dataclass
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                out.extend(items)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_shame(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["guilt"] >= THRESHOLD and ("shame",) not in world.fired:
        world.fired.add(("shame",))
        child.memes["shy"] += 1
        out.append("")
    return out


def _r_pact(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    elder = world.get("elder")
    if child.memes["honesty"] >= THRESHOLD and elder.memes["warmth"] >= THRESHOLD:
        sig = ("pact",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["relief"] += 1
        elder.memes["pride"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("shame", _r_shame), Rule("pact", _r_pact)]


def tell(setting: Setting, treasure: Treasure, creature: Creature) -> World:
    world = World()
    child = world.add(Entity("child", kind="character", type="girl", role="child"))
    elder = world.add(Entity("elder", kind="character", type="woman", role="elder"))
    ptero = world.add(Entity("ptero", kind="character", type="pterodactyl", role="helper", label=creature.label))
    chest = world.add(Entity("chest", label=treasure.label, type="thing"))
    grove = world.add(Entity("grove", label=setting.name, type="place"))
    child.memes["curiosity"] = 1
    elder.memes["warmth"] = 1
    ptero.meters["wings"] = 1
    world.facts.update(setting=setting, treasure=treasure, creature=creature)

    world.say(f"Long ago, in {setting.name}, a little girl wandered where the reeds leaned low and the river sang.")
    world.say(setting.place_line)
    world.say(f"There she found {treasure.phrase}. {treasure.found_line}")
    world.say(f"The little girl held it tight, and her heart beat fast with want.")
    world.para()
    world.say(f"Then her elder saw the gleam and spoke gently: '{treasure.moral}.'")
    child.memes["greed"] += 1
    child.memes["doubt"] += 1
    elder.memes["warmth"] += 1
    world.say("The child frowned, for she wanted the treasure for herself, and that was the start of the trouble.")
    world.say(f"At that very moment, {creature.phrase} drifted overhead. {creature.sound} it called, as if the sky itself had listened.")
    world.para()
    child.memes["guilt"] += 1
    world.say(f"The child looked at the treasure again, and then at the path home. She remembered what was right.")
    child.memes["honesty"] += 1
    world.say(f"She carried the treasure back to the old stone gate. {treasure.return_line}")
    ptero.meters["flight"] += 1
    ptero.memes["joy"] += 1
    world.say("The pterodactyl swooped down, not to frighten anyone, but to circle once above them like a guardian of the wind.")
    world.say("The elder smiled and kissed the child's brow. 'A good heart makes a good end,' she said.")
    world.para()
    world.say("So the treasure was returned, the path was made honest again, and the pterodactyl flew away over the bright fields.")
    world.say("That evening, the girl watched the red sky and felt light inside, because she had chosen kindness over keeping what was not hers.")
    world.facts.update(child=child, elder=elder, ptero=ptero, chest=chest, grove=grove, outcome="happy", returned=True)
    propagate(world, narrate=False)
    return world


SETTINGS = {
    "riverbank": Setting(
        "riverbank",
        "the riverbank",
        "The bank was soft with moss, and a line of willow trees bent toward the water.",
        "It felt like a place where secrets could be found and then kindly given back.",
    ),
    "meadow": Setting(
        "meadow",
        "the meadow",
        "The meadow was full of clover, and the grass shimmered under a mild blue sky.",
        "It felt like a place where a little mistake could turn into a wise choice.",
    ),
    "hill": Setting(
        "hill",
        "the green hill",
        "The hill rose above the village, where the wind could carry a voice far and wide.",
        "It felt like a place where the sky could witness a promise being kept.",
    ),
}

TREASURES = {
    "gold_ring": Treasure(
        "gold_ring",
        "a gold ring",
        "a small gold ring with a blue stone",
        "honest hands keep a home bright",
        "It had slipped from the elder's basket earlier that morning.",
        "The girl placed it in the elder's palm, and the elder laughed with relief.",
    ),
    "silver_needle": Treasure(
        "silver_needle",
        "a silver needle",
        "a bright silver needle wrapped in cloth",
        "what is found in kindness should be given in kindness",
        "It glittered like a tiny moonbeam in the grass.",
        "The girl returned it, and the elder tucked it safely back into her sewing pouch.",
    ),
    "red_charm": Treasure(
        "red_charm",
        "a red charm",
        "a red charm tied with a frayed string",
        "a borrowed thing is a promise until it goes home again",
        "It warmed the girl's hand as if it wanted to be remembered.",
        "The girl gave it back, and the elder smiled as though the day had been repaired.",
    ),
}

CREATURES = {
    "pterodactyl": Creature(
        "pterodactyl",
        "a great pterodactyl",
        "a great pterodactyl with a long beak and kind eyes",
        "Kraa-kraa!",
        helps=True,
    ),
    "sky_watcher": Creature(
        "sky_watcher",
        "a watchful pterodactyl",
        "a watchful pterodactyl circling the clouds",
        "Kreee!",
        helps=True,
    ),
}

NAMES = ["Mira", "Lina", "Tessa", "Nina", "Poppy", "Ivy", "Sera", "Faye"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TREASURES:
            for c in CREATURES:
                combos.append((s, t, c))
    return combos


@dataclass
class StoryParams:
    setting: str
    treasure: str
    creature: str
    name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld with a pterodactyl, a moral choice, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--name", choices=NAMES)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.treasure is None or c[1] == args.treasure)
              and (args.creature is None or c[2] == args.creature)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, treasure, creature = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting, treasure, creature, name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a young child that includes the word "pterodactyl" and ends happily.',
        f"Tell a gentle story where {f['child'].id} finds something valuable, feels a conflict about keeping it, and chooses the moral path.",
        f"Write a village tale in which a pterodactyl appears while a child learns that honesty matters more than keeping treasure.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    t: Treasure = f["treasure"]
    c: Creature = f["creature"]
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    return [
        ("What conflict was the child facing?",
         f"{child.id} wanted to keep the treasure, but the elder reminded her that it was not really hers. That made the choice feel hard until she decided to do the honest thing."),
        ("What moral did the story teach?",
         f"It taught that honest hands and kind hands should send a borrowed treasure back home. In this tale, doing the right thing leads to peace instead of trouble."),
        ("How did the story end?",
         f"It ended happily: the treasure was returned, the elder was relieved, and the pterodactyl flew away over the fields. The girl felt light inside because she had done what was right."),
        ("Why did the pterodactyl matter?",
         f"{c.label.capitalize()} made the scene feel magical and watched over the choice the child was making. It helped the tale feel like an old folk story, where the sky itself seems to notice goodness."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a pterodactyl?",
         "A pterodactyl is a flying prehistoric creature with wings and a long beak. In stories, it can feel grand and sky-like, almost like a dragon made by nature."),
        ("What makes a tale a folk tale?",
         "A folk tale is an old-style story that feels simple, wise, and a little magical. It often teaches a lesson and ends in a way that feels complete."),
        ("Why is honesty a moral value?",
         "Honesty matters because it helps people trust one another. When someone tells the truth or returns what they found, it keeps friendships and families strong."),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:12}) meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TREASURES[params.treasure], CREATURES[params.creature])
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


ASP_RULES = r"""
valid(S, T, C) :- setting(S), treasure(T), creature(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t))
    for c in CREATURES:
        lines.append(asp.fact("creature", c))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(StoryParams(*valid_combos()[0], name=NAMES[0]))
        _ = sample.story
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def explain_rejection() -> str:
    return "(No story: this world is always reasonable, so no rejection is needed.)"


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
        for s, t, c in combos:
            print(f"  {s:10} {t:12} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(s, t, c, NAMES[0])) for s, t, c in valid_combos()[:5]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
