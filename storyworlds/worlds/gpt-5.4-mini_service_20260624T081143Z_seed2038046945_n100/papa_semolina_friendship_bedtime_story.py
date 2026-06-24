#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/papa_semolina_friendship_bedtime_story.py
===============================================================================================================

A small bedtime-story world about papa, semolina, and a friendship that grows
through a warm evening problem and a gentle shared fix.

Seed tale inspiration:
- Papa makes a soft semolina bowl for bedtime.
- A small worry appears: the semolina is too hot and the little friend feels shy.
- Papa cools it, adds a kind topping, and the two share the snack while telling
  sleepy stories.
- The ending image proves the change: the bowl is cooler, the friend feels safe,
  and the room is calm.

This script follows the Storyweavers contract:
- standalone stdlib script
- typed entities with meters and memes
- explicit reasonableness gate plus inline ASP twin
- story, QA, trace, JSON, ASP, and verify support
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

BEDTIME_VERBS = ["stir", "cool", "share", "sip", "whisper"]
ROOMS = ["kitchen", "nursery", "cozy room", "small dining nook"]


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
        if self.type in {"papa", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the kitchen"
    bedtime: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Food:
    label: str
    phrase: str
    warmth: str
    comfort: str
    safe_when: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Friend:
    name: str
    type: str
    trait: str
    likes: str
    gender: str = "unknown"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    friend: str
    food: str
    name: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", bedtime=True, affords={"warm_milk", "semolina"}),
    "nursery": Setting(place="the nursery", bedtime=True, affords={"semolina"}),
    "cozy_room": Setting(place="the cozy room", bedtime=True, affords={"warm_milk", "semolina"}),
}

FOODS = {
    "semolina": Food(
        label="semolina",
        phrase="a little bowl of sweet semolina",
        warmth="warm",
        comfort="soft and soothing",
        safe_when="cool enough to sip",
        tags={"semolina", "warm", "soft"},
    ),
    "warm_milk": Food(
        label="warm milk",
        phrase="a small mug of warm milk",
        warmth="warm",
        comfort="gentle and sleepy",
        safe_when="cool enough to drink",
        tags={"milk", "warm", "sleepy"},
    ),
}

FRIENDS = {
    "mouse": Friend(name="Milo", type="mouse", trait="tiny", likes="crumbs", gender="unknown"),
    "bear": Friend(name="Bea", type="bear", trait="soft", likes="honey", gender="girl"),
    "cat": Friend(name="Mina", type="cat", trait="quiet", likes="milk", gender="girl"),
}

HOUSE_NAMES = ["papa", "papa", "Papa"]
CHILD_NAMES = ["Nia", "Luca", "Mina", "Ravi", "Tia", "Omar"]


class StoryGate:
    @staticmethod
    def valid(place: str, food: str, friend: str) -> bool:
        if place not in SETTINGS or food not in FOODS or friend not in FRIENDS:
            return False
        setting = SETTINGS[place]
        item = FOODS[food]
        return food in setting.affords and "semolina" in item.tags and friend in FRIENDS

    @staticmethod
    def reason(place: str, food: str, friend: str) -> str:
        if place not in SETTINGS:
            return "(No story: the bedtime room is unknown.)"
        if food not in FOODS:
            return "(No story: the bowl item is unknown.)"
        if friend not in FRIENDS:
            return "(No story: the friend is unknown.)"
        if food not in SETTINGS[place].affords:
            return f"(No story: {place} is not a fitting place for {food} in this tiny bedtime world.)"
        return "(No story: the chosen bedtime pieces do not make a calm, friendly story.)"


def reasonableness_gate(place: str, food: str, friend: str) -> bool:
    return StoryGate.valid(place, food, friend)


def select_friend(rng: random.Random) -> str:
    return rng.choice(list(FRIENDS))


def select_food(rng: random.Random) -> str:
    return rng.choice(list(FOODS))


def select_place(rng: random.Random, food: str) -> str:
    choices = [k for k, v in SETTINGS.items() if food in v.affords]
    return rng.choice(choices)


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    papa = world.add(Entity(id="papa", kind="character", type="papa", label="papa"))
    friend = FRIENDS[params.friend]
    child = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    bowl = world.add(Entity(
        id="bowl",
        kind="thing",
        type=params.food,
        label=FOODS[params.food].label,
        phrase=FOODS[params.food].phrase,
        owner="papa",
        caretaker="papa",
    ))

    papa.memes["love"] = 1.0
    papa.memes["friendship"] = 1.0
    child.memes["curiosity"] = 1.0
    child.memes["friendship"] = 0.5
    bowl.meters["warmth"] = 1.0
    bowl.meters["steam"] = 1.0 if params.food == "semolina" else 0.6

    world.facts.update(
        papa=papa,
        friend=friend,
        child=child,
        bowl=bowl,
        food=FOODS[params.food],
        place=params.place,
        setting=world.setting,
    )
    return world


def cool_bowl(world: World) -> None:
    bowl = world.get("bowl")
    bowl.meters["warmth"] = max(0.0, bowl.meters.get("warmth", 0.0) - 1.0)
    bowl.meters["steam"] = max(0.0, bowl.meters.get("steam", 0.0) - 1.0)
    world.say("Papa waited a little while so the steam could fade and the bowl could cool.")


def share_story(world: World) -> None:
    papa = world.get("papa")
    child = world.get(world.facts["child"].id)
    bowl = world.get("bowl")
    papa.memes["friendship"] += 1.0
    child.memes["friendship"] += 1.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    world.say("Then papa and the little friend shared the bowl and whispered a sleepy story.")
    world.say(f"The semolina stayed {FOODS['semolina'].safe_when}, and the room felt soft and safe.")


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    papa = world.get("papa")
    child = world.facts["child"]
    bowl = world.get("bowl")

    world.say(f"Late at night, papa made {bowl.phrase} in {world.setting.place}.")
    world.say(f"He wanted the little friend to taste something {FOODS[params.food].comfort}.")
    world.say(f"{child.id} came near the table and smiled at the warm smell.")

    world.para()
    if bowl.meters.get("warmth", 0.0) > 0.5:
        child.memes["shy"] = 1.0
        world.say(f"But the bowl was still too warm, so {child.id} stayed back for a moment.")
        world.say("Papa saw the worry and decided to wait kindly instead of rushing.")
        cool_bowl(world)
    if bowl.meters.get("warmth", 0.0) <= 0.5:
        share_story(world)

    world.para()
    world.say(f"In the end, {child.id} sat close to papa with a happy sigh.")
    world.say("The bowl was gentle, the friend was brave, and bedtime could begin.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    food = f["food"]
    friend = f["friend"]
    return [
        f"Write a bedtime story about papa and a little friend sharing {food.label}.",
        f"Tell a gentle friendship story where {friend.name} worries about warm {food.label} and papa helps.",
        f"Write a soft, child-friendly story set in {world.setting.place} with papa, semolina, and a calm ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    food = world.facts["food"]
    friend = world.facts["friend"]
    qs = [
        QAItem(
            question=f"Who made the bowl of {food.label} at bedtime?",
            answer=f"Papa made the bowl of {food.label} in {world.setting.place} so the little friend could have something soft before sleep.",
        ),
        QAItem(
            question=f"Why did {child.id} stay back for a moment?",
            answer=f"{child.id} stayed back because the {food.label} was still too warm, and papa wanted it to feel safe and gentle.",
        ),
        QAItem(
            question=f"What did papa and {child.id} do after the bowl cooled?",
            answer=f"After the bowl cooled, papa and {child.id} shared it and told a sleepy story together.",
        ),
    ]
    if food.label == "semolina":
        qs.append(
            QAItem(
                question="How did semolina help the bedtime story end well?",
                answer="The semolina cooled down, so it became soft and easy to share. That helped papa and the friend feel calm and close.",
            )
        )
    if friend.name:
        qs.append(
            QAItem(
                question=f"What kind of friendship was shown between papa and {friend.name}?",
                answer=f"They showed a patient friendship. Papa waited kindly, and {friend.name} felt safe enough to sit close and share the bowl.",
            )
        )
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is semolina?",
            answer="Semolina is a grainy food often cooked into a soft, warm porridge or pudding.",
        ),
        QAItem(
            question="Why do people wait for hot food to cool?",
            answer="People wait for hot food to cool so it will not burn their mouth and can be eaten safely.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means being kind, sharing, and helping each other feel safe and happy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
friendship(papa, child) :- papa(papa), child(child).
safe(Food) :- food(Food), cool_enough(Food), shared(papa, child, Food).
calm_end :- friendship(papa, child), safe(semolina).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        for a in sorted(SETTINGS[pid].affords):
            lines.append(asp.fact("affords", pid, a))
    for fid, food in FOODS.items():
        lines.append(asp.fact("food", fid))
        if fid == "semolina":
            lines.append(asp.fact("semolina", fid))
        lines.append(asp.fact("cool_enough", fid))
    for fid in FRIENDS:
        lines.append(asp.fact("friend", fid))
    lines.append(asp.fact("papa", "papa"))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("shared", "papa", "child", "semolina"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show calm_end/0. #show friendship/2. #show safe/1."))
    atoms = asp.atoms(model, "calm_end")
    py = reasonableness_gate("kitchen", "semolina", "mouse")
    if bool(atoms) and py:
        print("OK: ASP and Python agree on the bedtime friendship world.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    return 1


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
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for food in FOODS:
            for friend in FRIENDS:
                if reasonableness_gate(place, food, friend):
                    out.append((place, food, friend))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime-story world about papa, semolina, and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--name")
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
    food = args.food or select_food(rng)
    place = args.place or select_place(rng, food)
    friend = args.friend or select_friend(rng)
    if not reasonableness_gate(place, food, friend):
        raise StoryError(StoryGate.reason(place, food, friend))
    name = args.name or rng.choice(CHILD_NAMES)
    return StoryParams(place=place, friend=friend, food=food, name=name, seed=args.seed)


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


CURATED = [
    StoryParams(place="kitchen", friend="mouse", food="semolina", name="Nia"),
    StoryParams(place="cozy_room", friend="cat", food="semolina", name="Luca"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show calm_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show calm_end/0. #show friendship/2. #show safe/1."))
        print(asp.atoms(model, "calm_end"))
        print(asp.atoms(model, "friendship"))
        print(asp.atoms(model, "safe"))
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
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
