#!/usr/bin/env python3
"""
storyworlds/worlds/vanish_demonstrate_kingdom_reconciliation_kindness_heartwarming.py
=====================================================================================

A small heartwarming storyworld about a kingdom, a vanishing treasured thing,
and a kind demonstration that helps everyone reconcile.

Premise:
- In a tiny kingdom, a treasured object or helper goes missing.
- Someone is blamed or worried.
- A gentle act of kindness demonstrates the truth and helps repair feelings.
- The ending shows the kingdom calmer and closer than before.

This world is intentionally compact: fewer, stronger story variants with clear
state changes drive the prose.
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


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"queen", "woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"king", "man", "boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little kingdom"
    kind: str = "kingdom"


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    vanish_reason: str
    reveal_reason: str
    owner_kind: str = "kingdom"


@dataclass
class KindAct:
    id: str
    verb: str
    gerund: str
    demonstration: str
    effect: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    treasure: str
    act: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    ruler_name: str
    ruler_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting()

TREASURES = {
    "bell": Treasure(
        id="bell",
        label="silver bell",
        phrase="a bright silver bell",
        type="bell",
        vanish_reason="had vanished from the tower window",
        reveal_reason="was found tucked safely into a basket",
    ),
    "banner": Treasure(
        id="banner",
        label="festival banner",
        phrase="a soft blue festival banner",
        type="banner",
        vanish_reason="had vanished before the morning parade",
        reveal_reason="was found folded inside the bakery cart",
    ),
    "lantern": Treasure(
        id="lantern",
        label="lantern",
        phrase="a warm lantern for the palace path",
        type="lantern",
        vanish_reason="had vanished after dusk",
        reveal_reason="was found glowing near the rose gate",
    ),
}

ACTS = {
    "share_bread": KindAct(
        id="share_bread",
        verb="share warm bread",
        gerund="sharing warm bread",
        demonstration="brought a basket of fresh bread to the square",
        effect="the hungry villagers felt seen and soothed",
        keyword="kindness",
        tags={"kindness", "bread"},
    ),
    "fix_cloak": KindAct(
        id="fix_cloak",
        verb="fix a torn cloak",
        gerund="mending a torn cloak",
        demonstration="stitched the cloak carefully and gave it back with a smile",
        effect="the guard's pride softened into relief",
        keyword="kindness",
        tags={"kindness", "cloth"},
    ),
    "return_flower": KindAct(
        id="return_flower",
        verb="return a lost flower basket",
        gerund="returning a lost flower basket",
        demonstration="walked the basket back to its owner before anyone asked",
        effect="the gardener's worried face turned bright",
        keyword="reconciliation",
        tags={"reconciliation", "flowers"},
    ),
}

HERO_TYPES = ["girl", "boy"]
RULER_TYPES = ["queen", "king"]
HELPER_TYPES = ["girl", "boy", "woman", "man"]

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ada", "Tia", "Eli", "Ivy", "June"]
BOY_NAMES = ["Theo", "Finn", "Pip", "Noah", "Ben", "Owen", "Leo", "Max"]
RULER_NAMES = ["Queen Maren", "King Alden"]
HELPER_NAMES = ["Tessa", "Milo", "Rowan", "Pia", "Nico", "Lina"]

TRAITS = ["gentle", "curious", "brave", "patient", "soft-spoken", "cheerful"]

CURATED = [
    StoryParams(treasure="bell", act="share_bread", hero_name="Mina", hero_type="girl",
                helper_name="Tessa", helper_type="woman", ruler_name="Queen Maren", ruler_type="queen"),
    StoryParams(treasure="banner", act="fix_cloak", hero_name="Theo", hero_type="boy",
                helper_name="Milo", helper_type="boy", ruler_name="King Alden", ruler_type="king"),
    StoryParams(treasure="lantern", act="return_flower", hero_name="Nora", hero_type="girl",
                helper_name="Pia", helper_type="woman", ruler_name="Queen Maren", ruler_type="queen"),
]


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    world = World(SETTING)
    treasure = TREASURES[params.treasure]
    act = ACTS[params.act]

    ruler = world.add(Entity(id="ruler", kind="character", type=params.ruler_type, label=params.ruler_name))
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    item = world.add(Entity(
        id="treasure",
        kind="thing",
        type=treasure.type,
        label=treasure.label,
        phrase=treasure.phrase,
        owner=ruler.id,
        caretaker=ruler.id,
        meters={"missing": 0.0},
        memes={"worry": 0.0},
    ))

    world.facts.update(ruler=ruler, hero=hero, helper=helper, treasure=item, treasure_cfg=treasure, act=act)
    return world


def vanish(world: World) -> None:
    treasure: Entity = world.facts["treasure"]
    treasure.meters["missing"] = 1.0
    ruler: Entity = world.facts["ruler"]
    ruler.memes["worry"] = 1.0
    world.say(
        f"In {world.setting.place}, {treasure.label} had vanished from where everyone expected to see it."
    )
    world.say(
        f"{ruler.label} looked around the room and felt a small ache of worry because {treasure.phrase} was missing."
    )


def suspect(world: World) -> None:
    hero: Entity = world.facts["hero"]
    ruler: Entity = world.facts["ruler"]
    hero.memes["hurt"] = 1.0
    world.say(
        f"When the missing thing was noticed, some voices grew quiet, and {hero.label} thought the kingdom might be upset with {hero.pronoun('object')}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wished everyone could understand before the worry turned into blame."
    )


def demonstrate_kindness(world: World) -> None:
    helper: Entity = world.facts["helper"]
    act: KindAct = world.facts["act"]
    ruler: Entity = world.facts["ruler"]
    hero: Entity = world.facts["hero"]

    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1.0
    helper.meters["help"] = helper.meters.get("help", 0.0) + 1.0
    world.say(
        f"Then {helper.label} chose to {act.verb}, and {helper.pronoun('subject')} {act.demonstration}."
    )
    world.say(
        f"That small choice {act.effect}, and {hero.label} saw that kindness could speak more clearly than fear."
    )
    ruler.memes["hope"] = ruler.memes.get("hope", 0.0) + 1.0


def reconciliation(world: World) -> None:
    treasure: Entity = world.facts["treasure"]
    ruler: Entity = world.facts["ruler"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    treasure_cfg: Treasure = world.facts["treasure_cfg"]

    treasure.meters["missing"] = 0.0
    ruler.memes["worry"] = 0.0
    ruler.memes["reconciled"] = 1.0
    hero.memes["hurt"] = 0.0
    hero.memes["relief"] = 1.0

    world.say(
        f"Before long, {treasure.label} was found again: {treasure_cfg.reveal_reason}."
    )
    world.say(
        f"{ruler.label} smiled at {hero.label} and thanked {helper.label} for helping the whole kingdom breathe easier."
    )
    world.say(
        f"By the end, worry had faded, and the kingdom felt warm again because everyone had chosen reconciliation instead of blame."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    world.say(
        f"In the little kingdom, {world.facts['hero'].label} and {world.facts['helper'].label} noticed that something important was missing."
    )
    vanish(world)
    world.para()
    suspect(world)
    world.say(
        f"The missing {world.facts['treasure'].label} had {TREASURES[params.treasure].vanish_reason}."
    )
    world.para()
    demonstrate_kindness(world)
    reconciliation(world)
    return world


# ---------------------------------------------------------------------------
# Q&A and narration
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    treasure_cfg: Treasure = f["treasure_cfg"]
    act: KindAct = f["act"]
    return [
        f'Write a heartwarming story set in a kingdom where a {treasure_cfg.label} can vanish and kindness helps everyone reconcile.',
        f"Tell a gentle tale about {f['hero'].label} and {f['helper'].label} in the kingdom, using the words vanish, demonstrate, and reconciliation.",
        f"Write a child-friendly story where kindness demonstrates what really happened to the missing {treasure_cfg.label}.",
        f"Create a short story about a kingdom that feels sad when {treasure_cfg.label} disappears, then becomes warm again through {act.keyword}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    treasure_cfg: Treasure = f["treasure_cfg"]
    act: KindAct = f["act"]
    ruler: Entity = f["ruler"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"What vanished in the kingdom?",
            answer=f"The {treasure_cfg.label} vanished, and that made {ruler.label} worry.",
        ),
        QAItem(
            question=f"Who helped demonstrate kindness?",
            answer=f"{helper.label} helped demonstrate kindness by {act.gerund}.",
        ),
        QAItem(
            question=f"How did {hero.label} feel at the end?",
            answer=f"{hero.label} felt relief and gladness because the kingdom ended in reconciliation.",
        ),
        QAItem(
            question=f"What changed when the missing item was found again?",
            answer="The worry faded, blame softened, and everyone felt closer and calmer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone chooses to help, share, or speak gently so another person feels safe and cared for.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop feeling apart and start making peace again after a problem or misunderstanding.",
        ),
        QAItem(
            question="What is a kingdom?",
            answer="A kingdom is a place where a king or queen rules, and people live together there.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid_story/3.
#show valid_combo/2.

valid_story(Treasure, Act, Mood) :- treasure(Treasure), kind_act(Act), mood(Mood).
valid_combo(Treasure, Act) :- treasure(Treasure), kind_act(Act).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in TREASURES.values():
        lines.append(asp.fact("treasure", t.id))
    for a in ACTS.values():
        lines.append(asp.fact("kind_act", a.id))
    lines.append(asp.fact("mood", "heartwarming"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_combo/2.\n#show valid_story/3.")
    model = asp.one_model(program)
    combos = sorted(set(asp.atoms(model, "valid_combo")))
    stories = sorted(set(asp.atoms(model, "valid_story")))
    py_combos = sorted((t.id, a.id) for t in TREASURES.values() for a in ACTS.values())
    py_stories = sorted((t.id, a.id, "heartwarming") for t in TREASURES.values() for a in ACTS.values())
    if combos == py_combos and stories == py_stories:
        print(f"OK: ASP parity verified ({len(combos)} combos).")
        return 0
    print("MISMATCH between ASP and Python registries.")
    if combos != py_combos:
        print("  combos ASP:", combos)
        print("  combos PY :", py_combos)
    if stories != py_stories:
        print("  stories ASP:", stories)
        print("  stories PY :", py_stories)
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming kingdom storyworld about vanishing, kindness, and reconciliation.")
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--ruler-name", choices=RULER_NAMES)
    ap.add_argument("--ruler-type", choices=RULER_TYPES)
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
    treasure = args.treasure or rng.choice(list(TREASURES))
    act = args.act or rng.choice(list(ACTS))

    if args.hero_type is None:
        hero_type = rng.choice(HERO_TYPES)
    else:
        hero_type = args.hero_type
    if args.ruler_type is None:
        ruler_type = rng.choice(RULER_TYPES)
    else:
        ruler_type = args.ruler_type

    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    ruler_name = args.ruler_name or rng.choice(RULER_NAMES)

    if args.treasure and args.act:
        pass

    return StoryParams(
        treasure=treasure,
        act=act,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        ruler_name=ruler_name,
        ruler_type=ruler_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            parts = []
            if meters:
                parts.append(f"meters={meters}")
            if memes:
                parts.append(f"memes={memes}")
            print(f"{e.id}: {e.type} {e.label} {' '.join(parts)}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3.\n#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3.\n#show valid_combo/2."))
        combos = sorted(set(asp.atoms(model, "valid_combo")))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible combos")
        for t, a in combos:
            moods = [m for tt, aa, m in stories if tt == t and aa == a]
            print(f"  {t:10} {a:14}  [{', '.join(sorted(moods))}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.treasure} / {p.act}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
