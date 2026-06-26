#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/jabber_apartment_courtyard_rhyme_foreshadowing_fable.py
===========================================================================================================

A tiny fable world in an apartment courtyard, built around jabbering, rhyme,
and foreshadowing.

Premise:
- In a small courtyard between apartment buildings, a chatty sparrow keeps
  jabbering.
- The sparrow wants a bright red berry crown from a railing planter.
- A careful old turtle warns that loud jabbering will wake the sleeping cat
  on the windowsill.
- The sparrow ignores the warning, then learns that a quieter rhyme can win
  help instead of trouble.

The story is simulated from state:
- loudness meters can wake sleepers,
- trust memes grow when characters speak kindly,
- fear memes rise when the cat is startled,
- foreshadowing plants a warning sign in the world before the turn,
- rhyme is used as a concrete method to calm the courtyard.

This world intentionally stays small and fable-like.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World data model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    perched_on: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "cat"}
        male = {"boy", "father", "man", "sparrow", "turtle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the apartment courtyard"
    affords: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    region: str = "railing"
    shine: str = "bright"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting(place="the apartment courtyard", affords={"jabber", "rhyme"})

TREASURES = {
    "berries": Treasure(
        id="berries",
        label="berry crown",
        phrase="a tiny crown of red berries",
        region="railing",
        shine="bright",
    ),
}

# Simple living cast.
CHARACTER_ORDER = ["sparrow", "turtle", "cat"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A tale is valid when the courtyard supports the chosen action and the
% treasure is worth warning about.
at_risk(T) :- treasure(T), shiny(T), near_rail(T).
valid_story :- affords(courtyard, jabber), affords(courtyard, rhyme), at_risk(berries).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("setting", "courtyard"))
    for a in sorted(SETTING.affords):
        lines.append(asp.fact("affords", "courtyard", a))
    lines.append(asp.fact("treasure", "berries"))
    lines.append(asp.fact("shiny", "berries"))
    lines.append(asp.fact("near_rail", "berries"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/0."))
    has = any(sym.name == "valid_story" for sym in model)
    py = python_reasonable()
    if bool(has) == bool(py):
        print("OK: ASP and Python gates agree.")
        return 0
    print("MISMATCH: ASP and Python gates disagree.")
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def python_reasonable() -> bool:
    return "jabber" in SETTING.affords and "rhyme" in SETTING.affords


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def _bump(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _bump_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def predict_disruption(world: World, speaker: Entity, cat: Entity, treasure: Treasure) -> dict:
    sim = world.copy()
    do_jabber(sim, sim.get(speaker.id), narrate=False)
    return {
        "wake_cat": sim.get(cat.id).memes.get("startled", 0.0) >= THRESHOLD,
        "noise": sim.get(speaker.id).meters.get("noise", 0.0),
        "lost_trust": sim.get(speaker.id).memes.get("trust", 0.0) < THRESHOLD,
        "treasure_safe": treasure.id in sim.entities,
    }


def do_jabber(world: World, sparrow: Entity, narrate: bool = True) -> None:
    _bump(sparrow, "noise", 1.0)
    _bump_meme(sparrow, "pride", 1.0)
    world.facts["jabbered"] = True
    if narrate:
        world.say(
            f'The sparrow kept jabbering, "Quick, quick, bright little berries!" '
            f"Her words bounced off the courtyard bricks."
        )


def foreshadow(world: World, turtle: Entity, cat: Entity, treasure: Treasure) -> None:
    _bump_meme(turtle, "care", 1.0)
    world.facts["warning"] = "The turtle saw the cat stirring near the window."
    world.say(
        f'The old turtle squinted at the windowsill and said, '
        f'"Soft feet, soft beat; loud chatter wakes the one who sleeps."'
    )
    world.say(
        f"He pointed at the {treasure.label} and nodded toward the cat, "
        f"who twitched one whisker in the sun."
    )


def ignore_warning(world: World, sparrow: Entity) -> None:
    _bump_meme(sparrow, "stubborn", 1.0)
    world.say(
        f'The sparrow puffed her chest. "I can jabber and still be grand!" '
        f"she said, and she hopped closer to the railing."
    )


def wake_cat_if_needed(world: World, cat: Entity, sparrow: Entity) -> None:
    if sparrow.meters.get("noise", 0.0) >= THRESHOLD:
        _bump_meme(cat, "startled", 1.0)
        _bump_meme(cat, "annoyed", 1.0)
        world.say(
            f"The cat's eyes opened wide. One hissed breath filled the courtyard, "
            f"and the sparrow learned how big a small mistake can sound."
        )


def rhyme_fix(world: World, sparrow: Entity, turtle: Entity, cat: Entity, treasure: Treasure) -> None:
    _bump_meme(sparrow, "humble", 1.0)
    _bump_meme(sparrow, "trust", 1.0)
    _bump_meme(turtle, "trust", 1.0)
    _bump_meme(cat, "curious", 1.0)
    world.say(
        f'The sparrow tried again, but this time she sang, '
        f'"Quiet feet, neat feet, berry treats taste sweet."'
    )
    world.say(
        f"The turtle tapped the rhythm on a stone. The cat listened instead of hissing, "
        f"and the berry crown stayed safe on the railing."
    )


def resolve(world: World, sparrow: Entity, turtle: Entity, cat: Entity, treasure: Treasure) -> None:
    _bump_meme(sparrow, "joy", 1.0)
    _bump_meme(sparrow, "trust", 1.0)
    _bump_meme(cat, "calm", 1.0)
    world.say(
        f"In the end, the sparrow carried the berry crown down to the courtyard bench, "
        f"where all three could share the shade."
    )
    world.say(
        f"The sparrow had learned that a jabber can scatter a day, but a rhyme can gather one."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Sparrow"
    animal: str = "sparrow"


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    sparrow = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="sparrow",
            label="the sparrow",
            traits=["chatty", "quick"],
        )
    )
    turtle = world.add(
        Entity(
            id="Turtle",
            kind="character",
            type="turtle",
            label="the turtle",
            traits=["wise", "slow"],
        )
    )
    cat = world.add(
        Entity(
            id="Cat",
            kind="character",
            type="cat",
            label="the cat",
            traits=["sleepy", "stern"],
        )
    )
    treasure = TREASURES["berries"]

    world.facts.update(
        sparrow=sparrow,
        turtle=turtle,
        cat=cat,
        treasure=treasure,
        place=SETTING.place,
    )

    world.say(
        f"In {SETTING.place}, a little sparrow loved to jabber from sunrise to supper."
    )
    world.say(
        f"She liked the {treasure.label}, because its {treasure.shine} color looked like a song on the railing."
    )

    world.para()
    foreshadow(world, turtle, cat, treasure)
    do_jabber(world, sparrow)
    ignore_warning(world, sparrow)
    wake_cat_if_needed(world, cat, sparrow)

    world.para()
    world.say(
        f"The sparrow saw the trouble she had stirred, and her bright chatter grew small."
    )
    rhyme_fix(world, sparrow, turtle, cat, treasure)
    resolve(world, sparrow, turtle, cat, treasure)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short fable set in an apartment courtyard about a sparrow who jabbers too much, with a warning that comes true.',
        'Tell a child-friendly story in rhyme and foreshadowing where a chatty bird learns to speak more carefully.',
        'Write a small moral tale in an apartment courtyard: one noisy mistake, one wise warning, and one gentle rhyme that fixes it.',
    ]


def story_qa(world: World) -> list[QAItem]:
    sparrow = world.facts["sparrow"]
    turtle = world.facts["turtle"]
    cat = world.facts["cat"]
    treasure = world.facts["treasure"]
    return [
        QAItem(
            question="Who kept jabbering in the apartment courtyard?",
            answer=f"The sparrow kept jabbering in the apartment courtyard.",
        ),
        QAItem(
            question="What did the old turtle warn might happen?",
            answer="The turtle warned that loud chatter could wake the sleeping cat.",
        ),
        QAItem(
            question="What shiny thing did the sparrow want near the railing?",
            answer=f"The sparrow wanted the {treasure.label} near the railing.",
        ),
        QAItem(
            question="How did the sparrow solve the problem at the end?",
            answer="She stopped jabbering so loudly and used a gentle rhyme, which calmed the courtyard and kept the treasure safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a courtyard?",
            answer="A courtyard is an open space inside or between buildings where people and animals can gather.",
        ),
        QAItem(
            question="What is jabbering?",
            answer="Jabbering is talking very quickly and noisily, with lots of words.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the ends, which can make a saying or song easy to remember.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a hint that something important may happen later in the story.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny fable world in an apartment courtyard, with jabber, rhyme, and foreshadowing."
    )
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(seed=args.seed, name=rng.choice(["Pip", "Juno", "Nim", "Tavi"]))


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
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
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/0."))
        print("valid_story" if any(sym.name == "valid_story" for sym in model) else "no valid_story")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        params = StoryParams(seed=base_seed, name="Pip")
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 10):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            i += 1
            sample = generate(p)
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
        header = f"### sample {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
