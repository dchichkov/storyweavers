#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/trump_maze_dialogue_flashback_whodunit.py
========================================================================

A standalone storyworld for a small whodunit set in a hedge maze.

Seed idea
---------
A child hears a loud "trump" sound, finds a maze puzzle in the garden, and then
has to solve a gentle whodunit using dialogue and a flashback. The world model
tracks who heard what, where clues were found, and which reveal explains the
mystery at the end.

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- imports shared results eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python validity checks plus an inline ASP twin
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
class Place:
    id: str
    label: str
    has_maze: bool = False
    has_echo: bool = False

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
    hidden_in: str
    clue_type: str
    noisy: bool = False

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
class Suspect:
    id: str
    label: str
    alibi: str
    tell: str

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
class Reveal:
    id: str
    truth: str
    explanation: str

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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["puzzle"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("")
    return out


def _r_recall(world: World) -> list[str]:
    out: list[str] = []
    detective = world.facts.get("detective")
    if not detective:
        return out
    det = world.get(detective)
    if det.meters["flashback"] < THRESHOLD or ("recall", det.id) in world.fired:
        return out
    world.fired.add(("recall", det.id))
    det.memes["certainty"] += 1
    out.append("__flashback__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("recall", "story", _r_recall)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s and not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_maze(place: Place) -> bool:
    return place.has_maze


def clue_is_plausible(clue: Clue) -> bool:
    return clue.noisy or clue.clue_type in {"sound", "footprint", "tool"}


def whodunit_possible(place: Place, clue: Clue, suspect: Suspect, reveal: Reveal) -> bool:
    return valid_maze(place) and clue_is_plausible(clue) and bool(reveal.truth)


def predict_flashback(world: World, detective_id: str) -> bool:
    sim = world.copy()
    sim.get(detective_id).meters["flashback"] += 1
    propagate(sim, narrate=False)
    return sim.get(detective_id).memes["certainty"] >= THRESHOLD


def scene_open(world: World, detective: Entity, friend: Entity, place: Place) -> None:
    world.say(
        f"On a windy afternoon, {detective.id} and {friend.id} wandered into "
        f"{place.label}. The hedges made a green maze, and every turn felt a little secret."
    )
    world.say(
        f'"Did you hear that trump?" {friend.id} whispered. "It sounded like a small trumpet somewhere in the maze."'
    )
    detective.memes["puzzle"] += 1


def clue_found(world: World, detective: Entity, clue: Clue) -> None:
    detective.meters["search"] += 1
    if clue.clue_type == "sound":
        world.say(
            f"{detective.id} paused by the little gate. " 
            f'"I heard that same trump sound earlier," {detective.id} said. '
            f'"It came from near the hedge by {clue.hidden_in}."'
        )
    else:
        world.say(
            f"{detective.id} bent down and found {clue.label} tucked in {clue.hidden_in}."
        )


def suspect_dialogue(world: World, suspect: Suspect, detective: Entity, friend: Entity) -> None:
    world.say(
        f'"{suspect.label}? Are you the one who made the noise?" {detective.id} asked.'
    )
    world.say(
        f'"No," {suspect.id} said. "{suspect.alibi}"'
    )
    if suspect.tell:
        world.say(f'"But look at your {suspect.tell}," {friend.id} said softly.')


def flashback(world: World, detective: Entity, clue: Clue, reveal: Reveal) -> None:
    detective.meters["flashback"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {detective.id} remembered something: earlier, the same trump sound had bounced off the stone path."
    )
    world.say(
        f"In the flashback, {detective.id} had seen {clue.label} near the maze wall, and the clue made sense at last."
    )
    detective.memes["certainty"] += 1
    world.facts["flashback_used"] = True


def reveal_mystery(world: World, detective: Entity, friend: Entity, suspect: Suspect, reveal: Reveal) -> None:
    world.say(
        f'"It was not {suspect.label}," {detective.id} said. "{reveal.truth}"'
    )
    world.say(
        f'"{reveal.explanation}" {friend.id} said. "That is why the trump sound led us to the answer."'
    )
    detective.memes["joy"] += 1
    friend.memes["joy"] += 1


def ending_image(world: World, place: Place) -> None:
    world.say(
        f"By sunset, the maze was quiet again, and the children walked out holding the clue in their hands, smiling at how the secret had been solved."
    )


PLACES = {
    "maze_garden": Place("maze_garden", "the garden maze", has_maze=True, has_echo=True),
    "museum_maze": Place("museum_maze", "the old museum maze", has_maze=True, has_echo=True),
    "corn_maze": Place("corn_maze", "the corn maze", has_maze=True, has_echo=False),
}

CLUES = {
    "brass_note": Clue("brass_note", "a tiny brass note", "a fern", "sound", noisy=True),
    "mud_print": Clue("mud_print", "muddy prints", "the gate", "footprint"),
    "ribbon": Clue("ribbon", "a red ribbon", "a hedgeside branch", "tool"),
}

SUSPECTS = {
    "gardener": Suspect("gardener", "the gardener", "I was trimming the hedges all afternoon.", "boots"),
    "musician": Suspect("musician", "the music teacher", "I was in the hall with my class.", "coat"),
    "brother": Suspect("brother", "my big brother", "I was at home all morning.", "sleeves"),
}

REVEALS = {
    "trumpet_toy": Reveal("trumpet_toy", "the trump sound came from a toy trumpet", "A toy trumpet can make a loud trump sound when someone blows it."),
    "wind_pipe": Reveal("wind_pipe", "the trump sound came from a loose hollow pipe in the hedge", "The wind blew through the pipe and made the same sound."),
    "garden_game": Reveal("garden_game", "the trump sound came from a hidden clue in the maze game", "The maze game had a brass token that clinked when it was tapped."),
}

GIRL_NAMES = ["Maya", "Lina", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Theo", "Ben", "Max", "Leo", "Finn", "Owen"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES.values():
        for c in CLUES.values():
            for s in SUSPECTS.values():
                for r in REVEALS.values():
                    if whodunit_possible(p, c, s, r):
                        combos.append((p.id, c.id, s.id, r.id))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    clue: str
    suspect: str
    reveal: str
    detective: str
    detective_gender: str
    friend: str
    friend_gender: str
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
    ap = argparse.ArgumentParser(description="A small whodunit in a maze, with dialogue and a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.suspect is None or c[2] == args.suspect)
              and (args.reveal is None or c[3] == args.reveal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, suspect, reveal = rng.choice(sorted(combos))
    dgender = args.detective_gender or rng.choice(["girl", "boy"])
    fg = args.friend_gender or ("boy" if dgender == "girl" else "girl")
    detective = args.detective or rng.choice(GIRL_NAMES if dgender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (BOY_NAMES if fg == "boy" else GIRL_NAMES) if n != detective])
    return StoryParams(place, clue, suspect, reveal, detective, dgender, friend, fg)


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    suspect = SUSPECTS[params.suspect]
    reveal = REVEALS[params.reveal]
    det = world.add(Entity(id=params.detective, kind="character", type=params.detective_gender, role="detective"))
    fri = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender, role="friend"))
    world.facts.update(place=place, clue=clue, suspect=suspect, reveal=reveal, detective=det.id, friend=fri.id)

    scene_open(world, det, fri, place)
    world.para()
    clue_found(world, det, clue)
    suspect_dialogue(world, suspect, det, fri)

    world.para()
    if predict_flashback(world, det.id):
        flashback(world, det, clue, reveal)
    else:
        det.meters["flashback"] += 1
        world.say(f"{det.id} frowned, then remembered a small detail from before.")
        world.say(f'"Wait," {det.id} said. "{reveal.truth}"')
        det.memes["certainty"] += 1

    world.para()
    reveal_mystery(world, det, fri, suspect, reveal)
    ending_image(world, place)
    world.facts["done"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit for a 3-to-5-year-old set in {f["place"].label} that includes the word "trump".',
        f"Tell a child detective story where {f['detective']} follows a clue through a maze and uses dialogue to solve the mystery.",
        f"Write a gentle mystery with a flashback that explains who made the trump sound in the maze.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    fri = f["friend"]
    clue = f["clue"]
    suspect = f["suspect"]
    reveal = f["reveal"]
    return [
        QAItem(
            question=f"What mystery did {det} and {fri} have to solve?",
            answer=f"They had to find out who made the trump sound in the maze. The clue they found helped point the way."
        ),
        QAItem(
            question=f"How did {det} solve the mystery?",
            answer=f"{det} listened to the dialogue, remembered a flashback, and matched the clue to the truth. That made the answer clear without guessing."
        ),
        QAItem(
            question=f"Was it {suspect.label}?",
            answer=f"No, it was not {suspect.label}. {reveal.truth.capitalize()}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a maze?",
            answer="A maze is a place with twisting paths and dead ends. You follow clues and turns until you find the way out."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a memory scene that shows something from earlier. It helps explain why the answer makes sense."
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters talk to each other in the story. It helps readers hear their questions and clues."
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
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("maze_garden", "brass_note", "gardener", "wind_pipe", "Mia", "girl", "Theo", "boy"),
    StoryParams("museum_maze", "mud_print", "musician", "trumpet_toy", "Owen", "boy", "Lina", "girl"),
    StoryParams("corn_maze", "ribbon", "brother", "garden_game", "Ava", "girl", "Ben", "boy"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_type", cid, c.clue_type))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for rid in REVEALS:
        lines.append(asp.fact("reveal", rid))
    lines.append(asp.fact("maze_place", "maze_garden"))
    lines.append(asp.fact("maze_place", "museum_maze"))
    lines.append(asp.fact("maze_place", "corn_maze"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, C, S, R) :- place(P), clue(C), suspect(S), reveal(R), maze_place(P), clue_type(C, T), good_clue(T).
good_clue(sound).
good_clue(footprint).
good_clue(tool).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combinations.")
        rc = 1
    else:
        print(f"OK: ASP and Python agree on {len(valid_combos())} combinations.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, clue=None, suspect=None, reveal=None, detective=None, detective_gender=None, friend=None, friend_gender=None), random.Random(0)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as ex:
        print(f"SMOKE TEST FAILED: {ex}")
        return 1
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit in a maze with dialogue and flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective} in {p.place} ({p.clue}, {p.suspect}, {p.reveal})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
