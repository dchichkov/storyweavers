#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/binocular_fine_mystery_to_solve_magic_comedy.py
================================================================================

A small standalone storyworld about a child detective, a borrowed binocular,
and a mysteriously "fine" object that turns out to be the wrong kind of fine.
The world leans comedic: clues are silly, magic is real but harmless, and the
ending proves what changed in the world state.

Seed inspiration:
- Words: binocular, fine
- Features: Mystery to Solve, Magic
- Style: Comedy
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
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


@dataclass
class Mystery:
    id: str
    clue: str
    reveal: str
    oddity: str
    solved_by: str

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
class MagicItem:
    id: str
    label: str
    trick: str
    effect: str

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
    power: int
    text: str
    fail: str
    qa_text: str

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
@dataclass
class StoryParams:
    mystery: str
    magic: str
    response: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    adult: str
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


MYSTERIES = {
    "missing_cookie": Mystery(
        "missing_cookie",
        "a crumb trail",
        "the cookie was in the birdhouse",
        "powdered sugar on the windowsill",
        "a spoon",
    ),
    "sleepy_hat": Mystery(
        "sleepy_hat",
        "a soft thump from the coat rack",
        "the hat was nap-warm from the sunny windowsill",
        "a tiny feather in the hallway",
        "a pillow",
    ),
    "laughing_key": Mystery(
        "laughing_key",
        "a jingling sound under the rug",
        "the key was hiding in the toy piano",
        "a ribbon tied around a doorknob",
        "a magnet",
    ),
}

MAGICS = {
    "whisper_bubble": MagicItem("whisper_bubble", "a whisper bubble", "floats up clues", "shows little sparkles"),
    "tickle_chalk": MagicItem("tickle_chalk", "tickle chalk", "draws funny arrows", "leaves giggling arrows"),
    "moon_lens": MagicItem("moon_lens", "a moon lens", "makes clues look enormous", "turns clues into giant clues"),
}

RESPONSES = {
    "peek": Response("peek", 3, 2,
                     "peered through the binocular and followed the clue trail to the answer",
                     "peeked, but the clue trail only led to a very confused chair",
                     "followed the clue trail to the answer"),
    "magic_guess": Response("magic_guess", 2, 3,
                            "used the magic to nudge the clue into a neat little answer",
                            "used the magic, but it only made three suspicious hats appear",
                            "used the magic to nudge the clue into an answer"),
    "combination": Response("combination", 3, 4,
                            "looked carefully through the binocular and then used the magic to reveal the last clue",
                            "looked carefully and tried the magic, but the mystery stayed stubbornly silly",
                            "looked carefully and used the magic to reveal the last clue"),
    "sneeze": Response("sneeze", 1, 1,
                       "sneezed at the clue and hoped for the best",
                       "sneezed, and the mystery only got dustier",
                       "sneezed at the clue"),
}

GIRL_NAMES = ["Mina", "Lola", "Nina", "Tessa", "June", "Pia"]
BOY_NAMES = ["Ollie", "Milo", "Theo", "Ezra", "Finn", "Noel"]


def setup(world: World, d: Entity, h: Entity, adult: Entity, mystery: Mystery, magic: MagicItem) -> None:
    d.memes["curiosity"] += 1
    h.memes["curiosity"] += 1
    world.say(
        f"{d.id} and {h.id} were playing detective in the sitting room, where a missing snack had become a mystery to solve."
    )
    world.say(
        f"{h.id} held up the binocular. "  # intentional space
        f'"I can see clues better with this," {h.id} said. '
        f"Nearby, {magic.label} rested on the table, looking very magical and a little bit nosy."
    )
    world.say(
        f"Then {d.id} found something that was quite fine -- and also quite confusing -- beside the chair."
    )


def notice_fine(world: World, detective: Entity, mystery: Mystery) -> None:
    detective.memes["puzzled"] += 1
    world.say(
        f'"This clue is fine," {detective.id} said, squinting. '
        f'But the "fine" clue was strange: it was polished, glittery, and had {mystery.oddity}.'
    )


def explain_fine(world: World, helper: Entity, mystery: Mystery, magic: MagicItem) -> None:
    helper.memes["helpful"] += 1
    world.say(
        f'{helper.id} giggled. "Maybe fine means fancy, or maybe it means the clue is hiding a joke." '
        f'Then {helper.id} tapped {magic.label}, and {magic.trick}.'
    )


def solve(world: World, detective: Entity, helper: Entity, mystery: Mystery, response: Response) -> None:
    detective.memes["confidence"] += 1
    helper.memes["joy"] += 1
    world.say(
        f'{detective.id} looked through the binocular again and {response.text}.'
    )
    world.say(
        f"The last clue pointed to {mystery.reveal}, and the mystery stopped being mysterious."
    )


def ending(world: World, adult: Entity, mystery: Mystery, magic: MagicItem) -> None:
    adult.memes["relief"] += 1
    world.say(
        f"{adult.label_word.capitalize()} laughed when the answer came out. "
        f'"So that is where it was," {adult.pronoun()} said. '
        f'"{mystery.solved_by} helped after all."'
    )
    world.say(
        f"After that, {magic.label} went back on the table, the binocular stayed on the shelf, and the whole room felt wonderfully ordinary again."
    )


def tell(mystery: Mystery, magic: MagicItem, response: Response,
         detective_name: str, detective_gender: str,
         helper_name: str, helper_gender: str,
         adult_type: str) -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    adult = world.add(Entity(id="Grownup", kind="character", type=adult_type, role="adult", label="the grown-up"))
    world.add(Entity(id="binocular", type="thing", label="the binocular"))
    world.add(Entity(id=magic.id, type="thing", label=magic.label))

    setup(world, detective, helper, adult, mystery, magic)
    world.para()
    notice_fine(world, detective, mystery)
    explain_fine(world, helper, mystery, magic)
    world.para()
    solve(world, detective, helper, mystery, response)
    ending(world, adult, mystery, magic)

    world.facts.update(
        detective=detective,
        helper=helper,
        adult=adult,
        mystery=mystery,
        magic=magic,
        response=response,
        solved=True,
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for mid in MYSTERIES:
        for magic in MAGICS:
            for resp in RESPONSES.values():
                if resp.sense >= 2:
                    combos.append((mid, magic, resp.id))
    return combos


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy mystery storyworld with binoculars and magic.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def explain_rejection(resp: Response) -> str:
    return f"(No story: response '{resp.id}' is too silly to solve a mystery well.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_rejection(RESPONSES[args.response]))
    combos = [c for c in valid_combos()
              if (args.mystery is None or c[0] == args.mystery)
              and (args.magic is None or c[1] == args.magic)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    mystery, magic, response = rng.choice(sorted(combos))
    d_gender = args.detective_gender or rng.choice(["girl", "boy"])
    h_gender = args.helper_gender or ("boy" if d_gender == "girl" else "girl")
    detective = args.detective or choose_name(rng, d_gender)
    helper = args.helper or choose_name(rng, h_gender)
    adult = args.adult or rng.choice(["mother", "father"])
    if helper == detective:
        helper = choose_name(rng, "boy" if d_gender == "girl" else "girl")
    return StoryParams(mystery, magic, response, detective, d_gender, helper, h_gender, adult)


def generate(params: StoryParams) -> StorySample:
    world = tell(MYSTERIES[params.mystery], MAGICS[params.magic], RESPONSES[params.response],
                 params.detective, params.detective_gender, params.helper, params.helper_gender, params.adult)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny mystery story for a young child that includes the word "binocular" and the word "fine".',
        f"Tell a comedy story where {f['detective'].id} uses a binocular to solve a silly mystery with a little magic.",
        f"Write a magical detective story that ends with the answer to a fine little clue.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    d, h, mystery, magic = f["detective"], f["helper"], f["mystery"], f["magic"]
    return [
        ("Who is the story about?",
         f"It is about {d.id} and {h.id}, who were trying to solve a silly mystery together. The grown-up was there too, ready to laugh when the answer appeared."),
        ("What did the detective use?",
         f"{d.id} used the binocular to look for clues. That helped {d.pronoun('subject')} notice the strange fine clue more carefully."),
        ("What turned out to be fine?",
         f"The clue was fine in the sense that it looked fancy and shiny, but it was also a joke-like clue. It led them to {mystery.reveal}."),
        ("How did they solve the mystery?",
         f"They looked carefully through the binocular and used {magic.label} to reveal the last clue. That combination was enough to turn confusion into an answer."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a binocular?",
         "A binocular is a tool for looking at faraway things. It makes clues and birds and rooftops easier to see."),
        ("What does fine mean?",
         "Fine can mean good or fancy, but it can also mean a small penalty. In this story it mostly means the clue looked fancy."),
        ("Why can magic be funny in a story?",
         "Magic can be funny when it makes a clue do something surprising instead of scary. Silly magic helps a mystery feel playful."),
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("missing_cookie", "whisper_bubble", "combination", "Mina", "girl", "Ollie", "boy", "mother"),
    StoryParams("sleepy_hat", "tickle_chalk", "peek", "Theo", "boy", "June", "girl", "father"),
    StoryParams("laughing_key", "moon_lens", "magic_guess", "Lola", "girl", "Finn", "boy", "mother"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for mg in MAGICS:
        lines.append(asp.fact("magic", mg))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(M, G, R) :- mystery(M), magic(G), sensible(R).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_sensible()) != {r.id for r in RESPONSES.values() if r.sense >= 2}:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        print("OK: smoke test and parity checks passed.")
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


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is binocular used for?",
         "A binocular is used for looking at things that are far away or hard to see. It helps a detective notice tiny clues."),
        ("Can magic help in a mystery story?",
         "Yes. Magic can reveal clues or make them easier to understand, which is handy in a mystery."),
        ("Why is the clue called fine?",
         "Because it looked fancy and neat, almost like it was dressed for a party. That made the story funny."),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for m, g, r in asp_valid_combos():
            print(f"  {m:16} {g:14} {r}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
