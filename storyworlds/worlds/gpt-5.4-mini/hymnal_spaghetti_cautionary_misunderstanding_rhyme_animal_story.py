#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hymnal_spaghetti_cautionary_misunderstanding_rhyme_animal_story.py
==================================================================================================

A standalone storyworld for a small animal tale about a cautious misunderstanding:
a little animal wants to follow a hymn rhyme, mistakes a choir book for a snack,
spaghetti gets spilled, and a calm caregiver turns the moment into a safe lesson.

This world keeps the same general contract as the other storyworlds:
- typed entities with accumulating physical meters and emotional memes
- a forward-chained causal simulator
- a reasonableness gate plus inline ASP twin
- story-driven prompts, grounded QA, and world-knowledge QA
- CLI support for default runs, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp

The seed words are included as real story elements:
- hymnal
- spaghetti

The story style is an animal story: small creatures, a homely setting, a clear
misunderstanding, a cautious warning, and a gentle resolution with a rhyme.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "cow", "cat"}
        male = {"boy", "father", "dad", "man", "rooster", "dog", "mouse"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Creature:
    id: str
    species: str
    label: str
    size: str
    trait: str
    loves: str
    kind: str = "character"
    role: str = ""
    type: str = ""
    is_chief: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    category: str
    edible: bool = False
    spillable: bool = False
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str


@dataclass
class StoryParams:
    chief: str
    chief_species: str
    friend: str
    friend_species: str
    parent: str
    parent_species: str
    hymn: str
    food: str
    misread: str
    response: str
    delay: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def characters(self):
        return [e for e in self.entities.values() if getattr(e, "kind", "") == "character"]

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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    jar = world.get("spaghetti")
    if getattr(jar, "meters", defaultdict(float))["spilled"] < THRESHOLD:
        return out
    sig = ("spill", "spaghetti")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ch in world.characters():
        ch.memes["surprise"] += 1
    out.append("__spill__")
    return out


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    jar = world.get("spaghetti")
    if jar.meters["spilled"] < THRESHOLD:
        return out
    sig = ("mess", "spaghetti")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pot = world.get("table")
    pot.meters["mess"] += 1
    out.append("The spaghetti made a red, slippery mess across the table.")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("mess", "physical", _r_mess)]


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


def hazard_at_risk(food: Item, misread: Item) -> bool:
    return food.spillable and misread.edible


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= 1 + delay


def tell(chief: Creature, friend: Creature, parent: Creature, hymn: Item, food: Item,
         misread: Item, response: Response, delay: int = 0) -> World:
    world = World()
    world.add(chief)
    world.add(friend)
    world.add(parent)
    world.add(hymn)
    world.add(food)
    world.add(misread)
    table = world.add(Item("table", "table", "the table", "surface", spillable=False, fragile=False))
    world.add(table)

    chief.memes["curious"] += 1
    friend.memes["careful"] += 1
    world.say(
        f"In a cozy barn, {chief.id} and {friend.id} were a pair of small "
        f"animals with bright eyes and busy paws. {chief.id} loved {chief.loves}, "
        f"and {friend.id} liked to keep things neat."
    )
    world.say(
        f"They found {hymn.phrase} on the bench and started to hum a little rhyme: "
        f'"Soft song, strong paws, tidy nest, tidy nest."'
    )
    world.say(
        f"But then {chief.id} noticed {food.phrase} and frowned. "
        f'"Is that the snack book?" {chief.id} asked, peeking at {misread.phrase}.'
    )

    world.para()
    chief.memes["misunderstanding"] += 1
    world.say(
        f'{chief.id} was sure the shiny bowl held something sweet, so {chief.pronoun()} '
        f"reached for it. {friend.id} blinked and shook {friend.pronoun('possessive')} head."
    )
    world.say(
        f'"Careful," {friend.id} whispered. "{hymn.label} is for singing, not for '
        f"snacking. And {food.label} needs a plate, not a page."'
    )

    if delay == 0 and not is_contained(response, delay):
        raise StoryError("internal: default story must be containable")

    if delay >= 2:
        world.para()
        world.say(
            f"{chief.id} still tugged the wrong way, and the bowl tipped. "
            f"The spaghetti spilled right onto the table."
        )
        food.meters["spilled"] += 1
        propagate(world, narrate=True)
        world.para()
        world.say(
            f"{parent.label_word.capitalize()} came trotting over and {response.fail}. "
            f"Then {parent.pronoun()} scooped the noodles back into a bowl and wiped the table."
        )
        world.say(
            f'“When you are not sure,” {parent.pronoun()} said, “look twice and ask. '
            f"Rhymes are nice, but careful eyes are best.”"
        )
        world.say(
            f"{chief.id} and {friend.id} nodded, and this time they hummed their rhyme "
            f"while keeping the food far from the hymn book."
        )
        outcome = "contained" if response.power >= 1 + delay else "recovered"
    else:
        world.para()
        world.say(
            f"{chief.id} paused, thought of {friend.id}'s warning, and set the bowl down gently."
        )
        world.say(
            f"Instead of making a mess, {chief.id} and {friend.id} sang the rhyme once more "
            f"and carried {food.phrase} to the kitchen."
        )
        world.para()
        world.say(
            f"{parent.id} smiled and said, “A hymn belongs with singing, and spaghetti "
            f"belongs in a bowl. That is a fine way to keep a home.”"
        )
        world.say(
            f"By the end, the barn was quiet, the book was safe, and the spaghetti stayed put."
        )
        outcome = "averted"

    world.facts.update(
        chief=chief, friend=friend, parent=parent, hymn=hymn, food=food, misread=misread,
        response=response, delay=delay, outcome=outcome
    )
    return world


CHIEF_NAMES = ["Milo", "Pip", "Nora", "Luna", "Toby", "Mabel", "Rory", "Wren"]
FRIEND_NAMES = ["Penny", "Otis", "Daisy", "Hank", "Bella", "Jasper", "Ivy", "Clover"]
PARENT_NAMES = ["Mum", "Dad", "Auntie", "Uncle", "Gran", "Grandpa"]

HYMNS = {
    "hymnal": Item("hymnal", "hymnal", "the hymnal", "book", edible=False, spillable=False, fragile=True),
    "songbook": Item("songbook", "songbook", "the songbook", "book", edible=False, spillable=False, fragile=True),
}

FOODS = {
    "spaghetti": Item("spaghetti", "spaghetti", "a bowl of spaghetti", "food", edible=True, spillable=True),
    "soup": Item("soup", "soup", "a bowl of soup", "food", edible=True, spillable=True),
}

MISREADS = {
    "napkin": Item("napkin", "napkin", "a folded napkin", "paper", edible=False, spillable=False),
    "recipe": Item("recipe", "recipe card", "a recipe card", "paper", edible=False, spillable=False),
}

RESPONSES = {
    "scoop": Response("scoop", 3, 3, "scooped up the spilled spaghetti and saved most of it",
                      "was too late to stop the spill", "scooped up the spilled spaghetti"),
    "wipe": Response("wipe", 2, 2, "wiped the table clean with a cloth",
                     "could only watch the noodles slide away", "wiped the table clean"),
    "pause": Response("pause", 1, 1, "paused and asked for help",
                      "could not catch the mess in time", "paused and asked for help"),
}

TRAITS = ["cautious", "gentle", "curious", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for h in HYMNS:
        for f in FOODS:
            for m in MISREADS:
                if hazard_at_risk(FOODS[f], MISREADS[m]):
                    combos.append((h, f, m))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    chief, friend = f["chief"], f["friend"]
    return [
        f'Write an animal story for a child that includes the word "{f["hymn"].label}" '
        f"and the word \"{f['food'].label}\".",
        f"Tell a cautionary misunderstanding story where {chief.id} mistakes a songbook moment "
        f"for snack time, but {friend.id} warns {chief.pronoun('object')} first.",
        f"Write a gentle rhyme-filled barn story where small animals choose a careful way "
        f"after nearly spilling {f['food'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    chief, friend, parent = f["chief"], f["friend"], f["parent"]
    hymn, food, misread = f["hymn"], f["food"], f["misread"]
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {chief.id} and {friend.id}, two small animals in a cozy barn. {parent.id} helps at the end.",
        ),
        QAItem(
            question=f"What did {chief.id} misunderstand?",
            answer=f"{chief.id} thought {misread.phrase} might be a snack, but it was really just a paper thing. That mix-up is why the careful warning mattered.",
        ),
        QAItem(
            question="What did the careful friend say?",
            answer=f"{friend.id} warned that {hymn.label} is for singing, not for snacking, and that {food.label} belongs in a bowl. The warning helped keep the mess small.",
        ),
    ]
    if f["outcome"] == "averted":
        items.append(QAItem(
            question="How did the story end?",
            answer=f"It ended safely, with the animals choosing to keep the food away from the hymn book. The rhyme stayed cheerful and nothing spilled.",
        ))
    else:
        items.append(QAItem(
            question="How did the grown-up help?",
            answer=f"{parent.id} cleaned the spill, reminded everyone to look twice, and showed them a safer way to handle the food. The lesson turned the mistake into a careful habit.",
        ))
    return items


KNOWLEDGE = {
    "hymnal": [("What is a hymnal?", "A hymnal is a book of hymns, which are songs sung gently, often in a group.")],
    "spaghetti": [("What is spaghetti?", "Spaghetti is a long kind of pasta that people usually eat with a fork and a bowl.")],
    "careful": [("What does it mean to be careful?", "Being careful means looking closely and moving gently so you do not cause trouble.")],
    "rhyme": [("What is a rhyme?", "A rhyme is when words sound alike at the end, like sing and spring.")],
    "spilled": [("What happens when something spills?", "When something spills, it leaks or tips out of its container and makes a mess.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["hymn"].id, world.facts["food"].id, "careful", "rhyme"}
    if world.facts["food"].meters["spilled"] >= THRESHOLD:
        tags.add("spilled")
    out: list[QAItem] = []
    for key in ["hymnal", "spaghetti", "careful", "rhyme", "spilled"]:
        if key in tags:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(question=q, answer=a))
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
    for e in world.entities.values():
        meters = {k: v for k, v in getattr(e, "meters", {}).items() if v}
        memes = {k: v for k, v in getattr(e, "memes", {}).items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if getattr(e, "traits", None):
            bits.append(f"traits={getattr(e, 'traits')}")
        if getattr(e, "role", ""):
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} {bits}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: the chosen foods and misunderstandings do not make a plausible cautionary spill.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def outcome_of(params: StoryParams) -> str:
    if params.delay == 0:
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], params.delay) else "recovered"


ASP_RULES = r"""
hazard(Food, Misread) :- spillable(Food), edible(Misread).
sensible(Response) :- response(Response), sense(Response, S), sense_min(M), S >= M.
outcome(averted) :- chosen_delay(D), D = 0.
outcome(contained) :- chosen_delay(D), chosen_response(R), power(R, P), D > 0, P >= D + 1.
outcome(recovered) :- chosen_delay(D), chosen_response(R), power(R, P), D > 0, P < D + 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid in HYMNS:
        lines.append(asp.fact("hymn", hid))
    for fid, f in FOODS.items():
        lines.append(asp.fact("food", fid))
        if f.spillable:
            lines.append(asp.fact("spillable", fid))
        if f.edible:
            lines.append(asp.fact("edible", fid))
    for mid, m in MISREADS.items():
        lines.append(asp.fact("misread", mid))
        if m.edible:
            lines.append(asp.fact("edible", mid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show hazard/2."))
    return sorted(set(asp.atoms(model, "hazard")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_delay", params.delay),
        asp.fact("chosen_response", params.response),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: hazard gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("  only in python:", sorted(py - cl))
        print("  only in clingo:", sorted(cl - py))
    py_s = {r.id for r in sensible_responses()}
    cl_s = set(asp_sensible())
    if py_s == cl_s:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: story generation produced empty output.")
    else:
        print("OK: story generation smoke test passed.")
    cases = CURATED[:]
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print("OK: ASP outcome matches Python outcome.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld: hymnal, spaghetti, caution, misunderstanding, rhyme.")
    ap.add_argument("--chief", choices=CHIEF_NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
    ap.add_argument("--hymn", choices=HYMNS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--misread", choices=MISREADS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = valid_combos()
    if not combos:
        raise StoryError(explain_rejection())
    hymn, food, misread = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    return StoryParams(
        chief=args.chief or rng.choice(CHIEF_NAMES),
        chief_species="mouse",
        friend=args.friend or rng.choice([n for n in FRIEND_NAMES if n != args.chief]),
        friend_species="rabbit",
        parent=args.parent or rng.choice(PARENT_NAMES),
        parent_species="goat",
        hymn=args.hymn or hymn,
        food=args.food or food,
        misread=args.misread or misread,
        response=response,
        delay=args.delay if args.delay is not None else rng.randint(0, 2),
    )


def generate(params: StoryParams) -> StorySample:
    chief = Creature(params.chief, params.chief_species, params.chief, "small", "curious", "hymns", role="chief", type="mouse")
    friend = Creature(params.friend, params.friend_species, params.friend, "small", "cautious", "tidy nests", role="friend", type="rabbit")
    parent = Creature(params.parent, params.parent_species, params.parent, "big", "calm", "helping", role="parent", type="goat")
    hymn = copy.deepcopy(HYMNS[params.hymn]); hymn.id = params.hymn
    food = copy.deepcopy(FOODS[params.food]); food.id = params.food
    misread = copy.deepcopy(MISREADS[params.misread]); misread.id = params.misread
    world = tell(chief, friend, parent, hymn, food, misread, RESPONSES[params.response], params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("Milo", "mouse", "Penny", "rabbit", "Mum", "goat", "hymnal", "spaghetti", "napkin", "scoop", 0),
    StoryParams("Nora", "mouse", "Otis", "rabbit", "Dad", "goat", "songbook", "spaghetti", "recipe", "wipe", 1),
    StoryParams("Luna", "mouse", "Clover", "rabbit", "Gran", "goat", "hymnal", "soup", "napkin", "pause", 2),
]


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
        print(asp_program("#show hazard/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(asp_valid_combos())} hazard pairs:")
        for a, b in asp_valid_combos():
            print(f"  {a} / {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.chief} & {p.friend}: {p.hymn} / {p.food} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
