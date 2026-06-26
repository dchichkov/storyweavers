#!/usr/bin/env python3
"""
storyworlds/worlds/spirit_earth_sound_effects_rhyme_adventure.py
================================================================

A small adventure storyworld about a curious spirit who travels with Earth
through sound effects and rhyme.

Premise:
- A spirited traveler hears the world as rhythm and verse.
- The ground answers with booms, taps, hums, and hushes.
- A brave helper must cross from noisy trouble to a gentle, singing fix.

The world is intentionally compact: few combinations, strong causal turns.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"spirit"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str = "the bright valley"
    sky: str = "clear"
    path: str = "stone path"
    echo_level: str = "soft"


@dataclass
class Signal:
    id: str
    verb: str
    noise: str
    rhyme: str
    risk: str
    cue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    shield: str
    covers: set[str]
    kind: str = "thing"


@dataclass
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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
            scene=copy.deepcopy(self.scene),
            entities=copy.deepcopy(self.entities),
            facts=copy.deepcopy(self.facts),
            paragraphs=[[]],
            fired=set(self.fired),
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SCENES = {
    "valley": Scene(place="the bright valley", sky="clear", path="stone path", echo_level="soft"),
    "cave": Scene(place="the echo cave", sky="dim", path="rock floor", echo_level="loud"),
    "forest": Scene(place="the green forest", sky="dappled", path="leaf path", echo_level="hushed"),
}

SIGNALS = {
    "drum": Signal(
        id="drum",
        verb="beat the drum",
        noise="boom-boom",
        rhyme="BOOM, zoom, room-to-roam",
        risk="too loud",
        cue="the drum would shake the calm path",
        tags={"sound_effects", "rhythm"},
    ),
    "windchime": Signal(
        id="windchime",
        verb="spin the windchime",
        noise="ting-ting",
        rhyme="Ting-a-ling, let the breezes sing",
        risk="too sharp",
        cue="the chime would wake the sleeping echoes",
        tags={"sound_effects", "rhyme"},
    ),
    "footsteps": Signal(
        id="footsteps",
        verb="march down the path",
        noise="tap-tap",
        rhyme="Tap and clap, then follow the map",
        risk="too heavy",
        cue="the steps would rattle the stones",
        tags={"sound_effects", "adventure"},
    ),
    "whisper": Signal(
        id="whisper",
        verb="follow the whisper",
        noise="shh-shh",
        rhyme="Soft as moss, we cross, cross, cross",
        risk="too faint",
        cue="the whisper would guide a careful climb",
        tags={"sound_effects", "rhyme"},
    ),
}

GIFTS = {
    "cloak": Gift(
        id="cloak",
        label="a moon-cloak",
        phrase="a moon-cloak with a soft lining",
        shield="soft",
        covers={"heart", "voice"},
    ),
    "boots": Gift(
        id="boots",
        label="trail boots",
        phrase="trail boots with sturdy soles",
        shield="steady",
        covers={"feet"},
    ),
    "lantern": Gift(
        id="lantern",
        label="a lantern",
        phrase="a little lantern with a warm glow",
        shield="bright",
        covers={"hands", "path"},
    ),
}

NAMES = ["Nova", "Milo", "Aria", "Iris", "Juno", "Theo", "Luna", "Ezra"]
TRAITS = ["brave", "curious", "spirited", "gentle", "bold"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    scene: str
    signal: str
    gift: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene_id, scene in SCENES.items():
        for signal_id, sig in SIGNALS.items():
            for gift_id, gift in GIFTS.items():
                if signal_id == "drum" and gift_id == "boots":
                    combos.append((scene_id, signal_id, gift_id))
                elif signal_id == "windchime" and gift_id == "cloak":
                    combos.append((scene_id, signal_id, gift_id))
                elif signal_id == "footsteps" and gift_id == "boots":
                    combos.append((scene_id, signal_id, gift_id))
                elif signal_id == "whisper" and gift_id in {"cloak", "lantern"}:
                    combos.append((scene_id, signal_id, gift_id))
    return combos


def explain_rejection(signal: Signal, gift: Gift) -> str:
    return (
        f"(No story: {signal.verb} and {gift.label} do not make a believable fix "
        f"together. The gift should match the kind of trouble the signal causes.)"
    )


def select_gift(signal: Signal) -> Gift:
    if signal.id == "drum":
        return GIFTS["boots"]
    if signal.id == "windchime":
        return GIFTS["cloak"]
    if signal.id == "footsteps":
        return GIFTS["boots"]
    return GIFTS["lantern"]


def scene_sentence(scene: Scene, signal: Signal) -> str:
    if scene.place == "the echo cave":
        return f"{scene.place} waited like a giant shell, and every step came back as {signal.noise}."
    if scene.place == "the green forest":
        return f"{scene.place} smelled like pine, and the air held {signal.noise} between the trees."
    return f"{scene.place} stretched wide and bright, where even a small sound could travel far."


def simulate_noise(world: World, actor: Entity, signal: Signal, gift: Gift, narrate: bool = True) -> None:
    actor.meters["courage"] = actor.meters.get("courage", 0) + 1
    actor.memes["wonder"] = actor.memes.get("wonder", 0) + 1
    world.facts["noise"] = signal.noise
    world.facts["gift"] = gift
    world.facts["rhyme"] = signal.rhyme
    if narrate:
        world.say(f"{actor.id} felt {signal.noise} in the air, like the world was tapping a secret beat.")


# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------
def tell(scene: Scene, signal: Signal, gift: Gift, hero_name: str, trait: str) -> World:
    world = World(scene=scene)
    hero = world.add(Entity(id=hero_name, kind="character", type="spirit"))
    earth = world.add(Entity(id="Earth", kind="thing", type="earth", label="Earth"))
    gift_ent = world.add(Entity(
        id=gift.id,
        type=gift.id,
        label=gift.label,
        phrase=gift.phrase,
        caretaker=hero.id,
        owner=hero.id,
    ))

    world.facts.update(hero=hero, earth=earth, signal=signal, scene=scene, gift=gift_ent, trait=trait)

    world.say(f"{hero.id} was a {trait} spirit who loved to listen to Earth.")
    world.say(f"{hero.id} could hear {signal.noise} in tiny places and turn it into a rhyme.")
    world.say(scene_sentence(scene, signal))
    world.say(f"{hero.id} held {gift.label} close, because {gift.phrase} made the path feel ready for adventure.")

    world.para()
    world.say(f"One day, {hero.id} chose to {signal.verb}.")
    simulate_noise(world, hero, signal, gift)
    world.say(f"But {signal.cue}, and that meant the path might lose its calm and its way.")

    world.para()
    world.say(f"{hero.id} paused, then listened harder.")
    if signal.id in {"drum", "footsteps"}:
        world.say(f'"{signal.rhyme}," {hero.id} sang, and the beat slowed down like a kitten curling up.')
    else:
        world.say(f'"{signal.rhyme}," {hero.id} whispered, and the sound curled gently through the air.')

    if gift.id == "boots":
        world.say(f"{hero.id} stepped into the trail boots, and the ground answered with steady tap-tap steps.")
        world.say(f"With each careful step, {earth.label if earth.label else "Earth"} stayed smooth, and the adventure kept going.")
        world.facts["resolved"] = True
    elif gift.id == "cloak":
        world.say(f"{hero.id} wrapped on the moon-cloak, and the sharp air turned soft around the rhythm.")
        world.say(f"The rhyme came first, the noise came second, and the whole path felt safe enough to sing aloud.")
        world.facts["resolved"] = True
    else:
        world.say(f"{hero.id} lifted the lantern, and its warm glow made every turn easier to follow.")
        world.say(f"At the end, {hero.id} walked on with {earth.label if earth.label else 'Earth'} below and the rhyme above.")
        world.facts["resolved"] = True

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    signal = f["signal"]
    gift = f["gift"]
    return [
        f'Write a short adventure story for a young child about a spirit named {hero.id} who hears {signal.noise} and uses rhyme.',
        f"Tell a gentle adventure where {hero.id} follows a noisy path, worries about {signal.risk}, and finds help from {gift.label}.",
        f'Write a story that includes sound effects like "{signal.noise}" and a rhyme like "{signal.rhyme}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    signal: Signal = f["signal"]
    gift: Entity = f["gift"]
    scene: Scene = f["scene"]
    trait = f["trait"]
    qa = [
        QAItem(
            question=f"Who is the story about in {scene.place}?",
            answer=f"The story is about {trait} {hero.type} named {hero.id}, who goes on an adventure in {scene.place}.",
        ),
        QAItem(
            question=f"What sound did {hero.id} hear when {hero.id} chose to {signal.verb}?",
            answer=f"{hero.id} heard {signal.noise}, and it felt like a beat moving through the air.",
        ),
        QAItem(
            question=f"What helped {hero.id} make the adventure safe again?",
            answer=f"{gift.label} helped {hero.id}, because it made the journey steadier and easier to follow.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did {hero.id} use rhyme during the tricky part?",
                answer=f"{hero.id} said, \"{signal.rhyme}\" and the rhyme helped calm the moment down.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a word or phrase that helps a story make a noise feel vivid, like boom, tap, or shh.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a set of words or lines that sound alike at the end, which makes speech feel musical.",
        ),
        QAItem(
            question="What is Earth in a story like this?",
            answer="Earth can mean the ground and the world beneath a character's feet, which can feel steady, rough, or soft.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
signal_combo(Scene,Signal,Gift) :- scene(Scene), signal(Signal), gift(Gift), valid(Scene,Signal,Gift).

valid(Scene,drum,boots) :- scene(Scene), signal(drum), gift(boots).
valid(Scene,windchime,cloak) :- scene(Scene), signal(windchime), gift(cloak).
valid(Scene,footsteps,boots) :- scene(Scene), signal(footsteps), gift(boots).
valid(Scene,whisper,cloak) :- scene(Scene), signal(whisper), gift(cloak).
valid(Scene,whisper,lantern) :- scene(Scene), signal(whisper), gift(lantern).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for sig in SIGNALS.values():
        lines.append(asp.fact("signal", sig.id))
    for g in GIFTS.values():
        lines.append(asp.fact("gift", g.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: spirit, earth, sound effects, rhyme.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.signal and args.gift:
        if (args.scene or "valley", args.signal, args.gift) not in valid_combos():
            raise StoryError(explain_rejection(SIGNALS[args.signal], GIFTS[args.gift]))
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.signal is None or c[1] == args.signal)
              and (args.gift is None or c[2] == args.gift)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, signal, gift = rng.choice(sorted(combos))
    return StoryParams(
        scene=scene,
        signal=signal,
        gift=gift,
        name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], SIGNALS[params.signal], GIFTS[params.gift], params.name, params.trait)
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
    StoryParams(scene="valley", signal="drum", gift="boots", name="Nova", trait="brave"),
    StoryParams(scene="cave", signal="windchime", gift="cloak", name="Iris", trait="curious"),
    StoryParams(scene="forest", signal="whisper", gift="lantern", name="Theo", trait="spirited"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
