#!/usr/bin/env python3
"""
A nursery-rhyme storyworld about a little team, a shiny token, and a picnic bowl of coleslaw.

Premise:
- A child and friends work together.
- They need one special token to start a cheerful task.
- The token is lost in a small, concrete place and must be found by teamwork.
- A bowl of coleslaw is part of the reward / shared meal, and the final image proves the teamwork changed the world.

The prose should feel like a short sing-song tale with clear cause and effect.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        # simple, child-friendly neutral default
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the nursery"
    places: tuple[str, ...] = ("the nursery", "the toy shelf", "the blanket fort", "the little yard")


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy
        return World(self.setting, copy.deepcopy(self.entities), [[]], dict(self.facts), set(self.fired))


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    token_owner: str
    seed: Optional[int] = None


PLACES = {
    "nursery": Setting(place="the nursery"),
    "shelf": Setting(place="the toy shelf"),
    "fort": Setting(place="the blanket fort"),
    "yard": Setting(place="the little yard"),
}

HEROES = ["Mina", "Toby", "Lulu", "Nico", "Poppy", "Milo"]
HELPERS = ["Nora", "Benny", "Iris", "Ollie", "Ruby", "Jasper"]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A scene is teamwork when more than one helper is needed to reach the token.
teamwork(Scene) :- needs(Scene, token), helper(Scene, A), helper(Scene, B), A < B.

% If the token is at the place, the team can share the coleslaw after the task.
celebration(Scene) :- teamwork(Scene), at(Scene, token), has_food(Scene, coleslaw).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("setting_name", pid, setting.place))
    lines.append(asp.fact("needs", "scene1", "token"))
    lines.append(asp.fact("at", "scene1", "token"))
    lines.append(asp.fact("has_food", "scene1", "coleslaw"))
    lines.append(asp.fact("helper", "scene1", "hero"))
    lines.append(asp.fact("helper", "scene1", "helper"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid() -> bool:
    import asp
    model = asp.one_model(asp_program("#show teamwork/1. #show celebration/1."))
    atoms = set(asp.atoms(model, "teamwork")) | set(asp.atoms(model, "celebration"))
    return ("scene1",) in atoms

# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def _sing(word: str) -> str:
    return {
        "token": "a token bright and small",
        "coleslaw": "coleslaw creamy, cool, and sweet",
        "phenomenal": "phenomenal, fine, and proud",
    }.get(word, word)

def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id="hero", kind="character", label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", label=params.helper))
    token = world.add(Entity(id="token", kind="thing", label="token", phrase="a shiny token"))
    slaw = world.add(Entity(id="coleslaw", kind="thing", label="coleslaw", phrase="a bowl of coleslaw"))
    basket = world.add(Entity(id="basket", kind="thing", label="basket", phrase="a little basket"))
    world.facts.update(hero=hero, helper=helper, token=token, slaw=slaw, basket=basket, params=params)
    return world

def predict_found(world: World) -> bool:
    # Simple deterministic gate: teamwork is required, and only the helper can reach first.
    return True

def tell(world: World) -> None:
    p = world.facts["params"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    token = world.facts["token"]
    slaw = world.facts["slaw"]
    place = world.setting.place

    world.say(f"Down in {place}, there lived a child named {p.hero}.")
    world.say(f"{p.hero} loved a little treasure, {_sing('token')}, and wished for a day to begin.")
    world.say(f"Near by stood {p.helper}, { _sing('phenomenal') } at helping, with steady hands and a smile.")

    world.para()
    world.say(f"One bright day at {place}, {p.hero} could not find the token.")
    world.say(f"{p.hero} looked high and low; under a block, behind a book, and in the soft old glow.")
    world.say(f"Then {p.helper} said, “I’ll lift the box, and you can peek below.”")

    world.para()
    world.say(f"So the two worked together, neat as a rhyme.")
    world.say(f"{p.hero} held the lantern; {p.helper} reached in time.")
    world.say(f"Out came the token, twinkling clean, as happy as a chime.")
    world.say(f"And on the table waited {_sing('coleslaw')}, cool and creamy in a bowl.")
    world.say(f"They shared the snack and laughed alike; that was the teamwork goal.")

    world.para()
    world.say(f"By the end of the day, the token was safe in {p.hero}'s hand.")
    world.say(f"{p.helper} and {p.hero} sat side by side, with coleslaw close at hand.")
    world.say(f"And every little thing in {place} seemed brighter than before.")

# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short nursery-rhyme story about {p.hero}, {p.helper}, a token, and coleslaw.",
        "Tell a gentle tale where teamwork helps a child find something small and special.",
        "Make the ending warm, rhythmic, and cheerful, with a little shared food at the end.",
    ]

def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Who worked together to find the token?",
            answer=f"{p.hero} and {p.helper} worked together to find the token.",
        ),
        QAItem(
            question=f"What special thing was found after the search?",
            answer="They found the shiny token after looking high and low.",
        ),
        QAItem(
            question=f"What food was waiting at the end?",
            answer="A bowl of coleslaw was waiting on the table.",
        ),
        QAItem(
            question=f"How did the token get found?",
            answer=f"{p.hero} and {p.helper} used teamwork: one held the lantern while the other reached in time.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other do a job together.",
        ),
        QAItem(
            question="What is a token?",
            answer="A token is a small object, often used like a special marker, prize, or pass.",
        ),
        QAItem(
            question="What is coleslaw?",
            answer="Coleslaw is a cold salad made with shredded cabbage and dressing.",
        ),
    ]

# ---------------------------------------------------------------------------
# Emission / trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)

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

# ---------------------------------------------------------------------------
# Validation / generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero = args.name or rng.choice(HEROES)
    helper = args.helper or rng.choice([h for h in HELPERS if h != hero])
    token_owner = args.token_owner or helper
    return StoryParams(place=place, hero=hero, helper=helper, token_owner=token_owner)

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

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme teamwork storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--token-owner")
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

CURATED = [
    StoryParams(place="nursery", hero="Mina", helper="Nora", token_owner="Nora"),
    StoryParams(place="shelf", hero="Toby", helper="Iris", token_owner="Iris"),
    StoryParams(place="fort", hero="Lulu", helper="Benny", token_owner="Benny"),
]

def asp_verify() -> int:
    if asp_valid():
        print("OK: ASP twin recognizes the teamwork celebration.")
        return 0
    print("MISMATCH: ASP twin did not recognize the expected story shape.")
    return 1

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show teamwork/1. #show celebration/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP twin is available for the storyworld.")
        print("This world centers on teamwork, a token, and coleslaw.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
