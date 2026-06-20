#!/usr/bin/env python3
"""A mystery-leaning skate-park storyworld about a lost key, a rhyme, and reconciliation.

Internal source tale:
Two young skaters practice at dusk in a skate park beside a misty pond and a
crystal bush. Their shared silver skate key disappears. A chalk rhyme seems like
an unkind prank from the friend who loves wordplay, but the rhyme is really a
helpful clue to where the key bounced. When the friends stop blaming each other
and search the physical world together, they recover the key and make peace.
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
class Spot:
    id: str
    name: str
    opening: str
    wobble: str
    finish: str


@dataclass(frozen=True)
class Clue:
    id: str
    rhyme: str
    place: str
    hint: str
    misunderstanding: str


@dataclass(frozen=True)
class Cause:
    id: str
    place: str
    kind: str
    motion: str
    discovery: str
    aftereffect: str


@dataclass(frozen=True)
class Method:
    id: str
    tool: str
    solves: str
    action: str
    proof: str


@dataclass(frozen=True)
class StoryParams:
    spot: str
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
class SkateWorld:
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

    def copy(self) -> "SkateWorld":
        return copy.deepcopy(self)


SPOTS: dict[str, Spot] = {
    "rail": Spot(
        id="rail",
        name="the silver rail",
        opening="They started at the silver rail, where each landing rang like a spoon on glass.",
        wobble="Rin's front truck clicked loose after a sharp grind beside the rail.",
        finish="they flew by the silver rail in one clean line",
    ),
    "steps": Spot(
        id="steps",
        name="the pond steps",
        opening="They warmed up on the pond steps, where the mist made every wheel sound soft and secret.",
        wobble="Rin's front truck shivered loose after a jump down the damp steps.",
        finish="they hopped the pond steps together without missing a beat",
    ),
    "bowl": Spot(
        id="bowl",
        name="the moon bowl",
        opening="They saved the moon bowl for last, because the curved concrete held echoes like a whispered dare.",
        wobble="Rin's front truck knocked loose after she carved high along the bowl wall.",
        finish="they stitched the moon bowl together with matching turns",
    ),
}

CLUES: dict[str, Clue] = {
    "bush": Clue(
        id="bush",
        rhyme='Tao had chalked: "Past the jump and through the hush, seek your silver in the crystal bush."',
        place="bush",
        hint="the chalk line pointed toward the glittering bush by the fence",
        misunderstanding="Rin thought Tao had turned a real problem into a teasing game",
    ),
    "pond": Clue(
        id="pond",
        rhyme='Tao had chalked: "Do not stomp and do not bond to guesses; listen by the misty pond."',
        place="pond",
        hint="the rhyme aimed them toward the fog-soft planks beside the pond",
        misunderstanding="Rin heard the playful rhyme and assumed Tao was hiding the truth behind a joke",
    ),
    "drain": Clue(
        id="drain",
        rhyme='Tao had chalked: "Where the late wheels clatter on, check the drain before the dawn."',
        place="drain",
        hint="the couplet pointed toward the little drain slot under the far bank",
        misunderstanding="Rin mistook the neat couplet for a prank instead of a map",
    ),
}

CAUSES: dict[str, Cause] = {
    "gust": Cause(
        id="gust",
        place="bush",
        kind="snag",
        motion="A pond breeze had flipped the key off the bench and spun it into the crystal bush.",
        discovery="beads of mist were shining on one branch, and the silver key was snagged there like a tiny moon",
        aftereffect="The branch sprang back with a chiming shake, proving the wind had hidden the key, not Tao.",
    ),
    "skip": Cause(
        id="skip",
        place="pond",
        kind="reed",
        motion="A bouncing board had skipped the key across a wet plank near the pond.",
        discovery="the key had slid under the misty reeds, where fog drops made the metal blink and disappear",
        aftereffect="When the reeds parted, both children could see the wet trail the key had taken.",
    ),
    "roll": Cause(
        id="roll",
        place="drain",
        kind="grate",
        motion="The sloped concrete had rolled the key away until it clicked against the drain grate.",
        discovery="a ribbon of wheel dust ended at the grate, and the key was trapped just behind the bars",
        aftereffect="The metal answered with a tiny ping, the exact sound Tao had heard before he wrote the rhyme.",
    ),
}

METHODS: dict[str, Method] = {
    "glove": Method(
        id="glove",
        tool="a padded glove",
        solves="snag",
        action="Tao held the branch still while Rin reached in with a padded glove and twisted the key free.",
        proof="The glove kept the sharp crystals from scratching her hand while the branch stopped rattling.",
    ),
    "net": Method(
        id="net",
        tool="the park's stray-ball net",
        solves="reed",
        action="Rin lowered the stray-ball net between the reeds, and Tao guided the rim until the key slid into it.",
        proof="The wet reeds bowed into the mesh, and the silver key clinked against the net ring.",
    ),
    "magnet": Method(
        id="magnet",
        tool="a little magnet tied to a lace",
        solves="grate",
        action="Tao dropped a little magnet on a lace through the grate, and Rin drew it up with the key swinging underneath.",
        proof="The key rose cleanly once the magnet caught, which showed it had only been trapped, not stolen.",
    ),
}

PLACE_LABELS = {
    "bush": "the crystal bush",
    "pond": "the misty pond",
    "drain": "the drain by the far bank",
}

KIND_LABELS = {
    "snag": "a branch snag",
    "reed": "wet reeds",
    "grate": "a drain grate",
}


def sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.spot not in SPOTS:
        return False, f"unknown spot: {params.spot}"
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
        return False, "the rhyme clue has to point toward the place where the key really went"
    if method.solves != cause.kind:
        return False, "the recovery method must fit the way the key is trapped"
    return True, ""


def all_params() -> list[StoryParams]:
    combos: list[StoryParams] = []
    for spot in SPOTS:
        for clue in CLUES:
            for cause in CAUSES:
                for method in METHODS:
                    params = StoryParams(spot=spot, clue=clue, cause=cause, method=method)
                    if valid_params(params)[0]:
                        combos.append(params)
    return combos


def make_world(params: StoryParams) -> SkateWorld:
    spot = SPOTS[params.spot]
    clue = CLUES[params.clue]
    cause = CAUSES[params.cause]
    method = METHODS[params.method]
    world = SkateWorld(params)
    world.add(
        Entity(
            id="rin",
            kind="character",
            type="girl",
            label="Rin",
            role="accuser",
            traits=["focused", "quick"],
        )
    )
    world.add(
        Entity(
            id="tao",
            kind="character",
            type="boy",
            label="Tao",
            role="suspect",
            traits=["gentle", "rhyming"],
        )
    )
    world.add(
        Entity(
            id="bea",
            kind="character",
            type="woman",
            label="Coach Bea",
            role="coach",
            traits=["steady"],
        )
    )
    world.add(Entity(id="park", kind="place", type="skate_park", label="the skate park"))
    world.add(Entity(id="bush", kind="place", type="bush", label="the crystal bush"))
    world.add(Entity(id="pond", kind="place", type="pond", label="the misty pond"))
    world.add(Entity(id="drain", kind="place", type="drain", label="the drain by the far bank"))
    world.add(Entity(id="key", kind="object", type="tool", label="the silver skate key"))
    world.add(Entity(id="pair", kind="group", type="duo", label="the two friends"))

    world.get("park").meters["mist"] = 1.0
    world.get("park").meters["echo"] = 1.0
    world.get("bush").meters["glitter"] = 1.0
    world.get("pond").meters["fog"] = 1.0
    world.get("key").meters["present"] = 1.0
    world.get("pair").meters["routine_ready"] = 1.0
    world.get("pair").memes["trust"] = 2.0
    world.get("rin").memes["trust"] = 1.0
    world.get("tao").memes["trust"] = 1.0

    world.facts.update(
        spot_name=spot.name,
        clue_rhyme=clue.rhyme,
        clue_hint=clue.hint,
        misunderstanding=clue.misunderstanding,
        true_place=PLACE_LABELS[cause.place],
        tool=method.tool,
        cause_motion=cause.motion,
        cause_discovery=cause.discovery,
        cause_aftereffect=cause.aftereffect,
    )
    return world


def opening(world: SkateWorld) -> None:
    spot = SPOTS[world.params.spot]
    park = world.get("park")
    pair = world.get("pair")
    pair.memes["joy"] += 1.0
    park.meters["mist"] += 0.5
    world.record(
        "opening",
        "At dusk the skate park hummed beside the misty pond, and the crystal bush by the fence held the last light like a jar of stars.",
        "park",
    )
    world.record(
        "setup",
        f"{spot.opening} Rin and Tao were practicing a two-person run for Saturday, sharing one silver skate key because Rin's front truck always needed one last snug turn.",
        "pair",
        "key",
    )


def key_goes_missing(world: SkateWorld) -> None:
    spot = SPOTS[world.params.spot]
    key = world.get("key")
    pair = world.get("pair")
    key.meters["present"] = 0.0
    key.meters["lost"] = 1.0
    pair.meters["routine_ready"] = 0.0
    pair.memes["worry"] += 1.0
    world.record(
        "loss",
        f"{spot.wobble} When Rin rolled back to the bench, the silver skate key was gone.",
        "rin",
        "key",
    )


def reveal_rhyme(world: SkateWorld) -> None:
    clue = CLUES[world.params.clue]
    tao = world.get("tao")
    tao.memes["helpful"] += 1.0
    world.record(
        "rhyme",
        f"In its place {clue.rhyme} {sentence_start(clue.hint)}.",
        "tao",
        PLACE_LABELS[clue.place].replace("the ", ""),
    )


def accuse(world: SkateWorld) -> None:
    rin = world.get("rin")
    tao = world.get("tao")
    pair = world.get("pair")
    rin.memes["blame"] += 1.0
    rin.memes["hurt"] += 0.5
    tao.memes["hurt"] += 1.0
    pair.memes["trust"] -= 1.0
    world.record(
        "accuse",
        f'"Did you hide it to make me chase a poem?" Rin asked. {world.facts["misunderstanding"]}, and Tao\'s face fell because he had meant the rhyme as help, not mockery.',
        "rin",
        "tao",
    )


def coach_turn(world: SkateWorld) -> None:
    bea = world.get("bea")
    pair = world.get("pair")
    pair.memes["reflection"] += 1.0
    world.record(
        "turn",
        f'Coach Bea looked from the chalk to the empty bench. "A rhyme can hide a trick," she said, "but it can also carry a map. Read the ground before you read each other as enemies."',
        "bea",
        "pair",
    )


def search(world: SkateWorld) -> None:
    clue = CLUES[world.params.clue]
    cause = CAUSES[world.params.cause]
    rin = world.get("rin")
    tao = world.get("tao")
    pair = world.get("pair")
    rin.memes["curiosity"] += 1.0
    tao.memes["courage"] += 1.0
    pair.memes["trust"] += 0.5
    world.record(
        "search",
        f"So they followed the couplet together. {cause.motion} Soon they noticed the proof: {cause.discovery}.",
        "pair",
        clue.place,
    )


def recover(world: SkateWorld) -> None:
    cause = CAUSES[world.params.cause]
    method = METHODS[world.params.method]
    key = world.get("key")
    pair = world.get("pair")
    key.meters["lost"] = 0.0
    key.meters["present"] = 1.0
    key.meters["recovered"] = 1.0
    pair.meters["routine_ready"] = 1.0
    pair.memes["relief"] += 1.0
    world.record(
        "recover",
        f"{method.action} {method.proof} {cause.aftereffect}",
        "pair",
        "key",
    )


def reconcile(world: SkateWorld) -> None:
    rin = world.get("rin")
    tao = world.get("tao")
    pair = world.get("pair")
    rin.memes["blame"] = 0.0
    rin.memes["apology"] += 1.0
    tao.memes["hurt"] = 0.0
    tao.memes["forgiveness"] += 1.0
    pair.memes["trust"] += 1.5
    pair.memes["reconciliation"] += 1.0
    world.facts["reconciled"] = True
    world.record(
        "reconcile",
        '"I blamed the handwriting before I followed the clue," Rin said softly. "I was wrong. Quick blame, dark view; next time I will search with you." Tao let out the breath he had been holding and nodded. "That is a better rhyme," he said.',
        "rin",
        "tao",
    )


def closing(world: SkateWorld) -> None:
    spot = SPOTS[world.params.spot]
    pair = world.get("pair")
    pair.memes["joy"] += 1.0
    world.record(
        "ending",
        f"With the truck tightened at last, they tried the run again, and {spot.finish}. The misty pond kept its silver hush, the crystal bush gave one bright shake, and the mystery ended with both friends rolling home side by side.",
        "pair",
        "park",
    )


def tell(params: StoryParams) -> SkateWorld:
    world = make_world(params)
    opening(world)
    world.para()
    key_goes_missing(world)
    reveal_rhyme(world)
    accuse(world)
    coach_turn(world)
    world.para()
    search(world)
    recover(world)
    reconcile(world)
    world.para()
    closing(world)
    return world


def generation_prompts(world: SkateWorld) -> list[str]:
    spot = SPOTS[world.params.spot]
    return [
        'Write a child-facing mystery set in a skate park that clearly includes "crystal bush" and "misty pond."',
        f"Make the central problem a missing skate key during practice at {spot.name}, and let a rhyming chalk clue guide the turn.",
        "Resolve the story through physical search, a truthful apology, and a final image that proves the friends are reconciled.",
    ]


def story_grounded_qa(world: SkateWorld) -> list[QAItem]:
    clue = CLUES[world.params.clue]
    cause = CAUSES[world.params.cause]
    method = METHODS[world.params.method]
    return [
        QAItem(
            question="Why did Rin get upset with Tao?",
            answer=(
                f"Rin saw the silver skate key missing and found Tao's rhyming chalk clue in its place. "
                f"Because the rhyme sounded playful while she was worried, she thought Tao had hidden the key instead of helping her find it."
            ),
        ),
        QAItem(
            question="Where had the missing key really gone?",
            answer=(
                f"The key had really gone to {PLACE_LABELS[cause.place]}. "
                f"{cause.motion} That is why Tao's rhyme pointed there, even though Rin misunderstood it at first."
            ),
        ),
        QAItem(
            question="How did the friends solve the mystery and make up?",
            answer=(
                f"They followed the rhyme together and used {method.tool} to get the key back. "
                "After the recovery proved Tao had been guiding her instead of teasing her, Rin apologized and the two friends finished their run side by side."
            ),
        ),
        QAItem(
            question="What clue showed that Tao was telling the truth?",
            answer=(
                f"The physical proof matched the rhyme: {cause.discovery}. "
                f"Once they saw that, the clue stopped looking like a trick and started looking like a map."
            ),
        ),
    ]


def world_knowledge_qa(world: SkateWorld) -> list[QAItem]:
    cause = CAUSES[world.params.cause]
    method = METHODS[world.params.method]
    return [
        QAItem(
            question="Why can a small skate tool be hard to find at a skate park?",
            answer=(
                "A tiny metal tool can bounce, roll, or snag in places that are easy to overlook. "
                "Concrete slopes, reeds, and sharp bushes can hide something shiny until someone searches carefully."
            ),
        ),
        QAItem(
            question="How can a rhyme help in a mystery?",
            answer=(
                "A rhyme can help people remember where to look without using a long explanation. "
                "In this world, the couplet worked like a small map that pointed toward the right place."
            ),
        ),
        QAItem(
            question=f"Why was {method.tool} the right tool this time?",
            answer=(
                f"It was the right tool because the key was trapped by {KIND_LABELS[cause.kind]}, not carried away by a person. "
                f"That let the children recover the key safely once they understood the physical problem."
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
    spot(S), clue(C), cause(A), method(M),
    clue_place(C, P), cause_place(A, P),
    cause_kind(A, K), method_solves(M, K).

ok :- chosen(S, C, A, M), valid(S, C, A, M).

#show valid/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from asp import fact

    rows: list[str] = []
    for spot in SPOTS:
        rows.append(fact("spot", spot))
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
        rows.append(fact("chosen", params.spot, params.clue, params.cause, params.method))
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
    python_combos = {(p.spot, p.clue, p.cause, p.method) for p in all_params()}
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
        if len(sample.story_qa) < 3 or len(sample.world_qa) < 2:
            raise StoryError(f"QA too thin for params={params}")
        if not sample.world.facts.get("reconciled"):
            raise StoryError(f"story did not reconcile for params={params}")
    return f"OK: Python and ASP agree on {len(python_combos)} valid skate-park mysteries, and all generated stories reconcile cleanly."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spot", choices=sorted(SPOTS))
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
    explicit = any(getattr(args, key) is not None for key in ("spot", "clue", "cause", "method"))
    if explicit:
        params = StoryParams(
            spot=args.spot or rng.choice(list(SPOTS)),
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
    return StoryParams(choice.spot, choice.clue, choice.cause, choice.method, seed=args.seed)


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in all_params():
            yield generate(params)
        return
    explicit = any(getattr(args, key) is not None for key in ("spot", "clue", "cause", "method"))
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
        yield generate(StoryParams(chosen.spot, chosen.clue, chosen.cause, chosen.method, seed=args.seed + index))


def _trace_lines(world: SkateWorld) -> list[str]:
    lines = ["Trace:"]
    for event in world.history:
        lines.append(f"- {event.id}: {event.text}")
    lines.append("State:")
    lines.append(
        "  pair_trust={trust:.1f} routine_ready={ready:.1f} key_present={present:.1f} key_recovered={recovered:.1f}".format(
            trust=world.get("pair").memes["trust"],
            ready=world.get("pair").meters["routine_ready"],
            present=world.get("key").meters["present"],
            recovered=world.get("key").meters["recovered"],
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
                header = f"### spot={p.spot} clue={p.clue} cause={p.cause} method={p.method}"
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
