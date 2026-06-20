#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/savage_nifty_breather_bad_ending_magic_adventure.py
====================================================================================

A standalone storyworld for a tiny adventure tale with magic, a bad ending,
and the seed words "savage", "nifty", and "breather".

Premise:
- Two kids go on a small adventure with a magic map and a nifty gadget.
- They chase a glowing trail into a cave-like place.
- One child ignores a warning, the magic goes wrong, and the ending is sad.
- The story stays child-facing, concrete, and state-driven.

This script follows the storyworld contract:
- typed entities with meters and memes
- Python reasonableness gate + inline ASP twin
- generate / emit / build_parser / resolve_params / main
- QA grounded in simulated state, not rendered text
- verification that exercises normal generation and ASP parity
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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


@dataclass
class Place:
    id: str
    label: str
    scene: str
    dark_spot: str
    danger_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicItem:
    id: str
    label: str
    phrase: str
    glow: str
    purpose: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    flares: bool = False
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_collapse(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["glitched"] < THRESHOLD:
            continue
        sig = ("collapse", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "cave" in world.entities:
            world.get("cave").meters["danger"] += 1
        for kid in world.entities.values():
            if kid.kind == "character":
                kid.memes["fear"] += 1
        out.append("__collapse__")
    return out


CAUSAL_RULES = [Rule("collapse", "physical", _r_collapse)]


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


def hazard_at_risk(magic: MagicItem, hazard: Hazard) -> bool:
    return magic.safe and hazard.flares


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_strength(hazard: Hazard, delay: int) -> int:
    return 2 + delay


def is_contained(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= fire_strength(hazard, delay)


def predict_bad(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    _do_magic(sim, sim.get(hazard_id), narrate=False)
    return {"glitched": sim.get(hazard_id).meters["glitched"] >= THRESHOLD,
            "danger": sim.get("cave").meters["danger"]}


def _do_magic(world: World, hazard_ent: Entity, narrate: bool = True) -> None:
    hazard_ent.meters["glitched"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, a: Entity, b: Entity, place: Place) -> None:
    a.memes["wonder"] += 1
    b.memes["wonder"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} set out on a little adventure in "
        f"{place.label}. {place.scene}"
    )


def find_trail(world: World, place: Place, a: Entity, b: Entity) -> None:
    world.say(
        f"They followed a glittering trail toward {place.dark_spot}, where the dark "
        f"felt deep and exciting."
    )
    world.say(f'"This is a nifty place," {a.id} said, grinning at the mystery.')


def show_magic(world: World, item: MagicItem, a: Entity, b: Entity) -> None:
    world.say(
        f'{b.id} held up {item.phrase}. It {item.glow}, and the glow made the path feel '
        f"safe enough to try."
    )
    world.say(f'"We only need one more breather," {a.id} whispered, hoping the cave would stay calm.')


def warn(world: World, cautious: Entity, bold: Entity, item: MagicItem, hazard: Hazard, place: Place) -> None:
    pred = predict_bad(world, "hazard")
    cautious.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{cautious.id} bit {cautious.pronoun("possessive")} lip. "{bold.id}, don\'t use '
        f"{item.label} here. If it goes wrong, {hazard.label} can start a trouble {place.danger_word}."
    )


def defy(world: World, bold: Entity, item: MagicItem) -> None:
    bold.memes["defiance"] += 1
    world.say(
        f'"I can do it," {bold.id} said, and reached for {item.label} anyway.'
    )


def trigger(world: World, hazard: Entity, item: MagicItem, place: Place) -> None:
    _do_magic(world, hazard)
    world.say(
        f"With a tiny flash, {item.label} went wild. The light kinked sideways, "
        f"and a sharp spark skipped off the cave wall."
    )
    world.say(f"The adventure turned savage in an instant, and everyone froze.")


def alarm(world: World, cautious: Entity, bold: Entity, place: Place) -> None:
    world.say(f'"{bold.id}! Stop!" {cautious.id} shouted.')
    world.say(f'"{place.label_word if hasattr(place, "label_word") else "Help"}!"')


def rescue(world: World, parent: Entity, response: Response, hazard_ent: Entity, place: Place) -> None:
    hazard_ent.meters["glitched"] = 0.0
    world.get("cave").meters["danger"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came running and {response.text.replace('{place}', place.label)}."
    )
    world.say(
        f"The spark died down, but the room still smelled smoky, and the magic map had gone black."
    )


def bad_ending(world: World, parent: Entity, bold: Entity, cautious: Entity, place: Place) -> None:
    bold.memes["fear"] += 1
    cautious.memes["fear"] += 1
    world.say(
        f"{parent.label_word.capitalize()} got them out fast, but the glowing path was gone "
        f"and the cave shook loose dust onto the floor."
    )
    world.say(
        f"The treasure they had hoped to find was buried behind a cracked stone, and the old magic "
        f"would not come back."
    )
    world.say(
        f"They went home in silence, with no prize, only the memory of the dark {place.danger_word}."
    )


def lesson(world: World, parent: Entity, bold: Entity, cautious: Entity, item: MagicItem) -> None:
    bold.memes["lesson"] += 1
    cautious.memes["lesson"] += 1
    world.say(
        f"That night, {parent.label_word.capitalize()} said the kindest truth: "
        f'"Magic is nifty, but only when you use it safely."'
    )
    world.say(
        f"{bold.id} and {cautious.id} promised to ask for help next time, and to keep {item.label} for "
        f"quiet, careful games."
    )


def tell(place: Place, magic: MagicItem, hazard: Hazard, response: Response,
         bold_name: str = "Mila", bold_gender: str = "girl",
         cautious_name: str = "Jasper", cautious_gender: str = "boy",
         parent_type: str = "mother", delay: int = 1,
         bold_age: int = 6, cautious_age: int = 7, relation: str = "friends") -> World:
    world = World()
    bold = world.add(Entity(id=bold_name, kind="character", type=bold_gender,
                            role="instigator", traits=["bold"], age=bold_age))
    cautious = world.add(Entity(id=cautious_name, kind="character", type=cautious_gender,
                                role="cautioner", traits=["careful"], age=cautious_age,
                                attrs={"relation": relation}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    cave = world.add(Entity(id="cave", type="place", label=place.label))
    hazard_ent = world.add(Entity(id="hazard", type="hazard", label=hazard.label))
    item = world.add(Entity(id="magic", type="magic", label=magic.label))

    setup(world, bold, cautious, place)
    find_trail(world, place, bold, cautious)
    world.para()
    show_magic(world, magic, bold, cautious)
    warn(world, cautious, bold, magic, hazard, place)
    defy(world, bold, magic)
    world.para()
    trigger(world, hazard_ent, magic, place)
    alarm(world, cautious, bold, place)
    contained = is_contained(response, hazard, delay)
    world.facts.update(instigator=bold, cautioner=cautious, parent=parent,
                       place=place, magic=magic, hazard=hazard, response=response,
                       contained=contained, delay=delay, relation=relation)
    world.para()
    if contained:
        rescue(world, parent, response, hazard_ent, place)
        lesson(world, parent, bold, cautious, magic)
        world.say("They found a safer road home, where the lanterns were ordinary and kind.")
    else:
        bad_ending(world, parent, bold, cautious, place)
    return world


PLACES = {
    "cave": Place("cave", "the moon cave", "The floor sparkled with glassy pebbles, and the walls shone like silver.", "the deep tunnel", "mystery", {"cave", "adventure"}),
    "ruins": Place("ruins", "the old ruins", "Broken arches leaned over mossy steps, and vines curled like green ropes.", "the cracked hall", "echo", {"ruins", "adventure"}),
    "forest": Place("forest", "the lantern forest", "Tall trees held little circles of light, and every branch seemed to wait for a secret.", "the dark hollow", "shadow", {"forest", "adventure"}),
}

MAGIC_ITEMS = {
    "map": MagicItem("map", "magic map", "a magic map", "pulsed with blue light", "find the path", True, {"magic", "adventure"}),
    "stone": MagicItem("stone", "glow stone", "a nifty glow stone", "shimmered like a tiny moon", "light the way", True, {"magic", "adventure"}),
    "whistle": MagicItem("whistle", "whisper whistle", "a silver whistle", "hummed with a soft note", "call for help", True, {"magic", "adventure"}),
}

HAZARDS = {
    "curse": Hazard("curse", "the curse", "a sleeping curse", True, {"magic", "bad_ending"}),
    "mist": Hazard("mist", "the mist", "a trick mist", True, {"magic", "bad_ending"}),
}

RESPONSES = {
    "shield": Response("shield", 3, 3, "held up a shield charm and pushed the bad spark away", "tried a shield charm, but the bad spark was already too wild", "held up a shield charm and pushed the bad spark away"),
    "song": Response("song", 2, 2, "sang a steadying song that calmed the magic down", "sang a song, but the magic kept twisting", "sang a steadying song that calmed the magic down"),
    "cloak": Response("cloak", 3, 4, "wrapped the glowing stone in a heavy cloak and smothered the flash", "wrapped it too late, and the flash jumped free", "wrapped the glowing stone in a heavy cloak and smothered the flash"),
}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for h in HAZARDS:
            for m in MAGIC_ITEMS:
                if hazard_at_risk(MAGIC_ITEMS[m], HAZARDS[h]):
                    out.append((p, h, m))
    return out


@dataclass
class StoryParams:
    place: str
    hazard: str
    magic: str
    response: str
    bold_name: str
    bold_gender: str
    cautious_name: str
    cautious_gender: str
    parent: str
    delay: int = 1
    bold_age: int = 6
    cautious_age: int = 7
    relation: str = "friends"
    seed: Optional[int] = None


KNOWLEDGE = {
    "magic": [("What is magic in stories?", "Magic in stories is something surprising that can make impossible things happen, like a glowing map or a talking charm.")],
    "adventure": [("What is an adventure?", "An adventure is a trip or quest where characters go somewhere exciting and face a challenge.")],
    "bad_ending": [("What is a bad ending?", "A bad ending is when the plan goes wrong and the characters do not get the happy prize they wanted.")],
    "cave": [("Why can a cave be scary?", "A cave can be scary because it is dark, quiet, and hard to see inside.")],
    "shield": [("What does a shield do?", "A shield blocks or pushes danger away, so it helps protect someone from harm.")],
    "song": [("Can a calm song help?", "Yes. A calm song can help a frightened person breathe slowly and feel steadier.")],
    "cloak": [("What does a heavy cloak do?", "A heavy cloak can cover and smother a small flash, taking away the air it needs.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly adventure story that includes the words "savage", "nifty", and "breather", and uses magic in a scary way.',
        f"Tell a short adventure where {f['instigator'].id} and {f['cautioner'].id} find {f['magic'].phrase}, ignore a warning, and end with a bad outcome.",
        f"Write a magical cave story for a young child where a nifty thing goes wrong and the ending is sad, but the characters get home safely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["instigator"], f["cautioner"], f["parent"]
    place, magic, hazard = f["place"], f["magic"], f["hazard"]
    qa = [
        ("Who went on the adventure?", f"{a.id} and {b.id} went on the adventure, and {parent.label_word} came to help after the trouble started."),
        ("What made the trail interesting?", f"They found {magic.phrase}, and its glow made the trail feel nifty and exciting."),
        ("What went wrong?", f"{hazard.label.capitalize()} woke up in the cave, the magic went savage, and the bright plan turned into danger."),
    ]
    if f["contained"]:
        qa.append(("Did the magic get fixed?", f"Yes, {f['response'].qa_text} did the job, and the children got out with help."))
    else:
        qa.append(("How did the story end?", "It ended badly. They escaped, but they lost the treasure and the magic path could not be used again."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["place"].tags) | set(world.facts["magic"].tags) | set(world.facts["hazard"].tags)
    out: list[tuple[str, str]] = []
    for key, qa in KNOWLEDGE.items():
        if key in tags:
            out.extend(qa)
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("cave", "curse", "map", "shield", "Mila", "girl", "Jasper", "boy", "mother", 1),
    StoryParams("ruins", "mist", "stone", "song", "Nora", "girl", "Theo", "boy", "father", 1),
    StoryParams("forest", "curse", "whistle", "cloak", "Leo", "boy", "Ava", "girl", "mother", 2),
]


def explain_rejection(magic: MagicItem, hazard: Hazard) -> str:
    if not hazard_at_risk(magic, hazard):
        return f"(No story: {magic.label} does not create the kind of risky magic this bad ending needs.)"
    return "(No story: this combination does not produce a believable bad-ending magic adventure.)"


def outcome_of(params: StoryParams) -> str:
    if is_contained(RESPONSES[params.response], HAZARDS[params.hazard], params.delay):
        return "contained"
    return "bad"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


ASP_RULES = r"""
hazard(F, H) :- magic(F), flares(H).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(P, H, M) :- place(P), hazard(H), magic(M), hazard(H, M).
contained :- chosen_response(R), chosen_hazard(H), chosen_delay(D), power(R, P), severity(H, D, V), P >= V.
bad :- not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MAGIC_ITEMS:
        lines.append(asp.fact("magic", m))
    for h, hv in HAZARDS.items():
        lines.append(asp.fact("hazard", h))
        if hv.flares:
            lines.append(asp.fact("flares", h))
    for r, rv in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, rv.sense))
        lines.append(asp.fact("power", r, rv.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


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


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("chosen_hazard", params.hazard),
        asp.fact("chosen_delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show contained/0.\n#show bad/0."))
    atoms = {a for a, in asp.atoms(model, "contained")}
    return "contained" if atoms else "bad"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    # smoke test normal generation
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    for p in CURATED:
        if asp_outcome(p) != outcome_of(p):
            rc = 1
            print("MISMATCH in outcome:", p)
    print("OK: generation smoke test and outcome parity checked.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny magic adventure with a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--magic", choices=MAGIC_ITEMS)
    ap.add_argument("--hazard", choices=HAZARDS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, hazard, magic = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place, hazard, magic, response,
                       rng.choice(["Mila", "Nora", "Ava", "Lia", "Leo", "Theo"]),
                       rng.choice(["girl", "boy"]),
                       rng.choice(["Jasper", "Finn", "Tess", "Mia", "Eli"]),
                       rng.choice(["girl", "boy"]),
                       parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MAGIC_ITEMS[params.magic], HAZARDS[params.hazard],
                 RESPONSES[params.response], params.bold_name, params.bold_gender,
                 params.cautious_name, params.cautious_gender, params.parent, params.delay)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for x in asp_valid_combos():
            print(x)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
