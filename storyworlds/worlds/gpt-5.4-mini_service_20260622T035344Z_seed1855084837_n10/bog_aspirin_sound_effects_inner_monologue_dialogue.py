#!/usr/bin/env python3
"""
storyworlds/worlds/bog_aspirin_sound_effects_inner_monologue_dialogue.py
========================================================================

A compact fairy-tale storyworld about a muddy bog, a headache, and a kind
remedy. The tale uses sound effects, inner monologue, and dialogue while keeping
the state model small and concrete.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str | None = None
    caretaker: str | None = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "princess"}
        male = {"boy", "father", "dad", "man", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id


@dataclass
class BogScene:
    id: str
    place: str
    mud_depth: int
    sounds: list[str]
    setting_line: str
    risk_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    reason: str
    effect_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    scene: str
    remedy: str
    hero: str
    hero_type: str
    companion: str
    companion_type: str
    parent: str
    mood: str
    seed: int | None = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, ...]] = set()

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
        import copy as _copy
        clone = World()
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = _copy.deepcopy(self.facts)
        clone.history = _copy.deepcopy(self.history)
        clone.paragraphs = [list(p) for p in self.paragraphs]
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "mire_bog": BogScene(
        id="mire_bog",
        place="the mossy bog",
        mud_depth=3,
        sounds=["splash", "glop", "slurp"],
        setting_line="At the edge of the mossy bog, reeds leaned like sleepy green dancers.",
        risk_word="mud",
        tags={"bog", "mud"},
    ),
    "fairy_pool": BogScene(
        id="fairy_pool",
        place="the fairy bog",
        mud_depth=2,
        sounds=["plip", "plop", "splish"],
        setting_line="By a fairy bog with silver lilies, the water whispered under a moon-white mist.",
        risk_word="bog",
        tags={"bog"},
    ),
    "old_moor": BogScene(
        id="old_moor",
        place="the old moor bog",
        mud_depth=4,
        sounds=["glub", "glub", "squelch"],
        setting_line="On the old moor bog, the ground was soft and dark, and every step answered with a wet sigh.",
        risk_word="mud",
        tags={"bog", "mud"},
    ),
}

REMEDIES = {
    "aspirin": Remedy(
        id="aspirin",
        label="aspirin",
        phrase="a small aspirin tablet",
        reason="to calm a headache",
        effect_line="The little tablet helped the ache grow quiet, like a door closing on a noisy wind.",
        tags={"aspirin", "medicine"},
    ),
    "tea": Remedy(
        id="tea",
        label="tea",
        phrase="a warm cup of tea",
        reason="to rest and feel better",
        effect_line="The warm tea soothed the ache and made the whole cottage feel gentle again.",
        tags={"tea"},
    ),
    "nap": Remedy(
        id="nap",
        label="nap",
        phrase="a soft blanket and a short nap",
        reason="to rest the tired head",
        effect_line="After a little nap, the ache faded like mist in sunrise.",
        tags={"rest"},
    ),
}

GIRL_NAMES = ["Elin", "Mira", "Rose", "Lena", "Faye", "Iris"]
BOY_NAMES = ["Owen", "Bram", "Finn", "Jory", "Toby", "Nell"]
TRAITS = ["brave", "gentle", "curious", "lively", "careful"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for scene in SETTINGS:
        for remedy in REMEDIES:
            combos.append((scene, remedy))
    return combos


def explain_rejection(scene: str, remedy: str) -> str:
    return f"(No story: the chosen scene {scene!r} and remedy {remedy!r} do not fit this little fairy tale.)"


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, scene in SETTINGS.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("place", sid, scene.place))
        lines.append(asp.fact("mud_depth", sid, scene.mud_depth))
        for sfx in scene.sounds:
            lines.append(asp.fact("sound", sid, sfx))
    for rid, rem in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("reason", rid, rem.reason))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, R) :- scene(S), remedy(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH between Python and ASP valid combinations.")
        print("  only python:", sorted(py - cl))
        print("  only asp:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(scene=None, remedy=None, hero=None, hero_type=None, companion=None, companion_type=None, parent=None, mood=None), random.Random(7)))
        if not sample.story.strip():
            ok = False
            print("SMOKE TEST FAILED: empty story.")
    except Exception as err:
        ok = False
        print(f"SMOKE TEST FAILED: {err}")
    if ok:
        print(f"OK: ASP parity and smoke test passed ({len(py)} combos).")
        return 0
    return 1


@dataclass
class StoryParams:
    scene: str
    remedy: str
    hero: str
    hero_type: str
    companion: str
    companion_type: str
    parent: str
    mood: str
    seed: int | None = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale bog storyworld with aspirin, sound effects, inner monologue, and dialogue.")
    ap.add_argument("--scene", choices=SETTINGS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--mood", choices=["worried", "tired", "stubborn", "hopeful"])
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
    combos = valid_combos()
    if args.scene and args.scene not in SETTINGS:
        raise StoryError("Unknown scene.")
    if args.remedy and args.remedy not in REMEDIES:
        raise StoryError("Unknown remedy.")
    filtered = [
        c for c in combos
        if (args.scene is None or c[0] == args.scene)
        and (args.remedy is None or c[1] == args.remedy)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    scene, remedy = rng.choice(sorted(filtered))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    companion_type = args.companion_type or ("boy" if hero_type == "girl" and rng.random() < 0.5 else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    companion_pool = [n for n in (GIRL_NAMES if companion_type == "girl" else BOY_NAMES) if n != hero]
    companion = args.companion or rng.choice(companion_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    mood = args.mood or rng.choice(TRAITS)
    return StoryParams(scene=scene, remedy=remedy, hero=hero, hero_type=hero_type, companion=companion, companion_type=companion_type, parent=parent, mood=mood)


def tell(scene: BogScene, remedy: Remedy, params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero, traits=[params.mood], memes=defaultdict(float)))
    companion = world.add(Entity(id="companion", kind="character", type=params.companion_type, label=params.companion, traits=["kind"], memes=defaultdict(float)))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent, memes=defaultdict(float)))
    bog = world.add(Entity(id="bog", type="place", label=scene.place, tags=set(scene.tags), attrs={"mud_depth": scene.mud_depth}))
    aspirin = world.add(Entity(id="aspirin", type="medicine", label="aspirin", phrase=remedy.phrase, tags=set(remedy.tags), attrs={"reason": remedy.reason}))
    ache = world.add(Entity(id="ache", type="feeling", label="headache"))
    hero.meters["mud"] += scene.mud_depth / 2
    hero.memes["worry"] += 1
    hero.memes["hope"] += 1
    world.facts.update(hero=hero, companion=companion, parent=parent, bog=bog, aspirin=aspirin, ache=ache, scene=scene, remedy=remedy)
    world.say(f"Once upon a time, {params.hero} and {params.companion} wandered to {scene.place}.")
    world.say(scene.setting_line)
    world.say(f"Then came a soft sound: {' '.join(scene.sounds[:2])}! The bog tugged at their boots with a muddy grin.")
    world.para()
    world.say(f"{params.hero} felt a little ache behind the eyes.")
    world.say(f"Inside {params.hero}'s heart, a tiny thought whispered: “{remedy.phrase} might help.”")
    world.say(f"{params.companion} said, “Shall we go back to the cottage for {remedy.phrase}?”")
    world.say(f"{params.hero} answered, “Yes, please. My head feels as heavy as a rain cloud.”")
    hero.memes["relief"] += 1
    hero.meters["ache"] = 0
    world.para()
    world.say(f"Back at the cottage, {params.parent} listened kindly.")
    world.say(f"“Here you are,” {params.parent} said, “{remedy.phrase} can help {remedy.reason}.”")
    world.say(f"{remedy.effect_line}")
    world.say(f"{params.hero} smiled, and the bog-mud was left far behind at the door.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene = f["scene"]
    remedy = f["remedy"]
    return [
        f'Write a fairy-tale story that includes the words “bog” and “aspirin” and features sound effects, inner monologue, and dialogue.',
        f"Tell a gentle fairy tale where {f['hero'].label} gets a headache near {scene.place} and someone offers {remedy.phrase}.",
        f"Write a short magical story with a muddy bog, a worried child, and a kind remedy that helps the child feel better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    parent = f["parent"]
    scene = f["scene"]
    remedy = f["remedy"]
    return [
        QAItem(
            question=f"Why did {hero.label} want to leave {scene.place}?",
            answer=f"{hero.label} wanted to leave because {hero.label}'s head hurt and the bog felt muddy and tiring. The thought of {remedy.phrase} made {hero.label} feel hopeful about going home.",
        ),
        QAItem(
            question=f"What did {companion.label} say about {remedy.label}?",
            answer=f"{companion.label} said, “Shall we go back to the cottage for {remedy.phrase}?” It was a kind question that helped the story turn toward comfort.",
        ),
        QAItem(
            question=f"How did {parent.label} help at the end?",
            answer=f"{parent.label} listened kindly and brought {remedy.phrase} so {hero.label} could feel better. That choice closed the muddy adventure with a calm, cozy ending.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    scene = f["scene"]
    remedy = f["remedy"]
    return [
        QAItem("What is a bog?", "A bog is a wet marshy place where the ground feels soft, muddy, and slow to walk on."),
        QAItem("What is aspirin for?", "Aspirin is a medicine some grown-ups use to help with pain or a headache."),
        QAItem("Why do fairy tales often use dialogue?", "Dialogue lets the characters speak for themselves, which makes the story feel lively and easy to follow."),
        QAItem("What are sound effects in a story?", "Sound effects are words that suggest noises, like splash, glop, or whisper, so the reader can hear the scene in their mind."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story Q&A ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World Q&A ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"facts={list(world.facts.keys())}")
    lines.append(f"history={world.history}")
    return "\n".join(lines)


CURATED = [
    StoryParams(scene="mire_bog", remedy="aspirin", hero="Elin", hero_type="girl", companion="Bram", companion_type="boy", parent="mother", mood="worried"),
    StoryParams(scene="fairy_pool", remedy="tea", hero="Owen", hero_type="boy", companion="Lena", companion_type="girl", parent="father", mood="tired"),
    StoryParams(scene="old_moor", remedy="nap", hero="Faye", hero_type="girl", companion="Toby", companion_type="boy", parent="mother", mood="hopeful"),
]


def generate(params: StoryParams) -> StorySample:
    scene = SETTINGS.get(params.scene)
    remedy = REMEDIES.get(params.remedy)
    if scene is None or remedy is None:
        raise StoryError("Invalid params.")
    world = tell(scene, remedy, params)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for scene, remedy in asp_valid_combos():
            print(scene, remedy)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx + 1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
