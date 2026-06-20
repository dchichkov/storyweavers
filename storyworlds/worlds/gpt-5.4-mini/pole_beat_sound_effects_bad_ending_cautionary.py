#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pole_beat_sound_effects_bad_ending_cautionary.py
=================================================================================

A standalone tiny story world in a folk-tale mode: a child hears a strange beat
from a pole, ignores a careful warning, follows the sound into trouble, and the
ending proves why the caution mattered.

Domain sketch
-------------
This world keeps the action small and classical:
- a child finds a pole that makes a rhythmic beat,
- the beat draws attention and excitement,
- a cautious helper warns that the pole is unsafe,
- a bad choice leads to a messy, scary ending,
- the tale closes with a clear cautionary image.

The story is built from world state, not from a frozen paragraph with swapped
names. Physical state uses meters; emotional state uses memes.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    sound_place: str
    danger_place: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Pole:
    id: str
    label: str
    phrase: str
    sound: str
    beat: str
    warning: str
    bad_use: str
    danger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    caution: str
    rescue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ending:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    pole = world.get("pole")
    if child.meters["chasing_sound"] < THRESHOLD:
        return out
    sig = ("echo",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pole.memes["ominous"] += 1
    child.memes["thrill"] += 1
    out.append("__echo__")
    return out


def _r_trouble(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    pole = world.get("pole")
    if pole.meters["struck"] < THRESHOLD:
        return out
    sig = ("trouble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    world.get("lane").meters["danger"] += 1
    out.append("__trouble__")
    return out


CAUSAL_RULES = [
    Rule("echo", "social", _r_echo),
    Rule("trouble", "physical", _r_trouble),
]


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


def reasonableness_gate(pole: Pole, setting: Setting) -> bool:
    return "pole" in pole.tags and setting.id in {"village", "forest", "mill"}


def would_warning_help(pole: Pole, helper: Helper) -> bool:
    return "caution" in helper.tags and "warning" in pole.tags


def ending_severity(delay: int) -> int:
    return 2 + delay


def is_bad_ending(end: Ending, delay: int) -> bool:
    return end.power < ending_severity(delay)


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    _strike_pole(sim, sim.get("pole"), narrate=False)
    return {
        "danger": sim.get("lane").meters["danger"],
        "fear": sim.get("child").memes["fear"],
    }


def _strike_pole(world: World, pole_ent: Entity, narrate: bool = True) -> None:
    pole_ent.meters["struck"] += 1
    pole_ent.meters["ringing"] += 1
    world.get("child").meters["chasing_sound"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Once, in {setting.place}, {child.id} walked the lane where the old folk "
        f"gathered. {setting.opening}"
    )


def sound_call(world: World, child: Entity, pole: Pole, setting: Setting) -> None:
    world.say(
        f"Then from {setting.sound_place} came a curious sound: {pole.sound} "
        f"{pole.beat} {pole.beat}. It sounded like a little drum hiding in the wood."
    )
    world.say(
        f'{child.id} leaned close. "{pole.sound}" {child.pronoun("subject")} whispered, '
        f'and {child.pronoun("subject")} wanted to tap the pole once.'
    )


def warn(world: World, helper: Entity, child: Entity, pole: Pole) -> None:
    pred = predict_trouble(world)
    helper.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{helper.id} lifted {helper.pronoun("possessive")} hand. "{child.id}, do not '
        f"beat the pole. {pole.warning} {pole.bad_use}."
        f" If you strike it, {pole.danger}."
        f'"'
    )


def defy(world: World, child: Entity, pole: Pole) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'But {child.id} smiled anyway. "Just one little beat," {child.pronoun("subject")} '
        f'said, and {child.pronoun("subject")} touched the pole.'
    )


def strike(world: World, pole_ent: Entity, pole: Pole) -> None:
    _strike_pole(world, pole_ent)
    world.say(
        f"{pole.sound} {pole.beat}! The pole gave a hollow shout, and the sound ran "
        f"down the lane like running feet."
    )


def alarm(world: World, helper: Entity, child: Entity, setting: Setting) -> None:
    world.say(
        f'{helper.id} gasped. "Stop, {child.id}! That sound means the pole is loose!" '
        f'{setting.danger_place.capitalize()} felt suddenly too close.'
    )


def bad_end(world: World, helper: Entity, child: Entity, pole: Pole, delay: int) -> None:
    child.memes["fear"] += 2
    world.get("lane").meters["danger"] = 2 + delay
    world.say(
        f"The old pole cracked. It toppled into the lane with a hard thump, and dust "
        f"rose in a gray cloud."
    )
    world.say(
        f"{helper.label_word.capitalize()} ran in, but the broken pole had already "
        f"blocked the path. {child.id} had to back away, with tears in "
        f"{child.pronoun('possessive')} eyes."
    )
    world.say(
        f"In the end the lane was shut, the music was gone, and everyone remembered "
        f"the warning too late."
    )


def caution_lesson(world: World, helper: Entity, child: Entity, pole: Pole) -> None:
    helper.memes["love"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"Then {helper.id} knelt beside {child.id} and spoke softly. "
        f'"A beat can be a warning too," {helper.pronoun()} said. '
        f'"If something sounds wrong, leave it alone and call for help."'
    )
    world.say(
        f"{child.id} nodded, remembering how the cheerful sound had turned sour."
    )


SETTINGS = {
    "village": Setting(
        "village", "a small village", "The cottages slept under a pale sky.",
        "the old square", "the narrow lane", "quiet and watchful", {"folk", "lane"},
    ),
    "forest": Setting(
        "forest", "the forest path", "The trees stood tall like listening giants.",
        "the clearing", "the root-strewn path", "deep and hush-soft", {"folk", "woods"},
    ),
    "mill": Setting(
        "mill", "the mill road", "The mill wheel turned slow beside the stream.",
        "the mill yard", "the muddy road", "busy and echoing", {"folk", "road"},
    ),
}

POLES = {
    "pole": Pole(
        "pole", "pole", "an old pole", "tuk", "beat", "the pole should not be beaten",
        "it is not a toy drum", "it can crack and fall", {"pole", "warning"},
    ),
    "flagpole": Pole(
        "flagpole", "flagpole", "a tall flagpole", "tok", "beat", "the flagpole should not be struck",
        "it is not a drumstick", "it can sway and loosen", {"pole", "warning"},
    ),
    "fencepost": Pole(
        "fencepost", "fencepost", "a crooked fencepost", "thok", "beat", "the fencepost should not be pounded",
        "it is not a play stick", "it can split and break", {"pole", "warning"},
    ),
}

HELPERS = {
    "grandmother": Helper("grandmother", "grandmother", "an old grandmother", "caution", "rescue", {"caution", "folk"}),
    "father": Helper("father", "father", "a steady father", "caution", "rescue", {"caution", "folk"}),
    "neighbor": Helper("neighbor", "neighbor", "a kind neighbor", "caution", "rescue", {"caution"}),
}

ENDINGS = {
    "stomp": Ending("stomp", 3, 3, "stamped the pole down and tied it safe", "tried to hold it, but it was already falling", "stamped the pole down and tied it safe", {"ending"}),
    "rope": Ending("rope", 2, 2, "looped a rope around the pole and steadied it", "grabbed the rope too late", "looped a rope around the pole and steadied it", {"ending"}),
    "call": Ending("call", 4, 4, "called for help before the pole could fall", "called too late to stop the crash", "called for help before the pole could fall", {"ending"}),
}

GIRL_NAMES = ["Mara", "Lina", "Elsa", "Nina", "Anya", "Lila"]
BOY_NAMES = ["Bram", "Oren", "Tomas", "Evan", "Jory", "Milo"]
TRAITS = ["curious", "bright", "quick", "playful", "heedful"]


@dataclass
class StoryParams:
    setting: str
    pole: str
    helper: str
    ending: str
    child: str
    child_gender: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, pole in POLES.items():
            if not reasonableness_gate(pole, setting):
                continue
            for hid in HELPERS:
                combos.append((sid, pid, hid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world: a pole, a beat, and a cautionary bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pole", choices=POLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in POLES.items():
        lines.append(asp.fact("pole", pid))
        lines.append(asp.fact("warning", pid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for eid, e in ENDINGS.items():
        lines.append(asp.fact("ending", eid))
        lines.append(asp.fact("sense", eid, e.sense))
        lines.append(asp.fact("power", eid, e.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S, P, H) :- setting(S), pole(P), helper(H), warning(P).
good_end(E) :- ending(E), sense(E, N), sense_min(M), N >= M.
bad_end(E) :- ending(E), sense(E, N), sense_min(M), N < M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_good_endings() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show good_end/1."))
    return sorted(e for (e,) in asp.atoms(model, "good_end"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    else:
        print(f"OK: ASP and Python valid combos match ({len(valid_combos())}).")
    if set(asp_good_endings()) != {e.id for e in ENDINGS.values() if e.sense >= 2}:
        rc = 1
        print("MISMATCH in endings.")
    else:
        print("OK: ASP good endings match.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover - safety check
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_rejection() -> str:
    return "(No story: this world needs an unsafe pole that can really cause trouble in a folk tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pole and args.setting and not reasonableness_gate(POLES[args.pole], SETTINGS[args.setting]):
        raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.pole is None or c[1] == args.pole)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, pole, helper = rng.choice(sorted(combos))
    ending = args.ending or rng.choice(sorted(ENDINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child = args.name or rng.choice(pool)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, pole, helper, ending, child, gender, trait, delay)


def tell(setting: Setting, pole: Pole, helper: Helper, ending: Ending, child_name: str, child_gender: str, trait: str, delay: int) -> World:
    world = World()
    child = world.add(Entity("child", kind="character", type=child_gender, role="child", traits=[trait]))
    guide = world.add(Entity("guide", kind="character", type="woman" if helper.id == "grandmother" else "man", role="helper"))
    lane = world.add(Entity("lane", type="place", label=setting.danger_place))
    pole_ent = world.add(Entity("pole", type="thing", label=pole.label))
    world.facts["child_name"] = child_name
    world.facts["setting"] = setting
    world.facts["pole_cfg"] = pole
    world.facts["helper_cfg"] = helper
    world.facts["ending_cfg"] = ending
    world.facts["delay"] = delay

    intro(world, child, guide, setting)
    world.para()
    sound_call(world, child, pole, setting)
    warn(world, guide, child, pole)
    if child_name:
        child.id = child_name
        world.entities.pop("child")
        world.entities[child_name] = child
    world.para()
    defy(world, child, pole)
    strike(world, pole_ent, pole)
    alarm(world, guide, child, setting)
    world.para()
    bad_end(world, guide, child, pole, delay)
    caution_lesson(world, guide, child, pole)
    world.facts.update(child=child, guide=guide, lane=lane, pole=pole_ent, outcome="bad")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style cautionary story that includes the words "pole" and "beat".',
        f"Tell a child-safe but sad story where {f['child_name']} hears a beat from a pole, ignores a warning, and learns the hard way.",
        f"Write a short folk tale with sound effects, a warning, and a bad ending about a pole that should not be beaten.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    pole = f["pole_cfg"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {f['child_name']} and the cautious guide who tried to keep the lane safe. The child is the one who listened to the beat and made the wrong choice."
        ),
        QAItem(
            question=f"What did {f['child_name']} hear?",
            answer=f"{f['child_name']} heard {pole.sound} {pole.beat} {pole.beat} coming from the pole. The sound was exciting, but it was also a warning that the pole was not safe to strike."
        ),
        QAItem(
            question=f"What did the helper say?",
            answer=f"The helper said not to beat the pole because it was loose and could crack or fall. The warning mattered because the sound was not a game; it was a sign of danger."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly: the pole cracked, fell, and blocked the lane. The child had to back away, and the folk tale closed by showing that the warning should have been followed."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pole?",
            answer="A pole is a long, narrow piece of wood or metal. It can hold things up, but if it is old or loose it can be dangerous."
        ),
        QAItem(
            question="What does a beat mean in a sound effect?",
            answer="A beat is a regular hit or thump that repeats again and again. In stories it can sound like tapping, drumming, or marching."
        ),
        QAItem(
            question="Why should you listen to a caution?",
            answer="A caution is a warning meant to keep someone safe. Listening early can stop a small problem before it becomes a bigger one."
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("village", "pole", "grandmother", "call", "Mara", "girl", "curious", 1),
    StoryParams("forest", "flagpole", "father", "rope", "Bram", "boy", "bright", 0),
    StoryParams("mill", "fencepost", "neighbor", "stomp", "Lina", "girl", "playful", 2),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], POLES[params.pole], HELPERS[params.helper], ENDINGS[params.ending],
        params.child, params.child_gender, params.trait, params.delay
    )
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
        print(asp_program("", "#show compatible/3.\n#show good_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, pole, helper) combos:\n")
        for s, p, h in combos:
            print(f"  {s:8} {p:10} {h}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.pole} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
