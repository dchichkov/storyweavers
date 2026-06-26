#!/usr/bin/env python3
"""
A small superhero storyworld about teamwork, foreshadowing, and a classic rescue
with a sledge and a pot of linguini.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "hero"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    hero: str
    sidekick: str
    villain: str
    place: str
    team_tool: str
    prize: str
    seed: Optional[int] = None


HERO_NAMES = ["Nova", "Milo", "Ivy", "Tara", "Ezra", "Juno"]
SIDEKICK_NAMES = ["Pip", "Rue", "Bea", "Ollie", "Skye", "Luca"]
VILLAIN_NAMES = ["Captain Cloud", "Dr. Shade", "The Grumble Giant", "Mister Slip"]


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with teamwork and foreshadowing.")
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--villain")
    ap.add_argument("--place")
    ap.add_argument("--team-tool")
    ap.add_argument("--prize")
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
    place = args.place or rng.choice(["Old Harbor", "Bright City", "Moonbridge", "Pine Plaza"])
    team_tool = args.team_tool or rng.choice(["sledge", "classic grappling line", "signal mirror", "rope ladder"])
    prize = args.prize or rng.choice(["linguini", "the mayor's lunchbox", "the museum key", "a rescue cake"])
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    villain = args.villain or rng.choice(VILLAIN_NAMES)
    if "sledge" not in team_tool and "linguini" not in prize:
        raise StoryError("This world needs the seed words to matter: choose a sledge or linguini story.")
    return StoryParams(hero=hero, sidekick=sidekick, villain=villain, place=place, team_tool=team_tool, prize=prize)


def _story_name(p: StoryParams) -> str:
    return f"{p.hero} and {p.sidekick}"


def generate_world(p: StoryParams) -> World:
    w = World(p.place)
    hero = w.add(Entity(id="hero", kind="character", type="hero", label=p.hero))
    sidekick = w.add(Entity(id="sidekick", kind="character", type="hero", label=p.sidekick))
    villain = w.add(Entity(id="villain", kind="character", type="villain", label=p.villain))
    prize = w.add(Entity(id="prize", kind="thing", label=p.prize, owner="villain", caretaker="villain"))
    tool = w.add(Entity(id="tool", kind="thing", label=p.team_tool, owner="hero"))
    return w


def tell(world: World, p: StoryParams) -> World:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    villain = world.get("villain")
    prize = world.get("prize")
    tool = world.get("tool")

    world.say(f"{p.hero} was a classic little superhero who never gave up when trouble arrived in {p.place}.")
    world.say(f"{p.sidekick} was {hero.pronoun('possessive')} best teammate, and together they loved practicing teamwork.")
    world.say(f"One afternoon, {p.villain} rushed in and snatched a pot of {p.prize} from the town cart.")
    world.say(f"The cart was stuck under a heavy beam, and the beam looked older and shakier than it seemed at first.")

    world.para()
    world.say(f"Before anyone moved, {p.sidekick} noticed a cracked anchor hook beside the beam. That small clue was foreshadowing.")
    world.say(f'"If we pull the wrong way, the cart could tip," {p.sidekick} warned, and {p.hero} listened carefully.')
    world.say(f"{p.hero} grabbed {p.team_tool} while {p.sidekick} held the cart steady.")
    world.say(f"Working together, they used the {p.team_tool} like a lever and eased the cart free without breaking anything.")

    world.para()
    world.say(f"{p.villain} tried to dash away with the {p.prize}, but the heroes blocked the path.")
    world.say(f"{p.sidekick} distracted the villain, and {p.hero} lifted the prize back to safety.")
    world.say(f"In the end, the town kept its {p.prize}, the beam stayed in place, and the two teammates stood side by side like true heroes.")

    world.facts = {
        "hero": p.hero,
        "sidekick": p.sidekick,
        "villain": p.villain,
        "place": p.place,
        "team_tool": p.team_tool,
        "prize": p.prize,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story about {f['hero']} and {f['sidekick']} using teamwork to rescue {f['prize']}.",
        f"Tell a classic adventure where a sledge helps heroes in {f['place']} stop {f['villain']}.",
        f"Write a child-friendly story that includes foreshadowing, a team plan, and the word linguini.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who worked together in the story?",
            answer=f"{f['hero']} and {f['sidekick']} worked together as a team.",
        ),
        QAItem(
            question=f"What did the heroes use to help move the cart?",
            answer=f"They used a {f['team_tool']} to help move the cart safely.",
        ),
        QAItem(
            question=f"What did they rescue from {f['villain']}?",
            answer=f"They rescued the pot of {f['prize']} and kept it safe for the town.",
        ),
        QAItem(
            question=f"Why was the cracked hook important?",
            answer="It was foreshadowing, because it warned that the cart could tip if they pulled the wrong way.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together toward the same goal.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue that hints something important may happen later.",
        ),
        QAItem(
            question="What is a sledge?",
            answer="A sledge is a strong tool or sled-like object that can help move or lift heavy things.",
        ),
        QAItem(
            question="What is linguini?",
            answer="Linguini is a type of long, flat pasta that people often eat with sauce.",
        ),
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("tool", "sledge"),
            asp.fact("tool", "classic_grappling_line"),
            asp.fact("prize", "linguini"),
            asp.fact("prize", "museum_key"),
            asp.fact("place", "old_harbor"),
            asp.fact("place", "bright_city"),
            asp.fact("place", "moonbridge"),
            asp.fact("place", "pine_plaza"),
        ]
    )


ASP_RULES = r"""
compatible_story(Hero, Sidekick, Place, Tool, Prize) :-
    hero(Hero), sidekick(Sidekick), place(Place), tool(Tool), prize(Prize),
    team_ready(Tool), can_rescue(Tool, Prize).

hero(nova; milo; ivy; tara; ezra; juno).
sidekick(pip; rue; bea; ollie; skye; luca).
place(old_harbor; bright_city; moonbridge; pine_plaza).
tool(sledge; classic_grappling_line; signal_mirror; rope_ladder).
prize(linguini; the_mayors_lunchbox; the_museum_key; a_rescue_cake).

team_ready(sledge).
team_ready(classic_grappling_line).
can_rescue(sledge, linguini).
can_rescue(classic_grappling_line, the_mayors_lunchbox).
can_rescue(signal_mirror, the_museum_key).
can_rescue(rope_ladder, a_rescue_cake).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible_story/5."))
    clingo_set = set(asp.atoms(model, "compatible_story"))
    python_set = {
        ("Nova", "Pip", "old_harbor", "sledge", "linguini"),
        ("Milo", "Rue", "bright_city", "classic_grappling_line", "the_mayors_lunchbox"),
        ("Ivy", "Bea", "moonbridge", "signal_mirror", "the_museum_key"),
        ("Tara", "Ollie", "pine_plaza", "rope_ladder", "a_rescue_cake"),
        ("Ezra", "Skye", "old_harbor", "sledge", "linguini"),
        ("Juno", "Luca", "bright_city", "classic_grappling_line", "the_mayors_lunchbox"),
    }
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: kind={e.kind} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for title, items in [
            ("== Generation prompts ==", sample.prompts),
            ("== Story questions ==", sample.story_qa),
            ("== World questions ==", sample.world_qa),
        ]:
            print(title)
            for item in items:
                if isinstance(item, str):
                    print(item)
                else:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")
            print()


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    world = tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(hero="Nova", sidekick="Pip", villain="Captain Cloud", place="Old Harbor", team_tool="sledge", prize="linguini"),
    StoryParams(hero="Milo", sidekick="Rue", villain="Dr. Shade", place="Bright City", team_tool="classic grappling line", prize="the mayor's lunchbox"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.team_tool and args.prize and "sledge" in args.team_tool and "linguini" not in args.prize:
        raise StoryError("The sledge here is meant to foreshadow and solve a linguini rescue.")
    return StoryParams(
        hero=args.hero or rng.choice(HERO_NAMES),
        sidekick=args.sidekick or rng.choice(SIDEKICK_NAMES),
        villain=args.villain or rng.choice(VILLAIN_NAMES),
        place=args.place or rng.choice(["Old Harbor", "Bright City", "Moonbridge", "Pine Plaza"]),
        team_tool=args.team_tool or rng.choice(["sledge", "classic grappling line"]),
        prize=args.prize or rng.choice(["linguini", "the mayor's lunchbox"]),
    )


def format_json(samples: list[StorySample]) -> str:
    if len(samples) == 1:
        return samples[0].to_json()
    return json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/5."))
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        print(format_json(samples))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
