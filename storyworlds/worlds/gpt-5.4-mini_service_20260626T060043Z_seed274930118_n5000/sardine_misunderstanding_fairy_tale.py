#!/usr/bin/env python3
"""
storyworlds/worlds/sardine_misunderstanding_fairy_tale.py
=========================================================

A small fairy-tale storyworld about a royal misunderstanding involving a sardine.

Premise:
- A child or young helper finds a sardine-shaped clue or gift.
- A castle or cottage court mistakes the sardine for something else.
- The misunderstanding creates a small social problem.
- A gentle reveal resolves the confusion and leaves the characters relieved.

The world model tracks:
- physical meters: freshness, hunger, distance, value, tidiness
- emotional memes: curiosity, confusion, worry, relief, gratitude

The narration is driven by those world-state changes, not by a frozen template.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["freshness", "hunger", "distance", "value", "tidiness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "confusion", "worry", "relief", "gratitude", "kindness"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "woman", "mother"}
        male = {"boy", "king", "prince", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the moonlit cottage"
    outdoors: bool = False
    has_larder: bool = True
    has_market: bool = True


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    true_kind: str
    mistaken_for: str
    freshness: str
    smell: str
    value: float


@dataclass
class StoryParams:
    setting: str
    clue: str
    seeker: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts["clue"]
    seeker = world.get(world.facts["seeker"].id)
    if seeker.memes["confusion"] < THRESHOLD:
        return out
    sig = ("confusion", clue.id, seeker.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seeker.memes["worry"] += 1
    out.append(f"The more {seeker.name_or_label()} thought about it, the more confused {seeker.pronoun()} became.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts["clue"]
    seeker = world.get(world.facts["seeker"].id)
    helper = world.get(world.facts["helper"].id)
    if seeker.memes["confusion"] < THRESHOLD or helper.memes["kindness"] < THRESHOLD:
        return out
    sig = ("reveal", clue.id, seeker.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seeker.memes["confusion"] = 0.0
    seeker.memes["relief"] += 1
    helper.memes["gratitude"] += 1
    out.append("__reveal__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_confusion, _r_reveal):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend([x for x in lines if x != "__reveal__"])
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "cottage": Setting(place="the moonlit cottage", outdoors=False, has_larder=True, has_market=False),
    "village": Setting(place="the little village market", outdoors=True, has_larder=True, has_market=True),
    "harbor": Setting(place="the silver harbor", outdoors=True, has_larder=True, has_market=True),
}

CLUES = {
    "sardine": Clue(
        id="sardine",
        label="sardine",
        phrase="a tiny silver sardine",
        true_kind="fish",
        mistaken_for="shoe",
        freshness="fresh",
        smell="briny",
        value=1.0,
    ),
    "tin": Clue(
        id="tin",
        label="tin",
        phrase="a little tin box with a ribbon",
        true_kind="box",
        mistaken_for="treasure",
        freshness="shiny",
        smell="metallic",
        value=2.0,
    ),
    "song": Clue(
        id="song",
        label="song scroll",
        phrase="a rolled song scroll sealed with wax",
        true_kind="paper",
        mistaken_for="spell",
        freshness="new",
        smell="dusty",
        value=3.0,
    ),
}

NAMES = {
    "girl": ["Mira", "Elin", "Luna", "Rose", "Nora"],
    "boy": ["Finn", "Theo", "Bram", "Eli", "Jory"],
    "helper": ["the baker", "the miller", "the lantern keeper", "the old fisher"],
    "seer": ["the queen", "the prince", "the goose girl", "the castle page"],
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for clue_id in CLUES:
            if setting_id == "cottage" and clue_id == "song":
                combos.append((setting_id, clue_id))
            elif clue_id == "sardine":
                combos.append((setting_id, clue_id))
            else:
                combos.append((setting_id, clue_id))
    return sorted(set(combos))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld of sardine misunderstandings.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--seeker")
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue = rng.choice(combos)
    return StoryParams(
        setting=setting,
        clue=clue,
        seeker=args.seeker or rng.choice(NAMES["girl"] + NAMES["boy"]),
        helper=args.helper or rng.choice(NAMES["helper"]),
    )


def tell(setting: Setting, clue: Clue, seeker_name: str, helper_name: str) -> World:
    world = World(setting)
    seeker = world.add(Entity(id=seeker_name, kind="character", type="girl" if seeker_name in NAMES["girl"] else "boy", label=seeker_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="woman", label=helper_name))
    fish = world.add(Entity(id=clue.id, type=clue.true_kind, label=clue.label, phrase=clue.phrase, owner=seeker.id))
    fish.meters["freshness"] = 1.0
    fish.meters["value"] = clue.value

    world.facts.update(seeker=seeker, helper=helper, clue=fish)

    world.say(f"Once upon a time, {seeker.name_or_label()} lived near {setting.place}.")
    world.say(f"{seeker.name_or_label()} found {clue.phrase} at the door of the cottage and held it up like a secret.")
    seeker.memes["curiosity"] += 1
    fish.meters["distance"] = 0.0

    world.para()
    world.say(f"The court at {setting.place} saw the little thing and made a hurried guess.")
    seeker.memes["confusion"] += 1
    helper.memes["kindness"] += 1
    helper.meters["tidiness"] += 1
    world.say(f'"That is no fish," said {helper.name_or_label()}, "but a sign from the sea."')
    world.say(f"Yet the first guess was wrong, and {seeker.name_or_label()} worried the room would laugh.")

    propagate(world, narrate=False)
    world.para()
    world.say(f"{helper.name_or_label()} smiled softly and brought a bowl of clean water and a lantern.")
    world.say(f"At the light, everyone saw the truth: it was only {clue.phrase}, briny and small.")
    world.say(f"The misunderstanding melted away, and {seeker.name_or_label()} breathed out in relief.")
    seeker.memes["relief"] += 1
    helper.memes["gratitude"] += 1
    fish.meters["value"] += 0.5
    world.say(f"In the end, {seeker.name_or_label()} carried the {clue.label} home, and the room felt kind again.")

    world.facts.update(resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    clue = f["clue"]
    return [
        f'Write a short fairy tale for a young child about a misunderstanding involving "{clue.label}".',
        f"Tell a gentle story where {seeker.name_or_label()} finds {clue.phrase} and people guess wrong at first.",
        f"Write a simple castle story that ends with the truth about a {clue.label} being understood.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    clue = f["clue"]
    return [
        QAItem(
            question=f"What did {seeker.name_or_label()} find at the cottage door?",
            answer=f"{seeker.name_or_label()} found {clue.phrase} at the door, and it started the misunderstanding.",
        ),
        QAItem(
            question=f"Why did the room get confused about the {clue.label}?",
            answer=f"The room got confused because the little {clue.label} looked strange at first, so people made the wrong guess.",
        ),
        QAItem(
            question=f"Who helped clear up the misunderstanding?",
            answer=f"{helper.name_or_label()} helped by looking closely and gently showing everyone the truth.",
        ),
    ]


def world_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sardine?",
            answer="A sardine is a very small fish, usually silver and often found in the sea.",
        ),
        QAItem(
            question="What does a misunderstanding mean?",
            answer="A misunderstanding happens when people think something means one thing, but it really means something else.",
        ),
        QAItem(
            question="What does a kind helper do in a fairy tale?",
            answer="A kind helper listens carefully, brings calm ideas, and helps everyone understand each other.",
        ),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
clue(C) :- clue_fact(C).
misunderstanding(C) :- clue(C).
resolved(C) :- misunderstanding(C).

#show clue/1.
#show misunderstanding/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid in CLUES:
        lines.append(asp.fact("clue_fact", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show clue/1."))
    return sorted(set(asp.atoms(model, "clue")))


def asp_verify() -> int:
    import asp
    py = {(c,) for c in CLUES}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() style registry ({len(cl)} clues).")
        return 0
    print("MISMATCH between clingo and Python registry:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], params.seeker, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="cottage", clue="sardine", seeker="Mira", helper="the old fisher"),
    StoryParams(setting="village", clue="sardine", seeker="Finn", helper="the baker"),
    StoryParams(setting="harbor", clue="sardine", seeker="Luna", helper="the lantern keeper"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show clue/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show clue/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
