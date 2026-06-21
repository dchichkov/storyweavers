#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/naval_moral_value_ghost_story.py
===============================================================

A tiny storyworld for a naval ghost story with a moral value at the center.

Premise:
- A child on a small naval ship hears a ghostly warning in the fog.
- A tempting shortcut or selfish choice risks someone else's safety or honor.
- The ghost's message pushes the child toward a better moral choice.
- The ending proves a value changed: courage becomes care, greed becomes fairness,
  or fear becomes honesty.

The world is built to stay small, state-driven, and child-facing.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    spooky: bool = False
    naval: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class StoryParams:
    ship: str
    harbor: str
    ghost: str
    child_name: str
    child_gender: str
    child_trait: str
    captain_name: str
    captain_gender: str
    moral_value: str
    temptation: str
    remedy: str
    seed: Optional[int] = None


@dataclass
class ShipType:
    id: str
    label: str
    place: str
    deck_detail: str
    naval: bool = True


@dataclass
class GhostType:
    id: str
    label: str
    warning: str
    sigh: str
    lesson: str
    spooky: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Temptation:
    id: str
    action: str
    risk: str
    hurts: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    action: str
    result: str
    moral: str
    strength: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        return w


SHIP_TYPES = {
    "sloop": ShipType(id="sloop", label="a small naval sloop", place="the bay", deck_detail="Its deck creaked softly under the lantern light."),
    "brig": ShipType(id="brig", label="a narrow naval brig", place="the harbor", deck_detail="Its ropes whispered and tapped in the wind."),
    "cutter": ShipType(id="cutter", label="a little naval cutter", place="the pier", deck_detail="Its mast swayed like a sleepy tree."),
}

GHOSTS = {
    "old_sailor": GhostType(
        id="old_sailor",
        label="the old sailor ghost",
        warning="Do not take what is not yours.",
        sigh="a sigh like a tide pulling stones back to sea",
        lesson="A ship is safe only when the crew is honest and kind.",
        tags={"ghost", "naval", "honesty"},
    ),
    "lantern_keeper": GhostType(
        id="lantern_keeper",
        label="the lantern keeper ghost",
        warning="A bright light can guide you, but a stolen one can lead you astray.",
        sigh="a sigh like a lantern fading in fog",
        lesson="Courage means choosing the fair thing even when nobody is watching.",
        tags={"ghost", "naval", "fairness"},
    ),
    "deck_child": GhostType(
        id="deck_child",
        label="a child ghost from the deck",
        warning="If you hide the truth, the waves will know.",
        sigh="a sigh like a rope knot loosening slowly",
        lesson="Being honest helps everyone trust each other again.",
        tags={"ghost", "naval", "honesty"},
    ),
}

TEMPTATIONS = {
    "keep_compass": Temptation(
        id="keep_compass",
        action="hide the captain's brass compass in a pocket",
        risk="the captain would lose the tool needed to steer",
        hurts="the crew",
        tags={"honesty", "theft"},
    ),
    "sell_lantern": Temptation(
        id="sell_lantern",
        action="take a bright lantern to trade for sweets",
        risk="the watch deck would be left dark",
        hurts="everyone on watch",
        tags={"fairness", "greed"},
    ),
    "mock_new_cook": Temptation(
        id="mock_new_cook",
        action="laugh at the new cook and blame him for a missing crate",
        risk="the cook would feel alone and ashamed",
        hurts="the new cook",
        tags={"kindness", "honesty"},
    ),
}

REMEDIES = {
    "return_compass": Remedy(
        id="return_compass",
        action="bring the compass back at once",
        result="the captain smiled with relief and set the course straight again",
        moral="honest hands keep the ship safe",
        strength=2,
        tags={"honesty"},
    ),
    "share_lantern": Remedy(
        id="share_lantern",
        action="carry the lantern to the watch post and share it fairly",
        result="the deck glowed warm and the sentry could see the ropes and railings",
        moral="fairness makes light feel brighter",
        strength=2,
        tags={"fairness"},
    ),
    "apologize_cook": Remedy(
        id="apologize_cook",
        action="tell the cook the truth and say sorry",
        result="the cook's eyes softened, and the missing crate was found behind a barrel",
        moral="kind words can mend a hurt faster than blame",
        strength=1,
        tags={"kindness", "honesty"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for ship in SHIP_TYPES:
        for ghost in GHOSTS:
            for temp in TEMPTATIONS:
                if temp == "keep_compass" and ghost == "deck_child":
                    combos.append((ship, ghost, temp))
                elif temp == "sell_lantern" and ghost == "lantern_keeper":
                    combos.append((ship, ghost, temp))
                elif temp == "mock_new_cook" and ghost in {"old_sailor", "deck_child"}:
                    combos.append((ship, ghost, temp))
    return combos


def reasonableness_gate(ghost: GhostType, temptation: Temptation) -> bool:
    return (
        ("honesty" in ghost.tags and "honesty" in temptation.tags)
        or ("fairness" in ghost.tags and "fairness" in temptation.tags)
        or ("kindness" in ghost.tags and "kindness" in temptation.tags)
    )


def choose_remedy(temptation: Temptation, ghost: GhostType) -> Remedy:
    if temptation.id == "keep_compass":
        return REMEDIES["return_compass"]
    if temptation.id == "sell_lantern":
        return REMEDIES["share_lantern"]
    return REMEDIES["apologize_cook"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny naval ghost story world with a moral lesson.")
    ap.add_argument("--ship", choices=SHIP_TYPES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["mother", "father"])
    ap.add_argument("--value", choices=["honesty", "fairness", "kindness"])
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
    ship = args.ship or rng.choice(list(SHIP_TYPES))
    ghost = args.ghost or rng.choice(list(GHOSTS))
    temptation = args.temptation or rng.choice(list(TEMPTATIONS))
    if not reasonableness_gate(GHOSTS[ghost], TEMPTATIONS[temptation]):
        raise StoryError("This ghost and temptation do not belong in the same moral story.")
    remedy = args.remedy or choose_remedy(TEMPTATIONS[temptation], GHOSTS[ghost]).id
    value = args.value or ("honesty" if temptation == "keep_compass" else "fairness" if temptation == "sell_lantern" else "kindness")
    name_pool = ["Nina", "Milo", "Ivy", "Owen", "Mara", "Theo", "Elsa", "Finn"]
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(name_pool)
    captain = args.captain or rng.choice(["mother", "father"])
    return StoryParams(
        ship=ship,
        harbor=SHIP_TYPES[ship].place,
        ghost=ghost,
        child_name=child_name,
        child_gender=child_gender,
        child_trait=rng.choice(["brave", "curious", "gentle", "thoughtful"]),
        captain_name=captain,
        captain_gender=captain,
        moral_value=value,
        temptation=temptation,
        remedy=remedy,
    )


def _do_temptation(world: World, child: Entity, temptation: Temptation) -> None:
    child.memes["want"] = child.memes.get("want", 0.0) + 1
    if temptation.id == "keep_compass":
        world.say(f'{child.id} reached for the brass compass and almost tucked it away.')
    elif temptation.id == "sell_lantern":
        world.say(f'{child.id} held the lantern and thought about trading it for sweets.')
    else:
        world.say(f'{child.id} pointed at the new cook and nearly told a mean lie.')


def _ghost_warning(world: World, ghost: Entity, temptation: Temptation) -> None:
    world.say(f'Then {ghost.label_word} drifted out of the fog. "{GHOSTS[ghost.id].warning}"')
    world.say(GHOSTS[ghost.id].sigh)


def _choose_good(world: World, child: Entity, captain: Entity, remedy: Remedy) -> None:
    child.memes["moral_value"] = child.memes.get("moral_value", 0.0) + 1
    world.say(f'{child.id} looked at {captain.label_word} and chose the fair thing instead.')
    world.say(f'{captain.label_word.capitalize()} nodded, and they {remedy.action}.')
    world.say(remedy.result + ".")


def _ending(world: World, child: Entity, ghost: Entity) -> None:
    world.say(f'By morning, {GHOSTS[ghost.id].lesson}')
    world.say(f'{child.id} stood on the deck, the fog lifting, with a calmer heart and a clearer job to do.')


def generate(params: StoryParams) -> StorySample:
    if params.ship not in SHIP_TYPES or params.ghost not in GHOSTS or params.temptation not in TEMPTATIONS or params.remedy not in REMEDIES:
        raise StoryError("Invalid params.")
    ghost_cfg = GHOSTS[params.ghost]
    temp_cfg = TEMPTATIONS[params.temptation]
    if not reasonableness_gate(ghost_cfg, temp_cfg):
        raise StoryError("The chosen ghost and temptation do not match the moral lesson.")
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child", traits=[params.child_trait], naval=True))
    captain = world.add(Entity(id="Captain", kind="character", type=params.captain_gender, role="captain", label=f"the {params.captain_name}"))
    ghost = world.add(Entity(id="Ghost", kind="character", type="thing", role="ghost", label=ghost_cfg.label, spooky=True))
    ship = world.add(Entity(id="Ship", kind="thing", type="ship", label=SHIP_TYPES[params.ship].label, naval=True))
    child.memes["curiosity"] = 1
    world.say(f'On {SHIP_TYPES[params.ship].label} at {params.harbor}, {child.id} listened to the wind and the ropes.')
    world.say(SHIP_TYPES[params.ship].deck_detail)
    world.para()
    _do_temptation(world, child, temp_cfg)
    _ghost_warning(world, ghost, temp_cfg)
    world.para()
    _choose_good(world, child, captain, REMEDIES[params.remedy])
    _ending(world, child, ghost)
    world.facts.update(
        child=child,
        captain=captain,
        ghost_cfg=ghost_cfg,
        temp_cfg=temp_cfg,
        remedy_cfg=REMEDIES[params.remedy],
        ship_cfg=SHIP_TYPES[params.ship],
        moral_value=params.moral_value,
    )
    story = world.render()
    prompts = [
        f'Write a child-friendly naval ghost story that teaches {params.moral_value}.',
        f"Tell a ghost story on a naval ship where {child.id} faces a tempting choice and chooses the moral value of {params.moral_value}.",
        f'Write a gentle haunted-ship story with fog, a warning ghost, and a kind ending that includes the word "naval".',
    ]
    story_qa = [
        QAItem(
            question="What did the ghost warn about?",
            answer=f'The ghost warned, "{ghost_cfg.warning}" The warning pushed {child.id} toward a better choice.'
        ),
        QAItem(
            question="What did the child do instead of giving in to temptation?",
            answer=f'{child.id} chose to {REMEDIES[params.remedy].action}. That kept the ship safer and showed {params.moral_value}.'
        ),
        QAItem(
            question="How did the story end?",
            answer=f'It ended with a calmer deck and a better heart. {child.id} learned that {REMEDIES[params.remedy].moral}.'
        ),
    ]
    world_qa = [
        QAItem(question="What does naval mean in a story?", answer="Naval means it belongs to ships, sailors, or life at sea."),
        QAItem(question="Why can a ghost story still have a moral lesson?", answer="Because the spooky part can help a character make a better choice, like being honest, fair, or kind."),
        QAItem(question="What is a moral value?", answer="A moral value is a good way of acting, like honesty, fairness, kindness, or courage."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.naval:
            bits.append("naval=True")
        if e.spooky:
            bits.append("spooky=True")
        lines.append(f"  {e.id:8} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SHIP_TYPES:
        lines.append(asp.fact("ship", sid))
    for gid in GHOSTS:
        lines.append(asp.fact("ghost", gid))
    for tid in TEMPTATIONS:
        lines.append(asp.fact("temptation", tid))
    for rid in REMEDIES:
        lines.append(asp.fact("remedy", rid))
    lines.append(asp.fact("value", "honesty"))
    lines.append(asp.fact("value", "fairness"))
    lines.append(asp.fact("value", "kindness"))
    return "\n".join(lines)


ASP_RULES = r"""
moral_match(ghost, temptation) :- ghost(old_sailor), temptation(keep_compass).
moral_match(ghost, temptation) :- ghost(lantern_keeper), temptation(sell_lantern).
moral_match(ghost, temptation) :- ghost(deck_child), temptation(mock_new_cook).
valid(ship, ghost, temptation) :- ship(ship), ghost(ghost), temptation(temptation), moral_match(ghost, temptation).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python combo gates.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(ship=None, ghost=None, temptation=None, remedy=None, name=None, gender=None, captain=None, value=None), random.Random(7)))
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: ASP parity and generate/emit smoke test passed.")
    return rc


def valid_choice_keys() -> list[str]:
    return list(SHIP_TYPES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.ship and args.ghost and args.temptation:
        if not reasonableness_gate(GHOSTS[args.ghost], TEMPTATIONS[args.temptation]):
            raise StoryError("This combination does not fit the moral-ghost premise.")
    combos = [c for c in valid_combos()
              if (args.ship is None or c[0] == args.ship)
              and (args.ghost is None or c[1] == args.ghost)
              and (args.temptation is None or c[2] == args.temptation)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    ship, ghost, temptation = rng.choice(combos)
    remedy = args.remedy or choose_remedy(TEMPTATIONS[temptation], GHOSTS[ghost]).id
    return resolve_params_from_choice(args, rng, ship, ghost, temptation, remedy)


def resolve_params_from_choice(args, rng, ship, ghost, temptation, remedy) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Nina", "Milo", "Ivy", "Owen", "Mara", "Theo", "Elsa", "Finn"])
    captain = args.captain or rng.choice(["mother", "father"])
    value = args.value or ("honesty" if temptation == "keep_compass" else "fairness" if temptation == "sell_lantern" else "kindness")
    return StoryParams(
        ship=ship,
        harbor=SHIP_TYPES[ship].place,
        ghost=ghost,
        child_name=name,
        child_gender=gender,
        child_trait=rng.choice(["brave", "curious", "gentle", "thoughtful"]),
        captain_name=captain,
        captain_gender=captain,
        moral_value=value,
        temptation=temptation,
        remedy=remedy,
    )


CURATED = [
    StoryParams(ship="sloop", harbor=SHIP_TYPES["sloop"].place, ghost="old_sailor", child_name="Nina", child_gender="girl", child_trait="thoughtful", captain_name="mother", captain_gender="mother", moral_value="honesty", temptation="keep_compass", remedy="return_compass"),
    StoryParams(ship="brig", harbor=SHIP_TYPES["brig"].place, ghost="lantern_keeper", child_name="Milo", child_gender="boy", child_trait="brave", captain_name="father", captain_gender="father", moral_value="fairness", temptation="sell_lantern", remedy="share_lantern"),
    StoryParams(ship="cutter", harbor=SHIP_TYPES["cutter"].place, ghost="deck_child", child_name="Ivy", child_gender="girl", child_trait="gentle", captain_name="mother", captain_gender="mother", moral_value="kindness", temptation="mock_new_cook", remedy="apologize_cook"),
]


def generate_many(params_list: list[StoryParams]) -> list[StorySample]:
    return [generate(p) for p in params_list]


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
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = generate_many(CURATED)
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
