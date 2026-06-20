#!/usr/bin/env python3
"""A cozy-pond soccer-field mystery about a missing captain band and reconciliation.

Internal source tale:
Two children stay after soccer practice beside a cozy pond to finish one last
passing drill. The pond-blue captain band they are sharing goes missing, and
one child mistakes the other's hurried clue for a mean trick. Their coach asks
them to trust the field's physical signs more than their first angry guess.
They follow the evidence, recover the band, apologize, and prove the friendship
is repaired by trading the band back and forth during the final drill.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Sector:
    id: str
    name: str
    origin: str
    opening: str
    loss: str
    finish: str


@dataclass(frozen=True)
class Clue:
    id: str
    place: str
    marker: str
    lead: str
    misunderstanding: str


@dataclass(frozen=True)
class Cause:
    id: str
    place: str
    kind: str
    motion: str
    discovery: str
    proof: str


@dataclass(frozen=True)
class Method:
    id: str
    tool: str
    solves: str
    action: str
    proof: str


@dataclass
class StoryParams:
    sector: str
    clue: str
    cause: str
    method: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None


@dataclass
class PondBandWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str | bool | int | float] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        if ent.role:
            self.entities[ent.role] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, event_id: str, text: str, actor: str, target: str | None = None) -> None:
        self.history.append(Event(event_id, text, actor, target))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


SECTORS: dict[str, Sector] = {
    "pond_touchline": Sector(
        id="pond_touchline",
        name="the pond-side touchline",
        origin="the cone crate",
        opening="They set their cones along the pond-side touchline, where the grass leaned cool and shiny toward the water.",
        loss="Talia hung the captain band on the cone crate while Ruben reset the sideline cones by the touchline.",
        finish="they tapped the ball up the touchline and passed the blue band from wrist to wrist without a single pause",
    ),
    "center_circle": Sector(
        id="center_circle",
        name="the center circle",
        origin="the ball cart rim",
        opening="They started at the center circle, where the chalk ring looked pale and secret in the falling light.",
        loss="Talia laid the captain band on the ball cart rim while Ruben nudged the ball back to the kickoff spot.",
        finish="they rolled the ball around the center circle and traded the band so easily that the drill looked like one shared thought",
    ),
    "south_goal": Sector(
        id="south_goal",
        name="the south goal lane",
        origin="the folding bench rail",
        opening="They practiced beside the south goal, where the net whispered whenever the breeze from the pond crossed the field.",
        loss="Talia rested the captain band on the folding bench rail while Ruben hurried after the spare ball near the goal lane.",
        finish="they sent three quick passes through the south goal lane and laughed when the blue band flashed as it changed hands",
    ),
}

CLUES: dict[str, Clue] = {
    "dew_curve": Clue(
        id="dew_curve",
        place="reed_edge",
        marker="a curved stripe of brushed-away dew in the grass",
        lead="The stripe bent toward the cozy pond reeds beside the line.",
        misunderstanding="Talia saw the bent dew and decided Ruben had made a secret trail instead of giving her a plain answer",
    ),
    "mesh_thread": Clue(
        id="mesh_thread",
        place="net_clip",
        marker="one bright blue thread pinched in the goal mesh",
        lead="The thread pointed to the loose net clip tucked behind the post.",
        misunderstanding="Talia thought Ruben had hidden the band to make the search feel clever when she only wanted the truth",
    ),
    "chalk_halfmoon": Clue(
        id="chalk_halfmoon",
        place="bench_shadow",
        marker="a chalk half-moon beside the ball cart wheel",
        lead="The little mark faced the shadow under the aluminum bench.",
        misunderstanding="Talia took the chalk mark as a teasing riddle, and a riddle felt unkind while the band was missing",
    ),
}

CAUSES: dict[str, Cause] = {
    "reed_slide": Cause(
        id="reed_slide",
        place="reed_edge",
        kind="reed_tangle",
        motion="A hard first touch had bumped {origin}, and the soft band slid along a damp board until a low reed caught its loop.",
        discovery="The blue cloth was hanging from the reed like a sleepy flag just above the mud.",
        proof="Fresh drops on the board made a shining path from {origin} all the way to the water's edge.",
    ),
    "net_snag": Cause(
        id="net_snag",
        place="net_clip",
        kind="mesh_snag",
        motion="A breeze from the cozy pond had lifted the light band and wrapped it around a loose net clip behind the post.",
        discovery="The blue cloth peeped from the white mesh each time the net stirred.",
        proof="When Ruben touched the post, the band tapped the clip with the same tiny click he had heard before.",
    ),
    "bench_roll": Cause(
        id="bench_roll",
        place="bench_shadow",
        kind="bench_slot",
        motion="The band had rolled off {origin} and slipped into the dark shelf under the bench.",
        discovery="A fresh streak through the dust led to one blue corner folded in the shadow.",
        proof="The dust line ended exactly where the soft band was tucked against the bench leg.",
    ),
}

METHODS: dict[str, Method] = {
    "ball_rake": Method(
        id="ball_rake",
        tool="the long ball rake",
        solves="reed_tangle",
        action="Ruben slid the long ball rake under the reed loop while Talia held his sleeve, and the soft band lifted free without touching the mud.",
        proof="The rake kept the cloth dry enough to use and kept both children off the slick bank.",
    ),
    "keeper_glove": Method(
        id="keeper_glove",
        tool="a goalkeeper glove",
        solves="mesh_snag",
        action="Talia opened the mesh with a goalkeeper glove while Ruben unwound the cloth from the clip one careful turn at a time.",
        proof="The padded glove stopped the net from biting down on the band again.",
    ),
    "lace_loop": Method(
        id="lace_loop",
        tool="a spare lace loop",
        solves="bench_slot",
        action="Ruben fed a spare lace loop beneath the bench, and Talia caught the band's little tag so they could draw it back together.",
        proof="The lace bent through the narrow shelf where fingers could not fit.",
    ),
}

PLACE_LABELS = {
    "reed_edge": "the cozy pond reeds",
    "net_clip": "the loose net clip",
    "bench_shadow": "the shadow under the bench",
}

KIND_LABELS = {
    "reed_tangle": "a reed loop above muddy ground",
    "mesh_snag": "a tight net clip",
    "bench_slot": "a narrow bench shelf",
}


def sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.sector not in SECTORS:
        return False, f"unknown sector: {params.sector}"
    if params.clue not in CLUES:
        return False, f"unknown clue: {params.clue}"
    if params.cause not in CAUSES:
        return False, f"unknown cause: {params.cause}"
    if params.method not in METHODS:
        return False, f"unknown method: {params.method}"
    clue = CLUES[params.clue]
    cause = CAUSES[params.cause]
    method = METHODS[params.method]
    if clue.place != cause.place:
        return False, "the clue has to point to the place where the band really went"
    if method.solves != cause.kind:
        return False, "the recovery method must match the way the band is trapped"
    return True, ""


def all_params() -> list[StoryParams]:
    combos: list[StoryParams] = []
    for sector in SECTORS:
        for clue in CLUES:
            for cause in CAUSES:
                for method in METHODS:
                    params = StoryParams(sector=sector, clue=clue, cause=cause, method=method)
                    if valid_params(params)[0]:
                        combos.append(params)
    return combos


def make_world(params: StoryParams) -> PondBandWorld:
    sector = SECTORS[params.sector]
    clue = CLUES[params.clue]
    cause = CAUSES[params.cause]
    method = METHODS[params.method]
    world = PondBandWorld(params)
    world.add(
        Entity(
            id="talia",
            kind="character",
            type="girl",
            label="Talia",
            role="captain_turn",
            traits=["quick", "earnest"],
        )
    )
    world.add(
        Entity(
            id="ruben",
            kind="character",
            type="boy",
            label="Ruben",
            role="marker_friend",
            traits=["steady", "observant"],
        )
    )
    world.add(
        Entity(
            id="coach",
            kind="character",
            type="woman",
            label="Coach Sana",
            role="coach",
            traits=["calm"],
        )
    )
    world.add(Entity(id="field", kind="place", type="soccer_field", label="the soccer field"))
    world.add(Entity(id="pond", kind="place", type="pond", label="the cozy pond"))
    world.add(Entity(id="bench", kind="place", type="bench", label="the aluminum bench"))
    world.add(Entity(id="goal", kind="place", type="goal", label="the south goal"))
    world.add(Entity(id="band", kind="object", type="armband", label="the pond-blue captain band"))
    world.add(Entity(id="pair", kind="group", type="duo", label="the two teammates"))

    world.get("field").meters["dew"] = 1.0
    world.get("pond").meters["glow"] = 1.0
    world.get("band").meters["present"] = 1.0
    world.get("pair").meters["drill_ready"] = 1.0
    world.get("pair").memes["trust"] = 2.0
    world.get("talia").memes["trust"] = 1.0
    world.get("ruben").memes["trust"] = 1.0

    world.facts.update(
        sector_name=sector.name,
        clue_marker=clue.marker,
        clue_lead=clue.lead,
        misunderstanding=clue.misunderstanding,
        origin_label=sector.origin,
        true_place=PLACE_LABELS[cause.place],
        cause_motion=cause.motion,
        cause_discovery=cause.discovery,
        cause_proof=cause.proof,
        tool=method.tool,
        solved_kind=KIND_LABELS[cause.kind],
    )
    return world


def opening(world: PondBandWorld) -> None:
    sector = SECTORS[world.params.sector]
    pair = world.get("pair")
    pair.memes["joy"] += 1.0
    world.record(
        "opening",
        "Evening settled over the soccer field beside the cozy pond, and the water was so still that every rustle felt like the start of a mystery.",
        "field",
    )
    world.record(
        "setup",
        f"{sector.opening} Coach Sana let Talia and Ruben share the pond-blue captain band for one last passing drill, and both of them wanted the turn to go perfectly.",
        "pair",
        "band",
    )


def band_goes_missing(world: PondBandWorld) -> None:
    sector = SECTORS[world.params.sector]
    band = world.get("band")
    pair = world.get("pair")
    band.meters["present"] = 0.0
    band.meters["lost"] = 1.0
    pair.meters["drill_ready"] = 0.0
    pair.memes["worry"] += 1.0
    world.record(
        "loss",
        f"{sector.loss} When Talia reached for it again, the captain band was gone.",
        "talia",
        "band",
    )


def reveal_sign(world: PondBandWorld) -> None:
    clue = CLUES[world.params.clue]
    ruben = world.get("ruben")
    ruben.memes["helpful"] += 1.0
    world.record(
        "sign",
        f"Near where the band had rested was {clue.marker}. {sentence_start(clue.lead)} Ruben had spotted that sign after hearing the band move and had meant to explain it as soon as the spare ball stopped rolling away.",
        "ruben",
        clue.place,
    )


def accuse(world: PondBandWorld) -> None:
    talia = world.get("talia")
    ruben = world.get("ruben")
    pair = world.get("pair")
    talia.memes["blame"] += 1.0
    talia.memes["hurt"] += 0.5
    ruben.memes["hurt"] += 1.0
    pair.memes["trust"] -= 1.0
    world.record(
        "accuse",
        f'"Did you move it to make a game out of this?" Talia asked. {world.facts["misunderstanding"]}, and Ruben went still because he had been trying to save the clue, not play a trick.',
        "talia",
        "ruben",
    )


def coach_turn(world: PondBandWorld) -> None:
    pair = world.get("pair")
    pair.memes["reflection"] += 1.0
    world.record(
        "turn",
        'Coach Sana stepped closer and said, "When friends get scared, a clue can sound unkind. Let the field speak first. Grass, mesh, and shadows tell cleaner truths than a fast guess."',
        "coach",
        "pair",
    )


def search(world: PondBandWorld) -> None:
    cause = CAUSES[world.params.cause]
    sector = SECTORS[world.params.sector]
    pair = world.get("pair")
    band = world.get("band")
    world.get("talia").memes["curiosity"] += 1.0
    world.get("ruben").memes["patience"] += 1.0
    pair.memes["trust"] += 0.5
    if cause.kind == "reed_tangle":
        band.meters["damp"] = 1.0
    elif cause.kind == "mesh_snag":
        band.meters["snagged"] = 1.0
    else:
        band.meters["dusty"] = 1.0
    world.record(
        "search",
        "So the two teammates followed the sign together. "
        f"{cause.motion.format(origin=sector.origin)} "
        f"Then they found the proof: {cause.discovery} {cause.proof.format(origin=sector.origin)}",
        "pair",
        cause.place,
    )


def recover(world: PondBandWorld) -> None:
    method = METHODS[world.params.method]
    band = world.get("band")
    pair = world.get("pair")
    band.meters["lost"] = 0.0
    band.meters["present"] = 1.0
    band.meters["recovered"] = 1.0
    pair.meters["drill_ready"] = 1.0
    pair.memes["relief"] += 1.0
    world.record(
        "recover",
        f"{method.action} {method.proof}",
        "pair",
        "band",
    )


def reconcile(world: PondBandWorld) -> None:
    talia = world.get("talia")
    ruben = world.get("ruben")
    pair = world.get("pair")
    talia.memes["blame"] = 0.0
    talia.memes["apology"] += 1.0
    ruben.memes["hurt"] = 0.0
    ruben.memes["forgiveness"] += 1.0
    pair.memes["trust"] += 1.5
    pair.memes["reconciliation"] += 1.0
    world.facts["reconciled"] = True
    world.record(
        "reconcile",
        '"I saw a trick before I saw the clue," Talia said softly. "I was wrong to blame you before I checked the field." Ruben rubbed the blue band between his fingers and answered, "Next time I will say what I noticed right away." Their voices settled, and the sore feeling between them finally loosened.',
        "talia",
        "ruben",
    )


def closing(world: PondBandWorld) -> None:
    sector = SECTORS[world.params.sector]
    pair = world.get("pair")
    band = world.get("band")
    pair.memes["joy"] += 1.0
    band.meters["shared"] = 1.0
    world.record(
        "ending",
        f"Coach Sana looped the captain band onto Talia's wrist for the first turn, and after the next clean pass Talia slipped it onto Ruben's wrist herself. Then {sector.finish}, while the cozy pond watched in silver silence and the mystery ended with the friendship stronger than the fright.",
        "pair",
        "field",
    )


def tell(params: StoryParams) -> PondBandWorld:
    world = make_world(params)
    opening(world)
    world.para()
    band_goes_missing(world)
    reveal_sign(world)
    accuse(world)
    coach_turn(world)
    world.para()
    search(world)
    recover(world)
    reconcile(world)
    world.para()
    closing(world)
    return world


def generation_prompts(world: PondBandWorld) -> list[str]:
    sector = SECTORS[world.params.sector]
    return [
        'Write a child-facing mystery that clearly includes "cozy pond" and "soccer field."',
        f"Center the trouble on a missing pond-blue captain band during an after-practice drill at {sector.name}.",
        "Resolve the tension through physical evidence, a spoken apology, and a final image that proves the children are reconciled.",
    ]


def story_grounded_qa(world: PondBandWorld) -> list[QAItem]:
    cause = CAUSES[world.params.cause]
    method = METHODS[world.params.method]
    sector = SECTORS[world.params.sector]
    return [
        QAItem(
            question="What was the mystery on the soccer field?",
            answer=(
                "The mystery was that the pond-blue captain band vanished just before Talia and Ruben began their last passing drill. "
                "Because the band decided whose turn came first, its disappearance felt important right away."
            ),
        ),
        QAItem(
            question="Why did Talia get upset with Ruben?",
            answer=(
                f"Talia saw {world.facts['clue_marker']} near the place where the band had been, and she mistook it for part of a trick. "
                "She was worried and hurried, so she blamed Ruben before she understood that he had noticed a real sign."
            ),
        ),
        QAItem(
            question="Where had the missing band really gone?",
            answer=(
                f"The band had really gone to {PLACE_LABELS[cause.place]}. "
                f"{cause.motion.format(origin=sector.origin)} That is why the field's clue pointed there."
            ),
        ),
        QAItem(
            question="How did the children recover the captain band?",
            answer=(
                f"They followed the field sign together and used {method.tool} to get the band back. "
                f"That tool fit {KIND_LABELS[cause.kind]}, so careful teamwork worked better than grabbing in a hurry."
            ),
        ),
        QAItem(
            question="How did the story show reconciliation at the end?",
            answer=(
                "Talia apologized for blaming Ruben before checking the evidence, and Ruben answered with calm forgiveness. "
                "The repaired friendship showed in action when Talia handed the captain band back to him during the final drill."
            ),
        ),
    ]


def world_knowledge_qa(world: PondBandWorld) -> list[QAItem]:
    cause = CAUSES[world.params.cause]
    method = METHODS[world.params.method]
    return [
        QAItem(
            question="Why can a soft sports band vanish quickly on a field?",
            answer=(
                "A light cloth band can slide, snag, or roll faster than children expect during practice. "
                "Grass, netting, benches, and damp edges near a pond can hide it in only a moment."
            ),
        ),
        QAItem(
            question="Why is following clues better than blaming in a mystery like this?",
            answer=(
                "Following clues keeps the children tied to real signs in the world instead of frightened guesses about each other. "
                "That gives them a fair way to solve the problem and a fair way to protect the friendship."
            ),
        ),
        QAItem(
            question=f"Why was {method.tool} the right tool this time?",
            answer=(
                f"It was the right tool because the band was trapped by {KIND_LABELS[cause.kind]}, not hidden by a person. "
                f"Using {method.tool} let the children recover the band gently instead of making the problem worse."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_grounded_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(S, C, A, M) :-
    sector(S), clue(C), cause(A), method(M),
    clue_place(C, P), cause_place(A, P),
    cause_kind(A, K), method_solves(M, K).

ok :- chosen(S, C, A, M), valid(S, C, A, M).

#show valid/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from asp import fact

    rows: list[str] = []
    for sector in SECTORS:
        rows.append(fact("sector", sector))
    for clue_key, clue in CLUES.items():
        rows.append(fact("clue", clue_key))
        rows.append(fact("clue_place", clue_key, clue.place))
    for cause_key, cause in CAUSES.items():
        rows.append(fact("cause", cause_key))
        rows.append(fact("cause_place", cause_key, cause.place))
        rows.append(fact("cause_kind", cause_key, cause.kind))
    for method_key, method in METHODS.items():
        rows.append(fact("method", method_key))
        rows.append(fact("method_solves", method_key, method.solves))
    if params is not None:
        rows.append(fact("chosen", params.sector, params.clue, params.cause, params.method))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str]]:
    from asp import atoms, one_model

    model = one_model(asp_program())
    return {tuple(str(part) for part in atom) for atom in atoms(model, "valid")}


def asp_accepts(params: StoryParams) -> bool:
    from asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params)), "ok"))


def verify() -> str:
    python_combos = {(p.sector, p.clue, p.cause, p.method) for p in all_params()}
    asp_combos = asp_valid_combos()
    if python_combos != asp_combos:
        only_python = sorted(python_combos - asp_combos)
        only_asp = sorted(asp_combos - python_combos)
        raise StoryError(f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}")
    for params in all_params():
        if not asp_accepts(params):
            raise StoryError(f"ASP rejected valid params: {params}")
        sample = generate(params)
        if "cozy pond" not in sample.story or "soccer field" not in sample.story:
            raise StoryError(f"required seed language missing from story for params={params}")
        if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
            raise StoryError(f"QA too thin for params={params}")
        if not sample.world.facts.get("reconciled"):
            raise StoryError(f"story did not reconcile for params={params}")
        if sample.world.get("band").meters["recovered"] < 1.0:
            raise StoryError(f"band was not recovered for params={params}")
    return (
        f"OK: Python and ASP agree on {len(python_combos)} valid captain-band mysteries, "
        "and every generated story recovers the band and repairs the friendship."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sector", choices=sorted(SECTORS))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--cause", choices=sorted(CAUSES))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    rng = rng or random.Random(args.seed)
    explicit = any(getattr(args, key) is not None for key in ("sector", "clue", "cause", "method"))
    if explicit:
        params = StoryParams(
            sector=args.sector or rng.choice(list(SECTORS)),
            clue=args.clue or rng.choice(list(CLUES)),
            cause=args.cause or rng.choice(list(CAUSES)),
            method=args.method or rng.choice(list(METHODS)),
            seed=args.seed,
        )
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params
    choice = rng.choice(all_params())
    return StoryParams(choice.sector, choice.clue, choice.cause, choice.method, seed=args.seed)


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in all_params():
            yield generate(params)
        return
    count = max(1, args.n)
    explicit = any(getattr(args, key) is not None for key in ("sector", "clue", "cause", "method"))
    if explicit:
        rng = random.Random(args.seed)
        for index in range(count):
            params = resolve_params(args, rng)
            yield generate(
                StoryParams(
                    sector=params.sector,
                    clue=params.clue,
                    cause=params.cause,
                    method=params.method,
                    seed=(args.seed + index) if args.seed is not None else index,
                )
            )
        return
    combos = all_params()
    rng = random.Random(args.seed)
    rng.shuffle(combos)
    for index in range(count):
        chosen = combos[index % len(combos)]
        yield generate(
            StoryParams(
                sector=chosen.sector,
                clue=chosen.clue,
                cause=chosen.cause,
                method=chosen.method,
                seed=(args.seed + index) if args.seed is not None else index,
            )
        )


def trace_lines(world: PondBandWorld) -> list[str]:
    lines = ["Trace:"]
    for event in world.history:
        lines.append(f"- {event.id}: {event.text}")
    lines.append("State:")
    lines.append(
        "  pair_trust={trust:.1f} drill_ready={ready:.1f} band_present={present:.1f} band_recovered={recovered:.1f} band_shared={shared:.1f}".format(
            trust=world.get("pair").memes["trust"],
            ready=world.get("pair").meters["drill_ready"],
            present=world.get("band").meters["present"],
            recovered=world.get("band").meters["recovered"],
            shared=world.get("band").meters["shared"],
        )
    )
    return lines


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if header:
        print(header)
    print(sample.story)
    if args.trace:
        print()
        print("\n".join(trace_lines(sample.world)))
    if args.qa:
        print("\nPrompts:")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print("\nStory QA:")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\nWorld QA:")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            for combo in sorted(asp_valid_combos()):
                print("\t".join(combo))
            return 0

        samples = list(iter_samples(args))
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples):
            header = None
            if args.all:
                p = sample.params
                header = f"### sector={p.sector} clue={p.clue} cause={p.cause} method={p.method}"
            elif len(samples) > 1:
                header = f"### variant {index + 1}"
            emit(sample, args, header=header)
            if index < len(samples) - 1:
                print("\n---\n")
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
