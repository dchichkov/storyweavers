#!/usr/bin/env python3
"""
storyworlds/worlds/frog_lesson_learned_comedy.py
================================================

A small comedic storyworld about a frog who learns a lesson the hard way.

Premise:
- A frog wants something silly and convenient.
- The frog's plan causes a funny mess or awkward problem.
- A careful helper or the frog itself notices the consequence.
- The frog learns a simple lesson and ends with a better choice.

This world is intentionally small and classical: one main character, a few props,
and a state-driven turn that makes the ending feel earned.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"frog"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Pond:
    name: str = "the pond"
    safe_edges: set[str] = field(default_factory=lambda: {"lily_pad", "mud_bank"})


@dataclass
class Trinket:
    label: str
    phrase: str
    region: str
    mess_sensitive: set[str] = field(default_factory=lambda: {"muddy", "splashy"})
    plural: bool = False


@dataclass
class HelpfulThing:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)  # mess kinds it solves
    safe_places: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, pond: Pond) -> None:
        self.pond = pond
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
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
        import copy
        c = World(self.pond)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


@dataclass
class StoryParams:
    pond: str
    action: str
    trinket: str
    name: str
    seed: Optional[int] = None


PONDS = {
    "pond": Pond(name="the pond"),
    "lily_pond": Pond(name="the lily pond"),
    "mud_pond": Pond(name="the muddy pond"),
}

ACTIONS = {
    "dive": {
        "verb": "dive into the pond",
        "gerund": "diving into the pond",
        "rush": "splash straight in",
        "mess": "splashy",
        "lesson": "look before leaping",
        "setting": "at the pond",
    },
    "mud_wade": {
        "verb": "wade through the mud",
        "gerund": "wading through mud",
        "rush": "plop into the mud",
        "mess": "muddy",
        "lesson": "choose the muddy shortcut only when you really mean it",
        "setting": "near the muddy edge",
    },
    "bug_hunt": {
        "verb": "hunt for bugs",
        "gerund": "hunting for bugs",
        "rush": "dash after a buzzing bug",
        "mess": "splashy",
        "lesson": "slow down before chasing shiny things",
        "setting": "by the reeds",
    },
}

TRINKETS = {
    "crown": Trinket(label="crown", phrase="a shiny paper crown", region="head"),
    "sign": Trinket(label="sign", phrase="a tiny wooden sign", region="feet"),
    "cookie": Trinket(label="cookie", phrase="a crumbly cookie on a plate", region="mouth"),
    "book": Trinket(label="book", phrase="a picture book with a ribbon bookmark", region="hands"),
}

HERO_NAMES = ["Frodo", "Pip", "Milo", "Niko", "Lenny", "Toby"]


def reasonableness_gate(action: str, trinket: str) -> bool:
    act = ACTIONS[action]
    tr = TRINKETS[trinket]
    if tr.region in {"head", "hands", "mouth", "feet"}:
        return True
    return False


def select_help(action: str, trinket: str) -> Optional[HelpfulThing]:
    act = ACTIONS[action]
    tr = TRINKETS[trinket]
    for h in HELPS:
        if act["mess"] in h.helps and tr.region in h.safe_places:
            return h
    return None


def predict_mess(world: World, hero: Entity, action: str, trinket_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(hero.id), action, narrate=False)
    tr = sim.get(trinket_id)
    return {
        "messy": tr.meters.get("messy", 0.0) >= THRESHOLD,
        "silly": hero.memes.get("silly", 0.0),
    }


def _do_action(world: World, hero: Entity, action: str, narrate: bool = True) -> None:
    act = ACTIONS[action]
    hero.meters[act["mess"]] = hero.meters.get(act["mess"], 0.0) + 1
    hero.memes["glee"] = hero.memes.get("glee", 0.0) + 1
    # muddy or splashy actions can ruin held trinkets unless protected.
    for item in world.worn_items(hero):
        if item.id in world.facts.get("protected_items", set()):
            continue
        if item.meters.get("messy", 0.0) >= THRESHOLD:
            continue
        if item.label == "paper crown" and act["mess"] in {"splashy", "muddy"}:
            sig = ("mess", item.id, act["mess"])
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["messy"] = 1.0
            if narrate:
                world.say(f"{hero.pronoun('possessive').capitalize()} {item.label} got soggy and droopy.")


def _learn(world: World, hero: Entity, lesson: str) -> None:
    hero.memes["lesson"] = hero.memes.get("lesson", 0.0) + 1
    hero.memes["silly"] = 0.0
    world.say(f"{hero.pronoun('subject').capitalize()} learned a lesson: {lesson}.")


def tell(pond: Pond, action_id: str, trinket_id: str, name: str = "Pip") -> World:
    world = World(pond)
    hero = world.add(Entity(id=name, kind="character", type="frog", label="frog"))
    pondy = world.add(Entity(id="pond", kind="thing", type="pond", label=pond.name))
    tr = world.add(Entity(
        id="trinket",
        kind="thing",
        type=trinket_id,
        label=TRINKETS[trinket_id].label,
        phrase=TRINKETS[trinket_id].phrase,
        owner=hero.id,
        worn_by=hero.id,
        meters={"messy": 0.0},
    ))

    world.say(f"{hero.id} was a small frog who loved jokes, splashes, and shiny things.")
    world.say(f"One day, {hero.id} found {tr.phrase} and wore it like it was a royal treasure.")
    world.para()
    world.say(f"{hero.id} hopped down to {pondy.label} and wanted to {ACTIONS[action_id]['verb']}.")
    world.say(f"{hero.pronoun('subject').capitalize()} tried to {ACTIONS[action_id]['rush']} while the crown sat right on top of the plan.")

    pred = predict_mess(world, hero, action_id, tr.id)
    if pred["messy"]:
        world.say(f"Then the frog noticed that {tr.label} would get ruined, which was a very silly problem to discover late.")
        help_obj = select_help(action_id, trinket_id)
        if help_obj:
            world.say(f"A nearby helper smiled and said, \"How about we {help_obj.prep}?\"")
            world.facts["protected_items"] = {tr.id}
            tr.meters["messy"] = 0.0
            world.para()
            world.say(f"{hero.id} blinked, nodded, and took the safer idea.")
            world.say(f"They {help_obj.tail}, and soon {hero.id} was {ACTIONS[action_id]['gerund']} without ruining the crown.")
            _learn(world, hero, ACTIONS[action_id]["lesson"])
        else:
            world.say(f"No good fix fit the tiny problem, so {hero.id} sat back and made a wiser choice.")
            _learn(world, hero, ACTIONS[action_id]["lesson"])
    else:
        world.facts["protected_items"] = set()

    world.para()
    if tr.meters.get("messy", 0.0) >= THRESHOLD:
        world.say(f"In the end, the crown was soggy, and {hero.id} laughed at the very expensive lesson.")
    else:
        world.say(f"In the end, the crown stayed clean, and {hero.id} hopped away with a smarter grin.")
    world.facts.update(hero=hero, pond=pond, action=action_id, trinket=tr, learned=True)
    return world


HELPS = [
    HelpfulThing(
        id="lily_pad",
        label="a lily pad",
        prep="move the crown onto a lily pad first",
        tail="moved the crown to the lily pad and then hopped carefully",
        helps={"splashy"},
        safe_places={"head", "hands"},
    ),
    HelpfulThing(
        id="mud_boots",
        label="mud boots",
        prep="put on mud boots before the muddy wade",
        tail="pulled on mud boots and then waded with fewer regrets",
        helps={"muddy"},
        safe_places={"feet"},
    ),
    HelpfulThing(
        id="leaf_cap",
        label="a leaf cap",
        prep="tuck the paper crown under a big leaf",
        tail="tucked the crown under a leaf and bounced on",
        helps={"splashy", "muddy"},
        safe_places={"head"},
    ),
]

LESSONS = {
    "splashy": "look before leaping",
    "muddy": "choose the muddy shortcut only when you really mean it",
}

KNOWLEDGE = {
    "frog": [
        ("What is a frog?",
         "A frog is a small animal that likes ponds, hops on strong legs, and often lives near water."),
        ("Where do frogs like to live?",
         "Frogs like to live near ponds, marshes, and other wet places."),
    ],
    "pond": [
        ("What is a pond?",
         "A pond is a small body of still water, smaller than a lake."),
    ],
    "muddy": [
        ("What makes mud?",
         "Mud is made when dirt mixes with water and turns soft and sticky."),
    ],
    "splashy": [
        ("What does splashy mean?",
         "Splashy means full of splashes of water."),
    ],
}
KNOWLEDGE_ORDER = ["frog", "pond", "muddy", "splashy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a young child about a frog who tries to {ACTIONS[f["action"]]["verb"]} and learns a lesson.',
        f"Tell a comedy story where {f['hero'].id} the frog wears {f['trinket'].phrase} and discovers a safer way to play.",
        f'Write a short, silly story that includes a frog, {f["pond"].name}, and the idea "lesson learned".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    tr = f["trinket"]
    action = ACTIONS[f["action"]]
    qa = [
        QAItem(
            question=f"What kind of animal is {hero.id}?",
            answer=f"{hero.id} is a frog, and it likes silly adventures near water.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {f['pond'].name}?",
            answer=f"{hero.id} wanted to {action['verb']}. That sounded fun, but it caused a problem for {tr.label}.",
        ),
        QAItem(
            question=f"What shiny thing was {hero.id} wearing before the lesson?",
            answer=f"{hero.id} was wearing {tr.phrase}, which made the whole plan extra funny.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned to {action['lesson']}. That was the point of the story.",
        ),
    ]
    if f.get("learned"):
        qa.append(QAItem(
            question=f"How did the story end after {hero.id} made a smarter choice?",
            answer=f"The ending showed {hero.id} choosing the safer plan, and the little frog looked proud instead of soggy.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"frog", "pond"}
    if world.facts["action"] in {"mud_wade"}:
        tags.add("muddy")
    else:
        tags.add("splashy")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is reasonable if the chosen trinket can be ruined by the action.
trinket_at_risk(A,T) :- action(A), trinket(T), action_mess(A,M), sensitive(T,M).
has_help(A,T) :- trinket_at_risk(A,T), help(H), action_mess(A,M), helps(H,M), safe_for(H,T).
valid(A,T) :- action(A), trinket(T), trinket_at_risk(A,T), has_help(A,T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("action_mess", aid, a["mess"]))
    for tid, t in TRINKETS.items():
        lines.append(asp.fact("trinket", tid))
        lines.append(asp.fact("sensitive", tid, "muddy"))
        lines.append(asp.fact("sensitive", tid, "splashy"))
        lines.append(asp.fact("safe_for", "leaf_cap", tid))
    for h in HELPS:
        lines.append(asp.fact("help", h.id))
        for m in sorted(h.helps):
            lines.append(asp.fact("helps", h.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for a in ACTIONS:
        for t in TRINKETS:
            if reasonableness_gate(a, t) and select_help(a, t):
                out.append((a, t))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic frog storyworld with a lesson learned.")
    ap.add_argument("--pond", choices=PONDS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--trinket", choices=TRINKETS)
    ap.add_argument("--name", choices=HERO_NAMES)
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
    if args.action and args.trinket:
        if not (reasonableness_gate(args.action, args.trinket) and select_help(args.action, args.trinket)):
            raise StoryError("That frog plan is too unreasonable for this storyworld.")
    combos = [
        (a, t) for a, t in valid_combos()
        if (args.action is None or a == args.action)
        and (args.trinket is None or t == args.trinket)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    action, trinket = rng.choice(sorted(combos))
    pond = args.pond or rng.choice(sorted(PONDS))
    name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(pond=pond, action=action, trinket=trinket, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(PONDS[params.pond], params.action, params.trinket, params.name)
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


CURATED = [
    StoryParams(pond="pond", action="dive", trinket="crown", name="Pip"),
    StoryParams(pond="mud_pond", action="mud_wade", trinket="sign", name="Milo"),
    StoryParams(pond="lily_pond", action="bug_hunt", trinket="book", name="Frodo"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(sorted(set(asp.atoms(model, "valid"))))
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
            params = resolve_params(args, random.Random(seed))
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
