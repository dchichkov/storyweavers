#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.3-codex-spark/watt_prominent_sound_effects_detective_story.py
====================================================================================

Source tale:
At night in a prominent museum gallery, a child detective hears a tiny 12-watt lamp
repeat a sharp sound pattern: click, click, click, pause. The child tracks the sound,
then follows either a listening pattern, a watt trace, or a wire trace until the source
is exposed. The culprit is confronted with grounded evidence, and the lamp returns to a
steady visible state.

Implementation notes:
- Typed world entities with physical `meters` and emotional `memes`.
- Detective story arc with clear beginning, state-driven middle, and ending image.
- Sound effects drive the clue chain.
- ASP twin for deterministic gate parity checking.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Scene:
    key: str
    phrase: str
    opening_image: str
    ending_image: str
    suspects: tuple[str, ...]
    lamp_label: str
    ambient: str
    baseline_watt: float


@dataclass(frozen=True)
class Suspect:
    key: str
    name: str
    role: str
    motive: str
    tamper_mode: str
    signature_word: str
    signature: str
    scenes: tuple[str, ...]
    fear_gain: float


@dataclass(frozen=True)
class Method:
    key: str
    phrase: str
    solves: str
    gear: str
    note: str


@dataclass
class StoryParams:
    scene: str
    suspect: str
    method: str
    hero: str
    hero_gender: str
    helper: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "detective"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in {"boy", "adult"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryBeat:
    key: str
    text: str


@dataclass
class World:
    params: StoryParams
    scene_cfg: Scene
    suspect_cfg: Suspect
    method_cfg: Method
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[StoryBeat] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def remember(self, key: str, text: str) -> None:
        self.history.append(StoryBeat(key=key, text=text))

    def render(self) -> str:
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(f"  scene={self.scene_cfg.key}")
        lines.append(f"  suspect={self.suspect_cfg.key}")
        lines.append(f"  method={self.method_cfg.key}")
        for ent in self.entities.values():
            lines.append(
                f"  {ent.id}: kind={ent.kind} label={ent.label} location={ent.location} "
                f"meters={dict(ent.meters)} memes={dict(ent.memes)}"
            )
        lines.append(f"  facts={self.facts}")
        lines.append("  history:")
        for beat in self.history:
            lines.append(f"    - {beat.key}: {beat.text}")
        return "\n".join(lines)


SCENES: dict[str, Scene] = {
    "prominent_gallery": Scene(
        key="prominent_gallery",
        phrase="the prominent gallery with a brass display case",
        opening_image=(
            "the old brass lamp inside the case made the first room feel very quiet and very proud"
        ),
        ending_image=(
            "the same prominent 12-watt lamp glowed steadily and the room looked peaceful again"
        ),
        suspects=("milo", "jade"),
        lamp_label="the prominent 12-watt brass lamp",
        ambient="only soft footsteps and the clock room hush",
        baseline_watt=12.0,
    ),
    "prominent_clock_room": Scene(
        key="prominent_clock_room",
        phrase="the prominent clock room above the museum stair",
        opening_image=(
            "the clock cogs clicked on their own rhythm while the 12-watt display lamp blinked too brightly"
        ),
        ending_image=(
            "the clock room returned to a steady tick and the same lamp kept a calm 12-watt glow"
        ),
        suspects=("milo", "iris"),
        lamp_label="the prominent 12-watt lamp beside the clock case",
        ambient="a careful gear rhythm and faint paper rustle",
        baseline_watt=12.0,
    ),
}

SUSPECTS: dict[str, Suspect] = {
    "milo": Suspect(
        key="milo",
        name="Milo",
        role="night helper",
        motive="delay the alarm test to hide a missing spare part",
        tamper_mode="tone",
        signature_word="click",
        signature="a sharp click, click, click then pause",
        scenes=("prominent_gallery", "prominent_clock_room"),
        fear_gain=1.6,
    ),
    "iris": Suspect(
        key="iris",
        name="Iris",
        role="record keeper",
        motive="change a reading order and keep control for one more shift",
        tamper_mode="watt",
        signature_word="hiss",
        signature="a soft hiss that rose when the meter climbed",
        scenes=("prominent_clock_room",),
        fear_gain=1.4,
    ),
    "jade": Suspect(
        key="jade",
        name="Jade",
        role="case assistant",
        motive="cover a missing screw behind the wallboard",
        tamper_mode="wire",
        signature_word="buzz",
        signature="a low buzz that started at a loose wire",
        scenes=("prominent_gallery",),
        fear_gain=1.5,
    ),
}

METHODS: dict[str, Method] = {
    "listen_chain": Method(
        key="listen_chain",
        phrase="listen for the sound chain pattern and compare the rhythm",
        solves="tone",
        gear="listening notebook",
        note="A real signature usually repeats, not drifts.",
    ),
    "meter_probe": Method(
        key="meter_probe",
        phrase="run a watt check against the 12-watt baseline",
        solves="watt",
        gear="portable meter",
        note="A drift above baseline suggests added pull on the line.",
    ),
    "wire_trace": Method(
        key="wire_trace",
        phrase="trace the power route from the lamp to the nearby socket",
        solves="wire",
        gear="chalk tape and tracing sketch",
        note="Always secure a segment before touching a line.",
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Nora", "Lina", "Mina", "Iris"),
    "boy": ("Kai", "Theo", "Noah", "Ravi"),
}

HELPERS = ("Officer Rowan", "Mama Jo", "Uncle Kiran", "Mr. Bell")


def valid_combo(scene_key: str, suspect_key: str, method_key: str) -> bool:
    if scene_key not in SCENES or suspect_key not in SUSPECTS or method_key not in METHODS:
        return False
    scene = SCENES[scene_key]
    suspect = SUSPECTS[suspect_key]
    method = METHODS[method_key]
    return (
        suspect_key in scene.suspects
        and scene_key in suspect.scenes
        and method.solves == suspect.tamper_mode
    )


def invalid_reason(scene_key: str, suspect_key: str, method_key: str) -> str:
    if scene_key not in SCENES:
        return f"No story: unknown scene {scene_key!r}."
    if suspect_key not in SUSPECTS:
        return f"No story: unknown suspect {suspect_key!r}."
    if method_key not in METHODS:
        return f"No story: unknown method {method_key!r}."

    scene = SCENES[scene_key]
    suspect = SUSPECTS[suspect_key]
    method = METHODS[method_key]

    if scene_key not in suspect.scenes or suspect_key not in scene.suspects:
        return (
            f"No story: {suspect.name} is not present in {scene.phrase}. "
            f"This suspect belongs only to: {', '.join(suspect.scenes)}."
        )
    if method.solves != suspect.tamper_mode:
        return (
            f"No story: method {method.key} checks {method.solves} clues, "
            f"but this case needs {suspect.tamper_mode} clues."
        )
    return "No story: invalid combination."


def all_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for scene_key in sorted(SCENES):
        for suspect_key in sorted(SUSPECTS):
            for method_key in sorted(METHODS):
                if valid_combo(scene_key, suspect_key, method_key):
                    combos.append((scene_key, suspect_key, method_key))
    return combos


def _matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = all_combos()
    filtered = [
        (scene, suspect, method)
        for scene, suspect, method in combos
        if (args.scene is None or args.scene == scene)
        and (args.suspect is None or args.suspect == suspect)
        and (args.method is None or args.method == method)
    ]
    if (args.scene or args.suspect or args.method) and not filtered:
        raise StoryError("No story: no valid combination matches requested filters.")
    return filtered


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combos = _matching_combos(args)
    scene_key, suspect_key, method_key = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or rng.choice(HERO_NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(
        scene=scene_key,
        suspect=suspect_key,
        method=method_key,
        hero=hero,
        hero_gender=gender,
        helper=helper,
        seed=(args.seed or 1000) + index,
    )


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.scene, params.suspect, params.method):
        raise StoryError(invalid_reason(params.scene, params.suspect, params.method))

    scene = SCENES[params.scene]
    suspect = SUSPECTS[params.suspect]
    method = METHODS[params.method]

    world = World(params=params, scene_cfg=scene, suspect_cfg=suspect, method_cfg=method)

    hero = Entity(
        id="hero",
        kind=params.hero_gender,
        label=params.hero,
        location=scene.key,
        meters={"focus": 1.0, "confidence": 1.1, "patience": 0.7},
        memes={"curiosity": 1.2, "worry": 0.2, "relief": 0.0, "focus": 1.0, "confidence": 1.1},
    )
    helper = Entity(
        id="helper",
        kind="adult",
        label=params.helper,
        location=scene.key,
        meters={"steady": 1.3},
        memes={"care": 1.0, "calm": 1.1},
    )
    suspect_ent = Entity(
        id="suspect",
        kind="person",
        label=suspect.name,
        location=scene.key,
        meters={"opportunity": 0.6},
        memes={"guilt": 0.0, "fear": 0.1},
    )
    lamp = Entity(
        id="lamp",
        kind="object",
        label=scene.lamp_label,
        location=scene.key,
        meters={"watt": scene.baseline_watt, "noise": 0.0, "stability": 1.0},
        memes={"prominence": 1.0},
    )
    meter = Entity(
        id="meter",
        kind="instrument",
        label="portable meter",
        location=scene.key,
        meters={"reading": scene.baseline_watt, "drift": 0.0},
        memes={"clarity": 1.0},
    )
    trace = Entity(
        id="wire_trace",
        kind="artifact",
        label="wall route card",
        location=scene.key,
        meters={"segments": 0.0},
        memes={"order": 0.0},
    )

    world.add(hero)
    world.add(helper)
    world.add(suspect_ent)
    world.add(lamp)
    world.add(meter)
    world.add(trace)

    world.facts = {
        "seed_word_1": "watt",
        "seed_word_2": "prominent",
        "feature": "Sound Effects",
        "style": "Detective Story",
        "case_state": "active",
        "method": method.key,
        "evidence_mode": suspect.tamper_mode,
        "initial_sound": suspect.signature,
        "culprit": suspect.name,
        "ending_image": scene.ending_image,
        "baseline_watt": scene.baseline_watt,
    }
    world.remember("setup", f"scene={scene.key} suspect={suspect.key} method={method.key}")
    return world


def _opening(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    scene = world.scene_cfg

    world.say(
        f"{hero.label} arrived at {scene.phrase}, while {helper.label} waited by the side door."
    )
    world.say(
        f"The room was mostly quiet except for {scene.ambient}, but {scene.lamp_label} looked restless. "
        f"It was a prominent detail in the case, and {hero.label} started a full note sheet immediately."
    )
    world.remember("opening", "setting established")


def _hear_sound(world: World) -> None:
    hero = world.get("hero")
    scene = world.scene_cfg
    suspect = world.suspect_cfg
    lamp = world.get("lamp")

    hero.memes["curiosity"] += 0.6
    lamp.meters["noise"] = 1.8
    lamp.memes["prominence"] = 0.4
    world.say(
        f"A sound rose from {lamp.label}: {suspect.signature}. "
        f"It sounded like {suspect.signature_word}, then {suspect.signature_word}, then {suspect.signature_word} in a short chain."
    )
    world.say(
        f"{hero.label} wrote the sequence down as {suspect.signature_word}-{suspect.signature_word}-pause-" 
        f"{suspect.signature_word} and added a timestamp."
    )
    world.remember("sound", "initial_sound_logged")


def _investigate(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    method = world.method_cfg
    suspect_ent = world.get("suspect")
    lamp = world.get("lamp")
    meter = world.get("meter")
    trace = world.get("wire_trace")

    world.para()
    world.say(f"Method chosen: {method.phrase}.")
    world.say(method.note)

    if method.key == "listen_chain":
        hero.memes["focus"] += 0.8
        hero.memes["confidence"] += 0.3
        lamp.meters["noise"] = 0.4
        suspect_ent.memes["fear"] += 0.6
        world.remember("method", "listen_chain")
        world.say(
            f'"That is too clean to be drift," {helper.label} said. "The pattern repeats in a fixed rhythm."'
        )
        world.say(
            f"{hero.label} matched the rhythm to the suspect signature and marked it as a tone-based trail."
        )
    elif method.key == "meter_probe":
        hero.memes["focus"] += 0.3
        meter.meters["reading"] = world.scene_cfg.baseline_watt + 0.8
        meter.meters["drift"] = 0.8
        suspect_ent.memes["fear"] += 0.5
        world.remember("method", "meter_probe")
        world.say(
            f"{hero.label} checked the reading: it moved from {world.scene_cfg.baseline_watt:.0f} watts to "
            f"{meter.meters['reading']:.1f} watts."
        )
        world.say(
            f"That 0.8-watt rise was clear evidence that something had pulled the line without permission."
        )
    else:
        hero.memes["caution"] = 1.2
        hero.memes["focus"] += 0.9
        trace.meters["segments"] = 7.0
        suspect_ent.memes["fear"] += 0.5
        world.remember("method", "wire_trace")
        world.say(
            f"{hero.label} and {helper.label} followed seven marked segments from {world.scene_cfg.lamp_label} to a back shelf."
        )
        world.say(
            f"The final segment crossed {suspect_ent.label}'s tool drawer, which did not belong in the lamp route."
        )

    world.say(
        f"By then, {hero.label} had a state-backed explanation instead of a guess. "
        f"The case now pointed to one person and one mismatch point."
    )


def _resolve(world: World) -> None:
    hero = world.get("hero")
    suspect = world.suspect_cfg
    suspect_ent = world.get("suspect")
    lamp = world.get("lamp")
    scene = world.scene_cfg

    world.para()
    suspect_ent.memes["fear"] += suspect.fear_gain
    hero.memes["relief"] += 1.0
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.2)

    lamp.meters["watt"] = scene.baseline_watt
    lamp.meters["noise"] = 0.0
    lamp.meters["stability"] = 1.0
    world.facts["case_state"] = "solved"

    world.say(f"{suspect.name} confessed to rerouting the lamp line and causing the false signal pattern.")
    world.say(
        f"The team removed the wrong segment and restored the normal path. "
        f"Soon the room dropped to a calm {scene.baseline_watt:.0f}-watt glow."
    )
    world.say(
        f"At the ending image, {scene.ending_image}. "
        f"The culprit's fear was visible, and the case stood closed with no extra noise."
    )
    world.remember("resolve", "culprit_confronted")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    scene = world.scene_cfg
    suspect = world.suspect_cfg

    _opening(world)
    _hear_sound(world)
    _investigate(world)
    _resolve(world)

    prompts = [
        "Write a child-friendly detective story where sound effects guide each clue step.",
        "Use the required words watt and prominent naturally.",
        "Keep the story complete with a clear beginning, a state-driven turn, and an ending image.",
    ]

    story_qa = [
        QAItem(
            "What was the first clue in this case?",
            f"The first clue was the repeating {suspect.signature_word} pattern from {scene.lamp_label}. "
            f"That sound came before any person was confronted, so it became the anchor for the investigation."
        ),
        QAItem(
            "Why did this method fit this case?",
            f"The team used {world.method_cfg.phrase}, which is designed to test {world.suspect_cfg.tamper_mode} evidence. "
            f"Because the initial sound matched that mode, the method gave a grounded next step instead of guessing."
        ),
        QAItem(
            "What physical state changed to show the culprit's action?",
            f"The lamp moved away from a stable {scene.baseline_watt:.0f}-watt reading during the check and then returned to stable brightness at the end. "
            f"That shift in `meters['watt']` for the lamp proved the line had been tampered with."
        ),
        QAItem(
            "Where did the case end?",
            f"It ended at the same location as the beginning: {scene.phrase}, with the solved route and a steady prominent lamp. "
            f"The team did not move the story outside the gallery, they repaired the physical setup and ended with calm evidence."
        ),
        QAItem(
            "What did the ending image show?",
            f"{scene.ending_image}. "
            f"That image showed the same lamp now stable, no noise spikes, and no reason for continued suspicion."
        ),
    ]

    world_qa = [
        QAItem(
            "What does a prominent detail mean in this world?",
            "A prominent object is one the detective checks first because it gathers many clues. "
            f"Here, the prominent lamp was the shared physical witness for sound, power, and wire tests."
        ),
        QAItem(
            "Why is the 12-watt baseline useful?",
            "The baseline gives a numeric target for the lamp's normal state. "
            f"When readings move off 12 watts, it indicates a concrete state change in the circuit instead of a mood cue."
        ),
        QAItem(
            "How does method evidence stay grounded in this story?",
            "Each method produces state changes that are written into entity meters, such as meter drift and noise strength. "
            f"This lets the detective explain the outcome from world state rather than from a loose narrative guess."
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts"]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")

    lines.extend(["", "== (2) Story questions"])
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")

    lines.extend(["", "== (3) World-knowledge questions"])
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")

    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n" + sample.world.trace())
    if qa:
        print("\n" + format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Watt + prominent detective world.")
    parser.add_argument("--scene", choices=sorted(SCENES))
    parser.add_argument("--suspect", choices=sorted(SUSPECTS))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HERO_NAMES))
    parser.add_argument("--helper")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true", help="list only gate-valid combinations from clingo")
    parser.add_argument("--verify", action="store_true", help="check ASP/Python parity and run deterministic checks")
    parser.add_argument("--show-asp", action="store_true")
    return parser


ASP_RULES = r"""
% Domain and compatibility rules.
valid(S, C, M) :-
    scene(S),
    method(M),
    actor(C),
    suspect_scene(S, C),
    method_solves(M, Mode),
    culprit_mode(C, Mode).

ok :- chosen(S, C, M), valid(S, C, M).

#show valid/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for scene in SCENES:
        rows.append(fact("scene", scene))
    for scene in SCENES.values():
        for suspect in scene.suspects:
            rows.append(fact("suspect_scene", scene.key, suspect))
    for suspect in SUSPECTS.values():
        rows.append(fact("actor", suspect.key))
        rows.append(fact("culprit_mode", suspect.key, suspect.tamper_mode))
    for method in METHODS.values():
        rows.append(fact("method", method.key))
        rows.append(fact("method_solves", method.key, method.solves))
    if params is not None:
        rows.append(fact("chosen", params.scene, params.suspect, params.method))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}"


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from storyworlds.asp import atoms, one_model

    combos: set[tuple[str, str, str]] = set()
    for combo in atoms(one_model(asp_program("#show valid/3.")), "valid"):
        s, c, m = combo
        combos.add((str(s), str(c), str(m)))
    return combos


def asp_accepts(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    return bool(atoms(one_model(asp_facts(params) + "\n" + ASP_RULES + "\nok :- chosen(S, C, M), valid(S, C, M).\n#show ok/0."), "ok"))


def _all_params() -> list[StoryParams]:
    params: list[StoryParams] = []
    for scene_key, suspect_key, method_key in all_combos():
        params.append(
            StoryParams(
                scene=scene_key,
                suspect=suspect_key,
                method=method_key,
                hero="Nora",
                hero_gender="girl",
                helper="Officer Rowan",
            )
        )
    return params


def verify() -> int:
    python_set = {(s, c, m) for s, c, m in all_combos()}
    asp_set = asp_valid_combos()

    if python_set != asp_set:
        print("ASP/Python mismatch:")
        if python_set - asp_set:
            print("  only in Python:", sorted(python_set - asp_set))
        if asp_set - python_set:
            print("  only in ASP:", sorted(asp_set - python_set))
        return 1

    for params in _all_params():
        if not asp_accepts(params):
            raise StoryError(f"ASP rejected valid params: {params}")
        sample = generate(params)
        story = sample.story.lower()
        world = sample.world
        if world is None:
            raise StoryError(f"missing world for params={params}")
        if "watt" not in story or "prominent" not in story:
            raise StoryError(f"seed words missing in story for params={params}")
        if not any(x in story for x in ["click", "buzz", "hiss"]):
            raise StoryError(f"sound effects missing in story for params={params}")
        if world.facts.get("case_state") != "solved":
            raise StoryError(f"case did not resolve for params={params}")
        if world.facts.get("ending_image") not in story:
            raise StoryError(f"ending image not rendered for params={params}")
        if "{}" in story:
            raise StoryError(f"template fragments leaked for params={params}")
        if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
            raise StoryError(f"QA too thin for params={params}")

    print(
        f"OK: ASP and Python agree on {len(python_set)} valid combos, and all verified stories resolved cleanly."
    )
    return 0


def _emit_samples(samples: list[StorySample], args: argparse.Namespace) -> None:
    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### scene={p.scene} suspect={p.suspect} method={p.method}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


def main() -> int:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return 0
    if args.verify:
        try:
            return verify()
        except StoryError as err:
            print(err)
            return 1
    if args.asp:
        for combo in sorted(asp_valid_combos()):
            print("\t".join(combo))
        return 0

    samples: list[StorySample] = []
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)

    try:
        if args.all:
            for idx, (scene_key, suspect_key, method_key) in enumerate(_matching_combos(args)):
                p = StoryParams(
                    scene=scene_key,
                    suspect=suspect_key,
                    method=method_key,
                    hero=args.hero or HERO_NAMES[args.gender or "girl"][idx % len(HERO_NAMES[args.gender or "girl"])],
                    hero_gender=args.gender or "girl",
                    helper=args.helper or HELPERS[idx % len(HELPERS)],
                    seed=base_seed + idx,
                )
                samples.append(generate(p))
        else:
            seen: set[str] = set()
            rng = random.Random(base_seed)
            i = 0
            while len(samples) < args.n and i < args.n * 40:
                params = resolve_params(args, rng, index=i)
                sample = generate(params)
                i += 1
                if sample.story in seen:
                    continue
                seen.add(sample.story)
                samples.append(sample)
            if len(samples) < args.n:
                raise StoryError("Could not generate enough unique stories with this constraint set.")

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        _emit_samples(samples, args)
        return 0
    except StoryError as err:
        print(err)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
