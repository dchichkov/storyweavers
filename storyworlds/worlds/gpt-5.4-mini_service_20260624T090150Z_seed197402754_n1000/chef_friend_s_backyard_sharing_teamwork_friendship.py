#!/usr/bin/env python3
"""
chef_friend_s_backyard_sharing_teamwork_friendship.py
=====================================================

A small fable-like storyworld about a chef visiting a friend's backyard,
where sharing and teamwork turn a tricky cookout into a warm friendship story.

Premise:
- A chef arrives with ingredients and a plan.
- A friend in the backyard wants to help.
- A problem appears: one bowl, many hands, and not enough food ready.

Turn:
- The chef learns to share the work.
- The friend contributes a backyard-grown ingredient.
- Together they cook a simple dish without waste.

Resolution:
- The meal is enough for both.
- Friendship grows because each person gave and received help.

This file is self-contained and uses only stdlib plus the shared result/ASP
helpers from the Storyweavers repo.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"chef", "man", "boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl", "mother", "friend"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "a friend's backyard"
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Dish:
    id: str
    label: str
    phrase: str
    servings: int
    base_need: dict[str, float]
    requires_share: bool = True


@dataclass
class HelperTool:
    id: str
    label: str
    use: str
    helps: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _safe_add_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _safe_add_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    # shared bowl: if one person starts with the bowl, the other must ask to share
    bowl = world.entities.get("bowl")
    chef = world.entities.get("chef")
    friend = world.entities.get("friend")
    if bowl and chef and friend:
        if bowl.carried_by == chef.id and world.facts.get("asked_share") and ("share",) not in world.fired:
            world.fired.add(("share",))
            _safe_add_meme(chef, "generosity", 1)
            _safe_add_meme(friend, "trust", 1)
            out.append("The chef smiled and shared the bowl.")
        if bowl.carried_by == friend.id and world.facts.get("asked_share") and ("share2",) not in world.fired:
            world.fired.add(("share2",))
            _safe_add_meme(friend, "generosity", 1)
            _safe_add_meme(chef, "trust", 1)
            out.append("The friend passed the bowl back with a smile.")
    # teamwork: when both helped and ingredients are enough, dish is ready
    dish = world.entities.get("dish")
    if dish and world.facts.get("mixed") and ("ready",) not in world.fired:
        if world.facts.get("ingredient_total", 0.0) >= THRESHOLD and world.facts.get("shared_work", False):
            world.fired.add(("ready",))
            _safe_add_meme(chef, "joy", 1)
            _safe_add_meme(friend, "joy", 1)
            out.append("Together, they made the meal ready.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness_gate(dish: Dish, setting: Setting) -> bool:
    return "bowl" in setting.affords and dish.servings >= 2


def build_world(dish: Dish, setting: Setting) -> World:
    world = World(setting)
    chef = world.add(Entity(id="chef", kind="character", type="chef", label="the chef"))
    friend = world.add(Entity(id="friend", kind="character", type="friend", label="the friend"))
    bowl = world.add(Entity(id="bowl", type="bowl", label="a big bowl", carried_by="chef"))
    dish_ent = world.add(Entity(id="dish", type="dish", label=dish.label, phrase=dish.phrase))
    herbs = world.add(Entity(id="herbs", type="ingredient", label="fresh herbs", owner="friend"))
    world.facts.update(chef=chef, friend=friend, bowl=bowl, dish=dish_ent, herbs=herbs, setting=setting, dish_cfg=dish)
    return world


def _mix(world: World, actor: Entity, ingredient: Entity, amount: float = 1.0) -> None:
    _safe_add_meter(actor, "work", amount)
    _safe_add_meter(ingredient, "used", amount)
    world.facts["mixed"] = True
    total = world.facts.get("ingredient_total", 0.0) + amount
    world.facts["ingredient_total"] = total
    if total >= THRESHOLD:
        _safe_add_meme(actor, "pride", 1)
    propagate(world, narrate=True)


def tell_story(world: World, dish: Dish) -> None:
    chef = world.get("chef")
    friend = world.get("friend")
    bowl = world.get("bowl")
    herbs = world.get("herbs")

    world.say("A chef came to a friend's backyard with a recipe and a bright bowl.")
    world.say("The friend brought a smile, and the air smelled like a small feast waiting to happen.")
    world.say(f'The chef said, "{dish.phrase} will be enough if we work with care."')
    world.para()

    bowl.carried_by = chef.id
    _safe_add_meme(chef, "duty", 1)
    _safe_add_meme(friend, "eagerness", 1)
    world.say("But the chef had only one bowl, and the recipe needed two hands.")
    world.say("The friend wanted to help, yet the chef first tried to do everything alone.")
    _safe_add_meme(chef, "worry", 1)
    world.say("Soon the spoon bumped the rim, and the herbs waited on the table.")
    world.para()

    world.say("Then the friend pointed to the backyard patch and picked a few fresh herbs.")
    _safe_add_meter(herbs, "picked", 1)
    world.say("The chef paused, noticed the kind offer, and asked to share the bowl.")
    world.facts["asked_share"] = True
    bowl.carried_by = friend.id
    world.say("The friend nodded, and at once both of them found a place to help.")
    world.facts["shared_work"] = True
    propagate(world, narrate=True)
    world.para()

    _mix(world, chef, herbs, amount=1.0)
    world.say("The friend stirred while the chef tasted, and the soup grew warm and fragrant.")
    _safe_add_meter(friend, "stir", 1)
    world.facts["ingredient_total"] = world.facts.get("ingredient_total", 0.0) + 1.0
    world.facts["mixed"] = True
    propagate(world, narrate=True)

    world.say(f"At last, {dish.phrase} was ready for two.")
    world.say("The chef served the first bowl to the friend, and the friend shared the last spoonful back.")
    _safe_add_meme(chef, "friendship", 1)
    _safe_add_meme(friend, "friendship", 1)
    world.say("In that backyard, sharing made the meal bigger, and teamwork made the friendship stronger.")


@dataclass
class StoryParams:
    dish: str
    seed: Optional[int] = None


SETTINGS = {
    "friend_backyard": Setting(place="a friend's backyard", outdoors=True, affords={"bowl", "garden"}),
}

DISHES = {
    "herb_soup": Dish(
        id="herb_soup",
        label="herb soup",
        phrase="a pot of herb soup",
        servings=2,
        base_need={"ingredients": 2.0},
        requires_share=True,
    ),
    "berry_mash": Dish(
        id="berry_mash",
        label="berry mash",
        phrase="a bowl of berry mash",
        servings=2,
        base_need={"ingredients": 2.0},
        requires_share=True,
    ),
}

KNOWN_FACTS = {
    "sharing": [
        ("What is sharing?", "Sharing means giving some of what you have so someone else can use or enjoy it too."),
        ("Why do people share food?", "People share food so everyone can have enough and feel cared for."),
    ],
    "teamwork": [
        ("What is teamwork?", "Teamwork is when people work together and each person helps with part of the job."),
        ("Why does teamwork help?", "Teamwork helps because two careful helpers can do more than one helper alone."),
    ],
    "friendship": [
        ("What is friendship?", "Friendship is a kind relationship where people care about each other and like helping each other."),
        ("Why are friends kind?", "Friends are kind because they want each other to feel happy and safe."),
    ],
}

ASP_RULES = r"""
dish_ready(D) :- shared_work, enough_ingredients(D).
good_story(D) :- dish(D), dish_ready(D).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for did, dish in DISHES.items():
        lines.append(asp.fact("dish", did))
        lines.append(asp.fact("servings", did, dish.servings))
    lines.append(asp.fact("shared_work"))
    lines.append(asp.fact("enough_ingredients", "herb_soup"))
    lines.append(asp.fact("enough_ingredients", "berry_mash"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like chef and friend storyworld.")
    ap.add_argument("--dish", choices=sorted(DISHES))
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
    dish = args.dish or rng.choice(sorted(DISHES))
    if not reasonableness_gate(DISHES[dish], SETTINGS["friend_backyard"]):
        raise StoryError("This story needs a dish that can be shared by two helpers.")
    return StoryParams(dish=dish)


def generation_prompts(world: World) -> list[str]:
    dish = world.facts["dish_cfg"]
    return [
        f"Write a small fable about a chef and a friend sharing work in a backyard to make {dish.phrase}.",
        f"Tell a gentle story where the chef learns teamwork and friendship while cooking {dish.label}.",
        f"Write a child-friendly fable in a friend's backyard that shows sharing, teamwork, and friendship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    dish = world.facts["dish_cfg"]
    chef = world.get("chef")
    friend = world.get("friend")
    return [
        QAItem(
            question=f"Who came to the friend's backyard to make {dish.label}?",
            answer=f"The chef came to the friend's backyard to make {dish.phrase}."
        ),
        QAItem(
            question="Why did the chef stop trying to do everything alone?",
            answer="The chef stopped because the work went better when the friend helped and they shared the bowl."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with the meal ready, both helpers smiling, and friendship growing stronger."
        ),
        QAItem(
            question=f"What did {friend.id} add from the backyard?",
            answer="The friend picked fresh herbs from the backyard and gave them to the chef."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in KNOWN_FACTS["sharing"] + KNOWN_FACTS["teamwork"] + KNOWN_FACTS["friendship"]]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== (1) Generation prompts ==")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    dish = DISHES[params.dish]
    world = build_world(dish, SETTINGS["friend_backyard"])
    tell_story(world, dish)
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


def valid_combos() -> list[tuple[str]]:
    return [(did,) for did in DISHES if reasonableness_gate(DISHES[did], SETTINGS["friend_backyard"])]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def explain_rejection(dish: Dish) -> str:
    return f"(No story: {dish.label} does not fit the shared-work pattern for this backyard fable.)"


def resolve_story(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/1."))
        print(f"{len(set(asp.atoms(model, 'good_story')))} compatible story shape(s).")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for did in sorted(DISHES):
            params = StoryParams(dish=did, seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_story(args, random.Random(seed))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
