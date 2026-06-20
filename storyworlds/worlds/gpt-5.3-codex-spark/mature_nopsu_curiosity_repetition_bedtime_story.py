#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.3-codex-spark/mature_nopsu_curiosity_repetition_bedtime_story.py
=============================================================================

Seed source tale:
    At bedtime in a calm, mature room, a curious child keeps hearing a
    mature nopsu make the same little signal again and again. They repeat the
    check three times with growing understanding, solve the real mechanical
    cause, and the bedtime space visibly calms down.

This world script is built from that seed. It models physical meters and
emotional memes, keeps repetition as repeated state transitions, and produces
child-facing prose with a clear beginning, middle turn, and concrete ending.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
if not (ROOT / "storyworlds" / "results.py").exists():
    ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Setting:
    key: str
    phrase: str
    opening_image: str
    ending_image: str
    allowed_signals: tuple[str, ...]
    allowed_methods: tuple[str, ...]


@dataclass(frozen=True)
class Signal:
    key: str
    phrase: str
    refrain: str
    explanation: str
    cause: str
    lesson: str
    required_repetitions: int
    compatible_methods: tuple[str, ...]


@dataclass(frozen=True)
class Method:
    key: str
    phrase: str
    helper_needed: bool
    action_text: str
    why_works: str


@dataclass(frozen=True)
class StoryParams:
    setting: str
    signal: str
    method: str
    hero: str
    hero_kind: str
    helper: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    traits: list[str] = field(default_factory=list)
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "mother", "aunt", "grandmother", "woman", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in {"boy", "father", "uncle", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    params: StoryParams
    setting: Setting
    signal: Signal
    method: Method
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.name] = ent
        return ent

    def get(self, name: str) -> Entity:
        return self.entities[name]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        rows: list[str] = ["--- world model state ---"]
        rows.append(f"  setting={self.setting.key}")
        rows.append(f"  signal={self.signal.key}")
        rows.append(f"  method={self.method.key}")
        rows.append(f"  events={self.events}")
        for ent in self.entities.values():
            rows.append(
                f"  {ent.name:<12} kind={ent.kind:<10} "
                f"location={ent.location or 'n/a':<16} meters={dict(ent.meters)} memes={dict(ent.memes)}"
            )
        return "\n".join(rows)


SETTINGS = {
    "moonlight_nursery": Setting(
        key="moonlight_nursery",
        phrase="a moonlight nursery",
        opening_image="a soft quilted nook with a tiny lamp and warm blanket hills",
        ending_image="the blanket nook was still and sleepy, and the mature nopsu breathed a quiet glow",
        allowed_signals=("silver_rhythm", "window_breath"),
        allowed_methods=("count_beats", "ask_parent", "draw_circles"),
    ),
    "attic_study": Setting(
        key="attic_study",
        phrase="a small attic study under wooden beams",
        opening_image="a wooden desk and a tall chair waiting for one last story before bed",
        ending_image="the attic study settled, and the mature nopsu no longer pulsed against the moonlight",
        allowed_signals=("window_breath", "porch_pulse"),
        allowed_methods=("count_beats", "ask_parent", "draw_circles"),
    ),
    "window_veranda": Setting(
        key="window_veranda",
        phrase="a safe window veranda where the night air barely moved",
        opening_image="a chair, one star, and a narrow path of moonlight on the floor",
        ending_image="the veranda held a calm silver hush, and the mature nopsu was still",
        allowed_signals=("silver_rhythm", "porch_pulse"),
        allowed_methods=("count_beats", "draw_circles"),
    ),
}

SIGNALS = {
    "silver_rhythm": Signal(
        key="silver_rhythm",
        phrase="the mature nopsu beside the cushion stool",
        refrain="tap, tap, tap",
        explanation=(
            "The mature nopsu always gave three clear taps when the hidden spring was too tense "
            "at moonrise."
        ),
        cause="a tired spring inside the mature nopsu needed one gentle realignment",
        lesson="repetition can turn a noise into a readable pattern.",
        required_repetitions=3,
        compatible_methods=("count_beats", "ask_parent", "draw_circles"),
    ),
    "window_breath": Signal(
        key="window_breath",
        phrase="the mature nopsu on the window ledge",
        refrain="hush, hush, hush",
        explanation=(
            "The mature nopsu's breath-soft hum repeated in the same breath count every night "
            "while the airflow around it shifted."
        ),
        cause="a tiny lever pin had shifted and the airflow valve needed reset",
        lesson="careful repeated checking protects bedtime peace, no matter how curious a moment feels.",
        required_repetitions=4,
        compatible_methods=("count_beats", "ask_parent"),
    ),
    "porch_pulse": Signal(
        key="porch_pulse",
        phrase="a mature nopsu near the porch light",
        refrain="hum, hum, hum",
        explanation=(
            "The mature nopsu repeated a soft hum until the object beside it reached a true resting point."
        ),
        cause="a loose hinge had made the mature nopsu wobble and lose rhythm",
        lesson="a repeating sign is often a request for one specific physical fix.",
        required_repetitions=3,
        compatible_methods=("draw_circles",),
    ),
}

METHODS = {
    "count_beats": Method(
        key="count_beats",
        phrase="counted the repeated taps",
        helper_needed=False,
        action_text=(
            "{hero} counted the full rhythm with tiny fingers and a sleepy smile, then checked one more round "
            "to be sure the pattern was the same."
        ),
        why_works=(
            "Counting made the curiosity concrete, because the mature nopsu had to be heard as exact beats, "
            "not as a random sound."
        ),
    ),
    "ask_parent": Method(
        key="ask_parent",
        phrase="asked a parent to align the spring",
        helper_needed=True,
        action_text=(
            "{hero} asked {helper} for a hand, and together they traced the mature nopsu's tiny lever while saying "
            "one, two, three."
        ),
        why_works=(
            "An adult could hold the device steady while the child kept the repeated count, so the physical fix was safe."
        ),
    ),
    "draw_circles": Method(
        key="draw_circles",
        phrase="drew the rhythm in a small notebook",
        helper_needed=False,
        action_text=(
            "{hero} drew three circles, one for each repeat, and used the final circle to set the mature nopsu gently "
            "back to rest."
        ),
        why_works=(
            "The circles showed exactly when the mature nopsu looped the same way, which revealed the mechanical fix."
        ),
    ),
}

HEROES = {
    "girl": ("Mina", "Ella", "Sora", "Nia"),
    "boy": ("Leo", "Noah", "Milo", "Ivo"),
}

HELPERS = ("Mum", "Dad", "Grandma", "Uncle Ren")


def _pick_name(kind: str, rng: random.Random) -> str:
    return rng.choice(HEROES[kind])


def _pick_helper(rng: random.Random) -> str:
    return rng.choice(HELPERS)


def valid_combo(setting_key: str, signal_key: str, method_key: str) -> bool:
    if setting_key not in SETTINGS or signal_key not in SIGNALS or method_key not in METHODS:
        return False
    setting = SETTINGS[setting_key]
    signal = SIGNALS[signal_key]
    method = METHODS[method_key]
    return (
        signal_key in setting.allowed_signals
        and method_key in setting.allowed_methods
        and method_key in signal.compatible_methods
    )


def invalid_reason(setting_key: str, signal_key: str, method_key: str) -> str:
    if setting_key not in SETTINGS:
        return f"No story: unknown setting {setting_key!r}."
    if signal_key not in SIGNALS:
        return f"No story: unknown signal {signal_key!r}."
    if method_key not in METHODS:
        return f"No story: unknown method {method_key!r}."

    setting = SETTINGS[setting_key]
    signal = SIGNALS[signal_key]
    method = METHODS[method_key]

    if signal_key not in setting.allowed_signals:
        return (
            f"No story: {setting.phrase} does not allow signal {signal_key!r}. "
            f"Available signals are: {', '.join(setting.allowed_signals)}."
        )
    if method_key not in setting.allowed_methods:
        return (
            f"No story: {setting.phrase} does not allow method {method_key!r}. "
            f"Available methods are: {', '.join(setting.allowed_methods)}."
        )
    if method_key not in signal.compatible_methods:
        return (
            f"No story: {method.phrase} does not fit signal {signal_key!r}. "
            f"Compatible methods are: {', '.join(signal.compatible_methods)}."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting in sorted(SETTINGS):
        for signal in sorted(SIGNALS):
            for method in sorted(METHODS):
                if valid_combo(setting, signal, method):
                    combos.append((setting, signal, method))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if not valid_combo(params.setting, params.signal, params.method):
        raise StoryError(invalid_reason(params.setting, params.signal, params.method))


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    setting = SETTINGS[params.setting]
    signal = SIGNALS[params.signal]
    method = METHODS[params.method]
    world = World(params=params, setting=setting, signal=signal, method=method)

    hero = world.add(
        Entity(
            name=params.hero,
            kind=params.hero_kind,
            traits=["curious", "small", "bedtime_friendly"],
            location="bed",
            meters={"steps": 0.0, "repetitions_done": 0.0, "focus": 1.0},
            memes={"curiosity": 1.0, "peace": 0.5, "confidence": 0.2},
        )
    )
    helper = world.add(
        Entity(
            name=params.helper,
            kind="parent",
            traits=["kind", "steady"],
            location="bedroom",
            meters={"steady_help": 1.0},
            memes={"patience": 1.0},
        )
    )
    nopsu = world.add(
        Entity(
            name="mature_nopsu",
            kind="artifact",
            traits=["noisy", "repeating", "bedtime"],
            location=setting.key,
            meters={"tension": 1.0, "glow": 0.9, "resolved": 0.0},
            memes={"uneasy": 1.0},
        )
    )
    room = world.add(
        Entity(
            name=setting.key,
            kind="room",
            traits=["safe", "story_ready"],
            location="home",
            meters={"stillness": 1.0},
            memes={"coziness": 1.2},
        )
    )

    # Physical and emotional state used by prose choices later.
    hero.meters["focus"] += 0.5
    nopsu.meters["tension"] = 1.0
    room.meters["stillness"] = 1.0

    world.facts = {
        "setting": setting.key,
        "signal": signal.key,
        "method": method.key,
        "hero": hero.name,
        "helper": helper.name,
        "seed": str(params.seed),
        "seed_word": "mature,nopsu",
        "required_repetitions": str(signal.required_repetitions),
    }
    return world


def _opening(world: World) -> None:
    hero = world.get(world.params.hero)
    helper = world.get(world.params.helper)
    nopsu = world.get("mature_nopsu")
    setting = world.setting
    room = world.get(world.setting.key)

    world.say(
        f"In {setting.phrase}, {hero.name} crawled under {room.name.replace('_', ' ')} quilts and looked at the {nopsu.kind} waiting by the lamp. "
        f"It was a bedtime room with {setting.opening_image}."
    )
    world.say(
        f"The {nopsu.kind} was actually a mature nopsu, and tonight it said a small sentence again and again. "
        f"{helper.name} was nearby but let {hero.name} explore first, because it was storytime curiosity."
    )


def _repetition_turn(world: World) -> None:
    hero = world.get(world.params.hero)
    signal = world.signal
    nopsu = world.get("mature_nopsu")
    room = world.get(world.setting.key)

    room.meters["stillness"] = 0.8
    nopsu.memes["uneasy"] = 1.0
    nopsu.traits.append("inspiring curiosity")

    world.say(f"Then came the sentence: \"{signal.refrain}\".")
    for idx in range(1, signal.required_repetitions + 1):
        hero.meters["repetitions_done"] += 1
        hero.meters["steps"] += 0.2
        hero.memes["curiosity"] += 0.15
        room.meters["stillness"] -= 0.15
        nopsu.meters["glow"] -= 0.08
        world.events.append(f"heard_{signal.key}_{idx}")

        if idx == 1:
            world.say(
                f"{hero.name} heard {signal.refrain} once, then whispered, "
                f"\"maybe it means something important\" and went a little closer."
            )
        elif idx < signal.required_repetitions:
            world.say(
                f"{hero.name} heard it again: {signal.refrain}. "
                f"The count stayed the same, so the curiosity stayed gentle and calm."
            )
        else:
            world.say(
                f"After the final repeat, {hero.name} was sure the pattern was real: {signal.required_repetitions} clear rounds."
            )


def _method_turn(world: World) -> None:
    hero = world.get(world.params.hero)
    helper = world.get(world.params.helper)
    method = world.method
    signal = world.signal
    nopsu = world.get("mature_nopsu")

    if method.key == "ask_parent":
        world.say(method.action_text.format(hero=hero.name, helper=helper.name))
    elif method.key == "draw_circles":
        world.say(method.action_text.format(hero=hero.name))
    else:
        world.say(method.action_text.format(hero=hero.name, helper=helper.name))

    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 0.5
    nopsu.meters["tension"] = max(0.0, nopsu.meters["tension"] - 0.65)
    nopsu.meters["resolved"] = 1.0
    world.events.append(f"method_{method.key}")

    world.say(
        f"Why it worked: {method.why_works} That line is why a sleepy child can be curious without getting into trouble."
    )


def _resolution(world: World) -> None:
    hero = world.get(world.params.hero)
    setting = world.setting
    signal = world.signal
    nopsu = world.get("mature_nopsu")
    room = world.get(world.setting.key)

    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1.1
    hero.memes["curiosity"] = max(0.0, hero.memes["curiosity"] - 0.05)
    nopsu.memes["uneasy"] = max(0.0, nopsu.memes["uneasy"] - 0.95)
    room.meters["stillness"] = 1.2
    nopsu.meters["glow"] = max(0.0, nopsu.meters["glow"])

    world.say(signal.explanation)
    world.say(signal.lesson)
    world.say(
        f"By bedtime, the room changed: {setting.ending_image}. "
        f"The story ended clearly in the physical world because the mature nopsu was no longer tense."
    )


def simulate(world: World) -> World:
    _opening(world)
    world.para()
    _repetition_turn(world)
    world.para()
    _method_turn(world)
    world.para()
    _resolution(world)
    return world


def _prompts(world: World) -> list[str]:
    return [
        f"Tell a bedtime story in {world.setting.phrase} with a clear start, middle, and gentle ending.",
        f"Use the repeated phrase '{world.signal.refrain}' to show curiosity-driven repetition.",
        f"Keep both words mature and nopsu in the story, and explain how the character fixes the bedtime object safely.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    hero = world.params.hero
    signal = world.signal
    method = world.method
    helper = world.params.helper
    return [
        QAItem(
            "What made this a curious moment?",
            (
                f"{hero} kept asking what the repeated phrase meant after noticing the mature nopsu repeat the same rhythm. "
                f"Each repeat raised a bit of curiosity and gave a full clue, so curiosity stayed grounded instead of becoming confused guesswork."
            ),
        ),
        QAItem(
            "How many times did the signal repeat, and why did that matter?",
            (
                f"The signal repeated {world.facts.get('required_repetitions')} times, matching a real pattern in the world. "
                f"That repetition was the signal source itself: only after hearing the same rhythm repeatedly could {hero} decide on the safe next step."
            ),
        ),
        QAItem(
            "What action solved the problem?",
            (
                f"{hero} used this method: {method.phrase}. "
                f"That method worked because it changed a physical part of the mature nopsu, not just the imagined reason for the sound."
            ),
        ),
        QAItem(
            "Who helped, and what changed by the end?",
            (
                f"{helper} helped when the selected method needed an adult hand, otherwise {hero} solved it through careful repetition and tracking. "
                f"By the end, the mature nopsu was resolved and the room became steady and calm for sleep, which is the concrete change in the state."
            ),
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why is this world rejecting an invalid method for a setting or signal?",
            (
                f"Each world state ties signals to compatible methods and settings through tables before story text is generated. "
                f"That means a method only exists when its physical steps match what this setting and the mature nopsu signal can support."
            ),
        ),
        QAItem(
            "What entity carried the repeating behavior in the simulation?",
            (
                f"The repeating behavior was carried by the mature nopsu entity in the room. "
                f"Its meters tracked tension and glow, and repetition of the signal changed those meters step by step."
            ),
        ),
        QAItem(
            "How is repetition represented beyond sentence repetition in prose?",
            (
                f"The simulation stores repetition count as an entity meter called repetitions_done on the child and as required_repetitions from the signal. "
                f"Each observed round also lowers the nopsu's stillness-related tension, which lets the resolution be tied to world state rather than decoration."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = simulate(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = r"""
combo(S,Si,M) :-
    setting(S),
    signal(Si),
    method(M),
    setting_signal(S, Si),
    setting_method(S, M),
    signal_method(Si, M).

ok :- chosen(S,Si,M), combo(S,Si,M).

#show combo/3.
#show ok/0.
"""


def asp_facts() -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for setting_key, setting in sorted(SETTINGS.items()):
        rows.append(fact("setting", setting_key))
        for signal_key in setting.allowed_signals:
            rows.append(fact("setting_signal", setting_key, signal_key))
        for method_key in setting.allowed_methods:
            rows.append(fact("setting_method", setting_key, method_key))

    for signal_key, signal in sorted(SIGNALS.items()):
        rows.append(fact("signal", signal_key))
        for method_key in signal.compatible_methods:
            rows.append(fact("signal_method", signal_key, method_key))

    for method_key in sorted(METHODS):
        rows.append(fact("method", method_key))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    chosen = ""
    if params is not None:
        from storyworlds.asp import fact

        chosen = fact("chosen", params.setting, params.signal, params.method) + "\n"
    return asp_facts() + chosen + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        combos.update(atoms(model, "combo"))
    return combos


def asp_accepts(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    model = one_model(asp_program(params))
    return bool(atoms(model, "ok"))


def verify() -> str:
    python = set(valid_combos())
    asp = asp_valid_combos()
    if python != asp:
        only_python = sorted(python - asp)
        only_asp = sorted(asp - python)
        raise StoryError(f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}")

    for i, combo in enumerate(sorted(python), 1):
        params = StoryParams(
            setting=combo[0],
            signal=combo[1],
            method=combo[2],
            hero=_pick_name("girl", random.Random(2024 + i)),
            hero_kind="girl",
            helper=HELPERS[0],
            seed=i,
        )
        if not asp_accepts(params):
            raise StoryError(f"ASP rejected valid combo {combo!r}")

        sample = generate(params)
        text = sample.story.lower()
        if "nopsu" not in text:
            raise StoryError(f"Generated story for {combo!r} forgot seed word nopsu.")
        if "mature" not in text:
            raise StoryError(f"Generated story for {combo!r} forgot seed word mature.")
        if sample.world is None:
            raise StoryError(f"Generated sample for {combo!r} forgot world trace.")
        if sample.world.facts.get("required_repetitions") is None:
            raise StoryError(f"Generated sample for {combo!r} missed repetition fact.")
        if int(sample.world.facts["required_repetitions"]) != SIGNALS[combo[1]].required_repetitions:
            raise StoryError(f"Generated sample for {combo!r} has mismatched repetition state.")
        if sample.world.facts.get("required_repetitions") != str(SIGNALS[combo[1]].required_repetitions):
            raise StoryError(f"Generated sample for {combo!r} has incorrect repetition count fact.")
        if sample.story.count("\n\n") < 2:
            raise StoryError(f"Generated story for {combo!r} is missing a clear beginning/middle/ending.")
        if len(sample.prompts) != 3:
            raise StoryError(f"Generated sample for {combo!r} has wrong prompt count.")
        if len(sample.story_qa) < 4:
            raise StoryError(f"Generated sample for {combo!r} needs at least 4 story Q&A items.")
        if len(sample.world_qa) < 3:
            raise StoryError(f"Generated sample for {combo!r} needs at least 3 world Q&A items.")
        for qa in sample.story_qa:
            if qa.answer.count(".") < 2:
                raise StoryError(f"Story QA answer too short for {combo!r}: {qa.question}")
        for qa in sample.world_qa:
            if qa.answer.count(".") < 2:
                raise StoryError(f"World QA answer too short for {combo!r}: {qa.question}")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"Template leakage in generated story for {combo!r}.")

    return f"OK: matched ASP and Python for {len(python)} combos; generated stories passed baseline quality checks."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate mature-nopsu bedtime stories with curiosity and repetition.")
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--signal", choices=sorted(SIGNALS))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--hero")
    parser.add_argument("--hero-kind", choices=sorted(HEROES), default="girl")
    parser.add_argument("--helper", choices=HELPERS, default="Mum")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def _matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = valid_combos()
    filtered = [
        combo
        for combo in combos
        if (args.setting is None or combo[0] == args.setting)
        and (args.signal is None or combo[1] == args.signal)
        and (args.method is None or combo[2] == args.method)
    ]
    if not filtered:
        if args.setting or args.signal or args.method:
            raise StoryError("No story: no valid setting/signal/method combination matches the requested filters.")
        return combos
    return filtered


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combo = rng.choice(_matching_combos(args))
    setting_key, signal_key, method_key = combo
    hero_name = args.hero or _pick_name(args.hero_kind, rng)
    helper = args.helper or _pick_helper(rng)
    return StoryParams(
        setting=setting_key,
        signal=signal_key,
        method=method_key,
        hero=hero_name,
        hero_kind=args.hero_kind,
        helper=helper,
        seed=args.seed + index,
    )


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Story prompts ==")
    for i, prompt in enumerate(sample.prompts, 1):
        print(f"{i}. {prompt}")
    print("\n== (2) Story Q&A ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World Q&A ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        _print_qa(sample)


def _emit_asp() -> None:
    for setting, signal, method in sorted(asp_valid_combos()):
        print(f"{setting}\t{signal}\t{method}")


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            _emit_asp()
            return 0

        samples: list[StorySample] = []
        if args.all:
            combos = _matching_combos(args)
            for index, combo in enumerate(combos, 1):
                params = StoryParams(
                    setting=combo[0],
                    signal=combo[1],
                    method=combo[2],
                    hero=_pick_name("girl", random.Random(args.seed + index)),
                    hero_kind="girl",
                    helper=args.helper,
                    seed=args.seed + index,
                )
                samples.append(generate(params))
        else:
            count = max(1, args.n)
            for index in range(count):
                rng = random.Random(args.seed + index)
                samples.append(generate(resolve_params(args, rng, index)))

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for idx, sample in enumerate(samples, 1):
            if args.all:
                header = f"### {sample.params.setting} / {sample.params.signal} / {sample.params.method}"
            elif len(samples) > 1:
                header = f"### variant {idx}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if idx != len(samples):
                print("\n" + "=" * 72 + "\n")
        return 0

    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
