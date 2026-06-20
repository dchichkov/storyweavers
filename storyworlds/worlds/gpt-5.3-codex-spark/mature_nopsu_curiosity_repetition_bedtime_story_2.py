#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.3-codex-spark/mature_nopsu_curiosity_repetition_bedtime_story_2.py
===============================================================================

Seed source tale:
A little child in a sleepy room keeps noticing a mature nopsu repeating the same
soft signal three times in a row. Guided by curiosity and repeated listening, they
learn that bedtime peace depends on checking the same step in a calm loop, then
applying the right fix together with a helper when needed.

This script simulates that tale in a compact StoryWorld: entities carry physical
meters and emotional memes, repeated observations drive state changes, and the
ending image is a concrete world change from unresolved tension to calm.
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
    title: str
    bedtime_image: str
    opening_image: str
    ending_image: str
    allowed_signals: tuple[str, ...]
    allowed_methods: tuple[str, ...]


@dataclass(frozen=True)
class Signal:
    key: str
    phrase: str
    repeat: str
    repetitions: int
    cause: str
    explanation: str
    compatible_methods: tuple[str, ...]


@dataclass(frozen=True)
class Method:
    key: str
    phrase: str
    needs_helper: bool
    action_text: str
    why_it_works: str


@dataclass
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
    key: str
    kind: str
    traits: list[str] = field(default_factory=list)
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "mother", "aunt", "grandmother", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in {"boy", "father", "uncle", "grandfather", "grandpa", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    params: StoryParams
    setting: Setting
    signal: Signal
    method: Method
    entities: dict[str, Entity] = field(default_factory=dict)
    event_log: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.key] = ent
        return ent

    def get(self, key: str) -> Entity:
        return self.entities[key]

    def say(self, line: str) -> None:
        if self.paragraphs and line:
            self.paragraphs[-1].append(line)

    def break_paragraph(self) -> None:
        if self.paragraphs and self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(parts) for parts in self.paragraphs if parts)

    def trace(self) -> str:
        rows = ["--- world model state ---", f"  setting={self.setting.key}", f"  signal={self.signal.key}", f"  method={self.method.key}"]
        rows.append(f"  events={self.event_log}")
        for ent in self.entities.values():
            rows.append(
                f"  {ent.key:<14} kind={ent.kind:<11} location={ent.location or 'n/a':<14} "
                f"meters={dict(ent.meters)} memes={dict(ent.memes)}"
            )
        return "\n".join(rows)


SETTINGS = {
    "moonlit_room": Setting(
        key="moonlit_room",
        title="the moonlit bedroom",
        bedtime_image="warm curtain folds and a little lamp with a sleepy glow",
        opening_image="a narrow moonbeam across the rug and a soft blanket mound at the bed",
        ending_image="the room dimmed to a steady silver hush and the mature nopsu rested at stillness",
        allowed_signals=("three_taps", "soft_hum"),
        allowed_methods=("count_signals", "ask_helper", "draw_breath"),
    ),
    "window_lounge": Setting(
        key="window_lounge",
        title="the window-side lounge",
        bedtime_image="a small lamp, a window box, and a stacked storybook chair",
        opening_image="the windows showing a still street of distant porch lights",
        ending_image="the window breathed still air while the mature nopsu stopped its repeating call",
        allowed_signals=("three_taps", "paper_wave"),
        allowed_methods=("count_signals", "ask_helper"),
    ),
    "quiet_nook": Setting(
        key="quiet_nook",
        title="a quiet reading nook",
        bedtime_image="a tiny rocking chair, two cushions, and a sleepy blanket fort",
        opening_image="the wall clock glowed softly while the nopsu sat near the lamp stand",
        ending_image="the blankets stayed smooth and the mature nopsu held a soft, unblinking glow",
        allowed_signals=("soft_hum", "paper_wave"),
        allowed_methods=("draw_breath", "ask_helper", "count_signals"),
    ),
}

SIGNALS = {
    "three_taps": Signal(
        key="three_taps",
        phrase="the mature nopsu",
        repeat="tap... tap... tap...",
        repetitions=3,
        cause="a lifted spring pin made the nopsu reply the same rhythm each minute",
        explanation=(
            "Each full set of three taps was a physical signal from the same spring, not a random noise."
        ),
        compatible_methods=("count_signals", "ask_helper", "draw_breath"),
    ),
    "soft_hum": Signal(
        key="soft_hum",
        phrase="the mature nopsu",
        repeat="hummmm, hummmm, hummmm...",
        repetitions=4,
        cause="a loosened breath valve kept the airflow from settling after twilight",
        explanation=(
            "When a valve breath stays uneven, the mature nopsu hum loops with a repeating pattern."
        ),
        compatible_methods=("count_signals", "ask_helper"),
    ),
    "paper_wave": Signal(
        key="paper_wave",
        phrase="the mature nopsu",
        repeat="frrip, frrip, frrip",
        repetitions=2,
        cause="a folded paper spacer had shifted and made the cover flap bounce repeatedly",
        explanation=(
            "The repeated flap sound comes from a mechanical spacer position, so the pattern can be fixed by checking a touchpoint."
        ),
        compatible_methods=("ask_helper", "draw_breath"),
    ),
}

METHODS = {
    "count_signals": Method(
        key="count_signals",
        phrase="counted the repeated signal and matched each round",
        needs_helper=False,
        action_text=(
            "{hero} sat still, counted each {repeat} pattern, and marked the rounds with tiny stars. "
            "The count gave a reliable reason to act next."
        ),
        why_it_works="Pattern matching turns repetition into a testable clue instead of guesswork.",
    ),
    "ask_helper": Method(
        key="ask_helper",
        phrase="called for a helper and adjusted the nopsu together",
        needs_helper=True,
        action_text=(
            "{hero} called {helper} and together they held the mature nopsu steady, then reset the small lever."
        ),
        why_it_works="A second adult hand makes the bedtime fix safer while keeping the child focused on repetition cues.",
    ),
    "draw_breath": Method(
        key="draw_breath",
        phrase="drew a breathing chart beside the signal repeats",
        needs_helper=False,
        action_text=(
            "{hero} drew the signal in a gentle breathing chart, noticed the shared rhythm, and turned the flow tab a little."
        ),
        why_it_works="The visible rhythm diagram exposed when the repeating sound should stop changing, helping the child align actions with the physical timing.",
    ),
}

NAMES = {
    "girl": ("Mia", "Nora", "Suri", "Lena"),
    "boy": ("Leo", "Milo", "Ari", "Noah"),
}

HELPERS = ("Maya", "Dad", "Grandma", "Uncle Ren", "Nana")



def _pick_name(kind: str, rng: random.Random) -> str:
    return rng.choice(NAMES[kind])


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
            f"No story: {setting.title} does not pair with signal {signal_key!r}. "
            f"Allowed signals: {', '.join(setting.allowed_signals)}."
        )
    if method_key not in setting.allowed_methods:
        return (
            f"No story: {setting.title} does not allow method {method_key!r}. "
            f"Allowed methods: {', '.join(setting.allowed_methods)}."
        )
    if method_key not in signal.compatible_methods:
        return (
            f"No story: method {method_key!r} does not match signal {signal_key!r}. "
            f"Compatible methods: {', '.join(signal.compatible_methods)}."
        )
    return "No story: incompatible setting/signal/method combination."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting in sorted(SETTINGS):
        for signal in sorted(SIGNALS):
            for method in sorted(METHODS):
                if valid_combo(setting, signal, method):
                    combos.append((setting, signal, method))
    return combos


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    signal = SIGNALS[params.signal]
    method = METHODS[params.method]
    world = World(params=params, setting=setting, signal=signal, method=method)

    child = world.add(
        Entity(
            key=params.hero,
            kind=params.hero_kind,
            traits=["curious", "sleepy", "careful"],
            location="bed",
            meters={"focus": 0.7, "repetitions_seen": 0.0, "calm": 0.6},
            memes={"curiosity": 0.7, "peace": 0.3},
        )
    )
    helper = world.add(
        Entity(
            key=params.helper,
            kind="parent",
            traits=["warm", "steady"],
            location="chair",
            meters={"help_readiness": 1.0},
            memes={"patience": 0.8},
        )
    )
    nopsu = world.add(
        Entity(
            key="mature_nopsu",
            kind="artifact",
            traits=["repeating", "noisy", "bedtime"],
            location=setting.title,
            meters={"tension": 1.0, "stability": 0.2, "resolved": 0.0},
            memes={"unease": 1.0, "attention": 0.8},
        )
    )
    room = world.add(
        Entity(
            key=setting.key,
            kind="room",
            traits=["dim", "safe"],
            location="home",
            meters={"stillness": 0.4, "liveliness": 1.0},
            memes={"coziness": 0.9},
        )
    )

    child.memes["maturity_notice"] = 0.6
    room.meters["stillness"] = 0.7
    nopsu.memes["unease"] = 1.0
    world.facts = {
        "setting": setting.key,
        "signal": signal.key,
        "method": method.key,
        "resolved": "0",
        "hero": child.key,
        "helper": helper.key,
        "required_repetitions": str(signal.repetitions),
        "seed": str(params.seed),
    }
    return world


def _opening(world: World) -> None:
    hero = world.get(world.params.hero)
    setting = world.setting
    nopsu = world.get("mature_nopsu")
    helper = world.get(world.params.helper)

    world.say(
        f"In {setting.title}, {hero.key} tucked into the blanket with a sleepy smile. "
        f"The room had a gentle image: {setting.opening_image}."
    )
    world.say(
        f"A mature nopsu sat near the lamp and sounded a little pattern at night. "
        f"{helper.key} was in the corner chair, and {hero.pronoun('possessive')} curiosity woke up slowly."
    )


def _repetition_turn(world: World) -> None:
    hero = world.get(world.params.hero)
    helper = world.get(world.params.helper)
    nopsu = world.get("mature_nopsu")
    room = world.get(world.setting.key)
    signal = world.signal

    room.meters["stillness"] = max(0.3, room.meters["stillness"] - 0.1)
    room.meters["liveliness"] = min(1.0, room.meters["liveliness"] + 0.1)

    for i in range(1, signal.repetitions + 1):
        world.event_log.append(f"repeat_{signal.key}_{i}")
        hero.meters["repetitions_seen"] += 1
        hero.memes["curiosity"] += 0.15
        nopsu.meters["tension"] += 0.05
        nopsu.meters["stability"] = max(0.0, nopsu.meters["stability"] - 0.05)
        room.meters["stillness"] = max(0.2, room.meters["stillness"] - 0.05)

        if i == 1:
            world.say(
                f'The first repeat was: "{signal.repeat}". '
                f"{hero.key} leaned closer and asked, \"What is this doing?\""
            )
        elif i < signal.repetitions:
            world.say(
                f'It came again: "{signal.repeat}". '
                f"The exact same rhythm made the meaning clearer, and {hero.key} did not jump, they tracked it."
            )
        else:
            world.say(
                f"After the final repeat, {hero.key} was certain the pattern was consistent: {signal.repetitions} rounds exactly."
            )

    helper.memes["watchfulness"] = 0.7
    nopsu.memes["unease"] = min(1.0, nopsu.memes["unease"] + 0.1)


def _method_turn(world: World) -> None:
    hero = world.get(world.params.hero)
    helper = world.get(world.params.helper)
    method = world.method
    signal = world.signal
    nopsu = world.get("mature_nopsu")

    world.break_paragraph()

    if method.key == "count_signals":
        world.say(method.action_text.format(hero=hero.key, repeat=signal.repeat))
    elif method.key == "ask_helper":
        world.say(method.action_text.format(hero=hero.key, helper=helper.key))
    else:
        world.say(method.action_text.format(hero=hero.key))

    world.event_log.append(f"method_{method.key}")
    nopsu.meters["resolved"] = 1.0
    nopsu.meters["stability"] = 0.85
    nopsu.meters["tension"] = max(0.0, nopsu.meters["tension"] - 0.75)
    nopsu.memes["unease"] = 0.1
    hero.memes["confidence"] = hero.memes.get("confidence", 0.2) + 0.5
    world.facts["resolved"] = "1"
    world.say(f"Why it worked: {method.why_it_works}")


def _resolution(world: World) -> None:
    hero = world.get(world.params.hero)
    setting = world.setting
    nopsu = world.get("mature_nopsu")
    room = world.get(world.setting.key)

    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1.2
    hero.memes["curiosity"] = max(0.0, hero.memes["curiosity"] - 0.1)
    hero.meters["calm"] = min(1.0, hero.meters["calm"] + 0.35)
    room.meters["stillness"] = min(1.0, room.meters["stillness"] + 0.45)
    room.meters["liveliness"] = max(0.2, room.meters["liveliness"] - 0.2)

    world.say(
        signal := world.signal.explanation + " "
        f"The mature nopsu’s meter shifted from tension to stability: "
        f"resolved={nopsu.meters['resolved']}, stability={nopsu.meters['stability']}."
    )
    world.say(
        f"In the final image of {setting.ending_image}, the change is visible in the world state: "
        f"the room’s stillness rose and the mature nopsu finally relaxed instead of repeating stress."
    )


def simulate(world: World) -> World:
    _opening(world)
    world.break_paragraph()
    _repetition_turn(world)
    _method_turn(world)
    world.break_paragraph()
    _resolution(world)
    return world


def _prompts(world: World) -> list[str]:
    return [
        f"Write a Bedtime Story set in {world.setting.title} where repetition guides a curious child." ,
        f"Show the repeated sound '{world.signal.repeat}' and let curiosity lead to a careful method choice.",
        "Include the words mature and nopsu naturally while keeping the ending physical and concrete.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    params = world.params
    signal = world.signal
    method = world.method
    return [
        QAItem(
            "What started the child’s investigation?",
            (
                f"The story turns when {params.hero} noticed the mature nopsu giving the repeat '{signal.repeat}' in the room. "
                "That repeated signal was the concrete cue, so the child’s curiosity became action instead of worry."
            ),
        ),
        QAItem(
            "How was repetition used in the turn?",
            (
                f"The world observed the signal exactly {signal.repetitions} times, recorded as separate repetition events. "
                "Because each round matched, the child recognized a stable pattern and could choose the right next step."
            ),
        ),
        QAItem(
            "What method was chosen, and what changed?",
            (
                f"{params.hero} used the method '{method.phrase}'. "
                "That method reduced the mature nopsu’s tension and increased stability, moving the object from unresolved tension to settled rest."
            ),
        ),
        QAItem(
            "Who helped and why is the ending meaningful?",
            (
                f"{params.helper} helped if needed by standing with the child, but the procedure stayed keyed to what the observed pattern showed. "
                "By the end, the room changed physically: stillness and the mature nopsu’s calm state rose, which is visible in the closing image."
            ),
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    setting = world.setting
    signal = world.signal
    method = world.method
    return [
        QAItem(
            "Why is one method not valid for every signal?",
            (
                f"The simulator keeps a compatibility map where {signal.key} lists methods that can physically fit its cause. "
                "That prevents methods from being chosen from story convenience alone."
            ),
        ),
        QAItem(
            "How does this world represent repetition mechanically?",
            (
                f"Repetition is tracked as three values: event-log entries for each round, a hero meter, and a per-object signal count requirement. "
                f"In this case the required rounds were {world.facts['required_repetitions']}, which is stored on the world facts too."
            ),
        ),
        QAItem(
            "How does the world guarantee the ending is proven in the scene?",
            (
                f"The room and mature nopsu entities have meters for stillness, stability, and tension. "
                f"The final answer uses those meters: stillness rises while nopsu tension drops, so the resolution is checkable from the trace."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.setting, params.signal, params.method):
        raise StoryError(invalid_reason(params.setting, params.signal, params.method))
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
combo(S, Sig, M) :-
    setting(S), signal(Sig), method(M),
    setting_signal(S, Sig),
    setting_method(S, M),
    signal_method(Sig, M).

ok :- chosen(S, Sig, M), combo(S, Sig, M).

#show combo/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
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

    chosen = ""
    if params is not None:
        chosen = fact("chosen", params.setting, params.signal, params.method) + "\n"

    return "\n".join(rows) + "\n" + chosen


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        combos.update(atoms(model, "combo"))
    return combos


def asp_accepts(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params)), "ok"))


def verify() -> str:
    python = set(valid_combos())
    asp = asp_valid_combos()
    if python != asp:
        only_python = sorted(python - asp)
        only_asp = sorted(asp - python)
        raise StoryError(f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}")

    for index, combo in enumerate(sorted(python), 1):
        combo_seed_rng = random.Random(2000 + index)
        hero = _pick_name("girl", combo_seed_rng)
        helper = _pick_helper(combo_seed_rng)
        params = StoryParams(
            setting=combo[0],
            signal=combo[1],
            method=combo[2],
            hero=hero,
            hero_kind="girl",
            helper=helper,
            seed=777 + index,
        )

        if not asp_accepts(params):
            raise StoryError(f"ASP rejected Python-valid combo {combo!r}")

        sample = generate(params)
        text = sample.story.lower()
        if "mature" not in text or "nopsu" not in text:
            raise StoryError(f"Generated story for {combo!r} dropped required words.")
        if sample.world is None or sample.world.facts.get("required_repetitions") is None:
            raise StoryError(f"Generated sample for {combo!r} lost world trace facts.")
        if sample.world.facts.get("required_repetitions") != str(SIGNALS[combo[1]].repetitions):
            raise StoryError(f"Generated sample for {combo!r} has wrong repetition fact.")
        if sample.world.facts.get("resolved") != "1":
            raise StoryError(f"Generated sample for {combo!r} did not mark resolved state.")
        if sample.story.count("\n\n") < 2:
            raise StoryError(f"Generated sample for {combo!r} missed beginning-turn-ending shape.")
        if len(sample.prompts) != 3:
            raise StoryError(f"Generated sample for {combo!r} wrong prompt count.")
        if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
            raise StoryError(f"Generated sample for {combo!r} has too few QA items.")
        for qa in sample.story_qa:
            if "." not in qa.answer.strip():
                raise StoryError(f"Story QA answer too short for {combo!r}.")
        for qa in sample.world_qa:
            if "." not in qa.answer.strip():
                raise StoryError(f"World QA answer too short for {combo!r}.")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"Template leakage in story for {combo!r}.")
        if not any("method_" in evt for evt in sample.world.event_log):
            raise StoryError(f"Generated story for {combo!r} did not log method turn.")

    return f"OK: ASP and Python are aligned on {len(python)} combos and stories pass quality checks."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate mature-nopsu curiosity and repetition bedtime stories.")
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--signal", choices=sorted(SIGNALS))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--hero", default=None)
    parser.add_argument("--hero-kind", choices=sorted(NAMES), default="girl")
    parser.add_argument("--helper", choices=HELPERS, default=None)
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
            raise StoryError("No story: no valid combination matches requested filters.")
        return combos
    return filtered


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    setting, signal, method = rng.choice(_matching_combos(args))
    hero = args.hero or _pick_name(args.hero_kind, rng)
    helper = args.helper or _pick_helper(rng)
    return StoryParams(
        setting=setting,
        signal=signal,
        method=method,
        hero=hero,
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


def emit(sample: StorySample, args: argparse.Namespace, label: str | None = None) -> None:
    if label:
        print(label)
    print(sample.story)
    if args.trace and sample.world is not None:
        print(sample.world.trace())
    if args.qa:
        _print_qa(sample)


def _emit_asp() -> None:
    for setting, signal, method in sorted(asp_valid_combos()):
        print(f"{setting}\t{signal}\t{method}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

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
                    helper=args.helper or _pick_helper(random.Random(args.seed + index + 99)),
                    seed=args.seed + index,
                )
                samples.append(generate(params))
        else:
            count = max(1, args.n)
            for index in range(count):
                rng = random.Random(args.seed + index)
                params = resolve_params(args, rng, index)
                samples.append(generate(params))

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for idx, sample in enumerate(samples, 1):
            label = None
            if args.all:
                label = f"### {sample.params.setting} / {sample.params.signal} / {sample.params.method}"
            elif len(samples) > 1:
                label = f"### variant {idx}"
            emit(sample, args, label=label)
            if idx != len(samples):
                print("\n" + "=" * 72 + "\n")

        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
