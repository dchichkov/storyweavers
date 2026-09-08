#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None

    def __post_init__(self):
        for k in ["lost", "moved", "fixed", "scratched", "wobbly", "wet", "locked"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "trust", "curiosity", "relief", "fear", "care", "doubt", "friendship"]:
            self.memes.setdefault(k, 0.0)


@dataclass
class StoryParams:
    name: str = "Mira"
    friend: str = "Sol"
    helper: str = "Bean"
    setting: str = "the clock room"
    seed: Optional[int] = None
    variant: int = 0


@dataclass(frozen=True)
class Case:
    place: str
    goal: str
    mechanism: str
    clue: str
    false_lead: str
    caution: str
    twist: str
    reveal: str
    fix: str
    ending: str
    lesson: str


CASES = [
    Case(
        place="the attic workshop",
        goal="wind the sleepy lantern",
        mechanism="a brass crank with two side gears",
        clue="a tiny brass shaving by the left gear and a thread of blue ribbon caught on a nail",
        false_lead="the open window looked like the obvious thief",
        caution="don't force the crank when the gears are lined up wrong",
        twist="the missing key was not stolen at all; it was tucked inside the lantern base",
        reveal="the base had popped open when the crank jammed, and the key slid under a wool mat",
        fix="they set the gears straight, fished out the key, and wound the lantern together",
        ending="The lantern gave one warm blink and stayed steady beside their joined hands.",
        lesson="A careful look at a mechanism can explain a mystery faster than a quick guess.",
    ),
    Case(
        place="the library nook",
        goal="open the secret drawer in the reading table",
        mechanism="a wooden latch with a hidden sliding tooth",
        clue="a dust line shaped like a tiny smile near the latch and a fresh fingerprint on the table edge",
        false_lead="a stack of books seemed to cover the missing note",
        caution="pull gently, because the tooth catches if the drawer is rushed",
        twist="the note was inside the drawer all along, folded behind a bookmark",
        reveal="the latch only released after they slid the tooth left, and the note fell softly into view",
        fix="they cleaned the dust, tested the latch once, and shared the note with a grin",
        ending="The drawer closed with a neat click, as if it were proud of being understood.",
        lesson="Friendship helps when two people compare clues instead of arguing over one guess.",
    ),
    Case(
        place="the garden shed",
        goal="start the rain pump",
        mechanism="a hand pump with a squeaking seal and a cork float",
        clue="a wet footprint, a kinked hose, and a cork bobbing in a puddle",
        false_lead="the puddle made it seem as if rain had ruined everything",
        caution="never yank a pump when the hose is kinked, or the seal can tear",
        twist="the pump was fine; the cork float was blocking the valve from below",
        reveal="when they lifted the float, water rushed through and the sprayer woke up",
        fix="they untwisted the hose, reset the seal, and watered the beans together",
        ending="The bean leaves lifted in the spray like tiny green hands waving back.",
        lesson="A problem can look broken when it is only blocked.",
    ),
    Case(
        place="the toy repair bench",
        goal="repair the music box",
        mechanism="a little metal comb and a spinning drum",
        clue="one bent tooth on the comb and a ribbon scrap wound around the drum key",
        false_lead="the lid's painted flowers made the box seem decorative, not damaged",
        caution="turn the key slowly, because a fast spin can bend the comb worse",
        twist="the melody had not vanished; it was trapped in the ribbon scrap, which hummed when pulled free",
        reveal="the drum turned cleanly once the ribbon was removed and the bent tooth was eased straight",
        fix="they tuned the comb, wound the key with care, and listened to the song return",
        ending="The music box played one shy tune, and both friends smiled as if they had found a lost bird.",
        lesson="Small tools need gentle hands, especially when trust is part of the repair.",
    ),
    Case(
        place="the boat house",
        goal="unlock the rowboat chain",
        mechanism="a rusted chain lock with a spring catch",
        clue="rust flakes on the dock and a droplet trail leading to the oar rack",
        false_lead="the empty water bucket looked like the reason the boat could not move",
        caution="a spring catch can snap shut on a finger if it is pried too hard",
        twist="the key was not lost; it was tied to the oar rack with fishing line by mistake",
        reveal="the line had tangled in the hook, and the key swung free when they lifted the oars",
        fix="they freed the key, opened the lock slowly, and checked the catch before rowing",
        ending="The rowboat rocked loose at last, ready to float on the calm gray water.",
        lesson="A twist in a mystery often hides in plain sight, especially near the thing that is already there.",
    ),
    Case(
        place="the bakery storeroom",
        goal="turn the flour mill wheel",
        mechanism="a stone wheel with a tight wooden clamp",
        clue="a crescent of flour on the clamp and a crumb trail under the shelf",
        false_lead="the warm oven suggested that the heat had made the wheel stick",
        caution="don't pound the clamp; stone wheels can crack",
        twist="the wheel was blocked by a spoon that had fallen into the groove",
        reveal="once the spoon was lifted, the wheel spun and flour dust floated like fog",
        fix="they brushed the stones clean, re-set the clamp, and milled a fresh bag together",
        ending="The storeroom smelled sweet and plain, full of flour and the sound of relief.",
        lesson="When friends share a job, they can spot what one pair of eyes missed.",
    ),
    Case(
        place="the museum hall",
        goal="wake the speaking statue",
        mechanism="a hidden voice tube and a foot pedal",
        clue="a hollow echo near the pedestal and a torn ticket stub under the curtain",
        false_lead="the statue's stern face made it seem impossible that it could speak at all",
        caution="step lightly, because the pedal sticks if it is pressed too hard",
        twist="the statue had spoken earlier; the voice tube was only whispering from the next room",
        reveal="the real speaker was a guide behind the curtain, and the pedal simply opened a vent",
        fix="they straightened the tube, tested the pedal softly, and listened to the proper echo",
        ending="The statue's voice returned like a polite ghost, and the hall became bright with answers.",
        lesson="Mysteries are kinder when the truth is checked before anyone is blamed.",
    ),
    Case(
        place="the clock shop",
        goal="set the town chime",
        mechanism="a spring-driven hammer wheel",
        clue="one loose screw and a tiny smear of grease on the counter",
        false_lead="the bell itself sounded guilty because it was so loud",
        caution="a spring wheel can snap backward if it is wound carelessly",
        twist="the chime was off because a kitten had curled up inside the bell rope basket",
        reveal="the basket had bumped the wheel, and the kitten's tail had been the last clue",
        fix="they lifted the kitten, tightened the screw, and reset the hammer wheel together",
        ending="At noon, the chime rang clear while the kitten purred in a sunlit lap.",
        lesson="A gentle mystery sometimes ends with a gentle rescue.",
    ),
    Case(
        place="the greenhouse",
        goal="open the seed cabinet",
        mechanism="a glass dial lock with three painted rings",
        clue="mud on the dial rim and a smudge shaped like a thumbprint",
        false_lead="the wet plants made everyone think the cabinet had been soaked shut",
        caution="rotate the rings one at a time, or the glass dial can jam",
        twist="the lock was set correctly; the key had been taped to the back of the seed tray",
        reveal="the tray slid out, the key came with it, and the cabinet opened without a fuss",
        fix="they labeled the tray, cleaned the mud, and planted the seeds before sunset",
        ending="The cabinet door swung open, and the little seeds waited like a quiet promise.",
        lesson="Sometimes the answer is not hidden; it is merely attached to something overlooked.",
    ),
    Case(
        place="the harbor kiosk",
        goal="raise the signal flag",
        mechanism="a rope pulley with a jammed cleat",
        clue="salt grains in the pulley groove and a frayed loop on the rope",
        false_lead="the sea mist made the whole kiosk seem mysterious enough to blame",
        caution="keep fingers clear of the cleat, because the rope can snap tight",
        twist="the flag had already been raised by the lighthouse keeper, but the kiosk mirror had been covering it",
        reveal="when they shifted the mirror, the bright flag appeared and the pulley loosened",
        fix="they cleaned the groove, tied a new loop, and raised the flag again for practice",
        ending="The red flag fluttered above the kiosk like a brave little square of fire.",
        lesson="Friendship means helping another person see what is already true.",
    ),
]

THEME = "mechanism"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with a mechanism, friendship, caution, and a twist.")
    ap.add_argument("--name", default=None)
    ap.add_argument("--friend", default=None)
    ap.add_argument("--helper", default=None)
    ap.add_argument("--setting", default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random, sample_seed: int, base_seed: int) -> StoryParams:
    name = args.name or rng.choice(["Mira", "June", "Nia", "Iris", "Lena"])
    friend = args.friend or rng.choice(["Sol", "Ari", "Pip", "Eli", "Tess"])
    helper = args.helper or rng.choice(["Bean", "Moss", "Dot", "Rue", "Wren"])
    if len({name, friend, helper}) < 3:
        raise StoryError("The three characters must be different.")
    setting = args.setting or CASES[(sample_seed - base_seed) % len(CASES)].place
    return StoryParams(name=name, friend=friend, helper=helper, setting=setting, seed=sample_seed, variant=(sample_seed - base_seed) % len(CASES))


@dataclass
class World:
    hero: Entity
    friend: Entity
    helper: Entity
    mechanism: Entity
    clue: Entity
    story_bits: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.story_bits.append(text)

    def render(self) -> str:
        paras = []
        buf = []
        for bit in self.story_bits:
            if bit == "":
                if buf:
                    paras.append(" ".join(buf))
                    buf = []
            else:
                buf.append(bit)
        if buf:
            paras.append(" ".join(buf))
        return "\n\n".join(paras)


def build_world(params: StoryParams) -> World:
    hero = Entity(params.name, "character", "child", params.name)
    friend = Entity(params.friend, "character", "child", params.friend)
    helper = Entity(params.helper, "character", "animal", params.helper)
    mechanism = Entity("mechanism", "object", "device", "mechanism")
    clue = Entity("clue", "object", "clue", "clue")
    return World(hero=hero, friend=friend, helper=helper, mechanism=mechanism, clue=clue)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    case = CASES[params.variant % len(CASES)]
    h, f, x = world.hero, world.friend, world.helper
    h.memes["worry"] += 1
    f.memes["trust"] += 1
    x.memes["curiosity"] += 1

    world.say(f"In {case.place}, {h.id}, {f.id}, and {x.id} were trying to {case.goal}.")
    world.say(f"The important {THEME} was {case.mechanism}, but then the task stalled because something went wrong.")
    world.say(f"{case.false_lead.capitalize()}, and for a moment the room felt like it was hiding the answer on purpose.")
    world.say(f"{h.id} whispered, 'Let's not rush.' {f.id} answered, 'Right. We look, test, and talk it through.'")
    world.say(f"{case.clue.capitalize()}.")
    world.say(f"{h.id}'s inner thought stayed careful: '{case.caution.capitalize()}.'")

    world.say("")
    world.say(f"{f.id} said, 'I think the clue points near the {THEME}.'")
    world.say(f"{x.id} chittered, 'Then I will check the small spaces.'")
    world.say(f"{h.id} nodded. 'And I will try the simplest fix first.'")

    world.say("")
    world.say(f"That was the twist: {case.twist}.")
    world.say(f"When they checked again, {case.reveal}.")
    world.say(f"{h.id} said, 'So the mystery was not a thief after all.' {f.id} replied, 'No, just a hidden answer waiting for friends to find it.'")

    world.say("")
    world.say(f"Together they {case.fix}.")
    world.say(f"They remembered the caution: {case.caution.lower()}.")
    world.say(f"In the end, {case.ending}")
    world.say(f"The lesson was clear: {case.lesson}")

    world.facts.update(
        place=case.place,
        goal=case.goal,
        mechanism=case.mechanism,
        clue=case.clue,
        false_lead=case.false_lead,
        caution=case.caution,
        twist=case.twist,
        reveal=case.reveal,
        fix=case.fix,
        ending=case.ending,
        lesson=case.lesson,
        hero=h.id,
        friend=f.id,
        helper=x.id,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a small mystery set in {world.facts['place']} where the key clue is a {THEME}: {world.facts['mechanism']}.",
        f"Make the story child-friendly, include a brief dialogue, and let friendship change the plan after the twist.",
        "Keep the tone cautious and puzzling, then end with a concrete image that proves the problem was solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What problem started the mystery?",
            answer=f"The team could not finish their task in {world.facts['place']} because the {THEME} stopped behaving as expected.",
        ),
        QAItem(
            question="What clue helped them?",
            answer=f"They noticed {world.facts['clue']}, which pointed them back toward the mechanism instead of the false lead.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {world.facts['twist']}. That changed what the friends thought had happened.",
        ),
        QAItem(
            question="How was the mystery fixed?",
            answer=f"They {world.facts['fix']}. After that, the work could continue safely.",
        ),
        QAItem(
            question="What did the story teach?",
            answer=f"It taught that {world.facts['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move, lock, click, or do a job.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring bond where people help, trust, and listen to each other.",
        ),
        QAItem(
            question="What is caution?",
            answer="Caution means being careful and thinking about danger before acting.",
        ),
        QAItem(
            question="What is a twist in a mystery?",
            answer="A twist is a surprising turn that changes what you thought was true.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in [world.hero, world.friend, world.helper, world.mechanism, world.clue]:
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(mechanism_friendship_cautionary_twist_mystery).
requires(mechanism_friendship_cautionary_twist_mystery, mechanism).
requires(mechanism_friendship_cautionary_twist_mystery, friendship).
requires(mechanism_friendship_cautionary_twist_mystery, cautionary).
requires(mechanism_friendship_cautionary_twist_mystery, twist).
requires(mechanism_friendship_cautionary_twist_mystery, mystery).

ok(S) :- valid_story(S), requires(S, mechanism), requires(S, friendship), requires(S, cautionary), requires(S, twist), requires(S, mystery).
#show ok/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    return "\n".join(
        [
            asp.fact("valid_story", "mechanism_friendship_cautionary_twist_mystery"),
            asp.fact("requires", "mechanism_friendship_cautionary_twist_mystery", "mechanism"),
            asp.fact("requires", "mechanism_friendship_cautionary_twist_mystery", "friendship"),
            asp.fact("requires", "mechanism_friendship_cautionary_twist_mystery", "cautionary"),
            asp.fact("requires", "mechanism_friendship_cautionary_twist_mystery", "twist"),
            asp.fact("requires", "mechanism_friendship_cautionary_twist_mystery", "mystery"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy import
    models = asp.one_model(asp_program("#show ok/1."))
    if any(atom.name == "ok" for atom in models):
        print("OK: ASP/Python parity holds.")
        return 0
    print("MISMATCH: ASP validation failed.")
    return 1


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
    StoryParams(name="Mira", friend="Sol", helper="Bean"),
    StoryParams(name="Iris", friend="Ari", helper="Dot"),
    StoryParams(name="Lena", friend="Pip", helper="Wren"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp  # lazy import
        print(asp.one_model(asp_program("#show ok/1.")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(100, args.n * 50):
            sample_seed = base_seed + i
            params = resolve_params(args, random.Random(sample_seed), sample_seed, base_seed)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx + 1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
