#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/heist_previous_curiosity_rhyming_story.py
=========================================================================

A standalone story world for a tiny, child-facing rhyming tale about curiosity:
a child notices a closed room, remembers a previous clue, sneaks in for a tiny
"heist" of a missing ribbon, gets caught, tells the truth, and then helps put
everything right. The domain is built as a small simulation with typed entities,
physical meters, emotional memes, a simple causal engine, an ASP twin, and
grounded QA.

The story tone is light, rhythmic, and rhyme-friendly, but the world model still
drives the turn: curiosity increases, a risky choice is made, a grown-up notices,
and the ending proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/heist_previous_curiosity_rhyming_story.py
    python storyworlds/worlds/gpt-5.4-mini/heist_previous_curiosity_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/heist_previous_curiosity_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/heist_previous_curiosity_rhyming_story.py --trace
    python storyworlds/worlds/gpt-5.4-mini/heist_previous_curiosity_rhyming_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
class Setting:
    id: str
    place: str
    sound: str
    rhyme: str
    previous: str
    hidden: str
    can_heist: bool = True

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
class Prize:
    id: str
    label: str
    phrase: str
    owner: str
    hidden_in: str
    easy_to_spot: bool = True

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
    power: int
    sense: int
    text: str
    fail: str
    qa_text: str

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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("child")
    if kid.memes["curiosity"] < 2 or ("curious", "turn") in world.fired:
        return out
    world.fired.add(("curious", "turn"))
    kid.memes["bravery"] += 1
    out.append("__curious__")
    return out


CAUSAL_RULES = [Rule("curiosity", "social", _r_curiosity)]


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


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} and {b}"


def predict_heist(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.memes["curiosity"] += 2
    child.meters["sneak"] += 1
    sim.get("room").meters["touched"] += 1
    return {
        "noticed": sim.get("grownup").meters["alert"] >= THRESHOLD,
        "found": True,
    }


def build_setup(world: World, setting: Setting, prize: Prize) -> None:
    child = world.get("child")
    grownup = world.get("grownup")
    child.memes["joy"] += 1
    world.say(
        f"In a cozy nook by {setting.place}, a child felt a curious croon. "
        f"The air was light, the night was bright, and the room hummed like a tune."
    )
    world.say(
        f"{child.id} remembered {setting.previous}, a clue from a day before. "
        f"It hinted where {prize.label} might wait, behind a half-shut door."
    )
    grownup.memes["care"] += 1
    world.say(
        f"{grownup.label_word.capitalize()} smiled and tidied, neat and mild, with "
        f"{setting.sound} in the air."
    )


def tempt(world: World, prize: Prize) -> None:
    child = world.get("child")
    child.memes["curiosity"] += 2
    world.say(
        f"{child.id} peered at the door with shining eyes. "
        f'"What could be there? I must take a peek," {child.pronoun()} said.'
    )
    world.say(
        f"The thought was a little heist of sorts, a secret, sneaky spree -- "
        f"not for keep, but just to seek what curiosity could see."
    )


def warn(world: World, prize: Prize) -> None:
    child = world.get("child")
    grownup = world.get("grownup")
    pred = predict_heist(world)
    child.memes["warning"] += 1
    world.facts["predicted_notice"] = pred["noticed"]
    world.say(
        f'{grownup.label_word.capitalize()} called, "Dear {child.id}, please be wise. '
        f"Don't grab what's hidden out of sight; ask first, and keep things right."
    )


def do_heist(world: World, prize: Prize) -> None:
    child = world.get("child")
    child.meters["sneak"] += 1
    child.meters["stolen"] += 1
    world.get("room").meters["moved"] += 1
    world.say(
        f"{child.id} slipped inside with tiptoe pride and found {prize.phrase}. "
        f"For one small blink it felt like gold, a tiny, thrilling chance."
    )


def caught(world: World, prize: Prize) -> None:
    grownup = world.get("grownup")
    child = world.get("child")
    grownup.meters["alert"] += 1
    child.memes["guilt"] += 1
    world.say(
        f'But then {grownup.id} saw the trail and said, "{child.id}, come here, my dear." '
        f"The room went still; the hush was clear; the secret seemed too near."
    )


def confess(world: World, prize: Prize) -> None:
    child = world.get("child")
    grownup = world.get("grownup")
    child.memes["honesty"] += 1
    child.meters["stolen"] = 0
    world.say(
        f'{child.id} looked down low and spoke, "I made a tiny heist. '
        f"I used the previous clue, but I know I should have asked."
    )
    world.say(
        f"{grownup.label_word.capitalize()} knelt and nodded, calm and warm. "
        f'"Thank you for telling me the truth. Let’s set this right."'
    )


def repair(world: World, prize: Prize) -> None:
    child = world.get("child")
    grownup = world.get("grownup")
    child.memes["relief"] += 1
    child.memes["love"] += 1
    world.say(
        f"Together they set {prize.label} back where it belonged, all snug and neat. "
        f"The child then helped restore the shelf, and swept the tiny feet."
    )
    world.say(
        f"By the end, the heist was just a lesson bright: curiosity can knock, "
        f"but truth can make it right."
    )


def tell(setting: Setting, prize: Prize, response: Response) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type="girl", label="the child", role="curious"))
    grownup = world.add(Entity(id="grownup", kind="character", type="mother", label="mom", role="guardian"))
    room = world.add(Entity(id="room", type="room", label="the room"))
    world.add(Entity(id="prize", type="thing", label=prize.label))
    child.memes["curiosity"] = 2.0
    child.memes["joy"] = 1.0
    grownup.meters["alert"] = 0.0

    build_setup(world, setting, prize)
    world.para()
    tempt(world, prize)
    warn(world, prize)
    do_heist(world, prize)
    caught(world, prize)
    world.para()
    confess(world, prize)
    repair(world, prize)

    world.facts.update(
        setting=setting,
        prize=prize,
        response=response,
        child=child,
        grownup=grownup,
        room=room,
        outcome="truth",
    )
    return world


SETTINGS = {
    "attic": Setting(
        "attic", "the attic", "soft creak", "peek and seek",
        "a previous note on the stairs", "under a blue cloth", True,
    ),
    "closet": Setting(
        "closet", "the closet", "tiny tap", "hide and slide",
        "a previous whisper in the hall", "behind a stack of hats", True,
    ),
    "porch": Setting(
        "porch", "the porch", "wind hum", "glow and show",
        "a previous clue from the drawer", "inside a wicker box", True,
    ),
}

PRIZES = {
    "ribbon": Prize("ribbon", "a red ribbon", "a red ribbon", "mom", "under the cloth"),
    "marble": Prize("marble", "a shiny marble", "a shiny marble", "dad", "under the cloth"),
    "cookie": Prize("cookie", "a cookie in a tin", "a cookie in a tin", "mom", "inside a tin"),
}

RESPONSES = {
    "apology": Response("apology", 3, 3, "apologized, returned the prize, and helped tidy the room",
                        "tried to hide the prize, but the secret grew too big", "apologized and helped tidy"),
    "ask": Response("ask", 2, 3, "asked first, returned the prize, and helped tidy the room",
                    "kept the secret, and the room stayed upset", "asked first and helped tidy"),
}

GIRL_NAMES = ["Mia", "Luna", "Zoe", "Ava", "Nora", "Ivy"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Finn", "Leo", "Max"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        if not setting.can_heist:
            continue
        for pid in PRIZES:
            combos.append((sid, pid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    prize: str
    name: str
    gender: str
    response: str
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


KNOWLEDGE = {
    "curiosity": [("What is curiosity?",
                   "Curiosity is the feeling that makes you want to look, learn, and ask questions.")],
    "heist": [("What is a heist?",
               "A heist is a secret taking of something that does not belong to you. In this story it is small and mistaken, not a big crime tale.")],
    "ask": [("Why is it better to ask first?",
             "Asking first is kind and honest. It helps people trust you and keeps surprises from turning into trouble.")],
    "truth": [("Why does telling the truth help?",
               "Telling the truth helps fix mistakes. It lets grown-ups help and makes it easier to make things right.")],
    "previous": [("What does previous mean?",
                  "Previous means before this one, or earlier than now.")],
}
KNOWLEDGE_ORDER = ["curiosity", "heist", "previous", "ask", "truth"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s, p = f["setting"], f["prize"]
    return [
        f'Write a rhyming story for a preschooler about curiosity, a previous clue, '
        f'and a tiny heist involving {p.label}. Include the word "heist".',
        f"Tell a gentle rhyming story where {f['child'].id} sees a previous hint, "
        f"tries a small heist, then tells the truth and fixes it.",
        f'Write a short rhyme about a curious child, a hidden prize, and the word "previous".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, grownup, prize, setting = f["child"], f["grownup"], f["prize"], f["setting"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, a curious child, and {grownup.label_word}, who helps make things right."),
        ("What did the child remember?",
         f"{child.id} remembered {setting.previous}. That clue made {child.pronoun()} curious enough to go look."),
        ("What did the child take?",
         f"{child.id} took {prize.label} during a small heist, but then returned it after telling the truth."),
        ("How did the story end?",
         f"It ended with the prize back in place, the room tidy, and {child.id} feeling relieved because honesty fixed the mistake."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"curiosity", "heist", "previous", "truth", "ask"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("attic", "ribbon", "Mia", "girl", "apology"),
    StoryParams("closet", "marble", "Noah", "boy", "ask"),
    StoryParams("porch", "cookie", "Zoe", "girl", "apology"),
]


def explain_rejection(setting: Setting, prize: Prize) -> str:
    if not setting.can_heist:
        return "(No story: this setting does not support the little heist premise.)"
    return "(No story: this combination is not reasonable.)"


def valid_story_combos() -> list[tuple[str, str]]:
    return valid_combos()


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("previous", sid, s.previous.replace(" ", "_")))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for rid in RESPONSES:
        lines.append(asp.fact("response", rid))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P) :- setting(S), prize(P).
sensible(R) :- response(R).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    if set(asp_sensible()) == set(RESPONSES):
        print("OK: ASP sensible matches responses.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, prize=None, name=None, gender=None, response=None, seed=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming curiosity heist story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if args.setting and args.prize:
        if (args.setting, args.prize) not in valid_combos():
            raise StoryError(explain_rejection(SETTINGS[args.setting], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if args.setting is None or c[0] == args.setting
              and args.prize is None or c[1] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    response = args.response or rng.choice(sorted(RESPONSES))
    return StoryParams(setting, prize, name, gender, response)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PRIZES[params.prize], RESPONSES[params.response])
    world.get("child").id = params.name
    world.get("child").type = params.gender
    world.get("grownup").label = "mom" if params.gender == "girl" else "dad"
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program(show="#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
