#!/usr/bin/env python3
"""
storyworlds/worlds/new_bounty_cashew_rhyme_lesson_learned_kindness.py
=====================================================================

A small Space Adventure storyworld about a crew chasing a new bounty,
sharing cashews, and learning that kindness can turn a tense mission into a
better rhyme.

Premise:
- A young space crew hears about a new bounty drifting near a quiet station.
- The prize is tempting, but the cargo is delicate, and the crew must choose
  between speed and kindness.
- A tiny rhyme message and a lesson learned turn the mission from greedy to
  generous.

The world tracks physical meters and emotional memes for a few typed entities:
- meters: distance, cargo, sparkle, damage, drift
- memes: excitement, worry, pride, kindness, relief, greed, warmth

The prose is child-facing and state-driven: the ending image reflects whether
the crew handled the bounty kindly and what changed because of it.
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
# Core data model
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
    wears: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "captain", "pilot"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "mate", "engineer"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


def _zero() -> float:
    return 0.0


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    trace_log: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Venue:
    id: str
    label: str
    tone: str
    can_rhyme: bool = True


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    sparkle: str
    safe_handling: str
    kind: str = "cargo"


@dataclass
class CrewGear:
    id: str
    label: str
    protects: set[str]
    note: str


SETTINGS = {
    "dock": Venue("dock", "the moon dock", "quiet and silver"),
    "orbit": Venue("orbit", "a glowing orbit lane", "slow and starry"),
    "station": Venue("station", "the little star station", "bright and busy"),
    "bay": Venue("bay", "the cargo bay", "soft and echoing"),
}

ARTIFACTS = {
    "cashew": Artifact(
        id="cashew",
        label="cashews",
        phrase="a tin of new cashews",
        sparkle="a tiny golden shine",
        safe_handling="keep them sealed",
    ),
    "bounty": Artifact(
        id="bounty",
        label="the bounty",
        phrase="a new bounty crate",
        sparkle="a brave blue gleam",
        safe_handling="carry it gently",
    ),
}

GEAR = {
    "gloves": CrewGear("gloves", "soft gloves", {"scratch", "drop"}, "use soft gloves"),
    "belt": CrewGear("belt", "a steady cargo belt", {"drop", "drift"}, "clip on a steady cargo belt"),
    "lantern": CrewGear("lantern", "a tiny lantern", {"dark"}, "turn on a tiny lantern"),
}

NAMES = ["Nova", "Milo", "Zia", "Rex", "Luna", "Tess"]
TITLES = ["captain", "pilot", "engineer", "mate"]

# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    artifact: str
    name: str
    title: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for artifact in ARTIFACTS:
            out.append((place, artifact))
    return out


def explain_rejection(place: str, artifact: str) -> str:
    return f"(No story: the {artifact} cannot be paired with {place} in this tiny domain.)"


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------
def add_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def add_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def predict_risk(world: World, hero: Entity, artifact: Artifact) -> dict:
    sim = world.copy()
    _take_mission(sim, sim.get(hero.id), artifact, narrate=False)
    cargo = sim.get("cargo")
    return {
        "damaged": cargo.meters.get("damage", 0.0) > 0,
        "drift": cargo.meters.get("drift", 0.0),
    }


def rhyme_line(artifact: Artifact) -> str:
    if artifact.id == "cashew":
        return "Cashews in a tin keep the crumbs within."
    return "A careful hand can hold the starry plan."


def lesson_line(artifact: Artifact) -> str:
    if artifact.id == "cashew":
        return "The lesson learned was simple: seal the snack before the stars shake it loose."
    return "The lesson learned was simple: a gentle crew can guard a glowing prize."


def kindness_line() -> str:
    return "Kindness made the whole crew feel warmer than the ship's little lamp."


def _take_mission(world: World, hero: Entity, artifact: Artifact, narrate: bool = True) -> None:
    cargo = world.get("cargo")
    if artifact.id == "cashew":
        add_meter(cargo, "drift", 1)
        add_meme(hero, "greed", 1)
        if narrate:
            world.say("The tin bumped and the cashews rattled like tiny moons.")
        if cargo.meters.get("drift", 0) > 0 and "seal" not in world.fired:
            world.fired.add("seal")
            add_meter(cargo, "damage", 0)
            if narrate:
                world.say("But the lid stayed on, so nothing spilled into space.")
    else:
        add_meter(cargo, "sparkle", 1)
        add_meme(hero, "excitement", 1)
        if narrate:
            world.say("The crate glowed softly, and the crew moved like careful starlight.")


def story_events(world: World, hero: Entity, artifact: Artifact) -> None:
    cargo = world.get("cargo")
    add_meme(hero, "worry", 1)
    world.say(f"{hero.id} was a {hero.type} who loved space days when everything shimmered.")
    world.say(f"{hero.pronoun().capitalize()} heard about a new bounty near {world.place} and hurried to see it.")
    world.say(f"It was {artifact.phrase}, and it had {artifact.sparkle}.")
    world.say(f"{hero.pronoun().capitalize()} wanted to bring it home fast, but {artifact.safe_handling}.")

    world.para()
    world.say(f"The ship slid into {world.place}, which felt {SETTINGS[world.place].tone}.")
    world.say(f"{hero.id} reached for the cargo and felt the whole plan wobble a little.")
    if artifact.id == "cashew":
        world.say("A cashew tin can make a cheerful clatter, but it can also spill if it is shaken too hard.")
    else:
        world.say("A bounty crate can be bright and tempting, but it still needs a calm hand.")

    risk = predict_risk(world, hero, artifact)
    if risk["damaged"]:
        add_meme(hero, "worry", 1)
        world.say(f"{hero.pronoun().capitalize()} noticed the danger and paused.")
    else:
        world.say(f"{hero.pronoun().capitalize()} noticed there was a safer way and paused anyway.")

    world.para()
    add_meme(hero, "kindness", 1)
    world.say(f"{hero.pronoun().capitalize()} said, \"Let's be kind to the prize and to each other.\"")
    world.say(rhyme_line(artifact))
    gear = GEAR["gloves"] if artifact.id == "cashew" else GEAR["belt"]
    world.say(f"So the crew used {gear.label} and chose to {artifact.safe_handling}.")
    world.say(f"That made the mission slow down, but it also made it safe.")

    _take_mission(world, hero, artifact, narrate=True)

    world.para()
    add_meme(hero, "relief", 1)
    add_meme(hero, "warmth", 1)
    world.say(kindness_line())
    world.say(lesson_line(artifact))
    if artifact.id == "cashew":
        world.say("At the end, the tin was still closed, the cashews were still fresh, and the crew was smiling.")
    else:
        world.say("At the end, the bounty was steady, the ship was calm, and the crew had learned to move gently together.")

    world.facts.update(
        hero=hero,
        artifact=artifact,
        cargo=cargo,
        gear=gear,
        risk=risk,
        place=world.place,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    artifact: Artifact = f["artifact"]
    hero: Entity = f["hero"]
    return [
        f'Write a short space adventure for a young child about a new {artifact.label} bounty and a kind crew.',
        f"Tell a tiny story where {hero.id} learns a lesson learned about kindness while carrying {artifact.phrase}.",
        f'Write a gentle rhyme about "{artifact.label}" that ends with the crew choosing a safer way to help.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    artifact: Artifact = f["artifact"]
    gear: CrewGear = f["gear"]
    qa = [
        QAItem(
            question=f"What new thing did {hero.id} hear about near {world.place}?",
            answer=f"{hero.id} heard about a new bounty, {artifact.phrase}, and went to help bring it home.",
        ),
        QAItem(
            question=f"Why did {hero.id} slow down instead of grabbing {artifact.label} too fast?",
            answer=f"{hero.id} slowed down because {artifact.safe_handling}, and the crew wanted to keep the mission safe.",
        ),
        QAItem(
            question=f"What did the crew use to help with the {artifact.label} mission?",
            answer=f"They used {gear.label} so they could carry the cargo more carefully.",
        ),
        QAItem(
            question="What lesson was learned by the end of the story?",
            answer="The lesson learned was that kindness and careful hands can protect a prize better than rushing.",
        ),
    ]
    if artifact.id == "cashew":
        qa.append(QAItem(
            question="What sound did the cashew tin make?",
            answer="It rattled like tiny moons, but the lid stayed on.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    artifact: Artifact = world.facts["artifact"]
    if artifact.id == "cashew":
        return [
            QAItem(
                question="What are cashews?",
                answer="Cashews are crunchy nuts that people sometimes eat as a snack.",
            ),
            QAItem(
                question="Why do people keep snacks in a tin?",
                answer="A tin helps keep snacks dry and stops them from spilling out.",
            ),
            QAItem(
                question="What does kindness mean?",
                answer="Kindness means being gentle, helpful, and caring toward others.",
            ),
        ]
    return [
        QAItem(
            question="What is a bounty?",
            answer="A bounty is a prize or job that someone goes to find or bring back.",
        ),
        QAItem(
            question="What is a cargo belt for?",
            answer="A cargo belt helps hold things steady so they do not drop or drift away.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like light and bright.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_combo(P, A) :- place(P), artifact(A).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for aid in ARTIFACTS:
        lines.append(asp.fact("artifact", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python gates.")
    print("only in python:", sorted(py - cl))
    print("only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story building
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld about a new bounty, cashews, rhyme, lesson learned, and kindness.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--artifact", choices=ARTIFACTS.keys())
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--title", choices=TITLES)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.artifact:
        combos = [c for c in combos if c[1] == args.artifact]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, artifact = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    title = args.title or rng.choice(TITLES)
    return StoryParams(place=place, artifact=artifact, name=name, title=title)


def generate(params: StoryParams) -> StorySample:
    world = World(params.place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.title))
    cargo = world.add(Entity(id="cargo", kind="thing", type=params.artifact, label=ARTIFACTS[params.artifact].label))
    artifact = ARTIFACTS[params.artifact]
    story_events(world, hero, artifact)
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
        print("--- trace ---")
        for line in sample.world.trace_log:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="station", artifact="cashew", name="Nova", title="captain"),
    StoryParams(place="dock", artifact="bounty", name="Milo", title="pilot"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} ASP combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
