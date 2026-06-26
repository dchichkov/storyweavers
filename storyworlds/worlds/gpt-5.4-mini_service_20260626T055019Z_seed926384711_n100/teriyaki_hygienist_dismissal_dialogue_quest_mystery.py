#!/usr/bin/env python3
"""
storyworlds/worlds/teriyaki_hygienist_dismissal_dialogue_quest_mystery.py
==========================================================================

A small mystery storyworld about a hygienist, a teriyaki stain, and a sudden
dismissal that launches a dialogue-driven quest.

The story premise:
- A child notices something odd at a clinic.
- A hygienist is blamed for a mess involving teriyaki.
- A dismissal removes the hygienist from the room.
- Through dialogue and a short quest, the child learns what really happened.

The simulation keeps track of physical state (meters) and emotional state
(memes) and narrates from those changes.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "hygienist"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def subject_name(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    atmosphere: str
    clue: str


@dataclass
class Quest:
    target: str
    lead: str
    clue_item: str
    resolution: str


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    hygienist_name: str
    reason: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.ended: bool = False

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


SETTINGS = {
    "clinic": Setting(
        place="the small clinic",
        atmosphere="quiet and bright",
        clue="a faint smell of teriyaki by the sink",
    ),
    "hallway": Setting(
        place="the school hallway",
        atmosphere="still and echoing",
        clue="sticky footprints near the bulletin board",
    ),
    "cafeteria": Setting(
        place="the cafeteria",
        atmosphere="busy and warm",
        clue="a tipped tray and a shining spill",
    ),
}

REASONS = {
    "accident": "an accident",
    "coverup": "a cover-up",
    "mixup": "a mix-up",
}

GIRL_NAMES = ["Mina", "June", "Pia", "Tessa", "Luna"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Theo", "Milo"]
HERO_TYPES = ["girl", "boy"]


ASP_RULES = r"""
% A dismissal is suspicious when the room has a teriyaki clue and the hygienist is removed.
suspicious(R) :- room(R), clue(R, teriyaki), dismissed(hygienist).

% A quest is justified when a clue exists and the child asks questions.
needs_quest(H) :- hero(H), curious(H), suspicious(R), in_room(H, R).

% A resolution happens when the clue is matched with the sauce bottle.
resolved(R) :- suspicious(R), found(bottle), matched(teriyaki, bottle).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("room", sid))
        if "teriyaki" in setting.clue:
            lines.append(asp.fact("clue", sid, "teriyaki"))
    lines.append(asp.fact("dismissed", "hygienist"))
    lines.append(asp.fact("found", "bottle"))
    lines.append(asp.fact("matched", "teriyaki", "bottle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show suspicious/1.\n#show needs_quest/1.\n#show resolved/1."))
    atoms = set((sym.name, tuple(a.string if a.type == a.type.String else a.number if a.type == a.type.Number else a.name for a in sym.arguments)) for sym in model)
    ok = ("suspicious", ("clinic",)) in atoms and ("resolved", ("clinic",)) in atoms
    if ok:
        print("OK: ASP twin matches the story logic.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected mystery facts.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld about teriyaki, a hygienist, and a dismissal.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--hygienist", choices=["Ada", "Bea", "Cora", "Nell"])
    ap.add_argument("--reason", choices=REASONS)
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
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    hygienist = args.hygienist or rng.choice(["Ada", "Bea", "Cora", "Nell"])
    reason = args.reason or rng.choice(list(REASONS))
    return StoryParams(setting=setting, hero_name=name, hero_type=gender, hygienist_name=hygienist, reason=reason)


def _hero_pronoun(hero: Entity, case: str = "subject") -> str:
    return hero.pronoun(case)


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name, meters={}, memes={"curiosity": 1.0}))
    hygienist = world.add(Entity(id="hygienist", kind="character", type="hygienist", label=params.hygienist_name, role="hygienist", meters={"cleanliness": 1.0}, memes={"calm": 1.0}))
    clue = world.add(Entity(id="clue", kind="thing", type="spill", label="the spill", phrase="a sticky teriyaki spill", meters={"sticky": 1.0}))
    bottle = world.add(Entity(id="bottle", kind="thing", type="bottle", label="the sauce bottle", phrase="a half-full teriyaki bottle", meters={"tilted": 1.0}))
    world.facts.update(hero=hero, hygienist=hygienist, clue=clue, bottle=bottle, setting=setting, params=params)

    world.say(f"{hero.label} was in {setting.place}, where the air felt {setting.atmosphere}.")
    world.say(f"{hero.label} noticed {setting.clue}. That made {hero.pronoun('possessive')} brow pinch with curiosity.")
    world.say(f"{hygienist.label}, the hygienist, was nearby, holding a cloth and trying to keep everything neat.")

    world.para()
    world.say(f"{hero.label} asked, \"Why does it smell like teriyaki in a place that should smell clean?\"")
    world.say(f"{hygienist.label} answered softly, \"I did not mean to make trouble. I think someone spilled sauce and left in a hurry.\"")
    world.say(f"Before anyone could speak again, a supervisor said there would be a dismissal, and {hygienist.label} had to step out of the room.")
    hygienist.memes["dismissed"] = 1.0
    hero.memes["suspicion"] = 1.0
    world.facts["dismissal"] = True
    world.facts["reason"] = params.reason

    world.para()
    quest = Quest(
        target="find who handled the teriyaki bottle",
        lead="follow the sticky clue",
        clue_item="the sauce bottle",
        resolution="show that the spill came from a clumsy accident, not from carelessness",
    )
    world.facts["quest"] = quest

    world.say(f"That dismissal did not feel like the end of the matter, so {hero.label} began a small quest.")
    world.say(f"{hero.label} followed the clue from the sink to a cart, then to {quest.clue_item}.")
    world.say(f"There, {hero.label} found {bottle.label} tipped on its side, with a cap that had rolled under a tray.")

    if params.reason == "accident":
        world.say(f"{hero.label} whispered, \"Oh! This was just an accident.\"")
    elif params.reason == "mixup":
        world.say(f"{hero.label} whispered, \"Someone must have mixed up the bottles.\"")
    else:
        world.say(f"{hero.label} whispered, \"Someone wanted this to look worse than it was.\"")

    world.para()
    hygienist.memes["relief"] = 1.0
    hero.memes["understanding"] = 1.0
    world.say(f"{hero.label} went back and told {hygienist.label}, \"I found the bottle. The spill was teriyaki, but it was a simple mistake.\"")
    world.say(f"{hygienist.label} sighed with relief and said, \"Thank you for asking before deciding.\"")
    world.say(f"In the end, the room was cleaned, the misunderstanding lifted, and the faint teriyaki smell became only a clue, not a blame.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a child-friendly mystery story about {p.hero_name} and a teriyaki smell in {world.facts['setting'].place}.",
        f"Tell a short dialogue-driven quest where a hygienist is dismissed and the truth about a teriyaki spill is found.",
        f"Write a gentle mystery with a clue, a question, and an ending that explains the dismissal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    hygienist: Entity = world.facts["hygienist"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    quest: Quest = world.facts["quest"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where was {p.hero_name} when the mystery began?",
            answer=f"{p.hero_name} was in {setting.place}, where the air felt {setting.atmosphere} and the teriyaki clue stood out.",
        ),
        QAItem(
            question=f"Who was dismissed during the story?",
            answer=f"The hygienist, {hygienist.label}, was dismissed from the room before the mystery was solved.",
        ),
        QAItem(
            question=f"What did {p.hero_name} do to solve the mystery?",
            answer=f"{p.hero_name} followed the clue, found the sauce bottle, and used that discovery to complete the quest.",
        ),
        QAItem(
            question=f"Why did the mystery matter?",
            answer=f"It mattered because the teriyaki smell made the room seem suspicious, and the dismissal could have blamed the hygienist unfairly.",
        ),
        QAItem(
            question=f"What was the quest about?",
            answer=f"The quest was to {quest.target}, by {quest.lead}, so the truth about the spill could be explained clearly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teriyaki?",
            answer="Teriyaki is a sweet, savory sauce or flavor often used on food, and it can leave a sticky smell if it spills.",
        ),
        QAItem(
            question="What does a hygienist do?",
            answer="A hygienist helps keep a place clean and orderly, especially in a clinic or dental office.",
        ),
        QAItem(
            question="What is a dismissal?",
            answer="A dismissal is when someone is sent away, told to leave, or no longer allowed to stay in a place.",
        ),
        QAItem(
            question="What is a quest in a story?",
            answer="A quest is a small search or mission to find something important or solve a problem.",
        ),
    ]


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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"{e.id}: {e.label or e.type} {' '.join(parts)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params)
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


def asp_verify_python_parity() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show suspicious/1.\n#show needs_quest/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify_python_parity())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show suspicious/1.\n#show needs_quest/1.\n#show resolved/1."))
        print("ASP atoms:")
        for sym in model:
            print(sym)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="clinic", hero_name="Mina", hero_type="girl", hygienist_name="Ada", reason="accident"),
            StoryParams(setting="hallway", hero_name="Noah", hero_type="boy", hygienist_name="Bea", reason="mixup"),
            StoryParams(setting="cafeteria", hero_name="Luna", hero_type="girl", hygienist_name="Cora", reason="coverup"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            p.seed = (args.seed or 0) + i
            sample = generate(p)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
