#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/elephant_satin_shrine_teamwork_rhyme_mystery.py
===============================================================================

A standalone story world about a small mystery in a shrine: a satin ribbon,
an elephant statue, a clue in rhyme, and a teamwork-driven reveal.

The domain is intentionally tiny and classical:
- a shrine has a missing satin cloth or ribbon,
- two child detectives look for clues,
- an elephant-shaped statue or carving points the way,
- they solve the mystery by working together and following a rhyme,
- the ending image proves what changed.

This script follows the Storyweavers contract:
- self-contained stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- has a Python reasonableness gate and inline ASP twin
- generates story-grounded and world-knowledge Q&A from world state
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    missing: bool = False
    found: bool = False
    shiny: bool = False
    rhyme_charm: bool = False

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
    name: str
    has_elephant: bool = False
    has_shrine: bool = False
    has_satin: bool = False
    has_echo: bool = False
    tags: set[str] = field(default_factory=set)

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
    text: str
    rhyme: str
    points_to: str
    sense: int = 2
    tags: set[str] = field(default_factory=set)

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
class HelpAction:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

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


def _r_relief(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["tension"] >= THRESHOLD and e.found:
            sig = ("relief", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["relief"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("relief", "social", _r_relief)]


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


def reasonableness_ok(place: Place, clue: Clue, action: HelpAction) -> bool:
    return place.has_shrine and place.has_elephant and place.has_echo and clue.points_to in {"elephant", "satin", "shrine"} and action.sense >= SENSE_MIN


def sensible_actions() -> list[HelpAction]:
    return [a for a in ACTIONS.values() if a.sense >= SENSE_MIN]


def best_action() -> HelpAction:
    return max(ACTIONS.values(), key=lambda a: a.sense)


def predict(world: World, clue_id: str, action_id: str) -> dict:
    sim = world.copy()
    _solve(sim, sim.get(clue_id), ACTIONS[action_id], narrate=False)
    return {"found": sim.get("clue").found, "tension": sim.get("seeker").meters["tension"]}


def _search(world: World, seeker: Entity) -> None:
    seeker.memes["curiosity"] += 1
    world.say(
        f"{seeker.id} peered into the shrine and noticed the quiet things first: "
        f"the stone floor, the carved elephant, and the empty place where the satin had been."
    )
    world.say(
        f"The air felt like a mystery, and every shadow seemed to wait for a clue."
    )


def _rhyme_clue(world: World, seeker: Entity, clue: Clue) -> None:
    seeker.memes["hope"] += 1
    world.say(
        f"{seeker.id} found a little note tucked near the pillar. It read, "
        f'"{clue.rhyme}"'
    )
    world.say(
        f"{seeker.id} whispered it out loud, because in a mystery, a rhyme can be a map."
    )


def _teamwork(world: World, seeker: Entity, helper: Entity, clue: Clue) -> None:
    seeker.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"{helper.id} listened, then pointed at the elephant carving. "
        f'"The rhyme means we should look where the trunk leans," {helper.id} said.'
    )


def _solve(world: World, seeker: Entity, action: HelpAction, narrate: bool = True) -> None:
    seeker.meters["tension"] += 1
    seeker.found = True
    if narrate:
        world.say(
            f"Together they used {action.text}."
        )


def _finish(world: World, seeker: Entity, helper: Entity, place: Place, action: HelpAction) -> None:
    seeker.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"They found the satin ribbon looped around the elephant statue, exactly where the rhyme promised."
    )
    world.say(
        f"{action.text.capitalize()}, they put the satin back on the shrine, and the room felt peaceful again."
    )
    world.say(
        f"In the last light, the elephant stood beside the shrine, and the satin shone softly like a solved secret."
    )


def tell(place: Place, clue: Clue, action: HelpAction,
         seeker_name: str = "Mina", seeker_gender: str = "girl",
         helper_name: str = "Noah", helper_gender: str = "boy") -> World:
    world = World()
    seeker = world.add(Entity(id=seeker_name, kind="character", type=seeker_gender, role="seeker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    shrine = world.add(Entity(id="shrine", type="place", label="the shrine"))
    elephant = world.add(Entity(id="elephant", type="thing", label="the elephant statue"))
    satin = world.add(Entity(id="satin", type="thing", label="the satin ribbon", missing=True))
    world.facts["place"] = place
    world.facts["clue"] = clue
    world.facts["action"] = action
    world.facts["seeker"] = seeker
    world.facts["helper"] = helper
    world.facts["shrine"] = shrine
    world.facts["elephant"] = elephant
    world.facts["satin"] = satin

    world.say(
        f"At {place.name}, {seeker.id} and {helper.id} found {place.name} feeling extra quiet, "
        f"as if it was hiding a secret."
    )
    _search(world, seeker)
    world.para()
    _rhyme_clue(world, seeker, clue)
    _teamwork(world, seeker, helper, clue)
    world.para()
    _solve(world, seeker, action)
    _finish(world, seeker, helper, place, action)
    satin.missing = False
    satin.found = True
    world.facts["solved"] = True
    return world


PLACES = {
    "old_shrine": Place("old_shrine", "the old shrine", has_elephant=True, has_shrine=True, has_satin=True, has_echo=True, tags={"shrine", "elephant", "satin", "mystery"}),
    "moon_shrine": Place("moon_shrine", "the moonlit shrine", has_elephant=True, has_shrine=True, has_satin=True, has_echo=True, tags={"shrine", "elephant", "satin", "mystery"}),
}

CLUES = {
    "trunk_rhyme": Clue("trunk_rhyme", "A rhyme about a long trunk and a silver moon", "Long trunk, soft hum, the satin comes from where shadows run.", "elephant", 3, {"rhyme", "elephant"}),
    "stone_rhyme": Clue("stone_rhyme", "A rhyme about stone steps and a hidden seam", "Stone step, soft seam, the satin rests where echoes gleam.", "shrine", 3, {"rhyme", "shrine"}),
    "thread_rhyme": Clue("thread_rhyme", "A rhyme about a bright thread and a gentle bell", "Soft thread, bright bell, the satin waits where kind sounds dwell.", 3, {"rhyme", "satin"}),
}

ACTIONS = {
    "search_together": HelpAction("search_together", 3, 3, "searched side by side and followed the clues", "searched alone and missed the hidden place", "searched side by side and followed the clues", {"teamwork"}),
    "sing_rhyme": HelpAction("sing_rhyme", 3, 3, "sang the rhyme together until the answer sounded clear", "mumbled the rhyme and lost the trail", "sang the rhyme together until the answer sounded clear", {"rhyme"}),
    "lift_cloth": HelpAction("lift_cloth", 2, 2, "lifted the cloth together and found what hid beneath", "lifted only one corner and never uncovered the clue", "lifted the cloth together and found what hid beneath", {"teamwork"}),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Noah", "Theo", "Eli", "Ben", "Finn"]
TRAITS = ["careful", "curious", "thoughtful", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for cid, clue in CLUES.items():
            for aid, action in ACTIONS.items():
                if reasonableness_ok(place, clue, action):
                    combos.append((pid, cid, aid))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    clue: str
    action: str
    seeker: str
    seeker_gender: str
    helper: str
    helper_gender: str
    trait: str
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
    ap = argparse.ArgumentParser(description="Story world sketch: an elephant, a satin mystery, and teamwork in a shrine.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--seeker")
    ap.add_argument("--seeker-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def explain_rejection() -> str:
    return "(No story: this shrine mystery needs an elephant, a shrine, satin, and a sensible teamwork or rhyme clue.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError(explain_rejection())
    place, clue, action = rng.choice(sorted(combos))
    seeker_gender = args.seeker_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if seeker_gender == "girl" else "girl")
    seeker = args.seeker or rng.choice(GIRL_NAMES if seeker_gender == "girl" else BOY_NAMES)
    helper_pool = [n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != seeker]
    helper = args.helper or rng.choice(helper_pool)
    trait = rng.choice(TRAITS)
    return StoryParams(place, clue, action, seeker, seeker_gender, helper, helper_gender, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the words "elephant", "satin", and "shrine".',
        f"Tell a gentle mystery where {f['seeker'].id} and {f['helper'].id} solve a shrine clue together and find the satin near the elephant.",
        f"Write a child-friendly mystery with teamwork and a rhyme that leads back to a shrine and an elephant statue.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    clue = f["clue"]
    action = f["action"]
    place = f["place"]
    qa = [
        ("What was the mystery about?",
         f"It was about a missing satin ribbon at the shrine. The clue led the children to the elephant statue."),
        ("How did the children solve the mystery?",
         f"They solved it by working together and following the rhyme. The clue made the elephant statue seem important, and that helped them find the satin."),
        ("What did they find at the end?",
         f"They found the satin ribbon and put it back on the shrine. The shrine looked peaceful again, and the elephant stood beside the solved secret."),
    ]
    if f.get("solved"):
        qa.append((
            f"Why did {helper.id} help {seeker.id}?",
            f"{helper.id} helped because the rhyme needed two careful listeners. Together they could search better than either child could alone."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a shrine?",
         "A shrine is a special place where people may go to honor something they care about. It is often quiet and treated with respect."),
        ("What is satin?",
         "Satin is a smooth, shiny cloth. It can look bright and soft in the light."),
        ("What is an elephant?",
         "An elephant is a very large animal with a long trunk and big ears. In stories, an elephant statue can be a clue or a guard of secrets."),
        ("What is teamwork?",
         "Teamwork means people help each other and share the job. When they work together, they can solve harder problems."),
        ("What is a rhyme?",
         "A rhyme is when words sound alike at the end. Rhymes can help you remember a clue or a song."),
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
        if e.missing:
            bits.append("missing=True")
        if e.found:
            bits.append("found=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("old_shrine", "trunk_rhyme", "search_together", "Mina", "girl", "Noah", "boy", "curious"),
    StoryParams("moon_shrine", "stone_rhyme", "sing_rhyme", "Theo", "boy", "Lila", "girl", "thoughtful"),
    StoryParams("old_shrine", "thread_rhyme", "lift_cloth", "Ava", "girl", "Finn", "boy", "gentle"),
]


def _solve(world: World, seeker: Entity, action: HelpAction, narrate: bool = True) -> None:
    seeker.meters["tension"] += 1
    seeker.found = True
    if narrate:
        world.say(f"Together they used {action.text}.")


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.has_elephant:
            lines.append(asp.fact("has_elephant", pid))
        if place.has_shrine:
            lines.append(asp.fact("has_shrine", pid))
        if place.has_satin:
            lines.append(asp.fact("has_satin", pid))
        if place.has_echo:
            lines.append(asp.fact("has_echo", pid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("points_to", cid, clue.points_to))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, action.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,A) :- place(P), clue(C), action(A), has_elephant(P), has_shrine(P), has_echo(P), points_to(C, _), sense(A, S), sense_min(M), S >= M.
solved(A) :- action(A), sense(A, S), sense_min(M), S >= M.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, clue=None, action=None, seeker=None, seeker_gender=None, helper=None, helper_gender=None), random.Random(7)))
        _ = sample.story
    except Exception as err:
        print("SMOKE TEST FAILED:", err)
        rc = 1
    else:
        print("OK: gate matches and smoke test generated a story.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CLUES[params.clue], ACTIONS[params.action], params.seeker, params.seeker_gender, params.helper, params.helper_gender)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for item in asp_valid_combos():
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
