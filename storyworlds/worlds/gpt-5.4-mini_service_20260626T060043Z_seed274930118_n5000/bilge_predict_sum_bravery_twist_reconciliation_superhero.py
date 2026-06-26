#!/usr/bin/env python3
"""
Standalone storyworld: a small Superhero Story domain with a brave hero,
a surprising twist, and a reconciliation ending.

This world builds a tiny causal simulation around a harbor rescue:
- a hero wants to protect the docks,
- a twist reveals the bilge pump is the real problem,
- the hero predicts the trouble, sums up the clues, and resolves it with a
  reconciliation between people who were arguing.

The seed words are present as narrative instruments:
- bilge
- predict
- sum

Features:
- Bravery
- Twist
- Reconciliation
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    harbor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    danger: str
    clue: str
    weather: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    region: str
    protects: set[str] = field(default_factory=set)
    plural: bool = False


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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "harbor": Setting(place="the harbor", harbor=True, affords={"bilge", "storm"}),
    "dock": Setting(place="the dock", harbor=True, affords={"bilge", "storm"}),
    "shipyard": Setting(place="the shipyard", harbor=True, affords={"bilge"}),
}

CHALLENGES = {
    "bilge": Challenge(
        id="bilge",
        verb="fix the bilge pump",
        gerund="fixing the bilge pump",
        danger="water flooding the deck",
        clue="the bilge water kept rising",
        weather="stormy",
        tags={"bilge", "water", "boat"},
    ),
    "storm": Challenge(
        id="storm",
        verb="hold the ship steady",
        gerund="bracing against the storm",
        danger="waves slamming the hull",
        clue="the wind kept twisting the ropes",
        weather="stormy",
        tags={"storm", "wind", "water"},
    ),
}

ARTIFACTS = {
    "gloves": Artifact(
        id="gloves",
        label="power gloves",
        phrase="shiny power gloves",
        region="hands",
        protects={"water"},
    ),
    "cape": Artifact(
        id="cape",
        label="red cape",
        phrase="a bright red cape",
        region="back",
        protects={"wind"},
    ),
    "boots": Artifact(
        id="boots",
        label="storm boots",
        phrase="tall storm boots",
        region="feet",
        protects={"water"},
        plural=True,
    ),
}

NAMES = ["Nova", "Milo", "Iris", "Kai", "Rosa", "Tess", "Jett", "Lina"]
ROLES = ["hero", "captain", "engineer", "reporter"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    challenge: str
    artifact: str
    name: str
    role: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A challenge is risky if the setting affords it.
risky(P, C) :- setting(P), challenge(C), affords(P, C).

% An artifact is a reasonable answer if it protects the relevant danger type.
fix(C, A) :- challenge(C), artifact(A), protects(A, T), danger_type(C, T).

valid(P, C, A) :- risky(P, C), fix(C, A).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy inside ASP helpers
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.harbor:
            lines.append(asp.fact("harbor", pid))
        for c in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, c))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for t in sorted(ch.tags):
            lines.append(asp.fact("danger_type", cid, t))
    for aid, art in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        for p in sorted(art.protects):
            lines.append(asp.fact("protects", aid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

class Reason:
    def __init__(self) -> None:
        self.notes: list[str] = []


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for ch in setting.affords:
            if ch not in CHALLENGES:
                continue
            for art in ARTIFACTS:
                if ch == "bilge" and "water" in ARTIFACTS[art].protects:
                    combos.append((place, ch, art))
                if ch == "storm" and "wind" in ARTIFACTS[art].protects:
                    combos.append((place, ch, art))
    return combos


def can_fix(challenge: Challenge, artifact: Artifact) -> bool:
    if challenge.id == "bilge":
        return "water" in artifact.protects
    if challenge.id == "storm":
        return "wind" in artifact.protects
    return False


def predict(world: World, hero: Entity, challenge: Challenge) -> dict:
    if challenge.id == "bilge":
        return {"flood": True, "twist": "bilge", "reconcile": True}
    return {"flood": True, "twist": "storm", "reconcile": True}


def sum_clues(world: World, hero: Entity, challenge: Challenge) -> str:
    if challenge.id == "bilge":
        return "the bilge water, the dripping floor, and the squeaky pump all pointed to one problem"
    return "the snapping ropes, the leaning mast, and the wild wind all pointed to one problem"


def tell(setting: Setting, challenge: Challenge, artifact: Artifact, name: str, role: str) -> World:
    w = World(setting=setting)
    hero = w.add(Entity(id=name, kind="character", type="hero", label=role))
    ally = w.add(Entity(id="ally", kind="character", type="engineer", label="the engineer"))
    rival = w.add(Entity(id="rival", kind="character", type="captain", label="the captain"))
    item = w.add(Entity(id="gear", type=artifact.label, label=artifact.label, phrase=artifact.phrase, owner=hero.id))
    hero.meters["bravery"] = 0.0
    hero.memes["worry"] = 0.0
    ally.memes["frustration"] = 1.0
    rival.memes["stubborn"] = 1.0

    w.say(f"{hero.id} was a {role} with a brave heart and a bright suit.")
    w.say(f"{hero.id} kept {artifact.phrase} ready for hard days.")
    w.say(f"At {setting.place}, a small team waited while the {challenge.id} trouble grew.")

    w.para()
    hero.memes["alert"] = 1.0
    hero.meters["bravery"] += 1.0
    w.say(f"Then {hero.id} looked down, listened hard, and chose bravery instead of panic.")
    w.say(f"{challenge.clue.capitalize()}, and {hero.id} knew how to predict what it meant.")

    pred = predict(w, hero, challenge)
    w.facts["predicted"] = pred
    w.say(f"{hero.id} could predict the next step from the clues, and the plan became clear.")
    w.say(f"{hero.id} said the sum of the clues was simple: {sum_clues(w, hero, challenge)}.")

    w.para()
    if can_fix(challenge, artifact):
        hero.memes["confidence"] = 1.0
        if challenge.id == "bilge":
            w.say(f"{hero.id} used the {artifact.label} to seal the leak and stop the bilge water.")
        else:
            w.say(f"{hero.id} used the {artifact.label} to brace against the wind and steady the deck.")
        w.say(f"That was the twist: the loud problem was not the biggest problem.")
        w.say(f"The real trouble was the argument between {ally.label} and {rival.label}.")
        w.say(f"{hero.id} smiled and chose reconciliation instead of blame.")
        w.say(f"{hero.id} spoke kindly, and soon {ally.label} and {rival.label} were working side by side.")
        w.say(f"In the end, the harbor was safe, the team was calm, and the {artifact.label} shone in the light.")
        hero.memes["reconciliation"] = 1.0
    else:
        raise StoryError("This challenge and artifact do not form a reasonable superhero solution.")

    w.facts.update(hero=hero, ally=ally, rival=rival, item=item, challenge=challenge, artifact=artifact)
    return w


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    challenge: Challenge = f["challenge"]
    artifact: Artifact = f["artifact"]
    return [
        f"Write a short superhero story about {hero.id} at {world.setting.place} that includes the word bilge.",
        f"Tell a brave rescue story where a hero must predict the real danger and use a {artifact.label}.",
        f"Write a story with a twist and reconciliation, ending with {hero.id} saving the day.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    ally: Entity = f["ally"]
    rival: Entity = f["rival"]
    challenge: Challenge = f["challenge"]
    artifact: Artifact = f["artifact"]
    return [
        QAItem(
            question=f"What kind of story is this one about {hero.id}?",
            answer=f"It is a superhero story about {hero.id}, who acts bravely when trouble starts at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} predict from the clues?",
            answer=f"{hero.id} predicted that {challenge.id} trouble was coming, because the clues all pointed to the same danger.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the big problem was not only the {challenge.id} trouble; the argument between {ally.label} and {rival.label} mattered too.",
        ),
        QAItem(
            question=f"How did the story end after the reconciliation?",
            answer=f"It ended with {hero.id} helping everyone work together, so the team was calm and the {artifact.label} had done its job.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bilge pump?",
            answer="A bilge pump is a pump on a boat that helps move water out so the boat does not flood.",
        ),
        QAItem(
            question="What does it mean to predict something?",
            answer="To predict something means to think ahead and guess what will happen by using clues.",
        ),
        QAItem(
            question="What does sum mean?",
            answer="A sum is what you get when you add things together, or the total of several parts.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means people stop arguing and work things out together again.",
        ),
    ]


# ---------------------------------------------------------------------------
# Serialization / emit
# ---------------------------------------------------------------------------

def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {', '.join(bits)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="harbor", challenge="bilge", artifact="gloves", name="Nova", role="hero"),
    StoryParams(place="dock", challenge="storm", artifact="cape", name="Kai", role="hero"),
    StoryParams(place="shipyard", challenge="bilge", artifact="boots", name="Iris", role="hero"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero Story world with bravery, twist, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--challenge", choices=CHALLENGES.keys())
    ap.add_argument("--artifact", choices=ARTIFACTS.keys())
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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
    if args.challenge and args.artifact:
        if not can_fix(CHALLENGES[args.challenge], ARTIFACTS[args.artifact]):
            raise StoryError("This artifact cannot reasonably solve that challenge.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.artifact is None or c[2] == args.artifact)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, challenge, artifact = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    role = args.role or "hero"
    return StoryParams(place=place, challenge=challenge, artifact=artifact, name=name, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CHALLENGES[params.challenge],
        ARTIFACTS[params.artifact],
        params.name,
        params.role,
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


# ---------------------------------------------------------------------------
# CLI / ASP
# ---------------------------------------------------------------------------

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
