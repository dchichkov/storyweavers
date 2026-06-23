#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/mystic_feel_gerund_problem_solving_mystery.py
=============================================================================================================================

A standalone storyworld for a small mystery domain about a mystic helper,
careful noticing, and problem solving.

The seed words are built into the world as:
- mystic
- feel-gerund

The stories are framed as child-facing mysteries: a small puzzling loss,
clues that make the world state change, a chosen method that solves the
problem, and an ending image that proves what changed.
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
    role: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    clue_sound: str
    hiding_spots: list[str]
    supports: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    missing: str
    what: str
    risk: str
    feel: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    action: str
    finish: str
    helps: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    where: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str = ""
    problem: str = ""
    method: str = ""
    treasure: str = ""
    name: str = ""
    name2: str = ""
    role: str = ""
    seed: Optional[int] = None


PLACES = {
    "library": Place("library", "the library", "soft rustling", ["behind a shelf", "under a chair"], {"book", "ink"}),
    "attic": Place("attic", "the attic", "hollow creaks", ["under a trunk", "behind a box"], {"dust", "wood"}),
    "garden": Place("garden", "the garden", "tiny wind-chimes", ["under a rose bush", "beside the stone path"], {"leaf", "soil"}),
    "museum": Place("museum", "the museum", "quiet footsteps", ["behind a display", "near a bench"], {"glass", "map"}),
}

PROBLEMS = {
    "lost_map": Problem("lost_map", "a little map", "find a little map", "the path stays confusing", "feel-seeking", {"map", "paper"}),
    "missing_key": Problem("missing_key", "a brass key", "find a brass key", "the old box stays locked", "feel-searching", {"key", "metal"}),
    "quiet_note": Problem("quiet_note", "a whisper note", "find a whisper note", "the clue stays hidden", "feel-listening", {"note", "paper"}),
    "spilled_ink": Problem("spilled_ink", "a clean page", "save a clean page", "the writing blurs", "feel-caring", {"ink", "paper"}),
}

METHODS = {
    "track_clue": Method("track_clue", "follow the clue trail", "look for the small signs", "and the answer came into view", {"map", "note"}),
    "sort_things": Method("sort_things", "sort the things", "put the scattered things in order", "and the missing thing was easier to spot", {"key", "page"}),
    "peek_hidden": Method("peek_hidden", "peek into hiding spots", "check the hiding spots one by one", "and the missing thing was found", {"map", "key", "note", "page"}),
    "ask_mystic": Method("ask_mystic", "ask the mystic", "listen to the mystic's calm hint", "and the clue made sense at last", {"map", "key", "note", "page"}),
}

ARTIFACTS = {
    "lantern": Artifact("lantern", "a small lantern", "a small lantern", "on a table", False, {"light"}),
    "ribbon": Artifact("ribbon", "a blue ribbon", "a blue ribbon", "on a hook", False, {"mark"}),
    "shells": Artifact("shells", "tiny shells", "tiny shells", "in a bowl", True, {"collection"}),
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Lina", "Toby", "Ava", "Finn"]
ROLES = ["child", "girl", "boy"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for problem in PROBLEMS:
            for method in METHODS:
                for treasure in ARTIFACTS:
                    if method == "ask_mystic" or treasure in {"lantern", "ribbon", "shells"}:
                        combos.append((place, problem, method, treasure))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a small mystic mystery and a problem-solving turn.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--treasure", choices=ARTIFACTS)
    ap.add_argument("--name")
    ap.add_argument("--name2")
    ap.add_argument("--role", choices=ROLES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.method is None or c[2] == args.method)
              and (args.treasure is None or c[3] == args.treasure)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, method, treasure = rng.choice(sorted(combos))
    role = args.role or rng.choice(ROLES)
    name = args.name or rng.choice(NAMES)
    name2 = args.name2 or rng.choice([n for n in NAMES if n != name])
    return StoryParams(place=place, problem=problem, method=method, treasure=treasure, name=name, name2=name2, role=role)


def tell(params: StoryParams) -> World:
    place = PLACES.get(params.place)
    prob = PROBLEMS.get(params.problem)
    meth = METHODS.get(params.method)
    art = ARTIFACTS.get(params.treasure)
    if not place or not prob or not meth or not art:
        raise StoryError("Unknown story choice.")
    if not (prob.tags & meth.helps):
        raise StoryError("That method does not fit this problem.")
    if not (place.supports & prob.tags or "light" in art.tags or "mark" in art.tags or "collection" in art.tags):
        raise StoryError("That place cannot support the mystery well enough.")

    world = World(place)
    mystic = world.add(Entity(id="mystic", kind="character", type="woman", label="the mystic", role="helper"))
    child = world.add(Entity(id=params.name, kind="character", type="girl" if params.role == "girl" else ("boy" if params.role == "boy" else "child"), label=params.name, role="seeker"))
    partner = world.add(Entity(id=params.name2, kind="character", type="boy" if child.type == "girl" else "girl", label=params.name2, role="partner"))
    missing = world.add(Entity(id=prob.id, type="thing", label=prob.missing, phrase=prob.what, owner=child.id, meters={"lost": 1.0}, memes={"puzzle": 1.0}, attrs={"risk": prob.risk}))
    treasure = world.add(Entity(id=art.id, type="thing", label=art.label, phrase=art.phrase, owner=child.id, meters={"visible": 0.0}, memes={"shine": 1.0}, attrs={"where": art.where}))

    world.facts.update(
        mystic=mystic, child=child, partner=partner, missing=missing, treasure=treasure,
        place=place, problem=prob, method=meth, artifact=art, solved=False, clue_seen=False,
    )

    child.memes["curious"] = 1.0
    partner.memes["curious"] = 1.0
    mystic.memes["calm"] = 1.0
    world.say(f"At {place.label}, {child.label} noticed {prob.what} was gone.")
    world.say(f"{partner.label} heard the soft {place.clue_sound} and felt {prob.feel} too.")
    world.say(f"Then the mystic smiled, as if the answer was waiting in the room.")

    world.para()
    missing.meters["lost"] = 1.0
    child.memes["unease"] = 1.0
    world.say(f"{child.label} checked the floor, but the clue still did not show itself.")

    clue_support = _use_method(world, meth, child, partner, missing, treasure, mystic)
    if clue_support:
        _solve(world, meth, child, partner, missing, treasure, mystic)

    world.facts["solved"] = treasure.meters.get("found", 0.0) >= THRESHOLD or missing.meters.get("found", 0.0) >= THRESHOLD
    return world


def _use_method(world: World, meth: Method, child: Entity, partner: Entity, missing: Entity, treasure: Entity, mystic: Entity) -> bool:
    if ("method", meth.id) in world.fired:
        return False
    world.fired.add(("method", meth.id))
    child.memes["hope"] = 1.0
    partner.memes["hope"] = 1.0
    if meth.id == "ask_mystic":
        world.say(f"{child.label} asked the mystic for a hint, and {mystic.label} pointed to the quietest corner.")
    elif meth.id == "track_clue":
        world.say(f"{partner.label} looked for the small signs, from one shelf to the next.")
    elif meth.id == "sort_things":
        world.say(f"Together, they sorted the scattered things until the room felt less tangled.")
    else:
        world.say(f"They checked the hiding spots one by one, taking their time.")
    world.facts["clue_seen"] = True
    return True


def _solve(world: World, meth: Method, child: Entity, partner: Entity, missing: Entity, treasure: Entity, mystic: Entity) -> None:
    if ("solve", missing.id) in world.fired:
        return
    world.fired.add(("solve", missing.id))
    missing.meters["found"] = 1.0
    treasure.meters["found"] = 1.0
    child.memes["joy"] = 1.0
    partner.memes["joy"] = 1.0
    mystic.memes["warm"] = 1.0
    world.say(f"At last, the clue fit together, and {missing.label} was found where it had been hiding.")
    world.para()
    world.say(f"{treasure.label} sat in the open now, and the room looked tidy and bright again.")


ASP_RULES = r"""
problem_seen(P) :- missing(P).
method_helpful(M,P) :- helps(M,T), needs(P,T).
solved(P) :- problem_seen(P), method_helpful(M,P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("missing", pid))
        for t in p.tags:
            lines.append(asp.fact("needs", pid, t))
    for mid, m in METHODS.items():
        lines.append(asp.fact("method", mid))
        for t in m.helps:
            lines.append(asp.fact("helps", mid, t))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show problem_seen/1.\n#show solved/1."))
    return sorted(set(asp.atoms(model, "problem_seen")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()):
        print("OK: ASP twin produces problem facts.")
    else:
        print("MISMATCH: ASP twin empty.")
        ok = False
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, problem=None, method=None, treasure=None, name=None, name2=None, role=None), random.Random(777)))
        _ = sample.story
        print("OK: smoke story generation works.")
    except Exception as e:
        print(f"SMOKE FAIL: {e}")
        ok = False
    return 0 if ok else 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery for a child about {f["child"].label} and a mystic clue at {f["place"].label}. Include the word "mystic".',
        f"Tell a problem-solving story where {f['child'].label} notices something missing, listens carefully, and asks the mystic for help.",
        f'Write a gentle mystery where a small clue leads to the answer and the ending proves the room is no longer puzzling.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    partner: Entity = f["partner"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    prob: Problem = f["problem"]  # type: ignore[assignment]
    meth: Method = f["method"]  # type: ignore[assignment]
    art: Artifact = f["artifact"]  # type: ignore[assignment]
    mystic: Entity = f["mystic"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Who helped {child.label} at {place.label}?",
            f"The mystic helped {child.label}, and {partner.label} listened too. Together they used a calm clue to solve the mystery.",
        ),
        QAItem(
            f"What was missing in the story?",
            f"{prob.missing} was missing. That made the room feel puzzling until they used the clue and found it.",
        ),
        QAItem(
            f"How did {child.label} and {partner.label} solve the problem?",
            f"They used {meth.label}, which fit the problem and led them to the answer. The final clue showed where {prob.missing} had been hiding.",
        ),
        QAItem(
            f"What changed at the end of the story?",
            f"{art.label} was in the open and the missing thing was found. The room no longer felt mixed up or mysterious.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does a mystic usually do in a story?",
            "A mystic is a calm guide who notices clues and helps others think clearly. In a mystery story, that kind of helper can point to the right answer.",
        ),
        QAItem(
            "What does it mean to problem solve?",
            "Problem solving means noticing a problem, trying a sensible method, and checking whether it works. If the first try does not help, you choose another way.",
        ),
        QAItem(
            "What is a mystery?",
            "A mystery is a story with something puzzling or hidden. The characters look for clues until the answer makes sense.",
        ),
    ]


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
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
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


CURATED = [
    StoryParams(place="library", problem="lost_map", method="track_clue", treasure="lantern", name="Mia", name2="Leo", role="girl"),
    StoryParams(place="attic", problem="missing_key", method="peek_hidden", treasure="ribbon", name="Nora", name2="Ben", role="child"),
    StoryParams(place="garden", problem="quiet_note", method="ask_mystic", treasure="shells", name="Ava", name2="Finn", role="girl"),
    StoryParams(place="museum", problem="spilled_ink", method="sort_things", treasure="lantern", name="Toby", name2="Lina", role="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show problem_seen/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show problem_seen/1.\n#show solved/1."))
        print(f"problem_seen: {sorted(asp.atoms(model, 'problem_seen'))}")
        print(f"solved: {sorted(asp.atoms(model, 'solved'))}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.problem} at {p.place} with {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
