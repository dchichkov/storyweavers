#!/usr/bin/env python3
"""A cozy-pond soccer-field mystery about a missing whistle and reconciliation.

Internal source tale:
Two teammates stay after practice on a soccer field beside a cozy pond to tidy
their cones and take one last passing turn. The frog-shaped whistle they share
for captain turns disappears just after they have a sharp little disagreement,
so one child wrongly suspects the other of hiding it. A coach asks them to look
at the field itself instead of the first hurt guess. They follow a physical
clue, recover the whistle with the right tool, apologize, and prove the repair
by starting the final drill together.
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
class Patch:
    id: str
    name: str
    origin: str
    opening: str
    loss: str
    ending_image: str


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
    patch: str
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
class WhistleWorld:
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


PATCHES: dict[str, Patch] = {
    "pond_touchline": Patch(
        id="pond_touchline",
        name="the pond-side touchline",
        origin="the cone crate lid",
        opening="Evening practice had ended, but Mira and Benji stayed on the soccer field beside the cozy pond, where the reeds made soft secret sounds against the fence.",
        loss="Mira set the little frog whistle on the cone crate lid while Benji chased their last rolling ball toward the line.",
        ending_image="they passed the ball up the touchline while the frog whistle bounced on its cord between them like a tiny green promise",
    ),
    "north_goal": Patch(
        id="north_goal",
        name="the north goal mouth",
        origin="the folded bench arm",
        opening="The north goal stood in long blue shade, and the cozy pond beyond the field looked like a blanket laid flat under the sky.",
        loss="Mira rested the frog whistle on the folded bench arm while Benji hurried to untwist the net after a hard shot.",
        ending_image="they sent three quick passes through the north goal mouth, and the whistle flashed at Mira's wrist before Benji wore it for the next turn",
    ),
    "center_circle": Patch(
        id="center_circle",
        name="the center circle",
        origin="the chalk board rail",
        opening="At the center circle, the chalk ring looked pale and important, and the cozy pond at the edge of the soccer field held the last gold light of day.",
        loss="Mira balanced the frog whistle on the chalk board rail while Benji gathered the orange marker discs near the kickoff spot.",
        ending_image="they rolled the ball around the center circle and traded captain turns so smoothly that the whistle hardly stopped moving",
    ),
}


CLUES: dict[str, Clue] = {
    "reed_bend": Clue(
        id="reed_bend",
        place="reed_gate",
        marker="a bent tuft of reeds with two bright drops trembling on it",
        lead="The bent reeds leaned away from the fence, as if something light on a cord had tugged through them.",
        misunderstanding="Mira noticed damp cleat prints nearby and, for one sore moment, decided Benji had walked off with the whistle instead of answering her honestly",
    ),
    "net_click": Clue(
        id="net_click",
        place="post_hook",
        marker="a tiny silver click above the post brace whenever the breeze touched the net",
        lead="The click came from high on the goal frame, exactly where a loose loop might catch.",
        misunderstanding="When Benji said he had heard the click earlier, Mira took it as proof that he had known more than he told her",
    ),
    "chalk_crescent": Clue(
        id="chalk_crescent",
        place="bench_shadow",
        marker="a chalk crescent under the bench leg with a narrow clean line through the dust",
        lead="The clean line pointed straight into the low shelf under the bench.",
        misunderstanding="Because Benji had been kneeling by the bench for cones, Mira thought the mark was a teasing sign he had made on purpose",
    ),
}


CAUSES: dict[str, Cause] = {
    "reed_snag": Cause(
        id="reed_snag",
        place="reed_gate",
        kind="low_pull",
        motion="A pond breeze had flipped the whistle cord off {origin}, and the soft loop caught on a low reed by the fence.",
        discovery="The green frog whistle hung from the bent reed like a sleepy bead above the mud.",
        proof="Tiny drops along the board and the grass made a wet shining path from {origin} to the reeds.",
    ),
    "post_hook": Cause(
        id="post_hook",
        place="post_hook",
        kind="high_hook",
        motion="A bouncing ball had bumped the whistle free, and the cord sprang up until it caught on the loose hook behind the goal post.",
        discovery="The whistle peeped from the netting each time the white mesh stirred.",
        proof="When Benji tapped the post, the hook answered with the same little click they had heard before.",
    ),
    "bench_slide": Cause(
        id="bench_slide",
        place="bench_shadow",
        kind="narrow_slot",
        motion="The whistle had rolled off {origin}, crossed a chalky strip of dirt, and slipped into the low shelf under the bench.",
        discovery="One green corner of the frog whistle showed from the shadow beneath the bench slat.",
        proof="The dust line ended exactly where the cord had tucked itself against the bench leg.",
    ),
}


METHODS: dict[str, Method] = {
    "corner_flag_hook": Method(
        id="corner_flag_hook",
        tool="the corner-flag hook",
        solves="low_pull",
        action="Benji eased the corner-flag hook under the cord while Mira held his sleeve, and together they lifted the whistle free without stepping into the muddy edge.",
        proof="The long hook kept their shoes off the slick bank and kept the whistle clean enough to use at once.",
    ),
    "goalie_glove": Method(
        id="goalie_glove",
        tool="a goalkeeper glove",
        solves="high_hook",
        action="Mira pulled the net wide with a goalkeeper glove while Benji unwound the cord from the hook one careful turn at a time.",
        proof="The padded glove kept the mesh from pinching the cord again while they worked.",
    ),
    "lace_loop": Method(
        id="lace_loop",
        tool="a spare lace loop",
        solves="narrow_slot",
        action="Benji fed a spare lace loop into the low shelf, and Mira caught the whistle cord so they could draw it back together.",
        proof="The lace bent through the narrow gap where their fingers could not reach.",
    ),
}


PLACE_LABELS = {
    "reed_gate": "the reeds by the pond fence",
    "post_hook": "the back hook of the goal post",
    "bench_shadow": "the shadow under the aluminum bench",
}


def all_params() -> list[StoryParams]:
    rows: list[StoryParams] = []
    for patch_key in PATCHES:
        for clue_key in CLUES:
            for cause_key in CAUSES:
                for method_key in METHODS:
                    params = StoryParams(patch_key, clue_key, cause_key, method_key)
                    ok, _ = valid_params(params)
                    if ok:
                        rows.append(params)
    return rows


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.patch not in PATCHES:
        return False, f"unknown patch: {params.patch}"
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
        return False, f"clue {clue.id} points to {clue.place}, not {cause.place}"
    if method.solves != cause.kind:
        return False, f"method {method.id} solves {method.solves}, not {cause.kind}"
    return True, ""


def make_world(params: StoryParams) -> WhistleWorld:
    patch = PATCHES[params.patch]
    world = WhistleWorld(params=params)

    mira = world.add(
        Entity(
            id="mira",
            kind="character",
            type="girl",
            label="Mira",
            traits=["careful", "quick"],
        )
    )
    benji = world.add(
        Entity(
            id="benji",
            kind="character",
            type="boy",
            label="Benji",
            traits=["steady", "helpful"],
        )
    )
    coach = world.add(
        Entity(
            id="coach_ines",
            kind="character",
            type="woman",
            label="Coach Ines",
            traits=["patient"],
        )
    )
    whistle = world.add(
        Entity(
            id="whistle",
            kind="object",
            type="whistle",
            label="the little frog whistle",
            attrs={"material": "green enamel", "owner": "team"},
        )
    )
    pond = world.add(
        Entity(
            id="pond",
            kind="place",
            type="pond",
            label="the cozy pond",
            attrs={"setting": "soccer field edge"},
        )
    )
    field = world.add(
        Entity(
            id="field",
            kind="place",
            type="soccer_field",
            label="the soccer field",
        )
    )
    pair = world.add(
        Entity(
            id="pair",
            kind="relationship",
            type="friendship",
            label="Mira and Benji's teamwork",
        )
    )

    mira.memes["trust"] = 0.8
    mira.memes["hurt"] = 0.1
    benji.memes["trust"] = 0.8
    benji.memes["hurt"] = 0.1
    coach.memes["calm"] = 1.0
    pair.memes["trust"] = 0.8
    pair.memes["reconciliation"] = 0.0
    pair.meters["drill_ready"] = 0.4
    whistle.meters["present"] = 1.0
    whistle.meters["recovered"] = 0.0
    whistle.meters["dry"] = 1.0
    whistle.meters["shared"] = 0.0
    pond.meters["distance_m"] = 4.0
    field.meters["light"] = 0.5

    world.facts.update(
        {
            "patch_name": patch.name,
            "origin": patch.origin,
            "suspected": "benji",
            "helper": "coach_ines",
            "object_name": whistle.label,
            "setting": "soccer field",
            "seed_words": "cozy pond",
            "reconciled": False,
            "apology": "",
            "mystery_answer": "",
            "ending_image": patch.ending_image,
        }
    )
    return world


def opening_scene(world: WhistleWorld) -> None:
    patch = PATCHES[world.params.patch]
    world.say(patch.opening)
    world.record(
        "setup",
        "Coach Ines let them keep the little frog whistle for one last captain-turn drill, because both children had worked hard all afternoon.",
        "coach_ines",
        "pair",
    )
    world.record("loss", patch.loss, "mira", "whistle")
    world.get("whistle").meters["present"] = 0.0
    world.get("pair").meters["drill_ready"] = 0.2
    world.para()


def spark_misunderstanding(world: WhistleWorld) -> None:
    clue = CLUES[world.params.clue]
    patch = PATCHES[world.params.patch]
    mira = world.get("mira")
    benji = world.get("benji")
    pair = world.get("pair")
    mira.memes["hurt"] += 0.7
    mira.memes["trust"] -= 0.4
    benji.memes["hurt"] += 0.4
    pair.memes["trust"] -= 0.5
    world.record(
        "missing",
        f"When Mira reached back toward {patch.origin}, it was bare, and the small green cord was nowhere on the grass.",
        "mira",
        "whistle",
    )
    world.record(
        "guess",
        "Benji said he had only heard a small sound near the field edge, but the answer felt thin to Mira while her cheeks were still hot from their earlier disagreement.",
        "benji",
        "mira",
    )
    world.record("misread", clue.misunderstanding + ".", "mira", "benji")
    world.record(
        "coach_turn",
        "Coach Ines drew closer and said that mysteries on a soccer field should be solved with eyes, ears, and kind words before blame.",
        "coach_ines",
        "pair",
    )
    world.para()


def investigate(world: WhistleWorld) -> None:
    clue = CLUES[world.params.clue]
    place = PLACE_LABELS[clue.place]
    world.record(
        "clue",
        f"Near {place}, they found {clue.marker}.",
        "pair",
        clue.place,
    )
    world.record("lead", clue.lead, "coach_ines", clue.place)
    world.facts["clue_marker"] = clue.marker
    world.facts["clue_place"] = place
    world.para()


def recover_whistle(world: WhistleWorld) -> None:
    patch = PATCHES[world.params.patch]
    cause = CAUSES[world.params.cause]
    method = METHODS[world.params.method]
    whistle = world.get("whistle")
    pair = world.get("pair")
    world.record(
        "motion",
        cause.motion.format(origin=patch.origin),
        "coach_ines",
        "whistle",
    )
    world.record("discover", cause.discovery, "pair", "whistle")
    world.record("recover", method.action, "pair", "whistle")
    world.record("proof", method.proof + " " + cause.proof.format(origin=patch.origin), "coach_ines", "pair")
    whistle.meters["recovered"] = 1.0
    whistle.meters["present"] = 1.0
    whistle.meters["dry"] = 1.0 if method.id != "corner_flag_hook" else 0.9
    pair.meters["drill_ready"] = 0.8
    world.facts["mystery_answer"] = cause.motion.format(origin=patch.origin)
    world.facts["recovery_place"] = PLACE_LABELS[cause.place]
    world.facts["recovery_tool"] = method.tool
    world.facts["proof"] = cause.proof.format(origin=patch.origin)
    world.para()


def reconcile(world: WhistleWorld) -> None:
    mira = world.get("mira")
    benji = world.get("benji")
    pair = world.get("pair")
    whistle = world.get("whistle")
    mira.memes["trust"] += 0.5
    mira.memes["hurt"] = max(0.0, mira.memes["hurt"] - 0.6)
    benji.memes["trust"] += 0.3
    benji.memes["hurt"] = max(0.0, benji.memes["hurt"] - 0.3)
    pair.memes["trust"] += 0.6
    pair.memes["reconciliation"] = 1.0
    pair.meters["drill_ready"] = 1.0
    whistle.meters["shared"] = 1.0
    apology = (
        "Mira said she was sorry for turning a clue into an accusation, and Benji admitted he should have explained the strange sound right away instead of shrugging."
    )
    world.record("apology", apology, "mira", "benji")
    world.record(
        "repair",
        "Benji nodded, looped the whistle onto Mira's wrist first, and she passed it back to him before either of them touched the ball, just to show the field that the friendship was fixed.",
        "benji",
        "mira",
    )
    world.record(
        "ending",
        "Then " + PATCHES[world.params.patch].ending_image + ". Frogs chirped by the cozy pond while the last mystery of the soccer field closed as gently as a gate.",
        "pair",
        "field",
    )
    world.facts["reconciled"] = True
    world.facts["apology"] = apology


def build_story_qa(world: WhistleWorld) -> list[QAItem]:
    clue = CLUES[world.params.clue]
    cause = CAUSES[world.params.cause]
    method = METHODS[world.params.method]
    return [
        QAItem(
            "Why did Mira think Benji had hidden the whistle?",
            (
                f"She was already upset from their earlier disagreement, so the missing whistle made her rush to the worst guess. "
                f"When she saw {clue.marker}, she misread the sign before Coach Ines slowed her down."
            ),
        ),
        QAItem(
            "What clue led them to the whistle?",
            (
                f"They found {clue.marker} near {PLACE_LABELS[clue.place]}. "
                f"That sign pointed them toward the place where the whistle had really gone."
            ),
        ),
        QAItem(
            "Where was the whistle really hiding?",
            (
                f"It was at {PLACE_LABELS[cause.place]}. "
                f"{cause.discovery}"
            ),
        ),
        QAItem(
            "How did they get the whistle back?",
            (
                f"They used {method.tool} to recover it. "
                f"{method.proof}"
            ),
        ),
        QAItem(
            "How do we know the reconciliation was real at the end?",
            (
                "Mira apologized for accusing Benji, and Benji answered with calm honesty instead of staying hurt. "
                "They proved the repair by sharing the whistle and starting the last drill together."
            ),
        ),
    ]


def build_world_qa(world: WhistleWorld) -> list[QAItem]:
    return [
        QAItem(
            "Who helped solve the mystery besides the two teammates?",
            (
                "Coach Ines helped solve it. "
                "She pushed them to trust the field's evidence and to speak kindly before blaming each other."
            ),
        ),
        QAItem(
            "What feeling changed most in the story?",
            (
                "Trust changed the most. "
                "It dropped when Mira suspected Benji and then rose again after the apology and shared recovery."
            ),
        ),
        QAItem(
            "What final image proves the problem is over?",
            (
                f"The ending image is that {world.facts['ending_image']}. "
                "That shared drill shows the whistle is back and the friendship is steady again."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    opening_scene(world)
    spark_misunderstanding(world)
    investigate(world)
    recover_whistle(world)
    reconcile(world)
    story = world.render()
    prompts = [
        "Write a child-friendly mystery set on a soccer field beside a cozy pond.",
        "Center the plot on a missing whistle, a wrong suspicion, and reconciliation.",
        "Let concrete clues and physical state solve the problem instead of luck.",
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=build_story_qa(world),
        world_qa=build_world_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(P,C,U,M) :-
    patch(P),
    clue(C),
    cause(U),
    method(M),
    clue_place(C, Place),
    cause_place(U, Place),
    cause_kind(U, Kind),
    method_solves(M, Kind).

ok :-
    chosen(P,C,U,M),
    valid(P,C,U,M).

#show valid/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from asp import fact

    rows: list[str] = []
    for patch_key in PATCHES:
        rows.append(fact("patch", patch_key))
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
        rows.append(fact("chosen", params.patch, params.clue, params.cause, params.method))
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
    python_combos = {(p.patch, p.clue, p.cause, p.method) for p in all_params()}
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
        if len(sample.story_qa) < 5 or len(sample.world_qa) < 3:
            raise StoryError(f"QA too thin for params={params}")
        if not sample.world.facts.get("reconciled"):
            raise StoryError(f"story did not reconcile for params={params}")
        if sample.world.get("whistle").meters["recovered"] < 1.0:
            raise StoryError(f"whistle was not recovered for params={params}")
        if sample.world.get("pair").memes["trust"] <= 0.5:
            raise StoryError(f"friendship trust stayed too low for params={params}")
    return (
        f"OK: Python and ASP agree on {len(python_combos)} valid whistle mysteries, "
        "and every generated story restores the whistle and repairs the friendship."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patch", choices=sorted(PATCHES))
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
    explicit = any(getattr(args, key) is not None for key in ("patch", "clue", "cause", "method"))
    if explicit:
        params = StoryParams(
            patch=args.patch or rng.choice(list(PATCHES)),
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
    return StoryParams(choice.patch, choice.clue, choice.cause, choice.method, seed=args.seed)


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in all_params():
            yield generate(params)
        return
    count = max(1, args.n)
    explicit = any(getattr(args, key) is not None for key in ("patch", "clue", "cause", "method"))
    if explicit:
        rng = random.Random(args.seed)
        for index in range(count):
            params = resolve_params(args, rng)
            yield generate(
                StoryParams(
                    patch=params.patch,
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
                patch=chosen.patch,
                clue=chosen.clue,
                cause=chosen.cause,
                method=chosen.method,
                seed=(args.seed + index) if args.seed is not None else index,
            )
        )


def trace_lines(world: WhistleWorld) -> list[str]:
    lines = ["Trace:"]
    for event in world.history:
        lines.append(f"- {event.id}: {event.text}")
    lines.append("State:")
    lines.append(
        "  pair_trust={trust:.1f} pair_reconciliation={recon:.1f} drill_ready={ready:.1f} whistle_present={present:.1f} whistle_recovered={recovered:.1f} whistle_shared={shared:.1f}".format(
            trust=world.get("pair").memes["trust"],
            recon=world.get("pair").memes["reconciliation"],
            ready=world.get("pair").meters["drill_ready"],
            present=world.get("whistle").meters["present"],
            recovered=world.get("whistle").meters["recovered"],
            shared=world.get("whistle").meters["shared"],
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
                header = f"### patch={p.patch} clue={p.clue} cause={p.cause} method={p.method}"
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
