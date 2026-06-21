#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/whap_sound_effects_heartwarming.py
===================================================================

A standalone story world for a tiny heartwarming domain with sound effects.

Premise:
- A child and a grown-up are preparing a cozy surprise.
- A floppy cloth sign or banner makes a loud "whap" in the breeze.
- The child worries, but the grown-up helps turn the noisy moment into a warm
  celebration with a safer, better setup.

The simulation is state-driven:
- physical meters track wobble, snag, and comfort
- emotional memes track worry, courage, delight, and closeness

This file follows the shared Storyweavers storyworld contract.
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
COMFORT_GOAL = 2.0


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
    sounds: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(
            self.type, self.type
        )


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    adult_name: str
    adult_type: str
    object_kind: str
    object_name: str
    sound_effect: str
    help_method: str
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    place_sentence: str
    weather: str
    comfort_phrase: str


@dataclass
class ObjectKind:
    id: str
    label: str
    phrase: str
    risky_when: str
    fixable_with: str
    sound_line: str
    soft_finish: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelpMethod:
    id: str
    sense: int
    power: int
    action_line: str
    result_line: str
    warm_line: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    for child in world.entities.values():
        if child.kind != "character":
            continue
        if child.memes["comfort"] < COMFORT_GOAL:
            continue
        sig = ("comfort", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
        out.append("__comfort__")
    return out


CAUSAL_RULES = [Rule("comfort", _r_comfort)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    return f"{setting.place_sentence} {setting.comfort_phrase}"


def predict_whap(world: World, obj: Entity) -> dict:
    sim = world.copy()
    _make_whap(sim, sim.get(obj.id), narrate=False)
    return {
        "worry": sim.get("child").memes["worry"],
        "tangled": sim.get(obj.id).meters["tangled"],
    }


def _make_whap(world: World, obj: Entity, narrate: bool = True) -> None:
    obj.meters["tangled"] += 1
    obj.meters["wobble"] += 1
    world.get("child").memes["worry"] += 1
    if narrate:
        world.say(obj.sounds[0])


def start(world: World, child: Entity, adult: Entity, setting: Setting, obj: Entity) -> None:
    child.memes["joy"] += 1
    adult.memes["care"] += 1
    world.say(
        f"On a cozy afternoon, {child.id} and {adult.id} worked in {setting.id}. "
        f"{setting_detail(setting)}"
    )
    world.say(
        f'They were making {obj.phrase} together, because {adult.id} wanted the room '
        f'to feel extra warm and welcoming.'
    )


def sound_and_surprise(world: World, child: Entity, obj: Entity) -> None:
    pred = predict_whap(world, obj)
    world.facts["predicted_worry"] = pred["worry"]
    world.facts["predicted_tangled"] = pred["tangled"]
    world.say(
        f"{child.id} held up the last corner, and the cloth gave a sudden "
        f'"{obj.sounds[0]}!" in the breeze.'
    )
    world.say(
        f"{child.id} blinked. For a moment, it sounded bigger than it was, and the room felt very still."
    )


def worry_and_help(world: World, child: Entity, adult: Entity, obj: Entity, method: HelpMethod) -> None:
    child.memes["worry"] += 1
    adult.memes["care"] += 1
    world.say(
        f'{child.id} frowned. "{obj.sound_line}"'
    )
    world.say(
        f'{adult.id} smiled and said, "{method.action_line}"'
    )


def fix(world: World, child: Entity, adult: Entity, obj: Entity, method: HelpMethod) -> None:
    obj.meters["tangled"] = 0.0
    obj.meters["wobble"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["comfort"] += 2.0
    adult.memes["comfort"] += 1.0
    world.say(
        f"In a minute, {adult.id} {method.result_line}."
    )
    world.say(
        f"{method.warm_line} Then {child.id} could hold it steady with both hands."
    )


def ending(world: World, child: Entity, adult: Entity, setting: Setting, obj: Entity) -> None:
    child.memes["delight"] += 1
    adult.memes["delight"] += 1
    world.say(
        f"After that, the last bit went just right. {child.id} and {adult.id} stood back and smiled at "
        f"{obj.phrase}, now hanging neatly in {setting.id}."
    )
    world.say(
        f"It was still the same windy day, but now the only sound was a gentle breeze and happy laughter."
    )


SETTINGS = {
    "kitchen": Setting(
        id="the kitchen",
        place_sentence="The kitchen was bright and tidy.",
        weather="soft afternoon light",
        comfort_phrase="A warm cake was cooling on the counter.",
    ),
    "porch": Setting(
        id="the porch",
        place_sentence="The porch was full of fresh air.",
        weather="a breezy afternoon",
        comfort_phrase="A little potted plant sat by the door like a quiet friend.",
    ),
    "playroom": Setting(
        id="the playroom",
        place_sentence="The playroom was sunny and cozy.",
        weather="soft indoor air",
        comfort_phrase="A stuffed bear watched from the shelf.",
    ),
}

OBJECTS = {
    "banner": ObjectKind(
        id="banner",
        label="banner",
        phrase="a handmade welcome banner",
        risky_when="it flapped loose in the wind",
        fixable_with="tape and a second string",
        sound_line='that banner keeps going "whap" when the breeze catches it',
        soft_finish="The banner settled into place and looked proud and friendly.",
        tags={"banner", "cloth", "wind"},
    ),
    "towel": ObjectKind(
        id="towel",
        label="towel",
        phrase="a bright dish towel sign",
        risky_when="it swung near the doorway",
        fixable_with="a clothespin and a hook",
        sound_line='that towel makes a sharp "whap" when it slips loose',
        soft_finish="The towel hung neatly and made the room feel homemade and kind.",
        tags={"towel", "cloth", "wind"},
    ),
    "flag": ObjectKind(
        id="flag",
        label="flag",
        phrase="a little cloth flag",
        risky_when="it snapped in the air",
        fixable_with="a string loop and a chair",
        sound_line='that flag goes "whap" when the wind turns playful',
        soft_finish="The flag lifted gently and looked like a tiny celebration.",
        tags={"flag", "cloth", "wind"},
    ),
}

METHODS = {
    "tape": HelpMethod(
        id="tape",
        sense=3,
        power=3,
        action_line="Let's tape down the corner and give it a better anchor.",
        result_line="added a little tape and tied the corner to the hook",
        warm_line="The tape held, and the banner stopped dancing around.",
        tags={"tape", "safe"},
    ),
    "clothespin": HelpMethod(
        id="clothespin",
        sense=3,
        power=3,
        action_line="We can use a clothespin and a second string.",
        result_line="used a clothespin and tied on a second string",
        warm_line="The clothespin held fast, like a tiny helper with strong fingers.",
        tags={"clothespin", "safe"},
    ),
    "button": HelpMethod(
        id="button",
        sense=2,
        power=2,
        action_line="We can tuck it under the button board and smooth it out.",
        result_line="smoothed the cloth flat and tucked the loose bit in place",
        warm_line="That made the cloth calm down at once.",
        tags={"button", "safe"},
    ),
    "wrong_knot": HelpMethod(
        id="wrong_knot",
        sense=1,
        power=1,
        action_line="Just pull harder and hope it stays.",
        result_line="pulled once and hoped for the best",
        warm_line="It did not help much at all.",
        tags={"unsafe"},
    ),
}

CHILD_NAMES = ["Mia", "Lily", "Noah", "Eli", "Ava", "Finn", "Zoe", "Theo"]
ADULT_NAMES = ["Mom", "Dad", "Grandma", "Grandpa"]
CHILD_TYPES = ["girl", "boy"]
ADULT_TYPES = ["mother", "father", "grandmother", "grandfather"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for obj in OBJECTS:
            for method in METHODS:
                if METHODS[method].sense >= 2:
                    combos.append((place, obj, method, "default"))
    return combos


def explain_rejection(method: HelpMethod) -> str:
    return (
        f"(No story: the method '{method.id}' is too weak or too shaky for this "
        f"heartwarming setup. Pick a calmer, safer fix.)"
    )


def explain_params(args: argparse.Namespace) -> str:
    return "(No story: the chosen options do not make a reasonable cozy scene.)"


def _pick_name(rng: random.Random, names: list[str]) -> str:
    return rng.choice(names)


def _make_child(world: World, name: str, gender: str) -> Entity:
    return world.add(Entity(id=name, kind="character", type=gender, role="child"))


def _make_adult(world: World, name: str, adult_type: str) -> Entity:
    return world.add(Entity(id=name, kind="character", type=adult_type, role="adult"))


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.place]
    obj_cfg = OBJECTS[params.object_kind]
    method = METHODS[params.help_method]
    child = _make_child(world, params.child_name, params.child_type)
    adult = _make_adult(world, params.adult_name, params.adult_type)
    obj = world.add(Entity(id="thing", kind="thing", type="thing", label=obj_cfg.label, sounds=[params.sound_effect]))

    start(world, child, adult, setting, obj)
    world.para()
    sound_and_surprise(world, child, obj)
    worry_and_help(world, child, adult, obj, method)
    fix(world, child, adult, obj, method)
    world.para()
    ending(world, child, adult, setting, obj)

    world.facts.update(
        child=child,
        adult=adult,
        setting=setting,
        obj_cfg=obj_cfg,
        method=method,
        object=obj,
        outcome="warm",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    obj = f["obj_cfg"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the sound word "{obj.sound_line.split()[0].strip(\'"\')}".',
        f"Tell a cozy story where {child.id} and a grown-up make {obj.phrase} and a loud sound effect turns into a gentle, happy fix.",
        f'Write a warm family story where the word "whap" appears when a cloth object flaps, and the grown-up helps make it safe again.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    obj = f["obj_cfg"]
    method = f["method"]
    setting = f["setting"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {adult.id}, who were working together in {setting.id}. They were making {obj.phrase} as a sweet surprise."),
        (f'What sound did the cloth make?',
         f'It made a loud "{world.get("thing").sounds[0]}" when the breeze caught it. That sound was surprising, but it was only the loose cloth flapping around.'),
        (f'How did {adult.id} help?',
         f'{adult.id} used {method.id} to fix the loose cloth. That made the surprise feel safe and calm again.'),
        (f"How did the story end?",
         f"It ended with {obj.soft_finish.lower()} {child.id} and {adult.id} smiling at what they made. The noisy moment turned into a warm memory."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does whap sound like?",
         '“Whap” is a loud, flat flapping sound. People often hear it when cloth catches the wind.'),
        ("Why can loose cloth make a noise in the wind?",
         "When wind pushes fabric, the cloth can snap and flap quickly. That makes a whap sound."),
        ("What helps a banner stay up safely?",
         "A strong tie, tape, or a steady hook can keep a banner from wobbling around. That way it can stay neat and not fly loose."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.sounds:
            parts.append(f"sounds={e.sounds}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
warm_scene(P,O,M) :- place(P), object(O), method(M), good_method(M).
good_method(tape).
good_method(clothespin).
good_method(button).
sound_effect(whap).
story_ok(P,O,M) :- warm_scene(P,O,M), sound_effect(whap).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for m, method in METHODS.items():
        lines.append(asp.fact("method", m))
        if method.sense >= 2:
            lines.append(asp.fact("good_method", m))
    lines.append(asp.fact("sound_effect", "whap"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    if ok:
        print(f"OK: clingo matches valid_combos() ({len(valid_combos())} combos).")
        sample = generate(CURATED[0])
        print("OK: smoke-test story generation succeeded.")
        if not sample.story.strip():
            print("FAIL: empty story")
            return 1
        return 0
    print("MISMATCH between clingo and Python combo logic.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A warm little story world with a whap sound effect.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object-kind", choices=OBJECTS)
    ap.add_argument("--help-method", choices=METHODS)
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--adult-name", choices=ADULT_NAMES)
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--adult-type", choices=ADULT_TYPES)
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
    if args.help_method and METHODS[args.help_method].sense < 2:
        raise StoryError(explain_rejection(METHODS[args.help_method]))
    places = list(SETTINGS)
    objects = list(OBJECTS)
    methods = [m for m, v in METHODS.items() if v.sense >= 2]
    if args.place:
        places = [args.place]
    if args.object_kind:
        objects = [args.object_kind]
    if args.help_method:
        methods = [args.help_method]
    if not places or not objects or not methods:
        raise StoryError(explain_params(args))
    place = rng.choice(places)
    obj = rng.choice(objects)
    method = rng.choice(methods)
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    adult_type = args.adult_type or rng.choice(ADULT_TYPES)
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    adult_name = args.adult_name or rng.choice(ADULT_NAMES)
    if adult_name == child_name:
        adult_name = rng.choice([n for n in ADULT_NAMES if n != child_name])
    return StoryParams(
        place=place,
        child_name=child_name,
        child_type=child_type,
        adult_name=adult_name,
        adult_type=adult_type,
        object_kind=obj,
        object_name=OBJECTS[obj].label,
        sound_effect="whap",
        help_method=method,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError("Invalid place.")
    if params.object_kind not in OBJECTS:
        raise StoryError("Invalid object kind.")
    if params.help_method not in METHODS:
        raise StoryError("Invalid help method.")
    if METHODS[params.help_method].sense < 2:
        raise StoryError(explain_rejection(METHODS[params.help_method]))
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
    StoryParams(
        place="kitchen",
        child_name="Mia",
        child_type="girl",
        adult_name="Mom",
        adult_type="mother",
        object_kind="banner",
        object_name="banner",
        sound_effect="whap",
        help_method="tape",
    ),
    StoryParams(
        place="porch",
        child_name="Noah",
        child_type="boy",
        adult_name="Grandma",
        adult_type="grandmother",
        object_kind="flag",
        object_name="flag",
        sound_effect="whap",
        help_method="clothespin",
    ),
    StoryParams(
        place="playroom",
        child_name="Ava",
        child_type="girl",
        adult_name="Dad",
        adult_type="father",
        object_kind="towel",
        object_name="towel",
        sound_effect="whap",
        help_method="button",
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.child_name} and {p.adult_name} in the {p.place} ({p.object_kind}, {p.help_method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
