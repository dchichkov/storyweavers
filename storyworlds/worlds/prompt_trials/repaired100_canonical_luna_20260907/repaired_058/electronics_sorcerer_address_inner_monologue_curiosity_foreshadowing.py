#!/usr/bin/env python3
"""
A child-facing whodunit about electronics, a sorcerer, and a missing address.
Curiosity, an inner monologue, and foreshadowing guide the repair.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Theo"
    sorcerer: str = "Sorcerer Orin"
    place: str = "the lantern workshop"
    device: str = "a brass message machine"
    address: str = "the address of the moon tower"
    clue: str = "a blue wire loop"
    task: str = "deliver a message before moonrise"


@dataclass(frozen=True)
class Case:
    title: str
    mystery: str
    suspicion: str
    early_sign: str
    clue: str
    failed_step: str
    cause: str
    hero_action: str
    helper_action: str
    sorcerer_action: str
    repair: str
    lesson: str
    ending: str


CASES = [
    Case(
        "The Vanishing Tower Address",
        "the address card for the moon tower vanished from the message machine",
        "someone suspected the sorcerer had hidden it to keep the message secret",
        "the machine blinked three times whenever its brass lid was lifted",
        "a blue wire loop rested beneath the loose address tray",
        "they searched the ink cupboard and found only empty envelopes",
        "the address card had slipped into the machine when the wire tugged the tray",
        "followed the wire without pulling it",
        "held the tray level and checked the machine's tiny switch",
        "admitted that a new charm had made the wire twitch",
        "replaced the wire loop and slid the address back into its slot",
        "A curious question can reveal a mechanical mistake before blame grows.",
        "the moon tower address glowed on the repaired screen as the message began its journey",
    ),
    Case(
        "The Silent Copper Bell",
        "the electronic bell stopped ringing when the sorcerer tested the delivery circuit",
        "the helper thought the hero had forgotten to connect the power cell",
        "a faint warm smell came from the left side of the circuit box",
        "two clean screw marks showed that the battery cover had been turned around",
        "they pressed the bell button again and again, which only made the box warmer",
        "the cover blocked the contact even though the battery still had power",
        "turned off the cell before touching the wires",
        "read the diagram and found the reversed cover",
        "used a small cooling charm after checking that no wire was damaged",
        "fitted the cover correctly and tested the bell once",
        "Careful observation is safer than repeated guessing.",
        "one clear copper note rang beside the correctly written address",
    ),
    Case(
        "The Address in the Crystal",
        "a crystal display showed the wrong house number for the sorcerer's delivery",
        "everyone wondered whether the sorcerer had changed the address on purpose",
        "the last two digits shimmered whenever the workshop curtain moved",
        "a strand of curtain thread was caught around the display dial",
        "the moving curtain nudged the dial and changed the number",
        "watched the shimmer while keeping the curtain still",
        "read the old and new numbers aloud for comparison",
        "freed the thread with a gentle spell instead of forcing the dial",
        "covered the dial and rewrote the verified address",
        "secured the curtain and checked the display against the paper card",
        "A small moving object can create a large-looking mystery.",
        "the true house number shone steadily while the curtain stayed tied back",
    ),
    Case(
        "The Green Spark",
        "a green spark appeared beside the address printer",
        "the sorcerer feared a rival magician had tampered with his electronics",
        "the spark came only when a metal ruler touched the printer case",
        "a bright thread of wool lay between the ruler and the case",
        "static electricity jumped from the wool and was not magical sabotage",
        "removed the ruler and asked what materials had touched the case",
        "kept the printer unplugged while inspecting the wool",
        "explained how static could make a harmless snap",
        "grounded the case and moved the wool away from the printer",
        "tested the printer safely after the spark stopped",
        "Learning how a thing works can make a frightening clue less frightening.",
        "the printer produced a neat address label without another green spark",
    ),
    Case(
        "The Clockwork Courier",
        "the tiny electronic courier rolled toward the wrong street",
        "the hero believed the helper had entered a false address",
        "the courier paused beside a red button before turning",
        "a wax crumb covered the button's edge",
        "the crumb made the button stick and sent the courier into its old route",
        "watched the wheels and marked the exact moment the turn changed",
        "cleaned the button only after switching off the courier",
        "checked the route memory and found the old path still stored",
        "cleared the crumb and replaced the route with the verified address",
        "sent the courier again while all three watched its turns",
        "A mystery becomes smaller when each step is observed in order.",
        "the courier stopped at the moon tower gate with the correct address lit on its panel",
    ),
    Case(
        "The Whispering Receiver",
        "the receiver whispered a name that was not on the delivery list",
        "the helper thought the sorcerer had summoned a secret listener",
        "the whisper repeated whenever the workshop lamp was switched on",
        "a loose speaker wire touched the lamp's metal frame",
        "the receiver picked up a tiny buzz and shaped it into a voice-like sound",
        "compared the whisper with the lamp's switching rhythm",
        "held the receiver away from the frame while the power was off",
        "tightened the speaker wire and explained the interference",
        "separated the signal wire from the lamp wire",
        "recorded the real message and attached the correct address",
        "Sounds can suggest a story, but testing their source tells the truth.",
        "the receiver spoke clearly, and the message reached the named tower",
    ),
    Case(
        "The Inkless Label",
        "the label printer made a blank strip instead of printing the address",
        "the hero wondered if the sorcerer's invisible ink spell had failed",
        "the printer clicked twice before every blank strip",
        "a nearly empty ink cartridge rattled when shaken",
        "the cartridge had enough ink for marks but not enough for readable letters",
        "counted the clicks and compared the cartridge with a fresh one",
        "found the spare cartridge in the electronics drawer",
        "removed the invisible-ink charm and chose ordinary black ink",
        "replaced the cartridge and printed a test label",
        "checked the whole address before sticking the label to the parcel",
        "When a tool gives a weak result, check its supplies before inventing a grand cause.",
        "bold black letters named the moon tower on the finished parcel",
    ),
    Case(
        "The Reversed Signal",
        "the machine sent the message backward through the workshop",
        "the sorcerer thought an unseen spirit had turned the signal around",
        "the first light always appeared at the far end of the signal strip",
        "the red and white input plugs had been swapped",
        "the machine followed the reversed connection exactly as it was built",
        "traced the signal from the message button to the first light",
        "matched each plug with the colored marks on the diagram",
        "used a truth charm to confirm the circuit had no hidden break",
        "returned the plugs to their matching sockets",
        "sent a short test message before sending the full address",
        "A clear diagram can untangle a strange-looking path.",
        "the signal traveled forward, carrying the address to the moon tower",
    ),
]


OPENINGS = [
    "Before sunrise",
    "On the evening the stars first appeared",
    "At the edge of a quiet village",
    "While rain tapped the workshop roof",
    "On the morning of the lantern festival",
    "As the moon climbed above the chimneys",
]

QUESTIONS = [
    "What did we actually observe?",
    "Which part changed, and which part only seemed strange?",
    "Can we test the clue before we accuse anyone?",
    "Where did the signal begin, and where did it go?",
    "What small detail did we overlook?",
    "Let us follow the evidence one step at a time.",
]

FORESHADOWING = [
    "Earlier, Luna had noticed the same blue glow near the machine's loose tray.",
    "A faint click had sounded before anyone mentioned the missing address.",
    "The workshop curtain had fluttered beside the display twice that morning.",
    "The copper bell had warmed slightly during the first test.",
    "A tiny thread had been caught on the corner of the circuit box.",
    "The courier's wheels had paused for one breath before the trouble began.",
]

ENDING_IMAGES = [
    "The repaired machine shone softly while the correct address traveled into the night.",
    "The final signal crossed the room, and the waiting lantern turned gold.",
    "The moon tower answered with three bright flashes from its highest window.",
    "The parcel rolled through the open gate beneath a clear, steady address label.",
    "The workshop grew quiet except for the friendly hum of working electronics.",
    "The sorcerer's desk held the verified address, the cleaned clue, and a fresh plan.",
]


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    params: StoryParams
    hero: Entity
    helper: Entity
    sorcerer: Entity
    case: Case
    curious: bool = False
    solved: bool = False
    repaired: bool = False
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A whodunit about electronics, a sorcerer, and a missing address.")
    for name in ("hero", "helper", "sorcerer", "place", "device", "address", "clue", "task"):
        ap.add_argument(f"--{name}")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(["Luna", "Mira", "Nia", "Ivo"]),
        helper=args.helper or rng.choice(["Theo", "Pip", "Rin", "Bram"]),
        sorcerer=args.sorcerer or rng.choice(["Sorcerer Orin", "Sorcerer Vale", "Sorcerer Elio"]),
        place=args.place or rng.choice(["the lantern workshop", "the crystal post room", "the copper observatory"]),
        device=args.device or rng.choice(["a brass message machine", "a clockwork receiver", "an electronic courier"]),
        address=args.address or rng.choice(["the address of the moon tower", "the address of the comet library", "the address of the river wizard"]),
        clue=args.clue or rng.choice(["a blue wire loop", "a silver screw", "a red signal mark"]),
        task=args.task or "deliver a message before moonrise",
    )


def validate(params: StoryParams) -> None:
    if not params.hero or not params.helper or not params.sorcerer:
        raise StoryError("The electronics mystery needs a hero, a helper, and a sorcerer.")
    if not params.address.strip():
        raise StoryError("The mystery needs a readable address.")
    forbidden = {"poison", "weapon", "bomb", "dangerous"}
    if any(word in params.device.lower() for word in forbidden):
        raise StoryError("The electronics device must be suitable for a gentle child-facing story.")
    if params.hero.lower() == params.helper.lower():
        raise StoryError("The hero and helper must be different people so their dialogue can matter.")


def stable_rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xA91C37)
    text = "|".join(vars(params).values().__str__() for _ in [0])
    value = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")
    return random.Random(value)


def ground(case: Case, params: StoryParams) -> Case:
    values = vars(params)
    updates = {name: getattr(case, name).format(**values) for name in case.__dataclass_fields__}
    return Case(**updates)


def tell(params: StoryParams) -> World:
    validate(params)
    rng = stable_rng(params)
    case = ground(rng.choice(CASES), params)
    world = World(
        params=params,
        hero=Entity(params.hero, "hero"),
        helper=Entity(params.helper, "helper"),
        sorcerer=Entity(params.sorcerer, "sorcerer"),
        case=case,
    )
    world.say(
        f"{rng.choice(OPENINGS)}, {params.hero} worked with {params.helper} in {params.place}. "
        f"They were preparing {params.device} to {params.task}."
    )
    world.say(
        f"{params.sorcerer} had trusted them with {params.address}, because a message without a clear "
        f"address could wander like a moth around a lamp."
    )
    world.say(f"{rng.choice(FORESHADOWING)}")
    world.para()
    world.say(f"The case was called {case.title}. It began when {case.mystery}.")
    world.say(f"For one nervous moment, {case.suspicion}.")
    world.hero.add_meme("curiosity", 1)
    world.helper.add_meme("worry", 1)
    world.sorcerer.add_meme("patience", 1)
    world.say(f"Luna thought, 'A mystery is a locked box, but every lock leaves a mark. I should look before I guess.'")
    world.say(f"{params.hero} asked, '{rng.choice(QUESTIONS)}'")
    world.say(f"{params.helper} replied, 'I saw this: {case.clue}.'")
    world.curious = True
    world.say(f"They tried {case.failed_step}, but the trouble remained.")
    world.para()
    world.say(
        f"Then {params.hero} and {params.helper} followed the clue carefully. They discovered that {case.cause}."
    )
    world.say(
        f"{params.sorcerer} said, 'I feared a spell was responsible, but the evidence points to the electronics.'"
    )
    world.say(
        f"{params.hero} answered, 'Then we can repair the real cause.' {case.hero_action.capitalize()} "
        f"{params.helper} {case.helper_action}; and {params.sorcerer} {case.sorcerer_action}."
    )
    world.repaired = True
    world.solved = True
    world.para()
    world.say(f"Together they {case.repair}.")
    world.say(f"{params.sorcerer} said, '{case.lesson}'")
    world.say(f"{case.ending}. {rng.choice(ENDING_IMAGES)}")
    world.facts = {
        "case": case.title,
        "mystery": case.mystery,
        "clue": case.clue,
        "cause": case.cause,
        "repair": case.repair,
        "lesson": case.lesson,
        "address": params.address,
        "device": params.device,
        "curious": world.curious,
        "solved": world.solved,
        "repaired": world.repaired,
    }
    return world


ASP_RULES = r"""
hero(X) :- hero_name(X).
helper(X) :- helper_name(X).
sorcerer(X) :- sorcerer_name(X).
curious :- sees_clue, asks_question.
investigated :- curious, follows_evidence.
repaired :- investigated, fixes_device.
resolved :- repaired, verifies_address.
#show curious/0.
#show investigated/0.
#show repaired/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero_name", "luna"),
        asp.fact("helper_name", "theo"),
        asp.fact("sorcerer_name", "orin"),
        asp.fact("sees_clue"),
        asp.fact("asks_question"),
        asp.fact("follows_evidence"),
        asp.fact("fixes_device"),
        asp.fact("verifies_address"),
    ])


def asp_program(show: Optional[str] = None) -> str:
    if show is None:
        show = "#show curious/0.\n#show investigated/0.\n#show repaired/0.\n#show resolved/0."
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_available() -> bool:
    try:
        import clingo  # noqa: F401
        return True
    except Exception:
        return False


def asp_verify() -> int:
    if not asp_available():
        print("ASP verification unavailable: clingo is not installed.")
        return 1
    import asp
    model = {str(atom) for atom in asp.one_model(asp_program())}
    expected = {"curious", "investigated", "repaired", "resolved"}
    if not expected.issubset(model):
        print("MISMATCH: ASP twin did not reach the repaired address state.")
        return 1
    sample = generate(StoryParams(seed=17))
    if not sample.world or not sample.world.solved:
        print("MISMATCH: Python story did not solve the mystery.")
        return 1
    print("OK: Python and ASP both reach curiosity, investigation, repair, and resolution.")
    return 0


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a child-friendly whodunit about {p.hero} investigating electronics with {p.helper}.",
        f"Tell a mystery involving {p.sorcerer}, {p.address}, and a device that behaves strangely.",
        f"Use curiosity, inner monologue, and foreshadowing before the address is repaired.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    c = world.case
    return [
        QAItem(
            question=f"What mystery did {p.hero} and {p.helper} investigate?",
            answer=f"They investigated why {c.mystery}.",
        ),
        QAItem(
            question="What clue helped them solve the mystery?",
            answer=f"They found that {c.clue}. They followed that concrete clue instead of relying on suspicion.",
        ),
        QAItem(
            question="What was the real cause of the trouble?",
            answer=f"The real cause was that {c.cause}.",
        ),
        QAItem(
            question="How did the characters repair the problem?",
            answer=f"They {c.repair}. This restored the electronics and protected the address.",
        ),
        QAItem(
            question="What lesson did the sorcerer share?",
            answer=c.lesson,
        ),
        QAItem(
            question="What final image showed that the mystery was resolved?",
            answer=f"{c.ending}. The repaired device and verified address showed that the message could travel safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question="What are electronics?",
            answer="Electronics are devices and circuits that use electricity to sense, control, or send information.",
        ),
        QAItem(
            question="What is an address?",
            answer="An address is information that tells a person or message where to go.",
        ),
        QAItem(
            question="What is a sorcerer?",
            answer="A sorcerer is a story character who uses magic or spells.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn more by asking questions and looking closely.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early hint that prepares us for something important later.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thought written as words inside the story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.hero, world.helper, world.sorcerer):
        lines.append(f"{entity.kind}: {entity.name} meters={entity.meters} memes={entity.memes}")
    lines.append(
        f"state: curious={world.curious} solved={world.solved} repaired={world.repaired} "
        f"case={world.case.title!r}"
    )
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(seed=101, hero="Luna", helper="Theo", sorcerer="Sorcerer Orin", place="the lantern workshop"),
    StoryParams(seed=202, hero="Mira", helper="Pip", sorcerer="Sorcerer Vale", place="the crystal post room"),
    StoryParams(seed=303, hero="Nia", helper="Rin", sorcerer="Sorcerer Elio", place="the copper observatory"),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        if not asp_available():
            print("ASP mode unavailable: clingo is not installed.")
            return
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:", ", ".join(sorted(str(atom) for atom in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 30):
            if len(samples) >= args.n:
                break
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero} and {sample.params.helper} in {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
