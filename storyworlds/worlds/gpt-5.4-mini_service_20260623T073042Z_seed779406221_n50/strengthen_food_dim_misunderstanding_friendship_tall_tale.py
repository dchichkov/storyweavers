#!/usr/bin/env python3
"""
storyworlds/worlds/strengthen_food_dim_misunderstanding_friendship_tall_tale.py
===============================================================================

A standalone story world for a tall-tale friendship misunderstanding about
food-dimming a lamp, a supper mix-up, and a strengthening act that turns a
wobble into a warm ending.

Source-tale seed:
---
A small river town had a great big bell, a bright lantern, and two pals who
talked louder than thunder. One friend thought the other meant to "dim the food"
for supper, when really they meant to "feed the dim" old lantern by putting in
fresh oil. The misunderstanding made a mess of supper plans and hurt feelings,
until a stronger, kinder act fixed the friendship and the town laughed about it
for years.

This world keeps the tone close to tall tale: exaggerated names, vivid objects,
clear misunderstanding, then a friendship repair that changes the ending image.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    title: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def full_name(self) -> str:
        if self.title:
            return f"{self.title} {self.id}"
        return self.id


@dataclass
class Place:
    id: str
    label: str
    mood: str
    setting_line: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    misunderstanding_phrase: str
    actual_phrase: str
    turn_word: str
    strain: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    dimmable: bool
    appetite: str
    taste_note: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    act: str
    strength: str
    restore_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        w.facts = dict(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    talker = world.get("speaker")
    listener = world.get("listener")
    food = world.get("food")
    if talker.memes.get("clarity", 0) >= THRESHOLD:
        sig = ("misunderstanding",)
        if sig not in world.fired:
            world.fired.add(sig)
            listener.memes["misunderstanding"] = 1
            listener.memes["hurt"] += 1
            out.append("__misunderstanding__")
    return out


def _r_strengthen(world: World) -> list[str]:
    out: list[str] = []
    for eid, ent in world.entities.items():
        if ent.memes.get("hurt", 0) < THRESHOLD:
            continue
        if ent.memes.get("friendship_offer", 0) < THRESHOLD:
            continue
        sig = ("strengthen", eid)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["hurt"] = 0
        ent.memes["trust"] += 1
        ent.memes["friendship"] += 1
        ent.meters["steadiness"] += 1
        out.append("__strengthen__")
    return out


CAUSAL_RULES = [Rule("misunderstanding", _r_misunderstanding), Rule("strengthen", _r_strengthen)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend([b for b in bits if not b.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for a_id in p.affords:
            action = ACTIONS[a_id]
            for food_id, food in FOODS.items():
                if action.id == "feed" and food.dimmable:
                    combos.append((p.id, action.id, food_id))
    return combos


@dataclass
class StoryParams:
    place: str
    action: str
    food: str
    speaker: str
    listener: str
    speaker_kind: str
    listener_kind: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale friendship misunderstanding story world.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--action", choices=list(ACTIONS))
    ap.add_argument("--food", choices=list(FOODS))
    ap.add_argument("--speaker")
    ap.add_argument("--listener")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.food is None or c[2] == args.food)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, food = rng.choice(sorted(combos))
    speaker = args.speaker or rng.choice(BOY_NAMES + GIRL_NAMES)
    listener = args.listener or rng.choice([n for n in BOY_NAMES + GIRL_NAMES if n != speaker])
    return StoryParams(place=place, action=action, food=food, speaker=speaker, listener=listener,
                       speaker_kind=rng.choice(["boy", "girl"]), listener_kind=rng.choice(["boy", "girl"]))


def reasonableness_gate(action: Action, food: Food) -> bool:
    return action.id == "feed" and food.dimmable


def tell(place: Place, action: Action, food: Food, speaker: str, listener: str,
         speaker_kind: str, listener_kind: str) -> World:
    world = World(place)
    s = world.add(Entity(id="speaker", kind="character", type=speaker_kind, label=speaker,
                         title="Tall", traits=["big-voiced"]))
    l = world.add(Entity(id="listener", kind="character", type=listener_kind, label=listener,
                         title="Little", traits=["quick-eared"]))
    f = world.add(Entity(id="food", kind="thing", type="food", label=food.label, owner=s.id,
                         attrs={"dimmable": food.dimmable}))
    lamp = world.add(Entity(id="lamp", kind="thing", type="lamp", label="lantern",
                            meters={"dimness": 0.0}, memes={"glow": 1.0}))
    s.memes["clarity"] = 1
    s.memes["friendship"] = 1
    l.memes["friendship"] = 1
    l.memes["trust"] = 1
    l.memes["hurt"] = 0
    l.memes["misunderstanding"] = 0
    world.facts.update(speaker=s, listener=l, food=f, lamp=lamp, place=place, action=action)

    world.say(f"In {place.label}, Tall {speaker} and Little {listener} were the kind of pals who could outtalk a thunderhead.")
    world.say(place.setting_line)
    world.say(f"They stood beside the old lantern and a supper table that smelled like {food.appetite}.")
    world.para()
    world.say(f'Tall {speaker} said, "{action.misunderstanding_phrase}!"')
    world.say(f'Little {listener} heard "{food.label}" and thought it meant something quite different.')
    propagate(world)
    world.para()
    world.say(f"That misunderstanding dimmed {listener}'s smile and made the lantern seem dimmer too.")
    listener.memes["friendship_offer"] = 1
    world.say(f'But then Little {listener} took a breath, listened again, and offered a grin back to Tall {speaker}.')
    listener.meters["steadiness"] = 0
    propagate(world)
    world.para()
    world.say(f'Tall {speaker} chuckled, explained the real meaning, and together they chose the proper way to {action.verb}.')
    world.say(food.taste_note)
    listener.memes["friendship"] += 1
    speaker.memes["friendship"] += 1
    lamp.meters["dimness"] = 0
    world.say("The lantern shone bright as a noon sun over a fence post, and the two friends ate together as happy as hogs in clover.")
    world.facts.update(resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale friendship story for a child where {f["speaker"].label} and {f["listener"].label} misunderstand the phrase "{f["action"].misunderstanding_phrase}" near {f["food"].label}.',
        f"Tell a funny but gentle story about a misunderstanding involving food-dim and a lantern in {f['place'].label}, then show how friendship gets stronger.",
        f'Write a short tall tale where two pals sort out a mix-up about {f["food"].label} and end by laughing together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    s, l, food, action = f["speaker"], f["listener"], f["food"], f["action"]
    return [
        QAItem(
            question=f"Who are the story's two friends?",
            answer=f"They are Tall {s.label} and Little {l.label}, two pals in {world.place.label} who started out talking past each other.",
        ),
        QAItem(
            question=f"What phrase caused the misunderstanding?",
            answer=f"The mix-up began with the words \"{action.misunderstanding_phrase}\". {l.label} heard it the wrong way and thought it was about {food.label}.",
        ),
        QAItem(
            question=f"What did the lantern image change when the friends made up?",
            answer="At first it seemed dim with the misunderstanding, but after they spoke kindly, it shone bright again.",
        ),
        QAItem(
            question=f"How did the friendship change by the end?",
            answer=f"The friendship got stronger. They listened, explained, and ended the tale eating together with brighter smiles.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a misunderstanding?", answer="A misunderstanding happens when someone hears or thinks the wrong thing and the meaning gets mixed up."),
        QAItem(question="What does friendship mean?", answer="Friendship means being kind, listening, and helping each other stay close."),
        QAItem(question="What does it mean to strengthen something?", answer="To strengthen something means to make it stronger, steadier, or harder to break."),
        QAItem(question="What does dim mean?", answer="Dim means not very bright or shining softly."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="] + [f"{i+1}. {p}" for i, p in enumerate(sample.prompts)]
    parts += ["", "== story qa =="]
    for item in sample.story_qa:
        parts += [f"Q: {item.question}", f"A: {item.answer}"]
    parts += ["", "== world qa =="]
    for item in sample.world_qa:
        parts += [f"Q: {item.question}", f"A: {item.answer}"]
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs}")
    return "\n".join(lines)


PLACES = {
    "river_town": Place("river_town", "Rumblebend", "loud", "The whole town rang like a biscuit pan in a windstorm.", affords={"feed"}),
    "hill_farm": Place("hill_farm", "Whistle Hill", "wide", "The hills stood tall enough to make even a whisper wear boots.", affords={"feed"}),
}

ACTIONS = {
    "feed": Action(
        id="feed",
        verb="feed the lantern",
        gerund="feeding the lantern",
        misunderstanding_phrase="feed the dim lantern",
        actual_phrase="fresh oil for the lantern",
        turn_word="strengthen",
        strain="dimness",
        tags={"misunderstanding", "friendship"},
    )
}

FOODS = {
    "cornbread": Food("cornbread", "cornbread", "cornbread", True, "buttery cornbread", "The cornbread smelled warm and sweet as a hayloft in July.", {"food-dim"}),
    "stew": Food("stew", "stew", "bean stew", True, "bean stew", "The stew steamed up like a friendly cloud.", {"food-dim"}),
    "pie": Food("pie", "pie", "apple pie", True, "apple pie", "The pie sat bright as a red wheel in the moonlight.", {"food-dim"}),
}

GIRL_NAMES = ["Mabel", "Nell", "Ivy", "June", "Hazel", "Ruby"]
BOY_NAMES = ["Beau", "Owen", "Clint", "Earl", "Hank", "Duke"]


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for fid, food in FOODS.items():
        lines.append(asp.fact("food", fid))
        if food.dimmable:
            lines.append(asp.fact("dimmable", fid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, A, F) :- place(P), action(A), food(F), dimmable(F), A = feed.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    p = set(valid_combos())
    c = set(asp_valid_combos())
    if p == c:
        print(f"OK: {len(p)} combos match.")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(p - c))
    print("clingo-only:", sorted(c - p))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ACTIONS[params.action], FOODS[params.food],
                 params.speaker, params.listener, params.speaker_kind, params.listener_kind)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        curated = [
            StoryParams("river_town", "feed", "cornbread", "Mabel", "Beau", "girl", "boy"),
            StoryParams("hill_farm", "feed", "stew", "Duke", "Ivy", "boy", "girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            p = resolve_params(args, random.Random(base + i))
            p.seed = base + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
