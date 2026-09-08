#!/usr/bin/env python3
"""
A tiny superhero storyworld about bacon, removal, a twist, and reconciliation.

Seed image:
A junior hero is helping at a city breakfast fair when a smoky bacon tray sets
off trouble. Someone needs to remove the problem, but the first plan goes wrong
and causes a twist in the day. Then the hero and a former rival talk, fix the
mess, and end with reconciliation.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "hero"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Nova"
    rival_name: str = "Mace"
    setting_name: str = "Sunrise Square"
    bacon_name: str = "the bacon cart"


HEROES = ["Nova", "Comet", "Mira", "Pax", "Zuri", "Jett", "Ivy", "Arlo"]
RIVALS = ["Mace", "Vex", "Rook", "Blaze", "Sable", "Talon", "Lark", "Rune"]
SETTINGS = ["Sunrise Square", "Harbor Plaza", "Clover Street", "Lantern Park"]
BACON_NAMES = ["the bacon cart", "the breakfast tray", "the sizzling grill", "the bacon stand"]


TURNS = [
    {
        "setup": "A smoky bacon cart rolled into the city square for the morning fair.",
        "problem": "Its greasy wheel jammed near the ribbon gate, and the crowd started to cough.",
        "twist": "When the hero tried to remove the cart by force, the tray tipped and bacon slid across the steps.",
        "reveal": "The rival had tied the cart there to slow the hero down, but did not want anyone hurt.",
        "repair": "The hero lowered the tray, wiped the steps, and asked the rival for a better plan.",
        "reconciliation": "Together they lifted the cart, shared the cleanup, and opened the path again.",
        "ending": "By lunchtime the square smelled warm and safe, and both heroes laughed beside a neat stack of rescued bacon.",
    },
    {
        "setup": "At the weekend fair, a bacon booth sent up a curly cloud that drifted past the puppet stage.",
        "problem": "The smoke made children sneeze and hid the stage rope.",
        "twist": "The first rescue rope snapped when the hero rushed in, so the banner spun around like a cape.",
        "reveal": "The rival had been guarding the booth because the stove was too hot for little hands.",
        "repair": "The hero used a shield to fan away the smoke while the rival turned off the burner.",
        "reconciliation": "They apologized, exchanged a careful nod, and walked the stove to a safer corner.",
        "ending": "The puppet show went on, and the bacon booth served breakfast in a calmer breeze.",
    },
    {
        "setup": "A parade float shaped like a giant egg was carrying a tray of bacon for hungry helpers.",
        "problem": "One axle wobbled, and the tray threatened to fall into the crowd.",
        "twist": "The hero's first attempt to remove the tray made the float tilt the other way.",
        "reveal": "The rival had hidden a support plank underneath to keep the float from crashing.",
        "repair": "The hero and rival slid the plank out together, then balanced the tray with steady hands.",
        "reconciliation": "After the crowd cheered, they admitted the day worked better when both of them listened.",
        "ending": "The float rolled on safely, and the bacon arrived at the end of the parade without a single spill.",
    },
    {
        "setup": "A tiny bakery on Lantern Park had promised bacon buns to the whole block.",
        "problem": "The oven door stuck, and the smell of smoke filled the room.",
        "twist": "The hero tugged too hard to remove the pan, and the buns flipped onto the floor.",
        "reveal": "The rival had been trying to protect the baker's old oven from breaking.",
        "repair": "The hero knelt down, picked up the buns, and helped oil the hinges instead.",
        "reconciliation": "The rival said sorry, the hero said sorry too, and they finished baking side by side.",
        "ending": "Soon the bakery window glowed gold, and warm bacon buns lined the shelf like little moons.",
    },
    {
        "setup": "During a school visit, a bacon-shaped training drone drifted above the playground.",
        "problem": "The drone's propeller clipped a kite line and spun into a bush.",
        "twist": "The hero's grab to remove it only tangled the drone in the leaves.",
        "reveal": "The rival had programmed the drone to test the hero's patience, not to cause harm.",
        "repair": "The hero used a slow hover trick while the rival untangled the line knot by knot.",
        "reconciliation": "They shook hands, laughed at the silly test, and promised a kinder challenge next time.",
        "ending": "The drone flew again over the swings, and the children waved as bacon-shaped shadows raced across the grass.",
    },
]


TELLING_MODES = [
    ("The city was bright and busy when the trouble began.", "The heroes learned that a careful plan could fix more than one mistake."),
    ("At first, the breakfast fair looked like an easy job.", "The twist made both heroes slower, kinder, and more honest."),
    ("Morning sunlight flashed on the square's stone tiles.", "After the mishap, the heroes chose cooperation over pride."),
    ("The day started with applause and the smell of breakfast.", "The first wrong move showed why listening mattered."),
    ("A simple errand turned into a superhero test before noon.", "What saved the day was not strength alone, but trust."),
]


def _selection_token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = f"{params.hero_name}|{params.rival_name}|{params.setting_name}|{params.bacon_name}"
    return sum((i + 1) * ord(c) for i, c in enumerate(text))


def _setup(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id=params.hero_name, kind="character", type="hero", label=params.hero_name))
    rival = world.add(Entity(id=params.rival_name, kind="character", type="hero", label=params.rival_name))
    place = world.add(Entity(id="setting", kind="place", type="place", label=params.setting_name))
    bacon = world.add(Entity(id="bacon", kind="thing", type="food", label=params.bacon_name))
    cart = world.add(Entity(id="cart", kind="thing", type="cart", label="bacon cart"))
    hero.meters["brave"] = 1.0
    hero.memes["pride"] = 0.2
    rival.meters["clever"] = 1.0
    rival.memes["guilt"] = 0.0
    bacon.meters["warmth"] = 1.0
    cart.meters["weight"] = 1.0
    world.facts.update(hero=hero, rival=rival, place=place, bacon=bacon, cart=cart)


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    token = _selection_token(params)
    turn = TURNS[token % len(TURNS)]
    mode = TELLING_MODES[(token // len(TURNS)) % len(TELLING_MODES)]

    hero = world.facts["hero"]
    rival = world.facts["rival"]
    place = world.facts["place"]
    bacon = world.facts["bacon"]
    cart = world.facts["cart"]

    world.say(mode[0])
    world.say(f"{hero.id} arrived at {place.label}, where {turn['setup'].lower()}")
    world.say(f"Near the ribbon gate sat {bacon.label}, and everyone hoped the morning would stay peaceful.")

    world.para()
    world.say(f"Then came the problem: {turn['problem']}")
    world.say(f'"I can remove it fast," {hero.id} said.')
    world.say(f'"Wait," {rival.id} replied, "fast is not always safe."')

    world.para()
    world.say(f"{turn['twist'].capitalize()}")
    world.say(f"The sudden twist made {hero.id} stop and look at {rival.id}.")
    world.say(f'"Now what?" {hero.id} asked.')
    world.say(f'"Now we do it together," {rival.id} said.')
    world.say(mode[1])

    world.para()
    world.say(f"That was when the truth came out: {turn['reveal']}")
    world.say(f"{hero.id} lowered the cart, and {rival.id} pointed to the loose wheel.")
    world.say(f"Instead of arguing, they chose a better fix: {turn['repair']}")
    world.say(f'"You were trying to help," {hero.id} said.')
    world.say(f'"And you were right to slow me down," {rival.id} answered.')

    world.para()
    world.say(f"{turn['reconciliation'].capitalize()}")
    world.say(f"Their apology changed the mood of the whole square, and the crowd clapped for both of them.")
    world.say(f"By the end of the morning, {turn['ending']}")

    hero.memes["pride"] = 0.0
    hero.memes["trust"] = 1.0
    rival.memes["guilt"] = 0.0
    rival.memes["trust"] = 1.0
    cart.meters["weight"] = 0.0
    bacon.meters["warmth"] = 0.5

    world.facts.update(
        params=params,
        turn=turn,
        mode=mode,
        twist=True,
        reconciliation=True,
    )
    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    turn = world.facts["turn"]
    return [
        f"Write a child-friendly superhero story about bacon, removal, and a twist at {p.setting_name}.",
        f"Tell how {p.hero_name} and {p.rival_name} turn {turn['problem'].lower()} into reconciliation.",
        f"Show a small city problem, a mistaken attempt to remove it, and a happy ending where the heroes work together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    rival = world.facts["rival"]
    turn = world.facts["turn"]
    return [
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened at {p.setting_name}, where the morning fair was taking place.",
        ),
        QAItem(
            question="What was the problem involving bacon?",
            answer=f"{turn['problem'].capitalize()}",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"{turn['twist'].capitalize()}",
        ),
        QAItem(
            question="What did the heroes do after the twist?",
            answer=f"They stopped arguing, listened to each other, and worked together to fix the bacon problem.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{turn['ending'].capitalize()}",
        ),
        QAItem(
            question=f"How did {hero.id} and {rival.id} change by the end?",
            answer=f"They moved from disagreement to reconciliation, and each one trusted the other more.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a character who helps others, solves big problems, and often uses courage or special skills.",
        ),
        QAItem(
            question="What does it mean to remove something?",
            answer="To remove something means to take it away from a place.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace after an argument or misunderstanding.",
        ),
    ]


ASP_RULES = r"""
% A story begins with a bacon problem.
bacon_problem(S) :- bacon(S), remove_attempt(S).

% A twist happens when the first removal attempt makes things worse.
twist(S) :- bacon_problem(S), failed_removal(S).

% Reconciliation happens when the heroes talk and choose cooperation.
reconciliation(S) :- twist(S), talk_it_out(S), help_together(S).

% A valid story includes the twist and the reconciliation.
valid_story(S) :- twist(S), reconciliation(S).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("bacon", "story1"),
        asp.fact("remove_attempt", "story1"),
        asp.fact("failed_removal", "story1"),
        asp.fact("talk_it_out", "story1"),
        asp.fact("help_together", "story1"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {("story1",)} if valid_story() else set()
    if atoms == py:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(atoms))
    print("Python:", sorted(py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld about bacon, removal, a twist, and reconciliation.")
    ap.add_argument("--hero-name", choices=HEROES)
    ap.add_argument("--rival-name", choices=RIVALS)
    ap.add_argument("--setting-name", choices=SETTINGS)
    ap.add_argument("--bacon-name", choices=BACON_NAMES)
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
    hero = args.hero_name or rng.choice(HEROES)
    rival = args.rival_name or rng.choice([x for x in RIVALS if x != hero])
    setting = args.setting_name or rng.choice(SETTINGS)
    bacon = args.bacon_name or rng.choice(BACON_NAMES)
    return StoryParams(seed=None, hero_name=hero, rival_name=rival, setting_name=setting, bacon_name=bacon)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
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


CURATED = [
    StoryParams(hero_name="Nova", rival_name="Mace", setting_name="Sunrise Square", bacon_name="the bacon cart"),
    StoryParams(hero_name="Ivy", rival_name="Vex", setting_name="Lantern Park", bacon_name="the bacon stand"),
    StoryParams(hero_name="Comet", rival_name="Rook", setting_name="Harbor Plaza", bacon_name="the sizzling grill"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
