#!/usr/bin/env python3
"""
A tiny comedy storyworld about a child, a soggy measly snack, and a goofy
repetition-based fix.

Premise:
- A child loves a treat, but the treat is measly and gets soggy.
- The child keeps trying to make the snack feel grand.
- A helper offers a silly but effective solution.

The world model tracks:
- physical meters: soggy, crisp, full, messy
- emotional memes: joy, annoyance, pride, laughter, worry

The prose is driven by state changes, not a frozen template.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World primitives
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    region: str
    mess_sensitive: str  # soggy, smashed, etc.
    comedy_hook: str


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    protects_from: set[str]
    boosts: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.events = []
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"snack"}),
    "porch": Setting(place="the porch", indoor=False, affords={"snack"}),
    "picnic": Setting(place="the picnic table", indoor=False, affords={"snack"}),
}

SNACKS = {
    "cracker": Snack(
        id="cracker",
        label="cracker",
        phrase="a tiny cracker",
        region="mouth",
        mess_sensitive="soggy",
        comedy_hook="it was so small it looked like a polite apology",
    ),
    "cookie": Snack(
        id="cookie",
        label="cookie",
        phrase="a measly cookie",
        region="mouth",
        mess_sensitive="soggy",
        comedy_hook="it was measly enough to make a mouse sigh",
    ),
    "wafer": Snack(
        id="wafer",
        label="wafer",
        phrase="a flimsy wafer",
        region="mouth",
        mess_sensitive="soggy",
        comedy_hook="it was thin enough to wave back at you",
    ),
}

FIXES = {
    "plate": Fix(
        id="plate",
        label="a shiny plate",
        prep="put the snack on a shiny plate",
        tail="put the snack on a shiny plate and held it high",
        protects_from={"soggy"},
        boosts="pride",
    ),
    "napkin": Fix(
        id="napkin",
        label="a folded napkin",
        prep="wrap the snack in a folded napkin",
        tail="wrapped the snack in a folded napkin and gave it a little hat",
        protects_from={"soggy"},
        boosts="laughter",
    ),
    "umbrella": Fix(
        id="umbrella",
        label="a tiny umbrella",
        prep="open a tiny umbrella over the snack",
        tail="opened a tiny umbrella over the snack like it was famous",
        protects_from={"soggy"},
        boosts="joy",
    ),
}

NAMES = ["Mila", "Noah", "Ivy", "Leo", "Nina", "Owen"]
HUMOR_BEATS = [
    "The snack looked serious for one second, and then it looked sillier than before.",
    "Every time they fixed one thing, the snack found a new tiny problem to be dramatic about.",
    "The snack stayed so small that it seemed to be trying not to take up space.",
]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    snack: str
    name: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Logic
# ---------------------------------------------------------------------------
def snack_at_risk(snack: Snack) -> bool:
    return snack.mess_sensitive == "soggy"


def choose_fix(snack: Snack, setting: Setting) -> Optional[Fix]:
    if not snack_at_risk(snack):
        return None
    for fix in [FIXES["plate"], FIXES["napkin"], FIXES["umbrella"]]:
        if "soggy" in fix.protects_from and setting.indoor:
            return fix
        if "soggy" in fix.protects_from:
            return fix
    return None


def tell(setting: Setting, snack_def: Snack, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type="child", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="adult", label=helper_name))
    snack = world.add(Entity(
        id="snack",
        kind="thing",
        type="snack",
        label=snack_def.label,
        phrase=snack_def.phrase,
        owner=child.id,
        caretaker=helper.id,
        meters={"soggy": 0.0, "crisp": 1.0, "messy": 0.0},
        memes={"pride": 0.0},
    ))

    world.say(f"{child.id} found {snack.phrase} at {setting.place}.")
    world.say(f"It was {snack_def.comedy_hook}.")
    world.say(f"{child.id} wanted to make it feel grand anyway.")

    # Repetition beat 1
    world.say(f"{child.id} tried to nibble it carefully, but a little dampness sneaked in.")
    snack.meters["soggy"] += 1.0
    snack.meters["crisp"] -= 0.5
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0

    # Repetition beat 2
    world.say(f"Then {child.id} tried again, just in case the snack had changed its mind.")
    snack.meters["soggy"] += 1.0
    snack.meters["messy"] += 0.5
    child.memes["annoyance"] = child.memes.get("annoyance", 0.0) + 1.0

    # Repetition beat 3
    world.say(f"{child.id} tried one more time, and the snack only got more soggy and more measly.")
    snack.meters["soggy"] += 1.0
    snack.meters["crisp"] = max(0.0, snack.meters["crisp"] - 0.5)
    child.memes["laughter"] = child.memes.get("laughter", 0.0) + 1.0

    fix = choose_fix(snack_def, setting)
    if fix is None:
        raise StoryError("No sensible comic fix exists for this snack and setting.")

    fixed = world.add(Entity(
        id=fix.id,
        kind="thing",
        type="fix",
        label=fix.label,
        owner=helper.id,
    ))

    world.say(f"{helper.id} laughed and said, 'Let's {fix.prep}.'")
    fixed.worn_by = snack.id  # a playful fiction: the fix is now with the snack
    snack.meters["soggy"] = 0.0
    snack.meters["crisp"] = 1.0
    snack.memes["pride"] = 1.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    helper.memes["laughter"] = helper.memes.get("laughter", 0.0) + 1.0

    world.say(f"{fix.tail}.")
    world.say(f"At last, {child.id} took a bite and grinned instead of grimacing.")
    world.say(f"The snack was still measly, but now it was neatly saved, and everyone laughed.")

    world.facts.update(
        child=child,
        helper=helper,
        snack=snack,
        snack_def=snack_def,
        fix=fix,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short comedy story for children about {f['child'].id}, a {f['snack_def'].phrase}, and a silly fix.",
        f"Tell a repetitive, funny story where a snack gets soggy, a helper laughs, and the child still gets a happy ending.",
        f"Write a tiny comic tale set at {f['setting'].place} with the words 'soggy' and 'measly' in it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, snack, fix = f["child"], f["helper"], f["snack"], f["fix"]
    return [
        QAItem(
            question=f"What did {child.id} find at {f['setting'].place}?",
            answer=f"{child.id} found {snack.phrase}. It was so small and funny-looking that it seemed almost measly.",
        ),
        QAItem(
            question=f"Why did {child.id} keep reacting to the snack three times?",
            answer=f"{child.id} kept trying again because the snack looked disappointing, but each try made it soggier and sillier.",
        ),
        QAItem(
            question=f"How did {helper.id} help make the snack better?",
            answer=f"{helper.id} laughed and used {fix.label} to protect the snack from getting soggier, which turned the mess into a funny success.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"By the end, the snack was no longer soggy, {child.id} was grinning, and everyone was laughing together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does soggy mean?",
            answer="Soggy means wet and soft in an unhelpful way, like bread that has been left in water too long.",
        ),
        QAItem(
            question="What does measly mean?",
            answer="Measly means very small or disappointing, like a treat that is too tiny to feel like much of a reward.",
        ),
        QAItem(
            question="Why can repetition be funny in a comedy story?",
            answer="Repetition can be funny because the same problem happens again and again, but each time it gets a little stranger or sillier.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A snack is at risk when it is soggy-sensitive.
at_risk(S) :- snack(S), sensitive(S, soggy).

% A fix is compatible when it protects from soggy.
compatible(F, S) :- fix(F), snack(S), at_risk(S), protects(F, soggy).

% A story is valid when there is at least one compatible fix.
valid_story(Place, Snack, Fix) :- setting(Place), snack(Snack), compatible(Fix, Snack), hosted(Place, Snack).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
            lines.append(asp.fact("hosted", sid, "snack"))
    for nid, n in SNACKS.items():
        lines.append(asp.fact("snack", nid))
        lines.append(asp.fact("sensitive", nid, n.mess_sensitive))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for p in sorted(f.protects_from):
            lines.append(asp.fact("protects", fid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = valid_combos()
    ap = asp_valid_stories()
    py_set = set(py)
    ap_set = set(ap)
    if py_set == ap_set:
        print(f"OK: ASP and Python agree on {len(py_set)} valid story shapes.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(py_set - ap_set))
    print("only in ASP:", sorted(ap_set - py_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for snack_id, snack in SNACKS.items():
            if not snack_at_risk(snack):
                continue
            for fix_id, fix in FIXES.items():
                if "soggy" in fix.protects_from and "snack" in setting.affords:
                    out.append((place, snack_id, fix_id))
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a soggy measly snack.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--name")
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
    choices = valid_combos()
    if args.place:
        choices = [c for c in choices if c[0] == args.place]
    if args.snack:
        choices = [c for c in choices if c[1] == args.snack]
    if not choices:
        raise StoryError("No valid comic story matches the given options.")
    place, snack_id, _fix = rng.choice(sorted(choices))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != name])
    return StoryParams(place=place, snack=snack_id, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], SNACKS[params.snack], params.name, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} valid story shapes:")
        for item in stories:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, snack_id, _fix in valid_combos():
            params = StoryParams(place=place, snack=snack_id, name="Mila", helper="Noah")
            samples.append(generate(params))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
