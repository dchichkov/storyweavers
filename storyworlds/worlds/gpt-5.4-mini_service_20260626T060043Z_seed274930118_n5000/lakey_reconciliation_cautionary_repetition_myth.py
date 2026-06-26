#!/usr/bin/env python3
"""
A standalone storyworld for a tiny mythic tale of Lakey, caution, repetition,
and reconciliation.

Premise:
- Lakey is a small lake spirit who loves a shiny reed flute.
- A friend or sibling wants to borrow a sacred lantern or boat.
- Lakey warns them, twice, not to rush into the deep water at dusk.
- They ignore the caution, get into a little trouble, and then reconcile.
- The ending image proves the lake is calm, the objects are safe, and the
  relationship has softened.

The world is intentionally small, state-driven, and child-facing.
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


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the lake"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    caution: str
    outcome: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "lake": Setting(place="the lake", affords={"row", "fish", "sing"}),
    "shore": Setting(place="the shore", affords={"row", "fish", "sing"}),
    "islet": Setting(place="the little islet", affords={"row", "sing"}),
}

ACTIONS = {
    "row": Action(
        id="row",
        verb="row out at dusk",
        gerund="rowing at dusk",
        rush="push the little boat toward the deep water",
        risk="the boat would scrape the stones and wobble near the dark water",
        caution="Lakey warned that the water was deep after sunset",
        outcome="the oars kept time like a drum",
        tags={"lake", "water", "boat"},
    ),
    "fish": Action(
        id="fish",
        verb="cast the line",
        gerund="fishing by moonlight",
        rush="splash the line into the reeds",
        risk="the line would snag on the reeds and the bait would be lost",
        caution="Lakey warned that moonlight makes the reeds look closer than they are",
        outcome="the line floated gently beside the lilies",
        tags={"lake", "water", "reeds"},
    ),
    "sing": Action(
        id="sing",
        verb="sing to the lake",
        gerund="singing by the shore",
        rush="shout across the water",
        risk="the echo would frighten the nesting birds",
        caution="Lakey warned that a loud song can trouble sleeping wings",
        outcome="the song rose soft and round like mist",
        tags={"lake", "birds", "song"},
    ),
}

TREASURES = {
    "lantern": Treasure(
        id="lantern",
        label="lantern",
        phrase="a bright reed lantern",
        region="hands",
    ),
    "boat": Treasure(
        id="boat",
        label="little boat",
        phrase="a little cedar boat",
        region="hands",
    ),
    "cloak": Treasure(
        id="cloak",
        label="cloak",
        phrase="a blue cloak with silver thread",
        region="shoulders",
    ),
}

NAMES = ["Lakey", "Mara", "Niko", "Sela", "Tavi", "Rina", "Jon", "Ivo"]
KIN = ["sister", "brother", "friend", "mother", "father"]
TRAITS = ["gentle", "curious", "brave", "stubborn", "dreamy", "careful"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A setting supports an action when it affords it.
can(Place, Act) :- affords(Place, Act).

% A treasure is at risk when the action's risk region includes its region.
at_risk(Act, Treasure) :- risky(Act, Region), treasure_at(Treasure, Region).

% A cautionary story is valid when the action is supported and the treasure is at risk.
valid_story(Place, Act, Treasure) :- can(Place, Act), at_risk(Act, Treasure).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tags", aid, t))
        # encode one risky region for each action in this small world
        if aid == "row":
            lines.append(asp.fact("risky", aid, "hands"))
        elif aid == "fish":
            lines.append(asp.fact("risky", aid, "hands"))
        elif aid == "sing":
            lines.append(asp.fact("risky", aid, "shoulders"))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("treasure_at", tid, t.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for act in s.affords:
            for tid, t in TREASURES.items():
                if ACTIONS[act].id in {"row", "fish"} and t.region == "hands":
                    combos.append((place, act, tid))
                if ACTIONS[act].id == "sing" and t.region == "shoulders":
                    combos.append((place, act, tid))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    action: str
    treasure: str
    name: str
    kin: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic lake tale of caution and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--action", choices=ACTIONS.keys())
    ap.add_argument("--treasure", choices=TREASURES.keys())
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--kin", choices=KIN)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.action:
        combos = [c for c in combos if c[1] == args.action]
    if args.treasure:
        combos = [c for c in combos if c[2] == args.treasure]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, treasure = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        action=action,
        treasure=treasure,
        name=args.name or rng.choice(NAMES),
        kin=args.kin or rng.choice(KIN),
        trait=args.trait or rng.choice(TRAITS),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if (params.place, params.action, params.treasure) not in valid_combos():
        raise StoryError("That combination is not mythically plausible here.")


def predict_risk(world: World, hero: Entity, action: Action, treasure_id: str) -> dict:
    sim = world.copy()
    hero2 = sim.get(hero.id)
    hero2.memes["impulse"] = hero2.memes.get("impulse", 0) + 1
    sim.facts["risk"] = action.risk
    treasure = sim.get(treasure_id)
    return {"trouble": action.id in {"row", "fish", "sing"}, "treasure": treasure.label}


def generate_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    treasure: Entity = f["treasure"]
    action: Action = f["action"]

    world.say(f"Long ago, by {world.setting.place}, there lived {hero.id}, a small lake spirit who loved quiet water.")
    world.say(f"{hero.id} had a {treasure.phrase}, and every evening {hero.pronoun()} kept it close.")
    world.say(f"People said {hero.id} was {f['trait']} and kind, but {hero.pronoun('possessive')} heart still flared with the wish to {action.verb}.")

    world.para()
    world.say(f"One dusk, {f['companion'].id} came to the shore and wanted to borrow the {treasure.label}.")
    world.say(f"They hoped to {action.verb}, because the lake looked calm and inviting.")
    world.say(f"But {elder.id} looked at the darkening water and said, '{action.caution}.'")
    world.say(f"Then {elder.id} said it again, for old myths like to repeat what matters: '{action.caution}.'")

    hero.memes["warning"] = hero.memes.get("warning", 0) + 1
    f["warned_twice"] = True

    world.para()
    world.say(f"Still, {f['companion'].id} tried to {action.rush}.")
    world.say(f"The little boat wobbled, or the line snagged, or the song rose too loudly, and the lake answered with a restless shiver.")
    world.say(f"{action.risk.capitalize()}.")
    f["trouble"] = True

    world.para()
    world.say(f"Then {f['companion'].id} grew ashamed and quiet.")
    world.say(f"{hero.id} did not scold. {hero.pronoun().capitalize()} steadied the {treasure.label}, and {elder.id} offered a softer way.")
    world.say(f"Together they breathed slowly until the water stilled.")
    world.say(f"{f['companion'].id} said sorry, and {hero.id} said, 'Come back when the sun is high; we can do it the safe way.'")
    hero.memes["reconciliation"] = hero.memes.get("reconciliation", 0) + 1
    f["resolved"] = True

    world.para()
    world.say(f"So the next morning, {f['companion'].id} returned with careful hands, and this time they listened.")
    world.say(f"They {action.gerund}, and {action.outcome}.")
    world.say(f"{hero.id} smiled, for the lake was calm, the {treasure.label} was safe, and the old warning had become a kind promise.")


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="Lakey", kind="character", type="spirit", label="Lakey"))
    elder = world.add(Entity(id="Elder", kind="character", type="elder", label="the elder"))
    companion = world.add(Entity(id=params.name, kind="character", type=params.kin, label=params.name))
    treasure = world.add(Entity(
        id=params.treasure,
        type="thing",
        label=TREASURES[params.treasure].label,
        phrase=TREASURES[params.treasure].phrase,
        owner=hero.id,
        caretaker=hero.id,
    ))
    action = ACTIONS[params.action]
    hero.memes["calm"] = 1.0
    world.facts.update(hero=hero, elder=elder, companion=companion, treasure=treasure, action=action, trait=params.trait)
    generate_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short myth for children about {f['hero'].id}, where a warning is repeated and later becomes a promise.",
        f"Tell a gentle lake myth in which {f['companion'].id} wants to {f['action'].verb} but must learn caution.",
        f"Write a simple story that includes the name {f['hero'].id} and ends with reconciliation by the water.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    elder = f["elder"]
    treasure = f["treasure"]
    action = f["action"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, the little lake spirit who watched over the water and the {treasure.label}.",
        ),
        QAItem(
            question=f"What did {elder.label} repeat?",
            answer=f"{elder.label.capitalize()} repeated that {action.caution}. The warning was said twice because it mattered.",
        ),
        QAItem(
            question=f"What happened when {companion.id} ignored the warning?",
            answer=f"{companion.id} tried to {action.rush}, and the lake grew restless before everyone calmed down again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is caution?",
            answer="Caution means being careful and thinking about what might happen before you act.",
        ),
        QAItem(
            question="Why do stories sometimes repeat a warning?",
            answer="A repeated warning can help people remember it, especially when the warning is important or dangerous.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop arguing, make peace, and become friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = ["--- world trace ---"]
    for e in world.entities.values():
        bits.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    bits.append(f"facts={list(world.facts.keys())}")
    return "\n".join(bits)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def valid_all() -> list[StoryParams]:
    out = []
    for place, action, treasure in valid_combos():
        out.append(StoryParams(place=place, action=action, treasure=treasure, name="Lakey", kin="friend", trait="gentle"))
    return out


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:\n")
        for t in triples:
            print("  ", t)
        return

    if args.all:
        samples = [generate(p) for p in valid_all()]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as e:
                print(e)
                return
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
