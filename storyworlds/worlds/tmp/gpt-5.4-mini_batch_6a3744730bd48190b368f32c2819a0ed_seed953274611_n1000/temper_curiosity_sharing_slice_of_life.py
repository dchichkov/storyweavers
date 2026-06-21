#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/temper_curiosity_sharing_slice_of_life.py
========================================================================

A small slice-of-life storyworld about curiosity, a rising temper, and a
careful act of sharing that brings everyone back to calm.

The world is built to generate short, complete stories for children:
- a child notices something interesting,
- curiosity pulls them closer,
- impatience/temper rises when a turn is blocked,
- sharing turns the moment around,
- the ending shows the changed state.

This script is standalone and uses only the standard library plus the shared
Storyweavers result/ASP helpers.
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
TEMPER_START = 0.0
CURIOUS_START = 1.0
SHARING_START = 0.0


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
    id: str
    place: str
    mood: str
    detail: str


@dataclass
class CuriosityItem:
    id: str
    label: str
    phrase: str
    wonder: str
    can_share: bool = True
    needs_turns: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareMove:
    id: str
    label: str
    text: str
    outcome: str
    tags: set[str] = field(default_factory=set)


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
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_temper(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child is None:
        return out
    if child.memes["temper"] < THRESHOLD:
        return out
    sig = ("temper",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["stiff"] += 1
    out.append("__temper__")
    return out


def _r_peace(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    buddy = world.entities.get("buddy")
    item = world.entities.get("item")
    if not child or not buddy or not item:
        return out
    if child.memes["sharing"] < THRESHOLD:
        return out
    sig = ("peace",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["temper"] = max(0.0, child.memes["temper"] - 1.0)
    child.memes["calm"] += 1
    buddy.memes["calm"] += 1
    item.meters["shared"] += 1
    out.append("__peace__")
    return out


CAUSAL_RULES = [Rule("temper", "social", _r_temper), Rule("peace", "social", _r_peace)]


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


def shareable(item: CuriosityItem) -> bool:
    return item.can_share and item.needs_turns


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting in SETTINGS:
        for item_id, item in ITEMS.items():
            if shareable(item):
                combos.append((setting, item_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    item: str
    child_name: str
    child_gender: str
    buddy_name: str
    buddy_gender: str
    parent_name: str
    parent_gender: str
    temper: int = 2
    curiosity: int = 2
    sharing: int = 0
    seed: Optional[int] = None


SETTINGS = {
    "living_room": Setting(
        id="living_room",
        place="the living room",
        mood="quiet",
        detail="A low table sat near the rug, and sunlight made a bright square on the floor.",
    ),
    "kitchen_table": Setting(
        id="kitchen_table",
        place="the kitchen table",
        mood="cozy",
        detail="A bowl of fruit sat in the middle, and the chairs were pulled in close.",
    ),
    "porch": Setting(
        id="porch",
        place="the porch",
        mood="warm",
        detail="A little breeze moved the hanging plant and tapped softly at the screen door.",
    ),
}

ITEMS = {
    "storybook": CuriosityItem(
        id="storybook",
        label="storybook",
        phrase="a bright storybook with shiny pictures",
        wonder="the shiny page corners and tiny drawings",
        tags={"book", "story", "sharing"},
    ),
    "crayon_box": CuriosityItem(
        id="crayon_box",
        label="crayon box",
        phrase="a big box of crayons",
        wonder="the row of colors inside",
        tags={"crayon", "color", "sharing"},
    ),
    "puzzle": CuriosityItem(
        id="puzzle",
        label="puzzle",
        phrase="a small wooden puzzle",
        wonder="how the pieces locked together",
        tags={"puzzle", "sharing"},
    ),
}

SHARE_MOVES = {
    "take_turns": ShareMove(
        id="take_turns",
        label="taking turns",
        text="They took turns looking and listening one by one",
        outcome="shared kindly",
        tags={"turns", "sharing"},
    ),
    "trade": ShareMove(
        id="trade",
        label="trading",
        text="They traded places and passed it back and forth",
        outcome="shared gently",
        tags={"trade", "sharing"},
    ),
    "look_together": ShareMove(
        id="look_together",
        label="looking together",
        text="They leaned close and looked together at the same time",
        outcome="shared warmly",
        tags={"together", "sharing"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Theo", "Max", "Noah", "Eli", "Sam"]
TRAITS = ["curious", "thoughtful", "gentle", "restless"]

KNOWLEDGE = {
    "storybook": [("What is a storybook?",
                   "A storybook is a book with stories and pictures to read together. It is often shared because one person can read it while another looks at the pictures.")],
    "crayon_box": [("What is a crayon box?",
                     "A crayon box is a container that holds crayons. People share it when they take turns choosing colors.")],
    "puzzle": [("What is a puzzle?",
                "A puzzle is a game with pieces that fit together. It is fun to solve it with another person, because two pairs of eyes can spot the shapes faster.")],
    "sharing": [("What does sharing mean?",
                 "Sharing means letting someone else use or enjoy something too. It can mean taking turns, passing it back and forth, or looking at it together.")],
    "curious": [("What does curious mean?",
                 "Curious means wanting to know more or wanting to look closely at something new.")],
    "temper": [("What is a temper?",
                "A temper is the angry feeling that can flare up when someone is frustrated or has to wait.")],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about curiosity, temper, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--buddy-name")
    ap.add_argument("--buddy-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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
              and (args.item is None or c[1] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    buddy_gender = args.buddy_gender or ("boy" if child_gender == "girl" else "girl")
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    buddy_name = args.buddy_name or rng.choice([n for n in (BOY_NAMES if buddy_gender == "boy" else GIRL_NAMES) if n != child_name])
    parent_name = args.parent_name or ("Mom" if parent_gender == "mother" else "Dad")
    return StoryParams(
        setting=setting,
        item=item,
        child_name=child_name,
        child_gender=child_gender,
        buddy_name=buddy_name,
        buddy_gender=buddy_gender,
        parent_name=parent_name,
        parent_gender=parent_gender,
        temper=rng.randint(1, 3),
        curiosity=rng.randint(1, 3),
        sharing=0,
    )


def tell(world: World, params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    item = ITEMS[params.item]
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name))
    buddy = world.add(Entity(id="buddy", kind="character", type=params.buddy_gender, label=params.buddy_name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_gender, label=params.parent_name))
    obj = world.add(Entity(id="item", kind="thing", type="thing", label=item.label))
    child.memes["temper"] = float(params.temper)
    child.memes["curiosity"] = float(params.curiosity)
    child.memes["sharing"] = float(params.sharing)
    buddy.memes["sharing"] = 1.0

    world.say(
        f"It was a quiet day in {setting.place}. {setting.detail} "
        f"{child.label} noticed {item.phrase} on the table and leaned closer to see {item.wonder}."
    )
    world.say(
        f"{child.label} was curious, and that curiosity made {child.pronoun()} linger by the table."
    )
    world.para()
    world.say(
        f'"Can I look?" {child.label} asked, but the book was already in {buddy.label_word if False else buddy.label}'  # harmless placeholder avoided below
    )
    # rewrite the line above with clean prose while keeping a single logical beat
    world.paragraphs[-1].pop()
    world.say(
        f'"Can I look?" {child.label} asked, reaching toward {item.phrase}. '
        f'"I just want one turn."'
    )
    child.memes["temper"] += 1
    world.say(
        f"{buddy.label} hesitated, and {child.label}'s temper rose because waiting felt too long."
    )
    propagate(world, narrate=False)
    world.say(
        f"{child.label} crossed {child.pronoun('possessive')} arms and blew out a sharp breath."
    )
    if child.memes["temper"] >= 3:
        world.say(f'"I wanted it now," {child.label} muttered, and {setting.place} went very still.')
    world.para()
    child.memes["sharing"] += 1
    world.say(
        f"Then {parent.label} came by, saw the tight faces, and said, "
        f'"What if you share?"'
    )
    move = SHARE_MOVES["take_turns"] if item.id == "storybook" else (
        SHARE_MOVES["trade"] if item.id == "puzzle" else SHARE_MOVES["look_together"]
    )
    world.say(
        f'{buddy.label} smiled first and made room. {move.text}, and the little fight '
        f"slipped out of the room."
    )
    propagate(world, narrate=False)
    child.memes["temper"] = max(0.0, child.memes["temper"] - 2.0)
    child.memes["sharing"] += 1
    buddy.memes["sharing"] += 1
    obj.meters["shared"] += 1
    world.say(
        f"{child.label} took a slow breath, then nodded. {child.label} and {buddy.label} "
        f"shared {item.phrase}, and the table felt friendly again."
    )
    world.say(
        f"By the end, {child.label}'s temper had cooled, and {item.phrase} had become a thing they enjoyed together."
    )
    world.facts.update(
        child=child, buddy=buddy, parent=parent, item=obj, item_cfg=item, setting=setting,
        move=move, outcome="shared", temper=params.temper, curiosity=params.curiosity,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old about {f["child"].label} '
        f'being curious about {f["item_cfg"].phrase}, then learning to share.',
        f'Tell a small everyday story where {f["child"].label} feels a temper coming on, '
        f'but the day turns gentle again through sharing.',
        f'Write a calm story that includes the word "temper" and ends with {f["child"].label} '
        f'and {f["buddy"].label} enjoying {f["item_cfg"].phrase} together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, buddy, parent, item, cfg, move = f["child"], f["buddy"], f["parent"], f["item"], f["item_cfg"], f["move"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.label}, who was curious about {cfg.phrase}, and about {buddy.label}, who had to share the moment. {parent.label} helped them turn a small problem into a kinder one.",
        ),
        QAItem(
            question=f"Why did {child.label}'s temper go up?",
            answer=f"{child.label} wanted a turn right away, but had to wait while {buddy.label} held the item. That waiting made the temper rise, because the feeling of wanting something now can get big very fast.",
        ),
        QAItem(
            question="How did the problem get fixed?",
            answer=f"They chose {move.label}. That let both children use {cfg.phrase} without fighting, and it cooled the temper down.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["item_cfg"].tags) | {"sharing", "curious", "temper"}
    out: list[QAItem] = []
    for key, pairs in KNOWLEDGE.items():
        if key in tags:
            for q, a in pairs:
                out.append(QAItem(question=q, answer=a))
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.kind:
            bits.append(f"kind={e.kind}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="living_room",
        item="storybook",
        child_name="Mia",
        child_gender="girl",
        buddy_name="Noah",
        buddy_gender="boy",
        parent_name="Mom",
        parent_gender="mother",
        temper=2,
        curiosity=3,
        sharing=0,
    ),
    StoryParams(
        setting="kitchen_table",
        item="crayon_box",
        child_name="Ben",
        child_gender="boy",
        buddy_name="Ava",
        buddy_gender="girl",
        parent_name="Dad",
        parent_gender="father",
        temper=3,
        curiosity=2,
        sharing=0,
    ),
    StoryParams(
        setting="porch",
        item="puzzle",
        child_name="Zoe",
        child_gender="girl",
        buddy_name="Eli",
        buddy_gender="boy",
        parent_name="Mom",
        parent_gender="mother",
        temper=1,
        curiosity=3,
        sharing=0,
    ),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.can_share:
            lines.append(asp.fact("shareable", iid))
        if item.needs_turns:
            lines.append(asp.fact("needs_turns", iid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, I) :- setting(S), item(I), shareable(I), needs_turns(I).
"""


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if a - b:
            print("  only in clingo:", sorted(a - b))
        if b - a:
            print("  only in python:", sorted(b - a))
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, item=None, child_name=None, child_gender=None, buddy_name=None,
            buddy_gender=None, parent_name=None, parent_gender=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: default-style generation smoke test succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_rejection() -> str:
    return "(No story: this world only tells stories about something shareable that can genuinely be shared.)"


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description="Slice-of-life storyworld about curiosity, temper, and sharing.")


def valid_or_raise(args: argparse.Namespace) -> None:
    if args.item and not ITEMS[args.item].can_share:
        raise StoryError(explain_rejection())


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    valid_or_raise(args)
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == args.setting)
              and (getattr(args, "item", None) is None or c[1] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item = rng.choice(sorted(combos))
    child_gender = getattr(args, "child_gender", None) or rng.choice(["girl", "boy"])
    buddy_gender = getattr(args, "buddy_gender", None) or ("boy" if child_gender == "girl" else "girl")
    child_name = getattr(args, "child_name", None) or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    buddy_name = getattr(args, "buddy_name", None) or rng.choice([n for n in (BOY_NAMES if buddy_gender == "boy" else GIRL_NAMES) if n != child_name])
    parent_gender = getattr(args, "parent_gender", None) or rng.choice(["mother", "father"])
    parent_name = getattr(args, "parent_name", None) or ("Mom" if parent_gender == "mother" else "Dad")
    return StoryParams(
        setting=setting,
        item=item,
        child_name=child_name,
        child_gender=child_gender,
        buddy_name=buddy_name,
        buddy_gender=buddy_gender,
        parent_name=parent_name,
        parent_gender=parent_gender,
        temper=rng.randint(1, 3),
        curiosity=rng.randint(1, 3),
        sharing=0,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.item not in ITEMS:
        raise StoryError("(Invalid params: unknown setting or item.)")
    world = tell(World(), params)
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
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about curiosity, temper, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--buddy-name")
    ap.add_argument("--buddy-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    args = ap.parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, item) combos:\n")
        for setting, item in combos:
            print(f"  {setting:12} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and {p.buddy_name}: {p.item} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
