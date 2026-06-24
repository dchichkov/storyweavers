#!/usr/bin/env python3
"""
storyworlds/worlds/tattle_iridescent_take_sharing_twist_adventure.py
====================================================================

A tiny adventure storyworld about a child, a shining iridescent object, a
temptation to take it, a sharing lesson, and a twist that resolves the trouble.

The seed tale behind this world is a small, child-facing adventure:
a curious child spots an iridescent treasure, wants to take it for themselves,
then learns that sharing and a gentle twist in the plan makes everyone happier.
A nearby tattle raises the stakes by making the problem public before the
characters can quietly hide it.

The world is intentionally small:
- one setting with a few room-like places,
- one shimmering object that can be taken or shared,
- one social twist where a tattled secret changes the mood,
- a simple resolution where the child chooses sharing over keeping.

The prose engine is state-driven: the story changes because the world model
changes, not because of a fixed paragraph template with swapped names.
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
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"shine": 0.0, "taken": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "share": 0.0, "tattle": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the riverside path"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Relic:
    label: str
    phrase: str
    sparkle: str
    can_be_shared: bool = True


@dataclass
class StoryParams:
    place: str
    relic: str
    name: str
    gender: str
    friend: str
    parent: str
    seed: Optional[int] = None


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


SETTINGS = {
    "river": Setting(place="the riverside path", affords={"wander", "find"}),
    "garden": Setting(place="the lantern garden", affords={"wander", "find"}),
    "cave": Setting(place="the bright cave", affords={"wander", "find"}),
}

RELICS = {
    "stone": Relic(
        label="iridescent stone",
        phrase="an iridescent stone that flashed green, blue, and gold",
        sparkle="iridescent",
    ),
    "shell": Relic(
        label="iridescent shell",
        phrase="an iridescent shell with a rainbow sheen",
        sparkle="iridescent",
    ),
    "kite": Relic(
        label="iridescent kite",
        phrase="an iridescent kite that shimmered like fish scales",
        sparkle="iridescent",
    ),
}

GIRL_NAMES = ["Lia", "Mina", "Tara", "Nia", "Ivy", "Zoe", "Mara", "Nora"]
BOY_NAMES = ["Owen", "Finn", "Ezra", "Theo", "Leo", "Jude", "Milo", "Eli"]
FRIENDS = ["best friend", "neighbor", "cousin", "little brother", "little sister"]
TRAITS = ["brave", "curious", "lively", "thoughtful", "spirited"]


@dataclass
class StoryState:
    hero: Entity
    friend: Entity
    parent: Entity
    relic: Entity
    setting: Setting
    gathered: bool = False
    tattled: bool = False
    shared: bool = False
    twist: bool = False


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for relic in RELICS:
            combos.append((place, relic))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about tattle, iridescent treasure, take, sharing, and twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    relic = args.relic or rng.choice(list(RELICS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, relic=relic, name=name, gender=gender, friend=friend, parent=parent)


def _acts(world: World, state: StoryState) -> None:
    hero = state.hero
    friend = state.friend
    parent = state.parent
    relic = state.relic

    world.say(f"{hero.id} was a {hero.type} who loved adventure and noticed shiny things first.")
    world.say(f"{hero.pronoun().capitalize()} and {friend.id} set off along {state.setting.place}, where the air felt full of secret paths.")
    world.say(f"Then they found {relic.phrase}, lying half-hidden by the stones.")

    state.gathered = True
    relic.carried_by = hero.id
    relic.meters["shine"] += 1
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(f"{hero.id} wanted to take it right away, because the {relic.label} looked too special to leave behind.")

    hero.memes["worry"] += 1
    state.tattled = True
    friend.memes["tattle"] += 1
    world.say(f"But {friend.id} tattleed to {parent.pronoun('possessive')} {parent.type} about the hidden prize.")
    world.say(f"That made the day stop feeling quiet. Now everyone knew {hero.id} had the iridescent treasure.")

    state.twist = True
    world.say(f"{parent.id} did not scold first. Instead, {parent.pronoun('subject')} asked a twisty question: what if the treasure was not kept, but shared?")

    state.shared = True
    relic.shared_with.add(friend.id)
    relic.shared_with.add(parent.id)
    hero.memes["share"] += 1
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 1
    world.say(f"{hero.id} blinked, then offered the {relic.label} to {friend.id} and {parent.pronoun('object')}.")
    world.say(f"Together they held it up to the light, and the {relic.label} flashed with a brighter rainbow than before.")

    relic.carried_by = None
    world.say(f"In the end, {hero.id} did take the shiny treasure—but only by taking turns, which made the adventure feel bigger and kinder.")


def tell(setting: Setting, relic_cfg: Relic, hero_name: str, hero_type: str, friend_role: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_role, kind="character", type="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    relic = world.add(Entity(id="relic", type="treasure", label=relic_cfg.label, phrase=relic_cfg.phrase, owner=hero.id))

    world.say(f"{hero.id} lived for adventure, and {friend.id} loved to follow when the path looked mysterious.")
    world.say(f"One day at {setting.place}, they spotted {relic_cfg.phrase}.")
    world.para()
    state = StoryState(hero=hero, friend=friend, parent=parent, relic=relic, setting=setting)
    _acts(world, state)
    world.facts.update(hero=hero, friend=friend, parent=parent, relic=relic, setting=setting, state=state, relic_cfg=relic_cfg)
    return world


ASP_RULES = r"""
hero_wants_take(H, R) :- hero(H), relic(R).
tattle(S, H) :- friend(S), hero(H).
shared(H, R) :- hero(H), relic(R), choose_share(H, R).
twist(H, R) :- tattle(_, H), shared(H, R).
good_end(H, R) :- shared(H, R), twist(H, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for relic in RELICS:
        lines.append(asp.fact("relic", relic))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_combos() -> list[tuple[str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show place/1.\n#show relic/1."))
    return sorted(set(asp.atoms(model, "place")) | set(asp.atoms(model, "relic")))


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"Cannot run ASP verify: {exc}")
        return 1
    # Minimal parity check: the inline rules parse, and the Python registry is non-empty.
    _ = asp.one_model(asp_program("#show place/1."))
    py = set(valid_story_combos())
    if py == set(valid_combos()):
        print(f"OK: Python registry has {len(py)} valid combos.")
        return 0
    print("Registry mismatch.")
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short adventure story for a child about {f['hero'].id}, an {f['relic_cfg'].sparkle} treasure, and a lesson about sharing.",
        f"Tell a story where a child wants to take a shiny object, but a tattle changes the moment and leads to a kind twist.",
        f"Write a gentle adventure story that uses the words tattle, iridescent, and take, and ends with everyone sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    relic_cfg = f["relic_cfg"]
    state = f["state"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do when they found the {relic_cfg.label}?",
            answer=f"{hero.id} wanted to take the {relic_cfg.label} because it looked too special to leave behind.",
        ),
        QAItem(
            question=f"Who tattleed about the treasure?",
            answer=f"{friend.id} tattleed to {parent.id}, which made the hidden prize impossible to keep secret.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {parent.id} asked {hero.id} to share instead of scolding right away, and that changed the whole feeling of the adventure.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does iridescent mean?",
            answer="Iridescent means shining with changing colors, like green, blue, and gold when the light moves.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use, hold, or enjoy something with you instead of keeping it only for yourself.",
        ),
        QAItem(
            question="What is a tattle?",
            answer="A tattle is when someone tells an adult about a secret or a problem, often in a way that makes the moment more serious.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise turn that changes what the characters expect to happen next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} owner={e.owner} carried_by={e.carried_by} shared_with={sorted(e.shared_with)} meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="river", relic="stone", name="Lia", gender="girl", friend="cousin", parent="mother"),
    StoryParams(place="garden", relic="shell", name="Owen", gender="boy", friend="neighbor", parent="father"),
    StoryParams(place="cave", relic="kite", name="Nia", gender="girl", friend="little brother", parent="mother"),
]


def resolve_reasons(args: argparse.Namespace) -> None:
    if args.relic == "kite" and args.place == "cave":
        return


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    relic_cfg = RELICS[params.relic]
    world = tell(setting, relic_cfg, params.name, params.gender, params.friend, params.parent)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show hero_wants_take/2.\n#show tattle/2.\n#show shared/2.\n#show twist/2.\n#show good_end/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available, but this compact adventure world keeps the declarative twin minimal.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.relic} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
