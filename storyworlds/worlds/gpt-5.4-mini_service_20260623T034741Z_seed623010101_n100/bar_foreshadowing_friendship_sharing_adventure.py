#!/usr/bin/env python3
"""
storyworlds/worlds/bar_foreshadowing_friendship_sharing_adventure.py
====================================================================

A small standalone story world for an adventure about foreshadowing, friendship,
and sharing.

Premise:
- Two friends set out on a little adventure.
- A foreshadowing detail hints that the trip will be longer and harder than it
  first looks.
- One child has a snack bar; the other forgot theirs.
- The friends share the bar, which helps them finish the journey together.

The world models physical meters and emotional memes, state-driven narration,
a reasonableness gate, and an inline ASP twin for parity checks.
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
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    plural: bool = False

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
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    place: str
    trail_name: str
    foreshadow: str
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    energy: float = 1.0
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    setting: str
    hero: str
    friend: str
    snack: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "trail": Setting(place="the trail", trail_name="pine trail", foreshadow="dark clouds"),
    "hill": Setting(place="the hill path", trail_name="hill path", foreshadow="a long, windy climb"),
    "dock": Setting(place="the dock walk", trail_name="dock walk", foreshadow="a far-off bell"),
}

SNACKS = {
    "berry_bar": Snack(id="berry_bar", label="berry bar", phrase="a berry bar"),
    "oat_bar": Snack(id="oat_bar", label="oat bar", phrase="an oat bar"),
    "honey_bar": Snack(id="honey_bar", label="honey bar", phrase="a honey bar"),
}

NAMES = ["Mia", "Noah", "Luna", "Eli", "Ava", "Finn", "Zoe", "Theo"]
TRAITS = ["brave", "curious", "cheerful", "spirited"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, "hero", "friend") for s in SETTINGS for _ in [0] for _2 in [0]]


def pick_name(rng: random.Random, avoid: str = "") -> str:
    choices = [n for n in NAMES if n != avoid]
    return rng.choice(choices)


def foreshadow_line(world: World) -> str:
    return f"Above {world.setting.place}, {world.setting.foreshadow} rolled slowly in the sky."


def predict_hunger(world: World, snack: Snack) -> bool:
    return bool(snack.energy >= 1.0 and world.get("hero").memes.get("hunger", 0.0) >= 1.0)


def build_story(world: World, hero: Entity, friend: Entity, snack: Snack) -> None:
    hero.memes["joy"] = 0.0
    friend.memes["joy"] = 0.0
    hero.memes["friendship"] = 0.0
    friend.memes["friendship"] = 0.0
    hero.memes["hunger"] = 0.0
    friend.memes["hunger"] = 0.0
    world.say(f"{hero.id} and {friend.id} set out for an adventure on {world.setting.place}.")
    world.say(f"They carried a little map, and the path ahead looked simple at first.")
    world.say(foreshadow_line(world))
    hero.memes["curiosity"] += 1.0
    friend.memes["curiosity"] += 1.0
    world.say(
        f"{hero.id} noticed the clouds before anyone else and said they should keep going "
        f"while the sky was still bright."
    )
    world.para()
    hero.meters["steps"] += 1.0
    friend.meters["steps"] += 1.0
    hero.memes["hunger"] += 1.0
    friend.memes["hunger"] += 1.0
    world.say(
        f"The walk took longer than they expected, and their bellies started to feel empty."
    )
    if snack.id not in world.fired and predict_hunger(world, snack):
        world.fired.add(snack.id)
        holder = hero
        other = friend
        world.say(
            f"{holder.id} found {snack.phrase} in the pack and hesitated for a moment."
        )
        world.say(
            f"{other.id} looked tired, so {holder.id} split the {snack.label} in two."
        )
        holder.memes["sharing"] += 1.0
        other.memes["sharing"] += 1.0
        holder.memes["friendship"] += 1.0
        other.memes["friendship"] += 1.0
        holder.memes["joy"] += 1.0
        other.memes["joy"] += 1.0
        world.say(
            f"They each took a bite, and the shared snack made the rest of the trail feel easier."
        )
    world.para()
    hero.meters["steps"] += 1.0
    friend.meters["steps"] += 1.0
    world.say(
        f"By the time they reached the top, the clouds had turned gray, but the two friends "
        f"were still smiling."
    )
    world.say(
        f"Together, they followed the last bend and headed home with the empty {snack.label} wrapper "
        f"crinkling in {hero.id}'s pocket."
    )
    world.facts.update(hero=hero, friend=friend, snack=snack, setting=world.setting)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a young child that includes the word "bar" and a shared snack on {f["setting"].place}.',
        f"Tell a story where {f['hero'].id} and {f['friend'].id} go on a little adventure, notice a clue in the sky, and share a {f['snack'].label}.",
        f'Write a gentle story about friendship and sharing, with foreshadowing that makes the trail feel a little uncertain.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h, fr, sn = f["hero"], f["friend"], f["snack"]
    return [
        QAItem(
            question=f"Who went on the adventure in the story?",
            answer=f"{h.id} and {fr.id} went on the adventure together. They were friends, and they stayed side by side the whole way.",
        ),
        QAItem(
            question=f"What clue foreshadowed that the trip might be harder than it first looked?",
            answer=f"The foreshadowing clue was the dark sky over {world.setting.place}. It hinted that the easy-looking trip would take more effort.",
        ),
        QAItem(
            question=f"How did {h.id} help {fr.id} when the walk got long?",
            answer=f"{h.id} shared the {sn.label} instead of keeping it alone. That made {fr.id} feel cared for and gave both friends more energy.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the start they were simply heading out, but by the end they had shared their snack and finished the trail together. The empty wrapper in a pocket proved they had already eaten it on the way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a hint that tells you something important may happen later in the story. It helps the reader feel ready for what comes next.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else have some of what you have. It is kind because it helps both people.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other and help each other. Friends look out for one another during good times and hard ones.",
        ),
        QAItem(
            question="What is a bar in this story?",
            answer="A bar is a small snack that is easy to carry in a pocket or bag. It can give people energy during an adventure.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(out)


def tell(setting: Setting, hero_name: str, friend_name: str, snack: Snack) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy" if hero_name in {"Noah", "Eli", "Finn", "Theo"} else "girl"))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy" if friend_name in {"Noah", "Eli", "Finn", "Theo"} else "girl"))
    hero.meters["steps"] = 0.0
    friend.meters["steps"] = 0.0
    hero.memes["curiosity"] = 0.0
    friend.memes["curiosity"] = 0.0
    build_story(world, hero, friend, snack)
    return world


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams(setting="trail", hero="Mia", friend="Noah", snack="berry_bar"),
        StoryParams(setting="hill", hero="Ava", friend="Finn", snack="oat_bar"),
        StoryParams(setting="dock", hero="Zoe", friend="Eli", snack="honey_bar"),
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    settings = list(SETTINGS)
    snacks = list(SNACKS)
    heroes = NAMES
    friends = NAMES
    setting = args.setting or rng.choice(settings)
    snack = args.snack or rng.choice(snacks)
    hero = args.hero or rng.choice(heroes)
    friend = args.friend or pick_name(rng, avoid=hero) if args.friend is None else args.friend
    if hero == friend:
        raise StoryError("The two friends must be different people.")
    if setting not in SETTINGS or snack not in SNACKS:
        raise StoryError("Invalid setting or snack.")
    return StoryParams(setting=setting, hero=hero, friend=friend, snack=snack)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.snack not in SNACKS:
        raise StoryError("Unknown snack.")
    if params.hero == params.friend:
        raise StoryError("Hero and friend must be different.")
    world = tell(SETTINGS[params.setting], params.hero, params.friend, SNACKS[params.snack])
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


ASP_RULES = r"""
setting(trail). setting(hill). setting(dock).
snack(berry_bar). snack(oat_bar). snack(honey_bar).
valid(S, H, F, N) :- setting(S), snack(N), H != F.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for nid in SNACKS:
        lines.append(asp.fact("snack", nid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import tempfile
    ok = True
    if set(asp_valid_combos()) != set((p.setting, p.hero, p.friend, p.snack) for p in valid_story_params()):
        ok = False
        print("ASP mismatch with python combos.")
    try:
        sample = generate(valid_story_params()[0])
        _ = sample.story
        _ = format_qa(sample)
    except Exception as e:
        ok = False
        print(f"Smoke test failed: {e}")
    if ok:
        print("OK: ASP parity and smoke test passed.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world about friendship, sharing, and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--snack", choices=SNACKS)
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


CURATED = [
    StoryParams(setting="trail", hero="Mia", friend="Noah", snack="berry_bar"),
    StoryParams(setting="hill", hero="Ava", friend="Finn", snack="oat_bar"),
    StoryParams(setting="dock", hero="Zoe", friend="Eli", snack="honey_bar"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i - 1
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
