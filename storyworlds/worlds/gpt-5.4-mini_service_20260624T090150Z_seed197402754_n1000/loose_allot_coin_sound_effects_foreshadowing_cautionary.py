#!/usr/bin/env python3
"""
storyworlds/worlds/loose_allot_coin_sound_effects_foreshadowing_cautionary.py
=============================================================================

A small comedy storyworld about a child, a handful of loose coins, and a parent
who wants the money allotted wisely before it disappears into a candy machine.

Seed tale inspiration:
---
Nico found a little pile of loose coins under the sofa. The coins jingled, and
Nico wanted to spend them right away on a shiny toy.

Nico's parent noticed the pile and warned that if the coins were not allotted
for snacks, savings, and a gift, there would be nothing left later. Nico tried
to sneak off to the corner store anyway, but the coin purse spilled with a
clink-clink-clink.

Then the parent showed Nico three jars labeled "Now," "Later," and "Share."
Nico laughed, helped allot the coins, and still bought one tiny treat. The
other jars stayed ready for tomorrow.

World model:
---
Physical meters:
    coin_count, clutter, savings, snack_money, gift_money, treat_spent
Emotional memes:
    eagerness, worry, humor, relief, caution, pride

Narrative instruments:
---
* Sound effects: clink, jingle, plink, ding
* Foreshadowing: a rumor of the toy machine, the wobbling coin jar, the almost-empty purse
* Cautionary turn: a warning about spending all the loose coins at once
* Comedy: the solution is practical, small, and a little silly
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.id in {"Nina", "Mia", "Ava", "Luna"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass(frozen=True)
class StoryParams:
    setting: str = "living room"
    child_name: str = "Nico"
    child_gender: str = "boy"
    parent_name: str = "Parent"
    target: str = "toy"
    seed: Optional[int] = None


SETTINGS = {
    "living room": "living room",
    "bedroom": "bedroom",
    "kitchen": "kitchen",
}

CHILD_NAMES = {
    "boy": ["Nico", "Theo", "Finn", "Ben", "Milo", "Leo"],
    "girl": ["Mia", "Nina", "Ava", "Luna", "Zoe", "Ivy"],
}

TARGETS = {
    "toy": {
        "label": "toy robot",
        "shine": "shiny",
        "temptation": "robotic blinking",
    },
    "sticker": {
        "label": "sticker pack",
        "shine": "sparkly",
        "temptation": "glittery",
    },
    "book": {
        "label": "picture book",
        "shine": "bright",
        "temptation": "new-page rustling",
    },
}

SFX = {
    "coins": "clink-clink",
    "jar": "jingle",
    "warning": "ding-ding",
    "spill": "plink-plink-plink",
    "bag": "clack",
}

TRUTHS = [
    ("Why should you not spend every coin at once?",
     "If you spend every coin right away, you may not have any left for later needs, gifts, or treats."),
    ("What does allot mean?",
     "To allot means to divide something up and give each part a job or a place."),
    ("What is a coin purse for?",
     "A coin purse holds small money so the coins do not scatter everywhere."),
]


def ensure_reasonable(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("That setting is not part of this small coin storyworld.")
    if params.child_gender not in CHILD_NAMES:
        raise StoryError("Child gender must be 'boy' or 'girl'.")
    if params.target not in TARGETS:
        raise StoryError("That target is not part of this small coin storyworld.")


def build_world(params: StoryParams) -> World:
    ensure_reasonable(params)
    w = World(setting=params.setting)

    child = w.add(Entity(id=params.child_name, kind="character", label=params.child_name))
    parent = w.add(Entity(id=params.parent_name, kind="character", label=params.parent_name))

    coins = w.add(Entity(
        id="coins",
        label="loose coins",
        phrase="a little pile of loose coins",
        owner=child.id,
        plural=True,
        meters={"coin_count": 7, "clutter": 1},
        memes={"eagerness": 1, "caution": 0, "humor": 0, "worry": 0, "relief": 0, "pride": 0},
    ))

    jars = {
        "now": w.add(Entity(id="now_jar", label="Now jar", phrase="a jar for today")),
        "later": w.add(Entity(id="later_jar", label="Later jar", phrase="a jar for tomorrow")),
        "share": w.add(Entity(id="share_jar", label="Share jar", phrase="a jar for gifts")),
    }

    target = TARGETS[params.target]
    w.facts.update(child=child, parent=parent, coins=coins, jars=jars, target=target, params=params)
    return w


def sfx(name: str) -> str:
    return SFX[name]


def tell(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    coins: Entity = f["coins"]
    target = f["target"]
    jars = f["jars"]

    world.say(
        f"{child.id} was in the {world.setting} when {child.pronoun('possessive')} eyes found a "
        f"{coins.phrase} under the sofa. {sfx('coins')} went the coins, as if they were trying to "
        f"tattle on themselves."
    )
    world.say(
        f"{child.id} loved the {target['shine']} {target['label']}, and the thought of it made "
        f"{child.pronoun('possessive')} feet do a tiny tap-dance. That was the first clue that the day "
        f"might get silly."
    )
    world.say(
        f"{parent.id} noticed the pile and gave a careful {sfx('warning')}. "
        f'"We should allot those loose coins," {parent.pronoun().capitalize()} said. '
        f'"Some for now, some for later, and some for sharing."'
    )

    world.para()
    world.say(
        f"{child.id} peeked at the toy shop flyer on the table. It showed a {target['temptation']} "
        f"thing with a button that went {sfx('jar')} and a grin that said, 'Spend me!' "
        f"The coin purse beside the flyer sagged a little, which was a very suspicious-looking clue."
    )
    coins.memes["eagerness"] += 1
    coins.memes["worry"] += 1
    coins.meters["clutter"] += 1

    world.say(
        f'"If I buy it all now, I will have the best day ever," {child.id} said. '
        f"Then the purse tipped over with a {sfx('spill')}, and three coins skittered away like shiny mice."
    )
    child.memes["eagerness"] = child.memes.get("eagerness", 0) + 1
    child.memes["humor"] = child.memes.get("humor", 0) + 1

    world.say(
        f"{parent.id} pointed at three jars on the shelf: the {jars['now'].label}, the {jars['later'].label}, "
        f"and the {jars['share'].label}. {parent.pronoun().capitalize()} said, "
        f'"If you let all your loose coins race off at once, tomorrow may arrive wearing empty pockets."'
    )
    coins.memes["caution"] += 1
    child.memes["worry"] = child.memes.get("worry", 0) + 1

    world.para()
    world.say(
        f"{child.id} looked at the wobbling coins, then at the jars, and sighed a dramatic little sigh. "
        f'"Okay," {child.pronoun().capitalize()} said. "I can allot them."'
    )

    now_amt = 2
    later_amt = 3
    share_amt = 2
    coins.meters["coin_count"] = 0
    coins.meters["clutter"] = 0
    jars["now"].meters["coin_count"] = now_amt
    jars["later"].meters["coin_count"] = later_amt
    jars["share"].meters["coin_count"] = share_amt
    jars["now"].memes["pride"] = 1
    jars["later"].memes["caution"] = 1
    jars["share"].memes["humor"] = 1

    world.say(
        f"With a {sfx('clink')} for the now jar, a {sfx('jingle')} for the later jar, and a "
        f"{sfx('bag')} for the share jar, the loose coins became tidy and useful."
    )
    world.say(
        f"{child.id} used just one coin for a tiny treat, and that made {child.pronoun('object')} laugh because "
        f"the treat was small but the planning felt huge."
    )
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    child.memes["pride"] = child.memes.get("pride", 0) + 1
    parent.memes = {"pride": 1, "relief": 1, "humor": 1}

    world.say(
        f"In the end, the {jars['now'].label} had enough for today, the {jars['later'].label} kept tomorrow safe, "
        f"and the {jars['share'].label} waited like a polite little surprise. "
        f"{child.id} smiled at the organized coins and said, 'I guess money likes a bedtime story too.'"
    )

    world.facts["now_amt"] = now_amt
    world.facts["later_amt"] = later_amt
    world.facts["share_amt"] = share_amt
    world.facts["spent"] = 1
    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    target = f["target"]
    return [
        f'Write a funny short story for a young child about {child.id}, loose coins, and how to allot money wisely.',
        f"Tell a comedy story where {child.id} finds loose coins, wants a {target['label']}, and learns a cautionary lesson about saving.",
        "Write a child-friendly story that includes sound effects like clink and jingle, plus a neat ending about sorting coins into jars.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    target = f["target"]
    return [
        QAItem(
            question=f"What did {child.id} find under the sofa?",
            answer=f"{child.id} found a little pile of loose coins under the sofa, and they went {sfx('coins')} as they rolled around.",
        ),
        QAItem(
            question=f"What did {parent.id} want {child.id} to do with the coins?",
            answer=f"{parent.id} wanted {child.id} to allot the loose coins into the now jar, the later jar, and the share jar.",
        ),
        QAItem(
            question=f"Why did the parent give a cautionary warning?",
            answer=f"{parent.id} warned that spending every coin at once could leave nothing for later, so the story could not end with an empty pocket.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the coins divided into three jars, one tiny treat bought, and {child.id} smiling because the plan worked.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in TRUTHS]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id} ({e.kind}) " + " ".join(bits))
    return "\n".join(lines)


ASP_RULES = r"""
coin(C) :- loose_coin(C).
needs_allotment(C) :- coin(C).
good_story :- needs_allotment(_), parent_warns, child_accepts.
safe_end :- good_story, jars_filled.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("loose_coin", "coinpile"),
        asp.fact("parent_warns"),
        asp.fact("child_accepts"),
        asp.fact("jars_filled"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/0. #show safe_end/0."))
    shown = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    want = {"good_story/0", "safe_end/0"}
    if shown == want:
        print("OK: ASP and Python story gate agree.")
        return 0
    print("MISMATCH:", sorted(shown), sorted(want))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about loose coins and allotment.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--target", choices=sorted(TARGETS))
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
    setting = args.setting or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(CHILD_NAMES[gender])
    target = args.target or rng.choice(list(TARGETS))
    return StoryParams(setting=setting, child_name=name, child_gender=gender, target=target)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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


CURATED = [
    StoryParams(setting="living room", child_name="Nico", child_gender="boy", target="toy"),
    StoryParams(setting="bedroom", child_name="Mia", child_gender="girl", target="sticker"),
    StoryParams(setting="kitchen", child_name="Theo", child_gender="boy", target="book"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/0. #show safe_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/0. #show safe_end/0."))
        print("ASP model:", " ".join(sorted(f"{sym.name}/{len(sym.arguments)}" for sym in model)))
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
            params = StoryParams(**{**params.__dict__, "seed": base_seed + i})
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.setting} / {p.target}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
