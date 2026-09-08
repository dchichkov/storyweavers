#!/usr/bin/env python3
"""
A small mythic storyworld about a seventh trial, a spare lantern, and friendship.

Luna must cross seven moonlit gates to return a fallen star. At the last gate,
her lantern goes dark, but a spare flame carried by her friend reveals that the
journey was never meant to be faced alone.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("light", "distance", "height", "warmth"):
            self.meters.setdefault(key, 0.0)
        for key in ("courage", "fear", "trust", "joy", "loneliness"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Place:
    id: str
    name: str
    image: str


@dataclass(frozen=True)
class Trial:
    id: str
    obstacle: str
    clue: str
    action: str
    image: str


PLACES = {
    "moon_mountain": Place("moon_mountain", "the Mountain of Seven Echoes",
                           "silver stones rose like sleeping giants"),
    "cloud_bridge": Place("cloud_bridge", "the Bridge Above the Clouds",
                           "white clouds curled below the narrow path"),
    "star_garden": Place("star_garden", "the Garden Where Stars Sleep",
                          "blue flowers opened whenever the moon breathed"),
}

TRIALS = [
    Trial("echo_gate", "an echo repeated every doubt in Luna's voice",
          "the echo grew softer when she spoke kindly",
          "answered the mountain with a brave, gentle greeting",
          "Seven echoes bowed and became one clear bell"),
    Trial("glass_river", "a river of glass blocked the moon road",
          "a line of warm footprints crossed its shining surface",
          "followed the footprints instead of staring at the cold water",
          "the glass river opened like a bright ribbon"),
    Trial("sleeping_wind", "a sleeping wind guarded the stair",
          "a single feather pointed toward the quietest step",
          "walked softly enough not to wake the storm",
          "the wind dreamed a path through the clouds"),
    Trial("thorn_gate", "thorn vines closed around the fallen star",
          "the oldest thorn curled away from a song of thanks",
          "sang for the garden before reaching for the star",
          "the thorns made a crown of green light"),
    Trial("shadow_well", "a well showed Luna every shadow she feared",
          "her shadow held hands with another shadow",
          "looked closely and saw her friend's shape beside hers",
          "the dark well filled with reflected dawn"),
    Trial("silent_bell", "a giant bell demanded a sound no one could make",
          "its quiet center trembled when two hearts kept the same rhythm",
          "stood beside her friend and breathed in time",
          "the bell rang without a hand touching it"),
    Trial("seventh_door", "the seventh door had no handle and no light",
          "a spare flame glimmered beneath her friend's cloak",
          "accepted the light instead of pretending to be unafraid",
          "the door opened into a sky full of returning stars"),
]

FRIENDS = {
    "orion": ("Orion", "fox"),
    "mira": ("Mira", "swallow"),
    "tavi": ("Tavi", "small bear"),
    "sena": ("Sena", "deer"),
}

LUNAS = ["Luna", "Aster", "Nara", "Elia", "Veya"]
ASP_RULES = r"""
reason(place(P), trial(T), friend(F)) :-
    place(P), trial(T), friend(F), seventh(T), spare_flame(F).

valid_story(P,T,F) :- reason(place(P),trial(T),friend(F)).
#show valid_story/3.
"""


@dataclass
class World:
    place: Place
    hero: Entity
    friend: Entity
    lantern: Entity
    spare_flame: Entity
    trial: Trial
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)
    entities: dict[str, Entity] = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        paragraphs: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append(" ".join(current))
        return "\n\n".join(paragraphs)


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    friend_kind: str
    trial: str
    seed: Optional[int] = None


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("That place is not part of the moon myth.")
    if params.trial not in {t.id for t in TRIALS}:
        raise StoryError("That trial is not one of the seven trials.")
    if params.friend not in {v[0] for v in FRIENDS.values()}:
        raise StoryError("That friend is not in the friendship registry.")
    if params.friend_kind not in {v[1] for v in FRIENDS.values()}:
        raise StoryError("That friend-kind is not in the friendship registry.")
    if not params.hero.strip():
        raise StoryError("The moon traveler needs a name.")
    if params.hero == params.friend:
        raise StoryError("A hero and a friend must be different characters.")


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else repr(params))
    place = PLACES[params.place]
    trial = next(t for t in TRIALS if t.id == params.trial)
    hero = Entity(params.hero, "character", params.hero)
    friend = Entity("friend", "character", params.friend)
    lantern = Entity("lantern", "thing", "the moon lantern", owner=hero.id)
    spare = Entity("spare_flame", "thing", "the spare flame", owner=friend.id)
    hero.memes["courage"] = 1
    hero.memes["loneliness"] = 1
    friend.memes["trust"] = 2
    lantern.meters["light"] = 2
    spare.meters["light"] = 1
    world = World(place, hero, friend, lantern, spare, trial)
    world.entities = {e.id: e for e in (hero, friend, lantern, spare)}

    openings = [
        f"In the first age, when the moon still learned her path, {hero.label} climbed {place.name}.",
        f"Long ago, beneath a moon as bright as a pearl, {hero.label} came to {place.name}.",
        f"The old stars tell of {hero.label}, who journeyed to {place.name} before dawn.",
    ]
    world.say(rng.choice(openings))
    world.say(f"{place.image}, and seven gates waited above the earth. {friend.label} followed with a quiet step and a small cloak.")
    world.say(f'"You may walk first," said {friend.label}, "but I will not let you walk alone."')
    world.say(f'"Then I will carry the moon lantern," said {hero.label}. "Together we will return the fallen star."')
    world.para()

    world.say(f"At each gate, {trial.obstacle}.")
    world.say(f"{hero.label} remembered the first six trials, but the seventh trial felt larger than the sky.")
    world.say(f"Inside, {hero.label} thought, 'If I fail now, the star will remain lost, and my friend will see that I was never brave.'")
    world.hero.memes["fear"] = 2
    world.hero.meters["distance"] = 7
    world.lantern.meters["light"] = 0
    world.say(f"Then the moon lantern went dark. {trial.clue.capitalize()}.")
    world.para()

    world.say(f"{hero.label} stopped before {trial.obstacle}.")
    world.say(f'"Do not hide your fear from me," said {friend.label}. "Tell me what you need."')
    world.say(f'"I need the courage to take the seventh step," said {hero.label}. "But I cannot find it in the dark."')
    world.say(f'"You do not have to find it alone," said {friend.label}.')
    world.say(f"Those words changed {hero.label}'s choice. Instead of turning back, {hero.label} {trial.action}.")
    world.hero.memes["loneliness"] = 0
    world.hero.memes["trust"] = 2
    world.friend.memes["joy"] = 1
    world.spare_flame.meters["light"] = 3
    world.para()

    world.say(f"{friend.label} opened the cloak and revealed the spare flame.")
    world.say(f"It was small, yet it lit both faces. The seventh door opened, and {trial.image}.")
    world.say(f"{hero.label} lifted the fallen star, but did not lift it alone. {friend.label} held the other side.")
    world.say(f"Together they carried the star home, while the moon placed two bright marks in the heavens: one for courage and one for friendship.")
    world.say(f"From that night onward, people said, 'A brave heart may begin a journey, but a faithful friend helps it finish.'")

    world.facts.update(
        place=params.place,
        place_name=place.name,
        hero=params.hero,
        friend=params.friend,
        friend_kind=params.friend_kind,
        trial=params.trial,
        obstacle=trial.obstacle,
        clue=trial.clue,
        action=trial.action,
        ending=trial.image,
        seventh=True,
        spare=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Tell a myth about {f['hero']} facing a seventh trial at {f['place_name']}.",
        f"Write a friendship story in which {f['friend']} carries a spare flame for {f['hero']}.",
        f"Use inner monologue to show how {f['hero']} changes from loneliness to trust.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(f"Where did {f['hero']} go?", f"{f['hero']} went to {f['place_name']}."),
        QAItem("What was the seventh trial?", f"The seventh trial involved {f['obstacle']}."),
        QAItem(f"What clue helped {f['hero']}?", f"The clue was that {f['clue']}."),
        QAItem(f"What did {f['friend']} carry?", f"{f['friend']} carried a spare flame."),
        QAItem("How did friendship change the ending?", f"{f['hero']} accepted help, and the two friends carried the fallen star home together."),
        QAItem("What did the moon's two marks represent?", "They represented courage and friendship."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a myth?", "A myth is an old-style story about remarkable beings, origins, or lessons."),
        QAItem("What is inner monologue?", "Inner monologue is the private stream of thoughts a character has inside their mind."),
        QAItem("What is friendship?", "Friendship is a caring bond in which people trust, help, and enjoy being together."),
        QAItem("Why can a spare object matter?", "A spare object can help when the first one is lost, broken, or no longer enough."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"place={world.place.id} trial={world.trial.id}")
    for entity in world.entities.values():
        meters = ", ".join(f"{k}={v:g}" for k, v in entity.meters.items() if v)
        memes = ", ".join(f"{k}={v:g}" for k, v in entity.memes.items() if v)
        lines.append(f"{entity.id}: meters={{{meters}}} memes={{{memes}}}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for trial in TRIALS:
        lines.append(asp.fact("trial", trial.id))
    lines.append(asp.fact("seventh", "seventh_door"))
    for key in FRIENDS:
        lines.append(asp.fact("friend", key))
        lines.append(asp.fact("spare_flame", key))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "valid_story"))
    expected = {
        (place, "seventh_door", friend)
        for place in PLACES
        for friend in FRIENDS
    }
    if actual != expected:
        print("MISMATCH between ASP and Python registry gate.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1
    for params in curated_params():
        generate(params)
    print(f"OK: ASP/Python parity verified across {len(actual)} story shapes and generated stories.")
    return 0


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("moon_mountain", "Luna", "Orion", "fox", "seventh_door", 11),
        StoryParams("cloud_bridge", "Aster", "Mira", "swallow", "seventh_door", 22),
        StoryParams("star_garden", "Nara", "Tavi", "small bear", "seventh_door", 33),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mythic storyworld of the seventh trial and a spare flame.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--friend-kind", choices=sorted({v[1] for v in FRIENDS.values()}))
    parser.add_argument("--trial", choices=[t.id for t in TRIALS])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    friend_key = rng.choice(sorted(FRIENDS))
    friend_name, friend_kind = FRIENDS[friend_key]
    friend = args.friend or friend_name
    if args.friend:
        matches = [value for value in FRIENDS.values() if value[0] == args.friend]
        if not matches:
            raise StoryError("That friend is not in the friendship registry.")
        friend_kind = matches[0][1]
    params = StoryParams(
        place=args.place or rng.choice(sorted(PLACES)),
        hero=args.hero or rng.choice(LUNAS),
        friend=friend,
        friend_kind=args.friend_kind or friend_kind,
        trial=args.trial or "seventh_door",
        seed=args.seed,
    )
    reasonableness_gate(params)
    return params


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        values = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(values)} valid story shapes:")
        for place, trial, friend in values:
            print(f"  {place} / {trial} / {friend}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in curated_params()]
    else:
        samples = []
        seen = set()
        for offset in range(max(20, args.n * 20)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + offset)
            params = resolve_params(args, rng)
            params.seed = base_seed + offset
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero} and {sample.params.friend}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
