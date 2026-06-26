#!/usr/bin/env python3
"""
storyworlds/worlds/neighborhood_bad_ending_magic_pirate_tale.py
===============================================================

A small standalone story world for a pirate-tale-style neighborhood story
with magic and a bad ending.

Seed tale:
---
A little pirate in the neighborhood finds a magic trinket that seems like it
can help with treasure. The pirate gets excited, ignores a warning, and uses
the magic anyway. The spell goes wrong, the treasure is lost, and the crew
goes home empty-handed.

This world simulates:
- a child pirate crew in a neighborhood
- a magic object with a visible physical effect
- a tension beat where caution is ignored
- a bad ending where the hoped-for treasure is ruined or lost

The story remains child-facing, concrete, and state-driven.
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

NEIGHBORHOOD_SPACES = {
    "corner": "the corner of the neighborhood",
    "block": "the quiet neighborhood block",
    "yard": "the front yard in the neighborhood",
    "alley": "the narrow neighborhood alley",
    "porch": "the porch by the neighborhood gate",
}

ARTIFACTS = {
    "moon_shell": {
        "label": "moon shell",
        "phrase": "a pale moon shell that hummed when held near treasure",
        "magic": "shine",
        "effect": "made a little silver glow spill over everything nearby",
        "risk": "the glow would call curious wind",
        "bad_outcome": "the wind would carry the treasure away",
        "qa": "A moon shell is a shell that seems magical in stories and can glow like moonlight.",
    },
    "salt_knife": {
        "label": "salt knife",
        "phrase": "a little salt knife with a bright blue handle",
        "magic": "sparkle",
        "effect": "made a sparkling trail jump from one thing to the next",
        "risk": "the sparkles could wake up the wrong thing",
        "bad_outcome": "the wrong thing could start the trouble",
        "qa": "A magical knife in a story can be a pretend enchanted tool, not a real weapon.",
    },
    "gold_map": {
        "label": "gold map",
        "phrase": "a folded gold map that whispered when opened",
        "magic": "whisper",
        "effect": "made a whispering sound that pulled attention everywhere",
        "risk": "the whispers would lead everyone to the wrong place",
        "bad_outcome": "the treasure chest would be found empty",
        "qa": "A map shows a route or a place. A magical map in a story may seem to talk or glow.",
    },
}

TREASURES = {
    "toy_chest": {
        "label": "toy chest",
        "phrase": "a wooden toy chest full of shiny costume coins",
        "region": "hand",
        "qa": "A toy chest is a small pretend chest for play, not a real pirate chest.",
    },
    "kite": {
        "label": "kite",
        "phrase": "a striped kite with a long tail",
        "region": "hand",
        "qa": "A kite is a light flying toy that can be pulled by a string in the wind.",
    },
    "coin_pouch": {
        "label": "coin pouch",
        "phrase": "a soft coin pouch with three pretend gold coins",
        "region": "belt",
        "qa": "A pouch is a small bag used to carry little things like coins or keys.",
    },
}

RISK_ACTIONS = {
    "use_magic": "use the magic to open the treasure",
    "chase": "chase the treasure glow through the neighborhood",
    "hide": "hide the treasure before the wind finds it",
}

HERO_NAMES = ["Mina", "Jett", "Pip", "Nico", "Luna", "Ari"]
CREW_NAMES = ["Captain Bea", "Uncle Ro", "Aunt Nia", "Old Finn", "Captain Ivy"]
TRAITS = ["brave", "bouncy", "curious", "restless", "spirited", "eager"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the neighborhood"
    space: str = "the quiet neighborhood block"


@dataclass
class StoryParams:
    space: str
    artifact: str
    treasure: str
    name: str
    gender: str
    crew: str
    trait: str
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


def _p(world: World, text: str) -> None:
    world.say(text)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate-tale neighborhood story world with magic and a bad ending.")
    ap.add_argument("--space", choices=sorted(NEIGHBORHOOD_SPACES))
    ap.add_argument("--artifact", choices=sorted(ARTIFACTS))
    ap.add_argument("--treasure", choices=sorted(TREASURES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--crew", choices=[c.split()[0].lower() for c in CREW_NAMES])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.gender and args.treasure and args.gender not in {"girl", "boy"}:
        raise StoryError("Invalid gender.")
    spaces = [args.space] if args.space else list(NEIGHBORHOOD_SPACES)
    arts = [args.artifact] if args.artifact else list(ARTIFACTS)
    trs = [args.treasure] if args.treasure else list(TREASURES)
    combos = []
    for space in spaces:
        for art in arts:
            for tr in trs:
                combos.append((space, art, tr))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    space, artifact, treasure = rng.choice(combos)
    if args.gender:
        gender = args.gender
    else:
        gender = rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(HERO_NAMES)
    crew = args.crew or rng.choice([c.split()[0].lower() for c in CREW_NAMES])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(space=space, artifact=artifact, treasure=treasure, name=name, gender=gender, crew=crew, trait=trait)


def story_reasonable(params: StoryParams) -> bool:
    return params.space in NEIGHBORHOOD_SPACES and params.artifact in ARTIFACTS and params.treasure in TREASURES


def generate(params: StoryParams) -> StorySample:
    if not story_reasonable(params):
        raise StoryError("This neighborhood pirate tale needs a valid space, artifact, and treasure.")
    setting = Setting(place="the neighborhood", space=NEIGHBORHOOD_SPACES[params.space])
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={"hope": 1.0}, memes={"eagerness": 1.0}))
    crew = world.add(Entity(id="crew", kind="character", type="pirate", label=f"Captain {params.crew.capitalize()}", meters={"caution": 1.0}))
    artifact_cfg = ARTIFACTS[params.artifact]
    treasure_cfg = TREASURES[params.treasure]
    artifact = world.add(Entity(id="artifact", type="artifact", label=artifact_cfg["label"], phrase=artifact_cfg["phrase"], owner=hero.id, meters={"magic": 1.0}))
    treasure = world.add(Entity(id="treasure", type="treasure", label=treasure_cfg["label"], phrase=treasure_cfg["phrase"], owner=hero.id, carried_by=hero.id, meters={"safe": 1.0}))

    world.facts.update(hero=hero, crew=crew, artifact=artifact, treasure=treasure, params=params)

    _p(world, f"{hero.id} was a {params.trait} little pirate who loved the neighborhood as much as any ship at sea.")
    _p(world, f"{hero.id} also loved {artifact_cfg['label']}s, because {artifact_cfg['phrase']} felt like a clue to hidden treasure.")
    _p(world, f"One bright afternoon, {hero.id} found {treasure_cfg['phrase']} near {setting.space} and dreamed of being the cleverest pirate on the block.")
    world.para()

    _p(world, f"{crew.label} pointed a finger and said, \"Careful now. {artifact_cfg['risk'].capitalize()}, and then {artifact_cfg['bad_outcome']}.\"")
    hero.memes["warning"] = 1.0
    crew.memes["warning"] = 1.0
    _p(world, f"But {hero.id} felt too eager to listen. {hero.id} gripped the {artifact_cfg['label']} and decided to {RISK_ACTIONS['use_magic']} anyway.")
    hero.memes["defiance"] = 1.0
    world.para()

    # Action consequence: magic creates the bad ending.
    if params.artifact == "moon_shell":
        treasure.meters["safe"] = 0.0
        treasure.meters["lost"] = 1.0
        world.say(f"The moon shell made a little silver glow spill across {setting.space}, and the neighborhood wind came sneaking in.")
        world.say(f"The wind lifted the {treasure.label} right out of {hero.id}'s hands and carried {treasure.it()} behind the hedges.")
    elif params.artifact == "salt_knife":
        treasure.meters["safe"] = 0.0
        treasure.meters["dropped"] = 1.0
        world.say(f"The salt knife flashed a sparkly path from fence to fence, and the sparkles woke up a noisy flock of birds.")
        world.say(f"The birds startled {hero.id}, and the {treasure.label} fell into the grass where nobody could find {treasure.it()} again.")
    else:
        treasure.meters["safe"] = 0.0
        treasure.meters["empty"] = 1.0
        world.say(f"The gold map whispered too loudly, and every door in the neighborhood seemed to hear it.")
        world.say(f"By the time {hero.id} ran back, the {treasure.label} was empty and the pretend gold coins were gone.")
    world.para()

    hero.memes["sadness"] = 1.0
    crew.memes["regret"] = 1.0
    _p(world, f"{hero.id} stood still in the {setting.space}, with {artifact.label} dim in {hero.id}'s hand and {treasure.label} no longer safe.")
    _p(world, f"{crew.label} sighed. \"A pirate can chase treasure too hard,\" {crew.pronoun('subject')} said, \"and then the neighborhood keeps the best part.\"")
    _p(world, f"So the little crew went home empty-handed, and the only thing left shining was the faint magic on the {artifact.label}.")
    hero.memes["hope"] = 0.0
    treasure.meters["lost"] = 1.0

    world.facts["ending"] = "bad"
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a short pirate tale for a child about the neighborhood, magic, and a bad ending, using the word "{p.space}".',
        f"Tell a simple story where {f['hero'].id} finds {ARTIFACTS[p.artifact]['label']} magic in the neighborhood and loses {TREASURES[p.treasure]['label']}.",
        f"Write a pirate-style story with a warning, a magical mistake, and an empty-handed ending on the neighborhood block.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    hero = f["hero"]
    crew = f["crew"]
    artifact = f["artifact"]
    treasure = f["treasure"]
    cfg_a = ARTIFACTS[p.artifact]
    cfg_t = TREASURES[p.treasure]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a {p.trait} little pirate in the neighborhood who wanted to use {artifact.label} magic on {treasure.label}.",
        ),
        QAItem(
            question=f"What warning did {crew.label} give before the magic was used?",
            answer=f"{crew.label} warned that {cfg_a['risk']}, and then {cfg_a['bad_outcome']}.",
        ),
        QAItem(
            question=f"What went wrong after {hero.id} used the {artifact.label}?",
            answer=f"The magic went wrong and the {treasure.label} was lost or ruined, so the crew went home empty-handed.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended as a bad ending: {hero.id} was left holding dim magic in the neighborhood while the treasure was no longer safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    return [
        QAItem(question="What is a neighborhood?", answer="A neighborhood is a part of a town or city where homes and streets are close together."),
        QAItem(question="What does magic mean in a story?", answer="Magic in a story means something impossible or surprising happens, like a glow, a whisper, or a spell."),
        QAItem(question=f"What is a {ARTIFACTS[p.artifact]['label']}?", answer=ARTIFACTS[p.artifact]["qa"]),
        QAItem(question=f"What is a {TREASURES[p.treasure]['label']}?", answer=TREASURES[p.treasure]["qa"]),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(space="corner", artifact="moon_shell", treasure="toy_chest", name="Mina", gender="girl", crew="bea", trait="curious"),
    StoryParams(space="yard", artifact="salt_knife", treasure="kite", name="Jett", gender="boy", crew="nia", trait="eager"),
    StoryParams(space="porch", artifact="gold_map", treasure="coin_pouch", name="Pip", gender="boy", crew="ivy", trait="spirited"),
]


ASP_RULES = r"""
artifact(A) :- has_artifact(A).
treasure(T) :- has_treasure(T).
neighborhood(S) :- has_space(S).
bad_story(S,A,T) :- neighborhood(S), artifact(A), treasure(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in NEIGHBORHOOD_SPACES:
        lines.append(asp.fact("has_space", s))
    for a in ARTIFACTS:
        lines.append(asp.fact("has_artifact", a))
    for t in TREASURES:
        lines.append(asp.fact("has_treasure", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show bad_story/3."))
    return sorted(set(asp.atoms(model, "bad_story")))


def asp_verify() -> int:
    py = {(s, a, t) for s in NEIGHBORHOOD_SPACES for a in ARTIFACTS for t in TREASURES}
    clingo = set(asp_valid())
    if py == clingo:
        print(f"OK: clingo gate matches Python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible bad-story combinations:")
        for row in combos[:50]:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.artifact} / {p.treasure} at {p.space}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
