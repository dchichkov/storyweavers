#!/usr/bin/env python3
"""A mystery-leaning skate-park storyworld about a missing bell, a clue-rhyme, and reconciliation.

Internal source tale:
At a skate park beside a misty pond and a crystal bush, two young skaters are
rehearsing a twilight signal routine. Their small silver bell goes missing just
before the run. One friend leaves a rhyme clue because he noticed where the bell
flew, but the other mistakes the rhyme for a dramatic prank. When they stop
blaming each other and follow the physical signs together, they recover the bell
and make up.
"""

from __future__ import annotations

import argparse
import copy
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
class Run:
    id: str
    name: str
    opening: str
    loss: str
    finish: str


@dataclass(frozen=True)
class ClueMark:
    id: str
    rhyme: str
    place: str
    hint: str
    misread: str


@dataclass(frozen=True)
class Drift:
    id: str
    place: str
    trap: str
    motion: str
    proof: str
    reveal: str


@dataclass(frozen=True)
class Recovery:
    id: str
    tool: str
    solves: str
    action: str
    evidence: str


@dataclass(frozen=True)
class StoryParams:
    run: str
    clue: str
    drift: str
    recovery: str
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
class MysteryWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str | bool | int] = field(default_factory=dict)

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

    def copy(self) -> "MysteryWorld":
        return copy.deepcopy(self)


RUNS: dict[str, Run] = {
    "spine": Run(
        id="spine",
        name="the spine ramp",
        opening="They started on the spine ramp, where each wheel note bounced back like a secret answer.",
        loss="Lark clipped the top edge of the ramp, and the silver bell on her signal cord snapped free.",
        finish="they crossed the spine ramp in perfect order, bell first and wheels close behind",
    ),
    "banks": Run(
        id="banks",
        name="the pond banks",
        opening="They warmed up on the pond banks, where the evening mist made every landing sound farther away than it was.",
        loss="Lark hopped the low bank too hard, and the silver bell skipped off her signal cord.",
        finish="they sailed over the pond banks in one smooth ribbon of turns",
    ),
    "pad": Run(
        id="pad",
        name="the manual pad",
        opening="They saved the manual pad for dusk, because the flat top let them hear even the tiniest ring.",
        loss="Lark tipped out of a long manual, and the silver bell bounced away under the fading lights.",
        finish="they rolled the manual pad shoulder to shoulder, steady and bright again",
    ),
}

CLUES: dict[str, ClueMark] = {
    "bush": ClueMark(
        id="bush",
        rhyme='Oz had chalked: "If the silver song feels far, ask the crystal bush where lost things are."',
        place="bush",
        hint="The chalk arrow beneath it pointed toward the crystal bush by the back fence",
        misread="Lark heard the singsong line and thought Oz was turning her worry into a little show",
    ),
    "pond": ClueMark(
        id="pond",
        rhyme='Oz had chalked: "When the night grows soft beyond, search the hush by the misty pond."',
        place="pond",
        hint="A pale loop under the last word curled toward the boards beside the misty pond",
        misread="Lark saw the neat couplet and decided Oz must be hiding the truth inside a poem",
    ),
    "stand": ClueMark(
        id="stand",
        rhyme='Oz had chalked: "Do not guess and do not wander grand; hear the silver near the judge\'s stand."',
        place="stand",
        hint="The final line ended beside a quick chalk sketch of the little judge's stand",
        misread="Lark mistook the careful rhyme for a teasing puzzle instead of a fast clue",
    ),
}

DRIFTS: dict[str, Drift] = {
    "breeze": Drift(
        id="breeze",
        place="bush",
        trap="branch",
        motion="A sharp breeze had caught the snapped signal cord and flipped the bell into the crystal bush.",
        proof="a thread of blue cord was trembling between the glassy twigs, and the silver bell flashed there like a star with nowhere to fall",
        reveal="When the branch eased back, the bush gave a tiny chiming shake that proved the wind, not Oz, had hidden the bell",
    ),
    "slats": Drift(
        id="slats",
        place="pond",
        trap="plank",
        motion="A wheel tap had sent the bell skittering across wet boards until it slipped between two pond-side slats.",
        proof="small moon-colored drops were gathered around a silver curve beneath the boards beside the misty pond",
        reveal="As soon as the edge lifted, a wet track showed the bell's whole path from the landing to the gap",
    ),
    "mesh": Drift(
        id="mesh",
        place="stand",
        trap="mesh",
        motion="The bell had bounced under the judge's stand and snagged in the loose mesh banner hanging there.",
        proof="every passing breath of air made the banner twitch, and a tiny silver wink answered from inside the fold",
        reveal="Once the mesh was pulled straight, the trapped bell swung free with one clear ring that matched the sound Oz had heard",
    ),
}

RECOVERIES: dict[str, Recovery] = {
    "glove": Recovery(
        id="glove",
        tool="Coach Nessa's padded glove",
        solves="branch",
        action="Oz steadied the glittering branch while Lark reached in with Coach Nessa's padded glove and worked the bell free from the twigs.",
        evidence="The glove kept the sharp crystal leaves from scratching her fingers while the branch stopped rattling.",
    ),
    "ruler": Recovery(
        id="ruler",
        tool="the coach's long measuring ruler",
        solves="plank",
        action="Lark slid the coach's long measuring ruler through the gap while Oz knelt at the edge, and together they nudged the bell onto the board tops.",
        evidence="The ruler gave the bell a safe path back up without forcing their hands into the wet slats.",
    ),
    "hook": Recovery(
        id="hook",
        tool="a bent banner hook from the shed",
        solves="mesh",
        action="Oz fetched a bent banner hook from the shed, and Lark used it to lift the loose mesh until the bell dropped softly into her palm.",
        evidence="The hook pulled the fabric away without tearing it, which showed the bell had only been trapped, not taken.",
    ),
}

PLACE_LABELS = {
    "bush": "the crystal bush",
    "pond": "the misty pond",
    "stand": "the judge's stand",
}

TRAP_LABELS = {
    "branch": "glassy twigs",
    "plank": "pond-side slats",
    "mesh": "loose banner mesh",
}


def sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.run not in RUNS:
        return False, f"unknown run: {params.run}"
    if params.clue not in CLUES:
        return False, f"unknown clue: {params.clue}"
    if params.drift not in DRIFTS:
        return False, f"unknown drift: {params.drift}"
    if params.recovery not in RECOVERIES:
        return False, f"unknown recovery: {params.recovery}"
    clue = CLUES[params.clue]
    drift = DRIFTS[params.drift]
    recovery = RECOVERIES[params.recovery]
    if clue.place != drift.place:
        return False, "the rhyme clue must point toward the place where the bell really went"
    if recovery.solves != drift.trap:
        return False, "the recovery tool must match the way the bell is trapped"
    return True, ""


def all_params() -> list[StoryParams]:
    combos: list[StoryParams] = []
    for run in RUNS:
        for clue in CLUES:
            for drift in DRIFTS:
                for recovery in RECOVERIES:
                    params = StoryParams(run=run, clue=clue, drift=drift, recovery=recovery)
                    if valid_params(params)[0]:
                        combos.append(params)
    return combos


def make_world(params: StoryParams) -> MysteryWorld:
    run = RUNS[params.run]
    clue = CLUES[params.clue]
    drift = DRIFTS[params.drift]
    recovery = RECOVERIES[params.recovery]
    world = MysteryWorld(params)
    world.add(Entity(id="lark", kind="character", type="girl", label="Lark", role="worrier", traits=["brave", "quick"]))
    world.add(Entity(id="oz", kind="character", type="boy", label="Oz", role="poet", traits=["observant", "rhyming"]))
    world.add(Entity(id="nessa", kind="character", type="woman", label="Coach Nessa", role="coach", traits=["calm", "steady"]))
    world.add(Entity(id="park", kind="place", type="skate_park", label="the skate park"))
    world.add(Entity(id="bush", kind="place", type="bush", label="the crystal bush"))
    world.add(Entity(id="pond", kind="place", type="pond", label="the misty pond"))
    world.add(Entity(id="stand", kind="place", type="stand", label="the judge's stand"))
    world.add(Entity(id="bell", kind="object", type="signal_bell", label="the silver bell"))
    world.add(Entity(id="pair", kind="group", type="duo", label="the two friends"))

    world.get("park").meters["mist"] = 1.0
    world.get("park").meters["mystery"] = 1.0
    world.get("bush").meters["glitter"] = 1.0
    world.get("pond").meters["fog"] = 1.0
    world.get("bell").meters["present"] = 1.0
    world.get("bell").meters["lost"] = 0.0
    world.get("pair").meters["show_ready"] = 1.0
    world.get("pair").memes["trust"] = 2.0
    world.get("pair").memes["wonder"] = 1.0
    world.get("lark").memes["trust"] = 1.0
    world.get("oz").memes["trust"] = 1.0

    world.facts.update(
        run_name=run.name,
        clue_rhyme=clue.rhyme,
        clue_hint=clue.hint,
        misread=clue.misread,
        true_place=PLACE_LABELS[drift.place],
        trap_label=TRAP_LABELS[drift.trap],
        drift_motion=drift.motion,
        drift_proof=drift.proof,
        drift_reveal=drift.reveal,
        recovery_tool=recovery.tool,
        repaired_rhyme="Slow blame, bright clue; next time I will search with you.",
    )
    return world


def opening(world: MysteryWorld) -> None:
    run = RUNS[world.params.run]
    pair = world.get("pair")
    pair.memes["joy"] += 1.0
    world.record(
        "opening",
        "The skate park sat between the crystal bush and the misty pond, and dusk made every rail and ramp look full of hiding places.",
        "park",
    )
    world.record(
        "setup",
        f"{run.opening} Lark rang a small silver bell before each turn so Oz would know exactly when to drop in behind her for their twilight routine.",
        "pair",
        "bell",
    )


def bell_goes_missing(world: MysteryWorld) -> None:
    run = RUNS[world.params.run]
    bell = world.get("bell")
    pair = world.get("pair")
    bell.meters["present"] = 0.0
    bell.meters["lost"] = 1.0
    pair.meters["show_ready"] = 0.0
    pair.memes["worry"] += 1.0
    world.record(
        "loss",
        f"{run.loss} When Lark looked down at the flat concrete, the bell was gone.",
        "lark",
        "bell",
    )


def reveal_clue(world: MysteryWorld) -> None:
    clue = CLUES[world.params.clue]
    oz = world.get("oz")
    oz.memes["helpfulness"] += 1.0
    world.record(
        "clue",
        f"In the chalk dust nearby, {clue.rhyme} {sentence_start(clue.hint)}.",
        "oz",
        clue.place,
    )


def misunderstanding(world: MysteryWorld) -> None:
    lark = world.get("lark")
    oz = world.get("oz")
    pair = world.get("pair")
    lark.memes["blame"] += 1.0
    lark.memes["fear"] += 0.5
    oz.memes["hurt"] += 1.0
    pair.memes["trust"] -= 1.0
    world.record(
        "misunderstanding",
        f'"Did you hide it so the mystery would feel bigger?" Lark asked. {world.facts["misread"]}, and Oz looked stung because he had chalked the rhyme to help, not to tease her.',
        "lark",
        "oz",
    )


def coach_turn(world: MysteryWorld) -> None:
    pair = world.get("pair")
    pair.memes["reflection"] += 1.0
    world.record(
        "turn",
        'Coach Nessa touched the chalk line with one shoe. "A spooky place can make quick guesses feel true," she said, "but clues belong to the ground first. Follow what moved, then decide what it means."',
        "nessa",
        "pair",
    )


def search(world: MysteryWorld) -> None:
    drift = DRIFTS[world.params.drift]
    pair = world.get("pair")
    lark = world.get("lark")
    oz = world.get("oz")
    lark.memes["curiosity"] += 1.0
    oz.memes["courage"] += 1.0
    pair.memes["trust"] += 0.5
    world.record(
        "search",
        f"So the two friends followed the rhyme together. {drift.motion} Soon they found the proof: {drift.proof}.",
        "pair",
        drift.place,
    )


def recover(world: MysteryWorld) -> None:
    drift = DRIFTS[world.params.drift]
    recovery = RECOVERIES[world.params.recovery]
    bell = world.get("bell")
    pair = world.get("pair")
    bell.meters["lost"] = 0.0
    bell.meters["present"] = 1.0
    bell.meters["recovered"] = 1.0
    pair.meters["show_ready"] = 1.0
    pair.memes["relief"] += 1.0
    world.record(
        "recover",
        f"{recovery.action} {recovery.evidence} {drift.reveal}.",
        "pair",
        "bell",
    )


def reconcile(world: MysteryWorld) -> None:
    lark = world.get("lark")
    oz = world.get("oz")
    pair = world.get("pair")
    lark.memes["blame"] = 0.0
    lark.memes["apology"] += 1.0
    oz.memes["hurt"] = 0.0
    oz.memes["forgiveness"] += 1.0
    pair.memes["trust"] += 1.5
    pair.memes["reconciliation"] += 1.0
    world.facts["reconciled"] = True
    world.record(
        "reconcile",
        f'"I chased the mystery before I trusted my friend," Lark said, holding out the bell. "{world.facts["repaired_rhyme"]}" Oz smiled at that and tapped the bell once with his knuckle. "That is the best line of the night," he said.',
        "lark",
        "oz",
    )


def closing(world: MysteryWorld) -> None:
    run = RUNS[world.params.run]
    pair = world.get("pair")
    pair.memes["joy"] += 1.0
    world.record(
        "ending",
        f"Lark tied the bell back on, Oz dropped in at the sound, and {run.finish}. The misty pond held its pale breath, the crystal bush flashed once in the dark, and the mystery ended with both friends laughing at the same rhyme instead of arguing over it.",
        "pair",
        "park",
    )


def tell(params: StoryParams) -> MysteryWorld:
    world = make_world(params)
    opening(world)
    world.para()
    bell_goes_missing(world)
    reveal_clue(world)
    misunderstanding(world)
    coach_turn(world)
    world.para()
    search(world)
    recover(world)
    reconcile(world)
    world.para()
    closing(world)
    return world


def generation_prompts(world: MysteryWorld) -> list[str]:
    run = RUNS[world.params.run]
    return [
        'Write a child-facing mystery set in a skate park that clearly includes "crystal bush" and "misty pond."',
        f"Center the tension on a missing silver bell during practice at {run.name}, and use a clue-rhyme to drive the search.",
        "Resolve the story through physical evidence, a spoken apology, and a final skating image that proves the friends are reconciled.",
    ]


def story_grounded_qa(world: MysteryWorld) -> list[QAItem]:
    drift = DRIFTS[world.params.drift]
    recovery = RECOVERIES[world.params.recovery]
    return [
        QAItem(
            question="Why did Lark think Oz was playing a trick?",
            answer=(
                "Lark found the bell missing and saw Oz's rhyme written in the chalk dust right away. "
                "Because the clue sounded playful while she was scared about losing the signal bell, she thought he had turned the problem into a prank."
            ),
        ),
        QAItem(
            question="Where had the silver bell really gone?",
            answer=(
                f"The bell had really gone to {PLACE_LABELS[drift.place]}. "
                f"{drift.motion} That is why Oz wrote the rhyme toward that place instead of searching somewhere random."
            ),
        ),
        QAItem(
            question="How did the friends solve the mystery?",
            answer=(
                f"They followed the rhyme together, noticed the physical proof, and used {recovery.tool} to free the bell. "
                "Once the bell came back and the evidence matched Oz's clue, the mystery stopped feeling personal and started making sense."
            ),
        ),
        QAItem(
            question="What helped the two friends reconcile?",
            answer=(
                "The recovery showed that the bell had been trapped by the skate park, not hidden by Oz. "
                "After that, Lark apologized for blaming him too quickly, and they returned to their routine together."
            ),
        ),
    ]


def world_knowledge_qa(world: MysteryWorld) -> list[QAItem]:
    drift = DRIFTS[world.params.drift]
    recovery = RECOVERIES[world.params.recovery]
    return [
        QAItem(
            question="Why can a small metal bell disappear so quickly at a skate park?",
            answer=(
                "A light metal object can bounce, slide, or snag in places that are easy to miss when people are moving fast. "
                "Ramps, boards, mesh, and plants can all hide something shiny until a careful search slows the scene down."
            ),
        ),
        QAItem(
            question="How can a rhyme be useful in a mystery instead of confusing?",
            answer=(
                "A short rhyme can help someone remember the right place to check when there is no time for a long explanation. "
                "It works best when the rhyme points toward real evidence that other people can verify for themselves."
            ),
        ),
        QAItem(
            question=f"Why was {recovery.tool} the right tool in this story?",
            answer=(
                f"It was the right tool because the bell was trapped by {TRAP_LABELS[drift.trap]}, not carried off by a person. "
                "The tool matched the physical problem, so the children could recover the bell safely and prove what had really happened."
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
valid(R,C,D,Y) :-
    run(R), clue(C), drift(D), recovery(Y),
    clue_place(C, P), drift_place(D, P),
    drift_trap(D, T), recovery_solves(Y, T).

ok :- chosen(R, C, D, Y), valid(R, C, D, Y).

#show valid/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from asp import fact

    rows: list[str] = []
    for run in RUNS:
        rows.append(fact("run", run))
    for clue_key, clue in CLUES.items():
        rows.append(fact("clue", clue_key))
        rows.append(fact("clue_place", clue_key, clue.place))
    for drift_key, drift in DRIFTS.items():
        rows.append(fact("drift", drift_key))
        rows.append(fact("drift_place", drift_key, drift.place))
        rows.append(fact("drift_trap", drift_key, drift.trap))
    for recovery_key, recovery in RECOVERIES.items():
        rows.append(fact("recovery", recovery_key))
        rows.append(fact("recovery_solves", recovery_key, recovery.solves))
    if params is not None:
        rows.append(fact("chosen", params.run, params.clue, params.drift, params.recovery))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str]]:
    from asp import atoms, solve

    combos: set[tuple[str, str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        for combo in atoms(model, "valid"):
            combos.add(tuple(str(part) for part in combo))
    return combos


def asp_accepts(params: StoryParams) -> bool:
    from asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params)), "ok"))


def verify() -> str:
    python_combos = {(p.run, p.clue, p.drift, p.recovery) for p in all_params()}
    asp_combos = asp_valid_combos()
    if python_combos != asp_combos:
        only_python = sorted(python_combos - asp_combos)
        only_asp = sorted(asp_combos - python_combos)
        raise StoryError(f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}")
    for params in all_params():
        if not asp_accepts(params):
            raise StoryError(f"ASP rejected valid params: {params}")
        sample = generate(params)
        if "crystal bush" not in sample.story or "misty pond" not in sample.story or "skate park" not in sample.story:
            raise StoryError(f"required seed language missing from story for params={params}")
        if len(sample.story_qa) < 3 or len(sample.world_qa) < 3:
            raise StoryError(f"QA too thin for params={params}")
        if not sample.world.facts.get("reconciled"):
            raise StoryError(f"story did not reconcile for params={params}")
        if sample.world.get("bell").meters["present"] < 1.0:
            raise StoryError(f"bell was not recovered for params={params}")
    return f"OK: Python and ASP agree on {len(python_combos)} valid skate-park mysteries, and each story resolves the bell mystery through reconciliation."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", choices=sorted(RUNS))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--drift", choices=sorted(DRIFTS))
    parser.add_argument("--recovery", choices=sorted(RECOVERIES))
    parser.add_argument("--seed", type=int, default=13)
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
    explicit = any(getattr(args, key) is not None for key in ("run", "clue", "drift", "recovery"))
    if explicit:
        params = StoryParams(
            run=args.run or rng.choice(list(RUNS)),
            clue=args.clue or rng.choice(list(CLUES)),
            drift=args.drift or rng.choice(list(DRIFTS)),
            recovery=args.recovery or rng.choice(list(RECOVERIES)),
            seed=args.seed,
        )
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params
    choice = rng.choice(all_params())
    return StoryParams(choice.run, choice.clue, choice.drift, choice.recovery, seed=args.seed)


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in all_params():
            yield generate(params)
        return
    explicit = any(getattr(args, key) is not None for key in ("run", "clue", "drift", "recovery"))
    if explicit:
        rng = random.Random(args.seed)
        for _ in range(max(1, args.n)):
            yield generate(resolve_params(args, rng))
        return
    combos = all_params()
    rng = random.Random(args.seed)
    rng.shuffle(combos)
    count = max(1, args.n)
    for index in range(count):
        chosen = combos[index % len(combos)]
        yield generate(StoryParams(chosen.run, chosen.clue, chosen.drift, chosen.recovery, seed=args.seed + index))


def _trace_lines(world: MysteryWorld) -> list[str]:
    lines = ["Trace:"]
    for event in world.history:
        lines.append(f"- {event.id}: {event.text}")
    lines.append("State:")
    lines.append(
        "  pair_trust={trust:.1f} show_ready={ready:.1f} bell_present={present:.1f} bell_recovered={recovered:.1f}".format(
            trust=world.get("pair").memes["trust"],
            ready=world.get("pair").meters["show_ready"],
            present=world.get("bell").meters["present"],
            recovered=world.get("bell").meters["recovered"],
        )
    )
    return lines


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if args.json:
        payload = sample.to_dict()
        if header:
            payload = {"header": header, **payload}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    if header:
        print(header)
    print(sample.story)
    if args.trace:
        print()
        print("\n".join(_trace_lines(sample.world)))
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
                header = f"### run={p.run} clue={p.clue} drift={p.drift} recovery={p.recovery}"
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
