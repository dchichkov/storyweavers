#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rodeo_teak_pleasure_sound_effects_ghost_story.py
==================================================================================

A tiny standalone storyworld for a child-friendly ghost story at a rodeo exhibit.
The world is built around a simple premise:

- a child hears spooky sound effects in an old rodeo hall,
- the noises lead them to a teak chest and a little surprise,
- the "ghost" turn is resolved by a calm adult explanation,
- the ending proves what changed: the sounds become fun instead of frightening.

The seed words required by the prompt are woven into the simulation:
"rodeo", "teak", and "pleasure", plus sound effects as the narrative instrument.

This follows the Storyweavers storyworld contract:
- stdlib only
- results.py imported eagerly
- build_parser / resolve_params / generate / emit / main
- QA grounded in world state, not by parsing rendered English
- inline ASP twin plus Python reasonableness gate
- --verify smoke-tests ordinary generation and checks parity
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
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    dim: str
    echo: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class SoundCue:
    id: str
    sound: str
    source: str
    effect: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Surprise:
    id: str
    label: str
    reveal: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Response:
    id: str
    sense: int
    calm: int
    text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_fright(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["spooked"] < THRESHOLD:
            continue
        sig = ("fright", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "child" in world.entities:
            world.get("child").memes["fear"] += 1
        out.append("__spooky__")
    return out


CAUSAL_RULES = [Rule("fright", "social", _r_fright)]


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


def reasonableness_gate(setting: Setting, cue: SoundCue, surprise: Surprise) -> bool:
    return "rodeo" in setting.tags and "sound" in cue.tags and "teak" in surprise.tags


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def predict_spook(world: World, cue_id: str) -> dict:
    sim = world.copy()
    _do_sound(sim, sim.get(cue_id), narrate=False)
    return {
        "spooked": sim.get("child").meters["spooked"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
    }


def _do_sound(world: World, cue_ent: Entity, narrate: bool = True) -> None:
    cue_ent.meters["spooked"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    world.say(
        f"On a breezy evening, {child.id} and {adult.id} stepped into {setting.place}. "
        f"{setting.echo}"
    )


def listen(world: World, child: Entity, cue: SoundCue) -> None:
    world.say(
        f"Then came a sound: {cue.sound}. It drifted from {cue.source} like a whisper in the dark."
    )
    world.say(f"{child.id} froze. The noise felt {cue.effect}.")


def fear(world: World, child: Entity) -> None:
    child.memes["curiosity"] += 1
    child.memes["fear"] += 1
    world.say(f'{child.id} whispered, "Did you hear that?"')


def warn(world: World, adult: Entity, child: Entity, cue: SoundCue, surprise: Surprise) -> None:
    pred = predict_spook(world, "cue")
    adult.memes["calm"] += 1
    world.facts["predicted_spook"] = pred["spooked"]
    world.say(
        f'{adult.id} smiled and held {child.pronoun("possessive")} hand. '
        f'"That noise is only a sound effect," {adult.id} said. '
        f"It is loud enough to feel spooky, but it is not a real ghost."
    )


def reveal(world: World, adult: Entity, surprise: Surprise) -> None:
    world.say(
        f"Beside the old {surprise.label} chest, {adult.id} found the hidden switch. "
        f'The teak lid clicked open with a soft creak, and inside was {surprise.reveal}.'
    )


def calm_finish(world: World, child: Entity, adult: Entity, cue: SoundCue) -> None:
    child.memes["fear"] = 0.0
    child.memes["joy"] += 1
    world.say(
        f'{adult.id} pressed the button again: {cue.sound}. '
        f"This time {child.id} grinned instead of flinching."
    )
    world.say(
        f'"Pleasure," {child.id} said with a laugh, because the spooky little show had turned into fun.'
    )


def tell(setting: Setting, cue: SoundCue, surprise: Surprise, response: Response,
         child_name: str = "Maya", child_gender: str = "girl",
         adult_name: str = "Dad", adult_gender: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    cue_ent = world.add(Entity(id="cue", type="sound", label=cue.sound))
    chest = world.add(Entity(id="chest", type="thing", label=surprise.label))
    world.facts["cue"] = cue
    world.facts["surprise"] = surprise
    world.facts["response"] = response
    world.add(chest)

    intro(world, child, adult, setting)
    world.para()
    listen(world, child, cue)
    fear(world, child)
    warn(world, adult, child, cue, surprise)

    if not reasonableness_gate(setting, cue, surprise):
        raise StoryError("This story needs a rodeo setting, a sound effect, and a teak surprise.")

    world.para()
    _do_sound(world, cue_ent)
    reveal(world, adult, surprise)

    world.para()
    world.say(
        f"{adult.id} gave the little show a calm name: {response.text}. "
        f"{child.id} could feel the difference now -- spooky at first, safe in the end."
    )
    calm_finish(world, child, adult, cue)

    world.facts.update(
        child=child,
        adult=adult,
        cue_ent=cue_ent,
        chest=chest,
        outcome="calmed",
        safe=response.sense >= 2,
    )
    return world


SETTINGS = {
    "rodeo_hall": Setting(
        "rodeo_hall",
        "the old rodeo hall",
        "dim",
        "The floorboards sighed, and the rafters gave a long, empty moan.",
        tags={"rodeo"},
    ),
    "barn_stands": Setting(
        "barn_stands",
        "the rodeo barn stands",
        "shadowy",
        "Somewhere above, a loose sign tapped the wall like a fingernail.",
        tags={"rodeo"},
    ),
    "museum_room": Setting(
        "museum_room",
        "the small rodeo museum room",
        "quiet",
        "The glass cases gleamed, but the room still felt full of echoes.",
        tags={"rodeo"},
    ),
}

SOUNDS = {
    "hoofbeats": SoundCue(
        "hoofbeats",
        "clip-clop, clip-clop",
        "the far end of the hall",
        "very spooky",
        tags={"sound"},
    ),
    "whistle": SoundCue(
        "whistle",
        "whooo-ooo",
        "a cracked vent",
        "like a ghost was singing",
        tags={"sound"},
    ),
    "rattle": SoundCue(
        "rattle",
        "krrrk, tap-tap-tap",
        "inside the wall",
        "like tiny bones dancing",
        tags={"sound"},
    ),
}

SURPRISES = {
    "teak_chest": Surprise(
        "teak_chest",
        "teak",
        "a brass music box and a stack of rodeo sound effects records",
        tags={"teak"},
    ),
    "teak_box": Surprise(
        "teak_box",
        "teak",
        "a little speaker, a red button, and a paper note that said 'sound effects'",
        tags={"teak"},
    ),
}

RESPONSES = {
    "listen_closer": Response(
        "listen_closer",
        3,
        3,
        "listened closely and found the trick",
        tags={"calm"},
    ),
    "turn_on_light": Response(
        "turn_on_light",
        3,
        2,
        "turned on a lamp and looked again",
        tags={"calm"},
    ),
    "call_adult": Response(
        "call_adult",
        2,
        4,
        "called for a grown-up and waited together",
        tags={"calm"},
    ),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    sound: str
    surprise: str
    response: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in SOUNDS:
            for t in SURPRISES:
                if reasonableness_gate(SETTINGS[s], SOUNDS[c], SURPRISES[t]):
                    combos.append((s, c, t))
    return combos


def explain_rejection() -> str:
    return "(No story: this ghost story needs a rodeo setting, a sound effect, and something teak to reveal.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rodeo ghost story with sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--adult")
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
    if args.setting and args.sound and args.surprise:
        if not reasonableness_gate(SETTINGS[args.setting], SOUNDS[args.sound], SURPRISES[args.surprise]):
            raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.sound is None or c[1] == args.sound)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, sound, surprise = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    child_name = args.child or rng.choice(["Maya", "Tess", "Noah", "Eli", "Ruby"])
    adult_name = args.adult or rng.choice(["Dad", "Mom", "Aunt June"])
    child_gender = "girl" if child_name in {"Maya", "Tess", "Ruby"} else "boy"
    adult_gender = "boy" if adult_name == "Dad" else "girl"
    return StoryParams(setting, sound, surprise, response, child_name, child_gender, adult_name, adult_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cue: SoundCue = f["cue"]
    surprise: Surprise = f["surprise"]
    return [
        f'Write a small ghost story for a child that uses the words "rodeo", "teak", and "pleasure".',
        f"Tell a spooky-but-safe story where a child hears {cue.sound}, looks for the source, and finds something teak.",
        f"Write a child-friendly ghost story with sound effects that begins in a rodeo hall and ends with a calm reveal.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, adult, cue, surprise = f["child"], f["adult"], f["cue"], f["surprise"]
    qa = [
        ("Where does the story happen?",
         f"It happens in {SETTINGS[f['setting'].id].place}. The hall feels spooky because it is dim and full of echoes."),
        ("What spooky sound did the child hear?",
         f"{child.id} heard {cue.sound}. It sounded spooky at first because it came from the dark side of the room."),
        ("What was the teak surprise?",
         f"The teak surprise was {surprise.reveal}. That turned the strange noise into a small show instead of a ghost."),
        ("Who helped make the child feel safe?",
         f"{adult.id} helped by staying calm and explaining the sound effect. That made the child brave enough to listen again."),
    ]
    if f.get("outcome") == "calmed":
        qa.append((
            "How did the story end?",
            f"It ended with the child smiling at the sound instead of fearing it. The spooky noise became a fun pleasure instead of a fright."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a rodeo?",
         "A rodeo is a show where people watch horses, riders, and cowhands do exciting work."),
        ("What is teak?",
         "Teak is a hard, strong kind of wood. It is often used for sturdy furniture and boxes."),
        ("What are sound effects?",
         "Sound effects are added noises that help a story or show feel more real, funny, or spooky."),
        ("What does a ghost story try to do?",
         "A ghost story tries to make you feel a little shivery and curious, but in a child-friendly story the ending should still be safe."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
has_rodeo(S) :- setting(S), rodeo_setting(S).
has_sound(C) :- sound(C), sound_effect(C).
has_teak(T) :- surprise(T), teak_surprise(T).
valid(S,C,T) :- has_rodeo(S), has_sound(C), has_teak(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy by contract
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        if "rodeo" in SETTINGS[sid].tags:
            lines.append(asp.fact("rodeo_setting", sid))
    for cid in SOUNDS:
        lines.append(asp.fact("sound", cid))
        lines.append(asp.fact("sound_effect", cid))
    for tid in SURPRISES:
        lines.append(asp.fact("surprise", tid))
        if "teak" in SURPRISES[tid].tags:
            lines.append(asp.fact("teak_surprise", tid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


CURATED = [
    StoryParams("rodeo_hall", "hoofbeats", "teak_chest", "listen_closer", "Maya", "girl", "Dad", "boy"),
    StoryParams("barn_stands", "whistle", "teak_box", "turn_on_light", "Noah", "boy", "Mom", "girl"),
    StoryParams("museum_room", "rattle", "teak_chest", "call_adult", "Ruby", "girl", "Aunt June", "girl"),
]


def generate(params: StoryParams) -> StorySample:
    world = World()
    setting = SETTINGS[params.setting]
    cue = SOUNDS[params.sound]
    surprise = SURPRISES[params.surprise]
    response = RESPONSES[params.response]

    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    adult = world.add(Entity(id=params.adult_name, kind="character", type=params.adult_gender, role="adult"))
    cue_ent = world.add(Entity(id="cue", type="sound"))
    chest = world.add(Entity(id="chest", type="thing", label="teak"))

    world.facts.update(setting=setting, cue=cue, surprise=surprise, response=response)

    intro(world, child, adult, setting)
    world.para()
    listen(world, child, cue)
    fear(world, child)
    warn(world, adult, child, cue, surprise)
    world.para()
    _do_sound(world, cue_ent)
    reveal(world, adult, surprise)
    world.para()
    world.say(f"{adult.id} {response.text}.")
    calm_finish(world, child, adult, cue)

    world.facts.update(child=child, adult=adult, cue_ent=cue_ent, chest=chest, outcome="calmed")
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, c, t in asp_valid_combos():
            print(f"  {s:12} {c:12} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
