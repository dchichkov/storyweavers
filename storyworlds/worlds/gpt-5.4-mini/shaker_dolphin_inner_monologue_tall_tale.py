#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/shaker_dolphin_inner_monologue_tall_tale.py
============================================================================

A standalone story world for a tall-tale, inner-monologue story about a child,
a shaker, and a dolphin. The world is small on purpose: one seaside stage, one
attention-seeking shaker, one impossible dolphin, and one sensible turn where the
character realizes the best way to help the dolphin is to calm down and listen.

The domain supports a few close, constraint-checked variations:
- a child wants to show a shiny shaker to a dolphin from the dock or shore;
- the shaker's rattling spooks the dolphin or makes it hesitate;
- an inner monologue helps the child notice the problem and choose a gentler act;
- the ending proves the change with a bright, peaceful image.

Tall-tale flavor is preserved through exaggeration and wonder, but the state model
still drives every story beat.
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
    image: str
    wind: str
    water: str

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
class Shaker:
    id: str
    label: str
    glitter: str
    rattle: str
    calm: str
    loud: bool = True

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
class Dolphin:
    id: str
    label: str
    scene: str
    splash: str
    mood: str
    shy: bool = False

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_spook(world: World) -> list[str]:
    out = []
    child = world.get("child")
    dolphin = world.get("dolphin")
    shaker = world.get("shaker")
    if shaker.meters["rattling"] < THRESHOLD:
        return out
    sig = ("spook",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    dolphin.memes["unease"] += 1
    child.memes["worry"] += 1
    out.append("__spook__")
    return out


def _r_quiet(world: World) -> list[str]:
    out = []
    dolphin = world.get("dolphin")
    if dolphin.memes["unease"] < THRESHOLD:
        return out
    sig = ("quiet",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    dolphin.meters["distance"] += 1
    out.append("__quiet__")
    return out


CAUSAL_RULES = [Rule("spook", "social", _r_spook), Rule("quiet", "social", _r_quiet)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for hid in HOME_SPOTS:
            for did in DOLPHINS:
                if setting.id in did.allowed and hid != "inside_kitchen":
                    combos.append((sid, hid, did.id))
    return combos


def can_help(setting: Setting, shaker: Shaker, dolphin: Dolphin) -> bool:
    return setting.id in dolphin.allowed and shaker.loud


def inner_monologue(child: Entity, setting: Setting, shaker: Shaker, dolphin: Dolphin) -> str:
    return (
        f"{child.id} held the {shaker.label} and thought, "
        f"Maybe the dolphin only needs a little courage, not a whole thunderstorm. "
        f"The sea looked huge, but {setting.wind} was kinder than the rattling."
    )


def fear_line(child: Entity, dolphin: Dolphin, shaker: Shaker) -> str:
    return (
        f"{child.id} heard the {shaker.label} clatter and thought, "
        f"Oh no, that sound is a tin drum in a tiny storm. "
        f"The dolphin's bright eye looked unsure."
    )


def calm_line(child: Entity, shaker: Shaker) -> str:
    return (
        f"{child.id} set the {shaker.label} down and thought, "
        f"If I make less noise, maybe the sea will answer back."
    )


def nudge(world: World, child: Entity, shaker: Shaker) -> None:
    child.memes["hope"] += 1
    shaker.meters["rattling"] += 1
    world.say(
        f"On the dock at {world.setting.place}, {child.id} found a {shaker.label} "
        f"that flashed like a pocket sun. {shaker.glitter}"
    )


def meet(world: World, child: Entity, dolphin: Entity, setting: Setting) -> None:
    world.say(
        f"Out beyond the pilings, a dolphin came leaping through the blue, "
        f"as bold as a silver banner in a parade. {setting.image}"
    )


def think(world: World, child: Entity, shaker: Shaker, dolphin: Entity) -> None:
    child.memes["thought"] += 1
    world.say(inner_monologue(child, world.setting, shaker, dolphin))
    world.say(fear_line(child, dolphin, shaker))


def rattle(world: World, shaker: Entity) -> None:
    shaker.meters["rattling"] += 1
    shaker.meters["noise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The {shaker.label} rattled once, twice, and then a third time, loud as a "
        f"kettle in a thundercloud."
    )


def choose_calm(world: World, child: Entity, shaker: Shaker) -> None:
    child.memes["resolve"] += 1
    shaker.meters["rattling"] = 0.0
    world.say(calm_line(child, shaker))


def answer(world: World, child: Entity, dolphin: Entity, response: Response) -> None:
    dolphin.meters["distance"] = max(0.0, dolphin.meters["distance"] - 1.0)
    dolphin.memes["trust"] += 1
    body = response.text
    world.say(
        f"{child.id} took a breath and did the sensible thing: {body}."
    )
    world.say(
        f"The dolphin turned, listened, and swam closer with a face as bright as a moonlit coin."
    )


def fail_answer(world: World, child: Entity, dolphin: Entity, response: Response) -> None:
    world.say(
        f"{child.id} tried to help, but {response.fail}."
    )
    world.say(
        f"The dolphin stayed back, and the water felt wide and lonely."
    )


def ending(world: World, child: Entity, dolphin: Entity, shaker: Shaker, setting: Setting) -> None:
    world.say(
        f"In the end, the {shaker.label} stayed quiet in {child.pronoun('possessive')} hand, "
        f"and the dolphin glided beside the dock as calm as a storybook wave."
    )
    world.say(
        f"{setting.water.capitalize()} shone like glass, and {child.id} felt taller than the tide."
    )


def rescue_ending(world: World, child: Entity, dolphin: Entity, setting: Setting) -> None:
    world.say(
        f"In the end, the child waved, the dolphin answered with a great silver leap, "
        f"and the whole bay looked like it had learned to smile."
    )
    world.say(f"{setting.water.capitalize()} glittered under the sky like a thousand tiny bells.")


def tell(setting: Setting, shaker: Shaker, dolphin: Dolphin, response: Response,
         child_name: str = "Mina", child_gender: str = "girl",
         adult: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=adult, role="parent"))
    sh = world.add(Entity(id="shaker", type="thing", label=shaker.label))
    dl = world.add(Entity(id="dolphin", type="creature", label=dolphin.label))
    child.memes["curiosity"] = 1.0

    nudge(world, child, shaker)
    meet(world, child, dl, setting)
    world.para()
    think(world, child, shaker, dl)
    rattle(world, sh)
    if can_help(setting, shaker, dolphin):
        choose_calm(world, child, shaker)
        answer(world, child, dl, response)
        rescue_ending(world, child, dl, setting)
        outcome = "resolved"
    else:
        fail_answer(world, child, dl, response)
        outcome = "unresolved"
    ending(world, child, dl, shaker, setting)
    world.facts.update(child=child, parent=parent, shaker=shaker, dolphin=dolphin, response=response, outcome=outcome, setting=setting)
    return world


SETTINGS = {
    "dock": Setting("dock", "the dock", "The boards creaked underfoot, and the sea carried a song that seemed older than the town.", "the wind from the bay", "the bay"),
    "shore": Setting("shore", "the shore", "The waves rolled in like marching horses with white manes.", "the salt wind", "the water"),
    "pier": Setting("pier", "the pier", "The pier stretched out like a wooden finger pointing at the horizon.", "the sea breeze", "the harbor"),
}

HOME_SPOTS = {
    "dockbox",
    "shorebag",
    "pierpost",
}

DOLPHINS = {
    "dolphin": Dolphin("dolphin", "a dolphin", "the blue lane beyond the dock", "a spray of pearls", "shy", allowed={"dock", "shore", "pier"}),
}

SHAKERS = {
    "shaker": Shaker("shaker", "shaker", "It glittered with tiny bright beads.", "rattled like marching pebbles", "rested like a little lantern"),
}

RESPONSES = {
    "whisper": Response("whisper", 3, 3, "whispered to the dolphin and waved the shaker slowly like a friendly flag", "whispered, but the shake was still too wild and the dolphin would not come closer", "whispered and waved the shaker slowly"),
    "rest": Response("rest", 3, 4, "set the shaker on the dock and waited with quiet hands until the dolphin drifted near", "set the shaker down, but the moment had already slipped away", "set the shaker down and waited quietly"),
    "toss": Response("toss", 1, 1, "tossed the shaker into the water", "tossed the shaker, but that only made things stranger", "tossed the shaker into the water"),
}


def outcome_of(params: "StoryParams") -> str:
    return "resolved" if params.response in {"whisper", "rest"} else "unresolved"


@dataclass
@dataclass
class StoryParams:
    setting: str
    dolphin: str
    shaker: str
    response: str
    child_name: str
    child_gender: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a 3-to-5-year-old that includes the words "shaker" and "dolphin" and uses inner monologue.',
        f"Tell a windy dock story where {f['child'].id} meets a dolphin, hears the shaker rattling, and then quiets down to help.",
        f"Write a story where a child thinks to themself about a shaker and a dolphin, then chooses a gentler way and ends in a bright sea image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    shaker = f["shaker"]
    dolphin = f["dolphin"]
    setting = f["setting"]
    resp = f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, who went to {setting.place} with a shiny {shaker.label}. The story also follows a dolphin that came to the water beside the dock."),
        ("What did the child first want to do?",
         f"{child.id} wanted to show the {shaker.label} to the dolphin and make a grand splash of sound. That idea was exciting, but it was also too noisy."),
        ("What did the child think about inside their head?",
         f"{inner_monologue(child, setting, shaker, dolphin)}. That thought helped {child.id} notice that the dolphin needed calm, not clatter."),
    ]
    if f["outcome"] == "resolved":
        qa.append((
            "How did the child help the dolphin?",
            f"{child.id} chose {resp.qa_text} instead of rattling the {shaker.label} again. That softer choice let the dolphin swim closer and made the water feel friendly."
        ))
    else:
        qa.append((
            "Why did the dolphin stay back?",
            f"The {shaker.label} was still too loud, so the dolphin kept its distance. The child wanted to help, but the sound made the moment too jumpy."
        ))
    return qa


KNOWLEDGE = {
    "dolphin": [("What is a dolphin?",
                 "A dolphin is a sea animal that swims fast, leaps high, and often lives in groups called pods.")],
    "shaker": [("What is a shaker?",
                "A shaker is something that rattles when you move it. People use shakers in music or play, but they can make a lot of noise.")],
    "dock": [("What is a dock?",
              "A dock is a wooden place by the water where boats can stop and people can stand near the sea.")],
    "shore": [("What is the shore?",
               "The shore is the land right next to the water, where waves meet the sand or rocks.")],
    "quiet": [("Why can quiet help animals?",
               "Quiet lets animals feel safe, because sudden noise can make them nervous or scared.")],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"dolphin", "shaker", world.setting.id, "quiet"}
    out: list[tuple[str, str]] = []
    for tag in ["dolphin", "shaker", "dock", "shore", "quiet"]:
        if tag in tags:
            out.extend(KNOWLEDGE.get(tag, []))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("dock", "dolphin", "shaker", "whisper", "Mina", "girl", "mother"),
    StoryParams("shore", "dolphin", "shaker", "rest", "Eli", "boy", "father"),
    StoryParams("pier", "dolphin", "shaker", "toss", "Rose", "girl", "mother"),
]


def explain_rejection() -> str:
    return "(No story: the chosen setup does not give the child a believable way to help the dolphin.)"


def valid_story_choices() -> list[tuple[str, str, str, str]]:
    out = []
    for sid in SETTINGS:
        for did in DOLPHINS:
            for shid in SHAKERS:
                for rid in RESPONSES:
                    if rid in {"whisper", "rest", "toss"}:
                        out.append((sid, did, shid, rid))
    return out


ASP_RULES = r"""
valid(S, D, H, R) :- setting(S), dolphin(D), shaker(H), response(R).
resolved(R) :- response(R), (R = whisper; R = rest).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did in DOLPHINS:
        lines.append(asp.fact("dolphin", did))
    for hid in SHAKERS:
        lines.append(asp.fact("shaker", hid))
    for rid in RESPONSES:
        lines.append(asp.fact("response", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid()) == set(valid_story_choices()):
        print(f"OK: gate matches valid_story_choices() ({len(valid_story_choices())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, dolphin=None, shaker=None, response=None, child_name=None, child_gender=None, adult=None), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about a shaker and a dolphin.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    response = args.response or rng.choice(list(RESPONSES))
    if response == "toss":
        # explicit low-utility option allowed, but still a story
        pass
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(["Mina", "Eli", "Rose", "Noah", "Luna", "Finn"])
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(setting, "dolphin", "shaker", response, child_name, child_gender, adult)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    shaker = SHAKERS[params.shaker]
    dolphin = DOLPHINS[params.dolphin]
    response = RESPONSES[params.response]
    world = tell(setting, shaker, dolphin, response, params.child_name, params.child_gender, params.adult)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} compatible combos.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        print(json.dumps(samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
