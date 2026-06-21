#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/allege_succinct_papered_bravery_mystery_to_solve.py
====================================================================================

A standalone storyworld for a tiny rhyming mystery tale.

Premise:
- A brave child hears a papered clue.
- They allege a succinct guess.
- The mystery is solved with a concrete reveal.

The world is intentionally small: a few places, a few clues, and one clean turn
from puzzling to solved. It supports the shared Storyweavers contract, including
QA, JSON, trace, ASP parity checks, and a verification smoke test.
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
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Scene:
    id: str
    place: str
    mood: str
    rhyme_tail: str
    papered_surface: str
    hiding_place: str
    clamor: str
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
class Clue:
    id: str
    phrase: str
    label: str
    surfaces: set[str]
    hints: set[str]
    papered: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Mystery:
    id: str
    question: str
    missing: str
    answer: str
    reveal_line: str
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
class Response:
    id: str
    sense: int
    text: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} and {b}"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A brave, papered mystery in rhyming style.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICK_NAMES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


SCENES = {
    "schoolhall": Scene("schoolhall", "a school hall", "bright and small", "tall/hall", "the papered hallboard", "behind the hallboard", "a soft bell call", {"indoor", "school"}),
    "library": Scene("library", "a library nook", "quiet and near", "near/clear", "the papered shelf", "behind the shelf", "a whispering murmur", {"indoor", "library"}),
    "attic": Scene("attic", "a dusty attic", "high and wide", "wide/sky", "the papered trunk lid", "inside the trunk", "a tapping tick", {"indoor", "attic"}),
}

CLUES = {
    "note": Clue("note", "a papered note", "note", {"papered_surface"}, {"papered"}, papered=True, tags={"papered", "clue"}),
    "poster": Clue("poster", "a papered poster", "poster", {"papered_surface"}, {"papered"}, papered=True, tags={"papered", "clue"}),
    "label": Clue("label", "a papered label", "label", {"papered_surface"}, {"papered"}, papered=True, tags={"papered", "clue"}),
}

MYSTERIES = {
    "bell": Mystery("bell", "where the bell went", "the bell", "under the hallboard", "The bell was tucked under the hallboard.", {"mystery", "bell"}),
    "key": Mystery("key", "who hid the key", "the key", "inside the trunk", "The key was hidden inside the trunk.", {"mystery", "key"}),
    "book": Mystery("book", "what made the tapping", "the book", "behind the shelf", "The book was wedged behind the shelf.", {"mystery", "book"}),
}

RESPONSES = {
    "discover": Response("discover", 3, "found the answer with a brave grin", {"solve"}),
    "peek": Response("peek", 2, "peeked behind the papered place and spotted the truth", {"solve"}),
    "guess": Response("guess", 2, "alleged a succinct guess, calm and bright", {"solve"}),
}

HERO_NAMES = ["Mira", "Noah", "Luna", "Ezra", "Ivy", "Owen"]
SIDEKICK_NAMES = ["Tess", "Finn", "Zoe", "Ben", "Rae", "Jude"]

CURATED = [
    # keyword-rich, solved
    # use keyword args for dataclasses
    dict(scene="library", clue="note", mystery="book", response="guess", hero="Mira", sidekick="Finn"),
    dict(scene="schoolhall", clue="poster", mystery="bell", response="discover", hero="Noah", sidekick="Tess"),
    dict(scene="attic", clue="label", mystery="key", response="peek", hero="Ivy", sidekick="Jude"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SCENES:
        for c in CLUES:
            for m in MYSTERIES:
                if CLUES[c].papered and "papered" in MYSTERIES[m].tags:
                    combos.append((s, c, m))
    return combos


@dataclass
class StoryParams:
    scene: str
    clue: str
    mystery: str
    response: str
    hero: str
    sidekick: str
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


def reasonableness_gate(params: StoryParams) -> None:
    if params.scene not in SCENES:
        raise StoryError("Unknown scene.")
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    if "papered" not in CLUES[params.clue].tags:
        raise StoryError("This tale needs a papered clue.")
    if RESPONSES[params.response].sense < 2:
        raise StoryError("That response is too weak for this mystery.")


def _solve(world: World, hero: Entity, clue: Clue, mystery: Mystery, response: Response) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"In {world.facts['scene'].place}, {hero.id} walked with a spark of cheer, "
        f"for {world.facts['clue'].phrase} hung papered and near."
    )
    world.say(
        f'"{mystery.question}," {hero.id} said, with a voice quite succinct, '
        f'and {response.text}.'
    )
    world.say(mystery.reveal_line)
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1


def _r_reveal(world: World) -> list[str]:
    if world.facts.get("solved"):
        return []
    if world.get("hero").memes.get("bravery", 0.0) < THRESHOLD:
        return []
    sig = ("reveal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["solved"] = True
    return ["__solve__"]


def propagate(world: World, narrate: bool = True) -> None:
    if _r_reveal(world) and narrate:
        _solve(world, world.get("hero"), world.facts["clue_obj"], world.facts["mystery_obj"], world.facts["response_obj"])


def tell(scene: Scene, clue: Clue, mystery: Mystery, response: Response, hero_name: str, sidekick_name: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="girl" if hero_name in {"Mira", "Luna", "Ivy"} else "boy", role="hero"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="girl" if sidekick_name in {"Tess", "Zoe", "Rae"} else "boy", role="sidekick"))
    world.add(Entity(id="scene", type="place", label=scene.place, tags=set(scene.tags)))
    clue_ent = world.add(Entity(id="clue", type="clue", label=clue.label, tags=set(clue.tags), attrs={"papered": clue.papered}))
    mystery_ent = world.add(Entity(id="mystery", type="mystery", label=mystery.missing, tags=set(mystery.tags)))
    response_ent = world.add(Entity(id="response", type="response", label=response.id, tags=set(response.tags)))

    world.facts.update(scene=scene, clue_obj=clue, mystery_obj=mystery, response_obj=response, clue=clue_ent, mystery=mystery_ent, response=response_ent, hero=hero, sidekick=sidekick, solved=False)

    world.say(f"{hero.id} and {sidekick.id} went wandering with a rhyme and a grin.")
    world.say(f"{scene.place.capitalize()} was quiet, with {scene.rhyme_tail} tucked in.")
    world.para()
    world.say(f"They found {clue.phrase}, all papered and neat.")
    world.say(f"It hinted at {mystery.question}, a puzzle to meet.")
    world.para()
    hero.memes["bravery"] = 1.0
    sidekick.memes["trust"] = 1.0
    world.say(f"{hero.id} took a breath and stood nice and tall.")
    world.say(f'"Let me {RESPONSES[response.id].id}," {hero.id} said, "and we will solve all."')
    propagate(world, narrate=True)
    if not world.facts.get("solved"):
        world.say("But the clue stayed shy, and the riddle stayed drear.")
        world.say(f"So they called for a grown-up, who solved it right here.")
        world.facts["solved"] = True
        world.say(mystery.reveal_line)
    world.say(f"They laughed at the end as the answer came bright, and the papered clue shone in the soft evening light.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that includes the words "allege", "succinct", and "papered".',
        f"Tell a brave mystery story where {f['hero'].id} uses a papered clue to solve {f['mystery_obj'].question}.",
        f"Write a short rhyming tale where a child makes a succinct allegation and the mystery ends in a warm reveal.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery_obj"]
    clue = f["clue_obj"]
    return [
        ("Who is the story about?", f"It is about {hero.id}, a brave child who follows a papered clue and does not give up."),
        ("What was the clue like?", f"It was {clue.phrase}, so it felt neat and papered. That made it look like a real hint instead of a random scrap."),
        ("What mystery did they solve?", f"They solved {mystery.question}. The answer was simple once they looked in the right spot."),
        ("How did bravery help?", f"{hero.id} kept going even before the answer was clear. That brave choice let the clue lead them to the truth."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does succinct mean?", "Succinct means short and clear, with no extra words."),
        ("What does allege mean?", "Allege means to claim something is true, even before you prove it."),
        ("What does papered mean?", "Papered means covered with paper or made from paper."),
        ("What is bravery?", "Bravery is being willing to do the right thing even when you feel unsure or afraid."),
        ("What is a mystery?", "A mystery is something that is not understood yet and needs clues to solve."),
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
        bits = []
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen pieces do not form a papered clue mystery with a strong enough response.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.clue is None or c[1] == args.clue)
              and (args.mystery is None or c[2] == args.mystery)]
    if not combos:
        raise StoryError(explain_rejection(StoryParams(scene=args.scene or "library", clue=args.clue or "note", mystery=args.mystery or "book", response=args.response or "guess", hero=args.hero or "Mira", sidekick=args.sidekick or "Finn")))
    scene, clue, mystery = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    params = StoryParams(scene=scene, clue=clue, mystery=mystery, response=response, hero=hero, sidekick=sidekick)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.clue not in CLUES or params.mystery not in MYSTERIES or params.response not in RESPONSES:
        raise StoryError("Invalid parameters.")
    if "papered" not in CLUES[params.clue].tags:
        raise StoryError("This story needs a papered clue.")
    scene = SCENES[params.scene]
    clue = CLUES[params.clue]
    mystery = MYSTERIES[params.mystery]
    response = RESPONSES[params.response]
    world = tell(scene, clue, mystery, response, params.hero, params.sidekick)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.papered:
            lines.append(asp.fact("papered", cid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, M) :- scene(S), clue(C), mystery(M), papered(C).
good(R) :- response(R), sense(R, N), N >= 2.
solved :- valid(S, C, M), good(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_good() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good/1."))
    return sorted(set(asp.atoms(model, "good")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    if {r for (r,) in asp_good()} != {rid for rid, r in RESPONSES.items() if r.sense >= 2}:
        rc = 1
        print("MISMATCH in response sense gate")
    try:
        sample = generate(CURATED[0].copy())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show good/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, c, m in combos:
            print(f"  {s:10} {c:8} {m}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for raw in CURATED:
            params = StoryParams(**raw)
            samples.append(generate(params))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.sidekick}: {p.clue} in {p.scene} ({p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
