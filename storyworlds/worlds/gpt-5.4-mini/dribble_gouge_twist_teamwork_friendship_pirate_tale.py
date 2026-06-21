#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dribble_gouge_twist_teamwork_friendship_pirate_tale.py
======================================================================================

A standalone storyworld for a tiny Pirate Tale domain.

Premise
-------
Two young shipmates are playing pirates on a little boat and discover a strange
map mark on a wooden barrel: a salty dribble of water has made a gouge-like
groove that points toward a hidden hatch. One friend wants to rush ahead, but the
other notices the groove twists under the barrel and warns that the hatch might
stick or a loose board might catch. They work together, use the twist in the
mark as a clue, and solve the puzzle safely. The ending image proves the change:
their teamwork and friendship turn a scary little mystery into a shared win.

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- lazily imports storyworlds/asp.py inside ASP helpers
- includes StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- has a Python reasonableness gate and inline ASP twin
- produces story-grounded Q&A from world state, not rendered prose parsing
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
BRAVERY_INIT = 5.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    dribbles: bool = False
    gouges: bool = False
    twists: bool = False
    supports_map: bool = False

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
    scene: str
    has_boat: bool = True

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
    clue: str
    twists: bool = False

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
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["dribble"] < THRESHOLD:
            continue
        sig = ("spook", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for c in world.characters():
            c.memes["alert"] += 1
        out.append("__spook__")
    return out


CAUSAL_RULES = [Rule("spook", "social", _r_spook)]


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


def hazard_at_risk(clue: Clue) -> bool:
    return clue.twists


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for sid in SETTINGS:
        for cid, clue in CLUES.items():
            for rid, resp in RESPONSES.items():
                if hazard_at_risk(clue):
                    combos.append((sid, cid, rid))
    return combos


def reasonableness_gate(clue: Clue, response: Response) -> bool:
    return clue.twists and response.sense >= SENSE_MIN


def is_resolved(response: Response, clue: Clue) -> bool:
    return response.power >= (2 if clue.twists else 1)


def tell(setting: Setting, clue: Clue, response: Response,
         hero_name: str = "Twist", hero_gender: str = "boy",
         mate_name: str = "Mira", mate_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="instigator",
                            traits=["bold"], age=6))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="cautioner",
                            traits=["careful", "loyal"], age=6))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent",
                              label="the captain"))
    barrel = world.add(Entity(id="barrel", label="the barrel", dribbles=True, gouges=True, twists=True))
    hatch = world.add(Entity(id="hatch", label="the hatch", supports_map=True))
    hero.memes["bravery"] = BRAVERY_INIT
    mate.memes["trust"] = 6
    world.facts["clue"] = clue
    world.facts["response"] = response

    world.say(
        f"Out on a small pirate boat, {hero_name} and {mate_name} played at being bold shipmates. "
        f"{setting.scene}"
    )
    world.say(
        f"Near the deck, a salty dribble had cut a little gouge in the wood, and the mark twisted "
        f"around {barrel.label} like it was pointing to a secret."
    )
    world.say(
        f'"Look!" {mate_name} said. "That twist might be a clue."'
    )

    world.para()
    hero.memes["desire"] += 1
    mate.memes["caution"] += 1
    world.say(
        f'{hero_name} leaned forward. "I can open it fast," {hero_name} said, reaching toward {hatch.label}.'
    )
    world.say(
        f'"Wait," said {mate_name}. "If the board sticks, we should use teamwork, not force."'
    )

    world.para()
    if not reasonableness_gate(clue, response):
        raise StoryError("This clue and response do not make a sensible pirate story.")

    if clue.twists and mate.memes["caution"] >= THRESHOLD:
        world.say(
            f'Together they traced the twist in the mark, counted the boards, and slid a flat stick '
            f'into the gap before anyone tugged too hard.'
        )
        world.say(
            f'The hatch popped open with a soft creak, and the little secret inside turned out to be a map '
            f'piece tucked under the deck.'
        )
        hero.memes["joy"] += 1
        mate.memes["joy"] += 1
        hero.memes["friendship"] += 1
        mate.memes["friendship"] += 1
    else:
        world.say(
            f'{hero_name} pulled too hard, the hatch snapped back, and the dribble-marked board scraped with a harsh gouge.'
        )
        world.say(
            f'{mate_name} called for help, and the two shipmates had to slow down and try again the careful way.'
        )

    world.para()
    if is_resolved(response, clue):
        world.say(
            f'{parent.label_word.capitalize()} came over, smiled at their teamwork, and {response.text}.'
        )
        world.say(
            f'In the end, the shipmates lifted the map piece together, grinning at each other as the sea breeze ruffled the deck.'
        )
    else:
        world.say(
            f'{parent.label_word.capitalize()} came over and {response.fail}.'
        )
        world.say(
            f'The pirate game went quiet for a moment, but their friendship stayed steady, and they promised to try the gentle way.'
        )

    world.facts.update(hero=hero, mate=mate, parent=parent, setting=setting, clue=clue,
                       response=response, resolved=is_resolved(response, clue),
                       teamwork=True, friendship=True, barrel=barrel, hatch=hatch)
    return world


SETTINGS = {
    "deck": Setting("deck", "on the open deck", "The mast leaned over the deck, and a gull cried above the waves."),
    "harbor": Setting("harbor", "by the harbor rail", "The harbor rocked the little boat gently against the dock."),
    "cove": Setting("cove", "near the quiet cove", "The cove water glittered, and the boat bobbed beside a rope ladder."),
}

CLUES = {
    "dribble_twist": Clue("dribble_twist", "a twist-mark clue", "a dribble had made a gouge that twisted around the wood", twists=True),
    "salt_line": Clue("salt_line", "a salt line clue", "a salty line ran along the plank and curled near the hatch", twists=True),
    "plain_mark": Clue("plain_mark", "a plain mark", "a little mark sat on the wood", twists=False),
}

RESPONSES = {
    "wedge": Response("wedge", 3, 3,
                      "used a wooden wedge to lift the hatch safely",
                      "tried to lift it, but it was stuck fast",
                      "used a wooden wedge to lift the hatch safely"),
    "rope_pull": Response("rope_pull", 2, 2,
                          "looped a rope through the handle and pulled together until it opened",
                          "pulled at the rope, but the hatch would not budge",
                          "looped a rope through the handle and pulled together until it opened"),
    "shove": Response("shove", 1, 1,
                      "shoved hard at the hatch",
                      "shoved hard, but only made the gouge worse",
                      "shoved hard at the hatch"),
}

GIRL_NAMES = ["Mira", "Nora", "Luna", "Tess", "Ruby"]
BOY_NAMES = ["Twist", "Finn", "Kellan", "Rowan", "Bram"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    response: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
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


KNOWLEDGE = {
    "dribble": [("What does dribble mean?", "Dribble means to drop or trickle in little drops.")],
    "gouge": [("What is a gouge?", "A gouge is a deep groove or cut in a surface.")],
    "teamwork": [("What is teamwork?", "Teamwork means people work together to do something well.")],
    "friendship": [("What is friendship?", "Friendship is when people care about each other and help each other.")],
    "pirate": [("What is a pirate?", "A pirate is a sailor in stories who looks for treasure on the sea.")],
    "map": [("What is a map piece?", "A map piece is a part of a map that can help show where something is hidden.")],
}
KNOWLEDGE_ORDER = ["dribble", "gouge", "teamwork", "friendship", "pirate", "map"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child that includes the words "dribble" and "gouge".',
        f"Tell a story where {f['hero'].id} and {f['mate'].id} use teamwork and friendship to solve a twisty deck clue.",
        f'Write a gentle pirate story where a twisty mark on a barrel leads to a hidden hatch and a happy shared ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, mate, parent = f["hero"], f["mate"], f["parent"]
    clue, response = f["clue"], f["response"]
    qa = [
        ("Who are the story about?",
         f"They are about {hero.id} and {mate.id}, two shipmates who cared about each other and worked as a team."),
        ("What did the dribble and gouge show?",
         f"They showed a twisty clue on the wood. The mark pointed the shipmates toward the hidden hatch."),
        ("What helped them solve the problem?",
         f"Teamwork helped them solve it. Friendship helped them stay calm and think together instead of pulling too hard."),
    ]
    if f["resolved"]:
        qa.append((
            "How did they open the hatch?",
            f"They opened it by using {response.qa_text}. That careful way fit the twisty clue and kept the deck safe."
        ))
        qa.append((
            "How did the ending change?",
            f"At the end they were smiling together with the map piece. The puzzle turned from a tricky mystery into a shared win."
        ))
    else:
        qa.append((
            "What happened when they rushed?",
            f"They made the gouge worse at first, but then they slowed down and asked for help. The story still ended with friendship and a safer plan."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"dribble", "gouge", "teamwork", "friendship", "pirate", "map"}
    out = []
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
        flags = [n for n, on in (("dribbles", e.dribbles), ("gouges", e.gouges), ("twists", e.twists), ("supports_map", e.supports_map)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this pirate clue is not twisty enough for a sensible teamwork puzzle.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a pirate teamwork mystery with dribble and gouge.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["boy", "girl"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and not CLUES[args.clue].twists:
        raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, response = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["boy", "girl"])
    mate_gender = args.mate_gender or ("girl" if hero_gender == "boy" else "boy")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    mate = args.mate or rng.choice([n for n in (GIRL_NAMES if mate_gender == "girl" else BOY_NAMES) if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, clue, response, hero, hero_gender, mate, mate_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], RESPONSES[params.response],
                 params.hero, params.hero_gender, params.mate, params.mate_gender, params.parent)
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


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams("deck", "dribble_twist", "wedge", "Twist", "boy", "Mira", "girl", "mother"),
        StoryParams("harbor", "salt_line", "rope_pull", "Rook", "boy", "Luna", "girl", "father"),
        StoryParams("cove", "dribble_twist", "wedge", "Nia", "girl", "Tess", "girl", "mother"),
    ]


CURATED = valid_story_params()


ASP_RULES = r"""
twisty(C) :- clue(C), twists(C).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S, C, R) :- setting(S), twisty(C), sensible(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.twists:
            lines.append(asp.fact("twists", cid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    else:
        print("OK: smoke test story generation succeeded.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for sid, cid, rid in asp_valid_combos():
            print(f"  {sid:8} {cid:14} {rid}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.mate}: {p.clue} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
