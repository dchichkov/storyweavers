#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/toot_mystery_to_solve_myth.py
=============================================================

A standalone storyworld for a tiny mythic mystery: a village hears a strange
"toot", wonders where it came from, follows clues, and discovers the cause.
The world keeps the simulation small and state-driven: sound travels, characters
gain fear/curiosity/calm, clues accumulate, and the ending proves the mystery
was solved.

The story is intentionally myth-flavored: a torchlit hall, an old hill, a bronze
horn, a river spirit, and a gentle reveal that turns unease into wonder.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "priestess"}
        male = {"boy", "father", "dad", "man", "king", "priest"}
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    sky: str
    mood: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    sound: str
    source_hint: str
    clue: str
    reveal: str
    answer: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
        return c


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for ent in list(world.entities.values()):
            if ent.meters["mystery"] < THRESHOLD:
                continue
            sig = ("settle", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            if ent.role == "leader":
                ent.memes["resolve"] += 1
            out.append("")
            changed = True
    if narrate:
        for s in out:
            if s:
                world.say(s)
    return out


def mystery_at_risk(m: Mystery) -> bool:
    return bool(m.sound)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def clue_predict(world: World, mystery: Mystery) -> dict:
    sim = world.copy()
    sim.get("mystery").meters["heard"] += 1
    sim.get("seer").memes["curiosity"] += 1
    return {
        "heard": sim.get("mystery").meters["heard"] >= THRESHOLD,
        "fear": max((e.memes["fear"] for e in sim.characters()), default=0.0),
    }


def awaken(world: World, seer: Entity, companion: Entity, setting: Setting) -> None:
    seer.memes["curiosity"] += 1
    companion.memes["curiosity"] += 1
    world.say(
        f"At {setting.place}, under a {setting.sky}, {seer.id} and {companion.id} "
        f"kept watch beside the fire."
    )
    world.say(
        f"The old stories said the hill could whisper, and the air felt full of {setting.mood}."
    )


def toot(world: World, mystery: Mystery, seer: Entity, companion: Entity) -> None:
    mystery_ent = world.get("mystery")
    mystery_ent.meters["heard"] += 1
    seer.memes["fear"] += 1
    companion.memes["fear"] += 1
    world.say(f"Then came a sudden toot from the dark hill.")
    world.say(
        f"{seer.id} froze. {companion.id} listened hard, because the sound did not come twice."
    )


def seek_clue(world: World, seer: Entity, companion: Entity, mystery: Mystery) -> None:
    seer.memes["resolve"] += 1
    companion.memes["resolve"] += 1
    world.say(
        f"{seer.id} picked up a lamp and {companion.id} followed the trail toward the hill."
    )
    world.say(
        f"Along the grass they found {mystery.clue}, and it made the mystery feel smaller."
    )


def warn(world: World, seer: Entity, companion: Entity, mystery: Mystery, parent: Entity) -> None:
    pred = clue_predict(world, mystery)
    companion.memes["warning"] += 1
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'"That toot is not the wind," {companion.id} said. '
        f'"We should tell {parent.label_word} and look together."'
    )


def solve(world: World, seer: Entity, companion: Entity, mystery: Mystery, response: Response) -> None:
    answer = mystery.answer
    world.get("mystery").meters["solved"] += 1
    world.get("mystery").meters["heard"] = 0
    seer.memes["fear"] = 0
    companion.memes["fear"] = 0
    seer.memes["joy"] += 1
    companion.memes["joy"] += 1
    world.say(
        f"At the top of the hill, they found {answer}. It gave one last toot when the wind touched it."
    )
    world.say(
        f"{response.text}. At last the strange sound had a name, and the night felt friendly again."
    )


def celebrate(world: World, seer: Entity, companion: Entity, setting: Setting) -> None:
    world.say(
        f"Back at {setting.place}, {seer.id} and {companion.id} laughed by the fire."
    )
    world.say(
        "The mystery was solved, and the little village slept with the hill no longer afraid."
    )


SETTINGS = {
    "village": Setting("village", "the village square", "moonlight", "quiet worry"),
    "temple": Setting("temple", "the old temple steps", "starlight", "ancient hush"),
    "harbor": Setting("harbor", "the harbor wall", "salt wind", "restless wonder"),
}

MYSTERIES = {
    "horn": Mystery(
        "horn",
        "toot",
        "a bronze horn leaning in the reeds",
        "a line of wet footprints beside the reeds",
        "a bronze horn was caught in the roots",
        "a bronze horn",
        tags={"toot", "horn"},
    ),
    "goat": Mystery(
        "goat",
        "toot",
        "a small goat with a crooked bell",
        "a tuft of white fur on the hill path",
        "a little goat was nibbling a reed flute",
        "a little goat",
        tags={"toot", "goat"},
    ),
    "pipe": Mystery(
        "pipe",
        "toot",
        "a reed pipe tied with blue thread",
        "blue thread snagged on a thorn bush",
        "a reed pipe had slipped from a shepherd's pouch",
        "a reed pipe",
        tags={"toot", "pipe"},
    ),
}

RESPONSES = {
    "find": Response("find", 3,
                     "they carried the horn gently down the hill",
                     "they searched too late, and the wind kept fooling them",
                     "they carried it home and wrapped it in cloth",
                     tags={"answer", "careful"}),
    "name": Response("name", 2,
                     "they laughed because the mystery was only a lost thing",
                     "they guessed bravely, but the sound stayed strange",
                     "they named the thing and smiled at the clever trick",
                     tags={"answer"}),
    "share": Response("share", 2,
                      "they told the elders, who nodded and listened",
                      "they rushed alone and learned nothing new",
                      "they told the elders, who knew the old story at once",
                      tags={"answer", "elders"}),
}

SEER_NAMES = ["Ari", "Mira", "Niko", "Lina", "Tavi", "Sera"]
COMPANION_NAMES = ["Bren", "Kio", "Nia", "Oren", "Pia", "Rumi"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    response: str
    seer: str
    companion: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        for m in MYSTERIES:
            if mystery_at_risk(MYSTERIES[m]):
                for r in RESPONSES:
                    if RESPONSES[r].sense >= SENSE_MIN:
                        combos.append((s, m, r))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic mystery world built around a strange toot.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--seer")
    ap.add_argument("--companion")
    ap.add_argument("--parent", choices=["mother", "father", "elder", "priestess"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m, mv in MYSTERIES.items():
        lines.append(asp.fact("mystery", m))
        lines.append(asp.fact("sound", m, mv.sound))
    for r, rv in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, rv.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S, M, R) :- setting(S), mystery(M), response(R), sensible(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(v[0] for v in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos")
    if set(asp_sensible()) != {r for r, rv in RESPONSES.items() if rv.sense >= SENSE_MIN}:
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as e:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("That response is too weak for a mythic mystery.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, response = rng.choice(sorted(combos))
    seer = args.seer or rng.choice(SEER_NAMES)
    companion = args.companion or rng.choice([n for n in COMPANION_NAMES if n != seer])
    parent = args.parent or rng.choice(["elder", "mother", "priestess"])
    return StoryParams(setting, mystery, response, seer, companion, parent)


def tell(params: StoryParams) -> World:
    w = World()
    seer = w.add(Entity(id=params.seer, kind="character", type="girl"))
    companion = w.add(Entity(id=params.companion, kind="character", type="boy"))
    parent = w.add(Entity(id="Parent", kind="character", type=params.parent, label="the elder"))
    mystery = w.add(Entity(id="mystery", type="mystery"))
    setting = SETTINGS[params.setting]
    mv = MYSTERIES[params.mystery]
    resp = RESPONSES[params.response]

    awaken(w, seer, companion, setting)
    w.para()
    toot(w, mv, seer, companion)
    warn(w, seer, companion, mv, parent)
    seek_clue(w, seer, companion, mv)
    w.para()
    solve(w, seer, companion, mv, resp)
    celebrate(w, seer, companion, setting)

    w.facts.update(setting=setting, mystery=mv, response=resp, seer=seer,
                   companion=companion, parent=parent, outcome="solved")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic mystery story for a young child that includes the word "{f["mystery"].sound}".',
        f"Tell a gentle legend where {f['seer'].id} and {f['companion'].id} follow a strange sound and solve the mystery.",
        "Write a short story with a puzzle, a clue, and a calm ending in an old, legendary place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mv = f["mystery"]
    return [
        QAItem("What strange sound did they hear?",
               f"They heard a {mv.sound}. It came from the mystery thing on the hill."),
        QAItem("How did they solve the mystery?",
               f"They followed the clue, found {mv.answer}, and told the elders. That is how the strange toot was explained."),
        QAItem("How did the story end?",
               "It ended calmly, with the mystery solved and the village feeling safe again."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a mystery?",
               "A mystery is something you do not understand at first. You solve it by looking for clues and putting the clues together."),
        QAItem("What does the word toot mean here?",
               "Toot is a short horn-like sound. In this story it is the strange noise that starts the mystery."),
        QAItem("Why do clues matter?",
               "Clues matter because they help you figure out what is really happening. A good clue can turn a puzzling sound into an answer."),
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("village", "horn", "find", "Ari", "Bren", "elder"),
    StoryParams("temple", "goat", "share", "Mira", "Nia", "priestess"),
    StoryParams("harbor", "pipe", "name", "Tavi", "Rumi", "mother"),
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
        print(asp_program("#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for s, m, r in asp_valid_combos():
            print(f"{s:8} {m:8} {r}")
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
