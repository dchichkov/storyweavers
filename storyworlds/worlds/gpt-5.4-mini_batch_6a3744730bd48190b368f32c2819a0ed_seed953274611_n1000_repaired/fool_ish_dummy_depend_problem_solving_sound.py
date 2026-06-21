#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fool_ish_dummy_depend_problem_solving_sound.py
===============================================================================

A small comedy storyworld about a child trying to solve a mystery by listening
for a strange sound. The world is built around:
- a puzzling noise to investigate,
- a few silly false guesses,
- a sensible helper who makes a plan,
- a final reveal that explains the sound.

Seed words: fool-ish, dummy, depend
Features: Problem Solving, Sound Effects, Mystery to Solve
Style: Comedy
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    tags: set[str] = field(default_factory=set)
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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    affordances: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Mystery:
    id: str
    clue: str
    sound: str
    source_tag: str
    false_guess: str
    reveal: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Tool:
    id: str
    label: str
    use: str
    sound: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "role": v.role, "traits": list(v.traits), "attrs": dict(v.attrs),
            "tags": set(v.tags), "meters": defaultdict(float, dict(v.meters)),
            "memes": defaultdict(float, dict(v.memes)),
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    tool: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "bright and busy", {"listening", "searching"}),
    "hallway": Setting("hallway", "the hallway", "long and echoey", {"listening", "searching"}),
    "basement": Setting("basement", "the basement", "dim and squeaky", {"listening", "searching"}),
}

MYSTERIES = {
    "fridge_buzz": Mystery(
        "fridge_buzz", clue="a tiny buzz-buzz-buzz", sound="bzzz", source_tag="fridge",
        false_guess="a robot hiding in the cupboard", reveal="the refrigerator motor",
        tags={"sound", "buzz", "mystery"},
    ),
    "pipe_tap": Mystery(
        "pipe_tap", clue="a tap-tap-tap from the wall", sound="tap tap", source_tag="pipe",
        false_guess="a mouse with tap shoes", reveal="a loose pipe tapping the wall",
        tags={"sound", "tap", "mystery"},
    ),
    "chair_squeak": Mystery(
        "chair_squeak", clue="a squeeeeeak at every wiggle", sound="squeak", source_tag="chair",
        false_guess="a duck in tiny shoes", reveal="a chair with a wobbly leg",
        tags={"sound", "squeak", "mystery"},
    ),
}

TOOLS = {
    "flashlight": Tool("flashlight", "flashlight", "shine under things", "click", tags={"light"}),
    "stethoscope": Tool("stethoscope", "toy stethoscope", "listen carefully", "boop", tags={"listen"}),
    "magnifier": Tool("magnifier", "magnifying glass", "inspect clues", "glint", tags={"look"}),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Theo", "Finn"]
HELPER_TRAITS = ["careful", "curious", "patient", "clever", "sensible"]


def sound_phrase(mystery: Mystery) -> str:
    return mystery.sound


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["noise"] < THRESHOLD:
            continue
        sig = ("echo", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["curiosity"] += 1
        out.append("")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("solved") and not world.fired.__contains__(("relief",)):
        world.fired.add(("relief",))
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["relief"] += 1
        out.append("")
    return out


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_echo, _r_relief):
            before = len(world.fired)
            rule(world)
            if len(world.fired) != before:
                changed = True


def mystery_reasonable(setting: Setting, mystery: Mystery) -> bool:
    return "searching" in setting.affordances and "mystery" in mystery.tags


def best_tool(tool: Tool) -> bool:
    return tool.id in TOOLS


def explain_rejection(setting: Setting, mystery: Mystery) -> str:
    return f"(No story: {setting.place} does not support this kind of listening mystery.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("tagged", mid, "mystery"))
        lines.append(asp.fact("source_tag", mid, m.source_tag))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M) :- setting(S), mystery(M), affords(S, searching), tagged(M, mystery).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for mid, m in MYSTERIES.items():
            if mystery_reasonable(s, m):
                combos.append((sid, mid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy mystery-solving storyworld with sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.setting and args.mystery:
        if not mystery_reasonable(SETTINGS[args.setting], MYSTERIES[args.mystery]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], MYSTERIES[args.mystery]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" and rng.random() < 0.5 else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    tool = args.tool or rng.choice(sorted(TOOLS))
    return StoryParams(setting=setting, mystery=mystery, hero=hero, hero_gender=hero_gender,
                       helper=helper, helper_gender=helper_gender, tool=tool)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper",
                              traits=["fool-ish", "dummy", "depend"]))
    box = world.add(Entity(id="box", type="thing", label="a little box", tags={"clue"}))
    world.add(Entity(id="noise", type="thing", label=mystery.clue, tags=set(mystery.tags)))

    hero.memes["confused"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"In {setting.place}, {hero.id} stopped in the middle of the room. "
        f"Somewhere nearby went {sound_phrase(mystery)}."
    )
    world.say(
        f'"What is that {mystery.clue}?" {hero.id} asked. '
        f'"It sounds a little fool-ish," {hero.id} added, which was not very helpful.'
    )

    world.para()
    world.say(
        f"{helper.id} came over with {tool.label} and said, "
        f'"No need to act like a dummy. We can depend on clues."'
    )
    world.say(
        f'{helper.id} held up {tool.label} and made {tool.sound}. '
        f'Then {helper.id} listened, looked, and listened again.'
    )

    hero.meters["noise"] += 1
    propagate(world)

    world.para()
    world.say(
        f'The clue led them to {mystery.reveal}. '
        f'That was where the silly sound came from all along.'
    )
    world.say(
        f'{mystery.false_guess.capitalize()} was not real at all; it was just a joke '
        f'{hero.id} had been telling {hero.pronoun("object")}self.'
    )
    world.say(
        f'Both children laughed when the room answered with one last {mystery.sound} '
        f'from the {mystery.source_tag}.'
    )
    world.facts.update(
        setting=setting, mystery=mystery, hero=hero, helper=helper, tool=tool,
        solved=True, box=box, final_sound=mystery.sound, reveal=mystery.reveal,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny mystery story for a child that includes the words "fool-ish", "dummy", and "depend".',
        f"Tell a comedy story where {f['hero'].id} hears a strange sound in {f['setting'].place} and needs a helper to solve it.",
        f'Write a problem-solving story with sound effects, a silly wrong guess, and a reveal that explains the noise.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    qa = [
        ("What mystery did they solve?",
         f"They solved the mystery of {mystery.clue}. In the end, they found out that the sound came from {mystery.reveal}."),
        (f"What did {hero.id} first think the sound was?",
         f"{hero.id} first guessed {mystery.false_guess}. That guess was silly, so {helper.id} helped {hero.id} check the clues instead."),
        (f"How did {helper.id} help?",
         f"{helper.id} brought a {f['tool'].label} and listened carefully. That helped them follow the clue to the real source of the noise."),
        ("How did the story end?",
         f"It ended in laughter. The sound was explained, the mystery was solved, and nobody needed to depend on a wild guess.")
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tool = f["tool"]
    mystery = f["mystery"]
    return [
        ("What does a flashlight do?",
         "A flashlight makes a bright beam of light so you can see in the dark."),
        ("What does it mean to listen carefully?",
         "It means to stay quiet and pay close attention so you can notice small clues."),
        ("Why are sound effects fun in stories?",
         "Sound effects help you imagine what is happening and make a story feel lively and funny."),
        ("What should you do when something is a mystery?",
         "You should look for clues, ask careful questions, and solve it step by step."),
        (f"Why is {mystery.source_tag} a clue in this story?",
         f"Because the {mystery.source_tag} was the place where the sound really came from. The clue matched the noise, so it helped solve the mystery."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
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


CURATED = [
    StoryParams(setting="kitchen", mystery="fridge_buzz", hero="Lily", hero_gender="girl",
                helper="Ben", helper_gender="boy", tool="flashlight"),
    StoryParams(setting="hallway", mystery="pipe_tap", hero="Max", hero_gender="boy",
                helper="Mia", helper_gender="girl", tool="magnifier"),
    StoryParams(setting="basement", mystery="chair_squeak", hero="Nora", hero_gender="girl",
                helper="Theo", helper_gender="boy", tool="stethoscope"),
]


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    p = set(valid_combos())
    rc = 0
    if a == p:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if a - p:
            print("  only in clingo:", sorted(a - p))
        if p - a:
            print("  only in python:", sorted(p - a))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: generate() smoke test failed: {exc}")
    return rc


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    helper = args.helper or _pick_name(rng, helper_gender)
    tool = args.tool or rng.choice(sorted(TOOLS))
    return StoryParams(setting=setting, mystery=mystery, hero=hero, hero_gender=hero_gender,
                       helper=helper, helper_gender=helper_gender, tool=tool)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mystery) combos:\n")
        for setting, mystery in combos:
            print(f"  {setting:10} {mystery}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.helper}: {p.mystery} in {p.setting}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
