#!/usr/bin/env python3
"""
storyworlds/worlds/referee_sharing_tall_tale.py
================================================

A small story world about a referee who helps a pair of children learn to share
a remarkable prize in a tall-tale setting.

The seed image:
---
In a windy little town, two children found a prize that was too big for one set
of hands: a giant kite with ribbons like streamers. They each wanted to keep it,
and the bickering grew loud enough to wake the courthouse bell. Then the
referee, with a whistle bright as a star and a hat as wide as a wagon wheel,
stepped in and showed them how to share the kite so it could soar higher than
either child could reach alone.
---

This file follows the Storyworld contract:
- standalone stdlib script
- typed entities with physical meters and emotional memes
- state-driven prose, not a frozen template
- inline ASP twin plus a Python reasonableness gate
- story QA, world QA, trace, JSON, verify, and show-ASP support
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"size": 0.0, "wear": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "want": 0.0, "grumble": 0.0, "fairness": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "referee"}  # referee default neutral below
        male = {"boy", "father", "dad", "man"}
        if self.type == "referee":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_thing(self) -> bool:
        return self.kind == "thing"


@dataclass
class Setting:
    place: str
    weather: str
    airy: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    size: str
    plural: bool = False
    share_units: int = 2
    requires_referee: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SharingMove:
    id: str
    verb: str
    method: str
    reveal: str
    settle: str
    keyword: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.wind: float = 0.0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "courthouse_green": Setting(place="the courthouse green", weather="windy", airy=True, affords={"kite"}),
    "fairground": Setting(place="the fairground", weather="breezy", airy=True, affords={"kite", "banner"}),
    "river_bend": Setting(place="the river bend", weather="windy", airy=True, affords={"kite", "balloon"}),
}

SHARING_MOVES = {
    "turns": SharingMove(
        id="turns",
        verb="share turns",
        method="take turns holding the string",
        reveal="one child could fly it high while the other guided it low",
        settle="they traded places at every bright gust",
        keyword="turns",
        tags={"share", "turn"},
    ),
    "split": SharingMove(
        id="split",
        verb="share by splitting it up",
        method="split the ribbons between them",
        reveal="the ribbons sang like fiddle strings in the wind",
        settle="each child held a ribbon and the prize danced between them",
        keyword="split",
        tags={"share", "split"},
    ),
    "together": SharingMove(
        id="together",
        verb="share together",
        method="hold it together with both sets of hands",
        reveal="the whole thing lifted like a bright wooden bird",
        settle="they lifted it as one and laughed at the sky",
        keyword="together",
        tags={"share", "together"},
    ),
}

PRIZES = {
    "kite": Prize(
        label="kite",
        phrase="a giant kite with ribbon tails",
        type="kite",
        size="big",
        plural=False,
        share_units=2,
        requires_referee=True,
        tags={"wind", "sky", "share"},
    ),
    "banner": Prize(
        label="banner",
        phrase="a long parade banner made of bright cloth",
        type="banner",
        size="big",
        plural=False,
        share_units=2,
        requires_referee=True,
        tags={"cloth", "share"},
    ),
    "balloon": Prize(
        label="balloon",
        phrase="a sky-high balloon with a basket of streamers",
        type="balloon",
        size="big",
        plural=False,
        share_units=2,
        requires_referee=True,
        tags={"wind", "sky", "share"},
    ),
}

GIRL_NAMES = ["Mina", "Penny", "Hazel", "June", "Luna", "Ada"]
BOY_NAMES = ["Jasper", "Owen", "Finn", "Eli", "Theo", "Milo"]
REFEREE_NAMES = ["Ref", "Mister Whistle", "Aunt Bell", "Judge Bess"]
TRAITS = ["brave", "spunky", "stubborn", "cheerful", "rowdy", "lively"]


def prize_at_risk(move: SharingMove, prize: Prize) -> bool:
    return prize.requires_referee and "share" in move.tags


def select_move(prize: Prize, rng: random.Random) -> Optional[SharingMove]:
    choices = [m for m in SHARING_MOVES.values() if prize_at_risk(m, prize)]
    return rng.choice(choices) if choices else None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize_id, prize in PRIZES.items():
                if prize.requires_referee and act in {"kite", "banner", "balloon"}:
                    out.append((place, act, prize_id))
    return out


def explain_rejection(setting: Setting, prize: Prize) -> str:
    return (
        f"(No story: {prize.label} needs a real sharing conflict, but {setting.place} "
        f"does not support the right windy kind of contest for this tall-tale referee.)"
    )


@dataclass
class StoryParams:
    place: str
    prize: str
    name_a: str
    name_b: str
    gender_a: str
    gender_b: str
    referee: str
    trait_a: str
    trait_b: str
    seed: Optional[int] = None


class WorldState:
    pass


def _ensure_story_state(ent: Entity) -> None:
    ent.meters.setdefault("size", 0.0)
    ent.meters.setdefault("wear", 0.0)
    ent.memes.setdefault("joy", 0.0)
    ent.memes.setdefault("want", 0.0)
    ent.memes.setdefault("grumble", 0.0)
    ent.memes.setdefault("fairness", 0.0)
    ent.memes.setdefault("pride", 0.0)


def _rule_grumble(world: World) -> list[str]:
    out = []
    a = world.get("child_a")
    b = world.get("child_b")
    prize = world.get("prize")
    if a.memes["want"] >= THRESHOLD and b.memes["want"] >= THRESHOLD and prize.worn_by is None:
        sig = ("grumble",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["grumble"] += 1
            b.memes["grumble"] += 1
            out.append("The children grumbled so hard the wind had to listen.")
    return out


def _rule_fairness(world: World) -> list[str]:
    out = []
    referee = world.get("referee")
    if referee.memes["fairness"] >= THRESHOLD:
        sig = ("fair",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("The referee gave one sharp whistle and called for fair play.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_grumble, _rule_fairness):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, prize_cfg: Prize, move: SharingMove, params: StoryParams) -> World:
    world = World(setting)
    world.wind = 1.0 if "windy" in setting.weather or "breezy" in setting.weather else 0.3

    child_a = world.add(Entity(id="child_a", kind="character", type=params.gender_a, label=params.name_a))
    child_b = world.add(Entity(id="child_b", kind="character", type=params.gender_b, label=params.name_b))
    referee = world.add(Entity(id="referee", kind="character", type="referee", label=params.referee))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, plural=prize_cfg.plural))
    prize.owner = None
    prize.worn_by = None

    # Act 1
    world.say(
        f"On {setting.place}, where the wind went walking with a hat under its arm, "
        f"{child_a.label} and {child_b.label} found {prize_cfg.phrase}."
    )
    world.say(
        f"Each child wanted it, and each child wanted it first, which is how a small want can grow as tall as a barn."
    )
    child_a.memes["want"] += 1
    child_b.memes["want"] += 1
    referee.memes["fairness"] += 1

    # Act 2
    world.para()
    world.say(
        f"{child_a.label} held the prize tight, and {child_b.label} puffed up like a thunderhead."
    )
    propagate(world, narrate=True)
    world.say(
        f"Then {referee.label}, with a whistle bright as a star and a hat wide as a wagon wheel, stepped between them."
    )
    world.say(
        f'"Now hold on," {referee.pronoun("subject")} said. "A prize that big can make friends out of two hands if we {move.verb}."'
    )

    # Act 3
    world.para()
    child_a.memes["pride"] += 1
    child_b.memes["pride"] += 1
    world.say(
        f"The children blinked at one another, then tried {move.method}."
    )
    prize.worn_by = "child_a"
    prize.meters["wear"] += 1
    world.say(
        f"{move.reveal.capitalize()}, and the referee showed them how to keep the {prize.label} moving instead of fighting over it."
    )
    world.say(
        f"They settled it by sharing it {move.keyword}, and soon {move.settle}."
    )
    child_a.memes["joy"] += 1
    child_b.memes["joy"] += 1
    referee.memes["joy"] += 1
    referee.memes["fairness"] += 1

    world.facts.update(
        child_a=child_a,
        child_b=child_b,
        referee=referee,
        prize=prize,
        setting=setting,
        prize_cfg=prize_cfg,
        move=move,
        shared=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, ref, prize, move = f["child_a"], f["child_b"], f["referee"], f["prize_cfg"], f["move"]
    return [
        f'Write a tall-tale style story for a small child about "{f["prize"].label}" and a referee who helps two children share.',
        f"Tell a windy, playful story where {a.label} and {b.label} both want {prize.phrase}, but {ref.label} helps them {move.verb}.",
        f'Write a short sharing story that includes a referee, a giant prize, and the word "{move.keyword}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, ref, prize, move = f["child_a"], f["child_b"], f["referee"], f["prize_cfg"], f["move"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Where did {a.label} and {b.label} find the {prize.label}?",
            answer=f"They found it on {place}, where the wind was acting like it had a story to tell.",
        ),
        QAItem(
            question=f"Why did {a.label} and {b.label} start to squabble?",
            answer=f"They both wanted {prize.phrase}, and neither child wanted to be the second one to let go.",
        ),
        QAItem(
            question=f"Who helped the children share the {prize.label}?",
            answer=f"{ref.label} helped them share it with a whistle, a calm voice, and a fair plan.",
        ),
        QAItem(
            question=f"What did the referee tell them to do?",
            answer=f"The referee told them to {move.verb}, so the prize could keep moving and nobody would be left out.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the children sharing the {prize.label} and laughing together while the wind carried the joy upward.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    prize = f["prize_cfg"]
    out = [
        QAItem(
            question="What does a referee do?",
            answer="A referee watches a game or contest, helps keep things fair, and settles arguments so everyone can play safely.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use or enjoy something too, instead of keeping it all for yourself.",
        ),
    ]
    if "wind" in prize.tags:
        out.append(
            QAItem(
                question="What can wind do?",
                answer="Wind can push, lift, and carry light things like ribbons, kites, and leaves through the air.",
            )
        )
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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        parts = [f"kind={e.kind}", f"type={e.type}"]
        if e.label:
            parts.append(f"label={e.label}")
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id}: {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="courthouse_green", prize="kite", name_a="Mina", name_b="Jasper", gender_a="girl", gender_b="boy", referee="Ref", trait_a="brave", trait_b="stubborn"),
    StoryParams(place="fairground", prize="banner", name_a="Hazel", name_b="Owen", gender_a="girl", gender_b="boy", referee="Judge Bess", trait_a="cheerful", trait_b="rowdy"),
    StoryParams(place="river_bend", prize="balloon", name_a="June", name_b="Theo", gender_a="girl", gender_b="boy", referee="Aunt Bell", trait_a="lively", trait_b="spunky"),
]


ASP_RULES = r"""
prize_at_risk(Prize) :- prize(Prize), requires_referee(Prize).
valid_story(Place, Prize) :- setting(Place), affords(Place, Prize), prize_at_risk(Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.requires_referee:
            lines.append(asp.fact("requires_referee", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((p, prize) for p, prize in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale sharing storyworld with a referee.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
    ap.add_argument("--referee")
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
    place = args.place or rng.choice(list(SETTINGS))
    prize = args.prize or rng.choice(list(PRIZES))
    setting = SETTINGS[place]
    prize_cfg = PRIZES[prize]
    if prize_cfg.requires_referee and place not in SETTINGS:
        raise StoryError(explain_rejection(setting, prize_cfg))
    name_a = args.name_a or rng.choice(GIRL_NAMES if (args.gender_a or "girl") == "girl" else BOY_NAMES)
    name_b = args.name_b or rng.choice(BOY_NAMES if (args.gender_b or "boy") == "boy" else GIRL_NAMES)
    gender_a = args.gender_a or ("girl" if name_a in GIRL_NAMES else "boy")
    gender_b = args.gender_b or ("boy" if name_b in BOY_NAMES else "girl")
    referee = args.referee or rng.choice(REFEREE_NAMES)
    trait_a = rng.choice(TRAITS)
    trait_b = rng.choice(TRAITS)
    return StoryParams(place=place, prize=prize, name_a=name_a, name_b=name_b, gender_a=gender_a, gender_b=gender_b, referee=referee, trait_a=trait_a, trait_b=trait_b)


def generate(params: StoryParams) -> StorySample:
    move = select_move(PRIZES[params.prize], random.Random(params.seed or 0))
    if move is None:
        raise StoryError("No valid sharing move exists for this prize.")
    world = tell(SETTINGS[params.place], PRIZES[params.prize], move, params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, prize in combos:
            print(f"  {place:18} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name_a} and {p.name_b} at {p.place} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
