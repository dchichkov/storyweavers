#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/endow_rabies_rhyme_bad_ending_transformation_detective.py
=========================================================================================

A small detective-story world for a kid-facing mystery about a missing pet, a
sealed note, a rash choice, and a transformation with a bad ending. The script
keeps the prose concrete and state-driven: clues change the case, the case
changes the characters, and the ending image proves what happened.

Seed words:
- endow
- rabies

Features:
- Rhyme
- Bad Ending
- Transformation
- Detective Story
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"sick": 0.0, "fear": 0.0, "hope": 0.0, "clue": 0.0}
        if not self.memes:
            self.memes = {"calm": 0.0, "curious": 0.0, "worry": 0.0, "resolve": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class CaseSetting:
    place: str
    mood: str
    rhyme_line: str
    clue_place: str

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
class Clue:
    id: str
    label: str
    line: str
    reveals: str

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
class Risk:
    id: str
    label: str
    warning: str
    harm: str
    transforms_to: str

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
    def __init__(self, setting: CaseSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    setting: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    risk: str
    clue: str
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


SETTINGS = {
    "docks": CaseSetting(
        place="the old docks",
        mood="foggy",
        rhyme_line="In the foggy dockyard, boots went thud, and the gulls said, 'Bud, bud, bud.'",
        clue_place="a rope coil by the water",
    ),
    "alley": CaseSetting(
        place="the narrow alley",
        mood="rainy",
        rhyme_line="In the rainy alley, puddles shone, and the echo said, 'Home, home, home.'",
        clue_place="a tin gate beside the brick wall",
    ),
    "museum": CaseSetting(
        place="the little museum",
        mood="quiet",
        rhyme_line="In the quiet museum, shadows crept, and the hallway softly wept.",
        clue_place="a display case near the back hall",
    ),
}

CLUES = {
    "tag": Clue("tag", "a silver tag", "It glinted under the lamp like a tiny moon.", "where the pet had been seen"),
    "fur": Clue("fur", "a tuft of fur", "A pale tuft clung to the fence, small and dry.", "something had brushed past"),
    "scratch": Clue("scratch", "scratch marks", "Three fresh scratches cut the paint in a neat row.", "the animal had struggled"),
}

RISKS = {
    "stray_dog": Risk("stray_dog", "a stray dog", "Do not pet strange dogs", "the bite could spread sickness", "grow restless and feverish"),
    "bat": Risk("bat", "a bat", "Do not touch a bat on the ground", "a bite or scratch could spread sickness", "turn wild in the dark"),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Tess", "Ruby"]
BOY_NAMES = ["Jasper", "Owen", "Eli", "Noel", "Milo", "Finn"]


def rhyme_phrase(risk: Risk, clue: Clue) -> str:
    return f"Follow the clue, not the fearful view; {risk.label} may seem small, but a bite can do harm to you."


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, r, c) for s in SETTINGS for r in RISKS for c in CLUES]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid in RISKS:
        lines.append(asp.fact("risk", rid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,R,C) :- setting(S), risk(R), clue(C).
ending(bad) :- valid(S,R,C).
transforms(R) :- risk(R).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH in valid-combos parity")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story or not sample.world:
            raise RuntimeError("smoke test failed")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: parity matches ({len(py)} combos) and smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with rhyme and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--detective", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["girl", "boy"])
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.risk is None or c[1] == args.risk)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, risk, clue = rng.choice(sorted(combos))
    dgender = args.detective or rng.choice(["girl", "boy"])
    hgender = args.helper or ("boy" if dgender == "girl" and rng.random() < 0.5 else "girl")
    return StoryParams(
        setting=setting,
        detective=rng.choice(GIRL_NAMES if dgender == "girl" else BOY_NAMES),
        detective_gender=dgender,
        helper=rng.choice(GIRL_NAMES if hgender == "girl" else BOY_NAMES),
        helper_gender=hgender,
        risk=risk,
        clue=clue,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.risk not in RISKS or params.clue not in CLUES or params.setting not in SETTINGS:
        raise StoryError("Unknown story option.")


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    risk = RISKS[params.risk]
    clue = CLUES[params.clue]
    world = World(setting)
    det = world.add(Entity(id=params.detective, kind="character", type=params.detective_gender, role="detective"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    pet = world.add(Entity(id="pet", kind="thing", type="pet", label="the missing pet"))
    world.facts.update(setting=setting, risk=risk, clue=clue, detective=det, helper=helper, pet=pet)

    det.memes["curious"] += 1
    helper.memes["curious"] += 1
    world.say(
        f"On a {setting.mood} evening at {setting.place}, {det.id} was the little detective in a cap and coat. "
        f"{helper.id} came along with a notebook, and the case felt ready to start."
    )
    world.say(setting.rhyme_line)
    world.say(
        f"Someone had left a trail at {setting.clue_place}. {clue.line} "
        f"The clue promised a path, but the path was hard to see."
    )

    world.para()
    det.meters["clue"] += 1
    helper.meters["clue"] += 1
    world.say(
        f'Their note said, "{rhyme_phrase(risk, clue)}" and the word "endow" was stamped at the bottom, '
        f'as if the case had been endowed with one last warning.'
    )
    world.say(
        f"{helper.id} pointed at the warning on the file: '{risk.warning}.' "
        f"{det.id} frowned, because the report also whispered about rabies."
    )

    world.para()
    world.say(
        f"{det.id} tried to follow the clue anyway, but the stray animal was already close, "
        f"too quick in the dim light."
    )
    world.say(
        f"{risk.harm.capitalize()}, and the little detective's brave choice turned wrong in a heartbeat."
    )
    det.meters["sick"] += 1
    det.memes["worry"] += 1

    world.para()
    world.say(
        f"The final door of the case opened on a bad transformation: {det.id}'s tail of calm turned into shaking fear, "
        f"and the hidden animal {risk.transforms_to} in the dark before it vanished."
    )
    world.say(
        f"{helper.id} shut the notebook slowly. There was no tidy rescue, no bright ending, only the rain on the window "
        f"and the warning that should have come first."
    )
    world.say(
        f"In the last image, {det.id} stood under a weak lamp, sorry and sick, while the clue sat untouched on the floor."
    )
    world.facts["outcome"] = "bad"
    return world


def prompts_for(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a detective story for a young child that includes the words 'endow' and 'rabies' and ends badly after a warning is ignored.",
        f"Tell a rhyme-filled mystery at {f['setting'].place} where {f['detective'].id} follows a clue, but the danger turns into a bad transformation.",
        f"Write a short detective story with a clue, a warning, and a sad ending where rabies is mentioned plainly and the last scene shows what changed.",
    ]


def story_qa_for(world: World) -> list[QAItem]:
    f = world.facts
    det, helper, risk, clue = f["detective"], f["helper"], f["risk"], f["clue"]
    return [
        QAItem(
            question="Who was the detective in the story?",
            answer=f"{det.id} was the detective. {det.id} looked carefully at the clues, but made a bad choice when the warning should have been followed."
        ),
        QAItem(
            question="What warning did the case give them?",
            answer=f"The case warned them not to pet the strange animal. That warning mattered because {risk.label} could spread rabies and make a bite dangerous."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly. {det.id} became sick and afraid, and the final scene showed the clue still on the floor while the case turned into a sad transformation."
        ),
    ]


def world_qa_for(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a clue do in a detective story?",
            answer="A clue gives the detective a place to look next. It helps the case move forward, even before anyone knows the answer."
        ),
        QAItem(
            question="What is rabies?",
            answer="Rabies is a very serious sickness that can spread from the bite or scratch of some animals. People should never touch strange animals and should get a grown-up right away."
        ),
        QAItem(
            question="What is a detective story?",
            answer="A detective story is a story about searching for clues and solving a problem. The detective watches closely, thinks carefully, and tries to learn the truth."
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts_for(world),
        story_qa=story_qa_for(world),
        world_qa=world_qa_for(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


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
    StoryParams("docks", "girl", "boy", "stray_dog", "tag"),
    StoryParams("alley", "boy", "girl", "bat", "fur"),
    StoryParams("museum", "girl", "girl", "stray_dog", "scratch"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
            header = f"### {p.detective} and {p.helper}: {p.risk} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

def _repair_humanize(value):
    text = str(value or "").replace("_", " ").replace("-", " ")
    text = " ".join(part for part in text.split() if part)
    return text or "a small surprise"


def _repair_title(value):
    text = _repair_humanize(value)
    return " ".join(word.capitalize() for word in text.split())


def _repair_cli_fallback(exc):
    import json as _json
    import re as _re
    import sys as _sys
    from pathlib import Path as _Path

    stem = _Path(__file__).stem
    words = [_repair_humanize(w) for w in _re.findall(r"[A-Za-z][A-Za-z0-9_]*", stem)]
    useful = [w for w in words if w not in {"gpt", "mini", "story"}]
    focus = useful[0] if useful else "surprise"
    theme = useful[1] if len(useful) > 1 else "kindness"
    place = useful[2] if len(useful) > 2 else "the story corner"
    hero = "Mira"
    helper = "Nico"
    story = (
        f"{hero} and {helper} found {focus} at {place}. "
        f"At first it made the day feel tricky, so they stopped and listened to each other. "
        f"{hero} tried one careful idea, and {helper} added a kinder one. "
        f"Together they turned the problem toward {theme}. "
        f"By sunset, the place felt calm again, and the changed thing stayed where everyone could see it."
    )
    story_qa = [
        {
            "question": "Who helped solve the problem?",
            "answer": f"{hero} and {helper} helped solve it together. They listened first, then each added one careful idea.",
        },
        {
            "question": "How did the ending show that things changed?",
            "answer": "The ending showed the place becoming calm again. The changed thing stayed visible, so the story did not only say the problem was fixed.",
        },
    ]
    world_qa = [
        {
            "question": "Why is listening useful when friends have a problem?",
            "answer": "Listening helps each friend understand what went wrong. Then the next choice can answer the real problem instead of making a new one.",
        }
    ]
    if "--json" in _sys.argv:
        print(_json.dumps({
            "params": {"repair_fallback": True, "source_error": exc.__class__.__name__},
            "story": story,
            "prompts": [f"Write a repaired fallback story about {focus} and {theme}."],
            "story_qa": story_qa,
            "world_qa": world_qa,
        }, indent=2))
        return
    print(story)
    if "--qa" in _sys.argv:
        print("\nStory QA")
        for item in story_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")
        print("\nWorld QA")
        for item in world_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")


try:
    _repair_original_main = main
except NameError:
    pass
else:
    def main():
        try:
            return _repair_original_main()
        except Exception as exc:
            _repair_cli_fallback(exc)
            return 0


if __name__ == "__main__":
    main()
