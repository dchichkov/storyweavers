#!/usr/bin/env python3
"""
storyworlds/worlds/strengthen_food_dim_misunderstanding_friendship_tall_tale.py
===============================================================================

A standalone storyworld for a tall-tale-style friendship story built from the
seed words "strengthen" and "food-dim".

Premise:
- A small child and a big-hearted friend prepare a feast for a wide river-town.
- A misunderstanding makes one of them think "strengthen the food-dim" means to
  make the meal dimmer, when it actually means to strengthen the serving stand
  so the feast can travel safely.
- Friendship turns the mistake into a tall-tale solution: they build a stronger
  cart, keep the food bright, and share the meal with the whole town.

This file is self-contained, uses only stdlib plus the shared storyworld results
container, and includes a Python reasonableness gate plus an inline ASP twin.
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


THRESHOLD = 1.0
STRENGTH_GOAL = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    name: str
    detail: str
    food_dim: str
    crossing: str
    town: str


@dataclass
class Meal:
    label: str
    phrase: str
    bright: str
    flavor: str
    warms: bool = True


@dataclass
class FriendTool:
    id: str
    label: str
    phrase: str
    strength: float
    helps: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_strengthen(world: World) -> list[str]:
    out: list[str] = []
    cart = world.entities.get("cart")
    helper = world.entities.get("friend")
    if not cart or not helper:
        return out
    if cart.meters.get("weak", 0.0) >= THRESHOLD and helper.memes.get("care", 0.0) >= THRESHOLD:
        sig = ("strengthen",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        cart.meters["strong"] = cart.meters.get("strong", 0.0) + 1.0
        cart.meters["weak"] = 0.0
        out.append("__strengthened__")
    return out


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    speaker = world.entities.get("child")
    if not speaker:
        return out
    if speaker.memes.get("confused", 0.0) >= THRESHOLD:
        sig = ("confusion",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        speaker.memes["worry"] = speaker.memes.get("worry", 0.0) + 1.0
        out.append("__confused__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_strengthen, _r_confusion):
            got = fn(world)
            if got:
                changed = True
                out.extend(g for g in got if not g.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_cart(world: World) -> bool:
    sim = world.copy()
    sim.get("cart").meters["weak"] = 1.0
    sim.get("friend").memes["care"] = 1.0
    propagate(sim, narrate=False)
    return sim.get("cart").meters.get("strong", 0.0) >= STRENGTH_GOAL - 1.0


def valid_setup(place: Place, meal: Meal, tool: FriendTool) -> bool:
    return meal.warms and tool.strength >= 1.0 and "river" in place.detail.lower()


@dataclass
class StoryParams:
    place: str
    meal: str
    tool: str
    child_name: str
    friend_name: str
    seed: Optional[int] = None


PLACES = {
    "river_town": Place(
        name="River Town",
        detail="a river town with a long plank bridge and a windy landing",
        food_dim="food-dim",
        crossing="bridge",
        town="town",
    ),
    "hill_market": Place(
        name="Hill Market",
        detail="a hill market with a long ramp and a narrow stall row",
        food_dim="food-dim",
        crossing="ramp",
        town="market",
    ),
}

MEALS = {
    "stew": Meal("stew", "a big pot of stew", "bright steam", "rich"),
    "cornbread": Meal("cornbread", "a basket of cornbread", "golden crust", "sweet"),
}

TOOLS = {
    "rope": FriendTool("rope", "rope", "a coil of rope", 2.0, "tie the cart beams together"),
    "planks": FriendTool("planks", "planks", "three long planks", 2.5, "brace the cart wheels"),
}

GIRL_NAMES = ["Mina", "Lena", "Tess", "Nora", "Mabel"]
BOY_NAMES = ["Otis", "Pip", "Bram", "Jory", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for m in MEALS:
            for t in TOOLS:
                if valid_setup(PLACES[p], MEALS[m], TOOLS[t]):
                    out.append((p, m, t))
    return out


def explain_rejection() -> str:
    return "(No story: this tale needs a river-town crossing, a warming meal, and a tool that can truly strengthen the cart.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale friendship storyworld with a misunderstanding and a strong ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--meal", choices=MEALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.meal is None or c[1] == args.meal)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError(explain_rejection())
    p, m, t = rng.choice(sorted(combos))
    return StoryParams(
        place=p,
        meal=m,
        tool=t,
        child_name=args.name or rng.choice(GIRL_NAMES + BOY_NAMES),
        friend_name=args.friend or rng.choice(GIRL_NAMES + BOY_NAMES),
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    meal = MEALS[params.meal]
    tool = TOOLS[params.tool]
    world = World(place)
    child = world.add(Entity("child", kind="character", type="child", label=params.child_name))
    friend = world.add(Entity("friend", kind="character", type="child", label=params.friend_name, role="friend"))
    cart = world.add(Entity("cart", label="wagon cart", meters={"weak": 1.0}, attrs={"place": place.name}))
    basket = world.add(Entity("basket", label=meal.label, meters={"bright": 1.0}))

    child.memes["desire"] = 1.0
    child.memes["confused"] = 1.0
    friend.memes["care"] = 1.0
    friend.memes["trust"] = 1.0

    world.say(f"{child.label_word} and {friend.label_word} were as friendly as two barn owls on a fencepost. In {place.name}, they had a feast to carry across the {place.crossing}.")
    world.say(f"They loaded {meal.phrase} onto the wagon cart, and the steam rose {meal.bright} into the air like a little sunrise.")
    world.say(f"Then {child.label_word} heard a funny phrase: \"We should strengthen the {place.food_dim}!\"")
    world.say(f"{child.label_word} thought that meant to make the food dim and smaller, so {child.label_word} reached for the lantern cloth and began to fuss with the pot.")

    world.para()
    world.say(f"{friend.label_word} laughed kindly and shook {friend.pronoun('possessive')} head. \"No, friend. We mean strengthen the cart, not dim the food.\"")
    world.say(f"That was the tall-tale misunderstanding: the meal stayed bright, and the wagon needed the helping more than the supper did.")

    world.para()
    child.memes["confused"] += 1.0
    cart.meters["weak"] = 1.0
    propagate(world, narrate=False)
    if cart.meters.get("strong", 0.0) < STRENGTH_GOAL:
        cart.meters["strong"] = 0.0
    world.say(f"So {friend.label_word} brought out {tool.phrase} and showed how to {tool.helps}.")
    world.say(f"With one push, the cart stood straighter than a pine in a thunderstorm, and the load stopped wobbling.")

    world.para()
    world.say(f"Then the two friends rolled the feast over the {place.crossing} together.")
    world.say(f"The cart did not buckle, the meal did not dim, and the whole {place.town} came out to cheer when {meal.label} arrived warm and shining.")

    world.facts.update(
        child=child,
        friend=friend,
        cart=cart,
        basket=basket,
        place=place,
        meal=meal,
        tool=tool,
        strengthened=cart.meters.get("strong", 0.0) >= STRENGTH_GOAL - 1.0,
        misunderstood=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale friendship story about {f["child"].label_word} and {f["friend"].label_word} using the word "strengthen".',
        f'Tell a child-friendly misunderstanding story where someone thinks "{world.place.food_dim}" means making the meal dim, but the friends really need to strengthen the cart.',
        f'Write a windy, oversized little tale in which two friends save a feast and prove that friendship can strengthen a wobbly wagon.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, fr, meal, place, tool = f["child"], f["friend"], f["meal"], f["place"], f["tool"]
    return [
        QAItem(
            question=f"What misunderstanding did {c.label_word} have about the phrase '{place.food_dim}'?",
            answer=f"{c.label_word} thought it meant to make the meal dim and smaller, but the friends really meant to strengthen the cart for the crossing.",
        ),
        QAItem(
            question=f"How did {fr.label_word} help after the mistake?",
            answer=f"{fr.label_word} smiled, explained the meaning, and used {tool.phrase} to {tool.helps}. That turned the mistake into a helper for the feast.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The cart grew strong, the meal stayed bright, and the whole {place.town} got to share {meal.phrase}. The friendship made the ending bigger and better than the beginning.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does strengthen mean?",
            answer="To strengthen something means to make it stronger, steadier, or harder to break.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone hears or thinks the wrong meaning first, and then learns the right one.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and stay kind even when someone makes a mistake.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} label={e.label}")
    return "\n".join(lines)


ASP_RULES = r"""
strong_cart :- weak(cart), caring(friend).
misunderstanding :- confused(child).
resolved :- strong_cart, misunderstanding.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("weak", "cart"),
        asp.fact("caring", "friend"),
        asp.fact("confused", "child"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show strong_cart/0.\n#show misunderstanding/0.\n#show resolved/0."))
    atoms = {sym.name for sym in model}
    ok = {"strong_cart", "misunderstanding", "resolved"} <= atoms
    print("OK: ASP twin runs." if ok else "MISMATCH: ASP twin did not derive expected atoms.")
    return 0 if ok else 1


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show strong_cart/0."))
    return [tuple() for sym in model if sym.name == "strong_cart"]


CURATED = [
    StoryParams("river_town", "stew", "rope", "Mina", "Otis"),
    StoryParams("river_town", "cornbread", "planks", "Tess", "Bram"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show strong_cart/0.\n#show misunderstanding/0.\n#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP twin is present.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        print(s.story)
        if args.trace:
            print(dump_trace(s.world))
        if args.qa:
            print()
            print(format_qa(s))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
