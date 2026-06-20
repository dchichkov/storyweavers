#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ogre_bad_ending_folk_tale.py
=============================================================

A standalone story world for a small folk-tale domain: a village child, an ogre,
a tempting bargain, and a bad ending when the child ignores a wise warning.

The model keeps the story concrete and state-driven: characters have physical
meters and emotional memes, and the ending follows from what happened in the
world rather than from a frozen template.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man", "ogre"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Tale:
    village: str
    path: str
    home: str
    warning_sign: str
    ogre_den: str
    lure: str
    bargain: str
    danger: str
    ending_image: str

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
    def __init__(self) -> None:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


def hazard_at_risk(ogre: str, target: str) -> bool:
    return ogre == "ogre" and target in {"child", "goat", "bread"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def story_outcome(response: Response, delay: int) -> str:
    return "bad" if response.power < 2 + delay else "contained"


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    ogre = world.entities.get("ogre")
    bait = world.entities.get("bait")
    if child and ogre and bait and child.meters["taken"] >= THRESHOLD and "grab" not in world.fired:
        world.fired.add(("grab",))
        ogre.meters["angry"] += 1
        child.memes["fear"] += 1
        out.append("__grab__")
    if narrate:
        for s in out:
            if not s.startswith("__"):
                world.say(s)
    return out


def _do_step(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    ogre = world.get("ogre")
    bait = world.get("bait")
    child.meters["taken"] += 1
    child.memes["greed"] += 1
    propagate(world, narrate=narrate)


def predict_bad(world: World) -> bool:
    sim = world.copy()
    _do_step(sim, narrate=False)
    return sim.get("ogre").meters["angry"] >= THRESHOLD


def tell(tale: Tale, response: Response, delay: int, name: str, parent: str) -> World:
    world = World()
    child = world.add(Entity(id=name, kind="character", type="boy", role="child"))
    ogre = world.add(Entity(id="ogre", kind="character", type="ogre", label="the ogre", role="ogre"))
    adult = world.add(Entity(id=parent, kind="character", type="mother", label="the mother", role="adult"))
    bait = world.add(Entity(id="bread", kind="thing", type="thing", label="the warm bread", role="bait"))
    child.memes["curious"] = 1
    world.facts.update(tale=tale, response=response, delay=delay, child=child, ogre=ogre, adult=adult, bait=bait)

    world.say(
        f"Long ago, in {tale.village}, {name} lived in a little house near {tale.path}. "
        f"Each day, {name} passed {tale.warning_sign} and heard old folk say, "
        f'"{tale.warning_sign.capitalize()} means the ogre is near."'
    )
    world.say(
        f"One evening, the air smelled of supper and {name} saw {tale.lure}. "
        f"{name} thought of {tale.bargain} and forgot to keep far from {tale.ogre_den}."
    )
    world.para()
    if predict_bad(world):
        world.say(
            f'The {adult.label_word} called, "Do not go there." But {name} wanted the bread anyway, '
            f"so {name} stepped closer and took it."
        )
        _do_step(world)
        world.para()
        world.say(
            f"{ogre.pronoun('subject').capitalize()} thundered from {tale.ogre_den}. "
            f'"Who steals from my door?" roared the ogre, and the path felt small and dark.'
        )
        world.say(
            f"{adult.label_word.capitalize()} ran for help, but {response.fail.replace('{target}', 'the bread')}. "
            f"{tale.danger}."
        )
        world.para()
        world.say(
            f"In the end, {name} got away only by leaving the bread behind, hungry and crying, "
            f"and the ogre kept the basket. By morning, {tale.ending_image}."
        )
        outcome = "bad"
    else:
        world.say(
            f'The {adult.label_word} warned, and {name} listened, so the ogre never woke. '
            f"They went home with the bread and a steady heart."
        )
        outcome = "good"
    world.facts["outcome"] = outcome
    return world


THEMES = {
    "folk": Tale(
        village="a small village by the gray woods",
        path="the mossy lane",
        home="a cottage with a red door",
        warning_sign="don't take bread from the ogre's gate",
        ogre_den="the hill cave",
        lure="a basket of warm bread sitting at a stone gate",
        bargain="a loaf for a loaf and a smile for a smile",
        danger="The ogre had left the basket as bait",
        ending_image="the basket was gone, the bread was lost, and no one in the village forgot the lesson",
    ),
    "river": Tale(
        village="a river village under willow trees",
        path="the bank path",
        home="a snug cabin",
        warning_sign="never follow an ogre to the water",
        ogre_den="the roots under the bridge",
        lure="fresh pies cooling on a low sill",
        bargain="a pie for a story",
        danger="The ogre had hidden beside the water",
        ending_image="the pies were gone, the stream was quiet, and the child learned too late",
    ),
    "forest": Tale(
        village="a little village at the edge of the pines",
        path="the pine trail",
        home="a cottage with blue shutters",
        warning_sign="do not answer a stranger ogre at dusk",
        ogre_den="the hollow stump",
        lure="bright apples piled beside a stump",
        bargain="an apple for a song",
        danger="The ogre had waited in the shadows",
        ending_image="the apples were taken, the trail went dark, and the child came home shaken",
    ),
}

RESPONSES = {
    "shout": Response("shout", 3, 1, "shouted for the neighbors, but it was too late to stop the ogre", "shouted, but the ogre was already at the child", "shouted for the neighbors"),
    "door": Response("door", 3, 2, "slammed the door and barred it shut, but the ogre was already inside the yard", "barred the door, but the ogre was too close", "slammed the door and barred it shut"),
    "lantern": Response("lantern", 2, 2, "lit a lantern and waved it at the path, but the ogre's shadow stayed long", "held up a lantern, but the ogre still came", "lit a lantern and waved it"),
    "snare": Response("snare", 2, 1, "threw a snare on the path, but it tangled the bread basket instead", "set a snare, but it caught nothing useful", "threw a snare on the path"),
}

NAMES = ["Mina", "Pip", "Anya", "Jori", "Lena", "Toma", "Bram", "Sera"]


@dataclass
@dataclass
class StoryParams:
    tale: str
    response: str
    delay: int
    name: str
    parent: str
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
    ap = argparse.ArgumentParser(description="Folk tale storyworld with an ogre and a bad ending.")
    ap.add_argument("--tale", choices=THEMES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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


def valid_combos() -> list[tuple[str, str]]:
    return [("folk", rid) for rid in RESPONSES if hazard_at_risk("ogre", "child")]


def explain_rejection() -> str:
    return "(No story: this tale needs an ogre baiting a child into danger.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.tale and args.tale not in THEMES:
        raise StoryError(explain_rejection())
    tale = args.tale or rng.choice(sorted(THEMES))
    response = args.response or rng.choice(sorted(RESPONSES))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    if RESPONSES[response].sense < SENSE_MIN:
        raise StoryError("(Refusing weak response.)")
    return StoryParams(tale, response, delay, name, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tale, response = f["tale"], f["response"]
    return [
        f'Write a folk tale for a young child that includes an ogre and ends badly when a warning is ignored.',
        f"Tell a short story in a folk-tale style where {f['child'].id} goes near an ogre and the help comes too late.",
        f'Write a sad fairy-tale-like story with an ogre, a warning, and a lost treasure; use the word "{tale.warning_sign.split()[0]}".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    t: Tale = f["tale"]
    c: Entity = f["child"]
    qas = [
        ("Who is the story about?", f"It is about {c.id}, a child who wandered near an ogre."),
        ("What did the child want?", f"{c.id} wanted {t.lure} and forgot the warning about the ogre."),
        ("What happened at the end?", f"The child got away, but only by leaving the bread behind. The ogre kept the basket, so it was a bad ending."),
    ]
    if f["outcome"] == "bad":
        qas.append(("Why was it a bad ending?", f"The child lost the food and came home crying. The ogre won the prize, and the warning came true too late."))
    return qas


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an ogre?", "An ogre is a big scary giant from folk tales. In stories, ogres often guard things and frighten travelers."),
        ("What is bread?", "Bread is a food made from dough and baked until it is warm and soft or crusty."),
        ("Why should children listen to warnings?", "Warnings help children stay safe. Listening early can keep a bad surprise from becoming a bigger problem."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("ogre", "ogre"), asp.fact("sense_min", SENSE_MIN)]
    for t in THEMES:
        lines.append(asp.fact("tale", t))
    for r, resp in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, resp.sense))
        lines.append(asp.fact("power", r, resp.power))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(T,R) :- tale(T), sensible(R), ogre(ogre).
outcome(bad) :- chosen_response(R), power(R,P), delay(D), P < 2 + D.
outcome(good) :- chosen_response(R), power(R,P), delay(D), P >= 2 + D.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_response", params.response), asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: generation produced empty story.")
    else:
        print("OK: story generation smoke test passed.")
    if asp_outcome(CURATED[0]) != story_outcome(RESPONSES[CURATED[0].response], CURATED[0].delay):
        rc = 1
        print("MISMATCH: ASP outcome differs.")
    else:
        print("OK: outcome parity passes.")
    return rc


CURATED = [
    StoryParams("folk", "shout", 2, "Mina", "mother"),
    StoryParams("river", "door", 1, "Pip", "father"),
    StoryParams("forest", "lantern", 0, "Lena", "mother"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.tale], RESPONSES[params.response], params.delay, params.name, params.parent)
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t, r in asp_valid_combos():
            print(f"  {t} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            seed = base_seed + i
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
