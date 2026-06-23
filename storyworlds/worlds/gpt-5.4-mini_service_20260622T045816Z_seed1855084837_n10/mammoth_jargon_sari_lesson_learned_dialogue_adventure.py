#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T045816Z_seed1855084837_n10/mammoth_jargon_sari_lesson_learned_dialogue_adventure.py
======================================================================================================

A standalone storyworld for a small adventure tale about a mammoth find,
confusing jargon, and a sari-clad helper who turns a risky moment into a lesson.

The world is built around a child explorer, a guide who speaks in jargon, a
careful grown-up in a sari, and a valuable mammoth relic at an excavation site.
The child wants adventure, but the site has real hazards: loose ropes, deep pits,
and fragile bones. Dialogue and lesson learned are part of the engine, not just
the text style.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict, is_dataclass
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve()
for parent in [_HERE.parent] + list(_HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    location: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    place: str
    hazard: str
    prize: str
    guide_style: str
    helper: str
    name: str
    gender: str
    seed: Optional[int] = None


@dataclass
class Place:
    id: str
    label: str
    hazard: str
    afford: str
    climate: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    risk: str
    warning: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperSpec:
    id: str
    label: str
    outfit: str
    role: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "role": v.role, "owner": v.owner,
            "location": v.location, "tags": set(v.tags), "attrs": dict(v.attrs),
            "meters": defaultdict(float, dict(v.meters)),
            "memes": defaultdict(float, dict(v.memes)),
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


PLACES = {
    "dig_site": Place("dig_site", "the dig site", "rope_trench", "careful_steps", "hot", {"adventure", "mammoth"}),
    "museum_storage": Place("museum_storage", "the museum storage room", "crate_stack", "labels", "cool", {"adventure", "mammoth"}),
    "riverbank": Place("riverbank", "the riverbank camp", "mud_bank", "boots", "windy", {"adventure", "mammoth"}),
}

HAZARDS = {
    "rope_trench": Hazard("rope_trench", "a loose rope over a deep trench", "fall", "If you step too fast, you could slip into the trench.", "use careful steps and keep one hand on the rope rail", {"rope", "trench"}),
    "crate_stack": Hazard("crate_stack", "a pile of wobbly crates", "crush", "If the crates tip, they could squash the fossil box.", "move one crate at a time and clear a safe path", {"crate", "storage"}),
    "mud_bank": Hazard("mud_bank", "a slick mud bank by the water", "sink", "If you run there, your boots could slip into the mud.", "walk slowly and stay on the packed path", {"mud", "water"}),
}

PRIZES = {
    "tusk": Prize("tusk", "a mammoth tusk", "mammoth tusk", "dig_site", {"mammoth", "bone"}),
    "skull": Prize("skull", "a mammoth skull", "mammoth skull", "museum_storage", {"mammoth", "bone"}),
    "toy": Prize("toy", "a woolly mammoth model", "woolly mammoth model", "riverbank", {"mammoth", "toy"}),
}

HELPERS = {
    "aunt": HelperSpec("aunt", "an aunt", "a sari", "translator", {"sari", "family"}),
    "guide": HelperSpec("guide", "a site guide", "a field hat", "explainer", {"jargon", "adventure"}),
    "elder": HelperSpec("elder", "an elder cousin", "a bright sari", "translator", {"sari", "jargon"}),
}

GIRL_NAMES = ["Mina", "Anya", "Lila", "Nora", "Rani", "Tia"]
BOY_NAMES = ["Arun", "Kiran", "Omar", "Sami", "Eli", "Noah"]
TRAITS = ["curious", "brave", "quick", "thoughtful", "restless"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, h, r, hl) for p, h, r, hl in (
        ("dig_site", "rope_trench", "tusk", "aunt"),
        ("dig_site", "rope_trench", "tusk", "guide"),
        ("museum_storage", "crate_stack", "skull", "elder"),
        ("museum_storage", "crate_stack", "skull", "guide"),
        ("riverbank", "mud_bank", "toy", "aunt"),
        ("riverbank", "mud_bank", "toy", "guide"),
    )]


def reason_gate(place: Place, hazard: Hazard, prize: Prize, helper: HelperSpec) -> bool:
    return place.id == prize.place and hazard.id in place.hazard and (helper.id == "guide" or "sari" in helper.tags)


def explain_rejection(place: Place, hazard: Hazard, prize: Prize, helper: HelperSpec) -> str:
    return f"(No story: {place.label}, {hazard.label}, {prize.label}, and {helper.label} do not make a reasonable adventure.)"


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES or params.hazard not in HAZARDS or params.prize not in PRIZES or params.helper not in HELPERS:
        raise StoryError("Unknown story parameters.")
    place = PLACES[params.place]
    hazard = HAZARDS[params.hazard]
    prize = PRIZES[params.prize]
    helper = HELPERS[params.helper]
    if not reason_gate(place, hazard, prize, helper):
        raise StoryError(explain_rejection(place, hazard, prize, helper))
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name, role="explorer"))
    guide = world.add(Entity(id="Guide", kind="character", type="woman" if helper.id != "guide" else "man", label=helper.label, role=helper.role, tags=set(helper.tags)))
    relic = world.add(Entity(id=prize.id, kind="thing", type="relic", label=prize.label, phrase=prize.phrase, location=place.id, tags=set(prize.tags)))
    hazard_ent = world.add(Entity(id=hazard.id, kind="thing", type="hazard", label=hazard.label, phrase=hazard.warning, location=place.id, tags=set(hazard.tags)))

    hero.memes["wonder"] += 1
    guide.memes["patience"] += 1
    world.facts.update(hero=hero, guide=guide, relic=relic, hazard=hazard_ent, place=place, prize=prize, helper=helper, hazard_cfg=hazard)
    return world


def predict_mess(world: World) -> bool:
    sim = world.copy()
    hero = sim.facts.get("hero")
    if hero is None:
        return False
    hero.meters["risk"] += 1
    return hero.meters["risk"] >= THRESHOLD


def opening(world: World) -> None:
    hero = world.facts["hero"]
    guide = world.facts["guide"]
    prize = world.facts["prize"]
    place = world.facts["place"]
    world.say(f"{hero.id} arrived at {place.label} with a fast heartbeat and wide eyes.")
    world.say(f"Nearby, {guide.label} pointed at {prize.label} and said it was part of a real adventure.")
    hero.memes["joy"] += 1


def dialogue_and_turn(world: World) -> None:
    hero = world.facts["hero"]
    guide = world.facts["guide"]
    helper = world.facts["helper"]
    if helper.id == "aunt":
        guide_line = "Keep back, beta. The trench edge is thin, and the ropes are only for steady hands."
    elif helper.id == "elder":
        guide_line = "Listen carefully. The path is narrow, and the pit is deeper than it looks."
    else:
        guide_line = "Watch the stratigraphy and the load-bearing edge. Keep clear of the collapse zone."
    hero_line = "That sounds like jargon."
    world.say(f'"{guide_line}" {guide.id} said.')
    world.say(f'"{hero_line}" {hero.id} muttered.')
    hero.memes["confusion"] += 1
    if "sari" in helper.tags:
        world.say(f"{helper.label.capitalize()} smiled and translated it into plain words for {hero.id}.")
        world.say(f'"It means walk slowly, stay on the safe path, and do not race the trench," {helper.label} said.')
        hero.memes["trust"] += 1
    else:
        world.say(f"{guide.label.capitalize()} tried again and pointed at the hazard instead of using more jargon.")
    hero.memes["desire"] += 1


def risk_and_choice(world: World) -> None:
    hero = world.facts["hero"]
    hazard = world.facts["hazard"]
    hero.meters["risk"] += 1
    if hero.meters["risk"] >= THRESHOLD:
        world.say(f"{hero.id} leaned toward {hazard.label}, eager to see the mammoth find up close.")
    world.say(f"Then {hero.id} reached for the rope without thinking.")
    if world.facts["helper"].id in {"aunt", "elder"}:
        hero.memes["startled"] += 1
        world.say(f"{world.facts['guide'].label.capitalize()} caught {hero.id}'s sleeve and steadied {hero.id} before the edge.")
        hero.memes["relief"] += 1
    else:
        world.say(f"{world.facts['guide'].label.capitalize()} snapped, \"Stop!\" and moved between {hero.id} and the edge.")
        hero.memes["fear"] += 1


def resolution(world: World) -> None:
    hero = world.facts["hero"]
    guide = world.facts["guide"]
    relic = world.facts["relic"]
    helper = world.facts["helper"]
    place = world.facts["place"]
    if "sari" in helper.tags:
        world.say(f"{helper.label.capitalize()} handed {hero.id} a marker flag and asked for careful steps instead of speedy feet.")
        world.say(f'Together they marked the safe line, and the {relic.label} stayed untouched while the path became clear.')
        hero.memes["lesson"] += 1
        hero.memes["joy"] += 1
        world.say(f'"I get it now," {hero.id} said. "Adventure is better when everybody gets home safe."')
        world.say(f"{guide.label.capitalize()} nodded, and the {relic.label} shone like treasure in the warm light.")
    else:
        world.say(f"{guide.label.capitalize()} showed {hero.id} the safe path and repeated the warning in simpler words.")
        world.say(f"{hero.id} listened at last, and the {relic.label} stayed safe beside the trench.")
        hero.memes["lesson"] += 1
        world.say(f'"No more jargon for me," {hero.id} said. "Plain words make the best map."')
        world.say(f"By sunset, {place.label} was quiet again, and the mammoth find still waited for the next careful explorer.")


def tell(params: StoryParams) -> World:
    world = build_world(params)
    opening(world)
    world.para()
    dialogue_and_turn(world)
    world.para()
    risk_and_choice(world)
    world.para()
    resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that includes the words "mammoth", "jargon", and "sari".',
        f"Tell a dialogue-heavy adventure where {f['hero'].id} gets confused by jargon at {f['place'].label} but learns a safer way from {f['guide'].label}.",
        f"Write a lesson-learned story about a mammoth find, with plain speech, brave choices, and a helpful sari.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    prize = f["prize"]
    hazard = f["hazard_cfg"]
    helper = f["helper"]
    qas = [
        QAItem(
            question=f"Why did {hero.id} think the guide's words were hard to follow?",
            answer=f"{hero.id} called the guide's words jargon because they sounded technical and hard to picture. {helper.label.capitalize()} helped by turning them into plain steps about the safe path.",
        ),
        QAItem(
            question=f"What was the exciting thing waiting at {place.label}?",
            answer=f"The exciting thing was {prize.label}, a real mammoth find. It made the day feel like an adventure, but it also meant the children had to be careful near {hazard.label}.",
        ),
        QAItem(
            question=f"How did {hero.id} stay safe near the trench?",
            answer=f"{hero.id} stayed safe by listening, slowing down, and keeping away from the edge. The helper in the sari translated the warning so the lesson was easy to remember.",
        ),
    ]
    if f["helper"].id in {"aunt", "elder"}:
        qas.append(QAItem(
            question=f"What did the sari-wearing helper do after {hero.id} got confused?",
            answer=f"The sari-wearing helper translated the warning into plain words and pointed to the safe path. That made the danger easier to understand and helped {hero.id} choose the careful way.",
        ))
    qas.append(QAItem(
        question=f"What did {hero.id} learn by the end of the story?",
        answer=f"{hero.id} learned that adventure is best when the team uses simple words and careful steps. The lesson was that understanding the warning matters just as much as excitement.",
    ))
    return qas


WORLD_KNOWLEDGE = {
    "mammoth": [
        QAItem(
            question="What is a mammoth?",
            answer="A mammoth was a giant elephant-like animal that lived long ago and had huge tusks and shaggy hair.",
        )
    ],
    "jargon": [
        QAItem(
            question="What is jargon?",
            answer="Jargon is special language that can be hard for other people to understand if they do not know the topic.",
        )
    ],
    "sari": [
        QAItem(
            question="What is a sari?",
            answer="A sari is a long cloth outfit worn by many women in South Asia. It is wrapped in a graceful way.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["prize"].tags) | {"jargon", "sari", "mammoth"}
    out: list[QAItem] = []
    for key in ("mammoth", "jargon", "sari"):
        if key in tags:
            out.extend(WORLD_KNOWLEDGE[key])
    return out


ASP_RULES = r"""
valid(P,H,R,HL) :- place(P), hazard(H), prize(R), helper(HL), place_prize(P,R), place_hazard(P,H), helper_ok(HL).
lesson(L) :- helper_ok(L).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_hazard", pid, p.hazard))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
    for rid, r in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("place_prize", r.place, rid))
    for hlid, h in HELPERS.items():
        lines.append(asp.fact("helper", hlid))
        if "sari" in h.tags:
            lines.append(asp.fact("helper_ok", hlid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between ASP and Python valid_combos().")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in asp:", sorted(cl - py))
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, hazard=None, prize=None, helper=None, name=None, gender=None, n=1, seed=777, all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False), random.Random(777)))
        _ = sample.story
    except Exception as exc:
        print(f"Smoke test failed: {exc}")
        return 1
    print(f"OK: ASP matches Python ({len(py)} combos) and smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with mammoth, jargon, sari, dialogue, and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", "--n", type=int, default=1)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.hazard:
        combos = [c for c in combos if c[1] == args.hazard]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if args.helper:
        combos = [c for c in combos if c[3] == args.helper]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, hazard, prize, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, hazard=hazard, prize=prize, guide_style="dialogue", helper=helper, name=name, gender=gender, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.hazard not in HAZARDS or params.prize not in PRIZES or params.helper not in HELPERS:
        raise StoryError("Invalid parameters.")
    world = tell(params)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def sample_to_jsonable(sample: StorySample) -> dict:
    def convert(obj):
        if is_dataclass(obj):
            return convert(asdict(obj))
        if isinstance(obj, dict):
            return {str(k): convert(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [convert(v) for v in obj]
        return obj

    return convert(sample)


CURATED = [
    StoryParams(place="dig_site", hazard="rope_trench", prize="tusk", helper="aunt", guide_style="dialogue", name="Mina", gender="girl"),
    StoryParams(place="museum_storage", hazard="crate_stack", prize="skull", helper="elder", guide_style="dialogue", name="Kiran", gender="boy"),
    StoryParams(place="riverbank", hazard="mud_bank", prize="toy", helper="guide", guide_style="dialogue", name="Rani", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:\n")
        for c in asp_valid_combos():
            print("  ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        if len(samples) == 1:
            print(json.dumps(sample_to_jsonable(samples[0]), indent=2, ensure_ascii=False))
        else:
            print(json.dumps([sample_to_jsonable(s) for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
