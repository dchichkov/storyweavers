#!/usr/bin/env python3
"""
A standalone storyworld about a brave adventure at a disco cave where sound
effects trigger a surprising transformation.
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
    wore: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "male", "king", "prince", "brother"}
        female = {"girl", "woman", "mother", "mom", "queen", "princess", "sister"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    name: str
    gender: str
    trait: str
    place: str = "the disco cave"
    seed: Optional[int] = None


@dataclass(frozen=True)
class DiscoThing:
    id: str
    label: str
    phrase: str
    sound: str
    transform_to: str
    transform_label: str
    transform_phrase: str
    reveal: str


HERO_NAMES = ["Leo", "Max", "Theo", "Noah", "Ben", "Finn", "Jack", "Eli"]
TRAITS = ["curious", "brave", "cheerful", "lively", "bold"]
PLACES = ["the disco cave", "the neon hall", "the echo tunnel"]


DISCO_ARTIFACTS = {
    "mirror_ball": DiscoThing(
        id="mirror_ball",
        label="mirror ball",
        phrase="a silver mirror ball",
        sound="ting-ting",
        transform_to="glitter_cloak",
        transform_label="glitter cloak",
        transform_phrase="a soft glitter cloak",
        reveal="spun like a bright moon",
    ),
    "boom_box": DiscoThing(
        id="boom_box",
        label="boom box",
        phrase="a red boom box",
        sound="boom-boom",
        transform_to="dance_shoes",
        transform_label="dance shoes",
        transform_phrase="a pair of shiny dance shoes",
        reveal="thumped with a happy beat",
    ),
    "speaker_stone": DiscoThing(
        id="speaker_stone",
        label="speaker stone",
        phrase="a carved speaker stone",
        sound="whaaaam",
        transform_to="star_hat",
        transform_label="star hat",
        transform_phrase="a tiny starry hat",
        reveal="thrummed like a singing drum",
    ),
}


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_spark(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    for artifact in [e for e in world.entities.values() if e.kind == "artifact"]:
        if artifact.meters.get("sound", 0.0) < THRESHOLD:
            continue
        sig = f"spark:{artifact.id}"
        if sig in world.fired:
            continue
        world.fired.add(sig)
        artifact.memes["glow"] = artifact.memes.get("glow", 0.0) + 1
        out.append(f"The {artifact.label} {world.facts['disco_map'][artifact.id].reveal}.")
        hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    return out


def _r_transform(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    for artifact in [e for e in world.entities.values() if e.kind == "artifact"]:
        if artifact.memes.get("glow", 0.0) < THRESHOLD:
            continue
        sig = f"transform:{artifact.id}"
        if sig in world.fired:
            continue
        world.fired.add(sig)
        new_id = world.facts["disco_map"][artifact.id].transform_to
        if new_id in world.entities:
            continue
        spec = world.facts["transform_specs"][artifact.id]
        new_ent = Entity(
            id=new_id,
            kind="treasure",
            type="treasure",
            label=spec.transform_label,
            phrase=spec.transform_phrase,
            owner=hero.id,
        )
        new_ent.meters["bright"] = 1
        world.add(new_ent)
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        out.append(f"The sound turned into {spec.transform_phrase}.")
    return out


RULES = [Rule("spark", _r_spark), Rule("transform", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def play_sound(world: World, artifact: Entity, kind: DiscoThing) -> None:
    artifact.meters["sound"] = artifact.meters.get("sound", 0.0) + 1
    world.say(f"{world.get('hero').id} tapped the {artifact.label}, and it went {kind.sound}!")
    propagate(world, narrate=True)


def story_begin(world: World) -> None:
    hero = world.get("hero")
    world.say(
        f"{hero.id} was a little {hero.type} who loved adventure, especially when the night "
        f"glowed with disco lights."
    )
    world.say(
        f"He had heard that {world.place} hid strange sounds, bright secrets, and one special surprise."
    )


def story_middle(world: World) -> None:
    hero = world.get("hero")
    world.para()
    world.say(
        f"Inside {world.place}, the floor shimmered, and the air buzzed like it was waiting for music."
    )
    world.say(
        f"{hero.id} followed the echo until he found three glowing things resting in the dark."
    )
    for artifact in [world.get("mirror_ball"), world.get("boom_box"), world.get("speaker_stone")]:
        spec = world.facts["disco_map"][artifact.id]
        world.say(f"The {artifact.label} {spec.reveal}.")
        play_sound(world, artifact, spec)


def story_end(world: World) -> None:
    hero = world.get("hero")
    world.para()
    treasure_names = [e.label for e in world.entities.values() if e.kind == "treasure"]
    if treasure_names:
        joined = ", ".join(treasure_names[:-1]) + (f", and {treasure_names[-1]}" if len(treasure_names) > 1 else treasure_names[0])
        world.say(
            f"At last, {hero.id} stood in the sparkling room wearing a grin as wide as the tunnel."
        )
        world.say(
            f"The disco sounds had changed into {joined}, and {hero.id} carried the shining prizes home."
        )
    else:
        world.say(
            f"At last, {hero.id} smiled in the glow of the disco cave, glad that the strange sounds had led him safely onward."
        )


def build_world(params: StoryParams) -> World:
    world = World(params.place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name))
    # keep only one canonical hero entry for narration and Q&A
    world.entities.pop(params.name, None)
    world.entities["hero"] = Entity(id=params.name, kind="character", type=params.gender, label=params.name)

    world.add(Entity(id="mirror_ball", kind="artifact", type="thing", label="mirror ball", phrase="a silver mirror ball"))
    world.add(Entity(id="boom_box", kind="artifact", type="thing", label="boom box", phrase="a red boom box"))
    world.add(Entity(id="speaker_stone", kind="artifact", type="thing", label="speaker stone", phrase="a carved speaker stone"))

    world.facts["disco_map"] = DISCO_ARTIFACTS
    world.facts["transform_specs"] = DISCO_ARTIFACTS

    return world


def generate_story(world: World) -> None:
    story_begin(world)
    story_middle(world)
    story_end(world)


def generation_prompts(world: World) -> list[str]:
    hero = world.get("hero")
    return [
        f"Write a short adventure story about {hero.id} exploring a disco cave where sound effects cause magical transformations.",
        f"Tell a child-friendly story in which a male hero named {hero.id} hears disco sounds and discovers a surprising change.",
        f"Create a simple adventure with a glowing cave, sound effects like boom-boom and ting-ting, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    return [
        QAItem(
            question=f"Where did {hero.id} go on the adventure?",
            answer=f"{hero.id} went to {world.place}, a glowing place full of disco sounds and surprises.",
        ),
        QAItem(
            question=f"What made the story change as {hero.id} explored?",
            answer="The sound effects changed the scene. Each bright noise made something magical happen.",
        ),
        QAItem(
            question=f"What did the disco sounds turn into by the end?",
            answer="The disco sounds turned into shiny treasures that the hero could carry home.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a disco sound effect?",
            answer="A disco sound effect is a bright, musical noise like ting-ting or boom-boom that makes a scene feel lively.",
        ),
        QAItem(
            question="What is transformation in a story?",
            answer="Transformation means something changes into something new, like a sound turning into a shiny treasure.",
        ),
        QAItem(
            question="What makes an adventure story exciting?",
            answer="An adventure story is exciting because the character explores a new place, finds surprises, and learns what to do next.",
        ),
    ]


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
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


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
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
hero(H) :- chosen_hero(H).
sound(S) :- sound_effect(S).
artifact(A) :- disco_artifact(A).

triggers_transform(A) :- artifact(A), sound_level(A, L), L > 0.
makes_new_treasure(A, T) :- triggers_transform(A), transforms_into(A, T).

#show triggers_transform/1.
#show makes_new_treasure/2.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("chosen_hero", "hero"),
    ]
    for aid, spec in DISCO_ARTIFACTS.items():
        lines.append(asp.fact("disco_artifact", aid))
        lines.append(asp.fact("sound_effect", spec.sound))
        lines.append(asp.fact("transforms_into", aid, spec.transform_to))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show triggers_transform/1.\n#show makes_new_treasure/2."))
    trig = set(asp.atoms(model, "triggers_transform"))
    make = set(asp.atoms(model, "makes_new_treasure"))
    expected_trig = {(k,) for k in DISCO_ARTIFACTS}
    expected_make = {(k, v.transform_to) for k, v in DISCO_ARTIFACTS.items()}
    if trig == expected_trig and make == expected_make:
        print(f"OK: ASP parity verified for {len(expected_trig)} transformations.")
        return 0
    print("MISMATCH between ASP and Python registries.")
    print("triggers only in ASP:", sorted(trig - expected_trig))
    print("triggers only in python:", sorted(expected_trig - trig))
    print("makes only in ASP:", sorted(make - expected_make))
    print("makes only in python:", sorted(expected_make - make))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Disco adventure storyworld with sound-effect transformations.")
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--gender", choices=["male"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--place", choices=PLACES)
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
    gender = args.gender or "male"
    if gender != "male":
        raise StoryError("This world is built for a male hero.")
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    place = args.place or rng.choice(PLACES)
    return StoryParams(name=name, gender=gender, trait=trait, place=place)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
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


CURATED = [
    StoryParams(name="Leo", gender="male", trait="brave", place="the disco cave"),
    StoryParams(name="Max", gender="male", trait="curious", place="the neon hall"),
    StoryParams(name="Theo", gender="male", trait="lively", place="the echo tunnel"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show triggers_transform/1.\n#show makes_new_treasure/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        try:
            import asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            return
        model = asp.one_model(asp_program("#show triggers_transform/1.\n#show makes_new_treasure/2."))
        print("triggers_transform:", sorted(asp.atoms(model, "triggers_transform")))
        print("makes_new_treasure:", sorted(asp.atoms(model, "makes_new_treasure")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name}: {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
