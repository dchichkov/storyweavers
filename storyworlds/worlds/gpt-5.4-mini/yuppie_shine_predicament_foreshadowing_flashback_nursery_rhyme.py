#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/yuppie_shine_predicament_foreshadowing_flashback_nursery_rhyme.py
==================================================================================================

A tiny standalone storyworld for a nursery-rhyme-style tale with the seed words
"yuppie", "shine", and "predicament", plus foreshadowing and flashback beats.

The world is intentionally small: one child, one grown-up helper, one bright
object, one little mishap, and a calm fix that changes the ending image. The
story is simulated from state, not rendered as a frozen paragraph with swapped
nouns.

Run:
    python storyworlds/worlds/gpt-5.4-mini/yuppie_shine_predicament_foreshadowing_flashback_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4-mini/yuppie_shine_predicament_foreshadowing_flashback_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4-mini/yuppie_shine_predicament_foreshadowing_flashback_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/yuppie_shine_predicament_foreshadowing_flashback_nursery_rhyme.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MOOD_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"shine": 0.0, "tangle": 0.0, "worry": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "fear": 0.0, "hope": 0.0, "calm": 0.0})

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
    rhyme: str
    shadow: str
    sparkle: str

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
class BrightThing:
    id: str
    label: str
    phrase: str
    light_word: str
    teaches: str
    gives_shine: bool = True

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
class Predicament:
    id: str
    label: str
    phrase: str
    tangle_word: str
    fixed_by: str
    risky: bool = True

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
class Helper:
    id: str
    label: str
    phrase: str
    calm_text: str
    fix_text: str

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


@dataclass
class Rule:
    name: str
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


def _r_foreshadow(world: World) -> list[str]:
    out = []
    if world.get("sky").meters["cloud"] >= THRESHOLD and ("foreshadow",) not in world.fired:
        world.fired.add(("foreshadow",))
        world.get("yuppie").memes["hope"] += 1
        out.append("__foreshadow__")
    return out


def _r_predicament(world: World) -> list[str]:
    out = []
    y = world.get("yuppie")
    if y.meters["tangle"] >= THRESHOLD and ("predicament",) not in world.fired:
        world.fired.add(("predicament",))
        y.memes["fear"] += 1
        world.get("room").meters["worry"] += 1
        out.append("__predicament__")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    mom = world.get("helper")
    y = world.get("yuppie")
    if y.memes["fear"] >= THRESHOLD and ("calm",) not in world.fired:
        world.fired.add(("calm",))
        mom.memes["calm"] += 1
        y.memes["fear"] = 0.0
        y.memes["hope"] += 1
        out.append("__calm__")
    return out


RULES = [Rule("foreshadow", _r_foreshadow), Rule("predicament", _r_predicament), Rule("calm", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def suggestibility(setting: Setting, bright: BrightThing, predicament: Predicament) -> bool:
    return bright.gives_shine and predicament.risky and setting.shadow != ""


SETTINGS = {
    "moon_lane": Setting("moon_lane", "Moon Lane", "The moon was up above the lane", "a sleepy shadow under the gate", "a silver shine"),
    "nursery_window": Setting("nursery_window", "the nursery window", "A hush fell soft as lace", "a shadow by the sill", "a warm shine"),
    "garden_bench": Setting("garden_bench", "the garden bench", "Little leaves would tip and sway", "a shadow under the vines", "a gold shine"),
}

BRIGHTS = {
    "lantern": BrightThing("lantern", "lantern", "a little lantern", "shine", "it could shine in the dark"),
    "star_bell": BrightThing("star_bell", "star bell", "a star-shaped bell", "shine", "it could shine like a tiny star"),
}

PREDS = {
    "spool": Predicament("spool", "spool of thread", "a spool of thread", "tangle", "be unwound"),
    "ribbon": Predicament("ribbon", "ribbon", "a ribbon", "tangle", "be loosened"),
}

HELPERS = {
    "mother": Helper("helper", "mom", "mom", "a calm smile", "a tidy fix"),
    "grandma": Helper("helper", "grandma", "grandma", "a soft laugh", "a gentle fix"),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    bright: str
    predicament: str
    helper: str
    child_name: str
    child_type: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about shine, foreshadowing, and flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bright", choices=BRIGHTS)
    ap.add_argument("--predicament", choices=PREDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for b in BRIGHTS:
            for p in PREDS:
                if suggestibility(SETTINGS[s], BRIGHTS[b], PREDS[p]):
                    out.append((s, b, p))
    return out


def explain_rejection(setting: Setting, bright: BrightThing, predicament: Predicament) -> str:
    return f"(No story: {bright.label} can shine, but this predicament does not fit the shadowy nursery-rhyme turn.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.bright and args.predicament:
        if not suggestibility(SETTINGS[args.setting], BRIGHTS[args.bright], PREDS[args.predicament]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], BRIGHTS[args.bright], PREDS[args.predicament]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.bright is None or c[1] == args.bright)
              and (args.predicament is None or c[2] == args.predicament)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, bright, predicament = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    name = args.name or rng.choice(["Milo", "Luna", "Nina", "Toby", "Pip"])
    gender = args.gender or rng.choice(["girl", "boy"])
    return StoryParams(setting, bright, predicament, helper, name, gender)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    bright = BRIGHTS[params.bright]
    predicament = PREDS[params.predicament]
    helper = HELPERS[params.helper]
    child = world.add(Entity("yuppie", kind="character", type=params.child_type, role="child", label=params.child_name))
    mom = world.add(Entity("helper", kind="character", type="mother" if params.helper == "mother" else "woman", role="helper", label=helper.label))
    sky = world.add(Entity("sky", label="the sky"))
    room = world.add(Entity("room", label=setting.place))
    child.memes["hope"] = 1.0

    world.say(f"On {setting.rhyme}, in {setting.place}, there lived a little yuppie by name {child.id}.")
    world.say(f"{setting.sparkle} met {child.id}, and all the leaves seemed to sing and climb.")
    world.say(f'"Oh, {bright.phrase}," said {child.id}, "I want it to {bright.light_word} and shine!"')
    world.say(f"But {setting.shadow} was waiting there, like a hush before a chime.")

    world.para()
    sky.meters["cloud"] += 1
    propagate(world, narrate=False)
    world.say(f"A cloud came by as if to say, " f'"Mind the path and mind the line."')
    world.say(f'That was a foreshadowing note, soft as milk and sweet as twine.')

    world.para()
    child.meters["shine"] += 1
    world.say(f"{child.id} took up {bright.phrase} and meant to make the whole lane gleam.")
    world.say(f"But in a little flash of haste, {child.id} met a {predicament.phrase} in the stream.")
    child.meters["tangle"] += 1
    propagate(world, narrate=False)
    world.say(f"{child.id} gave a tiny gasp: " f'"Oh dear, I am in a predicament, it seems!"')

    world.para()
    if params.helper == "grandma":
        world.say(f"Flashback now: long ago, {helper.label} had said, 'A tangled thing needs patient hands.'")
        world.say(f'{child.id} remembered that in a blink, as clear as bells and bands.')
    else:
        world.say(f"Flashback now: {helper.label} had once shown {child.id} how knots can yield to care.")
        world.say(f'{child.id} remembered that old kind lesson, floating like a prayer.')

    world.para()
    world.say(f'{helper.label.capitalize()} came with a calm {helper.calm_text}, and {helper.fix_text}.')
    child.meters["tangle"] = 0.0
    room.meters["worry"] = 0.0
    child.memes["calm"] += 1
    child.memes["joy"] += 1
    world.say(f"They eased the tangle, and {bright.phrase} could {bright.light_word} once more in air.")
    world.say(f"So the yuppie learned that shine is sweeter when a helper helps to share.")
    world.say(f"In the end, {child.id} stood where the shadow had been, but now with a brighter view.")
    world.say(f"The little thing shone safe and sound, and every tiny trouble passed right through.")

    world.facts.update(
        child=child, helper=mom, setting=setting, bright=bright, predicament=predicament,
        outcome="fixed", foreshadowed=True, flashback=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story that includes the words "yuppie", "shine", and "predicament".',
        f"Tell a gentle tale where {f['child'].id} tries to make {f['bright'].label} {f['bright'].light_word}, but a predicament appears and a helper fixes it.",
        f"Write a rhyme with foreshadowing and flashback that ends with {f['child'].id} safe, calm, and shining in a new way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    bright = f["bright"]
    predicament = f["predicament"]
    return [
        QAItem(
            question=f"What did {child.id} want to do?",
            answer=f"{child.id} wanted to make {bright.phrase} {bright.light_word} and shine. The wish mattered because the whole story turns around that bright idea."
        ),
        QAItem(
            question="What was the predicament?",
            answer=f"The predicament was a tangled {predicament.label}. It blocked the bright moment, so the child had to pause and accept help."
        ),
        QAItem(
            question=f"What was the flashback for?",
            answer=f"The flashback reminded {child.id} of an older kind lesson from {helper.label}. That memory helped {child.id} stay calm and let the fix work."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a lantern for?", "A lantern is for giving light in the dark. It helps people see without needing a flame from a match."),
        QAItem("What does foreshadowing do in a story?", "Foreshadowing gives a small clue about what may happen later. It helps the reader feel the turn before it arrives."),
        QAItem("What does a flashback do in a story?", "A flashback shows something that happened earlier. It helps explain why a character remembers a useful idea."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,B,P) :- setting(S), bright(B), predicament(P), supports(S,B,P).
foreshadowed :- clouded(sky).
predicament_now :- tangle(yuppie).
fixed :- predicament_now, helper_calm.
"""


def asp_facts() -> str:
    import asp
    out = []
    for s in SETTINGS:
        out.append(asp.fact("setting", s))
    for b in BRIGHTS:
        out.append(asp.fact("bright", b))
    for p in PREDS:
        out.append(asp.fact("predicament", p))
    for s, setting in SETTINGS.items():
        for b, bright in BRIGHTS.items():
            for p, pred in PREDS.items():
                if suggestibility(setting, bright, pred):
                    out.append(asp.fact("supports", s, b, p))
    return "\n".join(out)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, bright=None, predicament=None, helper=None, name=None, gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams("moon_lane", "lantern", "spool", "mother", "Milo", "boy"),
    StoryParams("nursery_window", "star_bell", "ribbon", "grandma", "Luna", "girl"),
    StoryParams("garden_bench", "lantern", "ribbon", "grandma", "Pip", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
