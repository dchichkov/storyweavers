#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T035719Z_seed829048975_n10/eyed_bobcat_twist_curiosity_dialogue_ghost_story.py
==============================================================================================================================

A standalone storyworld for a small ghost-story domain with curiosity, dialogue,
and a twist. It includes the required words "eyed" and "bobcat" and tells a
child-facing spooky tale that resolves into a gentle ending image.

The world model tracks physical meters and emotional memes on typed entities,
then renders a short authored story from simulated state.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str | None = None
    caretaker: str | None = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, str]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, phrase=v.phrase,
            role=v.role, traits=list(v.traits), owner=v.owner, caretaker=v.caretaker,
            plural=v.plural, tags=set(v.tags), attrs=dict(v.attrs),
            meters=defaultdict(float, dict(v.meters)), memes=defaultdict(float, dict(v.memes)),
        ) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.history = list(self.history)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    spirit_kind: str
    seed: int | None = None


@dataclass
class PlaceCfg:
    id: str
    label: str
    dark_detail: str
    spooky_sound: str
    affordance: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SpiritCfg:
    id: str
    label: str
    phrase: str
    reveal: str
    twist: str
    tags: set[str] = field(default_factory=set)


PLACES = {
    "attic": PlaceCfg(
        id="attic",
        label="the attic",
        dark_detail="a row of boxes and a dusty round mirror",
        spooky_sound="a soft thump behind the rafters",
        affordance="moonlight slipped through the little window",
        tags={"dark", "house"},
    ),
    "garden": PlaceCfg(
        id="garden",
        label="the garden",
        dark_detail="the wet bushes and a crooked birdbath",
        spooky_sound="a rustle in the leaves",
        affordance="moonlight lay on the grass",
        tags={"dark", "outside"},
    ),
    "shed": PlaceCfg(
        id="shed",
        label="the shed",
        dark_detail="a stack of rakes and an old paint can",
        spooky_sound="a creak from the loose door",
        affordance="the porch light made a pale stripe on the floor",
        tags={"dark", "yard"},
    ),
}

SPIRITS = {
    "bobcat": SpiritCfg(
        id="bobcat",
        label="bobcat",
        phrase="the eyed bobcat",
        reveal="a little green costume mask with one bright button eye",
        twist="it was only a costume, not a haunted beast",
        tags={"bobcat", "eyed"},
    ),
    "lantern": SpiritCfg(
        id="lantern",
        label="lantern",
        phrase="the eyed lantern",
        reveal="a paper lantern with a painted eye and a candle inside",
        twist="it was hanging from a string, not floating by itself",
        tags={"eyed"},
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Luna", "Tess", "Ivy", "Maya"]
BOY_NAMES = ["Eli", "Otis", "Finn", "Theo", "Nate", "Rowan"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, s) for p in PLACES for s in SPIRITS]


def explain_rejection(place: str, spirit: str) -> str:
    return f"(No story: the combination {place!r} + {spirit!r} is not available.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with curiosity and a twist.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--spirit", choices=sorted(SPIRITS))
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("-n", "--n", type=int, default=1)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.spirit is None or c[1] == args.spirit)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, spirit = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in (GIRL_NAMES if helper_type == "girl" else BOY_NAMES) if n != hero_name])
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type,
                       helper_name=helper_name, helper_type=helper_type,
                       spirit_kind=spirit, seed=None)


def _setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, PlaceCfg, SpiritCfg]:
    if params.place not in PLACES or params.spirit_kind not in SPIRITS:
        raise StoryError("Invalid story parameters.")
    world = World()
    place = PLACES[params.place]
    spirit = SPIRITS[params.spirit_kind]
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name, traits=["curious"]))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name, traits=["quiet", "brave"]))
    ghost = world.add(Entity(id="ghost", kind="thing", type="thing", label=spirit.label, phrase=spirit.phrase))
    world.facts.update(place=place, spirit=spirit, hero=hero, helper=helper, ghost=ghost, twist=spirit.twist)
    hero.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.add(Entity(id="moon", kind="thing", type="thing", label="moonlight"))
    return world, hero, helper, ghost, place, spirit


def _haunt(world: World, hero: Entity, helper: Entity, ghost: Entity, place: PlaceCfg, spirit: SpiritCfg) -> None:
    hero.memes["fear"] += 1
    helper.memes["curiosity"] += 1
    world.say(f"Late one night, {hero.label} and {helper.label} slipped into {place.label}.")
    world.say(f"{place.affordance}, but {place.dark_detail} waited in the dark.")
    world.say(f"Then came {place.spooky_sound}, and {hero.label} whispered, \"Did you hear that?\"")
    world.say(f"{helper.label} answered, \"Let's look. Maybe it wants us to notice it.\"")
    world.event("haunt", place=place.id, spirit=spirit.id)


def _reveal(world: World, ghost: Entity, spirit: SpiritCfg) -> None:
    ghost.meters["mystery"] += 1
    world.say(f"A shape stepped out of the dark: {spirit.phrase}.")
    world.say(f"It had {spirit.reveal}.")
    world.event("reveal", spirit=spirit.id)


def _dialogue_twist(world: World, hero: Entity, helper: Entity, spirit: SpiritCfg) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["trust"] += 1
    world.say(f"\"Are you a ghost?\" {hero.label} asked.")
    world.say(f"\"No,\" said a tiny voice. \"I am only trying to get home.\"")
    world.say(f"{helper.label} stepped closer and saw the trick: {spirit.twist}.")
    world.event("twist", twist=spirit.twist)


def _resolve(world: World, hero: Entity, helper: Entity, ghost: Entity, spirit: SpiritCfg) -> None:
    hero.memes["fear"] = 0.0
    helper.memes["curiosity"] += 1
    ghost.meters["mystery"] = 0.0
    world.say(f"{hero.label} laughed in relief.")
    world.say(f"Together they carried the little thing outside, and the night felt friendly again.")
    world.say(f"By the gate, the strange {spirit.label} was just a costume, and the real dark was gone from it.")
    world.say(f"{hero.label} and {helper.label} walked home with the moon above them, both smiling at the twist.")
    world.event("resolve", calm=True)


def tell(params: StoryParams) -> World:
    world, hero, helper, ghost, place, spirit = _setup_world(params)
    _haunt(world, hero, helper, ghost, place, spirit)
    world.para()
    _reveal(world, ghost, spirit)
    _dialogue_twist(world, hero, helper, spirit)
    world.para()
    _resolve(world, hero, helper, ghost, spirit)
    world.facts.update(
        hero=hero, helper=helper, ghost=ghost, place=place, spirit=spirit,
        story_kind="ghost-story",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"].label
    spirit = f["spirit"].phrase
    return [
        f"Write a short ghost story for a young child set in {place} that includes the words 'eyed' and 'bobcat'.",
        f"Tell a spooky but gentle story where {f['hero'].label} and {f['helper'].label} hear {spirit} and find out what it really is.",
        f"Write a dialogue-heavy mystery with a twist, set in {place}, that ends happily after the scary thing is explained.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    place: PlaceCfg = f["place"]
    spirit: SpiritCfg = f["spirit"]
    return [
        QAItem(
            question=f"Where did {hero.label} and {helper.label} go at night?",
            answer=f"They went to {place.label}, where the dark felt spooky at first. The moonlight was there too, so they could still see enough to look around.",
        ),
        QAItem(
            question=f"What did {hero.label} think the sound might be?",
            answer=f"{hero.label} thought it might be a ghost or some haunted creature. The thump and the dark shadows made it seem scarier than it was.",
        ),
        QAItem(
            question=f"What was the twist about {spirit.phrase}?",
            answer=f"The twist was that it was really {spirit.twist}. The scary-looking shape was not a real ghost, just something ordinary wearing a spooky disguise.",
        ),
        QAItem(
            question=f"How did {helper.label} help the story turn from scary to safe?",
            answer=f"{helper.label} stayed curious and asked questions instead of running away. That helped them discover the truth and leave the dark place feeling brave.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does 'curiosity' mean in a story?",
            answer="Curiosity means wanting to know more and look carefully. It helps a character ask questions and find out the truth.",
        ),
        QAItem(
            question="What is a dialogue?",
            answer="Dialogue is when characters talk to each other in the story. It lets readers hear their questions, worries, and ideas.",
        ),
        QAItem(
            question="What is a bobcat?",
            answer="A bobcat is a wild cat with short tail and spotted fur. It is smaller than a big tiger, but it can still look very sneaky in the dark.",
        ),
        QAItem(
            question="Why can moonlight make a place feel spooky?",
            answer="Moonlight is pale and soft, so it can make shadows look strange. That can make an ordinary place seem mysterious at night.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  history: {world.history}")
    return "\n".join(lines)


ASP_RULES = r"""
place(attic). place(garden). place(shed).
spirit(bobcat). spirit(lantern).
valid(P,S) :- place(P), spirit(S).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for s in SPIRITS:
        lines.append(asp.fact("spirit", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    combos_py = set(valid_combos())
    combos_asp = set(asp_valid_combos())
    ok = True
    if combos_py != combos_asp:
        ok = False
        print("MISMATCH between Python and ASP combos.")
        print("python only:", sorted(combos_py - combos_asp))
        print("asp only:", sorted(combos_asp - combos_py))
    try:
        sample = generate(StoryParams(place="attic", hero_name="Mina", hero_type="girl", helper_name="Eli", helper_type="boy", spirit_kind="bobcat"))
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print(f"OK: ASP matches Python ({len(combos_py)} combos) and generation smoke test passed.")
        return 0
    return 1


CURATED = [
    StoryParams(place="attic", hero_name="Mina", hero_type="girl", helper_name="Eli", helper_type="boy", spirit_kind="bobcat"),
    StoryParams(place="garden", hero_name="Nora", hero_type="girl", helper_name="Theo", helper_type="boy", spirit_kind="lantern"),
    StoryParams(place="shed", hero_name="Otis", hero_type="boy", helper_name="Luna", helper_type="girl", spirit_kind="bobcat"),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.spirit_kind not in SPIRITS:
        raise StoryError("Invalid story parameters.")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for place, spirit in asp_valid_combos():
            print(place, spirit)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
