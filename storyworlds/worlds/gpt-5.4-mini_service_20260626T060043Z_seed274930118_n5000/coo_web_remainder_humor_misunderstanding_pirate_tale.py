#!/usr/bin/env python3
"""
A small pirate tale storyworld about a bird's coo, a sticky web, and the
remainder of a treasure share.

The core premise is a friendly misunderstanding aboard a tiny pirate ship:
the crew hears a coo in the rigging, mistakes the source, and discovers that
the "remainder" of the map isn't a leftover at all, but a clue hidden in a web.
The humor comes from the mix-up, and the resolution comes from the crew
carefully untangling what the sounds and scraps really mean.
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
    owner: Optional[str] = None
    carrier: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pirate", "sailor", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"captainess", "pirateess", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str = "the Wobblefin"
    setting: str = "on the little pirate ship"
    has_rigging: bool = True
    has_hold: bool = True


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mira"
    hero_type: str = "captain"
    mate_name: str = "Patch"
    mate_type: str = "pirate"
    bird_name: str = "Pip"
    bird_type: str = "seabird"


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.ship)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _story_opening(world: World, hero: Entity, mate: Entity, bird: Entity) -> None:
    world.say(
        f"On {world.ship.name}, little {hero.id} was a brave {hero.type} who loved "
        f"shining maps and silly sea tales."
    )
    world.say(
        f"{mate.id}, {mate.pronoun('subject')} stayed close by with a grin, and "
        f"{bird.id} the {bird.type} perched in the rigging, ready to coo."
    )


def _story_setup(world: World, hero: Entity, mate: Entity, bird: Entity) -> None:
    hero.memes["curiosity"] = 1
    mate.memes["cheer"] = 1
    bird.memes["play"] = 1
    world.say(
        f"The crew was hunting for the remainder of an old treasure share: the "
        f"last scrap of map that should have told them where to sail."
    )
    world.say(
        f"But whenever the wind went soft, {bird.id} gave a happy coo, and the "
        f"sound bounced across the deck like a tiny drumbeat."
    )


def _misunderstanding(world: World, hero: Entity, mate: Entity, bird: Entity) -> None:
    hero.memes["confusion"] = hero.memes.get("confusion", 0) + 1
    mate.memes["confusion"] = mate.memes.get("confusion", 0) + 1
    world.say(
        f"{mate.id} squinted upward and said, 'A coo! The captain's got a clue!' "
        f"But {hero.id} laughed, because {bird.id} was only talking to the waves."
    )
    world.say(
        f"Still, the crew searched the ropes, the barrels, and the wheel, looking "
        f"for the missing remainder of the map."
    )


def _discover_web(world: World, hero: Entity, mate: Entity, bird: Entity) -> None:
    world.say(
        f"Then {hero.id} noticed a silver web tucked beside the mast, sparkling "
        f"with a tiny folded strip caught in the threads."
    )
    world.say(
        f"It was not a leftover crumb at all. It was the remainder they needed: a "
        f"slip of map stuck fast in the web."
    )
    world.facts["web_found"] = True
    world.facts["remainder_found"] = True
    world.facts["coo_source"] = bird.id
    world.facts["misunderstanding"] = True


def _resolve(world: World, hero: Entity, mate: Entity, bird: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    mate.memes["joy"] = mate.memes.get("joy", 0) + 1
    hero.memes["confusion"] = 0
    mate.memes["confusion"] = 0
    world.say(
        f"{mate.id} laughed so hard {mate.pronoun('subject')} nearly dropped the "
        f"spyglass. 'We chased a coo and found a web!' {mate.pronoun('subject').capitalize()} said."
    )
    world.say(
        f"{hero.id} carefully freed the map scrap, and {bird.id} cooed again as if "
        f"{bird.pronoun('subject')} approved of the joke."
    )
    world.say(
        f"By sunset, the crew had stitched the scrap into the full chart and set "
        f"sail with a grin, the little mystery solved at last."
    )
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = World(Ship())
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type))
    mate = world.add(Entity(id=params.mate_name, kind="character", type=params.mate_type))
    bird = world.add(Entity(id=params.bird_name, kind="character", type=params.bird_type))
    world.facts.update(hero=hero, mate=mate, bird=bird)

    _story_opening(world, hero, mate, bird)
    world.para()
    _story_setup(world, hero, mate, bird)
    _misunderstanding(world, hero, mate, bird)
    world.para()
    _discover_web(world, hero, mate, bird)
    _resolve(world, hero, mate, bird)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    mate = world.facts["mate"]
    bird = world.facts["bird"]
    return [
        f"Write a short pirate tale for a small child about {hero.id}, {mate.id}, and {bird.id}, including a coo and a web.",
        f"Tell a funny shipboard story where a pirate hears a coo, mistakes it, and finds the remainder of a map in a web.",
        f"Write a gentle pirate adventure with a misunderstanding, a tiny joke, and a happy ending at sea.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    mate = world.facts["mate"]
    bird = world.facts["bird"]
    return [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"The story was mostly about {hero.id}, the little {hero.type}, sailing with {mate.id} and {bird.id}.",
        ),
        QAItem(
            question=f"What did {bird.id} keep doing that caused the funny mix-up?",
            answer=f"{bird.id} kept giving a soft coo from the rigging, and the crew thought it might be a clue.",
        ),
        QAItem(
            question="What did the crew think they were searching for?",
            answer="They thought they were searching for the remainder of the treasure map, the last missing scrap.",
        ),
        QAItem(
            question="Where did they finally find that scrap?",
            answer="They found it caught in a silver web beside the mast.",
        ),
        QAItem(
            question="Why was it funny?",
            answer="It was funny because the crew misheard the bird's coo as a clue, but the real clue was hidden in the web.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a web?",
            answer="A web is sticky silk made by a spider, and it can catch small things that drift into it.",
        ),
        QAItem(
            question="What does coo mean?",
            answer="A coo is a soft, gentle bird sound.",
        ),
        QAItem(
            question="What is a remainder?",
            answer="A remainder is what is left over after the rest is gone or already used.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: type={ent.type} meters={meters} memes={memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    lines.append(asp.fact("setting", "ship"))
    lines.append(asp.fact("feature", "humor"))
    lines.append(asp.fact("feature", "misunderstanding"))
    lines.append(asp.fact("word", "coo"))
    lines.append(asp.fact("word", "web"))
    lines.append(asp.fact("word", "remainder"))
    lines.append(asp.fact("can_sound", "bird", "coo"))
    lines.append(asp.fact("can_hold", "web", "remainder"))
    lines.append(asp.fact("can_cause", "misunderstanding", "coo"))
    return "\n".join(lines)


ASP_RULES = r"""
shown(humor) :- feature(humor).
shown(misunderstanding) :- feature(misunderstanding).
shown(tale) :- word(coo), word(web), word(remainder).
shown(revealed_remainder) :- can_hold(web, remainder), can_cause(misunderstanding, coo).
#show shown/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_model_atoms() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show shown/1."))
    return sorted(set(asp.atoms(model, "shown")))


def asp_verify() -> int:
    expected = {("humor",), ("misunderstanding",), ("tale",), ("revealed_remainder",)}
    got = set(asp_model_atoms())
    if got == expected:
        print(f"OK: ASP parity verified ({len(got)} atoms).")
        return 0
    print("MISMATCH:")
    print("got:", sorted(got))
    print("expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a coo, a web, and a remainder.")
    ap.add_argument("--name")
    ap.add_argument("--mate")
    ap.add_argument("--bird")
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
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(["Mira", "Nell", "Jory", "Rae", "Finn"]),
        hero_type="captain",
        mate_name=args.mate or rng.choice(["Patch", "Moss", "Brine", "Wren"]),
        mate_type="pirate",
        bird_name=args.bird or rng.choice(["Pip", "Coco", "Skim", "Twee"]),
        bird_type="seabird",
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show shown/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{x[0]}" for x in asp_model_atoms()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        seeds = [base_seed + i for i in range(5)]
    else:
        seeds = [base_seed + i for i in range(args.n)]

    seen: set[str] = set()
    for i, seed in enumerate(seeds):
        rng = random.Random(seed)
        params = resolve_params(args, rng)
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
