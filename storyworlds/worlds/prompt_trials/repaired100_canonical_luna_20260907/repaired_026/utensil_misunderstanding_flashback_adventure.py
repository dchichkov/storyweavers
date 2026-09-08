#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
while not os.path.exists(os.path.join(_storyworlds_dir, "results.py")) and os.path.dirname(_storyworlds_dir) != _storyworlds_dir:
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Tavi"
    guide: str = "Mara"
    place: str = "the cliffside trail"
    utensil: str = "silver camping spoon"


HERO_NAMES = ["Luna", "Pip", "Nia", "Rowan", "Kai", "Mira"]
HELPER_NAMES = ["Tavi", "Bramble", "Jo", "Wren", "Sol", "Ari"]
GUIDE_NAMES = ["Mara", "Captain Ivo", "Aunt Fern", "Guide Sela"]
PLACES = ["the cliffside trail", "the misty canyon", "the old forest pass", "the mountain camp", "the river gorge"]
UTENSILS = ["silver camping spoon", "brass fork", "wooden ladle", "tin cup", "folding knife"]


ARCS = [
    {
        "title": "the bell beneath the bridge",
        "object": "a tiny brass bell",
        "clue": "three blue scratches on a flat stone",
        "danger": "a rope bridge had begun to loosen in the wind",
        "memory": "the bell rang whenever a safe path was found",
        "reveal": "the scratches were trail marks left by the rescue team",
        "ending": "the bell chimed from the repaired bridge as dawn touched the peaks",
    },
    {
        "title": "the map in the rain",
        "object": "a rolled map sealed in wax",
        "clue": "a red thread caught on a thorn",
        "danger": "a flash flood was rising below the ravine",
        "memory": "the red thread marked places where travelers had needed help",
        "reveal": "the map belonged to the ranger who had planned the safe crossing",
        "ending": "the rescued map dried beside the warm campfire while rain drummed outside",
    },
    {
        "title": "the lantern on the ledge",
        "object": "a green trail lantern",
        "clue": "small bootprints pointing toward the high pass",
        "danger": "fog had hidden the return trail",
        "memory": "the lantern's green glass meant that a guide was waiting nearby",
        "reveal": "the bootprints belonged to a climber who had carried the lantern uphill",
        "ending": "the green lantern glowed above the ledge and showed everyone the way home",
    },
    {
        "title": "the seed pouch",
        "object": "a leather pouch of mountain seeds",
        "clue": "a row of tiny holes in the earth",
        "danger": "the dry slope could crumble under careless footsteps",
        "memory": "the pouch had been used to restore the trail after earlier storms",
        "reveal": "the holes were part of a planting plan, not a hidden treasure trail",
        "ending": "new seeds rested safely in the soil as the slope held firm beneath the evening sky",
    },
]


@dataclass
class StoryArc:
    data: dict


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adventure storyworld about a utensil, a misunderstanding, and a flashback.")
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--guide")
    parser.add_argument("--place")
    parser.add_argument("--utensil", choices=UTENSILS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([name for name in HELPER_NAMES if name != hero])
    guide = args.guide or rng.choice(GUIDE_NAMES)
    place = args.place or rng.choice(PLACES)
    utensil = args.utensil or rng.choice(UTENSILS)
    if hero == helper:
        raise StoryError("hero and helper must be different characters")
    if not place.strip():
        raise StoryError("place cannot be empty")
    return StoryParams(
        seed=args.seed,
        hero=hero,
        helper=helper,
        guide=guide,
        place=place,
        utensil=utensil,
    )


def make_world(params: StoryParams) -> World:
    world = World(params.place)
    world.add(Entity(
        "hero", "character", params.hero,
        meters={"distance": 0.0, "safety": 1.0, "balance": 0.8},
        memes={"curiosity": 0.8, "worry": 0.1, "trust": 0.4, "relief": 0.0},
    ))
    world.add(Entity(
        "helper", "character", params.helper,
        meters={"distance": 0.0, "safety": 1.0},
        memes={"confidence": 0.7, "confusion": 0.0, "trust": 0.4},
    ))
    world.add(Entity(
        "guide", "character", params.guide,
        meters={"distance": 2.0, "safety": 1.0},
        memes={"patience": 0.8, "trust": 0.6},
    ))
    world.add(Entity(
        "utensil", "utensil", params.utensil,
        meters={"cleanliness": 0.8, "distance": 0.0, "safety": 1.0},
        memes={"importance": 0.4},
        owner="guide",
    ))
    world.facts.update(
        hero=world.entities["hero"],
        helper=world.entities["helper"],
        guide=world.entities["guide"],
        utensil=world.entities["utensil"],
    )
    return world


def tell(params: StoryParams) -> World:
    stable_seed = params.seed if params.seed is not None else sum(ord(c) for c in params.hero + params.place)
    rng = random.Random(stable_seed ^ 0xC0FFEE)
    arc = rng.choice(ARCS)
    world = make_world(params)
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    guide = world.entities["guide"]
    utensil = world.entities["utensil"]

    world.facts.update(
        arc_title=arc["title"],
        object=arc["object"],
        clue=arc["clue"],
        danger=arc["danger"],
        memory=arc["memory"],
        reveal=arc["reveal"],
        ending=arc["ending"],
        misunderstanding=f"{helper.label} believed the utensil was a secret compass because it pointed toward a faint trail mark",
        flashback=f"{hero.label} remembered seeing the same utensil beside {guide.label}'s packed supper before the expedition began",
        action=f"{hero.label} used the utensil to tap the stones and test the ground instead of throwing it away",
        resolution=f"{guide.label} explained that the utensil was ordinary camp gear, while its position had accidentally pointed toward the real clue",
    )

    world.say(f"At {world.place}, {hero.label} and {helper.label} followed a narrow trail above the clouds.")
    world.say(f"They were searching for {arc['object']} after hearing that {arc['danger']}.")
    world.say(f"Near a cold stream, {helper.label} found {utensil.label} half buried beside {arc['clue']}.")
    world.para()

    world.say(f"\"Look! This utensil is pointing to the treasure,\" {helper.label} cried.")
    world.say(f"{hero.label} frowned. \"It belongs to someone. It may be a clue, but it may also be only a tool.\"")
    world.say(f"The misunderstanding grew when {helper.label} pulled toward a loose ledge. \"Then we must follow where it points!\"")
    helper.memes["confusion"] = 0.8
    utensil.meters["safety"] -= 0.3
    world.facts["misunderstanding_active"] = True

    world.say(f"Before taking another step, {hero.label} had a flashback: {world.facts['flashback']}.")
    world.say(f"In that memory, {guide.label} had said, \"A trail clue should lead us safely, not make us rush.\"")
    world.say(f"{hero.label} looked again and noticed that {utensil.label} was lying across a crack, not pointing toward it.")
    world.para()

    world.say(f"\"We misunderstood the utensil,\" {hero.label} said. \"It helped us notice the stones, but it is not a compass.\"")
    world.say(f"{helper.label} stepped back. \"Then what should we do?\"")
    world.say(f"\"We test the path and follow the real marks together,\" {hero.label} answered.")
    world.say(f"{hero.label} {world.facts['action']}.")
    world.say(f"The tapping revealed a hollow stone beside {arc['clue']}. Under it lay {arc['object']}.")
    world.facts["misunderstanding_active"] = False
    world.facts["object_found"] = True
    world.para()

    world.say(f"{guide.label} arrived and checked the discovery. {world.facts['resolution']}.")
    world.say(f"\"You did not let a quick guess lead you into danger,\" {guide.label} said. \"That is how an adventure becomes a safe return.\"")
    world.say(f"{helper.label} smiled. \"Next time I will ask what a thing is before I decide what it means.\"")
    world.say(f"Together they carried the found object and the utensil back to camp. {arc['ending']}.")

    hero.memes["relief"] = 0.9
    hero.memes["trust"] = 0.8
    helper.memes["confusion"] = 0.0
    helper.memes["trust"] = 0.8
    utensil.meters["safety"] = 1.0
    utensil.owner = "guide"
    world.facts["returned"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an adventure about {f['hero'].label} and {f['helper'].label} finding a utensil near {f['clue']}, with a misunderstanding and a flashback.",
        f"Tell a child-friendly adventure in {world.place} where a utensil seems like a compass, but careful testing reveals the truth.",
        "Write a short adventure with spoken dialogue, a misunderstanding, a flashback, a dangerous trail, and a safe resolution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            f"What did {f['helper'].label} misunderstand about the utensil?",
            f"{f['helper'].label} believed that the utensil was a secret compass because it seemed to point toward a trail clue.",
        ),
        QAItem(
            f"What did {f['hero'].label} remember in the flashback?",
            f"{f['hero'].label} remembered seeing the utensil beside {f['guide'].label}'s packed supper before the expedition.",
        ),
        QAItem(
            "How did the characters discover the real clue?",
            f"They stopped rushing, tested the ground with the utensil, and found a hollow stone beside {f['clue']}.",
        ),
        QAItem(
            "What danger did careful testing help them avoid?",
            f"Careful testing kept them away from the loose ledge and the danger that {f['danger']}.",
        ),
        QAItem(
            "How did the adventure end?",
            f"{f['guide'].label} confirmed the discovery, the characters returned the utensil, and they carried the found object safely back to camp.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a utensil?", "A utensil is a tool used for preparing, serving, or eating food, such as a spoon or fork."),
        QAItem("What is a misunderstanding?", "A misunderstanding is a mistaken idea about what someone said, did, or meant."),
        QAItem("What is a flashback?", "A flashback is a part of a story that shows something that happened earlier."),
        QAItem("Why should an explorer test a trail before stepping onto it?", "Testing a trail can reveal loose ground, hidden cracks, or other dangers before someone gets hurt."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}, owner={entity.owner}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_utensil(U) :- utensil(U), returned(U).
misunderstood(H, U) :- hero(H), utensil(U), confusion(H).
found_clue(H) :- hero(H), tested_ground(H), hidden_object_found.
resolved(H) :- hero(H), found_clue(H), not dangerous_choice(H).
"""


def asp_facts(world: Optional[World] = None) -> str:
    import storyworlds.asp as asp
    facts = [
        asp.fact("hero", "hero"),
        asp.fact("helper", "helper"),
        asp.fact("guide", "guide"),
        asp.fact("utensil", "utensil"),
        asp.fact("returned", "utensil"),
        asp.fact("confusion", "helper"),
        asp.fact("tested_ground", "hero"),
        asp.fact("hidden_object_found"),
    ]
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show safe_utensil/1. #show misunderstood/2. #show found_clue/1. #show resolved/1."))
    names = {(sym.name, tuple(str(arg) for arg in sym.arguments)) for sym in model}
    expected = {
        ("safe_utensil", ("utensil",)),
        ("misunderstood", ("helper", "utensil")),
        ("found_clue", ("hero",)),
        ("resolved", ("hero",)),
    }
    if names != expected:
        print("MISMATCH between ASP and Python assumptions.")
        print("got:", sorted(names))
        print("expected:", sorted(expected))
        return 1
    sample = generate(StoryParams(seed=7))
    if not sample.story or "misunderstood" in sample.story.lower():
        print("Generated story verification failed.")
        return 1
    print("OK: ASP and generated-story checks passed.")
    return 0


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
    StoryParams(hero="Luna", helper="Tavi", guide="Mara", place="the cliffside trail", utensil="silver camping spoon"),
    StoryParams(hero="Pip", helper="Wren", guide="Captain Ivo", place="the misty canyon", utensil="brass fork"),
    StoryParams(hero="Nia", helper="Bramble", guide="Guide Sela", place="the mountain camp", utensil="wooden ladle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_utensil/1. #show misunderstood/2. #show found_clue/1. #show resolved/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show safe_utensil/1. #show misunderstood/2. #show found_clue/1. #show resolved/1."))
        print("ASP atoms:")
        for symbol in model:
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
