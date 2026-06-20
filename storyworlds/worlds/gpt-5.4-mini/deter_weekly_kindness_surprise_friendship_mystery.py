#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/deter_weekly_kindness_surprise_friendship_mystery.py
====================================================================================

A small standalone storyworld about a weekly kindness mystery: two friends notice
a repeating surprise, follow clues, and learn that a thoughtful person has been
leaving kindness on purpose.

This world is built for child-facing mystery stories with a gentle turn:
- a weekly routine creates a pattern,
- something puzzling goes missing or appears,
- friendship and kindness help the children investigate,
- the ending reveals a warm surprise and a concrete change in the world.

The required seed words are woven in:
- deter
- weekly

The required features are central to the premise:
- Kindness
- Surprise
- Friendship

The tone stays close to a mystery, but the resolution is safe and warm.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
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
class Setting:
    id: str
    place: str
    detail: str
    vibe: str
    clue_spot: str
    weekly_routine: str


@dataclass
class Mystery:
    id: str
    source: str
    pattern: str
    missing: str
    found_where: str
    clue: str
    verb: str
    deter_word: str = "deter"
    weekly_word: str = "weekly"


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    effect: str
    kind: str = "kindness"


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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "library": Setting(
        "library",
        "the little library",
        "Shelves leaned high, and a round reading rug sat by the window.",
        "quiet",
        "the reading nook",
        "Every weekly visit ended with a stamp in a tiny card.",
    ),
    "garden": Setting(
        "garden",
        "the side garden",
        "A stone path curved past the flowers and the old mailbox.",
        "soft",
        "the mailbox corner",
        "Every weekly visit ended with a check of the seed row.",
    ),
    "hall": Setting(
        "hall",
        "the hallway",
        "Pictures hung straight, and a blue bench waited under the mirror.",
        "still",
        "the blue bench",
        "Every weekly visit ended with a note on the board.",
    ),
}

MYSTERIES = {
    "notes": Mystery(
        "notes",
        source="anonymous kindness notes",
        pattern="a new note appeared every week",
        missing="the note",
        found_where="inside the little basket",
        clue="a ribbon tied in a neat bow",
        verb="leave",
    ),
    "cookies": Mystery(
        "cookies",
        source="cookie crumbs",
        pattern="a small cookie kept showing up every week",
        missing="the cookie",
        found_where="on the windowsill",
        clue="a crumb trail near the door",
        verb="leave",
    ),
    "flowers": Mystery(
        "flowers",
        source="tiny flowers",
        pattern="a tiny flower kept appearing every week",
        missing="the flower",
        found_where="in a jar near the sign",
        clue="a bit of green ribbon",
        verb="place",
    ),
}

SURPRISES = {
    "card": Surprise("card", "a bright card", "a bright card with a smiley sun", "made the room feel warm"),
    "bookmark": Surprise("bookmark", "a paper bookmark", "a paper bookmark with stars", "made reading feel special"),
    "cookie": Surprise("cookie", "a small cookie", "a small cookie wrapped in a napkin", "made the children grin"),
    "flower": Surprise("flower", "a tiny flower", "a tiny flower in a cup", "made the day feel gentle"),
}

NAMES = ["Mia", "Noah", "Ava", "Leo", "Nora", "Eli", "Maya", "Finn", "Luna", "Theo"]
TRAITS = ["curious", "careful", "kind", "bright", "patient", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, m, u) for s in SETTINGS for m in MYSTERIES for u in SURPRISES]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    surprise: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle mystery about weekly kindness, surprise, and friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--surprise", choices=SURPRISES)
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in NAMES if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, surprise = rng.choice(sorted(combos))
    g1 = rng.choice(["girl", "boy"])
    g2 = "boy" if g1 == "girl" else "girl"
    c1 = _pick_name(rng, g1)
    c2 = _pick_name(rng, g2, avoid=c1)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, mystery, surprise, c1, g1, c2, g2, parent, trait)


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["kindness"] >= THRESHOLD and not e.meters["shared"]:
            sig = ("shared", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["shared"] = 1
            out.append("__shared__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for s in _r_kindness(world):
            changed = True
            if s != "__shared__":
                produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, mystery: Mystery, surprise: Surprise, a_name: str, a_gender: str,
         b_name: str, b_gender: str, parent_type: str, trait: str) -> World:
    world = World()
    a = world.add(Entity(id=a_name, kind="character", type=a_gender, role="observer", traits=["curious", trait]))
    b = world.add(Entity(id=b_name, kind="character", type=b_gender, role="helper", traits=["kind", "calm"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    clue = world.add(Entity(id="clue", label=mystery.clue))
    gift = world.add(Entity(id="gift", label=surprise.label, attrs={"kind": surprise.kind}))

    a.memes["curiosity"] += 1
    b.memes["friendship"] += 1
    world.say(
        f"On a quiet {setting.vibe} afternoon, {a.id} and {b.id} went to {setting.place}. "
        f"{setting.detail} {setting.weekly_routine}"
    )
    world.say(
        f"Every {mystery.weekly_word}, something strange happened: {mystery.pattern}. "
        f"{a.id} frowned. {b.id} smiled and said it might be a clue."
    )
    world.para()
    world.say(
        f'The children looked where the surprise should be, but {mystery.missing} was not there. '
        f"Only {mystery.clue} stayed behind."
    )
    a.memes["worry"] += 1
    world.say(
        f'"Someone is trying to {mystery.verb} something nice," {b.id} whispered. '
        f'"Maybe we should not {mystery.deter_word} the surprise until we know who it helps."'
    )
    world.say(
        f"{a.id} nodded. Their friendship made the mystery feel safe instead of scary."
    )

    world.para()
    a.memes["kindness"] += 1
    b.memes["kindness"] += 1
    world.say(
        f"They followed the clue to {mystery.found_where}. There they found {surprise.phrase}. "
        f"It was not a trick at all -- it was a weekly kindness surprise."
    )
    world.say(
        f"{parent.label_word.capitalize()} came over and laughed softly. "
        f'"I wanted you to find it together," {parent.pronoun()} said.'
    )
    world.say(
        f"The surprise {surprise.effect}, and the children felt proud that they had not rushed to {mystery.deter_word} it away."
    )
    world.para()
    world.say(
        f"From then on, {a.id} and {b.id} left a small kindness of their own each week. "
        f"This time the mystery had a happy answer, and friendship was the best clue of all."
    )

    world.facts.update(
        setting=setting, mystery=mystery, surprise=surprise,
        child1=a, child2=b, parent=parent, clue=clue, gift=gift,
        weekly=True, kindness=True, surprise_found=True
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mystery story for a child that includes the words "deter" and "weekly" and ends with a kindness surprise.',
        f"Tell a gentle friendship mystery set at {f['setting'].place} where a repeating weekly clue leads to a surprise.",
        f"Write a short story where two friends solve a small mystery by being kind, curious, and brave.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = f["child1"], f["child2"]
    mystery: Mystery = f["mystery"]
    surprise: Surprise = f["surprise"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question="Who are the story about?",
            answer=f"The story is about {a.id} and {b.id}, two friends who solve a small mystery together. Their friendship helps them stay calm while they look for clues."
        ),
        QAItem(
            question="What was the mystery?",
            answer=f"Every weekly visit, something kind appeared, and the children could not tell who left it. The clue led them to {mystery.found_where}, where they found the surprise."
        ),
        QAItem(
            question="Why did they not try to deter the surprise right away?",
            answer=f"They realized the surprise was a kindness, not something bad. Once they saw {mystery.clue}, they knew they should follow the clue first and understand the mystery."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with a warm surprise and a new weekly kindness from the children. {surprise.phrase} made the place feel happier, and the mystery turned into friendship."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    s: Setting = f["setting"]
    m: Mystery = f["mystery"]
    u: Surprise = f["surprise"]
    return [
        QAItem("What is a mystery?", "A mystery is something puzzling that makes you ask questions and look for clues. In a good mystery, the answer comes from noticing details."),
        QAItem("What does weekly mean?", "Weekly means once every week. If something happens weekly, it comes back again and again on a regular schedule."),
        QAItem("What is kindness?", "Kindness means doing something caring or helpful for someone else. A kind act can make another person feel safe and happy."),
        QAItem("What is friendship?", "Friendship is when people care about each other and help each other. Friends often feel braver when they work together."),
        QAItem("What is a surprise?", "A surprise is something unexpected. A good surprise can make people smile when it is safe and thoughtful."),
        QAItem("What is a clue?", "A clue is a small detail that helps solve a mystery. Clues can be objects, notes, patterns, or little signs."),
        QAItem("Why do clues matter in a mystery?", "Clues matter because they help you figure out what is happening. When you gather enough clues, the mystery becomes clear."),
        QAItem("What does it mean to deter something?", "To deter something means to stop it from happening or to make someone choose not to do it. In a story, a kind person can deter trouble or a bad idea."),
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("library", "notes", "bookmark", "Mia", "girl", "Noah", "boy", "mother", "curious"),
    StoryParams("garden", "cookies", "flower", "Ava", "girl", "Leo", "boy", "father", "kind"),
]


ASP_RULES = r"""
valid(S, M, U) :- setting(S), mystery(M), surprise(U).
weekly_kindness(M) :- mystery(M).
kind_story(U) :- surprise(U).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
        lines.append(asp.fact("weekly_kindness", m))
    for u in SURPRISES:
        lines.append(asp.fact("surprise", u))
        lines.append(asp.fact("kind_story", u))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo generation.")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_rejection() -> str:
    return "(No story: this world only supports gentle mystery combinations.)"


def explain_response() -> str:
    return "(No story: invalid request.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, surprise = rng.choice(sorted(combos))
    g1 = rng.choice(["girl", "boy"])
    g2 = "boy" if g1 == "girl" else "girl"
    child1 = _pick_name(rng, g1)
    child2 = _pick_name(rng, g2, avoid=child1)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, mystery, surprise, child1, g1, child2, g2, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        SURPRISES[params.surprise],
        params.child1, params.child1_gender,
        params.child2, params.child2_gender,
        params.parent,
        params.trait,
    )
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child1} & {p.child2}: {p.setting} / {p.mystery} / {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
