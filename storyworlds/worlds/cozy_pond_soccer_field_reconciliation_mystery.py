#!/usr/bin/env python3
"""A mystery-leaning soccer-field storyworld about a missing whistle and reconciliation.

Internal source tale:
Two children stay late on a soccer field beside a cozy pond to practice a pass
pattern. Their silver practice whistle disappears just before the final drill.
One child finds a clue marker from the other and mistakes it for a teasing game.
When their coach asks them to read the field instead of each other's anger, they
follow the physical evidence, recover the whistle, and make up before the first
evening kick.
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


@dataclass(frozen=True)
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
class PondFieldWorld:
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


SECTORS: dict[str, Sector] = {
    "north_goal": Sector(
        id="north_goal",
        name="the north goal",
        opening="They started beside the north goal, where the white net still held warm stripes of sunset.",
        loss="Mira set the whistle on the water bottle crate while Jonah tapped the ball back to her near the north goal.",
        finish="they sent three quick passes through the north goal lane and laughed when the net sang softly",
    ),
    "center_circle": Sector(
        id="center_circle",
        name="the center circle",
        opening="They began at the center circle, where the chalk ring looked pale and secret in the evening light.",
        loss="Mira placed the whistle on the cone stack while Jonah lined up a restart pass at the center circle.",
        finish="they spun the ball out of the center circle in one neat pattern and chased after it shoulder to shoulder",
    ),
    "corner_flag": Sector(
        id="corner_flag",
        name="the pond-side corner flag",
        opening="They practiced by the pond-side corner flag, where the field grass leaned toward the water like sleepy hair.",
        loss="Mira balanced the whistle on the bench rail while Jonah hurried to fetch the last orange cone by the corner flag.",
        finish="they curved the ball in from the corner flag and watched it skip across the goal mouth exactly as planned",
    ),
}

CLUES: dict[str, Clue] = {
    "mud_arrow": Clue(
        id="mud_arrow",
        place="reeds",
        marker="a muddy arrow pressed into the damp sideline dirt",
        lead="The arrow pointed toward the cozy pond reeds behind the goal.",
        misunderstanding="Mira saw the neat arrow and thought Jonah had turned a missing whistle into a puzzle on purpose",
    ),
    "blue_ribbon": Clue(
        id="blue_ribbon",
        place="net_sleeve",
        marker="a blue practice ribbon tied low on the goal net",
        lead="The ribbon marked the loose sleeve where the net folded against the post.",
        misunderstanding="Mira noticed the tied ribbon and decided Jonah must be making a show out of the trouble instead of helping",
    ),
    "shadow_note": Clue(
        id="shadow_note",
        place="bleacher_slot",
        marker='a folded note that read, "Look where the bench keeps its shadow"',
        lead="The note aimed them toward the hollow under the aluminum bleacher seat.",
        misunderstanding="Mira read the little note and took it as a teasing riddle when she wanted a plain answer",
    ),
}

CAUSES: dict[str, Cause] = {
    "reeds_skip": Cause(
        id="reeds_skip",
        place="reeds",
        kind="reeds",
        motion="A warm-up pass had clipped the bottle crate, and the whistle skittered over a damp board before slipping into the pond reeds.",
        discovery="Drops were trembling on the bent reeds, and the silver whistle was hanging there on its cord just above the mud.",
        proof="The wet mark on the board showed the whistle's whole path from the crate to the reeds.",
    ),
    "net_gust": Cause(
        id="net_gust",
        place="net_sleeve",
        kind="sleeve",
        motion="A breeze from the cozy pond had lifted the whistle cord and tucked it into the loose goal-net sleeve.",
        discovery="A bright bit of metal winked from the folded mesh where the sleeve wrapped the post.",
        proof="When the net shifted, the whistle gave the same tiny clink Jonah had heard a moment earlier.",
    ),
    "bench_roll": Cause(
        id="bench_roll",
        place="bleacher_slot",
        kind="slot",
        motion="The whistle had rolled off the rail and disappeared into the dark slot beneath the little bleacher bench.",
        discovery="Dust on the aluminum lip was broken by a fresh silver scratch leading into the slot.",
        proof="The mark ended exactly where the whistle rested in the cool bench shadow.",
    ),
}

METHODS: dict[str, Method] = {
    "scoop_net": Method(
        id="scoop_net",
        tool="the stray-ball scoop net",
        solves="reeds",
        action="Jonah lowered the stray-ball scoop net between the reeds while Mira steadied the handle, and the whistle slid into the mesh with a bright tap.",
        proof="The net kept their shoes out of the mud and lifted the whistle without tearing the reeds.",
    ),
    "keeper_glove": Method(
        id="keeper_glove",
        tool="a goalkeeper glove",
        solves="sleeve",
        action="Mira held the mesh open with a goalkeeper glove while Jonah teased the whistle cord free from the folded sleeve.",
        proof="The padded glove stopped the snag from tightening and let the whistle slip loose in one careful pull.",
    ),
    "tape_wand": Method(
        id="tape_wand",
        tool="a chalk stick wrapped with fresh tape",
        solves="slot",
        action="Jonah reached the chalk stick wrapped with fresh tape into the slot, and Mira guided it until the whistle cord caught and slid back out.",
        proof="The tape gave just enough grip to pull the whistle from the narrow bench shadow.",
    ),
}

PLACE_LABELS = {
    "reeds": "the cozy pond reeds",
    "net_sleeve": "the loose net sleeve",
    "bleacher_slot": "the hollow under the bleacher bench",
}

KIND_LABELS = {
    "reeds": "wet reeds by the pond",
    "sleeve": "a folded goal-net sleeve",
    "slot": "a narrow aluminum bench slot",
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
        return False, "the clue marker has to point to the place where the whistle really went"
    if method.solves != cause.kind:
        return False, "the recovery method must fit the way the whistle is trapped"
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


def make_world(params: StoryParams) -> PondFieldWorld:
    sector = SECTORS[params.sector]
    clue = CLUES[params.clue]
    cause = CAUSES[params.cause]
    method = METHODS[params.method]
    world = PondFieldWorld(params)
    world.add(
        Entity(
            id="mira",
            kind="character",
            type="girl",
            label="Mira",
            role="captain",
            traits=["quick", "earnest"],
        )
    )
    world.add(
        Entity(
            id="jonah",
            kind="character",
            type="boy",
            label="Jonah",
            role="marker",
            traits=["careful", "observant"],
        )
    )
    world.add(
        Entity(
            id="coach",
            kind="character",
            type="woman",
            label="Coach Imani",
            role="coach",
            traits=["steady"],
        )
    )
    world.add(Entity(id="field", kind="place", type="soccer_field", label="the soccer field"))
    world.add(Entity(id="pond", kind="place", type="pond", label="the cozy pond"))
    world.add(Entity(id="goal", kind="place", type="goal", label="the goal"))
    world.add(Entity(id="bench", kind="place", type="bench", label="the bleacher bench"))
    world.add(Entity(id="whistle", kind="object", type="tool", label="the silver practice whistle"))
    world.add(Entity(id="pair", kind="group", type="duo", label="the two teammates"))

    world.get("field").meters["dew"] = 1.0
    world.get("pond").meters["glow"] = 1.0
    world.get("whistle").meters["present"] = 1.0
    world.get("pair").meters["drill_ready"] = 1.0
    world.get("pair").memes["trust"] = 2.0
    world.get("mira").memes["trust"] = 1.0
    world.get("jonah").memes["trust"] = 1.0

    world.facts.update(
        sector_name=sector.name,
        clue_marker=clue.marker,
        clue_lead=clue.lead,
        misunderstanding=clue.misunderstanding,
        true_place=PLACE_LABELS[cause.place],
        cause_motion=cause.motion,
        cause_discovery=cause.discovery,
        cause_proof=cause.proof,
        tool=method.tool,
    )
    return world


def opening(world: PondFieldWorld) -> None:
    sector = SECTORS[world.params.sector]
    pair = world.get("pair")
    pair.memes["joy"] += 1.0
    world.record(
        "opening",
        "Evening settled over the soccer field beside the cozy pond, and the water held the last light so still that every sound felt like part of a secret.",
        "field",
    )
    world.record(
        "setup",
        f"{sector.opening} Mira and Jonah stayed after practice to rehearse a passing pattern, and Coach Imani had trusted them with the silver practice whistle to start their final drill.",
        "pair",
        "whistle",
    )


def whistle_goes_missing(world: PondFieldWorld) -> None:
    sector = SECTORS[world.params.sector]
    whistle = world.get("whistle")
    pair = world.get("pair")
    whistle.meters["present"] = 0.0
    whistle.meters["lost"] = 1.0
    pair.meters["drill_ready"] = 0.0
    pair.memes["worry"] += 1.0
    world.record(
        "loss",
        f"{sector.loss} When Mira turned back for it, the silver practice whistle was gone.",
        "mira",
        "whistle",
    )


def reveal_marker(world: PondFieldWorld) -> None:
    clue = CLUES[world.params.clue]
    jonah = world.get("jonah")
    jonah.memes["helpful"] += 1.0
    world.record(
        "marker",
        f"On the ground nearby was {clue.marker}. {sentence_start(clue.lead)} Jonah had left the marker after hearing the whistle's tiny sound and rushing to keep the last ball from rolling into the pond.",
        "jonah",
        clue.place,
    )


def accuse(world: PondFieldWorld) -> None:
    mira = world.get("mira")
    jonah = world.get("jonah")
    pair = world.get("pair")
    mira.memes["blame"] += 1.0
    mira.memes["hurt"] += 0.5
    jonah.memes["hurt"] += 1.0
    pair.memes["trust"] -= 1.0
    world.record(
        "accuse",
        f'"Did you hide it just to make the drill feel like a game?" Mira asked. {world.facts["misunderstanding"]}, and Jonah went quiet because he had been trying to mark the answer, not create a trick.',
        "mira",
        "jonah",
    )


def coach_turn(world: PondFieldWorld) -> None:
    pair = world.get("pair")
    pair.memes["reflection"] += 1.0
    world.record(
        "turn",
        'Coach Imani knelt by the mark and said, "A clue can feel mean when you are scared, but the field is telling us something. Read the grass, the net, and the shadows before you read each other as enemies."',
        "coach",
        "pair",
    )


def search(world: PondFieldWorld) -> None:
    cause = CAUSES[world.params.cause]
    pair = world.get("pair")
    mira = world.get("mira")
    jonah = world.get("jonah")
    mira.memes["curiosity"] += 1.0
    jonah.memes["courage"] += 1.0
    pair.memes["trust"] += 0.5
    world.record(
        "search",
        f"So the two teammates followed the clue together. {cause.motion} Then they saw the proof: {cause.discovery} {cause.proof}",
        "pair",
        cause.place,
    )


def recover(world: PondFieldWorld) -> None:
    method = METHODS[world.params.method]
    whistle = world.get("whistle")
    pair = world.get("pair")
    whistle.meters["lost"] = 0.0
    whistle.meters["present"] = 1.0
    whistle.meters["recovered"] = 1.0
    pair.meters["drill_ready"] = 1.0
    pair.memes["relief"] += 1.0
    world.record(
        "recover",
        f"{method.action} {method.proof}",
        "pair",
        "whistle",
    )


def reconcile(world: PondFieldWorld) -> None:
    mira = world.get("mira")
    jonah = world.get("jonah")
    pair = world.get("pair")
    mira.memes["blame"] = 0.0
    mira.memes["apology"] += 1.0
    jonah.memes["hurt"] = 0.0
    jonah.memes["forgiveness"] += 1.0
    pair.memes["trust"] += 1.5
    pair.memes["reconciliation"] += 1.0
    world.facts["reconciled"] = True
    world.record(
        "reconcile",
        '"I saw the mystery before I saw my friend," Mira said softly. "I was wrong to blame you before I followed the field." Jonah nodded and answered, "Next time I will leave the clue and the words together." The apology settled the last sharp feeling between them.',
        "mira",
        "jonah",
    )


def closing(world: PondFieldWorld) -> None:
    sector = SECTORS[world.params.sector]
    pair = world.get("pair")
    pair.memes["joy"] += 1.0
    world.record(
        "ending",
        f"Mira blew the whistle at last, and {sector.finish}. Beyond the line, the cozy pond kept its calm silver face, and the mystery ended with the two teammates starting the drill together instead of apart.",
        "pair",
        "field",
    )


def tell(params: StoryParams) -> PondFieldWorld:
    world = make_world(params)
    opening(world)
    world.para()
    whistle_goes_missing(world)
    reveal_marker(world)
    accuse(world)
    coach_turn(world)
    world.para()
    search(world)
    recover(world)
    reconcile(world)
    world.para()
    closing(world)
    return world


def generation_prompts(world: PondFieldWorld) -> list[str]:
    sector = SECTORS[world.params.sector]
    return [
        'Write a child-facing mystery that clearly includes "cozy pond" and "soccer field."',
        f"Center the tension on a missing silver practice whistle during an after-practice drill at {sector.name}.",
        "Resolve the story through physical evidence, a spoken apology, and a final image that proves the teammates are reconciled.",
    ]


def story_grounded_qa(world: PondFieldWorld) -> list[QAItem]:
    cause = CAUSES[world.params.cause]
    method = METHODS[world.params.method]
    return [
        QAItem(
            question="Why did Mira get upset with Jonah?",
            answer=(
                f"Mira saw the whistle missing and found {world.facts['clue_marker']} nearby. "
                "Because she was worried about disappointing Coach Imani, she mistook Jonah's quick marker for a teasing game instead of a helpful clue."
            ),
        ),
        QAItem(
            question="Where had the missing whistle really gone?",
            answer=(
                f"The whistle had really gone to {PLACE_LABELS[cause.place]}. "
                f"{cause.motion} That is why the marker pointed there, even though Mira misunderstood it at first."
            ),
        ),
        QAItem(
            question="How did the children solve the mystery?",
            answer=(
                f"They followed the field marker together and used {method.tool} to get the whistle back. "
                "Once the physical proof matched Jonah's clue, the mystery stopped feeling like a trick and started making sense."
            ),
        ),
        QAItem(
            question="How did the story show reconciliation at the end?",
            answer=(
                "Mira apologized for blaming Jonah before checking the evidence, and Jonah answered with calm forgiveness. "
                "They proved the friendship was repaired by starting the final drill side by side and listening to the whistle together."
            ),
        ),
    ]


def world_knowledge_qa(world: PondFieldWorld) -> list[QAItem]:
    cause = CAUSES[world.params.cause]
    method = METHODS[world.params.method]
    return [
        QAItem(
            question="Why can a small tool vanish quickly on a sports field?",
            answer=(
                "Small tools can bounce, roll, or snag in places that players barely notice during practice. "
                "Grass, netting, benches, and pond edges can hide something shiny until someone slows down and searches carefully."
            ),
        ),
        QAItem(
            question="Why is searching together better than blaming in this world?",
            answer=(
                "Searching together lets the children compare clues with the real field instead of guessing at each other's motives. "
                "That turns fear into evidence and gives them a fair path back to trust."
            ),
        ),
        QAItem(
            question=f"Why was {method.tool} the right tool this time?",
            answer=(
                f"It was the right tool because the whistle was trapped by {KIND_LABELS[cause.kind]}, not taken by a person. "
                f"That made careful recovery more useful than a wild search."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = tell(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_grounded_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(S,C,A,M) :-
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
        if len(sample.story_qa) < 3 or len(sample.world_qa) < 2:
            raise StoryError(f"QA too thin for params={params}")
        if not sample.world.facts.get("reconciled"):
            raise StoryError(f"story did not reconcile for params={params}")
    return (
        f"OK: Python and ASP agree on {len(python_combos)} valid soccer-field mysteries, "
        "and all generated stories recover the whistle and reconcile the teammates."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sector", choices=sorted(SECTORS))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--cause", choices=sorted(CAUSES))
    parser.add_argument("--method", choices=sorted(METHODS))
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
    explicit = any(getattr(args, key) is not None for key in ("sector", "clue", "cause", "method"))
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
        yield generate(StoryParams(chosen.sector, chosen.clue, chosen.cause, chosen.method, seed=args.seed + index))


def _trace_lines(world: PondFieldWorld) -> list[str]:
    lines = ["Trace:"]
    for event in world.history:
        lines.append(f"- {event.id}: {event.text}")
    lines.append("State:")
    lines.append(
        "  pair_trust={trust:.1f} drill_ready={ready:.1f} whistle_present={present:.1f} whistle_recovered={recovered:.1f}".format(
            trust=world.get("pair").memes["trust"],
            ready=world.get("pair").meters["drill_ready"],
            present=world.get("whistle").meters["present"],
            recovered=world.get("whistle").meters["recovered"],
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
