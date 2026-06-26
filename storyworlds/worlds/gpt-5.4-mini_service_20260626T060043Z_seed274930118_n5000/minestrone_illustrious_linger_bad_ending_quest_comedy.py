#!/usr/bin/env python3
"""
A small comedy storyworld about a quest for minestrone, an illustrious soup pot,
and the way a bad ending can be averted by a helpful turn before things linger
too long.

Premise:
- A hungry hero wants minestrone.
- A fancy "illustrious" soup bowl/pot/recipe is in the way.
- A delay or mistake can make the soup linger on the stove or go wrong.

The world is built as a tiny simulation:
- Entities have physical meters and emotional memes.
- State changes drive the prose.
- The resolution comes from a plausible comedic fix.

Seed words used by the domain:
- minestrone
- illustrious
- linger

Narrative instruments:
- Bad Ending
- Quest

The story style is light, concrete, child-facing comedy.
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
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

SETTING_NAME = "the tiny kitchen"

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    quest_item: str
    obstacle: str
    seed: Optional[int] = None


HERO_NAMES = ["Maya", "Theo", "Lina", "Owen", "Nora", "Finn"]
HELPER_NAMES = ["Auntie Jo", "Papa", "Milo", "Mimi", "Uncle Ben", "Sage"]

HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["mother", "father", "friend", "aunt", "uncle"]

QUEST_ITEMS = {
    "minestrone": {
        "label": "a steaming bowl of minestrone",
        "phrase": "a steaming bowl of minestrone",
        "needs": "warm",
    },
}

OBSTACLES = {
    "linger": {
        "label": "the long wait",
        "action": "linger",
        "problem": "made the soup linger too long on the stove",
    },
    "spill": {
        "label": "the wobble on the tray",
        "action": "wobble",
        "problem": "spilled a little soup on the floor",
    },
    "mixup": {
        "label": "the silly mix-up",
        "action": "mix up",
        "problem": "mixed up the salt and the sugar",
    },
}


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------


def build_world(params: StoryParams) -> World:
    world = World()

    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            type=params.hero_type,
            meters={"hunger": 0.0, "tired": 0.0},
            memes={"hope": 0.0, "frustration": 0.0, "joy": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper_name,
            kind="character",
            type=params.helper_type,
            meters={"busy": 0.0},
            memes={"care": 1.0, "humor": 1.0},
        )
    )
    soup = world.add(
        Entity(
            id="soup",
            type="minestrone",
            label="minestrone",
            phrase=QUEST_ITEMS["minestrone"]["phrase"],
            owner=hero.id,
            caretaker=helper.id,
            meters={"warm": 0.0, "ready": 0.0, "messy": 0.0},
            memes={"appeal": 1.0},
        )
    )
    obstacle = world.add(
        Entity(
            id="obstacle",
            type=params.obstacle,
            label=OBSTACLES[params.obstacle]["label"],
            phrase=OBSTACLES[params.obstacle]["label"],
            meters={"delay": 0.0, "mess": 0.0},
            memes={"ridiculous": 1.0},
        )
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        soup=soup,
        obstacle=obstacle,
        quest_item=params.quest_item,
        obstacle_key=params.obstacle,
        setting=SETTING_NAME,
    )
    return world


def _rule_warmth(world: World) -> list[str]:
    soup = world.get("soup")
    if soup.meters["warm"] >= THRESHOLD:
        return []
    soup.meters["warm"] += 1.0
    soup.meters["ready"] += 1.0
    return ["The minestrone started to steam softly."]


def _rule_linger_bad_end(world: World) -> list[str]:
    soup = world.get("soup")
    obstacle = world.get("obstacle")
    hero = world.get(world.facts["hero"].id)
    if obstacle.type != "linger":
        return []
    if soup.meters["warm"] < THRESHOLD:
        return []
    sig = ("linger",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    soup.meters["messy"] += 1.0
    hero.memes["frustration"] += 1.0
    return ["The soup kept trying to linger, and that gave the story a very bad ending shape."]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    out.extend(_rule_warmth(world))
    out.extend(_rule_linger_bad_end(world))
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell_story(world: World, params: StoryParams) -> World:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    soup = world.facts["soup"]
    obstacle = world.facts["obstacle"]

    world.say(
        f"Once in {SETTING_NAME}, {hero.id} started a Quest for {soup.phrase}."
    )
    world.say(
        f"{hero.id} wanted the bowl because {params.quest_item} sounded glorious and "
        f"the day felt empty without it."
    )

    world.para()
    world.say(
        f"{helper.id} promised to help, but {obstacle.label} turned the Quest into a comedy."
    )
    world.say(
        f"First there was a pause, then another pause, and the minestrone began to linger."
    )
    hero.memes["hope"] += 1.0
    hero.meters["hunger"] += 1.0
    obstacle.meters["delay"] += 1.0
    propagate(world, narrate=True)

    world.para()
    if params.obstacle == "linger":
        world.say(
            f"{hero.id} peered at the pot and said, \"This is turning into a Bad Ending!\""
        )
        world.say(
            f"{helper.id} laughed, stirred faster, and rescued the soup before the joke could get too long."
        )
        soup.meters["ready"] += 1.0
        soup.memes["appeal"] += 1.0
        hero.memes["joy"] += 1.0
        hero.memes["frustration"] = 0.0
        world.say(
            f"At last, {hero.id} ate the minestrone while it was still warm, and the bad ending did not win."
        )
    elif params.obstacle == "spill":
        world.say(
            f"{helper.id} wiped up the little spill and fixed the tray with a grin."
        )
        soup.meters["ready"] += 1.0
        hero.memes["joy"] += 1.0
        world.say(
            f"Then {hero.id} got the bowl, and the Quest ended with a happy slurp."
        )
    else:
        world.say(
            f"{helper.id} swapped the sugar and salt back again, and everyone giggled at the mistake."
        )
        soup.meters["ready"] += 1.0
        hero.memes["joy"] += 1.0
        world.say(
            f"After that, the minestrone tasted right, and the room felt bright and silly."
        )

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        "Write a short comedy story about a Quest for minestrone that almost turns into a Bad Ending.",
        f"Tell a child-friendly story where {hero.id} and {helper.id} try to get minestrone, but something has to be fixed first.",
        "Write a funny story that uses the words minestrone, illustrious, and linger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    soup = f["soup"]
    obstacle = f["obstacle"]

    return [
        QAItem(
            question=f"What was {hero.id}'s Quest about?",
            answer=f"{hero.id}'s Quest was about getting {soup.phrase} in {SETTING_NAME}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the minestrone?",
            answer=f"{helper.id} helped {hero.id}, and that made the Quest feel less serious and more funny.",
        ),
        QAItem(
            question=f"What made the story feel like a comedy?",
            answer=f"The silly delay from {obstacle.label} made everyone pause, laugh, and try again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is minestrone?",
            answer="Minestrone is a warm soup with vegetables and broth, often served in a bowl.",
        ),
        QAItem(
            question="What does illustrious mean?",
            answer="Illustrious means famous, shining, or very impressive in a proud and special way.",
        ),
        QAItem(
            question="What does linger mean?",
            answer="To linger means to stay around longer than expected or to take extra time before leaving.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or mission to find something important.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about minestrone, a Quest, and a bad ending that gets fixed.")
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--quest-item", choices=QUEST_ITEMS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
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
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    quest_item = args.quest_item or "minestrone"
    obstacle = args.obstacle or rng.choice(list(OBSTACLES))
    if hero_name == helper_name:
        raise StoryError("Hero and helper must be different characters.")
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        quest_item=quest_item,
        obstacle=obstacle,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
quest(H) :- hero(H).
comedy_story(H) :- quest(H), has_minestrone, not bad_ending.
bad_ending :- obstacle(linger), soup_lingers.
has_minestrone :- item(minestrone).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in HERO_NAMES:
        lines.append(asp.fact("name", name))
    for item in QUEST_ITEMS:
        lines.append(asp.fact("item", item))
    for key in OBSTACLES:
        lines.append(asp.fact("obstacle", key))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("has_minestrone"))
    lines.append(asp.fact("soup_lingers"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Reasonableness gate: one valid comedy quest domain, plus a sanity solve.
    import asp
    model = asp.one_model(asp_program("#show comedy_story/1."))
    if not model:
        print("MISMATCH: ASP produced no model.")
        return 1
    print("OK: ASP program is solvable and the twin is present.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(
        hero_name="Maya",
        hero_type="girl",
        helper_name="Mimi",
        helper_type="aunt",
        quest_item="minestrone",
        obstacle="linger",
    ),
    StoryParams(
        hero_name="Theo",
        hero_type="boy",
        helper_name="Papa",
        helper_type="father",
        quest_item="minestrone",
        obstacle="spill",
    ),
    StoryParams(
        hero_name="Lina",
        hero_type="girl",
        helper_name="Sage",
        helper_type="friend",
        quest_item="minestrone",
        obstacle="mixup",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show comedy_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show comedy_story/1."))
        print(sorted(asp.atoms(model, "comedy_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.quest_item} / {p.obstacle}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
