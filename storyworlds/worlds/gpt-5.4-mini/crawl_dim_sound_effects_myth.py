#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/crawl_dim_sound_effects_myth.py
=================================================================

A standalone story world for a small myth-like cave crawl with sound effects.

Premise
-------
A child and a guide enter a crawl-dim tunnel beneath an old hill to recover a
lost shrine bell. The tunnel is too small to stand in, the dark is thick, and
the way forward depends on careful movement, a useful sound, and a final
revelation that changes the cave from spooky to safe.

The world is built around:
- typed entities with physical meters and emotional memes
- a causal world model that drives prose
- a reasonableness gate for valid stories
- an inline ASP twin for parity checks
- child-facing Q&A grounded in the simulated state

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/crawl_dim_sound_effects_myth.py
    python storyworlds/worlds/gpt-5.4-mini/crawl_dim_sound_effects_myth.py --all
    python storyworlds/worlds/gpt-5.4-mini/crawl_dim_sound_effects_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/crawl_dim_sound_effects_myth.py --trace
    python storyworlds/worlds/gpt-5.4-mini/crawl_dim_sound_effects_myth.py --verify
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
    region: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "goddess"}
        male = {"boy", "father", "dad", "man", "king", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "queen": "queen", "king": "king"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    crawl_dim: bool
    dark: str
    echo: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    label: str
    lost: str
    sound: str
    prize: str
    danger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    sound: str
    helps: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    cave = world.entities.get("cave")
    bell = world.entities.get("bell")
    if cave and bell and bell.meters["found"] >= THRESHOLD and ("echoed",) not in world.fired:
        world.fired.add(("echoed",))
        cave.memes["wonder"] += 1
        out.append("__echo__")
    return out


CAUSAL_RULES = [Rule("echo", "myth", _r_echo)]


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


def hazard_at_risk(place: Place, quest: Quest) -> bool:
    return place.crawl_dim and "crawl" in quest.tags


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for p in PLACES:
        for q in QUESTS:
            for t in TOOLS:
                if hazard_at_risk(PLACES[p], QUESTS[q]):
                    combos.append((p, q, t))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.response not in RESPONSES:
        return "?"
    return "safe" if RESPONSES[params.response].power >= QUESTS[params.quest].danger_level + params.delay else "failed"


def _do_quest(world: World, hero: Entity, guide: Entity, place: Place, quest: Quest, tool: Tool) -> None:
    hero.meters["courage"] += 1
    hero.meters["movement"] += 1
    if place.crawl_dim:
        hero.meters["crawl"] += 1
    hero.memes["dread"] += 1
    world.get("cave").meters["shadow"] += 1
    world.get("bell").meters["near"] += 1
    propagate(world, narrate=False)


def run_story(world: World, hero: Entity, guide: Entity, parent: Entity, place: Place,
              quest: Quest, tool: Tool, response: Response, delay: int) -> None:
    world.say(f"Long ago, {hero.id} and {guide.id} came to {place.label}, where the path was crawl-dim and the air held its breath.")
    world.say(f"Inside, the old stones whispered {quest.sound} and the lost {quest.label} waited somewhere ahead.")
    world.para()
    world.say(f"{hero.id} wanted to follow the trail, but the tunnel was so small they had to crawl on hands and knees.")
    world.say(f'The dark felt thick, and every step answered with a soft {tool.sound} from their lantern-gourd and rope.')

    hero.memes["want"] += 1
    guide.memes["warn"] += 1
    world.say(f'"Be careful," {guide.id} said. "{quest.danger}"')
    hero.memes["bravery"] += 1
    world.say(f'But {hero.id} listened to the cave and said, "I can do it. {tool.sound}"')

    world.para()
    if delay <= 0:
        world.say(f"{hero.id} moved slowly, {tool.sound}! {quest.sound}! and the narrow way stayed calm.")
        world.get("bell").meters["found"] += 1
        world.get("bell").meters["recovered"] += 1
        world.get("cave").meters["shadow"] = max(0.0, world.get("cave").meters["shadow"] - 1)
        world.say(f"At last, the lost bell hung from a root, and {hero.id} lifted it free without making the cave shake.")
        guide.memes["relief"] += 1
        hero.memes["joy"] += 1
        world.para()
        world.say(f"Then came a bright {quest.sound.upper()}-ring, and the tunnel answered with a soft, happy echo.")
        world.say(f"The cave was still crawl-dim, but it was no longer scary. It felt like a home that had remembered its song.")
        world.get("cave").meters["safe"] += 1
        outcome = "safe"
    else:
        world.say(f"{hero.id} rushed once, and the stones answered with a hard {quest.sound}! The ceiling dust trembled.")
        world.get("cave").meters["danger"] += 1
        guide.memes["fear"] += 1
        if response.power >= quest.danger_level + delay:
            world.say(f"{parent.label_word.capitalize()} came quickly and used {response.text.replace('{quest}', quest.label)}.")
            world.say(f"The trouble settled at once. The bell was recovered, and the cave's scary hum went quiet.")
            world.get("bell").meters["found"] += 1
            world.get("bell").meters["recovered"] += 1
            world.get("cave").meters["safe"] += 1
            outcome = "safe"
        else:
            world.say(f"{parent.label_word.capitalize()} came quickly and {response.fail.replace('{quest}', quest.label)}.")
            world.say("The sound bounced bigger and bigger, and the little group had to back out of the tunnel.")
            world.get("cave").meters["danger"] += 1
            outcome = "failed"
    world.facts.update(outcome=outcome)


def tell(place: Place, quest: Quest, tool: Tool, response: Response,
         hero_name: str = "Mira", hero_gender: str = "girl",
         guide_name: str = "Oren", guide_gender: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(hero_name, "character", hero_gender, role="hero"))
    guide = world.add(Entity(guide_name, "character", guide_gender, role="guide"))
    parent = world.add(Entity("Parent", "character", parent_type, role="parent"))
    cave = world.add(Entity("cave", "place", "cave", label=place.label))
    bell = world.add(Entity("bell", "thing", "bell", label=quest.label))
    world.facts.update(hero=hero, guide=guide, parent=parent, place=place, quest=quest, tool=tool, response=response, delay=delay)
    run_story(world, hero, guide, parent, place, quest, tool, response, delay)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, quest, tool, response = f["place"], f["quest"], f["tool"], f["response"]
    return [
        f'Write a myth-style story for a 3-to-5-year-old using the word "crawl-dim" and the sound "{tool.sound}".',
        f"Tell a small cave-quest story where a child enters {place.label}, hears {quest.sound}, and finds the lost {quest.label}.",
        f'Write a gentle myth where {f["hero"].id} and {f["guide"].id} crawl through a dim tunnel, make sound effects, and end safely.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, guide, parent = f["hero"], f["guide"], f["parent"]
    place, quest, tool = f["place"], f["quest"], f["tool"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, {guide.id}, and the grown-up who helps them. They go into {place.label} to find the lost {quest.label}."),
        ("Why did they have to crawl?",
         f"The tunnel was crawl-dim and too small to stand up in. Crawling helped them move carefully without knocking the cave stones."),
        ("What sound did the cave make?",
         f"It made {quest.sound} sounds, and later the recovered bell made a bright ringing echo. That sound told everyone the quest had changed from scary to safe."),
    ]
    if world.facts.get("outcome") == "safe":
        qa.append((
            "How did the story end?",
            f"It ended safely, with the lost {quest.label} found and the cave feeling like a home again. The echo stayed, but the danger was gone."
        ))
        qa.append((
            f"What helped {hero.id} keep going?",
            f"{tool.phrase} and its small {tool.sound} sound helped {hero.id} keep steady. The guide's warning also helped {hero.id} slow down."
        ))
    else:
        qa.append((
            "What happened when the story got too risky?",
            f"The grown-up had to step in, but the first plan did not work. The group backed out before the cave could become truly dangerous."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["place"].tags) | set(world.facts["quest"].tags) | set(world.facts["tool"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


PLACE = Place("hill_cave", "the hill cave", True, "crawl-dim", "echo", {"crawl", "myth", "cave"})
PLACES = {"hill_cave": PLACE}

QUESTS = {
    "bell": Quest("bell", "bell", "lost bell", "ding-ding", "recovered", "danger_level=1", {"crawl", "myth", "bell"}),
}
# quick attribute addition for the simple model
QUESTS["bell"].danger_level = 1  # type: ignore[attr-defined]

TOOLS = {
    "gourd": Tool("gourd", "lantern-gourd", "a lantern-gourd", "tap-tap", "helped keep the way steady", {"light", "sound"}),
    "rope": Tool("rope", "rope", "a rope", "swish", "helped the child keep balance", {"sound"}),
}

RESPONSES = {
    "lantern": Response("lantern", 3, 3, "shone a lantern over the root and guided the child back", "shone a lantern, but the cave's hard echo kept growing", "shone a lantern over the root and guided the child back", {"light"}),
    "call_help": Response("call_help", 2, 2, "called for help and led everyone to the safe path", "called for help, but it was not enough to settle the sound", "called for help and led everyone to the safe path", {"help"}),
    "song": Response("song", 1, 1, "sang a soft song", "sang a soft song, but the cave was too loud to calm", "sang a soft song", {"sound"}),
}

KNOWLEDGE = {
    "crawl": [("Why do people crawl in a small cave?",
               "People crawl in a small cave because the space is too low to stand up in. Crawling helps them move safely without bumping the roof.")],
    "cave": [("What is a cave?",
              "A cave is a hollow place in the ground or a hill. It can be dark and echo sounds.")],
    "echo": [("What is an echo?",
              "An echo is a sound that bounces off walls and comes back again. Caves often make echoes." )],
    "light": [("Why do caves need light?",
               "Caves are dark, so a light helps people see the ground and the walls. Light makes it easier to move carefully.")],
    "sound": [("What are sound effects in a story?",
               "Sound effects are written sounds like ding-ding or tap-tap. They help you imagine what the characters hear.")],
    "bell": [("Why does a bell ring?",
              "A bell rings when it is moved, struck, or shaken. Its sound can be bright and clear.")],
}
KNOWLEDGE_ORDER = ["crawl", "cave", "echo", "light", "sound", "bell"]


@dataclass
class StoryParams:
    place: str
    quest: str
    tool: str
    response: str
    hero: str
    hero_gender: str
    guide: str
    guide_gender: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic crawl-dim story world with sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
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


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "hill_cave"),
        asp.fact("crawl_dim", "hill_cave"),
        asp.fact("quest", "bell"),
        asp.fact("tool", "gourd"),
        asp.fact("tool", "rope"),
        asp.fact("response", "lantern"),
        asp.fact("response", "call_help"),
        asp.fact("response", "song"),
        asp.fact("sense_min", SENSE_MIN),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,Q,T) :- place(P), quest(Q), tool(T), crawl_dim(P).
sensible(R) :- response(R), response_sense(R,S), sense_min(M), S >= M.
outcome(safe) :- chosen_response(R), response_power(R,P), quest_danger(Q,D), delay(X), P >= D + X.
outcome(failed) :- chosen_response(R), response_power(R,P), quest_danger(Q,D), delay(X), P < D + X.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    else:
        print("OK: smoke test passed.")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("(No story: the chosen response is too weak for this world.)")
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.quest is None or c[1] == args.quest) and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, tool = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    parent = args.parent or rng.choice(["mother", "father"])
    hero_name = rng.choice(["Mira", "Ivo", "Nia", "Tao", "Lena"])
    guide_name = rng.choice(["Oren", "Pax", "Suri", "Galen", "Rin"])
    hero_gender = rng.choice(["girl", "boy"])
    guide_gender = rng.choice(["girl", "boy"])
    delay = rng.randint(0, 1)
    return StoryParams(place, quest, tool, response, hero_name, hero_gender, guide_name, guide_gender, parent, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], TOOLS[params.tool], RESPONSES[params.response],
                 params.hero, params.hero_gender, params.guide, params.guide_gender, params.parent, params.delay)
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


CURATED = [
    StoryParams("hill_cave", "bell", "gourd", "lantern", "Mira", "girl", "Oren", "boy", "mother", 0),
    StoryParams("hill_cave", "bell", "rope", "call_help", "Ivo", "boy", "Suri", "girl", "father", 1),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
