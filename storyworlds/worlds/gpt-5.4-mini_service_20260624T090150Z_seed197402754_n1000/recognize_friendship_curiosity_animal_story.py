#!/usr/bin/env python3
"""
A small story world for an Animal Story about recognizing a friend through
curiosity, with friendship as the emotional turn.
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


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "animal"
    name: str = ""
    species: str = ""
    sound: str = ""
    home: str = ""
    owner: Optional[str] = None
    friend_of: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def label(self) -> str:
        return self.name or self.id


@dataclass
class Setting:
    place: str
    shelter: str
    detail: str


@dataclass
class StoryParams:
    setting: str
    hero: str
    friend: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": Setting(place="the sunny meadow", shelter="a low willow tree", detail="The grass was soft, and the air smelled sweet."),
    "pond": Setting(place="the quiet pond", shelter="a reed patch", detail="The water was still, and dragonflies drifted over the ripples."),
    "garden": Setting(place="the flower garden", shelter="a stone path", detail="Bright petals nodded in the breeze beside the path."),
}

ANIMALS = {
    "bunny": {"species": "bunny", "sound": "sniff", "home": "burrow"},
    "fox": {"species": "fox", "sound": "yip", "home": "den"},
    "kitten": {"species": "kitten", "sound": "mew", "home": "basket"},
    "duckling": {"species": "duckling", "sound": "peep", "home": "nest"},
    "puppy": {"species": "puppy", "sound": "woof", "home": "cushion"},
}

CURATED = [
    StoryParams(setting="meadow", hero="bunny", friend="duckling"),
    StoryParams(setting="pond", hero="duckling", friend="kitten"),
    StoryParams(setting="garden", hero="kitten", friend="puppy"),
]

KNOWLEDGE = {
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn more about something new."
        )
    ],
    "friendship": [
        QAItem(
            question="What is friendship?",
            answer="Friendship is when two living things care about each other, help each other, and enjoy being together."
        )
    ],
    "recognize": [
        QAItem(
            question="What does it mean to recognize someone?",
            answer="To recognize someone means to know who they are when you see them, even if they are far away or look a little different."
        )
    ],
}


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        other = World(self.setting)
        other.entities = {
            k: Entity(**{
                "id": v.id, "kind": v.kind, "type": v.type, "name": v.name,
                "species": v.species, "sound": v.sound, "home": v.home,
                "owner": v.owner, "friend_of": v.friend_of,
                "meters": dict(v.meters), "memes": dict(v.memes),
            }) for k, v in self.entities.items()
        }
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, info in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        lines.append(asp.fact("species", aid, info["species"]))
        lines.append(asp.fact("home", aid, info["home"]))
    return "\n".join(lines)


ASP_RULES = r"""
recognize(H,F) :- animal(H), animal(F), H != F.
curious_about(H,F) :- recognize(H,F).
friends(H,F) :- recognize(H,F).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_pairs() -> list[tuple[str, str, str]]:
    pairs = []
    for setting in SETTINGS:
        for hero in ANIMALS:
            for friend in ANIMALS:
                if hero != friend:
                    pairs.append((setting, hero, friend))
    return pairs


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world about recognizing a friend through curiosity.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--friend", choices=ANIMALS)
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
    hero = args.hero or rng.choice(list(ANIMALS))
    friend = args.friend or rng.choice([a for a in ANIMALS if a != hero])
    setting = args.setting or rng.choice(list(SETTINGS))
    if hero == friend:
        raise StoryError("The hero and friend must be different animals.")
    return StoryParams(setting=setting, hero=hero, friend=friend)


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.label()} was a little {hero.species} who lived near {world.setting.place}. "
        f"{hero.label().capitalize()} loved quiet mornings and small surprises."
    )
    world.say(
        f"One day, {hero.label()} noticed a tiny shape by the water and wondered if it was a stranger."
    )
    world.facts["hero"] = hero.id
    world.facts["friend"] = friend.id


def curiosity_turn(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(world.setting.detail)
    world.say(
        f"{hero.label().capitalize()} stepped closer with careful paws. "
        f"{hero.pronoun().capitalize()} wanted to know who was hiding there."
    )
    world.say(
        f"Then {hero.label()} heard a soft {friend.sound} and looked again."
    )


def recognize_friend(world: World, hero: Entity, friend: Entity) -> None:
    hero.meters["recognize"] = hero.meters.get("recognize", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0) + 1
    world.say(
        f"At last, {hero.label()} recognized {friend.label()}. "
        f"It was the same friend who had played there yesterday."
    )
    world.say(
        f"{hero.label().capitalize()} bounded forward, and the two animals touched noses and smiled."
    )


def ending(world: World, hero: Entity, friend: Entity) -> None:
    world.para()
    world.say(
        f"Soon {hero.label()} and {friend.label()} were exploring together beside {world.setting.shelter}, "
        f"happy that curiosity had turned a mystery into friendship."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero_info = ANIMALS[params.hero]
    friend_info = ANIMALS[params.friend]
    hero = world.add(Entity(id="hero", name=params.hero, species=hero_info["species"], sound=hero_info["sound"], home=hero_info["home"]))
    friend = world.add(Entity(id="friend", name=params.friend, species=friend_info["species"], sound=friend_info["sound"], home=friend_info["home"]))
    introduce(world, hero, friend)
    world.para()
    curiosity_turn(world, hero, friend)
    recognize_friend(world, hero, friend)
    ending(world, hero, friend)
    world.facts["setting"] = params.setting
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short Animal Story for a young child about curiosity leading to friendship.',
        f"Tell a gentle story where a {f['hero']} notices someone near {world.setting.place} and recognizes a friend.",
        'Write a simple story that includes the word "recognize" and ends with two animals becoming friends.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.get("hero")
    friend = world.get("friend")
    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"It was mainly about {hero.label()}, a little {hero.species} who lived near {world.setting.place}."
        ),
        QAItem(
            question=f"What did {hero.label()} want to do before recognizing the friend?",
            answer=f"{hero.label().capitalize()} wanted to learn who was by the water, so {hero.pronoun()} moved closer with curiosity."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.label()} recognizing {friend.label()} and the two animals playing together as friends."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [q for key in ("recognize", "curiosity", "friendship") for q in KNOWLEDGE[key]]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: species={e.species}, memes={e.memes}, meters={e.meters}")
    return "\n".join(lines)


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show recognize/2.")
    model = asp.one_model(program)
    atoms = asp.atoms(model, "recognize")
    expected = {(h, f) for _, h, f in valid_pairs() if h != f}
    got = set(atoms)
    if got == expected:
        print(f"OK: ASP recognize relation matches Python ({len(got)} pairs).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in ASP:", sorted(got - expected))
    print("only in Python:", sorted(expected - got))
    return 1


def asp_valid_pairs() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show recognize/2."))
    return sorted(set(asp.atoms(model, "recognize")))


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show recognize/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show recognize/2."))
        pairs = sorted(set(asp.atoms(model, "recognize")))
        for h, f in pairs:
            print(h, f)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
