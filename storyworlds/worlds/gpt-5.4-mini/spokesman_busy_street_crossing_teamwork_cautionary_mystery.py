#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/spokesman_busy_street_crossing_teamwork_cautionary_mystery.py
=============================================================================================

A standalone story world for a folk-tale style crossing scene: a small group
must cross a busy street, a spokesman speaks for the group, a cautionary warning
prevents a mistake, and a little mystery gets solved by teamwork.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- state-driven narration
- a reasonableness gate over valid story setups
- a Python logic twin plus an inline ASP twin
- three QA sets grounded in the simulated world state
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
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def name_word(self) -> str:
        return self.label or self.id



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
    busy: bool = True

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
    hidden_object: str
    where_found: str
    solved_with: str
    kind: str = "lost thing"
    plausible: bool = True

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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.street: str = ""
        self.mystery_found: bool = False

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.street = self.street
        clone.mystery_found = self.mystery_found
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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    if not world.street:
        return out
    sig = ("noise", world.street)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ch in world.characters():
        ch.memes["alertness"] += 1
    out.append("__noise__")
    return out


def _r_mystery(world: World) -> list[str]:
    out: list[str] = []
    if not world.mystery_found:
        return out
    sig = ("mystery", world.facts.get("mystery_id", ""))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ch in world.characters():
        ch.memes["curiosity"] += 1
    out.append("__mystery__")
    return out


CAUSAL_RULES = [Rule("noise", "physical", _r_noise), Rule("mystery", "social", _r_mystery)]


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


def busy_crossing_at_risk(crossing: Place, mystery: Mystery) -> bool:
    return crossing.busy and mystery.plausible


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def reason_about_crossing(response: Response, delay: int) -> bool:
    return response.power >= (1 + delay)


def choose_spokesman(group: list[Entity]) -> Entity:
    for ch in group:
        if "polite" in ch.traits or "clear voice" in ch.traits:
            return ch
    return group[0]


def predict(world: World, mystery_id: str, delay: int) -> dict:
    sim = world.copy()
    _do_misstep(sim, sim.get("child"), sim.get("spokesman"), narrate=False)
    return {
        "confusion": sim.get("child").meters["confusion"] >= THRESHOLD,
        "danger": delay + 1,
        "solved": sim.mystery_found,
    }


def _do_misstep(world: World, child: Entity, spokesman: Entity, narrate: bool = True) -> None:
    child.memes["worry"] += 1
    spokesman.memes["boldness"] += 1
    propagate(world, narrate=narrate)


def wait_and_watch(world: World, child: Entity, street: Place) -> None:
    world.say(
        f"At the busy street crossing, {child.id} and the others stood together like travelers at a gate. "
        f"Cars rushed past, and the wind carried dust and engine hum."
    )
    world.say(
        f"{child.id} leaned close and listened, because the crossing was no place for rushing."
    )


def speak_for_group(world: World, spokesman: Entity, child: Entity) -> None:
    world.say(
        f'"Let me speak," said the spokesman {spokesman.id}, and {spokesman.pronoun()} raised '
        f'{spokesman.pronoun("possessive")} hand so all would listen.'
    )
    world.say(
        f"{spokesman.id} spoke kindly for the group, and {child.id} felt steadier at once."
    )


def caution(world: World, guardian: Entity, child: Entity, street: Place) -> None:
    guardian.memes["care"] += 1
    world.say(
        f'"Do not step yet," said {guardian.id}. "The street is busy, and one quick mistake can turn to trouble."'
    )
    world.say(
        f"{child.id} watched the wheels go by and held still, remembering the warning."
    )


def first_clue(world: World, mystery: Mystery) -> None:
    world.say(
        f"Then a little mystery appeared: a {mystery.kind} lay near the crossing, and nobody knew who had dropped it."
    )
    world.say(
        f'On the cloth were the words, "{mystery.clue}", which made the children look at one another in wonder.'
    )


def teamwork_search(world: World, child: Entity, spokesman: Entity, helper: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] += 1
    helper.memes["helpfulness"] += 1
    spokesman.memes["leadership"] += 1
    world.say(
        f"The children did not scatter. Instead they searched together, one looking left, one looking right, and one checking the curb."
    )
    world.say(
        f"{spokesman.id} asked the questions, {child.id} spotted the small sign, and {helper.id} noticed the thread of {mystery.solved_with} caught on a bench."
    )
    world.mystery_found = True


def solve_mystery(world: World, spokesman: Entity, mystery: Mystery) -> None:
    world.say(
        f"With teamwork they matched the clue to the sign, and the answer became clear: the lost thing was {mystery.hidden_object}."
    )
    world.say(
        f"{spokesman.id} returned it to its place at {mystery.where_found}, and the little mystery was solved cleanly."
    )


def end_scene(world: World, child: Entity, spokesman: Entity, guardian: Entity) -> None:
    child.memes["relief"] += 1
    spokesman.memes["relief"] += 1
    guardian.memes["relief"] += 1
    world.say(
        f"The crosswalk lights changed, and the group crossed safely at last, shoulder to shoulder, with the spokesman in front and the others close behind."
    )
    world.say(
        f"By the time they reached the far side, the busy street still roared, but the little company walked on calm and proud."
    )


def tell(place: Place, mystery: Mystery, response: Response, delay: int = 0,
         child_name: str = "Mira", spokesman_name: str = "Pip",
         helper_name: str = "Hana", guardian_name: str = "Grandmother") -> World:
    world = World()
    world.street = place.label
    child = world.add(Entity(id=child_name, kind="character", type="girl", role="listener", traits=["patient"]))
    spokesman = world.add(Entity(id=spokesman_name, kind="character", type="boy", role="spokesman", traits=["polite", "clear voice"]))
    helper = world.add(Entity(id=helper_name, kind="character", type="girl", role="helper", traits=["quick-eyed"]))
    guardian = world.add(Entity(id=guardian_name, kind="character", type="woman", role="guardian", traits=["cautious"]))
    world.add(Entity(id="crossing", type="place", label=place.label))
    world.add(Entity(id="mystery", type="mystery", label=mystery.kind))
    world.facts["mystery_id"] = mystery.id

    wait_and_watch(world, child, place)
    world.para()
    speak_for_group(world, spokesman, child)
    caution(world, guardian, child, place)
    if busy_crossing_at_risk(place, mystery):
        first_clue(world, mystery)
        teamwork_search(world, child, spokesman, helper, mystery)
        if reason_about_crossing(response, delay):
            world.para()
            solve_mystery(world, spokesman, mystery)
            world.say(
                f'Then the guardian smiled, because the warning had been heeded and the mystery had been solved without anyone dashing into the road.'
            )
            end_scene(world, child, spokesman, guardian)
        else:
            world.para()
            world.say(
                f"The children tried to solve it quickly, but the answer took too long to fit the moment."
            )
            world.say(
                f"The guardian kept them back until the crossing was clear, and the mystery had to wait for another day."
            )
    world.facts.update(
        child=child, spokesman=spokesman, helper=helper, guardian=guardian,
        place=place, mystery=mystery, response=response, delay=delay,
        solved=world.mystery_found, warned=True
    )
    return world


PLACES = {
    "busy_crossing": Place("busy_crossing", "the busy street crossing", busy=True),
    "market_crossing": Place("market_crossing", "the market crossing", busy=True),
    "quiet_corner": Place("quiet_corner", "the quiet corner road", busy=False),
}

MYSTERIES = {
    "lost_key": Mystery("lost_key", "The key is near", "a brass key", "the little shop door", "a ribbon on a bench"),
    "missing_bell": Mystery("missing_bell", "Listen for the bell", "a silver hand bell", "the gatepost", "a strip of red cloth"),
    "dropped_map": Mystery("dropped_map", "Follow the little marks", "a folded map", "the market stall", "chalk dust"),
}

RESPONSES = {
    "steady_wait": Response("steady_wait", 3, 2, "waited steady and watched the road clear", "waited too little and the moment got lost", "waited steady"),
    "look_and_listen": Response("look_and_listen", 3, 3, "looked left and right, listened for the tires, and then crossed with care", "looked too late, and the crossing stayed unsafe", "looked and listened"),
    "too_hasty": Response("too_hasty", 1, 1, "stepped out at once", "stepped out too soon", "stepped out at once"),
}

GIRL_NAMES = ["Mira", "Hana", "Lena", "Sana", "Nora"]
BOY_NAMES = ["Pip", "Jon", "Reed", "Toma", "Basil"]


@dataclass
@dataclass
class StoryParams:
    place: str
    mystery: str
    response: str
    child_name: str
    spokesman_name: str
    helper_name: str
    guardian_name: str
    delay: int = 0
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for mid, mystery in MYSTERIES.items():
            if busy_crossing_at_risk(place, mystery):
                combos.append((pid, mid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale crossing story with a spokesman, caution, and a solved mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.place and args.place == "quiet_corner":
        raise StoryError("No story: the setting must be a busy street crossing, not a quiet road.")
    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              if args.mystery is None or c[1] == args.mystery]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    child_name = rng.choice(GIRL_NAMES)
    spokesman_name = rng.choice(BOY_NAMES)
    helper_name = rng.choice([n for n in GIRL_NAMES if n != child_name])
    guardian_name = "Grandmother"
    delay = rng.randint(0, 1)
    return StoryParams(place, mystery, response, child_name, spokesman_name, helper_name, guardian_name, delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style story about a spokesman named {f["spokesman"].id} at {f["place"].label}, where a warning keeps the children safe.',
        f'Write a cautionary crossing story that includes the word "spokesman" and ends with teamwork solving {f["mystery"].hidden_object}.',
        f'Tell a gentle mystery story set at a busy street crossing where children listen, wait, and solve a small clue together.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, spokesman, guardian, mystery, place = f["child"], f["spokesman"], f["guardian"], f["mystery"], f["place"]
    qa = [
        ("Who was the spokesman in the story?",
         f"{spokesman.id} was the spokesman. {spokesman.id} spoke for the group so the others could listen and stay calm."),
        ("Why did the guardian warn them?",
         f"The guardian warned them because the street was busy and a quick step could be dangerous. The warning helped them wait until the crossing was safe."),
        ("What mystery did they solve?",
         f"They solved the mystery of {mystery.hidden_object}. They found it by following the clue and working together."),
        ("How did they solve the mystery?",
         f"They searched as a team, with one child watching the road, one asking questions, and one finding the clue. That teamwork led them to the answer."),
    ]
    if f.get("solved"):
        qa.append(("How did the story end?",
                   f"It ended safely, with the children crossing the street after the mystery was solved. The crossing stayed calm because they listened first and hurried last."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = [
        ("What is a spokesman?",
         "A spokesman is a person who speaks for a group. The spokesman says the words that help everyone understand the plan."),
        ("Why should you be careful at a busy street crossing?",
         "Cars and people move quickly at a busy crossing. Waiting and looking carefully help keep everyone safe."),
        ("What does teamwork mean?",
         "Teamwork means people help one another to do a job. When they work together, they can solve problems more easily."),
        ("What is a mystery?",
         "A mystery is something that is not known yet. People solve it by noticing clues and thinking carefully."),
    ]
    return out


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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("busy_crossing", "lost_key", "look_and_listen", "Mira", "Pip", "Hana", "Grandmother", 0),
    StoryParams("market_crossing", "missing_bell", "steady_wait", "Lena", "Basil", "Nora", "Grandmother", 0),
]


def explain_rejection(place: Place) -> str:
    return f"(No story: {place.label} is not busy enough for this cautionary crossing tale.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.busy:
            lines.append(asp.fact("busy", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("plausible", mid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, M) :- place(P), busy(P), mystery(M), plausible(M).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    if set(asp_sensible()) == {r for r in RESPONSES if RESPONSES[r].sense >= SENSE_MIN}:
        print("OK: ASP sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in ASP sensible responses.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generate() succeeded.")
    except Exception as e:
        return 1 if not print(f"SMOKE TEST FAILED: {e}") else 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], RESPONSES[params.response], params.delay,
                 params.child_name, params.spokesman_name, params.helper_name, params.guardian_name)
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{p} {m}" for p, m in asp_valid_combos()))
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
