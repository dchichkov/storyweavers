#!/usr/bin/env python3
"""
A small pirate tale storyworld with obedient choices, a shared idea, conflict,
and a sharing-based resolution.

A seed tale premise:
- A young pirate and a captain sail for treasure.
- The pirate has an obedient streak but also a bright idea.
- A conflict starts when the map is kept secret.
- Sharing the idea and the map ends the tension and helps the crew.

This script turns that premise into a tiny simulated world.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captainess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "captain"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def them(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    captain_name: str
    place: str
    ship_name: str
    treasure: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    weather: str
    affords: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        return World(
            setting=self.setting,
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
            fired=set(self.fired),
        )


SETTINGS = {
    "harbor": Setting(place="the harbor", weather="windy", affords={"sail", "row"}),
    "reef": Setting(place="the reef", weather="stormy", affords={"sail"}),
    "island": Setting(place="the island shore", weather="warm", affords={"walk", "dig"}),
}

TREASURES = {
    "gold": ("a little chest of gold", "chest"),
    "pearls": ("a pouch of pearls", "pouch"),
    "map": ("the captain's treasure map", "map"),
}

HERO_NAMES = ["Nico", "Mina", "Pip", "Jory", "Lana", "Tess"]
CAPTAIN_NAMES = ["Captain Reed", "Captain Wave", "Captain Marlow", "Captain Brine"]
SHIP_NAMES = ["The Little Gull", "The Salt Wind", "The Moon Finch", "The Brave Crumb"]


def story_reasonable(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("The ship needs a real place to sail to.")
    if params.treasure not in TREASURES:
        raise StoryError("That treasure does not belong in this pirate tale.")
    if params.hero_type not in {"boy", "girl"}:
        raise StoryError("The young pirate must be a boy or a girl for this world.")


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting=setting)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        owner="crew",
        meters={"wet": 0.0, "tired": 0.0},
        memes={"obedient": 1.0, "idea": 1.0, "conflict": 0.0, "sharing": 0.0, "joy": 0.0, "trust": 0.0},
    ))
    captain = world.add(Entity(
        id="captain",
        kind="character",
        type="captain",
        label=params.captain_name,
        owner="crew",
        meters={"wind": 0.0},
        memes={"conflict": 0.0, "trust": 0.0, "joy": 0.0},
    ))
    treasure_phrase, treasure_type = TREASURES[params.treasure]
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type=treasure_type,
        label=params.treasure,
        phrase=treasure_phrase,
        owner="crew",
        caretaker="captain",
        meters={"safe": 1.0},
        memes={"value": 1.0},
    ))
    map_item = world.add(Entity(
        id="map",
        kind="thing",
        type="map",
        label="map",
        phrase="a wrinkled treasure map",
        owner="captain",
        caretaker="captain",
        meters={"hidden": 1.0},
        memes={"secret": 1.0},
    ))
    ship = world.add(Entity(
        id="ship",
        kind="thing",
        type="ship",
        label=params.ship_name,
        phrase=f"the ship {params.ship_name}",
        meters={"sway": 0.0},
    ))

    world.facts.update(hero=hero, captain=captain, treasure=treasure, map_item=map_item, ship=ship, params=params)
    return world


def _share_idea(world: World) -> None:
    hero = world.get("hero")
    captain = world.get("captain")
    map_item = world.get("map")
    if hero.memes["idea"] >= THRESHOLD and hero.memes["obedient"] >= THRESHOLD:
        hero.memes["sharing"] += 1.0
        captain.memes["trust"] += 1.0
        map_item.meters["hidden"] = 0.0
        world.say(f"{hero.label} had an obedient idea: if the crew shared the map, nobody would have to guess.")
        world.say(f"{hero.label} showed the map to {captain.label}, and the two of them leaned close over the same corner.")
        if ("conflict", "start") not in world.fired:
            world.fired.add(("conflict", "start"))
            hero.memes["conflict"] += 1.0
            captain.memes["conflict"] += 1.0
            world.say(f"But keeping the map secret had already started a small conflict on the deck.")


def _resolve_conflict(world: World) -> None:
    hero = world.get("hero")
    captain = world.get("captain")
    map_item = world.get("map")
    treasure = world.get("treasure")
    if hero.memes["sharing"] >= THRESHOLD and map_item.meters["hidden"] <= 0.0:
        hero.memes["conflict"] = 0.0
        captain.memes["conflict"] = 0.0
        hero.memes["joy"] += 1.0
        captain.memes["joy"] += 1.0
        captain.memes["trust"] += 1.0
        treasure.meters["safe"] = 1.0
        world.say(f"The captain smiled, because sharing the idea made the whole crew calmer.")
        world.say(f"With the map open, they found the treasure together, and the chest stayed safe beside {world.facts['params'].ship_name}.")
        world.say(f"By sunset, {hero.label} was proud of being obedient, and the little pirate's good idea had helped everyone win.")


def tell(params: StoryParams) -> World:
    story_reasonable(params)
    world = build_world(params)
    hero = world.get("hero")
    captain = world.get("captain")

    world.say(f"{hero.label} was a little {params.hero_type} pirate aboard {params.ship_name}.")
    world.say(f"{hero.label} was obedient, but {hero.pronoun()} also had one bright idea that kept tugging at {hero.pronoun('possessive')} mind.")
    world.say(f"Captain {captain.label.split()[-1]} wanted the crew to stay together while they sailed to {world.setting.place}.")

    world.para()
    if world.setting.weather == "stormy":
        world.say(f"The wind shook the sails at {world.setting.place}, and the deck creaked under gray waves.")
    elif world.setting.weather == "windy":
        world.say(f"The wind pushed at the sails, and the ship rocked gently in {world.setting.place}.")
    else:
        world.say(f"The water near {world.setting.place} was warm and bright, like a shiny blue blanket.")

    world.say(f"{hero.label} wanted to help, so {hero.pronoun()} kept watch for trouble and listened closely to the captain.")
    world.say(f"Then {hero.label} noticed the map tucked too tightly under a sleeve.")

    world.para()
    world.say(f"{hero.label} had an idea: if the map was shared, the crew could look together and choose the safest path.")
    world.say(f"But before that could happen, the secret map caused a conflict, because everyone wanted to know where the treasure was.")
    world.say(f"{hero.label} did the obedient thing and asked the captain before touching anything important.")

    _share_idea(world)
    _resolve_conflict(world)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short pirate tale for a child about {p.hero_name}, an obedient young pirate with a useful idea.',
        f"Tell a story where a pirate crew has a conflict about a map and solves it by sharing.",
        f"Write a simple sea adventure with a captain, a treasure, and a happy ending that comes from sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.get("hero")
    captain = world.get("captain")
    treasure = world.get("treasure")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {p.hero_name}, a little {p.hero_type} pirate who sailed with {captain.label} on {p.ship_name}.",
        ),
        QAItem(
            question=f"What was {p.hero_name}'s idea?",
            answer=f"{p.hero_name}'s idea was to share the map so the crew could decide together and stay calm.",
        ),
        QAItem(
            question=f"What caused the conflict on the ship?",
            answer=f"The conflict started because the map was being kept secret, and everyone wanted to know the safest way forward.",
        ),
        QAItem(
            question=f"How did the crew solve the problem?",
            answer=f"They solved it by sharing the map and listening to each other, which helped the captain and {p.hero_name} work together.",
        ),
        QAItem(
            question=f"How did {p.hero_name} feel at the end?",
            answer=f"{p.hero_name} felt proud and happy, because being obedient and sharing the idea helped the whole crew succeed.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a pirate map for?",
        answer="A pirate map shows a route or a hiding place, so sailors can try to find treasure or stay on course.",
    ),
    QAItem(
        question="Why does sharing help a crew?",
        answer="Sharing helps because everyone can see the same plan, which makes it easier to work together and avoid confusion.",
    ),
    QAItem(
        question="What is a captain on a ship?",
        answer="A captain is the person in charge of the ship and the crew, and the captain helps make big decisions.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate tale storyworld with conflict and sharing.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--captain")
    ap.add_argument("--ship")
    ap.add_argument("--treasure", choices=sorted(TREASURES))
    ap.add_argument("--gender", choices=["boy", "girl"])
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
    place = args.place or rng.choice(list(SETTINGS))
    treasure = args.treasure or rng.choice(list(TREASURES))
    gender = args.gender or rng.choice(["boy", "girl"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    captain_name = args.captain or rng.choice(CAPTAIN_NAMES)
    ship_name = args.ship or rng.choice(SHIP_NAMES)
    return StoryParams(
        hero_name=hero_name,
        hero_type=gender,
        captain_name=captain_name,
        place=place,
        ship_name=ship_name,
        treasure=treasure,
    )


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t))
    lines.append(asp.fact("emotion", "obedient"))
    lines.append(asp.fact("emotion", "idea"))
    lines.append(asp.fact("emotion", "conflict"))
    lines.append(asp.fact("emotion", "sharing"))
    return "\n".join(lines)


ASP_RULES = r"""
% A story is reasonable when a place exists, and an obedient idea can resolve conflict by sharing.
can_story(P, T) :- place(P), treasure(T).
has_conflict :- emotion(conflict).
has_sharing :- emotion(sharing).
resolves :- has_conflict, has_sharing.
#show can_story/2.
#show resolves/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_story/2.\n#show resolves/0."))
    atoms = {str(a) for a in model}
    ok = ("can_story" in " ".join(atoms)) and ("resolves" in " ".join(atoms))
    if ok:
        print("OK: ASP rules compile and produce the expected core atoms.")
        return 0
    print("ASP verification failed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_story/2.\n#show resolves/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for treasure in TREASURES:
                params = StoryParams(
                    hero_name="Pip",
                    hero_type="boy",
                    captain_name="Captain Reed",
                    place=place,
                    ship_name="The Little Gull",
                    treasure=treasure,
                )
                samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            p = sample.params
            print(f"### {p.hero_name} at {p.place} with {p.treasure}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
