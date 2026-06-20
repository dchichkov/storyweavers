#!/usr/bin/env python3
"""A standalone splash-pad mystery about opening a crystal door by solving the right physical problem.

Internal source tale:
At a meadow-themed splash pad, two children race toward a crystal door that
opens only when water reaches its hidden play wheel. The door suddenly stays
shut, and the pad seems to whisper in one strange place. The children first
worry that the door is acting magical, but a repeating clue shows that a real
mechanism is in trouble. With calm help from an attendant, they test a careful
idea, fix the exact problem, and watch the crystal door open in a shining rush.
"""

from __future__ import annotations

import argparse
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class MeadowPad:
    id: str
    name: str
    opening: str
    secret: str
    ending_image: str
    sites: tuple[str, ...]


@dataclass(frozen=True)
class Clue:
    id: str
    place: str
    line: str
    hint: str
    eerie_guess: str


@dataclass(frozen=True)
class Fault:
    id: str
    place: str
    kind: str
    hidden_motion: str
    evidence: str
    release: str


@dataclass(frozen=True)
class Fix:
    id: str
    solves: str
    tool: str
    action: str
    proof: str


@dataclass(frozen=True)
class StoryParams:
    meadow: str
    clue: str
    fault: str
    fix: str
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
    changes: dict[str, float] = field(default_factory=dict)


@dataclass
class SplashMysteryWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, Any] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        if entity.role:
            self.entities[entity.role] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(
        self,
        event_id: str,
        text: str,
        actor: str,
        target: str | None = None,
        **changes: float,
    ) -> None:
        self.history.append(Event(event_id, text, actor, target, dict(changes)))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)


MEADOWS: dict[str, MeadowPad] = {
    "clover_circle": MeadowPad(
        id="clover_circle",
        name="Clover Circle",
        opening=(
            "At Clover Circle, the splash pad floor curled into a painted meadow of green clover leaves, "
            "and quick silver sprays skipped over the warm stones like tiny rabbits."
        ),
        secret=(
            "At the far edge stood a crystal door with a water wheel glowing behind it, and the biggest fan of water "
            "would only start after that clear door opened."
        ),
        ending_image="the clover sprays stitched bright rings around their ankles while the crystal door flashed like clean morning glass",
        sites=("drain", "sensor"),
    ),
    "buttercup_bank": MeadowPad(
        id="buttercup_bank",
        name="Buttercup Bank",
        opening=(
            "At Buttercup Bank, yellow petal tiles spread across the splash pad like a tiny meadow in bloom, "
            "and every jumping jet smelled faintly of cool stone after sun."
        ),
        secret=(
            "A crystal door stood beside the tallest spray arch, guarding the hush-blue chamber where the last water wheel waited."
        ),
        ending_image="the buttercup arcs climbed high in smooth gold loops while the crystal door shone blue and wide",
        sites=("sensor", "plate"),
    ),
    "reed_ribbon": MeadowPad(
        id="reed_ribbon",
        name="Reed Ribbon",
        opening=(
            "At Reed Ribbon, tall painted reeds bent around the splash pad wall, and thin water lines hissed over meadow-colored tiles "
            "like a secret marsh learning to sing."
        ),
        secret=(
            "Near the reeds, a crystal door held a hidden splash tunnel, and everyone knew the tunnel only woke when the door caught the right push from the water."
        ),
        ending_image="the reed jets whispered in tall silver threads while the crystal door opened with a bright wet shimmer",
        sites=("drain", "plate"),
    ),
}


CLUES: dict[str, Clue] = {
    "leaf_whirl": Clue(
        id="leaf_whirl",
        place="drain",
        line="A little whirl of meadow leaves kept spinning over one round drain instead of washing away.",
        hint="The leaves circled in the same tiny ring every time the cycle tried to start, as if the water were pointing down.",
        eerie_guess='Mina whispered, "Maybe the crystal door likes to stay closed when clouds pass over it."',
    ),
    "dim_glint": Clue(
        id="dim_glint",
        place="sensor",
        line="A cloudy glint kept fogging one clear sensor bead beside the crystal door frame.",
        hint="Each time the sprays pulsed, the same dull blur crossed the bead and then clung there.",
        eerie_guess='Jules said the bead looked like "an eye that forgot how to wake up."',
    ),
    "tapping_tile": Clue(
        id="tapping_tile",
        place="plate",
        line="One stepping tile near the crystal door gave a trapped tapping sound whenever water ran under it.",
        hint="The tap came from the same corner again and again, sharp enough to sound more stuck than spooky.",
        eerie_guess='For one breath, both children thought a secret knocker might be rapping under the floor.',
    ),
}


FAULTS: dict[str, Fault] = {
    "petal_clog": Fault(
        id="petal_clog",
        place="drain",
        kind="clog",
        hidden_motion="A wad of soft foam petals had sealed the drain mouth, so the water path could not pull hard enough to nudge the crystal door open.",
        evidence="When they crouched low, they could see the petals pasted flat over the little slots while the water tugged around the edges.",
        release="The moment the drain could breathe again, the pipes gave one eager rush and the crystal door clicked free.",
    ),
    "sunscreen_film": Fault(
        id="sunscreen_film",
        place="sensor",
        kind="film",
        hidden_motion="A streak of sunscreen shimmer had coated the sensor bead, so the crystal door kept waiting for a clear signal that never came.",
        evidence="Up close, the bead wore a greasy rainbow smear, and the dull glint vanished only where a clean drop ran through it.",
        release="As soon as the bead turned clear, a blue light winked on and the crystal door slid open.",
    ),
    "marble_wedge": Fault(
        id="marble_wedge",
        place="plate",
        kind="wedge",
        hidden_motion="A tiny glass marble had rolled under the stepping plate, so the plate could not sink and send the crystal door its opening push.",
        evidence="The trapped tapping came from a marble knocking under the corner each time the water nudged the plate.",
        release="Once the plate could press all the way down, the hidden latch answered and the crystal door sprang wide.",
    ),
}


FIXES: dict[str, Fix] = {
    "skimmer_lift": Fix(
        id="skimmer_lift",
        solves="clog",
        tool="the long skimmer net",
        action="Mina slid the long skimmer net under the soggy petals while Jules held the drain ring steady, and the whole foamy bundle lifted away in one slow peel.",
        proof="The nearby sprays stood taller at once, which showed the water had found its full path again.",
    ),
    "cloth_rinse": Fix(
        id="cloth_rinse",
        solves="film",
        tool="a rinse cup and a soft cloth",
        action="Jules poured fresh water from a rinse cup while Mina wiped the sensor bead with a soft cloth wrapped over her fingers.",
        proof="The greasy rainbow smear thinned, then vanished, and the little bead flashed clear instead of dull.",
    ),
    "hook_slide": Fix(
        id="hook_slide",
        solves="wedge",
        tool="the rubber hook tool",
        action="Mina eased the rubber hook tool under the plate seam and teased the marble out while Jules listened for the trapped tapping to stop.",
        proof="With the marble gone, the plate dipped in one smooth push instead of catching on something hard.",
    ),
}


PLACE_LABELS = {
    "drain": "the round drain by the spray stones",
    "sensor": "the clear sensor bead beside the crystal door",
    "plate": "the stepping plate in front of the crystal door",
}


KIND_LABELS = {
    "clog": "a drain clog",
    "film": "a cloudy film on the sensor",
    "wedge": "a small wedge under the stepping plate",
}


def sentence(text: str) -> str:
    return text if text.endswith((".", "!", "?")) else f"{text}."


def explain_rejection(meadow_id: str, clue_id: str, fault_id: str, fix_id: str) -> str:
    if meadow_id not in MEADOWS:
        return f"unknown meadow: {meadow_id}"
    if clue_id not in CLUES:
        return f"unknown clue: {clue_id}"
    if fault_id not in FAULTS:
        return f"unknown fault: {fault_id}"
    if fix_id not in FIXES:
        return f"unknown fix: {fix_id}"
    meadow = MEADOWS[meadow_id]
    clue = CLUES[clue_id]
    fault = FAULTS[fault_id]
    fix = FIXES[fix_id]
    reasons: list[str] = []
    if fault.place not in meadow.sites:
        reasons.append(f"{meadow.name} does not route its crystal door trouble through {PLACE_LABELS[fault.place]}")
    if clue.place != fault.place:
        reasons.append("the clue has to point to the same part of the splash pad where the real problem lives")
    if fix.solves != fault.kind:
        reasons.append("the chosen fix must match the physical thing keeping the crystal door shut")
    if not reasons:
        return "valid"
    return "; ".join(reasons)


def valid_params(params: StoryParams) -> tuple[bool, str]:
    reason = explain_rejection(params.meadow, params.clue, params.fault, params.fix)
    return reason == "valid", reason


def all_params() -> list[StoryParams]:
    combos: list[StoryParams] = []
    for meadow in sorted(MEADOWS):
        for clue in sorted(CLUES):
            for fault in sorted(FAULTS):
                for fix in sorted(FIXES):
                    params = StoryParams(meadow=meadow, clue=clue, fault=fault, fix=fix)
                    if valid_params(params)[0]:
                        combos.append(params)
    return combos


def make_world(params: StoryParams) -> SplashMysteryWorld:
    meadow = MEADOWS[params.meadow]
    clue = CLUES[params.clue]
    fault = FAULTS[params.fault]
    fix = FIXES[params.fix]
    world = SplashMysteryWorld(params)

    world.add(Entity("mina", "character", "girl", "Mina", role="hero", traits=["careful", "curious"]))
    world.add(Entity("jules", "character", "boy", "Jules", role="friend", traits=["steady", "thoughtful"]))
    world.add(Entity("rhea", "character", "woman", "Attendant Rhea", role="helper", traits=["calm", "practical"]))
    world.add(Entity("pair", "group", "children", "the two children", role="team"))
    world.add(Entity("pad", "place", "splash_pad", meadow.name, role="pad"))
    world.add(Entity("door", "object", "door", "the crystal door", role="door"))
    world.add(Entity("drain", "mechanism", "drain", PLACE_LABELS["drain"]))
    world.add(Entity("sensor", "mechanism", "sensor", PLACE_LABELS["sensor"]))
    world.add(Entity("plate", "mechanism", "plate", PLACE_LABELS["plate"]))
    world.add(Entity("wheel", "object", "water_wheel", "the hidden water wheel"))

    world.get("pad").meters["water_flow"] = 3.0
    world.get("door").meters["open"] = 0.0
    world.get("door").meters["stuckness"] = 2.0
    world.get("pair").memes["trust"] = 2.0
    world.get("pair").memes["worry"] = 0.0
    world.get("pair").memes["teamwork"] = 1.0
    world.get("mina").memes["curiosity"] = 1.0
    world.get("jules").memes["patience"] = 1.0
    world.get("rhea").memes["steadiness"] = 2.0
    world.get(fault.place).meters["problem_here"] = 1.0

    world.facts.update(
        meadow_name=meadow.name,
        clue_place=clue.place,
        clue_line=clue.line,
        fault_place=fault.place,
        fault_kind=fault.kind,
        fault_label=KIND_LABELS[fault.kind],
        place_label=PLACE_LABELS[fault.place],
        fix_tool=fix.tool,
        style="mystery",
        feature="problem solving",
        setting="splash pad",
    )
    return world


def opening(world: SplashMysteryWorld) -> None:
    meadow = MEADOWS[world.params.meadow]
    world.get("pair").memes["joy"] += 1.0
    world.record("opening", f"{meadow.opening} {meadow.secret}", "pad", "door")
    world.record(
        "goal",
        "Mina and Jules wanted to wake the hidden water wheel before the end-of-play whistle, so they skipped through the cool sprays and hurried toward the crystal door together.",
        "team",
        "wheel",
    )


def problem_arrives(world: SplashMysteryWorld) -> None:
    world.get("pair").memes["worry"] += 1.0
    world.get("door").meters["stuckness"] += 1.0
    world.get("pad").meters["water_flow"] -= 1.0
    world.record(
        "problem",
        "But when Mina tapped the last stepping spot, the crystal door did not move. The nearest jets shivered, the hidden wheel stayed dark, and the splash pad suddenly felt full of a tiny careful mystery.",
        "door",
        "wheel",
    )


def notice_clue(world: SplashMysteryWorld) -> None:
    clue = CLUES[world.params.clue]
    world.get("mina").memes["curiosity"] += 1.0
    world.record(
        "clue",
        f"{clue.line} {sentence(clue.hint)}",
        "hero",
        clue.place,
    )


def reject_magic_guess(world: SplashMysteryWorld) -> None:
    clue = CLUES[world.params.clue]
    world.get("pair").memes["worry"] += 0.4
    world.record(
        "guess",
        f"{clue.eerie_guess} Then Attendant Rhea knelt beside them and said, \"A good mystery repeats a clue. If the same spot keeps whispering, we should listen to the machinery there.\"",
        "helper",
        "team",
    )


def form_theory(world: SplashMysteryWorld) -> None:
    fault = FAULTS[world.params.fault]
    if fault.kind == "clog":
        theory = "If the drain path was smothered, the water could not pull strongly enough to wake the crystal door."
    elif fault.kind == "film":
        theory = "If the sensor bead could not see clearly, the crystal door would wait forever for a clean signal."
    else:
        theory = "If the stepping plate could not sink all the way, the crystal door would never receive its opening push."
    world.facts["theory"] = theory
    world.get("pair").memes["trust"] += 0.5
    world.get("pair").memes["teamwork"] += 0.4
    world.record(
        "theory",
        f"Mina listened to the repeating clue, Jules matched it to the quiet wobble in the water, and together they made a careful guess: {theory}",
        "team",
        fault.place,
    )


def inspect_mechanism(world: SplashMysteryWorld) -> None:
    fault = FAULTS[world.params.fault]
    world.get("mina").memes["curiosity"] += 0.7
    world.get("jules").memes["patience"] += 0.6
    world.get("pair").memes["teamwork"] += 0.8
    world.record(
        "inspect",
        f"So the children crouched by {PLACE_LABELS[fault.place]} instead of staring at the crystal door and hoping. {fault.hidden_motion} Soon they saw the proof: {sentence(fault.evidence)}",
        "team",
        fault.place,
    )


def solve_problem(world: SplashMysteryWorld) -> None:
    fault = FAULTS[world.params.fault]
    fix = FIXES[world.params.fix]
    world.get("pad").meters["water_flow"] += 2.0
    world.get("door").meters["stuckness"] = 0.0
    world.get("door").meters["open"] = 1.0
    world.get("pair").memes["relief"] += 1.0
    world.get("pair").memes["trust"] += 0.7
    world.facts["solved"] = True
    world.record(
        "solve",
        f"{fix.action} {fix.proof} {fault.release}",
        "team",
        "door",
    )


def ending(world: SplashMysteryWorld) -> None:
    meadow = MEADOWS[world.params.meadow]
    world.get("pair").memes["joy"] += 1.1
    world.record(
        "ending",
        f"The crystal door slid aside at last, and the hidden water wheel spun bright behind it. Mina and Jules splashed through the opening, laughing when the tallest spray burst over their shoulders, and by whistle time {meadow.ending_image}.",
        "door",
        "wheel",
    )


def tell(params: StoryParams) -> SplashMysteryWorld:
    world = make_world(params)
    opening(world)
    world.para()
    problem_arrives(world)
    notice_clue(world)
    reject_magic_guess(world)
    form_theory(world)
    world.para()
    inspect_mechanism(world)
    solve_problem(world)
    world.para()
    ending(world)
    return world


def generation_prompts(world: SplashMysteryWorld) -> list[str]:
    return [
        'Write a child-facing mystery set in a splash pad that clearly includes the words "meadow" and "crystal door."',
        f"Build the middle around a repeating physical clue at {world.facts['place_label']} and let problem solving reveal the exact mechanism.",
        "End with a vivid image that proves the repair worked and the children can play again.",
    ]


def story_grounded_qa(world: SplashMysteryWorld) -> list[QAItem]:
    clue = CLUES[world.params.clue]
    fault = FAULTS[world.params.fault]
    fix = FIXES[world.params.fix]
    return [
        QAItem(
            question="Why did the crystal door stay shut at the splash pad?",
            answer=(
                f"The crystal door stayed shut because of {KIND_LABELS[fault.kind]}. "
                f"{fault.hidden_motion} That stopped the door from getting the clear signal or water push it needed."
            ),
        ),
        QAItem(
            question="What clue helped Mina and Jules stop guessing about magic?",
            answer=(
                f"The clue was that {clue.line.lower()} "
                f"Because the same sign kept appearing at {PLACE_LABELS[clue.place]}, they understood that one real mechanism needed attention."
            ),
        ),
        QAItem(
            question="How did the children solve the mystery?",
            answer=(
                f"They tested their theory by using {fix.tool} instead of poking around at random. "
                f"{fix.action} After that, {fault.release.lower()}"
            ),
        ),
    ]


def world_grounded_qa(world: SplashMysteryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What kind of place is this storyworld?",
            answer=(
                f"It is a meadow-themed splash pad mystery world called {world.facts['meadow_name']}. "
                "Water paths, sensors, and stepping parts matter here, so small physical changes can shape the whole story."
            ),
        ),
        QAItem(
            question="What usually opens the crystal door in this world?",
            answer=(
                "The crystal door opens when the splash-pad mechanism can send its full signal or water push through the correct path. "
                "If one part is blocked, smeared, or wedged, the door stays shut until someone solves the real problem."
            ),
        ),
        QAItem(
            question="Why is careful teamwork useful in this splash pad setting?",
            answer=(
                "Careful teamwork helps because the clues are small and repeat in one exact place. "
                "One child can notice the pattern while the other steadies a tool or checks whether the mechanism changes."
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
        world_qa=world_grounded_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(M,C,F,X) :-
    meadow(M),
    clue(C),
    fault(F),
    fix(X),
    clue_place(C,P),
    fault_place(F,P),
    fault_place(F,Site),
    meadow_site(M,Site),
    fault_kind(F,K),
    fix_solves(X,K).

#show valid/4.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from asp import fact

    lines: list[str] = []
    for meadow in MEADOWS.values():
        lines.append(fact("meadow", meadow.id))
        for site in meadow.sites:
            lines.append(fact("meadow_site", meadow.id, site))
    for clue in CLUES.values():
        lines.append(fact("clue", clue.id))
        lines.append(fact("clue_place", clue.id, clue.place))
    for fault in FAULTS.values():
        lines.append(fact("fault", fault.id))
        lines.append(fact("fault_place", fault.id, fault.place))
        lines.append(fact("fault_kind", fault.id, fault.kind))
    for fix in FIXES.values():
        lines.append(fact("fix", fix.id))
        lines.append(fact("fix_solves", fix.id, fix.solves))
    if params is not None:
        lines.append(fact("chosen_meadow", params.meadow))
        lines.append(fact("chosen_clue", params.clue))
        lines.append(fact("chosen_fault", params.fault))
        lines.append(fact("chosen_fix", params.fix))
    return "\n".join(lines) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def verify_asp_parity() -> str:
    import asp

    model = asp.one_model(asp_program())
    asp_valid = {tuple(parts) for parts in asp.atoms(model, "valid")}
    py_valid = {(p.meadow, p.clue, p.fault, p.fix) for p in all_params()}
    if asp_valid != py_valid:
        missing = sorted(py_valid - asp_valid)
        extra = sorted(asp_valid - py_valid)
        raise StoryError(f"ASP mismatch; missing={missing[:5]} extra={extra[:5]}")
    return f"ASP parity OK across {len(py_valid)} valid parameter combinations."


def verify_worlds() -> str:
    samples = [generate(params) for params in all_params()]
    if not samples:
        raise StoryError("no valid stories were generated")
    for sample in samples:
        story = sample.story
        if "meadow" not in story.lower():
            raise StoryError(f"story for {sample.params} does not mention meadow")
        if "crystal door" not in story.lower():
            raise StoryError(f"story for {sample.params} does not mention crystal door")
        if len(sample.world.history) < 7:
            raise StoryError(f"story for {sample.params} is missing world events")
        if sample.world.facts.get("solved") is not True:
            raise StoryError(f"story for {sample.params} did not resolve its physical problem")
        if sample.world.get("door").meters["open"] < 1.0:
            raise StoryError(f"story for {sample.params} never opened the crystal door")
        if "\n\n" not in story:
            raise StoryError(f"story for {sample.params} does not separate beginning, turn, and ending")
        for qa in [*sample.story_qa, *sample.world_qa]:
            if not qa.answer or "." not in qa.answer:
                raise StoryError(f"QA answer is too thin for {sample.params}: {qa.question}")
    return f"Generated and checked {len(samples)} complete splash-pad mysteries."


def verify() -> str:
    parity = verify_asp_parity()
    worlds = verify_worlds()
    return f"{parity} {worlds}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--meadow", choices=sorted(MEADOWS))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--fault", choices=sorted(FAULTS))
    parser.add_argument("--fix", choices=sorted(FIXES))
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
    explicit = any(getattr(args, name) is not None for name in ("meadow", "clue", "fault", "fix"))
    if explicit:
        params = StoryParams(
            meadow=args.meadow or rng.choice(list(MEADOWS)),
            clue=args.clue or rng.choice(list(CLUES)),
            fault=args.fault or rng.choice(list(FAULTS)),
            fix=args.fix or rng.choice(list(FIXES)),
            seed=args.seed,
        )
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params
    chosen = rng.choice(all_params())
    return StoryParams(chosen.meadow, chosen.clue, chosen.fault, chosen.fix, args.seed)


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in all_params():
            yield generate(params)
        return
    rng = random.Random(args.seed)
    for _ in range(max(1, args.n)):
        yield generate(resolve_params(args, rng))


def emit(sample: StorySample, args: argparse.Namespace) -> None:
    if args.json:
        print(sample.to_json())
        return
    print(sample.story)
    if args.trace:
        print("\nTrace:")
        for event in sample.world.history:
            print(f"- {event.id}: {event.text}")
    if args.qa:
        print("\nPrompts:")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print("\nStory QA:")
        for qa in sample.story_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")
        print("\nWorld QA:")
        for qa in sample.world_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")


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
            import asp

            print(asp.solve(asp_program()))
            return 0
        for index, sample in enumerate(iter_samples(args)):
            if index:
                print("\n---\n")
            emit(sample, args)
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
