#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/three_karaoke_loop_suspense_dialogue_curiosity_rhyming.py
=========================================================================================

A standalone storyworld for a tiny rhyming suspense tale about three children,
a karaoke machine, and a looped song that won't stop until curiosity reveals the
hidden button and the right helper action fixes it.

The world is built from typed entities with physical meters and emotional memes,
a small causal engine, a prediction gate, three QA sets, and an ASP twin for
reasonableness and outcome parity.

The seed words are honored in-world: three, karaoke, loop.
Style goal: rhyming story, child-facing, concrete, with dialogue and gentle suspense.
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
SUSPENSE_MIN = 1.0


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
    broken: bool = False
    looping: bool = False
    silenced: bool = False

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
class Setting:
    id: str
    place: str
    rhyme_tail: str
    atmosphere: str
    loop_echo: str
    stage: str

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
class Child:
    id: str
    gender: str
    trait: str
    age: int = 0
    brave: bool = False

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
class Machine:
    id: str
    label: str
    room: str
    loop_button: str
    stop_button: str
    mic_color: str
    song_name: str
    volume_word: str
    suspense_word: str
    can_loop: bool = True

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
class Trigger:
    id: str
    label: str
    action: str
    effect: str
    sense: int
    power: int
    success: str
    fail: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]


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


def _r_loop(world: World) -> list[str]:
    out: list[str] = []
    mach = world.get("machine")
    if mach.looping and mach.meters["sound"] >= THRESHOLD and ("loop", mach.id) not in world.fired:
        world.fired.add(("loop", mach.id))
        for c in world.characters():
            c.memes["suspense"] += 1
        out.append("__loop__")
    return out


def _r_rhyme(world: World) -> list[str]:
    out: list[str] = []
    if world.get("machine").meters["sound"] >= THRESHOLD and ("rhyme", "sound") not in world.fired:
        world.fired.add(("rhyme", "sound"))
        for c in world.characters():
            c.memes["joy"] += 0.5
        out.append("__rhyme__")
    return out


CAUSAL_RULES = [Rule("loop", "audio", _r_loop), Rule("rhyme", "audio", _r_rhyme)]


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


def predict_loop(world: World) -> dict:
    sim = world.copy()
    sim.get("machine").meters["sound"] += 1
    sim.get("machine").looping = True
    propagate(sim, narrate=False)
    return {
        "looping": sim.get("machine").looping,
        "suspense": sum(c.memes["suspense"] for c in sim.characters()),
    }


def start_song(world: World, machine: Entity, kids: list[Entity], setting: Setting) -> None:
    for k in kids:
        k.memes["curiosity"] += 1
    world.say(
        f"In {setting.place}, on a bright little stage, "
        f"three kids met a karaoke machine with a shiny face."
    )
    world.say(
        f"{kids[0].id}, {kids[1].id}, and {kids[2].id} leaned in to sing, "
        f"and the room felt warm like a round little spring."
    )


def press_play(world: World, singer: Entity, machine: Entity, setting: Setting) -> None:
    singer.memes["bravery"] += 1
    machine.meters["sound"] += 1
    world.say(
        f'"Let\'s try the song," said {singer.id} with a grin and a glow, '
        f'"The karaoke can sparkle; let the tune softly flow."'
    )
    world.say(
        f"The beat came alive in {setting.atmosphere}, light as a kite, "
        f"and the first verse went by in a shimmer of night."
    )
    propagate(world, narrate=False)


def suspense_beats(world: World, observer: Entity, machine: Entity, setting: Setting) -> None:
    observer.memes["suspense"] += 1
    world.say(
        f"But then, with a hum and a hover, the music made a loop, "
        f"turning back on itself like a merry-go-round scoop."
    )
    world.say(
        f'"Why does it repeat?" asked {observer.id}. "Why won\'t it stop?" '
        f'The chorus came back and came back at the top.'
    )


def ask_and_answer(world: World, curious: Entity, helper: Entity, machine: Entity) -> None:
    curious.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f'"See that tiny blue switch?" asked {helper.id} with a smile. '
        f'"That button can stop the loop in a moment or mile."'
    )
    world.say(
        f'{curious.id} peered near the mic and saw what was true: '
        f'a loop mark and stop mark, both waiting in view.'
    )


def stop_loop(world: World, stopper: Entity, machine: Entity, setting: Setting) -> None:
    machine.looping = False
    machine.meters["sound"] = 0.0
    machine.silenced = True
    stopper.memes["relief"] += 1
    world.say(
        f'"One press, little treasure," said {stopper.id}. "{It} can end the song."'
    )


def end_song(world: World, kids: list[Entity], machine: Entity, setting: Setting) -> None:
    for k in kids:
        k.memes["joy"] += 1
        k.memes["relief"] += 1
    world.say(
        f"At last, the loop grew quiet, and the room felt all right; "
        f"the stage kept its sparkle, but the echo took flight."
    )
    world.say(
        f"The three kids then sang once more, soft as a breeze, "
        f"with {machine.label} at rest and their hearts at ease."
    )


def tell(setting: Setting, kids: list[Child], machine_cfg: Machine, trigger: Trigger) -> World:
    world = World()
    children = []
    for child in kids:
        children.append(world.add(Entity(
            id=child.id, kind="character", type=child.gender, role="kid",
            traits=[child.trait], attrs={"age": child.age}, looping=False
        )))
    machine = world.add(Entity(
        id="machine", kind="thing", type="machine", label=machine_cfg.label,
        looping=True, attrs={"room": machine_cfg.room}
    ))
    world.add(Entity(id="helper", kind="character", type="mother", label="the helper", role="adult"))

    world.facts["setting"] = setting
    world.facts["machine_cfg"] = machine_cfg
    world.facts["trigger"] = trigger
    world.facts["kids"] = children

    start_song(world, machine, children, setting)
    world.para()
    press_play(world, children[0], machine, setting)
    suspense_beats(world, children[1], machine, setting)
    world.para()
    ask_and_answer(world, children[2], world.get("helper"), machine)
    stop_loop(world, world.get("helper"), machine, setting)
    world.para()
    end_song(world, children, machine, setting)

    world.facts.update(
        outcome="resolved",
        looped=True,
        stopped=True,
        suspense=sum(c.memes["suspense"] for c in children),
        curiosity=sum(c.memes["curiosity"] for c in children),
    )
    return world


SETTINGS = {
    "stage": Setting("stage", "the little stage", "glow", "bright and cozy", "loop", "spotlight"),
    "room": Setting("room", "the music room", "boast", "soft and warm", "loop", "shiny floor"),
}

CHILDREN = [
    Child("Mina", "girl", "curious", age=6),
    Child("Jace", "boy", "brave", age=7),
    Child("Tia", "girl", "thoughtful", age=6),
]

MACHINE = {
    "karaoke": Machine("karaoke", "karaoke machine", "stage", "loop button", "stop button", "blue", "the moon song", "loud", "suspenseful"),
}

TRIGGERS = {
    "loop": Trigger("loop", "loop button", "press loop", "repeat song", 3, 3,
                    "pressed the loop button and the song repeated",
                    "pressed the loop button, but nothing changed",
                    tags={"loop", "karaoke"}),
    "stop": Trigger("stop", "stop button", "press stop", "silence song", 3, 5,
                    "pressed the stop button and the song went quiet",
                    "pressed the stop button, but the loop was too strong",
                    tags={"stop", "karaoke"}),
}



@dataclass
class StoryParams:
    setting: str
    machine: str
    trigger: str
    kid1: str
    kid1_gender: str
    kid2: str
    kid2_gender: str
    kid3: str
    kid3_gender: str
    adult: str
    trait: str
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

CURATED = [
    StoryParams("stage", "karaoke", "loop", "Mina", "girl", "Jace", "boy", "Tia", "girl", "mother", "curious"),
    StoryParams("room", "karaoke", "loop", "Jace", "boy", "Tia", "girl", "Mina", "girl", "father", "thoughtful"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MACHINE:
            for t in TRIGGERS:
                combos.append((s, m, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld about a karaoke loop and curious kids.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--machine", choices=MACHINE)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--adult", choices=["mother", "father"])
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
    combos = [c for c in valid_combos() if (args.setting is None or c[0] == args.setting)]
    if not combos:
        raise StoryError("No valid karaoke story matches the given options.")
    setting, machine, trigger = rng.choice(combos)
    kid_names = ["Mina", "Jace", "Tia", "Noa", "Lio"]
    chosen = rng.sample(kid_names, 3)
    genders = [rng.choice(["girl", "boy"]) for _ in range(3)]
    adult = args.adult or rng.choice(["mother", "father"])
    trait = rng.choice(["curious", "careful", "thoughtful"])
    return StoryParams(setting, machine, trigger, chosen[0], genders[0], chosen[1], genders[1], chosen[2], genders[2], adult, trait)


def reasonableness_gate(params: StoryParams) -> bool:
    return params.trigger == "loop" and params.machine == "karaoke"


def outcome_of(params: StoryParams) -> str:
    return "resolved"


def _story_lines(world: World) -> str:
    return world.render()


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], [Child(params.kid1, params.kid1_gender, params.trait),
                                            Child(params.kid2, params.kid2_gender, "curious"),
                                            Child(params.kid3, params.kid3_gender, "careful")],
                 MACHINE[params.machine], TRIGGERS[params.trigger])
    return StorySample(
        params=params,
        story=_story_lines(world),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a rhyming suspense story for a young child that includes the words "three", "karaoke", and "loop".',
        "Tell a dialogue-driven story where three children hear a karaoke song loop and solve the mystery with curiosity.",
        "Write a gentle suspense rhyme about a looping song, a curious clue, and a happy ending with three kids.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    kids = world.facts["kids"]
    machine = world.facts["machine_cfg"]
    return [
        ("Who are the story's main characters?",
         f"The story is about three children: {kids[0].id}, {kids[1].id}, and {kids[2].id}. They are the ones who listen, wonder, and help fix the looping song."),
        ("What problem did they notice?",
         f"The karaoke song got stuck in a loop and kept repeating. That made the room feel suspenseful until they found the stop button."),
        ("How did they solve it?",
         f"The helper showed them the stop button on the karaoke machine, and the loop ended. After that, the music was quiet and the children could sing again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is karaoke?",
         "Karaoke is singing along with music on a machine or screen. People choose a song and sing it themselves."),
        ("What does a loop mean?",
         "A loop is something that repeats again and again. A song loop can play the same part over and over."),
        ("Why can curiosity help?",
         "Curiosity helps you notice clues and ask questions. That can lead you to the right answer when something strange happens."),
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.looping:
            bits.append("looping")
        if e.silenced:
            bits.append("silenced")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(setting(S), machine(M), trigger(T)) :- setting(S), machine(M), trigger(T).
looping(machine) :- trigger(loop).
resolved :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MACHINE:
        lines.append(asp.fact("machine", mid))
    for tid in TRIGGERS:
        lines.append(asp.fact("trigger", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP validity.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.asp:
        print(f"{len(asp_valid_combos())} valid karaoke combinations.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
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
