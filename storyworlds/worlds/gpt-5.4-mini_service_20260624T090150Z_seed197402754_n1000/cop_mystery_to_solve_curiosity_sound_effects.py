#!/usr/bin/env python3
"""
A small slice-of-life story world about a curious child, a friendly cop, and a
little mystery to solve with sound effects.

The premise:
- A child hears an odd sound.
- Curiosity pulls them toward a small mystery.
- A nearby cop helps them investigate safely.
- The answer is ordinary, comforting, and visible in the ending image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool
    sound_sources: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    sound: str
    source_label: str
    source_phrase: str
    clue: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CopTool:
    id: str
    label: str
    use_line: str
    reveal_line: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "street": Setting(place="the quiet street", indoor=False, sound_sources={"bike", "cart", "window"}),
    "apartment": Setting(place="the apartment hallway", indoor=True, sound_sources={"pipe", "door", "toy"}),
    "park": Setting(place="the little park", indoor=False, sound_sources={"swing", "duck", "cart"}),
}

MYSTERIES = {
    "rattle_cart": Mystery(
        id="rattle_cart",
        sound="a rattling clank-clank",
        source_label="the lemonade cart",
        source_phrase="a lemonade cart with loose cups",
        clue="metal cups bumped together when the cart rolled over a crack",
        reveal="the cart's lid was just shaking in the breeze",
        tags={"sound_effects", "curiosity", "cop"},
    ),
    "bump_pipe": Mystery(
        id="bump_pipe",
        sound="a thump-bump-bump",
        source_label="the hallway pipe",
        source_phrase="a warm pipe behind the wall",
        clue="the pipe clicked when hot water moved through it",
        reveal="the pipe was only waking up as the water warmed",
        tags={"sound_effects", "curiosity", "cop"},
    ),
    "chirp_toy": Mystery(
        id="chirp_toy",
        sound="a tiny chirp-chirp",
        source_label="the toy box",
        source_phrase="a toy box with a squeaky bird toy",
        clue="the toy bird chirped when the lid pressed its beak",
        reveal="the toy bird had been squeezed under a blanket",
        tags={"sound_effects", "curiosity", "cop"},
    ),
}

COP_TOOLS = [
    CopTool(id="notebook", label="a small notebook", use_line="wrote down the clue", reveal_line="checked the note and smiled"),
    CopTool(id="flashlight", label="a little flashlight", use_line="shined the light into the corner", reveal_line="pointed out the ordinary thing hiding there"),
    CopTool(id="radio", label="a radio", use_line="called for a quick listen", reveal_line="heard the sound again and nodded"),
]

NAMES = ["Mia", "Noah", "Lily", "Ben", "Zoe", "Finn", "Ava", "Leo", "Maya", "Eli"]
TRAITS = ["curious", "gentle", "brave", "patient", "bright", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    cop_name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: a curious child and a friendly cop solve a tiny mystery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--cop-name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    cop_name = args.cop_name or rng.choice(["Officer Sam", "Officer June", "Officer Kai", "Officer Nora"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, cop_name=cop_name, trait=trait)


def _child_type(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def _sound_word(mystery: Mystery) -> str:
    return mystery.sound


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=_child_type(params.gender)))
    cop = world.add(Entity(id="cop", kind="character", type="person", label=params.cop_name))
    mystery = MYSTERIES[params.mystery]
    tool = COP_TOOLS[0 if params.place == "street" else 1 if params.place == "apartment" else 2]

    world.facts.update(child=child, cop=cop, mystery=mystery, tool=tool, params=params)

    child.memes["curiosity"] = 1
    child.memes["worry"] = 0
    cop.memes["calm"] = 1

    world.say(f"{child.id} was a {params.trait} little {child.type} who loved noticing small things.")
    world.say(f"One ordinary day, {child.id} heard {_sound_word(mystery)} near {world.setting.place}, and {child.pronoun().capitalize()} tilted {child.pronoun('possessive')} head to listen.")

    world.para()
    world.say(f"{child.id} followed the sound, because curiosity felt bigger than staying still.")
    world.say(f'The sound went "{mystery.sound}!" and then it stopped, which made the little mystery even stranger.')

    world.para()
    child.memes["curiosity"] += 1
    child.meters["near_mystery"] = 1
    world.say(f"A friendly cop named {cop.label} came over and asked what {child.pronoun('subject')} had heard.")
    world.say(f'{cop.label} brought {tool.label} and said, "{tool.use_line.capitalize()}."')

    world.para()
    world.say(f"Together they looked carefully, listened once more, and found the answer.")
    world.say(f"They learned that {mystery.reveal}.")
    world.say(f"{cop.label} {tool.reveal_line}, and {child.id} laughed because the big sound had turned out to be something small and harmless.")

    world.para()
    child.memes["joy"] = 1
    child.memes["worry"] = 0
    world.say(f"At the end, {child.id} walked home feeling braver, and the street or hallway felt ordinary again.")
    world.say(f"The last thing they heard was a soft {mystery.sound.split(' a ')[-1] if ' a ' in mystery.sound else mystery.sound}, easy and friendly.")

    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    m = world.facts["mystery"]
    return [
        f'Write a short slice-of-life story for a child who hears "{m.sound}" and wants to know what it is.',
        f"Tell a gentle mystery story where {p.name} and {p.cop_name} solve a small sound problem at {world.setting.place}.",
        f'Write a child-friendly story about curiosity, a cop, and a sound effect like "{m.sound}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    m = world.facts["mystery"]
    child = world.facts["child"]
    cop = world.facts["cop"]
    return [
        QAItem(
            question=f"Why did {p.name} follow the sound near {world.setting.place}?",
            answer=f"{p.name} followed it because {child.pronoun('subject')} was curious and wanted to know what made the {m.sound}.",
        ),
        QAItem(
            question=f"What did {p.cop_name} do to help {p.name} solve the mystery?",
            answer=f"{p.cop_name} listened carefully, used {world.facts['tool'].label}, and helped {p.name} find the ordinary source of the sound.",
        ),
        QAItem(
            question=f"What did the mystery turn out to be?",
            answer=f"It turned out to be {m.source_phrase}, and the noise came from something harmless and small.",
        ),
        QAItem(
            question=f"How did {p.name} feel at the end?",
            answer=f"{p.name} felt braver and happier after solving the little mystery with {cop.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    m = world.facts["mystery"]
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, listen, and learn more about something new.",
        ),
        QAItem(
            question="What does a sound effect do in a story?",
            answer="A sound effect helps the reader imagine the noise, like a rattle, bump, chirp, or clank.",
        ),
        QAItem(
            question="What does a cop do?",
            answer="A cop helps keep people safe, listens to problems, and helps solve troubles in the neighborhood.",
        ),
        QAItem(
            question=f"Why can {m.sound} make a child look around?",
            answer="Because a surprising sound can seem mysterious, so a child may want to find out what made it.",
        ),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery_sound(M) :- mystery(M).
curious_child(C) :- child(C).
needs_help(C, M) :- curious_child(C), mystery(M).
resolved(M) :- mystery(M).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for name in SETTINGS:
        lines.append(asp.fact("setting", name))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("sound", mid, m.sound))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show resolved/1."))
    ok = bool(model)
    print("OK: ASP program solved." if ok else "MISMATCH: no model found.")
    return 0 if ok else 1


CURATED = [
    StoryParams(place="street", mystery="rattle_cart", name="Mia", gender="girl", cop_name="Officer Sam", trait="curious"),
    StoryParams(place="apartment", mystery="bump_pipe", name="Noah", gender="boy", cop_name="Officer June", trait="thoughtful"),
    StoryParams(place="park", mystery="chirp_toy", name="Lily", gender="girl", cop_name="Officer Kai", trait="gentle"),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print(sorted(asp.atoms(model, "resolved")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
