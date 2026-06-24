#!/usr/bin/env python3
"""
storyworlds/worlds/delicious_copper_repetition_twist_sharing_adventure.py
==========================================================================

A small adventure story world about a child, a tempting discovery, a twisty
route, and a sharing-based resolution.

Seed tale shape:
- A child wants to go on a little adventure.
- The path repeats and twists, making the journey confusing.
- A grown-up worries about the child's snack or treasure.
- They solve the problem by sharing a helpful item and taking the safer route.

This world keeps the prose child-facing and state-driven:
physical meters track distance, light, hunger, and carried objects;
emotional memes track curiosity, worry, frustration, and relief.

Included narrative instruments:
- repetition: retrying a path, revisiting a step, saying the same clue again
- twist: a surprise turn in the trail or map
- sharing: a companion shares lantern light, snack, or map
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    shared_with: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    label: str
    route: str
    twist: str
    repetition: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    value: str
    carries: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    helps: set[str]
    shares: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path_twice: int = 0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        clone.path_twice = self.path_twice
        clone.paragraphs = [[]]
        return clone


def meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def bump_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = meter(e, key) + amt


def bump_meme(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = meme(e, key) + amt


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved a good adventure.")


def delight(ch: Challenge) -> str:
    return {
        "trail": "the path curled like a ribbon through the trees",
        "bridge": "the bridge wobbled in a funny way and made the trip feel exciting",
        "cave": "the cave sparkled in tiny spots like it held secrets",
        "market": "the stalls smelled warm and sweet, like a treasure hunt for the nose",
    }.get(ch.id, "it looked like a place where something fun might happen")


def want_adventure(world: World, hero: Entity, challenge: Challenge, treasure: Treasure) -> None:
    bump_meme(hero, "curiosity")
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {challenge.route}, and "
        f"{delight(challenge)}."
    )
    world.say(
        f"{hero.id} had been thinking about the {treasure.label} all day because "
        f"it sounded {treasure.value}."
    )


def offer(world: World, parent: Entity, hero: Entity, treasure: Treasure) -> None:
    world.say(
        f"Before they left, {hero.pronoun('possessive')} {parent.type} gave "
        f"{hero.pronoun('object')} the {treasure.phrase}."
    )


def predict_loss(world: World, hero: Entity, challenge: Challenge, treasure: Treasure) -> bool:
    sim = world.copy()
    _take_path(sim, sim.get(hero.id), challenge, narrate=False)
    child = sim.get(hero.id)
    return meter(child, "lost") >= THRESHOLD or meter(sim.get(treasure.id), "safe") < THRESHOLD


def warn(world: World, parent: Entity, hero: Entity, challenge: Challenge, treasure: Treasure) -> bool:
    if not predict_loss(world, hero, challenge, treasure):
        return False
    bump_meme(parent, "worry")
    world.say(
        f'"If you take that {challenge.twist} way, you might lose the {treasure.label}," '
        f"{parent.pronoun('possessive')} {parent.type} warned."
    )
    return True


def repeat_step(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.meters["tries"] = meter(hero, "tries") + 1
    world.path_twice += 1
    bump_meme(hero, "frustration")
    world.say(
        f"{hero.id} tried the path once, then tried it again, but the turn came back "
        f"the same way and the trail felt repeated."
    )
    world.say(
        f"{hero.pronoun().capitalize()} counted the steps again, hoping the next try would be easier."
    )


def twist(world: World, hero: Entity, challenge: Challenge) -> None:
    bump_meme(hero, "surprise")
    bump_meter(hero, "lost")
    world.say(
        f"Then there was a twist in the trail: the little bend looked new, but it led to the same old spot."
    )


def share_gift(world: World, helper: Entity, hero: Entity, gift: Gift, challenge: Challenge) -> Optional[Entity]:
    if challenge.id not in gift.helps:
        return None
    item = world.add(Entity(
        id=gift.id,
        type="thing",
        label=gift.label,
        phrase=gift.phrase,
        owner=helper.id,
        shared_with=hero.id,
        plural=False,
    ))
    item.carried_by = hero.id
    bump_meme(helper, "kindness")
    bump_meme(hero, "relief")
    world.say(
        f"Then {helper.id} shared {hero.pronoun('object')} {gift.label} so they could both use it."
    )
    return item


def _take_path(world: World, hero: Entity, challenge: Challenge, narrate: bool = True) -> None:
    bump_meter(hero, "distance")
    bump_meter(hero, "lost", 1.0 if challenge.id in {"trail", "cave"} else 0.0)
    bump_meme(hero, "curiosity", 0.5)
    if narrate:
        world.say(f"{hero.id} went along the {challenge.label} and kept going.")


def solve(world: World, hero: Entity, helper: Entity, challenge: Challenge, treasure: Treasure) -> None:
    helper.memes["sharing"] = meme(helper, "sharing") + 1
    hero.memes["sharing"] = meme(hero, "sharing") + 1
    hero.memes["frustration"] = 0.0
    hero.memes["worry"] = 0.0
    hero.meters["lost"] = 0.0
    treasure_maybe = world.get(treasure.id)
    treasure_maybe.meters["safe"] = 1.0
    world.say(
        f"With the shared {helper.get('gift').label if 'gift' in world.entities else 'light'}, "
        f"{hero.id} finally saw the right turn."
    )
    world.say(
        f"They followed the safer way together, and the {treasure.label} stayed close and safe."
    )


def tell(setting: Setting, challenge: Challenge, treasure: Treasure, gift: Gift,
         hero_name: str = "Mina", hero_type: str = "girl",
         parent_type: str = "mother", helper_name: str = "Jules") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little", "brave", "curious"],
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    helper = world.add(Entity(id=helper_name, kind="character", type="boy", label="friend"))
    treasure_ent = world.add(Entity(
        id=treasure.id, type=treasure.type, label=treasure.label, phrase=treasure.phrase,
        owner=hero.id, caretaker=parent.id,
    ))
    treasure_ent.meters["safe"] = 0.0

    introduce(world, hero)
    want_adventure(world, hero, challenge, treasure)
    offer(world, parent, hero, treasure)

    world.para()
    warn(world, parent, hero, challenge, treasure)
    _take_path(world, hero, challenge)
    repeat_step(world, hero, challenge)
    twist(world, hero, challenge)
    _take_path(world, hero, challenge)

    world.para()
    gift_ent = share_gift(world, helper, hero, gift, challenge)
    if gift_ent:
        world.add(Entity(id="gift", type="thing", label=gift.label, phrase=gift.phrase))
        solve(world, hero, helper, challenge, treasure)

    world.facts.update(
        hero=hero,
        parent=parent,
        helper=helper,
        treasure=treasure_ent,
        challenge=challenge,
        gift=gift,
        resolved=gift_ent is not None,
        setting=setting,
    )
    return world


SETTINGS = {
    "forest": Setting(place="the forest", affords={"trail", "cave"}),
    "harbor": Setting(place="the harbor", affords={"bridge", "market"}),
    "hill": Setting(place="the hill path", affords={"trail", "bridge"}),
}

CHALLENGES = {
    "trail": Challenge(
        id="trail",
        label="trail",
        route="follow the trail",
        twist="twisty",
        repetition="again and again",
        risk="getting lost",
        keyword="adventure",
        tags={"trail", "twist", "repetition"},
    ),
    "bridge": Challenge(
        id="bridge",
        label="bridge",
        route="cross the bridge",
        twist="bending",
        repetition="step by step",
        risk="slipping",
        keyword="adventure",
        tags={"bridge", "twist"},
    ),
    "cave": Challenge(
        id="cave",
        label="cave",
        route="walk into the cave",
        twist="winding",
        repetition="once more",
        risk="losing the light",
        keyword="twist",
        tags={"cave", "twist"},
    ),
    "market": Challenge(
        id="market",
        label="market lane",
        route="wander through the market",
        twist="crooked",
        repetition="back and forth",
        risk="losing track",
        keyword="sharing",
        tags={"market", "sharing", "repetition"},
    ),
}

TREASURES = {
    "snack": Treasure(
        id="snack",
        label="snack box",
        phrase="a delicious copper snack box",
        type="thing",
        value="delicious",
        carries="snack",
        genders={"girl", "boy"},
    ),
    "copper_coin": Treasure(
        id="copper_coin",
        label="copper coin",
        phrase="a shiny copper coin",
        type="thing",
        value="bright",
        carries="coin",
    ),
    "map": Treasure(
        id="map",
        label="map",
        phrase="a folded map with a copper corner",
        type="thing",
        value="useful",
        carries="map",
    ),
}

GIFTS = {
    "lantern": Gift(
        id="lantern",
        label="a lantern",
        phrase="a little lantern with warm light",
        helps={"trail", "cave", "bridge"},
        shares="light",
        tail="walked with the lantern between them",
    ),
    "snack": Gift(
        id="snack",
        label="half the snack box",
        phrase="half the delicious copper snack",
        helps={"market", "trail"},
        shares="snack",
        tail="shared the snack on the way",
    ),
    "map": Gift(
        id="map",
        label="the map",
        phrase="the folded map with the copper corner",
        helps={"trail", "bridge", "market", "cave"},
        shares="map",
        tail="held the map together",
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nia", "Zoe", "Ava", "Ruby", "Maya"]
BOY_NAMES = ["Owen", "Noah", "Eli", "Finn", "Tate", "Leo", "Sam"]
TRAITS = ["curious", "brave", "cheerful", "clever", "lively"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    treasure: str
    gift: str
    name: str
    gender: str
    parent: str
    helper: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for challenge in setting.affords:
            ch = CHALLENGES[challenge]
            for treasure_id, treasure in TREASURES.items():
                if challenge in {"trail", "cave"} and treasure_id in {"snack", "map"}:
                    for gift_id, gift in GIFTS.items():
                        if challenge in gift.helps:
                            combos.append((place, challenge, treasure_id, gift_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world with repetition, twist, and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.challenge and args.treasure:
        if (args.challenge, args.treasure) not in [(c[1], c[2]) for c in valid_combos()]:
            raise StoryError("No story: that treasure does not make a good adventure problem for that challenge.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.treasure is None or c[2] == args.treasure)
              and (args.gift is None or c[3] == args.gift)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge, treasure, gift = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    helper = args.helper or rng.choice(["Jules", "Pip", "Toby", "Iris"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, challenge, treasure, gift, name, gender, parent, helper, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a child named {f["hero"].id} with the words "delicious" and "copper".',
        f"Tell a story where {f['hero'].id} wants to {f['challenge'].route}, but the trail has a twist and they must share a helpful item.",
        f"Write a gentle adventure about repetition, a surprise turn, and sharing that ends with the treasure staying safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    challenge = f["challenge"]
    treasure = f["treasure"]
    gift = f["gift"]
    return [
        QAItem(
            question=f"What kind of adventure did {hero.id} want to have?",
            answer=f"{hero.id} wanted to {challenge.route}. It felt exciting because the path was {challenge.twist}."
        ),
        QAItem(
            question=f"Why did {parent.type} worry about the {treasure.label}?",
            answer=f"{parent.pronoun('possessive').capitalize()} {parent.type} worried because the trip could make the {treasure.label} unsafe or hard to carry."
        ),
        QAItem(
            question=f"What helped {hero.id} after the repeated tries?",
            answer=f"They shared {gift.label if gift.label else 'a helpful item'} and used it together, which made the path easier and safer."
        ),
        QAItem(
            question=f"What happened to the {treasure.label} at the end?",
            answer=f"The {treasure.label} stayed safe, and {hero.id} finished the adventure with a happy feeling."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does delicious mean?",
            answer="Delicious means something tastes very good and makes you want another bite."
        ),
        QAItem(
            question="What is copper?",
            answer="Copper is a reddish-brown metal. People use it for coins, wires, and shiny objects."
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing something again and again, or saying something more than once."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise turn that changes what the characters expect."
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something with you."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    out.append(f"  path_twice={world.path_twice}")
    return "\n".join(out)


ASP_RULES = r"""
valid_combo(Place, Challenge, Treasure, Gift) :- place(Place), challenge(Challenge),
    affords(Place, Challenge), treasure(Treasure), gift(Gift), helps(Gift, Challenge).

problem(Challenge, Treasure) :- challenge(Challenge), treasure(Treasure),
    risky(Challenge, Treasure).

fix(Challenge, Gift) :- challenge(Challenge), gift(Gift), helps(Gift, Challenge).

story(Place, Challenge, Treasure, Gift) :- valid_combo(Place, Challenge, Treasure, Gift),
    problem(Challenge, Treasure), fix(Challenge, Gift).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for ch in sorted(s.affords):
            lines.append(asp.fact("affords", pid, ch))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for tag in sorted(ch.tags):
            lines.append(asp.fact("risky", cid, "treasure"))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        for ch in sorted(g.helps):
            lines.append(asp.fact("helps", gid, ch))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CHALLENGES[params.challenge], TREASURES[params.treasure], GIFTS[params.gift],
                 params.name, params.gender, params.parent, params.helper)
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
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in [
            StoryParams("forest", "trail", "snack", "lantern", "Mina", "girl", "mother", "Jules", "curious"),
            StoryParams("forest", "cave", "map", "lantern", "Owen", "boy", "father", "Pip", "brave"),
            StoryParams("harbor", "bridge", "copper_coin", "map", "Lila", "girl", "mother", "Toby", "clever"),
            StoryParams("hill", "trail", "snack", "map", "Finn", "boy", "father", "Iris", "lively"),
        ]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
