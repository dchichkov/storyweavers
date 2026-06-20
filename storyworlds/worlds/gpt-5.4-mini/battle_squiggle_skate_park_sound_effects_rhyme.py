#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/battle_squiggle_skate_park_sound_effects_rhyme.py
==================================================================================

A small storyworld for a bedtime-style tale set at a skate park. Two children
turn a quiet evening into a friendly rhyme-battle with chalk squiggles, wheel
sounds, and a final calm ending before home-time.

The world model tracks physical meters and emotional memes so the story is driven
by state, not by fixed prose. The story has a gentle tension turn: one child gets
too loud, the other worries the park will wake up, and a grown-up helps them turn
their battle into a soft rhyme game.

Supported CLI:
- default single story
- -n / --all / --seed / --trace / --qa / --json
- --asp / --verify / --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    label: str
    evening: str
    sounds: str
    quiet_goal: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class SoundToy:
    id: str
    label: str
    sound: str
    kind: str = "safe"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class BattleMove:
    id: str
    chant: str
    effect: str
    loudness: int
    rhyme: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
@dataclass
class StoryParams:
    place: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
    move: str
    toy: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


PLACES = {
    "skate_park": Place(
        "skate_park",
        "the skate park",
        "The sky was turning purple, and the skate park had a sleepy shimmer.",
        "wheel whisper, whoosh, tap-tap",
        "a quieter little rhyme",
        tags={"skate_park", "park"},
    )
}

SOUND_TOYS = {
    "bell": SoundToy("bell", "a little bell", "ding"),
    "board": SoundToy("board", "a skateboard", "clack"),
    "rattle": SoundToy("rattle", "a rattle toy", "rattle-rattle"),
}

MOVES = {
    "battle": BattleMove(
        "battle",
        "battle",
        "a playful rhyme battle",
        loudness=2,
        rhyme="battle patter, happy clatter",
        tags={"battle", "rhyme"},
    ),
    "squiggle": BattleMove(
        "squiggle",
        "squiggle",
        "a squiggle-doodle contest",
        loudness=1,
        rhyme="squiggle wiggle, soft and little",
        tags={"squiggle", "rhyme"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Zoe", "Nora", "Ava", "Ivy"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Max", "Noah", "Eli"]


def _r_sound(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["sound"] < THRESHOLD:
            continue
        sig = ("sound", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("park").meters["awake"] += 1
        for kid in ("hero", "friend"):
            world.get(kid).memes["alert"] += 1
        out.append("__sound__")
    return out


def _r_soften(world: World) -> list[str]:
    if world.get("park").meters["awake"] < THRESHOLD:
        return []
    sig = ("soften",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hero").memes["calm"] += 1
    world.get("friend").memes["calm"] += 1
    return ["__soften__"]


CAUSAL_RULES = [Rule("sound", "physical", _r_sound), Rule("soften", "social", _r_soften)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    return [("skate_park", move_id, toy_id) for move_id in MOVES for toy_id in SOUND_TOYS]


def reasonableness_gate(move: BattleMove, toy: SoundToy) -> bool:
    return True


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", pid) for pid in PLACES]
    lines += [asp.fact("move", mid) for mid in MOVES]
    lines += [asp.fact("toy", tid) for tid in SOUND_TOYS]
    lines += [asp.fact("allowed", mid, tid) for mid in MOVES for tid in SOUND_TOYS]
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,M,T) :- place(P), move(M), toy(T), allowed(M,T).
"""

def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def tell(place: Place, move: BattleMove, toy: SoundToy, hero: Entity, friend: Entity, parent: Entity) -> World:
    w = World()
    park = w.add(Entity("park", type="place", label=place.label))
    h = w.add(Entity(hero.id, kind="character", type=hero.type, role="hero"))
    f = w.add(Entity(friend.id, kind="character", type=friend.type, role="friend"))
    p = w.add(Entity("parent", kind="character", type=parent.type, role="parent", label=parent.label))
    toy_ent = w.add(Entity("toy", type="thing", label=toy.label))
    h.memes["joy"] += 1
    f.memes["joy"] += 1
    w.say(f"At {place.label}, {h.id} and {f.id} watched the dusk bloom soft and blue.")
    w.say(f"{place.evening} {place.sounds} floated by the ramps, and {h.id} held up {toy.label}.")
    w.say(f'"Let us do a {move.chant}," {h.id} said, and the two children began a {move.effect}.')
    w.para()
    toy_ent.meters["sound"] += move.loudness
    propagate(w, narrate=False)
    w.say(f"{toy.sound}! {move.rhyme.title()} spun from their mouths as they played.")
    if w.get("park").meters["awake"] >= THRESHOLD:
        w.say(f"But the skate park seemed less sleepy now, and {f.id} worried the rhyme was getting too loud.")
        f.memes["worry"] += 1
        w.say(f'{p.label_word.capitalize()} came over and smiled. "You can keep the rhyme, but make it softer."')
        w.say(f'{h.id} and {f.id} lowered their voices to a whisper: "{move.rhyme}, hush and tuck."')
        w.say(f"Their wheels rolled {place.sounds}, and the park settled back to sleep.")
        h.memes["calm"] += 1
        f.memes["calm"] += 1
    w.facts.update(place=place, move=move, toy=toy, hero=h, friend=f, parent=p, outcome="softened")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    move = f["move"]
    toy = f["toy"]
    return [
        f'Write a bedtime-style story set at a skate park that includes the words "{move.id}" and "{toy.label}".',
        f"Tell a gentle story where two children turn a skate park into a rhyme battle, make sound effects, and then get quiet again before bed.",
        f"Write a child-friendly story with a squiggle and a battle of rhymes that ends softly at the skate park.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    h, fr, p, move, toy = f["hero"], f["friend"], f["parent"], f["move"], f["toy"]
    return [
        ("Who is the story about?", f"It is about {h.id} and {fr.id}, two children at the skate park, and {p.label_word} who helps them stay calm."),
        ("What did they make?", f"They made {move.effect}, with {toy.sound} sound effects and a rhyme battle that filled the park with little echoes."),
        ("What changed at the end?", f"They lowered their voices and turned the battle into a softer rhyme, so the skate park could rest again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a skate park?", "A skate park is a place with ramps and smooth ground where people ride skateboards and scooters."),
        ("What are sound effects in a story?", "Sound effects are written noises like whoosh or clack that help you imagine what you hear."),
        ("What is a rhyme?", "A rhyme is when words sound alike at the end, like night and light."),
        ("Why is bedtime calm?", "Bedtime is calm so bodies and minds can get sleepy and rest."),
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        MOVES[params.move],
        SOUND_TOYS[params.toy],
        Entity(params.hero, type=params.hero_gender),
        Entity(params.friend, type=params.friend_gender),
        Entity("Parent", type=params.parent, label="the parent"),
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: battle, squiggle, rhyme, and soft sound effects at a skate park.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--toy", choices=SOUND_TOYS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid combos.")
    place, move, toy = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=args.place or place,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        parent=parent,
        move=args.move or move,
        toy=args.toy or toy,
    )


def verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(StoryParams("skate_park", "Mia", "girl", "Theo", "boy", "mother", "battle", "bell"))
        _ = sample.story
        _ = sample.prompts
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: verify passed.")
    return rc


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, m, t in asp_valid_combos():
            print(f"  {p:10} {m:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("skate_park", "Mia", "girl", "Theo", "boy", "mother", "battle", "bell"),
            StoryParams("skate_park", "Luna", "girl", "Eli", "boy", "father", "squiggle", "board"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.hero} & {p.friend}: {p.move} / {p.toy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
