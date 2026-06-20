#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/collage_friendship_comedy.py
============================================================

A small standalone story world about two friends making a collage, tripping over
their own cleverness, and finding a funny, kind solution.

The domain is intentionally tiny:
- two children are making a collage
- one child wants a flashy joke piece
- the other child worries it will ruin the picture or hurt the friendship
- a grown-up or friend helps them fix the plan
- the finished collage ends up better because they listened to each other

The prose is state-driven: the story changes as the world's physical meters and
emotional memes change. The ending image proves what changed.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    surface: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    mess: str
    sound: str
    colorful: bool = False
    sticky: bool = False
    risk: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Compromise:
    id: str
    sense: int
    text: str
    fix_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    for s in out:
        if not s.startswith("__"):
            world.say(s)
    return out


def _r_smudge(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["glue"] < THRESHOLD:
            continue
        sig = ("smudge", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["messy"] += 1
        out.append(f"Bits of glue made the collage surface look messy.")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["giddy"] < THRESHOLD:
            continue
        sig = ("laugh", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] += 1
        out.append(f"A giggle bounced around the room.")
    return out


RULES = [Rule("smudge", _r_smudge), Rule("laugh", _r_laugh)]


def item_at_risk(item: Item, setting: Setting) -> bool:
    return item.mess in setting.affords


def compatible_fix(item: Item) -> Optional[Compromise]:
    for c in COMPROMISES.values():
        if item.mess in c.tags:
            return c
    return None


def predict(world: World, item_id: str) -> dict:
    sim = world.copy()
    _do_glue(sim, sim.get("maker"), sim.get(item_id), narrate=False)
    return {
        "messy": sim.get(item_id).meters["messy"] >= THRESHOLD,
        "friendship": sim.get("friend").memes["hurt"] >= THRESHOLD,
    }


def _do_glue(world: World, maker: Entity, item: Entity, narrate: bool = True) -> None:
    item.meters["glue"] += 1
    maker.memes["glee"] += 1
    propagate(world)
    if narrate:
        world.say("Glue squeezed out in a silly squish.")


def setup(world: World, a: Entity, b: Entity, setting: Setting, item: Item) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} spread paper across "
        f"{setting.place}. They wanted to make a collage that would look as funny "
        f"as it felt."
    )
    world.say(
        f"They gathered scissors, scraps, and {item.phrase}. "
        f"The whole table looked ready for a laugh."
    )


def tempt(world: World, a: Entity, item: Item) -> None:
    a.memes["silliness"] += 1
    world.say(
        f'{a.id} grinned. "What if we stick on {item.label}?" {a.pronoun()} asked. '
        f'"It will be hilarious."'
    )


def warn(world: World, b: Entity, a: Entity, setting: Setting, item: Item) -> bool:
    pred = predict(world, "item")
    if not pred["messy"]:
        return False
    b.memes["care"] += 1
    world.facts["predicted_mess"] = True
    world.say(
        f'{b.id} tilted {b.pronoun("possessive")} head. "If we use {item.label} '
        f"like that, it may turn the collage sticky. We'd better keep the joke, "
        f"but make it gentler."'
    )
    return True


def defy(world: World, a: Entity, item: Item) -> None:
    a.memes["defiance"] += 1
    world.say(f'{a.id} snickered and reached for the glue anyway.')


def clash(world: World, b: Entity, a: Entity) -> None:
    b.memes["hurt"] += 1
    a.memes["regret"] += 1
    world.say(
        f"{b.id} crossed {b.pronoun('possessive')} arms. For a moment, the room "
        f"felt smaller and quieter."
    )


def repair(world: World, parent: Entity, item: Item, fix: Compromise) -> None:
    parent.memes["helpful"] += 1
    parent.memes["humor"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came over and laughed kindly. "
        f'"How about we use {fix.text} instead?"'
    )


def accept(world: World, a: Entity, b: Entity, item: Item, fix: Compromise) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["hurt"] = 0.0
    b.memes["hurt"] = 0.0
    world.say(
        f"{a.id}'s face changed from sneaky to sheepish. Then both friends nodded."
    )
    world.say(
        f"They {fix.fix_text}. Soon the collage had the joke, but not the mess, "
        f"and the two friends were laughing again."
    )


def finish(world: World, a: Entity, b: Entity, setting: Setting, item: Item) -> None:
    world.say(
        f"In the end, their collage showed a giant paper snail wearing a tiny hat, "
        f"a rainbow of scraps, and one shiny {item.label} glued down the safe way."
    )
    world.say(
        f"{a.id} and {b.id} stood back and smiled. Their friendship looked a lot "
        f"like the collage: a little goofy, very colorful, and held together with care."
    )


def tell(setting: Setting, item: Item, fix: Compromise,
         maker_name: str = "Mina", maker_type: str = "girl",
         friend_name: str = "Owen", friend_type: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    maker = world.add(Entity(id=maker_name, kind="character", type=maker_type, role="maker"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    obj = world.add(Entity(id="item", type="thing", label=item.label))

    setup(world, maker, friend, setting, item)
    world.para()
    tempt(world, maker, item)
    warned = warn(world, friend, maker, setting, item)
    if warned:
        defy(world, maker, item)
        clash(world, friend, maker)
        world.para()
        repair(world, parent, item, fix)
        accept(world, maker, friend, item, fix)
    else:
        world.say("But nothing got too messy, so they kept building and kept laughing.")
    world.para()
    finish(world, maker, friend, setting, item)
    world.facts.update(
        maker=maker, friend=friend, parent=parent, item=obj, item_cfg=item,
        setting=setting, fix=fix, warned=warned, resolved=warned
    )
    return world


SETTINGS = {
    "art_room": Setting("art_room", "the art table", "paper", "bright", {"sticky", "glue"}),
    "kitchen": Setting("kitchen", "the kitchen table", "tablecloth", "busy", {"sticky", "glue"}),
    "classroom": Setting("classroom", "the classroom table", "poster board", "cheery", {"sticky", "glue"}),
}

ITEMS = {
    "glitter": Item("glitter", "glitter", "sparkly glitter", "glitter", "shimmer", colorful=True, sticky=True, risk=2, tags={"glitter", "sticky"}),
    "yogurt": Item("yogurt", "yogurt cup", "an upside-down yogurt cup", "sticky", "plop", sticky=True, risk=2, tags={"sticky"}),
    "marker": Item("marker", "marker", "a wobbly marker", "ink", "squeak", colorful=True, risk=1, tags={"color"}),
}

COMPROMISES = {
    "tiny_scoop": Compromise("tiny_scoop", 3, "a tiny scoop of glitter in one corner", "used a tiny scoop of glitter in one corner", "used a tiny scoop of glitter in one corner", {"glitter"}),
    "paper_jokes": Compromise("paper_jokes", 3, "paper jokes and smiling faces", "cut out paper jokes and smiling faces", "cut out paper jokes and smiling faces", {"glitter", "sticky", "ink"}),
    "stickers": Compromise("stickers", 3, "stickers shaped like stars", "added stickers shaped like stars", "added stickers shaped like stars", {"sticky", "ink"}),
}

NAMES = ["Mina", "Owen", "Tia", "Leo", "Nora", "Finn", "Ruby", "Eli"]


@dataclass
class StoryParams:
    setting: str
    item: str
    fix: str
    maker: str
    maker_gender: str
    friend: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for iid, item in ITEMS.items():
            if not item_at_risk(item, s):
                continue
            fix = compatible_fix(item)
            if fix is not None:
                combos.append((sid, iid, fix.id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a 3-to-5-year-old about two friends making a collage and '
        f'arguing over {f["item_cfg"].label}.',
        f"Tell a comedy story where {f['maker'].id} wants to use {f['item_cfg'].label}, "
        f"but a friend worries the collage will get sticky and they fix it together.",
        f'Write a friendship story that includes the word "collage" and ends with both friends smiling.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    maker, friend, parent = f["maker"], f["friend"], f["parent"]
    item = f["item_cfg"]
    fix = f["fix"]
    qs = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {maker.id} and {friend.id}, two friends who were making a collage together. Their grown-up was nearby when the plan got silly.",
        ),
        QAItem(
            question=f"What did {maker.id} want to add to the collage?",
            answer=f"{maker.id} wanted to add {item.label}. {friend.id} worried it would make the collage sticky, so the friends had to rethink the joke.",
        ),
    ]
    if f["warned"]:
        qs.append(QAItem(
            question="Why did the friend warn them?",
            answer=f"{friend.id} warned them because {item.label} could make the collage messy and sticky. That would have made the picture less fun and could have caused a squabble between the friends.",
        ))
        qs.append(QAItem(
            question="How did they solve the problem?",
            answer=f"{parent.label_word.capitalize()} suggested {fix.text}, and the two friends listened. They kept the joke, avoided the mess, and finished the collage together.",
        ))
        qs.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with {maker.id} and {friend.id} smiling at a bright, funny collage. Their friendship stayed strong because they chose the safe joke instead of the sticky one.",
        ))
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    item = world.facts["item_cfg"]
    out = [
        QAItem(
            question="What is a collage?",
            answer="A collage is a picture made by gluing together different scraps, shapes, and pictures. People often make one with paper, scissors, and glue.",
        ),
        QAItem(
            question="Why can glue be messy?",
            answer="Glue can be messy because it is sticky and can spread onto fingers, paper, and tables. If you use too much, it may hold onto things you did not mean to glue down.",
        ),
    ]
    if item.sticky:
        out.append(QAItem(
            question=f"Why is {item.label} tricky to use in art?",
            answer=f"{item.label.capitalize()} is tricky because it can be sticky or hard to control. A little can be funny, but too much can make a collage clump together.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("art_room", "glitter", "tiny_scoop", "Mina", "girl", "Owen", "boy", "mother"),
    StoryParams("kitchen", "yogurt", "paper_jokes", "Tia", "girl", "Leo", "boy", "father"),
    StoryParams("classroom", "marker", "stickers", "Nora", "girl", "Finn", "boy", "mother"),
]


def explain_rejection(setting: Setting, item: Item) -> str:
    if not item_at_risk(item, setting):
        return f"(No story: {item.label} would not seriously threaten a collage in {setting.place}.)"
    return "(No story: no compatible friendship fix exists for that item.)"


def outcome_of(params: StoryParams) -> str:
    return "resolved" if compatible_fix(ITEMS[params.item]) else "no_story"


ASP_RULES = r"""
at_risk(Item, Set) :- item(Item), setting(Set), sticky(Item), gluey(Set).
can_fix(Item, Fix) :- item(Item), compromise(Fix), fix_tag(Fix, Tag), item_tag(Item, Tag).
valid(Set, Item, Fix) :- at_risk(Item, Set), can_fix(Item, Fix).

show_mess(Item) :- item(Item), sticky(Item).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in s.affords:
            if a == "sticky" or a == "glue":
                lines.append(asp.fact("gluey", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.sticky:
            lines.append(asp.fact("sticky", iid))
        for t in item.tags:
            lines.append(asp.fact("item_tag", iid, t))
    for cid, c in COMPROMISES.items():
        lines.append(asp.fact("compromise", cid))
        for t in c.tags:
            lines.append(asp.fact("fix_tag", cid, t))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import re
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generate smoke test failed: {e}")
    if rc == 0:
        print("OK: ASP parity and generate smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world: friendship, collage, and a funny fix.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--fix", choices=COMPROMISES)
    ap.add_argument("--maker")
    ap.add_argument("--friend")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
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
              and (args.item is None or c[1] == args.item)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, fix = rng.choice(sorted(combos))
    maker = args.maker or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != maker])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, item, fix, maker, "girl", friend, "boy", parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], COMPROMISES[params.fix],
                 params.maker, params.maker_gender, params.friend, params.friend_gender,
                 params.parent)
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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            i += 1
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
